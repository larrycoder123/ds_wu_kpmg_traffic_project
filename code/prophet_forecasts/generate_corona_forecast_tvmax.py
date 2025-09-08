import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from prophet import Prophet

corona_start = pd.Timestamp("2020-02-01")
corona_end = pd.Timestamp("2022-02-01")

df_data = pd.read_csv(os.path.abspath("./data/processed_data/dauerzaehlstellen_data.csv"), sep=",", dtype={"ZNR": str}, parse_dates=["DATUM"])
df_loc = pd.read_csv("./data/processed_data/dauerzaehlstellen_location.csv", sep=",", dtype={"ZNR": str})

district_numbers = df_loc["BEZIRK_NR"].drop_duplicates().sort_values().tolist()
df_data["FZTYP"] = df_data["FZTYP"].replace("LkwÄ", "Lkw")

vehicle_types = ["Kfz", "Lkw"]

def make_daily_df(df_area):
    rows = []
    for _,r in df_area.iterrows():
        start = r["DATUM"].replace(day=1)
        end = start + pd.offsets.MonthEnd(0)
        for d in pd.date_range(start, end, freq="D"):
            rows.append({"ds": d, "y": r["TVMAX"]})

    return pd.DataFrame(rows).dropna().sort_values("ds").reset_index(drop=True)

def generate_forecast(df_forecast, predict_future_days, file_postfix):
    for vehicle_type in vehicle_types:
        print(f"Calculating: {vehicle_type} ...")

        df_filtered = df_forecast[(df_forecast["RINAME"] == "Gesamt") & (df_forecast["FZTYP"] == vehicle_type)]        

        df = df_filtered.merge(df_loc[["ZNR", "BEZIRK_NR"]], on="ZNR", how="left").dropna(subset=["BEZIRK_NR"])
        df["BEZIRK_NR"] = df["BEZIRK_NR"].astype(int)

        training_rows = []
        forecast_rows = []

        for district_number in district_numbers:
            df_district = df[df["BEZIRK_NR"] == district_number]

            if df_district.empty:
                continue

            for znr in df_district["ZNR"].unique():
                print(f"Calculating ZNR: {vehicle_type}/{znr} ...")

                df_znr = df_district[df_district["ZNR"] == znr]

                daily = make_daily_df(df_znr)
                training_rows.append(daily)

                m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
                m.fit(daily[["ds", "y"]])
                future = m.make_future_dataframe(periods=predict_future_days, freq="D")
                fc = m.predict(future)

                fc_reduced = fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
                fc_reduced["district_number"] = district_number
                fc_reduced["znr"] = znr
                                
                fc_reduced["yhat"] = fc_reduced.apply(lambda row: 0.5 * row["yhat_upper"] if row["yhat"] <= 0 else row["yhat"], axis=1) # take 1/2 of yhat_upper on negative yhat
                fc_reduced["yhat_lower"] = fc_reduced["yhat_lower"].apply(lambda x: max(x, 0))

                for i in range(1, len(fc_reduced)): # if still negative yhat, take the previous value
                    if fc_reduced.loc[i, "yhat"] <= 0:
                        fc_reduced.loc[i, "yhat"] = fc_reduced.loc[i - 1, "yhat"]
                
                forecast_rows.append(fc_reduced)

        all_trainings = pd.concat(training_rows, ignore_index=True)
        all_trainings.to_csv(os.path.abspath(f"data/district_training_{file_postfix}_{vehicle_type}_tvmax.csv"), index=False)

        all_forecasts = pd.concat(forecast_rows, ignore_index=True)
        all_forecasts.to_csv(os.path.abspath(f"data/district_forecast_{file_postfix}_{vehicle_type}_tvmax.csv"), index=False)

def calculate_corona_delta(df_corona):
    for vehicle_type in vehicle_types:
        df_corona_forecast = pd.read_csv(os.path.abspath(f"data/district_forecast_corona_{vehicle_type}.csv"), sep=",", dtype={"znr": str, "district_number": int}, parse_dates=["ds"])
        df_corona_forecast = df_corona_forecast[(df_corona_forecast["ds"] >= corona_start) & (df_corona_forecast["ds"] <= corona_end)]        

        df_corona_filtered = df_corona[(df_corona["RINAME"] == "Gesamt") & (df_corona["FZTYP"] == vehicle_type)]        

        df = df_corona_filtered.merge(df_loc[["ZNR", "BEZIRK_NR"]], on="ZNR", how="left").dropna(subset=["BEZIRK_NR"])
        df["BEZIRK_NR"] = df["BEZIRK_NR"].astype(int)

        delta_rows = []

        for district_number in district_numbers:            
            df_district = df[df["BEZIRK_NR"] == district_number]

            if df_district.empty:
                continue

            for znr in df_district["ZNR"].unique():
                print(f"Calculating ZNR: {vehicle_type}/{znr} ...")

                df_znr = df_district[df_district["ZNR"] == znr]

                df_daily = make_daily_df(df_znr)
                df_daily["district_number"] = district_number 
                df_daily["znr"] = znr
                
                df_merged = pd.merge(df_daily, df_corona_forecast, on=["ds", "znr"], how="inner")
                df_merged["yhat"] = df_merged["yhat"].astype(int)
                
                df_merged["delta"] = df_merged["y"] - df_merged["yhat"]
                df_merged["delta_percent"] = ((df_merged["delta"] / df_merged["yhat"]) * 100).round(2)                

                df_delta = df_merged[["ds", "y", "yhat", "delta", "delta_percent", "znr"]].copy()
                df_delta.rename(columns={"y": "traffic_real"}, inplace=True)
                df_delta.rename(columns={"yhat": "traffic_forecast_without_corona"}, inplace=True)

                delta_rows.append(df_delta)

        all_deltas = pd.concat(delta_rows, ignore_index=True)
        all_deltas.to_csv(os.path.abspath(f"data/district_corona_delta_{vehicle_type}_tvmax.csv"), index=False)

def generate_plot(df_until_2032, df_corona_delta, title, file_path_output):
    plot_start = pd.to_datetime("2030-01-01")
    covid_19_start = pd.to_datetime("2020-02-01")
    covid_30_start = pd.to_datetime("2030-02-01")    

    df_until_2032["ds"] = pd.to_datetime(df_until_2032["ds"])    
    df_until_2032 = df_until_2032[df_until_2032["ds"] >= plot_start].copy()
    df_until_2032["year_month"] = df_until_2032["ds"].dt.to_period("M").dt.to_timestamp()
    df_corona_delta["ds"] = pd.to_datetime(df_corona_delta["ds"])

    df_covid_30 = df_until_2032[df_until_2032["ds"] >= covid_30_start].copy()

    day_offset = (covid_30_start - covid_19_start).days
    
    df_covid_30["ds_2020"] = df_covid_30["ds"] - pd.Timedelta(days=day_offset)
    df_covid_30 = df_covid_30.merge(df_corona_delta[["ds", "znr", "delta_percent"]], left_on=["ds_2020", "znr"], right_on=["ds", "znr"], how="left", suffixes=("", "_corona"))

    df_covid_30["delta_percent"] = df_covid_30["delta_percent"].fillna(0)
    df_covid_30["delta_percent"] = df_covid_30["delta_percent"].apply(lambda x: min(x, 0))
    df_covid_30["adjusted_yhat"] = df_covid_30["yhat"] * (1 + df_covid_30["delta_percent"].astype(float) / 100)
    
    #df_covid_30.to_csv(os.path.abspath(f"data/covid_30_temp.csv"), index=False)

    monthly_sum = df_until_2032.groupby("year_month")["yhat"].sum().reset_index()
    monthly_sum_covid_30 = df_covid_30.groupby("year_month")["adjusted_yhat"].sum().reset_index()
    
    tick_dates = monthly_sum["year_month"]
    tick_labels = [d.strftime("%Y") if d.month == 1 else '' for d in tick_dates]

    plt.figure(figsize=(12, 6))
    plt.plot(monthly_sum["year_month"], monthly_sum["yhat"], label="Forecast")
    plt.plot(monthly_sum_covid_30["year_month"], monthly_sum_covid_30["adjusted_yhat"], linestyle="dotted", label="Forecast with Covid 19")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Traffic Count")
    plt.xticks(ticks=tick_dates, labels=tick_labels, rotation=45)
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    plt.tight_layout()
    plt.grid(True)
    plt.legend()
    plt.savefig(file_path_output, dpi=300)
    #plt.show()

df_pre_corona = df_data[(df_data["DATUM"] < corona_start)]
generate_forecast(df_pre_corona, 365 * 2, "corona") # predict normal traffic during corona time

generate_forecast(df_data, 365 * 7, "2032") # predict traffic between 2024 and 2032

df_corona = df_data[(df_data["DATUM"] >= corona_start) & (df_data["DATUM"] <= corona_end)]
calculate_corona_delta(df_corona)

df_until_2032_kfz = pd.read_csv(os.path.abspath("data/district_forecast_2032_Kfz_tvmax.csv"), sep=",", parse_dates=["ds"])
df_corona_delta_kfz = pd.read_csv(os.path.abspath("data/district_corona_delta_Kfz_tvmax.csv"), sep=",", parse_dates=["ds"])
generate_plot(df_until_2032_kfz, df_corona_delta_kfz, "", os.path.abspath("output/generate_corona_forecast_Kfz_tvmax.png"))

df_until_2032_lkw = pd.read_csv(os.path.abspath("data/district_forecast_2032_Lkw_tvmax.csv"), sep=",", parse_dates=["ds"])
df_corona_delta_lkw = pd.read_csv(os.path.abspath("data/district_corona_delta_Lkw_tvmax.csv"), sep=",", parse_dates=["ds"])
generate_plot(df_until_2032_lkw, df_corona_delta_lkw, "", os.path.abspath("output/generate_corona_forecast_Lkw_tvmax.png"))

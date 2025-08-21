import os
import pandas as pd
from prophet import Prophet

predict_future_days = 365

df_data = pd.read_csv(os.path.abspath("./data/processed_data/dauerzaehlstellen_data.csv"), sep=",", dtype={"ZNR": str}, parse_dates=["DATUM"])
df_loc = pd.read_csv("./data/processed_data/dauerzaehlstellen_location.csv", sep=",", dtype={"ZNR": str})

district_numbers = df_loc["BEZIRK_NR"].drop_duplicates().sort_values().tolist()
df_data["FZTYP"] = df_data["FZTYP"].replace("LkwÄ", "Lkw")

vehicle_types = ["Kfz", "Lkw"]

def make_daily_df(df_area):
    rows = []
    for _, r in df_area.iterrows():
        start = r["DATUM"].replace(day=1)
        end = start + pd.offsets.MonthEnd(0)
        for d in pd.date_range(start, end, freq="D"):
            wd = d.weekday()
            if wd == 0:         y = r["DTVMO"]
            elif 1 <= wd <= 3:  y = r["DTVDD"]
            elif wd == 4:       y = r["DTVFR"]
            elif wd == 5:       y = r["DTVSA"]
            else:               y = r["DTVSF"]
            rows.append({"ds": d, "y": y})

    return pd.DataFrame(rows).dropna().sort_values("ds").reset_index(drop=True)

for vehicle_type in vehicle_types:
    print(f"Calculating: {vehicle_type} ...")

    df_filtered = df_data[(df_data["RINAME"] == "Gesamt") & (df_data["FZTYP"] == vehicle_type)]

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
            daily["district_number"] = district_number
            training_rows.append(daily)

            m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
            m.fit(daily[["ds", "y"]])
            future = m.make_future_dataframe(periods=predict_future_days, freq="D")
            fc = m.predict(future)

            fc_reduced = fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
            fc_reduced["district_number"] = district_number
            fc_reduced["znr"] = znr

            fc_reduced["yhat"] = fc_reduced["yhat"].clip(lower=0)
            fc_reduced["yhat_lower"] = fc_reduced["yhat_lower"].clip(lower=0)

            forecast_rows.append(fc_reduced)

    all_trainings = pd.concat(training_rows, ignore_index=True)
    all_trainings.to_csv(os.path.abspath(f"data/district_training_{vehicle_type}.csv"), index=False)

    all_forecasts = pd.concat(forecast_rows, ignore_index=True)
    all_forecasts.to_csv(os.path.abspath(f"data/district_forecast_{vehicle_type}.csv"), index=False)

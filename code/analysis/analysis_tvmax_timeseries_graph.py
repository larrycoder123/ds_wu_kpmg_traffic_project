import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

file_path_input = os.path.abspath("data/dauerzaehlstellen_data.csv")
file_path_output = os.path.abspath("output/analysis_tvmax_timeseries_graph.png")

df = pd.read_csv(file_path_input, sep=",", dtype={"ZNR": str}, parse_dates=["DATUM"])

def make_daily_df(df_area):
    rows = []
    for _,r in df_area.iterrows():
        start = r["DATUM"].replace(day=1)
        end   = start + pd.offsets.MonthEnd(0)
        for d in pd.date_range(start, end, freq = "D"):
            wd = d.weekday()
            if wd == 0:        y=r["DTVMO"]
            elif 1 <= wd <= 3: y=r["DTVDD"]
            elif wd == 4:      y=r["DTVFR"]
            elif wd == 5:      y=r["DTVSA"]
            else:              y=r["DTVSF"]
            rows.append({"DATUM": d, "COUNT": y, "FZTYP": r["FZTYP"]})

    return pd.DataFrame(rows).dropna().sort_values("DATUM").reset_index(drop=True)

df = df[df["RINAME"] == "Gesamt"]
df["FZTYP"] = df["FZTYP"].replace("LkwÄ", "Lkw")

df = make_daily_df(df)

df["Monat"] = df["DATUM"].dt.to_period("M").dt.to_timestamp()
df = df.groupby(["Monat", "FZTYP"], as_index=False)["COUNT"].sum()
df = df.rename(columns={"Monat": "Datum"})

tick_dates = df["Datum"].drop_duplicates().sort_values()
tick_dates = [d for d in tick_dates if d.month == 1]
tick_labels = [d.strftime("%Y") for d in tick_dates]

plt.figure(figsize=(12, 6))

start_date = pd.Timestamp("2020-02-01")
end_date = pd.Timestamp("2022-02-01")

for idx, (key, grp) in enumerate(df.groupby("FZTYP")):
    grp = grp.sort_values("Datum")
    before = grp[grp["Datum"] < start_date]
    during = grp[(grp["Datum"] >= start_date) & (grp["Datum"] <= end_date)]
    after = grp[grp["Datum"] > end_date]

    color = plt.cm.tab10(idx % 10)

    plt.plot(before["Datum"], before["COUNT"], label=key, color=color)
    plt.plot(during["Datum"], during["COUNT"], linestyle="dotted", color=color)
    plt.plot(after["Datum"], after["COUNT"], color=color)

plt.xlabel("Date")
plt.ylabel("Traffic Count")
plt.title("")
plt.legend(title="Type")
plt.xticks(ticks=tick_dates, labels=tick_labels, rotation=45)
plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
plt.tight_layout()
plt.grid(True)
plt.savefig(file_path_output, dpi=300)
#plt.show()

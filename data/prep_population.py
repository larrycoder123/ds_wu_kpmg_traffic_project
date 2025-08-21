import os
import pandas as pd

file_path = os.path.abspath("data/raw/vie-bez-pop-sex-stk-1869f.csv")
file_path_cleaned = os.path.abspath("data/population.csv")

df = pd.read_csv(file_path, delimiter=";", encoding="ISO-8859-1")

# Filter years
df = df[(df["REF_YEAR"] >= 2016) & (df["REF_YEAR"] <= 2024)][["REF_YEAR", "DISTRICT_CODE", "POP_TOTAL",]]

# Convert to string and get first 3 letters
df["DISTRICT_CODE"] = df["DISTRICT_CODE"].astype(str)
df["DISTRICT_CODE"] = df["DISTRICT_CODE"].str[:3]

df = df.rename(columns={"REF_YEAR": "Jahr", "DISTRICT_CODE": "Bezirk_Code", "POP_TOTAL": "Population"})

df.to_csv(file_path_cleaned, index=False, encoding="utf-8")

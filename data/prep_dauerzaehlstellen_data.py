import os
import pandas as pd

file_path = os.path.abspath("data/raw/dauerzaehlstellen.csv")
file_path_cleaned = os.path.abspath("data/dauerzaehlstellen_data.csv")

df = pd.read_csv(file_path, delimiter=";", encoding="ISO-8859-1")

# Dictionary to map German month abbreviations to numerical values
month_mapping = { "JAN.": "01", "JAN": "01", "FEB.": "02", "FEB": "02", "MÄRZ": "03", "APR.": "04", "APR": "04", "APRIL": "04", "MAI.": "05", "MAI": "05", "JUNI": "06", "JULI": "07", "AUG.": "08", "AUG": "08", "SEPT": "09", "SEP.": "09", "OKT.": "10", "OKT": "10", "NOV.": "11", "NOV": "11", "DEZ.": "12", "DEZ": "12" }

# Remove rows where DTVMS is less than 0
df = df[df["DTVMS"] >= 0]

# Convert the MONAT column to numeric values
df["MONAT"] = df["MONAT"].str.strip().map(month_mapping)  # Remove extra spaces and map months

# Create a new DATUM column from JAHR and MONAT
df["DATUM"] = pd.to_datetime(df["JAHR"].astype(str) + "-" + df["MONAT"] + "-01", format="%Y-%m-%d")

# Process the TVMAXT column to extract proper dates
df["TVMAXT"] = df["TVMAXT"].str.split(",", n=1).str[-1].str.strip()  # Remove everything before ','
df["TVMAXT"] = pd.to_datetime(df["TVMAXT"] + df["JAHR"].astype(str), format="%d.%m.%Y")

# Create ISTCOVID19
df["ISTCOVID19"] = ((df["DATUM"] >= pd.to_datetime("2020-02-01")) & (df["DATUM"] <= pd.to_datetime("2022-01-30"))).astype(int)

# Drop the original JAHR and MONAT columns
df.drop(columns=["JAHR", "MONAT"], inplace=True)

# Reorder columns to move DATUM to the first position
column_order = ["DATUM"] + [col for col in df.columns if col != "DATUM"]
df = df[column_order]

df.to_csv(file_path_cleaned, index=False, encoding="utf-8")

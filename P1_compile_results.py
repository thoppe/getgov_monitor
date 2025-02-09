import pandas as pd
from dspipe import Pipe

data = Pipe("data/changelog/")(pd.read_csv, -1)
df = pd.concat(data)

# Sort by latest
df = df.sort_values("commit_date", ascending=False)

# Drop the weird column that came into play
del df["Unnamed: 0"]

# Merge Organization and Organization name
idx0 = df["Organization"].isna()
idx1 = df["Organization Name"].isna()

# Make sure we have no overlaps
assert (~(idx0 + idx1)).sum() == 0

print(df.columns)
df.loc[~idx1, "Organization"] = df.loc[~idx1, "Organization Name"]
idx0 = df["Organization"].isna()

# Save the results to file
df.to_csv("data/all_federal_us_domain_changes.csv", index=False)

# Only keep results after a specific date
# cutoff_date = 1730841600 # Nov 6th 2024
cutoff_date = 1735689600  # Jan 1st 2025
df = df[df["commit_date"] >= cutoff_date]

# Drop columns that aren't useful (data changed in early years)
df = df.dropna(axis=1, how="all")

# Drop changed_old (already counted in changed old)
df = df[df["modification"].isin(["added", "deleted", "changed_new"])]

idx = df["modification"] == "changed_new"
df.loc[idx, "modification"] = "changed"

df.loc[df["modification"] == "added", "modification"] = "✅"
df.loc[df["modification"] == "deleted", "modification"] = "❌"
df.loc[df["modification"] == "changed", "modification"] = "✏️"

df = df.rename(columns={"commit_datetime": "date"})
df = df.rename(columns={"modification": ""})

keep_cols = ["Domain Name", "Agency", "", "date"]
df = df[keep_cols]

# Fix the URL
df["Domain Name"] = [f"[{url}](https://{url})" for url in df["Domain Name"]]

df = df.set_index("Domain Name")
df["date"] = df["date"].astype(str).str.split(" ").str[0]

table = df.to_markdown()
print(table)

f_README = "README.md"
with open(f_README) as FIN:
    text = FIN.read()

text = "##".join(text.split("##")[:-1])
text += "## Federal domain registrar updates\n"
text += "\n"
text += table

with open(f_README, "w") as FOUT:
    FOUT.write(text)

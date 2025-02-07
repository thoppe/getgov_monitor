import pandas as pd
from dspipe import Pipe

data = Pipe("data/changelog/")(pd.read_csv, -1)
df = pd.concat(data)

# Only keep results after Jan 1st 2025
# cutoff_date = 1730841600 # Nov 6th 2024

cutoff_date = 1735689600  # Jan 1st 2025
df = df[df["commit_date"] >= cutoff_date]

# Drop columns that aren't useful (data changed in early years)
df = df.dropna(axis=1, how="all")

# Sort by latest
df = df.sort_values("commit_date", ascending=False)

# Drop changed_old (already counted in changed old)
df = df[df["modification"].isin(["added", "deleted", "changed_new"])]

idx = df["modification"] == "changed_new"
df.loc[idx, "modification"] = "changed"

df = df.rename(columns={"commit_datetime": "date"})

keep_cols = ["Domain Name", "Agency", "modification", "date"]
df = df[keep_cols]
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

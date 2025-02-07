import pandas as pd
from pathlib import Path
from tqdm import tqdm
from git import Repo
from io import StringIO

# Define the repository URL and destination directory
repo_url = "https://github.com/cisagov/dotgov-data"
destination_dir = "dotgov-data"
f_target = Path("dotgov-data/current-federal.csv")

save_dest = Path("data/changelog")
save_dest.mkdir(exist_ok=True, parents=True)

# Clone the repo first
try:
    repo = Repo(destination_dir)
except:
    Repo.clone_from(repo_url, destination_dir)
    print(f"Repository cloned to {destination_dir}")

# Now pull the latest updates
repo = Repo(destination_dir)

# Force a checkout back to the main branch for a reset
repo.git.checkout("main")

# Pull the latest changes
pull_info = repo.remotes.origin.pull()

##################################################################

# Get a listing of all the commits
commits = list(repo.iter_commits())

# Step from oldest to newest
commits.reverse()

for k, commit in enumerate(tqdm(commits, total=len(commits))):

    hexsha = commit.hexsha
    #print(commit.committed_date, commit.committed_datetime)

    timestamp1 = commit.committed_date

    f_save = save_dest / f"{timestamp1}.csv"
    if f_save.exists():
        continue

    # Checkout the commit in a detached HEAD state
    repo.git.checkout(hexsha)

    if not f_target.exists():
        print(f"{f_target.name} does not exist in {commit.committed_datetime}")
        # Open an empty csv and save it
        pd.DataFrame().to_csv(f_save)

    # Target exists, now find previous target
    local_name = "current-federal.csv"

    data = []
    
    for diff in commit.diff(commits[k-1], paths=local_name):

        # We only want to keep the "modified" codes
        if diff.change_type != "M":
            continue

        if diff.a_path != local_name or diff.b_path != local_name:
            continue

        n1 = commits[k].tree[local_name].data_stream.read()
        d1 = pd.read_csv(StringIO(n1.decode("utf-8", errors="ignore")))

        n0 = commits[k-1].tree[local_name].data_stream.read()
        d0 = pd.read_csv(StringIO(n0.decode("utf-8", errors="ignore")))

        d0 = d0.set_index("Domain Name")
        d1 = d1.set_index("Domain Name")

        # Added rows
        for row in d1.index.difference(d0.index):
            item = d1.loc[row].to_dict()
            item['modification'] = 'added'
            item['Domain Name'] = row
            data.append(item)

        # Deleted rows
        for row in d0.index.difference(d1.index):
            item = d0.loc[row].to_dict()
            item['modification'] = 'deleted'
            item['Domain Name'] = row
            data.append(item)

        # Modified rows
        common_index = d1.index.intersection(d0.index)
        for idx in common_index:
            r0 = d0.loc[idx]
            r1 = d1.loc[idx]
            delta = (r0==r1)
            if not delta.all():

                item = d0.loc[idx].to_dict()
                item['modification'] = 'changed_old'
                item['Domain Name'] = idx
                data.append(item)

                item = d1.loc[idx].to_dict()
                item['modification'] = 'changed_new'
                item['Domain Name'] = idx
                data.append(item)

    # An empty changelog for whatever reason, don't mark anything
    if not len(data):
        pd.DataFrame().to_csv(f_save)
        continue        

    df = pd.DataFrame(data).set_index("Domain Name")

    df['commit_datetime'] = commit.committed_datetime
    df['commit_date'] = commit.committed_date

    print(f"Saved ({len(df)}) edits to {f_save} {commit.committed_datetime}")
    df.to_csv(f_save)

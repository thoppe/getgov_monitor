import pandas as pd
import json
import os
import hashlib
from datetime import datetime
from dspipe import Pipe

# Configuration
USERNAME = "fed-us-domain-bot.bsky.social"
APP_PASSWORD = os.getenv("BLUESKY_BOT_TOKEN")

assert APP_PASSWORD

df = pd.read_csv("data/bluesky_targets.csv")
df = df.sort_values("commit_date")

# Keep only added or deleted
df = df[df["modification"].isin(["added", "deleted"])]

# Create a UUID for each row to track tweets
df["uuid"] = [
    hashlib.sha1(json.dumps(row.to_dict(), sort_keys=True).encode("utf-8")).hexdigest()
    for _, row in df.iterrows()
]

df = df.set_index("uuid")


def tweet(hx, f1):
    row = df.loc[hx]

    post = []

    if row["modification"] == "added":
        label = "🚀 NOTICE: Federal US website newly registered."
        notice = "Federal US website registered. Content may not be visible yet."
    elif row["modification"] == "deleted":
        label = "❌ NOTICE Federal US website newly deleted."
        notice = "Federal US website delisted. URL is not valid."
    else:
        raise KeyError(row["modification"])

    post.append(label)

    url = f"https://{row['Domain Name']}"
    post.append(url)
    post.append("")

    time = row["commit_datetime"].split("+")[0]

    name = row["Agency"]
    org = row["Organization"]
    if org and isinstance(org, str) and org != name:
        name = f"{name} ({org})"

    post.append(f"Action taken by the {name} at or around {time}.")

    external_embed = {
        "$type": "app.bsky.embed.external",
        "external": {
            "uri": url,
            "title": row["Domain Name"],
            "thumb": None,
            "description": notice,
        },
    }

    post = "\n".join(post)
    print(post)

    # Initialize Bluesky client
    # Import everything here since it's slow, we might not need it!
    from atproto import Client

    client = Client()
    client.login(USERNAME, APP_PASSWORD)

    response = client.send_post(post, embed=external_embed)
    print(response)

    # Extract relevant details
    post_uri = response.uri

    # Convert post URI to a shareable link
    if post_uri:
        # Extract last part of the URI
        post_id = post_uri.split("/")[-1]
        # Extract the handle without .bsky.social
        handle = USERNAME.split(".")[0]
        post_link = f"https://bsky.app/profile/{handle}/post/{post_id}"
    else:
        post_link = None

    post_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    # Print post details
    post_data = {
        "date": post_date,
        "link": post_link,
        "post": post,
    }

    js = json.dumps(post_data, indent=2)
    print(js)

    with open(f1, 'w') as FOUT:
        FOUT.write(js)

Pipe(df.index, "data/bluesky_outputs", output_suffix=".json")(tweet, 1)

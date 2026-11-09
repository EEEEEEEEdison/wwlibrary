"""Write GitHub Release asset download counts into teams.json."""

import json
import os
import urllib.request
from pathlib import Path

REPO = "EEEEEEEEdison/wwlibrary"
TAG = "1"
API = "https://api.github.com"


def api(url, token):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "wwlibrary-sync",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_counts(token):
    release = api(f"{API}/repos/{REPO}/releases/tags/{TAG}", token)
    counts = {}
    page = 1
    while True:
        batch = api(
            f"{API}/repos/{REPO}/releases/{release['id']}/assets"
            f"?per_page=100&page={page}", token)
        for asset in batch:
            counts[asset["name"]] = int(asset.get("download_count") or 0)
        if len(batch) < 100:
            break
        page += 1
    return counts


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    counts = fetch_counts(token)

    path = Path("teams.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    missing = []
    for team in data.get("teams", []):
        for code in team.get("codes", []):
            asset = code.get("assetName")
            if not asset or asset not in counts:
                missing.append(code.get("filename"))
                continue
            count = counts[asset]
            if code.get("downloadCount") != count:
                code["downloadCount"] = count
                changed = True
    if missing:
        raise SystemExit(f"release assets missing: {missing}")
    if not changed:
        print("download counts unchanged")
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("download counts updated")


if __name__ == "__main__":
    main()

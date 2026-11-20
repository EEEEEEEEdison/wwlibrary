#!/usr/bin/env python3
"""自动发布 submissions/ 下已合并的投稿：
1. 复核投稿格式与唯一性（复用 validate_submission.py）
2. 将 code.zip 上传至 GitHub Release（tag: 1）
3. 更新 teams.json 与 teams/<Slug>.json
4. 清理已发布的 submissions/<Slug>/<版本>-<用户名>/ 目录

用法：
    python .github/scripts/publish_submissions.py
    python .github/scripts/publish_submissions.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_submission as vs  # noqa: E402

ROOT = vs.ROOT
SUBMISSIONS = vs.SUBMISSIONS
INDEX_PATH = vs.INDEX_PATH
TEAMS_DIR = ROOT / "teams"

REPO = os.environ.get("GITHUB_REPOSITORY", "EEEEEEEEdison/wwlibrary")
TAG = os.environ.get("RELEASE_TAG", "1")
API = "https://api.github.com"
UPLOADS_API = "https://uploads.github.com"


def api_json(
    url: str,
    token: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    content_type: str | None = None,
    timeout: int = 60,
) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "wwlibrary-publisher",
    }
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} 失败 ({exc.code}): {detail}") from exc


def fetch_release_and_assets(token: str) -> tuple[int, dict[str, dict]]:
    release = api_json(f"{API}/repos/{REPO}/releases/tags/{TAG}", token)
    if not isinstance(release, dict) or "id" not in release:
        raise RuntimeError(f"无法读取 Release tag={TAG}")
    release_id = int(release["id"])

    assets: dict[str, dict] = {}
    page = 1
    while True:
        batch = api_json(
            f"{API}/repos/{REPO}/releases/{release_id}/assets?per_page=100&page={page}",
            token,
        )
        if not isinstance(batch, list):
            break
        for asset in batch:
            assets[asset["name"]] = {
                "id": int(asset["id"]),
                "download_count": int(asset.get("download_count") or 0),
            }
        if len(batch) < 100:
            break
        page += 1
    return release_id, assets


def upload_release_asset(
    release_id: int,
    asset_name: str,
    zip_bytes: bytes,
    token: str,
) -> dict:
    encoded = urllib.parse.quote(asset_name, safe="")
    url = f"{UPLOADS_API}/repos/{REPO}/releases/{release_id}/assets?name={encoded}"
    res = api_json(
        url,
        token,
        method="POST",
        body=zip_bytes,
        content_type="application/zip",
        timeout=120,
    )
    if not isinstance(res, dict):
        raise RuntimeError(f"上传资产 {asset_name} 返回异常")
    return res


def delete_release_asset(asset_id: int, token: str) -> None:
    api_json(
        f"{API}/repos/{REPO}/releases/assets/{asset_id}",
        token,
        method="DELETE",
    )


def format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def make_asset_name(slug: str, version: str, zip_bytes: bytes) -> str:
    sha8 = hashlib.sha256(zip_bytes).hexdigest()[:8]
    return f"{slug}_{version}_{sha8}.zip"


def format_index_description(raw_description: str, scenes: list[str], difficulty: str) -> str:
    body = vs.description_body(raw_description)
    scenes_text = "、".join(scenes)
    return f"【场景】{scenes_text}\n【难度】{difficulty}\n\n【说明】\n{body}\n"


def pending_submission_dirs() -> list[Path]:
    dirs: list[Path] = []
    if not SUBMISSIONS.is_dir():
        return dirs
    for path in sorted(SUBMISSIONS.glob("*/*")):
        if path.is_dir() and not path.parent.name.startswith("_"):
            dirs.append(path)
    return dirs


def validate_all_pending(dirs: list[Path]) -> list[tuple[Path, dict]]:
    vs.ERRORS.clear()
    vs.WARNINGS.clear()
    schema = vs.load_schema()
    existing = vs.load_existing_index()

    validated: list[tuple[Path, dict]] = []
    items_for_dup: list[dict] = []
    for path in dirs:
        info = vs.check_submission_dir(path, schema)
        if info:
            meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
            validated.append((path, meta))
            items_for_dup.append(info)

    vs.check_duplicates(items_for_dup, existing)

    for line in vs.WARNINGS:
        print(f"[WARN] {line}")
    if vs.ERRORS:
        for line in vs.ERRORS:
            print(f"[ERROR] {line}", file=sys.stderr)
        raise SystemExit(f"发布中止：发现 {len(vs.ERRORS)} 个校验错误")
    return validated


def post_pr_comment(commit_sha: str, published: list[dict], page_url: str, token: str) -> None:
    if not commit_sha or not published:
        return
    try:
        pulls = api_json(f"{API}/repos/{REPO}/commits/{commit_sha}/pulls", token)
    except Exception as exc:
        print(f"[WARN] 查询关联 PR 失败（忽略）：{exc}")
        return
    if not isinstance(pulls, list) or not pulls:
        return

    lines = [
        "已自动发布到索引库与 Release，感谢投稿与署名！",
        "",
    ]
    for item in published:
        lines.extend([
            f"- **代码名**：`{item['name']}`（v`{item['version']}` / 作者：**{item['author']}**）",
            f"- **队伍**：`{item['team']}`",
            f"- **分类**：{' / '.join(item['scenes'])} · {item['difficulty']}",
            f"- **下载链接**：{item['downloadUrl']}",
            f"- **在线索引**：{page_url}/",
        ])
        if item.get("replacedVersion"):
            lines.append(
                f"- **替换升级**：已替换旧版本 v`{item['replacedVersion']}`（旧资产 `{item.get('replacedAsset') or '-'}` 已清理），"
                f"继承历史下载量 **{item.get('downloadCountOffset', 0)}** 次"
            )
        lines.append("")
    lines.append("下载量将由 `sync-downloads` 自动同步。")
    body_bytes = json.dumps({"body": "\n".join(lines)}, ensure_ascii=False).encode("utf-8")

    for pr in pulls:
        number = pr.get("number")
        if not number:
            continue
        try:
            api_json(
                f"{API}/repos/{REPO}/issues/{number}/comments",
                token,
                method="POST",
                body=body_bytes,
                content_type="application/json",
            )
            print(f"已在 PR #{number} 回复发布结果")
        except Exception as exc:
            print(f"[WARN] 回复 PR #{number} 失败（忽略）：{exc}")


def write_step_summary(published: list[dict]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path or not published:
        return
    lines = [
        "### 投稿自动发布完成",
        "",
        "| 队伍 | 代码名 | 作者 | 版本 | 资产名 | 备注 | 下载链接 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in published:
        note = (
            f"替换 v`{item['replacedVersion']}`（继承 {item.get('downloadCountOffset', 0)} 下载）"
            if item.get("replacedVersion")
            else "新增"
        )
        lines.append(
            f"| `{item['slug']}` | {item['name']} | {item['author']} | `{item['version']}` "
            f"| `{item['assetName']}` | {note} | [下载]({item['downloadUrl']}) |"
        )
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError):
            pass

    parser = argparse.ArgumentParser(description="自动发布 submissions/ 下的投稿到 Release 与 teams.json")
    parser.add_argument("--dry-run", action="store_true", help="仅校验并演练输出，不上传 Release 也不修改仓库文件")
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""), help="触发发布的 commit SHA（用于回复关联 PR）")
    parser.add_argument("--output-json", help="将本次发布摘要写入指定 JSON 文件")
    args = parser.parse_args()

    dirs = pending_submission_dirs()
    if not dirs:
        print("submissions/ 下没有待发布投稿，跳过")
        return 0

    validated = validate_all_pending(dirs)
    index_data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    page_url = str(index_data.get("pageUrl", "https://eeeeeeeedison.github.io/wwlibrary")).rstrip("/")

    token = os.environ.get("GITHUB_TOKEN", "")
    if not args.dry_run:
        if not token:
            raise SystemExit("缺少 GITHUB_TOKEN，无法上传 Release 资产")
        release_id, assets = fetch_release_and_assets(token)
    else:
        release_id, assets = 0, {}

    teams_by_slug: dict[str, dict] = {
        t["slug"]: t for t in index_data.get("teams", []) if isinstance(t, dict) and "slug" in t
    }

    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    published: list[dict] = []
    touched_slugs: set[str] = set()
    assets_to_delete: list[str] = []

    for sub_dir, meta in validated:
        members = [m.strip() for m in meta["team"]]
        slug = vs.team_slug(members)
        name = meta["name"].strip()
        author = meta["author"].strip()
        version = meta["version"].strip()
        scenes = list(meta["scenes"])
        difficulty = meta["difficulty"]
        replaces = str(meta.get("replaces") or "").strip()

        zip_path = sub_dir / "code.zip"
        zip_bytes = zip_path.read_bytes()
        asset_name = make_asset_name(slug, version, zip_bytes)
        download_url = f"https://github.com/{REPO}/releases/download/{TAG}/{asset_name}"
        filename = f"{name}_{author}_{version}.zip"

        team_obj = teams_by_slug.get(slug)
        replace_idx: int | None = None
        old_asset_name = ""
        inherited_offset = 0

        if replaces:
            if team_obj is None:
                raise RuntimeError(f"replaces 指定的队伍 {slug} 不存在")
            for idx, existing_code in enumerate(team_obj.get("codes", [])):
                if (
                    str(existing_code.get("author", "")).strip() == author
                    and str(existing_code.get("version", "")).strip() == replaces
                ):
                    replace_idx = idx
                    break
            if replace_idx is None:
                raise RuntimeError(f"replaces 指定的旧版本 {slug}/{author}/{replaces} 不存在")

            old_entry = team_obj["codes"][replace_idx]
            old_asset_name = str(old_entry.get("assetName") or "")
            old_offset = int(old_entry.get("downloadCountOffset") or 0)
            if old_asset_name == asset_name:
                inherited_offset = old_offset
            else:
                if old_asset_name in assets:
                    live_old_dl = int(assets[old_asset_name]["download_count"])
                else:
                    live_old_dl = max(0, int(old_entry.get("downloadCount") or 0) - old_offset)
                inherited_offset = old_offset + live_old_dl
                if old_asset_name:
                    assets_to_delete.append(old_asset_name)

        if args.dry_run:
            action_note = (
                f" [替换 v{replaces}，清理 {old_asset_name}，继承 {inherited_offset} 下载]"
                if replaces
                else ""
            )
            print(
                f"[DRY-RUN] 将上传 {sub_dir.relative_to(ROOT)} -> Release {TAG}/{asset_name} "
                f"({format_size(len(zip_bytes))}){action_note}"
            )
        else:
            if asset_name in assets:
                print(f"[SKIP UPLOAD] Release {TAG} 已存在资产 {asset_name}，复用现有资产")
            else:
                uploaded = upload_release_asset(release_id, asset_name, zip_bytes, token)
                assets[asset_name] = {
                    "id": int(uploaded.get("id") or 0),
                    "download_count": int(uploaded.get("download_count") or 0),
                }
                print(f"[UPLOADED] {asset_name} ({format_size(len(zip_bytes))})")

        current_asset_dl = int(assets.get(asset_name, {}).get("download_count", 0))
        code_entry: dict[str, object] = {
            "filename": filename,
            "downloadUrl": download_url,
            "rawUrl": download_url,
            "name": name,
            "description": format_index_description(meta["description"], scenes, difficulty),
            "author": author,
            "version": version,
            "team": ", ".join(members),
            "members": members,
            "size": len(zip_bytes),
            "sizeFormatted": format_size(len(zip_bytes)),
            "timestamp": now_ts,
            "modifiedAt": now_iso,
            "scenes": scenes,
            "difficulty": difficulty,
            "assetName": asset_name,
            "downloadCount": inherited_offset + current_asset_dl,
        }
        if inherited_offset > 0:
            code_entry["downloadCountOffset"] = inherited_offset

        if team_obj is None:
            team_obj = {
                "team": ", ".join(members),
                "slug": slug,
                "members": members,
                "totalCodes": 0,
                "jsonUrl": f"{page_url}/teams/{slug}.json",
                "codes": [],
            }
            index_data.setdefault("teams", []).append(team_obj)
            teams_by_slug[slug] = team_obj

        if replace_idx is not None:
            team_obj["codes"][replace_idx] = code_entry
        else:
            team_obj["codes"].append(code_entry)
        team_obj["totalCodes"] = len(team_obj["codes"])
        touched_slugs.add(slug)

        published.append({
            "slug": slug,
            "team": team_obj["team"],
            "name": name,
            "author": author,
            "version": version,
            "scenes": scenes,
            "difficulty": difficulty,
            "assetName": asset_name,
            "filename": filename,
            "downloadUrl": download_url,
            "submissionDir": sub_dir.relative_to(ROOT).as_posix(),
            "replacedVersion": replaces,
            "replacedAsset": old_asset_name,
            "downloadCountOffset": inherited_offset,
        })

    index_data["totalTeams"] = len(index_data.get("teams", []))
    index_data["totalCodes"] = sum(len(t.get("codes", [])) for t in index_data.get("teams", []))

    if args.dry_run:
        print(f"[DRY-RUN] 预计发布 {len(published)} 个投稿：totalTeams={index_data['totalTeams']}, totalCodes={index_data['totalCodes']}")
        print(json.dumps(published, ensure_ascii=False, indent=2))
        return 0

    # 新资产上传完成后再清理被替换的旧资产（若仍被其他条目引用则跳过删除）
    referenced_assets = {
        c.get("assetName")
        for t in index_data.get("teams", [])
        for c in t.get("codes", [])
        if c.get("assetName")
    }
    for old_asset in dict.fromkeys(assets_to_delete):
        if old_asset in referenced_assets:
            continue
        info = assets.get(old_asset)
        if info and info.get("id"):
            delete_release_asset(int(info["id"]), token)
            assets.pop(old_asset, None)
            print(f"[DELETED OLD ASSET] {old_asset}")

    # 校验 Release 资产完整性，确保后续 sync-downloads 不会报 missing
    missing = [
        c.get("filename")
        for t in index_data.get("teams", [])
        for c in t.get("codes", [])
        if not c.get("assetName") or c.get("assetName") not in assets
    ]
    if missing:
        raise RuntimeError(f"Release {TAG} 缺少以下资产，已中止写入 teams.json：{missing}")

    INDEX_PATH.write_text(json.dumps(index_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    for slug in sorted(touched_slugs):
        team_file = TEAMS_DIR / f"{slug}.json"
        team_file.write_text(
            json.dumps(teams_by_slug[slug], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for sub_dir, _ in validated:
        shutil.rmtree(sub_dir)
        parent = sub_dir.parent
        if parent != SUBMISSIONS and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(published, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    write_step_summary(published)
    post_pr_comment(args.commit_sha, published, page_url, token)

    print(f"✅ 已发布 {len(published)} 个投稿，totalTeams={index_data['totalTeams']}, totalCodes={index_data['totalCodes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

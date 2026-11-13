#!/usr/bin/env python3
"""wwlibrary 投稿校验器（只依赖 Python 标准库）。

用法：
    python .github/scripts/validate_submission.py --all
    python .github/scripts/validate_submission.py --base <base-sha> --head <head-sha>

退出码 0 表示通过，1 表示存在硬性错误。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
SUBMISSIONS = ROOT / "submissions"
SCHEMA_PATH = ROOT / ".github" / "submission-schema.json"
INDEX_PATH = ROOT / "teams.json"

META_REQUIRED = {
    "schemaVersion",
    "name",
    "team",
    "author",
    "version",
    "scenes",
    "difficulty",
    "description",
    "tested",
    "license",
}
META_OPTIONAL = {"video", "contact"}
META_KEYS = META_REQUIRED | META_OPTIONAL

VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SLUG_RE = re.compile(r"^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$")
FOLDER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)-([A-Za-z0-9][A-Za-z0-9._-]{0,39})$"
)
SUBMITTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")
URL_RE = re.compile(r"^https?://\S+$")
FORBIDDEN_AUTHOR_CHARS = set('/\\:*?"<>|')

ERRORS: list[str] = []
WARNINGS: list[str] = []


def _emit(kind: str, message: str, path: Path | None = None) -> None:
    message = " ".join(str(message).split())
    if os.environ.get("GITHUB_ACTIONS") == "true":
        if path is not None:
            rel = _rel(path)
            line = f"::{kind} file={rel}::{message}"
        else:
            line = f"::{kind}::{message}"
    else:
        line = f"{_rel(path)}: {message}" if path is not None else message
    (ERRORS if kind == "error" else WARNINGS).append(line)


def err(message: str, path: Path | None = None) -> None:
    _emit("error", message, path)


def warn(message: str, path: Path | None = None) -> None:
    _emit("warning", message, path)


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        err("文件不是 UTF-8 编码", path)
    except json.JSONDecodeError as exc:
        err(f"JSON 解析失败：第 {exc.lineno} 行第 {exc.colno} 列，{exc.msg}", path)
    return None


def load_schema() -> dict:
    data = load_json(SCHEMA_PATH)
    if not isinstance(data, dict):
        raise SystemExit("无法读取 .github/submission-schema.json")
    return data


def is_semver(value: str) -> bool:
    return bool(VERSION_RE.fullmatch(value))


def description_body(text: str) -> str:
    """复刻插件的描述清洗逻辑：去掉开头的【场景】【难度】【说明】标题行。"""
    lines = text.splitlines()
    while lines and (
        not lines[0].strip()
        or lines[0].strip().startswith(("【场景】", "【难度】", "【说明】"))
    ):
        lines.pop(0)
    return "\n".join(lines).strip()


def slugify_member(name: str) -> str:
    """把角色名转成目录/文件 Slug，兼容 “Yangyang: Xuanling” 这类带符号的名字。"""
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def team_slug(team: list[str]) -> str:
    return "_".join(slugify_member(member) for member in team)


def check_meta(meta: object, meta_path: Path, slug_dir: str, folder: str, schema: dict) -> dict | None:
    if not isinstance(meta, dict):
        err("meta.json 顶层必须是对象", meta_path)
        return None

    unknown = sorted(set(meta) - META_KEYS)
    if unknown:
        err(f"存在未知字段：{', '.join(unknown)}（拼写错误或多余字段都会被拒绝）", meta_path)
    missing = sorted(META_REQUIRED - set(meta))
    if missing:
        err(f"缺少必填字段：{', '.join(missing)}", meta_path)

    def text(key: str, lo: int, hi: int) -> str:
        value = meta.get(key)
        if not isinstance(value, str):
            err(f"{key} 必须是字符串", meta_path)
            return ""
        value = value.strip()
        if len(value) < lo or len(value) > hi:
            err(f"{key} 长度必须在 {lo}–{hi} 个字符之间（当前 {len(value)}）", meta_path)
        return value

    if meta.get("schemaVersion") != 1:
        err("schemaVersion 必须是 1", meta_path)

    name = text("name", 1, schema["limits"]["nameMax"])
    if any(ch in FORBIDDEN_AUTHOR_CHARS for ch in name):
        err('name 不能包含 / \\ : * ? " < > | 这些字符（会破坏下载文件名）', meta_path)
    author = text("author", 1, schema["limits"]["authorMax"])
    if any(ch in FORBIDDEN_AUTHOR_CHARS for ch in author):
        err('author 不能包含 / \\ : * ? " < > | 这些字符', meta_path)

    version = text("version", 5, 14)
    if version and not is_semver(version):
        err("version 必须是 X.Y.Z 形式的语义化版本，例如 1.0.0", meta_path)
    if version and not folder.startswith(version + "-"):
        err(f"目录名必须以版本号开头：{version}-<你的用户名>（当前 {folder}）", meta_path)

    team = meta.get("team")
    if not isinstance(team, list) or not all(isinstance(item, str) for item in team):
        err("team 必须是角色英文名数组，例如 [\"Buling\", \"Hsin\", \"Rover\"]", meta_path)
        team = []
    else:
        team = [item.strip() for item in team]
        if not (schema["limits"]["teamMin"] <= len(team) <= schema["limits"]["teamMax"]):
            err(f"team 必须是 {schema['limits']['teamMin']}–{schema['limits']['teamMax']} 名角色", meta_path)
        if len(set(team)) != len(team):
            err("team 中有重复角色", meta_path)
        roles = set(schema["roles"])
        lower_roles = {role.lower(): role for role in schema["roles"]}
        for member in team:
            if member in roles:
                continue
            hint = f"，正确写法是 {lower_roles[member.lower()]}" if member.lower() in lower_roles else ""
            err(f"角色 {member!r} 不在白名单{hint}；新角色请先开 Issue 由维护者加入", meta_path)

    expected_slug = team_slug(team)
    if expected_slug and slug_dir != expected_slug:
        err(f"目录 Slug 应为 {expected_slug}（按 team 顺序用下划线连接），当前是 {slug_dir}", meta_path)
    if not SLUG_RE.fullmatch(slug_dir):
        err("Slug 只能包含英文字母、数字和下划线", meta_path)

    scenes = meta.get("scenes")
    if not isinstance(scenes, list) or not scenes or not all(isinstance(item, str) for item in scenes):
        err("scenes 必须是非空字符串数组", meta_path)
    else:
        if len(set(scenes)) != len(scenes):
            err("scenes 中有重复项", meta_path)
        invalid = [item for item in scenes if item not in schema["scenes"]]
        if invalid:
            err(f"scenes 含未定义场景：{', '.join(invalid)}；可选值：{', '.join(schema['scenes'])}", meta_path)

    difficulty = meta.get("difficulty")
    if difficulty not in schema["difficulties"]:
        err(f"difficulty 必须是：{', '.join(schema['difficulties'])}", meta_path)

    description = text("description", schema["limits"]["descriptionMin"], schema["limits"]["descriptionMax"])
    if description and "【说明】" not in description:
        warn("description 建议以【说明】开头，方便读者快速抓重点", meta_path)
    if description and len(description_body(description)) < 10:
        err(
            "description 在【说明】等标题行下面必须有至少 10 个字的正文；"
            "如果整段只有一行【说明】开头，插件会显示“作者未填写详细说明”",
            meta_path,
        )
    text("tested", schema["limits"]["testedMin"], schema["limits"]["testedMax"])

    video = meta.get("video", "")
    if video not in ("", None):
        if not isinstance(video, str) or not URL_RE.fullmatch(video):
            err("video 必须是 http(s) 链接，没有就留空字符串", meta_path)

    contact = meta.get("contact", "")
    if contact not in ("", None):
        if not isinstance(contact, str) or len(contact.strip()) > 80:
            err("contact 必须是不超过 80 字的字符串", meta_path)

    if meta.get("license") != schema["license"]:
        err(f"license 必须固定为 {schema['license']}（提交即表示同意以此协议分发）", meta_path)

    return {
        "name": meta.get("name", ""),
        "author": author,
        "version": version,
        "team": team,
        "scenes": scenes if isinstance(scenes, list) else [],
        "difficulty": difficulty,
        "file": meta_path,
    }


def check_zip(zip_path: Path, meta: dict, schema: dict) -> None:
    limits = schema["limits"]
    size = zip_path.stat().st_size
    if size > limits["zipMaxBytes"]:
        err(f"code.zip 不能超过 {limits['zipMaxBytes'] // 1024 // 1024} MB（当前 {size / 1024:.0f} KB）", zip_path)
        return

    try:
        with zipfile.ZipFile(zip_path) as zf:
            bad = zf.testzip()
            if bad:
                err(f"code.zip 内文件损坏：{bad}", zip_path)
                return
            infos = zf.infolist()
            if len(infos) > limits["zipMaxEntries"]:
                err(f"code.zip 内文件数不能超过 {limits['zipMaxEntries']}（当前 {len(infos)}）", zip_path)
            total = sum(info.file_size for info in infos)
            if total > limits["zipMaxUncompressedBytes"]:
                err(f"code.zip 解压后不能超过 {limits['zipMaxUncompressedBytes'] // 1024 // 1024} MB", zip_path)

            allowed = {ext.lower() for ext in limits["allowedExtensions"]}
            names: dict[str, str] = {}
            for info in infos:
                raw = info.filename
                if "\\" in raw:
                    err(f"zip 内路径不能使用反斜杠：{raw}", zip_path)
                normalized = raw[2:] if raw.startswith("./") else raw
                pure = PurePosixPath(normalized)
                if pure.is_absolute() or ".." in pure.parts:
                    err(f"zip 内存在越界路径：{raw}", zip_path)
                if "__MACOSX" in pure.parts or pure.name == ".DS_Store":
                    err(f"zip 内含系统垃圾文件：{raw}，请重新打包", zip_path)
                if any(part.startswith(".") for part in pure.parts):
                    err(f"zip 内不允许隐藏文件：{raw}", zip_path)
                if info.is_dir():
                    continue
                if normalized in names:
                    err(f"zip 内存在重复路径：{raw}", zip_path)
                names[normalized] = raw
                if pure.suffix.lower() not in allowed:
                    err(f"不允许的文件类型：{raw}（允许 {', '.join(sorted(allowed))}）", zip_path)
                if info.file_size > limits["zipMaxSingleFileBytes"]:
                    err(f"单个文件不能超过 {limits['zipMaxSingleFileBytes'] // 1024 // 1024} MB：{raw}", zip_path)
                if pure.suffix.lower() == ".py":
                    source = zf.read(info).decode("utf-8", errors="replace")
                    try:
                        compile(source, raw, "exec")
                    except (SyntaxError, ValueError) as exc:
                        warn(f"{raw} 无法通过本机 Python 语法检查（第 {exc.lineno} 行），请确认游戏内能正常运行", zip_path)
                    risky = [
                        token
                        for token in (
                            "os.system",
                            "subprocess",
                            "socket.",
                            "requests.",
                            "urllib.",
                            "eval(",
                            "exec(",
                            "base64.b64decode",
                            "shutil.rmtree",
                            "pickle.loads",
                        )
                        if token in source
                    ]
                    if risky:
                        warn(f"{raw} 含需人工复核的调用：{', '.join(risky)}", zip_path)

            if "team.json" not in names:
                err("code.zip 根目录缺少 team.json", zip_path)
                return
            try:
                inner = json.loads(zf.read(names["team.json"]).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                err(f"code.zip 内的 team.json 不是合法 UTF-8 JSON：{exc}", zip_path)
                return
            if not isinstance(inner, dict):
                err("code.zip 内的 team.json 顶层必须是对象", zip_path)
                return

            for key in ("name", "author", "version", "team"):
                if key not in inner:
                    err(f"code.zip 内的 team.json 缺少 {key}", zip_path)
            for key in ("name", "author", "version"):
                if str(inner.get(key, "")).strip() != str(meta.get(key, "")).strip():
                    err(
                        f"code.zip 内 team.json 的 {key} 与 meta.json 不一致："
                        f"{inner.get(key)!r} vs {meta.get(key)!r}",
                        zip_path,
                    )
            inner_team = inner.get("team")
            if isinstance(inner_team, str):
                inner_team = [part.strip() for part in re.split(r"[,，]", inner_team) if part.strip()]
            if inner_team != meta.get("team"):
                err(f"code.zip 内 team.json 的 team 与 meta.json 不一致：{inner_team!r} vs {meta.get('team')!r}", zip_path)
    except zipfile.BadZipFile:
        err("code.zip 不是合法的 zip 文件", zip_path)


def check_submission_dir(path: Path, schema: dict) -> dict | None:
    rel_parts = path.relative_to(SUBMISSIONS).parts
    if len(rel_parts) != 2:
        err(f"投稿目录必须是 submissions/<Slug>/<版本>-<用户名>（当前 {path.relative_to(ROOT)}）", path)
        return None
    slug_dir, folder = rel_parts
    if not SLUG_RE.fullmatch(slug_dir):
        err("Slug 目录只能包含英文字母、数字和下划线", path)
    if not FOLDER_RE.fullmatch(folder):
        err("版本目录必须形如 1.0.0-yourname（版本号 + 连字符 + 用户名）", path)

    expected = {"meta.json", "code.zip"}
    actual = {item.name for item in path.iterdir() if item.is_file()}
    dirs = [item for item in path.iterdir() if item.is_dir()]
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        err(f"投稿目录缺少文件：{', '.join(missing)}", path)
    if extra:
        err(f"投稿目录只能有 meta.json 和 code.zip，多出：{', '.join(extra)}", path)
    if dirs:
        err("投稿目录内不能有子目录", path)

    meta_path = path / "meta.json"
    if not meta_path.is_file():
        return None
    meta = load_json(meta_path)
    info = check_meta(meta, meta_path, slug_dir, folder, schema)
    zip_path = path / "code.zip"
    if info and zip_path.is_file():
        check_zip(zip_path, info, schema)
    return info


def load_existing_index() -> dict[tuple[str, str, str], str]:
    if not INDEX_PATH.is_file():
        warn("找不到 teams.json，跳过重复与版本检查")
        return {}
    data = load_json(INDEX_PATH)
    if not isinstance(data, dict):
        return {}
    existing: dict[tuple[str, str, str], str] = {}
    for team in data.get("teams", []):
        if not isinstance(team, dict):
            continue
        slug = team.get("slug", "")
        for code in team.get("codes", []):
            if not isinstance(code, dict):
                continue
            author = str(code.get("author", "")).strip()
            version = str(code.get("version", "")).strip()
            existing[(slug, author, version)] = code.get("filename", "")
    return existing


def check_duplicates(new_items: list[dict], existing: dict[tuple[str, str, str], str]) -> None:
    seen: dict[tuple[str, str, str], Path] = {}
    latest: dict[tuple[str, str], tuple[tuple[int, int, int], str]] = {}
    for slug, author, version in existing:
        if not is_semver(version):
            continue
        key = (slug, author)
        parsed = tuple(int(part) for part in version.split("."))
        if key not in latest or parsed > latest[key][0]:
            latest[key] = (parsed, version)

    for item in new_items:
        slug = team_slug(item["team"])
        author = item["author"]
        version = item["version"]
        if not is_semver(version):
            continue
        key = (slug, author, version)
        if key in existing:
            err(
                f"{slug} 已有 {author} 的 {version} 版本（{existing[key]}），"
                "请提升版本号后重新提交",
                item["file"],
            )
        if key in seen:
            err(f"同一 PR 里重复提交了 {slug} / {author} / {version}", item["file"])
        seen[key] = item["file"]
        prev = latest.get((slug, author))
        if prev and tuple(int(part) for part in version.split(".")) <= prev[0]:
            err(f"版本号必须大于已发布的最新版本 {prev[1]}（当前 {version}）", item["file"])


def changed_submission_dirs(base: str, head: str) -> list[Path] | None:
    try:
        merge_base = subprocess.check_output(
            ["git", "merge-base", base, head], text=True, stderr=subprocess.STDOUT
        ).strip()
        output = subprocess.check_output(
            ["git", "diff", "--name-status", f"{merge_base}...{head}"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        err(f"无法计算 PR 改动：{exc.stdout.strip() or exc}")
        return None

    dirs: set[Path] = set()
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        file_path = parts[-1].replace("\\", "/")
        if status.startswith("D"):
            err(f"不允许删除已提交的文件：{file_path}")
            continue
        if not status.startswith("A"):
            err(f"投稿 PR 只能新增文件，不能修改已有文件：{file_path}")
            continue
        if not file_path.startswith("submissions/"):
            err(f"投稿 PR 只能在 submissions/ 下新增文件，不能修改 {file_path}")
            continue
        pure = PurePosixPath(file_path)
        if len(pure.parts) == 4:
            dirs.add(ROOT / pure.parts[0] / pure.parts[1] / pure.parts[2])
    return sorted(dirs)


def main() -> int:
    parser = argparse.ArgumentParser(description="wwlibrary 投稿格式校验")
    parser.add_argument("--all", action="store_true", help="扫描 submissions/ 下全部投稿")
    parser.add_argument("--base", help="PR 的 base SHA")
    parser.add_argument("--head", help="PR 的 head SHA")
    args = parser.parse_args()

    # Windows 控制台默认 GBK，遇到 ✅/❌ 会直接抛 UnicodeEncodeError；
    # 统一改成不可编码字符用 ? 替代，保证本地自检也能正常跑完。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError):
            pass

    schema = load_schema()
    existing = load_existing_index()

    if args.all:
        dirs = []
        for path in sorted(SUBMISSIONS.glob("*/*")):
            if path.is_dir() and not path.parent.name.startswith("_"):
                dirs.append(path)
        if not dirs:
            print("submissions/ 下没有投稿")
            return 0
    else:
        if not args.base or not args.head:
            parser.error("请使用 --all，或同时提供 --base 和 --head")
        dirs = changed_submission_dirs(args.base, args.head)
        if dirs is None:
            return 1
        if not dirs and not ERRORS:
            print("没有投稿变更，跳过校验")
            return 0
        if len(dirs) > 1:
            err("一个 PR 只能提交一个代码包；多个队伍请分开提 PR")

    items = []
    for path in dirs:
        if not path.is_dir():
            err("投稿目录不存在（不允许删除投稿）", path)
            continue
        info = check_submission_dir(path, schema)
        if info:
            items.append(info)

    check_duplicates(items, existing)

    for line in WARNINGS:
        print(line)
    for line in ERRORS:
        print(line, file=sys.stderr)

    if ERRORS:
        print(f"\n❌ 校验失败：{len(ERRORS)} 个硬性错误，{len(WARNINGS)} 个提醒", file=sys.stderr)
        return 1
    print(f"\n✅ 校验通过：{len(items)} 个投稿，{len(WARNINGS)} 个提醒")
    return 0


if __name__ == "__main__":
    sys.exit(main())

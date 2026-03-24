#!/usr/bin/env python3
"""Create a release zip for InteractiveHtmlBom per user's steps.

Steps implemented:
1. Determine current git tag; require repo clean and HEAD tagged.
2. Verify LAST_TAG in InteractiveHtmlBom/version.py matches git tag.
3. Create releases/<tag> folder.
4. Create a tmp dir.
5. Copy `resources` folder into tmp dir.
6. Copy `InteractiveHtmlBom` into tmp/plugins,
   excluding __pycache__ and .ini files.
7. Set `versions[0].version` in `releases/metadata.json` to tag
   without leading 'v'.
8. Copy resulting metadata.json into tmp dir.
9. Zip tmp dir contents to `InteractiveHtmlBom_{version}_pcm.zip`
   inside releases/<tag>.
10.Zip plugin code into InteractiveHtmlBom.zip suitable for manual install.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()


def get_head_tag() -> str:
    tags = run(["git", "tag", "--points-at", "HEAD"]).splitlines()
    if not tags:
        raise SystemExit("ERROR: current commit is not tagged. Aborting.")
    return tags[0]


def repo_is_dirty() -> bool:
    status = run(["git", "status", "--porcelain"]).strip()
    return bool(status)


def read_last_tag_from_version_file(path: Path) -> str | None:
    text = path.read_text(encoding="utf8")
    m = re.search(r"LAST_TAG\s*=\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else None


def update_metadata_version(metadata_path: Path, version: str) -> None:
    data = json.loads(metadata_path.read_text(encoding="utf8"))
    if "versions" not in data or not isinstance(data["versions"], list) or not data["versions"]:
        raise SystemExit(f"ERROR: {metadata_path} has no versions[0] entry")
    data["versions"][0]["version"] = version
    metadata_path.write_text(json.dumps(
        data, indent=4, ensure_ascii=False), encoding="utf8")


def copy_interactive_html_bom(src: Path, dst: Path) -> None:
    # copytree with ignore patterns for __pycache__ directories and .ini files
    def _ignore(dir, names):
        ignored = set()
        for name in list(names):
            if name == "__pycache__" or name.endswith(".ini"):
                ignored.add(name)
        return ignored

    shutil.copytree(src, dst, ignore=_ignore)


def main() -> None:
    root = Path.cwd()

    # 1. Ensure repo clean and HEAD is tagged
    if repo_is_dirty():
        raise SystemExit(
            "ERROR: repository has uncommitted changes (dirty). Commit or stash before releasing.")

    tag = get_head_tag()
    print(f"Found tag: {tag}")

    # 2. Verify LAST_TAG in InteractiveHtmlBom/version.py
    version_file = root / "InteractiveHtmlBom" / "version.py"
    if not version_file.exists():
        raise SystemExit(f"ERROR: {version_file} not found")
    last_tag = read_last_tag_from_version_file(version_file)
    if last_tag is None:
        raise SystemExit(f"ERROR: LAST_TAG not found in {version_file}")
    if last_tag != tag:
        raise SystemExit(
            f"ERROR: LAST_TAG ({last_tag}) does not match git tag ({tag})")
    print("LAST_TAG matches git tag.")

    # 3. Create releases/<tag> folder
    releases_dir = root / "releases"
    version_dir = releases_dir / tag
    version_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created/verified release folder: {version_dir}")

    # 4-9 inside a temporary directory
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # 5. Copy resources folder from repo root into tmp dir
        resources_src = root / "releases" / "resources"
        if not resources_src.exists() or not resources_src.is_dir():
            raise SystemExit(
                f"ERROR: resources folder not found at {resources_src}")
        shutil.copytree(resources_src, tmp_path / "resources")
        print("Copied resources into tmp dir.")

        # 6. Copy InteractiveHtmlBom into tmp/plugins excluding patterns
        plugins_dir = tmp_path / "plugins"
        copy_interactive_html_bom(
            root / "InteractiveHtmlBom", plugins_dir)
        print("Copied InteractiveHtmlBom into tmp/plugins (excluded __pycache__ and .ini files)")

        # 7. Set versions[0].version inside releases/metadata.json to package version without leading 'v'
        metadata_path = releases_dir / "metadata.json"
        if not metadata_path.exists():
            raise SystemExit(f"ERROR: {metadata_path} not found")
        package_version = tag.lstrip("v")
        update_metadata_version(metadata_path, package_version)
        print(
            f"Updated {metadata_path} versions[0].version to {package_version}")

        # 8. Copy resulting metadata.json file into tmp dir
        shutil.copy2(metadata_path, tmp_path / "metadata.json")
        print("Copied metadata.json into tmp dir.")

        # 9. Zip tmp dir contents into InteractiveHtmlBom-{version}-pcm.zip into the version folder
        zip_name = f"InteractiveHtmlBom_{tag}_pcm"
        archive_path = shutil.make_archive(
            str(version_dir / zip_name), 'zip', root_dir=tmp_path)
        print(f"Created archive: {archive_path}")

        # 10. Create "normal" zip of just plugin code
        shutil.move(plugins_dir, tmp_path / "InteractiveHtmlBom")
        zip_name = f"InteractiveHtmlBom"
        archive_path = shutil.make_archive(
            str(version_dir / zip_name), 'zip', root_dir=tmp_path, base_dir="InteractiveHtmlBom")
        print(f"Created archive: {archive_path}")

    print("Release package created successfully.")


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("ERROR: git command failed:\n", e.output, file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

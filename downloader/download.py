import io
import os
import subprocess
import tarfile
from pathlib import Path
from typing import cast

import brotli  # pyright: ignore[reportMissingTypeStubs]
import httpx
from githubkit import GitHub
from githubkit.exception import RequestFailed as GitHubRequestFailed
from githubkit.versions.v2022_11_28.models import Release

from downloader.raw_data import GitHubRepo, GitRepo


def clone_git_repo(repo: GitRepo, cloned_repo_path: Path) -> None:
    print(f"Cloning `{repo.uri}` to `{cloned_repo_path}`...")
    _ = subprocess.run(
        ["git", "clone", "--depth=1", repo.uri, str(cloned_repo_path)],
        check=True,
        capture_output=True,
    )


def download_package_tar_br(url: str, cloned_repo_path: Path) -> None:
    print(f"Downloading `{url}`...")
    response = httpx.get(url, follow_redirects=True)
    _ = response.raise_for_status()
    package_compressed = response.content
    package_decompressed = cast(bytes, brotli.decompress(package_compressed))  # pyright: ignore[reportUnknownMemberType]
    with tarfile.open(fileobj=io.BytesIO(package_decompressed), mode="r:") as tar:
        tar.extractall(cloned_repo_path, filter="data")


def get_latest_release(repo: GitHubRepo) -> Release:
    github = GitHub(os.getenv("GITHUB_TOKEN"))
    try:
        return github.rest.repos.get_latest_release(repo.owner, repo.repo).parsed_data
    except GitHubRequestFailed:
        all_releases = github.rest.repos.list_releases(
            repo.owner, repo.repo
        ).parsed_data
        return sorted(all_releases, key=lambda r: r.created_at, reverse=True)[0]


def get_download_url(repo: GitHubRepo) -> str:
    latest_release = get_latest_release(repo)
    asset = latest_release.assets[0]
    return asset.browser_download_url

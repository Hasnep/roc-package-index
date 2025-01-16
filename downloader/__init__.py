import json
import subprocess
from datetime import timedelta as TimeDelta
from pathlib import Path

import msgspec
from msgspec import Struct

from downloader.documentation import Module, get_package_documentation
from downloader.download import (
    clone_git_repo,
    download_package_tar_br,
    get_download_url,
)
from downloader.raw_data import (
    GitHubRepo,
    GitRepo,
    RawPackageData,
    UrlDownload,
    get_raw_packages_data,
)
from downloader.utils import get_temp_dir


class Package(Struct, kw_only=True, frozen=True, forbid_unknown_fields=True):
    package_id: str
    modules: list[Module] | None
    download_url: str | None
    source_code_url: str | None
    homepage_url: str | None
    documentation_url: str | None


def run_roc_test(entrypoint: Path) -> bool:
    print("Running tests...")
    if not entrypoint.exists():
        raise FileExistsError(f"Entrypoint `{entrypoint}` not found.")
    try:
        _ = subprocess.run(
            ["roc", "test", str(entrypoint.absolute())],
            timeout=TimeDelta(minutes=3).total_seconds(),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print("Tests failed!")
        return False
    except subprocess.TimeoutExpired:
        print("Tests timed out!")
        return False
    else:
        print("Tests passed.")
        return True


def process_package(package_id: str, package_data: RawPackageData) -> Package:
    print(f"Processing `{package_id}`.")
    with get_temp_dir() as package_dir:
        match package_data.source_code:
            case GitRepo() as git_repo:
                clone_git_repo(git_repo, package_dir)
                entrypoint = package_dir / git_repo.entrypoint
                download_url = None
                source_code_url = None

            case GitHubRepo() as github_repo:
                download_url = get_download_url(github_repo)
                download_package_tar_br(download_url, package_dir)
                entrypoint = package_dir / "main.roc"
                source_code_url = (
                    f"https://github.com/{github_repo.owner}/{github_repo.repo}"
                )

            case UrlDownload() as url_download:
                download_url = url_download.url
                download_package_tar_br(download_url, package_dir)
                entrypoint = package_dir / "main.roc"
                source_code_url = None

        # _passed_tests = run_roc_test(entrypoint)
        modules = get_package_documentation(entrypoint)
        return Package(
            package_id=package_id,
            modules=modules,
            download_url=download_url,
            homepage_url=package_data.homepage,
            documentation_url=package_data.documentation,
            source_code_url=source_code_url,
        )


def main() -> None:
    raw_packages_data = get_raw_packages_data()
    for package_id, raw_package_data in raw_packages_data.packages.items():
        print(package_id)
        package_data = process_package(package_id, raw_package_data)
        # Write package data to file
        package_data_path = Path() / "data" / "packages" / (package_id + ".json")
        package_data_path.parent.mkdir(exist_ok=True)
        with package_data_path.open("w") as package_data_file:
            _ = package_data_file.write(
                json.dumps(
                    json.loads(msgspec.json.encode(package_data, order="sorted")),
                    indent=2,
                )
                + "\n"
            )

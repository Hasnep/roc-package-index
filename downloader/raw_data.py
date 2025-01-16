import json
from pathlib import Path

import msgspec
from msgspec import Struct


class GitHubRepo(
    Struct, kw_only=True, forbid_unknown_fields=True, frozen=True, tag="github"
):
    owner: str
    repo: str


class GitRepo(Struct, kw_only=True, forbid_unknown_fields=True, frozen=True, tag="git"):
    uri: str
    entrypoint: str


class UrlDownload(
    Struct, kw_only=True, forbid_unknown_fields=True, frozen=True, tag="url"
):
    url: str


class RawPackageData(Struct, kw_only=True, forbid_unknown_fields=True, frozen=True):
    source_code: GitRepo | GitHubRepo | UrlDownload
    documentation: str | None = None
    homepage: str | None = None


class RawPackagesData(Struct, kw_only=True, forbid_unknown_fields=True, frozen=True):
    packages: dict[str, RawPackageData]


def get_raw_packages_data() -> RawPackagesData:
    packages_raw_data_file = Path() / "data" / "packages.json"
    with packages_raw_data_file.open("rb") as f:
        packages_raw_data = msgspec.json.decode(f.read(), type=RawPackagesData)

    with packages_raw_data_file.open("w") as f:
        _ = f.write(
            json.dumps(
                json.loads(msgspec.json.encode(packages_raw_data, order="sorted")),
                indent=2,
            )
            + "\n"
        )

    return packages_raw_data

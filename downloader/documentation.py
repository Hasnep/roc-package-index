import re
import string
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import final

from msgspec import Struct

from downloader.utils import get_temp_dir


@final
class ParseError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg
        super().__init__(self.msg)


def skip_literal_line(s: str, lines: list[str]) -> list[str]:
    line, *remaining_lines = lines
    if line == s:
        return remaining_lines
    else:
        raise ParseError(f"Expected line `{line}` to be `{s}`.")


def skip_blank_line(lines: list[str]) -> list[str]:
    return skip_literal_line("", lines)


class Value(
    Struct,
    kw_only=True,
    frozen=True,
    forbid_unknown_fields=True,
    tag_field="is_a",
    tag="value",
):
    name: str
    description: str | None
    type_annotation: str | None = None


class Type(
    Struct,
    kw_only=True,
    frozen=True,
    forbid_unknown_fields=True,
    tag_field="is_a",
    tag="type",
):
    name: str
    description: str | None
    type_annotation: str | None = None


type Definition = Type | Value


def _clean_up_type_annotation(type_annotation: str) -> str:
    return re.sub(r"\s+", " ", type_annotation.strip())


def parse_definition(lines: list[str]) -> tuple[Definition, list[str]]:
    # Name
    name_line, *remaining_lines = lines
    name = name_line.removeprefix("#### ")
    remaining_lines = skip_blank_line(remaining_lines)
    # Type annotation
    remaining_lines = skip_literal_line("**Type Annotation**", remaining_lines)
    remaining_lines = skip_blank_line(remaining_lines)
    # Check if there is actually a type annotation here
    try:
        next_line = remaining_lines[0]
    except IndexError:
        next_line = ""
    if next_line == "```roc":
        remaining_lines = skip_literal_line("```roc", remaining_lines)
        type_annotation_lines: list[str] = []
        while True:
            next_line = remaining_lines[0]
            if next_line == "```":
                break
            else:
                type_annotation_line, *remaining_lines = remaining_lines
                type_annotation_lines = [
                    *type_annotation_lines,
                    type_annotation_line,
                ]
        type_annotation = _clean_up_type_annotation("\n".join(type_annotation_lines))
        remaining_lines = skip_literal_line("```", remaining_lines)
        remaining_lines = skip_blank_line(remaining_lines)
    else:
        type_annotation = None
    # Description
    try:
        next_line = remaining_lines[0]
    except IndexError:
        next_line = ""
    if next_line == "**Description**":
        remaining_lines = skip_literal_line("**Description**", remaining_lines)
        remaining_lines = skip_blank_line(remaining_lines)
        description_lines: list[str] = []
        while True:
            try:
                next_line = remaining_lines[0]
                next_next_line = remaining_lines[1]
            except IndexError:
                break
            if next_line == "" and next_next_line.startswith(("#### ", "### ")):
                remaining_lines = skip_blank_line(remaining_lines)
                break
            else:
                description_line, *remaining_lines = remaining_lines
                description_lines = [*description_lines, description_line]
        description = "\n".join(description_lines)
    else:
        description = None

    # Type or value
    if name[0] in string.ascii_lowercase:
        return Value(
            name=name, description=description, type_annotation=type_annotation
        ), remaining_lines
    else:
        return Type(
            name=name, description=description, type_annotation=type_annotation
        ), remaining_lines


class Module(Struct, kw_only=True, frozen=True, forbid_unknown_fields=True):
    name: str
    definitions: Sequence[Definition]


def parse_module(lines: list[str]) -> tuple[Module, list[str]]:
    name_line, *remaining_lines = lines
    name = name_line.removeprefix("### ")
    remaining_lines = skip_blank_line(remaining_lines)
    definitions: list[Definition] = []
    while len(remaining_lines) > 0:
        next_line = remaining_lines[0]
        if next_line == "":
            remaining_lines = skip_blank_line(remaining_lines)
        elif next_line.startswith("### "):
            return Module(name=name, definitions=definitions), remaining_lines
        elif next_line.startswith("#### "):
            definition, remaining_lines = parse_definition(remaining_lines)
            definitions = [*definitions, definition]
        else:
            raise ParseError(
                f"Expected next line `{next_line}` to start with `### ` or `#### `."
            )
    return Module(name=name, definitions=definitions), remaining_lines


def parse_llms_dot_txt(llms_dot_txt: str) -> list[Module]:
    remaining_lines = llms_dot_txt.splitlines()

    # Heading
    remaining_lines = skip_literal_line(
        "# LLM Prompt for Documentation", remaining_lines
    )
    remaining_lines = skip_blank_line(remaining_lines)
    remaining_lines = skip_literal_line("## Documentation", remaining_lines)
    remaining_lines = skip_blank_line(remaining_lines)

    # Modules
    modules: list[Module] = []
    while len(remaining_lines) > 0:
        next_line = remaining_lines[0]
        if next_line.startswith("### "):
            module, remaining_lines = parse_module(remaining_lines)
            modules = [*modules, module]
        else:
            raise ParseError("Expected line `{line}` to start with `### `.")
    return modules


def get_package_documentation(entrypoint: Path) -> list[Module] | None:
    with get_temp_dir() as docs_dir:
        print(f"Generating docs in `{docs_dir}`...")
        if not entrypoint.exists():
            raise FileExistsError(f"Entrypoint `{entrypoint}` not found.")
        try:
            _ = subprocess.run(
                ["roc", "docs", f"--output={docs_dir}", str(entrypoint.absolute())],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            return None
        llms_dot_txt_file_path = docs_dir / "llms.txt"
        print(f"Parsing `{llms_dot_txt_file_path}`...")
        with llms_dot_txt_file_path.open("r") as llms_dot_txt_file:
            llms_dot_txt = llms_dot_txt_file.read()
    return parse_llms_dot_txt(llms_dot_txt)

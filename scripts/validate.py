#!/usr/bin/env python3
"""Check completed starter documents; no dependencies beyond Python 3.10+.

Metadata uses the documented one-line subset, not a general YAML parser.
Links check local file existence, not URL availability or heading anchors.
Run ``task`` metadata may contain comma-separated Task IDs.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOP_DIRS = {"wiki", "tasks", "runs", "scripts"}
TASK_KEYS = ("id", "type", "status", "priority", "trigger", "required_capabilities")
RUN_KEYS = ("run_id", "task", "executor")
LIFECYCLE_TYPES = {"standing", "temporary", "focused", "conditional"}
EMPTY_VALUES = {"", "null", "~", "[]", "{}"}
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
RESERVED_TASK_REFS = {"direct-request"}
FM_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|$)", re.S)
DEST = r"""(?:<[^>\n]*>|(?:[^\s()]+|\([^()\n]*\))+)"""
TITLE = r"""(?:\s+(?:"[^"\n]*"|'[^'\n]*'|\([^()\n]*\)))?"""
INLINE_RE = re.compile(r"\[[^\]\n]+\]\(\s*(" + DEST + r")" + TITLE + r"\s*\)")
DEFINITION_RE = re.compile(
    r"^ {0,3}\[([^\]\n]+)\]:\s*(" + DEST + r")" + TITLE + r"\s*$", re.M
)
REFERENCE_RE = re.compile(r"\[([^\]\n]+)\]\[([^\]\n]*)\]")
SHORTCUT_RE = re.compile(r"\[([^\]\n]+)\]")


def scalar(value: str) -> str:
    value = value.strip()
    if not value.startswith(("\"", "'")):
        value = value.split(" #", 1)[0].strip()
        if value.startswith("#"):
            value = ""
    if value.startswith(("\"", "'")):
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError("unclosed quoted value")
        value = value[1:-1].strip()
    elif any(mark in value for mark in ("[", "]", "{", "}")) or value.startswith(("|", ">", "&", "*", "!")):
        raise ValueError("use a one-line string; put structured details in the body")
    if value.lower() in EMPTY_VALUES:
        raise ValueError("empty value")
    return value


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FM_RE.match(text)
    if not match:
        if text.startswith("---"):
            raise ValueError("front matter must end with --- on its own line")
        return {}
    out = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator or not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise ValueError("metadata must use one key: value per line")
        if key in out:
            raise ValueError(f"duplicate metadata key {key}")
        value = value.strip()
        if key == "required_capabilities":
            if not re.fullmatch(r"\[\s*[A-Za-z0-9][A-Za-z0-9_-]*(?:\s*,\s*[A-Za-z0-9][A-Za-z0-9_-]*)*\s*\]", value):
                raise ValueError("required_capabilities must be a non-empty list of capability names")
            out[key] = value
        else:
            try:
                out[key] = scalar(value)
            except ValueError as exc:
                raise ValueError(f"{key}: {exc}") from exc
    return out


def parse_run_task_refs(value: str) -> list[str]:
    """Parse the intentionally simple comma-separated Run task field."""
    refs = [item.strip() for item in value.split(",")]
    if not refs or any(not item for item in refs):
        raise ValueError("task must contain non-empty comma-separated Task IDs")
    for item in refs:
        if not TOKEN_RE.fullmatch(item):
            raise ValueError(
                "task entries must use letters, digits, hyphens or underscores; "
                "separate multiple entries with commas"
            )
    return refs


def prose_only(text: str) -> str:
    """Ignore fenced examples, comments and inline code when checking links."""
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line):
                fence = None
            continue
        if marker:
            fence = marker.group(1)
            continue
        lines.append(line)
    prose = re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.S)

    def inline_code(match: re.Match) -> str:
        if prose[match.start() - 1:match.start()] == "[" and prose[match.end():match.end() + 1] == "]":
            return match.group(2)
        return ""

    return re.sub(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", inline_code, prose, flags=re.S)


def link_targets(text: str) -> tuple[list[str], list[str]]:
    prose = prose_only(text)
    normalize = lambda label: " ".join(label.lower().split())
    definitions = {normalize(label): target for label, target in DEFINITION_RE.findall(prose)}
    targets = list(definitions.values())
    prose = DEFINITION_RE.sub("", prose)
    targets.extend(INLINE_RE.findall(prose))
    prose = INLINE_RE.sub("", prose)
    missing = []
    for label, reference in REFERENCE_RE.findall(prose):
        name = normalize(reference or label)
        if name not in definitions:
            missing.append(name)
    prose = REFERENCE_RE.sub("", prose)
    for label in SHORTCUT_RE.findall(prose):
        name = normalize(label)
        if name in definitions:
            targets.append(definitions[name])
    return targets, missing


def validate(root: Path) -> tuple[list[str], dict[str, int]]:
    root = root.resolve()
    errors = []
    counts = {"tasks": 0, "runs": 0, "ids": 0}
    ids: dict[str, Path] = {}
    task_ids = set()
    run_tasks = []
    for directory in sorted(ALLOWED_TOP_DIRS):
        if not (root / directory).is_dir():
            errors.append(f"missing directory: {directory}")
    if not root.is_dir():
        return errors, counts
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name not in ALLOWED_TOP_DIRS | {".git"}:
            errors.append(f"unexpected top-level directory: {child.name}; update the documented layout and validator if intentional")
    documents = []
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = [name for name in subdirs if name != ".git"]
        documents.extend(Path(directory) / name for name in files if name.endswith(".md"))
    for md in sorted(documents):
        relative = md.relative_to(root)
        label = str(relative)
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{label}: cannot read document: {exc}")
            continue
        targets, missing = link_targets(text)
        for name in missing:
            errors.append(f"{label}: undefined link reference: {name}")
        for target in targets:
            target = target.removeprefix("<").removesuffix(">")
            try:
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                resolved = (md.parent / unquote(url.path)).resolve()
                if not resolved.exists():
                    errors.append(f"{label}: broken link: {target}")
            except (ValueError, OSError) as exc:
                errors.append(f"{label}: invalid link {target}: {exc}")
        if md.name == "_TEMPLATE.md":
            continue
        try:
            fm = parse_frontmatter(text)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue
        section = relative.parts[0]
        is_task = section == "tasks" and md.name not in {"README.md", "proposals.md"}
        is_run = section == "runs" and md.name != "README.md"
        required = TASK_KEYS if is_task else RUN_KEYS if is_run else ()
        for key in required:
            if key not in fm:
                errors.append(f"{label}: required metadata missing: {key}")
        if is_task:
            counts["tasks"] += 1
            if fm.get("priority") not in {f"P{i}" for i in range(5)}:
                errors.append(f"{label}: priority must be P0 through P4")
            if fm.get("type") in LIFECYCLE_TYPES:
                errors.append(f"{label}: type must describe the work; put lifecycle in the body")
            if fm.get("id"):
                if fm["id"] in RESERVED_TASK_REFS:
                    errors.append(f"{label}: reserved Task ID: {fm['id']}")
                else:
                    task_ids.add(fm["id"])
        if is_run:
            counts["runs"] += 1
            if fm.get("task"):
                try:
                    refs = parse_run_task_refs(fm["task"])
                except ValueError as exc:
                    errors.append(f"{label}: task: {exc}")
                else:
                    run_tasks.extend((label, ref) for ref in refs)
        for key in ("id", "run_id"):
            if key not in fm:
                continue
            ident = fm[key]
            if not TOKEN_RE.fullmatch(ident):
                errors.append(f"{label}: {key} must be an ID using letters, digits, hyphens or underscores")
            if ident in ids:
                errors.append(f"{label}: duplicate id {ident}: {ids[ident].relative_to(root)}")
            ids[ident] = md
    for label, task in run_tasks:
        if task not in RESERVED_TASK_REFS and task not in task_ids:
            errors.append(f"{label}: unknown task ID: {task}")
    if (root / "registry.json").exists():
        errors.append("registry.json is outside the starter layout; update the validator and move duplicated allocation metadata when introducing it")
    counts["ids"] = len(ids)
    return errors, counts


def main() -> int:
    errors, counts = validate(ROOT)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALIDATION OK: {counts['tasks']} tasks; {counts['runs']} runs; {counts['ids']} unique IDs (templates excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

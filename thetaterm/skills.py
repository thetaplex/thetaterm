"""Load and route HKUDS/Upskill-format SKILL.md files for thetaterm.

Stdlib-only so thetaterm keeps zero extra runtime dependencies.
Skills live in:
  1. Shipped package store: thetaterm/skills/**/SKILL.md
  2. User config store:     ~/.config/thetaterm/skills/**/SKILL.md
  3. Explicit override:     THETATERM_SKILLS_DIR or Agent(skills_dir=...)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

MAX_SKILLS = 2
MAX_SKILLS_CHARS = 1800

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
_TOKEN = re.compile(r"[a-z0-9][a-z0-9._+-]*")


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    category: str
    base_model: str
    trigger_keywords: tuple[str, ...]
    programs: tuple[str, ...]
    body: str
    source: str = ""


def _parse_list(raw: str) -> tuple[str, ...]:
    """Parse an inline YAML list like `[a, b, "c d"]`."""
    inner = raw.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    items = []
    for part in inner.split(","):
        cleaned = part.strip().strip("\"'").lower()
        if cleaned:
            items.append(cleaned)
    return tuple(items)


def _strip_quotes(raw: str) -> str:
    return raw.strip().strip("\"'")


def parse_skill(text: str, fallback_name: str = "skill", source: str = "") -> Skill:
    """Parse a SKILL.md file (YAML frontmatter + Markdown body) without PyYAML."""
    meta: dict[str, str] = {}
    body = text.strip()
    match = _FRONTMATTER.match(text)
    if match:
        frontmatter, body = match.group(1), match.group(2).strip()
        for line in frontmatter.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if value:
                meta[key] = value

    return Skill(
        name=_strip_quotes(meta.get("name", fallback_name)) or fallback_name,
        description=_strip_quotes(meta.get("description", "")),
        category=_strip_quotes(meta.get("category", "general")),
        base_model=_strip_quotes(meta.get("base_model", "")),
        trigger_keywords=_parse_list(meta.get("trigger_keywords", "")),
        programs=_parse_list(meta.get("programs", "")),
        body=body,
        source=source,
    )


def user_skills_dir() -> Path:
    return (
        Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")
        / "thetaterm"
        / "skills"
    )


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("SKILL.md") if p.is_file())


def load_skills(skills_dir: str | os.PathLike[str] | None = None) -> list[Skill]:
    """Load skills from shipped + user dirs, or exclusively from skills_dir if given."""
    by_name: dict[str, Skill] = {}

    if skills_dir is not None:
        roots = [Path(skills_dir)]
    else:
        env_dir = os.getenv("THETATERM_SKILLS_DIR")
        roots = []
        shipped = files("thetaterm") / "skills"
        if shipped.is_dir():
            roots.append(Path(str(shipped)))
        roots.append(user_skills_dir())
        if env_dir:
            roots.append(Path(env_dir))

    for root in roots:
        for path in _iter_skill_files(root):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            skill = parse_skill(text, fallback_name=path.parent.name, source=str(path))
            if skill.body:
                by_name[skill.name] = skill

    return list(by_name.values())


def _query_tokens(query: str) -> set[str]:
    raw = _TOKEN.findall(query.lower())
    out = set(raw)
    for w in raw:
        if len(w) > 3 and w.endswith("s"):
            out.add(w[:-1])
    return out


def match_skills(
    query: str,
    programs: list[str],
    skills: list[Skill],
    max_skills: int = MAX_SKILLS,
) -> list[Skill]:
    """Rank skills by chosen program overlap and trigger keyword matches."""
    if not skills or max_skills <= 0:
        return []
    q_lower = query.lower()
    q_tokens = _query_tokens(query)
    prog_set = {p.lower() for p in programs}

    scored: list[tuple[float, str, Skill]] = []
    for skill in skills:
        kw_score = 0.0
        for kw in skill.trigger_keywords:
            if " " in kw or "." in kw:
                if kw in q_lower:
                    kw_score += 2.0
            else:
                stem = kw[:-1] if len(kw) > 3 and kw.endswith("s") else kw
                if kw in q_tokens or stem in q_tokens:
                    kw_score += 2.0
        # A skill with trigger_keywords must match at least one keyword so broad
        # umbrella programs like `git` don't inject unrelated skills on every query.
        if skill.trigger_keywords and kw_score == 0.0:
            continue
        prog_score = sum(3.0 for prog in skill.programs if prog in prog_set)
        score = kw_score + prog_score
        if score > 0 and skill.description:
            desc_tokens = _query_tokens(skill.description)
            score += 0.25 * len(desc_tokens & q_tokens)
        if score > 0:
            scored.append((score, skill.name, skill))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [skill for _, _, skill in scored[:max_skills]]


def format_skills(
    query: str,
    programs: list[str],
    skills_dir: str | os.PathLike[str] | None = None,
    max_skills: int = MAX_SKILLS,
    budget: int = MAX_SKILLS_CHARS,
) -> str:
    """Return formatted matching SKILL.md blocks within the character budget."""
    matched = match_skills(
        query, programs, load_skills(skills_dir), max_skills=max_skills
    )
    if not matched:
        return ""

    blocks: list[str] = []
    used = 0
    for skill in matched:
        header = f"## Skill: {skill.name}"
        if skill.description:
            header += f" — {skill.description}"
        block = f"{header}\n{skill.body}".strip()
        remaining = budget - used - (2 if blocks else 0)
        if remaining <= 80:
            break
        if len(block) > remaining:
            block = block[: remaining - 1].rstrip() + "…"
        blocks.append(block)
        used += len(block) + (2 if len(blocks) > 1 else 0)
    return "\n\n".join(blocks)

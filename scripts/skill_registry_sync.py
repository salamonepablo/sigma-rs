"""Synchronize .atl/skill-registry.md from .agent/skills/SKILLS.md."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_INDEX = ROOT / ".agent" / "skills" / "SKILLS.md"
REGISTRY_PATH = ROOT / ".atl" / "skill-registry.md"


def _parse_skills_table(lines: list[str]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped.startswith("|---"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 3:
            continue
        if parts[0].lower() == "skill":
            continue
        skill, trigger, path = parts[0], parts[1], parts[2]
        rows.append((trigger, skill, path))
    return rows


def _render_registry(rows: list[tuple[str, str, str]]) -> str:
    lines = [
        "# Sigma-RS Skill Registry",
        "",
        "This file is generated for sub-agents. Orchestrators should resolve paths here",
        "and pass the exact SKILL.md path to sub-agents.",
        "",
        "## Project conventions",
        "",
        "- AGENTS: `AGENTS.md`",
        "- Orchestrator: `AGENT.md`",
        "- Claude bridge: `CLAUDE.md`",
        "- Skills index: `.agent/skills/SKILLS.md`",
        "",
        "## Skills",
        "",
        "| Trigger | Skill | Path |",
        "|---|---|---|",
    ]
    for trigger, skill, path in rows:
        lines.append(f"| {trigger} | {skill} | {path} |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Update this file when new skills are added or removed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    if not SKILLS_INDEX.exists():
        raise SystemExit(f"Missing skills index: {SKILLS_INDEX}")

    rows = _parse_skills_table(SKILLS_INDEX.read_text(encoding="utf-8").splitlines())
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(_render_registry(rows), encoding="utf-8")


if __name__ == "__main__":
    main()

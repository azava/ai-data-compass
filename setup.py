"""Build the distributable asset tree from the skill catalog and repository."""

import json
from collections import defaultdict
from pathlib import Path

from setuptools import setup


ROOT = Path(__file__).parent
CATALOG = ROOT / "src" / "ai_data_compass" / "skill_catalog.json"
ASSET_ROOT = Path("share") / "ai-data-compass" / "assets"


def data_file_groups():
    """Map bundled files to their installed relative directories."""

    sources = [
        *sorted((ROOT / ".ai-data-compass" / "docs").glob("*.md")),
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "GEMINI.md",
        ROOT / ".windsurfrules",
        ROOT / ".ai-data-compass" / "LICENSE",
        ROOT / ".ai-data-compass" / "THIRD-PARTY-NOTICES.md",
        ROOT / ".github" / "copilot-instructions.md",
        ROOT / ".cursor" / "rules" / "agents.mdc",
    ]
    for skill in json.loads(CATALOG.read_text(encoding="utf-8")):
        directory = skill["directory"]
        sources.extend(
            path
            for path in (ROOT / ".ai-data-compass" / "skills" / directory).rglob("*")
            if path.is_file()
        )
        for projection in (".agents/skills", ".claude/skills"):
            projected_skill = ROOT / projection / directory / "SKILL.md"
            if projected_skill.is_file():
                sources.append(projected_skill)

    grouped = defaultdict(list)
    for source in sources:
        relative = source.relative_to(ROOT)
        grouped[ASSET_ROOT / relative.parent].append(relative.as_posix())
    return [(destination.as_posix(), sorted(files)) for destination, files in sorted(grouped.items())]


setup(data_files=data_file_groups())

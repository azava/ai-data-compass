# AI Agent Skills

## Canonical source

Repository skills are maintained under `.agents/skills/<skill-name>/`.
The canonical `SKILL.md`, references, scripts, and tests in that directory are
the source of truth for supported coding agents.

## Claude Code projection

Claude Code discovers project skills under
`.claude/skills/<skill-name>/SKILL.md`. Each Claude adapter is a small,
versioned entry point that loads and follows the canonical skill under
`.agents/skills/`.

Adapters must not duplicate the canonical workflow or maintain separate
scanner logic. They may contain only host-specific discovery and safety
guidance required to reach the canonical skill.

## Adding or changing a skill

1. Add or update the canonical skill under `.agents/skills/`.
2. Add a Claude adapter under `.claude/skills/` when Claude Code support is in scope.
3. Keep all skill instructions, comments, and documentation in English.
4. Add deterministic tests using synthetic fixtures only.
5. Run the canonical tests and projection tests before committing.

## Security contract

Skills are trusted repository instructions and must be reviewed like executable
code. Security-sensitive skills must use local, deterministic tools where
possible, avoid external network calls unless explicitly required, and never
expose secret or personally identifiable values in output.

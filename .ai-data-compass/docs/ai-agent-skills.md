# AI Agent Skills

This document contains additional skill architecture and security details for
the rules in `AGENTS.md`.

## Canonical source

Repository skills are maintained under
`.ai-data-compass/skills/<skill-name>/`. The canonical `SKILL.md`, references,
scripts, and tests in that directory are the source of truth.

## Codex discovery adapter

Codex discovers repository skills under
`.agents/skills/<skill-name>/SKILL.md`. The distribution installs a small
discovery adapter there that points to the canonical skill under
`.ai-data-compass/skills/`.

The adapter must not duplicate the canonical workflow, scripts, references, or
security logic.

## Claude Code projection

Claude Code discovers project skills under
`.claude/skills/<skill-name>/SKILL.md`. The distribution installs each Claude
adapter as a small, versioned entry point to the canonical skill. Adapters
must not duplicate the canonical workflow or scanner logic.

## Adding or changing a skill

1. Add or update the canonical skill under `.ai-data-compass/skills/`.
2. Regenerate the discovery adapters for supported hosts.
3. Keep skill instructions, comments, and documentation in English.
4. Add deterministic tests using synthetic fixtures only.
5. Run canonical tests and projection tests before release.

## Security contract

Skills are trusted repository instructions and should be reviewed like
executable code. Security-sensitive skills should use local deterministic tools
where possible, avoid external network calls unless explicitly required, and
never expose secret or personally identifiable values in output.

## Pull request enforcement

When configured, the repository should run the security audit for pull
requests and scan both the pull request working tree and its Git history. The
scanner should come from the trusted base revision and scan the candidate
checkout separately. Scanner output should remain limited to redacted
metadata.

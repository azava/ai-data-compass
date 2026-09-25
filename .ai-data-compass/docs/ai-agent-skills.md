# AI Agent Skills

This document contains additional skill architecture and security details for the rules in `AGENTS.md`.

## Canonical source

Repository skills are maintained under `.ai-data-compass/skills/<skill-name>/`. The canonical `SKILL.md`, references, scripts, and tests in that directory are the source of truth.

## Codex discovery adapter

Codex discovers repository skills under `.agents/skills/<skill-name>/SKILL.md`. The distribution installs a small discovery adapter there that points to the canonical skill under `.ai-data-compass/skills/`.

The adapter must not duplicate the canonical workflow, scripts, references, or security logic.

## Claude Code projection

Claude Code discovers project skills under `.claude/skills/<skill-name>/SKILL.md`. The distribution installs each Claude adapter as a small entry point to the canonical skill. Adapters must not duplicate the canonical workflow or scanner logic.

## Adding or changing a skill

1. Add the skill's canonical files under `.ai-data-compass/skills/<directory>/`, including its scoped `LICENSE` and `THIRD-PARTY-NOTICES.md`.
2. Add one entry to `src/ai_data_compass/skill_catalog.json` with the CLI asset name, canonical directory, and interactive menu description.
3. Add Codex and Claude projections under `.agents/skills/<directory>/` and `.claude/skills/<directory>/`. Keep them as thin pointers to the canonical skill.
4. Write the frontmatter `description` as a short, single-sentence summary of the skill's main task and intended trigger. Keep workflow details and constraints in the body.
5. Keep skill instructions, comments, and documentation in English.
6. Add deterministic tests using synthetic fixtures only, then run the canonical and projection tests.

The catalog drives CLI selection and package inclusion. Adding a catalog entry does not generate the canonical files or host projections; those files must also be present in the repository.

A skill may include supporting subskills that its main workflow reads and follows. Keep these under the canonical skill directory; add separate catalog entries and host adapters only when they should also be independently discoverable.

## Security contract

Skills are trusted repository instructions and should be reviewed like executable code. Security-sensitive skills should use local deterministic tools where possible, avoid external network calls unless explicitly required, and never expose secret or personally identifiable values in output.

## Pull request enforcement

When configured, the repository should run the security audit for pull requests and scan both the pull request working tree and its Git history. The scanner should come from the trusted base revision and scan the candidate checkout separately. Scanner output should remain limited to redacted metadata.

# Testing Details

This document contains additional testing procedures for the rules in
`AGENTS.md`.

## Project Rules

- Security fixtures should be synthetic and should verify that scanner output does not contain the fixture value.
- Tests should cover both working-tree and Git-history modes.

## Test Commands

- `bash .ai-data-compass/skills/security-audit/tests/test_security_surface.sh`
- `bash .ai-data-compass/skills/security-audit/tests/test_claude_projection.sh`

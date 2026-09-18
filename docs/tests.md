# Testing Context

Add project-specific test commands, frameworks, fixtures, coverage requirements, and validation conventions here.

## Project Rules

- Security fixtures must be synthetic and must verify that scanner output does not contain the fixture value.
- Tests must cover both working-tree and Git-history modes.

## Test Commands

- `bash .agents/skills/security-audit/tests/test_security_surface.sh`
- `bash .agents/skills/security-audit/tests/test_claude_projection.sh`

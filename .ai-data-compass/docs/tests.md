# Testing Details

This document contains additional testing procedures for the rules in `AGENTS.md`.

## Project Rules

- Security fixtures should be synthetic and should verify that scanner output does not contain the fixture value.
- Tests should cover both working-tree and Git-history modes.

## Test Commands

- Run the full Python suite from the repository root:

`PYTHONPATH=src python -m unittest discover -s tests -v`

- The GitHub Actions test workflow runs the suite on Python 3.9 through 3.13 for pull requests, pushes to `main`, and manual dispatches.

- `bash .ai-data-compass/skills/security-audit/tests/test_security_surface.sh`
- `bash .ai-data-compass/skills/security-audit/tests/test_claude_projection.sh`
- `bash .ai-data-compass/skills/security-audit/tests/test_codex_projection.sh`
- `bash .ai-data-compass/skills/security-audit/tests/test_workflow_security_integration.sh`

Repository credential scans run in a separate workflow. For pull requests, that workflow loads the scanner from the trusted base revision and scans the proposed revision. Security skill regression tests also run in the standard test workflow, which intentionally executes the proposed revision's code.

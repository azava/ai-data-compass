# Testing Guidance

Use the project's documented test commands and run checks that cover the files and behavior affected by a change. Follow any test procedures defined in the repository's own instructions.

## Test Design

- Prefer deterministic tests with synthetic or representative fixtures.
- Cover expected behavior, relevant edge cases, and failure behavior.
- Do not place real credentials, personal records, or other sensitive values in test fixtures.
- For security tools, verify that output does not disclose fixture values.

## Running Checks

Run the checks configured by the repository, including focused tests for the changed behavior and the broader applicable suite before considering the work complete. If a required check is unavailable, report that limitation for review.

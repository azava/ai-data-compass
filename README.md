# AI Data Compass

AI Data Compass provides guidelines and automation for AI-assisted work in data repositories.

- **Guidelines.** Repository instructions guide coding agents on privacy, development practices, testing, and documentation.

- **Automation.** Reusable skills and scripts automate recurring developer tasks so teams can avoid repeating manual checks.

## Installation

The CLI supports Python 3.9 and newer. Install the package with pip, then run `init` to install assets in your repository:

```bash
python -m pip install ai-data-compass
ai-data-compass init --assets complete
```

The recommended `complete` selection installs the agent instructions and all available skills.

To choose assets interactively, run:

```bash
ai-data-compass init
```

Every installation includes the base documentation, license, and third-party notices. The installer creates missing files and preserves existing files whose content and required permissions already match.

If another existing target file differs, the installer refuses that asset instead of overwriting the file; it can continue with other selected assets and exits with a nonzero status.

When `AGENTS.md` already contains different instructions, the installer asks permission to create `AGENTS-ai-data-compass.md` (or the next available numbered name) and add a reference to it in the existing file; declining skips the agent-instructions asset.

When a skill directory name is already occupied by different content, the installer uses `<skill-name>-ai-data-compass` (or a numbered suffix) and updates the installed references to use that name.

## Example of use

A developer starts by installing AI Data Compass and launching its setup:

```bash
python -m pip install ai-data-compass
ai-data-compass init
```

The developer selects `complete` to install all guidance and skills, then types `y` to approve an added reference if **`AGENTS.md`** already contains different instructions.

From then on, the agent follows the AI Data Compass guidance in **`AGENTS.md`**, improving communication, code quality, documentation, and security throughout its work.

The developer asks **`project-review`** to inspect the repository and report findings, then decides which issues to fix.

Next, **`test-gap-review`** finds behaviors or bugs that need regression tests. The developer chooses an area and works through it with the project's test tools.

The **`data-quality-testing`** skill helps check rules such as required fields, allowed values, duplicates, and consistency while accounting for privacy, volume, infrastructure, and cost.

The **`project-quality-metrics`** skill helps choose and track useful measures of project health.

Before finishing, **`before-consider-done`** checks the project's tests, metrics, documentation, and security review procedures, and reports anything unavailable.

## Available assets

| Name | Description | How to use |
| --- | --- | --- |
| `agents.md` | `AGENTS.md` guidance and host adapters for supported coding agents. Tested with Claude and Codex | Your agent should import and follow `AGENTS.md`; instructions already defined by the project take precedence if they conflict. |
| `before_consider_done` | Validation procedure to run before considering a task done. | Ask your agent to run the `before-consider-done` skill when installed. |
| `project_review` | Read-only senior review of a complete repository, with an optional hosted-repository review. | Ask your agent to run the `project-review` skill; hosted review requires your approval to access the repository platform. |
| `documentation_validation` | Runs the documentation link and accuracy reviews together. | Ask your agent to run the `documentation-validation` skill. |
| `security_audit` | Security-audit skill with its scanner, references, tests, and Codex and Claude adapters. | Ask your agent to run the `security-audit` skill and review its metadata-only findings. |
| `test_gap_review` | Maps missing behavioral and regression tests and guides focused test-writing rounds. | Ask your agent to run the `test-gap-review` skill on the repository or selected changes. |
| `data_quality_testing` | Design and implement tests for data quality and business rules. | Ask your agent to run the `data-quality-testing` skill to plan privacy-aware tests and choose how and where to execute them. |
| `project_quality_metrics` | Define and track project quality metrics. | Ask your agent to run the `project-quality-metrics` skill to choose useful metrics and build a history and baseline suited to the project. |

## Documentation

Adopter guidance and package planning references:

- [Central AI agent instructions](AGENTS.md)
- [Documentation index](.ai-data-compass/docs/README.md)
- [Distribution and installation](.ai-data-compass/docs/distribution.md)
- [Security and privacy](.ai-data-compass/docs/security-and-privacy.md)
- [Testing guidance](.ai-data-compass/docs/tests.md)
- [Task completion checklist](.ai-data-compass/docs/task-completion.md)
- [Internal pending features backlog](PENDING_FEATURES.md)

Package maintainer procedures are documented in [docs/maintainers/README.md](docs/maintainers/README.md).

## License

This project is licensed under the [MIT License](LICENSE).

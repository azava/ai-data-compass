# AI Data Compass

AI Data Compass provides a practical, repository-level foundation for AI-assisted
data work. It establishes shared expectations for coding agents so they can work
with data projects safely, consistently, and with appropriate engineering rigor.

The guidance centers on privacy-aware data handling, focused changes, clear
documentation, maintainable design, testing, and measurable repository quality.
`AGENTS.md` is the primary instruction set for agents working in this repository.

## What it covers

- Protecting sensitive data, PII, credentials, and other private information.
- Maintaining concise, accurate project documentation.
- Applying pragmatic design and data-pipeline development patterns.
- Keeping changes focused, testable, and within scope.
- Evaluating quality, governance, reliability, and operational metrics.
- Completing work with validation and privacy-safe repository review.

## Documentation

Read the relevant documentation before starting work or making project-specific
assumptions:

- [Central AI agent instructions](AGENTS.md)
- [Documentation index](.ai-data-compass/docs/README.md)
- [Security and privacy](.ai-data-compass/docs/security-and-privacy.md)
- [Development patterns](.ai-data-compass/docs/development-patterns.md)
- [Testing guidance](.ai-data-compass/docs/tests.md)
- [Repository quality and metadata metrics](.ai-data-compass/docs/repository-quality-and-metadata-metrics.md)
- [Task completion checklist](.ai-data-compass/docs/task-completion.md)

## Installation

The command-line tool is packaged as the `ai-data-compass` Python package for
Python 3.9 and newer. Install it with pip in the target Python
environment:

```bash
python -m pip install ai-data-compass
ai-data-compass --version
```

For a globally available CLI isolated from other Python environments, use
pipx instead:

```bash
pipx install ai-data-compass
ai-data-compass --version
```

The CLI exposes `--version`, `init`, and `verify`. The base documentation is
installed with every asset selection. Select everything, the agent
instructions, one skill, or all skills with comma-separated values:

```bash
ai-data-compass init --assets complete
ai-data-compass init --assets agents.md,security_audit
ai-data-compass init --assets skills
```

Running `init` without `--assets` opens an interactive asset installer. It
defaults to `complete` when the selection is left empty. The interactive
output uses terminal colors when supported and honors `NO_COLOR`.

## License

This project is licensed under the [MIT License](LICENSE).

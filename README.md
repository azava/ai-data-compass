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

The recommended `complete` selection installs the agent instructions and all available skills. Run `ai-data-compass init` without `--assets` to choose interactively; leaving the selection empty chooses `complete`.

Every installation includes the base documentation, license, and third-party notices. The installer creates missing files and preserves existing files whose content and required permissions already match. If another existing target file differs, the installer refuses that asset instead of overwriting the file; it can continue with other selected assets and exits with a nonzero status.

When `AGENTS.md` already contains different instructions, the installer asks permission to create `AGENTS-ai-data-compass.md` (or the next available numbered name) and add a reference to it in the existing file; declining skips the agent-instructions asset. When a skill directory name is already occupied by different content, the installer uses `<skill-name>-ai-data-compass` (or a numbered suffix) and updates the installed references to use that name.

## Available assets

| Name | Description | How to use |
| --- | --- | --- |
| `agents.md` | `AGENTS.md` guidance and host adapters for supported coding agents. Tested with Claude and Codex | Your agent should import and follow `AGENTS.md`; instructions already defined by the project take precedence if they conflict. |
| `security_audit` | Security-audit skill with its scanner, references, tests, and Codex and Claude adapters. | Ask your agent to run the `security-audit` skill and review its metadata-only findings. |

## Documentation

Project guidance, workflows, and planning references:

- [Central AI agent instructions](AGENTS.md)
- [Documentation index](.ai-data-compass/docs/README.md)
- [Distribution and installation](.ai-data-compass/docs/distribution.md)
- [AI agent skills](.ai-data-compass/docs/ai-agent-skills.md)
- [Security and privacy](.ai-data-compass/docs/security-and-privacy.md)
- [Testing guidance](.ai-data-compass/docs/tests.md)
- [Task completion checklist](.ai-data-compass/docs/task-completion.md)
- [Internal pending features backlog](PENDING_FEATURES.md)

## License

This project is licensed under the [MIT License](LICENSE).

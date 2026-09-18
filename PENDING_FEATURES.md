# Pending Features

This is an internal backlog for AI Data Compass. It is intentionally stored at
the repository root because the content under `docs/` is intended to become
exportable project assets for repositories that adopt AI Data Compass.

The numbers below are stable reference identifiers only. They are not priority
levels, delivery order, or a statement that each number represents exactly one
implementation unit.

## Feature index

1. Distribution and project bootstrap
2. Language- and technology-agnostic code-testing skill
3. Data-quality and business-rule testing skill
4. Project-specific quality-metrics skill
5. Exportable documentation assets
6. Documentation validation and accuracy skills
7. Model and coding-harness integrations
8. Security-audit improvements

## Shared completion workflow

The repository's “before considering a task done” process must be implemented
as an explicit, repeatable workflow composed of skills and scripts. Each check
must also remain usable independently during development.

The workflow should discover the applicable project capabilities and invoke, as
appropriate:

- code-test analysis and test execution;
- data-quality and business-rule checks;
- project-specific quality-metric collection and comparison;
- documentation consistency, link, and reference validation;
- documentation accuracy review;
- security and privacy checks;
- repository-specific assertions and integration tests.

The workflow must make its scope explicit, such as the whole repository, the
current session, a branch, or a selected diff. It should produce concise,
reviewable evidence for every check, distinguish skipped checks from passing
checks, and fail or require explicit review when a required check cannot be
completed. It must respect the project's privacy rules and avoid exposing
sensitive data in reports or logs.

## 1. Distribution and project bootstrap

Create a supported way to distribute the reusable AI Data Compass assets to
other data projects. Candidate interfaces include a package and a command such
as `aidc init` or `ai-data start`; the final name and packaging model remain to
be decided.

The bootstrap must preserve the distinction between reusable assets and this
repository's internal backlog and development material.

### 1.1 Bootstrap for repositories without agent assets

Support repositories that do not yet contain `AGENTS.md`, skills, agent
configuration, or equivalent guidance artifacts.

The operation should add the required assets using a documented, deterministic
layout and should be safe to run repeatedly.

### 1.2 Integration with repositories that already have agent assets

Support repositories that already contain equivalent files, such as an
existing `AGENTS.md`, skills, rules, or model-specific adapters.

The integration must:

- append or compose guidance without silently changing existing repository
  rules;
- preserve the adopting repository's existing behavior and ownership;
- identify duplicate, contradictory, or overlapping rules;
- provide a standard conflict-resolution procedure using an LLM where human
  review is still required;
- offer a command or check that reports unresolved conflicts before completion;
- produce a deterministic result that can be reviewed in Git.

This capability depends on the initial bootstrap and may require a dedicated
skill for asset composition and conflict resolution.

### 1.3 Licensing of distributed assets

The bootstrap command or package must add the license and attribution notices
needed for assets copied from AI Data Compass, so the assets can be adopted in
corporate projects.

The implementation must define how notices are added, updated, and associated
with generated files.

## 2. Language- and technology-agnostic code-testing skill

Create a skill that helps an LLM and a developer find and create missing code
tests across different languages, frameworks, build systems, and execution
environments. The skill must be language- and technology-agnostic in its
orchestration and discovery process, but it must use the native testing
capabilities of the technology being tested rather than reducing every project
to generic language-level tests.

The skill should be usable in two scopes:

- the whole repository;
- only the current session's changes, branch changes, or another explicitly
  selected diff.

It should identify implemented functions or equivalent units of behavior that
lack meaningful tests, and it should identify documented bugs that do not have
regression tests. It must distinguish untestable infrastructure or generated
code from genuine coverage gaps instead of producing a purely numerical
coverage report.

The skill should discover and use the project's native test ecosystem and
execution model, including applicable tools for Python, SQL, dbt, PySpark,
Flink, Dataflow, pandas, and other data technologies. It should be extensible
through technology-specific adapters or playbooks without changing the
language-agnostic workflow.

The skill should support both workflows:

- invocation as part of the repository's “before considering a task done”
  procedure;
- standalone invocation to guide test creation during development.

This feature may include the unified validation entry point that runs the
applicable repository tests and other deterministic checks.

## 3. Data-quality and business-rule testing skill

Create a skill similar to Feature 2, but focused on data quality and business
rules rather than application-code behavior. Like Feature 2, it must be
language- and technology-agnostic at the orchestration level while using the
full native capabilities of the project's data stack.

The initial scope should prioritize tests that are appropriate for the rule and
execution environment. Row-level checks and uniqueness checks should be
available where they are cheap and do not require an unnecessary distributed
shuffle, but the skill must not impose a blanket restriction against using
distributed or platform-native execution when that is the correct trade-off.
The initial scope includes:

- row-level validity and required-field rules;
- type, range, format, and referential checks that can be evaluated locally;
- nullability and allowed-value rules;
- partition- or batch-level completeness checks where they do not require a
  full reshuffle;
- uniqueness tests and duplicate detection with explicitly documented cost,
  infrastructure, execution plan, and scope;
- business rules expressed as deterministic assertions.

The skill should support native approaches such as dbt tests and macros,
PySpark or pandas test suites, Flink job or operator tests, Dataflow pipeline
tests, SQL assertions, and framework-specific data-quality checks. It should
select between local, sampled, partitioned, cluster, and full-scale execution
based on the project's correctness needs and declared constraints.

For every proposed test, the skill should document the expected compute cost,
required infrastructure, data volume, shuffle or network behavior, runtime,
environment, and whether the test is suitable for local development, CI,
staging, or production-like execution. It should use schemas, aggregates,
synthetic fixtures, and metadata when possible, while respecting the project's
privacy rules and avoiding unnecessary exposure of sensitive row values.

Tests should be independent of production systems when that is technically and
operationally appropriate, but the skill must also support tests that require
realistic infrastructure, representative data, managed services, or production-
like execution when those are necessary to validate distributed behavior,
query planning, performance, data contracts, or platform-specific semantics.

The skill should support both whole-repository and change-focused analysis and
must make the selected scope and execution mode explicit in its output.

## 4. Project-specific quality-metrics skill

Create a skill that helps a project define the metrics it actually needs from
the topic groups listed in `AGENTS.md`, rather than assuming every project must
implement every metric.

The skill should:

- ask which topic groups are in scope;
- identify the owners, targets, thresholds, and review cadence;
- develop concrete metric definitions and collection procedures;
- distinguish required metrics from optional metrics;
- define how a baseline is created and how changes are compared with it;
- document expected cost, freshness, and failure behavior.

It must also help decide where and how metrics are stored, including a
documented choice among options such as:

- CI artifacts or workflow summaries;
- files committed to the repository;
- a project database or metrics store;
- an external observability or governance system.

The selected storage mechanism must include retention, access, reproducibility,
and privacy considerations.

## 5. Exportable documentation assets

Make it explicit which files under `docs/` are reusable assets intended to be
copied or composed into adopting projects, and which files are specific to the
AI Data Compass repository itself.

This work should include:

- removing or replacing placeholder `TODO` sections that would make exported
  guidance incomplete;
- separating templates, defaults, and repository-specific decisions;
- standardizing sections and merge points so guidance can be composed with
  existing project rules;
- documenting ownership, versioning, compatibility, and update behavior for
  exported assets;
- defining how an adopting project records local overrides without editing
  the upstream source of truth.

This feature is likely a prerequisite for Feature 1, especially the integration
path for repositories that already have equivalent guidance.

## 6. Documentation validation and accuracy skills

Create two related skills for use in the “before considering a task done”
procedure and as standalone development checks.

### 6.1 Documentation consistency and link-validation skill

This skill should validate, as applicable:

- internal links and referenced files;
- required sections and headings;
- consistency between canonical agent guidance and model-specific adapters;
- references to commands, scripts, skills, and configuration paths;
- stale or unresolved placeholders in exportable assets;
- documentation changes required by changed interfaces or behavior.

It must report actionable metadata without printing sensitive file contents and
should support repository-wide and change-focused scopes.

### 6.2 Documentation accuracy-review skill

Create a second skill that reviews whether project documentation is accurate,
complete, and consistent with the implementation and observed behavior.

The skill should compare documentation with applicable repository evidence,
including:

- public interfaces, schemas, configuration, and command-line options;
- source code behavior and error handling;
- tests, fixtures, and validation procedures;
- CI workflows and operational procedures;
- security, privacy, governance, and data-classification requirements;
- examples, version statements, ownership, and compatibility claims.

It should identify claims that are stale, incomplete, ambiguous, unsupported,
or contradicted by the implementation. It must distinguish a documentation
gap from a possible implementation bug and should recommend whether the code,
the documentation, or both require a change.

The review must use safe evidence: schemas, metadata, synthetic fixtures,
aggregates, command output, and source inspection. It must not require
exposing sensitive or production row values. Findings should include the
affected document, claim or section, supporting evidence type, confidence, and
recommended action without copying sensitive content.

The skill should support whole-repository and change-focused reviews, and it
should be able to run as part of the shared completion workflow described
above.

## 7. Model and coding-harness integrations

Integrate the canonical skills and exportable guidance with the models, coding
agents, and execution harnesses used by the project. The repository should
maintain one explicit compatibility matrix instead of referring to unnamed
future adapters.

The compatibility scope identified so far is:

### Models and coding agents

- Codex (current native support);
- Claude Code (current projection support);
- Gemini;
- Cursor;
- Windsurf;
- Kimi;
- GitHub Copilot;
- OpenCode;
- Grok;
- DeepSeek;
- GLM.

### Execution and automation harnesses

- GitHub Actions;
- the local command-line bootstrap and validation workflow;
- host-specific skill discovery and projection mechanisms required by the
  agents above.

Codex and Claude Code are the current reference integrations. The other model
and agent integrations are planned compatibility targets and must be validated
against their actual discovery, instruction-loading, skill, and execution
conventions before being marked as supported.

The integration design should keep one canonical implementation of each skill
and use thin host-specific adapters where required. Each adapter should have a
projection test that verifies discovery, loading, and version consistency
without duplicating business logic.

The final supported-platform matrix, installation instructions, and known
feature differences must be documented.

## 8. Security-audit improvements

Improve the current credential-exposure audit while preserving its safety
contract: read-only operation, metadata-only reports, no secret validation by
default, synthetic fixtures, and separate working-tree and Git-history scopes.

The following are separate improvement areas that may become separate
features, releases, or skills.

### 8.1 Broader credential-pattern coverage

Expand detection beyond the current credential-shaped patterns to cover more
provider-specific tokens, key formats, encoded values, multiline secrets, and
secrets split across configuration structures.

Every new rule must document expected false positives, severity, confidence,
and redaction behavior.

### 8.2 Binary, archive, and serialized-content scanning

Define a safe strategy for detecting credential candidates in binary,
compressed, archived, serialized, and common data files, including formats such
as SQLite, Parquet, Excel, PDF, and build artifacts where appropriate.

The implementation must set explicit size, recursion, decompression, and
resource limits. Encrypted or unreadable content must be reported as an
inspection limitation rather than treated as clean.

### 8.3 Tool-assisted PII and PHI detection

Add an optional PII/PHI detection mode based on specialized tools or services,
such as Presidio or comparable technology. The selected tools should support
the project's required regulatory context, including HIPAA-related controls
where applicable, without claiming that detection alone establishes compliance.

The mode must define supported entities, confidence thresholds, language
coverage, false-positive handling, and metadata-only reporting. It must support
schemas, aggregates, synthetic fixtures, or sampled data according to the
repository's privacy rules rather than exposing raw records to the agent.

### 8.4 Data-Catalog-driven PII and PHI detection

Add a second PII/PHI mode driven by the adopting project's own Data Catalog.
The catalog should be able to declare classifications for datasets, tables,
columns, fields, and rule-specific sensitivity categories.

The bootstrap and configuration commands from Feature 1 should be able to:

- enable or disable catalog-driven checks;
- select the catalog source and version;
- configure sensitive fields and project-specific patterns;
- define applicable regulations and retention or access metadata;
- choose whether checks run locally, in CI, or against an approved metadata
  service;
- validate that the catalog configuration is complete and internally
  consistent.

The scanner must not infer that a field is safe merely because it is absent
from the catalog. Unknown or unclassified fields should be reported according
to an explicit project policy.

### 8.5 Optional active-credential verification

Define an opt-in workflow for confirming whether a finding is active, valid, or
revocable through the owning provider.

This must never be part of the default offline scan. It requires explicit
authorization, provider-specific credentials supplied outside repository
content, audit logging, rate limits, and a policy for avoiding side effects.
The default output must still avoid exposing the credential value.

### 8.6 Broader working-tree scope

Provide an explicit mode for scanning ignored files, selected directories, or
the complete filesystem scope supplied by the user, while keeping the current
Git-aware mode as the safe default.

The implementation must define symlink handling, file-size limits, permission
errors, excluded paths, and how inaccessible files are reported.

### 8.7 More complete Git-history analysis

Improve history coverage for sensitive filenames, renamed and deleted files,
commit metadata where appropriate, and explicitly selected refs. Document the
limits around unreachable objects, reflogs, stashes, Git LFS, and shallow or
partial clones.

### 8.8 Safe diagnostics and triage support

Improve the metadata-only report so maintainers can distinguish likely
placeholders, examples, duplicates, and actionable findings without exposing
matched values.

Possible metadata includes rule explanations, deterministic finding IDs,
deduplication guidance, remediation links, and documented suppression or
allowlist mechanisms. Any suppression must be reviewable and must not silently
hide new findings.

### 8.9 Scanner error handling and completeness reporting

Ensure unreadable files, unsupported formats, skipped paths, truncation, and
resource-limit events are reported explicitly. A scan must not present an
incomplete inspection as a clean result.

### 8.10 Security-audit test coverage

Expand synthetic regression tests to cover every detection rule, binary and
archive behavior, ignored files, symlinks, sensitive filenames in history,
unreadable inputs, truncation, JSON/Markdown output, PII/PHI modes, and
metadata-only redaction.

Tests must never use real credentials, PII, or PHI.

### 8.11 CI coverage and execution modes

Extend CI coverage beyond the current pull-request events with an explicitly
chosen combination of push, scheduled, manual, and release checks.

The workflow must continue to obtain security-sensitive scanner logic from a
trusted source, scan the candidate separately, and fail safely when the scan
is incomplete or findings exceed configured limits.

## Cross-feature decisions still required

The following decisions affect multiple features and should be recorded before
implementation:

- canonical package and command name (`aidc`, `ai-data`, or another choice);
- asset manifest and versioning strategy;
- merge and conflict-resolution format for existing project rules;
- supported model and harness adapter contract;
- default storage for metrics and Data Catalog configuration;
- offline versus service-backed behavior for optional checks;
- licensing and attribution format for generated assets;
- policy for unknown, unclassified, or inaccessible data;
- minimum validation required before an asset or skill is considered complete.

## Maintenance

Update this backlog when a feature is implemented, split into separately
tracked work, blocked by an architectural decision, or replaced by a new
approach. Keep the numeric identifiers stable so discussions and implementation
references remain understandable across revisions.

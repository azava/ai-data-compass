# Metric History Format and Storage

Read this reference when a round introduces or changes persistent metric results. Use the smallest format that preserves safe, comparable history.

## Run and result fields

Use a versioned machine-readable format when results are collected repeatedly. JSONL is a practical repository-local default for small append-only histories; one result per line makes appends and parsing straightforward. Keep definitions and rationale in a concise project document or existing metric registry rather than repeating prose in each run.

Include fields only when they help identify, compare, retain, or audit a result. A compact run context can include:

- `schema_version`, `run_id`, `recorded_at_utc`, and `suite_version`.
- `environment`, `branch`, `commit`, `trigger`, and CI workflow or pipeline run ID when applicable.
- `data_window` or source freshness marker when the measurement depends on changing data.
- A `metric_id`, numeric or categorical `value`, `unit`, `status`, and applicable target or threshold.
- Safe dimensions needed for comparison, such as component, service, dataset identifier, or region, subject to the project's privacy classification.

The repository itself may identify the project, and local exploratory runs may not have a branch or pipeline ID. Do not fabricate missing context; omit it or mark it unavailable. Keep timestamps in UTC with an unambiguous format. Do not log raw records, credentials, PII, PHI, or confidential values. Confirm that even dimensions and metric values are safe to retain.

## Choose storage when needed

Check the project's existing metric stores first. Recommend new storage only when the current one cannot meet a real need.

| Option | Fits when | Check before choosing |
| --- | --- | --- |
| Repository JSONL or CSV | The history is small, non-sensitive, low-write-volume, and useful beside code. | Retention, repository visibility, concurrent CI writers, branch protection, commit noise, and preventing a metrics commit from retriggering collection. JSONL suits evolving records; CSV suits a stable flat schema. |
| CI artifacts | The team needs easy run-by-run inspection and bounded retention. | Artifact expiry and retrieval. Artifacts alone may not provide the durable baseline history the project needs. |
| Existing database, cloud logs, monitoring, or metrics platform | The project needs durable high-volume history, queries, access controls, multi-environment views, or operational alerts. | Authorized access, cost, retention, privacy, ownership, and whether the platform can expose safe summaries to the agent. |

If the project has no system and repository storage is unsuitable, compare only the viable options for its platform and ask the user to choose only if that choice changes cost, access, or ongoing operations. Do not create cloud resources, incur charges, or add credentials without explicit user agreement.

## History and baseline promotion

- Configure operational runs to persist observations needed for trends and alerts, including valid measurements showing regressions and safe failure records when collection fails. Record missing values as unavailable, never as zero or a passing result.
- Keep collection status and baseline eligibility distinct. A saved observation is historical evidence; it becomes a stable baseline only under the project's agreed promotion rule.
- Define that rule for the environment, such as accepted quality criteria after an approved deployment or data refresh. Successful collection alone does not establish acceptable quality.
- For a project without an existing promotion process, propose a first complete execution reviewed and accepted by the user as the initial baseline. Record its environment, scope, metric definitions, revision, and relevant data context, then explicitly persist the accepted result. This can start locally without CI or deployment automation; it establishes a comparison reference, not proof that undefined quality targets have been met.
- Preserve the previous stable baseline when a run is failed, partial, experimental, or incomparable. Retain safe results and failure metadata in history without promoting them.
- If no stable result exists, identify the event and acceptance criteria that can establish one. Verify retention and retrieval for the chosen store so the agent can access a suitable baseline later.

# Execution Planning

Use this reference for a selected round when external access, execution scale, sampling, infrastructure, or cost affects the recommendation. Inspect available evidence first and discuss only unresolved decisions with the user.

## Relevant execution constraints

- Determine whether the rule is local, batch-wide, or global, using the source, volume, partitions, and expected scan size.
- Check existing compute and storage, permissions, dependencies, network access, shuffle, and transfers between systems where relevant.
- Identify the execution environment and owner: local fixtures, CI, staging, an authorized cluster, or a managed service. Confirm privacy controls, read-only behavior, and operational side effects.
- Estimate runtime and cost with stated assumptions. Use qualitative estimates or ranges when precise measurements are unavailable.

Choose local, synthetic, sampled, partitioned, cluster, or full-scale execution according to the rule and project constraints. Distributed or representative infrastructure may be necessary; do not default to a small local test when it cannot establish the intended property. State the limits of sample and partition results.

## External execution handoff

- If the agent lacks access, provide reproducible commands or job instructions, prerequisites, scope, and the expected safe result format for the user to run in the approved environment.
- The handoff must satisfy the same privacy boundaries as direct execution. Do not use it to bypass prohibited access or request raw records, sensitive examples, or credentials.
- Ask for only the safe summary needed to evaluate the outcome: rule, environment, scope or window, execution status, safe aggregate findings, and measured runtime or cost when available.
- Report returned evidence as user-run, with its scope and limitations. A failed job or unavailable environment is not a passing data-quality check.

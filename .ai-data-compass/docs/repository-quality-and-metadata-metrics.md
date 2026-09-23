# Repository Quality and Metadata Metrics

Select the metric categories and individual metrics that fit the project's data, technology, operational needs, and governance requirements. This reference describes the scope of each category; it does not require every project to implement every metric.

| Category | Subcategory | What to observe |
| --- | --- | --- |
| Data quality and validation | Volume | Record counts, bytes, and partitions; deviations from expected or historical volumes. |
| Data quality and validation | Data completeness | Presence of expected records, fields, keys, and source partitions. |
| Data quality and validation | Missing values | Count and proportion of null or missing values by field, period, or relevant group. |
| Data quality and validation | Validity | Conformance to types, formats, allowed ranges, domains, and business rules. |
| Data quality and validation | Uniqueness | Compliance with uniqueness constraints for simple or composite keys. |
| Data quality and validation | Duplicates | Count and proportion of repeated records according to explicit identification criteria. |
| Data quality and validation | Data consistency | Agreement across fields, tables, sources, and business rules; consistency of equivalent results. |
| Data quality and validation | Data validation and test coverage | Validation rules executed, pass and failure results, coverage of expected checks, and changes in outcomes over time. |
| Freshness and timeliness | Freshness | Age of the newest available data and its difference from the expected update frequency. |
| Freshness and timeliness | Timeliness | Whether delivery meets defined schedules, deadlines, and processing windows. |
| Freshness and timeliness | Latency | Time from event occurrence to ingestion, processing, and availability. |
| Data observability and anomaly detection | Monitoring | Coverage of sources, pipeline stages, metrics, and data outputs. |
| Data observability and anomaly detection | Alerting | Alerts raised, detection delays, and events that were not alerted within defined limits. |
| Data observability and anomaly detection | Anomalies and data drift | Unexpected changes in volumes, distributions, values, patterns, or relationships between variables. |
| Data and pipeline reliability | Availability | Availability of sources, pipelines, and outputs when they are needed. |
| Data and pipeline reliability | Output completeness | Presence of all expected tables, files, partitions, or results after pipeline execution. |
| Data and pipeline reliability | Output consistency | Integrity and consistency of results across stages, executions, and destinations. |
| Data and pipeline reliability | Success and error rates | Proportion of successful and failed executions; distinguish execution errors from rejected records. |
| Data and pipeline reliability | Failure handling and recovery | Failures detected, recovery outcomes, data loss, and time to restore operation. |
| Data and pipeline reliability | Retries and reruns | Retry outcomes and any data duplication, omission, or corruption after reruns. |
| Schema evolution and compatibility | Schema conformance | Whether received data matches the expected schemas or contracts. |
| Schema evolution and compatibility | Schema evolution and drift | Columns added, removed, or changed, including changes to types, nullability, or meaning. |
| Schema evolution and compatibility | Compatibility | Effects of schema changes on existing producers, consumers, queries, and pipelines. |
| Security, privacy, and regulatory compliance | Security | Protection controls, unintended exposure, credential handling, and security check outcomes. |
| Security, privacy, and regulatory compliance | Privacy | Handling of sensitive data, access to values, minimization, anonymization, and PII or PHI protections. |
| Security, privacy, and regulatory compliance | Regulatory compliance | Conformance with applicable legal, regulatory, and contractual requirements, including evidence and identified gaps. |
| Security, privacy, and regulatory compliance | Access | Permissions, privileges, unauthorized access, and compliance with access policies. |
| Governance, documentation, and lineage | Ownership and stewardship | Assigned owners and stewards for data, metrics, and processes, and coverage of relevant assets. |
| Governance, documentation, and lineage | Retention | Compliance with retention periods, deletion requirements, and preservation obligations. |
| Governance, documentation, and lineage | Metadata management | Completeness, quality, freshness, and consistency of metadata and classifications. |
| Governance, documentation, and lineage | Table and column documentation | Coverage and freshness of descriptions, definitions, types, classifications, and usage rules. |
| Governance, documentation, and lineage | Data lineage | Traceability of data sources, transformations, dependencies, and destinations. |
| Code quality and testing | Code quality | Code quality, maintainability, and conformance to the standards of the project's technologies. |
| Code quality and testing | Code tests | Behavioral and edge-case coverage, failure-path coverage, test stability, and results. |
| Reproducibility and efficiency | Reproducibility | Ability to obtain equivalent results from the same inputs, parameters, code, and environment. |
| Reproducibility and efficiency | Idempotency | Consistency of results when the same process is rerun with the same inputs. |
| Reproducibility and efficiency | Performance | Runtime, CPU, memory, network, and storage use relative to operational requirements. |
| Reproducibility and efficiency | Cost efficiency | Processing, storage, and service costs relative to the volume handled and results produced. |

Data completeness and pipeline output completeness measure different things: the first checks whether expected input data arrived, while the second checks whether execution produced all expected outputs. Freshness measures the age of available data; latency measures elapsed processing or delivery time. Define each selected metric's formula, scope, source, collection frequency, owner, and thresholds or review criteria.

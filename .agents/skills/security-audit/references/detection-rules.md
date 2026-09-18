# Detection rules

The scanner reports candidates, not confirmed incidents. Rules are intentionally conservative and never include matched values in output.

| Rule | Category | Severity | Confidence | Scope |
| --- | --- | --- | --- | --- |
| `credential.private-key` | credential | critical | confirmed | Private-key PEM headers |
| `credential.assignment` | credential | high | likely | Credential-shaped key/value assignments |
| `credential.authorization` | credential | high | likely | Bearer or Basic authorization values |
| `credential.jwt` | credential | high | likely | JWT-shaped values |
| `credential.url-auth` | credential | high | likely | Credentials embedded in URLs |
| `credential.provider-key` | credential | high | likely | Common provider-key prefixes |
| `credential.filename` | credential | medium | possible | Credential-shaped filenames |

Known placeholders and examples may still produce findings. Review them without opening the matching value through the agent.

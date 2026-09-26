---
name: documentation-accuracy
description: Check whether project documentation agrees with the implementation and observed behavior.
---

# Documentation Accuracy

Review whether repository documentation accurately describes the implementation and observed behavior. Correct clear documentation inaccuracies using repository evidence. If the evidence is inconclusive or suggests an implementation defect, leave the claim unchanged and report the issue rather than guessing or modifying application code.

Compare claims in scope with relevant source code, configuration, command help, tests, and workflows. Report only claims that are incorrect, stale, or materially incomplete. Distinguish a documentation issue from a possible implementation bug; do not report style preferences.

When reviewing a repository that contains vendor-provided documentation or assets, distinguish claims about the adopting project from claims about the vendor or product. Do not assume an adopting repository includes the vendor's development sources. Verify product, CLI, or compatibility claims using installed distribution metadata, files, and command help from the active environment when available. Do not install dependencies or fetch external sources solely to verify them. If the evidence is unavailable, report a verification limitation rather than calling the claim inaccurate.

Report corrections to the parent skill with the document and section and the relevant repository evidence. The parent skill owns the final validation pass. Do not reproduce sensitive values or large source excerpts.

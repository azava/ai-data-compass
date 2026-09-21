#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../../../.." && pwd)
WORKFLOW="$REPO_ROOT/.github/workflows/security-audit.yml"

fail() {
    printf 'test failure: %s\n' "$1" >&2
    exit 1
}

assert_contains() {
    local needle=$1
    grep -F -- "$needle" "$WORKFLOW" >/dev/null || fail "expected workflow to contain: $needle"
}

assert_not_contains() {
    local needle=$1
    ! grep -F -- "$needle" "$WORKFLOW" >/dev/null || fail "workflow must not contain: $needle"
}

canonical_line=$(grep -nF 'SCANNER="$TRUSTED_ROOT/.ai-data-compass/skills/security-audit/scripts/security-surface.sh"' "$WORKFLOW" | cut -d: -f1)
legacy_line=$(grep -nF 'SCANNER="$TRUSTED_ROOT/.agents/skills/security-audit/scripts/security-surface.sh"' "$WORKFLOW" | cut -d: -f1)

[[ -n $canonical_line ]] || fail 'canonical trusted scanner resolution is missing'
[[ -n $legacy_line ]] || fail 'legacy trusted scanner fallback is missing'
(( canonical_line < legacy_line )) || fail 'canonical scanner must be preferred over the legacy path'

assert_contains 'if [ -x "$TRUSTED_ROOT/.ai-data-compass/skills/security-audit/scripts/security-surface.sh" ]'
assert_contains 'elif [ -x "$TRUSTED_ROOT/.agents/skills/security-audit/scripts/security-surface.sh" ]'
assert_contains 'echo "Trusted security scanner was not found."'
assert_contains 'bash "$SCANNER"'
assert_contains '--root "$CANDIDATE_ROOT"'
assert_not_contains 'SCANNER="$CANDIDATE_ROOT/'
assert_not_contains 'bash "$CANDIDATE_ROOT/.ai-data-compass/'
assert_not_contains 'bash "$CANDIDATE_ROOT/.agents/'

[[ $(grep -cF 'bash "$SCANNER"' "$WORKFLOW") -eq 2 ]] || fail 'working-tree and history scans must use the trusted scanner'

printf '%s\n' 'workflow security integration tests passed'

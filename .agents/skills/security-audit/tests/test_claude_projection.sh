#!/usr/bin/env bash

set -euo pipefail

# Locate the canonical skill and its Claude adapter.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../../../.." && pwd)
ADAPTER="$REPO_ROOT/.claude/skills/security-audit/SKILL.md"
CANONICAL="$REPO_ROOT/.agents/skills/security-audit/SKILL.md"
SCANNER="$REPO_ROOT/.agents/skills/security-audit/scripts/security-surface.sh"

fail() {
    # Stop the test with a concise failure message.
    printf 'test failure: %s\n' "$1" >&2
    exit 1
}

assert_contains() {
    # Check that the projection contains the required contract text.
    local file=$1 needle=$2
    grep -F -- "$needle" "$file" >/dev/null || fail "expected $file to contain: $needle"
}

# Verify the projection and canonical resources exist.
[[ -f $ADAPTER ]] || fail 'Claude adapter is missing'
[[ -f $CANONICAL ]] || fail 'canonical skill is missing'
[[ -x $SCANNER ]] || fail 'canonical scanner is not executable'

# Verify metadata and canonical source references.
assert_contains "$ADAPTER" 'name: security-audit'
assert_contains "$ADAPTER" 'description: Audit a repository for credential exposure in its working tree and Git history.'
assert_contains "$ADAPTER" '.agents/skills/security-audit/SKILL.md'
assert_contains "$ADAPTER" '.agents/skills/security-audit/scripts/security-surface.sh'
assert_contains "$CANONICAL" 'REPO_ROOT="$(git rev-parse --show-toplevel)"'

printf '%s\n' 'Claude skill projection tests passed'

#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../../../.." && pwd)
ADAPTER="$REPO_ROOT/.agents/skills/security-audit/SKILL.md"
CANONICAL="$REPO_ROOT/.ai-data-compass/skills/security-audit/SKILL.md"

fail() {
    printf 'test failure: %s\n' "$1" >&2
    exit 1
}

assert_contains() {
    local file=$1 needle=$2
    grep -F -- "$needle" "$file" >/dev/null || fail "expected $file to contain: $needle"
}

assert_not_contains() {
    local file=$1 needle=$2
    ! grep -F -- "$needle" "$file" >/dev/null || fail "unexpected duplicated reference in $file: $needle"
}

[[ -f $ADAPTER ]] || fail 'Codex adapter is missing'
[[ -f $CANONICAL ]] || fail 'canonical skill is missing'

description=$(awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && /description:/ {
        sub(/^.*description:[[:space:]]*/, "")
        print
        exit
    }
' "$CANONICAL")
[[ -n $description ]] || fail 'canonical skill description is missing'

assert_contains "$ADAPTER" 'name: security-audit'
assert_contains "$ADAPTER" "description: $description"
assert_contains "$ADAPTER" '.ai-data-compass/skills/security-audit/SKILL.md'
assert_not_contains "$ADAPTER" '.agents/skills/security-audit/scripts/'
assert_not_contains "$ADAPTER" '.agents/skills/security-audit/references/'

printf '%s\n' 'Codex skill projection tests passed'

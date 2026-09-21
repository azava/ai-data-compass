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

assert_contains 'scan_mode working-tree'
assert_contains 'scan_mode history'
[[ $(grep -cF 'bash "$SCANNER"' "$WORKFLOW") -eq 1 ]] || fail 'scanner invocation must remain inside scan_mode'
[[ $(grep -cF 'set +e' "$WORKFLOW") -eq 1 ]] || fail 'errexit must be disabled only around scan result collection'

# Execute the function extracted from the workflow so a failing working-tree
# scan cannot prevent the history scan from running.
RUNTIME_ROOT=$(mktemp -d)
trap 'rm -rf "$RUNTIME_ROOT"' EXIT
RUNTIME_FUNCTION="$RUNTIME_ROOT/scan-mode.sh"
sed -n '/^          scan_mode() {/,/^          }$/p' "$WORKFLOW" | sed 's/^          //' > "$RUNTIME_FUNCTION"
[[ -s $RUNTIME_FUNCTION ]] || fail 'scan_mode function could not be extracted'

FAKE_SCANNER="$RUNTIME_ROOT/scanner.sh"
CALL_LOG="$RUNTIME_ROOT/calls.log"
cat > "$FAKE_SCANNER" <<'SCANNER'
#!/usr/bin/env bash
set -u
case " $* " in
    *" --mode working-tree "*)
        printf '%s\n' working-tree >> "$CALL_LOG"
        exit 1
        ;;
    *" --mode history "*)
        printf '%s\n' history >> "$CALL_LOG"
        exit 0
        ;;
    *)
        exit 2
        ;;
esac
SCANNER
chmod +x "$FAKE_SCANNER"
export CALL_LOG
export SCANNER="$FAKE_SCANNER"
export CANDIDATE_ROOT="$RUNTIME_ROOT/candidate"
export RUNNER_TEMP="$RUNTIME_ROOT/reports"
export GITHUB_STEP_SUMMARY="$RUNTIME_ROOT/summary.md"
mkdir -p "$CANDIDATE_ROOT" "$RUNNER_TEMP"
# shellcheck disable=SC1090
source "$RUNTIME_FUNCTION"
set +e
scan_mode working-tree
working_status=$?
scan_mode history
history_status=$?
set -e
[[ $working_status -eq 1 ]] || fail 'working-tree scanner status was not preserved'
[[ $history_status -eq 0 ]] || fail 'history scanner status was not preserved'
[[ $(wc -l < "$CALL_LOG") -eq 2 ]] || fail 'history scan did not run after working-tree failure'
grep -Fx history "$CALL_LOG" >/dev/null || fail 'history scan invocation was not recorded'

printf '%s\n' 'workflow security integration tests passed'

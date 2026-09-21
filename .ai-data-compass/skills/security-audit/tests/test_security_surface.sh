#!/usr/bin/env bash
# Canonical synthetic regression tests for the security scanner.

set -euo pipefail

# Locate the scanner and create an isolated synthetic repository.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SCANNER="$SCRIPT_DIR/../scripts/security-surface.sh"
TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT

fail() {
    # Stop the test with a concise failure message.
    printf 'test failure: %s\n' "$1" >&2
    exit 1
}

assert_contains() {
    # Check that expected redacted metadata is present.
    local haystack=$1 needle=$2
    [[ $haystack == *"$needle"* ]] || fail "expected output to contain: $needle"
}

assert_not_contains() {
    # Ensure sensitive fixture values never appear in output.
    local haystack=$1 needle=$2
    [[ $haystack != *"$needle"* ]] || fail "output exposed sensitive fixture value"
}

# Create synthetic files that resemble credential exposure.
mkdir -p "$TEST_ROOT/repo/config"
git -C "$TEST_ROOT/repo" init -q
git -C "$TEST_ROOT/repo" config user.email test@example.invalid
git -C "$TEST_ROOT/repo" config user.name security-test

password_key=pass"word"
fixture_value="synthetic-value-$(printf '%s' fixture | sha256sum | cut -c1-12)"
printf '%s=%s\n' "$password_key" "$fixture_value" > "$TEST_ROOT/repo/config/settings.env"
printf '%s\n' 'ordinary documentation' > "$TEST_ROOT/repo/README.md"
printf '%s\n' 'http://localhost:5173/@vite/client' > "$TEST_ROOT/repo/frontend.js"
quoted_key=api_key
quoted_value=synthetic-quoted-value
printf '{"%s": "%s"}\n' "$quoted_key" "$quoted_value" > "$TEST_ROOT/repo/config/settings.json"
header_name=Authorization
header_scheme=Bearer
header_value=synthetic-bearer-value
printf '%s: %s %s\n' "$header_name" "$header_scheme" "$header_value" > "$TEST_ROOT/repo/config/headers.txt"
jwt_segment=eyJabcdefghijk
printf '%s.%s.%s\n' "$jwt_segment" "$jwt_segment" "$jwt_segment" > "$TEST_ROOT/repo/config/token.txt"
url_scheme=https
url_user=user
url_password=synthetic-pass
url_host=host.invalid
printf '%s://%s:%s@%s\n' "$url_scheme" "$url_user" "$url_password" "$url_host" > "$TEST_ROOT/repo/config/url.txt"
provider_prefix=AKIA
provider_suffix=ABCDEFGHIJKLMNOP
printf '%s%s\n' "$provider_prefix" "$provider_suffix" > "$TEST_ROOT/repo/config/provider.txt"
private_prefix='-----BEGIN'
private_suffix=' PRIVATE KEY-----'
printf '%s%s\n' "$private_prefix" "$private_suffix" > "$TEST_ROOT/repo/config/private-key.txt"
filename_key=secret
filename_value=synthetic-name-fixture
printf '%s = %s\n' "$filename_key" "$filename_value" > "$TEST_ROOT/repo/config/secret\"fixture|colon:name.txt"
ln -s README.md "$TEST_ROOT/repo/documentation-link"
# Git reports the symlink as a candidate; it does not report the FIFO.
mkfifo "$TEST_ROOT/repo/metadata-pipe"

# Verify working-tree detection and redaction.
working_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode working-tree --format json)
assert_contains "$working_report" 'credential.filename'
assert_contains "$working_report" 'credential.assignment'
assert_contains "$working_report" 'credential.authorization'
assert_contains "$working_report" 'credential.jwt'
assert_contains "$working_report" 'credential.url-auth'
assert_contains "$working_report" 'credential.provider-key'
assert_contains "$working_report" 'credential.private-key'
assert_contains "$working_report" '"files_skipped":1'
assert_contains "$working_report" 'some files were skipped because they were not regular readable files'
assert_not_contains "$working_report" "$fixture_value"
assert_not_contains "$working_report" 'password='

# A normal Vite development URL must not be classified as URL credentials.
safe_url_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode working-tree --format json)
assert_not_contains "$safe_url_report" 'http://localhost:5173/@vite/client'
url_finding_count=$(printf '%s' "$safe_url_report" | grep -o '"rule_id":"credential.url-auth"' | wc -l)
[[ $url_finding_count -eq 1 ]] || fail 'safe development URLs must not create URL credential findings'

# Quoted paths must still produce valid JSON metadata.
python3 -c 'import json, sys; json.load(sys.stdin)' <<< "$working_report" || fail 'JSON report is invalid for quoted paths'

# The finding limit must be explicit and return status 3.
truncated_status=0
bash "$SCANNER" --root "$TEST_ROOT/repo" --mode working-tree --format json --max-findings 1 >/dev/null || truncated_status=$?
[[ $truncated_status -eq 3 ]] || fail 'max-findings mode should return three'

# Verify the default mode reports findings without failing.
working_default_status=0
working_default_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode working-tree --format json) || working_default_status=$?
[[ $working_default_status -eq 0 ]] || fail 'default mode should return zero for findings'

# Verify the opt-in mode fails when findings are present.
working_fail_status=0
working_fail_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode working-tree --format json --fail-on-findings) || working_fail_status=$?
[[ $working_fail_status -eq 1 ]] || fail 'fail-on-findings mode should return one'

# Commit the synthetic exposure, then commit its removal.
git -C "$TEST_ROOT/repo" add README.md config
git -C "$TEST_ROOT/repo" commit -q -m initial

printf '%s\n' 'ordinary documentation' > "$TEST_ROOT/repo/config/settings.env"
git -C "$TEST_ROOT/repo" add config/settings.env
git -C "$TEST_ROOT/repo" commit -q -m cleanup

# Verify historical detection and redaction.
history_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode history --format json)
assert_contains "$history_report" '"commits_scanned":2'
assert_not_contains "$history_report" '"files_scanned"'
assert_contains "$history_report" 'git-history'
assert_contains "$history_report" 'credential.assignment'
assert_contains "$history_report" 'credential.authorization'
assert_contains "$history_report" 'credential.jwt'
assert_contains "$history_report" 'credential.url-auth'
assert_contains "$history_report" 'credential.provider-key'
assert_contains "$history_report" 'credential.private-key'
assert_contains "$history_report" 'credential.filename'
assert_not_contains "$history_report" "$fixture_value"
assert_not_contains "$history_report" 'password='

# Verify the opt-in mode also fails for historical findings.
history_fail_status=0
history_fail_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode history --format json --fail-on-findings) || history_fail_status=$?
[[ $history_fail_status -eq 1 ]] || fail 'history fail-on-findings mode should return one'

# Verify the human-readable report format.
markdown_report=$(bash "$SCANNER" --root "$TEST_ROOT/repo" --mode working-tree --format markdown)
assert_contains "$markdown_report" '# Security surface scan'
assert_not_contains "$markdown_report" "$fixture_value"

printf '%s\n' 'security surface tests passed'

#!/usr/bin/env bash

set -euo pipefail

# Set safe defaults for the scan.
ROOT="."
MODE="working-tree"
FORMAT="markdown"
MAX_FINDINGS=500
FAIL_ON_FINDINGS=0

# Keep only redacted findings and scan metadata in memory.
declare -a FINDINGS=()
declare -a WARNINGS=()
declare -A SEEN=()
FILES_SCANNED=0
COMMITS_SCANNED=0
FILES_SKIPPED=0
TRUNCATED=0

usage() {
    # Show the supported command-line options.
    cat <<'USAGE'
Usage: security-surface.sh [--root PATH] [--mode working-tree|history|full]
                          [--format markdown|json] [--max-findings N]
                          [--fail-on-findings]
USAGE
}

die() {
    # Stop without exposing repository content.
    printf '%s\n' "security-surface: scan failed safely" >&2
    exit 2
}

json_escape() {
    # Escape metadata before placing it in JSON output.
    local value=$1
    value=${value//\\/\\\\}
    value=${value//"/\\"}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    value=${value//$'\t'/\\t}
    printf '%s' "$value"
}

add_warning() {
    # Store a warning without storing matched content.
    WARNINGS+=("$1")
}

current_commit() {
    # Report the checked-out commit or an unborn repository state.
    git rev-parse --verify HEAD 2>/dev/null || printf '%s' 'unborn'
}

add_finding() {
    # Add a unique metadata-only finding.
    local source=$1 file=$2 line=$3 rule_id=$4 category=$5 severity=$6 confidence=$7 commit=${8:-}
    local key="${source}|${commit}|${file}|${line}|${rule_id}"

    [[ ${SEEN[$key]+yes} ]] && return 0
    SEEN[$key]=1

    if (( ${#FINDINGS[@]} >= MAX_FINDINGS )); then
        TRUNCATED=1
        return 0
    fi

    FINDINGS+=("$source|$file|$line|$rule_id|$category|$severity|$confidence|$commit")
}

scan_file_pattern() {
    # Search one file and keep only matching line numbers.
    local file=$1 pattern=$2 rule_id=$3 category=$4 severity=$5 confidence=$6
    local line

    while IFS= read -r line; do
        [[ $line =~ ^[0-9]+$ ]] || continue
        add_finding "working-tree" "$file" "$line" "$rule_id" "$category" "$severity" "$confidence"
    done < <(grep -nI -E -e "$pattern" -- "$file" 2>/dev/null | awk -F: '{print $1}')
}

scan_file() {
    # Scan one regular file for credential-shaped patterns.
    local file=$1

    if [[ -L $file || ! -f $file ]]; then
        FILES_SKIPPED=$((FILES_SKIPPED + 1))
        return 0
    fi

    FILES_SCANNED=$((FILES_SCANNED + 1))

    case ${file,,} in
        *.env|*.env.*|*credential*|*secret*|*token*|*.pem|*.key|*id_rsa*)
            add_finding "working-tree" "$file" 0 "credential.filename" "credential" "medium" "possible"
            ;;
    esac

    scan_file_pattern "$file" '-----BEGIN (RSA|DSA|EC|OPENSSH|PGP|[A-Z ]*PRIVATE) KEY-----' \
        "credential.private-key" "credential" "critical" "confirmed"
    scan_file_pattern "$file" '(^|[^[:alnum:]_])(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret|private[_-]?key)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_./+=:-]{8,}' \
        "credential.assignment" "credential" "high" "likely"
    scan_file_pattern "$file" '(^|[^[:alnum:]_])[Aa]uthorization[[:space:]]*:[[:space:]]*(Bearer|Basic)[[:space:]]+[A-Za-z0-9_./+=:-]{12,}' \
        "credential.authorization" "credential" "high" "likely"
    scan_file_pattern "$file" '(^|[^[:alnum:]_])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}([^A-Za-z0-9_-]|$)' \
        "credential.jwt" "credential" "high" "likely"
    scan_file_pattern "$file" '[A-Za-z][A-Za-z0-9+.-]{1,20}://[^[:space:]/:@]+:[^[:space:]@]+@' \
        "credential.url-auth" "credential" "high" "likely"
    scan_file_pattern "$file" '(^|[^A-Za-z0-9])(AKIA|ASIA)[A-Z0-9]{16}([^A-Za-z0-9]|$)' \
        "credential.provider-key" "credential" "high" "likely"
}

scan_working_tree() {
    # Scan tracked and nonignored untracked files.
    local file

    while IFS= read -r -d '' file; do
        scan_file "$file"
    done < <(git ls-files -co --exclude-standard -z)
}

scan_history_pattern() {
    # Search one commit and keep only file and line metadata.
    local commit=$1 pattern=$2 rule_id=$3 category=$4 severity=$5 confidence=$6
    local file line

    while IFS=$'\t' read -r file line; do
        [[ $line =~ ^[0-9]+$ ]] || continue
        add_finding "git-history" "$file" "$line" "$rule_id" "$category" "$severity" "$confidence" "$commit"
    done < <(git grep -nI -E -e "$pattern" "$commit" -- 2>/dev/null | awk -F: '{print $2 "\t" $3}')
}

scan_history() {
    # Scan every reachable commit in the repository history.
    local commit

    while IFS= read -r commit; do
        [[ -n $commit ]] || continue
        COMMITS_SCANNED=$((COMMITS_SCANNED + 1))
        scan_history_pattern "$commit" '-----BEGIN (RSA|DSA|EC|OPENSSH|PGP|[A-Z ]*PRIVATE) KEY-----' \
            "credential.private-key" "credential" "critical" "confirmed"
        scan_history_pattern "$commit" '(^|[^[:alnum:]_])(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret|private[_-]?key)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_./+=:-]{8,}' \
            "credential.assignment" "credential" "high" "likely"
        scan_history_pattern "$commit" '(^|[^[:alnum:]_])[Aa]uthorization[[:space:]]*:[[:space:]]*(Bearer|Basic)[[:space:]]+[A-Za-z0-9_./+=:-]{12,}' \
            "credential.authorization" "credential" "high" "likely"
        scan_history_pattern "$commit" '(^|[^[:alnum:]_])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}([^A-Za-z0-9_-]|$)' \
            "credential.jwt" "credential" "high" "likely"
        scan_history_pattern "$commit" '[A-Za-z][A-Za-z0-9+.-]{1,20}://[^[:space:]/:@]+:[^[:space:]@]+@' \
            "credential.url-auth" "credential" "high" "likely"
        scan_history_pattern "$commit" '(^|[^A-Za-z0-9])(AKIA|ASIA)[A-Z0-9]{16}([^A-Za-z0-9]|$)' \
            "credential.provider-key" "credential" "high" "likely"
    done < <(git rev-list --all)
}

emit_markdown() {
    # Print a redacted human-readable report.
    printf '%s\n\n' '# Security surface scan'
    printf '%s\n' "- mode: $MODE"
    printf '%s\n' "- commit: $(current_commit)"
    if [[ $MODE == history ]]; then
        printf '%s\n' "- commits scanned: $COMMITS_SCANNED"
    else
        printf '%s\n' "- files scanned: $FILES_SCANNED"
        if [[ $MODE == full ]]; then
            printf '%s\n' "- commits scanned: $COMMITS_SCANNED"
        fi
    fi
    printf '%s\n' "- files skipped: $FILES_SKIPPED"
    printf '%s\n' "- findings: ${#FINDINGS[@]}"
    printf '%s\n\n' "- truncated: $([[ $TRUNCATED -eq 1 ]] && printf true || printf false)"

    if ((${#WARNINGS[@]})); then
        printf '%s\n' '## Warnings'
        printf '%s\n' '- Scan warnings were recorded without including file contents.'
        printf '\n'
    fi

    printf '%s\n' '## Findings'
    if ((${#FINDINGS[@]} == 0)); then
        printf '%s\n' 'No credential candidates detected in the selected scope.'
        return 0
    fi

    local finding source file line rule category severity confidence commit
    for finding in "${FINDINGS[@]}"; do
        IFS='|' read -r source file line rule category severity confidence commit <<< "$finding"
        printf '%s\n' "- source=$source file=$file line=$line rule=$rule category=$category severity=$severity confidence=$confidence${commit:+ commit=$commit}"
    done
}

emit_json() {
    # Print a redacted machine-readable report.
    local finding source file line rule category severity confidence commit
    printf '{"mode":"%s","commit":"%s"' \
        "$(json_escape "$MODE")" "$(json_escape "$(current_commit)")"
    if [[ $MODE == history ]]; then
        printf ',"commits_scanned":%d' "$COMMITS_SCANNED"
    else
        printf ',"files_scanned":%d' "$FILES_SCANNED"
        if [[ $MODE == full ]]; then
            printf ',"commits_scanned":%d' "$COMMITS_SCANNED"
        fi
    fi
    printf ',"files_skipped":%d,"finding_count":%d,"truncated":%s,"findings":[' \
        "$FILES_SKIPPED" "${#FINDINGS[@]}" "$([[ $TRUNCATED -eq 1 ]] && printf true || printf false)"

    local first=1
    for finding in "${FINDINGS[@]}"; do
        IFS='|' read -r source file line rule category severity confidence commit <<< "$finding"
        (( first )) || printf ','
        first=0
        printf '{"source":"%s","file":"%s","line":%d,"rule_id":"%s","category":"%s","severity":"%s","confidence":"%s"' \
            "$(json_escape "$source")" "$(json_escape "$file")" "$line" "$(json_escape "$rule")" \
            "$(json_escape "$category")" "$(json_escape "$severity")" "$(json_escape "$confidence")"
        if [[ -n $commit ]]; then
            printf ',"commit":"%s"' "$(json_escape "$commit")"
        fi
        printf '}'
    done
    printf '],"warnings":['
    local first_warning=1 warning
    for warning in "${WARNINGS[@]}"; do
        (( first_warning )) || printf ','
        first_warning=0
        printf '"%s"' "$(json_escape "$warning")"
    done
    printf ']}\n'
}

# Parse command-line options before scanning.
while (($#)); do
    case $1 in
        --root) ROOT=${2:?missing value for --root}; shift 2 ;;
        --mode) MODE=${2:?missing value for --mode}; shift 2 ;;
        --format) FORMAT=${2:?missing value for --format}; shift 2 ;;
        --max-findings) MAX_FINDINGS=${2:?missing value for --max-findings}; shift 2 ;;
        --fail-on-findings) FAIL_ON_FINDINGS=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die ;;
    esac
done

[[ $MODE == working-tree || $MODE == history || $MODE == full ]] || die
[[ $FORMAT == markdown || $FORMAT == json ]] || die
[[ $MAX_FINDINGS =~ ^[1-9][0-9]*$ ]] || die

# Resolve the root and require a Git repository.
ROOT=$(cd "$ROOT" 2>/dev/null && pwd) || die
cd "$ROOT" || die
git rev-parse --show-toplevel >/dev/null 2>&1 || die

# Run the selected scan mode.
case $MODE in
    working-tree) scan_working_tree ;;
    history) scan_history ;;
    full) scan_working_tree; scan_history ;;
esac

if (( TRUNCATED )); then
    add_warning "finding limit reached"
fi
if (( FILES_SKIPPED > 0 )); then
    add_warning "some files were skipped because they were not regular readable files"
fi

case $FORMAT in
    markdown) emit_markdown ;;
    json) emit_json ;;
esac

if (( TRUNCATED )); then
    exit 3
fi

if (( FAIL_ON_FINDINGS && ${#FINDINGS[@]} > 0 )); then
    exit 1
fi

exit 0

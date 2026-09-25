#!/usr/bin/env bash
# Canonical scanner for the AI Data Compass security-audit skill.

set -euo pipefail

# Set safe defaults for the scan.
ROOT="."
MODE="working-tree"
FORMAT="markdown"
MAX_FINDINGS=500
FAIL_ON_FINDINGS=0

# Keep only redacted findings and scan metadata in memory.
declare -a FINDINGS=()
declare -a FINDING_SOURCE=()
declare -a FINDING_FILE=()
declare -a FINDING_LINE=()
declare -a FINDING_RULE=()
declare -a FINDING_CATEGORY=()
declare -a FINDING_SEVERITY=()
declare -a FINDING_CONFIDENCE=()
declare -a FINDING_COMMIT=()
declare -a WARNINGS=()
declare -A SEEN=()
FILES_SCANNED=0
COMMITS_SCANNED=0
FILES_SKIPPED=0
TRUNCATED=0
SCAN_INCOMPLETE=0
INCOMPLETE_WARNING=0
SCAN_SOURCE="working-tree"
TEMP_DIRECTORY=""

usage() {
    # Show the supported command-line options.
    cat <<'USAGE'
Usage: security-surface.sh [--root PATH] [--mode working-tree|filesystem|history|full]
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
    value=${value//\"/\\\"}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    value=${value//$'\t'/\\t}
    printf '%s' "$value"
}

add_warning() {
    # Store a warning without storing matched content.
    WARNINGS+=("$1")
}

cleanup_temporary_directory() {
    if [[ -n $TEMP_DIRECTORY ]]; then
        rm -rf -- "$TEMP_DIRECTORY"
    fi
}

current_commit() {
    # Report the checked-out commit or an unborn repository state.
    git rev-parse --verify HEAD 2>/dev/null || printf '%s' 'unborn'
}

add_finding() {
    # Add a unique metadata-only finding.
    local source=$1 file=$2 line=$3 rule_id=$4 category=$5 severity=$6 confidence=$7 commit=${8:-}
    if (( ${#FINDINGS[@]} >= MAX_FINDINGS )); then
        TRUNCATED=1
        return 0
    fi

    local key="${source}"$'\x1f'"${commit}"$'\x1f'"${file}"$'\x1f'"${line}"$'\x1f'"${rule_id}"

    [[ ${SEEN[$key]+yes} ]] && return 0
    SEEN[$key]=1

    local index=${#FINDINGS[@]}
    FINDINGS+=("$index")
    FINDING_SOURCE+=("$source")
    FINDING_FILE+=("$file")
    FINDING_LINE+=("$line")
    FINDING_RULE+=("$rule_id")
    FINDING_CATEGORY+=("$category")
    FINDING_SEVERITY+=("$severity")
    FINDING_CONFIDENCE+=("$confidence")
    FINDING_COMMIT+=("$commit")
}

scan_file_pattern() {
    # Search one file and keep only matching line numbers.
    local file=$1 pattern=$2 rule_id=$3 category=$4 severity=$5 confidence=$6
    local line

    while IFS= read -r line; do
        [[ $line =~ ^[0-9]+$ ]] || continue
        add_finding "$SCAN_SOURCE" "$file" "$line" "$rule_id" "$category" "$severity" "$confidence"
    done < <(grep -nI -E -e "$pattern" -- "$file" 2>/dev/null | awk -F: '{print $1}')
}

scan_file() {
    # Scan one regular file for credential-shaped patterns.
    local file=$1

    if [[ -L $file || ! -f $file ]]; then
        FILES_SKIPPED=$((FILES_SKIPPED + 1))
        return 0
    fi

    if [[ ! -r $file ]]; then
        FILES_SKIPPED=$((FILES_SKIPPED + 1))
        SCAN_INCOMPLETE=1
        if (( ! INCOMPLETE_WARNING )); then
            add_warning "some filesystem entries could not be read or enumerated"
            INCOMPLETE_WARNING=1
        fi
        return 0
    fi

    FILES_SCANNED=$((FILES_SCANNED + 1))

    case ${file,,} in
        *.env|*.env.*|*credential*|*secret*|*token*|*.pem|*.key|*id_rsa*)
            add_finding "$SCAN_SOURCE" "$file" 0 "credential.filename" "credential" "medium" "possible"
            ;;
    esac

    scan_file_pattern "$file" "$PRIVATE_KEY_PATTERN" \
        "credential.private-key" "credential" "critical" "confirmed"
    scan_file_pattern "$file" "$ASSIGNMENT_PATTERN" \
        "credential.assignment" "credential" "high" "likely"
    scan_file_pattern "$file" "$AUTHORIZATION_PATTERN" \
        "credential.authorization" "credential" "high" "likely"
    scan_file_pattern "$file" "$JWT_PATTERN" \
        "credential.jwt" "credential" "high" "likely"
    scan_file_pattern "$file" "$URL_AUTH_PATTERN" \
        "credential.url-auth" "credential" "high" "likely"
    scan_file_pattern "$file" "$PROVIDER_KEY_PATTERN" \
        "credential.provider-key" "credential" "high" "likely"
}

scan_working_tree() {
    # Scan tracked and nonignored untracked files.
    local file

    while IFS= read -r -d '' file; do
        scan_file "$file"
    done < <(git ls-files -co --exclude-standard -z)
}

scan_filesystem() {
    # Scan local files without consulting Git or following symlinks.
    local relative_temporary_path candidate file
    local -a find_exclusions=()

    TEMP_DIRECTORY=$(mktemp -d) || die
    trap cleanup_temporary_directory EXIT
    local file_list="$TEMP_DIRECTORY/files"
    local error_file="$TEMP_DIRECTORY/errors"
    : > "$file_list" || die
    : > "$error_file" || die
    if [[ $ROOT == "/" && $TEMP_DIRECTORY == /* ]]; then
        relative_temporary_path=${TEMP_DIRECTORY#/}
        find_exclusions=(-path "./$relative_temporary_path" -prune -o)
    elif [[ $TEMP_DIRECTORY == "$ROOT/"* ]]; then
        relative_temporary_path=${TEMP_DIRECTORY#"$ROOT/"}
        find_exclusions=(-path "./$relative_temporary_path" -prune -o)
    fi

    if ! find . "${find_exclusions[@]}" -name .git -prune -o \
        \( -type f -o -type l \) -print0 > "$file_list" 2> "$error_file"; then
        SCAN_INCOMPLETE=1
    fi
    if [[ -s $error_file ]]; then
        SCAN_INCOMPLETE=1
    fi
    if (( SCAN_INCOMPLETE && ! INCOMPLETE_WARNING )); then
        add_warning "some filesystem entries could not be read or enumerated"
        INCOMPLETE_WARNING=1
    fi

    SCAN_SOURCE="filesystem"
    while IFS= read -r -d '' candidate; do
        file=${candidate#./}
        scan_file "$file"
    done < "$file_list"
}

scan_history() {
    # Scan every reachable commit in the repository history.
    local commit prefix file line content

    while IFS= read -r commit; do
        [[ -n $commit ]] || continue
        COMMITS_SCANNED=$((COMMITS_SCANNED + 1))
        while IFS= read -r -d '' prefix && IFS= read -r -d '' line; do
            IFS= read -r content || true
            [[ $line =~ ^[0-9]+$ ]] || continue
            file=${prefix:41}
            [[ -n $file ]] || continue
            [[ $content =~ $PRIVATE_KEY_PATTERN ]] && add_finding "git-history" "$file" "$line" "credential.private-key" "credential" "critical" "confirmed" "$commit"
            [[ $content =~ $ASSIGNMENT_PATTERN ]] && add_finding "git-history" "$file" "$line" "credential.assignment" "credential" "high" "likely" "$commit"
            [[ $content =~ $AUTHORIZATION_PATTERN ]] && add_finding "git-history" "$file" "$line" "credential.authorization" "credential" "high" "likely" "$commit"
            [[ $content =~ $JWT_PATTERN ]] && add_finding "git-history" "$file" "$line" "credential.jwt" "credential" "high" "likely" "$commit"
            [[ $content =~ $URL_AUTH_PATTERN ]] && add_finding "git-history" "$file" "$line" "credential.url-auth" "credential" "high" "likely" "$commit"
            [[ $content =~ $PROVIDER_KEY_PATTERN ]] && add_finding "git-history" "$file" "$line" "credential.provider-key" "credential" "high" "likely" "$commit"
        done < <(git grep -nI -z -E -e "$HISTORY_PATTERN" "$commit" -- 2>/dev/null)

        while IFS= read -r -d '' file; do
            case ${file,,} in
                *.env|*.env.*|*credential*|*secret*|*token*|*.pem|*.key|*id_rsa*)
                    add_finding "git-history" "$file" 0 "credential.filename" "credential" "medium" "possible" "$commit"
                    ;;
            esac
        done < <(git ls-tree -r --name-only -z "$commit" 2>/dev/null)
    done < <(git rev-list --all)
}

emit_markdown() {
    # Print a redacted human-readable report.
    printf '%s\n\n' '# Security surface scan'
    printf '%s\n' "- mode: $MODE"
    if [[ $MODE == filesystem ]]; then
        printf '%s\n' '- commit: not applicable (filesystem scan)'
    else
        printf '%s\n' "- commit: $(current_commit)"
    fi
    if [[ $MODE == history ]]; then
        printf '%s\n' "- commits scanned: $COMMITS_SCANNED"
    else
        printf '%s\n' "- files scanned: $FILES_SCANNED"
        if [[ $MODE == full ]]; then
            printf '%s\n' "- commits scanned: $COMMITS_SCANNED"
        fi
    fi
    printf '%s\n' "- files skipped: $FILES_SKIPPED"
    printf '%s\n' "- complete: $([[ $SCAN_INCOMPLETE -eq 0 ]] && printf true || printf false)"
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

    local index display_file
    for index in "${!FINDINGS[@]}"; do
        display_file=$(printf '%q' "${FINDING_FILE[$index]}")
        printf '%s\n' "- source=${FINDING_SOURCE[$index]} file=${display_file} line=${FINDING_LINE[$index]} rule=${FINDING_RULE[$index]} category=${FINDING_CATEGORY[$index]} severity=${FINDING_SEVERITY[$index]} confidence=${FINDING_CONFIDENCE[$index]}${FINDING_COMMIT[$index]:+ commit=${FINDING_COMMIT[$index]}}"
    done
}

emit_json() {
    # Print a redacted machine-readable report.
    if [[ $MODE == filesystem ]]; then
        printf '{"mode":"%s","commit":null' "$(json_escape "$MODE")"
    else
        printf '{"mode":"%s","commit":"%s"' \
            "$(json_escape "$MODE")" "$(json_escape "$(current_commit)")"
    fi
    if [[ $MODE == history ]]; then
        printf ',"commits_scanned":%d' "$COMMITS_SCANNED"
    else
        printf ',"files_scanned":%d' "$FILES_SCANNED"
        if [[ $MODE == full ]]; then
            printf ',"commits_scanned":%d' "$COMMITS_SCANNED"
        fi
    fi
    printf ',"files_skipped":%d,"complete":%s,"finding_count":%d,"truncated":%s,"findings":[' \
        "$FILES_SKIPPED" "$([[ $SCAN_INCOMPLETE -eq 0 ]] && printf true || printf false)" \
        "${#FINDINGS[@]}" "$([[ $TRUNCATED -eq 1 ]] && printf true || printf false)"

    local first=1
    local index
    for index in "${!FINDINGS[@]}"; do
        (( first )) || printf ','
        first=0
        printf '{"source":"%s","file":"%s","line":%d,"rule_id":"%s","category":"%s","severity":"%s","confidence":"%s"' \
            "$(json_escape "${FINDING_SOURCE[$index]}")" "$(json_escape "${FINDING_FILE[$index]}")" "${FINDING_LINE[$index]}" "$(json_escape "${FINDING_RULE[$index]}")" \
            "$(json_escape "${FINDING_CATEGORY[$index]}")" "$(json_escape "${FINDING_SEVERITY[$index]}")" "$(json_escape "${FINDING_CONFIDENCE[$index]}")"
        if [[ -n ${FINDING_COMMIT[$index]} ]]; then
            printf ',"commit":"%s"' "$(json_escape "${FINDING_COMMIT[$index]}")"
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
PRIVATE_KEY_PATTERN='-----BEGIN (RSA|DSA|EC|OPENSSH|PGP|[A-Z ]*PRIVATE) KEY-----'
ASSIGNMENT_PATTERN="(^|[^[:alnum:]_])[\"']?(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret|private[_-]?key)[\"']?[[:space:]]*[:=][[:space:]]*[\"']?[A-Za-z0-9_./+=:-]{8,}[\"']?"
AUTHORIZATION_PATTERN='(^|[^[:alnum:]_])[Aa]uthorization[[:space:]]*:[[:space:]]*(Bearer|Basic)[[:space:]]+[A-Za-z0-9_./+=:-]{12,}'
JWT_PATTERN='(^|[^[:alnum:]_])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}([^A-Za-z0-9_-]|$)'
URL_AUTH_PATTERN='[A-Za-z][A-Za-z0-9+.-]{1,20}://[^[:space:]/:@]+:[^[:space:]/:@]+@'
PROVIDER_KEY_PATTERN='(^|[^A-Za-z0-9])(AKIA|ASIA)[A-Z0-9]{16}([^A-Za-z0-9]|$)'
HISTORY_PATTERN="(${PRIVATE_KEY_PATTERN}|${ASSIGNMENT_PATTERN}|${AUTHORIZATION_PATTERN}|${JWT_PATTERN}|${URL_AUTH_PATTERN}|${PROVIDER_KEY_PATTERN})"

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

[[ $MODE == working-tree || $MODE == filesystem || $MODE == history || $MODE == full ]] || die
[[ $FORMAT == markdown || $FORMAT == json ]] || die
[[ $MAX_FINDINGS =~ ^[1-9][0-9]*$ ]] || die

# Resolve the root and require Git only for Git-backed scan modes.
ROOT=$(cd "$ROOT" 2>/dev/null && pwd -P) || die
[[ -d $ROOT ]] || die
cd "$ROOT" || die
if [[ $MODE != filesystem ]]; then
    git rev-parse --show-toplevel >/dev/null 2>&1 || die
fi

# Run the selected scan mode.
case $MODE in
    working-tree) scan_working_tree ;;
    filesystem) scan_filesystem ;;
    history) scan_history ;;
    full) scan_working_tree; scan_history ;;
esac

if (( TRUNCATED )); then
    add_warning "finding limit reached"
fi
if (( FILES_SKIPPED > 0 )) && (( ! INCOMPLETE_WARNING )); then
    add_warning "some non-regular files or symlinks were skipped"
fi

case $FORMAT in
    markdown) emit_markdown ;;
    json) emit_json ;;
esac

if (( TRUNCATED )); then
    exit 3
fi

if (( SCAN_INCOMPLETE )); then
    exit 2
fi

if (( FAIL_ON_FINDINGS && ${#FINDINGS[@]} > 0 )); then
    exit 1
fi

exit 0

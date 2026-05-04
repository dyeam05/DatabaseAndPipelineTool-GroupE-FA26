#!/usr/bin/env bash
# Diagnose (and optionally heal) CVAT when the UI is stuck loading.
# Run from the repo root:
#   bash cvat_worker/debug_cvat.sh           # diagnose only
#   bash cvat_worker/debug_cvat.sh --heal    # diagnose + restart unhealthy containers
#
# Prints:
#   1. Container status (running / healthy / restarting / exited) for every CVAT service.
#   2. HTTP probes against traefik → UI and traefik → API.
#   3. Internal pings to Redis, kvrocks, and Postgres.
#   4. Filtered error tails + unfiltered log tail for containers flagged unhealthy.
#   5. (--heal) Restarts unhealthy containers in dependency order, then re-probes the API.

# Intentionally no `set -e`: every probe should run even if an earlier one failed.

HEAL=0
for arg in "$@"; do
    case "$arg" in
        --heal|--fix) HEAL=1 ;;
        -h|--help)   sed -n '2,11p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *)           echo "Unknown argument: $arg (use --heal or --help)" >&2; exit 2 ;;
    esac
done

CRITICAL=(traefik cvat_ui cvat_server cvat_opa cvat_redis_inmem cvat_redis_ondisk cvat_db)
WORKERS=(cvat_worker_import cvat_worker_export cvat_worker_annotation cvat_worker_webhooks
         cvat_worker_quality_reports cvat_worker_chunks cvat_worker_consensus cvat_worker_utils)
ALL=("${CRITICAL[@]}" "${WORKERS[@]}" cvat_clickhouse cvat_vector)

BOLD=$'\033[1m'; RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; DIM=$'\033[2m'; OFF=$'\033[0m'
UNHEALTHY=()

section() { printf "\n${BOLD}== %s ==${OFF}\n" "$1"; }

inspect_state() {
    # Returns "running/healthy", "running/unhealthy", "restarting/-", "exited/-", or "missing/-"
    local name=$1
    local state health
    state=$(docker inspect --format '{{.State.Status}}' "$name" 2>/dev/null) || { echo "missing/-"; return; }
    health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}' "$name" 2>/dev/null)
    echo "${state}/${health}"
}

mark_unhealthy() {
    local name=$1
    for u in "${UNHEALTHY[@]}"; do [[ "$u" == "$name" ]] && return; done
    UNHEALTHY+=("$name")
}

# ─── 1. Container status table ────────────────────────────────────────────────
section "Container status"
printf "%-32s %s\n" "CONTAINER" "STATE/HEALTH"
for c in "${ALL[@]}"; do
    s=$(inspect_state "$c")
    color=$GREEN
    case "$s" in
        running/healthy|running/-) color=$GREEN ;;
        running/starting)          color=$YELLOW; mark_unhealthy "$c" ;;
        running/unhealthy)         color=$RED;    mark_unhealthy "$c" ;;
        restarting/*)              color=$RED;    mark_unhealthy "$c" ;;
        exited/*|missing/*)        color=$RED;    mark_unhealthy "$c" ;;
        *)                         color=$YELLOW; mark_unhealthy "$c" ;;
    esac
    printf "%-32s ${color}%s${OFF}\n" "$c" "$s"
done

# ─── 2. HTTP probes via traefik ───────────────────────────────────────────────
section "HTTP probes (localhost:8080)"
probe_http() {
    local label=$1 url=$2 expected=$3
    local code
    code=$(curl -fsS -o /dev/null -m 5 -w "%{http_code}" "$url" 2>/dev/null)
    local rc=$?
    if [[ $rc -ne 0 ]]; then
        printf "  ${RED}FAIL${OFF} %-28s %s ${DIM}(curl exit %d — hung or refused)${OFF}\n" "$label" "$url" "$rc"
        return 1
    fi
    if [[ -n "$expected" && "$code" != "$expected" ]]; then
        printf "  ${YELLOW}WARN${OFF} %-28s %s ${DIM}(got %s, expected %s)${OFF}\n" "$label" "$url" "$code" "$expected"
        return 1
    fi
    printf "  ${GREEN}OK${OFF}   %-28s %s ${DIM}(%s)${OFF}\n" "$label" "$url" "$code"
    return 0
}
probe_http "UI root"       "http://localhost:8080/"                ""     || mark_unhealthy "cvat_ui"
probe_http "API /server/about" "http://localhost:8080/api/server/about" "200"  || mark_unhealthy "cvat_server"
probe_http "API /schema"       "http://localhost:8080/api/schema/?format=openapi" "200" || mark_unhealthy "cvat_server"

# ─── 3. Internal service pings ────────────────────────────────────────────────
section "Internal service pings"
check_exec() {
    local label=$1 container=$2; shift 2
    local out
    out=$(docker exec "$container" "$@" 2>&1)
    if [[ $? -eq 0 ]]; then
        printf "  ${GREEN}OK${OFF}   %-28s ${DIM}%s${OFF}\n" "$label" "$(echo "$out" | head -1)"
    else
        printf "  ${RED}FAIL${OFF} %-28s ${DIM}%s${OFF}\n" "$label" "$(echo "$out" | head -1)"
        mark_unhealthy "$container"
    fi
}
# OPA's image is distroless (no shell, no wget) — the container status table above covers it.
check_exec "Redis inmem PING"    cvat_redis_inmem  redis-cli ping
check_exec "Kvrocks PING"        cvat_redis_ondisk redis-cli -p 6666 ping
check_exec "Postgres ready"      cvat_db           pg_isready -U root -d cvat
check_exec "cvat_server Django"  cvat_server       python manage.py check --deploy --fail-level ERROR

# ─── 4. Error tails from unhealthy containers ─────────────────────────────────
if [[ ${#UNHEALTHY[@]} -eq 0 ]]; then
    section "Summary"
    printf "  ${GREEN}All checks passed.${OFF} If the UI is still hanging, hard-reload the browser (Ctrl+Shift+R)\n"
    printf "  to clear cached JS, and check the browser devtools Network tab for pending requests.\n"
    exit 0
fi

section "Error tails for unhealthy containers"
for c in "${UNHEALTHY[@]}"; do
    printf "\n${BOLD}--- %s ---${OFF}\n" "$c"
    if ! docker inspect "$c" >/dev/null 2>&1; then
        printf "  ${DIM}container does not exist — run setup_cvat.sh${OFF}\n"
        continue
    fi
    filtered=$(docker logs --tail 200 "$c" 2>&1 \
        | grep -iE "error|exception|traceback|fatal|refused|timeout|denied|unhealthy" \
        | tail -30)
    if [[ -n "$filtered" ]]; then
        printf "  ${DIM}(filtered)${OFF}\n"
        echo "$filtered" | sed 's/^/  /'
    fi
    # Startup messages on these containers often don't match the error grep — dump raw tail too.
    case "$c" in
        cvat_server|cvat_ui|traefik)
            printf "  ${DIM}(last 30 lines, unfiltered)${OFF}\n"
            docker logs --tail 30 "$c" 2>&1 | sed 's/^/  /'
            ;;
    esac
done

# ─── 5. Heal (optional) ───────────────────────────────────────────────────────
if [[ "$HEAL" == "1" ]]; then
    section "Healing"

    # Dependency order: infra → server → ui/edge → workers. cvat_server depends
    # on db/redis/opa and caches them at boot, so anything that restarts them
    # must also restart cvat_server.
    RESTART_ORDER=(cvat_db cvat_redis_inmem cvat_redis_ondisk cvat_opa
                   cvat_clickhouse cvat_vector
                   cvat_server cvat_ui traefik "${WORKERS[@]}")

    # Intersect UNHEALTHY with RESTART_ORDER to preserve dependency order.
    TO_RESTART=()
    for c in "${RESTART_ORDER[@]}"; do
        for u in "${UNHEALTHY[@]}"; do
            [[ "$u" == "$c" ]] && TO_RESTART+=("$c") && break
        done
    done

    # If any cvat_server dependency is being restarted, restart cvat_server too.
    needs_server=0
    for c in "${TO_RESTART[@]}"; do
        case "$c" in
            cvat_db|cvat_redis_inmem|cvat_redis_ondisk|cvat_opa) needs_server=1 ;;
        esac
    done
    if [[ $needs_server -eq 1 ]]; then
        has_server=0
        for r in "${TO_RESTART[@]}"; do [[ "$r" == "cvat_server" ]] && has_server=1 && break; done
        [[ $has_server -eq 0 ]] && TO_RESTART+=(cvat_server)
    fi

    if [[ ${#TO_RESTART[@]} -eq 0 ]]; then
        printf "  ${YELLOW}Nothing to restart (no recoverable containers flagged).${OFF}\n"
        exit 0
    fi

    printf "  Restart order: ${BOLD}%s${OFF}\n\n" "${TO_RESTART[*]}"
    for c in "${TO_RESTART[@]}"; do
        if ! docker inspect "$c" >/dev/null 2>&1; then
            printf "  ${YELLOW}skip${OFF}      %s ${DIM}(container missing — run setup_cvat.sh)${OFF}\n" "$c"
            continue
        fi
        printf "  ${DIM}→ restarting %-28s${OFF} " "$c"
        if docker restart "$c" >/dev/null 2>&1; then
            printf "${GREEN}done${OFF}\n"
        else
            printf "${RED}FAILED${OFF}\n"
        fi
    done

    printf "\n  Waiting for CVAT API to come back up (up to 60s)...\n"
    up=0
    for i in $(seq 1 20); do
        code=$(curl -fsS -o /dev/null -m 3 -w "%{http_code}" \
            http://localhost:8080/api/server/about 2>/dev/null)
        if [[ "$code" == "200" ]]; then
            printf "  ${GREEN}CVAT API is back up (after ~%ds).${OFF}\n" "$((i*3))"
            up=1
            break
        fi
        sleep 3
    done
    if [[ $up -eq 0 ]]; then
        printf "  ${RED}CVAT API still not responding after restart.${OFF}\n"
        printf "  Run ${BOLD}docker logs --tail 60 cvat_server${OFF} and investigate manually.\n"
        exit 1
    fi
    exit 0
fi

section "Summary"
printf "  ${RED}Unhealthy:${OFF} %s\n" "${UNHEALTHY[*]}"
printf "  Re-run with ${BOLD}--heal${OFF} to restart flagged containers in dependency order.\n"
cat <<EOF

Likely next step based on what failed:
  - cvat_opa unreachable        → ${BOLD}docker restart cvat_opa cvat_server${OFF} (server caches OPA at boot)
  - cvat_redis_inmem/ondisk     → ${BOLD}docker restart cvat_redis_inmem cvat_redis_ondisk cvat_server${OFF}
  - cvat_db not ready           → check disk space, then ${BOLD}docker restart cvat_db cvat_server${OFF}
  - traefik missing/failing     → ${BOLD}docker compose -f cvat/docker-compose.yml -f docker-compose.cvat.yml up -d traefik${OFF}
  - cvat_server healthy but API hangs → usually OPA or a worker queue; check cvat_worker_utils logs
EOF

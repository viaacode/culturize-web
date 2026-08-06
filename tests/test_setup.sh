#!/usr/bin/env bash
# Tests for setup.sh — exercises every prompt path in a temp directory.
# Also validates that the generated .env files supply everything the
# containers need to start (via docker compose config if available,
# otherwise via Python YAML + key presence checks).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
TMP=""

pass() { echo "  PASS: $1"; PASS=$(( PASS + 1 )); }
fail() { echo "  FAIL: $1"; FAIL=$(( FAIL + 1 )); }

cleanup() { [[ -n "$TMP" ]] && rm -rf "$TMP"; }
trap cleanup EXIT

TMP="$(mktemp -d)"
cp -r "${ROOT_DIR}/." "$TMP/"
cd "$TMP"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# run_setup <answer1> <answer2> ...
# Each argument is one interactive prompt answer, piped to setup.sh in order.
run_setup() {
  local input=""
  for line in "$@"; do input+="${line}\n"; done
  printf "%b" "$input" | bash setup.sh &>/dev/null
}

check_file_exists() {
  [[ -f "$1" ]] && pass "$1 created" || fail "$1 not created"
}

check_file_absent() {
  [[ ! -f "$1" ]] && pass "$1 correctly absent" || fail "$1 should not exist"
}

check_var() {
  local file="$1" var="$2" pattern="$3"
  if grep -qE "^${var}=${pattern}" "$file" 2>/dev/null; then
    pass "${file}: ${var} = '${pattern}'"
  else
    local actual
    actual=$(grep "^${var}=" "$file" 2>/dev/null || echo "(not found)")
    fail "${file}: expected ${var}='${pattern}' — got: ${actual}"
  fi
}

check_var_absent() {
  local file="$1" var="$2"
  if grep -qE "^${var}=" "$file" 2>/dev/null; then
    local val
    val=$(grep "^${var}=" "$file" | cut -d= -f2-)
    fail "${file}: ${var} should be absent (got '${val}')"
  else
    pass "${file}: ${var} correctly absent"
  fi
}

# ---------------------------------------------------------------------------
# Django venv — created once, reused by every validate_django_check call.
# ---------------------------------------------------------------------------
DJANGO_PYTHON="${ROOT_DIR}/app/venv/bin/python"

setup_django_venv() {
  local app_dir="${ROOT_DIR}/app"
  local venv_dir="${app_dir}/venv"
  local req="${app_dir}/requirements.txt"

  echo ""
  echo "--- Setting up Django venv ---"

  if [[ ! -d "$venv_dir" ]]; then
    if ! python3 -m venv "$venv_dir" 2>&1; then
      fail "could not create venv at ${venv_dir}"
      DJANGO_PYTHON=""
      return
    fi
  fi

  if ! "${venv_dir}/bin/pip" install -q -r "$req" 2>&1; then
    fail "pip install -r requirements.txt failed"
    DJANGO_PYTHON=""
    return
  fi

  local django_ver
  django_ver=$("${venv_dir}/bin/python" -c 'import django; print(django.__version__)')
  echo "  venv ready (Django ${django_ver})"
}

setup_django_venv

# Run Django's system check framework against the generated .env.web.
# manage.py check validates settings (backend importable, SECRET_KEY, ALLOWED_HOSTS,
# installed apps, middleware, etc.) without opening a database connection.
validate_django_check() {
  if [[ -z "${DJANGO_PYTHON:-}" || ! -x "$DJANGO_PYTHON" ]]; then
    echo "  SKIP: Django check skipped — venv unavailable"
    return
  fi

  local env_file
  env_file="$(pwd)/.env.web"

  local output
  if output=$(
    # Parse .env.web line-by-line so values containing spaces (cron expressions,
    # email subjects) are exported correctly without shell word-splitting.
    while IFS='=' read -r key value; do
      [[ -z "$key" || "$key" == \#* ]] && continue
      export "$key=$value"
    done < "$env_file"
    cd "${ROOT_DIR}/app" && "$DJANGO_PYTHON" manage.py check 2>&1
  ); then
    pass "manage.py check passed (settings accepted by Django)"
  else
    fail "manage.py check failed — .env.web values rejected by Django"
    echo "$output" | sed 's/^/    /'
  fi
}

# Validate that .env.web contains every variable the web/celery/beat containers require.
validate_env_web() {
  check_var ".env.web" "DEBUG" "[01]"
  check_var ".env.web" "SECRET_KEY" ".{10,}"
  check_var ".env.web" "DJANGO_ALLOWED_HOSTS" ".+"
  check_var ".env.web" "SQL_ENGINE" "django\.db\.backends\.postgresql"
  check_var ".env.web" "SQL_DATABASE" "culturize"
  check_var ".env.web" "SQL_USER" "culturize"
  check_var ".env.web" "SQL_PASSWORD" ".{8,}"
  check_var ".env.web" "SQL_HOST" "db"
  check_var ".env.web" "SQL_PORT" "5432"
  check_var ".env.web" "DATABASE" "postgres"
}

# Validate .env.db and that its password matches .env.web.
validate_env_db() {
  check_var ".env.db" "POSTGRES_USER" "culturize"
  check_var ".env.db" "POSTGRES_DB" "culturize"
  check_var ".env.db" "POSTGRES_PASSWORD" ".{8,}"

  local web_pw db_pw
  web_pw=$(grep "^SQL_PASSWORD=" .env.web | cut -d= -f2-)
  db_pw=$(grep "^POSTGRES_PASSWORD=" .env.db | cut -d= -f2-)
  [[ "$web_pw" == "$db_pw" ]] \
    && pass ".env.web SQL_PASSWORD matches .env.db POSTGRES_PASSWORD" \
    || fail "password mismatch: web='${web_pw}' db='${db_pw}'"
}

# Validate the generated docker-compose.yml using 'docker compose config' when
# available — this confirms env_file references resolve and YAML is valid.
# Falls back to Python YAML-only check when Docker is not present.
validate_compose_config() {
  if docker compose config --quiet 2>/dev/null; then
    pass "docker compose config validates (env files resolve)"
  elif docker-compose config --quiet 2>/dev/null; then
    pass "docker-compose config validates (env files resolve)"
  else
    if python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" 2>/dev/null; then
      pass "docker-compose.yml is valid YAML"
    else
      fail "docker-compose.yml is invalid YAML"
    fi
  fi
}

reset_env() {
  rm -f .env.web .env.db docker-compose.yml .env.nginx app/culturizeweb/accesskey
}

# ---------------------------------------------------------------------------
# Test 1: nginx mode — explicit API key — no monitoring
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 1: nginx mode, explicit key, no monitoring ==="

# Prompts: api_key  domain  swag  checker
run_setup "myapikey123" "test.example.com" "n" "n"

check_file_exists ".env.web"
check_file_exists ".env.db"
check_file_exists "docker-compose.yml"
check_file_exists "app/culturizeweb/accesskey"
check_file_absent ".env.nginx"

validate_env_web
validate_env_db
validate_compose_config

check_var ".env.web" "DJANGO_ALLOWED_HOSTS" "test\.example\.com"
validate_django_check

grep -q "^myapikey123$" app/culturizeweb/accesskey \
  && pass "accesskey stored verbatim" \
  || fail "accesskey has wrong content"

grep -q "127.0.0.1" docker-compose.yml \
  && pass "docker-compose.yml is nginx variant (127.0.0.1 bind)" \
  || fail "docker-compose.yml should be nginx variant"

check_var_absent ".env.web" "URL_MONITORING_ENABLED"

# ---------------------------------------------------------------------------
# Test 2: auto-generated API key
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 2: auto-generated API key ==="
reset_env

run_setup "" "auto.example.com" "n" "n"

check_file_exists "app/culturizeweb/accesskey"
key_len=$(wc -c < app/culturizeweb/accesskey | tr -d ' \n')
[[ "$key_len" -ge 10 ]] \
  && pass "auto-generated key length ≥10 (got ${key_len})" \
  || fail "auto-generated key too short (len=${key_len})"

validate_env_web
validate_env_db
validate_compose_config

# ---------------------------------------------------------------------------
# Test 3: SWAG (HTTPS) mode — no monitoring
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 3: SWAG (HTTPS) mode ==="
reset_env

run_setup "swagkey" "swag.example.com" "y" "n"

check_file_exists ".env.nginx"
check_file_exists ".env.web"
check_file_exists ".env.db"

check_var ".env.nginx" "VALIDATION" "http"
check_var ".env.nginx" "URL" "swag\.example\.com"
check_var ".env.nginx" "SUBDOMAINS" "www"

if grep -q "127.0.0.1" docker-compose.yml 2>/dev/null; then
  fail "SWAG docker-compose.yml should not bind to 127.0.0.1"
else
  pass "docker-compose.yml is SWAG variant (no 127.0.0.1 bind)"
fi

grep -q "443" docker-compose.yml \
  && pass "SWAG docker-compose.yml exposes port 443" \
  || fail "SWAG docker-compose.yml should expose port 443"

validate_env_web
validate_env_db
validate_django_check
validate_compose_config

# ---------------------------------------------------------------------------
# Test 4: monitoring — default frequency and rate — no reporting
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 4: monitoring, defaults, no reporting ==="
reset_env

# Prompts after checker=y: [freq] [rate] reporting
run_setup "monitorkey" "monitor.example.com" "n" "y" "" "" "n"

check_var ".env.web" "URL_MONITORING_ENABLED" "true"
check_var ".env.web" "URL_MONITORING_FREQUENCY" "1 1 \* \* \*"
check_var ".env.web" "URL_MONITORING_RATE_LIMIT" "10"
check_var_absent ".env.web" "URL_MONITORING_REPORTING_ENABLED"
check_var_absent ".env.web" "EMAIL_HOST"

validate_django_check
validate_compose_config

# ---------------------------------------------------------------------------
# Test 5: monitoring — custom frequency and rate — no reporting
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 5: monitoring, custom frequency/rate, no reporting ==="
reset_env

run_setup "customkey" "custom.example.com" "n" "y" "0 */6 * * *" "20" "n"

check_var ".env.web" "URL_MONITORING_ENABLED" "true"
check_var ".env.web" "URL_MONITORING_FREQUENCY" "0 \*/6 \* \* \*"
check_var ".env.web" "URL_MONITORING_RATE_LIMIT" "20"
check_var_absent ".env.web" "URL_MONITORING_REPORTING_ENABLED"

validate_compose_config

# ---------------------------------------------------------------------------
# Test 6: monitoring with email reporting — default subject
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 6: monitoring with email reporting, default subject ==="
reset_env

# Prompts after reporting=y: [subject] email_host email_user email_password email_port
run_setup "reportkey" "report.example.com" "n" "y" "" "" "y" "" "smtp.example.com" "noreply@example.com" "s3cr3t" "587"

check_var ".env.web" "URL_MONITORING_ENABLED" "true"
check_var ".env.web" "URL_MONITORING_REPORTING_ENABLED" "true"
check_var ".env.web" "URL_MONITORING_REPORTING_EMAIL_SUBJECT" "report\.example\.com"
check_var ".env.web" "EMAIL_HOST" "smtp\.example\.com"
check_var ".env.web" "EMAIL_HOST_USER" "noreply@example\.com"
check_var ".env.web" "EMAIL_HOST_PASSWORD" "s3cr3t"
check_var ".env.web" "EMAIL_PORT" "587"

validate_django_check
validate_compose_config

# ---------------------------------------------------------------------------
# Test 7: monitoring with email reporting — custom subject
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 7: monitoring with email reporting, custom subject ==="
reset_env

run_setup "subjectkey" "subject.example.com" "n" "y" "" "" "y" "My custom subject" "smtp.example.com" "user@example.com" "pass123" "25"

check_var ".env.web" "URL_MONITORING_REPORTING_EMAIL_SUBJECT" "My custom subject"
check_var ".env.web" "EMAIL_PORT" "25"

validate_compose_config

# ---------------------------------------------------------------------------
# Test 8: SWAG mode with monitoring and reporting
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 8: SWAG mode with monitoring and reporting ==="
reset_env

run_setup "fullkey" "full.example.com" "y" "y" "0 3 * * *" "5" "y" "" "smtp.full.com" "alerts@full.com" "fullpass" "465"

check_file_exists ".env.nginx"
check_var ".env.nginx" "URL" "full\.example\.com"
check_var ".env.web" "URL_MONITORING_ENABLED" "true"
check_var ".env.web" "URL_MONITORING_FREQUENCY" "0 3 \* \* \*"
check_var ".env.web" "URL_MONITORING_RATE_LIMIT" "5"
check_var ".env.web" "URL_MONITORING_REPORTING_ENABLED" "true"
check_var ".env.web" "EMAIL_HOST" "smtp\.full\.com"
check_var ".env.web" "EMAIL_PORT" "465"

validate_env_web
validate_env_db
validate_django_check
validate_compose_config

# ---------------------------------------------------------------------------
# Test 9: empty domain name must abort
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 9: empty domain aborts ==="
reset_env

if run_setup "mykey" ""; then
  fail "setup.sh should exit non-zero on empty domain"
else
  pass "setup.sh aborted with non-zero exit on empty domain"
fi

# ---------------------------------------------------------------------------
# Test 10: reporting — empty email host must abort
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 10: reporting — empty email host aborts ==="
reset_env

if run_setup "key" "abort.example.com" "n" "y" "" "" "y" "" ""; then
  fail "setup.sh should abort when email host is empty"
else
  pass "setup.sh aborted on empty email host"
fi

# ---------------------------------------------------------------------------
# Test 11: reporting — empty email user must abort
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 11: reporting — empty email user aborts ==="
reset_env

if run_setup "key" "abort.example.com" "n" "y" "" "" "y" "" "smtp.example.com" ""; then
  fail "setup.sh should abort when email user is empty"
else
  pass "setup.sh aborted on empty email user"
fi

# ---------------------------------------------------------------------------
# Test 12: reporting — empty email password must abort
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 12: reporting — empty email password aborts ==="
reset_env

if run_setup "key" "abort.example.com" "n" "y" "" "" "y" "" "smtp.example.com" "user@example.com" ""; then
  fail "setup.sh should abort when email password is empty"
else
  pass "setup.sh aborted on empty email password"
fi

# ---------------------------------------------------------------------------
# Test 13: reporting — empty email port must abort
# ---------------------------------------------------------------------------
echo ""
echo "=== Test 13: reporting — empty email port aborts ==="
reset_env

if run_setup "key" "abort.example.com" "n" "y" "" "" "y" "" "smtp.example.com" "user@example.com" "pass" ""; then
  fail "setup.sh should abort when email port is empty"
else
  pass "setup.sh aborted on empty email port"
fi

# ---------------------------------------------------------------------------
echo ""
echo "Setup tests: ${PASS} passed, ${FAIL} failed"
[[ $FAIL -eq 0 ]]

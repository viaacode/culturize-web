#!/usr/bin/env bash
# Run the full test suite.
# Usage: bash tests/run_all.sh [--skip-frontend] [--skip-backend] [--skip-shell]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_FRONTEND=false
SKIP_BACKEND=false
SKIP_SHELL=false

for arg in "$@"; do
  case "$arg" in
    --skip-frontend) SKIP_FRONTEND=true ;;
    --skip-backend)  SKIP_BACKEND=true  ;;
    --skip-shell)    SKIP_SHELL=true    ;;
  esac
done

OVERALL=0

run_section() {
  local name="$1"; shift
  echo ""
  echo "╔══════════════════════════════════════════╗"
  echo "║  $name"
  echo "╚══════════════════════════════════════════╝"
  if "$@"; then
    echo "→ PASSED"
  else
    echo "→ FAILED"
    OVERALL=1
  fi
}

# ---------------------------------------------------------------------------
# Backend (Django)
# ---------------------------------------------------------------------------
if [[ "$SKIP_BACKEND" == false ]]; then
  run_section "Django backend tests" \
    bash -c "cd '${ROOT_DIR}/app' && python manage.py test api --verbosity=2"
fi

# ---------------------------------------------------------------------------
# Frontend (Vitest)
# ---------------------------------------------------------------------------
if [[ "$SKIP_FRONTEND" == false ]]; then
  run_section "Vue frontend tests" \
    bash -c "cd '${ROOT_DIR}/frontend' && npm test"
fi

# ---------------------------------------------------------------------------
# Shell tests: setup script
# ---------------------------------------------------------------------------
if [[ "$SKIP_SHELL" == false ]]; then
  run_section "Setup script tests" \
    bash "${ROOT_DIR}/tests/test_setup.sh"
fi

echo ""
if [[ $OVERALL -eq 0 ]]; then
  echo "All test suites passed."
else
  echo "One or more test suites FAILED."
  exit 1
fi

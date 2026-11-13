#!/usr/bin/env bash
# Run the CI merge-gate checks locally.
#
# Usage:
#   tools/scripts/merge_gate.sh [--fix] [--fast] [--clean] [--use-current]
#
# Options:
#   --fix          Apply Ruff fixes and Python/Rust formatting.
#   --fast         Skip building, stub generation, and tests.
#                  Typechecking uses the existing stubs.
#   --clean        Delete .venv-gate after the run.
#   --use-current  Use the already-activated virtualenv instead.
#   -h, --help     Show this help.
#
# Generated stub changes are reported as reminders, not local failures.
# Commit reviewed stubs before pushing; CI checks committed stub freshness.
#
# Requires Bash 4+ (Git Bash on Windows is supported).

set -uo pipefail

usage() {
  cat <<'EOF'
Usage: tools/scripts/merge_gate.sh [options]

  --fix          Apply Ruff fixes and Python/Rust formatting.
  --fast         Skip building, stub generation, and tests.
                 Typechecking uses the existing stubs.
  --clean        Delete .venv-gate after the run.
  --use-current  Use the already-activated virtualenv.
  -h, --help     Show this help.

Generated stub changes produce a reminder, not a local failure.
Review and commit generated stubs before pushing.
EOF
}

PYTHON_VERSION="3.12"
VENV=".venv-gate"
MANIFEST="engine/Cargo.toml"
STUB_FILE="lj_hmc/_core.pyi"

FIX=0
FAST=0
CLEAN=0
USE_CURRENT=0
GATE_ENV_ACTIVE=0

for arg in "$@"; do
  case "$arg" in
    --fix)         FIX=1 ;;
    --fast)        FAST=1 ;;
    --clean)       CLEAN=1 ;;
    --use-current) USE_CURRENT=1 ;;
    -h|--help)     usage; exit 0 ;;
    *)
      printf 'Unknown option: %s\n' "$arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

ROOT=$(git rev-parse --show-toplevel) || exit 1
cd "$ROOT" || exit 1

export CARGO_TERM_COLOR=always
export PIP_DISABLE_PIP_VERSION_CHECK=1

cleanup() {
  local exit_status=$?

  if (( CLEAN && ! USE_CURRENT && GATE_ENV_ACTIVE )); then
    deactivate 2>/dev/null || true

    if ! rm -rf -- "$VENV"; then
      printf 'Warning: could not completely remove %s\n' "$VENV" >&2
    fi
  fi

  return "$exit_status"
}

trap cleanup EXIT

# ── Environment ───────────────────────────────────────
setup_env() {
  local have
  local python_cmd

  if (( USE_CURRENT )); then
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
      echo "ERROR: --use-current requires an activated virtualenv." >&2
      return 1
    fi
  else
    if [[ ! -d "$VENV" ]]; then
      printf 'Creating %s\n' "$VENV"

      if command -v py >/dev/null 2>&1; then
        py "-${PYTHON_VERSION}" -m venv "$VENV" || return 1
      else
        python_cmd=$(
          command -v "python${PYTHON_VERSION}" || command -v python3
        ) || return 1

        "$python_cmd" -m venv "$VENV" || return 1
      fi
    fi

    if [[ -f "$VENV/Scripts/activate" ]]; then
      # Windows / Git Bash
      # shellcheck disable=SC1091
      source "$VENV/Scripts/activate" || return 1
    elif [[ -f "$VENV/bin/activate" ]]; then
      # Linux / macOS
      # shellcheck disable=SC1091
      source "$VENV/bin/activate" || return 1
    else
      printf 'ERROR: no activation script found in %s\n' "$VENV" >&2
      return 1
    fi

    GATE_ENV_ACTIVE=1
  fi

  have=$(
    python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))'
  ) || return 1

  if [[ "$have" != "$PYTHON_VERSION" ]]; then
    printf 'ERROR: Python %s is active; CI requires %s.\n' \
      "$have" "$PYTHON_VERSION" >&2
    return 1
  fi

  # Reuse installed dependencies and install anything missing.
  python -m pip install -q \
    ruff pyright maturin pytest numpy h5py matplotlib || return 1

  if ! command -v cargo >/dev/null 2>&1; then
    echo "ERROR: cargo was not found. Install Rust first." >&2
    return 1
  fi

  if command -v rustup >/dev/null 2>&1; then
    rustup component add clippy rustfmt || return 1
  fi
}

# ── Python lint ────────────────────────────────────────
lint_python() {
  if (( FIX )); then
    python -m ruff check --fix .
    python -m ruff format .
  else
    python -m ruff format --check .
    python -m ruff check .
  fi
}

# ── Rust lint ──────────────────────────────────────────
lint_rust() {
  if (( FIX )); then
    cargo fmt --manifest-path "$MANIFEST"
  else
    cargo fmt --manifest-path "$MANIFEST" -- --check
  fi

  cargo clippy --manifest-path "$MANIFEST" -- -D warnings
}

# ── Build, generate stubs, and test ─────────────────────
build_test() {
  python -m maturin develop --manifest-path "$MANIFEST"

  # A generator error is a real failure.
  python tools/gen_stubs.py

  if [[ ! -s "$STUB_FILE" ]]; then
    printf 'ERROR: stub generation did not produce a nonempty %s.\n' \
      "$STUB_FILE" >&2
    return 1
  fi

  cargo test --manifest-path "$MANIFEST"
  python -m pytest tests/ -v --tb=short
}

# ── Typechecking ───────────────────────────────────────
typecheck() {
  if [[ ! -s "$STUB_FILE" ]]; then
    printf 'ERROR: %s is missing or empty.\n' "$STUB_FILE" >&2
    echo "Run the full gate without --fast to build and generate it." >&2
    return 1
  fi

  python -m pyright
}

# ── Informational stub status ──────────────────────────
report_stub_changes() {
  local changed
  local untracked
  local ignored

  changed=$(git diff --name-only HEAD -- "*.pyi") || return 1
  untracked=$(git ls-files --others --exclude-standard -- "*.pyi") \
    || return 1

  ignored=""

  # Also identify the required stub if a gitignore rule hides it.
  if [[ -f "$STUB_FILE" ]] &&
    ! git ls-files --error-unmatch "$STUB_FILE" >/dev/null 2>&1 &&
    git check-ignore -q "$STUB_FILE"; then
    ignored="$STUB_FILE"
  fi

  if [[ -n "$changed" || -n "$untracked" || -n "$ignored" ]]; then
    printf '\n━━━━ Stub reminder ━━━━\n'
    echo "Type stubs differ from the last commit or are not tracked."
    echo "This is not a build or test failure."

    if [[ -n "$changed" ]]; then
      printf '\nChanged or staged stubs:\n%s\n' "$changed"
    fi

    if [[ -n "$untracked" ]]; then
      printf '\nUntracked stubs:\n%s\n' "$untracked"
    fi

    if [[ -n "$ignored" ]]; then
      printf '\nStub hidden by a gitignore rule:\n%s\n' "$ignored"
      echo "Adjust the ignore rule so this source stub can be committed."
    fi

    printf '\nReview and commit the relevant .pyi files before pushing.\n'
  fi

  return 0
}

# ── Job runner ─────────────────────────────────────────
declare -A RESULT
ORDER=()

run_job() {
  local name=$1
  local fn=$2
  local job_status

  ORDER+=("$name")
  printf '\n━━━━ %s ━━━━\n' "$name"

  # Stop at the first failure within the job.
  # Other jobs still run.
  (
    set -e
    "$fn"
  )
  job_status=$?

  if (( job_status == 0 )); then
    RESULT["$name"]="success"
  else
    RESULT["$name"]="FAILED"
  fi
}

if ! setup_env; then
  echo "Environment setup failed." >&2
  exit 1
fi

run_job "lint-python" lint_python
run_job "lint-rust" lint_rust

if (( FAST )); then
  printf '\nFast mode: skipping build, stub generation, and tests.\n'
else
  run_job "build-test" build_test
fi

# Full runs have now generated the stub Pyright needs.
run_job "typecheck" typecheck

# Stub Git status is informational, outside build-test.
if ! report_stub_changes; then
  echo "WARNING: could not inspect stub Git status; review it manually." >&2
fi

# ── Final gate ─────────────────────────────────────────
printf '\n━━━━ Merge gate ━━━━\n'

status=0

for name in "${ORDER[@]}"; do
  printf '%-14s %s\n' "$name" "${RESULT[$name]}"

  if [[ "${RESULT[$name]}" != "success" ]]; then
    status=1
  fi
done

if (( status )); then
  echo "One or more jobs failed."
elif (( FAST )); then
  echo "Fast checks passed. Build and tests were not run."
else
  echo "All local checks passed."
fi

exit "$status"

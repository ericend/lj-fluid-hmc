#!/usr/bin/env bash
set -euo pipefail

PKG=lj_hmc

[ -f pyproject.toml ] || { echo "Run from project root"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null

gmv() {
  [ -e "$1" ] || { echo "skip (missing): $1"; return 0; }
  if git ls-files --error-unmatch "$1" >/dev/null 2>&1; then
    git mv "$1" "$2"
  else
    mv "$1" "$2"
  fi
}

git checkout -b "reorg-$(date +%Y%m%d-%H%M%S)"

# 1. Remove build artifacts and caches
rm -f engine/*.pyd engine/*.pdb
find . -path ./.venv -prune -o -name "__pycache__" -type d -print0 | xargs -0 rm -rf
rm -rf .pytest_cache .ruff_cache engine/target

# 2. Create the Python package and move the sources
mkdir -p "$PKG"
gmv engine/__init__.py "$PKG/__init__.py"
gmv engine/lj_fluid_init.py "$PKG/lj_fluid_init.py"

# 3. Rename the analysis folder typo
[ -d Analyzis ] && gmv Analyzis analysis

# 4. Rewrite imports in all Python files (skip venv and build dirs)
find . \( -path ./.venv -o -path ./engine/target -o -path ./.git \) -prune -o -name "*.py" -print0 |
while IFS= read -r -d '' f; do
  sed -i \
    -e "s/from engine\.src\.lj_fluid_init/from $PKG.lj_fluid_init/g" \
    -e "s/import engine\.src\.lj_fluid_init/import $PKG.lj_fluid_init/g" \
    -e "s/from engine\.lj_fluid_init/from $PKG.lj_fluid_init/g" \
    -e "s/import engine\.lj_fluid_init/import $PKG.lj_fluid_init/g" \
    -e "s/from Analyzis/from analysis/g" \
    -e "s/import Analyzis/import analysis/g" \
    "$f"
done

# 5. Write the new pyproject.toml (old one saved as .bak)
cp pyproject.toml pyproject.toml.bak
cat > pyproject.toml <<EOF
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[project]
name = "lj-hmc"
version = "0.1.0"
requires-python = ">=3.12"
description = "LJ-HMC simulation with Rust physics kernels"

[tool.maturin]
manifest-path = "engine/Cargo.toml"
module-name = "$PKG._core"
python-source = "."

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]

[tool.pyright]
extraPaths = ["."]
venvPath = "."
venv = ".venv"
typeCheckingMode = "strict"

[tool.ruff.lint]
extend-select = ["ANN"]
EOF

# 6. .gitignore
touch .gitignore
for p in "target/" "*.pyd" "*.pdb" "__pycache__/" ".venv/" ".pytest_cache/" ".ruff_cache/"; do
  grep -qxF "$p" .gitignore || echo "$p" >> .gitignore
done

cat <<MSG

Done. Remaining manual steps:
1. engine/Cargo.toml -> [lib] name = "_core", crate-type = ["cdylib"]
2. engine/src/lib.rs -> rename the #[pymodule] function to _core
3. tests/unit/test_engine.py -> _core = pytest.importorskip("$PKG._core")
4. python -m pip install -e .   (or: maturin develop)
5. pytest -rs
Review: git status && git diff
MSG

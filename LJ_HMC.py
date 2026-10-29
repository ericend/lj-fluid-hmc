from pathlib import Path

# region: Paths
_ROOT = Path(__file__).resolve().parent
print(f"Root: {_ROOT}")
DATA_DIR = _ROOT / "data"
OUT_DIR = _ROOT / "plots"
RESULTS_DIR = _ROOT / "results"

# Automatically create all required directories at startup
# for folder in (DATA_DIR, OUT_DIR, RESULTS_DIR):
#    folder.mkdir(parents=True, exist_ok=True)
# endregion

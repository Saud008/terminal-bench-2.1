import sys
from pathlib import Path

ROOT = Path("/app/environment/verifier_contracts")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

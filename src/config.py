from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INVENTORY_FILE = BASE_DIR / "inventory" / "devices.csv"
STATE_DIR = BASE_DIR / "state_data"
STATE_DIR.mkdir(exist_ok=True)

NET_USER = "admin"
NET_PASS = "admin"
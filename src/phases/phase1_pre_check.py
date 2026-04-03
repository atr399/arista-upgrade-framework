import json
from src.config import STATE_DIR

async def capture_bgp_state(ip, conn, stage="pre"):
    response = await conn.send_command("show ip bgp summary | json")
    bgp_data = json.loads(response.result)
    
    file_path = STATE_DIR / f"{ip}_bgp_{stage}.json"
    with open(file_path, "w") as f:
        json.dump(bgp_data, f, indent=4)
    print(f"[{ip}] Saved BGP state to {file_path.name}")

async def drain_bgp_traffic(ip, conn, asn):
    print(f"[{ip}] Applying DRAIN route-map...")
    commands = [
        "route-map DRAIN_OUT permit 10",
        "set as-path prepend " + f"{asn} " * 3,
        f"router bgp {asn}",
        "neighbor IPv4-PEERS route-map DRAIN_OUT out"
    ]
    await conn.send_configs(commands)
    print(f"[{ip}] BGP Traffic Drained Successfully.")
import json
import asyncio

async def verify_bgp_service(ip, conn, expected_asn):
    print(f"[{ip}] Verifying BGP Service convergence...")
    
    for attempt in range(1, 11):
        response = await conn.send_command("show ip bgp summary | json")
        try:
            bgp_data = json.loads(response.result)
            peers = bgp_data['vrfs']['default']['peers']
            
            for peer_ip, peer_info in peers.items():
                # eBGP ဖြစ်သောကြောင့် Peer ASN အတိအကျကို မစစ်တော့ဘဲ State ကိုသာ စစ်ပါမည်
                if peer_info['peerState'] == 'Established':
                    print(f"[{ip}] SUCCESS: BGP Service is fully converged and Established!")
                    return True
        except KeyError:
            pass

        print(f"[{ip}] BGP not Established yet... (Attempt {attempt}/10)")
        await asyncio.sleep(10)

    print(f"[{ip}] FATAL ERROR: OS is UP, but BGP routing failed to establish!")
    return False

async def restore_bgp_traffic(ip, conn, asn):
    print(f"[{ip}] Restoring BGP Traffic (Undrain)...")
    commands = [
        f"router bgp {asn}",
        "no neighbor IPv4-PEERS route-map DRAIN_OUT out",
        "exit",
        "no route-map DRAIN_OUT permit 10"
    ]
    await conn.send_configs(commands)
    await conn.send_command("write memory")
    print(f"[{ip}] BGP Traffic Restored Successfully.")
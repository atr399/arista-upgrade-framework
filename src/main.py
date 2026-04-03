import asyncio
import csv
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from logging.handlers import RotatingFileHandler
from scrapli.driver.core import AsyncEOSDriver

from src.config import INVENTORY_FILE, NET_USER, NET_PASS, BASE_DIR
from src.phases.phase1_pre_check import capture_bgp_state, drain_bgp_traffic
from src.phases.phase2_upgrade import transfer_software_image, set_boot_variable, reload_device, wait_and_verify
from src.phases.phase3_post_check import verify_bgp_service, restore_bgp_traffic

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(filename=LOG_DIR / "arista_upgrade.log", maxBytes=5 * 1024 * 1024, backupCount=5),
        logging.StreamHandler() 
    ]
)

logger = logging.getLogger("Orchestrator")
final_results = [] # Report ထုတ်ရန်အတွက် List

def get_inventory(file_path):
    with open(file_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row

def is_maintenance_window(tz_name):
    try:
        local_time = datetime.now(ZoneInfo(tz_name))
        # Lab စမ်းသပ်ရန်အတွက် အချိန်မရွေး အလုပ်လုပ်စေလိုပါက (0 မှ 24) ထားပါ
        # တကယ့်အပြင်တွင် 1 <= local_time.hour < 4 ဟု ပြင်ပါ
        if 0 <= local_time.hour < 24: 
            return True
        return False
    except Exception:
        return True # Timezone မှားနေလျှင် ကျော်ခိုင်းမည်

async def process_device(device, sem):
    ip = device['IP']
    asn = device['asn']
    timezone = device.get('timezone', 'UTC')
    
    async with sem:
        if not is_maintenance_window(timezone):
            logger.warning(f"[{ip}] Skipped: Outside of maintenance window ({timezone}).")
            final_results.append({"IP": ip, "Status": "SKIPPED", "Reason": "Outside Maintenance Window"})
            return

        device_cfg = {
            "host": ip, "auth_username": NET_USER, "auth_password": NET_PASS,
            "auth_strict_key": False, "transport": "asyncssh"
        }
        
        try:
            # === PHASE 1 & 2 (Pre-Check, Drain, OS Update, Reload) ===
            logger.info(f"[{ip}] Connecting to device for Phase 1 & 2...")
            async with AsyncEOSDriver(**device_cfg) as conn:
                await capture_bgp_state(ip, conn, stage="pre")
                await drain_bgp_traffic(ip, conn, asn)
                
                logger.info(f"[{ip}] Starting Phase 2: OS Upgrade...")
                await transfer_software_image(ip, conn, image_name="EOS-4.30.2F.swi")
                await set_boot_variable(ip, conn, image_name="EOS-4.30.2F.swi")
                await reload_device(ip, conn)
                
            # စက် Reboot ကျသွားသဖြင့် အောက်တွင် SSH လမ်းကြောင်း ပြတ်သွားပါမည်။
            
            # === POST-RELOAD VERIFICATION ===
            logger.info(f"[{ip}] Initiating Post-Reload Verification...")
            is_up = await wait_and_verify(ip, device_cfg, expected_image="4.30.2F")
            
            if not is_up:
                final_results.append({"IP": ip, "Status": "FAILED", "Reason": "Device unreachable after reload"})
                return

            # === PHASE 3 (Service Verification & Undrain) ===
            logger.info(f"[{ip}] Reconnecting for Phase 3 (BGP Check & Undrain)...")
            async with AsyncEOSDriver(**device_cfg) as conn2: # SSH လမ်းကြောင်း အသစ်ပြန်ဖွင့်ပါသည်
                service_ok = await verify_bgp_service(ip, conn2, asn)
                
                if service_ok:
                    await restore_bgp_traffic(ip, conn2, asn)
                    final_results.append({"IP": ip, "Status": "SUCCESS", "Reason": "Upgraded and Undrained"})
                else:
                    final_results.append({"IP": ip, "Status": "FAILED", "Reason": "BGP failed to establish"})

        except Exception as e:
            logger.error(f"[{ip}] Execution Failed: {e}")
            final_results.append({"IP": ip, "Status": "FAILED", "Reason": str(e)})

def generate_report():
    report_file = BASE_DIR / "upgrade_report.csv"
    with open(report_file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["IP", "Status", "Reason"])
        writer.writeheader()
        writer.writerows(final_results)
    logger.info(f"Final Execution Report generated at: {report_file.name}")

async def main():
    logger.info("Starting Enterprise Arista Upgrade Framework...")
    MAX_CONCURRENT_DEVICES = 50
    sem = asyncio.Semaphore(MAX_CONCURRENT_DEVICES)
    
    devices = get_inventory(INVENTORY_FILE)
    tasks = [process_device(d, sem) for d in devices]
    
    if tasks:
        await asyncio.gather(*tasks)
        generate_report()
    else:
        logger.warning("No devices found in inventory!")
        
    logger.info("All tasks completed across the fleet.")

if __name__ == "__main__":
    asyncio.run(main())
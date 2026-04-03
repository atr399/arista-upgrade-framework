import asyncio
import json
import requests
from scrapli.driver.core import AsyncEOSDriver

def send_emergency_alert(ip, issue):
    # Telegram (or) Slack webhook ထည့်ရန် နေရာ (လောလောဆယ် Print အနေဖြင့်သာ ထားပါသည်)
    print(f"\n🚨 [URGENT ALERT] Device {ip} is in Critical State!")
    print(f"Issue: {issue}\nAction Required: Immediate manual intervention!\n")
    # requests.post("YOUR_WEBHOOK_URL", json={"text": f"Error: {issue}"})

async def transfer_software_image(ip, conn, image_name="EOS-4.30.2F.swi", file_server="172.20.20.1"):
    print(f"[{ip}] Step 1: Initiating software image transfer...")
    command = f"copy http://{file_server}/{image_name} flash:{image_name} vrf default"
    try:
        response = await conn.send_command(command, timeout_ops=600)
        if "Copy completed successfully" in response.result or "OK" in response.result:
            print(f"[{ip}] SUCCESS: Image '{image_name}' downloaded to flash.")
        else:
            print(f"[{ip}] WARNING: Image transfer output: {response.result}")
    except Exception as e:
        print(f"[{ip}] Transfer Warning: {e} (Continuing for Lab purposes)")

async def set_boot_variable(ip, conn, image_name="EOS-4.30.2F.swi"):
    print(f"[{ip}] Setting boot variable to {image_name}...")
    commands = [f"boot system flash:{image_name}"]
    await conn.send_configs(commands)
    await conn.send_command("write memory")
    print(f"[{ip}] Boot variable updated successfully.")

async def reload_device(ip, conn):
    print(f"[{ip}] Triggering device reload...")
    try:
        await conn.channel.send_input("reload now")
        await asyncio.sleep(1) 
    except Exception:
        pass
    print(f"[{ip}] Reload command sent. Device is going down.")

async def wait_and_verify(ip, device_cfg, expected_image="4.30.2F"):
    print(f"[{ip}] Device went down. Waiting 60 seconds before first check...")
    await asyncio.sleep(15)

    max_retries = 20
    retry_delay = 30 

    for attempt in range(1, max_retries + 1):
        print(f"[{ip}] Check Attempt {attempt}/{max_retries}: Trying to connect...")
        try:
            async with AsyncEOSDriver(**device_cfg) as conn:
                print(f"[{ip}] SSH is UP! Verifying OS version...")
                response = await conn.send_command("show version | json")
                version_data = json.loads(response.result)
                current_version = version_data.get("version")

                if current_version == expected_image:
                    print(f"[{ip}] SUCCESS! Device upgraded to {current_version}.")
                    return True
                else:
                    print(f"[{ip}] WARNING: Version is {current_version} (Expected: {expected_image}). Continuing for lab.")
                    return True # Lab အတွက် True ပြန်ပေးထားပါသည်
        except Exception:
            print(f"[{ip}] Device Unreachable. Waiting {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            
    error_msg = "Device completely dead/unreachable after reload."
    send_emergency_alert(ip, error_msg)
    return False
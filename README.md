# Enterprise Arista Fleet Upgrade Framework 🚀

A production-grade, closed-loop network automation framework built with Python and `asyncio` to perform Zero-Downtime OS upgrades across thousands of Arista EOS devices. 
*(Arista Network စက်ပေါင်းများစွာကို Network လုံးဝ Down မသွားစေဘဲ (Zero-Downtime) OS အလိုအလျောက် အဆင့်မြှင့်တင်ပေးနိုင်သော Python Automation Framework ဖြစ်ပါသည်။)*

## 🌟 Core Architecture & Features (အဓိက လုပ်ဆောင်ချက်များ)

This project acts as an intelligent orchestrator utilizing Site Reliability Engineering (SRE) principles:
*(ဤ Project သည် ရိုးရှင်းသော Script တစ်ခုမဟုတ်ဘဲ၊ SRE အခြေခံမူများကို အသုံးပြုထားသော Intelligent Orchestrator တစ်ခု ဖြစ်ပါသည်-)*

* **Zero-Downtime Maintenance (Phase 1):** Automatically identifies current BGP states and seamlessly drains traffic using AS-Path Prepending and Outbound Route-Maps.
  *(BGP Traffic များကို ရုတ်တရက် မပိတ်ပစ်ဘဲ AS-Path Prepending အသုံးပြု၍ လမ်းကြောင်းများကို အရင်ဆုံး ညင်သာစွာ ပြောင်းလဲပေးပါသည်။)*
* **Asynchronous Concurrency (Phase 2):** Utilizes `scrapli` and `asyncio` to execute upgrades in parallel. Designed with a "Hit and Run" reload mechanism to handle abrupt SSH disconnections.
  *(စက်များကို တစ်ပြိုင်နက်တည်း Upgrade လုပ်နိုင်ရန် AsyncIO ကို သုံးထားပြီး၊ SSH Connection ရုတ်တရက် ပြတ်ကျသွားမှုကိုလည်း Error မတက်စေဘဲ ကိုင်တွယ်ဖြေရှင်းပေးပါသည်။)*
* **Service-Aware Verification (Phase 3):** Actively monitors BGP routing tables to ensure full protocol convergence (`Established` state) before performing the Undrain operation.
  *(စက်ပြန်တက်လာရုံဖြင့် မပြီးဘဲ၊ BGP Service အပြည့်အဝ အလုပ်လုပ်/မလုပ် စစ်ဆေးပြီးမှသာ Traffic လမ်းကြောင်းများကို ပုံမှန်အတိုင်း ပြန်လည်ဖွင့်ပေးပါသည်။)*
* **Automated Reporting:** Generates a comprehensive `upgrade_report.csv` detailing the exact outcome.
  *(လုပ်ဆောင်မှု ရလဒ်အားလုံးကို CSV ဖိုင်ဖြင့် အလိုအလျောက် Report ထုတ်ပေးပါသည်။)*

## 📂 Project Structure (ဖိုင်များ ဖွဲ့စည်းပုံ)

```text
arista-upgrade-framework/
├── inventory/
│   └── devices.csv               # Fleet inventory with IP, ASN, and Timezone
├── src/
│   ├── main.py                   # The Core Async Orchestrator
│   ├── config.py                 # Environment and Global Variables
│   └── phases/
│       ├── phase1_pre_check.py   # BGP Snapshot & Traffic Drain
│       ├── phase2_upgrade.py     # Image Transfer, Boot Var, Hit-and-Run Reload
│       └── phase3_post_check.py  # Convergence Verification & Traffic Undrain
├── logs/                         # Rotating execution logs
└── README.md
import requests
from colorama import Fore, Back, Style
import json
import time
from datetime import datetime
import os



with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

platforms = config.get("platforms")
api_url = config.get("api_url")
ping = config.get ("ping")
interval = config.get("interval", 300)

def read_old_id(storage_path: str):
    if not os.path.exists(storage_path):
        return None
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        if isinstance(old_data, list) and old_data:
            return old_data[0].get("id")
    except Exception:
        return None
    return None

def save_storage(storage_path: str, data):
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    with open(storage_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def process_platform(platform, api_url):
    params = platform["params"]
    storage = platform["storage"]
    icon = platform["icon"]
    webhook = platform["webhook"]
    category = platform["category"]
    name = platform["name"]

    if not storage or not webhook:
        print(Fore.RED + f"[{name}] Config incomplète (storage/webhook)" + Style.RESET_ALL)
        return

    old_id = read_old_id(storage)


    r = requests.get(api_url, params=params, timeout=5)
    r.raise_for_status()
    data = r.json()

    if not isinstance(data, list) or not data:
        print(Fore.RED + f"[{name}] Données invalides/vide" + Style.RESET_ALL)
        return
    
    d = data[0]
    id = d.get("id")

    if old_id == id:
        print(Fore.YELLOW +"Déjà envoyé, on ignore")
        return


    payload = {
        "content": ping,
        "embeds": [
            {
                "thumbnail": { "url": icon } ,
                "title": d.get("title"),
                "description": (
                    f"{d.get('description')}\n\n"
                    f"~~{d.get('worth')}~~ **Gratuit jusqu’au {d.get('end_date')}**\n"
                    f"🔗 [Ouvrir dans la boutique]({d.get('open_giveaway')})"
                ),
                "color": 0x7F00FF,
                "footer": { "text": "by choukettas" },
                "timestamp": datetime.utcnow().isoformat(),
                "image": { "url": d.get("image") }
            }
        ]
    }

    resp = requests.post(webhook, json=payload, timeout=8)
    if 200 <= resp.status_code < 300:
        print(Fore.GREEN + f"[{name}] [OK] {d.get('title')} envoyé" + Style.RESET_ALL)
        save_storage(storage, data)  # ✅ SUPER IMPORTANT
    else:
        print(Fore.RED + f"[{name}] Discord erreur {resp.status_code}" + Style.RESET_ALL)

while True:
    for platform in platforms:
        try:
            process_platform(platform, api_url)
        except Exception as e:
            print(Fore.RED + f"[ERREUR] {e}" + Style.RESET_ALL)

    time.sleep(interval) 

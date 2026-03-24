import pandas as pd
import json
import requests
import datetime
import io

# 1. Stiahnutie dát z EÚ priamo do pamäte (vyhneme sa problémom s formátom súboru)
URL = "https://ec.europa.eu/energy/observatory/reports/latest_prices_with_taxes.xlsx"
headers = {'User-Agent': 'Mozilla/5.0'} # Niektoré servery blokujú botov bez agenta
response = requests.get(URL, headers=headers)

if response.status_code == 200:
    # Použijeme io.BytesIO na spracovanie stiahnutých dát
    excel_data = io.BytesIO(response.content)
    
    # Pridaný parameter engine='openpyxl' vyrieši tvoju chybu
    df = pd.read_excel(excel_data, sheet_name=0, skiprows=8, engine='openpyxl')
else:
    print(f"Chyba pri sťahovaní: {response.status_code}")
    exit(1)

fuel_items = []
# Rozšírený zoznam krajín pre karavanistov
country_map = {
    'AT': 'Rakúsko', 'BE': 'Belgicko', 'BG': 'Bulharsko', 'HR': 'Chorvátsko',
    'CZ': 'Česko', 'DE': 'Nemecko', 'HU': 'Maďarsko', 'IT': 'Taliansko',
    'PL': 'Poľsko', 'SK': 'Slovensko', 'SI': 'Slovinsko', 'FR': 'Francúzsko',
    'NL': 'Holandsko', 'ES': 'Španielsko', 'GR': 'Grécko'
}

for _, row in df.iterrows():
    code = str(row[0]).strip()
    if code in country_map:
        try:
            # EÚ udáva ceny v 1000L, preto delíme 1000
            raw_price = row[4] 
            if pd.isna(raw_price): continue
            
            price = float(raw_price) / 1000 
            
            fuel_items.append({
                "name": {"sk": country_map[code]},
                "country": code,
                "price": f"{price:.3f} €",
                "isHot": True if price > 1.95 else False 
            })
        except Exception as e:
            print(f"Chyba pri spracovaní {code}: {e}")
            continue

# Zoraďme krajiny podľa abecedy (aby to v appke nevyzeralo chaoticky)
fuel_items.sort(key=lambda x: x['name']['sk'])

# 3. Aktualizácia tvojho JSON súboru
try:
    with open('app_emergency.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Súbor app_emergency.json sa nenašiel v hlavnom adresári!")
    exit(1)

# Aktualizujeme dátum
data["lastUpdated"] = datetime.datetime.now().strftime("%Y-%m-%d")

# Vytvoríme/Aktualizujeme modul
fuel_module = {
    "icon": "local_gas_station",
    "title": {
        "sk": "Aktuálne ceny nafty (EÚ)",
        "en": "Current Diesel Prices (EU)",
        "de": "Aktuelle Dieselpreise (EU)",
        "cs": "Aktuální ceny nafty (EU)",
        "hu": "Aktuális gázolajárak (EU)"
    },
    "sections": [{
        "heading": {"sk": "Priemerné ceny k dnešnému dňu"},
        "items": fuel_items
    }]
}

# Hľadanie a nahradenie modulu podľa ikony
existing_index = next((i for i, m in enumerate(data["modules"]) if m["icon"] == "local_gas_station"), None)
if existing_index is not None:
    data["modules"][existing_index] = fuel_module
else:
    data["modules"].append(fuel_module)

# Uloženie
with open('app_emergency.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Update úspešne dokončený!")

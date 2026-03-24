import pandas as pd
import json
import requests
import datetime

# 1. Stiahnutie dát z EÚ
URL = "https://ec.europa.eu/energy/observatory/reports/latest_prices_with_taxes.xlsx"
response = requests.get(URL)
with open("temp_prices.xlsx", "wb") as f:
    f.write(response.content)

# 2. Spracovanie Excelu (Nafta je v stĺpci "Gas oil automobile")
# EÚ bulletin má hlavičku, dáta začínajú cca na riadku 9
df = pd.read_excel("temp_prices.xlsx", sheet_name=0, skiprows=8)

fuel_items = []
# Mapovanie kódov krajín na názvy (pre ukážku SK a okolie)
country_map = {
    'AT': 'Rakúsko', 'BE': 'Belgicko', 'BG': 'Bulharsko', 'HR': 'Chorvátsko',
    'CZ': 'Česko', 'DE': 'Nemecko', 'HU': 'Maďarsko', 'IT': 'Taliansko',
    'PL': 'Poľsko', 'SK': 'Slovensko', 'SI': 'Slovinsko'
}

for _, row in df.iterrows():
    code = str(row[0]).strip()
    if code in country_map:
        try:
            # Cena nafty (stĺpec index 4 v bulletine)
            # EÚ udáva ceny v 1000L, preto delíme 1000
            price = float(row[4]) / 1000 
            
            fuel_items.append({
                "name": {"sk": country_map[code]},
                "country": code,
                "price": f"{price:.3f} €/l",
                "isHot": True if price > 1.9 else False # Označenie drahých krajín
            })
        except:
            continue

# 3. Aktualizácia tvojho JSON súboru
with open('app_emergency.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Aktualizujeme dátum v hlavnom JSON
data["lastUpdated"] = datetime.datetime.now().strftime("%Y-%m-%d")

# Vytvoríme nový modul s cenami
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

# Ak modul už existuje (podľa ikony), nahradíme ho, inak pridáme
existing_index = next((i for i, m in enumerate(data["modules"]) if m["icon"] == "local_gas_station"), None)
if existing_index is not None:
    data["modules"][existing_index] = fuel_module
else:
    data["modules"].append(fuel_module)

# Uloženie späť
with open('app_emergency.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
  

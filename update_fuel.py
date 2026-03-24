import pandas as pd
import json
import requests
import datetime
import io

# 1. Použijeme stabilnejšiu URL na priame stiahnutie (vždy aktuálny bulletin)
URL = "https://ec.europa.eu/energy/observatory/reports/latest_prices_with_taxes.xlsx"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"Sťahujem dáta z: {URL}")
response = requests.get(URL, headers=headers, allow_redirects=True)

if response.status_code == 200:
    # Kontrola, či sme naozaj stiahli súbor a nie HTML chybu
    if b"html" in response.content[:100].lower():
        print("Chyba: Server vrátil HTML namiesto Excelu. Skúšam záložnú metódu...")
        # Ak by hlavná linka zlyhala, skúsime túto alternatívnu štruktúru
        alt_url = "https://ec.europa.eu/energy/observatory/reports/Oil_Bulletin_Prices_History.xlsx"
        response = requests.get(alt_url, headers=headers)

    excel_data = io.BytesIO(response.content)
    
    try:
        # Skúsime načítať dáta (EÚ bulletin má dáta na hárku s názvom 'Prices with taxes')
        # Ak názov hárku nesedí, načítame prvý dostupný (sheet_name=0)
        df = pd.read_excel(excel_data, sheet_name=0, skiprows=8, engine='openpyxl')
        print("Excel úspešne načítaný.")
    except Exception as e:
        print(f"Kritická chyba pri parsovaní Excelu: {e}")
        exit(1)
else:
    print(f"Chyba pri sťahovaní: {response.status_code}")
    exit(1)

fuel_items = []
country_map = {
    'AT': 'Rakúsko', 'BE': 'Belgicko', 'BG': 'Bulharsko', 'HR': 'Chorvátsko',
    'CZ': 'Česko', 'DE': 'Nemecko', 'HU': 'Maďarsko', 'IT': 'Taliansko',
    'PL': 'Poľsko', 'SK': 'Slovensko', 'SI': 'Slovinsko', 'FR': 'Francúzsko',
    'NL': 'Holandsko', 'ES': 'Španielsko', 'GR': 'Grécko', 'RO': 'Rumunsko'
}

# Prejdeme riadky a hľadáme kódy krajín v prvom stĺpci (index 0)
for _, row in df.iterrows():
    code = str(row.iloc[0]).strip()
    if code in country_map:
        try:
            # Nafta (Euro-super 95 je zvyčajne stĺpec 2, Gas oil / Diesel je stĺpec 4)
            raw_price = row.iloc[4] 
            
            if pd.isna(raw_price) or not isinstance(raw_price, (int, float)):
                continue
            
            price = float(raw_price) / 1000 
            
            fuel_items.append({
                "name": {"sk": country_map[code]},
                "country": code,
                "price": f"{price:.3f} €",
                "isHot": True if price > 1.95 else False 
            })
        except:
            continue

fuel_items.sort(key=lambda x: x['name']['sk'])

# 3. Aktualizácia JSON súboru
try:
    with open('app_emergency.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print(f"Chyba pri otváraní app_emergency.json: {e}")
    exit(1)

data["lastUpdated"] = datetime.datetime.now().strftime("%Y-%m-%d")

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

existing_index = next((i for i, m in enumerate(data["modules"]) if m["icon"] == "local_gas_station"), None)
if existing_index is not None:
    data["modules"][existing_index] = fuel_module
else:
    data["modules"].append(fuel_module)

with open('app_emergency.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Hotovo! Aktualizovaných {len(fuel_items)} krajín.")

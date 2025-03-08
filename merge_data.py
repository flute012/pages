import json
import os
from datetime import datetime
import pandas as pd
import schedule
import time
# Updated merge_data.py with CSV handling, data filling, and scheduling
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, 'data')

def load_json(file_name):
    file_path = os.path.join(script_dir, file_name) if file_name == 'countylink.json' else os.path.join(data_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_csv(file_name):
    file_path = os.path.join(data_dir, file_name)
    return pd.read_csv(file_path)

def get_worldbank_data():
    current_year = datetime.now().year
    worldbank_data = {}
    for year in range(current_year - 3, current_year):
        file_name = f'worldbank_indicators_data_{year}.csv'
        file_path = os.path.join(data_dir, file_name)
        if os.path.exists(file_path):
            worldbank_data[year] = load_csv(file_name)
    return worldbank_data

def merge_data():
    print("Starting merge process...")
    countylink = load_json('countylink.json')
    cia_data = load_json('country_data.json')
    worldbank_data = get_worldbank_data()

    print("CIA Data structure:", type(cia_data))
    if isinstance(cia_data, list):
        print("CIA Data is a list with", len(cia_data), "items")
    elif isinstance(cia_data, dict):
        print("CIA Data keys:", cia_data.keys())
    else:
        print("CIA Data is neither a list nor a dict")

    if not worldbank_data:
        print("No World Bank data found. Merging only CIA data.")

    merged_data = {}

    for region, region_data in countylink.items():
        merged_data[region] = []
        for country in region_data['countries']:
            country_name = country['name']
            country_data = {
                'name': country_name,
                'chinese': country['chinese'],
                'code': country['code'],
                'url': country['url']
            }

            # Add CIA data
            if isinstance(cia_data, list):
                cia_country_data = next((item for item in cia_data if item['name'] == country_name), None)
            else:  # Assume it's a dict
                cia_country_data = next((item for item in cia_data.get(region, []) if item['name'] == country_name), None)

            if cia_country_data:
                country_data.update({
                    'capital': cia_country_data.get('capital'),
                    'area': cia_country_data.get('area'),
                    'population': cia_country_data.get('population')
                })

            # Add World Bank data
            if worldbank_data:
                years = sorted(worldbank_data.keys(), reverse=True)
                for indicator in worldbank_data[years[0]].columns:
                    if indicator != 'country':
                        for year in years:
                            value = worldbank_data[year].loc[worldbank_data[year]['country'] == country_name, indicator].values
                            if len(value) > 0 and pd.notna(value[0]):
                                country_data[indicator] = value[0]
                                break

            # Add latitude and longitude
            country_data['lat'] = country['lat']
            country_data['lng'] = country['lng']

            merged_data[region].append(country_data)

    return merged_data

def save_merged_data(data):
    output_file = os.path.join(data_dir, 'merged_country_data.json')
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    print(f"Merged data saved to {output_file}")

    # 保存为 CSV
    df_data = []
    for region, countries in data.items():
        for country in countries:
            country_data = country.copy()
            country_data['region'] = region
            df_data.append(country_data)
    
    df = pd.DataFrame(df_data)
    csv_output_file = os.path.join(data_dir, 'merged_country_data.csv')
    df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
    print(f"Merged data also saved as CSV to {csv_output_file}")

def run_merge():
    print(f"Running merge process at {datetime.now()}")
    merged_data = merge_data()
    save_merged_data(merged_data)
    print("Data merging process completed successfully.")

def run_scheduler():
    schedule.every(0.3).days.do(run_merge)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("Initial merge...")
    run_merge()
    print("Starting scheduler. The script will merge data every 2 days.")
    run_scheduler()
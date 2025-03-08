import requests
import pandas as pd
import json
import os
import time
import schedule
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
#pdated WorldBank Data Downloader with ordered countries
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

def load_json(file_name):
    file_path = os.path.join(script_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_ordered_countries():
    countylink = load_json('countylink.json')
    ordered_countries = []
    for region, region_data in countylink.items():
        for country in region_data['countries']:
            ordered_countries.append(country['name'])
    return ordered_countries

def get_recent_years(n=3):
    current_year = datetime.now().year
    return [str(year) for year in range(current_year-n, current_year)]

def download_indicator_data(indicator, name, year):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=1000&date={year}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()[1]  # The actual data is in the second element
        print(f"Successfully downloaded data for {name} - {year}")
        return indicator, name, data, year
    else:
        print(f"Failed to download data for {name} - {year}. Status code: {response.status_code}")
        return indicator, name, None, year

def process_indicator_data(indicator, name, data, year):
    if data is None:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df['indicator'] = name
    df['year'] = year
    df['country'] = df['country'].apply(lambda x: x['value'])
    df = df[['country', 'year', 'indicator', 'value']]
    return df

indicators = {
    "NY.GDP.MKTP.CD": "GDP (current US$)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "NY.GNP.PCAP.CD": "GNI per capita (current US$)",
    "SP.URB.TOTL.IN.ZS": "Urban population (% of total)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "TX.VAL.MRCH.CD.WT": "Merchandise exports (current US$)",
    "TM.VAL.MRCH.CD.WT": "Merchandise imports (current US$)",
    "SP.DYN.CBRT.IN": "Birth rate, crude (per 1,000 people)",
    "SP.DYN.CDRT.IN": "Death rate, crude (per 1,000 people)",
    "SP.POP.DPND": "Age dependency ratio (% of working-age population)"
}

def update_data():
    ordered_countries = get_ordered_countries()
    recent_years = get_recent_years()

    for year in recent_years:
        all_data = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_indicator = {executor.submit(download_indicator_data, indicator, name, year): (indicator, name) for indicator, name in indicators.items()}
            for future in as_completed(future_to_indicator):
                indicator, name, data, year = future.result()
                all_data.append(process_indicator_data(indicator, name, data, year))

        # Combine all data into a single DataFrame for the year
        combined_df = pd.concat(all_data, ignore_index=True)

        # Pivot the data to have indicators as columns
        pivoted_df = combined_df.pivot_table(values='value', index=['country'], columns='indicator')
        pivoted_df.reset_index(inplace=True)

        # Reorder the DataFrame based on the ordered_countries list
        ordered_df = pd.DataFrame({'country': ordered_countries})
        final_df = ordered_df.merge(pivoted_df, on='country', how='left')

        # Save to CSV
        csv_filename = os.path.join(data_dir, f'worldbank_indicators_data_{year}.csv')
        final_df.to_csv(csv_filename, index=False)
        print(f"Data for {year} saved to {csv_filename}")

        # Save to JSON
        json_filename = os.path.join(data_dir, f'worldbank_indicators_data_{year}.json')
        final_df.to_json(json_filename, orient='records', indent=2)
        print(f"Data for {year} saved to {json_filename}")

        # Display first few rows
        print(f"\nFirst few rows of data for {year}:")
        print(final_df.head())

    print("Data update complete.")

def run_scheduler():
    schedule.every(2).days.do(update_data)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("Initial data update...")
    update_data()
    print("Starting scheduler. The script will update data every 2 days.")
    run_scheduler()
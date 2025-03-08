import json
import requests
from bs4 import BeautifulSoup
import csv
import re
import os
import time
import schedule
import sys 

script_dir = os.path.dirname(os.path.abspath(__file__))

data_dir = os.path.join(script_dir, 'data')
os.makedirs(data_dir, exist_ok=True)


def parse_number(number_text):
    match = re.search(r'([\d,\.]+)\s*(?:million)?', number_text)
    if match:
        number = float(match.group(1).replace(',', ''))
        if 'million' in number_text:
            return int(number * 1000000)
        return int(number)
    return None

def scrape_country_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    area = population = capital = None

    # 提取 Area 数据
    geography_section = soup.find('h2', string='Geography')
    if geography_section:
        total_tag = geography_section.find_next('strong', string=re.compile(r'total\s*:'))
        if total_tag:
            area_text = total_tag.next_sibling
            if area_text:
                area = parse_number(area_text)

    # 提取 Population 数据
    people_section = soup.find('h2', string='People and Society')
    if people_section:
        population_header = people_section.find_next('a', string='Population')
        if population_header:
            total_tag = population_header.find_next('strong', string=re.compile(r'total\s*:'))
            if total_tag:
                population_text = total_tag.next_sibling
                if population_text:
                    population = parse_number(population_text)

    # 提取 Capital 数据
    government_section = soup.find('h2', string='Government')
    if government_section:
        capital_header = government_section.find_next('a', string='Capital')
        if capital_header:
            name_tag = capital_header.find_next('strong', string='name:')
            if name_tag:
                capital_text = name_tag.next_sibling
                if capital_text:
                    capital = capital_text.split('<br>')[0].strip()

    return area, population, capital

def generate_country_data(json_file, csv_output, json_output):
    with open(os.path.join(script_dir, json_file), 'r', encoding='utf-8') as f:
        data = json.load(f)

    output_data = {}
    csv_data = []

    csv_path = os.path.join(data_dir, csv_output)
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Region', 'Country', 'Chinese Name', 'Capital', 'Area (sq km)', 'Population'])

        for region, region_data in data.items():
            output_data[region] = []
            for country in region_data['countries']:
                area, population, capital = scrape_country_data(country['url'])
                country_data = {
                    "name": country['name'],
                    "chinese": country['chinese'],
                    "capital": capital,
                    "area": area,
                    "population": population,
                }
                output_data[region].append(country_data)

                # 写入CSV
                csvwriter.writerow([region, country['name'], country['chinese'], capital, area, population])

                print(f"Processed: {country['name']} - {country['chinese']} - Capital: {capital}, Area: {area}, Population: {population}")
                
                time.sleep(1) 

    print(f"CSV data saved to {csv_path}")

    # 写入JSON文件
    json_path = os.path.join(data_dir, json_output)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON data saved to {json_path}")

def job():
    print("开始更新 CIA 数据...")
    generate_country_data('countylink.json', 'country_data.csv', 'country_data.json')
    print("CIA 数据更新完成。")

def main():
    # 立即运行一次
    job()
    
    schedule.every(3).months.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  

if __name__ == "__main__":
    main()
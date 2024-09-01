#from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup
import requests
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#app = Flask(__name__)

# 读取CSV文件
df = pd.read_csv('countylink.csv')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/regions')
def get_regions():
    return jsonify(df.columns.tolist())

@app.route('/countries/<region>')
def get_countries(region):
    countries = df[region].dropna().tolist()
    return jsonify([{
        'name': country.split('/')[-1].replace('-', ' ').title(),
        'url': country
    } for country in countries])

@app.route('/country-data/<path:url>')
def get_country_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    divs = soup.find_all('div', id=['geography', 'people-and-society', 'environment', 'government'])
    
    text = ""
    for div in divs:
        for tag in div.find_all(['h2', 'h3', 'p', 'br']):
            if tag.name == 'br':
                text += "<br>"
            elif tag.name in ['h2', 'h3']:
                if tag.name == 'h3' and tag.a:
                    text += f"<{tag.name}>{tag.a.text}</{tag.name}>"
                else:
                    text += str(tag)
            elif tag.name == 'p':
                p_content = str(tag)
                if p_content not in text:
                    text += p_content
    
    return jsonify({'html': text})

#if __name__ == '__main__':
    #app.run(debug=True)

let fullData = {};
let countyLinkData = {};
let selectedCountriesData = {};
const regionSelect = document.getElementById('regionSelect');
const countryList = document.getElementById('countryList');
const selectedCountriesDiv = document.getElementById('selectedCountries');
const compareButton = document.getElementById('compareButton');
const countryData = document.getElementById('countryData');

const indicatorTranslations = {
    "area": "面积",
    "population": "人口",
    "Age dependency ratio (% of working-age population)": "年龄依赖比（占劳动年龄人口的百分比）",
    "GDP (current US$)": "国内生产总值（现价美元）",
    "GDP growth (annual %)": "国内生产总值增长率（年度百分比）",
    "GDP per capita (current US$)": "人均国内生产总值（现价美元）",
    "GNI per capita (current US$)": "人均国民总收入（现价美元）",
    "Merchandise exports (current US$)": "商品出口（现价美元）",
    "Merchandise imports (current US$)": "商品进口（现价美元）",
    "Urban population (% of total)": "城市人口（占总人口百分比）"
};

function initializeUI() {
    Promise.all([
        fetch('data/merged_country_data.json').then(response => response.json()),
        fetch('data/countylink.json').then(response => response.json())
    ]).then(([mergedData, countyLink]) => {
        fullData = mergedData;
        countyLinkData = countyLink;
        updateRegionSelect();
        initializeIndicatorList();
        checkCSVAvailability();
        updateLastModifiedDate();
    }).catch(error => console.error('Error loading data:', error));

    regionSelect.addEventListener('change', updateCountries);
    compareButton.addEventListener('click', compareCountries);
    document.getElementById('clearSelectedCountries').addEventListener('click', clearSelectedCountries);
}

function updateRegionSelect() {
    for (const region in countyLinkData) {
        const option = document.createElement('option');
        option.value = region;
        option.textContent = region;
        regionSelect.appendChild(option);
    }
}

function updateCountries() {
    const region = regionSelect.value;
    countryList.innerHTML = `
        <div class="checkbox-item">
            <input type="checkbox" id="selectAll" name="countries" value="全部">
            <label for="selectAll">全部</label>
        </div>
    `;
    countyLinkData[region].countries.forEach(country => {
        countryList.innerHTML += `
            <div class="checkbox-item">
                <input type="checkbox" id="${country.chinese}" name="countries" value="${country.chinese}">
                <label for="${country.chinese}">${country.chinese}</label>
            </div>
        `;
    });
    countryList.style.display = 'flex';

    document.querySelectorAll('input[name="countries"]').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (this.value === '全部') {
                handleSelectAll(this.checked);
            } else {
                handleCountrySelection(this.value, this.checked);
            }
        });
    });
}

function initializeIndicatorList() {
    const indicatorList = document.getElementById('indicatorList');
    for (const [key, value] of Object.entries(indicatorTranslations)) {
        indicatorList.innerHTML += `
            <div class="checkbox-item">
                <input type="checkbox" id="${key}" name="indicators" value="${key}" checked>
                <label for="${key}">${value}</label>
            </div>
        `;
    }
}

function handleSelectAll(isChecked) {
    document.querySelectorAll('input[name="countries"]').forEach(checkbox => {
        if (checkbox.value !== '全部') {
            checkbox.checked = isChecked;
            handleCountrySelection(checkbox.value, isChecked);
        }
    });
}

function handleCountrySelection(country, isSelected) {
    if (isSelected) {
        addCountry(country);
    } else {
        removeCountry(country);
    }
    updateSelectedCountriesDisplay();
}

function addCountry(country) {
    if (!selectedCountriesData[country]) {
        selectedCountriesData[country] = true;
    }
}

function removeCountry(country) {
    delete selectedCountriesData[country];
}

function updateSelectedCountriesDisplay() {
    const selectedCountriesList = document.getElementById('selectedCountriesList');
    selectedCountriesList.innerHTML = '';
    for (const country in selectedCountriesData) {
        selectedCountriesList.innerHTML += `
            <span class="selected-country">
                ${country}
                <span class="remove-country" onclick="handleCountrySelection('${country}', false)">×</span>
            </span>
        `;
    }
}

function clearSelectedCountries() {
    selectedCountriesData = {};
    document.querySelectorAll('input[name="countries"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    updateSelectedCountriesDisplay();
}

function compareCountries() {
    const selectedIndicators = Array.from(document.querySelectorAll('input[name="indicators"]:checked'))
        .map(checkbox => checkbox.value);

    if (Object.keys(selectedCountriesData).length === 0) {
        alert("请至少选择一个国家进行比较。");
        return;
    }

    let html = '<table class="comparison-table">';

    // 添加表头（指标名称）
    html += '<tr><th class="country-column">国家/指标</th>';
    selectedIndicators.forEach((indicator, index) => {
        html += `<th class="indicator-column ${index % 2 === 0 ? 'even-column' : 'odd-column'}">${indicatorTranslations[indicator]}</th>`;
    });
    html += '</tr>';

    // 添加每个国家的数据行
    let rowIndex = 0;
    const region = regionSelect.value;
    countyLinkData[region].countries.forEach(countryInfo => {
        const country = countryInfo.chinese;
        if (selectedCountriesData[country]) {
            html += `<tr class="${rowIndex % 2 === 0 ? 'even-row' : 'odd-row'}">`;
            html += `<td class="country-column">${country}</td>`;
            const countryData = findCountryData(country);
            selectedIndicators.forEach((indicator, index) => {
                const value = countryData ? countryData[indicator] : 'N/A';
                html += `<td class="${index % 2 === 0 ? 'even-column' : 'odd-column'}">${formatNumber(value)}</td>`;
            });
            html += '</tr>';
            rowIndex++;
        }
    });

    html += '</table>';
    countryData.innerHTML = html;
}

function findCountryData(countryName) {
    for (const region in fullData) {
        const country = fullData[region].find(c => c.chinese === countryName);
        if (country) return country;
    }
    return null;
}

function formatNumber(value, decimalPlaces = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }
    let num = parseFloat(value);
    if (Math.abs(num) >= 1e8) {
        return (num / 1e8).toFixed(decimalPlaces) + ' 億';
    } else if (Math.abs(num) >= 1e6) {
        return (num / 1e6).toFixed(decimalPlaces) + ' 百万';
    } else if (Math.abs(num) >= 1e3) {
        return num.toLocaleString('en-US', { maximumFractionDigits: decimalPlaces });
    } else {
        return num.toFixed(decimalPlaces);
    }
}

function checkCSVAvailability() {
    fetch('data/merged_country_data.csv', { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                document.getElementById('csvDownload').innerHTML =
                    '<a href="data/merged_country_data.csv" download>下载CSV文件</a>';
            } else {
                document.getElementById('csvDownload').textContent = 'CSV文件不可用';
            }
        })
        .catch(error => {
            console.error('Error checking CSV availability:', error);
            document.getElementById('csvDownload').textContent = 'CSV文件不可用';
        });
}

function updateLastModifiedDate() {
    fetch('data/merged_country_data.json', { method: 'HEAD' })
        .then(response => {
            const lastModified = response.headers.get('last-modified');
            if (lastModified) {
                const date = new Date(lastModified);
                document.getElementById('updateDate').textContent = date.toLocaleDateString();
            } else {
                document.getElementById('updateDate').textContent = '未知';
            }
        })
        .catch(error => {
            console.error('Error fetching last modified date:', error);
            document.getElementById('updateDate').textContent = '未知';
        });
}

document.addEventListener('DOMContentLoaded', initializeUI);
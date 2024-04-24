# Queries the Shelly EM PRO 50A  (port 0)
# And created a hourly graph + calculates the night minimum need between 2:00 AM and 06:00 AM


import requests
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz

def safe_request(url, params):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def calculate_night_consumption(hourly_consumption):
    paris_tz = pytz.timezone('Europe/Paris')
    night_consumptions = []
    for hour, consumption in hourly_consumption.items():
        hour_dt = datetime.strptime(hour, '%Y-%m-%d %H')
        hour_dt = paris_tz.localize(hour_dt)
        if hour_dt.hour < 6 and (datetime.now(paris_tz) - hour_dt).days < 2:
            night_consumptions.append(consumption)
    return sum(night_consumptions) / len(night_consumptions) if night_consumptions else 0

def fetch_data_and_display(base_url, initial_ts):
    ts = initial_ts
    hourly_consumption = {}
    paris_tz = pytz.timezone('Europe/Paris')

    while True:
        params = {'id': 0, 'ts': ts}
        data = safe_request(base_url, params)
        if not data or 'data' not in data:
            break

        for record_block in data['data']:
            base_time = datetime.fromtimestamp(record_block['ts'], tz=timezone.utc).astimezone(paris_tz)
            for i, values in enumerate(record_block['values']):
                hour = (base_time + timedelta(minutes=i)).strftime('%Y-%m-%d %H')
                hourly_consumption[hour] = hourly_consumption.get(hour, 0) + values[0]

        if 'next_record_ts' in data and data['next_record_ts'] != ts:
            ts = data['next_record_ts']
        else:
            break

    hours = list(hourly_consumption.keys())
    consumptions = list(hourly_consumption.values())
    total_consumption = sum(consumptions)
    night_consumption = calculate_night_consumption(hourly_consumption)

    plt.figure(figsize=(15, 5), facecolor='black')
    bars = plt.bar(hours, consumptions, color='lightgreen', edgecolor='green', width=0.5)

    plt.text(0.05, 0.95, f'Night Consumption Avg: {night_consumption:.2f} Wh',
             horizontalalignment='left', verticalalignment='top', transform=plt.gca().transAxes,
             color='white', fontsize=10)
    plt.text(0.95, 0.95, f'Total Consumption: {total_consumption:.2f} Wh',
             horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes,
             color='white', fontsize=10)

    plt.title(f'Consommation EM PRO50 {datetime.now(paris_tz).strftime("%Y-%m-%d")}', color='white', fontsize=14)
    plt.xlabel('Heure', color='white', fontsize=12)
    plt.ylabel('Consommation (Wh)', color='white', fontsize=12)
    plt.xticks(rotation=45, color='white', fontsize=8)
    plt.yticks(color='white', fontsize=10)
    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
    plt.gca().set_facecolor('black')
    plt.gcf().set_facecolor('black')

    plt.tight_layout()
    plt.savefig('consumption_chart.png', facecolor='black', edgecolor='black', bbox_inches='tight')
    plt.show()

base_url = "http://192.168.128.104/rpc/EM1Data.GetData"
fetch_data_and_display(base_url, 0)

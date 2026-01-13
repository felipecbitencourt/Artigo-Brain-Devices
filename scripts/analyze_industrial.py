import csv
import re
from collections import Counter

# Ler o CSV
with open('../Table1_v12 - Cópia de Página1.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    devices = list(reader)

print(f"Total de dispositivos: {len(devices)}\n")

# 1. TIPOS DE DISPOSITIVO (form factor)
print("=" * 60)
print("TIPOS DE DISPOSITIVO (Form Factor)")
print("=" * 60)
types = Counter()
for d in devices:
    device_type = d.get('Type', '').strip()
    if device_type:
        # Simplificar tipos compostos
        for t in ['Headset', 'Headband', 'Cap', 'Adhesive', 'Earphones', 'Headphones', 'In-Ear']:
            if t.lower() in device_type.lower():
                types[t] += 1
                break
        else:
            types[device_type] += 1

for t, count in types.most_common():
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{t:15} | {count:2} ({pct:5.1f}%) {bar}")

# 2. TIPO DE SENSOR (Dry vs Wet)
print("\n" + "=" * 60)
print("TIPO DE SENSOR (Setup Time)")
print("=" * 60)
sensor_types = {'Dry': 0, 'Semi-Dry': 0, 'Wet (gel/saline)': 0, 'Hybrid': 0, 'Optodes (fNIRS)': 0, 'Unknown': 0}
for d in devices:
    sensor = d.get('Sensor Type', '').strip().lower()
    if 'dry' in sensor and 'semi' not in sensor and 'hybrid' not in sensor:
        sensor_types['Dry'] += 1
    elif 'semi' in sensor:
        sensor_types['Semi-Dry'] += 1
    elif 'wet' in sensor or 'gel' in sensor or 'saline' in sensor:
        sensor_types['Wet (gel/saline)'] += 1
    elif 'hybrid' in sensor:
        sensor_types['Hybrid'] += 1
    elif 'optode' in sensor:
        sensor_types['Optodes (fNIRS)'] += 1
    else:
        sensor_types['Unknown'] += 1

for s, count in sensor_types.items():
    if count > 0:
        pct = (count / len(devices)) * 100
        bar = '█' * int(pct / 2)
        print(f"{s:20} | {count:2} ({pct:5.1f}%) {bar}")

# 3. CONECTIVIDADE WIRELESS
print("\n" + "=" * 60)
print("CONECTIVIDADE WIRELESS")
print("=" * 60)
connectivity = {'Bluetooth/BLE': 0, 'Wi-Fi': 0, 'RF 2.4 GHz': 0, 'Unknown': 0}
for d in devices:
    conn = d.get('Wireless Connectivity', '').strip().lower()
    if 'bluetooth' in conn or 'ble' in conn:
        connectivity['Bluetooth/BLE'] += 1
    if 'wi-fi' in conn or 'wifi' in conn or 'wlan' in conn:
        connectivity['Wi-Fi'] += 1
    if 'rf' in conn and '2.4' in conn:
        connectivity['RF 2.4 GHz'] += 1
    if not conn or conn == '---':
        connectivity['Unknown'] += 1

for c, count in connectivity.items():
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{c:15} | {count:2} ({pct:5.1f}%) {bar}")

# 4. CAPACIDADES AUXILIARES (relevantes para industrial)
print("\n" + "=" * 60)
print("CAPACIDADES AUXILIARES (Industrial-Relevant)")
print("=" * 60)
aux_features = {
    'IMU/Accelerometer': 0,
    'Heart Rate/HRV/PPG': 0,
    'EMG': 0,
    'EOG (Eye)': 0,
    'GSR/EDA': 0,
    'Respiration': 0,
    'Temperature': 0,
    'SpO2': 0
}

for d in devices:
    aux = d.get('Auxiliary capabilities', '').strip().lower()
    if 'imu' in aux or 'accelerometer' in aux or 'motion' in aux:
        aux_features['IMU/Accelerometer'] += 1
    if 'hr' in aux or 'hrv' in aux or 'ppg' in aux or 'heart' in aux:
        aux_features['Heart Rate/HRV/PPG'] += 1
    if 'emg' in aux:
        aux_features['EMG'] += 1
    if 'eog' in aux or 'eye' in aux:
        aux_features['EOG (Eye)'] += 1
    if 'gsr' in aux or 'eda' in aux:
        aux_features['GSR/EDA'] += 1
    if 'resp' in aux:
        aux_features['Respiration'] += 1
    if 'temp' in aux:
        aux_features['Temperature'] += 1
    if 'spo' in aux:
        aux_features['SpO2'] += 1

for f, count in sorted(aux_features.items(), key=lambda x: -x[1]):
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{f:20} | {count:2} ({pct:5.1f}%) {bar}")

# 5. DISPOSITIVOS IDEAIS PARA USO INDUSTRIAL
print("\n" + "=" * 60)
print("DISPOSITIVOS COM PERFIL INDUSTRIAL")
print("(Dry/Semi-Dry + Wireless + IMU ou HR)")
print("=" * 60)
industrial_candidates = []
for d in devices:
    sensor = d.get('Sensor Type', '').strip().lower()
    conn = d.get('Wireless Connectivity', '').strip().lower()
    aux = d.get('Auxiliary capabilities', '').strip().lower()
    device_type = d.get('Type', '').strip().lower()
    
    is_dry = 'dry' in sensor or 'semi' in sensor
    is_wireless = 'bluetooth' in conn or 'ble' in conn or 'wi-fi' in conn
    has_physio = 'imu' in aux or 'accelerometer' in aux or 'hr' in aux or 'ppg' in aux
    is_wearable = 'headset' in device_type or 'headband' in device_type or 'earphone' in device_type
    
    if is_dry and is_wireless and (has_physio or is_wearable):
        price_str = d.get('Price (USD)', '---')
        industrial_candidates.append((d['Model'], device_type.title(), price_str))

print(f"\nEncontrados: {len(industrial_candidates)} dispositivos\n")
for model, dtype, price in industrial_candidates[:15]:
    print(f"  {model:30} | {dtype:15} | {price}")

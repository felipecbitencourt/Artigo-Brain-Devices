import csv
import re
from collections import Counter

# Ler o CSV
with open('../Table1_v12 - Cópia de Página1.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    devices = list(reader)

print(f"Total de dispositivos: {len(devices)}\n")

# 1. DISPOSITIVOS COM CERTIFICAÇÃO MÉDICA
print("=" * 60)
print("DISPOSITIVOS COM CERTIFICAÇÃO MÉDICA")
print("=" * 60)
medical_keywords = ['fda', 'ce ', 'medical', 'clinical', 'cleared', 'approved', 'certification', 'certified']
medical_devices = []

for d in devices:
    # Buscar em todas as colunas
    all_text = ' '.join([str(v).lower() for v in d.values()])
    for keyword in medical_keywords:
        if keyword in all_text:
            aux = d.get('Auxiliary capabilities', '')
            medical_devices.append((d['Model'], aux))
            break

print(f"\nEncontrados: {len(medical_devices)} dispositivos ({len(medical_devices)/len(devices)*100:.1f}%)\n")
for model, aux in medical_devices:
    print(f"  {model:30} | {aux[:50]}...")

# 2. RAW DATA ACCESS
print("\n" + "=" * 60)
print("ACESSO A DADOS BRUTOS (Raw Data)")
print("=" * 60)
raw_access = Counter()
for d in devices:
    access = d.get('Raw data access', '').strip().lower()
    if 'available' in access:
        raw_access['Available'] += 1
    elif 'partial' in access:
        raw_access['Partial'] += 1
    elif 'requires' in access or 'license' in access:
        raw_access['Requires License'] += 1
    elif access == '---' or not access:
        raw_access['Not specified'] += 1
    else:
        raw_access['Other'] += 1

for r, count in raw_access.most_common():
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{r:20} | {count:2} ({pct:5.1f}%) {bar}")

# 3. SAMPLING RATE
print("\n" + "=" * 60)
print("SAMPLING RATE (Resolução Temporal)")
print("=" * 60)

def extract_max_sampling_rate(sr_str):
    """Extrai a taxa de amostragem máxima de uma string"""
    if not sr_str or sr_str == '---':
        return None
    # Encontrar todos os números seguidos de Hz ou kHz
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*(k?Hz)', sr_str, re.IGNORECASE)
    rates = []
    for value, unit in matches:
        rate = float(value)
        if unit.lower() == 'khz':
            rate *= 1000
        rates.append(rate)
    return max(rates) if rates else None

sampling_ranges = {
    '< 256 Hz': 0,
    '256 - 500 Hz': 0,
    '500 - 1000 Hz': 0,
    '1 - 2 kHz': 0,
    '> 2 kHz': 0,
    'Not specified': 0
}

for d in devices:
    sr = extract_max_sampling_rate(d.get('Sampling Rate', ''))
    if sr is None:
        sampling_ranges['Not specified'] += 1
    elif sr < 256:
        sampling_ranges['< 256 Hz'] += 1
    elif sr <= 500:
        sampling_ranges['256 - 500 Hz'] += 1
    elif sr <= 1000:
        sampling_ranges['500 - 1000 Hz'] += 1
    elif sr <= 2000:
        sampling_ranges['1 - 2 kHz'] += 1
    else:
        sampling_ranges['> 2 kHz'] += 1

for sr, count in sampling_ranges.items():
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{sr:20} | {count:2} ({pct:5.1f}%) {bar}")

# 4. RESOLUÇÃO ADC
print("\n" + "=" * 60)
print("RESOLUÇÃO ADC (Qualidade de Sinal)")
print("=" * 60)

def extract_adc_resolution(adc_str):
    if not adc_str or adc_str == '---':
        return None
    match = re.search(r'(\d+)-?bit', adc_str, re.IGNORECASE)
    return int(match.group(1)) if match else None

adc_ranges = {
    '≤ 14-bit': 0,
    '16-bit': 0,
    '24-bit': 0,
    '32-bit': 0,
    'Not specified': 0
}

for d in devices:
    adc = extract_adc_resolution(d.get('ADC resolution', ''))
    if adc is None:
        adc_ranges['Not specified'] += 1
    elif adc <= 14:
        adc_ranges['≤ 14-bit'] += 1
    elif adc <= 16:
        adc_ranges['16-bit'] += 1
    elif adc <= 24:
        adc_ranges['24-bit'] += 1
    else:
        adc_ranges['32-bit'] += 1

for adc, count in adc_ranges.items():
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{adc:20} | {count:2} ({pct:5.1f}%) {bar}")

# 5. DATA SYNCHRONIZATION (importante para integração hospitalar)
print("\n" + "=" * 60)
print("SINCRONIZAÇÃO DE DADOS (Integração)")
print("=" * 60)
sync_features = {
    'LSL': 0,
    'SDK': 0,
    'API': 0,
    'TCP/UDP': 0,
    'None/Unknown': 0
}

for d in devices:
    sync = d.get('Data Synchronization', '').strip().lower()
    if 'lsl' in sync:
        sync_features['LSL'] += 1
    if 'sdk' in sync:
        sync_features['SDK'] += 1
    if 'api' in sync:
        sync_features['API'] += 1
    if 'tcp' in sync or 'udp' in sync:
        sync_features['TCP/UDP'] += 1
    if not sync or sync == '---':
        sync_features['None/Unknown'] += 1

for s, count in sorted(sync_features.items(), key=lambda x: -x[1]):
    pct = (count / len(devices)) * 100
    bar = '█' * int(pct / 2)
    print(f"{s:20} | {count:2} ({pct:5.1f}%) {bar}")

# 6. PERFIL CLÍNICO (alta qualidade)
print("\n" + "=" * 60)
print("DISPOSITIVOS COM PERFIL CLÍNICO")
print("(24-bit + >=500 Hz + Raw Data + Sincronização)")
print("=" * 60)
clinical_profile = []
for d in devices:
    adc = extract_adc_resolution(d.get('ADC resolution', ''))
    sr = extract_max_sampling_rate(d.get('Sampling Rate', ''))
    raw = 'available' in d.get('Raw data access', '').lower()
    sync = d.get('Data Synchronization', '').strip()
    has_sync = sync and sync != '---'
    
    if adc and adc >= 24 and sr and sr >= 500 and raw and has_sync:
        clinical_profile.append((d['Model'], f"{int(sr)}Hz", f"{adc}-bit", sync[:30]))

print(f"\nEncontrados: {len(clinical_profile)} dispositivos\n")
for model, sr, adc, sync in clinical_profile[:15]:
    print(f"  {model:30} | {sr:8} | {adc:6} | {sync}")

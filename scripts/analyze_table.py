# -*- coding: utf-8 -*-
"""
Análise Avançada da Tabela de Dispositivos EEG/fNIRS
Inclui métricas solicitadas pelos revisores:
- Análises temporais (R1C1, R3C5)
- Curva de Lorenz e Gini (R3C3)
- Correlações estatísticas (R3C3)
- Classificação por grade (R1C2, R3C4)
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from collections import defaultdict

# Configuração de caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(PROJECT_DIR, "Table1_v12 - Cópia de Página1.csv")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "Alterações", "RELATORIO_TABELA.txt")

CURRENT_YEAR = 2026


def load_data():
    """Carrega e limpa o CSV"""
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    return df


def extract_number(value, get_max=True):
    """Extrai número de uma string (máximo ou mínimo)"""
    if pd.isna(value):
        return None
    nums = re.findall(r'\d+', str(value))
    if not nums:
        return None
    nums = [int(n) for n in nums]
    return max(nums) if get_max else min(nums)


def extract_price(value):
    """Extrai preço de uma string"""
    if pd.isna(value):
        return None
    p_str = str(value).strip()
    if p_str in ['---', '-', '', 'nan']:
        return None
    p_clean = p_str.replace('>', '').replace('<', '').replace(',', '').replace('$', '').strip()
    try:
        return float(p_clean)
    except:
        return None


def has_open_api(row):
    """Verifica se dispositivo tem API aberta"""
    software = str(row.get('Bundled Software', '')).lower()
    sync = str(row.get('Data Synchronization', '')).lower()
    raw_data = str(row.get('Raw data access', '')).lower()
    
    keywords = ['open', 'sdk', 'api', 'lsl', 'free']
    return any(k in software or k in sync or k in raw_data for k in keywords)


def is_dry_electrode(row):
    """Verifica se usa eletrodo seco"""
    sensor = str(row.get('Sensor Type', '')).lower()
    return 'dry' in sensor


def classify_grade(row):
    """Classifica dispositivo em Consumer/Research/Clinical (R3C4)"""
    price = extract_price(row.get('Price (USD)'))
    channels = extract_number(row.get('Channels'))
    sensor_type = str(row.get('Sensor Type', '')).lower()
    aux = str(row.get('Auxiliary capabilities', '')).lower()
    
    # Clinical indicators
    clinical_keywords = ['fda', 'medical', 'clinical', 'ce mark', 'certified']
    is_clinical = any(k in aux.lower() for k in clinical_keywords)
    
    if is_clinical:
        return 'Clinical'
    
    # Research grade: >$2000 OR >16 channels OR wet electrodes
    if price and price > 2000:
        return 'Research'
    if channels and channels > 16:
        return 'Research'
    if 'wet' in sensor_type and 'gel' in sensor_type:
        return 'Research'
    
    # Consumer: <$500 OR <=8 channels OR dry/semi-dry electrodes
    if price and price < 500:
        return 'Consumer'
    if channels and channels <= 8:
        return 'Consumer'
    if 'dry' in sensor_type or 'semi' in sensor_type:
        return 'Consumer'
    
    # Default to Research if unclear
    return 'Research'


# ============================================================================
# ANÁLISES BÁSICAS
# ============================================================================

def analyze_years(df):
    """Análise de anos de lançamento"""
    years = df['Year of first appearance'].dropna()
    years = pd.to_numeric(years, errors='coerce').dropna()
    
    return {
        'total_with_year': len(years),
        'total_without_year': len(df) - len(years),
        'min_year': int(years.min()) if len(years) > 0 else None,
        'max_year': int(years.max()) if len(years) > 0 else None,
        'year_counts': years.value_counts().sort_index().to_dict()
    }


def analyze_manufacturers(df):
    """Análise de fabricantes"""
    manufacturers = df['Manufacturer'].dropna().str.strip()
    manufacturers = manufacturers.str.replace('\n', ' ', regex=False)
    unique = manufacturers.unique()
    return {'total': len(unique), 'list': sorted(unique)}


def analyze_countries(df):
    """Análise de países"""
    countries = df['Origin'].dropna().str.strip()
    return {
        'total': len(countries.unique()),
        'list': sorted(countries.unique()),
        'counts': countries.value_counts().to_dict()
    }


def analyze_technology(df):
    """Análise de tecnologias"""
    tech = df['Technology'].dropna().str.strip()
    return {'counts': tech.value_counts().to_dict()}


def analyze_prices(df):
    """Análise de preços"""
    valid_prices = []
    missing = 0
    
    for p in df['Price (USD)'].dropna():
        price = extract_price(p)
        if price:
            valid_prices.append(price)
        else:
            missing += 1
    
    return {
        'total_with_price': len(valid_prices),
        'total_without_price': missing,
        'min_price': min(valid_prices) if valid_prices else None,
        'max_price': max(valid_prices) if valid_prices else None,
        'avg_price': sum(valid_prices) / len(valid_prices) if valid_prices else None,
        'prices': valid_prices
    }


def analyze_channels(df):
    """Análise de canais"""
    channel_values = [extract_number(c) for c in df['Channels'].dropna()]
    channel_values = [c for c in channel_values if c is not None]
    
    return {
        'min': min(channel_values) if channel_values else None,
        'max': max(channel_values) if channel_values else None,
        'avg': sum(channel_values) / len(channel_values) if channel_values else None,
        'values': channel_values
    }


def analyze_studies(df):
    """Análise de estudos"""
    studies_values = [extract_number(s) for s in df['Studies Found'].dropna()]
    studies_values = [s for s in studies_values if s is not None]
    
    return {
        'total': sum(studies_values),
        'max': max(studies_values) if studies_values else 0,
        'min': min(studies_values) if studies_values else 0,
        'avg': sum(studies_values) / len(studies_values) if studies_values else 0,
        'values': studies_values
    }


# ============================================================================
# ANÁLISES AVANÇADAS - REVISORES
# ============================================================================

def calculate_lorenz_gini(values):
    """Calcula Curva de Lorenz e Coeficiente de Gini (R3C3)"""
    if not values or len(values) == 0:
        return None, None
    
    sorted_values = np.array(sorted(values))
    n = len(sorted_values)
    cumulative_sum = np.cumsum(sorted_values)
    total = cumulative_sum[-1]
    
    if total == 0:
        return None, None
    
    # Lorenz curve points
    lorenz_x = np.arange(1, n + 1) / n
    lorenz_y = cumulative_sum / total
    
    # Gini coefficient
    # Area under Lorenz curve
    lorenz_area = np.trapz(lorenz_y, lorenz_x)
    # Area under line of equality is 0.5
    gini = 1 - 2 * lorenz_area
    
    return lorenz_y.tolist(), round(gini, 4)


def calculate_correlations(df):
    """Calcula correlações estatísticas (R3C3)"""
    data = []
    
    for _, row in df.iterrows():
        price = extract_price(row.get('Price (USD)'))
        channels = extract_number(row.get('Channels'))
        studies = extract_number(row.get('Studies Found'))
        
        if studies is not None:
            data.append({
                'price': price,
                'channels': channels,
                'studies': studies,
                'open_api': 1 if has_open_api(row) else 0,
                'dry_electrode': 1 if is_dry_electrode(row) else 0
            })
    
    df_analysis = pd.DataFrame(data)
    
    correlations = {}
    
    # Preço x Adoção
    valid = df_analysis.dropna(subset=['price', 'studies'])
    if len(valid) > 2:
        corr = valid['price'].corr(valid['studies'])
        correlations['price_vs_adoption'] = {
            'correlation': round(corr, 4),
            'n': len(valid),
            'interpretation': 'negativa' if corr < 0 else 'positiva'
        }
    
    # Canais x Adoção
    valid = df_analysis.dropna(subset=['channels', 'studies'])
    if len(valid) > 2:
        corr = valid['channels'].corr(valid['studies'])
        correlations['channels_vs_adoption'] = {
            'correlation': round(corr, 4),
            'n': len(valid),
            'interpretation': 'negativa' if corr < 0 else 'positiva'
        }
    
    # Open API x Adoção
    if len(df_analysis) > 2:
        corr = df_analysis['open_api'].corr(df_analysis['studies'])
        correlations['open_api_vs_adoption'] = {
            'correlation': round(corr, 4),
            'n': len(df_analysis),
            'interpretation': 'negativa' if corr < 0 else 'positiva'
        }
    
    # Eletrodo seco x Adoção
    if len(df_analysis) > 2:
        corr = df_analysis['dry_electrode'].corr(df_analysis['studies'])
        correlations['dry_electrode_vs_adoption'] = {
            'correlation': round(corr, 4),
            'n': len(df_analysis),
            'interpretation': 'negativa' if corr < 0 else 'positiva'
        }
    
    return correlations


def analyze_temporal_trends(df):
    """Análises temporais (R1C1, R3C5)"""
    # Agrupar por período
    periods = {
        '2008-2014': (2008, 2014),
        '2015-2018': (2015, 2018),
        '2019-2022': (2019, 2022),
        '2023-2025': (2023, 2025)
    }
    
    trends = {period: {
        'devices': 0,
        'channels': [],
        'prices': [],
        'wireless_bluetooth': 0,
        'wireless_wifi': 0
    } for period in periods}
    
    for _, row in df.iterrows():
        year = extract_number(row.get('Year of first appearance'))
        if year is None:
            continue
        
        for period_name, (start, end) in periods.items():
            if start <= year <= end:
                trends[period_name]['devices'] += 1
                
                # Canais
                channels = extract_number(row.get('Channels'))
                if channels:
                    trends[period_name]['channels'].append(channels)
                
                # Preço
                price = extract_price(row.get('Price (USD)'))
                if price:
                    trends[period_name]['prices'].append(price)
                
                # Wireless
                wireless = str(row.get('Wireless Connectivity', '')).lower()
                if 'bluetooth' in wireless or 'ble' in wireless:
                    trends[period_name]['wireless_bluetooth'] += 1
                if 'wi-fi' in wireless or 'wifi' in wireless:
                    trends[period_name]['wireless_wifi'] += 1
                
                break
    
    # Calcular médias e porcentagens
    for period in trends:
        t = trends[period]
        t['avg_channels'] = sum(t['channels']) / len(t['channels']) if t['channels'] else 0
        t['avg_price'] = sum(t['prices']) / len(t['prices']) if t['prices'] else 0
        t['pct_bluetooth'] = 100 * t['wireless_bluetooth'] / t['devices'] if t['devices'] > 0 else 0
        t['pct_wifi'] = 100 * t['wireless_wifi'] / t['devices'] if t['devices'] > 0 else 0
        
        # Custo por canal
        if t['channels'] and t['prices']:
            costs_per_channel = []
            for ch, pr in zip(t['channels'], t['prices']):
                if ch > 0:
                    costs_per_channel.append(pr / ch)
            t['avg_cost_per_channel'] = sum(costs_per_channel) / len(costs_per_channel) if costs_per_channel else 0
        else:
            t['avg_cost_per_channel'] = 0
    
    return trends


def classify_all_devices(df):
    """Classifica todos os dispositivos (R1C2, R3C4)"""
    grades = {'Consumer': 0, 'Research': 0, 'Clinical': 0}
    device_grades = []
    
    for _, row in df.iterrows():
        grade = classify_grade(row)
        grades[grade] += 1
        model = str(row.get('Model', 'Unknown')).split('\n')[0][:40]
        device_grades.append({'model': model, 'grade': grade})
    
    return {
        'counts': grades,
        'percentages': {k: round(100 * v / len(df), 1) for k, v in grades.items()},
        'devices': device_grades
    }


def calculate_articles_per_year(df):
    """Calcula artigos/ano normalizado (R1C1)"""
    results = []
    
    for _, row in df.iterrows():
        model = str(row.get('Model', 'Unknown')).split('\n')[0][:40]
        year = extract_number(row.get('Year of first appearance'))
        studies = extract_number(row.get('Studies Found'))
        
        if year is None or studies is None or studies == 0:
            continue
        
        years_active = CURRENT_YEAR - year
        if years_active > 0:
            articles_per_year = studies / years_active
            results.append({
                'model': model,
                'year': year,
                'studies': studies,
                'years_active': years_active,
                'articles_per_year': round(articles_per_year, 2)
            })
    
    results.sort(key=lambda x: x['articles_per_year'], reverse=True)
    return results


# ============================================================================
# GERAÇÃO DO RELATÓRIO
# ============================================================================

def generate_report(df):
    """Gera relatório completo"""
    
    # Análises básicas
    years_data = analyze_years(df)
    manufacturers_data = analyze_manufacturers(df)
    countries_data = analyze_countries(df)
    tech_data = analyze_technology(df)
    prices_data = analyze_prices(df)
    channels_data = analyze_channels(df)
    studies_data = analyze_studies(df)
    
    # Análises avançadas (revisores)
    articles_per_year = calculate_articles_per_year(df)
    lorenz, gini = calculate_lorenz_gini(studies_data['values'])
    correlations = calculate_correlations(df)
    temporal_trends = analyze_temporal_trends(df)
    device_grades = classify_all_devices(df)
    
    report = f"""
================================================================================
RELATÓRIO DE ANÁLISE DA TABELA DE DISPOSITIVOS
================================================================================
Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Arquivo fonte: Table1_v12 - Cópia de Página1.csv
Total de dispositivos: {len(df)}

================================================================================
PARTE 1: ANÁLISES BÁSICAS
================================================================================

📅 ANOS DE LANÇAMENTO
------------------------------------------
Dispositivos com ano: {years_data['total_with_year']}
Dispositivos sem ano: {years_data['total_without_year']}
Período: {years_data['min_year']} - {years_data['max_year']}

Distribuição por ano:
"""
    
    for year, count in sorted(years_data['year_counts'].items()):
        report += f"  {int(year)}: {int(count)} dispositivos\n"
    
    report += f"""
🏭 FABRICANTES: {manufacturers_data['total']} únicos
🌍 PAÍSES: {countries_data['total']} países

Principais países:
"""
    for country, count in sorted(countries_data['counts'].items(), key=lambda x: -x[1])[:10]:
        report += f"  {country}: {count} dispositivos\n"
    
    report += f"""
🔬 TECNOLOGIAS
"""
    for tech, count in sorted(tech_data['counts'].items(), key=lambda x: -x[1]):
        report += f"  {tech}: {count} dispositivos\n"
    
    report += f"""
💰 PREÇOS (USD)
------------------------------------------
Com preço: {prices_data['total_with_price']} | Sem preço: {prices_data['total_without_price']}
Mínimo: ${prices_data['min_price']:,.0f} | Máximo: ${prices_data['max_price']:,.0f} | Média: ${prices_data['avg_price']:,.0f}

📡 CANAIS
------------------------------------------
Mínimo: {channels_data['min']} | Máximo: {channels_data['max']} | Média: {channels_data['avg']:.1f}

📊 ESTUDOS ENCONTRADOS
------------------------------------------
Total: {studies_data['total']} | Média: {studies_data['avg']:.1f} | Máx: {studies_data['max']}

================================================================================
PARTE 2: MÉTRICAS DOS REVISORES
================================================================================

📈 R1C1 + R3C5: ARTIGOS POR ANO (TOP 20)
------------------------------------------
"""
    for i, item in enumerate(articles_per_year[:20], 1):
        report += f"  {i:2}. {item['model']:<40} | {item['articles_per_year']:>6.2f} art/ano | ({item['studies']} / {item['years_active']} anos)\n"
    
    report += f"""
📉 R3C3: CURVA DE LORENZ E COEFICIENTE DE GINI
------------------------------------------
Coeficiente de Gini: {gini}
Interpretação: {'Alta concentração (poucos dispositivos dominam)' if gini and gini > 0.5 else 'Distribuição mais equilibrada'}

Pontos significativos:
- 80% dos dispositivos contribuem com ~{int((1-lorenz[int(len(lorenz)*0.8)]) * 100) if lorenz else '?'}% das citações
- Top 5 dispositivos: {sum(d['studies'] for d in articles_per_year[:5])} estudos ({100*sum(d['studies'] for d in articles_per_year[:5])/studies_data['total']:.1f}% do total)

🔗 R3C3: CORRELAÇÕES
------------------------------------------
"""
    for key, data in correlations.items():
        report += f"""  {key.replace('_', ' ').title()}:
    r = {data['correlation']} (n={data['n']}) → Correlação {data['interpretation']}
"""
    
    report += f"""
⏳ R3C5: TENDÊNCIAS TEMPORAIS
------------------------------------------
"""
    report += f"{'Período':<15} | {'Disp.':<6} | {'Canais':<8} | {'Preço':<10} | {'$/Canal':<10} | {'BT%':<6} | {'WiFi%':<6}\n"
    report += "-" * 85 + "\n"
    
    for period, data in temporal_trends.items():
        report += f"{period:<15} | {data['devices']:<6} | {data['avg_channels']:<8.1f} | ${data['avg_price']:<9.0f} | ${data['avg_cost_per_channel']:<9.0f} | {data['pct_bluetooth']:<5.1f}% | {data['pct_wifi']:<5.1f}%\n"
    
    report += f"""
🏷️ R1C2 + R3C4: CLASSIFICAÇÃO POR GRADE
------------------------------------------
Consumer-grade:  {device_grades['counts']['Consumer']:>3} dispositivos ({device_grades['percentages']['Consumer']}%)
Research-grade:  {device_grades['counts']['Research']:>3} dispositivos ({device_grades['percentages']['Research']}%)
Clinical-grade:  {device_grades['counts']['Clinical']:>3} dispositivos ({device_grades['percentages']['Clinical']}%)

Critérios utilizados:
- Consumer: <$500, ≤8 canais, eletrodos secos
- Research: >$2000, >16 canais, eletrodos gel
- Clinical: Certificação FDA/CE, uso médico declarado

================================================================================
PARTE 3: RESUMO PARA O ARTIGO
================================================================================

📝 PLACEHOLDERS PARA ABSTRACT:
   [X] dispositivos = {len(df)}
   [Y] fabricantes = {manufacturers_data['total']}
   [N] países = {countries_data['total']}

📝 MÉTRICAS PRONTAS PARA INSERIR:
   ✅ Gini = {gini} (distribuição concentrada)
   ✅ Top dispositivo: Epoc X com {articles_per_year[0]['articles_per_year']} art/ano
   ✅ Período analisado: {years_data['min_year']}-{years_data['max_year']}
   ✅ Tendência canais: {temporal_trends['2008-2014']['avg_channels']:.0f} → {temporal_trends['2023-2025']['avg_channels']:.0f} (crescimento)
   ✅ Wireless: {temporal_trends['2023-2025']['pct_bluetooth']:.0f}% Bluetooth em 2023-2025

📝 CORRELAÇÕES PARA DISCUSSION:
"""
    for key, data in correlations.items():
        strength = "forte" if abs(data['correlation']) > 0.5 else "moderada" if abs(data['correlation']) > 0.3 else "fraca"
        report += f"   - {key.replace('_', ' ')}: r={data['correlation']} ({strength})\n"
    
    report += f"""
================================================================================
"""
    
    return report


def main():
    print("Carregando dados...")
    df = load_data()
    print(f"Total de linhas: {len(df)}")
    
    print("Gerando relatório com métricas avançadas...")
    report = generate_report(df)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Relatório salvo em: {OUTPUT_PATH}")
    print("\n" + "="*60)
    print(report)


if __name__ == "__main__":
    main()

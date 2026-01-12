# -*- coding: utf-8 -*-
"""
Gerador de Figura Timeline - Dispositivos EEG/fNIRS
Para resposta ao revisor R3C5
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import re

# Configuração de caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(PROJECT_DIR, "Table1_v12 - Cópia de Página1.csv")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Alterações", "Figuras")

# Criar diretório de saída se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_number(value):
    """Extrai número de uma string"""
    if pd.isna(value):
        return None
    nums = re.findall(r'\d+', str(value))
    return int(nums[0]) if nums else None


def load_and_prepare_data():
    """Carrega e prepara dados para visualização"""
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    
    data = []
    for _, row in df.iterrows():
        year = extract_number(row.get('Year of first appearance'))
        if year is None:
            continue
        
        model = str(row.get('Model', 'Unknown')).split('\n')[0][:30]
        tech = str(row.get('Technology', 'EEG')).split('+')[0].strip()
        studies = extract_number(row.get('Studies Found')) or 0
        
        data.append({
            'model': model,
            'year': year,
            'technology': tech,
            'studies': studies
        })
    
    return pd.DataFrame(data)


def create_timeline_scatter(df):
    """Cria gráfico de dispersão temporal"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Cores por tecnologia
    tech_colors = {
        'EEG': '#3498db',
        'fNIRS': '#e74c3c',
        'VR ': '#9b59b6',
        'AR ': '#1abc9c'
    }
    
    def get_color(tech):
        for key, color in tech_colors.items():
            if key in tech:
                return color
        return '#95a5a6'
    
    # Agrupar por ano para evitar sobreposição
    year_groups = df.groupby('year')
    
    for year, group in year_groups:
        n = len(group)
        # Distribuir verticalmente os dispositivos do mesmo ano
        y_positions = np.linspace(0.1, 0.9, n)
        
        for i, (_, device) in enumerate(group.iterrows()):
            color = get_color(device['technology'])
            size = max(30, min(200, device['studies'] * 0.5))
            
            ax.scatter(device['year'], y_positions[i], 
                      s=size, c=color, alpha=0.7, edgecolors='white', linewidth=0.5)
            
            # Adicionar label para dispositivos com muitos estudos
            if device['studies'] > 50:
                ax.annotate(device['model'], 
                           (device['year'], y_positions[i]),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=7, alpha=0.8)
    
    # Configurações do gráfico
    ax.set_xlabel('Year of Market Entry', fontsize=12, fontweight='bold')
    ax.set_ylabel('Device Distribution', fontsize=12, fontweight='bold')
    ax.set_title('Timeline of Wireless Brain Monitoring Devices (2008-2025)\n'
                 'Bubble size proportional to number of studies', 
                 fontsize=14, fontweight='bold')
    
    ax.set_xlim(2007, 2026)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks(range(2008, 2026, 2))
    
    # Grid
    ax.grid(True, axis='x', alpha=0.3)
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3)
    
    # Legenda
    legend_elements = [
        mpatches.Patch(color='#3498db', label='EEG'),
        mpatches.Patch(color='#e74c3c', label='fNIRS'),
        mpatches.Patch(color='#9b59b6', label='VR + EEG'),
        mpatches.Patch(color='#1abc9c', label='AR + EEG'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', title='Technology')
    
    plt.tight_layout()
    
    # Salvar
    output_path = os.path.join(OUTPUT_DIR, 'timeline_scatter.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Salvo: {output_path}")
    
    return output_path


def create_timeline_bar(df):
    """Cria gráfico de barras por ano"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Contar dispositivos por ano e tecnologia
    year_counts = df.groupby(['year', 'technology']).size().unstack(fill_value=0)
    
    # Cores
    colors = {
        'EEG': '#3498db',
        'fNIRS': '#e74c3c',
        'VR ': '#9b59b6',
        'AR ': '#1abc9c',
        'fNIRS ': '#e74c3c'
    }
    
    years = sorted(df['year'].unique())
    x = np.arange(len(years))
    width = 0.7
    
    bottom = np.zeros(len(years))
    
    for tech in year_counts.columns:
        values = [year_counts.loc[y, tech] if y in year_counts.index else 0 for y in years]
        color = colors.get(tech, '#95a5a6')
        ax.bar(x, values, width, bottom=bottom, label=tech, color=color, edgecolor='white')
        bottom += values
    
    ax.set_xlabel('Year of Market Entry', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Devices', fontsize=12, fontweight='bold')
    ax.set_title('Annual Distribution of New Brain Monitoring Devices (2008-2025)', 
                 fontsize=14, fontweight='bold')
    
    ax.set_xticks(x)
    ax.set_xticklabels(years, rotation=45, ha='right')
    ax.legend(title='Technology', loc='upper left')
    ax.grid(True, axis='y', alpha=0.3)
    
    # Adicionar linha de tendência
    totals = [sum(year_counts.loc[y]) if y in year_counts.index else 0 for y in years]
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'timeline_bar.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Salvo: {output_path}")
    
    return output_path


def create_trends_figure(df):
    """Cria figura com tendências temporais"""
    # Carregar dados originais para análise completa
    df_full = pd.read_csv(CSV_PATH, encoding='utf-8')
    
    # Agrupar por período
    periods = [(2008, 2014), (2015, 2018), (2019, 2022), (2023, 2025)]
    period_labels = ['2008-2014', '2015-2018', '2019-2022', '2023-2025']
    
    data = {
        'devices': [],
        'avg_channels': [],
        'pct_bluetooth': [],
        'pct_wifi': []
    }
    
    for start, end in periods:
        mask = df['year'].between(start, end)
        period_df = df[mask]
        
        data['devices'].append(len(period_df))
        
        # Para canais e wireless, precisamos dos dados originais
        full_mask = pd.to_numeric(df_full['Year of first appearance'], errors='coerce').between(start, end)
        period_full = df_full[full_mask]
        
        # Canais
        channels = [extract_number(c) for c in period_full['Channels'].dropna()]
        channels = [c for c in channels if c is not None]
        data['avg_channels'].append(np.mean(channels) if channels else 0)
        
        # Wireless
        wireless = period_full['Wireless Connectivity'].dropna()
        bt_count = sum(1 for w in wireless if 'bluetooth' in str(w).lower() or 'ble' in str(w).lower())
        wifi_count = sum(1 for w in wireless if 'wi-fi' in str(w).lower() or 'wifi' in str(w).lower())
        total = len(period_full)
        data['pct_bluetooth'].append(100 * bt_count / total if total > 0 else 0)
        data['pct_wifi'].append(100 * wifi_count / total if total > 0 else 0)
    
    # Criar figura com 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Número de dispositivos
    ax1 = axes[0, 0]
    bars = ax1.bar(period_labels, data['devices'], color='#3498db', edgecolor='white')
    ax1.set_ylabel('Number of Devices')
    ax1.set_title('A) New Devices per Period', fontweight='bold')
    ax1.bar_label(bars)
    ax1.set_ylim(0, max(data['devices']) * 1.2)
    
    # 2. Média de canais
    ax2 = axes[0, 1]
    ax2.plot(period_labels, data['avg_channels'], 'o-', color='#e74c3c', linewidth=2, markersize=10)
    ax2.set_ylabel('Average Channel Count')
    ax2.set_title('B) Average Channel Count Evolution', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    for i, v in enumerate(data['avg_channels']):
        ax2.annotate(f'{v:.1f}', (period_labels[i], v), textcoords='offset points', 
                    xytext=(0, 10), ha='center')
    
    # 3. Wireless adoption (Bluetooth)
    ax3 = axes[1, 0]
    ax3.plot(period_labels, data['pct_bluetooth'], 's-', color='#2ecc71', linewidth=2, markersize=10)
    ax3.set_ylabel('Percentage (%)')
    ax3.set_title('C) Bluetooth Adoption Rate', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 100)
    for i, v in enumerate(data['pct_bluetooth']):
        ax3.annotate(f'{v:.0f}%', (period_labels[i], v), textcoords='offset points', 
                    xytext=(0, 10), ha='center')
    
    # 4. Wireless adoption (WiFi)
    ax4 = axes[1, 1]
    ax4.plot(period_labels, data['pct_wifi'], 'd-', color='#9b59b6', linewidth=2, markersize=10)
    ax4.set_ylabel('Percentage (%)')
    ax4.set_title('D) Wi-Fi Adoption Rate', fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 100)
    for i, v in enumerate(data['pct_wifi']):
        ax4.annotate(f'{v:.0f}%', (period_labels[i], v), textcoords='offset points', 
                    xytext=(0, 10), ha='center')
    
    plt.suptitle('Temporal Trends in Wireless Brain Monitoring Devices (2008-2025)', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, 'temporal_trends.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Salvo: {output_path}")
    
    return output_path


def main():
    print("Carregando dados...")
    df = load_and_prepare_data()
    print(f"Total de dispositivos com ano: {len(df)}")
    
    print("\nGerando figuras...")
    
    # Figura 1: Timeline scatter
    path1 = create_timeline_scatter(df)
    
    # Figura 2: Bar chart por ano
    path2 = create_timeline_bar(df)
    
    # Figura 3: Tendências
    path3 = create_trends_figure(df)
    
    print("\n" + "="*60)
    print("FIGURAS GERADAS:")
    print("="*60)
    print(f"1. {path1}")
    print(f"2. {path2}")
    print(f"3. {path3}")
    print("\n✅ Todas as figuras foram salvas em:", OUTPUT_DIR)


if __name__ == "__main__":
    main()

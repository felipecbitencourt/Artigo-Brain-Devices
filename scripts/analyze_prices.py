import csv
import re

# Ler o CSV (está na pasta pai)
with open('../Table1_v12 - Cópia de Página1.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    devices = list(reader)

print(f"Total de dispositivos: {len(devices)}\n")

# Extrair preços
prices = []
for d in devices:
    price_str = d.get('Price (USD)', '').strip()
    if price_str and price_str != '---':
        # Remover > e , e espaços
        price_clean = re.sub(r'[>\s,]', '', price_str)
        try:
            price = int(price_clean)
            prices.append((d['Model'], price))
        except:
            pass

print(f"Dispositivos com preço: {len(prices)}")
print(f"Dispositivos sem preço: {len(devices) - len(prices)}\n")

# Ordenar por preço
prices.sort(key=lambda x: x[1])

# Distribuição por faixa
faixas = {
    '< $200': 0,
    '$200 - $500': 0,
    '$500 - $1000': 0,
    '$1000 - $2000': 0,
    '$2000 - $5000': 0,
    '$5000 - $10000': 0,
    '> $10000': 0
}

for model, price in prices:
    if price < 200:
        faixas['< $200'] += 1
    elif price < 500:
        faixas['$200 - $500'] += 1
    elif price < 1000:
        faixas['$500 - $1000'] += 1
    elif price < 2000:
        faixas['$1000 - $2000'] += 1
    elif price < 5000:
        faixas['$2000 - $5000'] += 1
    elif price < 10000:
        faixas['$5000 - $10000'] += 1
    else:
        faixas['> $10000'] += 1

print("=" * 50)
print("DISTRIBUIÇÃO DE PREÇOS")
print("=" * 50)
for faixa, count in faixas.items():
    pct = (count / len(prices)) * 100 if prices else 0
    bar = '█' * int(pct / 2)
    print(f"{faixa:15} | {count:2} dispositivos ({pct:5.1f}%) {bar}")

print("\n" + "=" * 50)
print("DISPOSITIVOS POR FAIXA DE PREÇO")
print("=" * 50)

# Listar dispositivos baratos (< $500)
print("\n📗 DISPOSITIVOS < $500:")
for model, price in prices:
    if price < 500:
        print(f"   ${price:,} - {model}")

# Listar dispositivos médios ($500 - $2000)
print("\n📙 DISPOSITIVOS $500 - $2000:")
for model, price in prices:
    if 500 <= price < 2000:
        print(f"   ${price:,} - {model}")

# Listar dispositivos caros (>= $2000)
print("\n📕 DISPOSITIVOS >= $2000:")
for model, price in prices:
    if price >= 2000:
        print(f"   ${price:,} - {model}")

# Estatísticas
print("\n" + "=" * 50)
print("ESTATÍSTICAS")
print("=" * 50)
price_values = [p[1] for p in prices]
print(f"Mínimo:  ${min(price_values):,}")
print(f"Máximo:  ${max(price_values):,}")
print(f"Média:   ${sum(price_values) / len(price_values):,.0f}")
print(f"Mediana: ${sorted(price_values)[len(price_values)//2]:,}")

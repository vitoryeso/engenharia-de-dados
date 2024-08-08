#!/usr/bin/env python3
import sys

counts = {}

for line in sys.stdin:
    line = line.strip()
    count, nome = line.split("\t", 1)
    try:
        count = int(count)
    except ValueError as err:
        print(f"ValueError: {err}", file=sys.stderr)
        continue
    
    if nome in list(counts.keys()):
        counts[nome] += count
    else:
        counts[nome] = count

# Filtro para pegar apenas os que tiveram mais de 2000 acessos
most_logged_users = {nome: count for nome, count in counts.items() if count > 2000}

# Ordenar os salários em ordem decrescente
most_logged_users = sorted(most_logged_users.items(), key=lambda x: x[1], reverse=True)

for count, nome in most_logged_users:  # Pegar apenas os 6 primeiros
    print(f"{count}\t{nome}")

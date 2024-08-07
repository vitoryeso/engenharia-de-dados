#!/usr/bin/env python3
import sys

salarios = []

for line in sys.stdin:
    line = line.strip()
    salario, nome = line.split("\t", 1)
    try:
        salario = float(salario)
    except ValueError as err:
        print(f"ValueError: {err}", file=sys.stderr)
        continue
    
    salarios.append((salario, nome))

# Ordenar os salários em ordem decrescente e pegar os 6 maiores
salarios.sort(reverse=True, key=lambda x: x[0])
top_6_salarios = salarios[:6]

for salario, nome in top_6_salarios:
    print(f"{salario}\t{nome}")

#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    words = line.split(",")
    if len(words) >= 2:  # Certifique-se de que há pelo menos dois campos
        nome = words[0] + ", " + words[1]
        try:
            salario = float(words[-2].replace('$', '').strip())  # Remove símbolo de moeda e converte para float
        except ValueError as err:
            print(f"ValueError: {err}", file=sys.stderr)
            continue  # Ignore linhas com valores inválidos de salário
        print(f"{salario}\t{nome}")

"""Crea tres gráficas de CPU en PNG a partir del CSV del benchmark.

Requiere matplotlib: py -m pip install matplotlib
Ejemplo: py graficar_resultados.py --csv resultados/resultados_benchmark.csv --salida graficas
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ORDEN = ['Burbuja','Quicksort','ShellSort','Radix','Intercalacion','Mezcla_Directa','Mezcla_Natural']
TITULOS = {'Aleatorio':'Entrada aleatoria', 'Ordenado':'Entrada previamente ordenada', 'Inverso':'Entrada en orden inverso'}


def generar(csv_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with csv_path.open(encoding='utf-8-sig', newline='') as archivo:
        registros = list(csv.DictReader(archivo))
    for escenario, titulo in TITULOS.items():
        fig, ax = plt.subplots(figsize=(9.2, 5.1))
        for algoritmo in ORDEN:
            puntos = sorted((int(r['tamano']), float(r['cpu_ms'])) for r in registros
                           if r['algoritmo']==algoritmo and r['escenario']==escenario and r['estado']=='OK')
            if puntos:
                x, y = zip(*puntos)
                ax.plot(x, y, marker='o', linewidth=2, markersize=6,
                        label=algoritmo.replace('_', ' '))
        ax.set_title('Tiempo de CPU por método - ' + titulo, fontsize=13, fontweight='bold')
        ax.set_xlabel('Cantidad de registros')
        ax.set_ylabel('CPU mediana (ms) - escala logarítmica')
        ax.set_yscale('log')
        ax.set_xticks([10000, 50000, 100000])
        ax.set_xticklabels(['10 000','50 000','100 000'])
        ax.grid(True, which='both', alpha=0.22)
        ax.legend(loc='best', fontsize=8, ncol=2)
        fig.tight_layout()
        path = output_dir / f'cpu_{escenario.lower()}.png'
        fig.savefig(path, dpi=170, bbox_inches='tight')
        plt.close(fig)
        print(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', required=True, type=Path)
    p.add_argument('--salida', required=True, type=Path)
    args = p.parse_args()
    generar(args.csv, args.salida)

if __name__ == '__main__':
    main()

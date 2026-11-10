"""Banco reproducible de siete algoritmos de ordenamiento.

Ejemplos:
  python benchmark.py --repeticiones 3 --salida ../resultados
  python benchmark.py --sizes 100 1000 --repeticiones 1 --salida ../prueba
  python benchmark.py --full-bubble --repeticiones 1   # MUY LENTO para n=100000

Se registran tiempos de CPU y transcurridos independientemente. Para ahorrar
horas de espera, Burbuja con 50000/100000 datos aleatorios/inversos se omite
por defecto; el parámetro --full-bubble desactiva esa protección.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import random
import statistics
import tempfile
import time
from algoritmos import EXTERNOS, INTERNOS, escribir_enteros, leer_enteros


def generar_datos(n: int, seed: int) -> dict[str, list[int]]:
    aleatorio = random.Random(seed + n)
    original = [aleatorio.randint(-1_000_000, 1_000_000) for _ in range(n)]
    ascendente = sorted(original)
    return {
        'Aleatorio': original,
        'Ordenado': ascendente,
        'Inverso': list(reversed(ascendente)),
    }


def medir(algoritmo, datos, categoria: str):
    if categoria == 'Interno':
        t0 = time.perf_counter_ns()
        c0 = time.process_time_ns()
        res = algoritmo(datos)
        cpu_ns = time.process_time_ns() - c0
        elapsed_ns = time.perf_counter_ns() - t0
        assert res == sorted(datos), 'SALIDA INCORRECTA'
        return cpu_ns / 1e6, elapsed_ns / 1e6
    with tempfile.TemporaryDirectory(prefix='benchmark_orden_') as d:
        entrada, salida = Path(d) / 'datos.bin', Path(d) / 'ordenado.bin'
        escribir_enteros(entrada, datos)  # Fuera de la medición.
        t0 = time.perf_counter_ns()
        c0 = time.process_time_ns()
        algoritmo(entrada, salida)
        cpu_ns = time.process_time_ns() - c0
        elapsed_ns = time.perf_counter_ns() - t0
        assert leer_enteros(salida) == sorted(datos), 'SALIDA INCORRECTA'
        return cpu_ns / 1e6, elapsed_ns / 1e6


def ejecutar(sizes, repeticiones, full_bubble, salida_dir):
    salida_dir = Path(salida_dir)
    salida_dir.mkdir(parents=True, exist_ok=True)
    algoritmos = [('Interno', n, fun) for n, fun in INTERNOS.items()] + [
        ('Externo', n, fun) for n, fun in EXTERNOS.items()
    ]
    registros = []
    for n in sizes:
        grupos = generar_datos(n, 20261106)
        for escenario, datos in grupos.items():
            for categoria, nombre, algoritmo in algoritmos:
                omitir = (nombre == 'Burbuja' and n >= 50_000
                          and escenario != 'Ordenado' and not full_bubble)
                if omitir:
                    registros.append({
                        'algoritmo': nombre, 'categoria': categoria,
                        'tamano': n, 'escenario': escenario,
                        'repeticiones': 0, 'cpu_ms': '', 'pared_ms': '',
                        'estado': 'OMITIDO: costo cuadrático',
                    })
                    print(f'OMITIDO {nombre:18} n={n:6} {escenario}', flush=True)
                    continue
                muestras = [medir(algoritmo, datos, categoria) for _ in range(repeticiones)]
                cpu = round(statistics.median(x[0] for x in muestras), 3)
                pared = round(statistics.median(x[1] for x in muestras), 3)
                registros.append({
                    'algoritmo': nombre, 'categoria': categoria,
                    'tamano': n, 'escenario': escenario,
                    'repeticiones': repeticiones,
                    'cpu_ms': cpu, 'pared_ms': pared, 'estado': 'OK',
                })
                print(f'{nombre:18} n={n:6} {escenario:9} CPU={cpu:9.3f} ms '
                      f'REAL={pared:9.3f} ms', flush=True)
    archivo_csv = salida_dir / 'resultados_benchmark.csv'
    with archivo_csv.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(registros[0]))
        writer.writeheader()
        writer.writerows(registros)
    datos_equipo = {
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'sistema': platform.platform(),
        'python': platform.python_version(),
        'procesador_reportado': platform.processor() or 'No reportado',
        'nucleos_logicos_reportados': os.cpu_count(),
        'semilla': 20261106,
        'tamanos': sizes,
        'repeticiones_por_escenario': repeticiones,
        'nota': 'CPU=process_time_ns; REAL=perf_counter_ns; mediana de repeticiones',
        'formato_archivo': 'Enteros int32 little-endian, 4 bytes por registro',
        'politica_burbuja': 'Hasta 10000 para aleatorio/inverso; otros casos opcionales',
    }
    (salida_dir / 'entorno_y_metodologia.json').write_text(
        json.dumps(datos_equipo, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'\nResultados: {archivo_csv}', flush=True)
    return registros


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', nargs='+', type=int,
                        default=[10000, 50000, 100000])
    parser.add_argument('--repeticiones', type=int, default=3)
    parser.add_argument('--salida', default='resultados')
    parser.add_argument('--full-bubble', action='store_true')
    args = parser.parse_args()
    if args.repeticiones < 1 or min(args.sizes) < 1:
        parser.error('Tamaños y repeticiones deben ser mayores que cero')
    ejecutar(args.sizes, args.repeticiones, args.full_bubble, args.salida)


if __name__ == '__main__':
    main()

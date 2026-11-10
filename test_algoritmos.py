"""Ejecutar: python -m unittest -v test_algoritmos.py"""
import random
import tempfile
from pathlib import Path
import unittest
from algoritmos import INTERNOS, EXTERNOS, escribir_enteros, leer_enteros


class TestOrdenamientos(unittest.TestCase):
    def test_variantes(self):
        rng = random.Random(123)
        datasets = [
            [], [0], [3, -1, 2, 2, -1, 7, 0],
            list(range(80)), list(range(79, -1, -1)),
            [1] * 99, [2**31-1, -2**31, 0, -1, 1],
            [rng.randint(-100, 100) for _ in range(131)],
        ]
        for datos in datasets:
            for nombre, algoritmo in INTERNOS.items():
                with self.subTest(tipo='interno', algoritmo=nombre, n=len(datos)):
                    self.assertEqual(algoritmo(datos), sorted(datos))
                    self.assertEqual(len(datos), len(algoritmo(datos)))
            with tempfile.TemporaryDirectory() as tmp:
                archivo_entrada = Path(tmp) / 'entrada.bin'
                archivo_salida = Path(tmp) / 'salida.bin'
                escribir_enteros(archivo_entrada, datos)
                for nombre, algoritmo in EXTERNOS.items():
                    with self.subTest(tipo='externo', algoritmo=nombre, n=len(datos)):
                        algoritmo(archivo_entrada, archivo_salida)
                        self.assertEqual(leer_enteros(archivo_salida), sorted(datos))

    def test_repetibles(self):
        datos = list(range(-40, 40)) * 2
        random.Random(55).shuffle(datos)
        for algoritmo in INTERNOS.values():
            self.assertEqual(algoritmo(datos), sorted(datos))


if __name__ == '__main__':
    unittest.main(verbosity=2)

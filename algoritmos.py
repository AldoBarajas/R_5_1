"""Unidad 5: ordenamiento interno y externo. Python >=3.10, sin dependencias externas.

ENTRADA: enteros con signo de 32 bits. Los métodos internos reciben una lista y
regresan una nueva lista ordenada. Los métodos externos reciben rutas y procesan
archivos binarios int32 little-endian (un número por 4 bytes).
"""
from __future__ import annotations
import heapq
import random
from pathlib import Path
import shutil
import struct
import tempfile
from typing import Callable, Iterator

I32 = struct.Struct('<i')


def burbuja(valores: list[int]) -> list[int]:
    a = valores.copy()
    ultimo = len(a) - 1
    while ultimo > 0:
        nuevo_ultimo = 0
        for j in range(ultimo):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                nuevo_ultimo = j
        ultimo = nuevo_ultimo
    return a


def quicksort(valores: list[int]) -> list[int]:
    """Quicksort iterativo con pivote pseudoaleatorio y partición 3 vías.

    Para ahorrar espacio, procesa primero el lado menor y apila el mayor;
    la profundidad de la pila así queda acotada por O(log n).
    """
    a = valores.copy()
    if len(a) < 2:
        return a
    pila = [(0, len(a) - 1)]
    rng = random.Random(20261106)  # reproducibilidad de las pruebas
    while pila:
        lo, hi = pila.pop()
        while lo < hi:
            piv = a[rng.randint(lo, hi)]
            lt, i, gt = lo, lo, hi
            while i <= gt:
                if a[i] < piv:
                    a[lt], a[i] = a[i], a[lt]
                    lt += 1
                    i += 1
                elif a[i] > piv:
                    a[i], a[gt] = a[gt], a[i]
                    gt -= 1
                else:
                    i += 1
            # Una mitad queda en pila y la otra se procesa inmediatamente.
            if lt - lo < hi - gt:
                if gt + 1 < hi:
                    pila.append((gt + 1, hi))
                hi = lt - 1
            else:
                if lo < lt - 1:
                    pila.append((lo, lt - 1))
                lo = gt + 1
    return a


def shellsort(valores: list[int]) -> list[int]:
    """Secuencia de incrementos de Knuth: 1, 4, 13, 40..."""
    a = valores.copy()
    n = len(a)
    h = 1
    while h < n // 3:
        h = 3 * h + 1
    while h >= 1:
        for i in range(h, n):
            temporal = a[i]
            j = i
            while j >= h and a[j - h] > temporal:
                a[j] = a[j - h]
                j -= h
            a[j] = temporal
        h //= 3
    return a


def radix(valores: list[int]) -> list[int]:
    """LSD, base 256 y 4 pasadas para int32 incluyendo valores negativos.

    La transformación XOR con 0x80000000 hace que el orden unsigned corresponda
    al orden signed. Counting estable desde izquierda a derecha.
    """
    if not all(-2**31 <= n < 2**31 for n in valores):
        raise ValueError('Radix requiere enteros con signo de 32 bits')
    a = [n ^ 0x80000000 for n in valores]
    n = len(a)
    for shift in (0, 8, 16, 24):
        conteo = [0] * 256
        for value in a:
            conteo[(value >> shift) & 255] += 1
        total = 0
        for i, cantidad in enumerate(conteo):
            conteo[i] = total
            total += cantidad
        salida = [0] * n
        for value in a:
            b = (value >> shift) & 255
            salida[conteo[b]] = value
            conteo[b] += 1
        a = salida
    return [n ^ 0x80000000 for n in a]


INTERNOS: dict[str, Callable[[list[int]], list[int]]] = {
    'Burbuja': burbuja,
    'Quicksort': quicksort,
    'ShellSort': shellsort,
    'Radix': radix,
}


def escribir_enteros(ruta: str | Path, numeros: list[int]) -> None:
    """Escribe datos int32 sin depender del endianness de la computadora."""
    with open(ruta, 'wb') as archivo:
        for n in numeros:
            archivo.write(I32.pack(n))


def leer_enteros(ruta: str | Path) -> list[int]:
    with open(ruta, 'rb') as f:
        datos = f.read()
    if len(datos) % 4:
        raise ValueError('Archivo de int32 incompleto')
    return [value[0] for value in struct.iter_unpack('<i', datos)]


def _leer_uno(f):
    dato = f.read(4)
    return I32.unpack(dato)[0] if dato else None


def _iterar_run(ruta: Path) -> Iterator[int]:
    with open(ruta, 'rb') as f:
        while (dato := f.read(4)):
            yield I32.unpack(dato)[0]


def intercalacion(entrada: str | Path, salida: str | Path,
                  tam_bloque: int = 4096) -> None:
    """Genera corridas ordenadas en disco y realiza intercalación k-way.

    La intercalación sola exige corridas ya ordenadas; la etapa de generación de
    corridas permite ordenar cualquier entrada. Incluida en el cronometraje.
    """
    if tam_bloque < 2:
        raise ValueError('tam_bloque debe ser >= 2')
    with tempfile.TemporaryDirectory(prefix='intercalacion_') as tmp:
        directorio = Path(tmp)
        rutas: list[Path] = []
        with open(entrada, 'rb') as archivo:
            i = 0
            while (datos := archivo.read(4 * tam_bloque)):
                if len(datos) % 4:
                    raise ValueError('Entrada no alineada a int32')
                numeros = sorted(x[0] for x in struct.iter_unpack('<i', datos))
                run = directorio / f'run_{i:05}.bin'
                escribir_enteros(run, numeros)
                rutas.append(run)
                i += 1
        if not rutas:
            Path(salida).write_bytes(b'')
            return
        # heapq.merge mantiene el orden de los runs para claves repetidas.
        with open(salida, 'wb') as archivo:
            for valor in heapq.merge(*(_iterar_run(r) for r in rutas)):
                archivo.write(I32.pack(valor))


def _fusionar_corridas(entrada: Path, salida: Path, largos, guardar_largos: bool = True) -> list[int]:
    """Mezcla parejas de corridas con dos cursores independientes sobre el archivo.

    En cada pareja se usan dos manejadores con seek a los inicios de cada
    segmento. La salida se escribe secuencialmente; memoria auxiliar O(1).
    """
    resultado: list[int] = []
    pos = 0
    with open(entrada, 'rb') as izq, open(entrada, 'rb') as der, open(salida, 'wb') as out:
        it = iter(largos)
        for a_total in it:
            b_total = next(it, 0)
            izq.seek(pos * 4)
            der.seek((pos + a_total) * 4)
            a, b = a_total, b_total
            x = _leer_uno(izq) if a else None
            y = _leer_uno(der) if b else None
            a -= int(x is not None)
            b -= int(y is not None)
            while x is not None and y is not None:
                if x <= y:
                    out.write(I32.pack(x))
                    x = _leer_uno(izq) if a else None
                    a -= int(x is not None)
                else:
                    out.write(I32.pack(y))
                    y = _leer_uno(der) if b else None
                    b -= int(y is not None)
            while x is not None:
                out.write(I32.pack(x))
                x = _leer_uno(izq) if a else None
                a -= int(x is not None)
            while y is not None:
                out.write(I32.pack(y))
                y = _leer_uno(der) if b else None
                b -= int(y is not None)
            pos += a_total + b_total
            if guardar_largos:
                resultado.append(a_total + b_total)
    return resultado


def mezcla_directa(entrada: str | Path, salida: str | Path) -> None:
    """Mezcla directa externa: corridas de tamaño 1, 2, 4, 8..."""
    n = Path(entrada).stat().st_size // 4
    if Path(entrada).stat().st_size % 4:
        raise ValueError('Entrada no alineada a int32')
    with tempfile.TemporaryDirectory(prefix='directa_') as tmp:
        origen = Path(tmp) / 'origen.bin'
        auxiliar = Path(tmp) / 'auxiliar.bin'
        shutil.copyfile(entrada, origen)
        run = 1
        while run < n:
            largos = (min(run, n - pos) for pos in range(0, n, run))
            _fusionar_corridas(origen, auxiliar, largos, guardar_largos=False)
            origen, auxiliar = auxiliar, origen
            run *= 2
        shutil.copyfile(origen, salida)


def _detectar_corridas(ruta: Path) -> list[int]:
    largos = []
    actual = 0
    anterior = None
    with open(ruta, 'rb') as f:
        while (dato := f.read(4)):
            valor = I32.unpack(dato)[0]
            if actual and valor < anterior:
                largos.append(actual)
                actual = 0
            anterior = valor
            actual += 1
    if actual:
        largos.append(actual)
    return largos


def mezcla_natural(entrada: str | Path, salida: str | Path) -> None:
    """Mezcla natural: detecta corridas no decrecientes; une pares de corridas."""
    with tempfile.TemporaryDirectory(prefix='natural_') as tmp:
        origen = Path(tmp) / 'origen.bin'
        auxiliar = Path(tmp) / 'auxiliar.bin'
        shutil.copyfile(entrada, origen)
        largos = _detectar_corridas(origen)
        while len(largos) > 1:
            largos = _fusionar_corridas(origen, auxiliar, largos)
            origen, auxiliar = auxiliar, origen
        shutil.copyfile(origen, salida)


EXTERNOS = {
    'Intercalacion': intercalacion,
    'Mezcla_Directa': mezcla_directa,
    'Mezcla_Natural': mezcla_natural,
}

# Unidad 5 - Banco de pruebas de métodos de ordenamiento

Proyecto académico de **Estructuras de Datos**. Implementa cuatro métodos internos y tres métodos externos con un **banco reproducible** de 10 000, 50 000 y 100 000 enteros bajo tres condiciones: aleatorio, ordenado e inverso.

**Lenguaje:** Python 3.10 o superior (sin dependencias para ejecutar los algoritmos).

## Archivos

- `algoritmos.py`: Burbuja, Quicksort, ShellSort y Radix (memoria); Intercalación multivía, Mezcla Directa y Mezcla Natural (archivos).
- `test_algoritmos.py`: pruebas de corrección independientes, incluyendo duplicados, números negativos, extremos `int32` y entradas vacías.
- `benchmark.py`: tiempos de CPU y transcurrido, prueba de verificación, medianas, CSV y metadata del entorno.
- `graficar_resultados.py`: reconstruye las gráficas de CPU usando el CSV.
- `.gitignore`: exclusión de archivos temporales de Python.

## Cómo ejecutar desde la terminal de Visual Studio Code / Windows

```powershell
py --version
py -m unittest -v test_algoritmos.py
py benchmark.py --repeticiones 3 --salida resultados
```

Otras opciones:

```powershell
py benchmark.py --sizes 100 1000 --repeticiones 1 --salida prueba
py benchmark.py --full-bubble --repeticiones 1 --salida resultados_completos
```

**Aviso:** `--full-bubble` en 100 000 elementos aleatorios o inversos puede llevar muchísimo tiempo. De manera predeterminada se omiten únicamente esos escenarios de Burbuja para 50 000 y 100 000; los tamaños de Burbuja con datos ordenados sí se ejecutan.

Para generar figuras en tu propio equipo:

```powershell
py -m pip install matplotlib
py graficar_resultados.py --csv resultados/resultados_benchmark.csv --salida graficas
```

## Diseño experimental

- Se usa la misma secuencia de datos por tamaño y escenario para todos los algoritmos. La semilla fija `20261106` garantiza que los datos sean repetibles.
- `Aleatorio`: enteros uniformes entre -1 000 000 y 1 000 000; `Ordenado`: mismos enteros ordenados; `Inverso`: mismos enteros en secuencia descendente.
- Se ejecutan **tres repeticiones**, reportando la **mediana** para disminuir el efecto de variaciones aisladas.
- **CPU (ms):** `time.process_time_ns()`, mide tiempo consumido por el proceso y NO incluye esperas de E/S o suspensión.
- **Tiempo real (ms):** `time.perf_counter_ns()`, sí considera esperas de E/S.
- La creación de los datos y la preparación del archivo de entrada **no** se incluyen en la medición; la clasificación, archivos intermedios y copia final **sí**. La comprobación de la salida es posterior a la medición.
- Se verifica cada resultado contra `sorted(datos)`; una diferencia hace fallar inmediatamente el experimento.
- En los métodos externos se usan archivos temporales binarios, **un registro `int32` little-endian por cuatro bytes**. No se simula E/S mediante listas.
- Intercalación forma corridas de hasta 4 096 registros ordenadas con la implementación estándar estable de Python; a continuación las intercala por múltiples vías. Se mide también la **formación de corridas** para comparar algoritmos completos de clasificación.
- Mezcla Directa fusiona corridas de longitud 1, 2, 4, 8, etc. Mezcla Natural detecta corridas ascendentes existentes para disminuir el número de pasadas. En cada fusión, se prefiere el elemento izquierdo cuando hay igualdad.
- Quicksort es de 3 vías, pivote pseudoaleatorio con semilla fija y pila iterativa optimizada. Radix utiliza cuatro pasadas base 256 y maneja enteros negativos mediante transformación del bit de signo.

Los tiempos dependen de **equipo, SO, intérprete, almacenamiento, antivirus, carga y cachés**. Repite las pruebas en tu computadora para obtener mediciones propias; las incluidas en el reporte corresponden al entorno de ejecución donde se generaron.

## GitHub

1. Crea un repositorio público, por ejemplo `unidad5-ordenamiento`.
2. Sube `algoritmos.py`, `benchmark.py`, `test_algoritmos.py`, `.gitignore` y este `README.md`.
3. Si el docente desea evidencia, agrega en `resultados/` el CSV, JSON de entorno y figuras; evita cargar binarios temporales.
4. Ejecuta las pruebas y copia la URL pública **real** del repositorio en Teams.

## Video de YouTube

Haz dos videos separados (Tarea 5.1 y Tarea 5.2) y súbelos **públicos al mismo canal**. Configura OBS para mostrar **captura de pantalla y cámara web en la esquina inferior derecha**, y evita tapar tablas/código. Los guiones sugeridos se incluyen en `Guia_videos_y_entrega.txt` (archivo aparte en la carpeta de la unidad).

## Nota académica

Las complejidades y resultados dependen de la **variante implementada**. No es válido aplicar una intercalación simple a dos archivos no ordenados y considerarla un algoritmo de ordenamiento completo. Tampoco debe llamarse “tiempo de CPU” al tiempo de reloj medido con `perf_counter`.

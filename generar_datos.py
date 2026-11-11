"""Genera los CSV de un inicio de semestre simulado.

Uso:
    python generar_datos.py                       # universidad, 450 perfiles, semilla 42
    python generar_datos.py --tipo colegio --perfiles 600 --semilla 7
"""
import argparse

from rai.simulacion import guardar_csv, simular

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tipo", choices=["universidad", "colegio"], default="universidad")
    ap.add_argument("--perfiles", type=int, default=450, help="entre 300 y 600")
    ap.add_argument("--necesidad", type=float, default=0.12, help="proporción con alguna necesidad (0-1)")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--salida", default=None, help="carpeta de salida (por defecto data/<tipo>)")
    a = ap.parse_args()
    datos = simular(a.tipo, a.perfiles, a.necesidad, a.semilla)
    carpeta = a.salida or f"data/{a.tipo}"
    guardar_csv(datos, carpeta)
    print(f"{len(datos['estudiantes'])} perfiles guardados en {carpeta}/")

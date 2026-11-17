"""
00 · Exportar los datos crudos de Étoile desde Supabase (API REST de PostgREST).

Minimización de datos en origen: NO se piden reviewer_name, reviewer_photo_url
ni raw_gbp_payload. Los datos personales del cliente nunca llegan al disco.

Salida (ignorada por git, *.csv):
  datos/crudo_resenas.csv
  datos/crudo_tiendas.csv

Uso:  .venv/bin/python 00_exportar.py      (lee SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY del .env del repo)
"""
import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

AQUI = Path(__file__).resolve().parent
load_dotenv(AQUI.parent / ".env")

URL = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1"
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEAD = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

COLUMNAS_RESENAS = ",".join([
    "id", "location_id", "stars", "text", "is_local_guide",
    "published_at", "updated_at", "reply_text", "reply_published_at",
    "classification",
])
COLUMNAS_TIENDAS = "id,nombre,region,active,latitude,longitude"


def traer(tabla: str, columnas: str, lote: int = 1000) -> list[dict]:
    """Paginado por rango (PostgREST limita cada respuesta)."""
    filas, desde = [], 0
    while True:
        r = requests.get(
            f"{URL}/{tabla}",
            params={"select": columnas, "order": "id"},
            headers={**HEAD, "Range": f"{desde}-{desde + lote - 1}"},
            timeout=60,
        )
        r.raise_for_status()
        pagina = r.json()
        filas.extend(pagina)
        if len(pagina) < lote:
            return filas
        desde += lote


def main() -> None:
    (AQUI / "datos").mkdir(exist_ok=True)

    resenas = pd.DataFrame(traer("reviews_core", COLUMNAS_RESENAS))
    # classification es JSONB: se guarda como texto JSON y se aplana en 01_limpieza.
    resenas["classification"] = resenas["classification"].apply(
        lambda c: None if c is None else json.dumps(c, ensure_ascii=False)
    )
    resenas.to_csv(AQUI / "datos/crudo_resenas.csv", index=False)

    tiendas = pd.DataFrame(traer("locations", COLUMNAS_TIENDAS))
    tiendas.to_csv(AQUI / "datos/crudo_tiendas.csv", index=False)

    print(f"reseñas: {len(resenas):,} filas · tiendas: {len(tiendas)} filas")


if __name__ == "__main__":
    main()

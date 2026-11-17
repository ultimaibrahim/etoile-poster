"""
01 · Limpieza y preparación de datos de Étoile.

Entrada:  datos/crudo_resenas.csv, datos/crudo_tiendas.csv   (de 00_exportar.py)
Salida:   datos/resenas_limpias.csv     una fila por reseña, tipos correctos, variables derivadas
          resultados/reporte_limpieza.md   embudo con cuántas filas toca cada paso

Cada paso queda registrado en BITACORA: qué se hizo, por qué y a cuántas filas afectó.
Nada se borra en silencio: lo dudoso se marca con una bandera (columna) y el
análisis de cada script decide si lo usa.
"""
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
ZONA = "America/Mexico_City"
ANONIMIZAR = True
SEMILLA_ANON = 2026
BITACORA: list[tuple[str, str, int]] = []


def anota(paso: str, porque: str, filas: int) -> None:
    BITACORA.append((paso, porque, int(filas)))
    print(f"  · {paso}: {filas:,}")


# ── Utilidades de texto ──────────────────────────────────────────────
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
URL = re.compile(r"https?://\S+|www\.\S+")
ES = re.compile(r"\b(el|la|los|las|muy|que|y|es|de|en|con|por|para|pero|no|me|mi)\b")
EN = re.compile(r"\b(the|and|very|good|great|food|was|is|were|with|nice|place|service)\b")


def sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normaliza(texto: str) -> str:
    """Forma canónica para modelos: minúsculas, sin acentos, sin URLs ni emojis, espacios simples.
    La ñ se conserva (año ≠ ano)."""
    t = texto.lower().replace("ñ", "\0")
    t = sin_acentos(t).replace("\0", "ñ")
    t = URL.sub(" ", t)
    t = EMOJI.sub(" ", t)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)          # «buenísimooooo» → «buenisimoo»
    t = re.sub(r"[^a-zñ0-9¿?¡!.,;:\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def idioma(texto: str) -> str:
    """Detector por palabras funcionales (sin dependencias). Suficiente para es/en."""
    t = texto.lower()
    es, en = len(ES.findall(t)), len(EN.findall(t))
    if es == 0 and en == 0:
        return "indeterminado"
    return "en" if en > es else "es"


# ── Pasos ─────────────────────────────────────────────────────────────
def main() -> None:
    (AQUI / "resultados").mkdir(exist_ok=True)
    df = pd.read_csv(AQUI / "datos/crudo_resenas.csv")
    tiendas = pd.read_csv(AQUI / "datos/crudo_tiendas.csv")
    print("Limpieza")
    anota("Filas crudas exportadas", "reviews_core completo (sin datos personales)", len(df))

    # 1. Duplicados por llave primaria (el sync hace upsert, pero se verifica, no se asume)
    dup = df["id"].duplicated()
    df = df[~dup]
    anota("Duplicados por id eliminados", "la llave de GBP debe ser única", dup.sum())

    # 2. Validación de dominio
    fuera = ~df["stars"].between(1, 5)
    df = df[~fuera]
    anota("Calificaciones fuera de 1–5 eliminadas", "regla CHECK de la base, verificada aquí", fuera.sum())
    huerfanas = ~df["location_id"].isin(tiendas["id"])
    df = df[~huerfanas]
    anota("Reseñas sin tienda válida eliminadas", "integridad referencial", huerfanas.sum())

    # 3. Tipos: fechas en UTC → hora local de México (la hora del día importa para patrones)
    for c in ["published_at", "updated_at", "reply_published_at"]:
        df[c] = pd.to_datetime(df[c], utc=True, format="ISO8601").dt.tz_convert(ZONA)
    df["stars"] = df["stars"].astype(int)
    futuras = df["published_at"] > pd.Timestamp.now(tz=ZONA)
    anota("Fechas en el futuro", "control de calidad del reloj", futuras.sum())
    df = df[~futuras]

    # 4. Texto: vacío → nulo, limpieza de espacios y saltos de línea
    df["text"] = df["text"].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
    df.loc[df["text"] == "", "text"] = pd.NA
    df["tiene_texto"] = df["text"].notna()
    anota("Reseñas sin texto (solo estrellas)", "se conservan para métricas, no sirven para NLP", (~df["tiene_texto"]).sum())

    df["n_emojis"] = df["text"].fillna("").apply(lambda s: len(EMOJI.findall(s)))
    df["texto_limpio"] = df["text"].fillna("").apply(normaliza)
    solo_emoji = df["tiene_texto"] & (df["texto_limpio"] == "")
    df.loc[solo_emoji, "texto_limpio"] = ""
    anota("Textos que eran solo emojis", "quedan vacíos tras normalizar; bandera solo_emoji", solo_emoji.sum())
    df["solo_emoji"] = solo_emoji
    df["n_palabras"] = df["texto_limpio"].str.split().str.len().fillna(0).astype(int)
    cortos = df["tiene_texto"] & (df["n_palabras"] <= 2)
    anota("Textos de 1–2 palabras («Excelente»)", "poca señal; bandera texto_corto", cortos.sum())
    df["texto_corto"] = cortos

    df["idioma"] = np.where(df["tiene_texto"], df["text"].fillna("").apply(idioma), "sin_texto")
    anota("Reseñas en inglés", "el léxico y el modelo son para español; bandera idioma", (df["idioma"] == "en").sum())

    dup_txt = df["tiene_texto"] & ~df["texto_corto"] & df.duplicated(["location_id", "texto_limpio"], keep="first")
    df["texto_repetido"] = dup_txt
    anota("Texto largo repetido en la misma tienda", "posible duplicado o spam; bandera texto_repetido", dup_txt.sum())

    # 5. Variables derivadas (ingeniería de características)
    df["anio"] = df["published_at"].dt.year
    df["mes"] = df["published_at"].dt.strftime("%Y-%m")
    df["hora"] = df["published_at"].dt.hour
    df["dia_semana"] = df["published_at"].dt.day_of_week
    df["editada"] = df["updated_at"] > df["published_at"]
    anota("Reseñas editadas por el cliente", "la calificación vigente es la última", df["editada"].sum())
    df["respondida"] = df["reply_text"].notna()
    df["horas_a_respuesta"] = (df["reply_published_at"] - df["published_at"]).dt.total_seconds() / 3600
    df["negativa"] = df["stars"] <= 2
    df["sentimiento"] = pd.cut(df["stars"], [0, 2, 3, 5], labels=["negativa", "neutra", "positiva"])

    # 6. Aplanar el JSONB de clasificación a columnas
    def plano(c):
        if pd.isna(c):
            return {}
        c = json.loads(c)
        cat = c.get("categoria_queja") or {}
        return {
            "clf_es_queja": c.get("es_queja"),
            "clf_servicio": cat.get("servicio"),
            "clf_calidad": cat.get("calidad"),
            "clf_valor": cat.get("valor"),
            "clf_n_empleados": len(c.get("empleados_mencionados") or []),
        }
    clf = pd.DataFrame(df["classification"].apply(plano).tolist(), index=df.index)
    df = pd.concat([df.drop(columns=["classification", "reply_text"]), clf], axis=1)
    anota("Reseñas con texto sin clasificación guardada", "backlog pendiente del clasificador", (df["tiene_texto"] & df["clf_es_queja"].isna()).sum())

    # 7. Enriquecer con la región (3FN en la base: la región vive en locations)
    df = df.merge(tiendas[["id", "nombre", "region"]].rename(columns={"id": "location_id", "nombre": "tienda"}),
                  on="location_id", how="left")

    # 8. Anonimización: la cadena se presenta de forma anónima en lo académico.
    #    Sucursales → «S01…» y regiones → «Región A…», con orden aleatorio fijo (semilla).
    #    La llave queda solo en datos/ (no se versiona). ANONIMIZAR = False para uso interno.
    if ANONIMIZAR:
        rng = np.random.default_rng(SEMILLA_ANON)
        ids = rng.permutation(sorted(tiendas["id"]))
        regs = rng.permutation(sorted(tiendas["region"].unique()))
        cod_t = {t: f"S{i + 1:02d}" for i, t in enumerate(ids)}
        cod_r = {r: f"Región {chr(65 + i)}" for i, r in enumerate(regs)}
        llave = tiendas.assign(codigo=tiendas["id"].map(cod_t), region_codigo=tiendas["region"].map(cod_r))
        llave[["id", "nombre", "region", "codigo", "region_codigo"]].to_csv(AQUI / "datos/llave_anonimizacion.csv", index=False)
        df["region"] = df["region"].map(cod_r)
        df["location_id"] = df["location_id"].map(cod_t)
        df["tienda"] = df["location_id"]
        anota("Sucursales y regiones anonimizadas", "la cadena se presenta de forma anónima", tiendas["id"].nunique())

    anota("Filas en el dataset limpio", "una por reseña", len(df))
    df.to_csv(AQUI / "datos/resenas_limpias.csv", index=False)

    # Reporte
    lineas = [
        "# Reporte de limpieza",
        "",
        f"Generado por `01_limpieza.py`. Rango: {df['published_at'].min():%Y-%m-%d} → {df['published_at'].max():%Y-%m-%d}.",
        "",
        "| Paso | Por qué | Filas |",
        "|---|---|---:|",
        *[f"| {p} | {r} | {n:,} |" for p, r, n in BITACORA],
        "",
        "## Selección de variables",
        "",
        "De la API de Google Business Profile se conservan: id, tienda, estrellas, texto, fechas de publicación,",
        "edición y respuesta, si es Local Guide y la clasificación. **Se descartan en origen** nombre y foto del",
        "cliente (datos personales que no aportan al análisis) y el JSON crudo de la API.",
        "",
        "## Distribución de estrellas",
        "",
        "| ★ | Reseñas | % |",
        "|---|---:|---:|",
        *[f"| {k} | {v:,} | {v / len(df):.1%} |" for k, v in df["stars"].value_counts().sort_index().items()],
        "",
        "Clases muy desbalanceadas: un modelo que dijera «todo es positivo» acertaría mucho sin servir.",
    ]
    (AQUI / "resultados/reporte_limpieza.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("→ datos/resenas_limpias.csv · resultados/reporte_limpieza.md")


if __name__ == "__main__":
    main()

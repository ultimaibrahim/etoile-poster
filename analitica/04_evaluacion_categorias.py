"""
04 · ¿De qué se queja? Evaluación del clasificador de categorías contra etiquetas.

El 02 responde «¿es negativa?». Este responde «¿la queja es de servicio, calidad o precio?»,
que es lo que étoile muestra a los gerentes. Aquí no hay estrellas que sirvan de etiqueta,
así que se usa una muestra etiquetada.

Muestra (183 reseñas con texto, estratificada, NO representativa de la población):
  120 de 1–2★ · 30 de 3★ · 30 de 4–5★ · 40 de 4–5★ con pista de nombre propio.
  Dividida en dev (para ajustar las reglas v2) y test (intocable). Lo que vale es TEST.
Etiquetas: hechas a ciegas por una IA (Claude) con criterios escritos, sin segundo juez → sin kappa.

Se comparan:
  1. Léxico de étoile v2 (lexico_etoile.py, idéntico al JavaScript en 7,320 reseñas).
  2. Clasificación guardada en la base (lo que ve el usuario): mezcla de Gemini y del léxico.
Intervalos de confianza al 95 % por bootstrap (2,000 remuestreos, semilla fija).

Entrada:  datos/etiquetas_categorias.csv (privado), datos/resenas_limpias.csv
Salida:   resultados/reporte_categorias.md, figuras/04_f1_categorias.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from lexico_etoile import clasifica

AQUI = Path(__file__).resolve().parent
CATS = ["servicio", "calidad", "valor"]
NOMBRE = {"servicio": "Servicio / espera", "calidad": "Calidad del producto", "valor": "Precio / porción"}
B, SEMILLA = 2000, 42
NOCHE, ORO, AZUL, GRIS = "#070A19", "#E0A040", "#5B74C9", "#9AA0B4"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRIS, "figure.dpi": 140, "savefig.bbox": "tight"})


def prf(y, p):
    tp, fp, fn = int((y & p).sum()), int((~y & p).sum()), int((y & ~p).sum())
    P = tp / (tp + fp) if tp + fp else 0.0
    R = tp / (tp + fn) if tp + fn else 0.0
    return P, R, (2 * P * R / (P + R) if P + R else 0.0), tp, fp, fn


def f1_ic(y, p, rng):
    n = len(y)
    vals = [prf(y[i], p[i])[2] for i in (rng.integers(0, n, n) for _ in range(B))]
    return np.percentile(vals, [2.5, 97.5])


def main() -> None:
    et = pd.read_csv(AQUI / "datos/etiquetas_categorias.csv")
    df = pd.read_csv(AQUI / "datos/resenas_limpias.csv", usecols=["id", "text", "stars", "clf_servicio", "clf_calidad", "clf_valor"])
    m = et.merge(df.drop(columns="stars"), on="id", how="left")
    perdidas = m["text"].isna().sum()
    m = m.dropna(subset=["text"])
    print(f"Muestra: {len(et)} · encontradas en la base: {len(m)} (dev {sum(m.split == 'dev')}, test {sum(m.split == 'test')})")

    pred = pd.DataFrame([clasifica(t, s) for t, s in zip(m["text"], m["stars"])], index=m.index)
    rng = np.random.default_rng(SEMILLA)
    filas = []
    for split in ["test", "dev"]:
        sub = m[m["split"] == split]
        for c in CATS:
            y = sub[c].astype(bool).to_numpy()
            # 1. Léxico
            p = pred.loc[sub.index, c].to_numpy()
            P, R, F, tp, fp, fn = prf(y, p)
            lo, hi = f1_ic(y, p, rng)
            filas.append(dict(split=split, metodo="Léxico v2", cat=c, n=len(sub), P=P, R=R, F1=F, lo=lo, hi=hi, tp=tp, fp=fp, fn=fn))
            # 2. Lo guardado en la base (solo reseñas que tienen clasificación)
            g = sub[sub[f"clf_{c}"].notna()]
            yg, pg = g[c].astype(bool).to_numpy(), g[f"clf_{c}"].astype(str).eq("True").to_numpy()
            P, R, F, tp, fp, fn = prf(yg, pg)
            lo, hi = f1_ic(yg, pg, rng)
            filas.append(dict(split=split, metodo="Guardada en la base", cat=c, n=len(g), P=P, R=R, F1=F, lo=lo, hi=hi, tp=tp, fp=fp, fn=fn))
    r = pd.DataFrame(filas)
    print(r[r.split == "test"].round(2).to_string(index=False))

    # Figura: F1 con intervalo, solo TEST
    t = r[r.split == "test"]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for k, (metodo, color, dy) in enumerate([("Léxico v2", ORO, -0.12), ("Guardada en la base", AZUL, 0.12)]):
        s = t[t.metodo == metodo].set_index("cat").loc[CATS]
        ypos = np.arange(len(CATS)) + dy
        ax.errorbar(s["F1"], ypos, xerr=[s["F1"] - s["lo"], s["hi"] - s["F1"]], fmt="o", color=color,
                    ms=8, capsize=4, lw=2, label=metodo)
        for x, yy in zip(s["F1"], ypos):
            ax.annotate(f"{x:.2f}", (x, yy), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=9, color=color)
    ax.set_yticks(range(len(CATS)), [NOMBRE[c] for c in CATS])
    ax.invert_yaxis()
    ax.set(xlim=(0, 1.05), xlabel="F1 en el conjunto de prueba (barra = IC 95 % por bootstrap)",
           title="¿Acierta étoile de qué se queja el cliente?")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=9)
    fig.savefig(AQUI / "figuras/04_f1_categorias.png"); plt.close(fig)

    fila = lambda d: (f"| {NOMBRE[d.cat]} | {d.metodo} | {d.n} | {d.P:.2f} | {d.R:.2f} | **{d.F1:.2f}** "
                      f"| {d.lo:.2f}–{d.hi:.2f} | {d.tp}/{d.fp}/{d.fn} |")
    tabla = lambda s: ["| Categoría | Método | n | Precisión | Recall | F1 | IC 95 % | VP/FP/FN |",
                       "|---|---|---:|---:|---:|---:|---:|---:|", *[fila(d) for d in r[r.split == s].itertuples()]]
    reporte = [
        "# Reporte · evaluación de categorías de queja",
        "",
        f"- Muestra etiquetada: {len(et)} reseñas ({len(m)} encontradas en la base actual"
        + (f"; {perdidas} ya no existen" if perdidas else "") + "). Estratificada: **no representa la población**,",
        "  así que las cifras valen para comparar métodos, no para estimar cuántas quejas hay de cada tipo.",
        "- Etiquetas a ciegas por una IA con criterios escritos; una sola etiquetadora, sin kappa.",
        f"- IC 95 % por bootstrap ({B:,} remuestreos). El léxico v2 se ajustó mirando **dev**; la cifra honesta es **test**.",
        "",
        "## Conjunto de prueba (test)",
        "",
        *tabla("test"),
        "",
        "## Conjunto de desarrollo (dev, optimista: se usó para ajustar las reglas)",
        "",
        *tabla("dev"),
        "",
        "## Lectura",
        "",
        "- Los intervalos son anchos: con ~90 reseñas por conjunto, una diferencia de 0.1 en F1 puede ser ruido.",
        "- «Guardada en la base» mezcla Gemini y el léxico sin registrar cuál; conviene guardar la fuente del clasificador.",
        "- Con 183 etiquetas no alcanza para **entrenar** un modelo de categorías (hay categorías con < 20 positivos).",
        "  Siguiente paso: etiquetar más (idealmente dos personas, para medir acuerdo con kappa) y entrenar como en `02_modelo.py`.",
    ]
    (AQUI / "resultados/reporte_categorias.md").write_text("\n".join(reporte) + "\n", encoding="utf-8")
    print("→ resultados/reporte_categorias.md · figuras/04_f1_categorias.png")


if __name__ == "__main__":
    main()

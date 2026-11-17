"""
03 · Aprendizaje no supervisado: K-means sobre el perfil de las 33 sucursales.

Pregunta: ¿hay «tipos» de sucursal que se parezcan en reputación más allá de su región?
Cada sucursal se describe con variables agregadas de sus reseñas, se estandarizan
(z-score, K-means usa distancia euclidiana) y k se elige con silueta + codo.
PCA solo sirve para dibujar los grupos en 2D.

Entrada:  datos/resenas_limpias.csv
Salida:   resultados/reporte_clusters.md, figuras/03_*.png, datos/perfil_tiendas.csv
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

AQUI = Path(__file__).resolve().parent
SEMILLA = 42
MIN_RESENAS = 50
NOCHE, GRIS = "#070A19", "#9AA0B4"
COLORES = ["#E0A040", "#5B74C9", "#3FA796", "#C2577A", "#8A6FD1", "#6B7A90"]
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRIS, "figure.dpi": 140, "savefig.bbox": "tight"})

VARIABLES = {
    "log_resenas": "Volumen (log de reseñas)",
    "media": "Calificación media",
    "pct_negativas": "% negativas (≤2★)",
    "pct_con_texto": "% con texto",
    "pct_q_servicio": "% de quejas por servicio",
    "pct_q_calidad": "% de quejas por calidad",
    "tendencia": "Media últimos 12 meses − media previa",
}


M_PRIOR = 10  # misma idea que el Brillo (js/rosa.js): el prior pesa como 10 quejas


def contraer(quejas: pd.DataFrame, col: str) -> pd.Series:
    """Proporción con contracción bayesiana hacia la proporción global.
    Una tienda con 1 queja de servicio no debe salir con «100 % servicio»."""
    global_ = quejas[col].astype(float).mean()
    g = quejas.groupby("location_id")[col]
    n, k = g.size(), g.sum().astype(float)
    return (k + M_PRIOR * global_) / (n + M_PRIOR) * 100


def perfil(df: pd.DataFrame) -> pd.DataFrame:
    hace12 = df["published_at"].max() - pd.DateOffset(months=12)
    quejas = df[df["clf_es_queja"] == True]  # noqa: E712 (columna con nulos)
    g = df.groupby("location_id")
    p = pd.DataFrame({
        "tienda": g["tienda"].first(),
        "region": g["region"].first(),
        "resenas": g.size(),
        "media": g["stars"].mean(),
        "pct_negativas": g["negativa"].mean() * 100,
        "pct_con_texto": g["tiene_texto"].mean() * 100,
        "pct_q_servicio": contraer(quejas, "clf_servicio"),
        "pct_q_calidad": contraer(quejas, "clf_calidad"),
        "tendencia": df[df["published_at"] >= hace12].groupby("location_id")["stars"].mean()
                     - df[df["published_at"] < hace12].groupby("location_id")["stars"].mean(),
    })
    p["log_resenas"] = np.log10(p["resenas"])
    return p


def main() -> None:
    (AQUI / "figuras").mkdir(exist_ok=True)
    (AQUI / "resultados").mkdir(exist_ok=True)
    df = pd.read_csv(AQUI / "datos/resenas_limpias.csv")
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, format="ISO8601")

    p = perfil(df)
    excluidas = p[p["resenas"] < MIN_RESENAS]
    p = p[p["resenas"] >= MIN_RESENAS].copy()
    faltan = p[list(VARIABLES)].isna().sum()
    p[list(VARIABLES)] = p[list(VARIABLES)].fillna(p[list(VARIABLES)].median())  # imputación por mediana
    print(f"Sucursales: {len(p)} (excluidas por < {MIN_RESENAS} reseñas: {len(excluidas)}) · nulos imputados: {int(faltan.sum())}")

    Z = StandardScaler().fit_transform(p[list(VARIABLES)])

    # Selección de k
    ks = range(2, 7)
    inercias, siluetas = [], []
    for k in ks:
        km = KMeans(k, n_init=50, random_state=SEMILLA).fit(Z)
        inercias.append(km.inertia_)
        siluetas.append(silhouette_score(Z, km.labels_))
    k = list(ks)[int(np.argmax(siluetas))]
    print("Silueta por k:", {kk: round(s, 3) for kk, s in zip(ks, siluetas)}, "→ k =", k)

    km = KMeans(k, n_init=50, random_state=SEMILLA).fit(Z)
    p["grupo"] = km.labels_
    # Ordenar grupos de mejor a peor calificación media para que el número signifique algo
    orden = p.groupby("grupo")["media"].mean().sort_values(ascending=False).index
    p["grupo"] = p["grupo"].map({g: i + 1 for i, g in enumerate(orden)})
    p.sort_values(["grupo", "media"], ascending=[True, False]).to_csv(AQUI / "datos/perfil_tiendas.csv")

    # Figuras
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    a1.plot(list(ks), inercias, "o-", color=NOCHE); a1.set(title="Codo (inercia)", xlabel="k")
    a2.plot(list(ks), siluetas, "o-", color=COLORES[0]); a2.axvline(k, color=GRIS, ls="--")
    a2.set(title="Silueta (más alto = grupos más claros)", xlabel="k")
    fig.savefig(AQUI / "figuras/03_eleccion_k.png"); plt.close(fig)

    pca = PCA(2, random_state=SEMILLA).fit(Z)
    xy = pca.transform(Z)
    fig, ax = plt.subplots(figsize=(8, 6))
    for g in sorted(p["grupo"].unique()):
        m = (p["grupo"] == g).to_numpy()
        ax.scatter(xy[m, 0], xy[m, 1], s=40 + 60 * p["log_resenas"][m], color=COLORES[g - 1], alpha=.85,
                   edgecolor="white", lw=1, label=f"Grupo {g}")
    for (x, yv), nombre in zip(xy, p["tienda"]):
        ax.annotate(nombre, (x, yv), fontsize=7.5, xytext=(4, 3), textcoords="offset points", color=NOCHE)
    v = pca.explained_variance_ratio_
    ax.set(xlabel=f"Componente 1 ({v[0]:.0%} de la varianza)", ylabel=f"Componente 2 ({v[1]:.0%})",
           title=f"Sucursales agrupadas por K-means (k = {k}) · tamaño = volumen")
    ax.legend(frameon=False)
    fig.savefig(AQUI / "figuras/03_clusters_pca.png"); plt.close(fig)

    # Perfil de cada grupo en unidades originales
    perfil_g = p.groupby("grupo")[list(VARIABLES) + ["resenas"]].mean()
    perfil_g["sucursales"] = p.groupby("grupo").size()
    cargas = pd.DataFrame(pca.components_.T, index=[VARIABLES[c] for c in VARIABLES], columns=["C1", "C2"])

    filas = [f"| {g} | {int(r.sucursales)} | {r.resenas:,.0f} | {r.media:.2f} | {r.pct_negativas:.1f} | "
             f"{r.pct_con_texto:.0f} | {r.pct_q_servicio:.0f} | {r.pct_q_calidad:.0f} | {r.tendencia:+.2f} |"
             for g, r in perfil_g.iterrows()]
    miembros = [f"- **Grupo {g}:** " + ", ".join(sub.sort_values('media', ascending=False)["tienda"])
                for g, sub in p.groupby("grupo")]
    reporte = [
        "# Reporte de clustering · K-means sobre sucursales",
        "",
        f"- {len(p)} sucursales con ≥ {MIN_RESENAS} reseñas; {len(excluidas)} excluidas por poco volumen"
        + (f" ({', '.join(excluidas['tienda'])})." if len(excluidas) else "."),
        f"- {len(VARIABLES)} variables estandarizadas (z-score). Nulos imputados con la mediana: {int(faltan.sum())}.",
        f"- k elegido por silueta máxima: **k = {k}** (silueta {max(siluetas):.3f}). "
        "Silueta < 0.25 indica estructura débil; < 0.5, moderada.",
        f"- PCA: los dos primeros componentes explican {v.sum():.0%} de la varianza (solo para graficar).",
        "",
        "## Perfil promedio de cada grupo (ordenados de mejor a peor media)",
        "",
        "| Grupo | Sucursales | Reseñas | Media ★ | % neg. | % texto | % q. servicio | % q. calidad | Tendencia |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        *filas,
        "",
        "## Integrantes",
        "",
        *miembros,
        "",
        "## Cargas del PCA",
        "",
        "| Variable | C1 | C2 |",
        "|---|---:|---:|",
        *[f"| {i} | {r.C1:+.2f} | {r.C2:+.2f} |" for i, r in cargas.iterrows()],
        "",
        "## Advertencias",
        "",
        "- K-means aquí es **exploratorio**: con ~30 puntos no hay «verdad» contra la cual validar.",
        "- `% de quejas por servicio/calidad` viene de la clasificación guardada, que mezcla Gemini y el léxico local,"
        " y se contrae hacia la media global con m = 10 (igual que el Brillo) porque varias tiendas tienen < 10 quejas.",
        "- 2026 concentra más de la mitad de las reseñas con media muy alta (probable campaña de solicitud):"
        " la `tendencia` refleja eso en todas las tiendas.",
        "- Los grupos dependen de las variables elegidas; otra selección daría otros grupos.",
    ]
    (AQUI / "resultados/reporte_clusters.md").write_text("\n".join(reporte) + "\n", encoding="utf-8")
    print(perfil_g.round(2).to_string())
    print("→ resultados/reporte_clusters.md · figuras/03_*.png")


if __name__ == "__main__":
    main()

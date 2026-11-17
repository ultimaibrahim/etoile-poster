"""
03 · Aprendizaje no supervisado: K-means sobre el perfil reciente de las sucursales.

Pregunta: ¿hay sucursales que se separen solas como «en riesgo», sin decirle al algoritmo cuáles?
Ventana: últimos 12 meses (la distribución cambió mucho entre años; ver 01 y 02).
Cinco variables por sucursal, estandarizadas (z-score) porque K-means mide distancias:
  log10 del volumen · calificación media · % de quejas (1–2★ con texto) · % sin texto · % publicadas desde las 20:00
k se elige con el coeficiente de silueta; k-means++ con 30 inicios y semilla fija.
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
SEMILLA, INICIOS = 42, 30
MIN_RESENAS = 15
MESES = 12
NOCHE, GRIS, AZUL, CORAL = "#070A19", "#9AA0B4", "#5B74C9", "#D9643F"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRIS, "figure.dpi": 140, "savefig.bbox": "tight"})

VARIABLES = {
    "log_volumen": "Volumen (log10 de reseñas)",
    "media": "Calificación media",
    "pct_quejas": "% de quejas (1–2★ con texto)",
    "pct_sin_texto": "% sin texto",
    "pct_noche": "% publicadas desde las 20:00",
}


def perfil(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(queja=df["negativa"] & df["tiene_texto"], noche=df["hora"] >= 20)
    g = df.groupby("location_id")
    p = pd.DataFrame({
        "resenas": g.size(),
        "media": g["stars"].mean(),
        "pct_quejas": g["queja"].mean() * 100,
        "pct_sin_texto": (1 - g["tiene_texto"].mean()) * 100,
        "pct_noche": g["noche"].mean() * 100,
    })
    p["log_volumen"] = np.log10(p["resenas"])
    return p


def main() -> None:
    (AQUI / "figuras").mkdir(exist_ok=True)
    (AQUI / "resultados").mkdir(exist_ok=True)
    df = pd.read_csv(AQUI / "datos/resenas_limpias.csv")
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, format="ISO8601")
    fin = df["published_at"].max()
    inicio = fin - pd.DateOffset(months=MESES)
    df = df[df["published_at"] >= inicio]

    p = perfil(df)
    excluidas = p[p["resenas"] < MIN_RESENAS]
    p = p[p["resenas"] >= MIN_RESENAS].copy()
    print(f"Ventana {inicio:%Y-%m-%d} → {fin:%Y-%m-%d} · sucursales: {len(p)} (excluidas: {len(excluidas)})")

    Z = StandardScaler().fit_transform(p[list(VARIABLES)])

    ks = range(2, 7)
    modelos = {k: KMeans(k, n_init=INICIOS, random_state=SEMILLA).fit(Z) for k in ks}
    siluetas = {k: silhouette_score(Z, m.labels_) for k, m in modelos.items()}
    k = max(siluetas, key=siluetas.get)
    print("Silueta:", {kk: round(s, 3) for kk, s in siluetas.items()}, "→ k =", k)

    p["grupo"] = modelos[k].labels_
    orden = p.groupby("grupo")["media"].mean().sort_values(ascending=False).index
    p["grupo"] = p["grupo"].map({g: i + 1 for i, g in enumerate(orden)})
    p.sort_values(["grupo", "media"], ascending=[True, False]).to_csv(AQUI / "datos/perfil_tiendas.csv")

    # Figuras
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    a1.plot(list(ks), [modelos[kk].inertia_ for kk in ks], "o-", color=NOCHE)
    a1.set(title="Codo (inercia)", xlabel="k")
    a2.plot(list(ks), [siluetas[kk] for kk in ks], "o-", color=AZUL)
    a2.axhline(0.25, color=GRIS, ls=":", lw=1)
    a2.axvline(k, color=GRIS, ls="--")
    a2.set(title="Silueta (bajo 0.25 = estructura débil)", xlabel="k")
    fig.savefig(AQUI / "figuras/03_eleccion_k.png"); plt.close(fig)

    pca = PCA(2, random_state=SEMILLA).fit(Z)
    xy = pca.transform(Z)
    colores = [AZUL, CORAL, "#3FA796", "#8A6FD1", "#E0A040", "#6B7A90"]
    fig, ax = plt.subplots(figsize=(8, 6))
    for g in sorted(p["grupo"].unique()):
        m = (p["grupo"] == g).to_numpy()
        ax.scatter(xy[m, 0], xy[m, 1], s=30 + 50 * p["log_volumen"][m], color=colores[g - 1], alpha=.85,
                   edgecolor="white", lw=1, label=f"Grupo {g} ({m.sum()} sucursales)")
    for (x, yv), nombre in zip(xy, p.index):
        ax.annotate(nombre, (x, yv), fontsize=7.5, xytext=(4, 3), textcoords="offset points", color=NOCHE)
    v = pca.explained_variance_ratio_
    ax.set(xlabel=f"Componente 1 ({v[0]:.0%} de la varianza)", ylabel=f"Componente 2 ({v[1]:.0%})",
           title=f"K-means (k = {k}) sobre los últimos {MESES} meses · tamaño = volumen")
    ax.legend(frameon=False)
    fig.savefig(AQUI / "figuras/03_clusters_pca.png"); plt.close(fig)

    perfil_g = p.groupby("grupo")[list(VARIABLES) + ["resenas"]].mean()
    perfil_g["sucursales"] = p.groupby("grupo").size()
    cargas = pd.DataFrame(pca.components_.T, index=list(VARIABLES.values()), columns=["C1", "C2"])
    filas = [f"| {g} | {int(r.sucursales)} | {r.resenas:,.0f} | {r.media:.2f} | {r.pct_quejas:.1f} | "
             f"{r.pct_sin_texto:.0f} | {r.pct_noche:.0f} |" for g, r in perfil_g.iterrows()]
    reporte = [
        "# Reporte de clustering · K-means sobre sucursales",
        "",
        f"- Ventana: {inicio:%Y-%m-%d} → {fin:%Y-%m-%d} (últimos {MESES} meses).",
        f"- {len(p)} sucursales con ≥ {MIN_RESENAS} reseñas en la ventana; {len(excluidas)} excluidas.",
        f"- {len(VARIABLES)} variables estandarizadas (z-score): " + ", ".join(VARIABLES.values()) + ".",
        f"- k-means++ con {INICIOS} inicios por k y semilla {SEMILLA}. k elegido por silueta máxima: **k = {k}**.",
        "",
        "| k | Silueta | Inercia |",
        "|---:|---:|---:|",
        *[f"| {kk} | {siluetas[kk]:.3f} | {modelos[kk].inertia_:.0f} |" for kk in ks],
        "",
        "## Perfil promedio de cada grupo",
        "",
        "| Grupo | Sucursales | Reseñas | Media ★ | % quejas | % sin texto | % desde 20:00 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *filas,
        "",
        "## Integrantes",
        "",
        *[f"- **Grupo {g}:** " + ", ".join(sub.sort_values("media", ascending=False).index)
          for g, sub in p.groupby("grupo")],
        "",
        "## Cargas del PCA (solo para graficar)",
        "",
        "| Variable | C1 | C2 |",
        "|---|---:|---:|",
        *[f"| {i} | {r.C1:+.2f} | {r.C2:+.2f} |" for i, r in cargas.iterrows()],
        "",
        "## Advertencias",
        "",
        "- Exploratorio: con ~30 puntos no hay etiquetas contra las cuales validar los grupos.",
        "- Las sucursales del grupo de menor media tienen pocas reseñas en la ventana: su señal es menos firme.",
        "- Con k ≥ 3 la silueta cae bajo 0.25: lo defendible es una sola separación.",
        "- Otra selección de variables o de ventana daría otros grupos.",
    ]
    (AQUI / "resultados/reporte_clusters.md").write_text("\n".join(reporte) + "\n", encoding="utf-8")
    print(perfil_g.round(2).to_string())
    print("→ resultados/reporte_clusters.md · figuras/03_*.png")


if __name__ == "__main__":
    main()

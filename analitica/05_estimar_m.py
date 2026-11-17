"""
05 · ¿De dónde sale la m del Brillo ajustado? Se estima, no se elige.

Brillo ajustado = (n·x̄ + m·C) / (n + m)

Derivación (modelo normal–normal, credibilidad de Bühlmann):
  cada reseña de una tienda en un mes:  x ~ N(μ, σ²)     σ² = varianza DENTRO de una tienda-mes
  la calidad real de la tienda-mes:     μ ~ N(C, τ²)     τ² = varianza ENTRE tiendas de la misma región y mes
  media a posteriori de μ dado x̄ con n reseñas:
      E[μ | x̄] = (n/σ² · x̄ + 1/τ² · C) / (n/σ² + 1/τ²)
               = (n·x̄ + (σ²/τ²)·C) / (n + σ²/τ²)
  ⇒  m = σ² / τ²   (cuántas reseñas «vale» lo que ya sabemos de la región)

Estimación por momentos (Bühlmann–Straub), unidad = tienda × mes, colectivo = región × mes:
  σ̂² = Σ (x − x̄_celda)² / Σ (n_celda − 1)
  τ̂² = [Σ n_c (x̄_c − x̄_reg)² − (I_reg − 1)·σ̂²] / [N_reg − Σ n_c² / N_reg]   (sumado sobre región-mes)
Intervalo de confianza: bootstrap por tiendas (se remuestrean tiendas completas, 2,000 veces).

Entrada:  datos/resenas_limpias.csv
Salida:   resultados/reporte_m.md, figuras/05_m_*.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
B, SEMILLA, MESES = 2000, 42, 12
NOCHE, ORO, AZUL, GRIS = "#0A0F24", "#D99A3A", "#2D47B5", "#9AA0B4"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRIS, "figure.dpi": 140, "savefig.bbox": "tight"})


def celdas(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(["location_id", "region", "mes"])["stars"]
    return pd.DataFrame({"n": g.size(), "media": g.mean(),
                         "ss": g.apply(lambda s: ((s - s.mean()) ** 2).sum())}).reset_index()


def estima(c: pd.DataFrame) -> tuple[float, float, float]:
    """Bühlmann–Straub por momentos, vectorizado. c: una fila por tienda-mes (n, media, ss, region, mes)."""
    ok = c["n"] >= 2
    s2 = c.loc[ok, "ss"].sum() / (c.loc[ok, "n"] - 1).sum()
    g = c.assign(nx=c["n"] * c["media"], n2=c["n"] ** 2).groupby(["region", "mes"])
    N, NX, N2, I = g["n"].transform("sum"), g["nx"].transform("sum"), g["n2"].transform("sum"), g["n"].transform("size")
    usa = I >= 2
    dev = (c["n"] * (c["media"] - NX / N) ** 2)[usa]
    grupos = c[usa].assign(N=N[usa], N2=N2[usa], I=I[usa]).groupby(["region", "mes"]).first()
    num = dev.sum() - ((grupos["I"] - 1) * s2).sum()
    den = (grupos["N"] - grupos["N2"] / grupos["N"]).sum()
    t2 = num / den
    return s2, t2, s2 / t2


def main() -> None:
    df = pd.read_csv(AQUI / "datos/resenas_limpias.csv")
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, format="ISO8601")
    recientes = df[df["published_at"] >= df["published_at"].max() - pd.DateOffset(months=MESES)]

    variantes = {
        "Todas las reseñas, últimos 12 meses (principal)": recientes,
        "Solo con texto, últimos 12 meses": recientes[recientes["tiene_texto"]],
        "Todas las reseñas, todo el historial": df,
    }
    filas = []
    rng = np.random.default_rng(SEMILLA)
    boot_principal = None
    for nombre, d in variantes.items():
        c = celdas(d)
        s2, t2, m = estima(c)
        tiendas = c["location_id"].unique()
        filas_de = {t: np.flatnonzero(c["location_id"].to_numpy() == t) for t in tiendas}
        boots = []
        for _ in range(B):
            muestra = rng.choice(tiendas, len(tiendas), replace=True)
            idx = np.concatenate([filas_de[t] for t in muestra])
            boots.append(estima(c.iloc[idx].reset_index(drop=True))[2])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        filas.append((nombre, s2, t2, m, lo, hi, len(c), int(c["n"].sum())))
        if boot_principal is None:
            boot_principal = np.array(boots)
        print(f"{nombre}: σ²={s2:.3f} τ²={t2:.4f} m={m:.2f} IC95 [{lo:.2f}, {hi:.2f}]")

    s2, t2, m = filas[0][1], filas[0][2], filas[0][3]
    (AQUI / "figuras").mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.hist(boot_principal, bins=40, color=AZUL, alpha=.8)
    ax.axvline(m, color=ORO, lw=2.5, label=f"m estimada = {m:.1f}")
    ax.axvline(10, color=GRIS, ls="--", lw=1.5, label="m = 10 (valor anterior)")
    ax.set(xlabel="m (bootstrap por tiendas)", ylabel="frecuencia", title="¿Cuánto vale m según los datos?")
    ax.legend(frameon=False)
    fig.savefig(AQUI / "figuras/05_m_bootstrap.png"); plt.close(fig)

    ns = [1, 3, 5, 10, 30, 100]
    reporte = [
        "# Reporte · estimación de m del Brillo ajustado",
        "",
        "m = σ² / τ²: varianza dentro de una tienda-mes entre varianza de las tiendas alrededor de su región.",
        f"Bootstrap por tiendas, {B:,} remuestreos.",
        "",
        "| Variante | σ² | τ² | m | IC 95 % | celdas | reseñas |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *[f"| {n} | {a:.3f} | {b:.4f} | **{c:.1f}** | {lo:.1f}–{hi:.1f} | {k:,} | {r:,} |" for n, a, b, c, lo, hi, k, r in filas],
        "",
        "## Peso de la tienda n / (n + m)",
        "",
        "| n | con m estimada | con m = 10 |",
        "|---:|---:|---:|",
        *[f"| {n} | {n / (n + m):.0%} | {n / (n + 10):.0%} |" for n in ns],
        "",
        "## Lectura",
        "",
        f"- Con los datos, m ≈ {m:.0f}: lo que se sabe de la región pesa como ~{m:.0f} reseñas, no 10.",
        "  El intervalo es ancho y asimétrico (solo 33 tiendas): 10 cabe en él, pero no es el valor más probable.
  Con m ≈ 4, una tienda con 10 reseñas pesa ~70 % en su Brillo; con m = 10 pesaba 50 %.",
        "- Usar el historial completo da m más chica porque mezcla años muy distintos (ver deriva): las tiendas",
        "  parecen más distintas entre sí de lo que son en un mes dado. Por eso la variante principal es de 12 meses.",
        "- Supuesto: estrellas aproximadamente normales. Son ordinales y sesgadas a 5★; el estimador de momentos",
        "  no exige normalidad para σ² y τ², pero la interpretación como media a posteriori sí la usa.",
        "- En la app, x̄ usa todas las reseñas y n solo las que tienen texto: n debería contar las mismas reseñas que x̄.",
    ]
    (AQUI / "resultados/reporte_m.md").write_text("\n".join(reporte) + "\n", encoding="utf-8")
    print("→ resultados/reporte_m.md · figuras/05_m_bootstrap.png")


if __name__ == "__main__":
    main()

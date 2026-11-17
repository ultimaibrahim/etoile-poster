# Reporte de clustering · K-means sobre sucursales

- 32 sucursales con ≥ 50 reseñas; 1 excluidas por poco volumen (S32).
- 7 variables estandarizadas (z-score). Nulos imputados con la mediana: 1.
- k elegido por silueta máxima: **k = 3** (silueta 0.225). Silueta < 0.25 indica estructura débil; < 0.5, moderada.
- PCA: los dos primeros componentes explican 60% de la varianza (solo para graficar).

## Perfil promedio de cada grupo (ordenados de mejor a peor media)

| Grupo | Sucursales | Reseñas | Media ★ | % neg. | % texto | % q. servicio | % q. calidad | Tendencia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16 | 218 | 4.58 | 9.2 | 76 | 75 | 58 | +0.89 |
| 2 | 11 | 650 | 4.54 | 7.9 | 61 | 81 | 47 | +0.98 |
| 3 | 5 | 95 | 4.20 | 19.1 | 81 | 79 | 50 | +0.86 |

## Integrantes

- **Grupo 1:** S31, S09, S10, S12, S15, S27, S24, S26, S28, S11, S21, S16, S19, S29, S13, S06
- **Grupo 2:** S17, S14, S03, S22, S05, S04, S07, S30, S23, S33, S01
- **Grupo 3:** S20, S18, S02, S08, S25

## Cargas del PCA

| Variable | C1 | C2 |
|---|---:|---:|
| Volumen (log de reseñas) | -0.50 | -0.20 |
| Calificación media | -0.52 | +0.32 |
| % negativas (≤2★) | +0.60 | -0.18 |
| % con texto | +0.31 | +0.35 |
| % de quejas por servicio | -0.07 | -0.53 |
| % de quejas por calidad | +0.04 | +0.65 |
| Media últimos 12 meses − media previa | -0.12 | -0.02 |

## Advertencias

- K-means aquí es **exploratorio**: con ~30 puntos no hay «verdad» contra la cual validar.
- `% de quejas por servicio/calidad` viene de la clasificación guardada, que mezcla Gemini y el léxico local, y se contrae hacia la media global con m = 10 (igual que el Brillo) porque varias tiendas tienen < 10 quejas.
- 2026 concentra más de la mitad de las reseñas con media muy alta (probable campaña de solicitud): la `tendencia` refleja eso en todas las tiendas.
- Los grupos dependen de las variables elegidas; otra selección daría otros grupos.

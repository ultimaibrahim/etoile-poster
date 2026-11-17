# Reporte de clustering · K-means sobre sucursales

- Ventana: 2025-11-17 → 2026-11-17 (últimos 12 meses).
- 33 sucursales con ≥ 15 reseñas en la ventana; 0 excluidas.
- 5 variables estandarizadas (z-score): Volumen (log10 de reseñas), Calificación media, % de quejas (1–2★ con texto), % sin texto, % publicadas desde las 20:00.
- k-means++ con 30 inicios por k y semilla 42. k elegido por silueta máxima: **k = 2**.

| k | Silueta | Inercia |
|---:|---:|---:|
| 2 | 0.397 | 106 |
| 3 | 0.220 | 82 |
| 4 | 0.201 | 70 |
| 5 | 0.231 | 58 |
| 6 | 0.293 | 48 |

## Perfil promedio de cada grupo

| Grupo | Sucursales | Reseñas | Media ★ | % quejas | % sin texto | % desde 20:00 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 27 | 246 | 4.80 | 3.7 | 26 | 22 |
| 2 | 6 | 64 | 4.17 | 17.0 | 13 | 17 |

## Integrantes

- **Grupo 1:** S29, S09, S31, S17, S26, S14, S07, S04, S19, S16, S30, S11, S10, S05, S27, S06, S22, S20, S23, S28, S13, S15, S21, S33, S03, S24, S08
- **Grupo 2:** S12, S02, S01, S25, S18, S32

## Cargas del PCA (solo para graficar)

| Variable | C1 | C2 |
|---|---:|---:|
| Volumen (log10 de reseñas) | -0.47 | -0.08 |
| Calificación media | -0.56 | +0.06 |
| % de quejas (1–2★ con texto) | +0.57 | -0.07 |
| % sin texto | -0.33 | -0.58 |
| % publicadas desde las 20:00 | -0.19 | +0.80 |

## Advertencias

- Exploratorio: con ~30 puntos no hay etiquetas contra las cuales validar los grupos.
- Las sucursales del grupo de menor media tienen pocas reseñas en la ventana: su señal es menos firme.
- Con k ≥ 3 la silueta cae bajo 0.25: lo defendible es una sola separación.
- Otra selección de variables o de ventana daría otros grupos.

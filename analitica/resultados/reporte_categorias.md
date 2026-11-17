# Reporte · evaluación de categorías de queja

- Muestra etiquetada: 183 reseñas (183 encontradas en la base actual). Estratificada: **no representa la población**,
  así que las cifras valen para comparar métodos, no para estimar cuántas quejas hay de cada tipo.
- Etiquetas a ciegas por una IA con criterios escritos; una sola etiquetadora, sin kappa.
- IC 95 % por bootstrap (2,000 remuestreos). El léxico v2 se ajustó mirando **dev**; la cifra honesta es **test**.

## Conjunto de prueba (test)

| Categoría | Método | n | Precisión | Recall | F1 | IC 95 % | VP/FP/FN |
|---|---|---:|---:|---:|---:|---:|---:|
| Servicio / espera | Léxico v2 | 91 | 0.89 | 0.84 | **0.86** | 0.77–0.94 | 32/4/6 |
| Servicio / espera | Guardada en la base | 73 | 0.78 | 0.71 | **0.75** | 0.62–0.85 | 25/7/10 |
| Calidad del producto | Léxico v2 | 91 | 0.55 | 0.65 | **0.59** | 0.38–0.77 | 11/9/6 |
| Calidad del producto | Guardada en la base | 73 | 0.45 | 0.87 | **0.59** | 0.39–0.75 | 13/16/2 |
| Precio / porción | Léxico v2 | 91 | 0.86 | 1.00 | **0.92** | 0.67–1.00 | 6/1/0 |
| Precio / porción | Guardada en la base | 73 | 0.57 | 0.80 | **0.67** | 0.25–0.93 | 4/3/1 |

## Conjunto de desarrollo (dev, optimista: se usó para ajustar las reglas)

| Categoría | Método | n | Precisión | Recall | F1 | IC 95 % | VP/FP/FN |
|---|---|---:|---:|---:|---:|---:|---:|
| Servicio / espera | Léxico v2 | 92 | 0.88 | 1.00 | **0.94** | 0.87–0.99 | 37/5/0 |
| Servicio / espera | Guardada en la base | 70 | 0.76 | 0.94 | **0.84** | 0.74–0.92 | 31/10/2 |
| Calidad del producto | Léxico v2 | 92 | 0.73 | 0.89 | **0.80** | 0.64–0.92 | 16/6/2 |
| Calidad del producto | Guardada en la base | 70 | 0.54 | 0.82 | **0.65** | 0.46–0.81 | 14/12/3 |
| Precio / porción | Léxico v2 | 92 | 0.75 | 0.75 | **0.75** | 0.40–0.95 | 6/2/2 |
| Precio / porción | Guardada en la base | 70 | 0.55 | 1.00 | **0.71** | 0.36–0.92 | 6/5/0 |

## Lectura

- Los intervalos son anchos: con ~90 reseñas por conjunto, una diferencia de 0.1 en F1 puede ser ruido.
- «Guardada en la base» mezcla Gemini y el léxico sin registrar cuál; conviene guardar la fuente del clasificador.
- Con 183 etiquetas no alcanza para **entrenar** un modelo de categorías (hay categorías con < 20 positivos).
  Siguiente paso: etiquetar más (idealmente dos personas, para medir acuerdo con kappa) y entrenar como en `02_modelo.py`.

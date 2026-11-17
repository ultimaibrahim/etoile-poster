# Reporte de limpieza

Generado por `01_limpieza.py`. Rango: 2013-09-07 → 2026-11-17.

| Paso | Por qué | Filas |
|---|---|---:|
| Filas crudas exportadas | reviews_core completo (sin datos personales) | 11,148 |
| Duplicados por id eliminados | la llave de GBP debe ser única | 0 |
| Calificaciones fuera de 1–5 eliminadas | regla CHECK de la base, verificada aquí | 0 |
| Reseñas sin tienda válida eliminadas | integridad referencial | 0 |
| Fechas en el futuro | control de calidad del reloj | 0 |
| Reseñas sin texto (solo estrellas) | se conservan para métricas, no sirven para NLP | 3,828 |
| Textos que eran solo emojis | quedan vacíos tras normalizar; bandera solo_emoji | 19 |
| Textos de 1–2 palabras («Excelente») | poca señal; bandera texto_corto | 980 |
| Reseñas en inglés | el léxico y el modelo son para español; bandera idioma | 80 |
| Texto largo repetido en la misma tienda | posible duplicado o spam; bandera texto_repetido | 62 |
| Reseñas editadas por el cliente | la calificación vigente es la última | 1,098 |
| Reseñas con texto sin clasificación guardada | backlog pendiente del clasificador | 3,099 |
| Sucursales y regiones anonimizadas | la cadena se presenta de forma anónima | 33 |
| Filas en el dataset limpio | una por reseña | 11,148 |

## Selección de variables

De la API de Google Business Profile se conservan: id, tienda, estrellas, texto, fechas de publicación,
edición y respuesta, si es Local Guide y la clasificación. **Se descartan en origen** nombre y foto del
cliente (datos personales que no aportan al análisis) y el JSON crudo de la API.

## Distribución de estrellas

| ★ | Reseñas | % |
|---|---:|---:|
| 1 | 759 | 6.8% |
| 2 | 209 | 1.9% |
| 3 | 360 | 3.2% |
| 4 | 937 | 8.4% |
| 5 | 8,883 | 79.7% |

Clases muy desbalanceadas: un modelo que dijera «todo es positivo» acertaría mucho sin servir.

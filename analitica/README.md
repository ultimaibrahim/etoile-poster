# Étoile · analítica (limpieza + ML)

Análisis académico **fuera de la app**: étoile en producción no entrena modelos. Estos scripts toman sus
datos reales y responden dos preguntas con aprendizaje automático. Los datos (`datos/*.csv`) no se publican:
`00_exportar.py` requiere acceso a la base, que es privada. Aquí quedan el código, los reportes y las figuras.

| Paso | Script | Qué hace | Sale |
|---|---|---|---|
| 0 | `00_exportar.py` | Descarga reseñas y tiendas por la API REST, **sin datos personales** | `datos/crudo_*.csv` |
| 1 | `01_limpieza.py` | Validación, fechas a hora local, normalización de texto, idioma, **anonimización de sucursales y regiones**, banderas de calidad, variables derivadas, aplanado del JSONB | `datos/resenas_limpias.csv`, `resultados/reporte_limpieza.md` |
| 2 | `02_modelo.py` | **Supervisado:** ¿reseña negativa (≤2★) por su texto? Léxico de Étoile vs. Naive Bayes vs. regresión logística (TF-IDF) | `resultados/reporte_modelo.md`, `figuras/02_*.png` |
| 3 | `03_clusters.py` | **No supervisado:** K-means sobre el perfil de las sucursales, k por silueta, PCA para graficar | `resultados/reporte_clusters.md`, `figuras/03_*.png` |
| 4 | `04_evaluacion_categorias.py` | **Evaluación con etiquetas:** ¿acierta étoile de qué se queja el cliente (servicio, calidad, precio)? F1 con IC 95 % por bootstrap | `resultados/reporte_categorias.md`, `figuras/04_*.png` |

```bash
cd analitica
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python 00_exportar.py      # necesita SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en ../.env
.venv/bin/python 01_limpieza.py
.venv/bin/python 02_modelo.py
.venv/bin/python 03_clusters.py
.venv/bin/python 04_evaluacion_categorias.py   # necesita datos/etiquetas_categorias.csv (privado)
```

`lexico_etoile.py` es el clasificador por reglas de étoile portado a Python; da **exactamente** lo mismo que el
original en JavaScript en las 7,320 reseñas con texto (0 diferencias). **No se publica:** es parte del código
privado de étoile y sus palabras clave identificarían a la cadena. `02` y `04` lo importan.

## Decisiones que hay que saber defender
- **Etiqueta = estrellas, no la clasificación guardada.** La base no registra si una clasificación la hizo Gemini o el
  léxico, así que no es «verdad». Las estrellas las pone el cliente.
- **Fuera 3★** del entrenamiento (ambiguas) y **fuera textos repetidos** (si el mismo texto cae en train y test, la nota se infla).
- **Métrica F1 / PR-AUC, no exactitud:** 87 % de las reseñas son positivas; «siempre positiva» tiene 87 % de exactitud y F1 = 0.
- **El umbral se elige en validación**, nunca mirando el conjunto de prueba.
- **Contracción bayesiana** (m = 10, la misma del Brillo) en los % de queja por tienda: con 1 queja no se puede decir «100 % servicio».
- **Anonimato:** sucursales como `S01…S33` y regiones como `Región A…`; la llave queda en `datos/` y no se sube.
- **Sesgo temporal:** 2026 tiene más de la mitad de las reseñas (media 4.8) y 2024 tuvo media 2.97. Se prueba un split temporal.
- **Categorías (04):** muestra de 183 estratificada, etiquetada a ciegas por una IA sin segundo juez. Vale para comparar
  métodos, no para estimar proporciones. La cifra honesta es la de **test** (las reglas se ajustaron con dev).

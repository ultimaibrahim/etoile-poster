# Reporte del modelo · reseña negativa a partir del texto

- Datos: 7,221 reseñas con texto en español → 7,040 sin 3★ → **6,219** sin textos repetidos.
- Negativas (≤2★): 815 (13.1%). Partición 80/20 estratificada, semilla 42: 4,975 entrenamiento · 1,244 prueba.
- Hiperparámetros por validación cruzada de 5 pliegues (métrica PR-AUC): `{'clf__C': 100, 'tfidf__ngram_range': (1, 2)}`.
- Umbral de decisión elegido en validación (no en prueba): **0.52**.

## Resultados en el conjunto de prueba (clase positiva = reseña negativa)

| Modelo | Precisión | Recall | F1 | PR-AUC | Exactitud |
|---|---:|---:|---:|---:|---:|
| Siempre «positiva» | 0.000 | 0.000 | **0.000** | 0.131 | 0.869 |
| Léxico de Étoile (reglas) | 0.659 | 0.890 | **0.757** | 0.601 | 0.925 |
| Naive Bayes + TF-IDF | 0.919 | 0.908 | **0.914** | 0.966 | 0.977 |
| Regresión logística (umbral 0.5) | 0.901 | 0.890 | **0.895** | 0.962 | 0.973 |
| Regresión logística (umbral 0.52) | 0.900 | 0.883 | **0.892** | 0.962 | 0.972 |

## Robustez temporal

| Modelo | Precisión | Recall | F1 | PR-AUC | Exactitud |
|---|---:|---:|---:|---:|---:|
| Regresión logística (train < 2025, test ≥ 2025) | 0.777 | 0.877 | **0.824** | 0.915 | 0.966 |

## Lectura

- La exactitud engaña: «siempre positiva» tiene exactitud alta y F1 = 0. Por eso se reporta F1 y PR-AUC.
- El léxico es explicable pero rígido: solo da un punto en la curva. El modelo deja elegir el balance
  precisión/recall moviendo el umbral, y sus pesos se pueden leer (figura `02_palabras_peso.png`).
- Errores del modelo para análisis cualitativo: `datos/errores_modelo.csv` (35 filas, no se versiona).

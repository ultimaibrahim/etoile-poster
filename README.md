# étoile: de miles de reseñas de Google a alertas claras

Póster del proyecto integrador de **Saul Ibrahim Garcia Ochoa**, Centro Universitario de Guadalajara (CUGDL).

- **Póster (90 × 120 cm):** [`poster.pdf`](poster.pdf), y con 3 mm de sangrado para imprenta: [`poster_sangrado.pdf`](poster_sangrado.pdf)
- **Vista previa:** [`vista_previa.png`](vista_previa.png)

![Vista previa del póster](vista_previa.png)

## Qué es étoile
*étoile* quiere decir «estrella» en francés. Es un tablero que lee las reseñas de Google Maps de cada sucursal de una cadena de restaurantes y avisa **qué falla, dónde y a qué hora**. Cada sucursal es una estrella, cada región una constelación, y la estrella brilla más cuanto mejor la califican sus clientes.

El caso de aplicación es una cadena de restaurantes de **33 sucursales en 10 regiones**. Se presenta de forma anónima. El código de étoile es privado.

## El problema
Una cadena recibe miles de reseñas y casi todas son elogios. En el caso de estudio, **11 de cada 100** reseñas con texto son quejas. Antes las reseñas nuevas se descargaban cada 15 días; hoy llegan en una mediana de unas 3 horas (la meta de la sincronización es de 30 minutos, que todavía no se cumple en la práctica).

**Objetivos**
1. Cargar las reseñas sin duplicados.
2. Medir cuánto se equivoca el programa que etiqueta las quejas.
3. Comparar tiendas con pocas y muchas reseñas de forma justa.
4. Ver a qué hora y qué día se quejan más, y que cada rol vea solo lo suyo.

## Metodología
1. **Reunir.** Más de 7,300 reseñas con texto (primero con un servicio de descarga automática y luego con la API oficial de Google). Variables: estrellas, texto, fecha, hora y sucursal.
2. **Limpiar.** Se quitan duplicados y las reseñas de 1–2★ sin texto.
3. **Clasificar.** Un programa de reglas explicables lee el texto: palabras clave por tema, una ventana que detecta negaciones y reglas de contexto. Marca si la reseña es queja y si trata de servicio, calidad o precio.
4. **Medir.** Se etiquetaron **183 reseñas a ciegas** (antes de ver la salida del programa): 92 para ajustar las reglas y 91 para probarlas. Se reporta **F1** (nota de 0 a 100 % de acierto) con intervalos al 95 % por *bootstrap*. Las reseñas de prueba son posteriores a las de ajuste, porque los clientes cambian con el tiempo.
5. **Mostrar.** Un tablero web con alertas. Una base de datos Postgres impone los permisos por rol.

**Brillo ajustado.** Para comparar tiendas con distinto número de reseñas se usa un promedio que mezcla el de la tienda con el de su región: `(n · promedio + 10 · C) / (n + 10)`, donde `n` es el número de reseñas y `C` el promedio regional. Una tienda con 3 reseñas de 5★ no le gana a una con 300 reseñas de 4.8★.

## Resultados
F1 en las 91 reseñas de prueba, antes y después de corregir las reglas:

| Tema | Antes | Después | Intervalo al 95 % (después) |
|---|---|---|---|
| Servicio | 69 % | **89 %** | 80–96 % |
| Calidad | 57 % | 56 % | 32–73 % |
| Valor (precio) | 75 % | **92 %** | 67–100 % |

- **Calidad no mejoró.** Al marcar una queja de calidad acierta más (precisión de 44 a 53 %), pero detecta menos quejas reales (exhaustividad de 82 a 59 %). Falta analizar por qué; es la tarea pendiente.
- **Hora.** A las 21 h, 1 de cada 5 reseñas es queja; el promedio es 1 de cada 9.
- **Día.** Los sábados a las 21 h, 1 de cada 3 reseñas es queja (27 de 82). Es una sola celda del mapa de calor: el margen es amplio.
- **Cambio en el tiempo.** Hace dos años la proporción de quejas era mucho mayor que hoy, por eso se prueba con reseñas posteriores.

## Historia
- **Mayo 2026:** primer tablero. **Junio:** descarga automática de reseñas, cada 15 días. **Agosto:** ranking justo (brillo ajustado). **9 de octubre:** API oficial de Google. **20 de octubre:** producto para cualquier cadena. **9 de noviembre:** versión 2.2.

## Limitaciones
- Las etiquetas las hizo **una sola persona-IA**; no hay acuerdo entre etiquetadores (kappa).
- Las muestras son pequeñas: el margen de error es de ±20 puntos en varias cifras.
- La hora de una reseña es la de su publicación, no la de la visita; se calcula en la zona horaria de cada región.
- En el póster, el ejemplo de reseña es un fragmento editado de una real, y las tiendas A y B del brillo ajustado son imaginarias.
- Es un conjunto de reglas evaluado, no un modelo entrenado. El siguiente paso propuesto es una regresión logística con TF-IDF, comparada contra las reglas.

## Referencias
- Efron, B., & Tibshirani, R. J. (1993). *An introduction to the bootstrap*. Chapman & Hall.
- Fellegi, I. P., & Sunter, A. B. (1969). A theory for record linkage. *Journal of the American Statistical Association, 64*(328), 1183–1210. https://doi.org/10.1080/01621459.1969.10501049
- Gelman, A., Carlin, J. B., Stern, H. S., Dunson, D. B., Vehtari, A., & Rubin, D. B. (2013). *Bayesian data analysis* (3.ª ed.). CRC Press.

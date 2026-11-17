# Reporte · estimación de m del Brillo ajustado

m = σ² / τ²: varianza dentro de una tienda-mes entre varianza de las tiendas alrededor de su región.
Bootstrap por tiendas, 2,000 remuestreos.

| Variante | σ² | τ² | m | IC 95 % | celdas | reseñas |
|---|---:|---:|---:|---:|---:|---:|
| Todas las reseñas, últimos 12 meses (principal) | 0.475 | 0.1151 | **4.1** | 3.3–12.6 | 368 | 7,022 |
| Solo con texto, últimos 12 meses | 0.539 | 0.1503 | **3.6** | 3.2–11.2 | 359 | 5,089 |
| Todas las reseñas, todo el historial | 0.713 | 0.3433 | **2.1** | 2.3–8.9 | 1,276 | 11,148 |

## Peso de la tienda n / (n + m)

| n | con m estimada | con m = 10 |
|---:|---:|---:|
| 1 | 20% | 9% |
| 3 | 42% | 23% |
| 5 | 55% | 33% |
| 10 | 71% | 50% |
| 30 | 88% | 75% |
| 100 | 96% | 91% |

## Lectura

- Con los datos, m ≈ 4: lo que se sabe de la región pesa como ~4 reseñas, no 10.
  El intervalo es ancho y asimétrico (solo 33 tiendas): 10 cabe en él, pero no es el valor más probable.
  Con m ≈ 4, una tienda con 10 reseñas pesa ~70 % en su Brillo; con m = 10 pesaba 50 %.
- Usar el historial completo da m más chica porque mezcla años muy distintos (ver deriva): las tiendas
  parecen más distintas entre sí de lo que son en un mes dado. Por eso la variante principal es de 12 meses.
- Supuesto: estrellas aproximadamente normales. Son ordinales y sesgadas a 5★; el estimador de momentos
  no exige normalidad para σ² y τ², pero la interpretación como media a posteriori sí la usa.
- En la app, x̄ usa todas las reseñas y n solo las que tienen texto: n debería contar las mismas reseñas que x̄.

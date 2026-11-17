"""
02 · Modelo supervisado: ¿la reseña es negativa (≤2★)? a partir SOLO del texto.

Por qué esta etiqueta: la clasificación guardada en la base mezcla dos fuentes
(Gemini y el léxico local) sin registrar cuál fue, así que no es una «verdad».
Las estrellas sí lo son: las puso el propio cliente. Es aprendizaje supervisado
sin etiquetar a mano.

Modelos comparados (mismo conjunto de prueba):
  0. Línea base trivial: siempre «positiva» (DummyClassifier)
  1. Léxico de Étoile: la señal de inconformidad de classifyLocally
     (netlify/functions/classify-review.js) portada a Python. Reglas, no aprende.
  2. Naive Bayes multinomial + TF-IDF
  3. Regresión logística + TF-IDF (unigramas y bigramas), C y n-gramas por validación cruzada

Entrada:  datos/resenas_limpias.csv
Salida:   resultados/reporte_modelo.md, figuras/*.png, datos/errores_modelo.csv
"""
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

AQUI = Path(__file__).resolve().parent
SEMILLA = 42
NOCHE, ORO, AZUL, GRIS = "#070A19", "#E0A040", "#5B74C9", "#9AA0B4"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRIS, "axes.labelcolor": NOCHE, "text.color": NOCHE,
                     "figure.dpi": 140, "savefig.bbox": "tight"})

# Señal de inconformidad de classifyLocally (copiada del JS; el texto ya viene sin acentos y en minúsculas).
NEG = re.compile(
    r"\b(mal\w*|pesim\w*|horribl\w*|horrend\w*|asco|asquer\w*|fe[oa]s?|nefast\w*|terribl\w*|peor\w*|groser\w*|despot\w*|apatic\w*|deficien\w*|lent[oa]s?|tard\w*|demor\w*|espera\w*|esperar|nunca|jamas|falt\w*|olvid\w*|equivocad\w*|incomplet\w*|crud[oa]s?|fri[oa]s?|quemad\w*|ranci\w*|insipid\w*|aguad\w*|escas\w*|poc[oa]s?|pobre\w*|decepci\w*|empalag\w*|irrisori\w*|miseri\w*|echad\w*|suci[oa]s?|caro|caros|carisim\w*|estafa|abusiv\w*|robo|elevad\w*|alt[oa]s|disgust\w*|niega\w*|negaron|nego|ignor\w*|desanimo|hostil\w*|cancel\w*|rebajad\w*|diferente|disminuy\w*|reduc\w*|neutro|llorar|queja\w*|exagerad\w*|embarrad\w*|barrada)\b"
    r"|\bno (me|nos|te|le|lo|la|los|las|tienen|tenian|tenia|hay|dieron|atend\w*|vale\w*|sirv\w*|ponen|ponian|respet\w*|pusieron)\b"
    r"|\bsin (queso|salsa|sabor|champi\w*|fresas?|cambio|educacion)\b|que desear|a disgusto|bola de|sabia a|saben a|sabe a"
)


class Lexico:
    """Envoltura con la interfaz de sklearn para comparar en igualdad de condiciones."""
    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.array([bool(NEG.search(t)) for t in X])

    def predict_proba(self, X):
        p = self.predict(X).astype(float)
        return np.column_stack([1 - p, p])


def metricas(nombre, y, pred, prob):
    return {
        "Modelo": nombre,
        "Precisión": precision_score(y, pred, zero_division=0),
        "Recall": recall_score(y, pred),
        "F1": f1_score(y, pred),
        "PR-AUC": average_precision_score(y, prob),
        "Exactitud": (y == pred).mean(),
    }


def main() -> None:
    (AQUI / "figuras").mkdir(exist_ok=True)
    (AQUI / "resultados").mkdir(exist_ok=True)
    df = pd.read_csv(AQUI / "datos/resenas_limpias.csv")
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, format="ISO8601")  # offsets mixtos por horario de verano

    # ── Conjunto de modelado ──
    base = df[df["tiene_texto"] & ~df["solo_emoji"] & (df["idioma"] != "en")]
    n_texto = len(base)
    base = base[base["stars"] != 3]                       # 3★ es ambigua: fuera del entrenamiento binario
    sin_3 = len(base)
    base = base.drop_duplicates("texto_limpio")            # evita fuga: el mismo texto en train y test
    print(f"Reseñas con texto en español: {n_texto:,} · sin 3★: {sin_3:,} · sin textos repetidos: {len(base):,}")
    X, y = base["texto_limpio"].to_numpy(), base["negativa"].to_numpy()
    print(f"Negativas: {y.sum():,} ({y.mean():.1%})")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEMILLA)

    # ── Regresión logística con búsqueda de hiperparámetros (validación cruzada 5 pliegues, solo en train) ──
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
    logreg = GridSearchCV(
        Pipeline([("tfidf", TfidfVectorizer(min_df=2, sublinear_tf=True)),
                  ("clf", LogisticRegression(class_weight="balanced", max_iter=2000))]),
        {"tfidf__ngram_range": [(1, 1), (1, 2)], "clf__C": [1, 3, 10, 30, 100]},
        scoring="average_precision", cv=cv, n_jobs=-1,
    ).fit(Xtr, ytr)
    mejor = logreg.best_estimator_
    print("Mejores hiperparámetros:", logreg.best_params_)

    # Umbral elegido con predicciones fuera de pliegue del TRAIN (el test no se toca para decidir nada)
    oof = cross_val_predict(mejor, Xtr, ytr, cv=cv, method="predict_proba")[:, 1]
    p, r, u = precision_recall_curve(ytr, oof)
    f1s = 2 * p * r / np.clip(p + r, 1e-9, None)
    umbral = float(u[np.argmax(f1s[:-1])])
    print(f"Umbral que maximiza F1 en validación: {umbral:.2f}")

    nb = Pipeline([("tfidf", TfidfVectorizer(min_df=2, ngram_range=(1, 2), sublinear_tf=True)),
                   ("clf", MultinomialNB(alpha=0.1))]).fit(Xtr, ytr)
    dummy = DummyClassifier(strategy="most_frequent").fit(Xtr, ytr)
    lex = Lexico()

    prob_lr = mejor.predict_proba(Xte)[:, 1]
    filas = [
        metricas("Siempre «positiva»", yte, dummy.predict(Xte), dummy.predict_proba(Xte)[:, 1]),
        metricas("Léxico de Étoile (reglas)", yte, lex.predict(Xte), lex.predict_proba(Xte)[:, 1]),
        metricas("Naive Bayes + TF-IDF", yte, nb.predict(Xte), nb.predict_proba(Xte)[:, 1]),
        metricas("Regresión logística (umbral 0.5)", yte, prob_lr >= 0.5, prob_lr),
        metricas(f"Regresión logística (umbral {umbral:.2f})", yte, prob_lr >= umbral, prob_lr),
    ]
    tabla = pd.DataFrame(filas)
    print(tabla.round(3).to_string(index=False))

    # ── Prueba de robustez temporal: entrenar con el pasado, evaluar con 2025–2026 ──
    corte = pd.Timestamp("2025-01-01 06:00", tz="UTC")  # medianoche, hora del centro de México
    pasado = base["published_at"] < corte
    temp = mejor.fit(X[pasado.to_numpy()], y[pasado.to_numpy()])
    pt = temp.predict_proba(X[~pasado.to_numpy()])[:, 1]
    yt = y[~pasado.to_numpy()]
    temporal = metricas("Regresión logística (train < 2025, test ≥ 2025)", yt, pt >= umbral, pt)
    mejor.fit(Xtr, ytr)  # se restaura el modelo del split aleatorio

    # ── Figuras ──
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for nombre, prob, color in [("Regresión logística", prob_lr, ORO),
                                ("Naive Bayes", nb.predict_proba(Xte)[:, 1], AZUL)]:
        pp, rr, _ = precision_recall_curve(yte, prob)
        ax.plot(rr, pp, color=color, lw=2.2, label=f"{nombre} (AP {average_precision_score(yte, prob):.2f})")
    lx = filas[1]
    ax.scatter([lx["Recall"]], [lx["Precisión"]], color=NOCHE, zorder=5, s=50, label="Léxico de Étoile (un solo punto)")
    ax.axhline(yte.mean(), color=GRIS, ls="--", lw=1, label=f"Azar ({yte.mean():.0%} negativas)")
    ax.set(xlabel="Recall (negativas encontradas)", ylabel="Precisión (aciertos al marcar)",
           title="Curva precisión–recall en el conjunto de prueba", xlim=(0, 1.02), ylim=(0, 1.02))
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    fig.savefig(AQUI / "figuras/02_curva_pr.png"); plt.close(fig)

    cm = confusion_matrix(yte, prob_lr >= umbral)
    fig, ax = plt.subplots(figsize=(4.4, 3.8))
    ax.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=14, color="white" if v > cm.max() / 2 else NOCHE)
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Positiva", "Negativa"], yticklabels=["Positiva", "Negativa"],
           xlabel="Predicción", ylabel="Real", title="Matriz de confusión · regresión logística")
    fig.savefig(AQUI / "figuras/02_matriz_confusion.png"); plt.close(fig)

    vocab = mejor.named_steps["tfidf"].get_feature_names_out()
    coef = mejor.named_steps["clf"].coef_[0]
    orden = np.argsort(coef)
    top = np.r_[orden[:12], orden[-12:]]
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    ax.barh(range(len(top)), coef[top], color=[AZUL if c < 0 else ORO for c in coef[top]])
    ax.set_yticks(range(len(top)), vocab[top])
    ax.axvline(0, color=GRIS, lw=1)
    ax.set(xlabel="Peso en el modelo (← positiva · negativa →)", title="Lo que el modelo aprendió")
    fig.savefig(AQUI / "figuras/02_palabras_peso.png"); plt.close(fig)

    # ── Errores para revisar a mano (se queda local: *.csv está en .gitignore) ──
    err = pd.DataFrame({"texto": Xte, "real_negativa": yte, "prob_negativa": prob_lr})
    err = err[(err["prob_negativa"] >= umbral) != err["real_negativa"]].sort_values("prob_negativa")
    err.to_csv(AQUI / "datos/errores_modelo.csv", index=False)

    fmt = lambda d: f"| {d['Modelo']} | {d['Precisión']:.3f} | {d['Recall']:.3f} | **{d['F1']:.3f}** | {d['PR-AUC']:.3f} | {d['Exactitud']:.3f} |"
    reporte = [
        "# Reporte del modelo · reseña negativa a partir del texto",
        "",
        f"- Datos: {n_texto:,} reseñas con texto en español → {sin_3:,} sin 3★ → **{len(base):,}** sin textos repetidos.",
        f"- Negativas (≤2★): {y.sum():,} ({y.mean():.1%}). Partición 80/20 estratificada, semilla {SEMILLA}: "
        f"{len(ytr):,} entrenamiento · {len(yte):,} prueba.",
        f"- Hiperparámetros por validación cruzada de 5 pliegues (métrica PR-AUC): `{logreg.best_params_}`.",
        f"- Umbral de decisión elegido en validación (no en prueba): **{umbral:.2f}**.",
        "",
        "## Resultados en el conjunto de prueba (clase positiva = reseña negativa)",
        "",
        "| Modelo | Precisión | Recall | F1 | PR-AUC | Exactitud |",
        "|---|---:|---:|---:|---:|---:|",
        *[fmt(d) for d in filas],
        "",
        "## Robustez temporal",
        "",
        "| Modelo | Precisión | Recall | F1 | PR-AUC | Exactitud |",
        "|---|---:|---:|---:|---:|---:|",
        fmt(temporal),
        "",
        "## Lectura",
        "",
        "- La exactitud engaña: «siempre positiva» tiene exactitud alta y F1 = 0. Por eso se reporta F1 y PR-AUC.",
        "- El léxico es explicable pero rígido: solo da un punto en la curva. El modelo deja elegir el balance",
        "  precisión/recall moviendo el umbral, y sus pesos se pueden leer (figura `02_palabras_peso.png`).",
        f"- Errores del modelo para análisis cualitativo: `datos/errores_modelo.csv` ({len(err):,} filas, no se versiona).",
    ]
    (AQUI / "resultados/reporte_modelo.md").write_text("\n".join(reporte) + "\n", encoding="utf-8")
    print("→ resultados/reporte_modelo.md · figuras/02_*.png")


if __name__ == "__main__":
    main()

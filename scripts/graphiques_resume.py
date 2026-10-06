"""Calcule les statistiques compactes utilisées pour les fiches métier dynamiques."""
import json
import statistics
from collections import Counter
from pathlib import Path


def _salaire(offre):
    minimum, maximum = offre.get("smin"), offre.get("smax")
    if minimum is None:
        return None
    return (minimum + maximum) / 2 if maximum is not None else minimum


def statistiques(code, nom, date, offres, contrats):
    total = len(offres)
    comptes = Counter(offre.get("contrat") for offre in offres)
    valeurs = [_salaire(offre) for offre in offres]
    salaires = [valeur for valeur in valeurs if valeur is not None]
    moyenne = statistics.mean(salaires) if salaires else None
    ecart = statistics.stdev(salaires) if len(salaires) > 1 else None
    quartiles = statistics.quantiles(salaires, n=4, method="inclusive") if len(salaires) > 1 else []
    if salaires:
        minimum, maximum = min(salaires), max(salaires)
        largeur = 10_000
        debut = int(minimum // largeur) * largeur
        fin = (int(maximum // largeur) + 1) * largeur
        effectifs = [0] * max(1, (fin - debut) // largeur)
        for salaire in salaires:
            index = min(len(effectifs) - 1, int((salaire - debut) // largeur))
            effectifs[index] += 1
        histogramme = [
            {
                "debut": debut + index * largeur,
                "fin": debut + (index + 1) * largeur,
                "effectif": effectif,
            }
            for index, effectif in enumerate(effectifs)
        ]
    else:
        minimum = maximum = None
        histogramme = []
    return {
        "code": code,
        "nom": nom,
        "source_date": date,
        "total_offres": total,
        "contrats": [
            {
                "code": contrat,
                "nom": contrats.get(contrat) or (f"Autre ({contrat})" if contrat else "Non renseigné"),
                "effectif": effectif,
                "pourcentage": effectif / total * 100 if total else 0,
            }
            for contrat, effectif in sorted(comptes.items(), key=lambda item: (-item[1], item[0] or ""))
        ],
        "salaires": {
            "count": len(salaires),
            "missing": total - len(salaires),
            "mean": moyenne,
            "median": statistics.median(salaires) if salaires else None,
            "std": ecart,
            "std_ddof": 1,
            "minimum": minimum,
            "q1": quartiles[0] if quartiles else (salaires[0] if salaires else None),
            "q3": quartiles[2] if quartiles else (salaires[0] if salaires else None),
            "maximum": maximum,
            "coefficient_variation_percent": ecart / moyenne * 100 if ecart and moyenne else None,
            "mean_plus_minus_std": (
                {"lower": moyenne - ecart, "upper": moyenne + ecart} if ecart is not None else None
            ),
            "histogramme": histogramme,
        },
    }


def ecrire_analyse(dossier, code, nom, date, offres, contrats):
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    stats = statistiques(code, nom, date, offres, contrats)
    (dossier / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return stats

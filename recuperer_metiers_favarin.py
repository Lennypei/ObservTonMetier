#!/usr/bin/env python3
"""Télécharge les métiers publiés par l'Observatoire et génère leurs statistiques et graphiques.

Le site distant expose un seul data/resume.json avec la liste des métiers et les offres
actives de chacun. Le script le télécharge une fois, puis répartit les offres par code ROME.

Usage :
    python3 recuperer_metiers_favarin.py
"""

import json
import math
import re
import tempfile
from collections import Counter
from pathlib import Path
from statistics import mean, median, stdev
from urllib.error import URLError
from urllib.request import Request, urlopen

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SOURCE_URL = "https://vincentfavarin.github.io/metier/data/resume.json"
ROME_PATTERN = re.compile(r"^[A-Z][0-9]{4}$")
CONTRACT_NAMES = {
    "CDI": "CDI",
    "CDD": "CDD",
    "MIS": "Intérim",
    "TTI": "Intérim",
    "SAI": "Saisonnier",
    "FRA": "Franchise",
    "LIB": "Profession libérale",
    "CCE": "Profession commerciale",
    "DDI": "CDI de chantier",
    "DIN": "CDI intérimaire",
    "CDS": "CDD senior",
    "REP": "Reprise d’entreprise",
}


def download_source():
    request = Request(
        SOURCE_URL,
        headers={"User-Agent": "metier-dashboard/1.0 (+local analysis)"},
    )
    try:
        with urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"Téléchargement de la source impossible : HTTP {response.status}")
            payload = json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Impossible de récupérer ou lire {SOURCE_URL}: {error}") from error

    if not isinstance(payload.get("metiers"), list) or not isinstance(payload.get("offres"), list):
        raise ValueError("Le JSON distant ne contient pas les listes 'metiers' et 'offres' attendues.")
    return payload


def annual_salary(offer):
    minimum = offer.get("smin")
    maximum = offer.get("smax")
    if minimum is None:
        return None
    if maximum is not None:
        return (float(minimum) + float(maximum)) / 2
    return float(minimum)


def calculate_stats(metier, offers, source_date):
    contracts = Counter(
        (offer.get("contrat") or "").strip() or "Non renseigné" for offer in offers
    )
    salaries = [value for offer in offers if (value := annual_salary(offer)) is not None]
    salary_stats = {
        "count": len(salaries),
        "missing": len(offers) - len(salaries),
        "mean": mean(salaries) if salaries else None,
        "median": median(salaries) if salaries else None,
        "std": stdev(salaries) if len(salaries) >= 2 else None,
        "std_ddof": 1,
        "minimum": min(salaries) if salaries else None,
        "q1": float(np.percentile(salaries, 25, method="linear")) if salaries else None,
        "q3": float(np.percentile(salaries, 75, method="linear")) if salaries else None,
        "maximum": max(salaries) if salaries else None,
    }
    salary_stats["coefficient_variation_percent"] = (
        salary_stats["std"] / salary_stats["mean"] * 100
        if salary_stats["std"] is not None and salary_stats["mean"]
        else None
    )
    salary_stats["mean_plus_minus_std"] = (
        {
            "lower": salary_stats["mean"] - salary_stats["std"],
            "upper": salary_stats["mean"] + salary_stats["std"],
        }
        if salary_stats["std"] is not None
        else None
    )

    return {
        "code": metier["code"],
        "nom": metier["libelle"],
        "source_date": source_date,
        "total_offres": len(offers),
        "contrats": [
            {
                "code": code,
                "nom": CONTRACT_NAMES.get(code, code),
                "effectif": count,
                "pourcentage": count / len(offers) * 100 if offers else 0,
            }
            for code, count in sorted(contracts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "salaires": salary_stats,
    }


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def set_plot_style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.labelcolor": "#334155",
            "text.color": "#0f172a",
        }
    )


def plot_contracts(stats, output):
    counts = stats["contrats"]
    fig = plt.figure(figsize=(9, 5.5), facecolor="white")
    ax = fig.add_axes([0.30, 0.15, 0.63, 0.62])
    if not counts:
        ax.text(0.5, 0.5, "Aucune offre recensée", ha="center", va="center", color="#64748b")
        ax.set_axis_off()
    else:
        rows = counts[::-1]
        labels = [row["nom"] for row in rows]
        values = [row["effectif"] for row in rows]
        bars = ax.barh(labels, values, color="#3978a8", height=0.58)
        ax.set_xlabel("Nombre d’offres")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_xlim(0, max(values) * 1.38 if max(values) else 1)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#cbd5e1")
        ax.tick_params(axis="y", length=0, labelsize=10)
        ax.tick_params(axis="x", colors="#64748b")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8)
        ax.set_axisbelow(True)
        for bar, row in zip(bars, rows):
            ax.text(
                bar.get_width() + max(values) * 0.035,
                bar.get_y() + bar.get_height() / 2,
                f'{row["effectif"]} offres · {row["pourcentage"]:.1f} %',
                va="center",
                fontsize=9,
                color="#334155",
            )

    fig.text(0.30, 0.94, f'Types de contrats — {stats["code"]}', fontsize=15, fontweight="bold")
    fig.text(0.30, 0.89, f'{stats["total_offres"]} offres · répartition par effectif', fontsize=9, color="#64748b")
    fig.savefig(output, dpi=180, facecolor="white")
    plt.close(fig)


def plot_salary_histogram(stats, salaries, output):
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="white")
    if not salaries:
        ax.text(0.5, 0.5, "Aucun salaire renseigné", ha="center", va="center", color="#64748b", fontsize=14)
        ax.set_axis_off()
    else:
        lower = math.floor(min(salaries) / 10_000) * 10_000
        upper = math.ceil(max(salaries) / 10_000) * 10_000
        if lower == upper:
            lower = max(0, lower - 10_000)
            upper += 10_000
        bins = np.arange(lower, upper + 10_000, 10_000)
        ax.hist(salaries, bins=bins, color="#3978a8", edgecolor="white", linewidth=1.5)
        ax.axvline(stats["salaires"]["mean"], color="#d97706", linestyle="--", linewidth=2,
                   label=f'Moyenne : {stats["salaires"]["mean"]:,.0f} €'.replace(",", " "))
        ax.axvline(stats["salaires"]["median"], color="#7c3aed", linestyle="-.", linewidth=2,
                   label=f'Médiane : {stats["salaires"]["median"]:,.0f} €'.replace(",", " "))
        ax.set_xlabel("Salaire brut annuel (€)")
        ax.set_ylabel("Nombre d’offres")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=7, integer=True))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#cbd5e1")
        ax.tick_params(colors="#64748b")
        ax.grid(axis="y", color="#e2e8f0", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.legend(frameon=False)
    ax.set_title(f'Salaires bruts annuels — {stats["code"]}', loc="left", fontsize=14, pad=14)
    fig.tight_layout()
    fig.savefig(output, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def plot_normal(stats, salaries, output):
    salary_stats = stats["salaires"]
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    if len(salaries) < 2 or not salary_stats["std"]:
        message = (
            "Aucun salaire renseigné"
            if not salaries
            else "Au moins deux salaires distincts sont nécessaires"
        )
        ax.text(0.5, 0.5, message, ha="center", va="center", color="#64748b", fontsize=14,
                transform=ax.transAxes)
        ax.set_axis_off()
    else:
        mu = salary_stats["mean"]
        sigma = salary_stats["std"]
        low = mu - sigma
        high = mu + sigma
        x = np.linspace(max(0, low - 2 * sigma), high + 2 * sigma, 900)
        density = np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
        central = (x >= low) & (x <= high)
        ax.plot(x, density, color="#2563eb", linewidth=2.8)
        ax.fill_between(x[central], density[central], color="#60a5fa", alpha=0.4)
        ax.axvline(mu, color="#b91c1c", linestyle="--", linewidth=2, label=f"Moyenne : {mu:,.0f} €".replace(",", " "))
        ax.axvline(salary_stats["median"], color="#7c3aed", linestyle=":", linewidth=2,
                   label=f'Médiane : {salary_stats["median"]:,.0f} €'.replace(",", " "))
        ax.annotate("68,3 %", (mu, density.max() * 0.48), ha="center", va="center",
                    fontsize=12, fontweight="bold", color="#1e3a8a",
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 4})
        ticks = [mu - 2 * sigma, low, mu, high, mu + 2 * sigma]
        ax.set_xticks(ticks, ["μ − 2σ", "μ − σ", "Moyenne", "μ + σ", "μ + 2σ"])
        ax.set_xlim(0, max(mu + 2.5 * sigma, high))
        ax.set_yticks([])
        ax.set_xlabel("Salaire brut annuel (€)")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#cbd5e1")
        ax.tick_params(colors="#64748b")
        ax.legend(frameon=False, loc="upper left")
    ax.set_title(f'Distribution normale théorique — {stats["nom"]} ({stats["code"]})',
                 loc="left", fontsize=14, fontweight="bold", pad=16)
    fig.tight_layout()
    fig.savefig(output, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def validate_source(payload):
    métiers = payload["metiers"]
    codes = set()
    for item in métiers:
        code = item.get("code")
        nom = item.get("libelle")
        if not isinstance(code, str) or not ROME_PATTERN.fullmatch(code) or not isinstance(nom, str) or not nom.strip():
            raise ValueError(f"Entrée métier invalide dans la source : {item!r}")
        if code in codes:
            raise ValueError(f"Code ROME dupliqué dans la source : {code}")
        codes.add(code)

    unexpected = sorted({offer.get("rome") for offer in payload["offres"]} - codes)
    if unexpected:
        raise ValueError(f"Offres trouvées pour des codes absents de la liste métiers : {unexpected}")
    return métiers


def process_metier(metier, source):
    code = metier["code"]
    folder = DATA_DIR / code
    folder.mkdir(parents=True, exist_ok=True)
    offers = [offer for offer in source["offres"] if offer.get("rome") == code]
    stats = calculate_stats(metier, offers, source.get("date"))
    salaries = [value for offer in offers if (value := annual_salary(offer)) is not None]

    resume = {
        "date": source.get("date"),
        "source": source.get("source"),
        "requete": f"Offres publiées par le site de l’Observatoire, filtrées par code ROME {code}",
        "metiers": [metier],
        "contrats": source.get("contrats", {}),
        "offres": offers,
    }
    save_json(folder / "resume.json", resume)
    save_json(folder / "stats.json", stats)
    plot_contracts(stats, folder / "contrats.png")
    plot_salary_histogram(stats, salaries, folder / "salaires.png")
    plot_normal(stats, salaries, folder / "courbe_gauss_salaires.png")
    return stats


def main():
    set_plot_style()
    source = download_source()
    métiers = validate_source(source)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    for metier in métiers:
        stats = process_metier(metier, source)
        summaries.append({"code": metier["code"], "nom": metier["libelle"]})
        print(
            f'{stats["code"]} · {stats["nom"]}: {stats["total_offres"]} offres, '
            f'{stats["salaires"]["count"]} salaires renseignés'
        )

    save_json(
        DATA_DIR / "metiers.json",
        summaries,
    )
    print(f"\nIndex des {len(summaries)} métiers écrit dans {DATA_DIR / 'metiers.json'}")
    print("Code    Offres  Salaires  Moyenne    Médiane    Écart-type")
    for metier in summaries:
        code = metier["code"]
        stats = json.loads((DATA_DIR / code / "stats.json").read_text(encoding="utf-8"))
        salary = stats["salaires"]
        format_value = lambda value: f"{value:,.0f} €".replace(",", " ") if value is not None else "—"
        print(
            f'{code:<7} {stats["total_offres"]:>6} {salary["count"]:>9}  '
            f'{format_value(salary["mean"]):>10} {format_value(salary["median"]):>10} '
            f'{format_value(salary["std"]):>10}'
        )


if __name__ == "__main__":
    main()

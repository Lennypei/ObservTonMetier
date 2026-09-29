import json
from pathlib import Path
from statistics import mean, median, stdev

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


CODE_ROME = "E1124"
DATA_PATH = Path(__file__).resolve().parent / "data" / "resume.json"
OUTPUT_PATH = Path.cwd() / "courbe_gauss_salaires.png"


def euro(value):
    return f"{value:,.0f} €".replace(",", " ")


def main():
    with DATA_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    offers = [offer for offer in data["offres"] if offer["rome"] == CODE_ROME]
    salaries = [
        (offer["smin"] + offer["smax"]) / 2
        if offer.get("smax") is not None
        else offer["smin"]
        for offer in offers
        if offer.get("smin") is not None
    ]
    if len(salaries) < 2:
        raise ValueError(f"Pas assez de salaires renseignés pour {CODE_ROME}.")

    mu = mean(salaries)
    sigma = stdev(salaries)
    salary_median = median(salaries)
    x = np.linspace(0, 75_000, 1_000)
    density = np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (
        sigma * np.sqrt(2 * np.pi)
    )
    lower = mu - sigma
    upper = mu + sigma
    inside = (x >= lower) & (x <= upper)

    fig = plt.figure(figsize=(10, 6.4), facecolor="white")
    ax = fig.add_axes([0.08, 0.14, 0.89, 0.52])
    ax.plot(x, density * 1_000, color="#2563eb", linewidth=2.8)
    ax.fill_between(
        x[inside],
        density[inside] * 1_000,
        color="#60a5fa",
        alpha=0.4,
        label="Entre μ − σ et μ + σ",
    )
    ax.axvline(
        mu,
        color="#b91c1c",
        linestyle="--",
        linewidth=2,
        label=f"Moyenne = {euro(mu)}",
    )
    ax.axvline(
        salary_median,
        color="#7c3aed",
        linestyle=":",
        linewidth=2.2,
        label=f"Médiane = {euro(salary_median)}",
    )
    ax.annotate(
        "68,3 %",
        xy=(lower + (upper - lower) * 0.25, density.max() * 1_000 * 0.52),
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#1e3a8a",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 4},
    )

    tick_values = [
        mu - 2 * sigma,
        mu - sigma,
        mu,
        mu + sigma,
        mu + 2 * sigma,
    ]
    tick_labels = [
        "μ − 2σ",
        "μ − σ",
        "Moyenne",
        "μ + σ",
        "μ + 2σ",
    ]
    ax.set_xticks(tick_values, tick_labels)
    ax.set_xlim(0, 75_000)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Salaire annuel (€)")
    ax.set_ylabel("")
    ax.set_yticks([])
    fig.text(
        0.08,
        0.95,
        "Distribution théorique normale des salaires - Social Media Manager (E1124)",
        ha="left",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
    )
    fig.text(
        0.08,
        0.90,
        f"D'après les {len(salaries)} salaires renseignés sur {len(offers)} offres : "
        f"moyenne = {euro(mu)} · écart-type = {euro(sigma)}",
        ha="left",
        fontsize=10,
        color="#64748b",
    )
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.tick_params(colors="#64748b")
    fig.legend(
        handles=[
            Patch(facecolor="#60a5fa", alpha=0.4, label="Entre μ − σ et μ + σ"),
            Line2D([0], [0], color="#b91c1c", linestyle="--", linewidth=2,
                   label=f"Moyenne = {euro(mu)}"),
            Line2D([0], [0], color="#7c3aed", linestyle=":", linewidth=2.2,
                   label=f"Médiane = {euro(salary_median)}"),
        ],
        loc="upper left",
        bbox_to_anchor=(0.08, 0.845),
        frameon=False,
        ncol=3,
        fontsize=9,
        columnspacing=1.5,
    )
    fig.savefig(OUTPUT_PATH, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Courbe de Gauss enregistrée : {OUTPUT_PATH}")
    print(
        f"ROME {CODE_ROME} — {len(salaries)} salaires parmi {len(offers)} offres\n"
        f"Moyenne : {euro(mu)} ; médiane : {euro(salary_median)} ; "
        f"écart-type empirique : {euro(sigma)}\n"
        f"Zone moyenne ± écart-type : [{euro(lower)} ; {euro(upper)}]\n"
        "68,3 % est la part théorique sous la courbe normale, pas le salaire moyen."
    )


if __name__ == "__main__":
    main()

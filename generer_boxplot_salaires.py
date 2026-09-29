import json
from pathlib import Path
from statistics import median, stdev

import matplotlib.pyplot as plt
import numpy as np


CODE_ROME = "E1124"
DATA_PATH = Path(__file__).resolve().parent / "data" / "resume.json"
OUTPUT_PATH = Path.cwd() / "dispersion_salaires.png"


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

    minimum, q1, middle, q3, maximum = np.percentile(
        salaries, [0, 25, 50, 75, 100], method="linear"
    )
    salary_median = median(salaries)
    salary_std = stdev(salaries)

    fig, ax = plt.subplots(figsize=(7.5, 8.5), facecolor="white")
    ax.boxplot(
        salaries,
        positions=[1],
        widths=0.45,
        vert=True,
        whis=(0, 100),
        showfliers=False,
        patch_artist=True,
        boxprops={"facecolor": "#e8eef5", "edgecolor": "#334155", "linewidth": 1.5},
        medianprops={"color": "#1d4ed8", "linewidth": 2.2},
        whiskerprops={"color": "#334155", "linewidth": 1.5},
        capprops={"color": "#334155", "linewidth": 1.5},
    )
    ax.axhline(salary_median, color="#1d4ed8", linewidth=1.2, alpha=0.8)

    stat_values = [minimum, q1, middle, q3, maximum]
    stat_labels = [
        f"Min — {euro(minimum)}",
        f"Q1 — {euro(q1)}",
        f"Médiane — {euro(middle)}",
        f"Q3 — {euro(q3)}",
        f"Max — {euro(maximum)}",
    ]
    ax.set_yticks(stat_values, stat_labels)
    ax.set_ylim(minimum - 4000, maximum + 4000)
    ax.set_xlim(0.35, 1.65)
    ax.set_xticks([])
    ax.set_ylabel("Salaire brut annuel")
    ax.set_title(
        "Dispersion des salaires - Social media manager (E1124)",
        loc="left",
        fontsize=14,
        fontweight="bold",
        pad=22,
    )
    ax.text(
        0,
        1.02,
        f"Médiane : {euro(salary_median)} | Écart-type : {euro(salary_std)} "
        f"(N = {len(salaries)} offres sur {len(offers)})",
        transform=ax.transAxes,
        fontsize=10,
        color="#475569",
    )
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.tick_params(axis="y", colors="#334155", length=0, pad=8, labelsize=8)
    ax.set_facecolor("white")

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(fig)

    print(f"Image enregistrée : {OUTPUT_PATH}")
    print(
        f"Min : {euro(minimum)} | Q1 : {euro(q1)} | Médiane : {euro(middle)} | "
        f"Q3 : {euro(q3)} | Max : {euro(maximum)}"
    )
    print(f"Écart-type : {euro(salary_std)} | N = {len(salaries)} / {len(offers)}")


if __name__ == "__main__":
    main()

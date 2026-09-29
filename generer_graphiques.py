import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


CODE_ROME = "E1124"
DATA_PATH = Path(__file__).resolve().parent / "data" / "resume.json"
OUTPUT_DIR = Path.cwd()
CONTRACT_LABELS = {
    "CDI": "CDI",
    "CDD": "CDD",
    "LIB": "Profession libérale",
    "MIS": "Intérim",
}


def main():
    with DATA_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    offers = [offer for offer in data["offres"] if offer["rome"] == CODE_ROME]
    if not offers:
        raise ValueError(f"Aucune offre trouvée pour le code ROME {CODE_ROME}.")

    contracts = Counter(offer.get("contrat") or "Non renseigné" for offer in offers)
    salaries = [
        (offer["smin"] + offer["smax"]) / 2
        if offer.get("smax") is not None
        else offer["smin"]
        for offer in offers
        if offer.get("smin") is not None
    ]
    if not salaries:
        raise ValueError(f"Aucun salaire renseigné pour le code ROME {CODE_ROME}.")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.labelcolor": "#334155",
            "text.color": "#0f172a",
        }
    )

    contract_order = sorted(contracts, key=lambda code: (-contracts[code], code))
    labels = [CONTRACT_LABELS.get(code, code) for code in contract_order]
    counts = [contracts[code] for code in contract_order]
    fig = plt.figure(figsize=(9, 5.5), facecolor="white")
    ax = fig.add_axes([0.27, 0.15, 0.65, 0.62])
    bars = ax.barh(labels[::-1], counts[::-1], color="#3978a8", height=0.58)
    fig.text(
        0.27,
        0.94,
        "Types de contrats — E1124",
        ha="left",
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
    )
    fig.text(
        0.27,
        0.89,
        f"{len(offers)} offres · catégories nominales, classées par effectif",
        ha="left",
        fontsize=9,
        color="#64748b",
    )
    ax.set_xlabel("Nombre d’offres")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(0, max(counts) * 1.32)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.tick_params(axis="y", length=0, labelsize=10)
    ax.tick_params(axis="x", colors="#64748b")
    ax.grid(axis="x", color="#e2e8f0", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, count in zip(bars, counts[::-1]):
        share = count / len(offers) * 100
        ax.text(
            bar.get_width() + max(counts) * 0.035,
            bar.get_y() + bar.get_height() / 2,
            f"{count} offres  ·  {share:.1f} %",
            va="center",
            fontsize=10,
            color="#334155",
        )
    fig.savefig(OUTPUT_DIR / "contrats.png", dpi=180, facecolor="white")
    plt.close(fig)

    average = mean(salaries)
    middle = median(salaries)
    fig = plt.figure(figsize=(9, 6.2), facecolor="white")
    ax = fig.add_axes([0.13, 0.17, 0.82, 0.5])
    bins = list(range(15_000, 65_001, 10_000))
    ax.hist(salaries, bins=bins, color="#3978a8", edgecolor="white", linewidth=1.5)
    ax.axvline(
        average,
        color="#d97706",
        linestyle="--",
        linewidth=2,
        label=f"Moyenne : {average:,.0f} €".replace(",", " "),
    )
    ax.axvline(
        middle,
        color="#7c3aed",
        linestyle="-.",
        linewidth=2,
        label=f"Médiane : {middle:,.0f} €".replace(",", " "),
    )
    fig.text(
        0.13,
        0.95,
        "Salaires bruts annuels — E1124",
        ha="left",
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
    )
    fig.text(
        0.13,
        0.90,
        f"{len(salaries)} salaires renseignés · classes de 10 000 €",
        ha="left",
        fontsize=9,
        color="#64748b",
    )
    ax.set_xlabel("Salaire brut annuel (€)")
    ax.set_ylabel("Nombre d’offres")
    ax.set_xlim(bins[0], bins[-1])
    ax.set_xticks(bins, [f"{value // 1000} k€" for value in bins])
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.tick_params(colors="#64748b")
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.legend(
        *ax.get_legend_handles_labels(),
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.84),
        ncol=2,
        columnspacing=2,
    )
    fig.savefig(OUTPUT_DIR / "salaires.png", dpi=180, facecolor="white")
    plt.close(fig)

    print(f"Offres E1124 : {len(offers)} (données du {data['date']})")
    print(f"Salaires renseignés : {len(salaries)}")
    print(f"Moyenne : {average:,.0f} € ; médiane : {middle:,.0f} €".replace(",", " "))
    print(f"Graphiques enregistrés : {OUTPUT_DIR / 'contrats.png'}, {OUTPUT_DIR / 'salaires.png'}")


if __name__ == "__main__":
    main()

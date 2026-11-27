"""Generate all TCC figures from pipeline data.

Usage:
    python scripts/generate_figures.py
"""

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- Config ---
PROJECT = Path(__file__).resolve().parent.parent
COEVO_FILE = PROJECT / "data" / "processed" / "coevolution.json"
MIG_FILE = PROJECT / "data" / "processed" / "migrations.json"
CLASS_FILE = PROJECT / "data" / "processed" / "corpus_classification.json"
OUT = PROJECT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# Style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})
COLORS = ["#2980b9", "#27ae60", "#e74c3c", "#f39c12", "#8e44ad",
          "#1abc9c", "#e67e22", "#3498db", "#c0392b", "#2c3e50"]


def load():
    with open(COEVO_FILE) as f:
        coevo = json.load(f)
    with open(CLASS_FILE) as f:
        classif = {r["full_name"].replace("/", "__"): r["nature"] for r in json.load(f)}
    return coevo, classif


def fig1_pipeline(out):
    """Fig 1: Pipeline overview (simplified box diagram)."""
    fig, ax = plt.subplots(figsize=(10, 2.5))
    steps = [
        ("1. Coleta\nGitHub API", "#3498db"),
        ("2. Filtragem\n131→124 repos", "#2980b9"),
        ("3. Extração\nAST parsing", "#27ae60"),
        ("4. Correlação\ngit log/diff", "#f39c12"),
        ("5. Classificação\ncamada Django", "#8e44ad"),
        ("6. Análise\nmétricas", "#e74c3c"),
    ]
    for i, (label, color) in enumerate(steps):
        ax.add_patch(plt.Rectangle((i * 1.6, 0), 1.4, 1, facecolor=color,
                                    edgecolor="white", linewidth=2, alpha=0.85))
        ax.text(i * 1.6 + 0.7, 0.5, label, ha="center", va="center",
                fontsize=9, color="white", fontweight="bold")
        if i < len(steps) - 1:
            ax.annotate("", xy=(i * 1.6 + 1.5, 0.5), xytext=(i * 1.6 + 1.55, 0.5),
                        arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))
    ax.set_xlim(-0.2, len(steps) * 1.6)
    ax.set_ylim(-0.3, 1.3)
    ax.axis("off")
    ax.set_title("Pipeline de análise", fontweight="bold", pad=10)
    fig.savefig(out / "fig1_pipeline.pdf")
    fig.savefig(out / "fig1_pipeline.png")
    plt.close(fig)
    print(f"  fig1_pipeline")


def fig2_funnel(out):
    """Fig 2: Selection funnel."""
    stages = ["Matches\nGitHub", "Avaliados", "Django\nreal", "≥15 mig", "Corpus\nfinal"]
    values = [3850, 1000, 416, 131, 124]
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(stages, values, color=[COLORS[0]]*3 + [COLORS[3]] + [COLORS[1]],
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 60,
                f"{val:,}".replace(",", "."), ha="center", va="bottom", fontweight="bold")
    ax.set_ylabel("Quantidade de repositórios")
    ax.set_title("Funil de seleção do corpus", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.savefig(out / "fig2_funnel.pdf")
    fig.savefig(out / "fig2_funnel.png")
    plt.close(fig)
    print(f"  fig2_funnel")


def fig3_corpus_pie(out):
    """Fig 3: Corpus composition (apps vs libs)."""
    fig, ax = plt.subplots(figsize=(5, 5))
    sizes = [86, 38]
    labels = ["Aplicações\n(86)", "Bibliotecas\n(38)"]
    ax.pie(sizes, labels=labels, colors=[COLORS[0], COLORS[1]],
           autopct="%1.0f%%", startangle=90, textprops={"fontsize": 12})
    ax.set_title("Composição do corpus (124 repos)", fontweight="bold")
    fig.savefig(out / "fig3_corpus_pie.pdf")
    fig.savefig(out / "fig3_corpus_pie.png")
    plt.close(fig)
    print(f"  fig3_corpus_pie")


def fig4_coevo_ratio_hist(out, coevo, classif):
    """Fig 4: Distribution of co-evolution ratio per repo."""
    repo_data = defaultdict(lambda: {"total": 0, "coupled": 0})
    for r in coevo:
        repo_data[r["repository"]]["total"] += 1
        if r["code_files_changed"] > 0:
            repo_data[r["repository"]]["coupled"] += 1
    ratios = [d["coupled"] / d["total"] * 100 for d in repo_data.values() if d["total"] >= 5]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(ratios, bins=20, color=COLORS[0], edgecolor="white", linewidth=0.8, alpha=0.85)
    ax.axvline(90.3, color=COLORS[2], linestyle="--", linewidth=2, label="Mediana (90,3%)")
    ax.axvline(86.0, color=COLORS[3], linestyle=":", linewidth=2, label="Média (86,0%)")
    ax.set_xlabel("Co-evolution ratio (%)")
    ax.set_ylabel("Número de repositórios")
    ax.set_title("Distribuição do co-evolution ratio por repositório", fontweight="bold")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.savefig(out / "fig4_coevo_ratio_hist.pdf")
    fig.savefig(out / "fig4_coevo_ratio_hist.png")
    plt.close(fig)
    print(f"  fig4_coevo_ratio_hist")


def fig5_layer_distribution(out, coevo):
    """Fig 5: Layer distribution bar chart."""
    cats = Counter()
    for r in coevo:
        for cat, count in r["file_categories"].items():
            if cat != "migration":
                cats[cat] += count

    layers = ["other", "other_python", "test", "template", "model",
              "view", "serializer", "admin", "form", "url"]
    values = [cats[l] for l in layers]
    total = sum(values)
    pcts = [v / total * 100 for v in values]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(layers[::-1], pcts[::-1], color=COLORS[0], edgecolor="white")
    for bar, pct in zip(bars, pcts[::-1]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"{pct:.1f}%", va="center", fontsize=10)
    ax.set_xlabel("Proporção dos arquivos co-modificados (%)")
    ax.set_title("Distribuição por camada arquitetural (excl. migration)", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.savefig(out / "fig5_layer_distribution.pdf")
    fig.savefig(out / "fig5_layer_distribution.png")
    plt.close(fig)
    print(f"  fig5_layer_distribution")


def fig6_operation_ratio(out, coevo):
    """Fig 6: Co-evolution ratio by operation type."""
    op_stats = defaultdict(lambda: {"total": 0, "coupled": 0})
    for r in coevo:
        for op in set(r["operation_types"]):
            op_stats[op]["total"] += 1
            if r["code_files_changed"] > 0:
                op_stats[op]["coupled"] += 1

    ops = [(op, s["coupled"] / s["total"] * 100, s["total"])
           for op, s in op_stats.items() if s["total"] >= 50]
    ops.sort(key=lambda x: -x[1])

    names = [o[0] for o in ops]
    ratios = [o[1] for o in ops]
    totals = [o[2] for o in ops]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(names[::-1], ratios[::-1], color=COLORS[0], edgecolor="white")
    for bar, ratio, total in zip(bars, ratios[::-1], totals[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f"{ratio:.1f}% (n={total})", va="center", fontsize=9)
    ax.set_xlabel("Co-evolution ratio (%)")
    ax.set_xlim(0, 105)
    ax.set_title("Co-evolution ratio por tipo de operação", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.savefig(out / "fig6_operation_ratio.pdf")
    fig.savefig(out / "fig6_operation_ratio.png")
    plt.close(fig)
    print(f"  fig6_operation_ratio")


def fig7_op_layer_heatmap(out, coevo):
    """Fig 7: Operation x Layer heatmap."""
    top_ops = ["CreateModel", "AddField", "AlterField", "RemoveField", "DeleteModel"]
    layers = ["model", "view", "admin", "serializer", "form", "test", "template", "url"]

    op_layer = defaultdict(lambda: Counter())
    for r in coevo:
        if r["code_files_changed"] > 0:
            for op in set(r["operation_types"]):
                if op in top_ops:
                    for cat, count in r["file_categories"].items():
                        if cat in layers:
                            op_layer[op][cat] += count

    matrix = []
    for op in top_ops:
        total_op = sum(op_layer[op].values())
        row = [op_layer[op][l] / total_op * 100 if total_op > 0 else 0 for l in layers]
        matrix.append(row)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels(layers, rotation=45, ha="right")
    ax.set_yticks(range(len(top_ops)))
    ax.set_yticklabels(top_ops)

    for i in range(len(top_ops)):
        for j in range(len(layers)):
            val = matrix[i][j]
            color = "white" if val > 15 else "black"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=9, color=color)

    ax.set_title("Proporção de cada camada por tipo de operação (%)", fontweight="bold")
    fig.colorbar(im, ax=ax, label="%", shrink=0.8)
    fig.savefig(out / "fig7_op_layer_heatmap.pdf")
    fig.savefig(out / "fig7_op_layer_heatmap.png")
    plt.close(fig)
    print(f"  fig7_op_layer_heatmap")


def fig8_apps_vs_libs(out, coevo, classif):
    """Fig 8: Apps vs Libs comparison."""
    apps = [r for r in coevo if classif.get(r["repository"]) == "app"]
    libs = [r for r in coevo if classif.get(r["repository"]) == "lib"]

    metrics = ["Co-evolution\nratio (%)", "Spread\nmediano", "Testes\n(%)"]

    app_coupled = [r for r in apps if r["code_files_changed"] > 0]
    lib_coupled = [r for r in libs if r["code_files_changed"] > 0]

    # App layer %
    app_cats = Counter()
    for r in apps:
        for cat, count in r["file_categories"].items():
            if cat != "migration":
                app_cats[cat] += count
    app_total = sum(app_cats.values())
    app_test_pct = app_cats["test"] / app_total * 100 if app_total else 0

    lib_cats = Counter()
    for r in libs:
        for cat, count in r["file_categories"].items():
            if cat != "migration":
                lib_cats[cat] += count
    lib_total = sum(lib_cats.values())
    lib_test_pct = lib_cats["test"] / lib_total * 100 if lib_total else 0

    app_ratio = len(app_coupled) / len(apps) * 100 if apps else 0
    lib_ratio = len(lib_coupled) / len(libs) * 100 if libs else 0

    app_spreads = sorted([r["code_files_changed"] for r in app_coupled])
    lib_spreads = sorted([r["code_files_changed"] for r in lib_coupled])
    app_spread_med = app_spreads[len(app_spreads)//2] if app_spreads else 0
    lib_spread_med = lib_spreads[len(lib_spreads)//2] if lib_spreads else 0

    app_vals = [app_ratio, app_spread_med, app_test_pct]
    lib_vals = [lib_ratio, lib_spread_med, lib_test_pct]

    x = range(len(metrics))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar([i - width/2 for i in x], app_vals, width, label=f"Apps (85)",
                   color=COLORS[0], edgecolor="white")
    bars2 = ax.bar([i + width/2 for i in x], lib_vals, width, label=f"Libs (37)",
                   color=COLORS[1], edgecolor="white")

    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_title("Comparação: Aplicações vs Bibliotecas", fontweight="bold")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.savefig(out / "fig8_apps_vs_libs.pdf")
    fig.savefig(out / "fig8_apps_vs_libs.png")
    plt.close(fig)
    print(f"  fig8_apps_vs_libs")


def fig9_operation_frequency(out):
    """Fig 9: Operation type frequency from migrations.json."""
    with open(MIG_FILE) as f:
        mig_data = json.load(f)

    op_counts = Counter()
    for m in mig_data:
        for op in m["operations"]:
            op_counts[op["type"]] += 1

    top = op_counts.most_common(10)
    names = [t[0] for t in top]
    values = [t[1] for t in top]
    total = sum(op_counts.values())

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(names[::-1], values[::-1], color=COLORS[0], edgecolor="white")
    for bar, val in zip(bars, values[::-1]):
        pct = val / total * 100
        ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                f"{val:,} ({pct:.1f}%)".replace(",", "."), va="center", fontsize=9)
    ax.set_xlabel("Número de ocorrências")
    ax.set_title("Top 10 tipos de operação de migration", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.savefig(out / "fig9_operation_frequency.pdf")
    fig.savefig(out / "fig9_operation_frequency.png")
    plt.close(fig)
    print(f"  fig9_operation_frequency")


if __name__ == "__main__":
    print("Generating figures...")
    coevo, classif = load()

    fig1_pipeline(OUT)
    fig2_funnel(OUT)
    fig3_corpus_pie(OUT)
    fig4_coevo_ratio_hist(OUT, coevo, classif)
    fig5_layer_distribution(OUT, coevo)
    fig6_operation_ratio(OUT, coevo)
    fig7_op_layer_heatmap(OUT, coevo)
    fig8_apps_vs_libs(OUT, coevo, classif)
    fig9_operation_frequency(OUT)

    print(f"\nDone! {len(list(OUT.glob('*.pdf')))} PDFs + {len(list(OUT.glob('*.png')))} PNGs in {OUT}")

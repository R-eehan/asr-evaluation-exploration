"""Phase 5: Generate visualization figures for cross-platform comparison.

Produces fig7-fig12 in report/figures/ to complement Part 1's fig1-fig6.

Usage:
    python -m src.visualize_cross_platform
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rcParams["font.size"] = 11
matplotlib.rcParams["figure.dpi"] = 150
matplotlib.rcParams["savefig.bbox"] = "tight"

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
FIGURES_DIR = PROJECT_ROOT / "report" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Consistent colors and labels
PROVIDER_COLORS = {
    "together_ai": "#6366f1",
    "groq": "#f97316",
    "fireworks": "#ef4444",
    "baseten": "#10b981",
}
PROVIDER_LABELS = {
    "together_ai": "Together AI",
    "groq": "Groq",
    "fireworks": "Fireworks",
    "baseten": "Baseten",
}
LANG_LABELS = {
    "en-IN": "English",
    "hi": "Hindi",
    "hi-en": "Hinglish",
    "ka": "Kannada",
    "kn-en": "Kannada-EN",
}
LANG_ORDER = ["en-IN", "hi", "hi-en", "ka", "kn-en"]
PROVIDERS = ["together_ai", "groq", "fireworks", "baseten"]


def load_cross_platform():
    path = sorted(RESULTS_DIR.glob("eval_results_cross_platform_v1_*.csv"))[-1]
    with open(path) as f:
        return list(csv.DictReader(f))


def load_turbo(provider_tag):
    path = sorted(RESULTS_DIR.glob(f"eval_results_{provider_tag}_*.csv"))[-1]
    with open(path) as f:
        return [r for r in csv.DictReader(f) if r["status"] == "ok"]


def fig7_wer_by_language(rows):
    """Grouped bar chart: WER per language per provider."""
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(LANG_ORDER))
    width = 0.18
    offsets = [-1.5, -0.5, 0.5, 1.5]

    for i, prov in enumerate(PROVIDERS):
        means = []
        for lang in LANG_ORDER:
            wers = [float(r["wer"]) for r in rows
                    if r["provider"] == prov and r["language"] == lang and r["status"] == "ok"]
            means.append(sum(wers) / len(wers) * 100 if wers else 0)

        bars = ax.bar(x + offsets[i] * width, means, width,
                      label=PROVIDER_LABELS[prov], color=PROVIDER_COLORS[prov])
        for bar, val in zip(bars, means):
            if val > 5:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f"{val:.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Language Category")
    ax.set_ylabel("Mean WER (%)")
    ax.set_title("Word Error Rate by Language and Provider\n(Whisper Large v3 across 4 inference platforms)")
    ax.set_xticks(x)
    ax.set_xticklabels([LANG_LABELS[l] for l in LANG_ORDER])
    ax.legend(loc="upper left")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", alpha=0.3)

    path = FIGURES_DIR / "fig7_wer_by_language_cross_platform.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def fig8_cost_quality_frontier(rows):
    """Scatter plot: cost per hour vs macro-average WER."""
    fig, ax = plt.subplots(figsize=(10, 7))

    cost_per_hour = {
        "together_ai": 0.09,
        "groq": 0.111,
        "fireworks": 0.09,
        "baseten": 3.75,
    }

    # Also plot turbo variants and managed APIs as reference
    extra_points = {
        "Groq Turbo": (0.04, None, "#f97316", "D"),
        "Fireworks Turbo": (0.054, None, "#ef4444", "D"),
        "OpenAI gpt-4o": (0.36, None, "#6b7280", "s"),
        "OpenAI gpt-4o-mini": (0.18, None, "#9ca3af", "s"),
    }

    for prov in PROVIDERS:
        # Compute macro-average WER
        cat_means = []
        for lang in LANG_ORDER:
            wers = [float(r["wer"]) for r in rows
                    if r["provider"] == prov and r["language"] == lang and r["status"] == "ok"]
            if wers:
                cat_means.append(sum(wers) / len(wers) * 100)
        macro = sum(cat_means) / len(cat_means)
        cost = cost_per_hour[prov]

        ax.scatter(cost, macro, s=200, c=PROVIDER_COLORS[prov], zorder=5,
                   label=PROVIDER_LABELS[prov], edgecolors="white", linewidth=1.5)
        ax.annotate(PROVIDER_LABELS[prov], (cost, macro),
                    textcoords="offset points", xytext=(10, 5), fontsize=9)

    # Load turbo results for additional points
    try:
        groq_turbo = load_turbo("groq_turbo")
        cat_means = []
        for lang in LANG_ORDER:
            wers = [float(r["wer"]) for r in groq_turbo if r["language"] == lang]
            if wers:
                cat_means.append(sum(wers) / len(wers) * 100)
        if cat_means:
            macro = sum(cat_means) / len(cat_means)
            ax.scatter(0.04, macro, s=150, c="#f97316", marker="D", zorder=5,
                       edgecolors="white", linewidth=1.5)
            ax.annotate("Groq Turbo", (0.04, macro),
                        textcoords="offset points", xytext=(10, -10), fontsize=8, style="italic")
    except Exception:
        pass

    try:
        fw_turbo = load_turbo("fireworks_turbo")
        cat_means = []
        for lang in LANG_ORDER:
            wers = [float(r["wer"]) for r in fw_turbo if r["language"] == lang]
            if wers:
                cat_means.append(sum(wers) / len(wers) * 100)
        if cat_means:
            macro = sum(cat_means) / len(cat_means)
            ax.scatter(0.054, macro, s=150, c="#ef4444", marker="D", zorder=5,
                       edgecolors="white", linewidth=1.5)
            ax.annotate("Fireworks Turbo", (0.054, macro),
                        textcoords="offset points", xytext=(10, 5), fontsize=8, style="italic")
    except Exception:
        pass

    # Reference lines for managed APIs (no WER data, just cost markers)
    for label, cost in [("OpenAI gpt-4o\n($0.36/hr)", 0.36), ("OpenAI gpt-4o-mini\n($0.18/hr)", 0.18)]:
        ax.axvline(x=cost, color="#9ca3af", linestyle="--", alpha=0.5)
        ax.text(cost, ax.get_ylim()[0] + 1, label, ha="center", va="bottom",
                fontsize=7, color="#6b7280")

    ax.set_xlabel("Cost per Hour of Audio (USD, March 2026)")
    ax.set_ylabel("Macro-Average WER (%)")
    ax.set_title("Cost-Quality Frontier\n(lower-left is better)")
    ax.set_xscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")

    path = FIGURES_DIR / "fig8_cost_quality_frontier.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def fig9_provider_agreement_heatmap(rows):
    """Heatmap: WER per file per provider."""
    fig, ax = plt.subplots(figsize=(8, 12))

    filenames = []
    seen = set()
    for r in rows:
        if r["filename"] not in seen:
            filenames.append(r["filename"])
            seen.add(r["filename"])

    data = np.full((len(filenames), len(PROVIDERS)), np.nan)
    for r in rows:
        if r["status"] == "ok" and r["provider"] in PROVIDERS:
            i = filenames.index(r["filename"])
            j = PROVIDERS.index(r["provider"])
            data[i, j] = float(r["wer"]) * 100

    im = ax.imshow(data, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=100)

    ax.set_xticks(range(len(PROVIDERS)))
    ax.set_xticklabels([PROVIDER_LABELS[p] for p in PROVIDERS], rotation=0)
    ax.set_yticks(range(len(filenames)))
    ax.set_yticklabels([fn[:40] for fn in filenames], fontsize=7)

    # Add text values
    for i in range(len(filenames)):
        for j in range(len(PROVIDERS)):
            val = data[i, j]
            if not np.isnan(val):
                color = "white" if val > 60 else "black"
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7, color=color)

    ax.set_title("WER (%) per File per Provider\n(green = low, red = high)")
    fig.colorbar(im, ax=ax, label="WER (%)", shrink=0.6)

    path = FIGURES_DIR / "fig9_provider_agreement_heatmap.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def fig10_latency_comparison(rows):
    """Box plot: latency distribution per provider."""
    fig, ax = plt.subplots(figsize=(10, 5))

    latency_data = []
    labels = []
    colors = []
    for prov in PROVIDERS:
        lats = [float(r["latency_seconds"]) for r in rows
                if r["provider"] == prov and r["status"] == "ok"]
        latency_data.append(lats)
        labels.append(PROVIDER_LABELS[prov])
        colors.append(PROVIDER_COLORS[prov])

    bp = ax.boxplot(latency_data, labels=labels, patch_artist=True, widths=0.5)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Transcription Latency Distribution by Provider\n(28 files, Whisper Large v3)")
    ax.grid(axis="y", alpha=0.3)

    # Add mean markers
    for i, lats in enumerate(latency_data):
        mean = sum(lats) / len(lats)
        ax.plot(i + 1, mean, "D", color="white", markersize=6, markeredgecolor="black", zorder=5)

    ax.legend([plt.Line2D([0], [0], marker="D", color="w", markeredgecolor="black", markersize=6)],
              ["Mean"], loc="upper right")

    path = FIGURES_DIR / "fig10_latency_comparison.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def fig11_error_type_breakdown(rows):
    """Stacked bar: substitution/insertion/deletion rates per provider per language."""
    fig, axes = plt.subplots(1, 5, figsize=(16, 5), sharey=True)

    for ax_idx, lang in enumerate(LANG_ORDER):
        ax = axes[ax_idx]
        lang_rows = [r for r in rows if r["language"] == lang and r["status"] == "ok"]

        sub_rates = []
        ins_rates = []
        del_rates = []

        for prov in PROVIDERS:
            prov_rows = [r for r in lang_rows if r["provider"] == prov]
            total_ref = sum(len(r["reference"].split()) for r in prov_rows)
            total_sub = sum(int(r["substitutions"]) for r in prov_rows)
            total_ins = sum(int(r["insertions"]) for r in prov_rows)
            total_del = sum(int(r["deletions"]) for r in prov_rows)

            sub_rates.append(total_sub / total_ref * 100 if total_ref else 0)
            ins_rates.append(total_ins / total_ref * 100 if total_ref else 0)
            del_rates.append(total_del / total_ref * 100 if total_ref else 0)

        x = np.arange(len(PROVIDERS))
        width = 0.6

        ax.bar(x, sub_rates, width, label="Substitutions", color="#6366f1", alpha=0.8)
        ax.bar(x, ins_rates, width, bottom=sub_rates, label="Insertions", color="#f97316", alpha=0.8)
        bottom = [s + i for s, i in zip(sub_rates, ins_rates)]
        ax.bar(x, del_rates, width, bottom=bottom, label="Deletions", color="#ef4444", alpha=0.8)

        ax.set_title(LANG_LABELS[lang], fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels([PROVIDER_LABELS[p][:5] for p in PROVIDERS], rotation=45, fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("Error Rate (% of reference words)")
    axes[2].legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, fontsize=9)
    fig.suptitle("Error Type Breakdown by Provider and Language\n(same WER can have very different error compositions)",
                 fontsize=12, y=1.02)

    path = FIGURES_DIR / "fig11_error_type_breakdown.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def fig12_turbo_vs_full_paired(rows):
    """Dot plot: per-file WER difference (Turbo - Full) for Groq and Fireworks."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 8), sharey=True)

    for ax_idx, (prov_tag, prov_name, color) in enumerate([
        ("groq_turbo", "Groq", "#f97316"),
        ("fireworks_turbo", "Fireworks", "#ef4444"),
    ]):
        ax = axes[ax_idx]

        try:
            turbo_rows = load_turbo(prov_tag)
        except Exception:
            continue

        prov_key = "groq" if "groq" in prov_tag else "fireworks"
        full_by_file = {r["filename"]: float(r["wer"]) for r in rows
                        if r["provider"] == prov_key and r["status"] == "ok"}

        files = []
        diffs = []
        langs = []
        for r in turbo_rows:
            fn = r["filename"]
            if fn in full_by_file:
                diff = (float(r["wer"]) - full_by_file[fn]) * 100
                files.append(fn[:35])
                diffs.append(diff)
                langs.append(r["language"])

        # Sort by diff
        sorted_idx = sorted(range(len(diffs)), key=lambda i: diffs[i])
        files = [files[i] for i in sorted_idx]
        diffs = [diffs[i] for i in sorted_idx]
        langs = [langs[i] for i in sorted_idx]

        lang_colors = {"en-IN": "#3b82f6", "hi": "#f59e0b", "hi-en": "#8b5cf6",
                       "ka": "#ef4444", "kn-en": "#ec4899"}

        y = range(len(files))
        for i, (f, d, l) in enumerate(zip(files, diffs, langs)):
            ax.barh(i, d, color=lang_colors.get(l, "#6b7280"), alpha=0.7, height=0.7)

        ax.axvline(x=0, color="black", linewidth=1)
        ax.set_yticks(range(len(files)))
        ax.set_yticklabels(files, fontsize=6)
        ax.set_xlabel("WER Difference (pp): Turbo - Full\n(← Turbo better | Turbo worse →)")
        ax.set_title(f"{prov_name}: Turbo vs Full (per file)")
        ax.grid(axis="x", alpha=0.3)

        # Mean line
        mean_diff = sum(diffs) / len(diffs)
        ax.axvline(x=mean_diff, color=color, linestyle="--", linewidth=2, alpha=0.7)
        ax.text(mean_diff, len(files) - 1, f"  mean: {mean_diff:+.1f}pp",
                color=color, fontsize=9, va="top")

    # Legend for language colors
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, alpha=0.7, label=LANG_LABELS.get(l, l))
                       for l, c in [("en-IN", "#3b82f6"), ("hi", "#f59e0b"),
                                    ("hi-en", "#8b5cf6"), ("ka", "#ef4444"), ("kn-en", "#ec4899")]]
    axes[1].legend(handles=legend_elements, loc="lower right", fontsize=8, title="Language")

    fig.suptitle("Turbo vs Full Model: Per-File WER Difference\n(aggregate hides per-file inconsistency)",
                 fontsize=12)

    path = FIGURES_DIR / "fig12_turbo_vs_full_paired.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def main():
    print("Generating Phase 5 visualization figures...")
    print()

    rows = load_cross_platform()
    print(f"Loaded {len(rows)} results from cross-platform CSV")
    print()

    fig7_wer_by_language(rows)
    fig8_cost_quality_frontier(rows)
    fig9_provider_agreement_heatmap(rows)
    fig10_latency_comparison(rows)
    fig11_error_type_breakdown(rows)
    fig12_turbo_vs_full_paired(rows)

    print()
    print(f"All figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_ROOT))
    main()

"""Day 3 analysis: per-scenario metrics, failure cases, and pattern documentation."""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.metrics.latency import compute_latency_stats


def load_results(results_path: str) -> pd.DataFrame:
    """Load evaluation results from CSV."""
    df = pd.read_csv(results_path)
    # Only keep successful transcriptions for metric analysis
    return df


def summary_by_provider(df: pd.DataFrame) -> pd.DataFrame:
    """Overall WER/CER/latency summary by provider."""
    ok = df[df["status"] == "ok"].copy()
    summary = ok.groupby("provider").agg(
        files=("wer", "count"),
        mean_wer=("wer", "mean"),
        median_wer=("wer", "median"),
        min_wer=("wer", "min"),
        max_wer=("wer", "max"),
        mean_cer=("cer", "mean"),
        mean_latency=("latency_seconds", "mean"),
        p50_latency=("latency_seconds", "median"),
    ).reset_index()

    # Compute p95 latency separately
    p95 = ok.groupby("provider")["latency_seconds"].quantile(0.95).reset_index()
    p95.columns = ["provider", "p95_latency"]
    summary = summary.merge(p95, on="provider")

    return summary


def metrics_by_provider_scenario(df: pd.DataFrame) -> pd.DataFrame:
    """WER/CER breakdown by provider x scenario."""
    ok = df[df["status"] == "ok"].copy()
    grouped = ok.groupby(["provider", "scenario"]).agg(
        files=("wer", "count"),
        mean_wer=("wer", "mean"),
        median_wer=("wer", "median"),
        mean_cer=("cer", "mean"),
        mean_latency=("latency_seconds", "mean"),
    ).reset_index()
    return grouped


def metrics_by_provider_language(df: pd.DataFrame) -> pd.DataFrame:
    """WER/CER breakdown by provider x language."""
    ok = df[df["status"] == "ok"].copy()
    grouped = ok.groupby(["provider", "language"]).agg(
        files=("wer", "count"),
        mean_wer=("wer", "mean"),
        median_wer=("wer", "median"),
        mean_cer=("cer", "mean"),
        mean_latency=("latency_seconds", "mean"),
    ).reset_index()
    return grouped


def metrics_by_provider_source(df: pd.DataFrame) -> pd.DataFrame:
    """WER/CER breakdown by provider x data source (public vs personal)."""
    ok = df[df["status"] == "ok"].copy()
    grouped = ok.groupby(["provider", "source"]).agg(
        files=("wer", "count"),
        mean_wer=("wer", "mean"),
        mean_cer=("cer", "mean"),
    ).reset_index()
    return grouped


def find_failure_cases(df: pd.DataFrame, top_n: int = 5) -> dict:
    """Find worst-performing files for each provider and best/worst comparisons."""
    ok = df[df["status"] == "ok"].copy()
    failures = {}

    for provider in ok["provider"].unique():
        prov_df = ok[ok["provider"] == provider].sort_values("wer", ascending=False)
        worst = prov_df.head(top_n)[
            ["filename", "language", "scenario", "wer", "cer", "reference", "hypothesis"]
        ].to_dict("records")
        best = prov_df.tail(top_n)[
            ["filename", "language", "scenario", "wer", "cer", "reference", "hypothesis"]
        ].to_dict("records")
        failures[provider] = {"worst": worst, "best": best}

    return failures


def find_provider_comparisons(df: pd.DataFrame) -> list:
    """Find files where providers diverge most — interesting for the report."""
    ok = df[df["status"] == "ok"].copy()
    pivoted = ok.pivot_table(index="filename", columns="provider", values="wer")

    comparisons = []
    for _, row in pivoted.iterrows():
        providers_wer = row.dropna().to_dict()
        if len(providers_wer) >= 2:
            best_prov = min(providers_wer, key=providers_wer.get)
            worst_prov = max(providers_wer, key=providers_wer.get)
            spread = providers_wer[worst_prov] - providers_wer[best_prov]
            comparisons.append({
                "filename": row.name,
                "best_provider": best_prov,
                "best_wer": providers_wer[best_prov],
                "worst_provider": worst_prov,
                "worst_wer": providers_wer[worst_prov],
                "spread": spread,
                "all_wers": providers_wer,
            })

    comparisons.sort(key=lambda x: x["spread"], reverse=True)
    return comparisons


def analyze_code_mixed(df: pd.DataFrame) -> dict:
    """Analyze code-mixed (hi-en, kn-en) handling patterns."""
    ok = df[df["status"] == "ok"].copy()
    code_mixed = ok[ok["language"].isin(["hi-en", "kn-en"])]
    mono = ok[~ok["language"].isin(["hi-en", "kn-en"])]

    result = {
        "code_mixed_by_provider": {},
        "monolingual_by_provider": {},
    }

    for provider in ok["provider"].unique():
        cm = code_mixed[code_mixed["provider"] == provider]
        ml = mono[mono["provider"] == provider]
        if len(cm) > 0:
            result["code_mixed_by_provider"][provider] = {
                "mean_wer": float(cm["wer"].mean()),
                "mean_cer": float(cm["cer"].mean()),
                "count": int(len(cm)),
            }
        if len(ml) > 0:
            result["monolingual_by_provider"][provider] = {
                "mean_wer": float(ml["wer"].mean()),
                "mean_cer": float(ml["cer"].mean()),
                "count": int(len(ml)),
            }

    return result


def analyze_specific_patterns(df: pd.DataFrame) -> dict:
    """Analyze number handling, proper nouns, and other specific patterns."""
    ok = df[df["status"] == "ok"].copy()
    patterns = {"number_handling": [], "proper_nouns": [], "script_issues": []}

    # Number-related clips
    number_keywords = ["₹", "18,500", "19,800", "हज़ार", "रुपए", "प्रतिशत",
                       "चार हज़ार", "दस बीस", "50,000", "lakh"]
    for _, row in ok.iterrows():
        ref = str(row["reference"])
        hyp = str(row["hypothesis"])
        if any(kw in ref for kw in number_keywords):
            patterns["number_handling"].append({
                "filename": row["filename"],
                "provider": row["provider"],
                "reference": ref,
                "hypothesis": hyp,
                "wer": row["wer"],
            })

    # Proper noun clips (bank names, personal names, city names)
    noun_keywords = ["SBI", "Gpay", "GPay", "Mumbai", "bank", "Bank",
                     "Canara", "Arunachal", "Hotstar", "UPI"]
    for _, row in ok.iterrows():
        ref = str(row["reference"])
        hyp = str(row["hypothesis"])
        if any(kw in ref for kw in noun_keywords):
            patterns["proper_nouns"].append({
                "filename": row["filename"],
                "provider": row["provider"],
                "reference": ref,
                "hypothesis": hyp,
                "wer": row["wer"],
            })

    return patterns


def format_report(
    summary: pd.DataFrame,
    by_scenario: pd.DataFrame,
    by_language: pd.DataFrame,
    by_source: pd.DataFrame,
    failures: dict,
    comparisons: list,
    code_mixed: dict,
    patterns: dict,
    errors: pd.DataFrame,
) -> str:
    """Format the full analysis report as markdown."""
    lines = []
    lines.append("# Day 3: Full ASR Evaluation Results\n")
    lines.append(f"**Date:** 2026-03-07")
    lines.append(f"**Total files:** 28 | **Providers:** 3 | **Total API calls:** 84\n")

    # 1. Overall summary
    lines.append("## 1. Overall Summary by Provider\n")
    lines.append("| Provider | Files | Mean WER | Median WER | Mean CER | Mean Latency | P50 Latency | P95 Latency |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['provider']} | {row['files']:.0f} | "
            f"{row['mean_wer']:.2%} | {row['median_wer']:.2%} | "
            f"{row['mean_cer']:.2%} | {row['mean_latency']:.2f}s | "
            f"{row['p50_latency']:.2f}s | {row['p95_latency']:.2f}s |"
        )
    lines.append("")

    # 2. By scenario
    lines.append("## 2. WER by Provider x Scenario\n")
    scenario_pivot = by_scenario.pivot_table(
        index="scenario", columns="provider", values="mean_wer"
    )
    lines.append("| Scenario | " + " | ".join(scenario_pivot.columns) + " |")
    lines.append("|---|" + "|".join(["---"] * len(scenario_pivot.columns)) + "|")
    for scenario, row in scenario_pivot.iterrows():
        vals = " | ".join(f"{v:.2%}" if pd.notna(v) else "N/A" for v in row)
        lines.append(f"| {scenario} | {vals} |")
    lines.append("")

    # 3. By language
    lines.append("## 3. WER by Provider x Language\n")
    lang_pivot = by_language.pivot_table(
        index="language", columns="provider", values="mean_wer"
    )
    lines.append("| Language | " + " | ".join(lang_pivot.columns) + " |")
    lines.append("|---|" + "|".join(["---"] * len(lang_pivot.columns)) + "|")
    for lang, row in lang_pivot.iterrows():
        vals = " | ".join(f"{v:.2%}" if pd.notna(v) else "N/A" for v in row)
        lines.append(f"| {lang} | {vals} |")
    lines.append("")

    # CER by language
    lines.append("### CER by Provider x Language\n")
    cer_pivot = by_language.pivot_table(
        index="language", columns="provider", values="mean_cer"
    )
    lines.append("| Language | " + " | ".join(cer_pivot.columns) + " |")
    lines.append("|---|" + "|".join(["---"] * len(cer_pivot.columns)) + "|")
    for lang, row in cer_pivot.iterrows():
        vals = " | ".join(f"{v:.2%}" if pd.notna(v) else "N/A" for v in row)
        lines.append(f"| {lang} | {vals} |")
    lines.append("")

    # 4. Public vs Personal recordings
    lines.append("## 4. Public vs Personal Recordings\n")
    lines.append("| Provider | Source | Files | Mean WER | Mean CER |")
    lines.append("|---|---|---|---|---|")
    for _, row in by_source.iterrows():
        lines.append(
            f"| {row['provider']} | {row['source']} | {row['files']:.0f} | "
            f"{row['mean_wer']:.2%} | {row['mean_cer']:.2%} |"
        )
    lines.append("")

    # 5. Code-mixed analysis
    lines.append("## 5. Code-Mixed vs Monolingual Performance\n")
    lines.append("| Provider | Type | Files | Mean WER | Mean CER |")
    lines.append("|---|---|---|---|---|")
    for provider in sorted(set(
        list(code_mixed["code_mixed_by_provider"].keys()) +
        list(code_mixed["monolingual_by_provider"].keys())
    )):
        cm = code_mixed["code_mixed_by_provider"].get(provider, {})
        ml = code_mixed["monolingual_by_provider"].get(provider, {})
        if cm:
            lines.append(
                f"| {provider} | Code-mixed | {cm['count']} | "
                f"{cm['mean_wer']:.2%} | {cm['mean_cer']:.2%} |"
            )
        if ml:
            lines.append(
                f"| {provider} | Monolingual | {ml['count']} | "
                f"{ml['mean_wer']:.2%} | {ml['mean_cer']:.2%} |"
            )
    lines.append("")

    # 6. Biggest provider divergences
    lines.append("## 6. Biggest Provider Divergences\n")
    lines.append("Files where providers disagreed most:\n")
    for comp in comparisons[:7]:
        lines.append(f"### `{comp['filename']}` (spread: {comp['spread']:.2%})")
        for prov, wer in sorted(comp["all_wers"].items()):
            marker = " **best**" if prov == comp["best_provider"] else ""
            marker = " **worst**" if prov == comp["worst_provider"] else marker
            lines.append(f"- {prov}: {wer:.2%}{marker}")
        lines.append("")

    # 7. Failure cases per provider
    lines.append("## 7. Worst Cases per Provider\n")
    for provider, data in failures.items():
        lines.append(f"### {provider.upper()} — Top 5 Worst WER\n")
        for case in data["worst"]:
            lines.append(f"**`{case['filename']}`** ({case['language']}, {case['scenario']}) — WER: {case['wer']:.2%}")
            ref_short = case["reference"][:120] + ("..." if len(case["reference"]) > 120 else "")
            hyp_short = case["hypothesis"][:120] + ("..." if len(case["hypothesis"]) > 120 else "")
            lines.append(f"- **Reference:** {ref_short}")
            lines.append(f"- **Hypothesis:** {hyp_short}")
            lines.append("")

    # 8. Specific pattern analysis
    lines.append("## 8. Pattern Analysis\n")

    # Number handling
    if patterns["number_handling"]:
        lines.append("### Number Handling\n")
        # Group by filename to show all providers side-by-side
        by_file = defaultdict(list)
        for p in patterns["number_handling"]:
            by_file[p["filename"]].append(p)
        for filename, items in list(by_file.items())[:5]:
            lines.append(f"**`{filename}`**")
            lines.append(f"- **Reference:** {items[0]['reference'][:150]}")
            for item in items:
                lines.append(f"- **{item['provider']}** (WER {item['wer']:.2%}): {item['hypothesis'][:150]}")
            lines.append("")

    # Proper noun handling
    if patterns["proper_nouns"]:
        lines.append("### Proper Noun Handling\n")
        by_file = defaultdict(list)
        for p in patterns["proper_nouns"]:
            by_file[p["filename"]].append(p)
        for filename, items in list(by_file.items())[:5]:
            lines.append(f"**`{filename}`**")
            lines.append(f"- **Reference:** {items[0]['reference'][:150]}")
            for item in items:
                lines.append(f"- **{item['provider']}** (WER {item['wer']:.2%}): {item['hypothesis'][:150]}")
            lines.append("")

    # 9. Errors
    if len(errors) > 0:
        lines.append("## 9. API Errors\n")
        lines.append("| Filename | Provider | Error |")
        lines.append("|---|---|---|")
        for _, row in errors.iterrows():
            lines.append(f"| {row['filename']} | {row['provider']} | {row['error']} |")
        lines.append("")

    return "\n".join(lines)


def main():
    """Run full analysis on the most recent results file."""
    import argparse
    parser = argparse.ArgumentParser(description="Analyze ASR evaluation results")
    parser.add_argument("results_csv", help="Path to evaluation results CSV")
    parser.add_argument("--output", default=None, help="Output markdown file path")
    args = parser.parse_args()

    results_path = Path(args.results_csv)
    if not results_path.exists():
        print(f"Results file not found: {results_path}")
        sys.exit(1)

    print(f"Loading results from {results_path}...")
    df = load_results(str(results_path))
    print(f"Loaded {len(df)} result rows ({df['filename'].nunique()} unique files, "
          f"{df['provider'].nunique()} providers)")

    ok_df = df[df["status"] == "ok"]
    error_df = df[df["status"] == "error"]
    print(f"Successful: {len(ok_df)} | Errors: {len(error_df)}")

    print("\nComputing metrics...")
    summary = summary_by_provider(df)
    by_scenario = metrics_by_provider_scenario(df)
    by_language = metrics_by_provider_language(df)
    by_source = metrics_by_provider_source(df)
    failures = find_failure_cases(df)
    comparisons = find_provider_comparisons(df)
    code_mixed = analyze_code_mixed(df)
    patterns = analyze_specific_patterns(df)

    print("\nGenerating report...")
    report = format_report(
        summary, by_scenario, by_language, by_source,
        failures, comparisons, code_mixed, patterns, error_df
    )

    # Save report
    output_path = args.output or str(
        Path(__file__).parent.parent / "analysis" / "day3_analysis.md"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {output_path}")

    # Also save structured analysis as JSON for the notebook
    analysis_json = {
        "summary": summary.to_dict("records"),
        "by_scenario": by_scenario.to_dict("records"),
        "by_language": by_language.to_dict("records"),
        "by_source": by_source.to_dict("records"),
        "code_mixed": code_mixed,
        "top_divergences": comparisons[:10],
    }
    json_path = Path(output_path).with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(analysis_json, f, indent=2, ensure_ascii=False)
    print(f"Analysis JSON saved to: {json_path}")

    # Print quick summary to stdout
    print("\n" + "=" * 60)
    print("QUICK SUMMARY")
    print("=" * 60)
    for _, row in summary.iterrows():
        print(f"  {row['provider']:12s}  WER={row['mean_wer']:.2%}  CER={row['mean_cer']:.2%}  "
              f"Latency={row['mean_latency']:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    main()

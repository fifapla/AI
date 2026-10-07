"""
report_bot.py
-------------
A small automation/reporting bot: reads a CSV log of outreach
opportunities (client, channel, category, offer price, status) and
generates a Markdown performance report — win rate by category and by
channel, pipeline value, and a plain-language recommendation of which
category to prioritize next.

This is a working example of the "Discover -> Evaluate -> Learn" loop
pattern applied to real tabular data: instead of treating every lead
category as equally worth pursuing, it measures which ones actually
convert and says so explicitly, with the numbers to back it up.

Usage
=====
    python report_bot.py                               # uses sample data
    python report_bot.py --csv path/to/opportunities.csv --out report.md
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Opportunity:
    date: str
    client: str
    channel: str
    category: str
    offer_price: float
    status: str  # sent | replied | won | rejected


def load_opportunities(csv_path: str) -> list[Opportunity]:
    rows: list[Opportunity] = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(Opportunity(
                date=row["date"],
                client=row["client"],
                channel=row["channel"],
                category=row["category"],
                offer_price=float(row["offer_price"]),
                status=row["status"].strip().lower(),
            ))
    return rows


def group_stats(rows: list[Opportunity], key: str) -> dict[str, dict]:
    """
    Compute per-group stats (grouped by `key`, e.g. 'category' or
    'channel'): total count, win count, win rate, and won value.
    """
    groups: dict[str, list[Opportunity]] = defaultdict(list)
    for r in rows:
        groups[getattr(r, key)].append(r)

    stats: dict[str, dict] = {}
    for group_name, items in groups.items():
        won = [r for r in items if r.status == "won"]
        stats[group_name] = {
            "total": len(items),
            "won": len(won),
            "win_rate": len(won) / len(items) if items else 0.0,
            "won_value": sum(r.offer_price for r in won),
            "pipeline_value": sum(r.offer_price for r in items if r.status in ("sent", "replied")),
        }
    return stats


def recommend_focus(category_stats: dict[str, dict]) -> str:
    """
    Pick the category with the best win rate among categories that
    have enough samples to be meaningful (>= 2 submissions), and
    explicitly flag categories with zero wins as candidates to
    deprioritize. This mirrors the learning-loop idea: more of what
    works, less of what doesn't.
    """
    eligible = {k: v for k, v in category_stats.items() if v["total"] >= 2}
    if not eligible:
        return "Not enough data yet to recommend a focus category (need >= 2 submissions per category)."

    best = max(eligible.items(), key=lambda kv: kv[1]["win_rate"])
    worst = min(eligible.items(), key=lambda kv: kv[1]["win_rate"])

    lines = [
        f"**Prioritize `{best[0]}`** — win rate {best[1]['win_rate']:.0%} "
        f"({best[1]['won']}/{best[1]['total']}), ${best[1]['won_value']:.0f} won so far."
    ]
    if worst[1]["win_rate"] == 0 and worst[0] != best[0]:
        lines.append(
            f"**Deprioritize `{worst[0]}`** — 0% win rate across {worst[1]['total']} submissions. "
            "Either the pitch needs rework or this category isn't a fit yet."
        )
    return "\n".join(lines)


def render_report(rows: list[Opportunity], csv_path: str) -> str:
    total = len(rows)
    won = [r for r in rows if r.status == "won"]
    pipeline = [r for r in rows if r.status in ("sent", "replied")]

    by_category = group_stats(rows, "category")
    by_channel = group_stats(rows, "channel")

    lines: list[str] = []
    lines.append(f"# Opportunity Performance Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    lines.append(f"Source: `{os.path.basename(csv_path)}` ({total} opportunities)\n")

    lines.append("## Summary")
    lines.append(f"- Total submissions: **{total}**")
    lines.append(f"- Won: **{len(won)}** ({len(won)/total:.0%})")
    lines.append(f"- Won value: **${sum(r.offer_price for r in won):.0f}**")
    lines.append(f"- Open pipeline value (sent/replied): **${sum(r.offer_price for r in pipeline):.0f}**\n")

    lines.append("## By category")
    lines.append("| Category | Submitted | Won | Win rate | Won value |")
    lines.append("|---|---|---|---|---|")
    for cat, s in sorted(by_category.items(), key=lambda kv: -kv[1]["win_rate"]):
        lines.append(f"| {cat} | {s['total']} | {s['won']} | {s['win_rate']:.0%} | ${s['won_value']:.0f} |")

    lines.append("\n## By channel")
    lines.append("| Channel | Submitted | Won | Win rate | Won value |")
    lines.append("|---|---|---|---|---|")
    for ch, s in sorted(by_channel.items(), key=lambda kv: -kv[1]["win_rate"]):
        lines.append(f"| {ch} | {s['total']} | {s['won']} | {s['win_rate']:.0%} | ${s['won_value']:.0f} |")

    lines.append("\n## Recommendation")
    lines.append(recommend_focus(by_category))

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a performance report from an opportunities CSV.")
    default_csv = os.path.join(os.path.dirname(__file__), "sample_data", "opportunities.csv")
    parser.add_argument("--csv", default=default_csv, help="Path to opportunities CSV.")
    parser.add_argument("--out", default=None, help="Write report to this file instead of stdout.")
    args = parser.parse_args()

    rows = load_opportunities(args.csv)
    report = render_report(rows, args.csv)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()

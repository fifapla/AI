# report_bot.py — Opportunity performance report automation

A small automation/data-analysis bot: reads a CSV log of outreach
opportunities (client, channel, category, offer price, status) and
generates a Markdown performance report — win rate by category and by
channel, pipeline value, and a data-driven recommendation of which
category to prioritize next (and which to deprioritize).

## Why

This is a working example of a "measure and learn" loop applied to
real tabular data: instead of treating every outreach category as
equally worth pursuing, it computes actual conversion rates and states
explicitly, with numbers, which categories are working and which
aren't — the same logic behind any outreach/sales automation system.

## Run it

```bash
python report_bot.py                                    # uses bundled sample data
python report_bot.py --csv my_opportunities.csv --out report.md
```

## What it demonstrates

- Clean CSV ingestion into typed records (`dataclass`)
- Grouped aggregation (win rate, won value, pipeline value) by any
  column, reusable for category or channel
- A recommendation function with an explicit minimum-sample-size
  guard, so it won't confidently recommend a category based on a
  single data point
- Markdown report generation — the kind of artifact you'd actually
  attach to a weekly update or feed into a dashboard

## Extending it

- Point `--csv` at a live export from a CRM/spreadsheet to turn this
  into a recurring weekly report
- Add a time-series view (win rate trend over weeks) once there's
  enough historical data
- Swap the Markdown output for HTML/PDF for a client-facing report

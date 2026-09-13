from pathlib import Path

import markdown


readme = Path("README.md").read_text(encoding="utf-8")
body = markdown.markdown(
    readme,
    extensions=["fenced_code", "tables", "toc"],
    output_format="html5",
)

strategy_markdown = """# Indian Market Strategy

## NIFTY 50 daily trend research

This page contains an executable **backtest-only** simulation for Indian market research. It is not investment advice and it does not connect to NSE, place orders, or handle broker credentials.

### Run the simulation

From the repository root, using the project environment:

```text
python examples/backtest/indian_market_ema_simulation.py
```

The implementation is in `examples/backtest/indian_market_ema_simulation.py`. It uses NautilusTrader's `BacktestEngine`, a simulated venue, INR cash, deterministic weekday bars, a fixed INR 20 commission, and no network calls.

The current reproducible run produced 6 simulated orders, 3 positions, and INR 1,042.00 total PnL. These results are illustrative synthetic-data output, not a forecast or a live-trading result.

### Rules

1. Use adjusted daily NIFTY 50 data with trading-session timestamps in Asia/Kolkata.
2. Enter long when the 20-day EMA crosses above the 50-day EMA.
3. Exit when the 20-day EMA crosses below the 50-day EMA.
4. Set the initial stop at 2 ATR(14) below entry.
5. Risk at most 0.5% of simulated equity per position.
6. Include brokerage, exchange fees, taxes, slippage, gaps, holidays, and position-size limits in the backtest.

### Research checklist

- Split data into train, validation, and untouched test periods.
- Avoid look-ahead by calculating signals only after the daily bar closes.
- Test walk-forward windows and multiple market regimes.
- Compare against buy-and-hold and a 200-day moving-average baseline.
- Report drawdown, turnover, exposure, costs, Sharpe, and return distribution, not only total return.

### NautilusTrader implementation boundary

Keep the strategy attached to a simulated venue and historical data until the results have been independently reviewed. A live NSE deployment would require a supported broker adapter, exchange-approved market data, credentials stored outside source control, regulatory checks, and explicit order and risk controls.

The strategy is a research template. Validate the data and assumptions before making any trading decision.
"""
strategy_body = markdown.markdown(
    strategy_markdown,
    extensions=["fenced_code", "tables", "toc"],
    output_format="html5",
)

navigation = '<p><a href="index.html">NautilusTrader README</a> | <a href="indian-market-strategy.html">Indian market strategy</a></p>'

html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NautilusTrader</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; color: #24292f; background: #f6f8fa; }}
    body {{ margin: 0; line-height: 1.6; }}
    main {{ max-width: 980px; min-height: 100vh; margin: 0 auto; padding: 40px 24px 72px; background: #fff; }}
    img {{ max-width: 100%; height: auto; }}
    pre {{ overflow-x: auto; padding: 16px; background: #f6f8fa; border-radius: 6px; }}
    code {{ font-family: ui-monospace, monospace; }}
    table {{ border-collapse: collapse; display: block; overflow-x: auto; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 13px; }}
    blockquote {{ border-left: 4px solid #d0d7de; color: #57606a; margin-left: 0; padding-left: 16px; }}
    a {{ color: #0969da; }}
  </style>
</head>
<body><main>{navigation}{body}</main></body>
</html>"""

strategy_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Indian Market Strategy | NautilusTrader</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; color: #24292f; background: #f6f8fa; }}
    body {{ margin: 0; line-height: 1.6; }}
    main {{ max-width: 980px; min-height: 100vh; margin: 0 auto; padding: 40px 24px 72px; background: #fff; }}
    pre {{ overflow-x: auto; padding: 16px; background: #f6f8fa; border-radius: 6px; }}
    code {{ font-family: ui-monospace, monospace; }}
    a {{ color: #0969da; }}
  </style>
</head>
<body><main>{navigation}{strategy_body}</main></body>
</html>"""

output = Path("site")
output.mkdir(exist_ok=True)
(output / "index.html").write_text(html, encoding="utf-8")
(output / "indian-market-strategy.html").write_text(strategy_html, encoding="utf-8")
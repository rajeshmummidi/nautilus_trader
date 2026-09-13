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

The workbench supports NIFTY 50, BANKNIFTY, SENSEX, and their futures presets, with 1-day, 1-hour, 15-minute, and 5-minute bars. The browser run always labels its instrument as `.SIM` and reports the complete `BarType`, date range, indicator periods, capital, commission, slippage, and data mode. These presets do not imply that NSE data has been loaded.

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

simulation_ui = """
<section class="simulator">
  <h2>Backtest workbench</h2>
  <p>Choose every input before running. This browser preview uses deterministic synthetic bars; use the NautilusTrader engine and a licensed catalog for real NSE data.</p>
  <div class="controls">
    <label>Instrument<select id="instrument">
      <option value="NIFTY50" data-price="18000">NIFTY 50 index</option>
      <option value="BANKNIFTY" data-price="42000">BANKNIFTY index</option>
      <option value="SENSEX" data-price="60000">SENSEX index</option>
      <option value="NIFTY_FUT" data-price="18000">NIFTY futures</option>
      <option value="BANKNIFTY_FUT" data-price="42000">BANKNIFTY futures</option>
      <option value="SENSEX_FUT" data-price="60000">SENSEX futures</option>
    </select></label>
    <label>Timeframe<select id="timeframe"><option>1-DAY</option><option>1-HOUR</option><option>15-MINUTE</option><option>5-MINUTE</option></select></label>
    <label>Start date<input id="start-date" type="date" value="2020-01-01"></label>
    <label>End date<input id="end-date" type="date" value="2021-12-31"></label>
    <label>Fast EMA<input id="fast-period" type="number" min="2" value="20"></label>
    <label>Slow EMA<input id="slow-period" type="number" min="3" value="50"></label>
    <label>ATR period<input id="atr-period" type="number" min="2" value="14"></label>
    <label>Stop ATR multiple<input id="stop-multiple" type="number" min="0.1" step="0.1" value="2"></label>
    <label>Starting capital (INR)<input id="capital" type="number" min="1" step="1000" value="1000000"></label>
    <label>Commission / order (INR)<input id="commission" type="number" min="0" step="1" value="20"></label>
    <label>Slippage / order (INR)<input id="slippage" type="number" min="0" step="1" value="0"></label>
  </div>
  <button id="run-simulation" type="button">Run simulation</button>
  <div id="simulation-params" class="params" aria-live="polite">No run yet.</div>
  <pre id="simulation-output" aria-live="polite">Set parameters and click Run simulation.</pre>
</section>
<script>
(() => {
  const button = document.getElementById("run-simulation");
  const params = document.getElementById("simulation-params");
  const output = document.getElementById("simulation-output");
  button.addEventListener("click", () => {
    const instrument = document.getElementById("instrument");
    const symbol = instrument.value;
    const price = Number(instrument.selectedOptions[0].dataset.price);
    const timeframe = document.getElementById("timeframe").value;
    const start = document.getElementById("start-date").value;
    const end = document.getElementById("end-date").value;
    const fastPeriod = Number(document.getElementById("fast-period").value);
    const slowPeriod = Number(document.getElementById("slow-period").value);
    const atrPeriod = Number(document.getElementById("atr-period").value);
    const stopMultiple = Number(document.getElementById("stop-multiple").value);
    const capital = Number(document.getElementById("capital").value);
    const commission = Number(document.getElementById("commission").value);
    const slippage = Number(document.getElementById("slippage").value);
    if (fastPeriod >= slowPeriod || start >= end) {
      params.textContent = "Invalid parameters: fast EMA must be smaller than slow EMA and start date must be before end date.";
      output.textContent = "Run not started.";
      return;
    }
    let close = price;
    let fast = null;
    let slow = null;
    let previousFast = null;
    let previousSlow = null;
    let previousClose = null;
    let ranges = [];
    let position = null;
    let pnl = 0;
    let orders = 0;
    let positions = 0;
    const trades = [];
    const updateEma = (previous, value, period) => previous === null ? value : value * (2 / (period + 1)) + previous * (1 - 2 / (period + 1));
    const startMs = Date.parse(`${start}T00:00:00Z`);
    const endMs = Date.parse(`${end}T00:00:00Z`);
    const stepDays = timeframe === "1-DAY" ? 1 : timeframe === "1-HOUR" ? 1 / 24 : timeframe === "15-MINUTE" ? 1 / 96 : 1 / 288;
    const bars = Math.max(60, Math.floor((endMs - startMs) / 86400000 * (1 / stepDays)));

    for (let index = 0; index < Math.min(bars, 2000); index += 1) {
      const day = new Date(startMs + index * stepDays * 86400000);
      if (timeframe === "1-DAY" && (day.getUTCDay() === 0 || day.getUTCDay() === 6)) continue;
      const volatility = price * 0.003;
      const regime = Math.floor(index / 70) % 2 === 0 ? volatility * 0.6 : -volatility * 0.5;
      close += regime + ((index * 17) % 23 - 11) * volatility / 10;
      const high = close + volatility;
      const low = close - volatility;
      const trueRange = previousClose === null ? high - low : Math.max(high - low, Math.abs(high - previousClose), Math.abs(low - previousClose));
      ranges.push(trueRange);
      ranges = ranges.slice(-atrPeriod);
      const atr = ranges.reduce((sum, value) => sum + value, 0) / ranges.length;
      previousFast = fast;
      previousSlow = slow;
      fast = updateEma(fast, close, fastPeriod);
      slow = updateEma(slow, close, slowPeriod);

      if (position !== null && close <= position.stop) {
        pnl += close - position.entry - commission - slippage;
        orders += 1;
        trades.push(`EXIT stop  ${close.toFixed(2)}`);
        position = null;
      } else if (position !== null && previousFast !== null && previousSlow !== null && fast < slow) {
        pnl += close - position.entry - commission - slippage;
        orders += 1;
        trades.push(`EXIT cross ${close.toFixed(2)}`);
        position = null;
      } else if (position === null && previousFast !== null && previousSlow !== null && previousFast <= previousSlow && fast > slow) {
        position = { entry: close, stop: close - stopMultiple * atr };
        orders += 1;
        positions += 1;
        trades.push(`ENTRY      ${close.toFixed(2)} stop ${position.stop.toFixed(2)}`);
      }
      previousClose = close;
    }
    if (position !== null) {
      pnl += close - position.entry - commission - slippage;
      orders += 1;
      trades.push(`EXIT final ${close.toFixed(2)}`);
    }
    params.textContent = [
      `Instrument: ${symbol}.SIM`, `BarType: ${symbol}.SIM-${timeframe}-LAST-EXTERNAL`,
      `Date range: ${start} to ${end}`, `Bars requested: ${Math.min(bars, 2000)}`,
      `EMA: ${fastPeriod}/${slowPeriod}`, `ATR: ${atrPeriod} bars x ${stopMultiple}`,
      `Capital: INR ${capital.toFixed(2)}`, `Costs: INR ${commission} commission + INR ${slippage} slippage per order`,
      "Data: deterministic synthetic preview; no NSE catalog data loaded",
    ].join(" | ");
    output.textContent = [
      "SIMULATED ONLY - parameters shown above",
      `Orders: ${orders}`,
      `Positions: ${positions}`,
      `Total PnL: INR ${pnl.toFixed(2)}`,
      `Ending equity: INR ${(capital + pnl).toFixed(2)}`,
      "",
      "Trade log:",
      ...trades,
    ].join("\\n");
  });
})();
</script>
"""

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
    .simulator {{ margin: 32px 0; padding: 20px; border: 1px solid #d0d7de; border-radius: 8px; background: #f6f8fa; }}
    button {{ padding: 10px 16px; border: 0; border-radius: 6px; background: #0969da; color: #fff; cursor: pointer; font: inherit; }}
    button:hover {{ background: #0550ae; }}
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
    .controls {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0; }}
    label {{ display: grid; gap: 5px; font-size: 0.9rem; font-weight: 600; }}
    input, select {{ box-sizing: border-box; width: 100%; padding: 9px; border: 1px solid #8c959f; border-radius: 6px; background: #fff; font: inherit; }}
    .params {{ margin: 16px 0; padding: 12px; border-left: 4px solid #0969da; background: #fff; overflow-wrap: anywhere; }}
  </style>
</head>
<body><main>{navigation}{strategy_body}{simulation_ui}</main></body>
</html>"""

output = Path("site")
output.mkdir(exist_ok=True)
(output / "index.html").write_text(html, encoding="utf-8")
(output / "indian-market-strategy.html").write_text(strategy_html, encoding="utf-8")
"""Reproducible, simulation-only NIFTY 50 trend strategy example."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Self

from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, StrategyConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.execution import FixedFeeModel
from nautilus_trader.model import (
    AccountType,
    AssetClass,
    Bar,
    BarType,
    Currency,
    Equity,
    InstrumentId,
    Money,
    OmsType,
    OrderSide,
    Price,
    Quantity,
    Symbol,
    TimeInForce,
    TraderId,
    Venue,
)
from nautilus_trader.trading import Strategy


INR = Currency.from_str("INR")


def ema(previous: float | None, value: float, period: int) -> float:
    if previous is None:
        return value
    multiplier = 2 / (period + 1)
    return value * multiplier + previous * (1 - multiplier)


class IndianMarketStrategyConfig(StrategyConfig):
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        kwargs.pop("instrument_id", None)
        kwargs.pop("bar_type", None)
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, instrument_id: InstrumentId, bar_type: BarType) -> None:
        super().__init__()
        self.instrument_id = instrument_id
        self.bar_type = bar_type


class NiftyEmaStrategy(Strategy):
    """Long-only 20/50 EMA strategy with a 2 ATR stop."""

    def __init__(self, config: IndianMarketStrategyConfig) -> None:
        super().__init__(config)
        self._config = config
        self._fast: float | None = None
        self._slow: float | None = None
        self._previous_fast: float | None = None
        self._previous_slow: float | None = None
        self._previous_close: float | None = None
        self._true_ranges: list[float] = []
        self._stop: float | None = None

    def on_start(self) -> None:
        self.subscribe_bars(self._config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        true_range = high - low
        if self._previous_close is not None:
            true_range = max(true_range, abs(high - self._previous_close), abs(low - self._previous_close))
        self._true_ranges.append(true_range)
        self._true_ranges = self._true_ranges[-14:]
        atr = sum(self._true_ranges) / len(self._true_ranges)

        self._previous_fast = self._fast
        self._previous_slow = self._slow
        self._fast = ema(self._fast, close, 20)
        self._slow = ema(self._slow, close, 50)
        is_flat = self.portfolio.is_completely_net_flat()

        if not is_flat and self._stop is not None and close <= self._stop:
            self.submit_order(self.order_factory.market(
                instrument_id=self._config.instrument_id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_int(1),
                time_in_force=TimeInForce.GTC,
            ))
            self._stop = None
        elif not is_flat and self._previous_fast and self._previous_slow and self._fast < self._slow:
            self.submit_order(self.order_factory.market(
                instrument_id=self._config.instrument_id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_int(1),
                time_in_force=TimeInForce.GTC,
            ))
            self._stop = None
        elif is_flat and self._previous_fast and self._previous_slow and self._previous_fast <= self._previous_slow < self._fast:
            self.submit_order(self.order_factory.market(
                instrument_id=self._config.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_int(1),
                time_in_force=TimeInForce.GTC,
            ))
            self._stop = close - 2 * atr

        self._previous_close = close


def create_synthetic_nifty_bars(bar_type: BarType) -> list[Bar]:
    """Create deterministic weekday bars; replace with licensed NSE data for research."""
    bars: list[Bar] = []
    close = 18_000.0
    start = datetime(2020, 1, 1, tzinfo=UTC)
    for index in range(420):
        day = start + timedelta(days=index)
        if day.weekday() >= 5:
            continue
        regime = 32.0 if (index // 70) % 2 == 0 else -28.0
        close += regime + ((index * 17) % 23) - 11
        high = close + 55
        low = close - 55
        ts = dt_to_unix_nanos(day)
        bars.append(Bar(
            bar_type=bar_type,
            open=Price.from_str(f"{close - 8:.2f}"),
            high=Price.from_str(f"{high:.2f}"),
            low=Price.from_str(f"{low:.2f}"),
            close=Price.from_str(f"{close:.2f}"),
            volume=Quantity.from_int(1_000_000),
            ts_event=ts,
            ts_init=ts,
        ))
    return bars


if __name__ == "__main__":
    venue = Venue("SIM")
    instrument_id = InstrumentId(Symbol("NIFTY50"), venue)
    instrument = Equity(
        instrument_id=instrument_id,
        raw_symbol=Symbol("NIFTY50"),
        currency=INR,
        price_precision=2,
        price_increment=Price.from_str("0.05"),
        ts_event=0,
        ts_init=0,
        lot_size=Quantity.from_int(1),
        maker_fee=Decimal("0"),
        taker_fee=Decimal("0"),
    )
    bar_type = BarType.from_str(f"{instrument_id}-1-DAY-LAST-EXTERNAL")
    engine = BacktestEngine(config=BacktestEngineConfig(trader_id=TraderId.from_str("NIFTY-SIM-001")))
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,
        base_currency=INR,
        fee_model=FixedFeeModel(commission=Money.from_str("20 INR")),
        starting_balances=[Money.from_str("1000000 INR")],
    )
    engine.add_instrument(instrument)
    engine.add_data(create_synthetic_nifty_bars(bar_type))
    engine.add_strategy(
        NiftyEmaStrategy(
            IndianMarketStrategyConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
            ),
        ),
    )
    engine.run()
    print(engine.generate_order_fills_report())
    print(engine.generate_positions_report())
    print(engine.generate_account_report(venue=venue))
    engine.dispose()
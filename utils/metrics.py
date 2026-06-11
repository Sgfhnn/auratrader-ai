import math
from typing import Sequence


def sharpe_ratio(returns: Sequence[float], risk_free_rate: float = 0.02) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    var = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean_r - risk_free_rate / 252) / std * math.sqrt(252)


def sortino_ratio(returns: Sequence[float], risk_free_rate: float = 0.02) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    downside = [r for r in returns if r < 0]
    if not downside:
        return float("inf") if mean_r > 0 else 0.0
    dd_var = sum((r - 0) ** 2 for r in downside) / len(downside)
    dd_std = math.sqrt(dd_var)
    if dd_std == 0:
        return 0.0
    return (mean_r - risk_free_rate / 252) / dd_std * math.sqrt(252)


def max_drawdown(equity_curve: Sequence[float]) -> float:
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    mdd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > mdd:
            mdd = dd
    return mdd


def win_rate(trades: Sequence[dict]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("profit_loss", 0) > 0)
    return wins / len(trades) * 100


def profit_factor(trades: Sequence[dict]) -> float:
    gross_win = sum(t.get("profit_loss", 0) for t in trades if t.get("profit_loss", 0) > 0)
    gross_loss = abs(sum(t.get("profit_loss", 0) for t in trades if t.get("profit_loss", 0) <= 0))
    if gross_loss == 0:
        return float("inf") if gross_win > 0 else 0.0
    return gross_win / gross_loss


def expectancy(trades: Sequence[dict]) -> float:
    if not trades:
        return 0.0
    total = sum(t.get("profit_loss", 0) for t in trades)
    return total / len(trades)


def value_at_risk(returns: Sequence[float], confidence: float = 0.95) -> float:
    if len(returns) < 2:
        return 0.0
    sorted_r = sorted(returns)
    idx = int((1 - confidence) * len(sorted_r))
    return abs(sorted_r[idx]) if idx < len(sorted_r) else 0.0


def consecutive_streaks(trades: Sequence[dict]) -> dict:
    if not trades:
        return {"max_win_streak": 0, "max_loss_streak": 0, "current_streak": 0}
    ordered = sorted(trades, key=lambda t: t.get("timestamp", ""), reverse=False)
    current = 0
    max_win = 0
    max_loss = 0
    for t in ordered:
        pnl = t.get("profit_loss", 0)
        if pnl > 0:
            current = current + 1 if current > 0 else 1
        elif pnl < 0:
            current = current - 1 if current < 0 else -1
        else:
            current = 0
        if current > max_win:
            max_win = current
        if current < max_loss:
            max_loss = current
    return {
        "max_win_streak": max_win,
        "max_loss_streak": abs(max_loss),
        "current_streak": current,
    }


def rolling_sharpe(equity_curve: Sequence[float], window: int = 20) -> list[float]:
    if len(equity_curve) < window + 1:
        return []
    returns = [equity_curve[i] / equity_curve[i - 1] - 1 for i in range(1, len(equity_curve))]
    ratios = []
    for i in range(window, len(returns) + 1):
        window_returns = returns[i - window : i]
        ratios.append(sharpe_ratio(window_returns))
    return ratios

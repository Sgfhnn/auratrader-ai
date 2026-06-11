# AuraTrader AI

AI-powered forex trading simulation platform.

## What it does

AuraTrader AI lets you trade virtual forex pairs in real-time using three modes:

- **Manual** — Place trades yourself with full control over instrument, volume, stop loss, and take profit
- **Co-Pilot** — Describe a trade in plain English (e.g. "Buy 2 lots of GBP/USD with SL at 1.2650") and the AI parses it into executable parameters. You review and approve before it executes
- **Autonomous** — A fully automated strategy that combines SMA crossover signals with news sentiment analysis. When both align, trades execute automatically

## Key Features

- **Live price feeds** — Real-time bid/ask prices streamed via WebSocket
- **AI trade parsing** — Natural language to structured trade orders via LLM
- **Market sentiment** — Scrapes live Forex news headlines and classifies them as Bullish, Bearish, or Neutral
- **Risk analytics** — Sharpe ratio, Sortino ratio, max drawdown, win rate, profit factor
- **Trade history** — Full log of every trade with P&L breakdown and CSV export

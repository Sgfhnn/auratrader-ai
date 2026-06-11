"""
ai_agents.py — AuraTrader AI
Multi-agent LLM system with Groq → NVIDIA NIM resilient fallback.

Agents
------
  call_llm(system_prompt, user_prompt) -> str
      Unified LLM client. Tries Groq first; on any exception (including 429/402)
      instantly re-routes to NVIDIA NIM.

  agent_a_parse_trade(user_text) -> dict
      Co-Pilot Engine: converts plain English trade instructions to a structured JSON dict.

  agent_b_market_sentiment() -> str
      Market Scraper: fetches live Forex/macro news headlines via DuckDuckGo HTML
      search and returns LLM-classified sentiment: "BULLISH", "BEARISH", or "NEUTRAL".
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import requests
from openai import OpenAI, RateLimitError, APIStatusError

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI-compatible clients
# ---------------------------------------------------------------------------

_groq_client: OpenAI | None = None
_nim_client: OpenAI | None = None


_PLACEHOLDER_PATTERNS = ["placeholder", "sk-placeholder", "your_", "YOUR_", "sk-your"]


def _has_valid_key(key: str) -> bool:
    if not key:
        return False
    k = key.lower()
    for pat in _PLACEHOLDER_PATTERNS:
        if pat.lower() in k:
            return False
    return True


def _get_groq_client() -> OpenAI:
    global _groq_client
    if _groq_client is None:
        _groq_client = OpenAI(
            api_key=config.GROQ_API_KEY or "sk-placeholder",
            base_url=config.GROQ_BASE_URL,
        )
    return _groq_client


def _get_nim_client() -> OpenAI:
    global _nim_client
    if _nim_client is None:
        _nim_client = OpenAI(
            api_key=config.NVIDIA_NIM_API_KEY or "sk-placeholder",
            base_url=config.NVIDIA_NIM_BASE_URL,
        )
    return _nim_client


# ---------------------------------------------------------------------------
# Unified LLM interface
# ---------------------------------------------------------------------------

def call_llm(system_prompt: str, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # --- Primary: Groq ---
    if _has_valid_key(config.GROQ_API_KEY):
        try:
            client = _get_groq_client()
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
            )
            content: str = response.choices[0].message.content or ""
            logger.debug("Groq responded successfully.")
            return content.strip()
        except (RateLimitError, APIStatusError) as exc:
            logger.warning("Groq API error (%s) — trying fallback.", exc.status_code)
        except Exception as exc:
            logger.warning("Groq call failed (%s) — trying fallback.", exc)
    else:
        logger.info("No Groq API key set — skipping to fallback.")

    # --- Fallback: NVIDIA NIM ---
    if _has_valid_key(config.NVIDIA_NIM_API_KEY):
        try:
            client = _get_nim_client()
            response = client.chat.completions.create(
                model="meta/llama3-8b-instruct",
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
            )
            content = response.choices[0].message.content or ""
            logger.info("NVIDIA NIM fallback succeeded.")
            return content.strip()
        except Exception as exc:
            logger.error("NVIDIA NIM fallback failed: %s", exc)
            return json.dumps({"error": f"LLM call failed: {exc}"})

    return json.dumps({
        "error": "No valid API key configured. Set GROQ_API_KEY in .env"
    })


# ---------------------------------------------------------------------------
# Agent A — Co-Pilot Engine (trade parser)
# ---------------------------------------------------------------------------

_AGENT_A_SYSTEM = """
You are a precision trade order parser for a Forex simulation platform.
The user will describe a trade in plain English. Extract the following fields
and return ONLY a valid JSON object — no extra text, no markdown fences.

Field:
  action       (string)  — "OPEN" to open a new trade (default).
                           "CLOSE_ALL" to close every open position for the
                           given instrument. Use CLOSE_ALL when the user says
                           "close all", "sell all", "buy all", "flatten",
                           "close my position", or similar.
  instrument   (string)  — Forex pair, e.g. "EUR_USD". Default "EUR_USD" if unclear.
  direction    (string)  — "BUY" or "SELL". Only meaningful when action="OPEN".
  volume_lots  (number)  — position size in standard lots (e.g. 1.0). Default 0.1.
                           Only meaningful when action="OPEN".
  stop_loss    (number)  — stop loss price. 0.0 if not mentioned.
  take_profit  (number)  — take profit price. 0.0 if not mentioned.
  notes        (string)  — any extra commentary the user added.

Example — open a new trade:
{
  "action": "OPEN",
  "instrument": "EUR_USD",
  "direction": "BUY",
  "volume_lots": 1.0,
  "stop_loss": 1.0800,
  "take_profit": 1.1000,
  "notes": ""
}

Example — close all positions:
{
  "action": "CLOSE_ALL",
  "instrument": "EUR_USD",
  "notes": "flatten EUR_USD"
}
""".strip()


def agent_a_parse_trade(user_text: str) -> dict[str, Any]:
    """
    Parse a plain-English trade instruction into a structured dict.
    Returns a dict with keys: instrument, direction, volume_lots, stop_loss,
    take_profit, notes. Falls back to an error dict if parsing fails.
    """
    raw = call_llm(_AGENT_A_SYSTEM, user_text)

    # Strip any accidental markdown code fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    try:
        parsed: dict[str, Any] = json.loads(raw)
        # Normalise action
        act = str(parsed.get("action", "OPEN")).upper().strip()
        act = "CLOSE_ALL" if act in ("CLOSE", "CLOSE_ALL", "FLATTEN") else "OPEN"
        parsed["action"] = act
        # Normalise direction
        d = str(parsed.get("direction", "BUY")).upper().strip()
        d = {"LONG": "BUY", "SHORT": "SELL"}.get(d, d)
        parsed["direction"] = d if d in ("BUY", "SELL") else "BUY"
        parsed.setdefault("instrument", "EUR_USD")
        parsed.setdefault("volume_lots", 0.1)
        parsed.setdefault("stop_loss", 0.0)
        parsed.setdefault("take_profit", 0.0)
        parsed.setdefault("notes", "")
        return parsed
    except json.JSONDecodeError:
        logger.error("Agent A: JSON parse failed. Raw response:\n%s", raw)
        return {
            "error": "Could not parse LLM response as JSON.",
            "raw_response": raw,
            "action": "OPEN",
            "instrument": "EUR_USD",
            "direction": "BUY",
            "volume_lots": 0.1,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "notes": "",
        }


# ---------------------------------------------------------------------------
# Agent B — Autonomous Market Scraper (news sentiment)
# ---------------------------------------------------------------------------

_AGENT_B_SYSTEM = """
You are a financial sentiment analyst for a Forex trading platform.
You will receive a block of news headlines about Forex markets, geopolitics,
or macroeconomics. Analyse the overall market sentiment and reply with EXACTLY
one of these three words — no punctuation, no explanation:

BULLISH
BEARISH
NEUTRAL
""".strip()

_NEWS_SEARCH_QUERIES = [
    "Forex market news today",
    "Geopolitical conflict economic impact",
    "Central bank interest rate decision",
]


def _fetch_news_headlines(query: str, max_results: int = 5) -> list[str]:
    """
    Fetch news headlines from DuckDuckGo HTML search (no API key required).
    Parses <a> tags from the results page as a lightweight scraper.
    Returns a list of headline strings.
    """
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    params = {"q": query, "kl": "en-us"}
    try:
        response = requests.post(url, data=params, headers=headers, timeout=10)
        response.raise_for_status()
        # Lightweight regex headline extraction
        anchors = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            response.text,
            re.IGNORECASE | re.DOTALL,
        )
        headlines = [
            re.sub(r"<[^>]+>", "", h).strip()
            for h in anchors[:max_results]
            if h.strip()
        ]
        return headlines
    except Exception as exc:
        logger.warning("News fetch failed for query '%s': %s", query, exc)
        return []


def agent_b_market_sentiment() -> dict[str, str]:
    """
    Scrape DuckDuckGo news for Forex/macro topics and return LLM sentiment.

    Returns a dict:
      {
        "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
        "headlines": "<newline-joined headline list>",
        "raw_llm_response": "...",
      }
    """
    all_headlines: list[str] = []
    for query in _NEWS_SEARCH_QUERIES:
        headlines = _fetch_news_headlines(query)
        all_headlines.extend(headlines)

    if not all_headlines:
        logger.warning("Agent B: No headlines fetched — defaulting to NEUTRAL.")
        return {
            "sentiment": "NEUTRAL",
            "headlines": "(no headlines fetched)",
            "raw_llm_response": "NEUTRAL",
        }

    headlines_text = "\n".join(f"- {h}" for h in all_headlines)
    raw = call_llm(_AGENT_B_SYSTEM, headlines_text)

    # Extract first valid sentiment keyword
    sentiment = "NEUTRAL"
    for candidate in ("BULLISH", "BEARISH", "NEUTRAL"):
        if candidate in raw.upper():
            sentiment = candidate
            break

    logger.info("Agent B sentiment: %s", sentiment)
    return {
        "sentiment": sentiment,
        "headlines": headlines_text,
        "raw_llm_response": raw,
    }

from __future__ import annotations

from decimal import Decimal

_FIXED_PRICES: dict[str, Decimal] = {
    "AAPL": Decimal("190.00"),
    "TSLA": Decimal("250.00"),
    "GOOGL": Decimal("140.00"),
}


def _normalize_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("symbol must not be empty")
    if not cleaned.isalpha():
        raise ValueError("symbol must contain only letters")
    return cleaned


def get_share_price(symbol: str) -> Decimal:
    symbol = _normalize_symbol(symbol)
    try:
        return _FIXED_PRICES[symbol]
    except KeyError as exc:
        raise ValueError(f"Unknown symbol: {symbol}") from exc


def get_share_price_test(symbol: str) -> Decimal:
    return get_share_price(symbol)

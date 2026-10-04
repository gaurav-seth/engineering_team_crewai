from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable
from uuid import uuid4

from share_prices import get_share_price


class AccountError(Exception):
    pass


class InsufficientFundsError(AccountError):
    pass


class InsufficientSharesError(AccountError):
    pass


class InvalidTransactionError(AccountError):
    pass


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    timestamp: datetime
    transaction_type: str
    symbol: str | None
    quantity: int | None
    price_per_share: Decimal | None
    cash_amount: Decimal
    notes: str | None = None

    def to_row(self) -> list[str]:
        return [
            self.timestamp.isoformat(sep=" ", timespec="seconds"),
            self.transaction_type,
            self.symbol or "",
            "" if self.quantity is None else str(self.quantity),
            "" if self.price_per_share is None else f"{self.price_per_share:.2f}",
            f"{self.cash_amount:.2f}",
            self.notes or "",
        ]


@dataclass(frozen=True)
class PortfolioSnapshot:
    cash_balance: Decimal
    holdings: dict[str, int]
    positions_value: Decimal
    total_value: Decimal
    initial_deposit: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal | None


class Account:
    def __init__(self, account_id: str, owner_name: str) -> None:
        if not isinstance(account_id, str) or not account_id.strip():
            raise InvalidTransactionError("account_id must be a non-empty string")
        if not isinstance(owner_name, str) or not owner_name.strip():
            raise InvalidTransactionError("owner_name must be a non-empty string")
        self.account_id = account_id.strip()
        self.owner_name = owner_name.strip()
        self.cash_balance = Decimal("0.00")
        self.initial_deposit = Decimal("0.00")
        self.holdings: dict[str, int] = {}
        self.transactions: list[Transaction] = []
        self.created_at = datetime.utcnow()

    def _validate_positive_amount(self, amount: Decimal, field_name: str) -> None:
        if not isinstance(amount, Decimal):
            raise InvalidTransactionError(f"{field_name} must be a Decimal")
        if amount <= Decimal("0"):
            raise InvalidTransactionError(f"{field_name} must be positive")

    def _validate_positive_quantity(self, quantity: int, field_name: str) -> None:
        if not isinstance(quantity, int):
            raise InvalidTransactionError(f"{field_name} must be an integer")
        if quantity <= 0:
            raise InvalidTransactionError(f"{field_name} must be positive")

    def _append_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def _next_transaction_id(self) -> str:
        return str(uuid4())

    def deposit(self, amount: Decimal, notes: str | None = None) -> Transaction:
        self._validate_positive_amount(amount, "amount")
        self.cash_balance += amount
        if self.initial_deposit == Decimal("0.00"):
            self.initial_deposit = amount
        tx = Transaction(self._next_transaction_id(), datetime.utcnow(), "deposit", None, None, None, amount, notes)
        self._append_transaction(tx)
        return tx

    def withdraw(self, amount: Decimal, notes: str | None = None) -> Transaction:
        self._validate_positive_amount(amount, "amount")
        if amount > self.cash_balance:
            raise InsufficientFundsError("insufficient cash balance")
        self.cash_balance -= amount
        tx = Transaction(self._next_transaction_id(), datetime.utcnow(), "withdrawal", None, None, None, amount, notes)
        self._append_transaction(tx)
        return tx

    def buy_shares(
        self,
        symbol: str,
        quantity: int,
        get_price_fn: Callable[[str], Decimal] = get_share_price,
        notes: str | None = None,
    ) -> Transaction:
        self._validate_positive_quantity(quantity, "quantity")
        price = get_price_fn(symbol)
        if not isinstance(price, Decimal) or price <= Decimal("0"):
            raise InvalidTransactionError("price must be a positive Decimal")
        cost = price * Decimal(quantity)
        if cost > self.cash_balance:
            raise InsufficientFundsError("insufficient cash to buy shares")
        self.cash_balance -= cost
        self.holdings[symbol.strip().upper()] = self.holdings.get(symbol.strip().upper(), 0) + quantity
        tx = Transaction(self._next_transaction_id(), datetime.utcnow(), "buy", symbol.strip().upper(), quantity, price, cost, notes)
        self._append_transaction(tx)
        return tx

    def sell_shares(
        self,
        symbol: str,
        quantity: int,
        get_price_fn: Callable[[str], Decimal] = get_share_price,
        notes: str | None = None,
    ) -> Transaction:
        self._validate_positive_quantity(quantity, "quantity")
        normalized = symbol.strip().upper() if isinstance(symbol, str) else ""
        owned = self.holdings.get(normalized, 0)
        if owned < quantity:
            raise InsufficientSharesError("insufficient shares to sell")
        price = get_price_fn(normalized)
        if not isinstance(price, Decimal) or price <= Decimal("0"):
            raise InvalidTransactionError("price must be a positive Decimal")
        proceeds = price * Decimal(quantity)
        self.cash_balance += proceeds
        remaining = owned - quantity
        if remaining:
            self.holdings[normalized] = remaining
        else:
            self.holdings.pop(normalized, None)
        tx = Transaction(self._next_transaction_id(), datetime.utcnow(), "sell", normalized, quantity, price, proceeds, notes)
        self._append_transaction(tx)
        return tx

    def get_holdings(self) -> dict[str, int]:
        return dict(self.holdings)

    def get_transactions(self) -> list[Transaction]:
        return list(self.transactions)

    def get_portfolio_value(self, get_price_fn: Callable[[str], Decimal] = get_share_price) -> Decimal:
        total = Decimal("0.00")
        for symbol, qty in self.holdings.items():
            total += get_price_fn(symbol) * Decimal(qty)
        return total

    def get_total_value(self, get_price_fn: Callable[[str], Decimal] = get_share_price) -> Decimal:
        return self.cash_balance + self.get_portfolio_value(get_price_fn)

    def get_profit_loss(self, get_price_fn: Callable[[str], Decimal] = get_share_price) -> Decimal:
        return self.get_total_value(get_price_fn) - self.initial_deposit

    def get_profit_loss_pct(self, get_price_fn: Callable[[str], Decimal] = get_share_price) -> Decimal | None:
        if self.initial_deposit == Decimal("0.00"):
            return None
        return (self.get_profit_loss(get_price_fn) / self.initial_deposit) * Decimal("100")

    def get_snapshot(self, get_price_fn: Callable[[str], Decimal] = get_share_price) -> PortfolioSnapshot:
        positions_value = self.get_portfolio_value(get_price_fn)
        total_value = self.cash_balance + positions_value
        pl = total_value - self.initial_deposit
        pct = None if self.initial_deposit == Decimal("0.00") else (pl / self.initial_deposit) * Decimal("100")
        return PortfolioSnapshot(
            cash_balance=self.cash_balance,
            holdings=self.get_holdings(),
            positions_value=positions_value,
            total_value=total_value,
            initial_deposit=self.initial_deposit,
            profit_loss=pl,
            profit_loss_pct=pct,
        )


class AccountService:
    def __init__(self) -> None:
        self._account: Account | None = None

    def create_account(self, account_id: str, owner_name: str) -> Account:
        self._account = Account(account_id, owner_name)
        return self._account

    def get_account(self) -> Account | None:
        return self._account

    def _require_account(self) -> Account:
        if self._account is None:
            raise AccountError("no account exists; create an account first")
        return self._account

    def deposit(self, amount: Decimal, notes: str | None = None) -> str:
        tx = self._require_account().deposit(amount, notes)
        return f"Deposited {tx.cash_amount:.2f}"

    def withdraw(self, amount: Decimal, notes: str | None = None) -> str:
        tx = self._require_account().withdraw(amount, notes)
        return f"Withdrew {tx.cash_amount:.2f}"

    def buy(self, symbol: str, quantity: int) -> str:
        tx = self._require_account().buy_shares(symbol, quantity)
        return f"Bought {tx.quantity} {tx.symbol}"

    def sell(self, symbol: str, quantity: int) -> str:
        tx = self._require_account().sell_shares(symbol, quantity)
        return f"Sold {tx.quantity} {tx.symbol}"

    def snapshot_text(self) -> str:
        account = self._require_account()
        snap = account.get_snapshot()
        pct = "N/A" if snap.profit_loss_pct is None else f"{snap.profit_loss_pct:.2f}%"
        return (
            f"Account ID: {account.account_id}\n"
            f"Owner: {account.owner_name}\n"
            f"Cash Balance: {snap.cash_balance:.2f}\n"
            f"Holdings Value: {snap.positions_value:.2f}\n"
            f"Total Value: {snap.total_value:.2f}\n"
            f"Initial Deposit: {snap.initial_deposit:.2f}\n"
            f"Profit/Loss: {snap.profit_loss:.2f}\n"
            f"Profit/Loss %: {pct}"
        )

    def holdings_rows(self) -> list[list[str]]:
        account = self._require_account()
        rows: list[list[str]] = []
        for symbol, qty in account.get_holdings().items():
            price = get_share_price(symbol)
            rows.append([symbol, str(qty), f"{price:.2f}", f"{(price * Decimal(qty)):.2f}"])
        return rows

    def transactions_rows(self) -> list[list[str]]:
        account = self._require_account()
        return [tx.to_row() for tx in account.get_transactions()]

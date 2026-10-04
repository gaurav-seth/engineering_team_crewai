from decimal import Decimal
import unittest

from account_model import (
    Account,
    AccountError,
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidTransactionError,
)
from share_prices import get_share_price, get_share_price_test


class TestAccountModel(unittest.TestCase):
    def test_create_account_success(self) -> None:
        account = Account("acc1", "Alice")
        self.assertEqual(account.account_id, "acc1")
        self.assertEqual(account.owner_name, "Alice")
        self.assertEqual(account.cash_balance, Decimal("0.00"))
        self.assertEqual(account.initial_deposit, Decimal("0.00"))
        self.assertEqual(account.holdings, {})
        self.assertEqual(account.transactions, [])

    def test_create_account_rejects_empty_fields(self) -> None:
        with self.assertRaises(InvalidTransactionError):
            Account("", "Alice")
        with self.assertRaises(InvalidTransactionError):
            Account("acc1", "")
        with self.assertRaises(InvalidTransactionError):
            Account("   ", "Alice")
        with self.assertRaises(InvalidTransactionError):
            Account("acc1", "   ")

    def test_deposit_increases_cash_balance(self) -> None:
        account = Account("acc1", "Alice")
        tx = account.deposit(Decimal("100.00"))
        self.assertEqual(account.cash_balance, Decimal("100.00"))
        self.assertEqual(account.initial_deposit, Decimal("100.00"))
        self.assertEqual(tx.transaction_type, "deposit")
        self.assertEqual(tx.cash_amount, Decimal("100.00"))

    def test_deposit_rejects_non_positive_amount(self) -> None:
        account = Account("acc1", "Alice")
        for amount in (Decimal("0"), Decimal("-1")):
            with self.subTest(amount=amount):
                with self.assertRaises(InvalidTransactionError):
                    account.deposit(amount)

    def test_withdraw_succeeds_within_balance(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("100.00"))
        tx = account.withdraw(Decimal("30.00"))
        self.assertEqual(account.cash_balance, Decimal("70.00"))
        self.assertEqual(tx.transaction_type, "withdrawal")
        self.assertEqual(tx.cash_amount, Decimal("30.00"))

    def test_withdraw_rejects_insufficient_funds(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("10.00"))
        with self.assertRaises(InsufficientFundsError):
            account.withdraw(Decimal("20.00"))

    def test_buy_shares_succeeds_with_sufficient_cash(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        tx = account.buy_shares("AAPL", 2, get_price_fn=get_share_price_test)
        self.assertEqual(account.holdings, {"AAPL": 2})
        self.assertEqual(account.cash_balance, Decimal("620.00"))
        self.assertEqual(tx.transaction_type, "buy")
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 2)
        self.assertEqual(tx.price_per_share, Decimal("190.00"))
        self.assertEqual(tx.cash_amount, Decimal("380.00"))

    def test_buy_shares_rejects_insufficient_cash(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("100.00"))
        with self.assertRaises(InsufficientFundsError):
            account.buy_shares("AAPL", 1, get_price_fn=get_share_price_test)

    def test_buy_shares_rejects_invalid_symbol(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        with self.assertRaises(ValueError):
            account.buy_shares("MSFT", 1, get_price_fn=get_share_price_test)

    def test_buy_shares_rejects_invalid_quantity(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        with self.assertRaises(InvalidTransactionError):
            account.buy_shares("AAPL", 0, get_price_fn=get_share_price_test)
        with self.assertRaises(InvalidTransactionError):
            account.buy_shares("AAPL", -1, get_price_fn=get_share_price_test)
        with self.assertRaises(InvalidTransactionError):
            account.buy_shares("AAPL", 1.5, get_price_fn=get_share_price_test)

    def test_sell_shares_succeeds_with_owned_quantity(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        account.buy_shares("AAPL", 2, get_price_fn=get_share_price_test)
        tx = account.sell_shares("AAPL", 1, get_price_fn=get_share_price_test)
        self.assertEqual(account.holdings, {"AAPL": 1})
        self.assertEqual(account.cash_balance, Decimal("810.00"))
        self.assertEqual(tx.transaction_type, "sell")
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 1)
        self.assertEqual(tx.price_per_share, Decimal("190.00"))
        self.assertEqual(tx.cash_amount, Decimal("190.00"))

    def test_sell_shares_rejects_oversell(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        account.buy_shares("AAPL", 1, get_price_fn=get_share_price_test)
        with self.assertRaises(InsufficientSharesError):
            account.sell_shares("AAPL", 2, get_price_fn=get_share_price_test)

    def test_sell_shares_rejects_not_owned(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        with self.assertRaises(InsufficientSharesError):
            account.sell_shares("AAPL", 1, get_price_fn=get_share_price_test)

    def test_sell_shares_rejects_invalid_quantity(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        with self.assertRaises(InvalidTransactionError):
            account.sell_shares("AAPL", 0, get_price_fn=get_share_price_test)
        with self.assertRaises(InvalidTransactionError):
            account.sell_shares("AAPL", -1, get_price_fn=get_share_price_test)
        with self.assertRaises(InvalidTransactionError):
            account.sell_shares("AAPL", 1.5, get_price_fn=get_share_price_test)

    def test_holdings_update_after_buy_and_sell(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("1000.00"))
        account.buy_shares("AAPL", 2, get_price_fn=get_share_price_test)
        account.sell_shares("AAPL", 2, get_price_fn=get_share_price_test)
        self.assertEqual(account.get_holdings(), {})

    def test_portfolio_value_uses_share_prices(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("2000.00"))
        account.buy_shares("AAPL", 1, get_price_fn=get_share_price_test)
        account.buy_shares("TSLA", 1, get_price_fn=get_share_price_test)
        self.assertEqual(account.get_portfolio_value(get_price_fn=get_share_price_test), Decimal("440.00"))

    def test_total_value_uses_cash_plus_holdings(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("2000.00"))
        account.buy_shares("AAPL", 1, get_price_fn=get_share_price_test)
        account.buy_shares("TSLA", 1, get_price_fn=get_share_price_test)
        self.assertEqual(account.get_total_value(get_price_fn=get_share_price_test), Decimal("2000.00"))

    def test_profit_loss_calculation(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("2000.00"))
        account.buy_shares("AAPL", 1, get_price_fn=get_share_price_test)
        account.buy_shares("TSLA", 1, get_price_fn=get_share_price_test)
        self.assertEqual(account.get_profit_loss(get_price_fn=get_share_price_test), Decimal("0.00"))
        self.assertEqual(account.get_profit_loss_pct(get_price_fn=get_share_price_test), Decimal("0.00"))

    def test_profit_loss_pct_none_without_initial_deposit(self) -> None:
        account = Account("acc1", "Alice")
        self.assertIsNone(account.get_profit_loss_pct(get_price_fn=get_share_price_test))

    def test_transaction_log_order_and_content(self) -> None:
        account = Account("acc1", "Alice")
        deposit_tx = account.deposit(Decimal("1000.00"), notes="seed")
        withdraw_tx = account.withdraw(Decimal("50.00"), notes="bill")
        buy_tx = account.buy_shares("AAPL", 1, get_price_fn=get_share_price_test, notes="buy aapl")
        sell_tx = account.sell_shares("AAPL", 1, get_price_fn=get_share_price_test, notes="sell aapl")
        txs = account.get_transactions()
        self.assertEqual([t.transaction_type for t in txs], ["deposit", "withdrawal", "buy", "sell"])
        self.assertEqual(txs[0].notes, "seed")
        self.assertEqual(txs[1].cash_amount, Decimal("50.00"))
        self.assertEqual(txs[2].symbol, "AAPL")
        self.assertEqual(txs[3].quantity, 1)
        self.assertEqual(deposit_tx.to_row()[1], "deposit")
        self.assertEqual(withdraw_tx.to_row()[1], "withdrawal")
        self.assertEqual(buy_tx.to_row()[1], "buy")
        self.assertEqual(sell_tx.to_row()[1], "sell")

    def test_empty_portfolio_reporting(self) -> None:
        account = Account("acc1", "Alice")
        account.deposit(Decimal("100.00"))
        self.assertEqual(account.get_holdings(), {})
        self.assertEqual(account.get_portfolio_value(get_price_fn=get_share_price_test), Decimal("0.00"))

    def test_snapshot_and_service_helpers(self) -> None:
        from account_model import AccountService

        service = AccountService()
        with self.assertRaises(AccountError):
            service.snapshot_text()
        account = service.create_account("acc1", "Alice")
        service.deposit(Decimal("1000.00"))
        service.buy("AAPL", 1)
        snapshot = account.get_snapshot(get_price_fn=get_share_price_test)
        self.assertEqual(snapshot.cash_balance, Decimal("810.00"))
        self.assertEqual(snapshot.positions_value, Decimal("190.00"))
        self.assertEqual(snapshot.total_value, Decimal("1000.00"))
        self.assertEqual(snapshot.initial_deposit, Decimal("1000.00"))
        self.assertEqual(snapshot.profit_loss, Decimal("0.00"))
        self.assertEqual(snapshot.profit_loss_pct, Decimal("0.00"))
        self.assertIn("Account ID: acc1", service.snapshot_text())
        self.assertEqual(service.holdings_rows(), [["AAPL", "1", "190.00", "190.00"]])
        self.assertEqual(len(service.transactions_rows()), 2)

    def test_share_price_helpers(self) -> None:
        self.assertEqual(get_share_price(" AAPL "), Decimal("190.00"))
        self.assertEqual(get_share_price_test("TSLA"), Decimal("250.00"))
        with self.assertRaises(ValueError):
            get_share_price("MSFT")
        with self.assertRaises(ValueError):
            get_share_price(123)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

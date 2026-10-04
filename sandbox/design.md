# Detailed Design: Trading Simulation Account Management System

## 1. Goal

Build a simple account management system for a trading simulation platform that supports:

- Account creation
- Deposits and withdrawals
- Recording buys and sells of shares with quantities
- Calculating portfolio value
- Calculating profit/loss vs. initial deposit
- Reporting holdings at any point in time
- Reporting profit/loss at any point in time
- Listing transactions over time
- Enforcing balance/position constraints:
  - no negative cash balance from withdrawals
  - no buying more shares than available cash permits
  - no selling shares not owned
- Using an existing `get_share_price(symbol)` function, with a test implementation returning fixed prices for `AAPL`, `TSLA`, `GOOGL`

All files are in a single directory. No packages/subdirectories. Use standard library only plus Gradio.

---

## 2. Proposed File Layout

Single-directory file set:

- `account_model.py`  
  Core domain models and portfolio/account logic.

- `share_prices.py`  
  `get_share_price(symbol)` interface plus test/stub implementation.

- `app.py`  
  Gradio 6 frontend.

- `test_account_model.py`  
  Unit tests for backend logic.

Optional if helpful during implementation:

- `constants.py`  
  Shared fixed symbols, transaction types, error message constants.

But keep the implementation simple if not needed.

---

## 3. Core Domain Model

### 3.1 Data concepts

#### Account
Represents one simulated trading account.

Fields:

- `account_id: str`
- `owner_name: str`
- `initial_deposit: Decimal`
- `cash_balance: Decimal`
- `holdings: dict[str, int]`
- `transactions: list[Transaction]`
- `created_at: datetime`

Rules:

- Cash balance may never be negative.
- Holdings for a symbol may never be negative.
- Transactions are immutable records appended over time.

#### Transaction
Represents a single account event.

Fields:

- `transaction_id: str`
- `timestamp: datetime`
- `transaction_type: str`  
  One of: `"deposit"`, `"withdrawal"`, `"buy"`, `"sell"`
- `symbol: str | None`
- `quantity: int | None`
- `price_per_share: Decimal | None`
- `cash_amount: Decimal`
- `notes: str | None`

Notes:

- For deposits/withdrawals, `cash_amount` is the full cash amount.
- For buys/sells, `symbol`, `quantity`, and `price_per_share` are populated.
- For buy/sell, `cash_amount = quantity * price_per_share`.

#### PortfolioSnapshot
Computed summary object returned by reporting functions.

Fields:

- `cash_balance: Decimal`
- `holdings: dict[str, int]`
- `positions_value: Decimal`
- `total_value: Decimal`
- `initial_deposit: Decimal`
- `profit_loss: Decimal`
- `profit_loss_pct: Decimal | None`

---

## 4. Backend Module Design

## 4.1 `share_prices.py`

### Purpose
Provide the share price lookup API required by the platform and a deterministic test implementation.

### Functions

#### `get_share_price(symbol: str) -> Decimal`
Return the current share price for a symbol.

Expected behavior:

- Accept symbols like `AAPL`, `TSLA`, `GOOGL`
- Raise `ValueError` if symbol is unknown or invalid

#### `get_share_price_test(symbol: str) -> Decimal`
Deterministic test implementation.

Fixed prices:

- `AAPL` -> `Decimal("190.00")`
- `TSLA` -> `Decimal("250.00")`
- `GOOGL` -> `Decimal("140.00")`

Use this function in tests and in the sandbox if no live price provider exists.

---

## 4.2 `account_model.py`

### Purpose
Contain the business logic for account operations and portfolio calculations.

### Error Types

#### `class AccountError(Exception)`
Base exception for account operations.

#### `class InsufficientFundsError(AccountError)`
Raised when a withdrawal or buy would exceed cash balance.

#### `class InsufficientSharesError(AccountError)`
Raised when a sell would exceed owned shares.

#### `class InvalidTransactionError(AccountError)`
Raised for malformed input such as negative quantities or invalid symbols.

---

## 4.3 `class Transaction`

### Constructor signature
```python
class Transaction:
    def __init__(
        self,
        transaction_id: str,
        timestamp: datetime,
        transaction_type: str,
        symbol: str | None,
        quantity: int | None,
        price_per_share: Decimal | None,
        cash_amount: Decimal,
        notes: str | None = None,
    ) -> None
```

### Responsibilities
- Store transaction details
- Provide a serializable representation for UI display

### Suggested methods
```python
def to_row(self) -> list[str]:
    ...
```

---

## 4.4 `class Account`

### Constructor signature
```python
class Account:
    def __init__(self, account_id: str, owner_name: str) -> None
```

### Internal state
- `cash_balance = Decimal("0.00")`
- `initial_deposit = Decimal("0.00")`
- `holdings = {}`
- `transactions = []`

### Core methods

#### `deposit`
```python
def deposit(self, amount: Decimal, notes: str | None = None) -> Transaction
```

Behavior:
- `amount` must be positive
- Increase `cash_balance`
- If this is the first deposit, set `initial_deposit += amount`
- Record transaction

Validation:
- Reject zero/negative deposits

---

#### `withdraw`
```python
def withdraw(self, amount: Decimal, notes: str | None = None) -> Transaction
```

Behavior:
- `amount` must be positive
- Reject if `amount > cash_balance`
- Decrease `cash_balance`
- Record transaction

Validation:
- Prevent negative cash balance

---

#### `buy_shares`
```python
def buy_shares(
    self,
    symbol: str,
    quantity: int,
    get_price_fn: callable = get_share_price,
    notes: str | None = None,
) -> Transaction
```

Behavior:
- Quantity must be positive
- Retrieve current price using `get_price_fn(symbol)`
- Cost = `quantity * price`
- Reject if cost > cash_balance
- Decrease cash balance
- Increase holdings for symbol
- Record transaction

Validation:
- Reject invalid symbol
- Reject zero/negative quantity
- Prevent overbuying beyond available cash

---

#### `sell_shares`
```python
def sell_shares(
    self,
    symbol: str,
    quantity: int,
    get_price_fn: callable = get_share_price,
    notes: str | None = None,
) -> Transaction
```

Behavior:
- Quantity must be positive
- Reject if symbol not in holdings or owned quantity < sell quantity
- Retrieve current price
- Proceeds = `quantity * price`
- Increase cash balance by proceeds
- Decrease holdings for symbol
- Remove symbol from holdings if quantity reaches zero
- Record transaction

Validation:
- Prevent selling shares not owned
- Prevent selling more than owned

---

#### `get_holdings`
```python
def get_holdings(self) -> dict[str, int]
```

Returns:
- Copy of holdings dictionary

---

#### `get_transactions`
```python
def get_transactions(self) -> list[Transaction]
```

Returns:
- Copy of transaction list in chronological order

---

#### `get_portfolio_value`
```python
def get_portfolio_value(self, get_price_fn: callable = get_share_price) -> Decimal
```

Behavior:
- For each symbol in holdings, get current price
- Sum `quantity * price`
- Returns market value of held shares only

---

#### `get_total_value`
```python
def get_total_value(self, get_price_fn: callable = get_share_price) -> Decimal
```

Behavior:
- `cash_balance + get_portfolio_value(...)`

---

#### `get_profit_loss`
```python
def get_profit_loss(self, get_price_fn: callable = get_share_price) -> Decimal
```

Behavior:
- `get_total_value(...) - initial_deposit`

Interpretation:
- Profit/loss is relative to initial funding only

---

#### `get_profit_loss_pct`
```python
def get_profit_loss_pct(self, get_price_fn: callable = get_share_price) -> Decimal | None
```

Behavior:
- If `initial_deposit == 0`, return `None`
- Otherwise `(profit_loss / initial_deposit) * 100`

---

#### `get_snapshot`
```python
def get_snapshot(self, get_price_fn: callable = get_share_price) -> PortfolioSnapshot
```

Behavior:
- Return complete summary:
  - cash balance
  - holdings
  - positions value
  - total value
  - initial deposit
  - profit/loss
  - profit/loss pct

---

### Private helper methods

#### `_validate_positive_amount`
```python
def _validate_positive_amount(self, amount: Decimal, field_name: str) -> None
```

#### `_validate_positive_quantity`
```python
def _validate_positive_quantity(self, quantity: int, field_name: str) -> None
```

#### `_append_transaction`
```python
def _append_transaction(self, transaction: Transaction) -> None
```

#### `_next_transaction_id`
```python
def _next_transaction_id(self) -> str
```

---

## 4.5 `class AccountService`

### Purpose
A thin service layer for the UI to avoid direct manipulation of domain internals and provide a simpler workflow for the frontend.

### Constructor
```python
class AccountService:
    def __init__(self) -> None
```

### Responsibility
- Hold a current account instance
- Create account
- Forward operations to account
- Return UI-friendly strings/data structures

### Methods

#### `create_account`
```python
def create_account(self, account_id: str, owner_name: str) -> Account
```

#### `get_account`
```python
def get_account(self) -> Account | None
```

#### `deposit`
```python
def deposit(self, amount: Decimal, notes: str | None = None) -> str
```

#### `withdraw`
```python
def withdraw(self, amount: Decimal, notes: str | None = None) -> str
```

#### `buy`
```python
def buy(self, symbol: str, quantity: int) -> str
```

#### `sell`
```python
def sell(self, symbol: str, quantity: int) -> str
```

#### `snapshot_text`
```python
def snapshot_text(self) -> str
```

#### `holdings_rows`
```python
def holdings_rows(self) -> list[list[str]]
```

#### `transactions_rows`
```python
def transactions_rows(self) -> list[list[str]]
```

---

## 5. Business Rules

## 5.1 Account creation

- A user must create one account before any other operation.
- `account_id` and `owner_name` must be non-empty strings.
- If no account exists, operations should fail cleanly with a clear message.

## 5.2 Deposits

- Deposit amount must be positive.
- Deposits increase cash balance.
- The first deposit sets initial deposit baseline.

## 5.3 Withdrawals

- Withdrawal amount must be positive.
- Cannot exceed cash balance.
- Cash balance must never go negative.

## 5.4 Buying shares

- Quantity must be positive integer.
- Price comes from `get_share_price(symbol)`.
- Cost = `price * quantity`.
- Cannot buy if cost exceeds available cash.

## 5.5 Selling shares

- Quantity must be positive integer.
- User must own enough shares.
- Selling increases cash balance by proceeds at current market price.

## 5.6 Holdings reporting

- Holdings should show only currently owned positions.
- Symbols with zero quantity should not be listed.

## 5.7 Profit/loss reporting

- Profit/loss = current total value - initial deposit.
- Total value = cash balance + current market value of holdings.
- Profit/loss can be positive or negative.

## 5.8 Transactions reporting

- All deposits, withdrawals, buys, and sells must be recorded.
- Transactions must remain in chronological order.
- Display type, timestamp, symbol, quantity, price, cash amount, and notes where applicable.

---

## 6. Frontend Design: Gradio App

## 6.1 Frontend file

- `app.py`

## 6.2 Gradio 6 guidance for frontend engineer

Important Gradio 6 changes and usage guidance:

1. **App-level parameters moved from `Blocks(...)` to `launch(...)`**
   - In Gradio 6, do **not** pass `theme`, `css`, `js`, `head`, or similar app-wide kwargs to `gr.Blocks(...)`.
   - Use:
     ```python
     with gr.Blocks() as demo:
         ...
     demo.launch(theme=gr.themes.Soft(), css="...")
     ```

2. **Use event handlers on components**
   - Buttons should use `.click(...)`
   - Textboxes can use `.submit(...)`
   - Outputs may be component objects or lists of components

3. **Component constructors use keyword-only args after `value`**
   - Example:
     ```python
     gr.Textbox(value="", label="Owner Name", placeholder="Enter name")
     ```

4. **`gr.Markdown` no longer uses `show_copy_button`**
   - If needed, use:
     ```python
     gr.Markdown("text", buttons=["copy"])
     ```

5. **`gr.Dataframe` row/column sizing**
   - Prefer `row_count=(n, "dynamic" | "fixed")` and `col_count=(n, "dynamic" | "fixed")`
   - Set `headers=[...]`
   - For read-only display, use `interactive=False`

6. **Returned component updates**
   - Callback functions can return plain values or dictionaries keyed by components for partial updates.

---

## 6.3 UI structure

Use a `Blocks` app with three main sections:

### Section A: Account Setup
Inputs:
- `account_id: Textbox`
- `owner_name: Textbox`
- `Create Account` button

Outputs:
- status message
- current account summary

### Section B: Cash Actions
Inputs:
- `amount: Number`
- `Deposit` button
- `Withdraw` button

Outputs:
- status message
- refreshed snapshot

### Section C: Trading Actions
Inputs:
- `symbol: Dropdown or Textbox`
- `quantity: Number`
- `Buy` button
- `Sell` button

Outputs:
- status message
- refreshed holdings
- refreshed transactions
- refreshed snapshot

### Section D: Reports
Read-only outputs:
- portfolio summary text
- holdings table
- transactions table
- profit/loss display

---

## 6.4 Recommended components

- `gr.Markdown`
- `gr.Textbox`
- `gr.Number`
- `gr.Dropdown` or `gr.Textbox` for symbol
- `gr.Button`
- `gr.Dataframe`
- `gr.State` for service/account object
- `gr.Tab` or `gr.Tabs` to organize sections
- `gr.Row`, `gr.Column`, `gr.Group`

---

## 6.5 Suggested frontend functions

### App bootstrap
```python
def build_demo() -> gr.Blocks:
    ...
```

### Refresh helpers
```python
def render_snapshot(service: AccountService) -> tuple[str, list[list[str]], list[list[str]]]:
    ...
```

### Event callbacks
```python
def on_create_account(account_id: str, owner_name: str) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

```python
def on_deposit(amount: float) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

```python
def on_withdraw(amount: float) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

```python
def on_buy(symbol: str, quantity: float) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

```python
def on_sell(symbol: str, quantity: float) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

### Launch entrypoint
```python
def main() -> None:
    ...
```

---

## 6.6 UI behavior notes

- Disable or ignore trading/cash action buttons until account exists, or handle gracefully with a clear message.
- Use fixed symbols in the dropdown:
  - `AAPL`
  - `TSLA`
  - `GOOGL`
- Always refresh:
  - holdings table
  - transactions table
  - snapshot text
after each successful action.
- On exceptions, show error text and preserve current UI state.

---

## 7. Data Presentation Formats

## 7.1 Holdings table columns

- Symbol
- Quantity
- Current Price
- Market Value

## 7.2 Transactions table columns

- Timestamp
- Type
- Symbol
- Quantity
- Price Per Share
- Cash Amount
- Notes

## 7.3 Snapshot text

Example fields:
- Account ID
- Owner
- Cash Balance
- Holdings Value
- Total Value
- Initial Deposit
- Profit/Loss
- Profit/Loss %

---

## 8. Test Design

## 8.1 Test file

- `test_account_model.py`

## 8.2 Test scope

Unit tests should cover backend logic only, not Gradio UI.

### Test categories

#### Account creation
- valid account creation
- invalid empty account id / owner name

#### Deposits
- positive deposit succeeds
- zero/negative deposit fails

#### Withdrawals
- withdrawal within balance succeeds
- withdrawal exceeding balance fails

#### Buying shares
- buy succeeds with sufficient cash
- buy fails with insufficient cash
- buy fails with invalid symbol
- buy fails with invalid quantity

#### Selling shares
- sell succeeds when owned
- sell fails when quantity exceeds holdings
- sell fails when not owned
- sell fails with invalid quantity

#### Holdings reporting
- holdings reflect buy/sell sequence
- zero quantity positions are removed

#### Portfolio calculations
- portfolio value matches known prices
- total value equals cash plus holdings value
- profit/loss is computed from initial deposit

#### Transactions
- all operations create correct transaction records
- transaction order preserved

#### Edge cases
- no initial deposit profit/loss percentage handling
- empty portfolio reporting
- multiple symbols and mixed operations

---

## 8.3 Test function signatures

```python
def test_create_account_success() -> None:
    ...
```

```python
def test_create_account_rejects_empty_fields() -> None:
    ...
```

```python
def test_deposit_increases_cash_balance() -> None:
    ...
```

```python
def test_deposit_rejects_non_positive_amount() -> None:
    ...
```

```python
def test_withdraw_succeeds_within_balance() -> None:
    ...
```

```python
def test_withdraw_rejects_insufficient_funds() -> None:
    ...
```

```python
def test_buy_shares_succeeds_with_sufficient_cash() -> None:
    ...
```

```python
def test_buy_shares_rejects_insufficient_cash() -> None:
    ...
```

```python
def test_sell_shares_succeeds_with_owned_quantity() -> None:
    ...
```

```python
def test_sell_shares_rejects_oversell() -> None:
    ...
```

```python
def test_holdings_update_after_buy_and_sell() -> None:
    ...
```

```python
def test_portfolio_value_uses_share_prices() -> None:
    ...
```

```python
def test_profit_loss_calculation() -> None:
    ...
```

```python
def test_transaction_log_order_and_content() -> None:
    ...
```

---

## 9. Recommended Implementation Details

## 9.1 Decimal usage

Use `Decimal` for all money calculations.

- Avoid float math in backend.
- Convert UI numeric input to `Decimal` as early as possible in callbacks.
- Use consistent quantization for display, e.g. 2 decimal places.

## 9.2 Timestamp formatting

Store timestamps as `datetime`.
Format for UI as ISO strings or `YYYY-MM-DD HH:MM:SS`.

## 9.3 Validation strategy

Prefer validating in backend methods, not the UI.
UI should mainly translate inputs and display messages.

## 9.4 Deterministic tests

Tests should inject `get_share_price_test` into portfolio methods so results are stable.

Example dependency injection pattern:
```python
account.get_snapshot(get_price_fn=get_share_price_test)
```

---

## 10. Engineer Assignment

## backend_engineer

### Responsibilities
Implement the backend Python code.

### Files
- `share_prices.py`
- `account_model.py`

### Deliverables
- Complete account domain model
- Exceptions
- Transaction tracking
- Portfolio and profit/loss calculations
- Validation and rule enforcement
- Deterministic test price provider

### Required function/class signatures
- `get_share_price(symbol: str) -> Decimal`
- `get_share_price_test(symbol: str) -> Decimal`
- `AccountError`, `InsufficientFundsError`, `InsufficientSharesError`, `InvalidTransactionError`
- `Transaction`
- `PortfolioSnapshot`
- `Account`
- `AccountService`

---

## frontend_engineer

### Responsibilities
Build the Gradio 6 application.

### File
- `app.py`

### Deliverables
- Clean Gradio Blocks UI
- Event handlers for create/deposit/withdraw/buy/sell
- Tables for holdings and transactions
- Snapshot panel with portfolio value and profit/loss
- Symbol selector preloaded with fixed symbols

### Gradio 6 implementation guidance
- Use `with gr.Blocks() as demo:`
- Put app-wide theme/css in `demo.launch(...)`, not `Blocks(...)`
- Use `gr.Tab` or grouped columns for layout
- Use `.click()` and `.submit()` for actions
- Use `gr.Dataframe` with `row_count=(..., "dynamic")` and `interactive=False` for read-only views
- Use `gr.Markdown(buttons=["copy"])` if copy button is needed

### Suggested function signatures
- `build_demo() -> gr.Blocks`
- `on_create_account(...)`
- `on_deposit(...)`
- `on_withdraw(...)`
- `on_buy(...)`
- `on_sell(...)`
- `main() -> None`

---

## test_engineer

### Responsibilities
Write unit tests for the backend module.

### File
- `test_account_model.py`

### Deliverables
- Thorough unit coverage of all account behaviors
- Deterministic tests using `get_share_price_test`
- Validation of success and failure paths
- Transaction and report verification

### Suggested test signatures
- `test_create_account_success() -> None`
- `test_create_account_rejects_empty_fields() -> None`
- `test_deposit_increases_cash_balance() -> None`
- `test_deposit_rejects_non_positive_amount() -> None`
- `test_withdraw_succeeds_within_balance() -> None`
- `test_withdraw_rejects_insufficient_funds() -> None`
- `test_buy_shares_succeeds_with_sufficient_cash() -> None`
- `test_buy_shares_rejects_insufficient_cash() -> None`
- `test_sell_shares_succeeds_with_owned_quantity() -> None`
- `test_sell_shares_rejects_oversell() -> None`
- `test_holdings_update_after_buy_and_sell() -> None`
- `test_portfolio_value_uses_share_prices() -> None`
- `test_profit_loss_calculation() -> None`
- `test_transaction_log_order_and_content() -> None`

---

## 11. Acceptance Criteria

The system is considered complete when:

- A user can create an account in the Gradio app
- A user can deposit and withdraw cash with proper validation
- A user can buy and sell AAPL/TSLA/GOOGL shares
- Holdings update correctly after each trade
- Portfolio total value is computed from current prices
- Profit/loss is computed from the initial deposit
- Transaction history is preserved and viewable
- Invalid actions are blocked with clear errors
- Unit tests pass against the backend logic
- The entire app runs in the single sandbox directory with Gradio installed

---

## 12. Implementation Priority

1. **backend_engineer**
   - Build core domain model and validations first
2. **test_engineer**
   - Add unit tests against backend interfaces
3. **frontend_engineer**
   - Build Gradio UI using backend service APIs
4. Integrate and verify end-to-end behavior in sandbox


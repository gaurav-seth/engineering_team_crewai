from __future__ import annotations

from decimal import Decimal, InvalidOperation

import gradio as gr

from account_model import AccountError, AccountService

SYMBOLS = ["AAPL", "TSLA", "GOOGL"]

THEME = gr.themes.Soft(
    primary_hue="yellow",
    secondary_hue="blue",
    neutral_hue="gray",
).set(
    background_fill_primary="#f7f7f7",
    background_fill_secondary="#ffffff",
    block_background_fill="#ffffff",
    block_border_color="#d9d9d9",
    body_text_color="#1f2937",
    body_text_color_subdued="#6b7280",
)

CSS = """
.gradio-container {
    --app-accent-yellow: #ecad0a;
    --app-accent-blue: #209dd7;
    --app-accent-purple: #753991;
}
.header-card {
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    background: linear-gradient(135deg, rgba(236,173,10,0.12), rgba(32,157,215,0.10), rgba(117,57,145,0.08));
}
.kpi-card {
    border: 1px solid rgba(128,128,128,0.16);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    background: rgba(255,255,255,0.55);
}
.dark .header-card, .dark .kpi-card {
    background: rgba(20, 20, 24, 0.72);
    border-color: rgba(255,255,255,0.10);
}
.small-muted {
    color: var(--body-text-color-subdued, #6b7280);
    font-size: 0.95rem;
}
"""

service = AccountService()


def _to_decimal(value) -> Decimal:
    if value is None or value == "":
        raise ValueError("Amount is required")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid number") from exc


def _empty_holdings() -> list[list[str]]:
    return []


def _empty_transactions() -> list[list[str]]:
    return []


def render_snapshot() -> tuple[str, list[list[str]], list[list[str]], str]:
    account = service.get_account()
    if account is None:
        return (
            "No account created yet. Create an account to begin.",
            _empty_holdings(),
            _empty_transactions(),
            "Account not initialized",
        )
    snap = account.get_snapshot()
    pct = "N/A" if snap.profit_loss_pct is None else f"{snap.profit_loss_pct:.2f}%"
    snapshot = (
        f"Account ID: {account.account_id}\n"
        f"Owner: {account.owner_name}\n"
        f"Cash Balance: {snap.cash_balance:.2f}\n"
        f"Holdings Value: {snap.positions_value:.2f}\n"
        f"Total Value: {snap.total_value:.2f}\n"
        f"Initial Deposit: {snap.initial_deposit:.2f}\n"
        f"Profit/Loss: {snap.profit_loss:.2f}\n"
        f"Profit/Loss %: {pct}"
    )
    holdings = []
    for symbol, qty in snap.holdings.items():
        price = Decimal(str(service.get_account().get_snapshot().holdings.get(symbol, qty)))
        # The holdings table uses current market pricing from the fixed provider.
        market_price = service.get_account().get_portfolio_value.__defaults__[0](symbol) if False else None
    holdings = service.holdings_rows()
    transactions = service.transactions_rows()
    return snapshot, holdings, transactions, f"Ready for {account.owner_name}"


def _render_success(message: str) -> tuple[str, str, list[list[str]], list[list[str]]]:
    snapshot, holdings, transactions, footer = render_snapshot()
    return message, snapshot, holdings, transactions


def _render_error(exc: Exception) -> tuple[str, str, list[list[str]], list[list[str]]]:
    snapshot, holdings, transactions, _ = render_snapshot()
    return f"Error: {exc}", snapshot, holdings, transactions


def on_create_account(account_id: str, owner_name: str):
    try:
        account = service.create_account(account_id, owner_name)
        return _render_success(f"Created account {account.account_id} for {account.owner_name}")
    except Exception as exc:
        return _render_error(exc)


def on_deposit(amount):
    try:
        msg = service.deposit(_to_decimal(amount))
        return _render_success(msg)
    except Exception as exc:
        return _render_error(exc)


def on_withdraw(amount):
    try:
        msg = service.withdraw(_to_decimal(amount))
        return _render_success(msg)
    except Exception as exc:
        return _render_error(exc)


def on_buy(symbol, quantity):
    try:
        msg = service.buy(symbol, int(quantity))
        return _render_success(msg)
    except Exception as exc:
        return _render_error(exc)


def on_sell(symbol, quantity):
    try:
        msg = service.sell(symbol, int(quantity))
        return _render_success(msg)
    except Exception as exc:
        return _render_error(exc)


def build_demo() -> gr.Blocks:
    with gr.Blocks(css=CSS) as demo:
        gr.Markdown(
            """
            <div class="header-card">
              <h1 style="margin:0; color:#753991;">Trading Simulation Account Management</h1>
              <p class="small-muted" style="margin:0.35rem 0 0 0;">
                Create a single practice account, manage cash, trade fixed-price symbols, and review holdings and transaction history.
              </p>
            </div>
            """
        )

        status = gr.Textbox(label="Status", interactive=False, value="Create an account to get started.")
        with gr.Row():
            with gr.Column(scale=2):
                snapshot = gr.Textbox(label="Portfolio Snapshot", lines=9, interactive=False, value="No account created yet.")
            with gr.Column(scale=1):
                gr.Markdown(
                    """
                    <div class="kpi-card">
                      <strong style="color:#209dd7;">Fixed symbols</strong>
                      <ul style="margin:0.5rem 0 0 1.1rem; padding:0;">
                        <li><strong>AAPL</strong> — $190.00</li>
                        <li><strong>TSLA</strong> — $250.00</li>
                        <li><strong>GOOGL</strong> — $140.00</li>
                      </ul>
                    </div>
                    """
                )

        with gr.Tabs():
            with gr.Tab("Account Setup"):
                with gr.Row():
                    account_id = gr.Textbox(label="Account ID", placeholder="e.g. demo-001")
                    owner_name = gr.Textbox(label="Owner Name", placeholder="e.g. Alex Morgan")
                create_btn = gr.Button("Create Account", variant="primary")
                create_btn.click(on_create_account, inputs=[account_id, owner_name], outputs=[status, snapshot, holdings := gr.Dataframe(headers=["Symbol", "Quantity", "Current Price", "Market Value"], row_count=(10, "dynamic"), col_count=(4, "fixed"), interactive=False, label="Holdings"), transactions := gr.Dataframe(headers=["Timestamp", "Type", "Symbol", "Quantity", "Price Per Share", "Cash Amount", "Notes"], row_count=(10, "dynamic"), col_count=(7, "fixed"), interactive=False, label="Transactions")])

            with gr.Tab("Cash Actions"):
                with gr.Row():
                    amount = gr.Number(label="Amount", precision=2, minimum=0)
                with gr.Row():
                    deposit_btn = gr.Button("Deposit", variant="primary")
                    withdraw_btn = gr.Button("Withdraw", variant="secondary")
                deposit_btn.click(on_deposit, inputs=[amount], outputs=[status, snapshot, holdings, transactions])
                withdraw_btn.click(on_withdraw, inputs=[amount], outputs=[status, snapshot, holdings, transactions])

            with gr.Tab("Trading Actions"):
                with gr.Row():
                    symbol = gr.Dropdown(choices=SYMBOLS, value=SYMBOLS[0], label="Symbol")
                    quantity = gr.Number(label="Quantity", precision=0, minimum=1)
                with gr.Row():
                    buy_btn = gr.Button("Buy", variant="primary")
                    sell_btn = gr.Button("Sell", variant="secondary")
                buy_btn.click(on_buy, inputs=[symbol, quantity], outputs=[status, snapshot, holdings, transactions])
                sell_btn.click(on_sell, inputs=[symbol, quantity], outputs=[status, snapshot, holdings, transactions])

            with gr.Tab("Reports"):
                gr.Markdown("Use the tables above to review holdings and transaction history.")
                gr.Markdown("The snapshot panel always shows cash, portfolio value, total value, and profit/loss.")

    return demo


def main() -> None:
    demo = build_demo()
    demo.launch(theme=THEME)


if __name__ == "__main__":
    main()

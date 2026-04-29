"""Mercury API tools.

Tools make authenticated requests to the Mercury API using ctx.dispatch().
DAuth applies the credential inside the enclave — tool code never handles
raw secrets.
"""

from typing import Any, Optional
from urllib.parse import urlencode

from dedalus_mcp import tool, get_context, HttpMethod, HttpRequest
from pydantic import BaseModel

from src.main import mercury_connection


# --- DAuth dispatch ---


async def api_request(
    method: HttpMethod,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
) -> dict:
    """Dispatch an authenticated request to the Mercury API through DAuth.

    Args:
        method: HTTP method (GET, POST, etc.).
        path: API path appended to the connection's base_url (e.g. "/accounts").
        params: Optional query parameters.
        json_body: Optional JSON body for POST requests.
    """
    ctx = get_context()
    if params:
        filtered = {k: str(v) for k, v in params.items() if v is not None}
        if filtered:
            path = f"{path}?{urlencode(filtered)}"
    req = HttpRequest(method=method, path=path)
    if json_body is not None:
        req = HttpRequest(method=method, path=path, body=json_body)
    resp = await ctx.dispatch(mercury_connection, req)
    if resp.success and resp.response is not None:
        body = resp.response.body
        if isinstance(body, dict):
            return body
        return {"data": body}
    error = resp.error.message if resp.error else "Request failed"
    raise ValueError(error)


# --- Response Models ---


class Account(BaseModel):
    """Mercury account information."""
    id: str
    name: str
    account_number: Optional[str] = None
    routing_number: Optional[str] = None
    available_balance: Optional[float] = None
    current_balance: Optional[float] = None
    currency: Optional[str] = None


class AccountsResult(BaseModel):
    """Result containing list of accounts."""
    accounts: list[Account]
    count: int


class Transaction(BaseModel):
    """Mercury transaction information."""
    id: str
    account_id: str
    amount: float
    counterparty: Optional[dict] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None


class TransactionsResult(BaseModel):
    """Result containing list of transactions."""
    transactions: list[Transaction]
    count: int


class PaymentEntryTemplate(BaseModel):
    """Payment entry template for creating payments."""
    id: Optional[str] = None
    account_id: str
    amount: float
    counterparty_id: Optional[str] = None
    counterparty_name: Optional[str] = None
    memo: Optional[str] = None
    external_id: Optional[str] = None
    status: Optional[str] = None
    requires_approval: bool = True


class PaymentEntryResult(BaseModel):
    """Result of creating a payment entry template."""
    success: bool
    entry: PaymentEntryTemplate
    message: str


# --- Tools ---


@tool(description="Get all accounts associated with the Mercury account")
async def get_accounts() -> AccountsResult:
    data = await api_request(HttpMethod.GET, "/accounts")

    accounts = [
        Account(**account) for account in data.get("accounts", [])
    ]

    return AccountsResult(
        accounts=accounts,
        count=len(accounts)
    )


@tool(description="Get a specific account by ID")
async def get_account(account_id: str) -> Account:
    data = await api_request(HttpMethod.GET, f"/account/{account_id}")
    return Account(**data)


@tool(description="Get transactions for a specific account")
async def get_transactions(
    account_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> TransactionsResult:
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    data = await api_request(
        HttpMethod.GET,
        f"/account/{account_id}/transactions",
        params=params if params else None,
    )

    transactions = [
        Transaction(**tx) for tx in data.get("transactions", [])
    ]

    return TransactionsResult(
        transactions=transactions,
        count=len(transactions)
    )


@tool(description="Create a payment entry template that requires admin approval")
async def create_payment_entry_template(
    account_id: str,
    amount: float,
    counterparty_id: Optional[str] = None,
    counterparty_name: Optional[str] = None,
    memo: Optional[str] = None,
    external_id: Optional[str] = None
) -> PaymentEntryResult:
    payload: dict[str, Any] = {
        "account_id": account_id,
        "amount": amount,
        "requires_approval": True
    }

    if counterparty_id:
        payload["counterparty_id"] = counterparty_id
    elif counterparty_name:
        payload["counterparty_name"] = counterparty_name

    if memo:
        payload["memo"] = memo
    if external_id:
        payload["external_id"] = external_id

    data = await api_request(
        HttpMethod.POST,
        "/transactions",
        json_body=payload,
    )

    entry = PaymentEntryTemplate(**data)

    return PaymentEntryResult(
        success=True,
        entry=entry,
        message="Payment entry template created successfully and is pending admin approval"
    )


@tool(description="Get all counterparties associated with the account")
async def get_counterparties() -> dict:
    data = await api_request(HttpMethod.GET, "/counterparties")
    return data


tools = [
    get_accounts,
    get_account,
    get_transactions,
    create_payment_entry_template,
    get_counterparties,
]

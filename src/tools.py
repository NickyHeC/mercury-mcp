"""Mercury API tools.

Tools make authenticated requests to the Mercury API using ctx.dispatch().
DAuth applies the credential inside the enclave — tool code never handles
raw secrets.
"""

from typing import Any
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
    """Dispatch an authenticated request to the Mercury API through DAuth."""
    ctx = get_context()
    if params:
        filtered = {k: str(v) for k, v in params.items() if v is not None}
        if filtered:
            path = f"{path}?{urlencode(filtered)}"
    if json_body is not None:
        req = HttpRequest(method=method, path=path, body=json_body)
    else:
        req = HttpRequest(method=method, path=path)
    resp = await ctx.dispatch(mercury_connection, req)
    if resp.success and resp.response is not None:
        body = resp.response.body
        if isinstance(body, dict):
            return {"success": True, "data": body}
        return {"success": True, "data": body}
    error = resp.error.message if resp.error else "Request failed"
    return {"success": False, "error": error}


# --- Result Model (flat dict to avoid $ref schema issues) ---


class MercuryResult(BaseModel):
    success: bool
    data: dict[str, Any] | list[dict[str, Any]] = {}
    error: str | None = None


# --- Tools ---


@tool(description="Get all accounts associated with the Mercury account")
async def get_accounts() -> MercuryResult:
    result = await api_request(HttpMethod.GET, "/accounts")
    return MercuryResult(**result)


@tool(description="Get a specific account by ID")
async def get_account(account_id: str) -> MercuryResult:
    result = await api_request(HttpMethod.GET, f"/account/{account_id}")
    return MercuryResult(**result)


@tool(description="Get transactions for a specific account")
async def get_transactions(
    account_id: str,
    limit: int | None = None,
    offset: int | None = None,
) -> MercuryResult:
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    result = await api_request(
        HttpMethod.GET,
        f"/account/{account_id}/transactions",
        params=params if params else None,
    )
    return MercuryResult(**result)


@tool(description="Create a payment entry template that requires admin approval")
async def create_payment_entry_template(
    account_id: str,
    amount: float,
    counterparty_id: str | None = None,
    counterparty_name: str | None = None,
    memo: str | None = None,
    external_id: str | None = None,
) -> MercuryResult:
    payload: dict[str, Any] = {
        "account_id": account_id,
        "amount": amount,
        "requires_approval": True,
    }
    if counterparty_id:
        payload["counterparty_id"] = counterparty_id
    elif counterparty_name:
        payload["counterparty_name"] = counterparty_name
    if memo:
        payload["memo"] = memo
    if external_id:
        payload["external_id"] = external_id

    result = await api_request(HttpMethod.POST, "/transactions", json_body=payload)
    return MercuryResult(**result)


@tool(description="Get all counterparties associated with the account")
async def get_counterparties() -> MercuryResult:
    result = await api_request(HttpMethod.GET, "/counterparties")
    return MercuryResult(**result)


tools = [
    get_accounts,
    get_account,
    get_transactions,
    create_payment_entry_template,
    get_counterparties,
]

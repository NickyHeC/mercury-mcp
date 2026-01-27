import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from dedalus_mcp import tool
from pydantic import BaseModel


# --- Configuration ---

# Load environment variables from .env file (if it exists)
# In deployment, environment variables should be set directly
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Try to load from current directory as fallback
    load_dotenv()

MERCURY_API_BASE_URL = "https://api.mercury.com/api/v1"


def get_api_token() -> str:
    """Get Mercury API token from environment variable."""
    token = os.getenv("MERCURY_API_TOKEN", "")
    if not token:
        raise ValueError(
            "MERCURY_API_TOKEN environment variable is not set. "
            "Please set it in your deployment environment variables."
        )
    return token


def make_mercury_request(method: str, endpoint: str, **kwargs) -> dict:
    """Make an authenticated request to the Mercury API."""
    token = get_api_token()
    url = f"{MERCURY_API_BASE_URL}/{endpoint}"
    
    response = requests.request(
        method=method,
        url=url,
        auth=(token, ""),
        **kwargs
    )
    response.raise_for_status()
    return response.json()


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
def get_accounts() -> AccountsResult:
    """
    Retrieve all accounts associated with the Mercury account.
    
    Returns:
        AccountsResult containing a list of all accounts and their details
    """
    data = make_mercury_request("GET", "accounts")
    
    accounts = [
        Account(**account) for account in data.get("accounts", [])
    ]
    
    return AccountsResult(
        accounts=accounts,
        count=len(accounts)
    )


@tool(description="Get a specific account by ID")
def get_account(account_id: str) -> Account:
    """
    Retrieve details for a specific account.
    
    Args:
        account_id: The unique identifier of the account
    
    Returns:
        Account with detailed information
    """
    data = make_mercury_request("GET", f"accounts/{account_id}")
    return Account(**data)


@tool(description="Get transactions for a specific account")
def get_transactions(
    account_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> TransactionsResult:
    """
    Retrieve transactions for a specific account.
    
    Args:
        account_id: The unique identifier of the account
        limit: Maximum number of transactions to return (optional)
        offset: Number of transactions to skip (optional)
    
    Returns:
        TransactionsResult containing a list of transactions
    """
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    
    data = make_mercury_request(
        "GET",
        f"accounts/{account_id}/transactions",
        params=params
    )
    
    transactions = [
        Transaction(**tx) for tx in data.get("transactions", [])
    ]
    
    return TransactionsResult(
        transactions=transactions,
        count=len(transactions)
    )


@tool(description="Create a payment entry template that requires admin approval")
def create_payment_entry_template(
    account_id: str,
    amount: float,
    counterparty_id: Optional[str] = None,
    counterparty_name: Optional[str] = None,
    memo: Optional[str] = None,
    external_id: Optional[str] = None
) -> PaymentEntryResult:
    """
    Create a payment entry template that requires admin approval.
    
    Args:
        account_id: The unique identifier of the account to debit
        amount: The payment amount (positive number)
        counterparty_id: The unique identifier of the counterparty (optional)
        counterparty_name: The name of the counterparty if counterparty_id is not provided (optional)
        memo: A memo or note for the payment (optional)
        external_id: An external identifier for tracking (optional)
    
    Returns:
        PaymentEntryResult indicating success and the created entry template
    """
    payload = {
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
    
    data = make_mercury_request(
        "POST",
        "transactions",
        json=payload
    )
    
    entry = PaymentEntryTemplate(**data)
    
    return PaymentEntryResult(
        success=True,
        entry=entry,
        message="Payment entry template created successfully and is pending admin approval"
    )


@tool(description="Get all counterparties associated with the account")
def get_counterparties() -> dict:
    """
    Retrieve all counterparties associated with the Mercury account.
    
    Returns:
        Dictionary containing list of counterparties
    """
    data = make_mercury_request("GET", "counterparties")
    return data


tools = [
    get_accounts,
    get_account,
    get_transactions,
    create_payment_entry_template,
    get_counterparties,
]

# mercury-mcp

A Model Context Protocol (MCP) server for interacting with Mercury banking API, built with the Dedalus Labs framework. This server provides tools to read account data and initiate payments that require admin approval.

## Features

This MCP server provides the following capabilities:

- **Read Account Data**: Retrieve account information, balances, and transaction history
- **Payment Management**: Create payment entry templates that require admin approval
- **Counterparty Management**: Access counterparty information for payments

## Available Tools

- `get_accounts()` - Retrieve all accounts associated with the Mercury account
- `get_account(account_id)` - Get detailed information for a specific account
- `get_transactions(account_id, limit, offset)` - Retrieve transactions for an account
- `create_payment_entry_template(...)` - Create payment entries that require admin approval
- `get_counterparties()` - Get all counterparties associated with the account

## Prerequisites

- Python 3.8+
- A Mercury API token with appropriate permissions

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mercury-mcp
```

2. Install dependencies:
```bash
pip install -e .
```

3. Create a `.env` file in the project root:
```bash
MERCURY_API_TOKEN=your-token-here
```

## Configuration

### API Token

This server uses a custom Mercury API token with the following permissions:
- Read all available data on Mercury account
- Initiate payments (create entry templates) that require and wait for admin approvals

**Token Usage Notes:**
- Tokens that are not used within any 45 day period are automatically deleted
- Tokens that have higher permissions than they utilize in a 45-day window are automatically adjusted to the appropriate permission level
- To further secure your token, Mercury requires you to whitelist IP addresses or ranges from which you expect to use Read and Write tokens

### Environment Variables

Set one of the following (tools use `MERCURY_TOKEN` when set, e.g. by Dedalus DAuth, and fall back to `MERCURY_API_TOKEN` for local dev):

- `MERCURY_TOKEN` - Used by the DAuth connection and by tools when deployed (e.g. Dedalus Labs).
- `MERCURY_API_TOKEN` - Your Mercury API token for local use (format: `secret-token:mercury_production_...`). Also works in `.env`.

## Usage

### Running the Server

Start the MCP server:

```bash
python -m src.main
```

The server will start on port 8080 by default.

### Using the Tools

The server exposes tools that can be called via the MCP protocol. Each tool is documented with its parameters and return types using Pydantic models for type safety.

Example API usage (for reference):
```python
import requests

token = 'secret-token:mercury_production_...'
req = requests.get('https://api.mercury.com/api/v1/accounts', auth=(token, ''))
```

## Project Structure

```
mercury-mcp/
├── src/
│   ├── main.py             # Entry point and server configuration
│   └── tools.py            # Tool definitions and implementations
├── pyproject.toml          # Project metadata and dependencies
├── PROJECT.md              # Platform research notes (not in git)
└── README.md               # Project documentation
```

## Alternative: Mercury Hosted MCP Server

Mercury offers a hosted MCP server that requires OAuth login, which is still in Beta as of January 2026. For more information, see: https://docs.mercury.com/docs/connecting-mercury-mcp

## Development

This project uses:
- [Dedalus Labs MCP Framework](https://docs.dedaluslabs.ai/) for the MCP server implementation
- [Pydantic](https://docs.pydantic.dev/) for data validation and type safety
- [Requests](https://requests.readthedocs.io/) for HTTP API calls

## License

See LICENSE file for details.

## Status

[In Development]

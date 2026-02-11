import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from dedalus_mcp import MCPServer
from dedalus_mcp.auth import Connection, SecretKeys

# Load environment variables from .env file
load_dotenv()

# DAuth: tools read MERCURY_TOKEN (same key) and use Basic auth for Mercury API.
mercury_connection = Connection(
    name="mercury",
    secrets=SecretKeys(token="MERCURY_TOKEN"),
    base_url="https://api.mercury.com/api/v1",
    auth_header_format="Bearer {token}",
)

# Import tools with error handling
# Lambda doesn't support relative imports, so we need to use absolute imports
try:
    # Try absolute import first (for Lambda)
    from src.tools import tools
except ImportError:
    # Fallback to relative import (for local development)
    try:
        from .tools import tools
    except ImportError as e:
        print(f"Error importing tools: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        tools = []
except Exception as e:
    print(f"Error importing tools: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    tools = []


# --- Server ---

server = MCPServer(
    name="mercury-mcp", 
    connections=[mercury_connection],
    authorization_server=os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai"),
    streamable_http_stateless=True,
    )

# Register all tools at module level so they're available for validation
for tool_func in tools:
    server.collect(tool_func)


# Lambda handler function for AWS Lambda deployment (Dedalus Labs)
def handler(event, context):
    """Lambda handler for Dedalus Labs deployment."""
    try:
        return server.handle(event, context)
    except Exception as e:
        print(f"Handler error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


# For local development or deployment validation (HTTP at /mcp)
def main() -> None:
    """Main entry point for the MCP server (local or container)."""
    import asyncio
    try:
        port = int(os.getenv("PORT", "8080"))
        # Bind to 0.0.0.0 so deployment/validation can reach /mcp (default 127.0.0.1 is local-only)
        host = os.getenv("HOST", "0.0.0.0")
        asyncio.run(server.serve(host=host, port=port))
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

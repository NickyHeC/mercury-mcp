import os
import sys

from dotenv import load_dotenv
from dedalus_mcp import MCPServer
from dedalus_mcp.auth import Connection, SecretKeys

load_dotenv()

mercury_connection = Connection(
    name="mercury-mcp",
    secrets=SecretKeys(token="MERCURY_TOKEN"),
    base_url="https://api.mercury.com/api/v1",
    auth_header_format="Bearer {api_key}",
)

try:
    from src.tools import tools
except ImportError:
    try:
        from .tools import tools
    except ImportError as e:
        print(f"Error importing tools: {e}", file=sys.stderr)
        tools = []


# --- Server ---

server = MCPServer(
    name="mercury-mcp",
    connections=[mercury_connection],
    authorization_server=os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai"),
    streamable_http_stateless=True,
)

for tool_func in tools:
    server.collect(tool_func)


def handler(event, context):
    """Lambda handler for Dedalus Labs deployment."""
    try:
        return server.handle(event, context)
    except Exception as e:
        print(f"Handler error: {e}", file=sys.stderr)
        raise


def main() -> None:
    """Start the MCP server for local development or container deployment."""
    import asyncio
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    asyncio.run(server.serve(host=host, port=port, stateless=True))


if __name__ == "__main__":
    main()

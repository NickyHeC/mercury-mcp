import os
import sys

from dedalus_mcp import MCPServer

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

server = MCPServer(name="mercury-mcp")

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


# For local development or non-Lambda environments
def main() -> None:
    """Main entry point for the MCP server (local development)."""
    import asyncio
    try:
        # Use port from environment variable or default to 8080
        port = int(os.getenv("PORT", "8080"))
        
        # Start the server (async server.run() wrapped in asyncio.run)
        asyncio.run(server.serve(port=port))
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

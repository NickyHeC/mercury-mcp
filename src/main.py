import os
import sys

from dedalus_mcp import MCPServer

# Import tools - fail fast if import fails to ensure tool discovery works
try:
    from .tools import tools
    if not tools:
        raise RuntimeError("tools list is empty - no tools available for discovery")
except Exception as e:
    print(f"CRITICAL: Error importing tools: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    # Don't silently fail - raise the error so deployment fails clearly
    raise RuntimeError(f"Failed to import tools: {e}") from e


# --- Server ---

server = MCPServer(name="mercury-mcp")

# Register all tools at module level so they're available for validation
for tool_func in tools:
    server.collect(tool_func)


# Lambda handler function for AWS Lambda deployment (Dedalus Labs)
def handler(event, context):
    """Lambda handler for Dedalus Labs deployment."""
    # Try calling server directly (MCPServer should be callable)
    try:
        return server(event, context)
    except (TypeError, AttributeError) as e:
        # Server might not be directly callable, try handle method
        try:
            if hasattr(server, 'handle'):
                return server.handle(event, context)
        except Exception:
            pass
        # If all else fails, return server object for Dedalus Labs introspection
        # This allows tool discovery to work even if handler methods fail
        return server
    except Exception as e:
        # Catch any other errors and return server object instead of crashing
        print(f"Handler error (non-fatal): {e}", file=sys.stderr)
        return server


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


# Expose server object at module level for Dedalus Labs introspection
# This allows Dedalus Labs to discover tools directly from the server object
__all__ = ['server', 'handler', 'tools']

if __name__ == "__main__":
    main()

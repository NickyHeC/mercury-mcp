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
    # Ensure tools are registered before handling
    if not tools:
        raise RuntimeError("No tools available - tool discovery will fail")
    
    try:
        # Use server.handle() if available, otherwise try calling server directly
        if hasattr(server, 'handle'):
            result = server.handle(event, context)
            return result
        elif callable(server):
            return server(event, context)
        else:
            # If neither works, return the server object itself
            # Dedalus Labs should be able to discover tools from the server object
            return server
    except AttributeError:
        # If handle doesn't exist, return server object for discovery
        return server
    except Exception as e:
        print(f"Handler error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Still return server for tool discovery even on error
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


if __name__ == "__main__":
    main()

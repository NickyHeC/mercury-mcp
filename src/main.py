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

# Verify tools are registered
if not hasattr(server, '_tools') or len(getattr(server, '_tools', [])) == 0:
    print(f"WARNING: No tools registered on server. Tools list: {tools}", file=sys.stderr)
else:
    print(f"INFO: Registered {len(tools)} tools on server", file=sys.stderr)


# Lambda handler function for AWS Lambda deployment (Dedalus Labs)
# Dedalus Labs expects the handler to process Lambda events and return responses
def handler(event, context):
    """Lambda handler for Dedalus Labs deployment."""
    # Ensure tools are registered
    if not tools:
        raise RuntimeError("No tools available - tool discovery will fail")
    
    # For tool discovery requests, Dedalus Labs might call the handler with a specific event
    # Check if this is a discovery request
    if isinstance(event, dict):
        # If it's a discovery request, return tool information
        if event.get("method") == "tools/list" or "tools" in str(event).lower():
            # Return tools list for discovery
            return {
                "tools": [tool.__name__ for tool in tools],
                "server": server
            }
    
    # For regular requests, use server.handle() if available
    try:
        if hasattr(server, 'handle'):
            return server.handle(event, context)
        elif hasattr(server, '__call__'):
            return server(event, context)
        else:
            # Fallback: return server object for Dedalus Labs to introspect
            return server
    except Exception as e:
        print(f"Handler error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Return server object for tool discovery even on error
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

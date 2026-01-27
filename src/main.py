import asyncio
import os

from dedalus_mcp import MCPServer

from .tools import tools


# --- Server ---

server = MCPServer(name="mercury-mcp")


async def main() -> None:
    for tool_func in tools:
        server.collect(tool_func)
    # Use port from environment variable or default to 8080
    port = int(os.getenv("PORT", "8080"))
    await server.serve(port=port)


if __name__ == "__main__":
    asyncio.run(main())

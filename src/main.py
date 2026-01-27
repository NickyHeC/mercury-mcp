import asyncio
from pathlib import Path

from dotenv import load_dotenv
from dedalus_mcp import MCPServer

from .tools import tools

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# --- Server ---

server = MCPServer(name="mercury-mcp")


async def main() -> None:
    for tool_func in tools:
        server.collect(tool_func)
    await server.serve(port=8080)


if __name__ == "__main__":
    asyncio.run(main())

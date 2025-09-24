import asyncio, os, sys
from pathlib import Path
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings


async def main():
    # Assumes server.py is in the same folder as this file
    server_path = (Path(__file__).parent / "server.py").resolve()

    async with MCPServerStdio(
        name="hello-mcp",
        params={
            "command": sys.executable,  # use the SAME interpreter/venv
            "args": [str(server_path)],
        },
        cache_tools_list=True,
    ) as server:
        agent = Agent(
            name="Local MCP Demo",
            instructions="Use the MCP tools to help the user.",
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="auto"),
        )
        result = await Runner.run(agent, "Call echo('katsu curry'), then add(7, 22), then tellJoke('curry').")
        print("\n=== FINAL OUTPUT ===\n", result.final_output)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your environment or .env")
    asyncio.run(main())


import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import Client, ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GitHubMCPClient:
    """
    MCP client supporting both stdio and Streamable HTTP.
    """

    def __init__(self):
        self.session: Any | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """
        Connect over HTTP if MCP_SERVER_URL is set.
        Otherwise, start the local server using stdio.
        """

        server_url = os.getenv("MCP_SERVER_URL")

        if server_url:
            # Connect to an already-running HTTP server.
            self.session = await self.exit_stack.enter_async_context(
                Client(server_url)
            )

            print(f"Connected to GitHub MCP server over HTTP: {server_url}")

        else:
            # Preserve the existing stdio workflow.
            server_params = StdioServerParameters(
                command="python",
                args=["-m", "app.server"],
            )

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            read_stream, write_stream = stdio_transport

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await self.session.initialize()

            print("Connected to GitHub MCP server over stdio.")

    async def list_tools(self) -> list[dict[str, Any]]:
        """Retrieve the tools exposed by the MCP server."""

        if self.session is None:
            raise RuntimeError("MCP client is not connected.")

        response = await self.session.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.input_schema,
            }
            for tool in response.tools
        ]

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Invoke a tool exposed by the MCP server."""

        if self.session is None:
            raise RuntimeError("MCP client is not connected.")

        return await self.session.call_tool(tool_name, arguments)

    async def close(self):
        """Close the MCP connection and its managed resources."""

        await self.exit_stack.aclose()

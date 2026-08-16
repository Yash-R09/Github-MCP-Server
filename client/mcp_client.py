from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GitHubMCPClient:
    """
    MCP client responsible for connecting to the GitHub MCP server,
    discovering its tools, and invoking them.
    """

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """
        Start the GitHub MCP server as a subprocess and establish
        an MCP client session.
        """

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

        print("Connected to GitHub MCP server.")

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        Retrieve the tools exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("MCP client is not connected.")

        response = await self.session.list_tools()

        tools = []

        for tool in response.tools:
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.input_schema,
                }
            )

        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Invoke a tool exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("MCP client is not connected.")

        result = await self.session.call_tool(
            tool_name,
            arguments,
        )

        return result

    async def close(self):
        """
        Close the MCP connection and subprocess.
        """

        await self.exit_stack.aclose()
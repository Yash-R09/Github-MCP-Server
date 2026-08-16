import asyncio

from client.mcp_client import GitHubMCPClient


async def main():

    client = GitHubMCPClient()

    try:
        await client.connect()

        tools = await client.list_tools()

        print("\nAvailable MCP tools:")
        print("=" * 60)

        for tool in tools:
            print(f"\n{tool['name']}")
            print(f"Description: {tool['description']}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
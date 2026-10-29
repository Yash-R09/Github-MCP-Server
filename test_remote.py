import asyncio
from client.mcp_client import GitHubMCPClient

async def main():
    client = GitHubMCPClient()
    try:
        await client.connect()
        result = await client.call_tool(
            "get_repository",
            {"owner": "microsoft", "repo": "vscode"}
        )
        print("Tool call successful:", not result.is_error)
        print(result)
    finally:
        await client.close()

asyncio.run(main())

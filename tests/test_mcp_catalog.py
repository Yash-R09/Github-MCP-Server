import asyncio

from client.mcp_client import GitHubMCPClient
from evaluation.evaluator import get_available_tools
from evaluation.test_cases import TEST_CASES


def test_local_mcp_catalog(monkeypatch):
    # Token is a placeholder: listing tools performs no GitHub API requests.
    monkeypatch.setenv('GITHUB_TOKEN', 'catalog-only-placeholder')
    monkeypatch.setenv('GITHUB_MCP_READ_ONLY', 'false')
    monkeypatch.setenv('MCP_TRANSPORT', 'stdio')
    monkeypatch.delenv('MCP_SERVER_URL', raising=False)
    async def check():
        client = GitHubMCPClient()
        try:
            await asyncio.wait_for(client.connect(), 30)
            tools = await get_available_tools(client)
            names = {t['function']['name'] for t in tools}
            assert len(names) == 21
            assert {c['expected_tool'] for c in TEST_CASES} <= names
        finally:
            await client.close()
    asyncio.run(check())

import asyncio

import pytest

from client.mcp_client import GitHubMCPClient
from evaluation.evaluator import get_available_tools
from evaluation.test_cases import TEST_CASES


@pytest.mark.parametrize('read_only,expected_count', [('false', 21), ('true', 16)])
def test_local_mcp_catalog(monkeypatch, read_only, expected_count):
    # Token is a placeholder: listing tools performs no GitHub API requests.
    monkeypatch.setenv('GITHUB_TOKEN', 'catalog-only-placeholder')
    monkeypatch.setenv('GITHUB_MCP_READ_ONLY', read_only)
    monkeypatch.setenv('PYTHON_DOTENV_DISABLED', '1')
    monkeypatch.setenv('MCP_TRANSPORT', 'stdio')
    monkeypatch.delenv('MCP_SERVER_URL', raising=False)
    async def check():
        client = GitHubMCPClient()
        try:
            await asyncio.wait_for(client.connect(), 30)
            tools = await get_available_tools(client)
            names = {t['function']['name'] for t in tools}
            assert len(names) == expected_count
            writes = {'create_issue', 'create_pull_request', 'create_branch',
                      'create_or_update_file', 'add_labels_to_issue'}
            if read_only == 'true':
                assert not names & writes
            else:
                assert {c['expected_tool'] for c in TEST_CASES} <= names
        finally:
            await client.close()
    asyncio.run(check())

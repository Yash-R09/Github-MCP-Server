
import httpx
from unittest.mock import Mock, patch

from app.github_client import GitHubClient


def make_response(status_code: int, body: str = "{}"):
    return httpx.Response(
        status_code=status_code,
        content=body.encode(),
        headers={"Content-Type": "application/json"},
        request=httpx.Request("GET", "https://api.github.com/user"),
    )


def test_get_retries_after_server_error():
    client = GitHubClient.__new__(GitHubClient)
    client.client = Mock()

    client.client.request.side_effect = [
        make_response(503),
        make_response(200, '{"login": "test-user"}'),
    ]

    with patch("app.github_client.time.sleep"):
        result = client._request("GET", "/user")

    assert result == {"login": "test-user"}
    assert client.client.request.call_count == 2


def test_post_does_not_retry_server_error():
    client = GitHubClient.__new__(GitHubClient)
    client.client = Mock()
    client.client.request.return_value = make_response(503)

    with patch("app.github_client.time.sleep"):
        try:
            client._request("POST", "/repos/test/repo/issues")
        except RuntimeError as exc:
            assert "GitHub server error (503)" in str(exc)
        else:
            raise AssertionError("Expected a RuntimeError")

    assert client.client.request.call_count == 1

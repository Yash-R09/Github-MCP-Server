from mcp.server import MCPServer

try:
    from app.github_client import GitHubClient
except ModuleNotFoundError:
    from github_client import GitHubClient

# ============================================================
# MCP Server
# ============================================================

mcp = MCPServer("GitHub MCP Server")

github = GitHubClient()


# ============================================================
# Repository Tools
# ============================================================

@mcp.tool()
def get_repository(
    owner: str,
    repo: str,
) -> dict:
    """
    Get structured information about a GitHub repository.

    Use when the user asks about repository metadata,
    such as description, stars, forks, language, or
    default branch.
    """

    return github.get_repository(owner, repo)


@mcp.tool()
def search_repositories(
    query: str,
    language: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Search GitHub repositories.

    Optionally filter results by programming language.
    """

    return github.search_repositories(
        query,
        language,
        limit,
    )


# ============================================================
# File Tools
# ============================================================

@mcp.tool()
def get_file_contents(
    owner: str,
    repo: str,
    path: str,
) -> dict:
    """
    Read and decode a file from a GitHub repository.

    Use for reading source code, README files,
    configuration files, or documentation.
    """

    return github.get_file_contents(
        owner,
        repo,
        path,
    )


@mcp.tool()
def list_directory(
    owner: str,
    repo: str,
    path: str = "",
) -> list[dict]:
    """
    List files and directories at a repository path.

    Leave path empty to list the repository root.
    """

    return github.list_directory(
        owner,
        repo,
        path,
    )


@mcp.tool()
def create_or_update_file(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str = "main",
    sha: str = "",
) -> dict:
    """
    Create a new file or update an existing file.

    Use sha only when updating an existing file.
    Leave sha empty when creating a new file.
    """

    return github.create_or_update_file(
        owner,
        repo,
        path,
        content,
        message,
        branch or None,
        sha or None,
    )


# ============================================================
# Issue Tools
# ============================================================

@mcp.tool()
def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> list[dict]:
    """
    List GitHub issues.

    State can be open, closed, or all.
    """

    return github.list_issues(
        owner,
        repo,
        state,
        limit,
    )


@mcp.tool()
def get_issue(
    owner: str,
    repo: str,
    issue_number: int,
) -> dict:
    """
    Get detailed information about a GitHub issue.
    """

    return github.get_issue(
        owner,
        repo,
        issue_number,
    )


@mcp.tool()
def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
) -> dict:
    """
    Create a new GitHub issue.

    Labels are optional.
    """

    return github.create_issue(
        owner,
        repo,
        title,
        body,
        labels,
    )


# ============================================================
# Pull Request Tools
# ============================================================

@mcp.tool()
def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> list[dict]:
    """
    List pull requests in a GitHub repository.
    """

    return github.list_pull_requests(
        owner,
        repo,
        state,
        limit,
    )


@mcp.tool()
def get_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
) -> dict:
    """
    Get detailed information about a GitHub pull request.
    """

    return github.get_pull_request(
        owner,
        repo,
        pull_number,
    )


@mcp.tool()
def create_pull_request(
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str = "",
    draft: bool = False,
) -> dict:
    """
    Create a GitHub pull request.

    head is the source branch.
    base is the target branch.
    """

    return github.create_pull_request(
        owner,
        repo,
        title,
        head,
        base,
        body,
        draft,
    )


# ============================================================
# Branch Tools
# ============================================================

@mcp.tool()
def list_branches(
    owner: str,
    repo: str,
    limit: int = 10,
) -> list[dict]:
    """
    List branches in a GitHub repository.
    """

    return github.list_branches(
        owner,
        repo,
        limit,
    )


@mcp.tool()
def get_branch(
    owner: str,
    repo: str,
    branch: str,
) -> dict:
    """
    Get information about a specific GitHub branch.
    """

    return github.get_branch(
        owner,
        repo,
        branch,
    )


@mcp.tool()
def create_branch(
    owner: str,
    repo: str,
    branch: str,
    from_branch: str = "main",
) -> dict:
    """
    Create a new branch from an existing branch.
    """

    return github.create_branch(
        owner,
        repo,
        branch,
        from_branch,
    )


# ============================================================
# Commit Tools
# ============================================================

@mcp.tool()
def list_commits(
    owner: str,
    repo: str,
    branch: str = "main",
    limit: int = 10,
) -> list[dict]:
    """
    List commits from a GitHub branch.

    Branch defaults to main.
    """

    return github.list_commits(
        owner,
        repo,
        branch,
        limit,
    )


@mcp.tool()
def get_commit(
    owner: str,
    repo: str,
    sha: str,
) -> dict:
    """
    Get details about a specific Git commit.
    """

    return github.get_commit(
        owner,
        repo,
        sha,
    )


# ============================================================
# Search Tools
# ============================================================

@mcp.tool()
def search_code(
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Search GitHub source code.

    The query can include GitHub search qualifiers such as
    repo:owner/name or language:python.
    """

    return github.search_code(
        query,
        limit,
    )


@mcp.tool()
def search_issues(
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Search GitHub issues using GitHub search syntax.
    """

    return github.search_issues(
        query,
        limit,
    )


@mcp.tool()
def search_pull_requests(
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Search GitHub pull requests using GitHub search syntax.
    """

    return github.search_pull_requests(
        query,
        limit,
    )


# ============================================================
# Label Tools
# ============================================================

@mcp.tool()
def list_labels(
    owner: str,
    repo: str,
    limit: int = 30,
) -> list[dict]:
    """
    List labels available in a GitHub repository.
    """

    return github.list_labels(
        owner,
        repo,
        limit,
    )


@mcp.tool()
def add_labels_to_issue(
    owner: str,
    repo: str,
    issue_number: int,
    labels: list[str],
) -> dict:
    """
    Add one or more existing GitHub labels to an issue.
    """

    return github.add_labels_to_issue(
        owner,
        repo,
        issue_number,
        labels,
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    mcp.run()
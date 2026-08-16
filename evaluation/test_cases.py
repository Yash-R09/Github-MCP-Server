TEST_CASES = [

    # ========================================================
    # Repository
    # ========================================================

    {
        "id": 1,
        "question": "Show me details about the microsoft/vscode repository.",
        "expected_tool": "get_repository",
    },
    {
        "id": 2,
        "question": "What is the default branch of microsoft/vscode?",
        "expected_tool": "get_repository",
    },
    {
        "id": 3,
        "question": "How many stars does microsoft/vscode have?",
        "expected_tool": "get_repository",
    },
    {
        "id": 4,
        "question": "Find repositories related to MCP written in Python.",
        "expected_tool": "search_repositories",
    },
    {
        "id": 5,
        "question": "Search GitHub for Python repositories about AI agents.",
        "expected_tool": "search_repositories",
    },

    # ========================================================
    # Files
    # ========================================================

    {
        "id": 6,
        "question": "Read README.md from microsoft/vscode.",
        "expected_tool": "get_file_contents",
    },
    {
        "id": 7,
        "question": "Show me the contents of package.json in microsoft/vscode.",
        "expected_tool": "get_file_contents",
    },
    {
        "id": 8,
        "question": "Read app.py from my repository.",
        "expected_tool": "get_file_contents",
    },
    {
        "id": 9,
        "question": "List the files in the root of microsoft/vscode.",
        "expected_tool": "list_directory",
    },
    {
        "id": 10,
        "question": "Show me the contents of the src directory.",
        "expected_tool": "list_directory",
    },

    # ========================================================
    # Issues
    # ========================================================

    {
        "id": 11,
        "question": "Show me the open issues in microsoft/vscode.",
        "expected_tool": "list_issues",
    },
    {
        "id": 12,
        "question": "List closed issues in my repository.",
        "expected_tool": "list_issues",
    },
    {
        "id": 13,
        "question": "Show me issue number 100.",
        "expected_tool": "get_issue",
    },
    {
        "id": 14,
        "question": "Get the details of issue #25.",
        "expected_tool": "get_issue",
    },
    {
        "id": 15,
        "question": "Create an issue titled Login is broken.",
        "expected_tool": "create_issue",
    },
    {
        "id": 16,
        "question": "Open a GitHub issue describing the authentication bug.",
        "expected_tool": "create_issue",
    },
    {
        "id": 17,
        "question": "Create an issue requesting dark mode.",
        "expected_tool": "create_issue",
    },
    {
        "id": 18,
        "question": "Show all issues, including closed ones.",
        "expected_tool": "list_issues",

    },

    # ========================================================
    # Pull Requests
    # ========================================================

    {
        "id": 19,
        "question": "List open pull requests in microsoft/vscode.",
        "expected_tool": "list_pull_requests",
    },
    {
        "id": 20,
        "question": "Show closed pull requests.",
        "expected_tool": "list_pull_requests",
    },
    {
        "id": 21,
        "question": "Get pull request number 500.",
        "expected_tool": "get_pull_request",
    },
    {
        "id": 22,
        "question": "Show me the details of PR #42.",
        "expected_tool": "get_pull_request",
    },
    {
        "id": 23,
        "question": "Create a pull request from feature-login into main.",
        "expected_tool": "create_pull_request",
    },
    {
        "id": 24,
        "question": "Open a PR merging my feature branch into develop.",
        "expected_tool": "create_pull_request",
    },
    {
        "id": 25,
        "question": "Create a draft pull request for my feature branch.",
        "expected_tool": "create_pull_request",
    },

    # ========================================================
    # Branches
    # ========================================================

    {
        "id": 26,
        "question": "List the branches in my repository.",
        "expected_tool": "list_branches",
    },
    {
        "id": 27,
        "question": "Show me all branches in microsoft/vscode.",
        "expected_tool": "list_branches",
    },
    {
        "id": 28,
        "question": "Get information about the main branch.",
        "expected_tool": "get_branch",
    },
    {
        "id": 29,
        "question": "What commit does the develop branch point to?",
        "expected_tool": "get_branch",
    },
    {
        "id": 30,
        "question": "Create a branch called feature-auth from main.",
        "expected_tool": "create_branch",
    },

    # ========================================================
    # Commits
    # ========================================================

    {
        "id": 31,
        "question": "Show the latest commits on main.",
        "expected_tool": "list_commits",
    },
    {
        "id": 32,
        "question": "List commits from the develop branch.",
        "expected_tool": "list_commits",
    },
    {
        "id": 33,
        "question": "Show details for commit abc123.",
        "expected_tool": "get_commit",
    },
    {
        "id": 34,
        "question": "What files were changed by commit abc123?",
        "expected_tool": "get_commit",
    },
    {
        "id": 35,
        "question": "Show the recent commits on the main branch.",
        "expected_tool": "list_commits",
    },

    # ========================================================
    # Search
    # ========================================================

    {
        "id": 36,
        "question": "Search GitHub code for FastMCP.",
        "expected_tool": "search_code",
    },
    {
        "id": 37,
        "question": "Find Python files containing MCPServer.",
        "expected_tool": "search_code",
    },
    {
        "id": 38,
        "question": "Search GitHub for issues mentioning authentication.",
        "expected_tool": "search_issues",
    },
    {
        "id": 39,
        "question": "Find open issues related to login.",
        "expected_tool": "search_issues",
    },
    {
        "id": 40,
        "question": "Search for pull requests about MCP.",
        "expected_tool": "search_pull_requests",
    },
    {
        "id": 41,
        "question": "Find PRs mentioning authentication.",
        "expected_tool": "search_pull_requests",
    },

    # ========================================================
    # Labels
    # ========================================================

    {
        "id": 42,
        "question": "List the labels in my repository.",
        "expected_tool": "list_labels",
    },
    {
        "id": 43,
        "question": "What labels are available?",
        "expected_tool": "list_labels",
    },
    {
        "id": 44,
        "question": "Add the bug label to issue #10.",
        "expected_tool": "add_labels_to_issue",
    },
    {
        "id": 45,
        "question": "Label issue #5 as enhancement.",
        "expected_tool": "add_labels_to_issue",
    },

    # ========================================================
    # Write / File Operations
    # ========================================================

    {
        "id": 46,
        "question": "Create a new file called test.txt containing Hello World.",
        "expected_tool": "create_or_update_file",
    },
    {
        "id": 47,
        "question": "Update the README file with new documentation.",
        "expected_tool": "create_or_update_file",
    },
    {
        "id": 48,
        "question": "Commit a new config.json file to my feature branch.",
        "expected_tool": "create_or_update_file",
    },

    # ========================================================
    # Ambiguous-but-distinguishable
    # ========================================================

    {
        "id": 49,
        "question": "I need to start a new feature branch from main.",
        "expected_tool": "create_branch",
    },
    {
        "id": 50,
        "question": "I want to merge my feature branch into main through GitHub.",
        "expected_tool": "create_pull_request",
    },
]
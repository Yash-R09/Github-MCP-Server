# GitHub MCP Server

An AI-powered GitHub integration built from scratch using the Model Context Protocol (MCP).

This project exposes GitHub operations as structured MCP tools that an AI assistant can discover and invoke based on natural-language requests. It integrates the GitHub REST API with an MCP server and a Groq-powered AI assistant, while requiring explicit confirmation before executing write operations.

---

## Overview

Large language models can reason about information available to them, but they cannot directly access private systems such as authenticated GitHub accounts.

This project demonstrates how MCP can act as a secure interface between an AI assistant and GitHub.

For example, instead of manually interacting with GitHub, a user can ask:

> "What is the default branch of microsoft/vscode?"

or:

> "Show me the open issues in microsoft/vscode."

The AI assistant determines which MCP tool is appropriate, invokes the tool through the MCP protocol, and the server communicates with GitHub's REST API.

For write operations, the assistant asks for explicit user confirmation before modifying GitHub data.

---

## Architecture

```text
                         User
                           |
                           v
                 +-------------------+
                 |   AI Assistant    |
                 |    Groq LLM       |
                 +---------+---------+
                           |
                           | MCP
                           v
                 +-------------------+
                 |  GitHub MCP       |
                 |     Server        |
                 +---------+---------+
                           |
                 +---------+---------+
                 |                   |
                 v                   v
          Read Operations       Write Operations
                 |                   |
                 |             Confirmation
                 |                   |
                 |                   v
                 |             User Approval
                 |                   |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |   GitHubClient    |
                 |      HTTPX        |
                 +---------+---------+
                           |
                           | HTTPS
                           v
                 +-------------------+
                 |   GitHub REST API |
                 +-------------------+
```

### Request Flow

1. User enters a natural-language request.
2. Groq determines which GitHub MCP tool is appropriate.
3. The AI assistant sends the tool request through MCP.
4. The MCP server validates the tool arguments.
5. For read operations, the request executes immediately.
6. For write operations, the assistant requests user confirmation.
7. GitHubClient communicates with the GitHub REST API using HTTPX.
8. The result is returned through MCP to the AI assistant.
9. The assistant presents the result to the user.

---

## Features

### Repository Tools
- `get_repository`
- `search_repositories`

Retrieve repository metadata and search GitHub repositories.

### File Tools
- `get_file_contents`
- `list_directory`
- `create_or_update_file`

Read repository files and perform controlled file creation/update operations.

### Issue Tools
- `list_issues`
- `get_issue`
- `create_issue`

Retrieve issues and create new GitHub issues.

### Pull Request Tools
- `list_pull_requests`
- `get_pull_request`
- `create_pull_request`

Inspect pull requests and create new pull requests.

### Branch Tools
- `list_branches`
- `get_branch`
- `create_branch`

Inspect branches and create new branches.

### Commit Tools
- `list_commits`
- `get_commit`

Retrieve branch commit history and individual commit information.

### Search Tools
- `search_code`
- `search_issues`
- `search_pull_requests`

Search GitHub using GitHub's search capabilities.

### Label Tools
- `list_labels`
- `add_labels_to_issue`

Inspect available repository labels and attach existing labels to issues.

---

## Tool Categories

The tools are intentionally separated by GitHub functionality.

| Category | Tools |
|---|---|
| Repository | `get_repository`, `search_repositories` |
| Files | `get_file_contents`, `list_directory`, `create_or_update_file` |
| Issues | `list_issues`, `get_issue`, `create_issue` |
| Pull Requests | `list_pull_requests`, `get_pull_request`, `create_pull_request` |
| Branches | `list_branches`, `get_branch`, `create_branch` |
| Commits | `list_commits`, `get_commit` |
| Search | `search_code`, `search_issues`, `search_pull_requests` |
| Labels | `list_labels`, `add_labels_to_issue` |

The tool descriptions are designed to give the LLM enough information to distinguish between similar operations.

---

## Security and Confirmation

The project follows a safety-first design for GitHub write operations.

### Read Operations

Read-only operations execute directly. Examples:

- Get repository information
- Read a file
- List issues
- Get an issue
- List branches
- Search code
- Get commit information

### Write Operations

Operations that modify GitHub require explicit confirmation from the user. Examples:

- Create or update a file
- Create an issue
- Create a pull request
- Create a branch
- Add labels to an issue

Example:

```text
============================================================
CONFIRMATION REQUIRED
============================================================

The assistant wants to execute:
  Tool: create_issue

Arguments:
{
  "owner": "Yash-R09",
  "repo": "Book-Tracker",
  "title": "AI Assistant Confirmation Test"
}

This operation will modify your GitHub account.

Proceed? (yes/no):
```

The operation is executed only when the user explicitly approves it.

This prevents the LLM from silently making destructive or unintended changes to a GitHub account.

---

## Authentication

The server uses a GitHub Personal Access Token for authenticated GitHub API access.

Environment variables are used so credentials are not hardcoded into the source code.

Example `.env`:

```env
GITHUB_TOKEN=your_github_token
GROQ_API_KEY=your_groq_api_key
```

Never commit `.env` or API keys to GitHub.

A `.env.example` file should be included in the repository:

```env
GITHUB_TOKEN=
GROQ_API_KEY=
```

---

## Technology Stack

- Python 3.12
- Model Context Protocol (MCP) Python SDK
- GitHub REST API
- HTTPX
- Groq API
- Pydantic
- Python asyncio
- MCP Inspector

---

## Project Structure

```text
github-mcp-server/
│
├── app/
│   ├── __init__.py
│   ├── github_client.py
│   ├── server.py
│   │
│   └── tools/
│       ├── ...
│
├── client/
│   ├── __init__.py
│   ├── mcp_client.py
│   ├── assistant.py
│   └── test_client.py
│
├── evaluation/
│   ├── __init__.py
│   ├── evaluator.py
│   ├── test_cases.py
│   └── predictions.json
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Running the MCP Server

Activate the virtual environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

Run the MCP development server:

```bash
mcp dev app\server.py
```

The MCP Inspector can then be used to inspect the available tools and execute test calls.

---

## Running the AI Assistant

The project includes a Groq-powered AI assistant that connects to the GitHub MCP server.

Run:

```bash
python -m client.assistant
```

Example:

```text
Connected to GitHub MCP server.

============================================================
GitHub MCP AI Assistant
============================================================

Type 'exit' to quit.

You: What is the default branch of microsoft/vscode?

Assistant: The default branch of the microsoft/vscode repository is "main".
```

---

## MCP Tool Discovery

The AI assistant dynamically discovers the tools exposed by the MCP server.

Example tools discovered by the client:

- `get_repository`
- `search_repositories`
- `get_file_contents`
- `list_directory`
- `create_or_update_file`
- `list_issues`
- `get_issue`
- `create_issue`
- `list_pull_requests`
- `get_pull_request`
- `create_pull_request`
- `list_branches`
- `get_branch`
- `create_branch`
- `list_commits`
- `get_commit`
- `search_code`
- `search_issues`
- `search_pull_requests`
- `list_labels`
- `add_labels_to_issue`

This demonstrates an important MCP concept: the AI client does not need GitHub-specific logic hardcoded into it. The MCP server exposes capabilities as tools that the client can discover and invoke.

---

## Evaluation

The project includes a 50-question tool-selection evaluation.

Each natural-language question has an expected MCP tool.

The evaluation measures three outcomes:

- **Correct Tool** — the AI selected the expected tool.
- **Wrong Tool** — the AI selected a valid MCP tool, but it was not the expected tool.
- **Tool Failed** — the AI failed to produce a valid tool selection.

### Evaluation Results

Baseline evaluation:

```text
============================================================
GitHub MCP Server Tool Selection Evaluation
============================================================

Total test cases : 50
Evaluated        : 50
Correct          : 47
Wrong Tool       : 3
Tool Failed      : 0
Accuracy         : 94.00%

============================================================
```

**Summary**

| Metric | Result |
|---|---|
| Total Questions | 50 |
| Correct Tool | 47 |
| Wrong Tool | 3 |
| Tool Failed | 0 |
| Accuracy | 94% |

The evaluation demonstrates that the AI assistant successfully selected the correct MCP tool for the majority of natural-language GitHub requests.

The three wrong-tool cases involved semantic overlap between tools, such as:

- Branch information vs. commit information
- Issue search vs. issue listing
- Issue labels vs. file operations

These cases demonstrate why precise MCP tool descriptions are important for reliable tool selection.

### Example Evaluation Cases

**Question:**
"What is the default branch of microsoft/vscode?"

- Expected: `get_repository`
- Predicted: `get_repository`
- Status: **CORRECT**

**Another example:**

**Question:**
"What commit does the develop branch point to?"

- Expected: `get_branch`
- Predicted: `get_commit`
- Status: **WRONG_TOOL**

This illustrates that tool-selection accuracy depends not only on the model, but also on how clearly tool capabilities are represented.

### Running the Evaluation

Run:

```bash
python -m evaluation.evaluator
```

The evaluator loads the 50 test cases from `evaluation/test_cases.py` and stores the model predictions in `evaluation/predictions.json`.

---

## MCP Concepts Demonstrated

This project demonstrates several important MCP concepts.

- **MCP Server** — The server exposes GitHub functionality as structured tools.
- **MCP Client** — The AI assistant connects to the MCP server and discovers available tools dynamically.
- **Tool Schema** — Each tool exposes structured parameters that the model can use to construct tool calls.
- **Tool Selection** — The LLM decides which tool best matches a user's natural-language request.
- **API Abstraction** — GitHub API communication is isolated inside `GitHubClient`, keeping API logic separate from MCP tool definitions.
- **Authentication** — GitHub authentication is handled using environment-based credentials.
- **Confirmation** — Write operations require explicit user approval before execution.
- **Error Handling** — GitHub API failures and invalid operations are handled and surfaced to the client.

---

## Design Principles

The project follows these principles:

1. **Separation of concerns**

   ```text
   AI Assistant
         |
         v
   MCP Client
         |
         v
   MCP Server
         |
         v
   GitHubClient
         |
         v
   GitHub API
   ```

   Each layer has a specific responsibility.

2. **Least privilege** — The server exposes only the GitHub operations required by the application.

3. **Explicit confirmation** — The AI cannot silently modify GitHub data.

4. **Structured interfaces** — Tools use structured inputs and outputs rather than relying on unstructured text.

5. **Testability** — The tool-selection layer is evaluated independently using 50 natural-language test cases.

---

## Why MCP?

Traditional LLM applications often hardcode API integrations directly into the application.

MCP provides a standardized interface between AI applications and external tools.

Instead of building GitHub-specific integration logic directly into every AI assistant, an MCP server exposes GitHub capabilities through standardized tools. This allows MCP-compatible AI clients to discover and use those capabilities.

---

## Example Use Cases

The assistant can handle requests such as:

- "What is the default branch of microsoft/vscode?"
- "Read README.md from microsoft/vscode."
- "Show me the open issues in microsoft/vscode."
- "List branches in my repository."
- "Show the latest commits on main."
- "Search GitHub code for FastMCP."
- "Find issues mentioning authentication."
- "Create a new branch called feature-auth from main."

For modifying operations, the assistant asks for confirmation before execution.

---

## Learning Outcomes

This project provides practical experience with:

- Model Context Protocol
- MCP server and client architecture
- LLM tool selection
- Tool schema design
- GitHub REST API integration
- HTTPX
- API authentication
- Structured tool inputs and outputs
- LLM error handling
- Confirmation workflows
- Evaluation of tool selection
- AI infrastructure design

---

## Future Improvements

Potential improvements include:

- OAuth-based GitHub authentication
- More GitHub API operations
- Better pagination support
- Retry and backoff handling
- Rate-limit awareness
- More comprehensive evaluation datasets
- Improved tool-selection accuracy
- Audit logging
- Fine-grained permission scopes
- Support for additional MCP-compatible clients

---

## Author

Built as an AI Engineering portfolio project to explore Model Context Protocol, LLM tool use, API integration, and AI infrastructure.
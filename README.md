# GitHub MCP Server

An AI-ready GitHub integration server built using the
Model Context Protocol (MCP).

The server exposes structured tools that allow AI assistants
to interact with GitHub repositories through the GitHub REST API.

---

## Features

- Repository information and search
- File reading and writing
- Issue management
- Pull request management
- Branch management
- Commit inspection
- GitHub code search
- Issue and pull request search
- Repository label management
- Token-based GitHub authentication
- Centralized API error handling
- Input validation
- MCP Inspector support
- Tool-selection evaluation benchmark

---

## Architecture

```text
AI Assistant
     |
     | Model Context Protocol
     v
+-------------------------+
|      MCP Server         |
|                         |
|      22 Typed Tools     |
+------------+------------+
             |
             v
+-------------------------+
|      GitHubClient       |
|                         |
| Authentication          |
| HTTP abstraction        |
| Validation              |
| Error handling          |
+------------+------------+
             |
             | HTTPS
             v
+-------------------------+
|     GitHub REST API     |
+-------------------------+
import base64
import os
from typing import Any

import httpx
from dotenv import load_dotenv


# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# GitHub Client
# ============================================================

class GitHubClient:
    """
    Abstraction layer over the GitHub REST API.

    The MCP tools should interact with this class instead of
    directly making HTTP requests.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self) -> None:
        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise RuntimeError(
                "GITHUB_TOKEN is not configured. "
                "Set it in your .env file."
            )

        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=30.0,
        )

    # ========================================================
    # Common helpers
    # ========================================================

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """
        Send an HTTP request and convert GitHub errors into
        useful application-level errors.
        """

        try:
            response = self.client.request(
                method,
                endpoint,
                **kwargs,
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                "GitHub API request timed out."
            )
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"GitHub API connection failed: {exc}"
            )

        if response.is_success:
            if not response.content:
                return {}

            return response.json()

        # Try to extract GitHub's error message.
        try:
            data = response.json()
            message = data.get(
                "message",
                "GitHub API request failed.",
            )
        except Exception:
            message = response.text or "GitHub API request failed."

        status = response.status_code

        if status == 401:
            raise RuntimeError(
                "GitHub authentication failed. "
                "Check that GITHUB_TOKEN is valid."
            )

        if status == 403:
            raise RuntimeError(
                f"GitHub permission denied or rate limit exceeded: "
                f"{message}"
            )

        if status == 404:
            raise RuntimeError(
                f"GitHub resource not found: {message}"
            )

        if status == 409:
            raise RuntimeError(
                f"GitHub conflict: {message}"
            )

        if status == 422:
            raise RuntimeError(
                f"GitHub validation failed: {message}"
            )

        if status == 429:
            raise RuntimeError(
                "GitHub API rate limit exceeded."
            )

        if status >= 500:
            raise RuntimeError(
                f"GitHub server error ({status}): {message}"
            )

        raise RuntimeError(
            f"GitHub API error ({status}): {message}"
        )

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit < 1 or limit > 100:
            raise ValueError(
                "limit must be between 1 and 100."
            )

    @staticmethod
    def _validate_state(state: str) -> None:
        if state not in {"open", "closed", "all"}:
            raise ValueError(
                "state must be one of: open, closed, all."
            )

    # ========================================================
    # Repository
    # ========================================================

    def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> dict:
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}",
        )

        return {
            "name": data["name"],
            "full_name": data["full_name"],
            "description": data.get("description"),
            "private": data["private"],
            "default_branch": data["default_branch"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "open_issues": data["open_issues_count"],
            "language": data.get("language"),
            "html_url": data["html_url"],
        }

    def search_repositories(
        self,
        query: str,
        language: str | None = None,
        limit: int = 5,
    ) -> list[dict]:

        self._validate_limit(limit)

        if not query.strip():
            raise ValueError("query cannot be empty.")

        search_query = query

        if language:
            search_query += f" language:{language}"

        data = self._request(
            "GET",
            "/search/repositories",
            params={
                "q": search_query,
                "per_page": limit,
            },
        )

        results = []

        for item in data.get("items", []):
            results.append(
                {
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "description": item.get("description"),
                    "stars": item["stargazers_count"],
                    "language": item.get("language"),
                    "html_url": item["html_url"],
                }
            )

        return results

    # ========================================================
    # Files
    # ========================================================

    def get_file_contents(
        self,
        owner: str,
        repo: str,
        path: str,
    ) -> dict:

        if not path.strip():
            raise ValueError("path cannot be empty.")

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
        )

        if isinstance(data, list):
            raise RuntimeError(
                "The requested path is a directory. "
                "Use list_directory instead."
            )

        encoded_content = data.get("content", "")
        encoding = data.get("encoding")

        if encoding == "base64":
            try:
                content = base64.b64decode(
                    encoded_content
                ).decode("utf-8")
            except UnicodeDecodeError:
                content = (
                    "[Binary or non-UTF-8 file content]"
                )
        else:
            content = encoded_content

        return {
            "name": data.get("name"),
            "path": data.get("path"),
            "sha": data.get("sha"),
            "size": data.get("size"),
            "content": content,
            "html_url": data.get("html_url"),
        }

    def list_directory(
        self,
        owner: str,
        repo: str,
        path: str = "",
    ) -> list[dict]:

        endpoint = f"/repos/{owner}/{repo}/contents/{path}"

        data = self._request(
            "GET",
            endpoint,
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "The requested path is a file, not a directory."
            )

        return [
            {
                "name": item["name"],
                "path": item["path"],
                "type": item["type"],
                "size": item.get("size"),
                "sha": item.get("sha"),
                "html_url": item.get("html_url"),
            }
            for item in data
        ]

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
        sha: str | None = None,
    ) -> dict:

        if not path.strip():
            raise ValueError("path cannot be empty.")

        if not message.strip():
            raise ValueError(
                "commit message cannot be empty."
            )

        encoded_content = base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

        payload: dict[str, Any] = {
            "message": message,
            "content": encoded_content,
        }

        if branch:
            payload["branch"] = branch

        if sha:
            payload["sha"] = sha

        data = self._request(
            "PUT",
            f"/repos/{owner}/{repo}/contents/{path}",
            json=payload,
        )

        return {
            "message": "File created/updated successfully.",
            "path": path,
            "sha": data.get("content", {}).get("sha"),
            "commit_sha": data.get("commit", {}).get("sha"),
            "html_url": data.get("content", {}).get("html_url"),
        }

    # ========================================================
    # Issues
    # ========================================================

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> list[dict]:

        self._validate_state(state)
        self._validate_limit(limit)

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": state,
                "per_page": limit,
            },
        )

        results = []

        for issue in data:

            # GitHub returns PRs from this endpoint too.
            if "pull_request" in issue:
                continue

            results.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "author": issue["user"]["login"],
                    "comments": issue["comments"],
                    "labels": [
                        label["name"]
                        for label in issue.get("labels", [])
                    ],
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "html_url": issue["html_url"],
                }
            )

        return results

    def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict:

        if issue_number < 1:
            raise ValueError(
                "issue_number must be positive."
            )

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
        )

        return {
            "number": data["number"],
            "title": data["title"],
            "body": data.get("body"),
            "state": data["state"],
            "author": data["user"]["login"],
            "comments": data["comments"],
            "labels": [
                label["name"]
                for label in data.get("labels", [])
            ],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "html_url": data["html_url"],
        }

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
    ) -> dict:

        if not title.strip():
            raise ValueError("title cannot be empty.")

        payload: dict[str, Any] = {
            "title": title,
            "body": body,
        }

        if labels:
            payload["labels"] = labels

        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json=payload,
        )

        return {
            "number": data["number"],
            "title": data["title"],
            "state": data["state"],
            "html_url": data["html_url"],
            "message": "Issue created successfully.",
        }

    # ========================================================
    # Pull Requests
    # ========================================================

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> list[dict]:

        self._validate_state(state)
        self._validate_limit(limit)

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": state,
                "per_page": limit,
            },
        )

        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "source_branch": pr["head"]["ref"],
                "target_branch": pr["base"]["ref"],
                "draft": pr["draft"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "html_url": pr["html_url"],
            }
            for pr in data
        ]

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> dict:

        if pull_number < 1:
            raise ValueError(
                "pull_number must be positive."
            )

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}",
        )

        return {
            "number": data["number"],
            "title": data["title"],
            "body": data.get("body"),
            "state": data["state"],
            "author": data["user"]["login"],
            "source_branch": data["head"]["ref"],
            "target_branch": data["base"]["ref"],
            "draft": data["draft"],
            "merged": data["merged"],
            "mergeable": data.get("mergeable"),
            "commits": data["commits"],
            "changed_files": data["changed_files"],
            "additions": data["additions"],
            "deletions": data["deletions"],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "html_url": data["html_url"],
        }

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str = "",
        draft: bool = False,
    ) -> dict:

        if not title.strip():
            raise ValueError("title cannot be empty.")

        if not head.strip():
            raise ValueError("head cannot be empty.")

        if not base.strip():
            raise ValueError("base cannot be empty.")

        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft,
        }

        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json=payload,
        )

        return {
            "number": data["number"],
            "title": data["title"],
            "state": data["state"],
            "draft": data["draft"],
            "html_url": data["html_url"],
            "message": "Pull request created successfully.",
        }

    # ========================================================
    # Branches
    # ========================================================

    def list_branches(
        self,
        owner: str,
        repo: str,
        limit: int = 10,
    ) -> list[dict]:

        self._validate_limit(limit)

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={"per_page": limit},
        )

        return [
            {
                "name": branch["name"],
                "sha": branch["commit"]["sha"],
                "protected": branch["protected"],
            }
            for branch in data
        ]

    def get_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
    ) -> dict:

        if not branch.strip():
            raise ValueError("branch cannot be empty.")

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches/{branch}",
        )

        return {
            "name": data["name"],
            "sha": data["commit"]["sha"],
            "protected": data["protected"],
            "html_url": (
                f"https://github.com/{owner}/{repo}"
                f"/tree/{branch}"
            ),
        }

    def create_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
        from_branch: str = "main",
    ) -> dict:

        if not branch.strip():
            raise ValueError("branch cannot be empty.")

        if not from_branch.strip():
            raise ValueError(
                "from_branch cannot be empty."
            )

        source = self._request(
            "GET",
            f"/repos/{owner}/{repo}/git/ref/"
            f"heads/{from_branch}",
        )

        sha = source["object"]["sha"]

        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            json={
                "ref": f"refs/heads/{branch}",
                "sha": sha,
            },
        )

        return {
            "name": branch,
            "sha": data["object"]["sha"],
            "message": (
                f"Branch '{branch}' created from "
                f"'{from_branch}'."
            ),
        }

    # ========================================================
    # Commits
    # ========================================================

    def list_commits(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        limit: int = 10,
    ) -> list[dict]:

        self._validate_limit(limit)

        if not branch.strip():
            raise ValueError("branch cannot be empty.")

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits",
            params={
                "sha": branch,
                "per_page": limit,
            },
        )

        return [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "html_url": commit["html_url"],
            }
            for commit in data
        ]

    def get_commit(
        self,
        owner: str,
        repo: str,
        sha: str,
    ) -> dict:

        if not sha.strip():
            raise ValueError("sha cannot be empty.")

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits/{sha}",
        )

        return {
            "sha": data["sha"],
            "message": data["commit"]["message"],
            "author": data["commit"]["author"]["name"],
            "date": data["commit"]["author"]["date"],
            "files_changed": data["files"],
            "stats": data.get("stats"),
            "html_url": data["html_url"],
        }

    # ========================================================
    # Search
    # ========================================================

    def search_code(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        self._validate_limit(limit)

        if not query.strip():
            raise ValueError("query cannot be empty.")

        data = self._request(
            "GET",
            "/search/code",
            params={
                "q": query,
                "per_page": limit,
            },
        )

        return [
            {
                "name": item["name"],
                "path": item["path"],
                "repository": item["repository"]["full_name"],
                "sha": item["sha"],
                "html_url": item["html_url"],
            }
            for item in data.get("items", [])
        ]

    def search_issues(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        self._validate_limit(limit)

        if not query.strip():
            raise ValueError("query cannot be empty.")

        data = self._request(
            "GET",
            "/search/issues",
            params={
                "q": query,
                "per_page": limit,
            },
        )

        return [
            {
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "repository": item["repository_url"].split(
                    "/repos/"
                )[-1],
                "author": item["user"]["login"],
                "html_url": item["html_url"],
            }
            for item in data.get("items", [])
        ]

    def search_pull_requests(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        self._validate_limit(limit)

        if not query.strip():
            raise ValueError("query cannot be empty.")

        data = self._request(
            "GET",
            "/search/issues",
            params={
                "q": f"{query} type:pr",
                "per_page": limit,
            },
        )

        return [
            {
                "number": item["number"],
                "title": item["title"],
                "state": item["state"],
                "repository": item["repository_url"].split(
                    "/repos/"
                )[-1],
                "author": item["user"]["login"],
                "html_url": item["html_url"],
            }
            for item in data.get("items", [])
        ]

    # ========================================================
    # Labels
    # ========================================================

    def list_labels(
        self,
        owner: str,
        repo: str,
        limit: int = 30,
    ) -> list[dict]:

        self._validate_limit(limit)

        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/labels",
            params={"per_page": limit},
        )

        return [
            {
                "name": label["name"],
                "color": label["color"],
                "description": label.get("description"),
            }
            for label in data
        ]

    def add_labels_to_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        labels: list[str],
    ) -> dict:

        if issue_number < 1:
            raise ValueError(
                "issue_number must be positive."
            )

        if not labels:
            raise ValueError(
                "At least one label is required."
            )

        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/"
            f"{issue_number}/labels",
            json={"labels": labels},
        )

        return {
            "issue_number": issue_number,
            "labels": [
                label["name"]
                for label in data
            ],
            "message": "Labels added successfully.",
        }

    # ========================================================
    # Cleanup
    # ========================================================

    def close(self) -> None:
        self.client.close()
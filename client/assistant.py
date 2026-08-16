import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from client.mcp_client import GitHubMCPClient


load_dotenv()


# ============================================================
# Tools that can modify GitHub data
# ============================================================

WRITE_TOOLS = {
    "create_or_update_file",
    "create_issue",
    "create_pull_request",
    "create_branch",
    "add_labels_to_issue",
}


class GitHubAssistant:
    """
    AI assistant that uses Groq for reasoning and the GitHub
    MCP server for executing GitHub operations.
    """

    def __init__(self, mcp_client: GitHubMCPClient):

        self.mcp_client = mcp_client

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        self.groq = Groq(api_key=api_key)

        self.model = "llama-3.3-70b-versatile"

        self.system_prompt = """
You are a GitHub AI assistant.

You interact with GitHub through the available MCP tools.

Rules:

1. Choose the most appropriate MCP tool for the user's request.
2. Never invent GitHub data.
3. Use MCP tools whenever GitHub information is required.
4. Use the tool arguments according to their schemas.
5. If required information is missing, ask the user for clarification.
6. Clearly explain the result returned by the tool.
7. Do not claim an operation succeeded unless the MCP tool confirms success.
8. When the user asks to read or show file contents, provide the
   actual file contents rather than only summarizing them unless
   the user explicitly asks for a summary.
"""

    # ========================================================
    # MCP tool discovery
    # ========================================================

    async def get_tools(self) -> list[dict[str, Any]]:
        """
        Retrieve MCP tools and convert them to the format expected
        by Groq's tool-calling API.
        """

        mcp_tools = await self.mcp_client.list_tools()

        groq_tools = []

        for tool in mcp_tools:

            groq_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"],
                    },
                }
            )

        return groq_tools

    # ========================================================
    # Confirmation
    # ========================================================

    @staticmethod
    def requires_confirmation(tool_name: str) -> bool:
        """
        Return True if the requested tool modifies GitHub data.
        """

        return tool_name in WRITE_TOOLS

    @staticmethod
    def ask_confirmation(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> bool:
        """
        Ask the user for confirmation before executing a
        write operation.
        """

        print("\n" + "=" * 60)
        print("⚠️  CONFIRMATION REQUIRED")
        print("=" * 60)

        print(
            f"\nThe assistant wants to execute:\n"
            f"  Tool: {tool_name}\n"
        )

        print("Arguments:")

        print(
            json.dumps(
                arguments,
                indent=2,
                ensure_ascii=False,
            )
        )

        print(
            "\nThis operation will modify your GitHub account."
        )

        while True:

            answer = input(
                "\nProceed? (yes/no): "
            ).strip().lower()

            if answer in {"yes", "y"}:
                return True

            if answer in {"no", "n"}:
                return False

            print(
                "Please enter 'yes' or 'no'."
            )

    # ========================================================
    # Ask assistant
    # ========================================================

    async def ask(self, question: str) -> str:
        """
        Send a user question to Groq and allow it to invoke
        MCP tools when necessary.
        """

        tools = await self.get_tools()

        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        while True:

            response = self.groq.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            message = response.choices[0].message

            # ------------------------------------------------
            # No tool call → final answer
            # ------------------------------------------------

            if not message.tool_calls:

                return message.content or ""

            # ------------------------------------------------
            # Add assistant tool call to conversation
            # ------------------------------------------------

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in message.tool_calls
                    ],
                }
            )

            # ------------------------------------------------
            # Execute requested tools
            # ------------------------------------------------

            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name

                # --------------------------------------------
                # Parse arguments
                # --------------------------------------------

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                except json.JSONDecodeError:

                    tool_result = {
                        "status": "error",
                        "error": (
                            "Invalid JSON arguments generated "
                            "by the model."
                        ),
                    }

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(
                                tool_result
                            ),
                        }
                    )

                    continue

                # --------------------------------------------
                # Confirmation for write tools
                # --------------------------------------------

                if self.requires_confirmation(tool_name):

                    confirmed = self.ask_confirmation(
                        tool_name,
                        arguments,
                    )

                    # User rejected the operation.
                    # Stop the current request immediately so
                    # Groq cannot retry the same write operation.
                    if not confirmed:

                        return (
                            f"Operation cancelled. "
                            f"The GitHub tool '{tool_name}' "
                            f"was not executed."
                        )

                # --------------------------------------------
                # Execute MCP tool
                # --------------------------------------------

                try:

                    result = await self.mcp_client.call_tool(
                        tool_name,
                        arguments,
                    )

                    tool_result = self._serialize_result(
                        result
                    )

                except Exception as exc:

                    tool_result = {
                        "status": "error",
                        "error": str(exc),
                    }

                # --------------------------------------------
                # Send result back to Groq
                # --------------------------------------------

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    }
                )

    # ========================================================
    # Result serialization
    # ========================================================

    @staticmethod
    def _serialize_result(result: Any) -> Any:
        """
        Convert MCP results into JSON-serializable data.
        """

        if hasattr(result, "model_dump"):
            return result.model_dump()

        if hasattr(result, "dict"):
            return result.dict()

        if isinstance(result, list):

            return [
                GitHubAssistant._serialize_result(item)
                for item in result
            ]

        if isinstance(result, dict):

            return {
                key: GitHubAssistant._serialize_result(value)
                for key, value in result.items()
            }

        return result


# ============================================================
# CLI
# ============================================================

async def main():

    client = GitHubMCPClient()

    try:

        await client.connect()

        assistant = GitHubAssistant(client)

        print("=" * 60)
        print("GitHub MCP AI Assistant")
        print("=" * 60)
        print("Type 'exit' to quit.")

        print(
            "\nWrite operations require confirmation."
        )

        while True:

            question = input("\nYou: ").strip()

            if question.lower() == "exit":
                break

            if not question:
                continue

            try:

                answer = await assistant.ask(
                    question
                )

                print(
                    f"\nAssistant: {answer}"
                )

            except Exception as exc:

                print(
                    f"\nAssistant error: {exc}"
                )

    finally:

        try:
            await client.close()

        except asyncio.CancelledError:
            pass


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\nAssistant stopped.")
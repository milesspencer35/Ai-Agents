"""
OpenAI API chat interface

This script shows how to:
- Connect the OpenAI Python SDK to an OpenAI model
- Register an MCP server for checking local weather
- Let the model decide when to call the tool
- Execute the tool and return the final answer

"""
#!/usr/bin/env python3
import argparse
import sys
from typing import List, Dict, Optional

from openai import OpenAI


client = OpenAI()


mcp_weather_tool = {
    "type": "mcp",
    "server_label": "byu-cs-mcp-demo",
    "server_url": "https://byu-cs-mcp-demo.fastmcp.app/mcp",
    "require_approval": "never",
}

def chat_once(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
) -> str:
    """
    Send chat messages to the model and return the assistant response text.
    """
    response = client.responses.create(
        model=model,
        stream=False,
        timeout=timeout,
        tools=[mcp_weather_tool],
        tool_choice="auto",
        input=messages
    )

    return response.output_text


def trim_history(messages: List[Dict[str, str]], max_history: int) -> List[Dict[str, str]]:
    """
    Keep the system message and the last `max_history` non-system messages.
    If max_history <= 0, no trimming is applied.
    """
    if not messages:
        return messages
    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    if max_history <= 0:
        return (system_msgs[:1] if system_msgs else []) + non_system
    trimmed = non_system[-max_history:]
    return (system_msgs[:1] if system_msgs else []) + trimmed


def chat(args) -> int:
    """
    Run an interactive chat session with the Ollama model.
    Supports:
      - exit: quit the session
      - /reset: clear context but preserve the system prompt
      - --max-history: cap number of non-system messages kept in context
    """
    # instructions = (
    #     "You are a helpful assistant. If the user asks about weather, "
    #     "use the weather tool to retrieve data and then respond clearly. "
    #     "If the server returns an error, report the error to the user. "
    #     "The user does not ask about the weather, proceed to answer as you "
    #     "would without access to any tool calls."
    # )
    instructions = (
        "You are a helpful assistant."
    )
    base_system_message = {"role": "system", "content": instructions}
    messages: List[Dict[str, str]] = [base_system_message]

    try:
        while True:
            try:
                user_input = input("\n--------------------\nYou: ").strip()
            except EOFError:
                print()  # newline after Ctrl-D
                break

            if user_input.lower() == "exit":
                break

            if user_input == "/reset":
                messages = [base_system_message]
                print("[Context reset]\n")
                continue

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            # Trim before sending to keep the request payload small
            messages = trim_history(messages, args.max_history)

            try:
                reply = chat_once(
                    model=args.model,
                    messages=messages,
                    timeout=args.timeout
                )
            except Exception as e:
                print(e)
                continue

            messages.append({"role": "assistant", "content": reply})
            # Trim again after appending assistant reply to enforce cap
            messages = trim_history(messages, args.max_history)

            print(f"Assistant: {reply}\n")
    except KeyboardInterrupt:
        print("\nExiting.")
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Simple terminal chat with an LLM model (with context, reset, and history limit).")
    parser.add_argument("--model", default="gpt-5-nano", help="Model name (defaults to gpt-5-nano)")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds")
    parser.add_argument("--max-history", type=int, default=30, help="Max number of non-system messages to keep in context (default: 30)")
    args = parser.parse_args(argv)

    return chat(args)


if __name__ == "__main__":
    sys.exit(main())

"""
Simple MCP Server Example
This server exposes basic tools for demonstration purposes.
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Create an MCP server instance
app = Server("simple-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="add",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        ),
        Tool(
            name="greet",
            description="Generate a greeting message",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="get_byu_football_schedule",
            description="Get the BYU football schedule",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_current_date",
            description="Get the current date",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="create_calendar_event",
            description="Create a calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event summary"},
                    "start_time": {"type": "string", "description": "Event start time"},
                    "end_time": {"type": "string", "description": "Event end time"},
                    "calendar_id": {"type": "string", "description": "Calendar ID"},
                },
                "required": ["summary", "start_time", "end_time", "calendar_id"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    if name == "add":
        a = arguments["a"]
        b = arguments["b"]
        result = a + b
        return [TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]
    elif name == "greet":
        name_arg = arguments["name"]
        return [TextContent(type="text", text=f"Hello, {name_arg}! Welcome to the MCP server.")]
    elif name == "get_byu_football_schedule":
        return [TextContent(type="text", text=f"{get_byu_football_schedule()}")]
    elif name == "get_current_date":
        return [TextContent(type="text", text=f"{get_current_date()}")]
    elif name == "create_calendar_event":
        summary = arguments["summary"]
        start_time = arguments["start_time"]
        end_time = arguments["end_time"]
        calendar_id = arguments["calendar_id"]
        return [TextContent(type="text", text=f"{create_calendar_event(summary, start_time, end_time, calendar_id)}")]
    else:
        raise ValueError(f"Unknown tool: {name}")

def get_byu_football_schedule():
    """Returns BYU's football schedule for the current season."""
    print("-> Getting BYU football schedule")
    url = "https://api.collegefootballdata.com/games"
    params = {
        "year": 2025,
        "team": "BYU",
        "seasonType": "regular"
    }
    headers = {
        "Authorization": f"Bearer {os.environ['CFD_API_KEY']}"
    }
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    print("Error:", resp.status_code, resp.text)
    return None

def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    print("-> Getting current date")
    return datetime.now().strftime("%Y-%m-%d")

def create_calendar_event(summary: str, start_time: str, end_time: str, calendar_id="primary"):
    """
    Create a Google Calendar event.

    Args:
        summary (str): Event title
        start_time (str): Start time in RFC3339 format (e.g. '2025-09-27T10:00:00-06:00')
        end_time (str): End time in RFC3339 format
        calendar_id (str): Calendar ID, defaults to primary calendar

    Returns:
        dict: Created event details
    """
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, 'credentials.json')
    TOKEN_FILE = os.path.join(SCRIPT_DIR, 'token.json')
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    print("-> Creating calendar event")
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
            "timeZone": "America/Denver",  # change to your timezone
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "America/Denver",
        },
    }

    event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
    print("-> Event created: %s" % (event_result.get("htmlLink")))
    return event_result

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
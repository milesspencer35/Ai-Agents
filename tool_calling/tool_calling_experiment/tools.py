from __future__ import print_function
import os
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

class ToolKit:
    # Tool definitions as a class variable
    tools = [
        {
            "type": "function",
            "name": "get_horoscope",
            "description": "Get today's horoscope for an astrological sign.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {
                        "type": "string",
                        "description": "An astrological sign like Taurus or Aquarius",
                    },
                },
                "required": ["sign"],
            },
        },
        {
            "type": "function",
            "name": "get_byu_football_schedule",
            "description": "Get BYU's football schedule for the current season.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "type": "function",
            "name": "get_current_date",
            "description": "Get the current date.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "type": "function",
            "name": "create_calendar_event",
            "description": "Create a Google Calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in RFC3339 format (e.g. '2025-09-27T10:00:00-06:00')",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in RFC3339 format",
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Calendar ID, defaults to primary calendar",
                    },
                },
                "required": ["summary", "start_time", "end_time"],
            },
        },
    ]

    @staticmethod
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

    @staticmethod
    def get_current_date() -> str:
        """Returns the current date in YYYY-MM-DD format."""
        print("-> Getting current date")
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_horoscope(sign: str) -> str:
        """
        Returns a horoscope for the given astrological sign.
        """
        print("Getting horoscope")
        return f"{sign}: Next Tuesday you will befriend a baby otter."

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    @staticmethod
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
        print("-> Creating calendar event")
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", ToolKit.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", ToolKit.SCOPES)
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

# Create an instance for easier importing
toolkit = ToolKit()
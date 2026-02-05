import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from utils import get_data_path

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]
TOKEN_FILE = get_data_path("token.pickle")
CREDENTIALS_FILE = get_data_path("google-oauth-credentials.json")


def credentials_file_exists() -> bool:
    """Check if the credentials file exists."""
    return CREDENTIALS_FILE.exists()


def is_authenticated() -> bool:
    return TOKEN_FILE.exists()


def authenticate():
    creds = None

    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)


def get_docs_service():
    """
    Returns a Google Docs API service object using existing credentials.
    """
    creds = None
    
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        raise Exception("Not authenticated. Please authenticate first.")
    
    return build("docs", "v1", credentials=creds)


def get_sheets_service():
    """
    Returns a Google Sheets API service object using existing credentials.
    """
    creds = None
    
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        raise Exception("Not authenticated. Please authenticate first.")
    
    return build("sheets", "v4", credentials=creds)


def get_authenticated_user_email(service=None):
    """
    Returns the Gmail address of the currently authenticated user.
    Requires a valid service object.
    """
    from googleapiclient.errors import HttpError

    try:
        if service is None:
            return "Unknown"
        # Make the API call
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress", "Unknown")
    except HttpError as e:
        # Token might be invalid or expired
        print(f"Gmail API error: {e}")
        return "Unknown"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Unknown"

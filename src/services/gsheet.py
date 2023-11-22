import gspread
from oauth2client.service_account import ServiceAccountCredentials


def authenticate_gspread():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("config/auth.json", scope)
    client = gspread.authorize(creds)
    return client

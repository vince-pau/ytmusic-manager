from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('token.json')
youtube = build('youtube', 'v3', credentials=creds)

resp = youtube.channels().list(part='snippet', mine=True).execute()
items = resp.get('items', [])
if items:
    ch = items[0]['snippet']
    print(f"Authenticated as: {ch['title']} ({ch.get('customUrl', 'no custom URL')})")
else:
    print("No channel found for this token.")
    print("The token may be for a different Google account than @vpau.")

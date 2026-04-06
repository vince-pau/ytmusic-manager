from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/youtube']

if not os.path.exists('credentials.json'):
    print("\nERROR: credentials.json not found.")
    print("Download it from Google Cloud Console:")
    print("  APIs & Services -> Credentials -> your OAuth client -> Download JSON")
    print("  Save it as 'credentials.json' in this directory.\n")
    exit(1)

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=8090)

with open('token.json', 'w') as f:
    f.write(creds.to_json())

print("\nDone! token.json saved. Now run: python3 app.py\n")

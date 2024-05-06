import os
import os.path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    load_dotenv()

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        response = service.files().list(
            q="name='MyBackup' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
        ).execute()

        if not response['files']:
            file_metadata = {
                'name': 'MyBackup',
                'mimeType': 'application/vnd.google-apps.folder',
            }

            file = service.files().create(body=file_metadata, fields='id').execute()
            folder_id = file.get('id')
        else:
            folder_id = response['files'][0]['id']

        backupdir = os.getenv('BACKUPDIR')
        for file in os.listdir(backupdir):
            file_metadata = {
                'name': file,
                'parents': [folder_id]
            }

            media = MediaFileUpload(f"{backupdir}/{file}")
            upload_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f'{upload_file}')
            print(f'Backed up file: {file}')

    except HttpError as e:
        print(f'ERROR: {e}')


if __name__ == '__main__':
    main()

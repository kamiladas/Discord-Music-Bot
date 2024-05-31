import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def save_load_credentials(credentials=None):
    token_path = 'token.pickle'
    if credentials:
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
    else:
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                return pickle.load(token)
    return None

def get_authenticated_service():
    credentials = save_load_credentials()
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json',
                scopes=['https://www.googleapis.com/auth/youtube.readonly'])
            credentials = flow.run_local_server(port=0)
        save_load_credentials(credentials)
    return build('youtube', 'v3', credentials=credentials)

def get_playlist_items(youtube, playlist_id):
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    playlist_items = []
    for item in response['items']:
        video_id = item['snippet']['resourceId']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        playlist_items.append(video_url)

    return playlist_items

async def fetch_playlist_urls(playlist_url):
    youtube = get_authenticated_service()
    playlist_id = playlist_url.split('list=')[1].split('&')[0]
    playlist_urls = get_playlist_items(youtube, playlist_id)
    return playlist_urls

# Przykład użycia zostałby uruchomiony w ten sposób:
# playlist_url = "https://www.youtube.com/playlist?list=PLdQ2dhYDK1YiQxgtSKWFYFZoZQo6_Mpst"
# urls = asyncio.run(fetch_playlist_urls(playlist_url))
# print(urls)


from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import httplib2
import google_auth_httplib2
import os
import sys
import re
import json
import time
from typing import Annotated

app = FastAPI()
templates = Jinja2Templates(directory="templates")

SCOPES = ['https://www.googleapis.com/auth/youtube']
TOKEN_FILE = 'token.json'
CACHE_DIR = 'cache'
CACHE_TTL = 3600  # seconds (1 hour)
HIDDEN_FILE = 'hidden.json'

os.makedirs(CACHE_DIR, exist_ok=True)


def load_hidden() -> set:
    if not os.path.exists(HIDDEN_FILE):
        return set()
    with open(HIDDEN_FILE) as f:
        return set(json.load(f))


def save_hidden(ids: set):
    with open(HIDDEN_FILE, 'w') as f:
        json.dump(list(ids), f)

SORT_KEYS = {
    "title":    lambda x: x.get("title", "").lower(),
    "artist":   lambda x: x.get("artist", "").lower(),
    "duration": lambda x: x.get("duration_seconds", 0),
    "year":     lambda x: x.get("release_year", ""),
    "added":    lambda x: x.get("added_at", ""),
}


def parse_duration(iso: str) -> int:
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso or '')
    if not m:
        return 0
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)


def fmt_duration(secs: int) -> str:
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def get_youtube():
    if not os.path.exists(TOKEN_FILE):
        print(f"\nERROR: {TOKEN_FILE} not found. Run: python3 auth.py\n")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    authorized_http = google_auth_httplib2.AuthorizedHttp(creds, http=httplib2.Http(proxy_info=None))
    return build('youtube', 'v3', http=authorized_http)


youtube = get_youtube()


def cache_path(playlist_id: str) -> str:
    return os.path.join(CACHE_DIR, f"{playlist_id}.json")


def load_cache(playlist_id: str) -> dict | None:
    path = cache_path(playlist_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    if time.time() - data.get('fetched_at', 0) > CACHE_TTL:
        return None
    return data


def save_cache(playlist_id: str, title: str, tracks: list):
    with open(cache_path(playlist_id), 'w') as f:
        json.dump({'fetched_at': time.time(), 'title': title, 'tracks': tracks}, f)


def all_playlist_items(playlist_id: str) -> list:
    items, page_token = [], None
    while True:
        kw = dict(part='snippet', playlistId=playlist_id, maxResults=50)
        if page_token:
            kw['pageToken'] = page_token
        resp = youtube.playlistItems().list(**kw).execute()
        items.extend(resp.get('items', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return items


def fetch_video_details(video_ids: list) -> dict:
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = youtube.videos().list(part='contentDetails,snippet', id=','.join(batch)).execute()
        for item in resp.get('items', []):
            published = item['snippet'].get('publishedAt', '')
            details[item['id']] = {
                'duration_seconds': parse_duration(item['contentDetails']['duration']),
                'release_year': published[:4] if published else '',
            }
    return details


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    hidden = load_hidden()
    resp = youtube.playlists().list(part='snippet,contentDetails', mine=True, maxResults=50).execute()
    playlists = [
        {'id': i['id'], 'title': i['snippet']['title'], 'count': i['contentDetails']['itemCount']}
        for i in resp.get('items', [])
        if i['id'] not in hidden
    ]
    return templates.TemplateResponse(request, "index.html", {"playlists": playlists, "hidden_count": len(hidden)})


@app.post("/hide-playlist/{playlist_id}")
def hide_playlist(playlist_id: str):
    hidden = load_hidden()
    hidden.add(playlist_id)
    save_hidden(hidden)
    return RedirectResponse('/', status_code=303)


@app.post("/unhide-playlist/{playlist_id}")
def unhide_playlist(playlist_id: str):
    hidden = load_hidden()
    hidden.discard(playlist_id)
    save_hidden(hidden)
    return RedirectResponse('/hidden', status_code=303)


@app.get("/hidden", response_class=HTMLResponse)
def hidden_playlists(request: Request):
    hidden = load_hidden()
    resp = youtube.playlists().list(part='snippet,contentDetails', mine=True, maxResults=50).execute()
    playlists = [
        {'id': i['id'], 'title': i['snippet']['title'], 'count': i['contentDetails']['itemCount']}
        for i in resp.get('items', [])
        if i['id'] in hidden
    ]
    return templates.TemplateResponse(request, "hidden.html", {"playlists": playlists})


def get_tracks(playlist_id: str, refresh: bool = False) -> tuple[str, list]:
    """Return (title, tracks) for a playlist, using cache when available."""
    cached = None if refresh else load_cache(playlist_id)
    if cached:
        return cached['title'], cached['tracks']

    pl_resp = youtube.playlists().list(part='snippet', id=playlist_id).execute()
    pl_title = pl_resp['items'][0]['snippet']['title'] if pl_resp.get('items') else 'Playlist'

    raw = all_playlist_items(playlist_id)
    video_ids = [
        i['snippet']['resourceId']['videoId']
        for i in raw
        if i['snippet'].get('resourceId', {}).get('kind') == 'youtube#video'
    ]
    video_details = fetch_video_details(video_ids)

    tracks = []
    for i in raw:
        sn = i.get('snippet', {})
        if sn.get('resourceId', {}).get('kind') != 'youtube#video':
            continue
        vid = sn['resourceId']['videoId']
        title = sn.get('title', '')
        if title in ('Deleted video', 'Private video'):
            continue
        details = video_details.get(vid, {})
        secs = details.get('duration_seconds', 0)
        added_iso = sn.get('publishedAt', '')
        tracks.append({
            'video_id': vid,
            'title': title,
            'artist': sn.get('videoOwnerChannelTitle', '').removesuffix(' - Topic'),
            'duration': fmt_duration(secs),
            'duration_seconds': secs,
            'release_year': details.get('release_year', ''),
            'added_at': added_iso,
            'added_date': added_iso[:10] if added_iso else '',
        })

    save_cache(playlist_id, pl_title, tracks)
    return pl_title, tracks


@app.get("/playlist/{playlist_id}", response_class=HTMLResponse)
def playlist(request: Request, playlist_id: str, sort_by: str = "title", order: str = "asc", refresh: bool = False):
    from_cache = not refresh and load_cache(playlist_id) is not None
    pl_title, tracks = get_tracks(playlist_id, refresh=refresh)
    tracks = sorted(tracks, key=SORT_KEYS.get(sort_by, SORT_KEYS["title"]), reverse=(order == "desc"))

    return templates.TemplateResponse(request, "playlist.html", {
        "playlist": {"title": pl_title},
        "tracks": tracks,
        "sort_by": sort_by,
        "order": order,
        "playlist_id": playlist_id,
        "from_cache": from_cache,
    })


@app.post("/create-playlist")
def create_playlist(
    title: Annotated[str, Form()],
    video_ids: Annotated[list[str], Form()],
):
    # Create the new playlist
    pl = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {'title': title},
            'status': {'privacyStatus': 'private'},
        }
    ).execute()
    new_id = pl['id']

    # Add each selected video
    for vid in video_ids:
        youtube.playlistItems().insert(
            part='snippet',
            body={'snippet': {
                'playlistId': new_id,
                'resourceId': {'kind': 'youtube#video', 'videoId': vid},
            }}
        ).execute()

    return RedirectResponse(f'/playlist/{new_id}?refresh=true', status_code=303)


@app.get("/duplicates", response_class=HTMLResponse)
def duplicates_page(request: Request):
    hidden = load_hidden()
    resp = youtube.playlists().list(part='snippet,contentDetails', mine=True, maxResults=50).execute()
    playlists = [
        {
            'id': i['id'],
            'title': i['snippet']['title'],
            'count': i['contentDetails']['itemCount'],
            'cached': os.path.exists(cache_path(i['id'])),
        }
        for i in resp.get('items', [])
        if i['id'] not in hidden
    ]
    return templates.TemplateResponse(request, "duplicates.html", {"playlists": playlists})


@app.post("/duplicates/results", response_class=HTMLResponse)
def duplicates_results(request: Request, playlist_ids: Annotated[list[str], Form()]):
    from collections import defaultdict

    # Load tracks for each selected playlist
    playlist_titles = {}
    video_to_playlists = defaultdict(list)

    for pl_id in playlist_ids:
        title, tracks = get_tracks(pl_id)
        playlist_titles[pl_id] = title
        for track in tracks:
            vid = track.get('video_id')
            if vid:
                video_to_playlists[vid].append({'playlist_id': pl_id, 'track': track})

    # Keep only videos appearing in 2+ playlists
    duplicates = [
        {
            'title': entries[0]['track']['title'],
            'artist': entries[0]['track']['artist'],
            'release_year': entries[0]['track'].get('release_year', ''),
            'video_id': vid,
            'playlists': [{'id': e['playlist_id'], 'title': playlist_titles[e['playlist_id']]} for e in entries],
            'count': len(entries),
        }
        for vid, entries in video_to_playlists.items()
        if len(entries) >= 2
    ]
    duplicates.sort(key=lambda x: (-x['count'], x['title'].lower()))

    return templates.TemplateResponse(request, "duplicates_results.html", {
        "duplicates": duplicates,
        "playlist_titles": playlist_titles,
        "total": len(duplicates),
    })


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8080, reload=True)

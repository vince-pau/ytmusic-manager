# YT Music Playlist Manager

A local web app for managing YouTube Music playlists with sorting, filtering, and playlist creation features not available in the YouTube Music UI.

## Features

- **Sort playlists** by title, artist, release year, date added, or duration (ascending/descending)
- **Filter songs** in real time by title or artist
- **Select songs and create new playlists** — filter by artist, select all, save as a new playlist
- **Save sorted copy** — duplicate a playlist in any sort order with one click
- **Multi-playlist duplicate detection** — find songs that appear across multiple playlists
- **Hide playlists** — remove video/non-music playlists from the home page
- **Local caching** — playlists are cached for 1 hour so repeat visits are instant
- **Quota cost estimate** — warns you before creating large playlists that may exceed the YouTube API daily quota

## Requirements

- Python 3.11+
- A Google account with YouTube Music
- A Google Cloud project with the YouTube Data API v3 enabled

## Setup

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **YouTube Data API v3** (APIs & Services → Library)
4. Create OAuth credentials (APIs & Services → Credentials → Create Credentials → OAuth client ID)
   - Application type: **Desktop app**
5. Add your Google account as a test user (APIs & Services → OAuth consent screen → Test users)
6. Download the credentials JSON and save it as `credentials.json` in the project directory

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Authenticate

```bash
python3 auth.py
```

This opens your browser to log in with Google. Your token is saved locally as `token.json`.

### 4. Run

```bash
python3 app.py
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

## Usage

- **Home page** — lists all your YouTube Music playlists. Click **✕** to hide a playlist.
- **Playlist page** — click any column header to sort. Use the filter box to search by title or artist.
- **Select songs** — check individual songs or use "Select visible" after filtering. A bar appears at the bottom to name and create a new playlist.
- **Save sorted copy** — sort by any column, then click "Save sorted copy…" to duplicate the playlist in that order.
- **Find duplicates** — click "find duplicates" on the home page, select playlists to scan, and see songs that appear in more than one playlist.

## Notes

- `credentials.json` and `token.json` are gitignored — never commit them
- The YouTube Data API has a default quota of 10,000 units/day. Creating playlists with 180+ songs may exceed this limit. Request a quota increase in Google Cloud Console if needed.
- Cached playlist data is stored in the `cache/` directory and expires after 1 hour

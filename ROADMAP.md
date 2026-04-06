# YT Music Playlist Manager — Roadmap

## Completed
- List all YouTube Music playlists
- View songs in a playlist
- Sort by title, artist, duration (ascending/descending)
- Caching — playlist data cached locally for 1 hour, with manual refresh option
- Strip "- Topic" suffix from auto-generated artist channel names
- Hide deleted and private videos from playlist view
- Search/filter — real-time filter by title or artist with visible match count
- Select songs and create new playlist — checkboxes per row, select-all-visible, sticky action bar with playlist name input
- Release Year and Date Added columns — sortable, fetched from YouTube video metadata
- Hide playlists from home page — per-playlist hide/unhide, stored in local hidden.json
- Multi-playlist deduplication — select playlists to scan, find songs appearing in 2+ playlists, results link back to each playlist
- Save sorted copy — one-click button to create a sorted duplicate of any playlist, keeps the original intact

## Planned Features

### 1. Select Songs and Create New Playlist
Select individual songs from an existing playlist and create a new YouTube Music playlist from the selection. Use case: filter all songs by a specific artist (e.g. all U2 songs across a playlist) and save them as their own playlist.

### 2. Push Sort Order Back to YouTube
Reorder the actual playlist on YouTube Music to match the sorted view in the app. Allows permanent sorting that persists in the YouTube Music app.

### 3. Search / Filter Within Playlist
Filter the song list in real time by title or artist without reloading the page. Makes it easy to find songs or select by artist before creating a new playlist.

### 4. Caching
Cache playlist data locally so repeat visits don't re-fetch from the API. Important for large playlists (1000+ songs) where API calls are slow and consume quota.

### 5. Multi-Playlist Deduplication
View songs across multiple playlists and identify duplicates. Useful for cleaning up overlapping playlists.

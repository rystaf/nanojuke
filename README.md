# nanojuke - a simple web frontend for mpd

- search and add music to the queue
- optional javascript
- skip/delete permissions available only on LAN
- todo: associate queued songs and reorder/delete permission to user

works well with ashuffle and consume mode

![screenshot](https://raw.githubusercontent.com/rystaf/nanojuke/main/scrnsht.png?raw=true)

## config

./config.ini or /etc/nanojuke.ini

```ini
[nanojuke]
mpdhost=127.0.0.1
mpdport=6600

pageTitle=nanojuke

# if set, audio player will be shown at top of page
# streamURL=127.0.0.1:8000

# if set, volume link will be shown
# snapcastURL=127.0.0.1:1780

# albumart served from /music/artist/album/Folder.jpg
albumartFilename=Folder.jpg
musicdir=/music
```

## docker

```bash
docker run -it \
  -v $(pwd)/config.ini:/app/config.ini \
  -v /my/music/directory:/music \
  -p 8000:8000 \
  ghcr.io/rystaf/nanojuke:latest
```

## local development

uses websocketd and watchexec to autorefresh page after changes are made

run `make`

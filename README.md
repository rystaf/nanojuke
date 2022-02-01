# nanojuke - a simple web frontend for mpd

Serves a legacy-first website for queueing music
optional javascript
skip/delete permissions only from private ip address
todo: associate queued songs and reorder permission to user session

## config

./config.ini or /etc/nanojuke.ini

```
[mpdjuke]
mpdhost=127.0.0.1
mpdport=6600

pageTitle=nanojuke

# if set audio player will be shown at top of page
#streamURL=127.0.0.1:8000

albumartFilename=Folder.jpg
musicdir=/music
# albumart is expected to be at /music/artist/album/Folder.jpg
```

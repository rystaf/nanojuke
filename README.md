# nanojuke - a simple web frontend for mpd

easily search and add music to the queue
optional javascript
skip/delete permissions only from private ip address
todo: associate queued songs and reorder/delete permission to user

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

# local development

uses websocketd at watchexec to autorefresh page after changes are made
run `make`

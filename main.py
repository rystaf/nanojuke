#!/usr/bin/env python3
from configparser import ConfigParser
from flask import (
    Flask,
    jsonify,
    render_template,
    Response,
    send_file,
    request,
    redirect,
    send_from_directory,
)
from mpd import MPDClient
from mpd.base import ProtocolError, ConnectionError
from math import floor
from ipaddress import ip_address
import time
from os import path
from io import BytesIO
from PIL import Image
import re

app = Flask(__name__)

cli = MPDClient()

config = ConfigParser()
config.read(("config.ini", "/etc/nanojuke.ini"))
cfg = config["nanojuke"]

mpdhost = cfg.get("mpdhost", "127.0.0.1")
mpdport = cfg.get("mpdport", 6600)
musicdir = cfg.get("musicdir")
streamURL = cfg.get("streamURL")
pageTitle = cfg.get("pageTitle", "nanojuke")
albumartFilename = cfg.get("albumartFilename", "Folder.jpg")
updateFreq = cfg.get("updateFreq", 10)  # seconds

cli.connect(mpdhost, mpdport)


@app.template_filter("timef")
def datef(s):
    return time.strftime("%M:%S", time.gmtime(s))


@app.template_filter("artwork")
def artwork(s):
    if "file" not in s or "//" in s["file"]:
        return ""
    return "/art/" + "/".join(s["file"].split("/")[:2]) + ".jpg"


@app.template_filter("filename")
def filename(file):
    return path.basename(file)


@app.template_filter("chr")
def fchr(n):
    return chr(n)


def firstEl(x):
    if isinstance(x, list):
        return firstEl(x)
    return x


def firstLtr(s):
    return re.sub("^THE ", "", firstEl(s).upper())[0]


def alphaOrd(a):
    a = a.upper()
    o = ord(a)
    if o < 65:
        o = 35
    return o


def alphaChr(a):
    if ord(a) < 65:
        a = "#"
    return a


@app.template_filter("firstlist")
def firstlist(l):
    return [
        alphaOrd(firstLtr(firstEl(x["albumartist"])))
        for x in l
        if "albumartist" in x and x["albumartist"]
    ]


@app.template_filter("first")
def first(l):
    return alphaChr(firstLtr(l))


@app.route("/")
@app.route("/nowplaying", methods=["GET", "POST"])
def nowplaying():
    template = (request.path[1:] or "index") + ".html"
    local = (
        app.debug
        or ip_address(request.environ.get("HTTP_X_REAL_IP", "8.8.8.8")).is_private
    )
    try:
        cli.ping()
    except (ProtocolError, UnicodeDecodeError):
        cli.close()
        cli.connect(mpdhost, mpdport)
    except (ConnectionError):
        cli.connect(mpdhost, mpdport)
    playlist = cli.playlistid()
    status = cli.status()
    if request.method == "POST":
        songid = request.form.get("songid")
        song = next((song for song in playlist if song["id"] == songid), None)
        submit = request.form.get("submit")
        if submit == "X":
            if not local:
                return Response(status=401)
            cli.deleteid(songid)
        if submit == "^":
            if song and int(song["pos"]) != int(status["song"]) + 1:
                cli.moveid(songid, int(song["pos"]) - 1)
        if submit == "T":
            if song:
                cli.moveid(songid, int(status["song"]) + 1)
        elif submit == "Add selected songs":
            for n, file in enumerate(request.form.getlist("s"), start=0):
                if not local and (len(playlist[int(status["song"]) :]) + n) > 40:
                    break
                if next((s for s in playlist if s["file"] == file), None):
                    continue
                cli.add(file)
            return redirect("/#c", code=302)
        elif submit == "Skip":
            if not local:
                return Response(status=401)
            cli.next()
            time.sleep(1)
        if request.headers.get("Sec-Fetch-Dest") == "Document":
            return redirect("/", code=302)
    status = cli.status()
    playlist = cli.playlistid()
    percent = 100
    if "duration" in status:
        try:
            percent = floor(float(status["elapsed"]) * 100 / float(status["duration"]))
        except TypeError:
            print("time error")
            print(status)
    song = {}
    if "song" in status:
        song = playlist[int(status["song"])]
    return render_template(
        template,
        status=status,
        playlist=playlist,
        song=song,
        percent=percent,
        updateFreq=updateFreq,
        pageTitle=pageTitle,
        streamURL=streamURL,
        local=local,
    )


@app.route("/search")
@app.route("/results")
def search():
    template = request.path[1:] + ".html"
    try:
        cli.ping()
    except (ProtocolError, UnicodeDecodeError):
        print("weird error")
        cli.close()
        cli.connect(mpdhost, mpdport)
    except ConnectionError:
        print("reconnecting")
        cli.connect(mpdhost, mpdport)
    q = request.args.get("q", "")
    artist = request.args.get("artist", "")
    if not q and not artist:
        try:
            results = sorted(
                cli.list("albumartist"),
                key=lambda x: re.sub("^THE ", "", firstEl(x["albumartist"]).upper()),
            )
        except (ProtocolError):
            results = []
        return render_template(template, results=results)
    results = []
    filters = []
    if artist:
        filters.append('(albumartist == "' + artist + '")')
    if q:
        filters += ["(file contains '" + x + "')" for x in q.split(" ")]
    s = " AND ".join(filters)
    results = sorted(
        cli.search("(" + s + ")"),
        key=lambda x: (
            re.sub("^THE", "", x.get("albumartist", "").upper()),
            x.get("date", ""),
        ),
    )
    return render_template(template, q=q, results=results, artist=artist)


def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, "JPEG", quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/jpeg")


@app.route("/art/<artist>/<album>.jpg")
def art(artist, album):
    p = path.join(musicdir, artist, album, albumartFilename)
    if not path.exists(p):
        # TODO check metadata
        return send_file(
            path.join(path.dirname(__file__), "public", "albumartmissing.png")
        )
    image = Image.open(p)
    return serve_pil_image(image.resize((100, 100)))


if __name__ == "__main__":

    @app.route("/<path:name>")
    def serve_file(name):
        return send_from_directory("public", name)

    @app.route("/debug")
    def getjson():
        try:
            cli.ping()
        except (ProtocolError):
            cli.close()
            cli.connect(mpdhost, mpdpor)
        except (ConnectionError):
            print("reconnecting")
            cli.connect(mpdhost, mpdport)
        status = cli.status()
        playlist = cli.playlistid()
        return jsonify(status=status, playlist=playlist)

    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)

    app.run(host="0.0.0.0", debug=True)

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
from ipaddress import ip_address, ip_network
import time
from os import path
from io import BytesIO
from PIL import Image
from urllib.request import Request, urlopen, urlretrieve
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


def checkIce(url):
    req = Request(url)
    req.add_header('Icy-MetaData', 1)
    response = urlopen(req)
    icy_metaint_header = response.headers.get('icy-metaint')

    regex = r"StreamUrl='(.*?)';"
    reg = re.compile(regex)

    if icy_metaint_header is not None:
        metaint = int(icy_metaint_header)
        read_buffer = metaint+255
        content = response.read(read_buffer)
        header = content[metaint:].decode('utf-8', errors='ignore')
        match = next(re.finditer(regex, header, re.MULTILINE), [])
        if match:
            return match.group(1)
    return ""



@app.template_filter("timef")
def datef(s):
    return time.strftime("%M:%S", time.gmtime(s))


@app.template_filter("artwork")
def artwork(s):
    if "file" not in s:
        return ""
    if "//" in s["file"]:
        return "/art/" + s["file"]
        #return checkIce(s["file"])
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
def firstlist(ltr):
    return [
        alphaOrd(firstLtr(firstEl(x["albumartist"])))
        for x in ltr
        if "albumartist" in x and x["albumartist"]
    ]


@app.template_filter("first")
def first(ltr):
    return alphaChr(firstLtr(ltr))


@app.route("/")
@app.route("/nowplaying", methods=["GET", "POST"])
def nowplaying():
    template = (request.path[1:] or "index") + ".html"
    local = (
        app.debug
        or ip_address(request.environ.get("HTTP_X_REAL_IP", "8.8.8.8")).is_private
        or ip_address(request.environ.get("X-Forwarded-For", "8.8.8.8")).is_private
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
        if submit == "P":
            if not local:
                return Response(status=401)
            if song:
                cli.moveid(songid, int(status["song"]) + 1)
                cli.next()
        if submit == "Play":
            for n, file in enumerate(request.form.getlist("s"), start=0):
                # dont add if already in list
                if not local and (len(playlist[int(status["song"]):]) + n) > 40:
                    break
                if next((s for s in playlist if s["file"] == file), None):
                    continue
                cli.addid(file, int(status["nextsong"])+n)
            cli.next()
            return redirect("/#c", code=302)
        elif submit == "Add":
            for n, file in enumerate(request.form.getlist("s"), start=0):
                # dont add if already in list
                if not local and (len(playlist[int(status["song"]):]) + n) > 40:
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
        if request.headers.get("Sec-Fetch-Mode", "").casefold() != "cors".casefold():
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

@app.route("/playlist/")
@app.route("/playlist/<name>")
def playlist(name=None):
    local = (
        app.debug
        or ip_address(request.environ.get("HTTP_X_REAL_IP", "8.8.8.8")).is_private
        or ip_address(request.environ.get("X-Forwarded-For", "8.8.8.8")).is_private
    )
    template = "playlists.html"
    results = []
    lists = []
    if name:
        results = cli.listplaylistinfo(name)
    else:
        lists = cli.listplaylists()
    if request.args.get("xhr"):
        template = "playlist.html"
    return render_template(template, songs=results, lists=lists, name=name, local=local)

@app.route("/search")
@app.route("/results")
def search():
    local = (
        app.debug
        or ip_address(request.environ.get("HTTP_X_REAL_IP", "8.8.8.8")).is_private
        or ip_address(request.environ.get("X-Forwarded-For", "8.8.8.8")).is_private
    )
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
    return render_template(template, q=q, results=results, artist=artist, local=local)


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

@app.route("/art/<path:subpath>")
def streamart(subpath):
    r = urlopen(checkIce(subpath))
    if r.getcode() != 200:
        return send_file(
            path.join(path.dirname(__file__), "public", "albumartmissing.png")
        )
    return Response(r.read(), headers={'Content-Type': r.info()['Content-Type']})
    #return checkIce(subpath)


@app.route("/<path:name>")
def serve_file(name):
    return send_from_directory("public", name)


if __name__ == "__main__":

    @app.route("/debug")
    def getjson():
        try:
            cli.ping()
        except (ProtocolError):
            cli.close()
            cli.connect(mpdhost, mpdport)
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

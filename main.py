#!/usr/bin/env python3
# coding: utf-8
from flask import Flask,jsonify,render_template,Response,send_file,request,redirect,send_from_directory
import mpd
from math import floor
import time
import os
import io
import asyncio
app = Flask(__name__)

cli = mpd.MPDClient()
cli.connect('mamba',6600)

@app.template_filter('timef')
def datef(s):
    return time.strftime('%M:%S', time.gmtime(s))

@app.template_filter('artwork')
def artwork(s):
    if '//' in s["file"]: return ""
    return "/art/"+"/".join(s["file"].split('/')[:2])+".jpg"

@app.template_filter('chr')
def fchr(n):
    return chr(n)
def alphaOrd(a):
    if isinstance(a,list):
        a = a[0]
    a = a.upper()
    o = ord(a)
    if o < 65:
        o = 35
    return o

def alphaChr(a):
    a = a.upper()
    if ord(a) < 65:
        a = "#"
    return a

@app.template_filter('firstlist')
def firstlist(l):
    return [alphaOrd(x["albumartist"][0]) for x in l if "albumartist" in x and x["albumartist"] and not isinstance(x["albumartist"], list)]
@app.template_filter('first')
def first(l):
    if isinstance(l,list):
        return alphaChr(l[0][0])
    return alphaChr(l[0])

@app.route("/test")
async def test():
    await asyncio.sleep(5)
    return "cool"

@app.route("/")
def index():
    try:
        cli.ping()
    except mpd.base.ConnectionError:
        print('reconnecting')
        cli.connect('mamba', 6600)
    status = cli.status()
    playlist = cli.playlistid()
    percent=100
    results=[]
    q = request.args.get("q", "")
    if len(q) > 0:
        s = " AND ".join(["(file =~ '"+x+"')" for x in q.split(" ")])
        results = cli.search("("+s+")")
    if 'duration' in status:
        percent=floor(float(status["elapsed"])*100/float(status["duration"]))
    #return jsonify(status=status, playlist=playlist)
    return render_template("index.html", q=q, results=results, status=status, playlist=playlist, song=playlist[int(status["song"])], percent=percent)

@app.route("/nowplaying", methods=['GET', 'POST'])
def nowplaying():
    try:
        cli.ping()
    except mpd.base.ConnectionError:
        print('reconnecting')
        cli.connect('mamba', 6600)
    if request.method == "POST":
        for file in request.form.getlist("s"):
            cli.add(file)
        if "redirect" in request.args:
            return redirect("/", code=302)
    status = cli.status()
    playlist = cli.playlistid()
    percent=100
    if 'duration' in status:
        percent=floor(float(status["elapsed"])*100/float(status["duration"]))
    return render_template("nowplaying.html", status=status, playlist=playlist, song=playlist[int(status["song"])], percent=percent)

@app.route("/search")
@app.route("/results")
def search():
    template = request.path[1:]+".html"
    try:
        cli.ping()
    except mpd.base.ConnectionError:
        print('reconnecting')
        cli.connect('mamba', 6600)
    q = request.args.get("q", "")
    artist = request.args.get("artist", "")
    if not q and not artist:
        results = cli.list('albumartist')
        #results = cli.search('(artist contains "Cold")')
        return render_template(template, results=results)
    results = []
    filters = []
    if artist:
        filters.append("(albumartist == '"+artist+"')")
    if q:
        filters += ["(file contains '"+x+"')" for x in q.split(" ")]
    s = " AND ".join(filters)
    results = cli.search("("+s+")")
#    return jsonify(results)
    return render_template(template, q=q, results=results)

@app.route("/art/<artist>/<album>.jpg")
def art(artist, album):
    path = os.path.join('/media','Music',artist, album,"Folder.jpg")
    if not os.path.exists(path):
        return Response(status=404)
    return send_file(path)

if __name__ == '__main__':
    @app.route("/<path:name>")
    def serve_file(name):
        return send_from_directory('public', name)
    app.run(host='0.0.0.0', debug=True)


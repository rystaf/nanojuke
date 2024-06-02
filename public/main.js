if (window.location.hash == '#c') {
  window.close()
  history.replaceState(null, null, ' ')
}
function $(selector) { return document.querySelector(selector); }

function insertResponse(res){
  $("#nowplaying").innerHTML=res.substring(res.indexOf("nowplaying")+12, res.indexOf("<!--now"))
  $("#queue ol").innerHTML=res.substring(res.indexOf("<ol>")+4, res.indexOf("</ol>"))
}

function getNowPlaying() {
  var r = Math.floor(Math.random()*10000)
  request('/nowplaying?r='+r, null, insertResponse)
}

function popup(e) {
  e.preventDefault();
  var win = window.open(e.target.action,'popup','scrollbars=1,width=600,height=600');
  var timer = setInterval(function() {
    if(win.closed) {
      clearInterval(timer);
      getNowPlaying();
    }
  }, 500);
}

function progressUpdate(){
  var elapsed = parseFloat($("#elapsed").getAttribute("data-ms"))
  var duration = parseFloat($("#duration").getAttribute("data-ms"))
  if ((elapsed + 1) >= duration) {
    $("#bar").style.width = "100%"
    $("#elapsed").innerHTML = $("#duration").innerHTML
    return
  }
  elapsed += 1
  $("#elapsed").setAttribute("data-ms", elapsed)
  $("#bar").style.width = Math.floor(elapsed / duration * 100)+"%"
  $("#elapsed").innerHTML = new Date(elapsed * 1000).toISOString().substr(14, 5);
}

function formSubmit(e) {
  e.preventDefault();
  request(e.target.action, "submit="+document.activeElement.value+"&songid="+(e.target.querySelector('input[name=songid')||{}).value, insertResponse)
  return false;
}

function artistClick(e) {
  e.preventDefault();
  request('/results'+e.target.getAttribute('href'),null, function(res) {
    e.target.parentNode.innerHTML = res;
  })
  return false;
}

function playlistClick(e) {
  e.preventDefault();
  request(e.target.getAttribute('href'),null, function(res) {
    e.target.parentNode.innerHTML = res;
  })
  return false;
}

function albumClick(e) {
  e.currentTarget.checked = !e.currentTarget.checked
  var tracks = e.currentTarget.parentNode.getElementsByTagName('input')
  for (var i = 0; i < tracks.length; i++ ) {
    tracks[i].checked = e.currentTarget.checked;
  }
}

function request(theUrl, params, callback) {
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.onreadystatechange = function() { 
    if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
      callback(xmlHttp.responseText);
  }
  var method = "GET"
  if (params) method = "POST"
  xmlHttp.open(method, theUrl, true);
  if (method = "POST")
    xmlHttp.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  xmlHttp.send(params);
}

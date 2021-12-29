if (window.location.hash == '#c') {
  window.close()
  history.replaceState(null, null, ' ')
}
function $(selector) { return document.querySelector(selector); }
function insertResponse(res){
  document.getElementById("nowplaying").innerHTML=res.substring(res.indexOf("nowplaying")+12, res.indexOf("<!--now"))
  document.getElementById("nowplaying").innerHTML=res.substring(res.indexOf("nowplaying")+12, res.indexOf("<!--now"))
  document.querySelector("#queue ol").innerHTML=res.substring(res.indexOf("<ol>")+4, res.indexOf("</ol>"))
}
function getNowPlaying() {
  const r = Math.floor(Math.random()*10000)
  request('/nowplaying?r='+r,null, insertResponse)
}
function popup() {
  const win = window.open('/search','popup','scrollbars=1,width=600,height=600'); 
  const timer = setInterval(function() {
    if(win.closed) {
      clearInterval(timer);
      getNowPlaying();
    }
  }, 500);
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
function albumClick(e) {
  e.currentTarget.checked = !e.currentTarget.checked
  for (let box of e.currentTarget.parentNode.getElementsByTagName('input')) {
    box.checked = e.currentTarget.checked
  }
}
function request(theUrl, params, callback) {
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.onreadystatechange = function() { 
    if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
      callback(xmlHttp.responseText);
  }
  var method = "GET"
  if (params) { 
    params += "&ajax=True"
    method = "POST"
  }
  xmlHttp.open(method, theUrl, true); // true for asynchronous 
  if (method = "POST") {
    xmlHttp.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  }
  xmlHttp.send(params);
}

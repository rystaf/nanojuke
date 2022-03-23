if (typeof WebSocket != 'undefined') {
  var ws = new WebSocket('ws://localhost:8080/');
  var x = false
  ws.onmessage = function() {
    if (x) window.location.reload();
    x = true
  }
}

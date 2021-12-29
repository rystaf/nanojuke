const ws = new WebSocket('ws://localhost:8080/');
let x = false
ws.onmessage = function() {
  if (x) window.location.reload();
  x = true
}

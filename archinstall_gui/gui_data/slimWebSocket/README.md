# slimWebSocket
A wrapper around WebSocket for JavaScript

# Example usecases

```html
<script>
	let socket = new slimWebSocket('wss://obtain.life');
	
	socket.subscribe('certain_key', (json) => {
		console.log('Got data containing certain_key:', json);
	})
	socket.send({"test" : "ping"});
</script>
```

# Features

 * Auto-reconnect
 * Simple message queue (with limited re-send error handling)
 * Type parsing attempt if you're sending a non-string
 * Hook in `socket.socket.addEventListener('message', function(data) {} )` if you need to replace event hooks.

# Installation

```html
<script type="text/javascript">
	let socket = null; // Create a global socket element, initate it with `new slimWebSocket();` later
	
	// Loading JavaScript from a cross-site resource is blocked.
	// But there's nothing stopping us from downloading the script
	// as a text-blob and placing it within the <script> </ script> tags,
	// which causes the browser to parse it, but not as a forrain object.
	//
	// #LoadingScriptsFromGithub

	let xhr = new XMLHttpRequest();
	xhr.open("GET", 'https://raw.githubusercontent.com/Torxed/slimWebSocket/master/slimWebSocket.js', true);
	xhr.onreadystatechange = function() {
		if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
			let script = document.createElement('script');
			script.type = 'text/javascript';
			script.innerHTML = this.responseText;
			document.head.appendChild(script);

			socket = new slimWebSocket();
		}
	}
	xhr.send();
</script>
```

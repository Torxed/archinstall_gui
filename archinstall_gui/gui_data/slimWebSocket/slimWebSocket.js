function isset(obj) {
	if(typeof obj !== 'undefined')
		return true;
	return false;
}

class SimplifiedWebSocket {
	constructor(url='wss://obtain.life', connect_func=null, message_func=null, close_func=null) {
		let self = this; // Plaeholder for anon functions
		this.debug = false;
		this.resource_handlers = {};
		this.timers = {};
		this.send_queue = [];
		this.last_message = null;

		if(!connect_func) {
			connect_func = function(event) {
				//TODO: Debug variable: console.log("WebSocket Connected!");
				self.dispatch_send();
			}
		}
		if(!close_func) {
			close_func = function (event) {
				//TODO: Debug variable: console.log("WebSocket closed!");
				if(self.last_message) {
					self.send_queue.push(self.last_message);
					self.last_message = null;
				}
				self.socket.close();
				self.timers['reconnecting'] = setTimeout(function() {
					self.connect();
				}, 500);
			}
		}
		if(!message_func) {
			message_func = function(event) {
				let data = event.data;
				if(typeof data == "string") {
					try {
						data = JSON.parse(data);
					} catch(err) {
						//console.log(err);
					}

					let parsed = false;
					if (self.debug)
						console.log('Got:', data)

					Object.keys(data).forEach((key) => {
						if(!parsed) {
							if(typeof self.resource_handlers[key] !== 'undefined') {
								//console.log('Trigger on key:', resource_handlers[key])
								self.resource_handlers[key].forEach((f) => {
									parsed = f(data)
								});
								return;
							} else if(typeof self.resource_handlers[data[key]] !== 'undefined') {
								//console.log('Trigger on data:', resource_handlers[data[key]])
								self.resource_handlers[data[key]].forEach((f) => {
									parsed = f(data)
								});
								return;
							}
						} else {
							return;
						}
					})
					if(!parsed)
						console.warn('No handler registered for data:', data)
				}
				//TODO: Debug variable: console.log("WebSocket got data:");
				//TODO: Debug variable: console.log(data);
			}
		}


		this.connect_func = function(event) {
			connect_func.call(self, event);
		}
		this.close_func = function(event) {
			close_func.call(self, event);
		};
		this.message_func = function(event) {
			message_func.call(self, event);
		};

		this.url = url;
		this.connect();
	}


	setTimer(name, func, time=10) {
		this.timers[name] = setInterval(func, time);
	}

	clearTimer(name) {
		if(isset(this.timers[name])) {
			window.clearInterval(this.timers[name]);
			delete(this.timers[name]);
			return true;
		}
		return false;
	}

	dispatch_send() {
		let self = this;
		for (let i=0; i<this.send_queue.length; i++) {
			if (this.socket && this.socket.readyState == 1) {
				let data = this.send_queue.pop();
				this.last_message = data;
				this.socket.send(data);
				if (this.debug)
					console.log('Sent:', data);
			} else {
				this.timers['resend'] = setTimeout(() => {
					self.dispatch_send();
					self.clearTimer('resend');
				}, 25)
			}
		}
	}

	connect() {
		this.socket = new WebSocket(this.url);
		this.socket.addEventListener('open', this.connect_func);
		this.socket.addEventListener('close', this.close_func);
		this.socket.addEventListener('message', this.message_func);
	}

	send(data) {
		if (typeof data == "object")
			data = JSON.stringify(data);
		this.send_queue.push(data);
		this.dispatch_send();
	}

	clear_subscribers() {
		this.resource_handlers = {};
	}

	subscribe(event, func) {
		if(typeof this.resource_handlers[event] === 'undefined')
			this.resource_handlers[event] = [func]
		else 
			this.resource_handlers[event].push(func)
	}

	has_subscription(event) {
		return typeof this.resource_handlers[event] !== 'undefined'
	}

	subscriptions(event) {
		if(typeof this.resource_handlers[event] !== 'undefined') {
			return this.resource_handlers[event].length;
		}
		return 0;
	}
}

window.slimWebSocket = SimplifiedWebSocket;

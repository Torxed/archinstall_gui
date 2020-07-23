# <img src="https://github.com/Torxed/slimWS/raw/master/docs/_static/slimWS.png" alt="drawing" width="200"/>
WebSocket framework writtein in Python.<br>
Works standalone but is preferred as `@upgrader` for [slimHTTP](https://github.com/Torxed/slimHTTP). 

 * slimWS [documentation](https://slimws.readthedocs.io/en/latest)
 * slimWS via slimHTTP's [discord](https://discord.gg/CMjZbwR) server

# Installation

### pypi

    pip install slimWS

### Git it to a project

    git submodule add -b master https://github.com/Torxed/slimWS.git 

*(Or just `git clone https://github.com/Torxed/slimWS.git`)*

# Usage

Most examples will be found under the [documentation](https://slimws.readthedocs.io/en/latest), but here's a quick one.

```python
from slimWS import slimws

server = slimws.host(address='', port=4001)

@server.frame
def parse_frame(self, frame):
	print('Got WebSocket frame:', frame.data)
	yield {'status' : 'successful'}

while 1:
	for event, *event_data in server.poll():
		pass
```
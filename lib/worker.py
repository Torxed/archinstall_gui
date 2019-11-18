import os
from threading import Thread, enumerate as tenum
from select import epoll, EPOLLIN, EPOLLHUP

class _spawn(Thread):
	def __init__(self, func, callback, start_callback=None, *args, **kwargs):
		if not 'worker_id' in kwargs: kwargs['worker_id'] = gen_uid()
		Thread.__init__(self)
		self.func = func
		self.args = args
		self.kwargs = kwargs
		self.callback = callback
		self.data = None
		self.start_callback = start_callback
		self.started = time.time()
		self.ended = None
		self.worker_id = kwargs['worker_id']
		self.status = 'starting'

		if start_callback: start_callback(self, *args, **kwargs)
		self.start()

	def run(self):
		main = None
		for t in tenum():
			if t.name == 'MainThread':
				main = t
				break

		if not main:
			print('Main thread not existing')
			return
		
		self.status = 'running'
		self.data = self.func(*self.args, **self.kwargs)

		self.ended = time.time()
		
		if 'dependency' in self.kwargs:
			pass

		if self.callback:
			self.callback(self, *self.args, **self.kwargs)
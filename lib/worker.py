import os, time
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
		self.start()

	def run(self):
		print('RUNNING')
		main = None
		for t in tenum():
			if t.name == 'MainThread':
				main = t
				break

		if not main:
			print('Main thread not existing')
			return
		
		if 'dependency' in self.kwargs:
			while self.kwargs['dependency'].ended is None:
				time.sleep(0.25)
			if self.kwargs['dependency'].data is None:
				log('Dependency:', self.kwargs['dependency'].func, 'did not exit clearly. There for,', self.func, 'can not execute.', level=2, origin='worker', function='run')
				self.ended = time.time()
				self.status = 'aborted'
				return None

		log(self.func, 'is being called.', level=4, origin='worker', function='run')
		if self.start_callback: self.start_callback(self, *args, **kwargs)
		self.status = 'running'
		self.data = self.func(*self.args, **self.kwargs)

		self.ended = time.time()
		
		if self.data is None:
			log(self.func, 'did not exit clearly.', level=2, origin='worker', function='run')
			self.status = 'failed'
		elif self.callback:
			self.callback(self, *self.args, **self.kwargs)
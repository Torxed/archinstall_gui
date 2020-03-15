import os, time
from threading import Thread, enumerate as tenum
from select import epoll, EPOLLIN, EPOLLHUP

class _spawn(Thread):
	def __init__(self, client, func, callback=None, start_callback=None, error_callback=None, on_output=None, *args, **kwargs):
		if not 'worker_id' in kwargs: kwargs['worker_id'] = gen_uid()
		Thread.__init__(self)
		self.func = func
		self.client = client
		self.args = args
		self.kwargs = kwargs
		self.callback = callback
		self.error_callback = error_callback
		self.on_output = on_output
		self.data = None
		self.start_callback = start_callback
		self.started = time.time()
		self.ended = None
		self.worker_id = kwargs['worker_id']
		self.status = 'starting'
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
		
		if 'dependency' in self.kwargs:
			dependency = self.kwargs['dependency']
			if type(dependency) == str:
				# Dependency is a progress-string. Wait for it to show up.
				while main and main.isAlive() and dependency not in progress or progress[dependency] is None:
					time.sleep(0.25)
				dependency = progress[dependency]

			if type(dependency) == str:
				log(f"{self.func} waited for progress {dependency} which never showed up. Aborting.", level=2, origin='worker', function='run')
				self.ended = time.time()
				self.status = 'aborted'
				return None

			while main and main.isAlive() and dependency.ended is None:
				time.sleep(0.25)

			print('  *** Dependency released for:', self.func)

			if dependency.data is None or not main or not main.isAlive():
				log('Dependency:', dependency.func, 'did not exit clearly. There for,', self.func, 'can not execute.', level=2, origin='worker', function='run')
				self.ended = time.time()
				self.status = 'aborted'
				return None

		print('--->', self.func, 'is now being called')
		log(self.func, 'is being called.', level=4, origin='worker', function='run')
		if self.start_callback: self.start_callback(self, *self.args, **self.kwargs)
		self.status = 'running'
		self.data = self.func(*self.args, **self.kwargs)

		self.ended = time.time()
		
		if self.data is None:
			log(self.func, 'did not exit clearly.', level=2, origin='worker', function='run')
			self.status = 'failed'
			if self.error_callback:
				self.error_callback(self, *self.args, **self.kwargs)
		elif self.callback:
			log(self.func, f'has finished, calling callback {self.callback}.', level=4, origin='worker', function='run')
			self.callback(self, *self.args, **self.kwargs)
import os, time
from threading import Thread, enumerate as tenum
from select import epoll, EPOLLIN, EPOLLHUP

from .helpers import gen_uid
import session

# TODO: Spawn() needs to be reworked a bit, it's cluttered
class spawn(Thread):
	def __init__(self, frame, func, callback=None, start_callback=None, error_callback=None, dependency=None, *args, **kwargs):
		if not 'worker_id' in kwargs: kwargs['worker_id'] = gen_uid()
		if not 'worker' in kwargs: kwargs['worker'] = self
		Thread.__init__(self)
		self.func = func
		self.frame = frame
		self.args = args
		self.kwargs = kwargs
		self.callback = callback
		self.error_callback = error_callback
		self.data = None
		self.start_callback = start_callback
		self.started = time.time()
		self.ended = None
		self.dependency = dependency
		self.worker_id = kwargs['worker_id']
		self.status = 'starting'
		self.log = frame.CLIENT_IDENTITY.server.log
		self.start()

	def run(self):
		main = None
		self.name = str(self.func)
		for t in tenum():
			if t.name == 'MainThread':
				main = t
				break

		if not main:
			print('Main thread not existing')
			return
		
		if self.dependency:
			print('--->', self.func, f'will be called after dependency {self.dependency}')
			while main and main.isAlive() and self.dependency \
				and (type(self.dependency) is str and (self.dependency not in session.steps or (type(session.steps[self.dependency]) is bool and session.steps[self.dependency]) or session.steps[self.dependency].ended is None)) \
				or (type(self.dependency) is spawn and self.dependency.ended is None):

				time.sleep(0.25)

			if type(self.dependency) is str: self.dependency = session.steps[self.dependency]
			
			if self.dependency.data is None or not main or not main.isAlive():
				self.log('Dependency:', self.dependency.func, 'did not exit clearly. There for,', self.func, 'can not execute.')
				self.ended = time.time()
				self.status = 'aborted'
				return None

		self.log(self.func, f'is being called.')
		if self.start_callback: self.start_callback(self)
		self.status = 'running'
		self.data = self.func(self.frame, *self.args, **self.kwargs)

		self.ended = time.time()
		
		if self.data is None:
			print(self.func, 'did not exit clearly.')
			self.log(self.func, 'did not exit clearly.')
			self.status = 'failed'
			if self.error_callback:
				self.error_callback(self)
		elif self.callback:
			self.status = 'finished'
			print(self.func, f'has finished, calling callback {self.callback}.')
			self.log(self.func, f'has finished, calling callback {self.callback}.')
			self.callback(self)
		else:
			self.status = 'finished'
			print(self.func, f'has finished with data: {self.data}')
			self.log(self.func, f'has finished with data: {self.data}')
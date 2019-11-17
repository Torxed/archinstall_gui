import os
from threading import Thread, enumerate as tenum
from select import epoll, EPOLLIN, EPOLLHUP

class _spawn(Thread):
	def __init__(self, cmd, callback=None, start_callback=None, *args, **kwargs):
		if not 'worker_id' in kwargs: kwargs['worker_id'] = gen_uid()
		Thread.__init__(self)
		self.cmd = shlex.split(cmd)
		self.args = args
		self.kwargs = kwargs
		self.callback = callback
		self.pid = None
		self.exit_code = None
		self.started = time.time()
		self.ended = None
		self.worker_id = kwargs['worker_id']
		self.trace_log = b''
		self.status = 'starting'

		user_catalogue = '/home/anton'
		self.cwd = f"{user_catalogue}/ADderall/cache/workers/{kwargs['worker_id']}/"
		self.exec_dir = f'{self.cwd}/{basename(self.cmd[0])}_workingdir'

		if not self.cmd[0][0] == '/':
			log('Worker command is not executed with absolute path, trying to find: {}'.format(self.cmd[0]), origin='spawn', level=5)
			o = b''.join(sys_command('/usr/bin/which {}'.format(self.cmd[0])).exec())
			log('This is the binary {} for {}'.format(o.decode('UTF-8'), self.cmd[0]), origin='spawn', level=5)
			self.cmd[0] = o.decode('UTF-8')

		if not isdir(self.exec_dir):
			os.makedirs(self.exec_dir)

		if start_callback: start_callback(self, *args, **kwargs)
		self.start()

	def __repr__(self, *args, **kwargs):
		return self.trace_log.decode('UTF-8')

	def dump(self):
		return {
			'status' : self.status,
			'worker_id' : self.worker_id,
			'worker_result' : self.trace_log.decode('UTF-8'),
			'started' : self.started,
			'ended' : self.ended,
			'started_pprint' : '{}-{}-{} {}:{}:{}'.format(*time.localtime(self.started)),
			'ended_pprint' : '{}-{}-{} {}:{}:{}'.format(*time.localtime(self.ended)) if self.ended else None,
			'exit_code' : self.exit_code
		}

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
		old_dir = os.getcwd()
		os.chdir(self.exec_dir)
		self.pid, child_fd = pty.fork()
		if not self.pid: # Child process
			# Replace child process with our main process
			os.execv(self.cmd[0], self.cmd)
		os.chdir(old_dir)

		poller = epoll()
		poller.register(child_fd, EPOLLIN | EPOLLHUP)

		alive = True
		last_trigger_pos = 0
		while alive and main and main.isAlive():
			for fileno, event in poller.poll(0.1):
				try:
					output = os.read(child_fd, 8192).strip()
					self.trace_log += output
				except OSError:
					alive = False
					break

				if 'debug' in self.kwargs and self.kwargs['debug'] and len(output):
					log(self.cmd[0],'gave:', output.decode('UTF-8'), origin='spawn', level=4)

				lower = output.lower()
				broke = False
				if 'events' in self.kwargs:
					for trigger in list(self.kwargs['events']):
						if trigger.lower() in self.trace_log[last_trigger_pos:].lower():
							trigger_pos = self.trace_log[last_trigger_pos:].lower().find(trigger.lower())

							if 'debug' in self.kwargs and self.kwargs['debug']:
								log(f"Writing to subprocess {self.cmd[0]}: {self.kwargs['events'][trigger].decode('UTF-8')}", origin='spawn', level=5)

							last_trigger_pos = trigger_pos
							os.write(child_fd, self.kwargs['events'][trigger])
							del(self.kwargs['events'][trigger])
							broke = True
							break

					if broke:
						continue

					## Adding a exit trigger:
					if len(self.kwargs['events']) == 0:
						if 'debug' in self.kwargs and self.kwargs['debug']:
							log(f"Waiting for last command {self.cmd[0]} to finish.", origin='spawn', level=4)

						if bytes(f']$'.lower(), 'UTF-8') in self.trace_log[0-len(f']$')-5:].lower():
							if 'debug' in self.kwargs and self.kwargs['debug']:
								log(f"{self.cmd[0]} has finished.", origin='spawn', level=4)
							alive = False
							break

		self.status = 'done'

		if 'debug' in self.kwargs and self.kwargs['debug']:
			log(f"{self.cmd[0]} waiting for exit code.", origin='spawn', level=5)

		try:
			self.exit_code = os.waitpid(self.pid, 0)[1]
		except ChildProcessError:
			try:
				self.exit_code = os.waitpid(child_fd, 0)[1]
			except ChildProcessError:
				self.exit_code = 1

		if self.exit_code != 0:
			log(f"{self.cmd[0]} did not exit gracefully, exit code {self.exit_code}.", origin='spawn', level=3)
			log(self.trace_log.decode('UTF-8'), origin='spawn', level=3)
		else:
			log(f"{self.cmd[0]} exit nicely.", origin='spawn', level=5)

		self.ended = time.time()
		with open(f'{self.cwd}/trace.log', 'wb') as fh:
			fh.write(self.trace_log)

		worker_history[self.worker_id] = self.dump()

		if 'dependency' in self.kwargs:
			## If this had a dependency waiting,
			## Start it since there's no hook for this yet, the worker has to spawn it's waiting workers.
			module = self.kwargs['dependency']['module']
			print(self.cmd[0],'fullfills a dependency:', module)
			dependency_id = self.kwargs['dependency']['id']
			dependencies[module][dependency_id]['fullfilled'] = True
			dependencies[module][dependency_id]['spawn'](*dependencies[module][dependency_id]['args'], **dependencies[module][dependency_id]['kwargs'], start_callback=_worker_started_notification)

		if self.callback:
			self.callback(self, *self.args, **self.kwargs)
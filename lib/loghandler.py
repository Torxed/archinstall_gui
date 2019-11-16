## Set up logging early on:
import logging
from systemd.journal import JournalHandler

# Custom adapter to pre-pend the 'origin' key.
# TODO: Should probably use filters: https://docs.python.org/3/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
class CustomAdapter(logging.LoggerAdapter):
	def process(self, msg, kwargs):
		return '[{}] {}'.format(self.extra['origin'], msg), kwargs

logger = logging.getLogger() # __name__
journald_handler = JournalHandler()
journald_handler.setFormatter(logging.Formatter('[{levelname}] {message}', style='{'))
logger.addHandler(journald_handler)
logger.setLevel(logging.DEBUG)

class LOG_LEVELS:
	CRITICAL = 1
	ERROR = 2
	WARNING = 3
	INFO = 4
	DEBUG = 5

def _log(*msg, origin='UNKNOWN', level=5, **kwargs):
	if level <= LOG_LEVEL:
		msg = [item.decode('UTF-8', errors='backslashreplace') if type(item) == bytes else item for item in msg]
		msg = [str(item) if type(item) != str else item for item in msg]
		log_adapter = CustomAdapter(logger, {'origin': origin})
		if level <= 1:
			log_adapter.critical(' '.join(msg))
		elif level <= 2:
			log_adapter.error(' '.join(msg))
		elif level <= 3:
			log_adapter.warning(' '.join(msg))
		elif level <= 4:
			log_adapter.info(' '.join(msg))
		else:
			log_adapter.debug(' '.join(msg))

try:
	__builtins__.__dict__['log'] = _log
except:
	__builtins__['log'] = _log
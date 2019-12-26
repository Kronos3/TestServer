from typing import TextIO
import time


class Log:
	BOLD = "\u001b[1m"
	RED = "\u001b[31m" + BOLD
	GREEN = "\u001b[32m" + BOLD
	YELLOW = "\u001b[33m" + BOLD
	RESET = "\u001b[0m"
	
	filename: str
	_print: bool
	file: TextIO
	
	def __init__(self, filename: str, _print: bool):
		self.filename = filename
		self._print = _print
		self.file = open(self.filename, "a+")
	
	@staticmethod
	def get_time():
		return time.strftime("%c", time.localtime())
	
	def raw(self, message):
		if self._print:
			print(message)
		
		self.file.write(message)
		self.file.write("\n")
	
	def info(self, message):
		self.raw(Log.GREEN + "[%s INFO] %s" % (self.get_time(), message) + Log.RESET)
	
	def warn(self, message):
		self.raw(Log.YELLOW + "[%s WARN] %s" % (self.get_time(), message) + Log.RESET)
	
	def error(self, message):
		self.raw(Log.RED + "[%s ERROR] %s" % (self.get_time(), message) + Log.RESET)
	
	def close(self):
		self.file.flush()
		self.file.close()
	
	def test(self, f, name):
		self.info("TEST '%s'..." % name)
		
		try:
			res = f()
		except:
			import traceback
			traceback.print_exc()
			
			res = False
		
		if res:
			self.info("TEST '%s' passed!" % name)
		else:
			self.error("TEST '%s' failed!" % name)
		
		return res

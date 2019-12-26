from typing import Union
import socket
from log import Log
from sock import SockIO


class TestServer:
	sock: socket.socket
	log: Log
	client: Union[SockIO, None]
	
	def __init__(self, port: int):
		self.log = Log("server.log", True)
		self.client = None
		
		
		#addr = socket.getaddrinfo("", port, proto=socket.IPPROTO_TCP)
		
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	
	def exit(self, code: int):
		if code != 0:
			self.log.error("Exiting with ERROR %d" % code)
		else:
			self.log.info("Server shutting down")
		self.log.close()
		
		if self.client is not None:
			self.client.close()
		
		self.sock.shutdown(1)
		self.sock.close()
		exit(code)
	
	def handle_client(self, client: SockIO):
		assert self.log.test(client.send_ack, "ACK")
		assert self.log.test(lambda: client.send_algorithm("LINEAR"), "ALG LINEAR")
		assert self.log.test(lambda: client.send_algorithm("QUADRATIC"), "ALG QUADRATIC")
		assert self.log.test(client.send_arbitrary, "ARBITRARY")
	
	def start(self):
		self.sock.listen()
		try:
			self.loop()
		except KeyboardInterrupt:
			self.log.warn("KeyboardInterrupt()")
			self.exit(0)
	
	def loop(self):
		while True:
			client_sock, addr = self.sock.accept()
			self.log.info(str(addr) + " connected")
			
			self.client = SockIO(client_sock, self.log)
			
			try:
				self.handle_client(self.client)
			except AssertionError:
				self.exit(1)
			
			self.client.close()
			
			self.client = None


def main(argv):
	if len(argv) != 2:
		print("usage %s port" % argv[0])
		return 1
	
	server = TestServer(int(argv[1]))
	server.start()
	
	return 0


if __name__ == "__main__":
	import sys
	exit(main(sys.argv))

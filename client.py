from sock import SockIO
from log import Log
import socket
from typing import Union
import ipaddress


class TestClient:
	client: Union[SockIO, None]
	log: Log
	
	def __init__(self, ip: str, port: int):
		self.log = Log("client.log", True)
		self.client = None
		
		addr = socket.getaddrinfo(ip, port, proto=socket.IPPROTO_TCP)
		
		sock = None
		for address in addr:
			sock = self.connect(address[0], address[1], address[4])
		
		if sock is None:
			self.log.warn("No working connections for %s:%s" % (ip, port))
			self.exit(111)
		self.client = SockIO(sock, self.log)
	
	def connect(self, family, socket_kind, addr):
		self.log.info("Attempting to connect to %s:%d" % addr[:2])
		sock = socket.socket(family, socket_kind, 0)
		try:
			sock.connect(addr)
		except ConnectionRefusedError:
			self.log.warn("Failed to connect to %s:%d" % addr[:2])
			return None
		return sock
	
	def test(self):
		assert self.log.test(self.client.get_ack, "ACK")
		assert self.log.test(self.client.get_algorithm, "ALG LINEAR")
		assert self.log.test(self.client.get_algorithm, "ALG QUADRATIC")
		assert self.log.test(self.client.get_arbitrary, "ARBITRARY")
	
	def run(self):
		try:
			self.test()
		except AssertionError:
			self.exit(1)
	
	def exit(self, code: int):
		if code != 0:
			self.log.error("Exiting with ERROR %d" % code)
		else:
			self.log.info("Server shutting down")
		self.log.close()
		
		if self.client is not None:
			self.client.close()
		
		exit(code)


def main(argv):
	if len(argv) != 3:
		print("usage %s ip port" % argv[0])
		return 1
	
	client = TestClient(argv[1], int(argv[2]))
	client.run()
	
	return 0


if __name__ == "__main__":
	import sys
	exit(main(sys.argv))

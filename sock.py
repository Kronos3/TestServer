import socket
from log import Log
from protocol import Protocol
import random
import struct


class SockIO:
	sock: socket.socket
	log: Log
	
	def __init__(self, sock: socket.socket, log: Log):
		self.sock = sock
		self.log = log
	
	def read_int(self, length=4):
		buf = self.sock.recv(length)
		while len(buf) > 0 and len(buf) != length:
			buf += self.sock.recv(length - len(buf))
		
		if len(buf) == 0:
			return -1
		
		if length == 4:
			return struct.unpack('i', buf)[0]
		else:
			return struct.unpack('l', buf)[0]
	
	def read(self):
		e_raw = self.read_int()
		
		try:
			e = Protocol.ProtoTypes(e_raw)
		except ValueError:
			self.log.error("Invalid request of type %s" % e_raw)
			return None
		
		length = self.read_int(length=8)
		
		if e == Protocol.ProtoTypes.ARBITRARY:
			block = self.sock.recv(Protocol.BLOCK_SIZE)
			
			import time
			start = time.time()
			
			total_read = len(block)
			mib = 1024 * 1024
			
			while total_read < length:
				block = self.sock.recv(Protocol.BLOCK_SIZE)
				total_read += len(block)
			
			end_time = time.time()
			if end_time != start:
				print("%.4f miB/sec" % ((length // mib) / (time.time() - start)))
			else:
				print("No time drop!!")
			
			return Protocol(Protocol.ProtoTypes.ARBITRARY, (length, total_read))
		
		raw_request = self.sock.recv(length)
		while len(raw_request) < length:
			add_on = self.sock.recv(length)
			raw_request += add_on
		
		request = Protocol.parse(e, raw_request)
		return request

	def send(self, request: Protocol):
		for block in request.generate():
			self.sock.send(block)
	
	def validate(self, response: Protocol, expected_type: Protocol.ProtoTypes):
		if response is None:
			return False
		
		if response.e != expected_type:
			self.log.error("Expected type %s got %s" % (expected_type, response.e))
			return False
		
		if not response.validate():
			self.log.error("Invalid %s response" % expected_type)
			return False
		
		return True
	
	def check_valid(self):
		valid = self.read()
		assert self.validate(valid, Protocol.ProtoTypes.VALID)
		
		return bool(valid.args[0])
	
	def send_ack(self):
		request = Protocol.generate_ack()
		
		self.send(request)
		
		return self.check_valid()
	
	def send_algorithm(self, alg: str):
		request = Protocol.generate_algorithm(alg, random.randint(1024, 2048), random.randint(2, 60))
		
		self.send(request)
		return self.check_valid()
	
	def send_arbitrary(self):
		request = Protocol.generate_arbitrary((1024 ** 3) * 40)
		self.send(request)
		return self.check_valid()
	
	def respond(self, valid: bool):
		self.send(Protocol.generate_valid(valid))
	
	def get_ack(self):
		response = self.read()
		valid = self.validate(response, Protocol.ProtoTypes.ACK)
		self.respond(valid)
		return valid
	
	def get_algorithm(self):
		response = self.read()
		valid = self.validate(response, Protocol.ProtoTypes.ALGORITHM)
		self.respond(valid)
		return valid
	
	def get_arbitrary(self):
		response = self.read()
		valid = self.validate(response, Protocol.ProtoTypes.ARBITRARY)
		self.respond(valid)
		return valid
	
	def get_ping(self):
		response = self.read()
		valid = self.validate(response, Protocol.ProtoTypes.PING)
		self.respond(valid)
		return valid
	
	def close(self):
		self.sock.close()

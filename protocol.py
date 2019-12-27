from typing import Union, Tuple
from enum import Enum
import time
import sys


class ProtocolError(IOError):
	pass


class ValidityError(IOError):
	pass


class Algorithm:
	@staticmethod
	def linear(length: int, step: int):
		temp = []
		current = 0
		for i in range(length):
			temp.append(str(current))
			current += step
		
		return ' '.join(temp)
	
	@staticmethod
	def quadratic(length: int, step: int):
		temp = []
		current = 0
		for i in range(length):
			temp.append(str(current ** 2))
			current += step
		
		return ' '.join(temp)
	
	@staticmethod
	def validate(args: Tuple[str]):
		if len(args) != 4:
			raise ProtocolError("Algorithm data looking for %d args got %d" % (4, len(args)))
		
		f = Algorithm.get_function(args[0])
		
		valid_str = f(int(args[1]), int(args[2]))
		return valid_str == args[3]
	
	@staticmethod
	def get_function(name):
		algor_bindings = {
			"LINEAR": Algorithm.linear,
			"QUADRATIC": Algorithm.quadratic
		}
		
		return algor_bindings[name]


class Protocol:
	"""
	Verifies validity of data
	"""
	
	BLOCK_SIZE = 8192
	
	class ProtoTypes(Enum):
		ARBITRARY = 0
		ALGORITHM = 1
		ACK = 2
		PING = 3
		VALID = 4
	
	e: ProtoTypes
	args: Tuple[Union[str, int]]
	
	def __init__(self, _type: Union[ProtoTypes, int], args: Tuple):
		if isinstance(_type, Protocol.ProtoTypes):
			self.e = _type
		else:
			self.e = Protocol.ProtoTypes(_type)
		self.args = args
		
		self.type_bindings = [
			self._arbitrary_data,
			self._algorithm_data,
			self._ack,
			self._ping,
			lambda: True
		]
		
		if self.e.value >= len(self.type_bindings):
			raise ProtocolError("Type %s not valid" % _type)
	
	def _valid(self) -> bool:
		return len(self.args) == 1
	
	def _ping(self) -> bool:
		return len(self.args) == 1
	
	def _ack(self) -> bool:
		return len(self.args) == 0
	
	def _arbitrary_data(self) -> bool:
		if len(self.args) != 2:
			raise ProtocolError("Arbitrary data looking for %d args got %d" % (2, len(self.args)))
		
		length = self.args[0]
		read_len = self.args[1]
		
		return int(length) == read_len
	
	def _algorithm_data(self) -> bool:
		return Algorithm.validate(self.args)
	
	def validate(self):
		return self.type_bindings[self.e.value]()
	
	def generate(self):
		yield self.e.value.to_bytes(4, sys.byteorder)
		if self.e != Protocol.ProtoTypes.ARBITRARY:
			data = ",".join(self.args).encode("utf-8")
			yield len(data).to_bytes(8, sys.byteorder)
			yield data
		else:
			length = int(self.args[0])
			yield length.to_bytes(8, sys.byteorder)
			
			block_n = length // self.BLOCK_SIZE
			for i in range(block_n):
				block = (" " * self.BLOCK_SIZE).encode("utf-8")
				yield block
			
			if length % self.BLOCK_SIZE:
				yield (" " * (length % self.BLOCK_SIZE)).encode("utf-8")
	
	@staticmethod
	def parse(e: ProtoTypes, to_parse: bytes):
		return Protocol(e, tuple(to_parse.decode("utf-8").split(",")) if len(to_parse) != 0 else ())
	
	def __repr__(self):
		data = ",".join(self.args) if self.e != Protocol.ProtoTypes.ARBITRARY else ",%s" % self.args[0]
		
		return "Protocol<%s %s>" % (self.e, data[:10])
	
	def __str__(self):
		return "%d %s" % (self.e.value, ",".join(self.args))
	
	def __eq__(self, other):
		"""Overrides the default implementation"""
		if isinstance(other, Protocol):
			return str(self) == str(other)
		return False
	
	@staticmethod
	def generate_arbitrary(length):
		return Protocol(Protocol.ProtoTypes.ARBITRARY, (str(length),))
	
	@staticmethod
	def generate_algorithm(algorithm: str, length: int, step: int):
		return Protocol(Protocol.ProtoTypes.ALGORITHM, (
			algorithm,
			str(length),
			str(step),
			Algorithm.get_function(algorithm)(length, step)
		))
	
	@staticmethod
	def generate_ping():
		return Protocol(Protocol.ProtoTypes.PING, (str(time.time()),))
	
	@staticmethod
	def generate_ack():
		return Protocol(Protocol.ProtoTypes.ACK, ())
	
	@staticmethod
	def generate_valid(validity: bool):
		return Protocol(Protocol.ProtoTypes.VALID, (str(validity),))

import ctypes
import migration_decision as migration
import netaddr
import socket
import struct
import xen_utils as xen

RECV_BUF_SIZE = 1024
TOKEN_PORT = 8011

class Token(object):
	"""
	Class representing a basic token.
	"""

	def __init__(self, *args):
		"""
		Initialise a token with a list of IPs in int format.
		"""
		#self.buf = ctypes.create_string_buffer(0)
		print len(args)
		print args
		self.buf = ctypes.create_string_buffer(len(args)*4+4)
		i = 0
		for id in args:
			struct.pack_into("I", self.buf, i, id)
			i += 4

	def extract_tuples(self):
		"""
		Extract values from the buffer and return as a tuple of IDs.

		return: Tuples of IDs.
		"""
		size = ctypes.sizeof(self.buf)/4
		ids = tuple()
		i = 0
		for id in range(size-1):
			ids += struct.unpack_from("I", self.buf, i)
			i += 4
		return ids

	def strip_token_tup_head(self, token_tup):
		"""
		Strip leading value from token tuple.

		return: Remaining token tuples minus the head value.
		"""
		return token_tup[1:]

def construct_empty_token():
	return Token()

def construct_large_token_buf():
	return Token(*range(10000))

def repack_token_buf(token_tup):
	return Token(*token_tup)

class DistributedToken(object):
	"""
	Class representing a distributed migration token, which stores both VM IDs
	and highest cost.
	"""
	def __init__(self, *args):
		"""
		Initialise a token with a list of IPs in int format.
		"""
		#self.buf = ctypes.create_string_buffer(0)
		print len(args)
		print args
		self.buf = ctypes.create_string_buffer(len(args)*5+5)
		i = 0
		for id in args:
			struct.pack_into("I", self.buf, i, id[0])
			i += 4
			struct.pack_into("B", self.buf, i, id[1])
			i += 1

	def extract_tuples(self):
		"""
		Extract values from the buffer and return as a tuple of IDs and costs.

		return: Tuples of IDs and costs.
		"""
		size = ctypes.sizeof(self.buf)/5
		ids = tuple()
		i = 0
		for id in range(size-1):
			ids += struct.unpack_from("I", self.buf, i)
			i += 4
			ids += struct.unpack_from("B", self.buf, i)
			i += 1
		return ids

	def strip_token_tup_head(self, token_tup):
		"""
		Strip leading value from token tuple.

		return: Remaining token tuples minus the head value.
		"""
		return token_tup[1:]

def repack_distrib_token_buf(token_tup):
	return DistributedToken(*token_tup)

class TokenServer(object):
	"""
	Server class that waits on a migration token being delivered, and takes
	appropriate action upon receiving a token.
	"""

	def __init__(self, dpthread, lookup, algorithm):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.migration = MigrationDecision(dpthread, lookup)
		self.algorithm = algorithm

	def close(self):
		self.sock.close()

	def receive_token(self, host, port):
		token = ''

		self.sock.bind((host, port))
		self.sock.listen(1)
		while True:
			connection, client = socket.accept()
			try:
				data = connection.recv(1024)
				while len(data):
					token = token + data
					data = connection.recv(1024)
			finally:
				connection.close()
		token_tuples = token.extract_tuples()
		ipaddr = ipv4_int_to_str(token_tuples[0])
		do_algorithm(ipaddr, token_tuples)
		next_vm = ipv4_int_to_str(token_tups[1])
		#token = strip_leading_token_entry(token)
		token_tups = token.strip_token_tup_head(token_tups)
		token = Token(*token_tups)
		forward_token(next_vm, port, token.buf)

	def do_algorithm(self, ipaddr, token):
		"""
		Perform the appropriate migration decision algorithm.

		param ipaddr:	The IP address of the virtual machine to consider
							migration for.
		param token:	The migration token.
		return:			The IP of the destination server to send the VM to;
							None if the VM should not be migrated.
		"""
		hypervisor = None
		if (self.algorithm == 'round_robin'):
			hypervisor = self.migration.round_robin(ipaddr)
		elif (self.algorithm == 'distributed'):
			hypervisor = self.migration.distributed(ipaddr, token)
		else:
			# No such algorithm - don't do a migration!
			return False
		mac = hypervisor[0]
		dst = hypervisor[1]
		doms = xen.xm_get_parsed_doms()
		for dom in doms:
			if (xen.xm_get_mac(dom) == mac):
				live_migrate(dom, dst, None)
				return True

	def forward_token(self, host, port, token):
		"""
		Forward a token to a new host.

		param socket:	Socket to send token on.
		param host:		Next VM to send token to.
		param port:		Port on dst host to send token to.
		param token:	The token to send.
		"""
		self.sock.connect((host, port))
		self.sock.sendall(token)

	def strip_leading_token_entry(self, token):
		"""
		Strip leading ID (the one for the current VM under consideration) from
		the token.

		param token:	Token of VM IDs.
		return:			The token minus the leading (current) entry.
		"""
		# Can this be done within ctypes?
		token_tups = token.extract_tuples()
		token_tups = token.strip_token_tup_head(token_tups)
		token = Token(*token_tups)
		return token


def ipv4_int_to_str(ipaddrint):
	"""
	Wrapper for converting an IPv4 address in int for to a human-readable
	string.

	param ipaddrint:	IP address in int format.
	return:				IP address in str format.
	"""
	if (ipaddrint > 4294967295 or ipaddrint < 0):
		raise netaddr.AddrFormatError("IP address out of range: " + str(ipaddrint))
	addrlist = [str(ipaddrint >> 24 & 0xFF), str(ipaddrint >> 16 & 0xFF),
			   str(ipaddrint >> 8 & 0xFF), str(ipaddrint & 0xFF)]
	addrstr = '.'.join(addrlist)
	return addrstr

def ipv4_str_to_int(ipaddrstr):
	"""
	Wrapper for converting an IPv4 address from a human-readable string to an int.

	param ipaddrstr:	IP address in str format.
	return:				IP address in int format.
	"""
	if (len(ipaddrstr.split('.')) != 4):
		raise netaddr.AddrFormatError("Invalid IPv4 address format: " + ipaddrstr)
	try:
		return int(netaddr.IPAddress(ipaddrstr))
	except netaddr.AddrFormatError, e:
		raise

#def run()
#token = construct_empty_token()
#token = construct_token_buf(1,2,3,4,5,6,7,32,4321423,234,234,45,54456)
#token = construct_large_token_buf()
#token_tup = extract_token_tuples(token)
#print strip_token_head(token_tup)
#socket = init_socket()
#send_token(socket,'192.168.2.1',8005,token)
#close_socket(socket)

import socket
import subprocess as sub
import xen_utils as xen

"""
Classes for dealing with looking up the location of a VM.
"""

class LocationLookupServer():
	"""
	Server class that sits on a hypervisor, waiting on requests on a particular port.
	To enable this, the hypervisor must install a redirect to capture requests sent to VMs, of the form:

		iptables -t nat -A PREROUTING -p tcp --dport <port> -j DNAT --to-destination <hypervisor_ip>
	"""
	BUFF_SIZE = 1024

	def __init__(self, host, port, bridge):
		"""
		Initialise the server.

		param host: Address this server should bind to.
		param port: Port this server should bind to.
		param bridge: dom0-to-domU bridge with an IP address assigned.
		"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.bridge = bridge
		self.socket.bind((host, port))

	def listen(self):
		"""
		Listen for and identify a hypervisor ID request packet, then send IP address of hypervisor in 
		return.
		"""
		self.socket.listen(1)
		request = ''

		while True:
			connection, client = self.socket.accept()
			try:
				data = connection.recv(self.BUFF_SIZE)
				while (len(data) >= self.BUFF_SIZE):
					request = request + data
					data = connection.recv(self.BUFF_SIZE)
				request = request + data
				if (request.startswith('hypervisor_id_request')):
					self.respond(connection)
				elif (request.startswith('hypervisor_capacity_request')):
					self.respond_vm_capacity(connection)
			finally:
				connection.close()
				request = ''

	def close(self):
		"""
		Close the socket when the server is finished listening.
		"""
		self.socket.close()

	def respond_vm_capacity(self, connection):
		"""
		Respond to a hypervisor capacity request by getting number of VMs and
		available memory of the hypervisor.

		param connection: The connection established by a client after the listen() call.
		"""
		num_doms = xen.xm_get_num_doms()
		mem = xen.xm_get_avail_mem()
		connection.sendall('hypervisor_capacity_response ' + str(num_doms) + ' ' + str(mem))

	def respond(self, connection):
		"""
		Respond to a hypervisor ID request by getting IP addr of the hypervisor.

		param connection: The connection established by a client after the listen() call.
		"""
		addr = self.get_addr_ifconfig(self.bridge)
		connection.sendall('hypervisor_id_response ' + addr)

	def get_addr_ifconfig(self, iface):
		"""
		Get the ip address of a given interface and return it as a string.

		param iface:	The interface to retrieve the IP address for.
		return:			The IP address of iface, None if iface doesn't exist.
		"""
		addr = None
		proc = sub.Popen('ifconfig ' + iface, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
		lines = proc.stdout.readlines()
		for line in lines:
			if line.strip().startswith('inet addr:'):
				line = line.strip().split()
				line = line[1].split(':')
				addr = line[1]
		return addr


class LocationLookupClient():
	"""
	Client class that looks up a hypervisor IP address for a particular VM, then consults a
	hard-coded lookup table to identify subnet/subclass location and communication cost.
	"""
	BUFF_SIZE = 1024

	def __init__(self, port, bridge):
		"""
		param port:		Port number to make lookup requests on.
		param bridge:	The Open vSwitch bridge running on this system,
							with an IP address assigned to it.
		"""
		self.lookup = dict()
		self.netmask = ''
		self.port = port
		self.bridge = bridge

	def location_request(self, host):
		"""
		Request the location of a particular VM.

		param host: IP address of the VM of interest.
		return:		IP address of underlying hypervisor.
		"""
		dstaddr = (host, self.port)
		response = ''
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(dstaddr)
		try:
			sock.sendall('hypervisor_id_request')
			data = sock.recv(self.BUFF_SIZE)
			while len(data):
				response = response + data
				data = sock.recv(self.BUFF_SIZE)
			response = response + data
			if (response.startswith('hypervisor_id_response')):
				response = response.split()
				response = response[1]
			else:
				response = None
		finally:
			sock.close()
				
		return response

	def capacity_request(self, host):
		"""
		Request the capacity of a particular hypervisor.

		param host: IP address of the VM of interest.
		return:		Number of VMs and available mem on hypervisor.
		"""
		dstaddr = (host, self.port)
		response = ''
		capacity = []
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(dstaddr)
		try:
			sock.sendall('hypervisor_capacity_request')
			data = sock.recv(self.BUFF_SIZE)
			while len(data):
				response = response + data
				data = sock.recv(self.BUFF_SIZE)
			response = response + data
			if (response.startswith('hypervisor_capacity_response')):
				response = response.split()
				capacity.append(response[1])
				capacity.append(response[2])
			else:
				capacity = None
		finally:
			sock.close()
				
		return capacity

	def location_lookup_init(self, file):
		"""
		Initialise a hard-coded lookup file.

		param file: The file to read subnet data in from.
		"""
		f = open(file, 'r')
		line = f.readline()
		while line:
			if (line.startswith('netmask')):
				line = line.split()
				self.netmask = line[1]
			elif (line.startswith('subnets')):
				line = line.split()
				if (self.lookup.has_key(line[1])):
					self.lookup[line[1]][line[2]] = int(line[3])
				else:
					self.lookup[line[1]] = {line[2]: int(line[3])}
			line = f.readline()
		f.close()

	def location_lookup(self, src, dst):
		"""
		Consult the lookup file to match a hypervisor IP address to a subnet.

		param src:	The address of the current hypervisor.
		param dst:	The address of the destination hypervisor.
		return:		The cost of communicating with that subnet/subclass/hypervisor;
						-1 if subnet is not in the lookup file.
		"""
		if self.lookup.has_key(src):
			if self.lookup[src].has_key(dst):
				return self.lookup[src][dst]
		return -1

	def get_own_hypervisor_addr(self, iface):
		"""
		Get the ip address of a given interface and return it as a string.

		param iface:	The interface to retrieve the IP address for.
		return:			The IP address of iface, None if the iface doesn't exist.
		"""
		addr = None
		proc = sub.Popen('ifconfig ' + iface, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
		lines = proc.stdout.readlines()
		for line in lines:
			if line.strip().startswith('inet addr:'):
				line = line.strip().split()
				line = line[1].split(':')
				addr = line[1]
		return addr

	def communication_cost(self, addr):
		"""
		Perform a location request, get the response, and then look up the
		communication cost. 

		param addr:	IP address of the VM to retrieve a cost for
		return:		The cost of communication from the current host to addr.
		"""
		src = self.get_own_hypervisor_addr(self.bridge)
		if (src is None):
			return None, None
		hypervisor = self.location_request(addr)
		if (hypervisor is None):
			return None, None
		else:
			return hypervisor, self.location_lookup(src, hypervisor)


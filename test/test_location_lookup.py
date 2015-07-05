import add_to_sys_path
import location_lookup as location
import unittest
from thread import start_new_thread

#client = location.LocationLookupClient()
#addr = client.location_request('localhost', 8023)
#print addr
#client.location_lookup_init('../data/costs.txt')
#print client.lookup
#print client.location_lookup(addr)

HOST = '127.0.0.1'
PORT = 8010
LOOKUP_FILE = '../data/costs_test.txt'
LOCALHOST_LOOKUP_FILE = '../data/costs_localhost.txt'
BRIDGE = 'lo'

class TestLocationLookupServerIpRetrieve(unittest.TestCase):
	""" Test the location lookup server IP retrieval capabilities. """

	def setUp(self):
		self.server = location.LocationLookupServer(HOST, PORT, BRIDGE)

	def tearDown(self):
		self.server.close()

	def test_get_addr(self):
		""" Test ability to look up own IP address. """
		addr = self.server.get_addr_ifconfig(BRIDGE)
		self.assertEquals(addr, HOST)

	def test_get_own_ip_no_iface(self):
		""" Test that lookup up a non-existant interface returns an IP address of None. """
		addr = self.server.get_addr_ifconfig('ethNone')
		self.assertEquals(addr, None)

class TestLocationLookupServerLookup(unittest.TestCase):
	""" Test the location lookup server listening and responding capabilites. """

	def setUp(self):
		self.server = location.LocationLookupServer(HOST, PORT, BRIDGE)
		self.lookup = location.LocationLookupClient(PORT, BRIDGE)

	def tearDown(self):
		self.server.close()

	def test_listen(self):
		""" Test that the server responds to appropriate ID requests. """
		thread = start_new_thread(self.server.listen, ())
		addr = self.lookup.location_request('127.0.0.1')
		self.assertEquals(addr, '127.0.0.1')

class TestLocationLookupClientFiles(unittest.TestCase):
	""" Test the location lookup client file handling and lookup capabilities. """

	def setUp(self):
		self.lookup = location.LocationLookupClient(PORT, BRIDGE)

	def test_lookup_init(self):
		""" Test that reading static lookup file works without unexpected
			 errors. """
		self.lookup.location_lookup_init(LOOKUP_FILE)

	def test_location_lookup_colocated(self):
		""" Test that a basic lookup of the same IP returns the expected cost of 0. """
		self.lookup.location_lookup_init(LOOKUP_FILE)
		cost = self.lookup.location_lookup('192.168.100.101', '192.168.100.101')
		self.assertEquals(cost, 0)

	def test_location_lookup_different(self):
		""" Test that a basic lookup of two different IPs returns the expected costs. """
		self.lookup.location_lookup_init(LOOKUP_FILE)
		cost = self.lookup.location_lookup('192.168.100.101', '192.168.100.102')
		self.assertEquals(cost, 2)

	def test_location_lookup_different_reverse(self):
		""" Test that reversing the IPs in test_location_lookup_different returns
			 the same result. """
		self.lookup.location_lookup_init(LOOKUP_FILE)
		cost = self.lookup.location_lookup('192.168.100.102', '192.168.100.101')
		self.assertEquals(cost, 2)

	def test_location_lookup_invalid_src(self):
		""" Test that looking up an unknown src IP results in a return value of -1. """
		self.lookup.location_lookup_init(LOOKUP_FILE)
		cost = self.lookup.location_lookup('192.168.100.110', '192.168.100.101')
		self.assertEquals(cost, -1)

	def test_location_lookup_invalid_src(self):
		""" Test that looking up an unknown dst IP results in a return value of -1. """
		self.lookup.location_lookup_init(LOOKUP_FILE)
		cost = self.lookup.location_lookup('192.168.100.101', '192.168.100.110')
		self.assertEquals(cost, -1)

class TestLocationLookupClientLookup(unittest.TestCase):
	""" Test the location lookup client ability to query itself and other hosts for IPs. """

	def setUp(self):
		self.lookup = location.LocationLookupClient(PORT, BRIDGE)

	def test_get_own_ip(self):
		""" Test ability to look up own IP address. """
		addr = self.lookup.get_own_hypervisor_addr(BRIDGE)
		self.assertEquals(addr, HOST)

	def test_get_own_ip_no_iface(self):
		""" Test that lookup up a non-existant interface returns an IP address of None. """
		addr = self.lookup.get_own_hypervisor_addr('ethNone')
		self.assertEquals(addr, None)

if (__name__ == '__main__'):
	unittest.main()


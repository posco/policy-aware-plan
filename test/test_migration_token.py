import add_to_sys_path
import migration_token as token
import netaddr
import unittest

class TestToken(unittest.TestCase):
	""" Test the token object class. """

	def test_empty_token_size(self):
		""" Test that creating and extracting an empty token results in no
			 tuples. """
		tok = token.Token()
		tok_tuples = tok.extract_tuples()
		self.assertEqual(len(tok_tuples), 0)

	def test_single_token_size(self):
		""" Test that creating and extracting a single tuple from a basic token
			 results in a token of size 1. """
		tok = token.Token(123456789)
		tok_tuples = tok.extract_tuples()
		self.assertEqual(len(tok_tuples), 1)

	def test_single_token_value(self):
		""" Test that creating and extracting a single tuple from a basic token
			 results in the same value returned. """
		tok = token.Token(123456789)
		tok_tuples = tok.extract_tuples()
		self.assertEqual(tok_tuples[0], 123456789)

	def test_multiple_tokens_size(self):
		""" Test that creating multiple token entries and extracting them returns
			 the expected number of tuples. """
		tok = token.Token(1, 2)
		tok_tuples = tok.extract_tuples()
		self.assertEqual(len(tok_tuples), 2)

	def test_multiple_tokens_value(self):
		""" Test that creating multiple token entries and extracting them returns
			 the expected number of tuples. """
		tok = token.Token(1, 2)
		tok_tuples = tok.extract_tuples()
		self.assertEqual(tok_tuples, (1, 2))

	def test_multiple_tokens_value(self):
		""" Test that creating multiple token entries and extracting them returns
			 the expected number of tuples. """
		tok = token.Token(1, 2)
		tok_tuples = tok.extract_tuples()
		self.assertEqual(tok_tuples, (1, 2))

	def test_empty_token_strip(self):
		""" Test that attempting to strip the head off an empty token still
			 results in an empty token. """
		tok = token.Token()
		tok_tuples = tok.extract_tuples()
		tok_tuples = tok.strip_token_tup_head(tok_tuples)
		self.assertEqual(len(tok_tuples), 0)

	def test_single_token_strip(self):
		""" Test that stripping a single entry from a token results in no entries. """
		tok = token.Token(123456789)
		tok_tuples = tok.extract_tuples()
		tok_tuples = tok.strip_token_tup_head(tok_tuples)
		self.assertEqual(len(tok_tuples), 0)

	def test_multiple_token_strip_size(self):
		""" Test that stripping a single token entry results in only one entry being
			 removed. """
		tok = token.Token(1, 2)
		tok_tuples = tok.extract_tuples()
		tok_tuples = tok.strip_token_tup_head(tok_tuples)
		self.assertEqual(len(tok_tuples), 1)

	def test_multiple_token_strip(self):
		""" Test that stripping a single token entry removes the leading entry. """
		tok = token.Token(1, 2)
		tok_tuples = tok.extract_tuples()
		tok_tuples = tok.strip_token_tup_head(tok_tuples)
		self.assertEqual(tok_tuples, (2,))

	def test_recurring_token_strip(self):
		""" Test that two subsequent strip operations removes the expected number
			 of entries. """
		tok = token.Token(1, 2, 3)
		tok_tuples = tok.extract_tuples()
		tok_tuples = tok.strip_token_tup_head(tok_tuples)
		tok_tuples = tok.strip_token_tup_head(tok_tuples)
		self.assertEqual(tok_tuples, (3,))


class TestIpIntToStr(unittest.TestCase):
	""" Test convenience wrapper for IP int to str format conversion. """

	def test_zero(self):
		""" Test that a value of zero gives us a network of 0.0.0.0. """
		ipaddrint = 0
		ipaddrstrexp = '0.0.0.0'
		ipaddrstr = token.ipv4_int_to_str(ipaddrint)
		self.assertEqual(ipaddrstr, ipaddrstrexp)

	def test_uint_max(self):
		""" Test that a 32-bit UINT MAX value returns 255.255.255.255 """
		ipaddrint = 4294967295
		ipaddrstrexp = '255.255.255.255'
		ipaddrstr = token.ipv4_int_to_str(ipaddrint)
		self.assertEqual(ipaddrstr, ipaddrstrexp)

	def test_normal(self):
		""" Test that a normal IPv4 int value gives us the expected result. """
		ipaddrint = 3221225985
		ipaddrstrexp = '192.0.2.1'
		ipaddrstr = token.ipv4_int_to_str(ipaddrint)
		self.assertEqual(ipaddrstr, ipaddrstrexp)

	def test_negative(self):
		""" Test a negative int value. """
		ipaddrint = -1
		self.assertRaises(netaddr.AddrFormatError, lambda: token.ipv4_int_to_str(ipaddrint))

	def test_out_of_range(self):
		""" Test a positive value out of 32-bit range. """
		ipaddrint = 4294967296
		self.assertRaises(netaddr.AddrFormatError, lambda: token.ipv4_int_to_str(ipaddrint))

class TestIpStrToInt(unittest.TestCase):
	""" Test convenience wrapper for IP str to int format conversion. """

	def test_zeros(self):
		""" Test that an IP of 0.0.0.0 has an int value of 0. """
		ipaddrstr = '0.0.0.0'
		ipaddrintexp = 0
		ipaddrint = token.ipv4_str_to_int(ipaddrstr)
		self.assertEqual(ipaddrint, ipaddrintexp)

	def test_max(self):
		""" Test than an IP of 255.255.255.255 has an int value of 4294967295. """
		ipaddrstr = '255.255.255.255'
		ipaddrintexp = 4294967295
		ipaddrint = token.ipv4_str_to_int(ipaddrstr)
		self.assertEqual(ipaddrint, ipaddrintexp)

	def test_normal(self):
		""" Test that a normal IPv4 address gives us the expected int result. """
		ipaddrstr = '10.2.0.1'
		ipaddrintexp = 167903233
		ipaddrint = token.ipv4_str_to_int(ipaddrstr)
		self.assertEqual(ipaddrint, ipaddrintexp)

	def test_random_string(self):
		""" Test that passing a random string causes an exception to be raised. """
		ipaddrstr = 'Bacon'
		self.assertRaises(netaddr.AddrFormatError, lambda: token.ipv4_str_to_int(ipaddrstr))

	def test_invalid_octet(self):
		""" Test that an IP address with an octet out of range causes an exception
			to be raised. """
		ipaddrstr = '255.255.255.256'
		self.assertRaises(netaddr.AddrFormatError, lambda: token.ipv4_str_to_int(ipaddrstr))

	def test_too_few_octets(self):
		""" Test that an IP address with too few octets causes an exception to be
			raised"""
		ipaddrstr = '192.168.1'
		self.assertRaises(netaddr.AddrFormatError, lambda: token.ipv4_str_to_int(ipaddrstr))

	def test_too_many_octets(self):
		""" Test that an IP address with too many octets causes an exception to be
			raised"""
		ipaddrstr = '192.168.1.1.1'
		self.assertRaises(netaddr.AddrFormatError, lambda: token.ipv4_str_to_int(ipaddrstr))

if (__name__ == '__main__'):
	unittest.main()


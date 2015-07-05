import datetime
import dpctl
import threading
import time

class DpReadClass(threading.Thread):
	"""
	Class wrapping DpCtl in a thread, for continual updating of flow throughput.
	"""

	def __init__(self, interval=1, bridge='xenbr0'):
		"""
		Initialise the DpCtl thread.

		param interval:	Polling interval for reading datapath flow data. Default: 1 sec.
		param bridge:	Bridge to read datapath flow data from. Default: 'xenbr0'.
		"""
		super(DpReadClass, self).__init__()
		self.interval = interval
		self.bridge = bridge
		self.doLoop = True
		self.lock = threading.Lock()
		self.dpctl = dpctl.DpCtl(bridge)

	def run(self):
		"""
		Continually loop and update flow data.
		"""
		while self.doLoop:
			lines = self.dpctl.get_dp_flows()
			self.lock.acquire()
			self.dpctl.update_entries(lines)
			self.lock.release()
			time.sleep(self.interval)

	def terminate(self):
		"""
		Tell the DpCtl thread to terminate.
		"""
		self.doLoop = False

	def get_mac_by_ip(self, ipaddr):
		"""
		Get the MAC address associated with the given IP address.

		param ipaddr:	IP address to retrieve associated MAC address for.
		return:			MAC address.
		"""
		self.lock.acquire()
		ip = self.dpctl.get_mac_by_ip(ipaddr)
		self.lock.release()
		return ip

	def lock_access_get_entries(self, funct, ipaddr):
		"""
		Simple wrapper function to marshal access to DpCtl, to ensure that flow
		data isn't corrupted by access via multiple threads.

		param funct:	The function to be called to access flow data.
		param ipaddr:	The IP address to retrieve flow data for.
		return:			Flow entries corresponding to the given IP address.
		"""
		self.lock.acquire()
		entries_copy = funct(ipaddr)
		self.lock.release()
		return entries_copy

	def get_entries_by_src_ip(self, srcIp):
		"""
		Retrieve source entries by IP address.

		param srcIp:	Source IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		funct = self.dpctl.get_src_flows_by_ip
		return self.lock_access_get_entries(funct, srcIp)

	def copy_entries_by_src_ip(self, srcIp):
		"""
		Retrieve a copy of source entries by IP address.

		param srcIp:	Source IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		funct = self.dpctl.copy_src_flows_by_ip
		return self.lock_access_get_entries(funct, srcIp)

	def copy_and_reset_entries_by_src_ip(self, srcIp):
		"""
		Retrieve a copy of source entries by IP address and reset flows.

		param srcIp:	Source IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		funct = self.dpctl.copy_and_reset_src_flows_by_ip
		return self.lock_access_get_entries(funct, srcIp)

	def get_entries_by_dst_ip(self, dstIp):
		"""
		Retrieve destination entries by IP address.

		param dstIp:	Destination IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		funct = self.dpctl.get_dst_flows_by_ip
		return self.lock_access_get_entries(funct, dstIp)

	def copy_entries_by_dst_ip(self, dstIp):
		"""
		Retrieve a copy of destination entries by IP address.

		param dstIp:	Destination IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		funct = self.dpctl.copy_dst_flows_by_ip
		return self.lock_access_get_entries(funct, dstIp)

	def copy_and_reset_entries_by_dst_ip(self, dstIp):
		"""
		Retrieve a copy of destination entries by IP address and reset flows.

		param dstIp:	Destination IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		funct = self.dpctl.copy_and_reset_dst_flows_by_ip
		return self.lock_access_get_entries(funct, dstIp)
"""
thread = DpReadClass()
thread.start()
time.sleep(2)
print thread.get_entries_by_src_ip('192.168.2.1')
print thread.get_entries_by_dst_ip('192.168.2.1')
src_copy = thread.copy_entries_by_src_ip('192.168.2.1')
print 'src_copy: ' + str(src_copy)
dst_copy = thread.copy_entries_by_dst_ip('192.168.2.1')
print 'dst_copy: ' + str(dst_copy)
print 'at reset: ' + str(thread.copy_and_reset_entries_by_src_ip('192.168.2.1'))
print 'at reset: ' + str(thread.copy_and_reset_entries_by_dst_ip('192.168.2.1'))
time.sleep(120)
print thread.get_entries_by_src_ip('192.168.2.1')
print thread.get_entries_by_dst_ip('192.168.2.1')
print 'src_copy: ' + str(src_copy)
print 'dst_copy: ' + str(dst_copy)
thread.terminate()
thread.join()
"""

from datetime import datetime
import array
import os
import sys
import subprocess as sub

class FlowEntry(object):
	"""
	Class representing a single piece of flow data.
	"""

	def __init__(self, src_mac, dst_mac, src_ip, dst_ip, bytes):
		"""
		Initialise a flow entry.

		param srcMac:	MAC address of src host.
		param dstMac:	MAC address of dst host.
		param srcIp:	IP address of src host.
		param dstIp:	IP address of dst host.
		param bytes:	Bytes transferred during the measurement period this
						entry is taken from.
		"""
		self.srcMac = src_mac
		self.dstMac = dst_mac
		self.srcIp = src_ip
		#self.srcPort = src_port
		self.dstIp = dst_ip
		#self.dstPort = dst_port
		self.bytes = bytes

class Flows(object):
	"""
	Class representing a set of flows.
	"""

	def __init__(self):
		"""
		Initialise an empty flowset.
		"""
		self._src = dict()
		self._dst = dict()
		#self.tmp_src = []
		#self.tmp_dst = []

	def has_flow_history(self, ipaddr, flowset):
		"""
		Check if there are any existing src flow entries for the given IP address.

		param ipaddr:	IP address to query against src flows.
		param flowset:	The src or dst flowset.
		return:			True if an entry already exists for the given IP address,
						False otherwise.
		"""
		return flowset.has_key(ipaddr)

	def has_src_flow_history(self, ipaddr):
		"""
		Check if there are any existing src flow entries for the given IP address.

		param ipaddr:	IP address to query against src flows.
		return:			True if an entry already exists for the given IP address,
						False otherwise.
		"""
		return self._src.has_key(ipaddr)

	def has_dst_flow_history(self, ipaddr):
		"""
		Check if there are any existing dst flow entries for the given IP address.

		param ipaddr:	IP address to query against dst flows.
		return:			True if an entry already exists for the given IP address,
						False otherwise.
		"""
		return self._dst.has_key(ipaddr)

	def has_src_flow_dst_entry(self, srcIp, dstIp):
		"""
		Check if there are any existing flows from srcIp to dstIp.

		param srcIp:	IP address to query against src flows.
		param dstIp:	IP address to query as a src flow end-point.
		return:			True if an entry already exists for the given IP addresses,
						False otherwise.
		"""
		if not self._src.has_key(srcIp):
			return False
		else:
			return self._src[srcIp][1].has_key(dstIp)

	def has_dst_flow_src_entry(self, dstIp, srcIp):
		"""
		Check if there are any existing flows from srcIp to dstIp.

		param srcIp:	IP address to query against src flows.
		param dstIp:	IP address to query as a src flow end-point.
		return:			True if an entry already exists for the given IP addresses,
						False otherwise.
		"""
		if not self._dst.has_key(dstIp):
			return False
		else:
			return self._dst[dstIp][1].has_key(srcIp)

	def add_new_src_flow(self, entry):
		"""
		Add a new src flow entry into the flowset.

		param entry: Flow entry containing flow data.
		"""
		self._src[entry.srcIp] = [entry.srcMac, dict(), datetime.now()]
		self._src[entry.srcIp][1][entry.dstIp] = [entry.bytes, 0]

	def add_new_dst_flow(self, entry):
		"""
		Add a new dst flow entry into the flowset.

		param entry: Flow entry containing flow data.
		"""
		self._dst[entry.dstIp] = [entry.dstMac, dict(), datetime.now()]
		self._dst[entry.dstIp][1][entry.srcIp] = [entry.bytes, 0]
	
	def add_new_src_dst_flow(self, entry):
		"""
		Add a new dst flow entry for a src IP with existing flows.
		
		param entry: Flow entry containing flow data.
		"""
		if self.has_src_flow_history(entry.srcIp):
			self._src[entry.srcIp][1][entry.dstIp] = [entry.bytes, 0]

	def add_new_dst_src_flow(self, entry):
		"""
		Add a new src flow entry for a dst IP with existing flows.
		
		param entry: Flow entry containing flow data.
		"""
		if self.has_dst_flow_history(entry.dstIp):
			self._dst[entry.dstIp][1][entry.srcIp] = [entry.bytes, 0]

	def increment_src_flow(self, entry):
		"""
		Increment an existing src-to-dst flow entry with an updated byte count.

		param entry: Flow entry containing flow data.
		"""
		if (self.has_src_flow_dst_entry(entry.srcIp, entry.dstIp)):
			flow_bytes = self._src[entry.srcIp][1][entry.dstIp]
			if flow_bytes[0] <= entry.bytes:
				# Flow count has incremented beyond our current tally;
				# overwrite with new tally.
				flow_bytes[0] = entry.bytes
			else:
				# A new flow has been started but a previous flow exists;
				# update current tally and offset our previous bytes to account
				# for the new flow.
				flow_bytes[1] = flow_bytes[1] + flow_bytes[0]
				flow_bytes[0] = entry.bytes

	def increment_dst_flow(self, entry):
		"""
		Increment an existing dst-to-src flow entry with an updated byte count.

		param entry: Flow entry containing flow data.
		"""
		if (self.has_dst_flow_src_entry(entry.dstIp, entry.srcIp)):
			flow_bytes = self._dst[entry.dstIp][1][entry.srcIp]
			if flow_bytes[0] <= entry.bytes:
				# Flow count has incremented beyond our current tally;
				# overwrite with new tally.
				flow_bytes[0] = entry.bytes
			else:
				# A new flow has been started but a previous flow exists;
				# update current tally and offset our previous bytes to account
				# for the new flow.
				flow_bytes[1] = flow_bytes[1] + flow_bytes[0]
				flow_bytes[0] = entry.bytes

	def reset_src_flow(self, srcIp, dstIp):
		"""
		Reset a src flow so that further updates will be calculated against the
		value at the most recent reading.

		param srcIp:	Source IP address of the flow.
		param dstIp:	Destination IP address of the flow.
		"""
		if (self.has_src_flow_dst_entry(srcIp, dstIp)):
			flow_bytes = self._src[srcIp][1][dstIp]
			flow_bytes[1] = 0 - flow_bytes[0]

	def reset_src_flows(self, srcIp):
		"""
		Reset all flows for a src IP address so that further updates will be
		calculated against the value at the most recent reading.

		param srcIp:	Source IP address of the flow.
		"""
		if (self.has_src_flow_history(srcIp)):
			for key in self._src[srcIp][1].keys():
				flow_bytes = self._src[srcIp][1][key]
				flow_bytes[1] = 0 - flow_bytes[0]
			self._src[srcIp][2] = datetime.now()

	def reset_dst_flow(self, dstIp, srcIp):
		"""
		Reset a src flow so that further updates will be calculated against the
		value at the most recent reading.

		param dstIp:	Destination IP address of the flow.
		param srcIp:	Source IP address of the flow.
		"""
		if (self.has_dst_flow_src_entry(dstIp, srcIp)):
			flow_bytes = self._dst[dstIp][1][srcIp]
			flow_bytes[1] = 0 - flow_bytes[0]

	def reset_dst_flows(self, dstIp):
		"""
		Reset all flows for a dst IP address so that further updates will be
		calculated against the value at the most recent reading.

		param dstIp:	Destination IP address of the flow.
		"""
		if (self.has_dst_flow_history(dstIp)):
			for key in self._dst[dstIp][1].keys():
				flow_bytes = self._dst[dstIp][1][key]
				flow_bytes[1] = 0 - flow_bytes[0]
			self._dst[dstIp][2] = datetime.now()

	def update_src_flow(self, entry):
		"""
		Take appropriate action to update a src flow, which may involve adding
		a new entry or updating an existing entry.

		param entry:	Flow entry containing flow data.
		"""
		if self.has_src_flow_history(entry.srcIp):
			if self.has_src_flow_dst_entry(entry.srcIp, entry.dstIp):
				self.increment_src_flow(entry)
			else:
				self.add_new_src_dst_flow(entry)
		else:
			self.add_new_src_flow(entry)

	def update_dst_flow(self, entry):
		"""
		Take appropriate action to update a dst flow, which may involve adding
		a new entry or updating an existing entry.

		param entry:	Flow entry containing flow data.
		"""
		if self.has_dst_flow_history(entry.dstIp):
			if self.has_dst_flow_src_entry(entry.dstIp, entry.srcIp):
				self.increment_dst_flow(entry)
			else:
				self.add_new_dst_src_flow(entry)
		else:
			self.add_new_dst_flow(entry)

	def update_flows(self, entry):
		"""
		Update both the src and dst flow entries, using the given flow entry.

		param entry:	Flow entry containing flow data.
		"""
		self.update_src_flow(entry)
		self.update_dst_flow(entry)

		#dstIp, proto, srcPort, dstPort, currentBytes, offsetBytes
#		src_entry_list = array.array('I', [entry.dstIp, 0, 0, 0, entry.bytes, 0])
#		if not self._src.has_key(entry.srcIp):
#			self._src[entry.srcIp] = [entry.srcMac]
#		self._src[entry.srcIp].append(src_entry_list)

#		dst_entry_list = array.array('I', [entry.srcIp, 0, 0, 0, entry.bytes, 0])
#		if not self._dst.has_key(entry.dstIp):
#			self._dst[entry.dstIp] = [entry.dstMac]
#		self._dst[entry.dstIp].append(dst_entry_list)
		
#		src_entry_list = array.array('I', [1, 1, entry.srcIp, entry.dstIp, entry.bytes])
#		self.tmp_src.append(src_entry_list)
#		self.tmp_src.append(1)
#		self.tmp_src.append(1)
#		self.tmp_src.append(entry.srcIp)
#		self.tmp_src.append(entry.dstIp)
#		self.tmp_src.append(entry.bytes)
#		print sys.getsizeof(src_entry_list)
#		dst_entry_list = array.array('I', [1, 1, entry.srcIp, entry.dstIp, entry.bytes])
#		self.tmp_src.append(src_entry_list)
#		dst_flow_entry = FlowEntry(entry.srcMac, entry.dstMac,
#							  entry.srcIp, entry.dstIp, entry.bytes)
#		self.tmp_dst.append(dst_entry_list)

	def get_src_flows_by_ip(self, srcIp):
		"""
		Get src flows corresponding to the given src IP address.

		param srcIP:	Source IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		entries = None
		if self.has_src_flow_history(srcIp):
			entries = self._src[srcIp]
		return entries

	def copy_flows_by_ip(self, ipaddr, flowset):
		"""
		Copy flows corresponding to the given IP address into new data structures.

		param ipaddr:	IP address of flows to retrieve.
		param flowset:	src or dst flowset.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		entries_copy = None
		if self.has_flow_history(ipaddr, flowset):
			entries = flowset[ipaddr]
			entries_copy = [entries[0], dict(), entries[2]]
			for key in entries[1].keys():
				entries_copy[1][key] = [entries[1][key][0], entries[1][key][1]]
		return entries_copy

	def copy_src_flows_by_ip(self, srcIp):
		"""
		Copy src flows corresponding to the given src IP address into new data
		structures.

		param srcIP:	Source IP address of flows to retrieve.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		entries_copy = None
		if self.has_src_flow_history(srcIp):
			entries = self._src[srcIp]
			entries_copy = [entries[0], dict(), entries[2]]
			for key in entries[1].keys():
				entries_copy[1][key] = [entries[1][key][0], entries[1][key][1]]
		return entries_copy

	def copy_dst_flows_by_ip(self, dstIp):
		"""
		Copy dst flows corresponding to the given dst IP address into new data
		structures.

		param dstIP:	Destination IP address of flows to retrieve.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		entries_copy = None
		if self.has_dst_flow_history(dstIp):
			entries = self._dst[dstIp]
			entries_copy = [entries[0], dict(), entries[2]]
			for key in entries[1].keys():
				entries_copy[1][key] = [entries[1][key][0], entries[1][key][1]]
		return entries_copy

	def copy_and_reset_flows_by_ip(self, ipaddr, flowset):
		"""
		Copy flows corresponding to the given IP address into new data structures
		and reset all flows so that further updates will be calculated against
		the value at the most recent reading.

		param ipaddr:	IP address of flows to retrieve.
		param flowset:	src or dst flowset.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		entries_copy = None
		if self.has_flow_history(ipaddr, flowset):
			entries = flowset[ipaddr]
			entries_copy = [entries[0], dict(), entries[2]]
			for key in entries[1].keys():
				entries_copy[1][key] = [entries[1][key][0], entries[1][key][1]]
				entries[1][key][1] = entries[1][key][0]
		return entries_copy

	def get_dst_flows_by_ip(self, dstIp):
		"""
		Get dst flows corresponding to the given dst IP address.

		param dstIP:	Destination IP address of flows to retrieve.
		return:			Flow entries with this IP address as the destination;
						None is no such flows exist.
		"""
		entries = None
		if self.has_dst_flow_history(dstIp):
			entries = self._dst[dstIp]
		return entries

	def del_src_flows_by_ip(self, srcIp):
		"""
		Delete src flows corresponding to the given src IP address.

		param srcIP:	Source IP address of flows to delete.
		"""
		entries = None
		if self.has_src_flow_history(srcIp):
			del self._src[srcIp]

	def del_dst_flows_by_ip(self, dstIp):
		"""
		Delete dst flows corresponding to the given dst IP address.

		param dstIP:	Source IP address of flows to delete.
		"""
		entries = None
		if self.has_dst_flow_history(dstIp):
			del self._dst[dstIp]

	def get_src_mac_by_ip(self, srcIp):
		"""
		Retrieve the MAC address corresponding to the given src IP address.

		param srcIP:	Source IP address linked to the desired MAC address.
		return:			The MAC address linked to the given IP address;
						None otherwise.
		"""
		entries = self.get_src_flows_by_ip(srcIp)
		if entries is not None:
			return entries[0]
		else:
			return None	

	def get_dst_mac_by_ip(self, dstIp):
		"""
		Retrieve the MAC address corresponding to the given dst IP address.

		param dstIP:	Destination IP address linked to the desired MAC address.
		return:			The MAC address linked to the given IP address;
						None otherwise.
		"""
		entries = self.get_dst_flows_by_ip(dstIp)
		if entries is not None:
			return entries[0]
		else:
			return None

	def get_mac_by_ip(self, ipaddr):
		"""
		Retrieve the MAC address corresponding to the given IP address.

		param ipaddr:	IP address linked to the desired MAC address.
		return:			The MAC address linked to the given IP address;
						None otherwise.
		"""
		ip = self.get_src_mac_by_ip(ipaddr)
		if ip is None:
			ip = self.get_dst_mac_by_ip(ipaddr)
		return ip

		
class DpCtl(object):
	"""
	Class wrapping the 'ovs-dpctl dump-flows' command.
	Provides utility functions for handling/updating flows.
	"""

	def __init__(self, bridge):
		"""
		Initialise the DpCtl class.

		param bridge:	The network bridge to dump datapath flows for.
		"""
		self.bridge = bridge
		self.flows = Flows()

	def get_dp_flows(self):
		"""
		Get flows for the bridge specified at class construction time.
		
		return:	Unprocessed output of the 'ovs-dpctl dump-flows' command as a
				list of lines.
		"""
		proc = sub.Popen('ovs-dpctl dump-flows ' + self.bridge, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
		lines = proc.stdout.readlines()
		return lines

	def update_entries(self, lines):
		"""
		Update the flow entries using the 'ovs-dpctl dump-flows' output.

		param lines:	Output from 'ovs-dpctl dump-flows' command.
		"""
		for line in lines:
			line = line.split(',')
			# Check we have an IPv4 packet
			if (line[3] == 'eth_type(0x0800)'):
				# Now add the entry to the dictionaries
				# First, extract MAC, IP and packets
				srcMac = line[1][8:]
				dstMac = line[2][4:-1]
				srcIp = line[4][9:]
				dstIp = line[5][4:]
				if not (line[13].strip().startswith('bytes')):
					# This happens with IGMP packets (IP proto 2).
					# If it happens with other packet types in other unknown ways,
					# might be best to process just TCP/UDP packets.
					#print 'Out-of-normal line: ' + str(line)
					bytes = int(line[11].strip()[6:])
				else:
					bytes = int(line[13].strip()[6:])
				entry = FlowEntry(srcMac, dstMac, srcIp, dstIp, bytes)
				self.flows.update_flows(entry)

	def get_src_flows_by_ip(self, srcIp):
		"""
		Get src flows corresponding to the given src IP address.

		param srcIP:	Source IP address of flows to retrieve.
		return:			Flow entries with this IP address as the source;
						None if no such flows exist.
		"""
		return self.flows.get_src_flows_by_ip(srcIp)

	def get_dst_flows_by_ip(self, dstIp):
		"""
		Get dst flows corresponding to the given dst IP address.

		param dstIP:	Destination IP address of flows to retrieve.
		return:			Flow entries with this IP address as the destination;
						None is no such flows exist.
		"""
		return self.flows.get_dst_flows_by_ip(dstIp)

	def copy_flows_by_ip(self, ipaddr, flowset):
		"""
		Copy flows corresponding to the given IP address into new data
		structures.

		param ipaddr:	IP address of flows to retrieve.
		param flowset:	src or dst flowset.
		return:			A copy of the flow entries with this IP address as the
						originator; None if no such flows exist.
		"""
		return self.flows.copy_flows_by_ip(ipaddr, flowset)

	def copy_src_flows_by_ip(self, srcIp):
		"""
		Copy src flows corresponding to the given IP address into new data
		structures.

		param srcIp:	Source IP address of flows to retrieve.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		return self.copy_flows_by_ip(srcIp, self.flows.src_flows)

	def copy_dst_flows_by_ip(self, dstIp):
		"""
		Copy dst flows corresponding to the given IP address into new data
		structures.

		param dstIp:	Destination IP address of flows to retrieve.
		return:			A copy of the flow entries with this IP address as the
						destination; None if no such flows exist.
		"""
		return self.copy_flows_by_ip(dstIp, self.flows.dst_flows)

	def copy_and_reset_flows_by_ip(self, ipaddr, flowset):
		"""
		Copy flows corresponding to the given IP address and reset all flows.

		param ipaddr:	IP address of flows to retrieve.
		param flowset:	src or dst flowset.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		return self.flows.copy_and_reset_flows_by_ip(ipaddr, flowset)

	def copy_and_reset_src_flows_by_ip(self, srcIp):
		"""
		Copy flows corresponding to the given src IP address and reset all src flows.

		param srcIp:	Source IP address of flows to retrieve.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		return self.copy_and_reset_flows_by_ip(srcIp, self.flows._src)

	def copy_and_reset_dst_flows_by_ip(self, dstIp):
		"""
		Copy flows corresponding to the given dst IP address and reset all dst flows.

		param dstIp:	Destination IP address of flows to retrieve.
		return:			A copy of the flow entries with this IP address as the
						source; None if no such flows exist.
		"""
		return self.copy_and_reset_flows_by_ip(dstIp, self.flows._dst)

	def get_src_mac_by_ip(self, srcIp):
		"""
		Retrieve the MAC address corresponding to the given src IP address.

		param srcIP:	Source IP address linked to the desired MAC address.
		return:			The MAC address linked to the given IP address;
						None otherwise.
		"""
		return self.flows.get_src_mac_by_ip(srcIp)	

	def get_dst_mac_by_ip(self, dstIp):
		"""
		Retrieve the MAC address corresponding to the given dst IP address.

		param dstIP:	Destination IP address linked to the desired MAC address.
		return:			The MAC address linked to the given IP address;
						None otherwise.
		"""
		return self.flows.get_dst_mac_by_ip(dstIp)

	def get_mac_by_ip(self, ipaddr):
		"""
		Retrieve the MAC address corresponding to the given IP address.

		param ipaddr:	IP address linked to the desired MAC address.
		return:			The MAC address linked to the given IP address;
						None otherwise.
		"""
		return self.flows.get_mac_by_ip(ipaddr)

#dpctl = DpCtl('xenbr0')
#lines = dpctl.get_dp_flows()
#dpctl.update_entries(lines)
#print dpctl.get_mac_by_ip('192.168.2.1')
#print dpctl.get_src_flows_by_ip('192.168.2.1')
#print dpctl.get_dst_flows_by_ip('192.168.2.1')
#print dpctl.get_src_mac_by_ip('192.168.2.1')
#print dpctl.get_dst_mac_by_ip('192.168.2.1')


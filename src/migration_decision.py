import datetime
import sys
import xen_utils as xen

MAX_DOMS = 4

class MigrationDecision(object):
	"""
	Class containing algorithms that operate upon a single host to determine
	suitability of a VM for migration.
	"""

	def __init__(self, dpthread, lookup):
		"""
		Initialise the migration decision class.

		param dpctl: 	dpctl thread for taking measurements.
		param lookup:	A pre-computed lookup table for communication costs.
		"""
		self.dpthread = dpthread
		self.lookup = lookup

	def round_robin(self, ipaddr):
		"""
		Perform a round-robin decision process for the VM with given IP address.

		param ipaddr:	The IP address of the VM to consider for migration.
		return:			IP address of server to migrate to, None otherwise.
		"""
		src, dst, mac = self.get_entries_and_mac(ipaddr)
		values = dict()
		total_cost = 0
		total_cost_new = 0
		hypervisor = None
		current = datetime.datetime.now()

		if (src is None and dst is None):
			#print 'Returning.'
			return None

		# Get aggregate throughput to/from neighbouring VMs, and communication costs.
		if (src is not None):
			for ip in src[1].keys():
				if (ip.startswith('')):#192.168.1.')):
					values[ip] = [src[1][ip][0]+src[1][ip][1], 0, 0, '']
					### EVALUATION ###
					hypervisor, cost = self.lookup.communication_cost('192.168.1.4')
					#hypervisor, cost = self.lookup.communication_cost(ip)
					#print ip
					#print hypervisor, cost
					if (hypervisor is None and cost is None):
						# Can't find hypervisor and associated cost, so can't migrate here.
						del values[ip]
					else:
						values[ip][1] = cost
						values[ip][2] = 2*values[ip][0]*values[ip][1] / (current - src[2]).total_seconds()
						total_cost = total_cost + values[ip][2]
						values[ip][3] = hypervisor
			if (dst is not None):
				for ip in dst[1].keys():
					if not (values.has_key(ip)):
						if (ip.startswith('')):#192.168.1.')):
							values[ip] = ([dst[1][ip][0]+dst[1][ip][1], 0, 0, '']) / (current - src[2]).total_seconds()
							### EVALUATION ###
							hypervisor, cost = self.lookup.communication_cost('192.168.1.4')
							#hypervisor, cost = self.lookup.communication_cost(ip)
							values[ip][1] = cost
							values[ip][2] = 2*values[ip][0]*values[ip][1]
							total_cost = total_cost + values[ip][2]
							values[ip][3] = hypervisor
					else:
						# Cost should already exist - save doing another lookup.
						values[ip][0] = (values[ip][0] + dst[1][ip][0]+dst[1][ip][1]) / (current - src[2]).total_seconds()
						values[ip][2] = 2*values[ip][0]*values[ip][1]
						total_cost = total_cost + values[ip][2]

			# Find a destination server to migrate to, with appropriate space.
			max_cost = sys.maxint
			while (max_cost > 0):
				hypervisor, max_cost = self.get_highest_cost_hypervisor(values, max_cost)
				#print hypervisor, max_cost
				if (hypervisor is not None):
					### EVALUATION ###
					capacity = self.lookup.capacity_request(hypervisor)
					#capacity = self.lookup.capacity_request(hypervisor)
					if (capacity is not None):
						doms = xen.xm_get_parsed_doms()
						print capacity
						#print doms
						for dom in doms:
							#print dom, mac
							#print xen.xm_get_mac(dom)
							if (xen.xm_get_mac(dom) == mac):
								if (capacity[0] < MAX_DOMS and capacity[1] > xen.xm_get_mem_vmid(dom)):
									return (mac, hypervisor)
			return None

			# Calculate new communication cost if migration takes place.
			new_values = dict()
			for ip in values.keys():
				new_cost = self.lookup.communication_cost(hypervisor, values[ip][3])
				new_values[ip] = values[ip][1] * new_cost
				total_cost_new = total_cost_new + new_values[ip]
		
			# Make/return migration decision.
			if (total_cost_new < total_cost):
				return hypervisor
			return None
		return None

	def distributed(self, ipaddr, token):
		"""
		Perform a distributed decision process for the VM with given IP address.

		param ipaddr:	The IP address of the VM to consider for migration.
		param token:	The token of VMs to consider for migration.
		return:			IP address of server to migrate to, None otherwise.
		"""

	def get_entries_and_mac(self, ipaddr):
		"""
		Get src and dst entries of the VM with the given IP address, along with
		its MAC address.

		param ipaddr:	The IP address of the VM to consider for migration.
		return:			Src and dst flow entries, and MAC address, of the VM,
							None if no traffic exists.
		"""
		src = self.dpthread.copy_and_reset_entries_by_src_ip(ipaddr)
		dst = self.dpthread.copy_and_reset_entries_by_dst_ip(ipaddr)
		mac = ""
		if (src is not None or dst is not None):
			mac = self.dpthread.get_mac_by_ip(ipaddr)
		else:
			# There is no network traffic from the given host; no migration
			# should take place.
			return None, None, None
		return src, dst, mac

	def get_highest_cost_hypervisor(self, values, cost_ceil):
		"""
		Find the IP address of the hypervisor with the highest cost that is below
		the cost ceiling.

		param values:		List of total communication cost values to consider.
		param cost_ceil:	Cost ceiling to search for highest cost within.
		return:				The IP address of the hypervisor with the highest cost
								that is still below the cost ceiling, None otherwise.
		"""
		hypervisor = None
		max_cost = 0
		for ip in values.keys():
			if ((values[ip][2] > max_cost) and (values[ip][2] < cost_ceil)):
				hypervisor = values[ip][3]
				max_cost = values[ip][2]
		return hypervisor, max_cost


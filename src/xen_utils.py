#!/usr/bin/python
import sys
sys.path.insert(1, '/usr/lib/xen-default/lib/python/')
import subprocess as sub
from xen.xm import main 
from xen.xm import migrate

class OutputBuffer:
    def __init__(self):
        self.value = []
    def write(self, string):
        self.value.append(string)
    def __str__(self):
	return ''.join(self.value).strip()

def xm_get_doms():
	out = OutputBuffer()
	stdout_old = sys.stdout
	sys.stdout = out
	args = []
	main._run_cmd(main.xm_list, 'list', args)
	sys.stdout = stdout_old
	return out

def xm_get_parsed_doms():
	out = xm_get_doms()
	return xm_parse_doms(out)

def xm_parse_doms(buffer):
	domus = []
	for line in buffer.value:
		if not line.startswith('Name') and not line.startswith('Domain-0') and not line.startswith('\n'):
			line = line.strip()
			line = line.split()
			domain = int(line[1])
			domus.append(domain)
	return domus

def xm_get_mac(vmid):
	out = OutputBuffer()
	stdout_old = sys.stdout
	sys.stdout = out
	args = [str(vmid)]
	main._run_cmd(main.xm_network_list, 'network-list', args)
	sys.stdout = stdout_old
	return xm_parse_mac(out)

def xm_parse_mac(buffer):
	mac = ''
	for line in buffer.value:
		if not line.startswith('Idx') and not line.startswith('\n'):
			line = line.strip()
			line = line.split()
			mac = line[2]
	return mac

def xm_parse_dom_mem(buffer):
	domus = [0, dict()]
	for line in buffer.value:
		if line.startswith('Domain-0'):
			line = line.strip()
			line = line.split()
			tot_mem = int(line[2])
			domus[0] = tot_mem
		elif not line.startswith('Name') and not line.startswith('Domain-0') and not line.startswith('\n'):
			line = line.strip()
			line = line.split()
			domain = int(line[1])
			mem = int(line[2])
			domus[1][domain] = mem
	return domus

def xm_get_num_doms():
	buf = xm_get_doms()
	doms = xm_parse_doms(buf)
	return len(doms)

def xm_get_mem():
	buf = xm_get_doms()
	return xm_parse_dom_mem(buf)

def xm_get_mem_vmid(vmid):
	buf = xm_get_doms()
	domus = xm_parse_dom_mem(buf)
	return domus[1][vmid]

def xm_get_avail_mem():
	buf = xm_get_doms()
	domus = xm_parse_dom_mem(buf)
	mem_avail = domus[0]
	mem_used = 0
	for key in domus[1].keys():
		mem_used = mem_used + domus[1][key]
	return mem_avail-mem_used

def live_migrate(vmid, dstIp, port):
	#out = OutputBuffer()
	#stdout_old = sys.stdout
	#args = [str(vmid), dstIp, '-l']
	#if port is not None:
	#	args.append('-p')
	#	args.append(str(port))
	#cmd = main.xm_lookup_cmd('migrate')
	#main._run_cmd(cmd, 'migrate', args)
	#sys.stdout = stdout_old
	#return out
	cmd = 'xm migrate ' + str(vmid) + ' ' + dstIp + ' -l'
	if port is not None:
		cmd = cmd + ' -p ' + str(port)
	proc = sub.Popen(cmd, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
	lines = proc.stderr.readlines()
	return lines

#print 'Num doms: ' + str(xm_get_num_doms())
#print 'Mem: ' + str(xm_get_mem())
#print 'Mem VMID 4: ' + str(xm_get_mem_vmid(4))
#print 'Avail mem: ' + str(xm_get_avail_mem())
#print str(live_migrate(5, '192.168.1.4', None))


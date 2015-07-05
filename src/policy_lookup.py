import httplib2
import json

h = httplib2.Http(".cache")
h.add_credentials('admin', 'admin')
controllerUrl = 'http://192.168.56.101:8080/controller/nb/v2'

resp, content = h.request(controllerUrl, "GET")
allFlowStats = json.loads(content)
flowStats = allFlowStats['flowStatistics']

for fs in flowStats:
	print "\nSwitch ID : " + fs['node']['id']
	print '{0:8} {1:8} {2:5} {3:15}'.format('Count', 'Action', 'Port', 'DestIP')
	for aFlow in fs['flowStat']:
		count = aFlow['packetCount']
		actions = aFlow['flow']['actions'] 
		actionType = ''
		actionPort = ''
		#print actions
		if(type(actions) == type(list())):
			actionType = actions[1]['type']
			actionPort = actions[1]['port']['id']
		else:
			actionType = actions['type']
			actionPort = actions['port']['id']
		dst = aFlow['flow']['match']['matchField'][0]['value']
		print '{0:8} {1:8} {2:5} {3:15}'.format(count, actionType, actionPort, dst)

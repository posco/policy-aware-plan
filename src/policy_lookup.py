import httplib2
import json
import sys

"""
Classes for dealing with looking up policies from (SDN) controller.
"""

class PolicyLookup():

    def __init__(self):

        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')
        self.controllerIp='192.168.0.16'

        #self.get_statistics()

    def get_policies(self):
        self.controllerUrl = 'http://'+self.controllerIp+':8080/controller/nb/v2/statistics/default/flow'

        resp, content = self.h.request(self.controllerUrl, "GET")
        print sys.getsizeof(content)

        allFlowStats = json.loads(content)
        flowStats = allFlowStats['flowStatistics']

        for fs in flowStats:
            print "\nSwitch ID : " + fs['node']['id']
            print '{0:8} {1:8} {2:5} {3:15}'.format('Count', 'Action', 'Port', 'DestIP')
            for aFlow in fs['flowStatistic']:
                count = aFlow['packetCount']
                actions = aFlow['flow']['actions']
                actionType = ''
                actionPort = ''
                #print actions
                if(type(actions) == type(list())):
                    actionType = actions[0]['type']
                    if actions[0].get('port') is not None:
                        actionPort = actions[0]['port']['id']
                else:
                    actionType = actions['type']
                    actionPort = actions['port']['id']
                dst = aFlow['flow']['match']['matchField'][0]['value']
                print '{0:8} {1:8} {2:5} {3:15}'.format(count, actionType, actionPort, dst)

plookup=PolicyLookup();
print plookup.controllerIp
plookup.get_policies()
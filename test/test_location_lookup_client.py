import add_to_sys_path
import location_lookup as location

client = location.LocationLookupClient(8000, 'xenbr0')
addr = client.location_request('192.168.1.4')
print addr
#client.location_lookup_init('../data/costs_localhost.txt')
#print client.lookup
#print client.location_lookup('127.0.0.1', addr)

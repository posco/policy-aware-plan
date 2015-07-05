import add_to_sys_path
import location_lookup as location

server = location.LocationLookupServer('localhost', 8023, 'lo')
server.listen()
server.close()

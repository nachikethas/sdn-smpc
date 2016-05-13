
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
import time
import socket
import threading
import SocketServer

log = core.getLogger()

# We don't want to flood immediately when a switch connects.
# Can be overriden on commandline.
_flood_delay = 0
th=0
c_data=0
s_data=0
class LearningSwitch (object):
 
  def __init__ (self, connection, transparent):
    # Switch we'll be adding L2 learning switch capabilities to
    self.connection = connection
    self.transparent = transparent

    # Our table
    self.macToPort = {}

    # We want to hear PacketIn messages, so we listen
    # to the connection
    connection.addListeners(self)

    # We just use this to know when to log a helpful message
    self.hold_down_expired = _flood_delay == 0

    #log.debug("Initializing LearningSwitch, transparent=%s",
    #          str(self.transparent))

  def _handle_PacketIn (self, event):
    """
    Handle packet in messages from the switch to implement above algorithm.
    """

    packet = event.parsed

    def flood (message = None):
      """ Floods the packet """
      msg = of.ofp_packet_out()
      if time.time() - self.connection.connect_time >= _flood_delay:
        # Only flood if we've been connected for a little while...

        if self.hold_down_expired is False:
          # Oh yes it is!
          self.hold_down_expired = True
          log.info("%s: Flood hold-down expired -- flooding",
              dpid_to_str(event.dpid))

        if message is not None: log.debug(message)
        #log.debug("%i: flood %s -> %s", event.dpid,packet.src,packet.dst)
        # OFPP_FLOOD is optional; on some switches you may need to change
        # this to OFPP_ALL.
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      else:
        pass
        #log.info("Holding down flood for %s", dpid_to_str(event.dpid))
      msg.data = event.ofp
      msg.in_port = event.port
      self.connection.send(msg)

    def drop (duration = None):
      """
      Drops this packet and optionally installs a flow to continue
      dropping similar ones for a while
      """
      if duration is not None:
        if not isinstance(duration, tuple):
          duration = (duration,duration)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.idle_timeout = duration[0]
        msg.hard_timeout = duration[1]
        msg.buffer_id = event.ofp.buffer_id
        self.connection.send(msg)
      elif event.ofp.buffer_id is not None:
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        msg.in_port = event.port
        self.connection.send(msg)

    self.macToPort[packet.src] = event.port # 1

    if not self.transparent: # 2
      if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
        drop() # 2a
        return

    if packet.dst.is_multicast:
      flood() # 3a
    else:
      if packet.dst not in self.macToPort: # 4
        flood("Port for %s unknown -- flooding" % (packet.dst,)) # 4a
      
      
      else:
        port = self.macToPort[packet.dst]
        if port == event.port: # 5
          # 5a
          log.warning("Same port for packet from %s -> %s on %s.%s.  Drop."
              % (packet.src, packet.dst, dpid_to_str(event.dpid), port))
          drop(10)
          return
        # 6
        log.debug("installing flow for %s.%i -> %s.%i" %
                  (packet.src, event.port, packet.dst, port))
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 50000 
        msg.hard_timeout = 50000
        msg.actions.append(of.ofp_action_output(port = port))
        msg.data = event.ofp # 6a
        self.connection.send(msg)

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    #rec data from switch 
    def handle(self):
	global c_data
	global s_data

	some=''
        while 1:
        	data = self.request.recv(4096)
        	words=data.split()
        	len1=0
        	if len(words)==2: len1=int(words[1])
        	data=words[0]
        	some=some+data
        	if len(some)==int(len1):
                	#print "before break ->>>>>>>>>>>"+str(len(some))
                	break
	s_data=some
	msg =  some + " " + str(len(some))
	HOST = '10.120.113.36'
        PORT=50007
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.sendall(msg)
	s_data=some
	s.close()

class ThreadedTCPRequestHandler_c(SocketServer.BaseRequestHandler):
    #data rec from other controller	
    def handle(self):
        global c_data
	global s_data
	some=''
	#get data from switch
        while 1:
                data = self.request.recv(4096)
                words=data.split()
                len1=0
                if len(words)==2: 
			len1=int(words[1])
                data=words[0]
                some=some+data
                if len(some)==int(len1):
                        break
        c_data=some
	#apply xor to get data back
	def function_xor(a,b):
    	 if a == b:
    	  return 0
       	 else:
          return 1
	rec=''
        i = 0
	for i in range(0,len(c_data)):
	  rec=rec+str(function_xor(c_data[i],s_data[i]))
	myvar=''.join(chr(int(rec[i:i+8], 2)) for i in xrange(0, len(rec), 8))
	print myvar
	print "time befor gen" + str(time.time())
	new_my_var=myvar.split()

        #for integrating with fast gc not complete
	'''from py4j.java_gateway import JavaGateway
        gateway = JavaGateway()
        eva = gateway.get_eva()
        eva.fun_run()
	print "time after gen" + (time.time())
	c_data=''
	s_data=''
	'''
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
class l2_learning (object):
  """
  Waits for OpenFlow switches to connect and makes them learning switches.
  """
  def __init__ (self, transparent):
    core.openflow.addListeners(self)
    self.transparent = transparent

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s" % (event.connection,))
    LearningSwitch(event.connection, self.transparent)
    # create the tcp servers/listeners
    global th
    if th==0:
     th=1
     HOST, PORT = "10.120.113.141", 50008
    
     server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
     ip, port = server.server_address
     server_thread = threading.Thread(target=server.serve_forever)
     server_thread.daemon = True
     server_thread.start()
     print "Server loop running in thread:", server_thread.name
  
     HOST, PORT = "10.120.113.141", 50007

     server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler_c)
     ip, port = server.server_address
     server_thread = threading.Thread(target=server.serve_forever)
     server_thread.daemon = True
     server_thread.start()





def launch (transparent=False, hold_down=_flood_delay):
  """
  Starts an L2 learning switch.
  """
  try:
    global _flood_delay
    _flood_delay = int(str(hold_down), 10)
    assert _flood_delay >= 0
  except:
    raise RuntimeError("Expected hold-down to be a number")

  core.registerNew(l2_learning, str_to_bool(transparent))

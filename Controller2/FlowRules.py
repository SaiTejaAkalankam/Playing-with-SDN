from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of

log = core.getLogger()


#datapath ids (dpid) are the identifiers for the switches from controller point of view.
#controller uses dpids to install respective flows in a switch according to the requirements
s1_dpid=0
s2_dpid=0
s3_dpid=0
s4_dpid=0

#it gets invoked when a virtual connection from switches are made with the controller 

def _handle_ConnectionUp(event):             
	global s1_dpid, s2_dpid, s3_dpid, s4_dpid
	for prt in event.connection.features.ports:
		if prt.name == "s1-eth1":
			s1_dpid = event.connection.dpid
			print("s1_dpid=", s1_dpid)
		elif prt.name == "s2-eth1":
			s2_dpid = event.connection.dpid
			print("s2_dpid=", s2_dpid)
		elif prt.name == "s3-eth1":
			s3_dpid = event.connection.dpid
			print("s3_dpid=", s3_dpid)
		elif prt.name == "s4-eth1":
			s4_dpid = event.connection.dpid
			print("s4_dpid=", s4_dpid)

#this is the event handler for handling "PacketIN" event --> whenever switch came across unknown packet 
#it forwards that packet to controller causing packetIN event and letting the controller to handle it

def _handle_PacketIn(event):
	global s1_dpid, s2_dpid, s3_dpid, s4_dpid
	print("PacketIn: ", dpid_to_str(event.connection.dpid))

	dpid = event.connection.dpid
	inport = event.port
	packet = event.parsed
	if not packet.parsed:
		log.warning("%i %i ignoring unparsed packet", dpid, inport)

	if dpid==s1_dpid:
		msg = of.ofp_flow_mod()
		msg.priority =1
		msg.match.dl_type = 0x0806
		msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))  #1
		event.connection.send(msg)
		
		#no traffic is allowed from h1 to h3
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.1"
		msg.match.nw_dst = "10.0.0.3"
		# By default attribute 'actions' = [] --> NONE in the of.ofp_flow_mod() library function
		event.connection.send(msg)
		
		#http traffic from h1 to h4 routed via switch 2
		msg = of.ofp_flow_mod()
		msg.priority = 15
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.tp_dst = 80                 # we have to follow 'NORMAL FORM' in constructing the flow, when specifying about
		msg.match.nw_proto = 6                # http traffic-- 'port 80', we have to specify using TCP protocol--nw_proto 6 
		msg.match.nw_src = "10.0.0.1"         # then below IP layer addresses 
		msg.match.nw_dst = "10.0.0.4"
		msg.actions.append(of.ofp_action_output(port = 3))
		event.connection.send(msg)
		
		#non-http traffic from h1 to h4 routed via switch 3
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.1"
		msg.match.nw_dst = "10.0.0.4"
		msg.actions.append(of.ofp_action_output(port = 4))
		event.connection.send(msg)
		
		#traffic from h2 to h3 routed via switch 3
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.2"
		msg.match.nw_dst = "10.0.0.3"
		msg.actions.append(of.ofp_action_output(port = 4))
		event.connection.send(msg)
		
		#traffic to h2 ( this will handle all traffic coming to host2 from all other hosts in the network )
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.match.nw_dst = "10.0.0.2"
		msg.actions.append(of.ofp_action_output(port = 2))
		event.connection.send(msg)	
		
		#traffic to h1 ( this will handle all traffic coming to host1 from all other hosts in the network )
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_dst = "10.0.0.1"
		msg.actions.append(of.ofp_action_output(port = 1))
		event.connection.send(msg)
		
		#shortest path from h2 to h4 via s2  ---> considered this path depending on the delays
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.2"
		msg.match.nw_dst = "10.0.0.4"
		msg.actions.append(of.ofp_action_output(port = 3))
		event.connection.send(msg)					
				
	elif dpid==s4_dpid:
		msg = of.ofp_flow_mod()
		msg.priority =1
		msg.match.dl_type = 0x0806
		msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))  #2
		event.connection.send(msg)
		
		#no traffic from h3 to h1
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.3"
		msg.match.nw_dst = "10.0.0.1"
		# By default attribute 'actions' = [] --> NONE in the of.ofp_flow_mod() library function
		event.connection.send(msg)
		
		#http traffic from h4 to h1 routed via switch 2
		msg = of.ofp_flow_mod()
		msg.priority =15
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.tp_dst = 80               # we have to follow 'NORMAL FORM' in constructing the flow, when specifying about       
		msg.match.nw_proto = 6              # http traffic-- 'port 80', we have to specify using TCP protocol--nw_proto 6 
		msg.match.nw_src = "10.0.0.4"       # then below IP layer addresses 
		msg.match.nw_dst = "10.0.0.1"
		msg.actions.append(of.ofp_action_output(port = 1))
		event.connection.send(msg)
		
		#non-http traffic from h4 to h1 routed via switch 3
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.4"
		msg.match.nw_dst = "10.0.0.1"
		msg.actions.append(of.ofp_action_output(port = 2))
		event.connection.send(msg)	
		
		#traffic from h3 to h2 routed switch 3
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.3"
		msg.match.nw_dst = "10.0.0.2"
		msg.actions.append(of.ofp_action_output(port = 2))
		event.connection.send(msg)

		#traffic to h3 ( this will handle all traffic coming to host3 from all other hosts in the network )
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_dst = "10.0.0.3"
		msg.actions.append(of.ofp_action_output(port = 3))
		event.connection.send(msg)	
		
		#traffic to h4 ( this will handle all traffic coming to host4 from all other hosts in the network )
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_dst = "10.0.0.4"
		msg.actions.append(of.ofp_action_output(port = 4))
		event.connection.send(msg)
		
		#shortest path from h4 to h2 via s2  ---> considered this path depending on the delays
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.match.dl_type = 0x0800
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.nw_src = "10.0.0.4"
		msg.match.nw_dst = "10.0.0.2"
		msg.actions.append(of.ofp_action_output(port = 1))
		event.connection.send(msg)
		
	elif dpid==s2_dpid:
		#just forwarding bi-directional way
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.in_port = 1
		msg.actions.append(of.ofp_action_output(port = 2 ))
		event.connection.send(msg)

		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.in_port = 2
		msg.actions.append(of.ofp_action_output(port = 1 ))
		event.connection.send(msg)	
		
	elif dpid==s3_dpid:
		#just forwarding bi-directional way
		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.in_port = 1
		msg.actions.append(of.ofp_action_output(port = 2 ))
		event.connection.send(msg)

		msg = of.ofp_flow_mod()
		msg.priority =10
		msg.idle_timeout = 100
		msg.hard_timeout = 200
		msg.match.in_port = 2
		msg.actions.append(of.ofp_action_output(port = 1 ))
		event.connection.send(msg)		


#"Launch()" adds event-listeners to handle events which occur in the network
#it is invoked implicitly when we run the controller.py file in pox associated terminal

def launch():
	core.openflow.addListenerByName("ConnectionUp",_handle_ConnectionUp)
	core.openflow.addListenerByName("PacketIn",_handle_PacketIn)

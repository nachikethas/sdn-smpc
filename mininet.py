#!/usr/bin/python

"""
This example creates a multi-controller network from
semi-scratch; note a topo object could also be used and
would be passed into the Mininet() constructor.
"""
import time
import subprocess
from threading import Thread
from time import sleep
import socket
from random import randint

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from datetime import datetime
Switch = OVSKernelSwitch
n=0
def addHost( net, N ):
    "Create host hN and add to net."
    name = 'h%d' % N
    ip = '10.0.0.%d' % N
    return net.addHost( name, ip=ip )
c1_ip="10.120.113.141"
c2_ip="10.120.113.36"
def multiControllerNet():
    "Create a network with multiple controllers."

    net = Mininet( controller=RemoteController, switch=OVSKernelSwitch)

    print "*** Creating controllers"
    c2 = net.addController( 'c2',controller=RemoteController,ip=c2_ip, port=6633 )
    c1 = net.addController( 'c1',controller=RemoteController,ip=c1_ip, port=6633 )

    print "*** Creating switches"
    s1 = net.addSwitch( 's1' )
    s1.listenPort=6635
    s2 = net.addSwitch( 's2' )
    s4 = net.addSwitch( 's4' )
    s3 = net.addSwitch( 's3' )

    print "*** Creating hosts"

    hosts1 = [ addHost( net, n ) for n in range(1,2)]
    hosts2 = [ addHost( net, n ) for n in range(4,5) ]
    hosts3 = [ addHost( net, n ) for n in range(8,9)]
    hosts4 = [ addHost( net, n ) for n in range(12,13)]    

    print "*** Creating links"
    for h in hosts1:
        s1.linkTo( h )
    for h in hosts2:
        s2.linkTo( h )
    for h in hosts3:
    	s3.linkTo( h )
    for h in hosts4:
	s4.linkTo( h)

    s1.linkTo( s2 )
    s2.linkTo( s3 ) 
    s3.linkTo( s4 )

    print "*** Starting network"
    net.build()
    c1.start()
    c2.start()
    s1.start( [ c1 ] )
    s2.start( [ c1 ] )
    s3.start( [ c2 ] )
    s4.start( [ c2 ] )
    print "*** Testing network"
    net.pingAll()



def threaded_function():
     while 1 and thread.kill:
      #get the message from the switch
      send_msg=subprocess.check_output('''dpctl dump-flows tcp:10.120.120.82:6635|awk '{FS=",";print $6, $15, $16}' |awk '{FS="="; print $2, $3, $4}'| awk '{print $1, $3, $5}' ''', shell=True)	
      send_bin=''
      if len(send_msg)==3:
        send_msg='none'
      send_msg.rstrip()
      send_msg=send_msg+" "+str(time.time())
      before=0.0
      before=time.time()
      for ch in send_msg:
       send_bin=send_bin+bin(ord(ch))[2:].zfill(8) 
      after_binary=time.time()
      print "after converting to binary %f" %(after_binary-before)
      binary=after_binary-before
      
      #generating random string
      random_no=''
      def rand_gen():
	global n
	if n==0 : n=1
	else : n=0
	return n
      random_b_xor=''
      random_ele=['01010010', '11010011', '01010101', '11001100', '11110011']
      random_no1=''
      
      new_rand=time.time()
      while i<len(send_bin):
	random_no1=random_no1+random_ele[randint(0,4)]
	i=i+8
      for i in range(0,len(send_bin)-i):
        random_no1=random_no1+str(rand_gen()) #randint(0,1))
      new_rand_a=time.time()
      print 'the time of new random %f' % (new_rand_a-new_rand)

      # xor the random number and data
      rand_b=time.time()
      for i in range(0,len(send_bin)):
	random_no=random_no+str(randint(0,1)) #randint(0,1))
      after_random=time.time()
      print "after random_no: %f"%(after_random-rand_b)
      before_xor=time.time()
      for i in range(0,len(send_bin)):
	if random_no[i] == send_bin[i]:
         random_b_xor=random_b_xor+str(0);
        else:
         random_b_xor=random_b_xor+str(1);

      #connect to controller 1
      def conn_c1():
       HOST = c1_ip
       PORT=50008
       s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       s.connect((HOST, PORT))
       i=0
       len1=len(random_b_xor)
       s.sendall(random_b_xor+" "+str(len(random_b_xor)))
       data=''
       s.close()

      #connect to controller 2
      def conn_c2():
	HOST, PORT = c2_ip, 50008    
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	before=time.time()
	s.sendall(random_no+" "+str(len(random_no)))
	a=''
	some=''
      	after=time.time()
	print "communication delay : %f" % (after-before)
	s.close()

      #create threads for different controllers
      thread1 = Thread(target = conn_c1)
      thread2 = Thread(target = conn_c2)
      thread1.start()
      thread2.start() 
      thread1.join()
      thread2.join()
      sleep(20)

    thread = Thread(target = threaded_function)
    
    thread.kill=1
   
    thread.start()
    #thread.join() 
    CLI( net )
    thread.kill=0
    thread.join()
    print "*** Stopping network"
    net.stop()
if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    multiControllerNet()

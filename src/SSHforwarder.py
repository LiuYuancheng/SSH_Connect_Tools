#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SSHforwarder.py
#
# Purpose:     This module is used to forward a remote host port through several 
#              jumphosts to a local/other-remote host's port (Assume the firewall
#              between only allows port 22 open). Such as connect a port of a remote 
#              web server (i.e. 80/443/8080) where only SSH port (usually port 22) 
#              is reachable.
#              
# Author:      Yuancheng Liu
#
# Created:     2022/08/08
# Version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License      
#-----------------------------------------------------------------------------
"""Program Design:
    We want to create port forwarding function through several jump-hosts as 
    shown below so we can access the web page host on the web-server behind 
    the firewall+jumphosts from the users' local browser.

    Connection diagram:
    ----------------------------------------------------------------------

                                |       Jump host tunnel:22
    -------------+              |    +----------+               +---------
        LOCAL    |              |    |  REMOTE  |               | PRIVATE
        CLIENT   | <== SSH ========> |  SERVERs | <== local ==> | SERVER
    -------------+              |    +----------+               +---------
    port:8080                   |                               80/443 web service
                            FIREWALL (only port 22 is open)

    ----------------------------------------------------------------------

    This module follow the same method shown in the python ssh lib paramiko 
    "demo/forward.py" module:
    https://github.com/paramiko/paramiko/blob/1824a27c644132e5d46f2294c1e2fa131c523559/demos/forward.py

    Dependency: SSHconnector.py

    Usage steps:
    1. Init the forwarder obj by pass in the parameters.
    2. Add the jumphost info(address, user, password) in the sequence from user
    to the target remote host one by one.
    3. Call forward function to start.

Returns:
    _type_: _description_
"""

import select
import socketserver as SocketServer
from SSHconnector import sshConnector, CH_KIND

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class Handler(SocketServer.BaseRequestHandler):
    
    def handle(self):
        channel = None
        # Init the transport channel
        try:
            channel = self.ssh_transport.open_channel(CH_KIND,
                    (self.chain_host, self.chain_port), self.request.getpeername())
        except Exception as err:
            print("Error > handle() Incoming request to %s:%d failed: %s" 
                  % (self.chain_host, self.chain_port, str(err)))
            return
        
        if channel is None:
            print( "Warning > handle() Incoming request to %s:%d was rejected by the SSH server."
                % (self.chain_host, self.chain_port))
            return

        print("Connected!  Tunnel open %r -> %r -> %r"
            % ( self.request.getpeername(), channel.getpeername(), (self.chain_host, self.chain_port)))
        
        while True:
            r, w, x = select.select([self.request, channel], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0: break
                channel.send(data)
            if channel in r:
                data = channel.recv(1024)
                if len(data) == 0: break
                self.request.send(data)

        peername = self.request.getpeername()
        channel.close()
        self.request.close()
        print("Tunnel closed from %r" % (peername,))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class localForwarder(object):

    def __init__(self, localPort, remoteHost, remotePort, 
                 remoteUser=None, remotePwd=None) -> None:
        """ Init the forwarder object. Example:
            forwarder = localForwarder(localport, <target_IP>, <target_Port>)
            Args:
                localPort (int): local port 
                remoteHost (str): target remote host address.
                remotePort (str): target remote host's port need to be forwarded to local.
                remoteUser (str, optional): remote host username. Defaults to None.
                remotePwd (str, optional): remote host password. Defaults to None.
        """
        self.localPort = localPort
        self.remoteHost = remoteHost
        self.remotePort = remotePort
        self.remoteUser = remoteUser
        self.remotePasswd= remotePwd
        self.forwardServer = None
        self.connectors = [] # sshConnectors list.

#-----------------------------------------------------------------------------
    def addNextJH(self,jumphost, username, password, port=22):
        """ Add next one jump host in the jumphost queue.
            Args:
                jumphost (str): jumphost address.
                username (str): jumphost ssh login user name.
                password (str): jumphost ssh login password.
                port (int, optional): ssh port. Defaults to 22.
        """
        parent = None if len(self.connectors) == 0 else self.connectors[-1]
        nextConnector = sshConnector(parent, jumphost, username, password, port=port)
        if parent:parent.addChild(nextConnector)
        self.connectors.append(nextConnector)

#-----------------------------------------------------------------------------
    def getJsonInfo(self):
        """ Get current object's info under Json format"""
        return {
            'local port:': self.localPort, 
            'remote host': self.remoteHost,
            'remote port': self.remotePort,
            'remote user': self.remoteUser,
            'remote password': self.remotePasswd,
            'Connectors num': len(self.connectors),
            'Forward server set': not (self.forwardServer is None)
        }

#-----------------------------------------------------------------------------
    def startForward(self):
        """ Start to forward the remote host bind port to the local port."""
        if len(self.connectors) == 0:
            print("Error: no jumphost server setup.")
            return None
        # Init the jumphost tunnel chain.
        self.connectors[0].InitTunnel()
        transport = self.connectors[-1].getTransport()
        if transport is None:
            print("Error: connectors not provide any transport channel.")
            return None
        # create a handler class and pass in the handler in TCP forward server.
        class SubHander(Handler):
            chain_host = self.remoteHost
            chain_port = self.remotePort
            ssh_transport = transport
        print('Starting the forward server ...')  
        try:
            self.forwardServer = ForwardServer(("", self.localPort), SubHander)
            self.forwardServer.serve_forever()
        except KeyboardInterrupt:
            self.stopForward()
            self.connectors[0].close()
        print('Finished close all ssh session.')

#-----------------------------------------------------------------------------
    def stopForward(self):
        """ Stop the forward server."""
        if self.forwardServer:
            self.forwardServer.shutdown()
            self.forwardServer = None
        print('Port forwarding stopped.')

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
    print("Test init single line ssh tunnel connection through multiple jumphosts.")
    localport = int(input("Please input the local port to bind: "))
    targetip = str(input("Please input the target ip: "))
    targetport = int(input("Please input the target port to bind: "))
    forwarder = localForwarder(localport, targetip, targetport)
    jumphostNum = int(input("Input jumphost number (int):"))
    if jumphostNum > 0:
        for i in range (int(jumphostNum)):
            host = str(input("Input jumphost %d hostname:"%(i+1)))
            username = str(input("Input jumphost %d username:"%(i+1)))
            password = str(input("Input jumphost %d password:"%(i+1)))
            forwarder.addNextJH(host, username, password)
    print("Start forward with below ssh tunnel config:")        
    print(forwarder.getJsonInfo())
    forwarder.startForward()

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

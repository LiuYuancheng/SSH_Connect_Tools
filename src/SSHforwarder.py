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
# Version:     v_0.1
# Copyright:   National Cybersecurity R&D Laboratories
# License:     
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
    1. Init the forwarder obj by pass in the paramters.
    2. Add the jumphost info(address, user, password) in the sequence from user
    to the target remote host one by one.
    3. Call forward function to start.

Returns:
    _type_: _description_
"""

import select
import socketserver as SocketServer
from SSHconnector import sshConnector, CH_KIND

DEBUG_MD = True # debug mode flag

#-----------------------------------------------------------------------------
def debugprint(s):
    if DEBUG_MD: print(s)

# Forward tunnerl function.
def forward_tunnel(local_port, remote_host, remote_port, transport):
    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)
    class SubHander(Handler):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport

    ForwardServer(("", local_port), SubHander).serve_forever()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class Handler(SocketServer.BaseRequestHandler):
    
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                CH_KIND,
                (self.chain_host, self.chain_port),
                self.request.getpeername(),
            )
        except Exception as e:
            debugprint( "Incoming request to %s:%d failed: %s"
                % (self.chain_host, self.chain_port, repr(e))
            )
            return
        if chan is None:
            debugprint( "Incoming request to %s:%d was rejected by the SSH server."
                % (self.chain_host, self.chain_port)
            )
            return

        debugprint("Connected!  Tunnel open %r -> %r -> %r"
            % ( self.request.getpeername(), 
                chan.getpeername(), 
                (self.chain_host, self.chain_port),)
        )
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0: break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0: break
                self.request.send(data)

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        debugprint("Tunnel closed from %r" % (peername,))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class localForwarder(object):

    def __init__(self, localPort, remoteHost, remotePort, remoteUser=None, remotePwd=None) -> None:
        """ Init the forwarder object.

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
        self.connectors = [] # sshConnectors string.

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
        """ Start to forward the remote host bind port to the local port.
        Returns:
            _type_: _description_
        """
        if len(self.connectors) == 0:
            print("Error: no jumphost server setup.")
            return None
        # Init the jumphost tunnel chain.
        self.connectors[0].InitTunnel()
        transport = self.connectors[-1].getTransport()
        if transport is None:
            print("Error: connectors not provide any transport channel.")
            return None
        # create a handler class and pass in the handler in TCP forwared server.
        class SubHander(Handler):
            chain_host = self.remoteHost
            chain_port = self.remotePort
            ssh_transport = transport

        debugprint('Starting the forward server ...')  
        try:
            self.forwardServer = ForwardServer(("", self.localPort), SubHander)
            self.forwardServer.serve_forever()
        except KeyboardInterrupt:
            self.stopForward()
            self.connectors[0].close()
        debugprint('Finihsed close all ssh session.')

#-----------------------------------------------------------------------------
    def stopForward(self):
        """ Stop the forward server."""
        if self.forwardServer:
            self.forwardServer.shutdown()
            self.forwardServer = None
        debugprint('Port forwarding stopped.')


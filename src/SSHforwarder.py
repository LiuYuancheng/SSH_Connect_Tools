#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SSHforwarder.py
#
# Purpose:     This module is used to forward 
#              
# Author:      Yuancheng Liu
#
# Created:     2022/08/08
# Version:     v_0.1
# Copyright:   National Cybersecurity R&D Laboratories
# License:     
#-----------------------------------------------------------------------------
import sys
import time
import select
import socketserver as SocketServer
from SSHconnector import sshConnector, CH_KIND

g_verbose = True

def verbose(s):
    if g_verbose:
        print(s)

class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                CH_KIND,
                (self.chain_host, self.chain_port),
                self.request.getpeername(),
            )
        except Exception as e:
            verbose(
                "Incoming request to %s:%d failed: %s"
                % (self.chain_host, self.chain_port, repr(e))
            )
            return
        if chan is None:
            verbose(
                "Incoming request to %s:%d was rejected by the SSH server."
                % (self.chain_host, self.chain_port)
            )
            return

        verbose(
            "Connected!  Tunnel open %r -> %r -> %r"
            % (
                self.request.getpeername(),
                chan.getpeername(),
                (self.chain_host, self.chain_port),
            )
        )
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        verbose("Tunnel closed from %r" % (peername,))

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
class localForwarder(object):

    def __init__(self, localPort, remoteHost, remotePort, remoteUser=None, remotePwd=None) -> None:
        self.localPort = localPort
        self.remoteHost = remoteHost
        self.remotePort = remotePort
        self.remoteUser = remoteUser
        self.remotePasswd= remotePwd
        self.connectors = [] # sshConnectors string.

    def addNextJH(self,jumphost, username, password, port=22):
        parent = None if len(self.connectors) == 0 else self.connectors[-1]
        nextConnector = sshConnector(parent, jumphost, username, password, port=port)
        if parent:parent.addChild(nextConnector)
        self.connectors.append(nextConnector)

    def startForward(self):
        if len(self.connectors) == 0:
            print("Error: no jumphost server setup.")
            return None
        # Init the jumphost tunnel chain.
        self.connectors[0].InitTunnel()
        transport = self.connectors[-1].getTransport()
        if transport is None:
            print("Error: connectors no transport channel.")
            return None
        class SubHander(Handler):
            chain_host = self.remoteHost
            chain_port = self.remotePort
            ssh_transport = transport

        print('Starting the forward server ...')
        forwardServer = None
        try:
            forwardServer = ForwardServer(("", self.localPort), SubHander)
            forwardServer.serve_forever()
        except KeyboardInterrupt:
            print('Port forwarding stopped.')
            if forwardServer: forwardServer.shutdown()
            self.connectors[0].close()
        print('Finihsed close all ssh session')


    def stop(self):
        pass



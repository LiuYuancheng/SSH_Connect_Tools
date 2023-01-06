#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SCPconnector.py
#
# Purpose:     This module will use SSHconnector and python-scp module to scp 
#              upload/ddownload file in the program running host to the dest 
#              server (through a jump hosts chain)
#              
# Author:      Yuancheng Liu
#
# Created:     2022/08/01
# Version:     v_0.1
# Copyright:   National Cybersecurity R&D Laboratories
# License:     
#-----------------------------------------------------------------------------

import os
import scp
import sys
from scp import SCPClient
from SSHconnector import sshConnector

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class scpConnector(object):

    def __init__(self, destInfo, jumpChain=None, showProgress=False) -> None:
        self.destHost = None
        if not jumpChain or len(jumpChain) == 0:
            self.destHost = sshConnector(None, destInfo[0], destInfo[1], destInfo[2])
            self.destHost.InitTunnel()
            self.destHost.addCmd('pwd', None)
            self.destHost.runCmd(interval=0.1)

        def progress4(filename, size, sent, peername):
            sys.stdout.write("(%s:%s) %s's progress: %.2f%%   \r" % (peername[0], peername[1], filename, float(sent)/float(size)*100) )
        
        self.scpClient = SCPClient(self.destHost.getTransport(), progress4=progress4) if showProgress else SCPClient(self.destHost.getTransport())

#-----------------------------------------------------------------------------
    def uploadFile(self, srcPath, destPath):
        if self.scpClient: 
            if os.path.exists(srcPath):
                try:
                    self.scpClient.put(srcPath, destPath)
                except Exception as err:
                    print("File translate failed: %s" %str(err))
            else:
                print("The srouce file is not exist")
        else:
            print("The scp client is not inited")

#-----------------------------------------------------------------------------
    def downFile(self, srcPath, destPath=None):
        if self.scpClient: 
            try:
                self.scpClient.get(srcPath)
            except Exception as err:
                print("File translate failed: %s" %str(err))
        else:
            print("The scp client is not inited")

#-----------------------------------------------------------------------------
    def close(self):
        self.scpClient.close()
        self.destHost.close()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def testCase(mode):
    destInfo = ('gateway.ncl.sg', 'rp_fyp_ctf', 'rpfyp@ncl2022')
    scpClient = scpConnector(destInfo, showProgress=True)
    scpClient.uploadFile('scpTest.txt', '~/scpTest2.txt')
    scpClient.downFile('~/scpTest2.txt')
    scpClient.close()

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    testCase('all')



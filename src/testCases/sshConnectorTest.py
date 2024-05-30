#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        sshConnectorTest.py
#
# Purpose:     Test case program of module SCPconnector.py
#
# Author:      Yuancheng Liu
#
# Created:     2024/05/29
# Version:     v_0.1.2
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License    
#-----------------------------------------------------------------------------

import os
import sys
import json

print("Current working directory is : %s" % os.getcwd())
DIR_PATH = dirpath = os.path.dirname(os.path.abspath(__file__))
print("Current source code location : [%s]" % dirpath)

TOPDIR = 'src'

idx = dirpath.find(TOPDIR)
gTopDir = dirpath[:idx + len(TOPDIR)] if idx != -1 else dirpath   # found it - truncate right after TOPDIR
if os.path.exists(gTopDir): sys.path.insert(0, gTopDir)

import SSHconnector

def testCase(case):

    print("Test Case 1: test ssh tunnel chain and run cmd.")
    # load the ssh credential and config file
    credentialCfgFile = 'sshConnectorTestConfig01.json'
    credentialCfg = []
    with open(os.path.join(dirpath, credentialCfgFile), 'r') as f:
        credentialCfg = json.load(f)
    # data handling function
    def test1RplyHandleFun(data):
        print("Host: %s" % data['host'])
        print("Cmd: %s" % data['cmd'])
        print("Result:\n%s" % data['reply'])

    mainhost = None
    for idx, val in enumerate(credentialCfg):
        if idx == 0:
            mainhost = SSHconnector.sshConnector(None, val['host'], val['user'], val['password'], port=val['port'])
            for cmdline in val['cmdlist']:
                mainhost.addCmd(cmdline, test1RplyHandleFun)
        else:
            jpHost = SSHconnector.sshConnector(mainhost, val['host'], val['user'], val['password'], port=val['port'])
            mainhost.addChild(jpHost)
            for cmdline in val['cmdlist']:
                jpHost.addCmd(cmdline, test1RplyHandleFun)

    mainhost.InitTunnel()
    mainhost.runCmd(interval=0.1)
    mainhost.close()


#-----------------------------------------------------------------------------
if __name__ == '__main__':
    testCase('all')



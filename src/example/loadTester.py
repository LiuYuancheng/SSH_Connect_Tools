#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        cissredloadTester.py
#
# Purpose:     This program is used to generate the network ssh traffic load to 
#              the cissred 2023 CTF-D environment.
#              
# Author:      Yuancheng Liu
#
# Created:     2023/06/23
# Version:     v_0.1.2
# Copyright:   National Cybersecurity R&D Laboratories
# License:     
#-----------------------------------------------------------------------------
"""
Example of config *.json file: 
{
    "cmdlines": [
        "ls",
        "pwd",
        "ip a",
        "who",
        "ps"
    ],
    "Teaminfo": [
        {
            "teamSize": 8,
            "gatewayInfo": {
                "ipaddress": "gateway.ncl.sg",
                "username": "xxx",
                "password": "xxx"
            },
            "teamLoginInfo": {
                "ipaddress": "xxx.xxx.xxx.xxx",
                "port": xxxx,
                "username": "xxxx",
                "password": "xxxx",
                "cmdrepeat": 10,
                "cmdinterval": 1
            }
        },
}
"""

import json
import threading
from SSHconnector import sshConnector

# load all the config 
CFG_FILE = 'config.json'

# load the config file.
print("Load the configuration file.")
gConfigDict = None 
with open(CFG_FILE, 'r') as f:
  gConfigDict = json.load(f)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class userTester(threading.Thread):
    """ Start a parallel thread to start a ssh session to connect to the target 
        VM to act as one user to run ssh commands. 
    """
    def __init__(self, parent, threadID, gatewayInfo, targetVMInfo):
        """_summary_
        Args:
            parent (_type_): _description_
            threadID (_type_): _description_
            gatewayInfo (dict): jump host information dict.
            targetVMInfo (dict): target host information dict.
        """
        threading.Thread.__init__(self)
        self.parent = parent
        self.threadID = threadID
        self.cmdList = gConfigDict['cmdlines']
        self.mainInfo = gatewayInfo
        self.jumpInfo = targetVMInfo
        # Init the gateway ssh connector :
        self.mainHost = sshConnector(None,
                                     self.mainInfo['ipaddress'],
                                     self.mainInfo['username'],
                                     self.mainInfo['password'])
        # Init the transaction ssh connector :
        self.tgtHost = sshConnector(self.mainHost,
                                    self.jumpInfo['ipaddress'],
                                    self.jumpInfo['username'],
                                    self.jumpInfo['password'],
                                    port=self.jumpInfo['port'])
        for cmdStr in self.cmdList:
            self.tgtHost.addCmd(cmdStr, self.testRplFunction)
        self.mainHost.addChild(self.tgtHost)
        try:
            self.mainHost.InitTunnel()
            self.mainHost.runCmd(interval=1)
            print('===> User login success.')
        except Exception as err:
            print('xxx> User login failed, Error: %s' %str(err))

    def testRplFunction(self, replyStr):
        print("Got reply: %s" % str(replyStr))

    def run(self):
        for _ in range(int(self.jumpInfo['cmdrepeat'])):
            self.mainHost.runCmd(interval=float(self.jumpInfo['cmdinterval']))
        self.mainHost.close()

    def stop(self):
        self.mainHost.close()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class teamTester(object):
    """ Create a team with thread pool to simulate set of users."""
    def __init__(self, memberCount=8, gatewayInfo=None, targetVMInfo=None) -> None:
        self.memberCount = memberCount
        self.gatewayInfo = gatewayInfo
        self.targetVMInfo = targetVMInfo
        self.testTesters = {}
        for i in range(self.memberCount):
            key = 'user:'+str(i)
            usertester = userTester(self, i, self.gatewayInfo, self.targetVMInfo)
            print(key+'inited')
            self.testTesters[key] = usertester
        print("Finished init all the users.")

    def startTest(self):
        print("Start to launch all the user tester")
        for key in self.testTesters.keys():
            self.testTesters[key].start()

#-----------------------------------------------------------------------------
def main():
    print("Start ssh access loading test.")
    loadTestList = []
    for i, teamInfo in enumerate(gConfigDict['Teaminfo']):
        print('Init the team [%s]' % str(i))
        loadtester = teamTester(memberCount=teamInfo['teamSize'],
                                gatewayInfo=teamInfo['gatewayInfo'],
                                targetVMInfo=teamInfo['teamLoginInfo'])
        loadTestList.append(loadtester)
    print("Start load testing")
    for loadtester in loadTestList:
        loadtester.startTest()

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

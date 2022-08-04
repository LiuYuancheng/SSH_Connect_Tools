# SSH-Connector

**Program Design Purpose**: This module is used to create a ssh connector to provide nested ssh tunnel connection through jumphosts with an editable tcp port. (host with NAT port forwarding setup such as: ssh -p port ...@host).

[TOC]

### Introduction 

This program is aimed to create a ssh connector to build a ssh connection tunnel tree to let the user can access and execute command on different hosts. The ssh connector be used for implementing below tasks/scenario. 

1. Single user uses one account to access the targe host through several jump hosts: 

   ![](doc/img/sshTunnel1.png)

2. Multiple users use same account to access the same target host through several jump hosts:

   ![](doc/img/sshTunnel2.png)

3. Single user use different account to access multiple targe hosts through jump hosts:

   ![](doc/img/sshTunnel3.png)

4. Multiple user use different accounts to access multiple target hosts through different/same jump hosts:

   ![](doc/img/sshTunnel4.png)

5. -- 
# SSH Connection Tools

![](doc/img/logo.png)

**Program Design Purpose**: We want to create a python SSH tool lib which can do SSH communication, SCP file transfer and SSH port forwarding through multiple jump hosts SSH tunnel chain. The lib is design to provide a simple way with API to create nested SSH tunnel connection through jump hosts with an editable TCP port for user or their program to automated finish the SSH tasks such as:

1. Batching process the SSH connection running command tasks such as connect to several server's IPMI to collect server operation data. 
2. Start hundreds thread to SSH connect to the target service to do the load and Stress. 
3. SCP transfer file among different servers. 
4. Forward different server's port to local host for user to check multiple web interface host in a cluster. 

```
# Created:     2022/08/01
# Version:     v_0.1.3
# Copyright:   Copyright (c) 2024 LiuYuancheng
# License:     MIT License  
```

**Table of Contents**

[TOC]

------

### Introduction

This project provide 3 main modules to help user to automated SSH run multiple commands on different host, SCP file among different servers and SSH forward traffic to the local host. 

1. **SSH-Connector**: The SSH connector is aimed to create a SSH connector to build a ssh connection tunnel tree to let the user can access and execute command on different hosts through multiple jump hosts in a cluster. 
2. **SCP-Connector**: The SCP connector is used to do the file transfer(upload/download) files among different node through the SSH  tunnel tree. 
3. **SSH-Forwarder**: The SSH forwarder is aimed to help do the ssh port forward to forward the communication traffic from a node in the network to the user's local machine through the SSH tunnel tree. 

We use the lib [paramiko](https://www.paramiko.org/) and [python-scp](https://pypi.org/project/scp/) to implement the modules, in the project will will also provide the testcase module and usage example such as the target SSH load testing program. 



#### SSH Connector Introduction

The SSH connector is aimed to create a SSH connector to build a ssh connection tunnel tree to let the user can access and execute command on different hosts through multiple jump hosts in a cluster. It can be apply on below usage scenarios

**Scenario01**: linear connection uses one account to access the targe host through several jump hosts

![](doc/img/rm_03_sce1.png)

- Description: User can pass the SSH command set config to the connector and run the commands set on different hosts in the SSH tunnel chain parallel or in sequence. Each account will be use d to login the hosts once.
- Use case: normal SSH command automated and result collection.
- Connector Configuration:

| SSH command List/Set       | SSH credential            | Thread        | SSH tunnel    |
| -------------------------- | ------------------------- | ------------- | ------------- |
| One list/set for each host | One account for each host | Single thread | Single tunnel |



**Scenario02**: Multiple linear connection use single/multiple account to access the target host through several jump hosts

![](doc/img/rm_04_sce2.png)

- Description: User can pass different SSH command set config to the connector and run different SSH command in parallel thread run the command set with same account on the host in the SSH tunnel chain at the same time. Each account will be used to login the hosts multiple times.
- Use case: Cluster nodes stress test or traffic generation.
- Connector Configuration:

| SSH command List/Set            | SSH credential                 | Thread          | SSH tunnel      |
| ------------------------------- | ------------------------------ | --------------- | --------------- |
| multiple list/set for each host | multiple account for each host | multiple thread | multiple tunnel |



**Scenario03**: tree connection uses multiple account to access the targe host through several jump hosts

![](doc/img/rm_05_sce3.png)

- Description: User can the connector to build the ssh tunnel tree to run different SSH command in parallel thread. 
- Use case: Linked to cluster server's management interface(ILO or IPMI) to collect the data. 
- Connector Configuration:

| SSH command List/Set            | SSH credential            | Thread          | SSH tunnel      |
| ------------------------------- | ------------------------- | --------------- | --------------- |
| multiple list/set for each host | One account for each host | multiple thread | multiple tunnel |



**Scenario04**: mixed connection uses multiple account to access the targe host through several jump hosts

![](doc/img/rm_06_sce4.png)

- Description: User can use the connector to build the ssh tunnel chain and tree to run different SSH command in parallel thread on different hosts.
- Use case: Loading test for a ssh service such as CTF hands-on VM service cluster. 
- Connector Configuration:

| SSH command List/Set            | SSH credential                  | Thread          | SSH tunnel      |
| ------------------------------- | ------------------------------- | --------------- | --------------- |
| multiple list/set for each host | multiple accounts for each host | multiple thread | multiple tunnel |




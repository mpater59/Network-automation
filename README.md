# Network-automation Overview

## Introduction

This repository contains the work done for my engineering diploma thesis. Its title is "Leaf & Spine Architecture as a Case Study of the Automation of Network Configuration Using Python Programming Language" ("Automatyzacja konfiguracji sieci teleinformatycznych przy użyciu języka programowania Python na przykładzie architektury Leaf & Spine" in Polish).

## Project description

This project is about the automation of telecommunication networks using the Python programming language. For this purpose, I've created a system that would allow for the automatic creation and management of networks in data centers based on the Leaf & Spine architecture.

The diagram below shows the general architecture of my system for automating ICT networks.

![schemat_ang](https://user-images.githubusercontent.com/32270817/230618742-416253c1-c2d6-4bdd-9ab8-1fe3f796e77e.PNG)


### 1. Management

The heart of this project was the management machine. On it were python scripts and yaml files that allowed for automatic configuration of Cumulus VX devices in the topology. 
The source codes in this project have been divided into 3 modules: Devices_configuration, Update_database and Sites_configuration. 
Each of them was responsible for different operations, which could then be used by scripts to automate appropriate things in the topology.
In addition, this machine was used to connect to the database containing the configurations stored in it and to the network devices themselves in the topology.


### 2. Description of devices and domains

As part of this project, some scripts required YAML files to work properly, which would contain relevant information about the device configuration or topology. 
The YAML_exmaples folder contains examples of this type of files that were used in this project.


### 3. NoSQL Database MongoDB

In this project, an additional NoSQL MongoDB database was implemented, which was to store current and archived configurations from a given network node. 
With its help, it was possible to automatically restore previous configuration versions on network devices.


### 4. Device configuration description

In this project, it was required to create additional YAML files, which would hold basic information about each of the active nodes and domains. 
Their need results primarily from the operating characteristics of the Netmiko library, which require appropriate information to set up SSH connections between the managemenet device and a given network node.


### 5. Emulated network infrastracture

In this project I designed my own topology in which I could implement and test my created system. 
In the figure below you can see its final form.

![topologia_cala](https://user-images.githubusercontent.com/32270817/230609993-b57adad1-f0fc-45f7-bd39-9a25fe0f5c8b.PNG)

This topology was designed in accordance with the Leaf & Spine architecture, which between Leaf switches allowed the hosts attached to them to communicate using VxLAN technology. 
All this has been implemented in the GNS3 network emulator using virtual L2/L3 Cumulus VX switches that are used in data centers.


## System use cases

My system allows you to automate the following operations:

1. Ability to modify configuration in network nodes using YAML files,
2. Ability to restore previous configuration versions on selected network nodes,
3. Ability to automatically add and remove network nodes from the topology in the Leaf & Spine architecture,
4. Ability to automatically add, remove and migrate VxLAN settings on selected network nodes.

All of this operations can be achieved with appropriate python scripts.
To learn how to use it, you can use the ``-h`` or ``--help`` flag to display optional parameters.


## Project remarks

It is worth noting that this network automation system is only a prototype in which many different aspects could be improved.
The most important things I would improve in this project is the quality of the source codes, because during this project I was still learning how to write properly in Python.
In addition, I would also add the possibility of parallel connection to network machines in the topology to this system, because as of now, all changes to the devices are made serially, which can sometimes significantly delay the operation of this automation.

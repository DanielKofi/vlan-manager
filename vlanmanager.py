#!/usr/bin/env python

# 58f3.9cf6.038c
import re
from netmiko import ConnectHandler 
import netmiko
import getpass
import os
import sys
import time
from vlandata import vlans



global ip
#ip address of 1 of the pair of nexus core switch
ip = '10.10.10.253'


def menu():
    
    print('     *****************************************************')
    print('     *           IOE UCL Desktop Manager                 *')   
    print('     *                                                   *')
    print('     *            1. Change vlan via MAC                 *')
    print('     *                                                   *')
    print('     *                                                   *')
    print('     *                  2. Exit                          *') 
    print('     *****************************************************')
    
    choice = input('                        :')
    choice = int(choice)
    if choice == 1:
        getCred()
    elif choice ==2:
        print('exiting program......') 
        sys.exit(2)
    else:
        ('Please enter a Valid Selection')


# Prompt for Credentials
def getCred(): 
    global UN
    global PW
    global EP
    UN = raw_input("Username : ")
    PW = getpass.getpass("Password : ")
    EP = getpass.getpass("Enable Password :")
    inputMac()

# Input mac address
def inputMac():
    global macr
    macr = raw_input('         Enter Mac Address: ')
    print(macr)
    formatMac()

# Valid Mac address 
def formatMac():
    global mac
    mac = macr
    mac = re.sub('[.:-]', '', mac).lower() 
    mac = ''.join(mac.split())   
    if len(mac) != 12:
        print('len should be exacly 12')
        inputMac()
        
    elif mac.isalnum() == False:
        print('should only contain numbers and letters')
        inputMac()
    mac = ".".join(["%s%s%s%s" % (mac[i], mac[i+1], mac[i+2], mac[i+3]) for i in range(0,12,4)])
    sshSwitch()

# Connect to device 
def sshSwitch():
    global connect
    global secret
    try:
        print('checking please wait........')
        connect = ConnectHandler(device_type='cisco_ios'
                                 ,ip=ip
                                 ,username=UN
                                 ,password=PW
                                 ,secret=EP)
    except:
        print('cound not connect to',ip)
        with open('ntpfail.txt','w') as f:
            f.write('script could not log into ' + ip)
    sendMac()

# send show mac address table command
def sendMac(): 
    global macOut
    #macOut = connect.send_command('show mac address-table | inc {}'.format(mac))
    macOut = connect.send_command('show mac address-table | inc %s'%(mac))
    if 'Peer-Link' in macOut:
        peer()
    elif macOut == "":
        print('Mac Address not found')
        time.sleep(2)
        menu()
    elif 'Gi' in macOut:
        GiRegEx()
    PoRegEx()

def peer():
    global ip
    ip = '10.10.10.252'
    sshSwitch()    

# grab port channel inteface from output string
def PoRegEx(): 
    global pc
    pp = 'Po\d+'
    pchan = re.search(pp,macOut)
    pc = pchan.group(0)   
    getEther()  

# send show interface port channel command
def getEther(): 
    global memOut
    memOut = connect.send_command('show int '+ pc +' | inc Members \n')
    EthRegEx()

# grab ethernet interface of port channel  
def EthRegEx(): 
    global ethport
    #global ethportd
    ee = 'Eth\d+\/\d+'
    ether = re.search(ee,memOut)
    ethport = ether.group(0)
    #print('connected to ' + ethport)
    showCdp()

# send show cdp neigbour command    
def showCdp(): 
    global cdpOut
    global ipsub
    pcdp = '-17-107-\d{1,2}'
    cdpOut = connect.send_command('show cdp neighbors interface ' + ethport)
    #print(cdpOut)
    pcdp1 = re.search(pcdp,cdpOut)
    ipsub = pcdp1.group(0)
    CdpRegEx()
    
def CdpRegEx():
    global ethport
    global ip
    host = re.sub('-','.',ipsub)
    ip = ('172' + host)
    #print('connected to',ip)
    sshSwitch()
    
# grab interface on switch
def GiRegEx(): 
    global pt
    gp = 'Gi\d\/\d\/\d+'
    gpint = re.search(gp,macOut)
    pt = gpint.group(0)
    #print('Device Connected to {} on {}'.format(ip,pt))
    print('Device Connected to %s on %s'%(ip,pt))

    configSwitchInt()
    
    
def configSwitchInt():
    connect.enable()
    connect.config_mode()
    configSwitchVlan()

def configSwitchVlan():
    global getPc
    global vlan
    print('1:  763  128.41.63.0/24_UCL_Desktop')
    print('2:  757  128.41.57.0/24_UCL_Desktop')
    print('3:  Other Vlan                     ') 
    choice = input('Choose Vlan: ')
  
    choice = int(choice)
    if choice == 1:
        vlan = '763'
    elif choice ==2:
        vlan = '757'
    elif choice ==3:
        vlan = input('Enter Vlan:')
    else:
        if choice != 1 or 2:
            ('Print please enter a vlaid selection')
            configSwitchVlan()
    
    #cmd = ['interface {}'.format(pt),'sw ac vl {}'.format(vlan)]
    cmd = ['interface %s'%(pt),'sw ac vl %s'%(vlan)]       
    outVlan = connect.send_config_set(cmd)   
    print(outVlan)
    logChange()
 
  
def logChange():
    global now
    now = time.strftime("%c")
    #print(' changed {} {} to Vlan {}'.format(ip,pt,vlan))
    print(' changed %s %s to Vlan %s'%(ip,pt,vlan))
    with open('ioechange.txt','a') as f:
        #f.write('s:{} changed {} {} to Vlan {} at {} \n'.format(connect.username,ip,pt,vlan, str(now)))
        f.write('%s changed %s %s to Vlan %s at %s \n'%(connect.username,ip,pt,vlan, str(now)))
        eChoice = raw_input('Make another vlan change Y/N')
        if eChoice == 'y':
            inputMac()
        elif eChoice == 'n':
            connect.disconnect()
            sys.exit(2)
            print('exiting program ............')
        
          

menu()
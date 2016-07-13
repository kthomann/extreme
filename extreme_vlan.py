#!/usr/bin/python2
from __future__ import print_function
import sys
from extreme_functions import *


# Require hostname as argument
try:
    hostname = sys.argv[1]
except IndexError:
    print('Hostname or IP not provided')
    exit()

# Require SNMP community as an argument
try:
    snmp_community = sys.argv[2]
except IndexError:
    print('SNMP community not provided')
    exit()

# Require an operation argument, as we need it to know what should be done.
try:
    operation = sys.argv[3]
except IndexError:
    print('Operation argument not provided')
    exit()

# The following handles the specific operation options from cacti

# num_indexes returns the count of indexes which are existing
# Usage: extreme_vlan.py <host> <snmpcommunity> num_indexes
# Returns a simple number without newline
if operation == 'num_indexes':
    # Query VLAN Table of the device
    vlans = getvlans(hostname, snmp_community)
    print(len(vlans), end='')
    exit()

# index returns all index values line by line, which is the SNMP ifIndex value
# Usage: extreme_vlan.py <host> <snmpcommunity> index
# Prints only all index values (ifIndex)
if operation == 'index':
    # Query VLAN Table of the device
    vlans = getvlans(hostname, snmp_community)
    for oid, vlanname in vlans.items():
        print(oid)
    exit()

# query needs an additional argument, to know what exactly it should return
if operation == 'query':
    # Assign the name of the queried object to a variable
    try:
        querytype = sys.argv[4]
    except IndexError:
        print('query function needs an argument to know what it should return')
        exit()

    # Usage: extreme_vlan.py <host> <snmpcommunity> query ifIndex
    # returns the ifIndex to the index (which is the ifIndex...), but AFAIK cacti requires it
    # to display it in the query table...
    if querytype == 'ifIndex':
        # Query VLAN Table of the device
        vlans = getvlans(hostname, snmp_community)
        # print the index value with ifIndex and ! as delimiter
        for index in vlans.keys():
            print('{}!{}'.format(index, index))
        exit()

    # Usage: extreme_vlan.py <host> <snmpcommunity> query vlanTag
    # Returns the index value with the VLAN description (if it's configured per VLAN)
    if querytype == 'vlanTag':
        # Query VLAN Table of the device
        vlans = getvlans(hostname, snmp_community)
        # Query the VLAN tag values from the Extreme VLAN MIB and replace the VLAN name with the
        # VLAN tags as the dict isn't used again we can modify it
        for ifIndex in vlans.keys():
            # Generate Extreme VLAN MIB OID for the specific vlan
            vlantagoid = '.1.3.6.1.4.1.1916.1.2.1.2.1.10.' + ifIndex
            # Update the dict with the specific snmpget value
            vlans[ifIndex] = snmpget(hostname, vlantagoid, snmp_community)

        # print the index value with VLAN tag (VLAN ID) and ! as delimiter
        for index, vlanid in vlans.items():
            print('{}!{}'.format(index, vlanid))
        exit()

    # Usage: extreme_vlan.py <host> <snmpcommunity> query ifName
    # returns the index value with the VLAN name used on the device
    if querytype == 'ifName':
        # Query VLAN Table of the device
        vlans = getvlans(hostname, snmp_community)
        # print the index value with ifName (VLAN Name) and ! as delimiter
        for index, vlanname in vlans.items():
            print('{}!{}'.format(index, vlanname))
        exit()

    # Usage: extreme_vlan.py <host> <snmpcommunity> query ifAlias
    # returns the index value with the VLAN description (if it's configured per VLAN)
    if querytype == 'ifAlias':
        # Query VLAN Table of the device
        vlans = getvlans(hostname, snmp_community)
        # Query the ifAlias values from the IETF IF:MIB and replace the VLAN name with the description
        # as the dict isn't used again we can modify it
        for ifIndex in vlans.keys():
            # Generate IF:MIB OID for the specific vlan
            ifmiboid = '.1.3.6.1.2.1.31.1.1.1.18.' + ifIndex
            # Update the dict with the specific snmpget value
            vlans[ifIndex] = snmpget(hostname, ifmiboid, snmp_community)

        # print the index value with ifAlias (VLAN description) and ! as delimiter
        for index, vlanname in vlans.items():
            print('{}!{}'.format(index, vlanname))
        exit()

    # Usage: extreme_vlan.py <host> <snmpcommunity> query ipAddress
    # returns the index value with the IP address of the VLAN (if it's configured)
    if querytype == 'ipAddress':
        # Query VLAN Table of the device
        vlans = getvlans(hostname, snmp_community)
        # Query the IP Addresses values from the Extreme VLAN MIB and replace the VLAN name with the IP
        # as the dict isn't used again we can modify it
        for ifIndex in vlans.keys():
            # Generate Extreme MIB OID for the specific vlan
            ipoid = '.1.3.6.1.4.1.1916.1.2.4.1.1.1.' + ifIndex
            # Update the dict with the specific snmpget value
            vlans[ifIndex] = snmpget(hostname, ipoid, snmp_community, pretty=True)

        # Print the index value with ifAlias (VLAN description) and ! as delimiter
        for index, vlanname in vlans.items():
            print('{}!{}'.format(index, vlanname))
        exit()

    # Print notice if no query argument has matched
    print('No usable query argument found, please check your arguments')
    exit()

# get return a requested value for the graph's rrd file, needs two additional arguments
# Usage: extreme_vlan.py <host> <snmpcommunity> get <receive|transmit> <index>
if operation == 'get':
    try:
        direction = sys.argv[4]
    except IndexError:
        print('get function needs an argument to know what it should return (receive|transmit)')
        exit()

    try:
        index = sys.argv[5]
    except IndexError:
        print('No index provided for which the data should be returned')
        exit()

    # Create variable which stores the snmp byte value
    bytes = 0
    if direction == 'receive' or direction == 'transmit':
        # Do some generic functions which are direction independent
        # Get the VLAN name from the provided index
        vlanname = getvlannamefromindex(index, getvlans(hostname, snmp_community))
        # Now we need the same format of the VLAN name as in the oid within the stats dict
        oidcode = getintegername(vlanname)

    if direction == 'receive':
        # Query all available data for vlans which have monitoring enabled
        stats = getstatistics(direction, hostname, snmp_community)
        # Count all values from matching oid's in the byte variable
        for oid, bytecount in stats.items():
            if oidcode in oid:
                bytes += bytecount
        print(bytes, end='')
        exit()

    if direction == 'transmit':
        # Query all available data for vlans which have monitoring enabled
        stats = getstatistics(direction, hostname, snmp_community)
        # Count all values from matching oid's in the byte variable
        for oid, bytecount in stats.items():
            if oidcode in oid:
                bytes += bytecount
        print(bytes, end='')
        exit()

    print('No usable direction provided')
    exit()

# Print error notice, if no operation argument matched
print('No usable operation argument found, please check your arguments')

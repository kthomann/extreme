from pysnmp.entity.rfc3413.oneliner import cmdgen


# Simple snmpwalk implementation which returns the oid and value based on the example from pysnmp site.
def snmpwalk(host, oid, community):
    result = dict()
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        oid,
    )

    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex) - 1] or '?'
            )
                  )
        else:
            result = dict()
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    result[name.prettyPrint()] = val.prettyPrint()
    return result


# Simple snmgget which returns the value of the oid with a small hack
def snmpget(host, oid, community, pretty=False):
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        cmdgen.CommunityData(community, mpModel=1),
        cmdgen.UdpTransportTarget((host, 161)),
        oid, )

    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1] or '?'
            )
                  )
        else:
            # Need the "pretty" hack to control the formatting for IP addresses
            # If it shouldn't be pretty return the value
            if pretty == False:
                return varBinds[0][1]
            else:
                # Output should be "pretty"
                # If there is no output return the empty value instead of "No Such Instance ..." message
                # as it isn't the type of "pretty" I want
                if varBinds[0][1] == '':
                    return varBinds[0][1]
                else:
                    # There is printable output and it should be "pretty" -> i.e readable IP Addresses
                    # instead of unreadable garbage output
                    return varBinds[0][1].prettyPrint()


# Builds a dict with all oid, vlanname mappings via snmpwalk
# Output is processed to only return the ifIndex of the VLAN and not the whole oid
def getvlans(host, community):
    oidvlan = dict()
    for oid, vlanname in snmpwalk(host, 'iso.3.6.1.4.1.1916.1.2.1.2.1.2', community).items():
        key = oid.rstrip('"').split('.')[-1]
        oidvlan[key] = vlanname
    return oidvlan


# Needs to know if it should return transmit or receive value, and returns all
# VLAN + byte count values
def getstatistics(direction, host, community):
    oidstat = dict()
    if direction == 'receive':
        baseoid = 'iso.3.6.1.4.1.1916.1.2.8.2.1.7'
    if direction == 'transmit':
        baseoid = 'iso.3.6.1.4.1.1916.1.2.8.2.1.12'

    if baseoid:
        for oid, value in snmpwalk(host, baseoid, community).items():
            key = oid.rstrip('"')
            oidstat[key] = int(value)
    return oidstat


# Returns the name of the VLAN from the index and the provided dict of VLANs from getvlans()
def getvlannamefromindex(index, vlans):
    name = None
    for ifIndex, vlanname in vlans.items():
        if ifIndex == index:
            name = vlanname
            break
    return name

# We need the name of the vlan encoded as integers and separated with "."
def getintegername(name):
    integername = ''
    for char in name:
        # convert the character of the name to an int and append it to the string
        integername = integername + str(ord(char)) + '.'
    # return the converted string without the last "."
    return integername[0:-2]
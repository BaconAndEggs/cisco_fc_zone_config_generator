#!/usr/bin/python

######################################################
#
#   This script is used to write zone configuration
#       data for Cisco SAN fabrick switches.
#
######################################################

import sys

try:
    from optparse import OptionParser
except:
    sys.stderr.write('Failed to load "optparse" module.')
    sys.exit(1)

usage = """
%prog -a [HBA List File] -s [SAN Interface List File] -v [vsan number] -t [1:1|1:many] -z [zonesetName] -o [Configuration Cmds Out File]

This script is used to generate zone configuration
commands to be pasted into a Cisco NX-OS config.

You must provide it 2 files.
1 file containing a list of HBAs (eg: ESX blade adapter WWN numbers).
1 file containing a list of SAN interfaces on the fabric (eg: storage processor interface WWNs).

We know that 1:1 zoning (the "-t 1:1" option) will reliably isolate traffic between individual source and destination interfaces.
The "-t 1:many" option is experimental; it would reduce the number of zones greatly, howeve, it would allow traffic to be seen between multiple SAN interfaces (as well as interfaces from seperate sans in the 1:many zones).
"""

def printFullUsageInfo():
    print """
There are 2 ways to use this zone data:

Use 1) If you have an existing zoneset, and you are only adding a couple new zones, you can enter configuration mode and paste in configuration for 1 zone at a time:

    Telnet or SSH into your fabric switch, then after logging in
    execute the following:
        conf t

    Then paste the configuration text for a single zone into the terminal, and repeat for each zone.

    When done adding the zones, you must add each new zone as a member of the active zoneset.
        zoneset name <existing zoneset name> vsan <vsan#>
        member <new zone name>

    Then type "exit" to exit zoneset configuration, and run the command
        zoneset activate name <new zoneset name>
        exit

    To save the configuration type:
        copy run start

Use 2) If you are reconfiguring an existing fabric with many zones then you will want to do the following:

    Schedule a time for the fabric to be shutdown.

    Telnet, or ssh into your switch, and copy your running-configuration, or startup-configuration, to some network storage using either TFTP, FTP, or SCP.

    Connect to the network storage you copied the config to.

    Make a backup copy of your switch configuration in case we make an error during our edit.

    Open the configuration file for editing, as well as the newly generated zone config data.

    Remove all zone and zoneset configuration data from your switch configuration.

    Select and copy the new zone, and zoneset, configuration data, and paste it into the appropriate section of your switch configuration file (it should be at the end, right before the "zoneset activate name <zoneset name>"configuration line).

    If using a new zoneset name, change the "zoneset activate" line to identify your new zoneset for activation.

    Save the switch configuration you edited offline.

    Connect back into the Nexus using a console cable (because we will lose network management configuration), and download your switch configuration to bootflash: using TFTP, FTP, or SCP.

    Run "write erase" to erase the startup configuration.

    Run "reload".

    Configure an initial admin login and password, and exit any additional configuration wizard.

    Copy the configuration you had edited offline, and saved to bootflash:, to running-configuration (#copy bootflash:new1to1config running-configuration).

    Copy the new running configuration to the startup configuration (#copy run start), and reload the switch and check if everything works after booting with the new configursation.

To check for active membership in the zoneset run:
    show zoneset active vsan <vsan#>

To check which zoneset is active enter:
    show zoneset brief
    """



# Gather command line arguments
optionParser = OptionParser(usage=usage)

optionParser.add_option("-a", "--hbalistfile",action="store", type="string", dest="HBAListFile")
optionParser.add_option("-s", "--saninterfacelistfile", action="store", type="string", dest="SANInterfaceListFile")
optionParser.add_option("-v", "--vsan", action="store", type="string", dest="vsan")
optionParser.add_option("-t", "--zonetype", action="store", dest="zonetype", default="1:1")
optionParser.add_option("-z", "--zonesetName", action="store", type="string", dest="zonesetName")
optionParser.add_option("-o", "--outfile", action="store", type="string", dest="OutputFilePath")
optionParser.add_option("-u", "--fullUsage", action="store_true", dest="HowToUseData", default=False)

(options, args) = optionParser.parse_args()

# Print extended use data if requested
if options.HowToUseData:
    optionParser.print_help()
    print "\n"
    printFullUsageInfo()
    sys.exit(0)

# Make sure all of our required arguments are there
if options.HBAListFile is None:
    print "The --hbalistfile was not specified.\n"
    optionParser.print_help()
    sys.exit(1)

if options.SANInterfaceListFile is None:
    print "The --saninterfacelistfile was not specified.\n"
    optionParser.print_help()
    sys.exit(1)

if options.OutputFilePath is None:
    print "The --outfile was not specified.\n"
    optionParser.print_help()
    sys.exit(1)

if options.vsan is None:
    print "The --vsan option was not specified.\n"
    optionParser.print_help()
    sys.exit(1)

if options.zonesetName is None:
    print "The --zonesetName option was not specified.\n"
    optionParser.print_help()
    sys.exit(1)

# If zone model is specified make sure it is an acceptable value
if not (options.zonetype == "1:1" or options.zonetype == "1:many"):
    print "If the --zonetype option is used it must be set to either \"1:1\" or \"1:many\".\n"
    optionParser.print_help()
    sys.exit(1)

HBAListFile = options.HBAListFile
SANInterfaceListFile = options.SANInterfaceListFile
vsan = options.vsan
zonetype = options.zonetype
OutputFilePath = options.OutputFilePath
zonesetName = options.zonesetName
zonelist = []

print "zonetype is: " + zonetype

# Actually open our files
fHBAListFile = open(HBAListFile, "r")
fSANInterfaceListFile = open(SANInterfaceListFile, "r")
fOutputFilePath = open(OutputFilePath, "w")

# Build a dictionary from our HBA interfaces PWWN Alias list file.
SANIntListDict = {}
for line in fSANInterfaceListFile:
    PWWNAndAlias = str.split(line)
    PWWN = PWWNAndAlias[0]
    Alias = PWWNAndAlias[1]
    # Create our value pairs.
    SANIntListDict[PWWN] = Alias

# For each host interface create a zone with ALL SAN interfaces
for line in fHBAListFile:
    PWWNAndAlias = str.split(line)
    HBAPWWWN = PWWNAndAlias[0]
    HBAAlias = PWWNAndAlias[1]
    if zonetype == "1:many":
        zoneName = "%s_zone" % (HBAAlias)
        fOutputFilePath.write("zone name %s_zone vsan %s \n" % (HBAAlias, vsan))
        fOutputFilePath.write("member pwwn %s \n" % (HBAPWWWN))
        for sanInt in SANIntListDict:
           fOutputFilePath.write("member pwwn %s \n" % (sanInt))
        fOutputFilePath.write("exit")
        fOutputFilePath.write("\n")
        zonelist.append(zoneName)
    elif zonetype == "1:1":
        for sanInt in SANIntListDict:
            zoneName = "%s_%s_zone" % (HBAAlias, SANIntListDict[sanInt])
            fOutputFilePath.write("zone name %s vsan %s \n" % (zoneName, vsan))
            fOutputFilePath.write("    member pwwn %s \n" % (HBAPWWWN))
            fOutputFilePath.write("    member pwwn %s \n" % (sanInt))
            fOutputFilePath.write("exit")
            fOutputFilePath.write("\n")
            zonelist.append(zoneName)
    else:
        print "Script failed, you must specify the zone configuration model from the -t argument."
        sys.exit(1)

# Now we define the zoneset
fOutputFilePath.write("zoneset name %s vsan %s \n" % (zonesetName, vsan))
for zone in zonelist:
    fOutputFilePath.write("    member %s \n" % (zone))

fOutputFilePath.write("\n")

print """
Finished writing zone configuration commands to the text file %s.\n

""" % (OutputFilePath)



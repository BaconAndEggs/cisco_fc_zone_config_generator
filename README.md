cisco_fc_zone_config_generator
==============================

   This is a simple script that can be used to generate large single
initiator zonesets for fc zoning.  Basically, you create a couple text files,
one file with the storage array interface addresses in the format:
<WWN> <TextNameForInterface>
and another text file with the client HBA WWNs and unique text names, in 
the same format.

Then you can run the script with the appropriate params for either 1:1,
 or 1:many single initiator zones, and a text file is generated that can be
pasted into your MDS/NXOS config terminal.



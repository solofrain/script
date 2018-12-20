# #############################################################################
#
#  This script is used to read/write the RDBD field of the motor axes in 
#  associated with PMAC controllers in a IOC server.
#
#  Usage:
#
#      Put this script in an IOC server and run:
#
#          python pmac_rdbd.py [-t ioc_name] [-s] [-r file_name] [mag] 
#
#  1. An IOC is considered to be a PMAC IOC if pmacStatus.substitutions 
#     exists in /epics/iocs/$(ioc_name)/db/ folder. Only the running IOCs 
#     are concerned.
#
#  2. Axis information is extracted from motorstatus.substitutions in
#     /epics/iocs/$(ioc_name)/db/ folder.
#
#  3. RDBD is calculated as
#         RDBD = MRES * mag
#     where x is the input argument when calling the script.
#
#  4. The changes are recorded in $(hostname).pmac.rdbd.$(%Y%m%d-%H%M%S)
#     in the current folder.
#
#------------------------------------------------------------------------------
#
#  Author:
#      Ji Li <liji@bnl.gov>
#
# #############################################################################
import sys
import os
import socket
import datetime


num_axis = 0

iocs = [ [0 for col in range(1)] for row in range(1)]
axes = [ [0 for col in range(1)] for row in range(1)]


#========================================================
# Get the list of the IOCs
#--------------------------------------------------------
def get_iocs():
    global iocs
    
    os.system('manage-iocs status > ' + IOC_LIST_FILE)

    with open (IOC_LIST_FILE, 'r' ) as f:
        for line in f:
            if 'Running' in line:
                ind = line.find('\t')
                ioc = line[20:ind]
                key = IOCS_ROOT + '/' + ioc + '/db/' + MOTOR_FILE
                if (os.path.exists(key)):
                    print('\n\nFind PMAC IOC %s' %(ioc))
                    iocs.append(ioc)
    f.close()
    
    #os.system('rm ' + IOC_LIST_FILE)

    iocs.pop(0)
    iocs.sort()
    #print(iocs)
#========================================================


#========================================================
def read_axes():
    for ioc in iocs:
        sub_file = IOCS_ROOT + '/' + ioc + '/db/' + MOTOR_FILE      # from which file we get the axis
                
        with open (sub_file, 'r') as sub:
            for line in sub:
#                if 'pmacStatusAxis' in line:    # all the axis have been found
#                    break
                            
                if ('\"XF:' in line) and (not ('#' in line)): # find the lines with information
                    for j in range(0,4):    # for all "
                        ind = line.index('\"')
                                
                        if j==0 or j==2:
                           line = line[ind+1:len(line)]
                        else:
                            if j==1:
                                axis = line[0:ind]
                                line = line[ind+1:len(line)]
                            else:
                                #if 'Mtr' in line:
                                axis = axis + line[0:ind]
                                #else:
                                #    axis = axis + '{' + line[1:ind-1] + '}Mtr'
                                axes.append(axis)
                                update_field(ioc, axis)
                                #if (update_field(axis)<0):
                                #    sub.close()
                                #    return(-1)
                            # end of if j==1:
                        # end of if j==0 or j==2
                   # end of for j in range(0,4):
                # end of if '\"XF:' in line:
            # end of  for line in sub:
        sub.close()
        # end of  with open (sub_file, 'r') as sub:
    # end of  for dir in iocs:

#========================================================

#========================================================
# Main program.
#--------------------------------------------------------
# 0. Variable initialization
host = socket.gethostname()
IOCS_ROOT = '/epics/iocs'
DB_DIR = 'db'
KEY_FILE = 'pmacStatus.substitutions'
MOTOR_FILE = 'motor.substitutions'
IOC_LIST_FILE = 'ioc.list'

print('\n\n')

#--------------------------------------------------------
# 1. Command-line arguments parsing
#if (parse_cmd()<0):
#    sys.exit()

#--------------------------------------------------------
# 2. Get IOC list, and add the running ones to the list
#get_iocs()

#--------------------------------------------------------
# 3. Operation
#if op_mode==RECOVERY_MODE:
#    restore_field()
#else:
read_axes()


#--------------------------------------------------------    
# 4. log processing


#--------------------------------------------------------
# 5. End of operation
print('\n*********************************************************\n')
print('End of operation.\n')

if len(axes)>1:
    axes.pop(0)

    axis_file = host + '.axix.' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    f = open(axis_file, 'w')
    for axis in axes:
        f.write(axis)
        f.write('\n')
    f.close()
    
    print('See %s for all axes.\n' %(axis_file))

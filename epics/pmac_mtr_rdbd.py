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
from epics import caget, caput


# operation mode
NULL_MODE = -1
READ_MODE = 1
WRITE_MODE = READ_MODE + 1
TEST_MODE = WRITE_MODE + 1
RECOVERY_MODE = TEST_MODE + 1

op_mode = NULL_MODE
mag = 1
num_axis = 0

logs = [ [0 for col in range(1)] for row in range(1)]
fail_logs = [ [0 for col in range(1)] for row in range(1)]
iocs = [ [0 for col in range(1)] for row in range(1)]
axes = [ [0 for col in range(1)] for row in range(1)]



#========================================================
# Parse the command-line arguments
#--------------------------------------------------------
def input_error():
    print('Input error.')
    print('Usage:\n\tpython pmac_rdbd.py [-t ioc_name] [-s] [-r file_name] [mag] \n')
    print('\t-t : TEST mode')
    print('\t-s : READ mode')
    print('\t-r : RESTORE mode (not implemented yet)')
    print('\tThe default mode is WRITE mode.')
    print('\tmag is mandatory for test mode and write mode.')
#========================================================


#========================================================
# Parse the command-line arguments
#--------------------------------------------------------
def parse_cmd():
    
    global op_mode
    global mag
    global iocs
    
    if '-r' in sys.argv:    # recovery mode. make sure the file exists
        index = sys.argv.index('-r')
        
        if ('-s' in sys.argv) or ('-t' in sys.argv) or (len(sys.argv)<index+1):
            input_error()
            return(-1)
        
        sys.argv.pop(index)
        recovery_file = os.getcwd() + '/' + sys.argv[index]
        if not os.path.exists(recovery_file):
            print('Please enter correct filename')
            return(-1)
            
        sys.argv.pop(index)
        get_iocs()
        op_mode = RECOVERY_MODE

    elif '-s' in sys.argv:  # read mode. only display the value of MRES and RDBD
        index = sys.argv.index('-s')
        
        if ('-r' in sys.argv):
            input_error()
            return(-1)
            
        sys.argv.pop(index)
        get_iocs()
        op_mode = READ_MODE
        
    elif '-t' in sys.argv:    # test mode
        index = sys.argv.index('-t')
        
        if len(sys.argv) < 4:   # at least 4 arguments for test mode
            input_error()
            return(-1)
            
        sys.argv.pop(index)
        iocs.append(sys.argv[index])
        iocs.pop(0)
        sys.argv.pop(index)
        op_mode = TEST_MODE
        
        
    elif len(sys.argv)<2:
        input_error()
        return(-1)
    
    else:
        mag = float(sys.argv[1])
        get_iocs()
        op_mode = WRITE_MODE
        
    return(0)
#========================================================
    
    


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
                key = IOCS_ROOT + '/' + ioc + '/db/' + KEY_FILE
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
# Update the fields
#--------------------------------------------------------
def update_field(ioc, axis):
    global logs
    global num_axis
    
    # get the PV names for the axis
    mres = axis + '.MRES'
    rdbd = axis + '.RDBD'

    logs.append(axis)
    
    mres_rdbv = caget(mres)
    if mres_rdbv is None:
        fail_logs.append(ioc +': ' + mres)
        print('Error: failed in caget %s' %(mres))
        return
    logs.append('%s: %f' %(mres, (mres_rdbv)))

    rdbd_rdbv = caget(rdbd)
    if rdbd_rdbv is None:
        fail_logs.append(ioc +': ' + rdbd)
        print('Error: failed in caget %s' %(rdbd))
        return
    logs.append('%s (current value): %f' %(rdbd, (rdbd_rdbv)))

    if (op_mode==WRITE_MODE) or (op_mode==TEST_MODE):
        rdbd_sp = mres_rdbv * mag
        val = caput(rdbd, rdbd_sp, wait=True)
        #val = 0
        if val is None:
            fail_logs.append(ioc +': ' + rdbd)
            print('Error: failed in caput %s' %(rdbd))
            return
        logs.append('%s (new value): %f' %(rdbd, (rdbd_sp)))

    logs.append('')

    num_axis = num_axis + 1

    return
# end of def update_field
#========================================================


#========================================================
def access_field():
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
# Restore the fields to the previous value stored in
# the log file.
#--------------------------------------------------------
def restore_field():
    print('This function has not been implemented yet.')
    
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
if (parse_cmd()<0):
    sys.exit()

#--------------------------------------------------------
# 2. Get IOC list, and add the running ones to the list
#get_iocs()

#--------------------------------------------------------
# 3. Operation
if op_mode==RECOVERY_MODE:
    restore_field()
else:
    access_field()


#--------------------------------------------------------    
# 4. log processing
if len(logs)>1:
    logs.pop(0)

    log_file = host + '.pmac.rdbd.' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    f = open(log_file, 'w')
    for log in logs:
        f.write(log)
        f.write('\n')
    f.close()    

if len(axes)>1:
    axes.pop(0)

    axis_file = host + '.axix.' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    f = open(axis_file, 'w')
    for axis in axes:
        f.write(axis)
        f.write('\n')
    f.close()

#--------------------------------------------------------
# 5. End of operation
print('\n*********************************************************\n')
print('End of operation.\n' )

if len(fail_logs)>1:
    fail_logs.pop(0)
    print('Failed to access %d PVs.\n' %(len(fail_logs)))
    for i in range(len(fail_logs)):
        print(fail_logs[i])
    print('\n')

if num_axis>0:
    if (op_mode==TEST_MODE) or (op_mode==WRITE_MODE):
        print('%d PVs have been successfully changed.\n' %(num_axis))    
    print('Refer to ' + log_file + ' for details.\n')

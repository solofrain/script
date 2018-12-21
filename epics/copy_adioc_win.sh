#############################################################################################################
##
##  This file makes a copy of an pre-built areaDetector. It copies the necessary folders/files from a 
##  pre-built EPICS base and areaDetector IOC. Unneeded folders/files are neglected. This reduces the size
##  of the IOCs from GBs to MBs.
##
##===========================================================================================================
##  
##  The structure of the folder containing the pre-built EPICS base and synApps modules should be:
##
##     C:\----epics
##              |
##              |----base-x.x
##              |
##              |----synApps
##                      |
##                      |----Rx-x
##                            |
##                            |----support
##                                    |
##                                    |----areaDetector-x-x/
##                                    |
##                                    |----asyn-x-x
##                                    |
##                                    |----autosave-x-x
##                                    |
##                                    |----busy-x-x
##                                    |
##                                    |----calc-x-x
##                                    |
##                                    |----iocStats-x-x-x (or devIocStats-x-x-x)
##                                    |
##                                    |----seq-x-x-x
##                                    |
##                                    |----sscan-x-x-x
##
##  The script picks the latest version for each module.
##
##===========================================================================================================
##
##  Folders:
##
##    . base-x.x/bin/windows-x64-static/
##
##    . synApps/Rx-x/support/areaDetector-x-x/ADCore/db/
##    . synApps/Rx-x/support/areaDetector-x-x/ADCore/iocBoot/
##    . synApps/Rx-x/support/areaDetector-x-x/ADCore/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/areaDetector-x-x/ADPerkinElmer/bin/windows-x64-static/
##    . synApps/Rx-x/support/areaDetector-x-x/ADPerkinElmer/db/
##    . synApps/Rx-x/support/areaDetector-x-x/ADPerkinElmer/iocs/perkinElmerIOC/bin/windows-x64-static/
##    . synApps/Rx-x/support/areaDetector-x-x/ADPerkinElmer/iocs/perkinElmerIOC/dbd/
##    . synApps/Rx-x/support/areaDetector-x-x/ADPerkinElmer/iocs/perkinElmerIOC/iocBoot/iocPerkinElmer/
##    . synApps/Rx-x/support/areaDetector-x-x/ADPerkinElmer/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/areaDetector-x-x/ADSupport/bin/windows-x64-static/
##    . synApps/Rx-x/support/areaDetector-x-x/ADSupport/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/asyn-x-x/bin/windows-x64-static/
##    . synApps/Rx-x/support/asyn-x-x/db/
##    . synApps/Rx-x/support/asyn-x-x/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/iocStats-x-x/bin/windows-x64-static/
##    . synApps/Rx-x/support/iocStats-x-x/db/
##    . synApps/Rx-x/support/iocStats-x-x/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/autosave-x-x/bin/
##    . synApps/Rx-x/support/autosave-x-x/asApp/Db/
##    . synApps/Rx-x/support/autosave-x-x/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/busy-x-x/bin/windows-x64-static/
##    . synApps/Rx-x/support/busy-x-x/busyApp/Db/
##    . synApps/Rx-x/support/busy-x-x/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/calc-x-x/calcApp/Db/
##    . synApps/Rx-x/support/calc-x-x/db/
##    . synApps/Rx-x/support/calc-x-x/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/seq-x-x/bin/windows-x64-static/
##    . synApps/Rx-x/support/seq-x-x/lib/windows-x64-static/
##
##    . synApps/Rx-x/support/sscan-x-x/sscanApp/Db/
##    . synApps/Rx-x/support/sscan-x-x/db/
##    . synApps/Rx-x/support/sscan-x-x/lib/windows-x64-static/
##
##===========================================================================================================
##
##  Environment:
##
##    This is a Linux bash script, thus Linux environment is required on the Windows IOC server. One option 
##    to create Linux environment in Windows is to use Cmder, which can be downloaded at:
##        http://cmder.net/
##
##    Other methods should also work, but have not been tested.
##
##===========================================================================================================
##
##  Usage:
##
##    . Put this script on the Windows IOC server;
##    . Specify detector and Detector in line 60 and line 61
##    . In Cmder, run command:
##          bash copy_adioc_win.sh
##    . The IOC is in file
##          AD${Detector}-Prebuilt-windows-x64-static.tar.gz
##
##===========================================================================================================
##
##  Author:
##    Ji Li <liji@bnl.gov>
##
#############################################################################################################
copy_en=1	# Enable copy. Used for debug.

# Detector model
detector="perkinElmer"
Detector="PerkinElmer"

#================================
mkcd()
{
    mkdir "$1" && cd "$1"
}
#================================
get()
{
    echo "Copying $1/ ..."
    if [ $copy_en -eq 1 ]; then
        cp -r "$1" .
    fi
}
#================================
comp()
{
    tar cf "$1" "$2"
}
#================================
	
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Main program
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

synapps_modules=("asyn" "Stat")


build_dir="C:/epics"
base_dir="base-7.0.2-rc1"


if [ -d "epics" ]; then
    rm -rf epics
fi

mkdir epics
cd epics

#*****************************************************
# 1. Copy EPICS base
#*****************************************************
folders=$(ls -r1 $build_dir | grep base)  # use -r to get the latest version

for folder in $folders
do
    base=$folder
	break
done

mkcd $base

base_dir=$build_dir"/"$base

get $base_dir"/bin"

cd ..

#*****************************************************
# 2. Copy synApps modules
#*****************************************************
folders=$(ls -r1 $build_dir | grep synApps)

#echo $folders

for folder in $folders
do
    synapps_dir=$build_dir"/"$folder
	break
done


mkcd synApps

# now in epics/synApps

# Get synApps version
folders=$(ls -r1 $synapps_dir)

for folder in $folders
do
    synapps_ver=$folder
	break
done

support_dir=$synapps_dir"/"$synapps_ver"/support"

mkcd $synapps_ver
mkcd support


#========================================================
# 2.1 Copy the asyn/iocStatus whose bin/, db/, 
#     and lib/ folders are needed.
#========================================================
for synapps_module in ${synapps_modules[*]}
do
	folder=$(ls -r1 $support_dir | grep $synapps_module)
	mkcd $folder
	get $support_dir"/"$folder"/bin"
	get $support_dir"/"$folder"/db"
	get $support_dir"/"$folder"/lib"
	cd ..
done


#========================================================
# 2.2 Copy autosave
#========================================================
folders=$(ls -r1 $support_dir | grep autosave)

for folder in $folders
do
    autosave=$folder
	break
done

autosave_dir=$support_dir"/"$autosave

mkcd $autosave

get $autosave_dir"/bin"

mkcd asApp

get $autosave_dir"/asApp/Db"
cd ..

get $autosave_dir"/lib"

cd ..


#========================================================
# 2.3 Copy busy
#========================================================
folders=$(ls -r1 $support_dir | grep busy)

for folder in $folders
do
    busy=$folder
	break
done

busy_dir=$support_dir"/"$busy

mkcd $busy

get $busy_dir"/bin"

mkcd busyApp

get $busy_dir"/busyApp/Db"
cd ..

get $busy_dir"/lib"

cd ..


#========================================================
# 2.4 Copy calc
#========================================================
folders=$(ls -r1 $support_dir | grep calc)

for folder in $folders
do
    calc=$folder
	break
done

calc_dir=$support_dir"/"$calc

mkcd $calc

mkcd calcApp

get $calc_dir"/calcApp/Db"
cd ..

get $calc_dir"/lib"

cd ..


#========================================================
# 2.5 Copy seq
#========================================================
folders=$(ls -r1 $support_dir | grep seq)

for folder in $folders
do
    seq=$folder
	break
done

seq_dir=$support_dir"/"$seq

mkcd $seq

get $seq_dir"/bin"

get $seq_dir"/lib"

cd ..


#========================================================
# 2.6 Copy sscan
#========================================================
folders=$(ls -r1 $support_dir | grep sscan)

for folder in $folders
do
    sscan=$folder
	break
done

sscan_dir=$support_dir"/"$sscan

mkcd $sscan

mkcd sscanApp


get $sscan_dir"/sscanApp/Db"
cd ..

get $sscan_dir"/lib"

cd ..


#========================================================
# 2.7 Copy areaDetector
#========================================================

# Get areaDetector folder name
folders=$(ls -r1 $support_dir | grep areaDetector)

for folder in $folders
do
    areadetector=$folder
	break
done

areadetector_ver=${areadetector:13}
areadetector_ver=${areadetector_ver//-/.}

echo $areadetector_ver

areadetector_dir=$support_dir"/"$areadetector

mkcd $areadetector


#----------------------------------------------------
# 2.7.1 synApps/Rx-x/support/areaDetector-x-x/ADCore/
#----------------------------------------------------
folders=$(ls -r1 $areadetector_dir | grep ADCore)

for folder in $folders
do
    adcore=$folder
	break
done
adcore_dir=$areadetector_dir"/"$adcore

mkcd $adcore

# db/

get $adcore_dir"/db"


mkcd ADApp

get $adcore_dir"/ADApp/Db"

cd ..

# iocBoot/
get $adcore_dir"/iocBoot"

# lib/
get $adcore_dir"/lib"

cd ..


#----------------------------------------------------
# 2.7.2 synApps/Rx-x/support/areaDetector-x-x/AD$Detector/
#----------------------------------------------------
folders=$(ls -r1 $areadetector_dir | grep "AD"$Detector)

for folder in $folders
do
    addetector=$folder
	break
done
addetector_dir=$areadetector_dir"/"$addetector

mkcd $addetector

# bin/
get $addetector_dir"/bin"


#db/
get $addetector_dir"/db"


#iocs/perkinElmerIOC/bin/
mkcd iocs
mkcd $detector"IOC"

ioc_dir=$addetector_dir"/iocs/"$detector"IOC"

get $ioc_dir"/bin"


# iocs/perkinElmerIOC/dbd/
get $ioc_dir"/dbd"


# iocs/perkinElmerIOC/iocBoot/
get $ioc_dir"/iocBoot"

cd ../..


# lib/windows-x64-static/
get $addetector_dir"/lib"

# perkinElmerApp/Db/
mkcd $detector"App"

get $addetector_dir"/"$detector"App/Db"

cd ../..


#----------------------------------------------------
# 2.9.10 synApps/Rx-x/support/areaDetector-x-x/ADSupport/
#----------------------------------------------------
folders=$(ls -r1 $areadetector_dir | grep ADSupport)

for folder in $folders
do
    adsupport=$folder
	break
done
adsupport_dir=$areadetector_dir"/"$adsupport

mkcd $adsupport

# bin/
get $adsupport_dir"/bin"


# lib/
get $adsupport_dir"/lib"


#*****************************************************
# 3. Clean up
#*****************************************************
cd ../../../../../..

comp $Detector"-AD"$areadetector_ver"-Prebuilt-windows-x64-static.tar.gz" epics

#rm -rf epics

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

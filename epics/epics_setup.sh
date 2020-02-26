#!/bin/bash
################################################################################
#
#  This script creates EPICS environment.
#
#  On most IOC servers at NSLS-II, EPICS base and modules are installed as 
#  Debian packages and are available in /usr/lib/epics/.
#
#  Different versions of EPICS bases and modules should be installed in
#  /epics/modules/.
#
#  Desired folder structure:
#
#    /--
#      |
#      +--epics
#      |  |
#      |  +--modules
#      |     |
#      |     +--base-xxxx
#      |     |  |
#      |     |  +--modules
#      |     |     |
#      |     |      +--moduleyyyy
#      |     |
#      |     +--modulezzzz
#      |
#      +--usr
#         |
#         +--lib
#            |
#            +epics
#
#================================================================================
#
#  Usage:
#
#    1. Edit this script, change arch/mod_name/mod_ver/dont_care definitions in 
#       step 0.
#    2. Switch user as softioc, and run this script in /epics/modules/.
#    3. If the desired version of EPICS base has been installed, but the 
#       desired version of module doesn't exist, run install_epics_modules.sh
#       with sudo.
#
#================================================================================
#
#  Bugs? Contact: Ji Li <liji@bnl.gov>
#
#################################################################################

#==========================================
# Function:
#   Set the variable definitions
#   in ${MODULE}/configure/RELEASE.
#------------------------------------------
var_correction() {
    # Correct EPICS_BASE
    sed -i "s|^EPICS_BASE.*$|EPICS_BASE=$BASE_DIR|g" RELEASE

    # Correct SUPPORT
    sed -i "s|^SUPPORT.*$|SUPPORT=$SUPPORT_DIR|g" RELEASE

    # Correct the mandatory modules
    for ((k=0;k<num;k++))
    {
        sed -i "s|^${mod_name[k]^^}.*$|${mod_name[k]^^}=\$(SUPPORT)\/${mod_name[k]}-${mod_ver[k]}|g" RELEASE
    }

    # Comment the non-mandatory modules
    num_dont_care=${#dont_care[@]}
    for ((m=0;m<num_dont_care;m++))
    {
        sed -i '/^${dont_care[m]}/ s/^/#/' RELEASE
    }
}


#==========================================
# Function compile_base:
#   Download the source code of the EPICS
#   base and compile.
#------------------------------------------
compile_base() {
    wget -O base-${base_ver}.zip https://codeload.github.com/epics-base/epics-base/zip/${base_ver}
        
    unzip base-${base_ver}.zip
    rm base-${base_ver}.zip
    mv epics-base-${base_ver} base-${base_ver}

    cd base-${base_ver}
    make
}

#==========================================
# Function compile_module:
#   Download the source code of the module
#   and compile against the EPICS base.
#------------------------------------------
compile_module() {
    echo -e "Download source file and compile ${module_name}-${module-version}\n"
    wget -O ${module_version}.zip https://codeload.github.com/epics-modules/${module_name}/zip/${module_version}

    unzip -q ${module_version}.zip
    rm ${module_version}.zip

    cd ${module_name}-${module_version}/configure

    var_correction

    cd ../..

    make

    echo -e "\nInstallation of ${module_name}-${module_version} completed.\n"
}

#***********************************************

clear

my_name=${0##*/}

#==========================================
# 0. Preparation.
#    Define the modules to be installed
#    and the modules appears in 
#    configure/RELEASE files but are 
#    optional. The modules to be installed 
#    must be entered in the sequence of 
#    dependency.
#------------------------------------------

arch='linux-x86_64'

base_ver='R7.0.3.1'

mod_name=()
mod_ver=()

ASYN=${#mod_name[@]}
mod_name[$ASYN]='asyn'
mod_ver[$ASYN]='R4-8'

AUTOSAVE=${#mod_name[@]}
mod_name[$AUTOSAVE]='autosave'
mod_ver[$AUTOSAVE]='R5-10'

BUSY=${#mod_name[@]}
mod_name[$BUSY]='busy'
mod_ver[$BUSY]='R1-7-2'

CALC=${#mod_name[@]}
mod_name[$CALC]='calc'
mod_ver[$CALC]='R3-7-3'

SSCAN=${#mod_name[@]}
mod_name[$SSCAN]='sscan'
mod_ver[$SSCAN]='R2-11-3'

IOCSTATS=${#mod_name[@]}
mod_name[$IOCSTATS]='iocStats'
mod_ver[$IOCSTATS]='3.1.16'


dont_care=('SNCSEQ' 'IPAC' )

num=${#mod_name[@]}

echo -e "The following modules will be installed:\n"
echo "    > base-${base_ver}"

for ((j=0;j<num;j++))
{
#    mod_dir[j]=${SUPPORT_DIR}/${mod_name[j]}-${mod_ver[j]}
    echo "    > ${mod_name[j]}-${mod_ver[j]}"
}
echo -e "\nPress any key to continue..."
read ans

#==========================================
# 1. Install EPICS base
#------------------------------------------
echo -e "=====================================\n"

dpkg -l |grep libepics$base_ver

if [ $? -eq 0 ]; then
    libepics_installed=1
    BASE_DIR="/usr/lib/epics"
    SUPPORT_DIR="/usr/lib/epics"
    
    echo -e "base-${base_ver} already installed\n"
else
    libepics_installed=0
    
    ROOT_DIR=`pwd`
    BASE_DIR=${ROOT_DIR}/base-${base_ver}
    SUPPORT_DIR=${BASE_DIR}/modules

    echo "Installing EPICS base..."
    echo -e "Version: ${base_ver}\n"

    if [ ! -d ${BASE_DIR} ]; then
        ls
        echo -e "base-${base_ver} doesn't exist\n"

        compile_base
        echo -e "\nInstallation of base-${base_ver} completed.\n"
    else
        cd ${BASE_DIR}
        echo -e "\nbase-${base_ver} already installed.\n"
    fi

    cd modules
fi

echo -e "===========================================\n"

#==========================================
# 2. Install modules
#------------------------------------------
pending_mod_index=0
pending_mod_name[0]=" "



if [ $libepics_installed -eq 0 ]; then # if the desired EPICS base has not been installed
    for ((i=0;i<num;i++))
    {
        module_name=${mod_name[i]}
        module_version=${mod_ver[i]}

        echo -e "Processing $[$i+1] of $num: ${module_name}-${module_version}\n"

        if [ -d ${module_name}-${module_version} ]; then
            echo -e "${module_name}-${module_version} already installed.\n"
        else
            echo -e "${module_name}-${module_version} doesn't exist."
            compile_module
        fi

        mod_dir[i]=${SUPPORT_DIR}/${module_name}-${module_version}

        echo -e "===========================================\n"
    }
else
    for ((i=0;i<num;i++))
    {
        module_name=${mod_name[i]}
        module_version=${mod_ver[i]}

        dpkg -l | grep epics-${mod_name[i]}

        if [ $? -eq 1 ]; then  # The module hasn't been installed, install later as a Debian package.
            pending_mod_name[pending_mod_index]=${mod_name[i]}
            pending_mod_ver[pending_mod_index]=${mod_ver[i]}
        else
            dpkg -l | grep epics-${mod_name[i]} | grep ${mod_ver[i]}
            if [ $? -eq 1 ]; then
                if [ -d ${module_name}-${module_version} ]; then
                    echo -e "${module_name}-${module_version}} already installed.\n"
                else
                    compile_module
                fi
            fi
        fi
    }
fi

#for ((i=0;i<num;i++))
#{
#    module_name=${mod_name[i]}
#    module_version=${mod_ver[i]}
#
#    echo -e "Installing $[$i+1] of $num: ${module_name}-${module_version}\n"
#    ls
#    if [ $libepics_installed -eq 0 ]; then # if the desired EPICS base has not been installed
#        if [ -d ${module_name}-${module_ver}} ]; then
#            echo -e "${module_name}-${module_ver}} already installed"
#        else
#            compile_module
#        fi
#
#        echo -e "===========================================\n"
#    else
#        dpkg -l | grep epics-${mod_name[i]}
#
#        if [ $? -eq 1 ]; then  # The module hasn't been installed, install later as a Debian package.
#            pending_mod_name[pending_mod_index]=${mod_name[i]}
#            pending_mod_ver[pending_mod_index]=${mod_ver[i]}
#        else
#           dpkg -l | grep epics-${mod_name[i]} | grep ${mod_ver[i]}
#           if [ $? -eq 1 ]; then
#               if [ -d ${module_name}-${module_ver}} ]; then
#                   echo -e "${module_name}-${module_ver}} already installed"
#               else
#                    compile_module
#               fi
#           fi
#       fi
#    fi
#}

cd ../..

#==========================================
# 3. If the specific version of EPICS base 
#    has been installed and some specific 
#    version of modules have not been 
#    installed, create a script to install
#    these mode later.
#------------------------------------------
#if [ ${#pending_mod_name[0][@]} -gt 2 ]; then
#    echo "Please run install_epics_modules.sh with sudo"
#    echo "to install the following modules, and rerun"
#    echo "${my_name} to install the rest modules."

#    echo '#!/bin/bash' > install_epics_modules.sh
#    num_pending_mod=${#pending_mod_name[@]}
#    for ((n=0;n<num_pemding_mod;n++))
#    {
#        mod="epics-${pending_mod_name[n]}-${pending_mod_ver[n]}"
#        echo "> ${mod}}"
#        echo "apt install ${mod}" >> install_epics_modules.sh
#    }
#    chmod +x install_epics_modules.sh
#fi


#==========================================


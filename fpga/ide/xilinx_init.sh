#!/bin/bash
############################################################
# This script sets the environment for a specific IDE
# (listed in ide[]) installed at locations specified in
# loc[].
############################################################

##======================================
## Preparation.
##======================================

#---------------------------------------
# List all possible IDEs here: 
#     . Vivado
#     . PetaLinux
#     . Vitis
#---------------------------------------
ide=( "Vivado"
      "PetaLinux"
      "Vitis"
     )

#---------------------------------------
# List all possible locations of installations here:
#     . /opt/Xilinx
#     . /home/liji/data/opt/Xilinx
#---------------------------------------
loc=( "/opt/Xilinx"
      "/home/liji/data/opt/Xilinx"
    )



##======================================
clear

source /opt/anaconda3/etc/profile.d/conda.sh
conda activate fpga

num_loc=${#loc[@]}
num_ide=${#ide[@]}

##======================================
## Select the IDE
##======================================

echo -e "\nPlease select the IDE:"

index=0
for ((i=0;i<num_ide;i++))
{
    index=`expr $index + 1`
    echo "    > ${index}. ${ide[${i}]}"
}

read ide_sel
ide_sel=$[ $ide_sel-1 ]
ide=${ide[ide_sel]}

echo -e "\n${ide} selected."

i=0


##-------------------------------------
## Find all the installed versions.
##-------------------------------------
k=0
for ((i=0;i<num_loc;i++))
{
    location=${loc[$i]}/${ide}
#    echo "Search in $location:"
    if [ -d ${location} ]; then
        version=(`ls ${location}`)
        num_version=${#version[@]}
        for ((j=0;j<$num_version;j++,k++))
        {
            ver[$k]=${version[$j]}
            ver_loc[$k]=$i
        }
    fi
}


##======================================
## Select the version.
##======================================
echo -e "\nPlease select the version:"
i=0
for v in ${ver[@]}
do
#    ver[i]=$v
    i=`expr $i + 1`
    echo "    > $i. $v"
done

read ver_sel
ver_sel=`expr $ver_sel - 1`
ver=${ver[ver_sel]}
loc=${loc[${ver_loc[$ver_sel]}]}/${ide}/${ver}
#echo $loc

echo -e "\n$ide $ver selected.\n"

##======================================
## Set environment.
##======================================
if [ $ide = "PetaLinux" ]; then
    source "${loc}/settings.sh"
    export PATH=${loc}/common/petalinux/bin:$PATH
else
    source "${loc}/settings64.sh"
    export PATH=${loc}/bin:$PATH
fi


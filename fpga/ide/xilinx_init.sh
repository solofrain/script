#!/bin/bash
#===========================================================
# This script sets the environment for a specific IDE 
# installed as /opt/Xilinx/${IDE_name}/${Version}.
#===========================================================
clear

ide=("Vivado" "PetaLinux")

num=${#ide[@]}

echo -e "\nPlease select the IDE:"

i=0
index=0
for ((i=0;i<num;i++))
{
    if [ -d /opt/Xilinx/${ide[${i}]} ]; then
        index=`expr $index + 1`
        echo "    > ${index}. ${ide[${i}]}"
    else
        unset ide[$i]
    fi
  
}

read ide_sel
ide_sel=$[ $ide_sel-1 ]
ide=${ide[ide_sel]}


echo -e "\nPlease select the version:"
i=0
version=`ls /opt/Xilinx/${ide[$ide_sel]}`
for v in $version
do
    ver[i]=$v
    i=`expr $i + 1`
    echo "    > $i. $v"
done

read ver_sel
ver_sel=`expr $ver_sel - 1`
ver=${ver[ver_sel]}

echo -e "\n"

if [ $ide = "PetaLinux" ]; then
    source "/opt/Xilinx/${ide}/${ver}/settings.sh"
else
    source "/opt/Xilinx/${ide}/${ver}/settings64.sh"
fi

echo -e "\nEnvironment set to ${ide} ${ver}."

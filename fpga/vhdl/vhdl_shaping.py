#########################################################
# 
# VHDL file reformat.
#
#     . Fix indent.
#
#########################################################
import os, sys


def exit_bracket(line):
    if (')') in line:
        if line.index(')')==0:
            return True
        elif line.count('(')<line.count(')'):
            return True
        else:
            return False

null = "NULL_"
entity = "ENTI_"
entity_generic = "EN_GE"
entity_port = "EN_PO"
arch = "ARCH_"
arch_declare = "AR_DE"
arch_comp = "AR_CO"
arch_comp_generic = "AR_CG"
arch_comp_port = "AR_CP"
arch_body = "AR_BD"
process = "PROCESS"
case    = "CASE_"
generate = "GENERATE"
arch_inst = "ARCH_INST"

#=============================
# argument check
#=============================
if (len(sys.argv)<2):
    print("Please define the VHDL file to be processed.")
    sys.exit()
   
if ( ".vhd" not in sys.argv[1] and
     ".VHD" not in sys.argv[1] ):
    print("This script processes VHDL file only.")
    sys.exit()

new_file = sys.argv[1]
old_file = sys.argv[1]
index =old_file.index(".")
old_file = old_file[0:index] + "_orig" + old_file[index:len(old_file)]

os.system("cp " + new_file + " " + old_file)

#print(new_file)
#print(old_file)

fw = open(new_file, "w")

state = null
indent = 0
indent_pr_adj = 0
indent_po_adj = 0
empty_line = 0

with open(old_file) as fr:
    for line in fr:
        line = line.strip()
        lo_line = line.lower()
        if ' ' in lo_line:
            lo_line = lo_line.replace(' ', '')

        if '\t' in lo_line:
            lo_line = lo_line.replace('\t', '')

        if "--" in lo_line and lo_line.index("--") == 0:
            continue

        if len(lo_line)<2:
            empty_line = empty_line + 1
        else:
            empty_line = 0
            #=========================================
    
            if state == null:
                indent = 0
    
                if "entity" in lo_line:
                    indent_po_adj = 1
                    state = entity
                elif "architecture" in lo_line:
                    indent_po_adj = 1
                    state = arch_declare
    
            elif state == entity:
                if "generic" in lo_line:
                    indent_po_adj = 1
                    state = entity_generic
                elif "port" in lo_line:
                    indent_po_adj = 1
                    state = entity_port
                elif "end" in lo_line:
                    state = arch
    
            elif state == entity_generic:
                if exit_bracket(lo_line):
                #if ')' in lo_line and lo_line.index(')') == 0:
                    state = entity_port
                    indent_pr_adj = -1
                #elif "))" in lo_line:
                #    state = entity_port
                #    indent_pr_adj = -1
    
            elif state == entity_port:
                if "port" in lo_line:
                    indent_po_adj = 1
                elif exit_bracket(lo_line):
                #elif ')' in lo_line and lo_line.index(')') == 0:
                    state = entity
                    indent_pr_adj = -1
                    indent_po_adj = -1
                #elif "))" in lo_line:
                #    state = entity
                #    indent_pr_adj = -1
                #    indent_po_adj = -1
    
            #=========================================
    
            elif state == arch:
                if "architecture" in lo_line:
                    indent_po_adj = 1
                    state = arch_declare
    
            elif state == arch_declare:
                if "component" in lo_line:
                    state = arch_comp
                    indent_po_adj = 1
                if "begin" in lo_line:
                    indent_pr_adj = -1
                    indent_po_adj = 1
                    state = arch_body
    
            elif state == arch_comp:
                if "generic" in lo_line:
                    indent_po_adj = 1
                    state = arch_comp_generic
                elif "port" in lo_line:
                    indent_po_adj = 1
                    state = arch_comp_port
                elif "end" in lo_line:
                    state = arch
                
            elif state == arch_comp_generic:
                if exit_bracket(lo_line):
                #if ')' in lo_line and lo_line.index(')') == 0:
                    state = arch_comp_port
                    indent_pr_adj = -1
                #elif "))" in lo_line:
                #    state = arch_comp_port
                #    indent_pr_adj = -1
    
            elif state == arch_comp_port:
                if "port" in lo_line:
                    indent_po_adj = 1
                elif exit_bracket(lo_line):
                #elif ')' in lo_line and lo_line.index(')') == 0:
                    state = arch_comp_port
                    indent_pr_adj = -1
                    indent_po_adj = -1
                #elif "))" in lo_line:
                #    state = arch_comp_port
                #    indent_pr_adj = -1
                #    indent_po_adj = -1
                elif "endcomponent" in lo_line:
                    state = arch_declare
    
            #=========================================
    
            elif state == arch_body:
                if "process" in lo_line:
                    state = process
    
                elif "generate" in lo_line:
                    indent_po_adj = 1
                    state = generate
    
                elif "entity" in lo_line:
                    indent_po_adj = 1
                    state = arch_inst
    
                elif "end" in lo_line:
                    indent_pr_adj = -1
    
            elif state == process:
                if "begin" in lo_line:
                    indent_po_adj = 1
                elif "if" in lo_line and lo_line.index("if")==0:
                    indent_po_adj = 1
                elif "elsif" in lo_line:
                    indent_pr_adj = -1
                    indent_po_adj = 1
                elif "else" in lo_line:
                    indent_pr_adj = -1
                    indent_po_adj = 1
                elif "endif" in lo_line:
                    indent_pr_adj = -1
                elif "case" in lo_line and lo_line.index("case")==0:
                    indent_po_adj = 1
                elif "when" in lo_line and lo_line.index("when")==0:
                    indent_po_adj = 1
                    state = case
                elif "endprocess" in lo_line and lo_line.index("endprocess")==0:
                    indent_pr_adj = -1
                    state = arch_body
    
            elif state == case:
                if "when" in lo_line and lo_line.index("when")==0:
                    indent_pr_adj = -1
                    indent_po_adj = 1
                if "endcase" in lo_line and lo_line.index("endcase")==0:
                    indent_pr_adj = -2
                    state = process
    
            elif state == generate:
                if "begin" in lo_line and lo_line.index("begin")==0:
                    indent_pr_adj = -1
                    indent_po_adj = 1
                elif "endgenerate" in lo_line and lo_line.index("endgenerate")==0:
                    indent_pr_adj = -1
                    state = arch_body
    
            elif state == arch_inst:
                if "genericmap" in lo_line and lo_line.index("genericmap")==0:
                    indent_po_adj = 1
                    state = arch_inst_gen
                elif "portmap" in lo_line and lo_line.index("portmap")==0:
                    indent_po_adj = 1
    
            elif state == arch_inst_gen:
                if ");" in lo_line:
                    indent_pr_adj = -1
                    state = arch_inst_gen
                elif "portmap" in lo_line and lo_line.index("portmap")==0:
                    indent_po_adj = 1
    
            elif state == arch_port:
                if "portmap" in lo_line and lo_line.index("portmap")==0:
                    indent_po_adj = 1
                elif ");" in lo_line:
                    indent_pr_adj = -2
                    state = arch_body                

        # No more than two empty lines
        if empty_line<2:
            indent = indent + indent_pr_adj
            line = (4*indent) * ' ' + line + '\n'
            print(state + '\t' + line)
            fw.write(line)
    
            indent = indent + indent_po_adj
            indent_pr_adj = 0
            indent_po_adj = 0
    
fr.close()
fw.close()

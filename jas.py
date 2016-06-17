#!/usr/bin/env python3

import sys, codecs
import os.path
import subprocess
from math import ceil

# When available, offer to upload the binary using perturbo
PERTURBO_BIN = './perturbo'

opsWithoutArg = {
    'BACK': 0x01,
    'SWAP': 0x03,
    'POP': 0x04,
    'RET': 0x0c,
    'LI': 0x0d,
    'LC': 0x0e,
    'SI': 0x0f,
    'SC': 0x10,
    'PSH': 0x11,
    'OR': 0x12,
    'XOR': 0x13,
    'AND': 0x14,
    'EQ': 0x15,
    'NE': 0x16,
    'LT': 0x17,
    'GT': 0x18,
    'LE': 0x19,
    'GE': 0x1a,
    'SHL': 0x1b,
    'SHR': 0x1c,
    'ADD': 0x1d,
    'SUB': 0x1e,
    'MUL': 0x1f,
    'DIV': 0x20,
    'MOD': 0x21,
    'PUSHARG': 0x34,
    'RETP': 0x38,
}

opsWithArg = {
    'REL': 0x02,
    'IMM': 0x05,
    'JMP': 0x06,
    'JSR': 0x07,
    'BZ': 0x08,
    'BNZ': 0x09,
    'ENT': 0x0a,
    'ADJ': 0x0b,
    'INT': 0x22,
    'JSRP': 0x37,
}

metadata = '{\n\
    "ok": true,\n\
    "bss": "%s",\n\
    "po": 0,\n\
    "eov": 0,\n\
    "raw": "%s",\n\
    "ep": 0,\n\
    "row": 0,\n\
    "text": "",\n\
    "token": "",\n\
    "functions": [\n\
        {\n\
        "offset": 0,\n\
        "name": "main"\n\
        }\n\
    ]\n\
}'

# Yes. Global variables.
source = []
lineNum = 0
labels = {}
labelRelocs = {}
text = b''
bss = b''
    
def die(msg):
    print(msg)
    sys.exit(1)
    
def badInstruction(op):
    die("Unknown instruction '"+op+"' on line "+str(lineNum))
    
def badImmediate(imm):
    die("Invalid immediate (and not a label) '"+imm+"' on line "+str(lineNum))

def bytesToStr(bytes):
    return codecs.encode(bytes, 'hex').decode('utf8')

def strToImm32(s):
    try:
        imm32 = int(s, 16)
    except ValueError:
        badImmediate(s)
    if imm32 > 2**32 or imm32 < -2**32:
        badImmediate(s)
    imm32 = imm32 % (2**32)
    try:
        imm32b = imm32.to_bytes(4, byteorder='big')
    except ValueError:
        badImmediate(s)
    return imm32b

def cleanLine(line):
    try:
        line = line[:line.index(';')]
    except ValueError:
        pass
    return line.strip()

def cleanSource():
    global source
    source = [cleanLine(line) for line in source]

def populateLabels():
    lineNum = 0
    for line in source:
        lineNum += 1
        if len(line) == 0 or line.find(' ') != -1:
            continue
        if line[len(line)-1] != ':':
            continue
        label = line[:len(line)-1]
        if label in labels:
            die("Label '"+label+"' redefined on line "+str(lineNum))
        labels[label] = 0

def compileLine(line):
    code = b''
    if len(line) == 0:
        return code
    
    words = line.split(' ')
    op = words[0]
    
    if len(words) == 1:
        if op[len(op)-1] == ':':
            # Now that we've codegen'd the preceding code, we know the label's address
            label = op[:len(op)-1]
            labels[label] = len(text)
            return code
        
        if not op in opsWithoutArg:
            badInstruction(op)
        code = bytes([opsWithoutArg[op]])
    elif len(words) == 2:
        imm = words[1]
        if op == 'DB':
            try:
                if imm.find('0x') == 0:
                    imm = imm[2:]
                return int(imm, 16).to_bytes(ceil(len(imm)/2), byteorder='big')
            except ValueError:
                die("Invalid hex literal immediate on line "+str(lineNum))

        if not op in opsWithArg:
            badInstruction(op)
        if not imm[0].isdigit() and imm in labels:
            # We don't know the label's target yet, mark it as needing a reloc
            labelRelocs[len(text)+1] = imm
            imm = bytes(4)
        else:
            imm = strToImm32(imm)
        code = bytes([opsWithArg[op]])+imm
    else:
        die("Too many operands on line "+str(lineNum))
    return code

def fixupLabels():
    global text
    for addr in labelRelocs:
        target = labels[labelRelocs[addr]].to_bytes(4, byteorder="big")
        text = text[:addr] + target + text[addr+4:]

def compile():
    global text, lineNum
    

# Assemble source using amazing state of the art token-for-token codegen technology!
if len(sys.argv) <= 1:
    print('Usage: '+sys.argv[0]+' <source.asm>')
    sys.exit(1)

print("Jailbreak Assembler")
with open(sys.argv[1], 'r') as f:
    source = f.read().split('\n')

cleanSource()
populateLabels()
lineNum = 0
for line in source:
    lineNum += 1
    text += compileLine(line)
fixupLabels()

# Save results
basename = sys.argv[1]
if basename.rfind('.') != -1:
    basename = basename[:basename.rfind('.')]
with open(basename+'.data', 'wb') as f:
    f.write(text)
with open(basename+'.json', 'w') as f:
    f.write(metadata)
with open(basename+'.bss', 'wb') as f:
    f.write(bytes(0x10)) # We don't use the BSS yet, but it needs to exist

# Brag about it
print("Success, generated binary is "+str(len(text))+" bytes long")
print("Hex dump: "+bytesToStr(text))

# If we have perturbo, now would be a good time to use it
if os.path.isfile(PERTURBO_BIN):
    print("Upload to device? ", end="")
    reply = input().lower()
    if reply == 'y' or reply == 'yes':
        env = os.environ.copy()
        if not "SF_API_KEY" in env:
            print("Enter your API key: ", end="")
            env["SF_API_KEY"] = input()
        print("Uploading...", end="")
        sys.stdout.flush()
        child = subprocess.Popen([PERTURBO_BIN, "write", basename+".json", basename+".bss", basename+".data"],
              env=env, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        out = child.stderr.read().decode('utf8')
        child.communicate()[0]
        if child.returncode == 0:
            print("Done!")
        else:
            print("Fail: "+out)


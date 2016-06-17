# JAS: Stockfighter Jailbreak Assembler

This is a cheap and dirty assembler for the Stockfighter Jailbreak virtual machine for the purpose of perturbing blobs.

It supports all the instructions I could stumble upon, as well a DB instruction to include raw hex data in the text.  
Labels can be defined and used instead of an immediate to any instruction that takes an operand, immediates are otherwise interpreted as hexadecimal numbers (even without a "0x" prefix).

If [perturbo](https://github.com/dcw303/perturbo) is found in the current directory, jas will offer to use it to upload the compiled program directly to the device.  
Put your API key in the SF_API_KEY environment variable if you don't want to be prompted for it every time.

## Example usage
src.asm:
```
; Print a number
IMM 2A
PUSHARG
INT 1
ADJ 1

; Suicide by stack overflow
ENT 0
IMM 0xCC
loop:
PSH
JMP loop
DB 0x0C ; Unreachable RET
RET ; Seriously unreachable RET
```

Compiling:
```
$ ./jas.py src.asm
Jailbreak Assembler
Success, generated binary is 34 bytes long
Hex dump: 050000002a3422000000010b000000010a0000000005000000cc11060000001a0c0c
Upload to device? Yes
Enter your API key: a37c14623abde1731fcdd33caf1895132e23695f
Uploading...Done!
$ ls
jas.py  perturbo  src.asm  src.bss  src.data  src.json
```

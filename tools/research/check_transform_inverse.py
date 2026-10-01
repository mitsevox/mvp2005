#!/usr/bin/env python3
"""Reproduce two exact-integer witnesses for the original Transform inverse divisor.

Requires the configured GV4E69 split assembly. This evaluates only the determinant
prefix and two small-integer inputs; it is not a general PPC/FMA emulator or a
Dolphin gameplay test. All intermediates in these witnesses are exactly representable.
"""
from pathlib import Path
from fractions import Fraction
import re, struct
asm=Path("build/GV4E69/asm/eagl/transform.s").read_text()
def single(x):return struct.unpack(">f",struct.pack(">f",x))[0]
def target(values):
    registers={}
    for line in asm.splitlines():
        match=re.match(r"/\* ([0-9A-F]{8}).*?\*/\s*(\w+)\s+(.*)",line)
        if not match:continue
        address=int(match[1],16)
        if not 0x803DE81C<=address<=0x803DE8F4:continue
        op,args=match[2],match[3].split(", ")
        if op=="lis":continue
        if op=="lfs":
            load=re.match(r"0x([0-9a-f]+)\(r3\)",args[1])
            registers[args[0]]=values[int(load[1],16)//4] if load else 0.0
        elif op in ("fmuls","fadds","fsubs","fmadds","fmsubs"):
            operands=[registers[name] for name in args[1:]]
            a,b=operands[:2]
            value=a*b if op=="fmuls" else a+b if op=="fadds" else a-b if op=="fsubs" else a*b+operands[2] if op=="fmadds" else a*b-operands[2]
            registers[args[0]]=single(value)
        else:raise AssertionError((hex(address),op))
    return registers["f30"]
def det(values):
    rows=[[Fraction(values[i*4+j]) for j in range(4)] for i in range(4)]
    result=Fraction(1)
    for i in range(4):
        pivot=next((j for j in range(i,4) if rows[j][i]),None)
        if pivot is None:return Fraction(0)
        if pivot!=i:rows[i],rows[pivot]=rows[pivot],rows[i];result=-result
        factor=rows[i][i];result*=factor
        for j in range(i+1,4):
            scale=rows[j][i]/factor
            for k in range(i,4):rows[j][k]-=scale*rows[i][k]
    return result
identity=[float(i//4==i%4) for i in range(16)]
assert target(identity)==det(identity)==1
example=identity[:]
example[2]=example[11]=example[13]=1
assert det(example)==1 and target(example)==2
print("Identity: actual target expression1, true determinant1")
print("Counterexample identity+m2=m11=m13=1: actual target expression2, true determinant1")
print("All operations for these inputs use exactly representable small integers; no FMA rounding ambiguity.")

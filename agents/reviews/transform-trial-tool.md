# trial.py relocation review

Verdict: SHIP

The added `.text` case resolves only a zero-addend section relocation, using the function symbol actually present at section offset zero. It is equivalent to the existing `.text+0x0` normalization and leaves `.text` unchanged when no function begins at zero. It does not substitute the expected target symbol or collapse distinct functions.

I independently inspected the real candidate `build/trial/transform.o`: its symbol table places `MultMatrix__FPC7MATRIX4T0P7MATRIX4` at `.text+0`, and PostMult's call at object offset 0x994 has `R_PPC_REL24 .text`. Running the changed disassembler against that object and `build/GV4E69/obj/eagl/transform.o` produced identical normalized instruction lists for PostMult (16 instructions) and PreMult (18 instructions), including distinct named MultMatrix and MEM_copy calls.

Negative checks preserve genuine mismatches: substituting a wrong first-function name in the candidate symbol lookup makes both comparisons fail; a nonzero interior addend remains `<First+0x4>`; an addend at another function stays `Second`; an unrelated external name is unchanged; absent zero symbols and unrecognized negative-addend syntax remain unresolved. These checks executed the actual root `tools/match/trial.py` functions without changing tracked files or the candidate object.

This is separate from the source verdict in hostile.md; the normalization fix does not repair or excuse a source fidelity finding.

# Transform CI verification

Code commit:4f8da3a03f111efd1f7545dc9e9ccee86514bfad.

Push run36813942442 and PR run36813945994 both completed successfully. The downloaded
GV4E69_report/report.json has the exact same1,165 exact-address/name set as the
root combined local report. The baseline1,139 exact addresses are all preserved.
Transform25/31exact,4,760/7,960 code bytes; viewport15/17exact,5,092/5,324 bytes.
Whole report1,165exactfunctions/262,816codebytes. The downloaded PR build log
explicitly confirms build/GV4E69/main.dol: OK.

Transform and viewport remain NonMatching and assembly-linked. This confirms build
integrity and per-function scoring, not complete source-object/data replacement.
Independent source-fidelity review is SHIP (transform-hostile-final.md); blind final
reconciliation is30/30 for names and comments. Claude's additional review remains
pending. No merge occurred.

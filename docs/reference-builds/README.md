# Reference builds (discovery step 6)

Status 2026-09-29: candidates found by web search only. Nothing has been downloaded, and no game
file from another title has been looked at. Each row says what the build could give us and what
getting it would take. Whether to get any of them is the owner's call (`agents/state.md`).

## What we would want from one

MVP 2005 ships no symbols (`docs/names.md`). A related build helps when it shares code with us and
carries names: a symbol table (function names), DWARF (names, types, struct layouts, file order,
inlines) or a link map (names and file order). Code shared with MVP is most likely in EA's
cross-title libraries: SND audio (V9.02.04 here), SPCH speech, the VP6 and MAD video codecs, file
and memory card code, and possibly EAGL and gamelib. The baseball code itself is only in MVP titles.

## Candidates, most useful first

| Build | What it has | Shares with MVP (to check) | What getting it takes |
|---|---|---|---|
| NFS Most Wanted, GameCube USA (GOWE69), EA Black Box, 2005 | `NFSMWRELEASE.ELF` on the retail disc with full DWARF. The public decomp (github.com/dbalatoni13/nfsmw) keeps a text dump of it in `symbols/mw_dwarfdump.nothpp` | Same year and same ProDG 3.9.3 (its decomp's owner, via Lucas). EA audio, video codec, file and memory card code are the likely overlap | Reading the public dump is a download from a public repo; the owner decides |
| NFS Underground 2, GameCube, EA Black Box, 2004 | `Speed.elf` with symbols on the disc (13,870 symbols, per retroreversing.com) | As above, a year earlier | Needs the disc (a game file; not in the repo) |
| NFS Underground, GameCube, EA Black Box, 2003 (retail PAL and a preview build) | `Speed.elf` with symbols (10,162 retail, 9,604 preview; the preview notes "SN Systems library + debugger") | Older versions of the same EA libraries | Needs the disc |
| MVP Baseball 2005 on PS2, Xbox and PC; MVP 2004 on GameCube | Unknown: no report of symbols found | The whole game (same code base) | Would need someone to check their files for maps or symbols; the PC build is the most likely to carry names |
| MVP 06 and MVP 07 NCAA Baseball (PS2, Xbox, 360) | Unknown | Later versions of the same code base | As above |

Other public decomps of EA GameCube titles: none found besides NFS Most Wanted. Checked: the
public "games shipped with debug symbols" lists (a GitHub gist by mariomadproductions and
retroreversing.com's GameCube page) list no MVP, EA Sports or EA Canada title.

## Next checks (after the owner's go-ahead)

1. From the NFS MW dump: do the SND, SPCH, VP6/MAD, memory card or file library functions appear, and
   do their names and sizes line up with ours? One library that lines up gives EA's names and struct
   layouts for that whole block.
2. Whether the owner has, or wants, any of the other builds checked for maps or symbols.

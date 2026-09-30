# Viewport next three: blind naming and behavior review

2026-09-30. A fresh reviewer with no conversation history received only three original-assembly
functions labelled SubjectA/B/C, the disc's type layouts and the referenced literal values.
It did not receive C++, map function names, lane reports or coordinator reasoning.
The coordinator reconciled the results against the code and subsequently inspected map names.

| Subject | Address / applied EA name | Independent description | Name / comment assessment |
| --- | --- | --- | --- |
| A | 0x803E1C10 / GetShape | GetGeometry: returns origin, width/height and depth range through six output addresses, in field order | right / right; semantic agreement, not prediction of EA's exact spelling |
| B | 0x803E1CDC / SetOrthographic | SetCenteredOrthographicProjection: bounds -1..1 horizontally and +/- first argument vertically, supplied near/far, GX upload | right / right; the first argument is a vertical half-extent even though cached as mAspect |
| C | 0x803E1DB0 / SetOrthographicScreenSpace | SetScreenSpaceProjection: bounds 0..width and 0..height with y down, supplied near/far, GX upload | right / right; no narrower font/UI purpose was inferred |

The reviewer also identified the fixed 0.75 aspect cache in C, the six cached matrix entries
left untouched by both setters, and the absence of perspective side-plane updates. A stores
outputs sequentially: pointers versus references and receiver const cannot be inferred from
instructions; the reference maps supply those parts of the signature. Aliasing does not
receive a general safety guarantee. Return types and local names remain code-derived.

All three new functions were sampled. Semantic name agreement: 3/3; comment agreement: 3/3.
The existing two functions were not part of this blind sample; the hostile reviewer covered
all five written functions.

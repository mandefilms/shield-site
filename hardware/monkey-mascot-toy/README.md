# Monkey Mascot Toy — 100mm (XIAO in the head, real button + decorative heart)

Built from the chibi monkey sculpt you uploaded, scaled to **100mm** tall —
double the original 50mm build, per your feedback that 50mm ended up too
small once you saw it built. Same overall approach throughout: split front/
back, real tactile button + separate decorative heart, real-size LED holes,
**XIAO nRF52840 in the head** (not the torso).

## Open question: overall size

You mentioned 100mm might be a bit big now. Nothing's changed size-wise in
this build yet — still 100mm — pending you settling on a target (75mm was
on the table). Say the word and I'll rebuild at whatever size you land on;
the button/LED position fixes below are expressed as fractions of the raw
mesh so they'll carry over correctly to a rescaled build, but I'll still
re-run the full validation (chin clearance included) rather than assume
it holds at a different scale.

## Status: front shell only, pending your size check

Per your request, only `stl/front_shell.stl` reflects the latest changes
below — **`back_shell.stl` and `heart_cap.stl` in this repo are still the
previous pass** (correct 100mm size, but the heart cap not yet resized to
match — see below). Once you've confirmed the front's size/proportions,
say so and I'll regenerate the back shell (which has no button/LED
features of its own, so it isn't expected to change) and rebuild the heart
cap at a larger size to match the bigger monkey.

**Latest front-shell changes:**
- **Button hole moved down — further than a small nudge, once the chin
  clearance check below made that necessary.** You asked to move it down
  a fraction and separately asked me to check it wouldn't hit the chin
  with the heart cap on. Those turned out to be the same issue: at the
  first "fraction" position (raw Y=82→80 on the mesh) I placed the actual
  `heart_cap` mesh over the button (cusp pointing down, its natural
  orientation) and boolean-intersected it with the body — **real 422 mm³
  of overlap with the chin/jaw overhang, not a close call.** Walked the
  button position down and re-ran the same check at each step: still
  touching (~0.02 mm³) one step up from where it landed, fully clear (0
  mm³, real margin) at raw Y=70. That's about 6mm further down (scaled)
  than the previous version, more than "a fraction" — but the alternative
  was a heart cap that physically couldn't sit flush. Re-verified against
  the actual exported `front_shell.stl` + `heart_cap.stl` together (not
  just the pre-export in-memory shapes): **zero overlap.**
- **LED holes moved up a fraction** to match, re-probed at the new belly
  position — still ~12mm scaled centre-to-centre from the button, well
  clear of the ~8.6mm minimum (button + bulb hole radii combined).
- **All 4 LED holes are present and correctly spaced** — in an earlier
  straight-on render the 4th one was barely visible because the belly
  surface curves away from the camera right at that angle (confirmed by
  re-rendering looking straight down the belly's own surface normal — all
  4 show up as full circles).
- **Head-to-tummy channel confirmed still open** at 100mm, verified along
  the actual head→neck→torso path (not a naive straight line between the
  two cavity centers, which cuts across solid material and gives a
  false "blocked" result since the neck channel doesn't sit on that line).
- Re-ran the full fragmentation and wall-thickness checks after these
  moves — unchanged from the previous pass (same known head/neck-transition
  thin spot, nothing new introduced).
- **Fixed: button and LED holes weren't actually open.** You said the
  button "looks like there is no actual hole" — you were right. The
  cutters' `inside` reach (3.0mm for the button, 2.0mm for the LEDs) was
  measured from the wrong assumption that the hollow cavity sits right
  behind the surface; it doesn't everywhere. Marching inward from several
  points across each hole's own footprint (not just its centre — the
  surface and the cavity boundary aren't parallel, so the real material
  depth varies across a single hole) found up to **5.75mm** of solid
  material still standing behind the button and up to **6.75mm** behind
  the LED holes, both well past the old cut depth. Every hole was a blind
  dimple, not a through-hole. Deepened both to `inside=8.0` and verified
  properly this time: cast a ray straight down each hole's own axis on the
  actual exported shell and confirmed it crosses exactly 2 surfaces (into
  the skin, then out the far side into the open cavity) for the button and
  all 4 LEDs — not just "does the cutter reach some point," but "is there
  a real opening a wire could pass through."
- **Heart cap still needs resizing** — you asked for it to match the
  bigger monkey's proportions. So far it's intentionally stayed at its
  fixed 50mm-build size (30.1×27.4×9.4mm) because it's sized to the real
  button hardware, not the shell — that hasn't changed, but the *visible*
  heart shape around that fixed-size pocket can grow to look
  proportionate on the bigger body. Held off on this until the shell size
  itself is confirmed, per your ask.

## Why 100mm

The first pass targeted 50mm (the smallest size that fit the XIAO board with
real margin — see the sizing history below). After looking it over you said
it needed to be bigger, but that doubling from there ("the last one was
huge") felt like too much of a jump in the other direction historically —
so this build doubles the **50mm** version, not the original 114mm otter
scale. **Fixed-size hardware does not scale up with the shell**: the
14.04mm button, 3.2mm/4.5mm-pitch LED holes, and the heart cap all stay at
their real physical dimensions. Only the shell geometry and cavity
*positions* doubled — the cavities themselves also grew in absolute size,
which is why the electronics now fit with much more margin than at 50mm.

## Design

- **Head cavity**: a box (not an ellipsoid) sized to the XIAO's footprint,
  corners clipped back by an ellipsoid so they don't poke through the
  head's rounded exterior — same approach as the 50mm build, dimensions
  doubled. **The XIAO mounts against the front (—Z-facing) wall of the
  cavity**, board flat, with the **CR2032 stacked directly behind it in the
  now-generous spare Z depth** (the head cavity's Z half-extent is 21.2mm
  clipped / 14mm box half-extent — the board's 4.8mm thickness leaves ample
  room behind it for the coin cell, verified below).
- **Torso cavity**: the whole torso is hollow except the legs, same as
  before, dimensions doubled.
- **Neck channel**: thin tunnel connecting head and torso cavities for
  wiring, verified open (see Verification).
- **Button**: plain through-hole, **14.04mm diameter** (fixed real size),
  upper belly, no counterbore, no dedicated back-pocket (per your earlier
  feedback on the 50mm build) — opens straight into the general torso
  cavity.
- **LED holes**: 4× 3.2mm dia, 4.5mm pitch (fixed real size), lower belly.
- **Heart cap**: unchanged from the 50mm build (30.1×27.4×9.4mm) — it's
  sized to the real button hardware, not the shell, so it doesn't grow with
  the doubling. Rounded heart profile, hollow cap with a recessed pocket
  that sits down over the button.
- **Alignment dowels — repositioned, not just doubled.** The 50mm build's
  dowel Y-positions (proportionally carried into this build via the same
  `raw * SCALE` formula) turned out to be **wrong at 100mm**: doubling the
  head cavity's absolute size ate into the "solid gap" the upper dowel used
  to sit in, and the lower dowel landed in the empty gap between the legs.
  Both printed as **disconnected floating pins**, not welded to the shell —
  caught by checking `split(only_watertight=False)` on the back shell
  (found 2 extra small disconnected pieces exactly matching the pin
  dimensions) rather than assumed safe from the 50mm numbers. Re-positioned
  by directly sampling solid-vs-cavity points at the new scale: one dowel
  now sits inside a leg (off the model's midline, clear of both the
  inter-leg gap and the torso cavity), the other in the actual (now
  narrower, ~4.8mm) solid gap between the torso and head cavities.
  Re-verified: both weld cleanly into the main shell as one piece.

## Fixed: front/back split was silently clipping off the whole head

The split-into-two-halves step uses a large box to intersect against, sized
just bigger than the model so the "keep everything on this side of the Z
midplane" cut doesn't accidentally act on X or Y too. That box's size had
been **deliberately shrunk from 400 down to 100 (half-extent 50)** during
the earlier front/back mixup investigation on the *50mm* build, back when
the whole model was under 50mm on every axis. **That number was never
revisited when the shell doubled to 100mm tall** — a box with Y half-extent
50 no longer covers a 100mm-tall model, so the split was silently slicing
the entire head off above Y=50mm. Caught by rendering the actual exported
STL in OpenSCAD before shipping (the same practice that caught the
button/LED mixup on the 50mm build) — the first 100mm render showed only a
headless torso. Fixed by sizing the box (300, half-extent 150) safely above
the model's real ~100×84×55mm extents instead of carrying over a number
tuned for a different scale.

## Verification (not assumed)

Every check below was re-run from scratch at the 100mm scale — none of the
50mm build's numbers were assumed to still hold.

- **Fragmentation**: `front_shell.stl` is 1 connected piece spanning the
  full model height (Y 0.25–100.15mm). `back_shell.stl` is the main welded
  piece (Y 0.25–100.25mm, dowels included) plus one negligible ~0.08mm
  degenerate sliver (a boolean-precision artifact, not a real feature —
  effectively zero volume, invisible, won't affect printing).
- **XIAO + CR2032 fit**: sampled the full board footprint (not just
  corners) against the actual head cavity shape — **192/192** points
  inside. CR2032, correctly stacked *behind* the board in the cavity's Z
  depth (not below it in Y, which doesn't have room) — **216/216** points
  inside. Both fit with real margin at this scale.
- **Wall thickness**: sampled thousands of real exterior points against
  the real cavity shapes (excluding the button/LED holes themselves).
  Front: median ~5.9mm, back: median ~5.3mm — healthy. Both still have a
  small cluster of near-zero-thickness points at the head cavity's lower
  corners near the neck/shoulder transition (front: 40/1662 sampled points
  under 0.5mm; back: 20/1790) — **the same known fragile spot flagged on
  the 50mm build**, in the same relative location, not a new regression
  from doubling. Worth a look in the slicer; say the word if you want the
  head cavity trimmed back further there.
- **Neck channel connectivity**: verified open (head cavity to torso
  cavity) the same way as the 50mm build — a genuinely watertight
  in-memory mesh, not an unreliable reloaded STL, was used for the
  containment check.

## Parts (3 STL, 2 colours)

| File | Colour | Contents |
|---|---|---|
| `stl/front_shell.stl` | body | front half — face, belly, button hole, 4 LED holes, hollow head+torso |
| `stl/back_shell.stl` | body | back half, plain, no holes — mates via 2 alignment dowels |
| `stl/heart_cap.stl` | pink | separate decorative heart cap — presses over the button's own cap, glue optional |

## Assembly

1. Mount your tactile button through the belly hole (14.04mm straight
   through-hole) from outside before closing the shell.
2. Fit the XIAO nRF52840 flat against the head cavity's front wall, and the
   CR2032 directly behind it in the same cavity. Route wires down through
   the neck channel, through the hollowed torso, to the button and LED
   holes.
3. Route bulb leads through the 4 belly holes and glue/friction-fit the
   bulbs from outside.
4. Close front/back on the 2 alignment dowels; glue or tape the seam (no
   snap clip).
5. Press `heart_cap.stl` down over the button's own cap; glue if you want
   it permanent.

## Regenerating

`build.py` is the actual script used (trimesh + manifold3d, consolidated
single-boolean-difference technique). All cavity, button, LED, dowel, and
split parameters are named near the top. If you change `SCALE` again,
**re-run the full validation** (fragmentation check via
`split(only_watertight=False)`, wall-thickness sampling, XIAO/CR2032 fit,
and an OpenSCAD render of the actual exported STL) rather than assuming
positions and box sizes tuned for one scale still hold at another — this
build's own history (dowels, the split box size) is the reason why.

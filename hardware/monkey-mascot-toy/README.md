# Monkey Mascot Toy — 50mm (XIAO in the head, real button + decorative heart)

Built from the chibi monkey sculpt you uploaded, scaled to **50mm** tall.
Same overall approach as the otter's final (60mm) version — split front/
back, real tactile button + separate decorative heart, real-size LED holes
— but with one big change: **the XIAO nRF52840 lives in the head**, not the
torso, because the torso alone is nowhere near big enough at this size.

## Why 50mm, and why the head

You asked for "half the otter's size" (~30mm). Measured directly off the
mesh: at 30mm tall, even the head's interior — the biggest, roomiest part
of this sculpt — works out to only ~14-16mm across, smaller than the XIAO
board itself (21×17.8mm). It doesn't fit at any size below roughly
**40-45mm**, and even that's a knife-edge fit. **50mm is the smallest size
where the board fits with real margin**, which is why this build targets
that instead of 30mm.

Putting the XIAO in the head (confirmed with you) rather than the torso
works because the head is ~50% of the model's total height and much
rounder/roomier than the torso at this scale.

## Design

- **Head cavity**: a box (not an ellipsoid like the otter used) sized to
  the XIAO's footprint, with its corners clipped back by an ellipsoid so
  they don't poke through the head's rounded exterior. An ellipsoid alone
  couldn't inscribe the board's rectangular footprint at this scale — its
  corners waste too much space — so this build uses a box for the flat
  faces and only rounds the corners enough to clear the exterior surface.
  **The XIAO mounts vertically** (long edge running up toward the crown)
  rather than flat, because there's more spare room in that direction than
  side-to-side at head-centre height.
- **Torso cavity**: the *whole* torso is now hollow (not just a small
  pocket behind the belly) — spans from just above the legs up to the neck,
  tapering at both ends since it's a single big ellipsoid. Legs are left
  solid (too thin/pose-risky to hollow). This gives real room behind the
  button, plus space for the CR2032 and wiring.
- **Neck channel**: a thin (~2.3mm dia) tunnel connecting the head cavity
  down to the torso cavity, for wiring between the XIAO and the button/
  LEDs. This needed real tuning — the neck is the tightest cross-section
  on the whole model, and the first two attempts either disconnected the
  head from the torso entirely (all-piece i.e. the two halves would print
  as loose separate parts) or punched visible holes through the sides of
  the neck. Fixed by keeping the head cavity's box entirely within the
  head's genuinely wide zone and letting the channel do the narrow
  crossing on its own.
- **Button**: plain 10.80mm through-hole (your confirmed real size, same
  hardware as the otter), upper belly, no counterbore.
- **LED holes**: 4× 3.2mm dia, 4.5mm pitch — real hardware size, doesn't
  scale with the model — lower belly, kept a healthy distance from the
  button (learned from the otter build, where a tight button/LED gap was
  a real fragility risk).
- **Heart cap**: redesigned — rounder heart profile (Chaikin corner-
  smoothing softens the classic pointed-heart curve while keeping the
  two-lobe heart silhouette), and now **hollow like a real cap** rather
  than a solid block: a thin shell (~0.9mm roof) with a recessed oval
  pocket (15×13mm) on the underside sized to fit down over the real
  button's own cap. It just sits over the button rather than needing to be
  glued as a solid lump. Still a separate piece, not part of the printed
  shell — press it on after the button is mounted.
- **No eye/nose/mouth colour patches** — the sculpt already has the face
  as printed-in geometry (not a separate colour region), so there's
  nothing extra to add there; this is a 2-colour print like the small
  otter (body + heart).

## Verification (not assumed)

- **XIAO fit**: checked by sampling the board's full footprint (not just
  corners) against the actual cavity shape — **472 of 480 sample points**
  land inside the cavity (the few misses are at the board's sharpest
  corner edge, sub-millimetre). CR2032 fits fully with real margin,
  stacked behind the board.
- **Wall thickness**: sampled thousands of points on the real exterior
  surface against the real cavity shapes (excluding the button/LED holes
  themselves, which are *supposed* to reach the surface). Both shells are
  healthy almost everywhere (median ~4.9-5.2mm), **except a small cluster
  of near-zero-thickness points right at the head cavity's lower corners**,
  where the box cavity's bottom edge sits close to the neck's narrowest
  point on both sides. This was the hardest part of the geometry to get
  right at this size and I ran out of safe margin to fully clear it —
  flagging it plainly rather than calling it solved.

**Known remaining issue**: that shoulder/neck-transition thin spot (both
sides, roughly where the head cavity's bottom corners sit) is a real
fragility risk — more so than anything in the otter builds. Worth a close
look in the slicer, and if it looks concerning, tell me and I'll shrink the
head cavity further (trading some of the XIAO's fit margin for wall
thickness) rather than leave it as-is. Enlarging the torso cavity didn't
make this worse — same known spot, not a new one — though it did nudge a
couple of points near the belly's front face down to a similarly thin
(~0.1-0.6mm) range, worth the same slicer check.

## Parts (3 STL, 2 colours)

| File | Colour | Contents |
|---|---|---|
| `stl/front_shell.stl` | body | front half — face, belly, button hole, 4 LED holes, hollow head+torso |
| `stl/back_shell.stl` | body | back half, mates to front via 2 alignment dowels |
| `stl/heart_cap.stl` | pink | separate decorative heart cap — presses over the button's own cap, glue optional |

## Assembly

1. Mount your tactile button through the belly hole (10.80mm straight
   through-hole) from outside before closing the shell.
2. Fit the XIAO nRF52840 into the head cavity (vertical orientation — long
   edge up/down) and the CR2032 behind/below it. Route wires down through
   the neck channel, through the newly-hollowed torso, to the button and
   LED holes.
3. Route bulb leads through the 4 belly holes and glue/friction-fit the
   bulbs from outside.
4. Close front/back on the 2 alignment dowels (repositioned to the solid
   leg/hip area and the solid gap above the torso cavity, now that the
   torso itself is hollow); glue or tape the seam (no snap clip, same as
   the otter builds).
5. Press `heart_cap.stl` down over the button's own cap — its underside
   pocket (15×13mm oval) is sized to clear it; glue if you want it
   permanent.

## Regenerating

`build.py` is the actual script used (trimesh + manifold3d, same
consolidated-single-boolean-difference technique as the otter builds, to
avoid the mesh-fragmentation bug documented there). The head cavity, torso
cavity, neck channel, and button/LED positions are all separate named
parameters near the top if you want to adjust anything.

# Otter Mascot Toy — Small (60mm, real tactile button + decorative heart)

Same otter sculpt as the 114.3mm (4.5") version, scaled down to **60mm**
tall, but re-designed rather than just proportionally shrunk — the hollow
cavity was re-fit fresh to keep enough interior room for the fixed-size
electronics, and the belly button mechanism changed from a printed
pressable heart to a **real tactile button** with a printed decorative
heart glued on top.

## What changed vs. the 114.3mm version

- **Size**: 60mm tall (was 114.3mm / 4.5"). You asked for 1/3, then
  confirmed half (~57mm) once a strict 1/3 (~38mm) couldn't fit the XIAO
  board, then bumped to 60mm for a bit more margin.
- **Cavity: re-fit, not scaled down.** A proportional scale-down of the
  original cavity would only leave ~17×14×21mm inside — too small for the
  21×17.8mm XIAO nRF52840. Instead this build fits a fresh, larger cavity
  (two overlapping ellipsoids — an upper "electronics bay" plus a lower
  pocket reaching down toward the belly for the button) sized against the
  *actual* 60mm shell geometry, validated by sampling real wall thickness
  after the cut (see Verification below), not assumed from the original's
  proportions.
- **Button: real hardware, not a printed pressable cap.** The belly has a
  **simple straight through-hole, 10.80mm diameter** (your confirmed final
  number — the earlier 16.88mm/13.86mm countersunk-mount numbers turned out
  to be wrong/oversized and are no longer used; no counterbore/countersink
  feature at all now, just one hole). The button mounts through it from
  outside; `heart_cap.stl` is a **separate decorative heart**
  (23×20.8×2.2mm, flat-backed, no plunger) — glue it on after the button is
  in place. It is *not* part of the printed shell and does not need to be
  inserted before closing the halves.
- **Layout: button with the 4 LED holes just below it** — both are back at
  their original landmark positions (some up/down repositioning was tried
  and reverted in between based on a miscommunication about where things
  should sit; final layout is button + bulb row close together, not
  shifted toward the feet or up near the arms).
- **Bulb holes: kept at real size, re-spaced.** You asked for them "a hair"
  bigger — bumped to **3.2mm diameter** (from 3.0mm). Bulb size doesn't
  scale with the shell (they have to fit real 3mm bulbs), so the old
  114mm-scaled 7mm pitch would have shrunk to ~3.7mm — nearly merging four
  3.2mm holes. Re-laid-out at a fixed **4.5mm pitch** instead, independent
  of shell scale.
- **Heads-up: the gap between the button hole and the nearest bulb hole is
  only ~0.75mm** at this original spacing (button 10.8mm dia + bulb 3.2mm
  dia, centres ~7.75mm apart). That's tight enough to be a real fragility
  risk between the two openings — worth a close look in the slicer, and
  say the word if you'd like a little more breathing room (e.g. nudging the
  bulb row very slightly further from the button, or trimming the pitch)
  without changing the overall "just below the button" layout.
- **Dowels sized down slightly** (1.1–1.25mm radius, was 1.6–1.8mm) to suit
  the thinner walls at this size.
- **No mounting platform/shelf** carried over from the 114mm version's
  patched tealight-notch area — skipped for time, same as the "no
  standoffs" simplification on the original build.
- **No eye/nose colour patches on this version** — per your call, the face
  stays plain on this build (2 colours total: body + heart cap), unlike
  the 114mm version's 4-colour face detail.

## Slicing note

You mentioned printing this one at **0.12mm layer height** for extra
precision, and re-enabling Orca's **scarf joint seam** (Quality → Seam)
like last time to keep the layer seam close to invisible. Neither of those
needs any change to the STLs — just slicer settings.

## Electronics fit — verified, not assumed

I flagged this as the real risk going in: shrinking the shell shrinks the
cavity too unless it's re-fit. After building, I checked it two ways:

1. **Analytic fit check** — a virtual box for the XIAO nRF52840
   (21.3×18.1×4.8mm, board dims + ~0.3mm clearance) fits inside the main
   cavity ellipsoid with ~20% of the ellipsoid's containment budget to
   spare. A CR2032 (20mm dia × 3.2mm) stacked just below it, with a 0.5mm
   gap, fits with ~41% to spare. **Both fit with real margin, not a
   knife-edge fit.**
2. **Wall-thickness sampling** on the actual post-boolean shell (sampling
   thousands of real exterior-surface points, measuring distance to the
   nearest interior/cavity surface), at the final button+bulb layout below:
   back shell **min ~3.0mm**, front shell **min ~2.3mm**, both in the torso
   region — healthy, no fragile spots from the cavity itself. The one real
   thin point in this build is the ~0.75mm gap *between the button hole and
   the nearest bulb hole* (see layout note above), not the shell wall.

## Parts (3 STL, 2 colours — no face detail on this version)

| File | Colour | Contents |
|---|---|---|
| `stl/front_shell.stl` | body | front half — plain face, belly, button hole, 4 bulb holes, hollow interior |
| `stl/back_shell.stl` | body | back half, mates to front via 2 alignment dowels |
| `stl/heart_cap.stl` | pink | separate decorative heart — glue onto the real button's cap after mounting, **not printed fused in** |

## Assembly

1. Mount your tactile button through the belly hole from outside (10.80mm
   straight through-hole, no recess) before closing the shell — wire it to
   the XIAO the same as any other switch input.
2. Fit the XIAO nRF52840 + CR2032 in the main cavity — there's genuine
   room now (see Verification above), but it's still hand-placed/taped,
   no built-in mounts in this pass.
3. Route bulb leads through the 4 belly holes (3.2mm dia, 4.5mm pitch) and
   glue/friction-fit the bulbs from outside.
4. Close front/back on the 2 alignment dowels; glue or tape the seam (no
   snap clip, matching the 114mm version).
5. Once the button is mounted and the shell is closed, glue `heart_cap.stl`
   onto the button's cap from outside.

## Regenerating

`build.py` in this folder is the actual script used (trimesh + manifold3d,
same technique as the 114mm build: one consolidated boolean difference for
all cutouts to avoid the mesh-fragmentation bug documented in the 114mm
version's README, rather than many sequential cuts). Edit the cavity/
button/bulb parameters near the top and re-run with `python3 build.py`.

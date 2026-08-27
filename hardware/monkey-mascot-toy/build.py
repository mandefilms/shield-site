import trimesh, numpy as np, time
from shapely.geometry import Polygon
t0=time.time()

SCALE = 100.0/199.0
print("SCALE=", SCALE)

mesh = trimesh.load("monkey_raw.stl")
mesh.apply_translation([-100.0, 0, 0])   # recenter X (was centered on 100)
mesh.apply_scale(SCALE)
outer_pristine = mesh.copy()
print("shell loaded+scaled, extents=", mesh.extents, time.time()-t0)

def scale_pt(pt_raw_centered):
    return np.array(pt_raw_centered) * SCALE

def transform_upright(pt, normal, world_up=np.array([0,0,1.0])):
    z = np.array(normal, dtype=float); z /= np.linalg.norm(z)
    up_proj = world_up - np.dot(world_up, z) * z
    if np.linalg.norm(up_proj) < 1e-6: up_proj = np.array([1,0,0])
    y = up_proj / np.linalg.norm(up_proj)
    x = np.cross(y, z)
    T = np.eye(4); T[:3,0]=x; T[:3,1]=y; T[:3,2]=z; T[:3,3]=pt
    return T

def cyl_at(pt, normal, r, inside=2.0, outside=5.0, sections=32):
    h = inside+outside
    c = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    T = transform_upright(pt, normal); c.apply_transform(T)
    shift = (outside-inside)/2.0
    c.apply_translation(np.array(normal)/np.linalg.norm(normal) * shift)
    return c

def ellipsoid(rx,ry,rz,center,sub=3):
    e = trimesh.creation.icosphere(subdivisions=sub, radius=1.0)
    e.apply_transform(np.diag([rx,ry,rz,1]))
    e.apply_translation(center)
    return e

# ---------------------------------------------------------------------------
# Cavities -- XIAO nRF52840 + CR2032 live in the HEAD (much roomier than the
# torso at this size), with a small torso cavity behind the belly for the
# button + wire routing, connected by a channel through the neck.
# All params found by raycasting the actual scaled mesh (see monkey_probe
# notes) -- not guessed proportionally.
# ---------------------------------------------------------------------------
# Head cavity is a BOX, not an ellipsoid -- an ellipsoid wastes too much
# corner room to fit a rectangular PCB (checked analytically: the safe
# raycasted head envelope could not inscribe the 21.3x18.1mm XIAO footprint
# using an ellipsoid's corner-containment constraint, even using nearly the
# full available space). A box uses the envelope efficiently instead.
# Box sits entirely within the head's wide zone (raw Y 106-178, consistently
# 85mm+ across) -- NOT reaching down into the narrower neck/shoulder area,
# which a full-width box would otherwise breach on the sides (a tapering
# ellipsoid could reach further down safely, a box can't).
# XIAO mounts VERTICALLY (its 21.3mm long edge along Y) rather than flat --
# checked diagonal clearance analytically: right at head-centre height the
# X-Z diagonal room is almost exactly eaten up by the board's footprint if
# laid flat (essentially zero margin). Standing it up trades into Y, which
# has real spare room up toward the crown.
HEAD_CAVITY_HALF   = np.array([21.0, 22.8, 14.0])   # scaled mm (X, Y, Z) -- doubled with the shell
HEAD_CAVITY_CENTER = np.array([0, 145, 52]) * SCALE

# Whole torso hollowed out (not just a small pocket behind the belly) for
# real room behind the button and general wiring space -- legs excluded
# (too thin/pose-risky to hollow). Spans from just above the legs (raw
# Y~34) up to the neck transition (raw Y~90), tapering at both ends since
# it's an ellipsoid (safer than a box near the narrowing leg/neck zones,
# same lesson learned from the head cavity).
TORSO_CAVITY_R      = np.array([35, 28, 26]) * SCALE
TORSO_CAVITY_CENTER = np.array([0, 62, 52]) * SCALE

NECK_CHANNEL_R = 4.5 * SCALE
NECK_TOP    = np.array([0, 118, 42]) * SCALE
NECK_BOTTOM = np.array([0, 78, 42]) * SCALE

def neck_channel():
    c = trimesh.creation.cylinder(radius=NECK_CHANNEL_R, height=np.linalg.norm(NECK_TOP-NECK_BOTTOM)+2, sections=32)
    axis = (NECK_TOP-NECK_BOTTOM); axis/=np.linalg.norm(axis)
    R = trimesh.geometry.align_vectors([0,0,1], axis)
    T = np.eye(4); T[:3,:3]=R[:3,:3]; T[:3,3]=(NECK_TOP+NECK_BOTTOM)/2
    c.apply_transform(T)
    return c

def head_cavity_box():
    b = trimesh.creation.box(extents=HEAD_CAVITY_HALF*2)
    b.apply_translation(HEAD_CAVITY_CENTER)
    # clip the box's corners back with a safe-radius ellipsoid -- a plain
    # box's body-diagonal corners reach further than any single flat face,
    # far enough to poke through the head's rounded surface even when each
    # axis alone measured safe (confirmed: caused small breach caps on the
    # first attempt without this clip).
    clip = ellipsoid(27.0, 30.0, 21.2, HEAD_CAVITY_CENTER, sub=3)
    return b.intersection(clip, engine="manifold")

cavity = head_cavity_box().union(
         ellipsoid(*TORSO_CAVITY_R, TORSO_CAVITY_CENTER), engine="manifold").union(
         neck_channel(), engine="manifold")
print("cavity union: watertight=", cavity.is_watertight, "pieces=", len(cavity.split(only_watertight=False)), time.time()-t0)

# ---------------------------------------------------------------------------
# Button: plain through-hole, upper belly. Diameter updated to your latest
# measurement (14.04mm, was 10.80mm).
#
# NOTE: the dedicated back-clearance pocket (tried at 11mm, 9.5mm, then
# 7.3mm deep to avoid breaching the back skin near the shoulder) has been
# REMOVED per your feedback -- the previous shell (whole-torso hollow,
# no separate button pocket) was closer to what you wanted. The general
# torso cavity still gives room behind the button; there's just no extra
# dedicated pocket stacked on top of it any more.
# ---------------------------------------------------------------------------
# CORRECTED: the original landmark raycast probed from the wrong (-Z)
# direction and found the plain, unmarked side of the belly bulge -- the
# actual face-forward side (confirmed via direct OpenSCAD render: the face
# and the belly's decorative circle are BOTH on the +Z side) is opposite.
# Re-probed from +Z looking toward -Z to get the real belly landmark.
# Moved down further than a small nudge -- you asked to check the heart
# cap wouldn't hit the chin, and at the previous position (raw Y=80) it
# genuinely did: placing the actual heart_cap mesh at that spot (in its
# natural cusp-down orientation) and boolean-intersecting it with the raw
# body found a real 422 mm^3 overlap with the chin/jaw overhang, not just
# a close call. Walked the button position down and re-checked the same
# way at each step: still ~0 mm^3 touching at raw Y=75, fully clear (0
# overlap, real margin) at raw Y=70 -- used that. Re-probed the actual
# belly surface at Y=70 rather than assuming the old normal still applies.
# FIXED (round 1): this hole wasn't actually open all the way through.
# `inside=3.0` only cuts 3mm into the material, but the real distance to
# the hollow torso cavity is up to 5.75mm across the button's own
# footprint -- fixed by deepening to inside=8.0.
#
# DEEPENED FURTHER (round 2, for real access): 8mm only just breaches into
# the torso cavity's own near wall, so what's actually visible/reachable
# right behind the opening is that cavity wall itself, only ~2mm past the
# breach point -- fine for "is it open" but not for physically reaching in
# to work on the button/LEDs, which is what you actually wanted this for.
# Checked the real room available first: the torso cavity's FAR wall sits
# at 27.75mm+ depth everywhere across the button's footprint (29mm+ for
# the LEDs) -- so deepened both to inside=20.0, giving a real ~20mm
# straight corridor before opening into the general cavity, with 7-10mm
# of margin still before that cavity's own far side. Also applied to the
# LED holes below, not just the button.
BUTTON_DIA = 14.04
BUTTON_PT  = scale_pt([0, 70, 83.62])
BUTTON_N   = np.array([-0.053, 0.316, 0.947])
button_cutter = cyl_at(BUTTON_PT, BUTTON_N, BUTTON_DIA/2.0, inside=20.0, outside=6.0)

# ---------------------------------------------------------------------------
# LED holes: 4x, 3.2mm dia (real size), 4.5mm pitch, lower belly. Nudged up
# per your feedback (raw Y 40 -> 46, re-probed the actual surface there) --
# still kept well clear of the button (raw Y=46 vs button raw Y=80, ~17mm
# scaled centre distance, well over the button+bulb hole radii, learned
# from the otter build where a tighter gap there was a fragility risk).
# ---------------------------------------------------------------------------
# FIXED (round 1): same blind-hole bug as the button -- up to 6.75mm of
# real material across the four holes' footprints, past the old
# inside=2.0 reach. Deepened to inside=8.0.
# DEEPENED FURTHER (round 2, for real access): same reasoning as the
# button -- deepened to inside=20.0 for a real corridor, not just barely
# breaching the cavity's near wall. Cavity's far wall confirmed at 28mm+
# depth across all 4 holes' footprints, so 20mm keeps 8mm+ margin.
BULB_DIA = 3.2
PITCH = 4.5
BULB_CENTER = scale_pt([0, 46, 83.71])
BULB_N = np.array([0.056, -0.282, 0.958])
offsets = (np.arange(4) - 1.5) * PITCH
bulb_holes = [cyl_at(BULB_CENTER + np.array([1,0,0])*off, BULB_N, BULB_DIA/2.0, inside=20.0, outside=6.0) for off in offsets]

print("all cutters built", time.time()-t0)

all_cutters = trimesh.util.concatenate([cavity, button_cutter] + bulb_holes)
work = mesh.difference(all_cutters, engine="manifold")
print("shell+cavity+cutouts done: watertight=", work.is_watertight,
      "pieces=", len(work.split(only_watertight=False)), time.time()-t0)

# ---------------------------------------------------------------------------
# Split front/back at the mesh's natural mid-depth (Z), + alignment dowels.
# CORRECTED: front (face + button + LEDs) = +Z side, back (plain) = -Z side
# -- flipped from the original assumption, per the same landmark correction
# above. Also using a smaller box (100, not 400) here: confirmed via direct
# testing that boolean/slice operations against a box wildly oversized
# relative to the model can silently erode fine surface relief on this
# mesh -- ruled out as the actual cause of the front/back mixup (a plain
# manual per-triangle Z-filter, no boolean library involved at all, showed
# the same result), but kept smaller anyway as a low-cost precaution.
# ---------------------------------------------------------------------------
SPLIT_Z = 55.0 * SCALE
# CAUGHT BY VALIDATION: `big` here only bounds the box; it must exceed the
# model's full extents on every axis, or the split silently chops off
# whatever sticks out (it did -- at big=100 (half-extent 50) the box's Y
# range was only [-50,50], clipping off the ENTIRE HEAD once the shell was
# doubled to 100mm tall). `big` was previously shrunk from 400 to 100 as a
# low-cost precaution during the earlier front/back mixup investigation,
# back when the model was only 50mm tall -- it was never revisited when
# the model doubled in size. Set well above the model's own extents
# (~100mm tall, ~84mm wide) rather than a number carried over from a
# different scale.
def half_space(sign, big=300):
    b = trimesh.creation.box(extents=[big,big,big])
    b.apply_translation([0, 0, SPLIT_Z + sign*(big/2+0.05)])
    return b
front = work.intersection(half_space(1), engine="manifold")
back  = work.intersection(half_space(-1), engine="manifold")
print("split: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

# ---------------------------------------------------------------------------
# Front/back interlocking lip -- per your request, an actual registration
# lip in addition to the 2 alignment dowels: a thin tongue on the back
# piece nests into a matching (slightly oversized, for a real fit gap)
# pocket on the front piece. Computed from the ACTUAL cross-section of the
# hollowed body at the split plane (not a guessed shape), so it follows
# the real silhouette at that exact depth.
#
# Only applied to the main torso+head region, not the arm cross-sections:
# tried it there too (arm cross-section area ~337 each) but their
# thinner/more complex shape produced small disconnected fragments after
# the ring cut (confirmed via split() on the in-memory mesh, not a reload
# artifact) -- the main body is the biggest, most visible seam and the one
# that benefits most from a registration lip; arms/legs keep relying on
# the dowels alone.
# ---------------------------------------------------------------------------
LIP_WIDTH = 2.0        # how wide the lip ring is, following the silhouette inward
LIP_DEPTH = 1.0        # how far the tongue protrudes from back into front
LIP_CLEARANCE = 0.15   # pocket is this much larger all round, for a real fit gap
MIN_AREA = 500.0       # only the main torso+head region (area ~1398) qualifies
MIN_SUBPOLY_AREA = 2.0 # drop tiny sliver sub-polygons the buffer op can spit out
OVERLAP = 0.3          # extra reach INTO existing material so booleans weld/cut cleanly

section = work.section(plane_origin=[0,0,SPLIT_Z], plane_normal=[0,0,1])
planar, T2d = section.to_planar()

tongue_solids, pocket_solids = [], []
for poly in planar.polygons_full:
    ext = Polygon(poly.exterior.coords)
    if ext.area < MIN_AREA:
        continue
    # Use the real solid shape (exterior minus interior holes -- e.g. the
    # general torso cavity poking into this same cross-section), not just
    # the exterior outline, so the ring naturally narrows/avoids any spot
    # where the cavity already comes close to the skin.
    solid_poly = Polygon(poly.exterior.coords, [ring.coords for ring in poly.interiors]).buffer(0)
    inner = solid_poly.buffer(-LIP_WIDTH, join_style=2)
    if inner.is_empty or inner.area < 5.0:
        continue
    tongue_ring = solid_poly.difference(inner)
    pocket_outer = solid_poly.buffer(LIP_CLEARANCE, join_style=2)
    pocket_inner = solid_poly.buffer(-LIP_WIDTH - LIP_CLEARANCE, join_style=2)
    if pocket_inner.is_empty:
        continue
    pocket_ring = pocket_outer.difference(pocket_inner)

    # tongue extrudes from -OVERLAP (into the back's existing material) to
    # +LIP_DEPTH (into the front's territory); pocket from -OVERLAP to
    # +LIP_DEPTH+LIP_CLEARANCE -- both need real overlap with existing
    # material, not a 0-thickness seam, or they don't weld/cut cleanly
    # (same lesson as the alignment dowels above).
    for geom, target, z0, z1 in [(tongue_ring, tongue_solids, -OVERLAP, LIP_DEPTH),
                                  (pocket_ring, pocket_solids, -OVERLAP, LIP_DEPTH+LIP_CLEARANCE)]:
        polys = geom.geoms if hasattr(geom, "geoms") else [geom]
        for p in polys:
            if p.is_empty or p.area < MIN_SUBPOLY_AREA:
                continue
            path2d = trimesh.load_path(np.array(p.exterior.coords))
            solid = path2d.extrude(z1 - z0)
            if isinstance(solid, list):
                solid = trimesh.util.concatenate(solid)
            solid.apply_translation([0, 0, z0])
            target.append(solid)

tongue_world = trimesh.util.concatenate(tongue_solids)
tongue_world.apply_transform(T2d)
pocket_world = trimesh.util.concatenate(pocket_solids)
pocket_world.apply_transform(T2d)

back = back.union(tongue_world, engine="manifold")
front = front.difference(pocket_world, engine="manifold")
print("lip done: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

def dowel_cyl(pt, axis, r, h):
    c = trimesh.creation.cylinder(radius=r, height=h, sections=24)
    R = trimesh.geometry.align_vectors([0,0,1], axis)
    T = np.eye(4); T[:3,:3]=R[:3,:3]; T[:3,3]=pt
    c.apply_transform(T); return c

# Re-verified at the 100mm scale by sampling actual solid-vs-cavity points
# (not assumed from the old raw*SCALE positions, which turned out to be
# wrong at this scale -- see below). Two dowels, spread in both X and Y
# for a stable anti-rotation lock:
#  - one in a leg (X=8, well clear of the mid-line gap between the legs
#    and clear of the torso cavity)
#  - one in the solid gap between the torso cavity's top and the head
#    cavity's bottom (a much narrower gap than at 50mm since the head
#    cavity box was doubled in absolute size -- confirmed by direct
#    point-sampling, not proportional carry-over)
# CAUGHT BY VALIDATION: the old DOWEL_Y = [20*SCALE, 110*SCALE] positions
# (both at X=0) were WRONG at this scale -- the lower one landed in the
# empty gap between the legs (outside the mesh entirely, not solid), and
# the upper one landed inside the doubled head cavity box. Both produced
# floating, unwelded dowel pins (confirmed via split(only_watertight=False)
# showing 2 extra disconnected pieces on the back shell) -- a real defect
# that would NOT have printed as functional alignment pins. Repositioned
# and each candidate individually verified solid + clear of every cavity
# with a small ring of sample points, not just a single point.
#
# MOVED to run AFTER the lip (not before, as originally written): doing
# the dowel hole/pin cuts before the lip caused extra fragmentation --
# the upper dowel sits close to where the lip ring runs, and cutting the
# dowel hole first then the lip pocket on top of it produced more complex,
# badly-behaved overlapping cuts than doing the lip first and the (much
# smaller, simpler) dowel features afterward.
DOWEL_XY = [(8.0, 10.0), (0.0, 47.5)]
pins = trimesh.util.concatenate([dowel_cyl((dx,dy,SPLIT_Z+0.6), [0,0,1], 1.1, 2.6) for dx,dy in DOWEL_XY])
back = back.union(pins, engine="manifold")
holes = trimesh.util.concatenate([dowel_cyl((dx,dy,SPLIT_Z-0.4), [0,0,1], 1.25, 3.6) for dx,dy in DOWEL_XY])
front = front.difference(holes, engine="manifold")
print("clip done: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

# `front` (the low-Z half, containing the face/button/LED holes) exports
# as front_shell.stl -- reverted back to this straightforward mapping per
# final feedback, after a brief detour swapping the names the other way.
front.export("front_shell_monkey.stl")
back.export("back_shell_monkey.stl")
print("exported shells", time.time()-t0)

# ---------------------------------------------------------------------------
# Decorative heart cap -- rounded-out heart profile (Chaikin corner-cutting
# smooths the pointed classic-heart curve while keeping the two-lobe heart
# silhouette), and now built HOLLOW like a real cap/cup instead of a solid
# block: a thin shell with a recessed pocket on the underside sized to fit
# down over the real button's own cap, so it just sits over it rather than
# needing to be glued as a solid lump.
# ---------------------------------------------------------------------------
import math
def heart_pts_2d(scale):
    pts=[]
    for i in range(41):
        t = math.pi - (i/40)*2*math.pi
        x = 16*math.sin(t)**3
        y = 13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
        pts.append((x*scale,y*scale))
    return pts

def chaikin_smooth(pts, iterations=3):
    pts = list(pts)
    for _ in range(iterations):
        new_pts = []
        n = len(pts)
        for i in range(n):
            p0 = np.array(pts[i]); p1 = np.array(pts[(i+1) % n])
            new_pts.append(tuple(0.75*p0 + 0.25*p1))
            new_pts.append(tuple(0.25*p0 + 0.75*p1))
        pts = new_pts
    return pts

# Resized per your button measurements: cap needs to clear a 14.04mm hole
# and the button sticks up ~8.03mm, so the pocket has to be both deeper and
# wider than the first pass. Heart enlarged to keep a solid wall/roof
# around a bigger pocket.
heart_scale = 0.95
outer_pts = chaikin_smooth(heart_pts_2d(heart_scale), iterations=3)
outer_path = trimesh.load_path(np.array(outer_pts + [outer_pts[0]]))
POCKET_DEPTH = 8.2   # 8.03mm measured + ~0.2mm clearance
ROOF = 1.2
CAP_HEIGHT = POCKET_DEPTH + ROOF
shell = outer_path.extrude(CAP_HEIGHT)
if isinstance(shell, list):
    shell = trimesh.util.concatenate(shell)

# pocket: a plain circle (not a small heart -- that curve self-intersects
# and produces a broken mesh at this scale, confirmed via broken_faces()
# check) recessed up from the open (button-facing) bottom face. It's a
# hidden internal cavity, invisible from outside, so it doesn't need to be
# heart-shaped -- just big enough to clear the button's own cap (14.04mm)
# with a comfortable roof and wall margin all round.
pocket = trimesh.creation.cylinder(radius=9.0, height=POCKET_DEPTH, sections=48)
pocket.apply_translation([0, 0, POCKET_DEPTH/2])
# extrude() builds Z=0..depth; align pocket's open face with the shell's
# bottom (Z=0) so the recess opens downward onto the button
heart_cap = shell.difference(pocket, engine="manifold")
heart_cap.export("heart_cap_monkey.stl")
print("heart cap: watertight=", heart_cap.is_watertight, "extents=", heart_cap.extents)
print("ALL DONE", time.time()-t0)

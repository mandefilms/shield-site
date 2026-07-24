"""
Parametric build for the Shield owl companion keyring toy (rev B, matches
VCX_mascot_component_sheet.pdf + VCX_mascot_toy_concept.pdf).

Architecture: single printed body, split front/back with a snap clip for
full assembly access, PLUS a small screwed battery door on the back for
routine CR2032 swaps without opening the main clip.

Electronics: XIAO nRF52840 (vertical, against back wall), CR2032 holder
(against back wall, upper/head area, behind the screwed door), momentary
tummy button (behind the chest heart), 4x LED light-pipe holes (charge
bar row), 12mm piezo + sound-slit vents (lower front).

Outputs 6 colour-separated STLs: back_teal, front_teal, cream_face,
orange_beak_feet, heart_accent, battery_door.

Run: python3 build.py
"""
import os
import cadquery as cq
from cadquery import Vector, Matrix
import params as P

OUT = "out"
os.makedirs(OUT, exist_ok=True)


def ellipsoid(rx, ry, rz):
    full_sphere = cq.Solid.makeSphere(1.0, angleDegrees1=-90, angleDegrees2=90, angleDegrees3=360)
    return full_sphere.transformGeometry(Matrix([[rx, 0, 0, 0], [0, ry, 0, 0], [0, 0, rz, 0]]))


def box_at(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def half_box(y_sign, big=300):
    """Solid occupying y>0.05 (y_sign=+1, 'front') or y<-0.05 (y_sign=-1,
    'back'), offset off the exact seam so booleans don't hit tangency."""
    half = big / 2
    if y_sign > 0:
        return box_at(-half, half, 0.05, half, -half, half)
    return box_at(-half, half, -half, -0.05, -half, half)


def cyl_y(radius, length, x, y0, z):
    """Cylinder whose axis runs along +Y, base at y0."""
    return cq.Solid.makeCylinder(radius, length, Vector(x, y0, z), Vector(0, 1, 0))


BODY_Z = P.BODY_RZ - 3.0
HEAD_Z = P.HEAD_Z_OFFSET

# ---------------------------------------------------------------------------
# 1. OUTER SILHOUETTE
# ---------------------------------------------------------------------------
body = ellipsoid(P.BODY_RX, P.BODY_RY, P.BODY_RZ).translate((0, 0, BODY_Z))
head = ellipsoid(P.HEAD_RX, P.HEAD_RY, P.HEAD_RZ).translate((0, 0, HEAD_Z))

foot_l = ellipsoid(6.0, 5.2, 3.4).translate((-7.5, 4.0, -2.5))
foot_r = ellipsoid(6.0, 5.2, 3.4).translate((7.5, 4.0, -2.5))

ear_l = ellipsoid(2.6, 2.3, 3.6).rotate((0, 0, 0), (0, 1, 0), -14).translate((-9.8, 1.4, HEAD_Z + 10.8))
ear_r = ellipsoid(2.6, 2.3, 3.6).rotate((0, 0, 0), (0, 1, 0), 14).translate((9.8, 1.4, HEAD_Z + 10.8))

# compact "tucked" wings sitting against the body sides (folded-arm look,
# closer to the otter reference than the marketing render's spread wings)
def make_wing(sign):
    w = ellipsoid(6.0, 4.2, 9.5)
    w = w.rotate((0, 0, 0), (0, 0, 1), sign * 10)
    return w.translate((sign * (P.BODY_RX + 2.0), 2.0, BODY_Z - 1.0))

wing_l = make_wing(-1)
wing_r = make_wing(1)

outer_body = body.fuse(head).fuse(foot_l).fuse(foot_r).fuse(ear_l).fuse(ear_r).fuse(wing_l).fuse(wing_r)

loop_outer_r, loop_inner_r, loop_tube_r = 4.2, 2.1, 1.3
loop = (
    cq.Workplane("XZ")
    .center(0, HEAD_Z + P.HEAD_RZ + loop_outer_r - 1.6)
    .circle(loop_outer_r).circle(loop_inner_r)
    .extrude(loop_tube_r, both=True)
    .val()
)
loop_post = ellipsoid(2.6, 2.6, 4.0).translate((0, -0.5, HEAD_Z + P.HEAD_RZ - 2.0))
outer = outer_body.fuse(loop).fuse(loop_post)

bb = outer.BoundingBox()
print(f"Outer silhouette: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm (W x D x H)")
cq.exporters.export(cq.Workplane(obj=outer), f"{OUT}/_debug_outer.stl")


def skin_layer(thickness, extra_z=0.0):
    inner = ellipsoid(P.BODY_RX - thickness, P.BODY_RY - thickness, P.BODY_RZ - thickness).translate((0, 0, BODY_Z)).fuse(
        ellipsoid(P.HEAD_RX - thickness, P.HEAD_RY - thickness, P.HEAD_RZ - thickness).translate((0, 0, HEAD_Z))
    )
    return outer_body.cut(inner)


# ---------------------------------------------------------------------------
# 2. HOLLOW CAVITY — head + body only
# ---------------------------------------------------------------------------
cav_body = ellipsoid(P.BODY_RX - P.WALL, P.BODY_RY - P.WALL, P.BODY_RZ - P.WALL).translate((0, 0, BODY_Z))
cav_head = ellipsoid(P.HEAD_RX - P.WALL, P.HEAD_RY - P.WALL, P.HEAD_RZ - P.WALL).translate((0, 0, HEAD_Z))
cavity = cav_body.fuse(cav_head)

shell_raw = outer.cut(cavity)
print("Hollow shell volume:", round(shell_raw.Volume(), 1))

# ---------------------------------------------------------------------------
# 3. ELECTRONICS STANDOFFS
# ---------------------------------------------------------------------------
BURY = -60
FRONT_BURY = 60

# --- XIAO nRF52840: vertical, against the back wall (y<0)
rail_w = 1.8
rail_gap_half = P.XIAO_W / 2 + P.XIAO_CLEARANCE
xiao_z0, xiao_z1 = 2.0, 2.0 + P.XIAO_L + 2.0
slot_front_y = -9.0  # y-plane where the board's front face lands

rail_l = box_at(-rail_gap_half - rail_w, -rail_gap_half, BURY, slot_front_y, xiao_z0, xiao_z1)
rail_r = box_at(rail_gap_half, rail_gap_half + rail_w, BURY, slot_front_y, xiao_z0, xiao_z1)
z_stop = box_at(-rail_gap_half, rail_gap_half, BURY, slot_front_y - P.XIAO_T - P.XIAO_CLEARANCE, xiao_z0 - 1.2, xiao_z0)
xiao_back_features = rail_l.fuse(rail_r).fuse(z_stop)
xiao_front_boss = box_at(-rail_gap_half, rail_gap_half, slot_front_y, FRONT_BURY, xiao_z0, xiao_z1)

# --- CR2032 holder: against the back wall, upper body / head-junction area,
#     behind a removable screwed door. Round-face-out orientation (diameter
#     spans X-Z, thickness along Y).
holder_r = max(P.HOLDER_L, P.HOLDER_W) / 2 + P.HOLDER_CLEARANCE
holder_cx, holder_cz = 0.0, 34.0
holder_y_back = -13.0
holder_y_front = holder_y_back + P.HOLDER_T + P.HOLDER_CLEARANCE

# shallow registration lip the holder drops into (helps it stay centred)
holder_lip = cq.Solid.makeCylinder(holder_r + 1.6, 1.2, Vector(holder_cx, BURY, holder_cz), Vector(0, 1, 0))
holder_lip = holder_lip.cut(cq.Solid.makeCylinder(holder_r, 1.2 + 0.2, Vector(holder_cx, BURY - 0.1, holder_cz), Vector(0, 1, 0)))

# access opening through the back shell (cut, not union) + surrounding flat
# rim for the door to seat against
door_open_r = holder_r + 1.0
door_opening = cq.Solid.makeCylinder(door_open_r, 20, Vector(holder_cx, -20, holder_cz), Vector(0, 1, 0))
door_seat = cq.Solid.makeCylinder(door_open_r + P.DOOR_SCREW_INSET + 3.0, 1.0, Vector(holder_cx, -0.9, holder_cz), Vector(0, 1, 0))

# 2 screw bosses for the door, opposite corners of the opening
screw_positions = [
    (holder_cx - (door_open_r + P.DOOR_SCREW_INSET) * 0.75, holder_cz - (door_open_r + P.DOOR_SCREW_INSET) * 0.55),
    (holder_cx + (door_open_r + P.DOOR_SCREW_INSET) * 0.75, holder_cz + (door_open_r + P.DOOR_SCREW_INSET) * 0.55),
]
screw_bosses = []
screw_pilot_holes = []
for sx, sz in screw_positions:
    boss = cq.Solid.makeCylinder(2.6, 6.0, Vector(sx, BURY, sz), Vector(0, 1, 0))
    boss = boss.intersect(box_at(-40, 40, BURY, -0.8, -40, 40))
    screw_bosses.append(boss)
    pilot = cq.Solid.makeCylinder(P.DOOR_SCREW_D / 2, 8.0, Vector(sx, BURY, sz), Vector(0, 1, 0))
    screw_pilot_holes.append(pilot)

battery_features = holder_lip
for b in screw_bosses:
    battery_features = battery_features.fuse(b)
for p in screw_pilot_holes:
    battery_features = battery_features.cut(p)

# --- Tummy button: small boss on the front wall, behind the chest heart
button_cx, button_cz = 0.0, 21.0
button_boss = cyl_y(P.BUTTON_D / 2 + 1.2, 30, button_cx, -2, button_cz)
button_hole = cq.Solid.makeCylinder(P.BUTTON_CAP_D / 2 + 0.25, 20, Vector(button_cx, -1, button_cz), Vector(0, 1, 0))

# --- LED charge-bar: 4 light-pipe channels through the front shell
led_z = 12.5
led_xs = [-1.5 * P.LED_PITCH, -0.5 * P.LED_PITCH, 0.5 * P.LED_PITCH, 1.5 * P.LED_PITCH]
led_holes = [cq.Solid.makeCylinder(P.LED_PIPE_D / 2, 30, Vector(x, -2, led_z), Vector(0, 1, 0)) for x in led_xs]
led_shelf = box_at(led_xs[0] - 3, led_xs[-1] + 3, BURY, -6.5, led_z - 3, led_z + 3)

# --- Piezo (12mm) + sound-slit vents, lower front
piezo_cz = 6.0
piezo_pocket_seat = cq.Solid.makeCylinder(P.PIEZO_D / 2 + 0.4, 1.0, Vector(0, 12.0, piezo_cz), Vector(0, 1, 0))
piezo_boss = cq.Solid.makeCylinder(P.PIEZO_D / 2 + 1.6, 30, Vector(0, -2, piezo_cz), Vector(0, 1, 0))
slit_holes = [box_at(x - 2.2, x + 2.2, -2, 6, piezo_cz - 0.4, piezo_cz + 0.4) for x in (-5.5, 0.0, 5.5)]

standoffs = (
    xiao_back_features.fuse(xiao_front_boss)
    .fuse(battery_features)
    .fuse(button_boss)
    .fuse(led_shelf)
    .fuse(piezo_boss)
)
shell_with_standoffs = shell_raw.fuse(standoffs)
for h in [door_opening] + led_holes + slit_holes + [button_hole]:
    shell_with_standoffs = shell_with_standoffs.cut(h)
shell_with_standoffs = shell_with_standoffs.fuse(door_seat)
shell_with_standoffs = shell_with_standoffs.intersect(outer)
print("Standoffs + door opening + LED/piezo features OK. Volume:", round(shell_with_standoffs.Volume(), 1))

# ---------------------------------------------------------------------------
# 4. SPLIT INTO FRONT / BACK + THE CLIP
# ---------------------------------------------------------------------------
front_raw = shell_with_standoffs.intersect(half_box(+1))
back_raw = shell_with_standoffs.intersect(half_box(-1))

dowel_positions = [(-13, BODY_Z), (13, BODY_Z)]
bump_positions = [(0, HEAD_Z + P.HEAD_RZ - 3), (0, 3.0)]
bump_r = 1.2

back_half = back_raw
for dx, dz in dowel_positions:
    back_half = back_half.fuse(cq.Solid.makeCylinder(P.DOWEL_D / 2, P.DOWEL_L, Vector(dx, -0.5, dz), Vector(0, 1, 0)))
for bx, bz in bump_positions:
    back_half = back_half.fuse(
        cq.Solid.makeSphere(bump_r, angleDegrees1=-90, angleDegrees2=90, angleDegrees3=360).translate((bx, -0.3, bz))
    )

front_half = front_raw
for dx, dz in dowel_positions:
    front_half = front_half.cut(cq.Solid.makeCylinder(P.DOWEL_D / 2 + 0.15, P.DOWEL_L + 1, Vector(dx, 0.5, dz), Vector(0, -1, 0)))
for bx, bz in bump_positions:
    front_half = front_half.cut(
        cq.Solid.makeSphere(bump_r + 0.15, angleDegrees1=-90, angleDegrees2=90, angleDegrees3=360).translate((bx, 0.3, bz))
    )

# ---------------------------------------------------------------------------
# 5b. COLOUR PATCHES — carved as thin surface-conforming "skins" so they sit
#     flush with the body's curvature, using skin_layer() + a region shape.
# ---------------------------------------------------------------------------
PATCH_T = 1.1  # colour-patch thickness recessed into the teal shell

def region_prism(shape2d_solid):
    return shape2d_solid

# face + chest patch: one contiguous cream area from the face down over the
# chest (matches the reference art — face and belly are one connected patch)
face_region = ellipsoid(9.5, 30, 15.5).translate((0, 0, 27.0))
cream_patch_full = skin_layer(PATCH_T).intersect(face_region).intersect(half_box(+1))

# beak: small cone poking from the face, orange
beak = (
    cq.Solid.makeCone(2.6, 0.3, 5.0, Vector(0, 0, 0), Vector(0, 1, 0))
    .rotate(Vector(0, 0, 0), Vector(1, 0, 0), -6)
    .translate((0, P.HEAD_RY - 3.0, HEAD_Z - 3.0))
)
beak_region = cq.Solid.makeCylinder(4.0, 20, Vector(0, 6.0, HEAD_Z - 3.0), Vector(0, 1, 0))

# feet tips: small orange rounded toe accents at the base of each foot
foot_tip_l = ellipsoid(3.4, 3.0, 1.6).translate((-7.5, 6.5, -3.6))
foot_tip_r = ellipsoid(3.4, 3.0, 1.6).translate((7.5, 6.5, -3.6))
feet_tip_region = box_at(-11, 11, -60, 60, -60, 0.4)

orange_parts = beak.fuse(foot_tip_l.intersect(outer)).fuse(foot_tip_r.intersect(outer))
orange_parts = orange_parts.intersect(outer)

# cream patch: remove the beak footprint (beak sits in its own hole) — the
# feet tips are separate small protrusions, not part of the cream skin.
cream_patch = cream_patch_full.cut(beak_region)

# heart accent: a small heart-profile pad over the tummy button, 4th colour
def heart_wire(scale, z_off):
    pts = []
    import math
    for i in range(41):
        t = math.pi - (i / 40) * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * scale, y * scale + z_off))
    return pts

heart_pts = heart_wire(0.30, 0)
heart_profile = cq.Workplane("XZ").center(button_cx, button_cz).polyline(heart_pts).close()
heart_prism = heart_profile.extrude(20).translate((0, -10, 0)).val()

heart_patch = skin_layer(PATCH_T).intersect(heart_prism).intersect(half_box(+1))
# extend the heart inward so it also caps the button hole (acts as the cap
# the child presses, contacting the tactile switch behind it)
heart_plunger = cq.Solid.makeCylinder(P.BUTTON_CAP_D / 2 - 0.2, 4.0, Vector(button_cx, 9.0, button_cz), Vector(0, 1, 0))
heart_accent = heart_patch.fuse(heart_plunger.intersect(box_at(-20, 20, 9.0, 20, -20, 60)))

# remove the patch footprints from the front teal shell so they seat flush
front_half = front_half.cut(cream_patch_full).cut(beak.intersect(outer)).cut(foot_tip_l.intersect(outer)).cut(foot_tip_r.intersect(outer)).cut(heart_patch)

print("Front/back split + clip + colour patches OK. front vol", round(front_half.Volume(), 1), "back vol", round(back_half.Volume(), 1))
cq.exporters.export(cq.Workplane(obj=back_half), f"{OUT}/_debug_back.stl")
cq.exporters.export(cq.Workplane(obj=front_half), f"{OUT}/_debug_front.stl")
cq.exporters.export(cq.Workplane(obj=cream_patch), f"{OUT}/_debug_cream.stl")
cq.exporters.export(cq.Workplane(obj=orange_parts), f"{OUT}/_debug_orange.stl")
cq.exporters.export(cq.Workplane(obj=heart_accent), f"{OUT}/_debug_heart.stl")

# ---------------------------------------------------------------------------
# 5. BATTERY DOOR (separate small part, screws to back_half)
# ---------------------------------------------------------------------------
door_blank_region = cq.Solid.makeCylinder(door_open_r + P.DOOR_SCREW_INSET + 3.0, 6, Vector(holder_cx, -20, holder_cz), Vector(0, 1, 0))
door_skin = skin_layer(1.8)
battery_door = door_skin.intersect(door_blank_region)
for sx, sz in screw_positions:
    battery_door = battery_door.cut(cq.Solid.makeCylinder(P.DOOR_SCREW_D / 2 + 0.15, 8, Vector(sx, -20, sz), Vector(0, 1, 0)))
print("Battery door volume:", round(battery_door.Volume(), 1))

# ---------------------------------------------------------------------------
# 6. FINAL EXPORTS — STL (fine tessellation, for slicing) + STEP (exact
#    BREP, for re-import/inspection or if a slicer's STL repair struggles)
# ---------------------------------------------------------------------------
final_parts = {
    "back_teal": back_half,
    "front_teal": front_half,
    "cream_face": cream_patch,
    "orange_beak_feet": orange_parts,
    "heart_accent": heart_accent,
    "battery_door_teal": battery_door,
}
for name, solid in final_parts.items():
    wp = cq.Workplane(obj=solid)
    cq.exporters.export(wp, f"{OUT}/{name}.stl", tolerance=0.01, angularTolerance=0.05)
    cq.exporters.export(wp, f"{OUT}/{name}.step")
    print(f"exported {name}: volume={round(solid.Volume(),1)}mm3")

print("\nDone. All 6 parts exported to", OUT)

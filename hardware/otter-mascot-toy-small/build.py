import trimesh, numpy as np, pickle, time
t0=time.time()

SCALE = 60.0/114.3
print("SCALE=", SCALE)

BASE = "../otter-build/"
mesh = trimesh.load(BASE+"otter_patched2.stl")
mesh.apply_scale(SCALE)
outer_pristine = mesh.copy()
print("shell loaded+scaled, extents=", mesh.extents, time.time()-t0)

with open(BASE+"landmarks2.pkl","rb") as f: lm_body = pickle.load(f)
with open(BASE+"landmarks3.pkl","rb") as f: lm_face = pickle.load(f)

def scale_pt(pt): return np.array(pt)*SCALE

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

# ---------------------------------------------------------------------------
# Cavity: NOT a proportional scale-down of the original -- re-fit fresh so the
# fixed-size XIAO nRF52840 (21 x 17.8mm) + CR2032 + button body still has room
# at 60mm total height. Two overlapping ellipsoids: an upper "electronics bay"
# for the board/battery, and a lower "button pocket" reaching down toward the
# belly so the button + its wiring have somewhere to sit.
# ---------------------------------------------------------------------------
def ellipsoid(rx,ry,rz,center):
    e = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
    e.apply_transform(np.diag([rx,ry,rz,1]))
    e.apply_translation(center)
    return e

main_cavity = ellipsoid(17, 15, 12, [0, -3, 8])
button_pocket = ellipsoid(7, 14, 9, [-2, -9, -9])
cavity = main_cavity.union(button_pocket, engine="manifold")
print("cavity union: watertight=", cavity.is_watertight, "pieces=", len(cavity.split(only_watertight=False)), time.time()-t0)

# ---------------------------------------------------------------------------
# Button mount: simple straight through-hole, no counterbore/countersink.
# Confirmed size: 10.80mm diameter -- that's the only number needed.
# ---------------------------------------------------------------------------
BUTTON_HOLE_R = 10.80/2.0

heart_pt_raw, heart_n_raw = lm_body["heart"]
heart_pt_raw = scale_pt(heart_pt_raw)

# moved up per your ask -- it was sitting down near the feet. Same
# surface-tangent-shift + raycast-reproject technique used for the bulbs,
# just in the "up" direction instead of "down".
world_up = np.array([0,0,1.0])
up_tangent = world_up - np.dot(world_up, heart_n_raw) * heart_n_raw
up_tangent /= np.linalg.norm(up_tangent)
BUTTON_SHIFT_UP = 14.0
target = heart_pt_raw + up_tangent * BUTTON_SHIFT_UP
ray_origin = target + np.array(heart_n_raw) * 30.0
locs, ir, it = mesh.ray.intersects_location(ray_origin.reshape(1,3), (-np.array(heart_n_raw)).reshape(1,3))
if len(locs):
    dists = np.linalg.norm(locs - ray_origin, axis=1)
    heart_pt = locs[np.argmin(dists)]
    heart_n = mesh.face_normals[it[np.argmin(dists)]]
    heart_n /= np.linalg.norm(heart_n)
else:
    heart_pt = target; heart_n = heart_n_raw
print("button moved up", BUTTON_SHIFT_UP, "mm: old", heart_pt_raw, "-> new", heart_pt, time.time()-t0)

button_cutter = cyl_at(heart_pt, heart_n, BUTTON_HOLE_R, inside=3.0, outside=6.0)

# ---------------------------------------------------------------------------
# Bulb holes: kept at their real physical size (3.2mm dia, "a hair" bigger
# than 3.0mm per your ask) regardless of shell scale -- these have to fit
# actual 3mm bulbs, so they do NOT shrink with the shell. Re-laid-out along
# the belly with a fixed 4.5mm pitch (not the old scaled-down 7mm pitch,
# which would leave under 1mm of material between holes at this size).
# ---------------------------------------------------------------------------
bulb_pts = np.array([scale_pt(lm_body[n][0]) for n in ["bulb1","bulb2","bulb3","bulb4"]])
bulb_normal = np.mean([lm_body[n][1] for n in ["bulb1","bulb2","bulb3","bulb4"]], axis=0)
bulb_normal /= np.linalg.norm(bulb_normal)
center_pt_raw = bulb_pts.mean(axis=0)
row_dir = bulb_pts[-1]-bulb_pts[0]
row_dir /= np.linalg.norm(row_dir)

# moved down a bit per your ask -- shift along the local surface-tangent
# "down" direction, then re-project onto the actual belly surface (raycast)
# so the holes stay properly seated on the curved shell, not just floating
# in space at the shifted coordinate.
world_up = np.array([0,0,1.0])
up_tangent = world_up - np.dot(world_up, bulb_normal) * bulb_normal
up_tangent /= np.linalg.norm(up_tangent)
down_dir = -up_tangent
SHIFT_DOWN = 6.0
target = center_pt_raw + down_dir * SHIFT_DOWN
ray_origin = target + bulb_normal * 30.0
locs, ir, it = mesh.ray.intersects_location(ray_origin.reshape(1,3), (-bulb_normal).reshape(1,3))
if len(locs):
    dists = np.linalg.norm(locs - ray_origin, axis=1)
    center_pt = locs[np.argmin(dists)]
    bulb_normal = mesh.face_normals[it[np.argmin(dists)]]
    bulb_normal /= np.linalg.norm(bulb_normal)
else:
    center_pt = target  # fallback, shouldn't happen
print("bulb row moved down", SHIFT_DOWN, "mm: old center", center_pt_raw, "-> new center", center_pt, time.time()-t0)

PITCH = 4.5
BULB_R = 1.6  # 3.2mm dia
offsets = (np.arange(4) - 1.5) * PITCH
bulb_holes = []
for off in offsets:
    pt = center_pt + row_dir*off
    bulb_holes.append(cyl_at(pt, bulb_normal, BULB_R, inside=2.0, outside=6.0))

# NOTE: no eye/nose colour patches on this build -- face stays plain, per your
# call to skip those details on the small version.

print("all cutters built", time.time()-t0)

all_cutters = trimesh.util.concatenate([cavity, button_cutter] + bulb_holes)
work = mesh.difference(all_cutters, engine="manifold")
print("shell+cavity+cutouts done: watertight=", work.is_watertight,
      "pieces=", len(work.split(only_watertight=False)), time.time()-t0)

# split front/back
def half_box(sign, big=300):
    b = trimesh.creation.box(extents=[big,big,big]); b.apply_translation([0, sign*(big/2+0.05), 0]); return b
front = work.intersection(half_box(-1), engine="manifold")
back  = work.intersection(half_box(+1), engine="manifold")
print("split: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

# alignment dowels -- slightly smaller than the 114mm version since walls are thinner here
def dowel_cyl(pt, axis, r, h):
    c = trimesh.creation.cylinder(radius=r, height=h, sections=24)
    R = trimesh.geometry.align_vectors([0,0,1], axis)
    T = np.eye(4); T[:3,:3]=R[:3,:3]; T[:3,3]=pt
    c.apply_transform(T); return c
pins = trimesh.util.concatenate([dowel_cyl((dx,0.6,0), [0,-1,0], 1.1, 2.6) for dx in [-11,11]])
back = back.union(pins, engine="manifold")
holes = trimesh.util.concatenate([dowel_cyl((dx,-0.4,0), [0,1,0], 1.25, 3.6) for dx in [-11,11]])
front = front.difference(holes, engine="manifold")
print("clip done: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

front.export("front_shell_small.stl")
back.export("back_shell_small.stl")
print("exported shells", time.time()-t0)

# ---------------------------------------------------------------------------
# Decorative heart cap -- glued on top of the real button afterward, NOT a
# functional plunger. Sized to comfortably overhang the 16.88mm button cap.
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
heart_scale = 0.72  # width ~ 16*0.72*2 = 23mm across, overhangs the 16.88mm button
path2d = trimesh.load_path(np.array(heart_pts_2d(heart_scale) + [heart_pts_2d(heart_scale)[0]]))
heart_cap = path2d.extrude(2.2)
if isinstance(heart_cap, list):
    heart_cap = trimesh.util.concatenate(heart_cap)
heart_cap.export("heart_cap_small.stl")
print("heart cap exported", time.time()-t0)

with open("build_summary.pkl","wb") as f:
    pickle.dump({
        "main_cavity_params": (17,15,12,[0,-3,8]),
        "button_pocket_params": (10,15,10,[-2,-9,-9]),
        "heart_pt": heart_pt, "heart_n": heart_n,
        "bulb_pts": [center_pt + row_dir*o for o in offsets],
        "bulb_normal": bulb_normal,
    }, f)
print("ALL DONE", time.time()-t0)

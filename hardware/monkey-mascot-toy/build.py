import trimesh, numpy as np, time
t0=time.time()

SCALE = 50.0/199.0
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
HEAD_CAVITY_HALF   = np.array([10.5, 11.4, 7])   # scaled mm (X, Y, Z)
HEAD_CAVITY_CENTER = np.array([0, 145, 52]) * SCALE

TORSO_CAVITY_R      = np.array([20, 16, 12]) * SCALE
TORSO_CAVITY_CENTER = np.array([0, 60, 36]) * SCALE

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
    clip = ellipsoid(13.5, 15.0, 10.6, HEAD_CAVITY_CENTER, sub=3)
    return b.intersection(clip, engine="manifold")

cavity = head_cavity_box().union(
         ellipsoid(*TORSO_CAVITY_R, TORSO_CAVITY_CENTER), engine="manifold").union(
         neck_channel(), engine="manifold")
print("cavity union: watertight=", cavity.is_watertight, "pieces=", len(cavity.split(only_watertight=False)), time.time()-t0)

# ---------------------------------------------------------------------------
# Button: plain 10.80mm through-hole (confirmed real size), upper belly.
# ---------------------------------------------------------------------------
BUTTON_DIA = 10.80
BUTTON_PT  = scale_pt([0, 85, 25.109])
BUTTON_N   = np.array([0.0807, 0.3031, -0.9495])
button_cutter = cyl_at(BUTTON_PT, BUTTON_N, BUTTON_DIA/2.0, inside=3.0, outside=6.0)

# ---------------------------------------------------------------------------
# LED holes: 4x, 3.2mm dia (real size), 4.5mm pitch, lower belly -- kept well
# clear of the button (raw Y=38 vs button raw Y=85, ~11.8mm scaled centre
# distance, ~4.8mm real clearance after hole radii, learned from the otter
# build where a tighter gap there was a fragility risk).
# ---------------------------------------------------------------------------
BULB_DIA = 3.2
PITCH = 4.5
BULB_CENTER = scale_pt([0, 38, 24.3])
BULB_N = np.array([-0.0433, -0.65, -0.7587])
offsets = (np.arange(4) - 1.5) * PITCH
bulb_holes = [cyl_at(BULB_CENTER + np.array([1,0,0])*off, BULB_N, BULB_DIA/2.0, inside=2.0, outside=6.0) for off in offsets]

print("all cutters built", time.time()-t0)

all_cutters = trimesh.util.concatenate([cavity, button_cutter] + bulb_holes)
work = mesh.difference(all_cutters, engine="manifold")
print("shell+cavity+cutouts done: watertight=", work.is_watertight,
      "pieces=", len(work.split(only_watertight=False)), time.time()-t0)

# ---------------------------------------------------------------------------
# Split front/back at the mesh's natural mid-depth (Z), + alignment dowels.
# Front = -Z side (face), Back = +Z side.
# ---------------------------------------------------------------------------
SPLIT_Z = 55.0 * SCALE
def half_space(sign, big=400):
    b = trimesh.creation.box(extents=[big,big,big])
    b.apply_translation([0, 0, SPLIT_Z + sign*(big/2+0.05)])
    return b
front = work.intersection(half_space(-1), engine="manifold")
back  = work.intersection(half_space(1), engine="manifold")
print("split: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

def dowel_cyl(pt, axis, r, h):
    c = trimesh.creation.cylinder(radius=r, height=h, sections=24)
    R = trimesh.geometry.align_vectors([0,0,1], axis)
    T = np.eye(4); T[:3,:3]=R[:3,:3]; T[:3,3]=pt
    c.apply_transform(T); return c

DOWEL_Y = [40*SCALE, 130*SCALE]  # roughly torso and head-base height
pins = trimesh.util.concatenate([dowel_cyl((0,dy,SPLIT_Z+0.6), [0,0,1], 1.1, 2.6) for dy in DOWEL_Y])
back = back.union(pins, engine="manifold")
holes = trimesh.util.concatenate([dowel_cyl((0,dy,SPLIT_Z-0.4), [0,0,1], 1.25, 3.6) for dy in DOWEL_Y])
front = front.difference(holes, engine="manifold")
print("clip done: front pieces=", len(front.split(only_watertight=False)),
      "back pieces=", len(back.split(only_watertight=False)), time.time()-t0)

front.export("front_shell_monkey.stl")
back.export("back_shell_monkey.stl")
print("exported shells", time.time()-t0)

# ---------------------------------------------------------------------------
# Decorative heart cap -- same as the otter's final version, glued on top of
# the real button afterward, no plunger.
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
heart_scale = 0.72
path2d = trimesh.load_path(np.array(heart_pts_2d(heart_scale) + [heart_pts_2d(heart_scale)[0]]))
heart_cap = path2d.extrude(2.2)
if isinstance(heart_cap, list):
    heart_cap = trimesh.util.concatenate(heart_cap)
heart_cap.export("heart_cap_monkey.stl")
print("ALL DONE", time.time()-t0)

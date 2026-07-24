"""
Shared parameters for the Shield mascot companion toy.
Units: millimetres throughout.

Source of truth: VCX_mascot_component_sheet.pdf + VCX_mascot_toy_concept.pdf
(rev B, 4-window charge bar). Values still marked PLACEHOLDER need a real
part/holder model confirmed against the datasheet before final print.
"""

# ---------------------------------------------------------------------------
# Overall figure size — concept sheet: "~45-55mm tall, 3D-printed".
# Sized to the TOP of that range (not 50mm nominal): a strict 50mm shell
# leaves under 1mm margin around the XIAO + coin-cell holder + button/LED/
# piezo stack in several spots — too tight to reliably print/assemble. This
# lands the finished figure (feet to ear-tuft tip) around 56-58mm.
# ---------------------------------------------------------------------------
BODY_RX      = 18.5    # body half-width (left-right)
BODY_RY      = 14.6    # body half-depth (front-back)
BODY_RZ      = 17.4    # body half-height contribution (torso)
HEAD_RX      = 15.1
HEAD_RY      = 12.9
HEAD_RZ      = 12.3
HEAD_Z_OFFSET = 37.1    # head sphere center height (absolute Z)

WALL = 1.6              # outer shell wall thickness (thinner — small part)

# ---------------------------------------------------------------------------
# Seeed XIAO nRF52840 — component sheet: 21 x 17.8mm, BLE.
# "USB faces battery door" — board is oriented so its USB-C port is
# reachable through the same opening as the CR2032 battery door, for
# reflashing without a second cutout.
# ---------------------------------------------------------------------------
XIAO_L = 21.0
XIAO_W = 17.8
XIAO_T = 4.5             # PLACEHOLDER clearance height incl. USB-C connector
XIAO_CLEARANCE = 0.3
USB_PORT_W = 9.5          # PLACEHOLDER USB-C cutout, only needed if not fully
USB_PORT_H = 3.6           # covered by the battery-door opening

# ---------------------------------------------------------------------------
# CR2032 coin cell + holder — PLACEHOLDER footprint (generic through-hole
# side-entry holder). Confirm exact holder model/dims before final print —
# holder shapes vary a lot (top-load vs side-load vs SMD clip).
# ---------------------------------------------------------------------------
CELL_DIA = 20.0
CELL_T = 3.2
HOLDER_L = 21.5          # PLACEHOLDER — generic compact THT clip holder
HOLDER_W = 21.5           # (e.g. Keystone 3034-class). Confirm real part.
HOLDER_T = 5.6
HOLDER_CLEARANCE = 0.4

# Battery door (back, 2 screws)
DOOR_W = HOLDER_W + 6.0
DOOR_H = HOLDER_L + 6.0
DOOR_SCREW_D = 2.2         # self-tap pilot hole dia, e.g. for M2 or #2 self-tapper
DOOR_SCREW_INSET = 3.0     # screw hole inset from door edge

# ---------------------------------------------------------------------------
# Momentary tummy button — PLACEHOLDER generic tactile switch.
# ---------------------------------------------------------------------------
BUTTON_D = 6.0            # tactile switch body diameter/width
BUTTON_H = 3.5
BUTTON_CAP_D = 4.3         # actuator cap diameter
BUTTON_TRAVEL = 0.6

# ---------------------------------------------------------------------------
# 4x LED charge bar — behind light pipes, front of chest, in a row.
# ---------------------------------------------------------------------------
LED_D = 3.0                # 3mm LED lens diameter (confirm: 3mm vs 5mm LEDs)
LED_PIPE_D = 2.4            # light pipe channel diameter through the shell
LED_COUNT = 4
LED_PITCH = 5.5             # centre-to-centre spacing across the row

# ---------------------------------------------------------------------------
# Piezo buzzer — 12mm, behind sound slits near the bottom front.
# ---------------------------------------------------------------------------
PIEZO_D = 12.0
PIEZO_T = 2.5               # PLACEHOLDER thickness

# ---------------------------------------------------------------------------
# Snap clip / seam (character shell, or core split — depends on architecture)
# ---------------------------------------------------------------------------
SNAP_TAB_W = 3.0
SNAP_TAB_T = 1.1
SNAP_HOOK  = 0.6
DOWEL_D    = 1.8
DOWEL_L    = 2.8

"""Check a LiPo pouch placed under the bottom side against bottom-side parts."""
import pcbnew

BOARD = r"C:\Users\aa095\Desktop\esp32s3-camera\esp32s3-camera.kicad_pcb"
mm = pcbnew.ToMM

# Component height above the board surface (mm), by footprint name fragment
HEIGHTS = [
    ("PinHeader_1x04", 8.5),          # 2.54 plastic + 6 mm pins
    ("JST_PH_B2B", 6.0),
    ("microSD_HC_Hirose_DM3AT", 1.7),
    ("SOIC-8", 1.55),
    ("SOT-23", 1.15),
    ("D_SOD-123", 1.2),
    ("C_0805", 1.3),
    ("C_0603", 0.9),
    ("R_0603", 0.55),
    ("LED_0603", 0.65),
]

BOARD_W, BOARD_H = 60.0, 85.0
ANTENNA_Y = 74.5          # antenna keepout starts here (no copper, keep battery away)
RF_MARGIN = 4.0           # extra distance to keep the pouch from the antenna zone
PAD_T = 2.0               # foam pad thickness under the pouch

# candidate batteries: name, (x_size, y_size, thickness), centre (x, y)
CANDS = [
    ("603040 目前示意 30x40x6 @ (33,42)", (30, 40, 6), (33, 42)),
    ("603040 建議 30x40x6 @ (34,44)", (30, 40, 6), (34, 44)),
    ("803040 30x40x8 @ (34,44)", (30, 40, 8), (34, 44)),
    ("103450 34x50x10 @ (35,45)", (34, 50, 10), (35, 45)),
    ("502535 25x35x5 @ (34,44)", (25, 35, 5), (34, 44)),
]


def height_of(fp):
    name = fp.GetFPIDAsString()
    for frag, h in HEIGHTS:
        if frag in name:
            return h
    return 2.0


b = pcbnew.LoadBoard(BOARD)
bottom = []
for fp in b.Footprints():
    if not fp.IsFlipped():
        continue
    if fp.GetReference().startswith("H"):
        continue
    bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox() if fp.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() else fp.GetBoundingBox(False, False)
    bottom.append((fp.GetReference(), mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom()), height_of(fp)))

print("bottom-side parts (courtyard bbox, est. height):")
for r, x0, y0, x1, y1, h in sorted(bottom, key=lambda t: -t[5]):
    print(f"  {r:4s} x {x0:5.1f}..{x1:5.1f}  y {y0:5.1f}..{y1:5.1f}  h {h:.2f}")

def check(name, size, centre):
    sx, sy, t = size
    cx, cy = centre
    bx0, bx1 = cx - sx / 2, cx + sx / 2
    by0, by1 = cy - sy / 2, cy + sy / 2
    print(f"\n== {name}: pouch x {bx0:.1f}..{bx1:.1f}, y {by0:.1f}..{by1:.1f}, sits {PAD_T} mm off the board")
    ok = True
    if bx0 < 0 or bx1 > BOARD_W or by0 < 0:
        print("  !! exceeds board outline"); ok = False
    if by1 > ANTENNA_Y - RF_MARGIN:
        print(f"  !! too close to antenna zone (y {by1:.1f} > {ANTENNA_Y - RF_MARGIN:.1f})"); ok = False
    for r, x0, y0, x1, y1, h in bottom:
        overlap = not (x1 < bx0 or x0 > bx1 or y1 < by0 or y0 > by1)
        if overlap and h > PAD_T:
            print(f"  !! collides with {r} (h {h:.1f} mm > pad {PAD_T} mm)"); ok = False
    # clearance to the tall parts
    for r, x0, y0, x1, y1, h in bottom:
        if h <= PAD_T:
            continue
        dx = max(x0 - bx1, bx0 - x1, 0)
        dy = max(y0 - by1, by0 - y1, 0)
        d = (dx * dx + dy * dy) ** 0.5
        print(f"  gap to {r:3s} (h {h:.1f}): {d:5.1f} mm")
    stack = max(PAD_T + t, max(h for *_, h in bottom))
    print(f"  bottom stack height: pouch {PAD_T + t:.1f} mm vs tallest part {max(h for *_, h in bottom):.1f} mm -> {stack:.1f} mm")
    print("  RESULT:", "OK" if ok else "NOT OK")

for c in CANDS:
    check(*c)

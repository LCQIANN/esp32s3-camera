"""v1.4 PCB edit with pcbnew: move the SHUTTER button SW3 from the lens face (top-actuated
SKQG at (9, 40)) to a side-actuated ALPS SKRTLAE010 on the top board edge at (50.6, 2.6),
actuator pointing -y through the enclosure's top wall. BOOT/RESET (SW1/SW2) stay.

Steps
 1. remove the old SW3 footprint and the F.Cu branch that fed it (BTN_SHUTTER), plus GND stubs
 2. clear the top-right corner: delete GND stitching vias (51,3) and (54,3); move C12 down 0.8 mm
 3. place the new SW3, pad 1 = BTN_SHUTTER, pad 2 = GND (+ GND via below it)
 4. route BTN_SHUTTER: pad -> via (53.8, 2.0) -> B.Cu along the right edge x = 59.35 -> channel
    y = 65.0 -> joins the existing B.Cu track of the net at (44.5, 62.7) (R8 pull-up side)
 5. silkscreen v1.4, title rev 1.4, zone refill
Run with KiCad's python. Board must not be open in KiCad."""
import os
import pcbnew
from pcbnew import VECTOR2I, FromMM

PROJ = os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera")
BOARD = os.path.join(PROJ, "esp32s3-camera.kicad_pcb")
FPLIB = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
NEW_FP = ("Button_Switch_SMD", "SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010")
LCSC = "C110293"
SW_X, SW_Y, SW_ROT = 50.6, 2.6, 180      # centre; stem tip lands at y = 0.56, body y 1.39..3.95
LANE_X, CHAN_Y, TOP_Y = 59.35, 65.0, 2.0

b = pcbnew.LoadBoard(BOARD)
assert b.GetTitleBlock().GetRevision() == "1.3", "expected v1.3 board"
mm = pcbnew.ToMM
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
F, B = b.GetLayerID("F.Cu"), b.GetLayerID("B.Cu")
FSILK = b.GetLayerID("F.SilkS")
_keep = []          # python refs to removed items (see v13 note about dangling pointers)


def net(name):
    n = b.FindNet(name); assert n is not None, name; return n


def fp_by_ref(ref):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    raise KeyError(ref)


def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError(num)


def track(x1, y1, x2, y2, layer, netname, w=0.2):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(P(x1, y1)); t.SetEnd(P(x2, y2)); t.SetLayer(layer); t.SetWidth(FromMM(w)); t.SetNet(net(netname))
    b.Add(t); return t


def via(x, y, netname):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(x, y)); v.SetDrill(FromMM(0.3))
    try:
        v.SetWidth(pcbnew.PADSTACK.ALL_LAYERS, FromMM(0.6))
    except Exception:
        v.SetWidth(FromMM(0.6))
    v.SetLayerPair(F, B); v.SetNet(net(netname)); b.Add(v); return v


def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return ((round(mm(s.x), 1), round(mm(s.y), 1)), (round(mm(e.x), 1), round(mm(e.y), 1)))


def remove_tracks(netname, segs, expect):
    kill = []
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname:
            k = key(t)
            if k in segs or (k[1], k[0]) in segs:
                kill.append(t)
    for t in kill:
        b.Remove(t); _keep.append(t)
    assert len(kill) == expect, f"{netname}: removed {len(kill)}, expected {expect}"
    return len(kill)


def remove_vias(netname, points):
    kill = []
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_VIA" and t.GetNetname() == netname:
            pos = (round(mm(t.GetPosition().x), 1), round(mm(t.GetPosition().y), 1))
            if pos in points:
                kill.append(t)
    for t in kill:
        b.Remove(t); _keep.append(t)
    assert len(kill) == len(points), f"{netname} vias: removed {len(kill)} of {points}"


def set_rot(fp, deg):
    try:
        fp.SetOrientation(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T))
    except Exception:
        fp.SetOrientationDegrees(deg)


# ------------------------------------------------------------------ 1. old SW3 and its feed
old = fp_by_ref("SW3")
sw3_path = old.GetPath()
gnd_pads = [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in old.Pads() if p.GetNetname() == "GND"]
b.Remove(old); _keep.append(old)
print("old SW3 removed; path", sw3_path.AsString())
branch = {((21.2, 72.5), (20.7, 72.0)), ((20.7, 72.0), (20.2, 72.0)), ((20.2, 72.0), (19.9, 71.7)), ((19.9, 71.7), (19.9, 70.3)),
          ((19.9, 70.3), (13.0, 63.4)), ((13.0, 63.4), (13.0, 51.4)), ((13.0, 51.4), (12.4, 50.8)), ((12.4, 50.8), (12.4, 44.2)),
          ((12.4, 44.2), (10.9, 42.7)), ((10.9, 42.7), (10.9, 42.4)), ((10.9, 42.4), (9.9, 41.4)), ((9.9, 41.4), (9.9, 38.6)),
          ((9.9, 38.6), (10.4, 38.1)), ((10.4, 38.1), (12.1, 38.1)), ((9.9, 38.6), (9.4, 38.1)), ((9.4, 38.1), (5.9, 38.1))}
print("BTN_SHUTTER branch segments removed:", remove_tracks("BTN_SHUTTER", branch, 16))
# GND stubs that ended on the old SW3 GND pads
kill = []
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "GND":
        for (px, py) in gnd_pads:
            for pt in (t.GetStart(), t.GetEnd()):
                if abs(mm(pt.x) - px) < 1.0 and abs(mm(pt.y) - py) < 1.0:
                    kill.append(t); break
            else:
                continue
            break
for t in {id(t): t for t in kill}.values():
    print("  GND stub removed", key(t)); b.Remove(t); _keep.append(t)

# ------------------------------------------------------------------ 2. clear the corner, move C12
remove_vias("GND", {(51.0, 3.0), (54.0, 3.0)})
c12 = fp_by_ref("C12")
remove_tracks("GND", {((47.5, 4.7), (47.5, 3.9))}, 1)
remove_tracks("+3V3", {((47.5, 6.3), (48.3, 6.3))}, 1)
c12.SetPosition(P(47.5, 6.3))
p3, pg = pad(c12, "1"), pad(c12, "2")
assert p3.GetNetname() == "+3V3" and pg.GetNetname() == "GND"
print(f"C12 moved: +3V3 pad @ ({mm(p3.GetPosition().x):.2f},{mm(p3.GetPosition().y):.2f}) GND pad @ ({mm(pg.GetPosition().x):.2f},{mm(pg.GetPosition().y):.2f})")
gx, gy = mm(pg.GetPosition().x), mm(pg.GetPosition().y)
vx, vy = mm(p3.GetPosition().x), mm(p3.GetPosition().y)
track(gx, gy, gx, 3.9, F, "GND", 0.3)                       # to the existing GND via (47.5, 3.9)
track(vx, vy, vx, 6.6, F, "+3V3", 0.3); track(vx, 6.6, 47.8, 6.3, F, "+3V3", 0.3); track(47.8, 6.3, 48.3, 6.3, F, "+3V3", 0.3)

# ------------------------------------------------------------------ 3. new SW3
fp = pcbnew.FootprintLoad(f"{FPLIB}\\{NEW_FP[0]}.pretty", NEW_FP[1]); assert fp, "footprint not found"
fp.SetReference("SW3"); fp.SetValue("SHUTTER")
b.Add(fp)
set_rot(fp, SW_ROT); fp.SetPosition(P(SW_X, SW_Y))
fp.SetPath(sw3_path)
fp.SetFPID(pcbnew.LIB_ID(NEW_FP[0], NEW_FP[1]))
if not fp.HasField("LCSC"):
    fp.SetField("LCSC", LCSC)
for fld in fp.GetFields():
    if fld.GetName() == "LCSC":
        fld.SetText(LCSC); fld.SetVisible(False); fld.SetLayer(pcbnew.F_Fab); fld.SetPosition(fp.GetPosition())
for p in fp.Pads():
    n = p.GetNumber()
    if n == "1": p.SetNet(net("BTN_SHUTTER"))
    elif n == "2": p.SetNet(net("GND"))
    print(f"  SW3.{n or 'MP/NPTH'} @ ({mm(p.GetPosition().x):.3f},{mm(p.GetPosition().y):.3f})")
p2 = pad(fp, "2"); p2x, p2y = mm(p2.GetPosition().x), mm(p2.GetPosition().y)
p1r = max((p for p in fp.Pads() if p.GetNumber() == "1"), key=lambda p: p.GetPosition().x)
p1x, p1y = mm(p1r.GetPosition().x), mm(p1r.GetPosition().y)
assert abs(p2y - 3.5) < 0.01 and p1y > 2.6, "actuator must point to -y (pads on the +y side)"
fp.Reference().SetPosition(P(44.6, 1.4)); fp.Reference().SetTextAngleDegrees(0)
# GND for pad 2: short stub to a new via just below the courtyard
track(p2x, p2y, p2x, 4.6, F, "GND", 0.3); via(p2x, 4.6, "GND")

# ------------------------------------------------------------------ 4. route BTN_SHUTTER
track(p1x, p1y, 53.2, p1y, F, "BTN_SHUTTER"); track(53.2, p1y, 53.8, p1y - 0.6, F, "BTN_SHUTTER")
track(53.8, p1y - 0.6, 53.8, TOP_Y, F, "BTN_SHUTTER"); via(53.8, TOP_Y, "BTN_SHUTTER")
track(53.8, TOP_Y, LANE_X, TOP_Y, B, "BTN_SHUTTER")
track(LANE_X, TOP_Y, LANE_X, CHAN_Y - 0.85, B, "BTN_SHUTTER")
track(LANE_X, CHAN_Y - 0.85, LANE_X - 0.85, CHAN_Y, B, "BTN_SHUTTER")
track(LANE_X - 0.85, CHAN_Y, 45.3, CHAN_Y, B, "BTN_SHUTTER")
track(45.3, CHAN_Y, 44.5, CHAN_Y - 0.8, B, "BTN_SHUTTER")
track(44.5, CHAN_Y - 0.8, 44.5, 62.7, B, "BTN_SHUTTER")        # meets the existing track end (R8 side)

# ------------------------------------------------------------------ 5. silkscreen + version
t = pcbnew.PCB_TEXT(b); t.SetText("SHUTTER"); t.SetPosition(P(44.6, 2.9)); t.SetLayer(FSILK)
t.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); t.SetTextThickness(FromMM(0.12)); b.Add(t)
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and "v1.3" in d.GetText():
        d.SetText(d.GetText().replace("v1.3", "v1.4")); print("silkscreen ->", d.GetText())
tb = b.GetTitleBlock(); tb.SetRevision("1.4"); b.SetTitleBlock(tb)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(BOARD, b)
print("saved", BOARD)

"""v1.2 PCB edit with pcbnew: add SW4 (power slide switch), R21 (EN pull-up),
R20 + D5 (blue power LED); split U2 pin 3 (EN) from VSYS; reconnect the
C1/C2 VSYS branch with a short In2 jumper; silkscreen/title -> v1.2.
Run with KiCad's python. Board must not be open in KiCad."""
import json, os, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = os.path.join(os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera"), "esp32s3-camera.kicad_pcb")
FPLIB = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
UUIDS = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "v12_uuids.json")))

b = pcbnew.LoadBoard(BOARD)
mm = pcbnew.ToMM
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
F, B, IN1, IN2 = (b.GetLayerID(n) for n in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"))

def net(name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    return n

def track(x1, y1, x2, y2, layer, netname, w):
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

def add_fp(lib, name, ref, value, x, y, rot, bottom, sym_uuid):
    fp = pcbnew.FootprintLoad(f"{FPLIB}\\{lib}.pretty", name)
    assert fp, f"footprint {lib}:{name} not found"
    fp.SetReference(ref); fp.SetValue(value)
    b.Add(fp)
    if bottom:
        fp.SetLayerAndFlip(B)
    fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
    fp.SetPath(pcbnew.KIID_PATH(f"/{UUIDS['sheet']}/{sym_uuid}"))
    return fp

def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p
    raise KeyError(num)

def padxy(fp, num):
    p = pad(fp, num).GetPosition(); return mm(p.x), mm(p.y)

def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return ((round(mm(s.x), 1), round(mm(s.y), 1)), (round(mm(e.x), 1), round(mm(e.y), 1)))

# ------------------------------------------------------------------ 1. split EN from VSYS
u2 = b.FindFootprintByReference("U2")
pad(u2, "3").SetNet(net("LDO_EN"))
seg_del = {((50.1, 46.2), (50.5, 46.2)), ((51.1, 46.0), (51.2, 45.9)), ((51.2, 45.9), (51.3, 45.9)),
           ((51.3, 45.9), (51.4, 45.8)), ((51.4, 45.8), (53.2, 45.8)), ((53.2, 45.8), (53.6, 45.4)),
           ((53.6, 45.4), (53.6, 44.6)), ((53.6, 44.6), (53.2, 44.2)), ((53.2, 44.2), (51.7, 44.2)),
           ((47.9, 46.2), (50.1, 46.2))}                      # F.Cu stub into the old via
via_del = {("VSYS", (50.1, 46.2)), ("GND", (53.5, 42.7))}     # old branch via; stitching via in R21's way
kill = []
for t in list(b.GetTracks()):   # single pass: iterating after Remove() breaks in SWIG
    if t.GetClass() == "PCB_TRACK" and t.GetNetname() == "VSYS":
        k = key(t)
        if k in seg_del or (k[1], k[0]) in seg_del:
            kill.append(("seg", t))
    elif t.GetClass() == "PCB_VIA":
        pos = (round(mm(t.GetPosition().x), 1), round(mm(t.GetPosition().y), 1))
        if (t.GetNetname(), pos) in via_del:
            kill.append(("via", t))
for _, t in kill:
    b.Remove(t)
nseg = sum(1 for k, _ in kill if k == "seg"); nvia = sum(1 for k, _ in kill if k == "via")
print(f"removed: {nseg} VSYS segments, {nvia} vias")
assert nseg == 10 and nvia == 2

# re-attach the C1/C2 VSYS branch: new via clear of U2 pad 3, In2 jumper to a via on the VSYS trunk
track(47.9, 46.2, 49.3, 46.2, F, "VSYS", 0.6)
track(49.3, 46.2, 49.6, 46.5, F, "VSYS", 0.6)
track(49.6, 46.5, 49.6, 46.9, F, "VSYS", 0.6)
via(49.6, 46.9, "VSYS")
track(49.6, 46.9, 50.7, 45.6, IN2, "VSYS", 0.35)
track(50.7, 45.6, 50.9, 43.45, IN2, "VSYS", 0.35)
via(50.9, 43.45, "VSYS")

# ------------------------------------------------------------------ 2. new footprints
sw4 = add_fp("Button_Switch_SMD", "SW_SPDT_Shouhan_MSK12C02", "SW4", "PWR", 57.6, 11.0, 90, False, UUIDS["symbols"]["SW4"])
r21 = add_fp("Resistor_SMD", "R_0603_1608Metric", "R21", "100k", 53.2, 41.7, 90, True, UUIDS["symbols"]["R21"])
r20 = add_fp("Resistor_SMD", "R_0603_1608Metric", "R20", "1k", 53.0, 8.2, 0, False, UUIDS["symbols"]["R20"])
d5 = add_fp("LED_SMD", "LED_0603_1608Metric", "D5", "BLUE", 53.0, 11.2, 0, False, UUIDS["symbols"]["D5"])
# reference text positions (keep silkscreen off pads / other refs)
sw4.Reference().SetPosition(P(57.6, 16.6)); sw4.Reference().SetTextAngleDegrees(0)
r21.Reference().SetPosition(P(51.9, 41.7))
d5.Reference().SetPosition(P(53.0, 13.1))
r20.Reference().SetPosition(P(53.0, 6.6))
for fp in (sw4, r21, r20, d5):
    for p in fp.Pads():
        print(f"  {fp.GetReference()}.{p.GetNumber()} @ ({mm(p.GetPosition().x):.2f},{mm(p.GetPosition().y):.2f}) {'B' if fp.IsFlipped() else 'F'}")

pad(sw4, "2").SetNet(net("LDO_EN")); pad(sw4, "3").SetNet(net("GND"))
pad(r20, "1").SetNet(net("+3V3")); pad(r20, "2").SetNet(net("LEDA_PWR"))
pad(d5, "1").SetNet(net("GND")); pad(d5, "2").SetNet(net("LEDA_PWR"))
# R21: whichever pad ends up on top (smaller y) is VSYS, the lower one is LDO_EN
(rxa, rya), (rxb, ryb) = padxy(r21, "1"), padxy(r21, "2")
if rya < ryb:
    pad(r21, "1").SetNet(net("VSYS")); pad(r21, "2").SetNet(net("LDO_EN")); top, bot = (rxa, rya), (rxb, ryb)
else:
    pad(r21, "2").SetNet(net("VSYS")); pad(r21, "1").SetNet(net("LDO_EN")); top, bot = (rxb, ryb), (rxa, rya)

# ------------------------------------------------------------------ 3. routing
# SW4 pad 3 -> GND via above it
x, y = padxy(sw4, "3"); track(x, y, x, 7.3, F, "GND", 0.3); via(x, 7.3, "GND")
# SW4 pad 2 (common) -> LDO_EN: west, down past the switch, east to the edge strip, south, then in between J5 pads 2/3
x, y = padxy(sw4, "2")
track(x, y, 54.7, y, F, "LDO_EN", 0.2)
track(54.7, y, 54.7, 15.8, F, "LDO_EN", 0.2)
track(54.7, 15.8, 58.6, 15.8, F, "LDO_EN", 0.2)
track(58.6, 15.8, 58.6, 43.81, F, "LDO_EN", 0.2)
track(58.6, 43.81, 54.5, 43.81, F, "LDO_EN", 0.2)
via(54.5, 43.81, "LDO_EN")
# B.Cu: via -> R21 (EN pad) -> U2 pad 3 ; R21 VSYS pad -> trunk
track(54.5, 43.81, 53.2, 43.81, B, "LDO_EN", 0.2)
track(bot[0], bot[1], bot[0], 43.81, B, "LDO_EN", 0.2)
track(top[0], top[1], top[0], 40.6, B, "VSYS", 0.3)
track(top[0], 40.6, 51.2, 40.6, B, "VSYS", 0.3)
track(53.4, 43.81, 53.4, 46.6, B, "LDO_EN", 0.2)
track(53.4, 46.6, 51.9, 46.6, B, "LDO_EN", 0.2)
ux, uy = padxy(u2, "3")
track(51.9, 46.6, 51.5, 46.2, B, "LDO_EN", 0.2)
track(51.5, 46.2, ux, uy, B, "LDO_EN", 0.2)
# power LED: R20 -> +3V3 via ; R20 -> D5 anode ; D5 cathode -> GND via
(x1, y1), (x2, y2) = padxy(r20, "1"), padxy(r20, "2")
if x1 > x2:
    pad(r20, "1").SetNet(net("LEDA_PWR")); pad(r20, "2").SetNet(net("+3V3")); (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
track(x1, y1, x1, 6.9, F, "+3V3", 0.3); via(x1, 6.9, "+3V3")
(kx, ky), (ax, ay) = padxy(d5, "1"), padxy(d5, "2")
if kx > ax:   # keep cathode on the left (pad 1 of LED_0603 is K)
    pad(d5, "1").SetNet(net("LEDA_PWR")); pad(d5, "2").SetNet(net("GND")); (kx, ky), (ax, ay) = (ax, ay), (kx, ky)
track(x2, y2, ax, ay, F, "LEDA_PWR", 0.2)
track(kx, ky, kx, 12.6, F, "GND", 0.3); via(kx, 12.6, "GND")

# ------------------------------------------------------------------ 4. version text
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and "v1.1" in d.GetText():
        d.SetText(d.GetText().replace("v1.1", "v1.2")); print("silkscreen ->", d.GetText())
tb = b.GetTitleBlock(); tb.SetRevision("1.2"); b.SetTitleBlock(tb)

# ------------------------------------------------------------------ 5. zones + save
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(BOARD, b)
print("saved", BOARD)

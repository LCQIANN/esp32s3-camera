"""v1.3 PCB edit with pcbnew: drop the 1x4 headers J5/J6, add a 1x7 female
socket J5 on the bottom side at the right board edge so the 1.3" ST7789
module plugs straight in (screen facing out, module body over the battery).
Re-terminate the seven nets, add pin labels, bump silkscreen/title to v1.3.
Run with KiCad's python. Board must not be open in KiCad."""
import json, os, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM

PROJ = os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera")
BOARD = os.path.join(PROJ, "esp32s3-camera.kicad_pcb")
FPLIB = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
UUIDS = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "v13_uuids.json")))

b = pcbnew.LoadBoard(BOARD)
assert b.GetTitleBlock().GetRevision() == "1.2", "expected v1.2 board"
mm = pcbnew.ToMM
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
F, B, IN1, IN2 = (b.GetLayerID(n) for n in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"))
BSILK, BFAB = b.GetLayerID("B.SilkS"), b.GetLayerID("B.Fab")


def net(name):
    n = b.FindNet(name)
    assert n is not None, name
    return n


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


def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return ((round(mm(s.x), 2), round(mm(s.y), 2)), (round(mm(e.x), 2), round(mm(e.y), 2)))


def set_rot(fp, deg):
    try:
        fp.SetOrientation(pcbnew.EDA_ANGLE(deg, pcbnew.DEGREES_T))
    except Exception:
        fp.SetOrientationDegrees(deg)


# ------------------------------------------------------------------ 1. remove J5, J6
# keep python references alive: letting the removed footprint be garbage-collected mid-script
# leaves a dangling pointer in the board list (SwigPyObject without GetReference)
_removed = [fp_by_ref("J5"), fp_by_ref("J6")]
for old in _removed:
    b.Remove(old)
print("J5, J6 removed")

# ------------------------------------------------------------------ 2. cut the old tails
seg_del = {
    "IO4": {((51.6, 60.9), (56.0, 56.5))},
    "IO5": {((57.1, 62.8), (57.1, 60.5)), ((57.1, 60.5), (56.9, 60.3)), ((56.9, 60.3), (56.9, 60.0)), ((56.9, 60.0), (56.0, 59.1))},
    "UART_RX": {((48.5, 47.6), (56.0, 47.6))},
    "UART_TX": {((54.2, 46.9), (56.0, 45.1))},
}
kill = []
for t in list(b.GetTracks()):
    if t.GetClass() == "PCB_TRACK" and t.GetNetname() in seg_del:
        k = key(t)
        if k in seg_del[t.GetNetname()] or (k[1], k[0]) in seg_del[t.GetNetname()]:
            kill.append(t)
for t in kill:
    b.Remove(t)
print(f"removed {len(kill)} old tail segments")
assert len(kill) == 7

# ------------------------------------------------------------------ 3. new socket
fp = pcbnew.FootprintLoad(f"{FPLIB}\\Connector_PinSocket_2.54mm.pretty", "PinSocket_1x07_P2.54mm_Vertical")
assert fp, "PinSocket_1x07 footprint not found"
fp.SetReference("J5"); fp.SetValue("DISPLAY 1.3in ST7789")
b.Add(fp)
fp.SetLayerAndFlip(B)
# pin 1 (GND) at y = 52.62, pin 7 (BLK) at y = 37.38: the module's header row is 2.5 mm from its top
# edge, first pin 6.27 mm from its left edge; with the header edge facing +x and the screen facing
# out from the bottom, pin 1 ends up toward the antenna end (larger y).
PIN_X, PIN1_Y = 56.0, 52.62
NETS = ["GND", "+3V3", "UART_RX", "UART_TX", "IO6", "IO5", "IO4"]    # pins 1..7 = GND VCC SCL SDA RES DC BLK
for rot in (180, 0, 90, 270):
    set_rot(fp, rot)
    fp.SetPosition(P(PIN_X, PIN1_Y))
    p7 = pad(fp, "7").GetPosition()
    if abs(mm(p7.x) - PIN_X) < 0.01 and abs(mm(p7.y) - (PIN1_Y - 6 * 2.54)) < 0.01:
        break
else:
    raise SystemExit("could not orient socket")
fp.SetPath(pcbnew.KIID_PATH(f"/{UUIDS['sheet']}/{UUIDS['symbols']['J5']}"))
# hidden LCSC field like the other footprints (schematic parity compares fields)
try:
    fld = fp.GetFieldByName("LCSC")
    if fld is None:
        fld = pcbnew.PCB_FIELD(fp, fp.GetFieldCount(), "LCSC")
        fp.AddField(fld)
    fld.SetText("C225482"); fld.SetLayer(BFAB); fld.SetVisible(False)
except Exception as e:
    print("LCSC field:", e)
pin_pos = {}
for n, netname in enumerate(NETS, start=1):
    p = pad(fp, str(n)); p.SetNet(net(netname))
    pin_pos[n] = (round(mm(p.GetPosition().x), 2), round(mm(p.GetPosition().y), 2))
    print(f"  J5.{n} {netname:8s} @ {pin_pos[n]}")
assert pin_pos[1] == (56.0, 52.62) and pin_pos[7] == (56.0, 37.38)
fp.Reference().SetPosition(P(56.0, 34.9)); fp.Reference().SetTextAngleDegrees(0)
fp.Reference().SetLayer(BSILK); fp.Reference().SetMirrored(True)
fp.Value().SetPosition(P(56.0, 55.6))

# ------------------------------------------------------------------ 4. routing
y = {n: pin_pos[n][1] for n in pin_pos}
# pin 3 SCL = UART_RX (GPIO44): old F.Cu run along y 47.6 now ends on pad 3 (y 47.54)
track(48.5, 47.6, 55.94, 47.6, F, "UART_RX"); track(55.94, 47.6, 56.0, y[3], F, "UART_RX")
# pin 4 SDA = UART_TX (GPIO43): old 45-degree approach, 0.1 mm shorter
track(54.2, 46.9, 56.0, 45.1, F, "UART_TX"); track(56.0, 45.1, 56.0, y[4], F, "UART_TX")
# pins 5/6/7 RES/DC/BLK = IO6/IO5/IO4: three B.Cu lanes along the right edge (x 57.4 / 58.05 / 58.7),
# entered from the south in order so nothing crosses; each turns west into its pad.
track(56.0, 61.6, 57.4, 61.6, F, "IO6"); via(57.4, 61.6, "IO6")
track(57.4, 61.6, 57.4, y[5], B, "IO6"); track(57.4, y[5], 56.0, y[5], B, "IO6")
track(57.1, 62.8, 58.05, 62.8, F, "IO5"); via(58.05, 62.8, "IO5")
track(58.05, 62.8, 58.05, y[6], B, "IO5"); track(58.05, y[6], 56.0, y[6], B, "IO5")
track(51.6, 60.9, 53.6, 58.9, F, "IO4"); track(53.6, 58.9, 58.7, 58.9, F, "IO4"); via(58.7, 58.9, "IO4")
track(58.7, 58.9, 58.7, y[7], B, "IO4"); track(58.7, y[7], 56.0, y[7], B, "IO4")
# pins 1/2 GND/+3V3 are through-hole: they reach the In1 GND / In2 +3V3 planes directly.

# ------------------------------------------------------------------ 5. silkscreen + fab notes
def btext(s, x, y, size=0.6, layer=None, thick=0.1, angle=0):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer or BSILK)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(thick))
    t.SetMirrored(True); t.SetTextAngleDegrees(angle)
    b.Add(t); return t


for n, lbl in enumerate(["GND", "3V3", "SCL", "SDA", "RES", "DC", "BLK"], start=1):
    btext(lbl, 58.4, y[n])
btext("DISPLAY", 56.0, 55.9, 0.7, thick=0.12)
# module footprint on B.Fab: 27.78 x 39.22, header row 2.5 mm from its +x edge, centred on the socket
cx, cy = 58.5 - 39.22 / 2, (y[1] + y[7]) / 2
rect = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_RECT)
rect.SetStart(P(cx - 39.22 / 2, cy - 27.78 / 2)); rect.SetEnd(P(cx + 39.22 / 2, cy + 27.78 / 2))
rect.SetLayer(BFAB); rect.SetWidth(FromMM(0.1)); b.Add(rect)
btext("1.3in ST7789 module 27.78 x 39.22, plugs into J5", cx, cy, 1.0, layer=BFAB, thick=0.12)
print(f"display module footprint: x {cx - 39.22/2:.1f}..{cx + 39.22/2:.1f}  y {cy - 27.78/2:.1f}..{cy + 27.78/2:.1f}")

# ------------------------------------------------------------------ 6. version text
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and "v1.2" in d.GetText():
        d.SetText(d.GetText().replace("v1.2", "v1.3")); print("silkscreen ->", d.GetText())
tb = b.GetTitleBlock(); tb.SetRevision("1.3"); b.SetTitleBlock(tb)

# ------------------------------------------------------------------ 7. zones + save
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(BOARD, b)
print("saved", BOARD)

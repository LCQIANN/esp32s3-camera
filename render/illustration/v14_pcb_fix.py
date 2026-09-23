"""v1.4 follow-up: reroute BTN_SHUTTER under the ESP32 module (y = 73.3) instead of the blocked
y = 65 channel, shift the IPROG diagonal off C12, swap SW3 to the project-library copy with
narrowed pads, tidy silkscreen."""
import pcbnew
from pcbnew import VECTOR2I, FromMM
BOARD = r"C:\Users\aa095\Desktop\esp32s3-camera\esp32s3-camera.kicad_pcb"
b = pcbnew.LoadBoard(BOARD); mm = pcbnew.ToMM
def P(x, y): return VECTOR2I(FromMM(x), FromMM(y))
F, B = b.GetLayerID("F.Cu"), b.GetLayerID("B.Cu"); _keep = []
def net(n): x = b.FindNet(n); assert x is not None, n; return x
def key(t): s, e = t.GetStart(), t.GetEnd(); return ((round(mm(s.x), 2), round(mm(s.y), 2)), (round(mm(e.x), 2), round(mm(e.y), 2)))
def track(x1, y1, x2, y2, layer, n, w=0.2):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(x1, y1)); t.SetEnd(P(x2, y2)); t.SetLayer(layer); t.SetWidth(FromMM(w)); t.SetNet(net(n)); b.Add(t)
def via(x, y, n):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetDrill(FromMM(0.3))
    try: v.SetWidth(pcbnew.PADSTACK.ALL_LAYERS, FromMM(0.6))
    except Exception: v.SetWidth(FromMM(0.6))
    v.SetLayerPair(F, B); v.SetNet(net(n)); b.Add(v)
def remove(n, segs=(), vias=()):
    kill = []
    for t in list(b.GetTracks()):
        if t.GetNetname() != n: continue
        if t.GetClass() == "PCB_VIA":
            if (round(mm(t.GetPosition().x), 2), round(mm(t.GetPosition().y), 2)) in vias: kill.append(t)
        else:
            k = key(t)
            if k in segs or (k[1], k[0]) in segs: kill.append(t)
    for t in kill: b.Remove(t); _keep.append(t)
    assert len(kill) == len(segs) + len(vias), (n, len(kill), len(segs) + len(vias))
# 1 wrong channel out, module-underside route in
remove("BTN_SHUTTER", segs={((59.35, 2.0), (59.35, 64.15)), ((59.35, 64.15), (58.5, 65.0)), ((58.5, 65.0), (45.3, 65.0)),
                            ((45.3, 65.0), (44.5, 64.2)), ((44.5, 64.2), (44.5, 62.7))})
remove("GND", vias={(40.0, 73.8)})
u1 = [f for f in b.GetFootprints() if f.GetReference() == "U1"][0]
p39 = [p for p in u1.Pads() if p.GetNumber() == "39"][0]; px, py = mm(p39.GetPosition().x), mm(p39.GetPosition().y)
assert p39.GetNetname() == "BTN_SHUTTER"
track(px, py, 19.4, py, F, "BTN_SHUTTER"); via(19.4, py, "BTN_SHUTTER")
track(19.4, py, 19.4, 72.5, B, "BTN_SHUTTER"); track(19.4, 72.5, 20.2, 73.3, B, "BTN_SHUTTER")
track(20.2, 73.3, 58.5, 73.3, B, "BTN_SHUTTER"); track(58.5, 73.3, 59.35, 72.45, B, "BTN_SHUTTER")
track(59.35, 72.45, 59.35, 2.0, B, "BTN_SHUTTER")
# 2 IPROG diagonal 0.5 mm further from C12
remove("IPROG", segs={((44.6, 6.7), (46.0, 6.7)), ((46.0, 6.7), (47.7, 8.4))})
track(44.6, 6.7, 45.5, 6.7, F, "IPROG"); track(45.5, 6.7, 47.2, 8.4, F, "IPROG"); track(47.2, 8.4, 47.7, 8.4, F, "IPROG")
# 3 SW3 -> project-library copy with narrowed pads (same position, nets, path)
old = [f for f in b.GetFootprints() if f.GetReference() == "SW3"][0]
pos, rot, path = old.GetPosition(), old.GetOrientation(), old.GetPath()
b.Remove(old); _keep.append(old)
fp = pcbnew.FootprintLoad(r"C:\Users\aa095\Desktop\esp32s3-camera\esp32s3-camera.pretty", "SW_Push_SKRTLAE010_Side"); assert fp
fp.SetReference("SW3"); fp.SetValue("SHUTTER"); b.Add(fp); fp.SetOrientation(rot); fp.SetPosition(pos); fp.SetPath(path)
fp.SetFPID(pcbnew.LIB_ID("esp32s3-camera", "SW_Push_SKRTLAE010_Side"))
fp.SetField("LCSC", "C110293")
for fld in fp.GetFields():
    if fld.GetName() == "LCSC": fld.SetVisible(False); fld.SetLayer(pcbnew.F_Fab); fld.SetPosition(pos)
for p in fp.Pads():
    if p.GetNumber() == "1": p.SetNet(net("BTN_SHUTTER"))
    elif p.GetNumber() == "2": p.SetNet(net("GND"))
    print("  SW3", p.GetNumber() or "MP/NPTH", round(mm(p.GetPosition().x), 3), round(mm(p.GetPosition().y), 3), "size", round(mm(p.GetSize().x), 2))
fp.Reference().SetPosition(P(50.6, 5.4)); fp.Reference().SetTextAngleDegrees(0)
# 4 silkscreen tidy
for f in b.GetFootprints():
    if f.GetReference() == "C12": f.Reference().SetPosition(P(49.8, 7.6))
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetText() == "SHUTTER": d.SetPosition(P(44.6, 1.4))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(BOARD, b); print("saved")

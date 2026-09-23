"""v1.4 follow-up 2: start the shutter route below the VBAT diagonal, drop the GND stitching via in
its way, route IPROG around the GND via, bridge the two pad-1 halves of SW3, GND via for pad 2 on the
edge side."""
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
remove("BTN_SHUTTER", segs={((19.4, 72.49), (19.4, 72.5)), ((19.4, 72.5), (20.2, 73.3)), ((20.2, 73.3), (58.5, 73.3)),
                            ((58.5, 73.3), (59.35, 72.45)), ((59.35, 72.45), (59.35, 2.0)), ((21.25, 72.49), (19.4, 72.49)),
                            ((50.6, 3.5), (50.6, 4.6)) if False else ((21.25, 72.49), (19.4, 72.49))} - {((21.25, 72.49), (19.4, 72.49))} | {((21.25, 72.49), (19.4, 72.49))},
       vias={(19.4, 72.49)})
remove("GND", segs={((50.6, 3.5), (50.6, 4.6))}, vias={(22.4, 73.8), (50.6, 4.6)})
# shutter: pad 39 -> west/down-left stub -> via below the VBAT diagonal -> B.Cu y 73.4 -> right edge lane
track(21.25, 72.49, 20.0, 72.49, F, "BTN_SHUTTER"); track(20.0, 72.49, 19.4, 73.09, F, "BTN_SHUTTER"); track(19.4, 73.09, 19.4, 73.4, F, "BTN_SHUTTER")
via(19.4, 73.4, "BTN_SHUTTER")
track(19.4, 73.4, 58.5, 73.4, B, "BTN_SHUTTER"); track(58.5, 73.4, 59.35, 72.55, B, "BTN_SHUTTER"); track(59.35, 72.55, 59.35, 2.0, B, "BTN_SHUTTER")
# IPROG around the GND via (45.7, 7.3) and clear of C12
remove("IPROG", segs={((44.6, 6.7), (45.5, 6.7)), ((45.5, 6.7), (47.2, 8.4)), ((47.2, 8.4), (47.7, 8.4))})
track(44.6, 6.7, 46.5, 6.7, F, "IPROG"); track(46.5, 6.7, 46.5, 7.7, F, "IPROG"); track(46.5, 7.7, 47.2, 8.4, F, "IPROG"); track(47.2, 8.4, 47.7, 8.4, F, "IPROG")
# SW3: bridge the two pad-1 halves below pad 2; GND for pad 2 through a via on the edge side
track(49.375, 3.5, 49.375, 4.9, F, "BTN_SHUTTER"); track(49.375, 4.9, 51.825, 4.9, F, "BTN_SHUTTER"); track(51.825, 4.9, 51.825, 3.5, F, "BTN_SHUTTER")
track(50.6, 3.5, 50.6, 1.3, F, "GND", 0.3); via(50.6, 1.3, "GND")
for f in b.GetFootprints():
    if f.GetReference() == "SW3": f.Reference().SetPosition(P(50.6, 5.7))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(BOARD, b); print("saved")

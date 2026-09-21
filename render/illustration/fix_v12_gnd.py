"""v1.2 fix, run in steps:  python fix_v12.py <board> <step>
step A: GND via+track for C3.2, IPROG reroute + GND via for J2.23
step B: rotate R21 180 deg and align pad nets with schematic; fix FPID lib nicknames
step C: refill zones
Each step loads the board, applies, saves."""
import sys
import pcbnew

src, step = sys.argv[1], sys.argv[2].upper()
board = pcbnew.LoadBoard(src)
FromMM = pcbnew.FromMM

def P(x, y):
    return pcbnew.VECTOR2I(FromMM(x), FromMM(y))

def net(name):
    n = board.FindNet(name)
    assert n is not None, name
    return n

def log(*a):
    print(*a, flush=True)

if step == "A":
    GND, IPROG = net("GND"), net("IPROG")
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    def find_track(netname, layer, a, b, tol=0.02):
        for t in board.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetNetname() != netname or t.GetLayer() != layer:
                continue
            s, e = t.GetStart(), t.GetEnd()
            for (p, q) in ((s, e), (e, s)):
                if abs(pcbnew.ToMM(p.x) - a[0]) < tol and abs(pcbnew.ToMM(p.y) - a[1]) < tol and \
                   abs(pcbnew.ToMM(q.x) - b[0]) < tol and abs(pcbnew.ToMM(q.y) - b[1]) < tol:
                    return t
        raise RuntimeError(f"track {netname} {a}->{b} not found")

    def add_track(n, layer, a, b, w):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNetCode(n.GetNetCode())
        board.Add(t)

    def add_via(n, x, y, dia=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(x, y))
        v.SetWidth(FromMM(dia))
        v.SetDrill(FromMM(drill))
        v.SetNetCode(n.GetNetCode())
        board.Add(v)

    # --- IPROG reroute: edit existing segments in place, add two new ones
    t1 = find_track("IPROG", F, (33.5, 3.0), (35.5, 3.0))
    t1.SetStart(P(33.5, 3.0)); t1.SetEnd(P(34.4, 3.0))
    t2 = find_track("IPROG", F, (35.5, 3.0), (36.7, 4.2))
    t2.SetStart(P(35.9, 2.85)); t2.SetEnd(P(37.25, 4.2))
    t3 = find_track("IPROG", F, (36.7, 4.2), (40.9, 4.2))
    t3.SetStart(P(37.25, 4.2)); t3.SetEnd(P(40.9, 4.2))
    add_track(IPROG, F, (34.4, 3.0), (34.55, 2.85), 0.2)
    add_track(IPROG, F, (34.55, 2.85), (35.9, 2.85), 0.2)
    log("IPROG rerouted")

    # --- J2.23
    add_via(GND, 35.55, 3.45)
    add_track(GND, F, (35.25, 4.65), (35.25, 3.95), 0.2)
    add_track(GND, F, (35.25, 3.95), (35.55, 3.45), 0.2)
    log("J2.23: via (35.55, 3.45) + tracks")

    # --- C3.2
    add_via(GND, 43.05, 53.05)
    add_track(GND, B, (43.05, 52.00), (43.05, 53.05), 0.3)
    log("C3.2: via (43.05, 53.05) + track")

elif step == "B":
    VSYS, LDO_EN = net("VSYS"), net("LDO_EN")
    fps = {}
    for f in board.GetFootprints():
        fps[f.GetReference()] = f
    r21 = fps["R21"]
    ang = r21.GetOrientation()
    r21.SetOrientation(pcbnew.EDA_ANGLE(ang.AsDegrees() + 180, pcbnew.DEGREES_T))
    for pad in list(r21.Pads()):
        pad.SetNetCode(VSYS.GetNetCode() if pad.GetNumber() == "1" else LDO_EN.GetNetCode())
    log("R21 rotated to", r21.GetOrientationDegrees(), "deg; pads:",
        [(p.GetNumber(), p.GetNetname(), round(pcbnew.ToMM(p.GetPosition().y), 3)) for p in r21.Pads()])
    for ref, lib in (("D5", "LED_SMD"), ("R20", "Resistor_SMD"), ("R21", "Resistor_SMD"), ("SW4", "Button_Switch_SMD")):
        fp = fps[ref]
        fpid = fp.GetFPID()
        if str(fpid.GetLibNickname()) == "":
            fp.SetFPID(pcbnew.LIB_ID(lib, str(fpid.GetLibItemName())))
            log(f"{ref}: FPID -> {fp.GetFPID().GetUniStringLibId()}")

elif step == "D":
    # relocate the two GND vias away from B.Cu tracks missed in step A; restore R21 ref text
    GND, IPROG = net("GND"), net("IPROG")
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    def near(p, x, y, tol=0.02):
        return abs(pcbnew.ToMM(p.x) - x) < tol and abs(pcbnew.ToMM(p.y) - y) < tol

    def add_track(n, layer, a, b, w):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(*a)); t.SetEnd(P(*b)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNetCode(n.GetNetCode())
        board.Add(t)

    tracks = [t for t in board.GetTracks()]
    for t in tracks:
        cls, nm = t.GetClass(), t.GetNetname()
        if cls == "PCB_VIA" and nm == "GND" and (near(t.GetPosition(), 35.55, 3.45) or near(t.GetPosition(), 43.05, 53.05)):
            board.Remove(t); log("removed via", pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y))
        elif cls == "PCB_TRACK" and nm == "GND" and t.GetLayer() == F and near(t.GetStart(), 35.25, 3.95) and near(t.GetEnd(), 35.55, 3.45):
            board.Remove(t); log("removed GND track to old via (J2.23)")
        elif cls == "PCB_TRACK" and nm == "GND" and t.GetLayer() == B and near(t.GetStart(), 43.05, 52.0) and near(t.GetEnd(), 43.05, 53.05):
            board.Remove(t); log("removed GND track to old via (C3.2)")
        elif cls == "PCB_TRACK" and nm == "IPROG" and t.GetLayer() == F and near(t.GetStart(), 34.55, 2.85) and near(t.GetEnd(), 35.9, 2.85):
            t.SetEnd(P(38.3, 2.85)); log("IPROG horizontal extended to x=38.3")
        elif cls == "PCB_TRACK" and nm == "IPROG" and t.GetLayer() == F and near(t.GetStart(), 35.9, 2.85) and near(t.GetEnd(), 37.25, 4.2):
            t.SetStart(P(38.3, 2.85)); t.SetEnd(P(39.65, 4.2)); log("IPROG diagonal moved to (38.3,2.85)-(39.65,4.2)")
        elif cls == "PCB_TRACK" and nm == "IPROG" and t.GetLayer() == F and near(t.GetStart(), 37.25, 4.2) and near(t.GetEnd(), 40.9, 4.2):
            t.SetStart(P(39.65, 4.2)); log("IPROG tail starts at x=39.65")

    def add_via(n, x, y, dia=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(x, y)); v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(drill)); v.SetNetCode(n.GetNetCode())
        board.Add(v)

    add_via(GND, 37.0, 3.45)
    add_track(GND, F, (35.25, 3.95), (35.7, 3.5), 0.2)
    add_track(GND, F, (35.7, 3.5), (37.0, 3.45), 0.2)
    log("J2.23: new via (37.0, 3.45)")
    add_via(GND, 42.8, 53.0)
    add_track(GND, B, (43.05, 52.0), (42.8, 53.0), 0.3)
    log("C3.2: new via (42.8, 53.0)")

    for f in board.GetFootprints():
        if f.GetReference() == "R21":
            ref = f.Reference()
            ref.SetPosition(P(51.9, 41.7))
            ref.SetTextAngle(pcbnew.EDA_ANGLE(270, pcbnew.DEGREES_T))
            log("R21 ref text moved to (51.9, 41.7)")

elif step == "E":
    # add hidden LCSC field to every footprint (from netlist.net) so schematic parity is clean; move C9 ref label
    import re, os
    netlist = open(os.path.join(os.path.dirname(src), "netlist.net"), encoding="utf-8").read()
    lcsc = {}
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)\n\t\t\)', netlist, re.S):
        ref, body = m.group(1), m.group(2)
        f = re.search(r'\(field\s+\(name "LCSC"\)\s+"([^"]*)"\)', body)
        if f:
            lcsc[ref] = f.group(1)
    log("LCSC values found in netlist:", len(lcsc))
    added = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in lcsc or fp.HasField("LCSC"):
            continue
        fp.SetField("LCSC", lcsc[ref])
        for fld in fp.GetFields():
            if fld.GetName() == "LCSC":
                fld.SetVisible(False)
                fld.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
                fld.SetPosition(fp.GetPosition())
        added += 1
    log("LCSC fields added:", added)
    for fp in board.GetFootprints():
        if fp.GetReference() == "C9":
            fp.Reference().SetPosition(P(24.0, 14.43))
            log("C9 ref moved below the part")

elif step == "F":
    name = "unconnected-(SW4-A-Pad1)"
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        log("net created:", name)
    for fp in board.GetFootprints():
        if fp.GetReference() == "SW4":
            for pad in fp.Pads():
                if pad.GetNumber() == "1":
                    pad.SetNetCode(n.GetNetCode())
                    log("SW4 pad 1 ->", pad.GetNetname())

elif step == "C":
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    log("zones refilled")

else:
    raise SystemExit("unknown step")

pcbnew.SaveBoard(src, board)
log("saved", src, "after step", step)

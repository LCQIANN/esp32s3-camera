"""Geometric connectivity check for one net: which pads are NOT reachable from the In1 plane."""
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
NET = sys.argv[2] if len(sys.argv) > 2 else "GND"
netcode = board.GetNetcodeFromNetname(NET)
mm = pcbnew.ToMM
MAXERR = pcbnew.FromMM(0.005)
LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LNAME = {l: board.GetLayerName(l) for l in LAYERS}

def shape_poly(item, layer):
    p = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(p, layer, 0, MAXERR, pcbnew.ERROR_INSIDE)
    return p

def intersects(a, b):
    t = pcbnew.SHAPE_POLY_SET(a)
    t.BooleanIntersection(b)
    return t.OutlineCount() > 0

# ---- collect nodes
parent = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
def add(x):
    parent.setdefault(x, x)

islands = []   # (key, layer, polyset(single unit), area)
zones = [z for z in board.Zones() if z.GetNetCode() == netcode]
for zi, z in enumerate(zones):
    for L in LAYERS:
        if not z.IsOnLayer(L):
            continue
        polys = z.GetFilledPolysList(L)
        for i in range(polys.OutlineCount()):
            unit = polys.UnitSet(i)
            key = ("island", zi, LNAME[L], i)
            add(key)
            islands.append((key, L, unit, unit.Area() / 1e12))

vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == netcode]
tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetCode() == netcode]
pads = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetCode() == netcode]
vkeys = {id(v): ("via", i) for i, v in enumerate(vias)}
tkeys = {id(t): ("trk", i) for i, t in enumerate(tracks)}
pkeys = {id(p): ("pad", p.GetParentFootprint().GetReference() + "." + p.GetNumber()) for p in pads}
for k in list(vkeys.values()) + list(tkeys.values()) + list(pkeys.values()):
    add(k)

# ---- edges
# via <-> island (any copper layer the via spans)
for v in vias:
    for key, L, unit, _ in islands:
        if v.IsOnLayer(L) and intersects(unit, shape_poly(v, L)):
            union(vkeys[id(v)], key)
# pad <-> island
for p in pads:
    for key, L, unit, _ in islands:
        if p.IsOnLayer(L) and intersects(unit, shape_poly(p, L)):
            union(pkeys[id(p)], key)
# track <-> island
for t in tracks:
    L = t.GetLayer()
    for key, IL, unit, _ in islands:
        if IL == L and intersects(unit, shape_poly(t, L)):
            union(tkeys[id(t)], key)
# track <-> pad / via / track
for t in tracks:
    L = t.GetLayer()
    for pt in (t.GetStart(), t.GetEnd()):
        for p in pads:
            if p.IsOnLayer(L) and p.HitTest(pt):
                union(tkeys[id(t)], pkeys[id(p)])
        for v in vias:
            if v.IsOnLayer(L) and v.HitTest(pt):
                union(tkeys[id(t)], vkeys[id(v)])
        for t2 in tracks:
            if t2 is not t and t2.GetLayer() == L and t2.HitTest(pt):
                union(tkeys[id(t)], tkeys[id(t2)])
# via <-> pad
for v in vias:
    for p in pads:
        if p.HitTest(v.GetPosition()):
            union(vkeys[id(v)], pkeys[id(p)])

# ---- main cluster = the one with the biggest In1 island
main_island = max(islands, key=lambda x: x[3])
main = find(main_island[0])
print(f"Net {NET}: {len(pads)} pads, {len(vias)} vias, {len(tracks)} tracks, {len(islands)} fill islands")
print(f"Main cluster anchored on {LNAME[main_island[1]]} island {main_island[0][3]} (area {main_island[3]:.0f} mm2)")

bad_pads = [p for p in pads if find(pkeys[id(p)]) != main]
print(f"\n*** Pads NOT connected to main {NET} cluster: {len(bad_pads)}")
for p in bad_pads:
    pos = p.GetPosition()
    print(f"   {pkeys[id(p)][1]:10s} layer {p.GetLayerName():6s} at ({mm(pos.x):.2f}, {mm(pos.y):.2f})")

print(f"\nFill islands NOT connected to main cluster:")
for key, L, unit, area in islands:
    if find(key) != main:
        bb = unit.BBox()
        members = [pkeys[id(p)][1] for p in pads if find(pkeys[id(p)]) == find(key)]
        print(f"   {LNAME[L]:6s} island {key[3]:3d} area {area:6.1f} mm2  bbox x {mm(bb.GetLeft()):.1f}-{mm(bb.GetRight()):.1f} y {mm(bb.GetTop()):.1f}-{mm(bb.GetBottom()):.1f}  pads in cluster: {members}")

bad_vias = [v for v in vias if find(vkeys[id(v)]) != main]
print(f"\nVias not in main cluster: {len(bad_vias)}")
for v in bad_vias[:20]:
    pos = v.GetPosition()
    print(f"   via at ({mm(pos.x):.2f}, {mm(pos.y):.2f})")

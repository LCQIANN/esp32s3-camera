"""Inspect the KiCad schematic: U2 pin positions, wires touching them, labels,
overall extents. Minimal S-expression parser."""
import re, sys, math
from pathlib import Path

SCH = Path(r"C:\Users\aa095\Desktop\esp32s3-camera\esp32s3-camera.kicad_sch")
text = SCH.read_text(encoding="utf-8")

# --- tiny sexp parser
def parse(s):
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+', s)
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            lst = stack.pop()
            stack[-1].append(lst)
        else:
            stack[-1].append(t)
    return stack[0][0]

doc = parse(text)

def kids(node, name):
    return [k for k in node[1:] if isinstance(k, list) and k and k[0] == name]

def kid(node, name):
    r = kids(node, name)
    return r[0] if r else None

def unq(s):
    return s[1:-1] if isinstance(s, str) and s.startswith('"') else s

lib_symbols = kid(doc, "lib_symbols")
libs = {unq(s[1]): s for s in kids(lib_symbols, "symbol")}
print("lib_symbols:", ", ".join(sorted(libs)))

def lib_pins(libname):
    """Return {pin_number: (x, y, rot)} in symbol coords (KiCad: y up in lib)."""
    pins = {}
    root = libs[libname]
    for unit in kids(root, "symbol"):
        for p in kids(unit, "pin"):
            at = kid(p, "at")
            num = unq(kid(p, "number")[1])
            pins[num] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0)
    return pins

def inst_pin_pos(inst, pins):
    at = kid(inst, "at")
    ix, iy = float(at[1]), float(at[2])
    rot = float(at[3]) if len(at) > 3 else 0.0
    mirror = kid(inst, "mirror")
    m = unq(mirror[1]) if mirror else None
    out = {}
    for num, (px, py, prot) in pins.items():
        x, y = px, -py  # lib y-up -> sheet y-down
        if m == "x":
            y = -y
        elif m == "y":
            x = -x
        a = math.radians(rot)
        xr = x * math.cos(a) + y * math.sin(a)
        yr = -x * math.sin(a) + y * math.cos(a)
        out[num] = (round(ix + xr, 3), round(iy + yr, 3))
    return out

symbols = kids(doc, "symbol")
wires = kids(doc, "wire")
labels = kids(doc, "label") + kids(doc, "global_label") + kids(doc, "hierarchical_label")
power_syms = []

def ref_of(inst):
    for p in kids(inst, "property"):
        if unq(p[1]) == "Reference":
            return unq(p[2])
    return "?"

def val_of(inst):
    for p in kids(inst, "property"):
        if unq(p[1]) == "Value":
            return unq(p[2])
    return "?"

xs, ys = [], []
for s in symbols:
    at = kid(s, "at"); xs.append(float(at[1])); ys.append(float(at[2]))
for w in wires:
    for xy in kids(kid(w, "pts"), "xy"):
        xs.append(float(xy[1])); ys.append(float(xy[2]))
print(f"sheet extents: x {min(xs):.1f}..{max(xs):.1f}  y {min(ys):.1f}..{max(ys):.1f}  (paper {unq(kid(doc,'paper')[1])})")

def wires_at(pt, tol=0.01):
    res = []
    for w in wires:
        pts = [(float(xy[1]), float(xy[2])) for xy in kids(kid(w, "pts"), "xy")]
        for p in pts:
            if abs(p[0] - pt[0]) < tol and abs(p[1] - pt[1]) < tol:
                res.append(pts)
                break
    return res

def labels_at(pt, tol=0.01):
    res = []
    for l in labels:
        at = kid(l, "at")
        if abs(float(at[1]) - pt[0]) < tol and abs(float(at[2]) - pt[1]) < tol:
            res.append((l[0], unq(l[1])))
    return res

targets = sys.argv[1:] or ["U2"]
for s in symbols:
    r = ref_of(s)
    if r in targets:
        lib = unq(kid(s, "lib_id")[1])
        at = kid(s, "at")
        print(f"\n{r} {val_of(s)} lib={lib} at={at[1:]} mirror={kid(s,'mirror')}")
        pp = inst_pin_pos(s, lib_pins(lib))
        for num in sorted(pp, key=lambda n: int(re.sub(r'\D', '', n) or 0)):
            pt = pp[num]
            ws = wires_at(pt)
            ls = labels_at(pt)
            print(f"  pin {num} @ {pt}  wires: {ws}  labels: {ls}")

# power symbols near U2 for context
for s in symbols:
    lib = unq(kid(s, "lib_id")[1])
    if lib.startswith("power:"):
        at = kid(s, "at")
        power_syms.append((val_of(s), float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0))
print("\npower symbols:", sorted(set(p[0] for p in power_syms)))

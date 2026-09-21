"""v1.2 schematic edit: power switch SW4 on the 3.3V LDO enable, pull-up R21,
power LED D5 + R20. Text-level edit of esp32s3-camera.kicad_sch.

Steps
 1. U2 pin 3 (EN): rename the global label at its wire end from VSYS to LDO_EN.
 2. Add lib symbol Switch:SW_SPDT (copied from KiCad's Switch.kicad_sym).
 3. Add SW4, R21, R20, D5 with wires + global labels in a free area.
 4. Title block rev -> 1.2.
Writes symbol UUIDs to v12_uuids.json for the PCB script.
"""
import json, re, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sch_inspect import parse, kids, kid, unq  # reuse the tiny parser

import os
PROJ = Path(os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera"))
SCH = PROJ / "esp32s3-camera.kicad_sch"
LIB = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Switch.kicad_sym")
OUT_JSON = Path(__file__).with_name("v12_uuids.json")
SHEET_UUID = "865191c2-abe4-4835-8228-69722a4314d0"

text = SCH.read_text(encoding="utf-8")
assert "(rev \"1.1\")" in text, "expected v1.1 schematic"

# ---------------------------------------------------------------- 1. relabel U2 EN
# wire from U2 pin 3 (162.56,299.72) ends at (160.02,299.72); the VSYS global label sits there
m = re.search(r'\(global_label "VSYS"\s*\(shape [a-z_]+\)\s*\(at 160\.02 299\.72 [\d.]+\)', text)
assert m, "VSYS label at U2 pin 3 not found"
text = text[:m.start()] + m.group(0).replace('"VSYS"', '"LDO_EN"') + text[m.end():]
print("U2 pin 3 label -> LDO_EN")

# ---------------------------------------------------------------- 2. lib symbol SW_SPDT
lib_text = LIB.read_text(encoding="utf-8")
start = lib_text.index('\t(symbol "SW_SPDT"\n')
# balanced paren scan
depth, i = 0, start
while True:
    c = lib_text[i]
    if c == '"':
        j = lib_text.index('"', i + 1)
        while lib_text[j - 1] == "\\":
            j = lib_text.index('"', j + 1)
        i = j + 1
        continue
    if c == "(":
        depth += 1
    elif c == ")":
        depth -= 1
        if depth == 0:
            i += 1
            break
    i += 1
block = lib_text[start:i]
block = block.replace('(symbol "SW_SPDT"', '(symbol "Switch:SW_SPDT"', 1)
# indent one more tab level to sit inside lib_symbols
block = "\n".join("\t" + ln if ln.strip() else ln for ln in block.splitlines())
# pins of SW_SPDT (for wiring)
sw_sym = parse(lib_text[start:i])
sw_pins = {}
for unit in kids(sw_sym, "symbol"):
    for p in kids(unit, "pin"):
        at = kid(p, "at")
        sw_pins[unq(kid(p, "number")[1])] = (float(at[1]), float(at[2]))
print("SW_SPDT pins:", sw_pins)
assert set(sw_pins) == {"1", "2", "3"}

def block_end(s, start):
    """index just past the ')' that closes the S-expression starting at s[start] == '('"""
    depth, i = 0, start
    while True:
        c = s[i]
        if c == '"':
            j = s.index('"', i + 1)
            while s[j - 1] == "\\":
                j = s.index('"', j + 1)
            i = j + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1

ls_start = text.index("(lib_symbols")
ls_close = block_end(text, ls_start) - 1          # index of the ')' closing lib_symbols
# back up over the whitespace before that ')' so the new block sits on its own lines
ins = text.rfind("\n", 0, ls_close)
text = text[:ins] + "\n" + block + text[ins:]
print("lib symbol Switch:SW_SPDT added")

# pin geometry of Device:R and Device:LED from the existing lib_symbols
doc = parse(text)
libs = {unq(s[1]): s for s in kids(kid(doc, "lib_symbols"), "symbol")}
def pins_of(name):
    out = {}
    for unit in kids(libs[name], "symbol"):
        for p in kids(unit, "pin"):
            at = kid(p, "at")
            out[unq(kid(p, "number")[1])] = (float(at[1]), float(at[2]))
    return out
R_PINS, LED_PINS = pins_of("Device:R"), pins_of("Device:LED")
print("R pins", R_PINS, "LED pins", LED_PINS)

# ---------------------------------------------------------------- 3. new circuit
def u():
    return str(uuid.uuid4())

def prop(name, value, x, y, hide=False, justify="left"):
    h = "\n\t\t\t(hide yes)" if hide else ""
    j = f"\n\t\t\t\t(justify {justify})" if not hide else ""
    return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {x} {y} 0){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}\n\t\t\t)\n\t\t)\n')

def symbol(lib_id, ref, value, footprint, lcsc, x, y, rot, pin_numbers, sid):
    s = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x} {y} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
         f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n'
         f'\t\t(uuid "{sid}")\n')
    s += prop("Reference", ref, x + 2.54, y - 2.54)
    s += prop("Value", value, x + 2.54, y)
    s += prop("Footprint", footprint, x, y, hide=True)
    s += prop("Datasheet", "", x, y, hide=True)
    s += prop("Description", "", x, y, hide=True)
    s += prop("LCSC", lcsc, x, y, hide=True)
    for n in pin_numbers:
        s += f'\t\t(pin "{n}"\n\t\t\t(uuid "{u()}")\n\t\t)\n'
    s += (f'\t\t(instances\n\t\t\t(project "esp32s3-camera"\n\t\t\t\t(path "/{SHEET_UUID}"\n'
          f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    return s

def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1:g} {y1:g}) (xy {x2:g} {y2:g})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')

def glabel(name, x, y, rot):
    just = "left" if rot in (0, 90) else "right"
    return (f'\t(global_label "{name}"\n\t\t(shape input)\n\t\t(at {x:g} {y:g} {rot})\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{u()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {x:g} {y:g} 0)\n\t\t\t(hide yes)\n'
            f'\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')

def no_connect(x, y):
    return f'\t(no_connect\n\t\t(at {x:g} {y:g})\n\t\t(uuid "{u()}")\n\t)\n'

def stext(s, x, y):
    return (f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {x:g} {y:g} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 2.54 2.54)\n\t\t\t\t(bold yes)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')

def sheet_pt(inst_x, inst_y, rot, px, py):
    # lib y-up -> sheet y-down, then rotate (rot in degrees, KiCad convention)
    import math
    x, y = px, -py
    a = math.radians(rot)
    xr = x * math.cos(a) + y * math.sin(a)
    yr = -x * math.sin(a) + y * math.cos(a)
    return (round(inst_x + xr, 2), round(inst_y + yr, 2))

# free column at the right of the sheet (existing content ends at x ~531 on the A2 page)
X0 = 560.07   # 441 x 1.27 mm: keep every pin on the 1.27 mm connection grid
ids = {"SW4": u(), "R21": u(), "R20": u(), "D5": u()}
new = ""
new += stext("POWER SWITCH + POWER LED (v1.2)", X0 - 25, 62.23)

# SW4 --------------------------------------------------------------------
y = 80.01
new += symbol("Switch:SW_SPDT", "SW4", "PWR", "Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02", "C431540", X0, y, 0, ["1", "2", "3"], ids["SW4"])
p2 = sheet_pt(X0, y, 0, *sw_pins["2"])   # common
p1 = sheet_pt(X0, y, 0, *sw_pins["1"])
p3 = sheet_pt(X0, y, 0, *sw_pins["3"])
# common -> LDO_EN (wire to the left)
lx = p2[0] - 2.54
new += wire(p2[0], p2[1], lx, p2[1]) + glabel("LDO_EN", lx, p2[1], 180)
# pin 3 -> GND (wire to the right)
rx = p3[0] + 2.54
new += wire(p3[0], p3[1], rx, p3[1]) + glabel("GND", rx, p3[1], 0)
# pin 1 unused
new += no_connect(*p1)

# R21 100k pull-up VSYS -> LDO_EN ---------------------------------------
y = 120.65
new += symbol("Device:R", "R21", "100k", "Resistor_SMD:R_0603_1608Metric", "C25803", X0, y, 0, ["1", "2"], ids["R21"])
a = sheet_pt(X0, y, 0, *R_PINS["1"]); b = sheet_pt(X0, y, 0, *R_PINS["2"])
top, bot = (a, b) if a[1] < b[1] else (b, a)
new += wire(top[0], top[1], top[0], top[1] - 2.54) + glabel("VSYS", top[0], top[1] - 2.54, 90)
new += wire(bot[0], bot[1], bot[0], bot[1] + 2.54) + glabel("LDO_EN", bot[0], bot[1] + 2.54, 270)

# R20 1k from +3V3 -----------------------------------------------------
y = 149.86
new += symbol("Device:R", "R20", "1k", "Resistor_SMD:R_0603_1608Metric", "C21190", X0, y, 0, ["1", "2"], ids["R20"])
a = sheet_pt(X0, y, 0, *R_PINS["1"]); b = sheet_pt(X0, y, 0, *R_PINS["2"])
top, bot = (a, b) if a[1] < b[1] else (b, a)
new += wire(top[0], top[1], top[0], top[1] - 2.54) + glabel("+3V3", top[0], top[1] - 2.54, 90)
new += wire(bot[0], bot[1], bot[0], bot[1] + 2.54) + glabel("LEDA_PWR", bot[0], bot[1] + 2.54, 270)

# D5 blue power LED ----------------------------------------------------
y = 175.26
new += symbol("Device:LED", "D5", "BLUE", "LED_SMD:LED_0603_1608Metric", "C2288", X0, y, 0, ["1", "2"], ids["D5"])
k = sheet_pt(X0, y, 0, *LED_PINS["1"]); an = sheet_pt(X0, y, 0, *LED_PINS["2"])
left, right = (k, an) if k[0] < an[0] else (an, k)
lname, rname = ("GND", "LEDA_PWR") if left == k else ("LEDA_PWR", "GND")
new += wire(left[0], left[1], left[0] - 2.54, left[1]) + glabel(lname, left[0] - 2.54, left[1], 180)
new += wire(right[0], right[1], right[0] + 2.54, right[1]) + glabel(rname, right[0] + 2.54, right[1], 0)

# insert before sheet_instances
si = text.index("\n\t(sheet_instances")
text = text[:si] + "\n" + new.rstrip("\n") + text[si:]

# ---------------------------------------------------------------- 4. rev
text = text.replace('(rev "1.1")', '(rev "1.2")', 1)

SCH.write_text(text, encoding="utf-8", newline="\n")
OUT_JSON.write_text(json.dumps({"sheet": SHEET_UUID, "symbols": ids}, indent=1), encoding="utf-8")
print("schematic written; uuids ->", OUT_JSON)

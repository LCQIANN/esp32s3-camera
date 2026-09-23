"""v1.3 schematic edit: replace the two 1x4 headers J5 (UART/DEBUG) and J6
(EXPANSION) with one 1x7 female socket J5 that the generic 1.3" ST7789
module plugs into directly. Text-level edit of esp32s3-camera.kicad_sch.

Pin order = module order:  1 GND, 2 VCC(+3V3), 3 SCL, 4 SDA, 5 RES, 6 DC, 7 BLK
SCL = GPIO44 (net UART_RX), SDA = GPIO43 (net UART_TX): both are plain GPIO-matrix
pins, this pairing keeps the existing PCB traces. RES/DC/BLK = GPIO6/5/4.

Steps
 1. Add lib symbol Connector_Generic:Conn_01x07 (copied from KiCad's library).
 2. Delete J5, J6 symbols, their 8 wires and 8 global labels.
 3. Add J5 (Conn_01x07) at the same spot with wires + global labels + a note.
 4. Title block rev -> 1.3.
Writes the new symbol UUID to v13_uuids.json for the PCB script.
"""
import json, os, re, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sch_inspect import parse, kids, kid, unq

PROJ = Path(os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera"))
SCH = PROJ / "esp32s3-camera.kicad_sch"
LIB = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Connector_Generic.kicad_sym")
OUT_JSON = Path(__file__).with_name("v13_uuids.json")
SHEET_UUID = "865191c2-abe4-4835-8228-69722a4314d0"
J5_OLD, J6_OLD = "89c77f86-7001-4f6f-9ea5-ced454cf95c3", "ed0d8235-26a8-42db-8df3-6f2312631f7e"
LCSC_SOCKET = "C225482"      # CJT A2541WV-7P, 2.54 mm 1x7 straight female header

text = SCH.read_text(encoding="utf-8")
assert '(rev "1.2")' in text, "expected v1.2 schematic"


def block_end(s, start):
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


def u():
    return str(uuid.uuid4())


# ---------------------------------------------------------------- 1. lib symbol Conn_01x07
lib_text = LIB.read_text(encoding="utf-8")
start = lib_text.index('\t(symbol "Conn_01x07"\n')
end = block_end(lib_text, start)
block = lib_text[start:end].replace('(symbol "Conn_01x07"', '(symbol "Connector_Generic:Conn_01x07"', 1)
block = "\n".join("\t" + ln if ln.strip() else ln for ln in block.splitlines())
pins = {}
for unit in kids(parse(lib_text[start:end]), "symbol"):
    for p in kids(unit, "pin"):
        at = kid(p, "at")
        pins[unq(kid(p, "number")[1])] = (float(at[1]), float(at[2]))
print("Conn_01x07 pins (lib coords):", pins)
assert set(pins) == {str(i) for i in range(1, 8)}
assert "Connector_Generic:Conn_01x07" not in text
ls_start = text.index("(lib_symbols")
ls_close = block_end(text, ls_start) - 1
ins = text.rfind("\n", 0, ls_close)
text = text[:ins] + "\n" + block + text[ins:]
print("lib symbol Connector_Generic:Conn_01x07 added")

# ---------------------------------------------------------------- 2. delete J5, J6 + wiring
X_PIN, X_LBL = 525.78, 523.24
OLD_Y = [297.18, 299.72, 302.26, 304.8, 358.14, 360.68, 363.22, 365.76]


def remove_blocks(text, head, pred, expect):
    """remove every top-level block starting with `head` for which pred(block) is true"""
    out, i, n = [], 0, 0
    while True:
        j = text.find(head, i)
        if j < 0:
            out.append(text[i:]); break
        e = block_end(text, j)
        blk = text[j:e]
        if pred(blk):
            n += 1
            # also swallow the newline that preceded the block
            k = text.rfind("\n", i, j)
            out.append(text[i:k if k >= 0 else j])
        else:
            out.append(text[i:e])
        i = e
    assert n == expect, f"{head}: removed {n}, expected {expect}"
    return "".join(out)


text = remove_blocks(text, "\n\t(symbol\n", lambda b: J5_OLD in b or J6_OLD in b, 2)
wire_pts = {f"(xy {X_PIN:g} {y:g}) (xy {X_LBL:g} {y:g})" for y in OLD_Y}
text = remove_blocks(text, "\n\t(wire\n", lambda b: any(w in b for w in wire_pts), 8)
lbl_at = {f"(at {X_LBL:g} {y:g} 0)" for y in OLD_Y}
text = remove_blocks(text, "\n\t(global_label ", lambda b: any(a in b.split("(effects")[0] for a in lbl_at), 8)
print("J5, J6 symbols, 8 wires, 8 labels removed")

# ---------------------------------------------------------------- 3. new J5
def prop(name, value, x, y, hide=False):
    h = "\n\t\t\t(hide yes)" if hide else ""
    j = "" if hide else "\n\t\t\t\t(justify left)"
    return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {x:g} {y:g} 0){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}\n\t\t\t)\n\t\t)\n')


def symbol(lib_id, ref, value, footprint, lcsc, x, y, pin_numbers, sid):
    s = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x:g} {y:g} 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
         f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n'
         f'\t\t(uuid "{sid}")\n')
    s += prop("Reference", ref, x - 2.54, y - 12.7)
    s += prop("Value", value, x - 2.54, y - 10.16)
    s += prop("Footprint", footprint, x, y, hide=True)
    s += prop("Datasheet", "", x, y, hide=True)
    s += prop("Description", "1.3in IPS 240x240 ST7789 7-pin module plugs in here (bottom side)", x, y, hide=True)
    s += prop("LCSC", lcsc, x, y, hide=True)
    for n in pin_numbers:
        s += f'\t\t(pin "{n}"\n\t\t\t(uuid "{u()}")\n\t\t)\n'
    s += (f'\t\t(instances\n\t\t\t(project "esp32s3-camera"\n\t\t\t\t(path "/{SHEET_UUID}"\n'
          f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    return s


def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1:g} {y1:g}) (xy {x2:g} {y2:g})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')


def glabel(name, x, y):
    return (f'\t(global_label "{name}"\n\t\t(shape input)\n\t\t(at {x:g} {y:g} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n\t\t(uuid "{u()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {x:g} {y:g} 0)\n\t\t\t(hide yes)\n'
            f'\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def stext(s, x, y, size=1.27, bold=False):
    b = "\n\t\t\t\t(bold yes)" if bold else ""
    return (f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {x:g} {y:g} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size {size:g} {size:g}){b}\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n\t\t(uuid "{u()}")\n\t)\n')


X0, Y0 = 530.86, 302.26          # pin 4 lands on the old J5 pin 3 row
NETS = ["GND", "+3V3", "UART_RX", "UART_TX", "IO6", "IO5", "IO4"]   # pins 1..7
j5_uuid = u()
new = symbol("Connector_Generic:Conn_01x07", "J5", "DISPLAY 1.3in ST7789",
             "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical", LCSC_SOCKET, X0, Y0, [str(i) for i in range(1, 8)], j5_uuid)
pin_y = {}
for n, netname in enumerate(NETS, start=1):
    px, py = pins[str(n)]
    sx, sy = round(X0 + px, 2), round(Y0 - py, 2)          # lib y-up -> sheet y-down
    assert abs(sx - X_PIN) < 1e-6, (n, sx)
    pin_y[n] = sy
    new += wire(sx, sy, X_LBL, sy) + glabel(netname, X_LBL, sy)
print("J5 pin rows:", pin_y)
new += stext("DISPLAY SOCKET (v1.3)", 503.0, 288.0, 2.54, True)
new += stext("1x7 female 2.54 mm socket on the BOTTOM side; the 1.3in IPS 240x240 ST7789", 503.0, 315.0)
new += stext("7-pin module (GND VCC SCL SDA RES DC BLK) plugs straight in, screen facing out.", 503.0, 317.5)
new += stext("SCL = GPIO44 (UART_RX), SDA = GPIO43 (UART_TX), RES = GPIO6, DC = GPIO5, BLK = GPIO4.", 503.0, 320.0)
new += stext("UART0 header is gone: use the USB-CDC console. Unplug the display to reach TX/RX here.", 503.0, 322.5)

si = text.index("\n\t(sheet_instances")
text = text[:si] + "\n" + new.rstrip("\n") + text[si:]

# ---------------------------------------------------------------- 4. rev
text = text.replace('(rev "1.2")', '(rev "1.3")', 1)

SCH.write_text(text, encoding="utf-8", newline="\n")
OUT_JSON.write_text(json.dumps({"sheet": SHEET_UUID, "symbols": {"J5": j5_uuid}}, indent=1), encoding="utf-8")
print("schematic written; uuids ->", OUT_JSON)

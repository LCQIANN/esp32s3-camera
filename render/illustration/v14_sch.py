"""v1.4 schematic edit: SW3 (SHUTTER) becomes a side-actuated ALPS SKRTLAE010 on the top board
edge. Only the footprint/LCSC fields change, plus a note; wiring is untouched. Rev -> 1.4."""
import os, re, uuid
from pathlib import Path

PROJ = Path(os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera"))
SCH = PROJ / "esp32s3-camera.kicad_sch"
text = SCH.read_text(encoding="utf-8")
assert '(rev "1.3")' in text, "expected v1.3 schematic"

start = text.index('(property "Reference" "SW3"')
end = text.index("(instances", start)
blk = text[start:end]
new = blk.replace('"Button_Switch_SMD:SW_SPST_SKQG_WithoutStem"',
                  '"esp32s3-camera:SW_Push_SKRTLAE010_Side"', 1)
new = re.sub(r'\(property "LCSC" "C115351"', '(property "LCSC" "C110293"', new, count=1)
assert new != blk and "C110293" in new and "SW_Push_SKRTLAE010_Side" in new
text = text[:start] + new + text[end:]

def stext(s, x, y, size=1.27, bold=False):
    b = "\n\t\t\t\t(bold yes)" if bold else ""
    return (f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {x:g} {y:g} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size {size:g} {size:g}){b}\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')

# note next to the display-socket note added in v1.3
note = (stext("SHUTTER BUTTON (v1.4)", 503.0, 328.0, 2.54, True)
        + stext("SW3 is a side-actuated ALPS SKRTLAE010 (LCSC C110293) on the TOP board edge at (50.6, 2.6),", 503.0, 332.0)
        + stext("stem pointing off the edge so the enclosure's top wall carries the shutter button.", 503.0, 334.5)
        + stext("SW1 BOOT / SW2 RESET stay top-actuated on the lens face (pinholes in the enclosure).", 503.0, 337.0))
si = text.index("\n\t(sheet_instances")
text = text[:si] + "\n" + note.rstrip("\n") + text[si:]
text = text.replace('(rev "1.3")', '(rev "1.4")', 1)
SCH.write_text(text, encoding="utf-8", newline="\n")
print("schematic written: SW3 footprint/LCSC updated, rev 1.4")

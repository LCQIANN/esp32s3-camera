"""Add ON / OFF silkscreen labels next to SW4 and tidy nearby reference texts.
Mechanics (Vimex MSK-12C02 drawing): knob slid toward a terminal connects the
common (middle, pad 2) to THAT terminal. Pad 3 = GND (OFF), pad 1 = open (ON).
With SW4 at (57.6, 11) rot 90: pad 3 is at y 8.75 (toward the board top edge),
pad 1 at y 13.25 (toward the module). So OFF label above, ON label below.
Note: pcbnew/SWIG objects fetched before a Remove() can go stale, so all
footprint edits happen first and the text removal/addition last."""
import os
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = os.path.join(os.environ.get("PROJ_DIR", r"C:\Users\aa095\Desktop\esp32s3-camera"), "esp32s3-camera.kicad_pcb")
b = pcbnew.LoadBoard(BOARD)
F_SILK = b.GetLayerID("F.SilkS")

# 1. reference text positions (before any Remove)
sw4 = b.FindFootprintByReference("SW4")
assert sw4 and round(pcbnew.ToMM(sw4.GetPosition().x), 1) == 57.6
sw4.Reference().SetPosition(VECTOR2I(FromMM(57.6), FromMM(17.4)))
b.FindFootprintByReference("R20").Reference().SetPosition(VECTOR2I(FromMM(53.0), FromMM(9.7)))

# 2. drop earlier ON/OFF labels (idempotent), collected in one pass
old = [d for d in list(b.GetDrawings())
       if d.GetClass() == "PCB_TEXT" and d.GetLayer() == F_SILK and d.GetText() in ("ON", "OFF")]
for d in old:
    b.Remove(d)

# 3. add labels
def silk(text, x, y, size=0.8, thick=0.15):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text); t.SetLayer(F_SILK)
    t.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(thick))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    b.Add(t)

silk("OFF", 55.3, 6.3)
silk("ON", 55.3, 15.9)
pcbnew.SaveBoard(BOARD, b)
print(f"removed {len(old)} old labels, added ON/OFF, moved SW4/R20 refs; saved {BOARD}")

import pcbnew
from pcbnew import VECTOR2I, FromMM
BOARD = r"C:\Users\aa095\Desktop\esp32s3-camera\esp32s3-camera.kicad_pcb"
b = pcbnew.LoadBoard(BOARD)
fp = [f for f in b.GetFootprints() if f.GetReference() == "J5"][0]
fp.SetField("Description", "1.3in IPS 240x240 ST7789 7-pin module plugs in here (bottom side)")
for fld in fp.GetFields():
    if fld.GetName() == "Description":
        fld.SetVisible(False); fld.SetLayer(pcbnew.B_Fab)
n = 0
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.B_SilkS and d.GetText() in ("GND", "3V3", "SCL", "SDA", "RES", "DC", "BLK"):
        d.SetTextSize(VECTOR2I(FromMM(0.6), FromMM(0.8))); d.SetPosition(VECTOR2I(FromMM(58.6), d.GetPosition().y)); n += 1
print("labels moved:", n)
pcbnew.SaveBoard(BOARD, b)

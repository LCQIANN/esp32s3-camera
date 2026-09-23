"""v1.3 follow-up: library nickname on J5's footprint id, hidden LCSC field, silk labels >= 0.8 mm."""
import pcbnew
from pcbnew import VECTOR2I, FromMM
BOARD = r"C:\Users\aa095\Desktop\esp32s3-camera\esp32s3-camera.kicad_pcb"
b = pcbnew.LoadBoard(BOARD)
fps = [f for f in b.GetFootprints() if f.GetReference() == "J5"]
fp = fps[0]
fp.SetFPID(pcbnew.LIB_ID("Connector_PinSocket_2.54mm", "PinSocket_1x07_P2.54mm_Vertical"))
if not fp.HasField("LCSC"):
    fp.SetField("LCSC", "C225482")
for fld in fp.GetFields():
    if fld.GetName() == "LCSC":
        fld.SetVisible(False); fld.SetLayer(pcbnew.B_Fab); fld.SetPosition(fp.GetPosition())
print("FPID", fp.GetFPID().GetUniStringLibId(), "fields", [f.GetName() for f in fp.GetFields()])
n = 0
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.B_SilkS and d.GetText() in ("GND", "3V3", "SCL", "SDA", "RES", "DC", "BLK", "DISPLAY"):
        d.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); d.SetTextThickness(FromMM(0.12)); n += 1
print("labels resized:", n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(BOARD, b)

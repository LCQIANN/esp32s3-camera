"""Create render/illustration/esp32s3-camera-illustration.kicad_pcb: a copy of the
real board plus pad-less footprints carrying simple VRML models of the off-board
parts (camera module + ribbon, microSD card, LiPo battery). For rendering only;
the real board file is not touched. Model paths use ${KIPRJMOD}/models so the
folder is self-contained.
"""
import shutil
import uuid
from pathlib import Path

PROJ = Path(r"C:\Users\aa095\Desktop\esp32s3-camera")
SRC = PROJ / "esp32s3-camera.kicad_pcb"
OUT_DIR = PROJ / "render" / "illustration"
DST = OUT_DIR / "esp32s3-camera-illustration.kicad_pcb"
MODEL_SRC = OUT_DIR / "models"  # models live next to this script

# name, ref, x, y, rot, model file, offset xyz (mm)
ITEMS = [
    ("CameraModule", "ILL1", 30.0, 6.5, 0, "camera_module.wrl", (0, 0, 0)),
    ("MicroSDCard", "ILL2", 3.5, 44.0, 0, "microsd_card.wrl", (0, 0, -2.5)),
    # pouch top face 2.0 mm below the board underside (1.6 mm board + 2.0 mm foam pad)
    ("LiPoBattery", "ILL3", 34.0, 44.0, 180, "lipo_battery.wrl", (0, 0, -3.6)),
    # 1.3" ST7789 preview display, face-down on top of the battery (battery bottom face at z = -9.6)
    # 1.3" 7-pin module (27.78 x 39.22) turned 90 deg so its header edge faces J5/J6 at the right board edge;
    # rot 90: local +Y (header edge) -> board +X. Sits on the battery (battery bottom face z = -9.6).
    ("DisplayModule", "ILL4", 34.0, 45.0, 90, "display_module.wrl", (0, 0, -9.7)),
]


def prop(name, value, layer):
    return f"""\t\t(property "{name}" "{value}"
\t\t\t(at 0 0 0)
\t\t\t(layer "{layer}")
\t\t\t(hide yes)
\t\t\t(uuid "{uuid.uuid4()}")
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)
\t\t)
"""


def footprint(name, ref, x, y, rot, model, off):
    return f"""\t(footprint "Illustration:{name}"
\t\t(layer "F.Cu")
\t\t(uuid "{uuid.uuid4()}")
\t\t(at {x} {y} {rot})
{prop("Reference", ref, "F.SilkS")}{prop("Value", name, "F.Fab")}{prop("Datasheet", "", "F.Fab")}{prop("Description", "illustration only, not a real part", "F.Fab")}\t\t(attr exclude_from_pos_files exclude_from_bom board_only)
\t\t(embedded_fonts no)
\t\t(model "${{KIPRJMOD}}/models/{model}"
\t\t\t(offset
\t\t\t\t(xyz {off[0]} {off[1]} {off[2]})
\t\t\t)
\t\t\t(scale
\t\t\t\t(xyz 1 1 1)
\t\t\t)
\t\t\t(rotate
\t\t\t\t(xyz 0 0 0)
\t\t\t)
\t\t)
\t)
"""


(OUT_DIR / "models").mkdir(parents=True, exist_ok=True)
for it in ITEMS:
    src, dst = MODEL_SRC / it[5], OUT_DIR / "models" / it[5]
    if src.resolve() != dst.resolve():
        shutil.copyfile(src, dst)
    assert dst.exists(), f"missing model {dst}"

text = SRC.read_text(encoding="utf-8")
assert text.rstrip().endswith(")")
body = text.rstrip()[:-1]
extra = "".join(footprint(*it) for it in ITEMS)
DST.write_text(body + extra + ")\n", encoding="utf-8", newline="\n")
(OUT_DIR / "README.txt").write_text(
    "僅供 3D 示意渲染用的板檔複本。多了 ILL1–ILL3 三個沒有焊盤的假零件，\n"
    "掛著 models/ 內簡化的相機模組、microSD 卡、鋰電池 VRML 模型。\n"
    "不要拿這個檔案出 Gerber；真正的板檔是上層的 esp32s3-camera.kicad_pcb。\n",
    encoding="utf-8",
)
print("wrote", DST)

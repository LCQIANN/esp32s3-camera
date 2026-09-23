# -*- coding: utf-8 -*-
"""Export the v1.4 decks to PDF and per-slide PNGs with PowerPoint (COM), and build a contact sheet.
    python tools/export_decks.py [out_dir_for_pngs]
"""
import os, sys
import win32com.client
from PIL import Image

PROJ = r"C:\Users\aa095\Desktop\esp32s3-camera"
OUT = os.path.normpath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ, "render", "deck-qa"))
os.makedirs(OUT, exist_ok=True)
DECKS = ["esp32s3-camera-v1.4.pptx", "esp32s3-camera-v1.4-簡易版.pptx"]

app = win32com.client.Dispatch("PowerPoint.Application")
for deck in DECKS:
    path = os.path.join(PROJ, deck)
    pres = app.Presentations.Open(path, True, False, False)      # ReadOnly, Untitled=False, WithWindow=False
    pdf = os.path.splitext(path)[0] + ".pdf"
    pres.SaveAs(pdf, 32)                                          # ppSaveAsPDF
    tag = "simple" if "簡易" in deck else "full"
    imgs = []
    for i in range(1, pres.Slides.Count + 1):
        png = os.path.normpath(os.path.join(OUT, f"{tag}-{i:02d}.png"))
        pres.Slides(i).Export(png, "PNG", 1600, 900)
        imgs.append(png)
    pres.Close()
    cols = 3; ims = [Image.open(p).resize((800, 450)) for p in imgs]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 800, rows * 450), "white")
    for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * 800, (k // cols) * 450))
    sheet.save(os.path.join(OUT, f"{tag}-sheet.png"))
    print(deck, "->", pdf, len(imgs), "slides")

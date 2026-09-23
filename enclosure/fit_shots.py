# -*- coding: utf-8 -*-
"""Render fit-check views of the enclosure assembly: shells hidden or ghosted so the camera module,
folded ribbon, battery, leads, microSD card, display module and its Dupont jumpers are visible inside the case.
    python enclosure/fit_shots.py   (SolidWorks open, assembly already built)"""
import os, sys, importlib.util
sys.argv = ["x"]
spec = importlib.util.spec_from_file_location("be", os.path.join(os.path.dirname(__file__), "build_enclosure_sw.py"))
be = importlib.util.module_from_spec(spec); spec.loader.exec_module(be)
W, val, sw, OUT = be.W, be.val, be.sw, be.OUT
be.close_untitled()
path = os.path.join(OUT, "esp32s3-camera-enclosure.SLDASM")
r = sw.OpenDoc6(path, 2, 0, "", 0, 0); m = W(r[0] if isinstance(r, tuple) else r, 'IModelDoc2')
asm = W(m, 'IAssemblyDoc'); ext = W(m.Extension, 'IModelDocExtension')
sw.ActivateDoc3(val(m.GetTitle), False, 0, 0)
comps = {}
for c in asm.GetComponents(True):
    c = W(c, 'IComponent2'); comps[val(c.Name2).split("-1")[0].replace("esp32s3-camera-", "")] = c
print("components:", list(comps))
shells = [comps[k] for k in ("shell-front", "shell-back")]

import pythoncom
from win32com.client import VARIANT
def vis(c, on): c.Visible = 2 if on else 0            # swComponentVisible=2, swComponentHidden=0
def paint(c, rgb, alpha=0.0, spec=0.4, shin=0.3):
    vals = [rgb[0], rgb[1], rgb[2], 1.0, 1.0, spec, shin, alpha, 0.0]   # R G B ambient diffuse specular shininess transparency emission
    c.SetMaterialPropertyValues2(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, vals), 1, None)  # swThisConfiguration
def ghost(c, alpha): paint(c, (0.55, 0.62, 0.70), alpha)
# realistic-ish colours for the simplified off-board parts (whole-component colours)
paint(comps["offboard-camera-module"], (0.12, 0.12, 0.13), spec=0.5)      # black module (ribbon shares the part)
paint(comps["offboard-battery-card"], (0.80, 0.80, 0.82), spec=0.7)       # silver pouch, card, leads
paint(comps["offboard-display-module"], (0.06, 0.12, 0.32), spec=0.6)     # dark blue module PCB / glass
paint(comps["offboard-ribbon"], (0.92, 0.55, 0.12), spec=0.3)             # orange FPC
paint(comps["offboard-display-cable"], (0.78, 0.12, 0.10), spec=0.4)      # red Dupont jumpers + housings
m.EditRebuild3()
def shot(name, view_id, rot=None, zoom=None):
    """zoom = (x1, y1, z1, x2, y2, z2) in mm, board frame (X, Y_b = -y_kicad, Z_b)"""
    m.ShowNamedView2("", view_id); m.ViewZoomtofit2()
    if rot:
        mv = W(m.ActiveView, 'IModelView'); mv.RotateAboutCenter(rot[0], rot[1]); m.ViewZoomtofit2()
    if zoom:
        m.ViewZoomTo2(*[v * 0.001 for v in zoom])
    m.GraphicsRedraw2(); ext.SaveAs3(os.path.join(OUT, name), 0, 1, None, None, 0, 0); print("saved", name)

# 1 front shell off: lens side looking into the back shell
vis(comps["shell-front"], False); vis(comps["shutter-cap"], False); m.EditRebuild3()
shot("fit-front-open-iso.png", 7); shot("fit-front-open-top.png", 1)
# ribbon close-ups: the camera corner, x 12..48, y_k 0..38
Z = (12, -38, -3, 48, 4, 12)
shot("fit-ribbon-top.png", 1, zoom=Z)
shot("fit-ribbon-iso.png", 7, zoom=Z)
vis(comps["shell-front"], True); vis(comps["shutter-cap"], True)
ghost(comps["shell-front"], 0.7); ghost(comps["shutter-cap"], 0.7); m.EditRebuild3()
shot("fit-ribbon-iso-ghost.png", 7, zoom=Z)
comps["shell-front"].RemoveMaterialProperty2(1, None); comps["shutter-cap"].RemoveMaterialProperty2(1, None); m.EditRebuild3()
# 2 back shell off: screen side, battery / leads / card / display on the board
vis(comps["shell-back"], False); m.EditRebuild3()
shot("fit-back-open.png", 2, rot=(0.45, -0.55)); shot("fit-back-open-flat.png", 2)
# Dupont jumpers: display module hidden so the wire path from its header to J5 is visible; then a side view
vis(comps["offboard-display-module"], False); m.EditRebuild3()
shot("fit-cable-back.png", 2, rot=(0.45, -0.55)); shot("fit-cable-back-flat.png", 2)
vis(comps["offboard-display-module"], True); m.EditRebuild3()
shot("fit-cable-right.png", 4)
vis(comps["shell-back"], True)
# 3 both shells ghosted
for c in shells: ghost(c, 0.72)
ghost(comps["shutter-cap"], 0.72); m.EditRebuild3()
shot("fit-ghost-iso.png", 7); shot("fit-ghost-back.png", 2, rot=(0.45, -0.55)); shot("fit-ghost-right.png", 4)
for c in shells: c.RemoveMaterialProperty2(1, None)
comps["shutter-cap"].RemoveMaterialProperty2(1, None)
m.EditRebuild3(); m.Save3(1, 0, 0)     # keep the coloured off-board parts in the assembly
m.ShowNamedView2("", 7); m.ViewZoomtofit2()
print("done")

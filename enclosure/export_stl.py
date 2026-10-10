# -*- coding: utf-8 -*-
"""Re-export the three printable parts (front shell, back shell, shutter cap) as binary STL.

Run with the project's Python (pywin32) while SolidWorks 2024 is open:
    python enclosure/export_stl.py

SolidWorks writes the STL of the *active* document, so each part is opened, activated and its
selection cleared before SaveAs3; the result is checked for triangle count and bounding box (mm).
"""
import os, struct, sys, win32com.client
from win32com.client import gencache

S = gencache.EnsureModule('{83A33D31-27C5-11CE-BFD4-00400513BB57}', 0, 32, 0)
def W(o, n): return getattr(S, n)(o._oleobj_) if o is not None else None
def val(x): return x() if callable(x) else x
OUT = os.path.dirname(os.path.abspath(__file__))
# minimum triangle count that proves the export is complete (the cap is a plain T of two boxes)
PARTS = {"esp32s3-camera-shell-front": 5000, "esp32s3-camera-shell-back": 5000, "esp32s3-camera-shutter-cap": 24}


def stl_stats(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[80:84])[0]
    assert len(b) == 84 + 50 * n, f"{path}: not a binary STL"
    lo = [1e9] * 3; hi = [-1e9] * 3
    for i in range(n):
        off = 84 + 50 * i + 12
        for k in range(3):
            x, y, z = struct.unpack_from('<3f', b, off + 12 * k)
            for j, v in enumerate((x, y, z)):
                lo[j] = min(lo[j], v); hi[j] = max(hi[j], v)
    return n, [round(h - l, 2) for l, h in zip(lo, hi)]


def export(sw, name, min_tri):
    path = os.path.join(OUT, name + ".SLDPRT")
    r = sw.OpenDoc6(path, 1, 1, "", 0, 0)
    m = W(r[0] if isinstance(r, tuple) else r, "IModelDoc2")
    assert m is not None, f"open failed: {path} {r}"
    try:
        sw.ActivateDoc3(val(m.GetTitle), False, 0, 0)
        m.ClearSelection2(True)
        stl = os.path.join(OUT, name + ".STL")
        if os.path.exists(stl):
            os.remove(stl)
        r = W(m.Extension, "IModelDocExtension").SaveAs3(stl, 0, 1, None, None, 0, 0)
        assert r[0] and os.path.exists(stl), f"STL export failed: {stl} {r}"
        n, size = stl_stats(stl)
        assert n >= min_tri, f"{stl}: only {n} triangles, export is incomplete"
        print(f"{name}.STL  triangles {n:>6}  size {size[0]} x {size[1]} x {size[2]} mm")
    finally:
        sw.CloseDoc(val(m.GetTitle))


if __name__ == "__main__":
    sw = W(win32com.client.Dispatch("SldWorks.Application"), 'ISldWorks')
    for name in (sys.argv[1:] or PARTS):
        export(sw, name, PARTS[name])

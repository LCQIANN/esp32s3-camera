# -*- coding: utf-8 -*-
"""Build the ESP32-S3 Camera v1.4 enclosure in SolidWorks 2024 through its COM API.

Run with the project's Python (pywin32) while SolidWorks is open:
    python enclosure/build_enclosure_sw.py

Board frame B (right-handed, what the assembly uses):
    X_b = KiCad x, Y_b = -KiCad y, Z_b = 0 at the board TOP face (component side with the lens),
    board bottom at Z_b = -1.6. Front shell above (Z_b 0..9), back shell below (Z_b -18.6..0).
Each part is modelled in its own local frame so every feature is a +Z extrusion or a cut from the
Front plane (sketch u,v = X,Y) or the Right plane (sketch u,v = -Z, Y); the assembly places them:
    back shell : local = (X_b, Y_b, Z_b + 18.6)            -> translate (0, 0, -18.6)
    front shell: local = (X_b, KiCad y, 9 - Z_b)           -> rotate 180 deg about X, translate (0, 0, +9)
    shutter cap: flange inner face at local Y 0, axis +Y   -> rotate 180 deg about Z, translate (50.6, -0.56, 1.75)
All API lengths are metres.
"""
import math, os, sys, time
import win32com.client
from win32com.client import gencache

PROJ = r"C:\Users\aa095\Desktop\esp32s3-camera"
OUT = os.path.join(PROJ, "enclosure")
BOARD_STEP = os.path.join(PROJ, "esp32s3-camera.step")
TPL_PART = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\零件.PRTDOT"
TPL_ASM = r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\組合件.ASMDOT"
FRONT, TOP, RIGHT = "前基準面", "上基準面", "右基準面"
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ design numbers (mm)
BW, BH, BT = 60.0, 85.0, 1.6          # board
CLR, WALL = 0.5, 2.0                  # board-to-wall clearance, wall thickness
R_OUT = 4.5                           # vertical corner radius (outer); the three wall rings are concentric
R_MID, R_IN = R_OUT - 1.0, R_OUT - 2.0
EDGE_FILLET = 2.5                     # round-over of the front face and the back face outer edge loops
LENS_BEZEL = dict(od=16.0, h=1.5)     # raised ring around the lens hole (inner diameter = lens hole)
GRIP = dict(x0=3.5, x1=15.5, ys=(50, 54, 58, 62, 66, 70), w=1.0, depth=0.6)   # grooves on the lens face, left strip
SCREEN_FRAME = dict(w=28.5, h=28.5, depth=0.8)   # shallow recessed frame around the display window
FRONT_CAV = 7.0                       # clearance above board top (camera module + lens shoulder)
FRONT_PLATE = 2.0
FRONT_H = FRONT_CAV + FRONT_PLATE     # 9.0: front shell spans Z_b 0..9
BACK_CAV = 14.5                       # below board bottom: socket 8.5 + module header 2.54 + PCB 1.2 + LCD 1.6 + 0.6 gap
BACK_FLOOR = 2.5
BACK_H = BT + BACK_CAV + BACK_FLOOR   # 18.6: back shell spans Z_b -18.6..0
LIP = 1.0                             # back-shell lip height / front-shell recess
HOLES = [(4, 4), (56, 4), (4, 71), (56, 71)]     # KiCad coords of H1..H4 (2.2 mm holes)
POST_D, POST_PILOT, POST_PILOT_DEPTH = 4.6, 1.6, 6.0   # front posts (M2 self-tap)
STANDOFF_D, SCREW_CLR, HEAD_D, HEAD_DEPTH = 5.0, 2.4, 4.2, 1.5
PINHOLES = [(9, 24), (9, 32)]                    # SW2 RESET, SW1 BOOT: top-actuated SKQG, poked through 2 mm holes
PINHOLE_D = 2.0
# v1.4 SHUTTER: side-actuated ALPS SKRTLAE010 at KiCad (50.6, 2.6), stem pointing at the top edge (y = 0);
# stem tip at y = 0.56, stem centre 1.75 above the board, switch 3.5 tall. A T-shaped cap sits in the top wall.
SHUTTER = dict(x=50.6, tip_y=0.56, z_centre=2.2, win_w=6.0, win_zb0=0.2, win_zb1=4.4,
               head_w=5.6, head_h=3.6, flange_w=7.6, flange_h=4.0, flange_t=0.8, proud=1.0)   # flange Z_b 0.2..4.2 clears the PCB
LENS = (30, 25, 10.0)                            # KiCad x, y, hole diameter
LEDS_TOP = [(14, 4.5), (9, 4.5), (53, 11.2)]     # D1 green, D4 white, D5 blue (top side)
LED_HOLE_D = 1.5
LED_BOTTOM = (53, 14, 2.0)                       # D2 red charge LED (bottom side)
USB = dict(y0=18.75, y1=29.25, zb0=0.0, zb1=4.2)          # right wall, KiCad y range, Z_b range
SW4 = dict(y0=7.0, y1=15.0, zb0=0.0, zb1=4.5, pocket_y0=5.0, pocket_y1=17.0, pocket_zb0=0.0, pocket_zb1=6.0, pocket_depth=1.0)
SD = dict(y0=37.5, y1=50.5, zb0=-4.8, zb1=-2.0)            # left wall slot for the microSD card
DISPLAY_WIN = dict(cx=40.5, cy=45.0, w=24.5, h=24.5)       # KiCad coords of the active-area centre
# 1.3" ST7789 module plugged into J5 (KiCad coords): PCB 27.78 x 39.22 turned 90 deg, four O2.0 holes 2.5 mm from
# its edges (lcdwiki drawing, GMT130 / ZJY133T). Its PCB back face sits socket 8.5 + header plastic 2.54 below the board.
DISPLAY_MODULE = dict(x0=19.3, x1=58.5, y0=31.1, y1=58.9, hole_inset=2.5, hole_d=2.0, back_zb=-(BT + 8.5 + 2.54))
PEG = dict(post_d=4.0, peg_d=1.8, peg_h=1.5)     # posts from the back-shell floor up to the module back, pegs into its holes

# ------------------------------------------------------------------ SolidWorks plumbing
S = gencache.EnsureModule('{83A33D31-27C5-11CE-BFD4-00400513BB57}', 0, 32, 0)
def W(o, name): return getattr(S, name)(o._oleobj_) if o is not None else None
def val(x): return x() if callable(x) else x
sw = W(win32com.client.Dispatch("SldWorks.Application"), 'ISldWorks')
sw.Visible = True
M = 0.001


class Part:
    def __init__(self, name):
        self.name = name
        self.m = W(sw.NewDocument(TPL_PART, 0, 0, 0), 'IModelDoc2')
        self.part = W(self.m, 'IPartDoc')
        self.ext = W(self.m.Extension, 'IModelDocExtension')
        self.sk = W(self.m.SketchManager, 'ISketchManager')
        self.fm = W(self.m.FeatureManager, 'IFeatureManager')
        self.title = val(self.m.GetTitle)
        self.log = []

    # -- sketch helpers (metres) ---------------------------------------------------------
    def begin(self, plane):
        self.m.ClearSelection2(True)
        ok = self.ext.SelectByID2(plane, "PLANE", 0, 0, 0, False, 0, None, 0)
        assert ok, f"cannot select plane {plane}"
        self.sk.InsertSketch(True)
        self.sk.AddToDB = True

    def end(self):
        self.sk.AddToDB = False
        self.sk.InsertSketch(True)

    def rect(self, x0, y0, x1, y1):
        # four lines: CreateCornerRectangle returns None for rectangles that straddle the sketch origin
        L = self.sk.CreateLine
        x0, y0, x1, y1 = x0 * M, y0 * M, x1 * M, y1 * M
        L(x0, y0, 0, x1, y0, 0); L(x1, y0, 0, x1, y1, 0); L(x1, y1, 0, x0, y1, 0); L(x0, y1, 0, x0, y0, 0)

    def circle(self, x, y, d):
        self.sk.CreateCircleByRadius(x * M, y * M, 0, d / 2 * M)

    def rrect(self, x0, y0, x1, y1, r):
        L, A = self.sk.CreateLine, self.sk.CreateArc
        x0, y0, x1, y1, r = (v * M for v in (x0, y0, x1, y1, r))
        L(x0 + r, y0, 0, x1 - r, y0, 0); L(x1, y0 + r, 0, x1, y1 - r, 0)
        L(x1 - r, y1, 0, x0 + r, y1, 0); L(x0, y1 - r, 0, x0, y0 + r, 0)
        A(x1 - r, y0 + r, 0, x1 - r, y0, 0, x1, y0 + r, 0, 1); A(x1 - r, y1 - r, 0, x1, y1 - r, 0, x1 - r, y1, 0, 1)
        A(x0 + r, y1 - r, 0, x0 + r, y1, 0, x0, y1 - r, 0, 1); A(x0 + r, y0 + r, 0, x0, y0 + r, 0, x0 + r, y0, 0, 1)

    # -- features --------------------------------------------------------------------------
    def volume(self):
        return val(W(self.ext.CreateMassProperty(), 'IMassProperty').Volume) * 1e9

    def extrude(self, depth, label, merge=True):
        """+normal of the sketch plane, from the plane, blind."""
        f = self.fm.FeatureExtrusion3(True, False, False, 0, 0, depth * M, 0.0, False, False, False, False, 0, 0,
                                       False, False, False, False, merge, True, True, 0, 0, False)
        assert f is not None, f"extrude failed: {label}"
        W(f, 'IFeature').Name = label
        self.log.append((label, round(self.volume(), 1)))
        return f

    def extrude_out(self, depth, label):
        """toward -normal of the sketch plane (outside the shell's outer face at Z_l = 0)."""
        f = self.fm.FeatureExtrusion3(True, False, True, 0, 0, depth * M, 0.0, False, False, False, False, 0, 0,
                                       False, False, False, False, True, True, True, 0, 0, False)
        assert f is not None, f"extrude_out failed: {label}"
        W(f, 'IFeature').Name = label
        self.log.append((label, round(self.volume(), 1)))
        return f

    def fillet_loop(self, x, y, z, r, label):
        """Constant-radius fillet on the tangent edge loop that passes through point (x, y, z) mm."""
        v0 = self.volume()
        self.m.ClearSelection2(True)
        assert self.ext.SelectByID2("", "EDGE", x * M, y * M, z * M, False, 1, None, 0), f"edge not found: {label}"
        f = self.fm.FeatureFillet3(3, r * M, 0, 0, 0, 0, 0, None, None, None, None, None, None, None)   # 3 = propagate | uniform radius
        assert f is not None, f"fillet failed: {label}"
        W(f, 'IFeature').Name = label
        dv = v0 - self.volume(); assert dv > 1.0, f"fillet removed nothing: {label}"
        self.log.append((label, round(-dv, 1)))
        return f

    def cut(self, label, through=True, depth=0.0, start=0.0, positive=True):
        """Cut from the sketch plane. start = offset along +normal where the cut begins;
        positive=True cuts toward +normal, False toward -normal."""
        v0 = self.volume()
        t0 = 3 if start else 0
        f = self.fm.FeatureCut4(True, False, positive, 1 if through else 0, 0, depth * M, 0.0, False, False, False, False,
                                0, 0, False, False, False, False, False, True, True, True, True, False, t0, start * M, False, False)
        assert f is not None, f"cut failed: {label}"
        W(f, 'IFeature').Name = label
        dv = v0 - self.volume()
        assert dv > 1e-3, f"cut removed nothing: {label}"
        self.log.append((label, round(-dv, 1)))
        return f

    def save(self, stl=True, png_view="*Isometric"):
        path = os.path.join(OUT, self.name + ".SLDPRT")
        if os.path.exists(path):
            os.remove(path)
        r = self.ext.SaveAs3(path, 0, 1, None, None, 0, 0)
        assert r[0], f"save failed {path} {r}"
        self.m.ViewZoomtofit2(); self.m.ShowNamedView2(png_view, 7); self.m.ViewZoomtofit2()
        self.ext.SaveAs3(os.path.join(OUT, self.name + ".png"), 0, 1, None, None, 0, 0)
        if stl:
            self.ext.SaveAs3(os.path.join(OUT, self.name + ".STL"), 0, 1, None, None, 0, 0)
        self.path = path
        return path

    def close(self):
        sw.CloseDoc(self.title)


# ------------------------------------------------------------------ FRONT SHELL (local: X, y_kicad, Z_l = 9 - Z_b)
def build_front():
    p = Part("esp32s3-camera-shell-front")
    zl = lambda zb: FRONT_H - zb                      # Z_b -> local
    X0, Y0, X1, Y1 = -CLR - WALL, -CLR - WALL, BW + CLR + WALL, BH + CLR + WALL
    # 1 top plate
    p.begin(FRONT); p.rrect(X0, Y0, X1, Y1, R_OUT); p.end(); p.extrude(FRONT_PLATE, "top plate")
    # 2 outer half of the wall, full height
    p.begin(FRONT); p.rrect(X0, Y0, X1, Y1, R_OUT); p.rrect(X0 + 1, Y0 + 1, X1 - 1, Y1 - 1, R_MID); p.end()
    p.extrude(FRONT_H, "wall outer half")
    # 3 inner half, 1 mm shorter -> recess that takes the back-shell lip
    p.begin(FRONT); p.rrect(X0 + 1, Y0 + 1, X1 - 1, Y1 - 1, R_MID); p.rrect(-CLR, -CLR, BW + CLR, BH + CLR, R_IN); p.end()
    p.extrude(FRONT_H - LIP, "wall inner half")
    # 3b round the outer edge of the lens face (whole tangent loop) and raise a bezel ring around the lens
    p.fillet_loop(30, Y0, 0, EDGE_FILLET, "lens face round-over")
    p.begin(FRONT); p.circle(LENS[0], LENS[1], LENS_BEZEL["od"]); p.circle(LENS[0], LENS[1], LENS[2]); p.end()
    p.extrude_out(LENS_BEZEL["h"], "lens bezel ring")
    # 4 corner posts down to the board top, with M2 pilot holes
    p.begin(FRONT)
    for x, y in HOLES: p.circle(x, y, POST_D)
    p.end(); p.extrude(FRONT_H, "corner posts")
    p.begin(FRONT)
    for x, y in HOLES: p.circle(x, y, POST_PILOT)
    p.end(); p.cut("post pilot holes M2", through=False, depth=POST_PILOT_DEPTH, start=FRONT_H, positive=False)
    # 4b grip grooves on the left strip of the lens face (after the posts, so they are not refilled by them)
    p.begin(FRONT)
    for gy in GRIP["ys"]: p.rect(GRIP["x0"], gy - GRIP["w"] / 2, GRIP["x1"], gy + GRIP["w"] / 2)
    p.end(); p.cut("grip grooves", through=False, depth=GRIP["depth"])
    # 5 BOOT / RESET pinholes (poke with a SIM tool); SHUTTER window through the top wall (Top plane: u = X, v = -Z_l,
    #   cut toward -Y from Y = 0 through the wall at Y_l -0.5..-2.5)
    p.begin(FRONT)
    for x, y in PINHOLES: p.circle(x, y, PINHOLE_D)
    p.end(); p.cut("BOOT/RESET pinholes")
    sh = SHUTTER
    p.begin(TOP); p.rect(sh["x"] - sh["win_w"] / 2, -zl(sh["win_zb0"]), sh["x"] + sh["win_w"] / 2, -zl(sh["win_zb1"])); p.end()
    p.cut("shutter window", through=True, positive=False)
    # 6 lens hole and LED light holes
    p.begin(FRONT); p.circle(LENS[0], LENS[1], LENS[2]); p.end(); p.cut("lens hole")
    p.begin(FRONT)
    for x, y in LEDS_TOP: p.circle(x, y, LED_HOLE_D)
    p.end(); p.cut("LED light holes D1 D4 D5")
    # 7 right wall: USB-C window and power-switch slot (Right plane: u = -Z_l, v = Y_l). Blind cut from
    #   X = 59 outward so the button bosses inside are never touched.
    def wall_window(label, y0, y1, zb0, zb1, x_start=BW - 1.0, depth=WALL + CLR + 2.0):
        p.begin(RIGHT); p.rect(-zl(zb0), y0, -zl(zb1), y1); p.end()
        p.cut(label, through=False, depth=depth, start=x_start, positive=True)
    wall_window("USB-C window", USB["y0"], USB["y1"], USB["zb0"], USB["zb1"])
    wall_window("power switch slot", SW4["y0"], SW4["y1"], SW4["zb0"], SW4["zb1"])
    # finger pocket outside the switch so the 1.5 mm knob can be reached
    p.begin(RIGHT); p.rect(-zl(SW4["pocket_zb0"]), SW4["pocket_y0"], -zl(SW4["pocket_zb1"]), SW4["pocket_y1"]); p.end()
    p.cut("switch finger pocket", through=False, depth=SW4["pocket_depth"] + 0.5,
          start=BW + CLR + WALL - SW4["pocket_depth"], positive=True)
    p.save()
    return p


# ------------------------------------------------------------------ BACK SHELL (local: X, Y_b = -y_kicad, Z_l = Z_b + 18.6)
def build_back():
    p = Part("esp32s3-camera-shell-back")
    zl = lambda zb: zb + BACK_H
    Y = lambda yk: -yk                                # KiCad y -> local Y
    X0, X1 = -CLR - WALL, BW + CLR + WALL
    Y0, Y1 = Y(BH) - CLR - WALL, Y(0) + CLR + WALL    # -87.5 .. 2.5
    # 1 floor
    p.begin(FRONT); p.rrect(X0, Y0, X1, Y1, R_OUT); p.end(); p.extrude(BACK_FLOOR, "floor")
    # 2 outer half of the wall up to the parting line (board top)
    p.begin(FRONT); p.rrect(X0, Y0, X1, Y1, R_OUT); p.rrect(X0 + 1, Y0 + 1, X1 - 1, Y1 - 1, R_MID); p.end()
    p.extrude(BACK_H, "wall outer half")
    # 3 inner half of the wall, same height
    p.begin(FRONT); p.rrect(X0 + 1, Y0 + 1, X1 - 1, Y1 - 1, R_MID); p.rrect(-CLR, Y(BH) - CLR, BW + CLR, Y(0) + CLR, R_IN); p.end()
    p.extrude(BACK_H, "wall inner half")
    # 4 lip: 0.9 mm thick ring that rises 1 mm into the front-shell recess (0.1 mm clearance inside)
    p.begin(FRONT); p.rrect(X0 + 1.1, Y0 + 1.1, X1 - 1.1, Y1 - 1.1, R_MID - 0.1); p.rrect(-CLR - 0.1, Y(BH) - CLR - 0.1, BW + CLR + 0.1, Y(0) + CLR + 0.1, R_IN + 0.1); p.end()
    p.extrude(BACK_H + LIP, "lip")
    # 4b round the outer edge of the screen face; shallow recessed frame around the window
    p.fillet_loop(30, Y0, 0, EDGE_FILLET, "screen face round-over")
    # 5 standoffs to the board underside, screw clearance bores, head recesses in the floor
    p.begin(FRONT)
    for x, y in HOLES: p.circle(x, Y(y), STANDOFF_D)
    p.end(); p.extrude(zl(-BT), "standoffs")
    p.begin(FRONT)
    for x, y in HOLES: p.circle(x, Y(y), SCREW_CLR)
    p.end(); p.cut("screw bores")
    p.begin(FRONT)
    for x, y in HOLES: p.circle(x, Y(y), HEAD_D)
    p.end(); p.cut("screw head recesses", through=False, depth=HEAD_DEPTH)
    # 5b four locating posts for the display module: Ø4 up to the module's PCB back face, Ø1.8 pegs into its holes
    dm, pg = DISPLAY_MODULE, PEG
    holes = [(x, y) for x in (dm["x0"] + dm["hole_inset"], dm["x1"] - dm["hole_inset"])
                    for y in (dm["y0"] + dm["hole_inset"], dm["y1"] - dm["hole_inset"])]
    p.begin(FRONT)
    for x, y in holes: p.circle(x, Y(y), pg["post_d"])
    p.end(); p.extrude(zl(dm["back_zb"]), "display posts")
    p.begin(FRONT)
    for x, y in holes: p.circle(x, Y(y), pg["peg_d"])
    p.end(); p.extrude(zl(dm["back_zb"]) + pg["peg_h"], "display pegs")
    print("  display posts at", holes, "top Z_b %.2f, pegs to Z_b %.2f" % (dm["back_zb"], dm["back_zb"] + pg["peg_h"]))
    # 6 recessed screen frame (after the posts, so they cannot refill it), display window and charge LED hole
    d, sf = DISPLAY_WIN, SCREEN_FRAME
    p.begin(FRONT); p.rect(d["cx"] - sf["w"] / 2, Y(d["cy"]) - sf["h"] / 2, d["cx"] + sf["w"] / 2, Y(d["cy"]) + sf["h"] / 2); p.end()
    p.cut("screen frame recess", through=False, depth=sf["depth"])
    p.begin(FRONT); p.rect(d["cx"] - d["w"] / 2, Y(d["cy"]) - d["h"] / 2, d["cx"] + d["w"] / 2, Y(d["cy"]) + d["h"] / 2); p.end()
    p.cut("display window")
    p.begin(FRONT); p.circle(LED_BOTTOM[0], Y(LED_BOTTOM[1]), LED_BOTTOM[2]); p.end(); p.cut("charge LED hole D2")
    # 7 microSD slot through the left wall (Right plane: u = -Z_l, v = Y_l; cut toward -X from X = 0)
    p.begin(RIGHT); p.rect(-zl(SD["zb0"]), Y(SD["y1"]), -zl(SD["zb1"]), Y(SD["y0"])); p.end()
    p.cut("microSD slot", through=True, positive=False)
    # 8 notch the lip / wall top on the right side where the USB-C plug and the switch knob pass (Z_b -1..+1)
    for label, y0, y1 in (("USB-C lip notch", USB["y0"], USB["y1"]), ("switch lip notch", SW4["y0"], SW4["y1"])):
        p.begin(RIGHT); p.rect(-zl(-1.0), Y(y1), -(BACK_H + LIP + 0.5), Y(y0)); p.end()
        p.cut(label, through=False, depth=WALL + CLR + 2.0, start=BW - 1.0, positive=True)
    sh = SHUTTER
    p.begin(TOP); p.rect(sh["x"] - sh["win_w"] / 2, -zl(-1.0), sh["x"] + sh["win_w"] / 2, -(BACK_H + LIP + 0.5)); p.end()
    p.cut("shutter lip notch", through=True, positive=True)
    p.save()
    return p


# ------------------------------------------------------------------ BUTTON CAP
def build_cap():
    """Shutter cap: flange (local Z 0..0.8) + head through the wall, 1 mm proud. Modelled on the Front
    plane with +Z = outward; the assembly turns local +Z into board -Y (the top wall)."""
    sh = SHUTTER
    p = Part("esp32s3-camera-shutter-cap")
    gap = sh["tip_y"] + CLR                                      # stem tip (y 0.56) -> wall inner face (y -0.5) = 1.06 mm
    p.begin(FRONT); p.rect(-sh["flange_w"] / 2, -sh["flange_h"] / 2, sh["flange_w"] / 2, sh["flange_h"] / 2); p.end()
    p.extrude(sh["flange_t"], "flange")
    p.begin(FRONT); p.rect(-sh["head_w"] / 2, -sh["head_h"] / 2, sh["head_w"] / 2, sh["head_h"] / 2); p.end()
    p.extrude(gap + WALL + sh["proud"], "head")                  # flange face -> outside of the wall + proud
    p.save()
    return p


# ------------------------------------------------------------------ BOARD (KiCad STEP -> SLDPRT)
def import_board():
    path = os.path.join(OUT, "esp32s3-camera-board.SLDPRT")
    if os.path.exists(path):
        os.remove(path)
    t = time.time()
    # KiCad writes an assembly-structured STEP; map it to ONE multibody part (Tools > Options > Import)
    PREF_MAP, MULTIBODY_PART = 579, 2        # swImportNeutralAssemblyStructureMapping, ..._MultibodyPart
    old_map = sw.GetUserPreferenceIntegerValue(PREF_MAP)
    sw.SetUserPreferenceIntegerValue(PREF_MAP, MULTIBODY_PART)
    try:
        res = sw.LoadFile4(BOARD_STEP, "r", None, 0)
    finally:
        sw.SetUserPreferenceIntegerValue(PREF_MAP, old_map)
    m = res[0] if isinstance(res, tuple) else res
    assert m is not None, "STEP import failed"
    m = W(m, 'IModelDoc2')
    assert val(m.GetType) == 1, f"imported document is not a part (type {val(m.GetType)})"
    part = W(m, 'IPartDoc'); ext = W(m.Extension, 'IModelDocExtension')
    bodies = [W(b, 'IBody2') for b in part.GetBodies2(0, True)]
    pcb = None
    for b in bodies:
        bx = [v * 1000 for v in b.GetBodyBox()]
        if abs((bx[3] - bx[0]) - BW) < 0.5 and abs((bx[4] - bx[1]) - BH) < 0.5:
            pcb = bx; break
    assert pcb, "PCB body not found in STEP"
    print(f"  STEP imported in {time.time()-t:.0f} s, {len(bodies)} bodies; PCB box x {pcb[0]:.2f}..{pcb[3]:.2f} y {pcb[1]:.2f}..{pcb[4]:.2f} z {pcb[2]:.2f}..{pcb[5]:.2f}")
    r = ext.SaveAs3(path, 0, 1, None, None, 0, 0); assert r[0], r
    sw.CloseDoc(val(m.GetTitle))
    return path, pcb


# ------------------------------------------------------------------ INTERFERENCE CHECK
def check_interference(asm, comps):
    """Report every interference between different components (bodies inside the multibody board part are ignored)."""
    idm = W(asm.InterferenceDetectionManager, 'IInterferenceDetectionMgr')
    idm.TreatCoincidenceAsInterference = False
    idm.TreatSubAssembliesAsComponents = True
    idm.IncludeMultibodyPartInterferences = False
    idm.MakeInterferingPartsTransparent = False
    ints = idm.GetInterferences()
    n = idm.GetInterferenceCount()
    print(f"  interference check: {n} interference(s)")
    total = 0.0
    if ints:
        for i in ints:
            i = W(i, 'IInterference')
            vol = val(i.Volume) * 1e9
            names = []
            for c in (i.Components or []):
                names.append(val(W(c, 'IComponent2').Name2))
            total += vol
            print(f"    {vol:9.2f} mm3  {' <-> '.join(names)}")
    idm.Done()
    return n, total


# ------------------------------------------------------------------ ASSEMBLY
def build_assembly(front, back, cap, board_path, pcb_box):
    asm_m = W(sw.NewDocument(TPL_ASM, 0, 0, 0), 'IModelDoc2')
    asm = W(asm_m, 'IAssemblyDoc'); ext = W(asm_m.Extension, 'IModelDocExtension')
    mu = W(sw.GetMathUtility(), 'IMathUtility')
    def xform(rot, t):   # rot: 3x3 row-major, t: mm
        arr = [rot[0][0], rot[0][1], rot[0][2], rot[1][0], rot[1][1], rot[1][2], rot[2][0], rot[2][1], rot[2][2],
               t[0] * M, t[1] * M, t[2] * M, 1.0, 0, 0, 0]
        import pythoncom
        from win32com.client import VARIANT
        return mu.CreateTransform(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, arr))
    I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    RX180 = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
    comps = []
    def add(path, rot, t, name):
        # the component document must be open in the session before AddComponent5 can reference it
        ext_ = os.path.splitext(path)[1].lower()
        r = sw.OpenDoc6(path, 2 if ext_ == ".sldasm" else 1, 0, "", 0, 0)
        doc = r[0] if isinstance(r, tuple) else r
        assert doc is not None, f"OpenDoc6 failed {path} {r}"
        c = asm.AddComponent5(path, 0, "", False, "", 0, 0, 0)
        assert c is not None, f"AddComponent failed {path}"
        c = W(c, 'IComponent2')
        c.Transform2 = xform(rot, t)
        comps.append((name, c))
        return c
    # board: STEP has X = KiCad x, Y = -KiCad y; shift so its top face is Z_b = 0
    add(board_path, I, (0, 0, -pcb_box[5]), "board")
    add(back.path, I, (0, 0, -BACK_H), "back")
    add(front.path, RX180, (0, 0, FRONT_H), "front")
    # cap: local x -> X, local z -> +Y_b (outward: the top board edge y_k = 0 is Y_b = 0 and the wall lies at
    # Y_b +0.5..+2.5), local y -> -Z_b. SolidWorks stores the rotation row-wise (rows = images of the local axes);
    # the placed bounding box is checked and the transpose used if the cap ever points inward.
    RCAP, RCAP_T = [[1, 0, 0], [0, 0, -1], [0, 1, 0]], [[1, 0, 0], [0, 0, 1], [0, -1, 0]]
    tcap = (SHUTTER["x"], -SHUTTER["tip_y"], SHUTTER["z_centre"])
    ccap = add(cap.path, RCAP, tcap, "shutter-cap"); asm_m.EditRebuild3()
    box = [v * 1000 for v in ccap.GetBox(False, False)]
    if not (box[4] > 3.0 and box[1] > -0.7):
        ccap.Transform2 = xform(RCAP_T, tcap); asm_m.EditRebuild3(); box = [v * 1000 for v in ccap.GetBox(False, False)]
    print("  shutter cap box x %.1f..%.1f  y %.2f..%.2f  z %.1f..%.1f" % (box[0], box[3], box[1], box[4], box[2], box[5]))
    asm_m.EditRebuild3()
    for name, c in comps:
        asm_m.ClearSelection2(True)
        if c.Select4(False, None, False):
            asm.FixComponent()
    asm_m.ClearSelection2(True)
    path = os.path.join(OUT, "esp32s3-camera-enclosure.SLDASM")
    if os.path.exists(path):
        os.remove(path)
    r = ext.SaveAs3(path, 0, 1, None, None, 0, 0); assert r[0], f"assembly save failed {r}"
    # the parts opened by OpenDoc6 stole the foreground: make the assembly the active document again
    sw.ActivateDoc3(val(asm_m.GetTitle), False, 0, 0)
    check_interference(asm, comps)
    # swStandardViews_e: 1 front, 2 back, 3 left, 4 right, 5 top, 6 bottom, 7 isometric (view names are localized, use ids)
    def shot(name, view_id):
        asm_m.ShowNamedView2("", view_id); asm_m.ViewZoomtofit2()
        ext.SaveAs3(os.path.join(OUT, name), 0, 1, None, None, 0, 0)
    shot("enclosure-iso.png", 7); shot("enclosure-lens-side.png", 1); shot("enclosure-screen-side.png", 2)
    shot("enclosure-right-usb-switch.png", 4); shot("enclosure-left-sd.png", 3)
    # exploded look: lift the front shell 30 mm, drop the back shell 30 mm, save, then put them back
    dict(comps)["front"].Transform2 = xform(RX180, (0, 0, FRONT_H + 30)); dict(comps)["back"].Transform2 = xform(I, (0, 0, -BACK_H - 30))
    asm_m.EditRebuild3(); shot("enclosure-exploded.png", 7)
    dict(comps)["front"].Transform2 = xform(RX180, (0, 0, FRONT_H)); dict(comps)["back"].Transform2 = xform(I, (0, 0, -BACK_H))
    asm_m.EditRebuild3(); asm_m.ShowNamedView2("", 7); asm_m.ViewZoomtofit2()
    ext.SaveAs3(path, 0, 1, None, None, 0, 0)
    # close the part windows (the assembly keeps them loaded) and leave the assembly on screen
    for pth in (board_path, back.path, front.path, cap.path):
        sw.CloseDoc(os.path.basename(pth))
    sw.ActivateDoc3(val(asm_m.GetTitle), False, 0, 0)
    return path


def close_untitled():
    """Close unsaved documents left behind by an earlier aborted run (their titles are 零件N / 組合件N)."""
    d = sw.GetFirstDocument()
    while d is not None:
        d = W(d, 'IModelDoc2'); nxt = d.GetNext()
        pth = val(d.GetPathName)
        if not pth or r"\Temp\swx" in pth or r"\scratchpad\swtest" in pth or pth.startswith(OUT):
            print("  closing:", val(d.GetTitle)); sw.CloseDoc(val(d.GetTitle))
        else:
            print("  leaving open:", val(d.GetPathName))
        d = nxt


if __name__ == "__main__":
    t0 = time.time()
    print("open documents"); close_untitled()
    if "--asm-only" in sys.argv:      # reuse the parts saved by an earlier run
        class Saved: pass
        front, back, cap = Saved(), Saved(), Saved()
        for obj, n in ((front, "shell-front"), (back, "shell-back"), (cap, "shutter-cap")):
            obj.path = os.path.join(OUT, f"esp32s3-camera-{n}.SLDPRT"); assert os.path.exists(obj.path), obj.path
    else:
        print("front shell"); front = build_front(); [print("  ", *l) for l in front.log]
        print("back shell"); back = build_back(); [print("  ", *l) for l in back.log]
        print("button cap"); cap = build_cap(); [print("  ", *l) for l in cap.log]
        for p in (front, back, cap): p.close()
    print("board"); board_path, pcb_box = import_board()
    print("assembly"); apath = build_assembly(front, back, cap, board_path, pcb_box)
    print("done in %.0f s ->" % (time.time() - t0), apath)
    print(sorted(os.listdir(OUT)))

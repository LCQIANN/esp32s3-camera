# -*- coding: utf-8 -*-
"""Bring the two v1.2 PowerPoint decks up to board v1.4 + enclosure, editing them in place with
python-pptx (text, images, tables, a few shape moves) and adding enclosure slides in the same style.

    python tools/update_decks_v14.py
Outputs esp32s3-camera-v1.4.pptx and esp32s3-camera-v1.4-簡易版.pptx in the project root.
PDF export and the QA renders are done afterwards with PowerPoint itself (tools/export_decks.py).
"""
import copy, io, os, re
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

PROJ = r"C:\Users\aa095\Desktop\esp32s3-camera"
os.chdir(PROJ)
R = lambda n: os.path.join("render", n)
E = lambda n: os.path.join("enclosure", n)
FONT = "Microsoft JhengHei"
INK, INK2, CARD, DARK = "1B2420", "55625B", "EEF1EC", "1F3F30"
TEAL, AMBER, PINK, SHELL = "23A3A3", "E0A021", "D1467F", "7D8FA6"
FOOTER_FULL = "ESP32-S3 Camera · v1.4 · 60 × 85 mm · 4 層 · 2026-09-23"
FOOTER_SIMPLE = "ESP32-S3 相機板 · 簡易說明"


# ------------------------------------------------------------------ generic helpers
def shapes_at(slide, x=None, y=None, tol=0.06, text_prefix=None, kind=None):
    out = []
    for sh in slide.shapes:
        if x is not None and abs(sh.left / 914400 - x) > tol: continue
        if y is not None and abs(sh.top / 914400 - y) > tol: continue
        if kind == "pic" and sh.shape_type != 13: continue
        if text_prefix is not None:
            if not sh.has_text_frame or not sh.text_frame.text.strip().startswith(text_prefix): continue
        out.append(sh)
    return out


def one(slide, **kw):
    r = shapes_at(slide, **kw)
    assert len(r) == 1, (kw, [s.name for s in r])
    return r[0]


def by_text(slide, prefix):
    return one(slide, text_prefix=prefix)


def set_text(shape, lines):
    """Replace all paragraphs, keeping the first paragraph's paragraph/run formatting."""
    if isinstance(lines, str): lines = [lines]
    tf = shape.text_frame
    p0 = tf.paragraphs[0]._p
    r0 = p0.findall(qn("a:r"))
    rpr = copy.deepcopy(r0[0].find(qn("a:rPr"))) if r0 and r0[0].find(qn("a:rPr")) is not None else None
    ppr = copy.deepcopy(p0.find(qn("a:pPr"))) if p0.find(qn("a:pPr")) is not None else None
    txBody = tf._txBody
    for p in txBody.findall(qn("a:p")): txBody.remove(p)
    for line in lines:
        p = etree.SubElement(txBody, qn("a:p"))
        if ppr is not None: p.append(copy.deepcopy(ppr))
        r = etree.SubElement(p, qn("a:r"))
        if rpr is not None: r.append(copy.deepcopy(rpr))
        t = etree.SubElement(r, qn("a:t")); t.text = line


def set_runs(shape, texts):
    """Set the text of the existing runs of paragraph 0 (mixed formatting kept)."""
    runs = shape.text_frame.paragraphs[0].runs
    assert len(runs) >= len(texts), (len(runs), texts)
    for r, t in zip(runs, texts): r.text = t


def move(shape, x=None, y=None, w=None, h=None):
    if x is not None: shape.left = Inches(x)
    if y is not None: shape.top = Inches(y)
    if w is not None: shape.width = Inches(w)
    if h is not None: shape.height = Inches(h)


def set_line(shape, x1, y1, x2, y2):
    move(shape, min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    xfrm = shape._element.spPr.find(qn("a:xfrm"))
    if (x2 - x1) * (y2 - y1) < 0: xfrm.set("flipV", "1")
    elif "flipV" in xfrm.attrib: del xfrm.attrib["flipV"]
    if "flipH" in xfrm.attrib: del xfrm.attrib["flipH"]


def delete(shape):
    el = shape._element; el.getparent().remove(el)


def clone(slide, shape, dx=0.0, dy=0.0):
    new = copy.deepcopy(shape._element)
    shape._element.addnext(new)
    # unique id
    ids = [int(e.get("id")) for e in slide._element.iter() if e.tag == qn("p:cNvPr")]
    new.find(".//" + qn("p:cNvPr")).set("id", str(max(ids) + 1))
    for sh in slide.shapes:
        if sh._element is new:
            move(sh, sh.left / 914400 + dx, sh.top / 914400 + dy); return sh
    raise RuntimeError("clone not found")


def replace_pic(slide, pic, path, keep_size=True):
    """Swap the picture's image. keep_size: resample to the old pixel size so crops stay identical."""
    im = Image.open(path).convert("RGB")
    if keep_size:
        old = Image.open(io.BytesIO(pic.image.blob)).size
        if im.size != old: im = im.resize(old, Image.LANCZOS)
    bio = io.BytesIO(); im.save(bio, "PNG"); bio.seek(0)
    part, rId = slide.part.get_or_add_image_part(bio)
    blip = pic._element.xpath(".//a:blip")[0]
    blip.set(qn("r:embed"), rId)


def set_crop(pic, l=0, t=0, r=0, b=0):
    pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = l, t, r, b


def cell_set(cell, text):
    tf = cell.text_frame
    p0 = tf.paragraphs[0]
    runs = p0.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]: r._r.getparent().remove(r._r)
    else:
        p0.text = text
    for p in tf.paragraphs[1:]: p._p.getparent().remove(p._p)


def table_remove_row(table, idx):
    tr = table._tbl.tr_lst[idx]; table._tbl.remove(tr)


def recolor(shape, color):
    for p in shape.text_frame.paragraphs:
        for r in p.runs: r.font.color.rgb = RGBColor.from_string(color)


def fill(shape, color):
    shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(color)


# ------------------------------------------------------------------ new-slide builders (match the deck's style)
def style_run(run, size, bold=False, color=INK, font=FONT):
    run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None: el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", font)


def tbox(slide, x, y, w, h, lines, size=12, bold=False, color=INK, anchor="t", align="l", space_after=4):
    if isinstance(lines, str): lines = [lines]
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for c in list(bodyPr): bodyPr.remove(c)          # no autofit
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        p.space_after = Pt(space_after)
        r = p.add_run(); r.text = line; style_run(r, size, bold, color)
    return tb


def rect(slide, x, y, w, h, color=CARD, radius=0.04, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    fill(s, color); s.line.fill.background(); s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    # drop the theme effect (shadow) that add_shape inherits
    st = s._element.find(qn("p:style"))
    if st is not None: s._element.remove(st)
    return s


def square(slide, x, y, color, size=0.22):
    return rect(slide, x, y, size, size, color, radius=0.2)


def pic(slide, path, x, y, w, h=None):
    im = Image.open(path)
    if h is None: h = w * im.size[1] / im.size[0]
    return slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))


def title(slide, text, sub=None):
    tbox(slide, 0.6, 0.45, 12.1, 0.7, text, 30, True, INK)
    if sub: tbox(slide, 0.6, 1.13, 12.1, 0.4, sub, 12, False, INK2)


def add_slide_at(prs, index):
    layout = [l for l in prs.slide_layouts if l.name == "Blank"][0]
    slide = prs.slides.add_slide(layout)
    lst = prs.slides._sldIdLst; ids = list(lst)
    lst.remove(ids[-1]); lst.insert(index, ids[-1])
    return slide


def finish(prs, footer, page_x, footer_x=0.6):
    """Footer text and page numbers on every slide (creating them on new slides)."""
    for i, slide in enumerate(prs.slides, 1):
        foots = [s for s in slide.shapes if s.has_text_frame and s.text_frame.text.startswith(footer[:12]) and s.top / 914400 > 6.9]
        nums = [s for s in slide.shapes if s.has_text_frame and s.top / 914400 > 6.9 and abs(s.left / 914400 - page_x) < 0.15 and re.fullmatch(r"\d+", s.text_frame.text.strip() or "x")]
        if foots: set_text(foots[0], footer)
        else:
            fx = 6.8 if any(s.shape_type == 13 and s.left == 0 and s.width / 914400 > 5 for s in slide.shapes) else footer_x
            t = tbox(slide, fx, 7.05 if page_x > 11.65 else 7.0, 8.0, 0.3, footer, 9, False, INK2)
            for r in t.text_frame.paragraphs[0].runs: r.font.name = "Consolas"
        if nums: set_text(nums[0], str(i))
        else: tbox(slide, page_x, 7.05 if page_x > 11.65 else 7.0, 1.0, 0.3, str(i), 9, False, INK2, align="r")


# ================================================================== FULL DECK
def update_full():
    prs = Presentation("esp32s3-camera-v1.2.pptx")
    S = prs.slides

    # --- 1 cover
    s = S[0]
    replace_pic(s, one(s, kind="pic"), R("assembled-iso-top.png"))
    set_text(by_text(s, "ESP32-S3 CAMERA · V1.2"), "ESP32-S3 CAMERA · V1.4 · 60 × 85 MM · 4 層 · 含 3D 列印外殼")
    set_text(by_text(s, "零件分工圖、組裝示意"), "零件分工圖、組裝示意、3D 渲染、外殼與採購清單。依實際 PCB 座標整理，對應 2026-09-22 定稿的電路板 v1.4。")
    set_text(by_text(s, "插件三顆"), "插件兩顆")

    # --- 2 version history: 5 cards
    s = S[1]
    set_text(by_text(s, "本頁對應電路板 v1.2"), "本頁對應電路板 v1.4")
    set_text(by_text(s, "2026-09-21 定稿，快照存在"), "2026-09-22 定稿，快照存在專案 versions/v1.4/，含 Gerber、BOM、CPL、ERC/DRC 報告，視為唯讀。v1.2、v1.3 都沒有下單。")
    for a in shapes_at(s, text_prefix="›"): delete(a)
    cards = []
    for cx in (0.60, 4.85, 9.10):
        rc = one(s, x=cx, y=1.90); tt = one(s, x=cx + 0.3, y=2.10); st = one(s, x=cx + 0.3, y=2.80); bd = one(s, x=cx + 0.3, y=3.35)
        cards.append((rc, tt, st, bd))
    W, G = 2.26, 0.20
    def place(card, i):
        rc, tt, st, bd = card; x = 0.60 + i * (W + G)
        move(rc, x, 1.90, W, 3.60); move(tt, x + 0.15, 2.10, W - 0.3); move(st, x + 0.15, 2.80, W - 0.3); move(bd, x + 0.15, 3.35, W - 0.3, 2.0)
    dark = cards[2]
    v14 = tuple(clone(s, sh) for sh in dark)           # copy of the dark "current" card, becomes v1.4
    v13 = tuple(clone(s, sh) for sh in cards[0])       # light card copy, becomes v1.3
    # recolor the old v1.2 card to the light style, copying run colors from card 1
    fill(dark[0], CARD)
    for src, dst in zip(cards[0][1:], dark[1:]):
        c = src.text_frame.paragraphs[0].runs[0].font.color.rgb; recolor(dst, str(c))
    set_text(v13[1], "v1.3"); set_text(v13[2], "螢幕母座")
    set_text(v13[3], ["J5、J6 兩條排針換成 1×7 母座 J5", "1.3 吋 ST7789 螢幕直插，不用杜邦線", "SCL = GPIO44、SDA = GPIO43", "為 3D 列印外殼而改"])
    set_text(v14[1], "v1.4"); set_text(v14[2], "側按快門")
    set_text(v14[3], ["快門 SW3 換成側按式 ALPS SKRTLAE010", "移到上板邊右段 (50.6, 2.6)", "C12 下移、快門線改繞模組下方", "外殼上牆做快門帽"])
    for i, card in enumerate([cards[0], cards[1], dark, v13, v14]): place(card, i)
    set_text(by_text(s, "預覽螢幕為外接"), "v1.3 起螢幕直插板上母座、v1.4 起快門在上板邊側按，兩版都是為了相機式 3D 列印外殼（鏡頭正面、螢幕背面、快門頂邊）而改；外殼見第 14、15 頁。")

    # --- 3 three categories
    s = S[2]
    set_runs(by_text(s, "3  顆插件"), ["2", "  顆插件"])
    set_text(by_text(s, "J4 電池座、J5 UART 排針"), "J4 電池座、J5 1×7 螢幕母座。J4 一定要焊才能接電池，J5 要焊才能插螢幕。")
    set_runs(by_text(s, "6  項板外零件"), ["7", "  項板外零件"])
    set_text(by_text(s, "相機模組、鋰電池、microSD"), "相機模組、1.3 吋螢幕、鋰電池、microSD 卡、USB-C 線、M2×25 螺絲、3D 列印外殼三件。")
    tb = [sh for sh in s.shapes if sh.has_table][0].table
    cell_set(tb.cell(1, 2), "58 顆 SMD + J4、J5 兩顆插件")
    cell_set(tb.cell(2, 1), "買 J4 電池座與 J5 母座回來手焊")
    cell_set(tb.cell(2, 2), "不用買插件，收到板子接電池、插螢幕")

    # --- 4 top view diagram
    s = S[3]
    sw3 = by_text(s, "SW3"); q1 = by_text(s, "Q1")
    move(sw3, 7.23, 1.62, 0.27, 0.16)
    for p in sw3.text_frame.paragraphs:
        for r in p.runs: r.font.size = q1.text_frame.paragraphs[0].runs[0].font.size
    c12 = one(s, x=7.13, y=1.86); move(c12, 7.13, 1.907)
    set_text(by_text(s, "外殼 / 夾具"), "3D 列印外殼")
    set_text(by_text(s, "自製或 3D 列印，固定相機模組"), "相機式兩片殼：鏡頭孔對 (30, 25)，快門帽在上牆，BOOT / RESET 針孔。見第 14、15 頁。")
    set_text(by_text(s, "v1.2 新增：SW4、D5、R20"), "v1.4：SW3 快門移到上板邊")
    set_text(by_text(s, "右上角 SW4 電源滑動開關撥桿突出板邊"), "側按式 ALPS SKRTLAE010，觸桿朝上板邊伸出，由外殼上牆的快門帽按。旁邊仍是 SW4 電源開關與 D5 藍燈。左欄只剩 SW1 BOOT、SW2 RESET。")
    set_line(one(s, x=7.91, y=2.22), 9.20, 3.95, 7.52, 1.72)
    set_text(by_text(s, "四角 Ø2.2 定位孔"), "四角 Ø2.2 定位孔。外殼的 M2×25 螺絲從背面穿過立柱與板子，鎖進前殼。")
    set_text(by_text(s, "M2 螺絲 × 4"), "M2 × 25 螺絲 × 4 → H1–H4")

    # --- 5 bottom view diagram
    s = S[4]
    set_text(by_text(s, "底面 Bottom · B.Cu"), "底面 Bottom · B.Cu · 28 顆 SMD + 2 插件")
    j5 = one(s, x=4.43, y=3.86); j6 = one(s, x=4.43, y=4.71)
    move(j5, 4.466, 3.742, 0.154, 1.079); delete(j6)
    set_text(by_text(s, "J5 UART、J6 擴充排針"), "J5 螢幕母座（插件）")
    set_text(by_text(s, "1×4 2.54 mm。要接螢幕建議用 90°"), "1×7 2.54 mm 立式母座 C225482。螢幕模組自帶的排針直插；腳序 GND 3V3 SCL SDA RES DC BLK，方形 pin 1 靠天線端。")
    set_line(one(s, x=3.90, y=4.63), 3.90, 5.95, 4.47, 4.30)
    set_text(by_text(s, "1.3 吋預覽螢幕（選配）"), "1.3 吋預覽螢幕 → J5")
    set_text(by_text(s, "疊在電池外側、亮面朝外，7 pin"), "直插母座、亮面朝外，身體蓋在電池上方；模組背面離板底 11.0 mm，亮面約 13.9 mm。外殼四支定位柱插進它四角的 Ø2 孔。")
    set_text(by_text(s, "插件，Economic 要自己焊"), "插件，Economic 要自己焊（J4、J5）")

    # --- 6 SMD list
    s = S[5]
    body = by_text(s, "U1 ESP32-S3-WROOM-1-N16R8 模組")
    set_text(body, ["U1 ESP32-S3-WROOM-1-N16R8 模組 C2913202",
                    "U2 AP2112K 3.3V LDO；U5 2.8V、U6 1.2V LDO 供相機",
                    "U3 TP4056 充電；U4 USBLC6 ESD；Q1 Q2 MOSFET",
                    "J1 USB-C 座；J2 24P FPC 座；J3 microSD 座",
                    "SW1 BOOT、SW2 RESET 頂按式；SW3 快門 側按式 ALPS SKRTLAE010 C110293（v1.4）",
                    "SW4 電源滑動開關 C431540；D5 藍色電源燈 C2288",
                    "D1 D2 D4 LED；D3 B5819W C8598",
                    "21 顆電阻、17 顆電容，全部 Basic Part"])
    set_text(by_text(s, "配對頁要看的料號"), "配對頁要看的料號：U1 C2913202（N16R8 模組，可能預購）、D3 C8598（SOD-123，不是 SS14）、SW4 C431540、SW3 C110293（側按快門，不要被換成頂按式）。逐行確認有貨。")
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.top)
    replace_pic(s, pics[0], R("iso-top.png")); replace_pic(s, pics[1], R("closeup-power.png"))
    set_text(by_text(s, "裸板貼片後的頂面"), "裸板貼片後的頂面：兩顆按鍵、FPC 座、上板邊的側按快門、ESP32 模組與天線淨空區")
    set_text(by_text(s, "v1.2 新增的三顆"), "右上角特寫：v1.4 的側按快門 SW3 在上板邊，SW4 電源開關、D5 藍燈在旁邊，一起由 JLCPCB 貼好。")

    # --- 7 THT parts
    s = S[6]
    set_text(by_text(s, "插件三顆：Economic"), "插件兩顆：Economic 自己焊，Standard 由 JLCPCB 焊")
    set_text(by_text(s, "三顆通孔零件"), "兩顆通孔零件")
    tb = [sh for sh in s.shapes if sh.has_table][0].table
    cell_set(tb.cell(2, 1), "螢幕母座 1×7 2.54 mm 立式（CJT A2541WV-7P）"); cell_set(tb.cell(2, 2), "C225482"); cell_set(tb.cell(2, 3), "插 1.3 吋螢幕，v1.3 起")
    table_remove_row(tb, 3)
    set_text(by_text(s, "這三顆會被略過"), "這兩顆會被略過，要自己買回來手焊。J4 一定要焊才能接電池；J5 要焊才能插螢幕，母座買 8.5 mm 高的標準款。")
    set_text(by_text(s, "含插件焊接，這三顆"), "含插件焊接，這兩顆 JLCPCB 會一起焊好，不用自己買。收到板子接上電池、插上螢幕就能開機。")
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.top)
    replace_pic(s, pics[1], R("low-angle.png"))
    set_text(by_text(s, "低角度側視：排針與 JST 座"), "低角度側視：底面的 J5 母座（8.5 mm）是板上最高的插件。")

    # --- 8 off-board parts: 7 rows
    s = S[7]
    set_text(by_text(s, "板外零件 6 項"), "板外零件 7 項：一律自己買")
    rows_y = [1.55, 2.35, 3.15, 3.95, 4.75, 5.55]
    groups = []
    for y in rows_y:
        g = shapes_at(s, y=y + 0.03, tol=0.08) + shapes_at(s, y=y + 0.32, tol=0.05)
        groups.append(g)
    items = [("OV2640 相機模組", "24 pin 0.5 mm 排線，ESP32-CAM 相容", "→ J2"),
             ("1.3 吋 ST7789 螢幕", "IPS 240×240，7 pin 直排針已焊，直插母座", "→ J5"),
             ("3.7V 鋰電池", "JST PH 2.0 插頭，帶保護板", "→ J4"),
             ("microSD 卡", "8–32 GB，Class 10", "→ J3"),
             ("USB-C 線", "要能傳資料，不要只能充電的線", "→ J1"),
             ("M2 × 25 盤頭螺絲 × 4", "從外殼背面鎖穿立柱與板子", "→ H1–H4"),
             ("3D 列印外殼三件", "前殼、後殼、快門帽；STL 在 enclosure/", "")]
    pitch = 0.70
    for i, g in enumerate(groups):
        dy = (1.55 + i * pitch) - rows_y[i]
        for sh in g: move(sh, y=sh.top / 914400 + dy)
    g7 = [clone(s, sh, dy=pitch) for sh in groups[5]]
    for i, g in enumerate(groups + [g7]):
        name, spec, dest = items[i]
        for sh in g:
            t = sh.text_frame.text.strip() if sh.has_text_frame else ""
            if re.fullmatch(r"\d", t): set_text(sh, str(i + 1))
            elif t.startswith("→"): set_text(sh, dest)
            elif sh.has_text_frame and t and abs(sh.top / 914400 - (1.55 + i * pitch)) < 0.1: set_text(sh, name)
            elif sh.has_text_frame and t: set_text(sh, spec)
    note = by_text(s, "相機排線容易折壞"); move(note, y=6.45);
    for sh in shapes_at(s, x=0.60, y=6.35): move(sh, y=6.40)
    replace_pic(s, one(s, kind="pic"), R("assembled-iso-bottom.png"))
    set_text(by_text(s, "組裝完成，底面。603040"), "組裝完成，底面。603040 鋰電池墊泡棉貼在底面中央，黃色膠帶端是保護板；1.3 吋 ST7789 螢幕直接插在右板邊的 J5 母座上、蓋在電池上方；microSD 卡插在 J3。")

    # --- 9 assembled views
    s = S[8]
    set_text(by_text(s, "相機排線插進 J2 後反折"), "相機排線插進 J2 後反折 180° 讓模組貼回板面；microSD 卡插 J3；鋰電池墊在底面；螢幕直插 J5 母座朝外。相機、記憶卡、電池、螢幕與側按快門是依實際尺寸畫的簡化模型，其餘是 KiCad 庫原廠 3D 模型。")
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.left)
    replace_pic(s, pics[0], R("assembled-iso-top.png")); replace_pic(s, pics[1], R("assembled-iso-right.png"))
    set_text(by_text(s, "橘色排線從 J2 出來反折"), "橘色排線從 J2 出來反折，相機模組躺回板面、鏡頭朝上；左欄只剩兩顆鍵，快門在上板邊右段")
    set_text(by_text(s, "從開關那一側看（v1.2）"), "從開關那一側看（v1.4）")
    set_text(by_text(s, "右上角是 SW4 電源開關"), "螢幕模組插在 J5 母座上、蓋在電池上方；右上角 SW4 電源開關撥桿突出板邊，上板邊是側按快門 SW3")

    # --- 10 bottom = user side
    s = S[9]
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.left)
    replace_pic(s, pics[0], R("assembled-bottom.png")); replace_pic(s, pics[1], R("assembled-bottom-low.png"))
    set_text(by_text(s, "螢幕亮面朝外，7 pin 排針邊朝右"), [
        "螢幕模組的 7 pin 直排針插進右板邊的 J5 母座，亮面朝外，沒有任何線。腳序一對一：GND、3V3、SCL (GPIO44)、SDA (GPIO43)、RES (GPIO6)、DC (GPIO5)、BLK (GPIO4)。",
        "模組投影 x 19.3–58.5、y 31.1–58.9；四角 Ø2 孔在 (21.8, 33.6)、(56, 33.6)、(21.8, 56.4)、(56, 56.4)，套進外殼後殼的四支定位柱。",
        "有效顯示區 23.4 × 23.4，中心約 (40.5, 45)，外殼螢幕窗對這裡。"])
    tb = [sh for sh in s.shapes if sh.has_table][0].table
    cell_set(tb.cell(2, 0), "J5 母座 + 模組排針塑膠"); cell_set(tb.cell(2, 1), "8.5 + 2.54 mm")
    cell_set(tb.cell(3, 0), "模組 PCB 背面 → 亮面"); cell_set(tb.cell(3, 1), "11.0 → 約 13.9 mm")
    cell_set(tb.cell(4, 0), "電池頂到模組背面 / 外殼底側內深"); cell_set(tb.cell(4, 1), "3 mm / 14.5 mm")
    set_text(by_text(s, "外殼開孔位置"), "外殼開孔位置：鏡頭 (30, 25) 頂面、快門上板邊 x 47.6–53.6、BOOT / RESET 針孔 (9, 24) (9, 32)、開關右板邊 y 8–14、USB-C 右板邊、記憶卡左板邊、螢幕窗 23.4 × 23.4 中心 (40.5, 45)。")

    # --- 11 camera module position
    s = S[10]
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.left)
    replace_pic(s, pics[0], R("assembled-top.png"))
    p5 = pics[1]; replace_pic(s, p5, R("closeup-shutter.png"), keep_size=False); move(p5, h=3.70 * 952 / 1544)
    set_text(by_text(s, "從開關側看：SW4"), "上板邊右段：側按快門 SW3 觸桿朝板邊，SW4 撥桿突出右板邊，D5 藍燈在旁邊。")
    set_text(by_text(s, "模組落在 x 25.5–34.5"), ["模組落在 x 25.5–34.5、y 20.5–29.5 mm 的空區，鏡頭中心 (30, 25)，外殼鏡頭孔與 Ø16 鏡座環對這個位置。",
                                                 "排線長度不同，落點會前後移；底下墊一塊約 2 mm 厚、8 × 8 mm 的雙面泡棉膠，不再懸出板邊。"])

    # --- 12 bare-board renders
    s = S[11]
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: (round(p.top / 914400, 1), p.left))
    replace_pic(s, pics[0], R("iso-top.png")); replace_pic(s, pics[1], R("iso-bottom.png"))
    replace_pic(s, pics[2], R("top.png")); replace_pic(s, pics[3], R("bottom.png")); replace_pic(s, pics[4], R("low-angle.png"))
    set_text(by_text(s, "只有 JLCPCB 出貨時"), "只有 JLCPCB 出貨時板上會有的零件，沒有板外零件。用 KiCad 10 光線追蹤引擎從 v1.4 板檔輸出。")
    set_text(by_text(s, "頂面立體。相機 FPC 座"), "頂面立體。相機 FPC 座在上緣，快門在上緣右段，模組天線端懸在下方淨空區。")
    set_text(by_text(s, "底面立體。microSD 座"), "底面立體。microSD 座、JST 電池座與 J5 螢幕母座都在這一面。")
    set_text(by_text(s, "低角度側視。排針"), "低角度側視。底面的母座是最高的插件。")

    # --- 13 closeups
    s = S[12]
    set_text(by_text(s, "v1.2 重點特寫"), "v1.4 重點特寫：側按快門、電源開關、USB-C、電池座")
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.left)
    replace_pic(s, pics[0], R("closeup-shutter.png"))
    set_text(by_text(s, "電源開關與電源燈（v1.2）"), ["側按快門與電源開關（v1.4）。SW3 ALPS SKRTLAE010 在上板邊右段 (50.6, 2.6)，觸桿朝板邊伸出，外殼上牆的快門帽壓它；兩個 pad 1 用細線連通，GND 走板邊過孔。",
                                                   "SW4 撥桿朝右板邊，絲印 ON / OFF：撥向板子上緣是 OFF，撥向模組是 ON。D5 藍燈接 3.3V 開機必亮。"])

    # --- 14 purchase A
    s = S[13]
    tb = sorted([sh for sh in s.shapes if sh.has_table], key=lambda t: t.top)
    cell_set(tb[0].table.cell(3, 1), "U1 C2913202（N16R8 模組，可能預購）、D3 C8598（SOD-123，不是 SS14）、SW4 C431540、SW3 C110293（ALPS SKRTLAE010 側按，不要被換成頂按式）")
    cell_set(tb[1].table.cell(2, 0), "J5 2.54 mm 1×7 立式母座（8.5 mm 高）"); cell_set(tb[1].table.cell(2, 1), "LCSC C225482 CJT A2541WV-7P；或 ICShop／蝦皮任何單排母座 2.54 1×7"); cell_set(tb[1].table.cell(2, 2), "螢幕直插用；不要買 90° 或矮款")
    set_text(by_text(s, "採購清單 2026-09-21 整理"), "採購清單 2026-09-23 整理，與 fab/採購清單.md 同步。連結與價格為查詢當日所見，下單前再確認庫存與規格。")
    set_text(by_text(s, "上傳 fab/esp32s3-camera-gerber.zip"), "上傳 fab/JLCPCB-上傳-v1.4/ 內的 gerber zip、BOM、CPL 三個檔。步驟見 fab/JLCPCB-下單清單.md。")

    # --- 15 purchase B
    s = S[14]
    tb = [sh for sh in s.shapes if sh.has_table][0].table
    cell_set(tb.cell(3, 0), "預覽螢幕"); cell_set(tb.cell(3, 1), "通用型 1.3 吋 IPS 240×240 ST7789，7 pin 2.54 mm 直排針已焊，27.78 × 39.22 mm，直插 J5")
    cell_set(tb.cell(3, 3), "替代：ICShop Waveshare 1.3inch LCD（NT$225），腳序不同、不能直插")
    cell_set(tb.cell(4, 0), "快門帽（外殼零件）"); cell_set(tb.cell(4, 1), "3D 列印，T 形，凸緣 7.6 × 4.0 在牆內、頭露出 1 mm"); cell_set(tb.cell(4, 2), "STL 在 enclosure/"); cell_set(tb.cell(4, 3), "放在前殼上牆的窗裡，蓋殼時被 SW3 觸桿與牆夾住")
    cell_set(tb.cell(7, 0), "M2 螺絲"); cell_set(tb.cell(7, 1), "M2 × 25 mm 盤頭 4 支"); cell_set(tb.cell(7, 3), "從後殼沉孔鎖穿立柱與板子，自攻進前殼；螢幕靠定位柱與窗框固定，不用鎖")
    cell_set(tb.cell(9, 0), "外殼前殼、後殼"); cell_set(tb.cell(9, 1), "3D 列印，PLA/PETG，開口朝下印，前殼約 20 g、後殼約 29 g"); cell_set(tb.cell(9, 2), "STL 在 enclosure/")
    cell_set(tb.cell(9, 3), "開孔：鏡頭 (30, 25)、快門上板邊、針孔、開關與 USB-C 右板邊、記憶卡左板邊、螢幕窗 23.4 × 23.4")

    # --- 16 alternatives
    s = S[15]
    set_text(by_text(s, "J2 FH12-24S"), "J2 FH12-24S　J3 DM3AT　J1 USB-C 16P　J4 B2B-PH-K-S　J5 A2541WV-7P　SW3 SKRTLAE010　U1 模組")
    set_text(one(s, x=0.90, y=4.85),
             ["OV2640 相機模組", "3.7V 鋰電池（JST PH 2.0，帶保護板）", "microSD 卡", "USB-C 線（能傳資料）", "Economic 方案再加 J4 電池座；要看畫面再加 1.3 吋螢幕與 J5 母座"])

    # --- 17 next steps
    s = S[16]
    replace_pic(s, one(s, kind="pic"), R("assembled-iso-top.png"))
    set_text(by_text(s, "上傳 Gerber、BOM、CPL；在配對頁"), "上傳 Gerber、BOM、CPL；在配對頁逐行確認 U1、D3、SW3、SW4 有貨；選 Standard 或 Economic。")
    set_text(by_text(s, "相機模組、鋰電池、microSD 卡、USB-C 線；Economic"), "相機模組、1.3 吋螢幕、鋰電池、microSD 卡、USB-C 線、M2×25 螺絲；Economic 再加 J4、J5。同時把外殼三件印出來。")
    set_text(by_text(s, "接電池前先量極性"), "接電池前先量極性（J4 pin 1 = 正極）。排線反折讓模組貼回板面，墊 2 mm 泡棉膠。螢幕插 J5 母座、對到 GND 那格，再裝進外殼。")

    # --- new 14, 15: enclosure
    e1 = add_slide_at(prs, 13)
    title(e1, "3D 列印外殼：相機式兩片殼", "SolidWorks 2024 依板檔座標用腳本建模，組合件放進板子 STEP 做過干涉檢查（0 件）。整組 65 × 90 × 27.6 mm，壁厚 2 mm，外緣 R2.5 倒圓。")
    pic(e1, E("enclosure-exploded.png"), 0.60, 1.65, 6.40)
    pic(e1, E("enclosure-iso.png"), 7.40, 1.65, 5.35)
    tbox(e1, 0.60, 5.70, 6.40, 0.30, "爆炸圖：左前殼（鏡頭面）、中板子、右後殼（螢幕面）", 11, False, INK2)
    tbox(e1, 7.40, 5.05, 5.35, 0.30, "合起來：頂邊小方塊是快門帽，右側牆是開關槽與 USB-C 窗", 11, False, INK2)
    for i, (hd, bd) in enumerate([("前殼 · 鏡頭面", "Ø10 鏡頭孔加 Ø16 凸 1.5 mm 鏡座環；上牆快門窗與 T 形快門帽；BOOT / RESET Ø2 針孔；三個 LED 導光孔；左側握持溝紋；右側牆 USB-C 窗、開關槽加指窪。"),
                                 ("後殼 · 螢幕面", "24.5 × 24.5 螢幕窗外一層 0.8 mm 內縮邊框；左側牆記憶卡槽；四支 Ø5 立柱撐板子；四支 Ø4 定位柱、頂端 Ø1.8 凸柱插進螢幕四角孔。"),
                                 ("固定與尺寸", "四支 M2 × 25 從後殼沉孔鎖穿立柱與板子，自攻進前殼；後殼唇口對進前殼凹槽。前殼內高 7 mm，後殼內深 14.5 mm；螢幕亮面離板底 13.9 mm。")]):
        x = 0.60 + i * 4.10
        rect(e1, x, 6.05 - 0.05, 3.90, 0.95 + 0.05)
        sq = square(e1, x + 0.15, 6.10, [TEAL, PINK, AMBER][i], 0.18)
        tbox(e1, x + 0.42, 6.05, 3.35, 0.28, hd, 12, True, INK)
        tbox(e1, x + 0.15, 6.36, 3.60, 0.64, bd, 9, False, INK2, space_after=0)
    e2 = add_slide_at(prs, 14)
    title(e2, "外殼各面，與怎麼印", "灰藍色渲染是 SolidWorks 組合件的標準視角；STL、SLDPRT、尺寸依據表在專案 enclosure/，改尺寸改腳本參數重跑即可。")
    views = [("enclosure-lens-side.png", "鏡頭面", "Ø10 鏡頭孔對 (30, 25)，外圈鏡座環；左欄兩個 Ø2 針孔是 RESET、BOOT；上方三個小孔透 D4 白、D1 綠，右上透 D5 藍。"),
             ("enclosure-screen-side.png", "螢幕面", "24.5 × 24.5 螢幕窗壓在模組玻璃邊上、內側貼 0.5 mm 泡棉；四角是 M2 螺絲頭沉孔；左上小孔透 D2 紅色充電燈。"),
             ("enclosure-right-usb-switch.png", "右側牆", "上：電源開關槽 y 7–15 加 1 mm 深指窪，撥桿只伸出板邊 0.7 mm 所以牆要薄；下：USB-C 窗 y 18.75–29.25、高 4.2 mm。"),
             ("enclosure-left-sd.png", "左側牆", "記憶卡槽在分模線下方的後殼上，卡插到底仍露出殼外 2 mm 好拔。")]
    for i, (f, hd, bd) in enumerate(views):
        x = 0.60 + i * 3.075
        pic(e2, E(f), x, 1.65, 2.90)
        tbox(e2, x, 3.55, 2.90, 0.30, hd, 13, True, INK)
        tbox(e2, x, 3.88, 2.90, 1.10, bd, 9.5, False, INK2, space_after=0)
    rect(e2, 0.60, 5.10, 12.10, 1.75)
    square(e2, 0.85, 5.30, SHELL, 0.20)
    tbox(e2, 1.15, 5.25, 11.30, 0.30, "列印方向：兩片殼都開口朝下、外面朝上", 13, True, INK)
    tbox(e2, 0.85, 5.62, 11.60, 1.20, [
        "外緣有 R2.5 倒圓，外面朝下印會讓圓角從近乎水平開始一層層外擴、表面很糙；翻過來讓圓角像圓頂往上收就沒有懸空，鏡座環、溝紋、螢幕邊框也都落在最上面那一面。",
        "代價是殼內柱子變成從天花板往下長：前殼四支柱離床 2 mm，後殼立柱離床 1.6 mm、螢幕定位柱離床 12.6 mm。切片選「只在列印床上生成支撐」加樹狀支撐，支撐只會長在柱子下面。",
        "各牆上的窗與槽都是垂直面上的橋接，不用支撐；快門帽凸緣朝下印。PLA / PETG 皆可，層高 0.2 mm、壁 3 圈；前殼約 20 g、後殼約 29 g。"], 9.5, False, INK2, space_after=3)

    finish(prs, FOOTER_FULL, page_x=11.70)
    prs.save("esp32s3-camera-v1.4.pptx"); print("saved esp32s3-camera-v1.4.pptx", len(prs.slides), "slides")


# ================================================================== SIMPLE DECK
def update_simple():
    prs = Presentation("esp32s3-camera-v1.2-簡易版.pptx")
    S = prs.slides

    s = S[0]
    replace_pic(s, one(s, kind="pic"), R("assembled-iso-top.png"))
    set_text(by_text(s, "第 1.2 版"), "第 1.4 版 · 2026 年 9 月")
    set_text(by_text(s, "手掌大小、可以裝電池"), "手掌大小、可以裝電池、拍完存進記憶卡，還有一個 3D 列印的相機外殼。這份簡報用最少的專業名詞，說明它是什麼、要買什麼、怎麼組起來。")

    s = S[1]
    set_text(by_text(s, "板上插一顆小鏡頭，按一下快門鍵"), "板上插一顆小鏡頭，按一下頂邊的快門就拍。")
    set_text(by_text(s, "可以加小螢幕（選配）"), "有小螢幕")
    set_text(by_text(s, "外接一片 1.3 吋螢幕"), "背面插一片 1.3 吋螢幕，拍之前先看畫面。")
    p = one(s, kind="pic"); replace_pic(s, p, R("closeup-power.png"), keep_size=False); move(p, h=5.00 * 952 / 1544)
    set_text(by_text(s, "板子右上角是電源開關"), "板子右上角：頂邊那顆是快門，旁邊是電源開關和藍色電源燈，下面是 USB-C 充電孔。")

    s = S[2]
    replace_pic(s, one(s, kind="pic"), R("assembled-top.png"))
    set_text(by_text(s, "鏡頭朝這一面，四個角有螺絲孔"), "鏡頭朝這一面。快門在板子頂邊，四個角有螺絲孔鎖進外殼。")
    set_text(by_text(s, "三顆按鍵"), "兩顆小鍵")
    set_text(by_text(s, "上面兩顆是開發用的"), "這兩顆是開發用的，平常不用碰；快門不在這裡。")
    # right column: shutter / power switch / USB-C
    set_text(by_text(s, "電源開關"), "快門"); set_text(by_text(s, "往上撥關機、往下撥開機"), "板子頂邊右側一顆側面按的小開關，裝進外殼後從頂邊按，就像真的相機。")
    set_text(by_text(s, "USB-C 孔"), "電源開關"); set_text(by_text(s, "跟現在的手機一樣的接頭"), "右邊板邊的小撥桿，往上撥關機、往下撥開機，板上印了 ON / OFF。")
    set_text(by_text(s, "擴充排針"), "USB-C 孔"); set_text(by_text(s, "右邊兩排金色小孔"), "跟現在的手機一樣的接頭，用來充電和把程式燒進去。")
    set_line(one(s, x=8.38, y=2.50), 9.30, 2.45, 7.90, 1.98)
    set_line(one(s, x=8.50, y=3.33), 9.30, 4.10, 8.42, 2.55)
    set_line(one(s, x=8.38, y=4.91), 9.30, 5.60, 8.45, 3.35)

    s = S[3]
    replace_pic(s, one(s, kind="pic"), R("assembled-bottom.png"))
    set_text(by_text(s, "電池貼在背面中間，螢幕再疊在電池上"), "電池貼在背面中間，螢幕插在右邊的插座上、蓋在電池上方。這一面是使用的時候朝著自己的那一面。")
    set_text(by_text(s, "小螢幕（選配）"), "小螢幕")
    set_text(by_text(s, "1.3 吋正方形螢幕，蓋在電池上面"), "1.3 吋正方形螢幕，自帶的七支針直接插進板子右邊那排插座，不用接線。")

    s = S[4]
    set_text(by_text(s, "把設計圖做成 4 層的電路板"), ["把設計圖做成 4 層的電路板", "把 58 顆小零件焊上去（最小的比米粒還小，人手焊不了）", "焊好寄回來，收到就是一塊完整的板子", "選「含插件」方案的話，電池插座和螢幕插座也會一起焊好"])
    set_text(by_text(s, "另外買鏡頭、電池、記憶卡"), ["另外買鏡頭、螢幕、電池、記憶卡、USB 線", "把鏡頭的排線插上、螢幕插上、電池貼上、記憶卡插入", "把程式燒進板子", "3D 列印外殼三件（設計圖已經畫好），鎖四支螺絲", "想改東西可以再改，所有檔案都在專案裡"])
    set_text(by_text(s, "全部不需要焊接"), "全部不需要焊接，除非選了「只焊小零件」的便宜方案，那兩顆插座要自己焊。")

    s = S[5]
    set_text(by_text(s, "板子本身不含這些。前四項是必要的"), "板子本身不含這些。前五項是必要的，最後一項是外殼相關。")
    set_text(by_text(s, "小螢幕（選配）"), "小螢幕")
    set_text(by_text(s, "1.3 吋 IPS 240×240，ST7789，7 針焊接式。加 7 條"), "1.3 吋 IPS 240×240，ST7789，7 針直排針已焊好那種。直接插板子，不用線。")
    set_text(by_text(s, "螺絲、泡棉膠、外殼（選配）"), "螺絲、泡棉膠、外殼")
    set_text(by_text(s, "M2 螺絲和銅柱 4 組"), "M2 × 25 螺絲 4 支、2 mm 厚雙面泡棉膠、3D 列印外殼三件（前殼、後殼、快門帽）。")
    set_text(by_text(s, "看外殼"), "外殼自己印")

    s = S[6]
    pics = sorted(shapes_at(s, kind="pic"), key=lambda p: p.left)
    replace_pic(s, pics[1], R("assembled-iso-bottom.png"))
    set_text(by_text(s, "貼電池、插記憶卡"), "貼電池、插螢幕、插記憶卡")
    set_text(by_text(s, "電池用泡棉膠貼在背面中間"), "電池用泡棉膠貼在背面中間，插頭插進白色小座，插之前先確認紅線對到有 L 形記號那一邊。螢幕的七支針對準右邊那排插座插到底。記憶卡從左邊推進去。")
    set_text(by_text(s, "接上 USB-C 線，把開關往下撥"), "接上 USB-C 線，把開關往下撥，藍燈亮就是開機了。第一次先不要接電池，確認燈會亮再說。都好了再裝進外殼、鎖四支螺絲。")

    s = S[8]
    p = one(s, kind="pic"); replace_pic(s, p, E("enclosure-iso.png"), keep_size=False); set_crop(p, 0.242, 0, 0.242, 0)
    set_text(by_text(s, "製作加運送大約兩到三週"), "製作加運送大約兩到三週。這段時間把鏡頭、螢幕、電池、記憶卡買齊，外殼三件印出來。")
    set_text(by_text(s, "照前面三步組起來"), "照前面三步組起來，接 USB 看藍燈亮，再裝進外殼。")

    # new slide before the last one: the enclosure
    e = add_slide_at(prs, 8)
    tbox(e, 0.70, 0.50, 12.0, 0.80, "外殼長這樣", 30, True, INK)
    tbox(e, 0.70, 1.30, 12.0, 0.50, "兩片殼夾住板子，鏡頭在正面、螢幕在背面、快門在頂邊，像一台小相機。用 3D 列印機印出來就好。", 13, False, INK2)
    pic(e, E("enclosure-exploded.png"), 0.70, 1.95, 6.30)
    pic(e, E("enclosure-iso.png"), 7.20, 1.95, 5.40)
    tbox(e, 0.70, 5.95, 6.30, 0.30, "拆開看：前殼、板子、後殼", 11, False, INK2)
    tbox(e, 7.20, 5.35, 5.40, 0.30, "合起來：頂邊那顆就是快門", 11, False, INK2)
    for i, (hd, bd, col) in enumerate([("三件", "前殼、後殼、快門帽，塑膠印的，四支小螺絲從背面鎖起來。", TEAL),
                                       ("看得到的孔", "正面鏡頭孔和兩個針孔，頂邊快門，右邊開關和充電孔，左邊記憶卡口，背面螢幕窗。", PINK),
                                       ("尺寸", "65 × 90 × 27.6 mm，差不多一張名片的長寬、三根手指的厚度。", AMBER)]):
        x = 0.70 + i * 4.05
        rect(e, x, 6.30, 3.85, 0.62)
        square(e, x + 0.15, 6.42, col, 0.18)
        tbox(e, x + 0.42, 6.34, 1.2, 0.26, hd, 12, True, INK)
        tbox(e, x + 1.55, 6.34, 2.20, 0.58, bd, 9, False, INK2, space_after=0)

    finish(prs, FOOTER_SIMPLE, page_x=11.60, footer_x=0.7)
    prs.save("esp32s3-camera-v1.4-簡易版.pptx"); print("saved esp32s3-camera-v1.4-簡易版.pptx", len(prs.slides), "slides")


if __name__ == "__main__":
    update_full()
    update_simple()

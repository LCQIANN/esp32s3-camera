# -*- coding: utf-8 -*-
"""2026-09-23: the display is connected to J5 with seven male-female Dupont jumpers instead of being
plugged in, and the back shell grew to 27 mm. Edit both v1.4 decks in place to match (text, tables,
re-rendered enclosure pictures, one new slide in the full deck).

    python tools/update_decks_dupont.py
Then tools/export_decks.py for the PDFs.
"""
import importlib.util, os
spec = importlib.util.spec_from_file_location("ud", os.path.join(os.path.dirname(__file__), "update_decks_v14.py"))
ud = importlib.util.module_from_spec(spec); spec.loader.exec_module(ud)
from pptx import Presentation
E, R = ud.E, ud.R
one, by_text, set_text, replace_pic, cell_set, shapes_at = ud.one, ud.by_text, ud.set_text, ud.replace_pic, ud.cell_set, ud.shapes_at
tbox, pic, rect, square, title = ud.tbox, ud.pic, ud.rect, ud.square, ud.title
INK, INK2, TEAL, PINK, AMBER = ud.INK, ud.INK2, ud.TEAL, ud.PINK, ud.AMBER


def table_of(slide):
    t = [s for s in slide.shapes if s.has_table]; assert len(t) == 1; return t[0].table


def pic_at(slide, x, y=None):
    return one(slide, x=x, y=y, kind="pic")


# ================================================================== FULL DECK
prs = Presentation("esp32s3-camera-v1.4.pptx"); S = prs.slides; assert len(S) == 20

s = S[1]   # version history
set_text(by_text(s, "J5、J6 兩條排針換成 1×7 母座 J5"), ["J5、J6 兩條排針換成 1×7 母座 J5", "1.3 吋 ST7789 螢幕直插（09-23 改為杜邦線接）", "SCL = GPIO44、SDA = GPIO43", "為 3D 列印外殼而改"])
set_text(by_text(s, "v1.3 起螢幕直插板上母座"), "v1.3 起板上有螢幕母座、v1.4 起快門在上板邊側按，兩版都是為了相機式 3D 列印外殼（鏡頭正面、螢幕背面、快門頂邊）而改。2026-09-23 螢幕改用七條公–母杜邦線接母座（省事、不焊），後殼因此加深到 27 mm 內深；外殼見第 14–17 頁。")

s = S[2]
set_text(by_text(s, "相機模組、1.3 吋螢幕、鋰電池、microSD 卡、USB-C 線、M2×25"), "相機模組、1.3 吋螢幕與 7 條公–母杜邦線、鋰電池、microSD 卡、USB-C 線、M2×35 與 M2×4 螺絲、3D 列印外殼三件。")
cell_set(table_of(s).cell(2, 2), "不用買插件，收到板子接電池、接螢幕")

s = S[3]
set_text(by_text(s, "M2 × 25 螺絲 × 4"), "M2 × 35 螺絲 × 4 → H1–H4")
set_text(by_text(s, "四角 Ø2.2 定位孔。外殼的 M2×25"), "四角 Ø2.2 定位孔。外殼的 M2×35 螺絲從背面穿過立柱與板子，鎖進前殼。")

s = S[4]
set_text(by_text(s, "1×7 2.54 mm 立式母座 C225482"), "1×7 2.54 mm 立式母座 C225482。螢幕用七條公–母杜邦線接過來，公頭插這裡；腳序 GND 3V3 SCL SDA RES DC BLK，方形 pin 1 靠天線端。")
set_text(by_text(s, "直插母座、亮面朝外"), "七條公–母杜邦線接 J5、亮面朝外；模組用 M2×4 鎖在後殼四支矮柱上、蓋在電池上方，背面離板底 23.6 mm，亮面約 26.4 mm。")

s = S[6]
cell_set(table_of(s).cell(2, 3), "接 1.3 吋螢幕的杜邦線，v1.3 起")
set_text(by_text(s, "這兩顆會被略過"), "這兩顆會被略過，要自己買回來手焊。J4 一定要焊才能接電池；J5 要焊才能接螢幕，母座買 8.5 mm 高的標準款。")
set_text(by_text(s, "含插件焊接，這兩顆 JLCPCB"), "含插件焊接，這兩顆 JLCPCB 會一起焊好，不用自己買。收到板子接上電池、接上螢幕就能開機。")

s = S[7]
set_text(by_text(s, "IPS 240×240，7 pin 直排針已焊，直插母座"), "IPS 240×240，7 pin 直排針已焊；加 7 條公–母杜邦線接 J5")
set_text(by_text(s, "M2 × 25 盤頭螺絲 × 4"), "M2 × 35 盤頭螺絲 × 4，M2 × 4 × 4")
set_text(by_text(s, "從外殼背面鎖穿立柱與板子"), "M2×35 從外殼背面鎖穿；M2×4 把螢幕鎖在後殼上")
set_text(by_text(s, "組裝完成，底面。603040"), "組裝完成，底面（v1.3 直插版渲染）。603040 鋰電池墊泡棉貼在底面中央，黃色膠帶端是保護板；螢幕現在改用七條杜邦線接右板邊的 J5 母座，模組移到中央、鎖在後殼上；microSD 卡插在 J3")

s = S[8]
set_text(by_text(s, "相機排線插進 J2 後反折 180°"), "相機排線插進 J2 後反折 180° 讓模組貼回板面；microSD 卡插 J3；鋰電池墊在底面；螢幕接 J5 朝外（渲染為直插版，現改用杜邦線）。相機、記憶卡、電池、螢幕與側按快門是依實際尺寸畫的簡化模型，其餘是 KiCad 庫原廠 3D 模型。")
set_text(by_text(s, "螢幕模組插在 J5 母座上、蓋在電池上方；右上角"), "螢幕模組蓋在電池上方（此圖為直插版）；右上角 SW4 電源開關撥桿突出板邊，上板邊是側按快門 SW3")

s = S[9]
set_text(by_text(s, "螢幕模組的 7 pin 直排針插進右板邊的 J5 母座"), [
    "螢幕亮面朝外，2026-09-23 起用七條公–母杜邦線接右板邊的 J5 母座（左圖仍是直插版渲染）。腳序一對一：GND、3V3、SCL (GPIO44)、SDA (GPIO43)、RES (GPIO6)、DC (GPIO5)、BLK (GPIO4)。",
    "杜邦線版模組移到 x 10.4–49.6、y 31.1–58.9，排針那排朝左；四角 Ø2 孔在 (12.9, 33.6)、(47.1, 33.6)、(12.9, 56.4)、(47.1, 56.4)，用 M2×4 鎖在後殼矮柱上"])
t = table_of(s)
cell_set(t.cell(2, 0), "J5 母座 + 杜邦公頭膠殼"); cell_set(t.cell(2, 1), "8.5 + 14 mm")
cell_set(t.cell(3, 1), "23.6 → 約 26.4 mm")
cell_set(t.cell(4, 0), "電池底到模組背面 / 外殼底側內深"); cell_set(t.cell(4, 1), "15.6 mm / 27 mm")
set_text(by_text(s, "外殼開孔位置：鏡頭 (30, 25) 頂面"), "外殼開孔位置：鏡頭 (30, 25) 頂面、快門上板邊 x 47.6–53.6、BOOT / RESET 針孔 (9, 24) (9, 32)、開關右板邊 y 8–14、USB-C 右板邊、記憶卡左板邊、螢幕窗 23.4 × 23.4 中心 (28.4, 45)。")

s = S[13]  # enclosure overview
set_text(by_text(s, "SolidWorks 2024 依板檔座標用腳本建模"), "SolidWorks 2024 依板檔座標用腳本建模，組合件放進板子 STEP 與相機模組、電池、記憶卡、螢幕、杜邦線的簡化模型做過干涉檢查（0 件）。整組 65 × 90 × 40.1 mm，壁厚 2 mm，外緣 R2.5 倒圓。")
replace_pic(s, pic_at(s, 0.60, 1.65), E("enclosure-exploded.png"))
replace_pic(s, pic_at(s, 7.40, 1.65), E("enclosure-iso.png"))
set_text(by_text(s, "24.5 × 24.5 螢幕窗外一層 0.8 mm 內縮邊框"), "24.5 × 24.5 螢幕窗（中心 (28.4, 45)）外一層 0.8 mm 內縮邊框；左側牆記憶卡槽；四支 Ø5 立柱撐板子；四支 Ø4.5 矮柱，螢幕四角用 M2×4 鎖上。")
set_text(by_text(s, "四支 M2 × 25 從後殼沉孔鎖穿"), "四支 M2 × 35 從後殼沉孔鎖穿立柱與板子，自攻進前殼；後殼唇口對進前殼凹槽。前殼內高 8 mm，後殼內深 27 mm（給 J5 上的杜邦公頭膠殼）；螢幕亮面離板底 26.4 mm。")

s = S[14]  # enclosure views + printing
for x, f in ((0.60, "enclosure-lens-side.png"), (3.67, "enclosure-screen-side.png"), (6.75, "enclosure-right-usb-switch.png"), (9.82, "enclosure-left-sd.png")):
    replace_pic(s, pic_at(s, x, 1.65), E(f))
set_text(by_text(s, "外緣有 R2.5 倒圓，外面朝下印"), [
    "外緣有 R2.5 倒圓，外面朝下印會讓圓角從近乎水平開始一層層外擴、表面很糙；翻過來讓圓角像圓頂往上收就沒有懸空，鏡座環、溝紋、螢幕邊框也都落在最上面那一面。",
    "代價是殼內柱子變成從天花板往下長：前殼四支柱離床 2 mm，後殼立柱離床 1.6 mm、四支 2.2 mm 高的螢幕矮柱離床 26.4 mm。切片選「只在列印床上生成支撐」加樹狀支撐，支撐只會長在柱子下面。",
    "各牆上的窗與槽都是垂直面上的橋接，不用支撐；快門帽凸緣朝下印。PLA / PETG 皆可，層高 0.2 mm、壁 3 圈；前殼約 20 g、後殼約 40 g（牆高 31 mm）。"])

s = S[15]  # fit checks
set_text(by_text(s, "相機模組與反折排線、電池與電池線、記憶卡、螢幕模組都依文件尺寸"), "相機模組與反折排線、電池與電池線、記憶卡、螢幕模組、七條杜邦線都依文件尺寸建成簡化模型放進 SolidWorks 組合件，和兩片殼一起跑干涉檢查：0 件。殼拿掉或調半透明拍的。")
replace_pic(s, pic_at(s, 0.60, 1.70), E("fit-front-open-iso.png"))
replace_pic(s, pic_at(s, 4.70, 1.70), E("fit-back-open.png"))
replace_pic(s, pic_at(s, 8.80, 1.70), E("fit-ghost-back.png"))
set_text(by_text(s, "藍色螢幕模組插在 J5 母座上"), "藍色螢幕模組鎖在後殼矮柱的高度、蓋在銀色電池上方，紅色是七條杜邦線的膠殼與線束；電池線從尾端繞到 J4 插頭；記憶卡從左板邊露出，正好穿過後殼的卡槽。")
set_text(by_text(s, "看穿前殼：鏡頭穿出鏡座環"), "看穿前殼：鏡頭穿出鏡座環、快門帽坐在上牆的窗裡對著開關觸桿、四支柱子壓在板子四角。後殼四支矮柱則頂住螢幕四角，M2×4 鎖住。")
set_text(by_text(s, "電池底下的泡棉（會包住 1.3 mm 高的零件"), "電池底下的泡棉（會包住 1.3 mm 高的零件，放進去只會報假警報）、插在 J4 裡的插頭本體、插在 J3 裡的卡身、膠殼與母座裡的針腳、杜邦線多出來的長度。相機鏡座原本只離天花板 0.1 mm，所以前殼內高從 7 改成 8 mm。")

# ---- new slide 17: the Dupont wiring
s = ud.add_slide_at(prs, 16)
title(s, "螢幕改用杜邦線：線怎麼走，殼為什麼變厚", "2026-09-23 決定不焊、直接用市售公–母杜邦線接螢幕。膠殼 14 mm 長，是後殼從 14.5 加深到 27 mm 內深的原因；紅色是七條線的膠殼與線束的簡化模型。")
pic(s, E("fit-cable-back.png"), 0.60, 1.65, 6.40)
pic(s, E("fit-cable-right.png"), 7.40, 1.65, 5.35)
tbox(s, 0.60, 5.70, 6.40, 0.30, "後殼與螢幕都拿掉：母頭在左、公頭站在右邊的 J5 母座上，線走電池底下", 11, False, INK2)
tbox(s, 7.40, 5.05, 5.35, 0.30, "右側視：公頭膠殼到板底下 22.5 mm，螢幕吊在更深處", 11, False, INK2)
for i, (hd, bd, col) in enumerate([
        ("怎麼接", "七條公–母杜邦線：公頭插 J5 母座、母頭套模組排針，腳序一對一，GND 對 GND，不用焊。模組改鎖在後殼四支矮柱上（M2×4），排針那排朝左。", TEAL),
        ("線怎麼走", "母頭朝板子伸 16.5 mm，線 S 彎後走電池底下 0.7 mm 的縫到模組右邊，沿模組邊下去、從底下繞進 J5 上的公頭；多出來的線盤在模組右邊。", PINK),
        ("代價", "公頭膠殼 14 mm 站在 8.5 mm 母座上，線再彎出來 3.5：後殼內深 14.5 → 27 mm，整機 28.6 → 40.1 mm，外殼螺絲 M2×25 → M2×35。", AMBER)]):
    x = 0.60 + i * 4.10
    rect(s, x, 6.00, 3.90, 1.00)
    square(s, x + 0.15, 6.10, col, 0.18)
    tbox(s, x + 0.42, 6.05, 3.35, 0.28, hd, 12, True, INK)
    tbox(s, x + 0.15, 6.36, 3.60, 0.64, bd, 9, False, INK2, space_after=0)

s = S[17]  # was 17: shopping A (two tables; the second one lists the through-hole parts)
tb = sorted([sh for sh in s.shapes if sh.has_table], key=lambda sh: sh.top)
assert len(tb) == 2 and tb[1].table.cell(2, 0).text.startswith("J5")
cell_set(tb[1].table.cell(2, 2), "接螢幕的杜邦公頭插這裡；不要買 90° 或矮款")

s = S[18]  # was 18: shopping B
t = table_of(s)
cell_set(t.cell(3, 1), "通用型 1.3 吋 IPS 240×240 ST7789，7 pin 2.54 mm 直排針已焊，27.78 × 39.22 mm；加 7 條公–母 10 cm 杜邦線接 J5")
cell_set(t.cell(3, 3), "替代：ICShop Waveshare 1.3inch LCD（NT$225），腳序不同，用它附的線接")
cell_set(t.cell(7, 1), "M2 × 35 盤頭 4 支 + M2 × 4 盤頭 4 支")
cell_set(t.cell(7, 3), "M2×35 從後殼沉孔鎖穿立柱與板子，自攻進前殼；M2×4 把螢幕鎖在後殼矮柱上")
cell_set(t.cell(9, 1), "3D 列印，PLA/PETG，開口朝下印，前殼約 20 g、後殼約 40 g")
cell_set(t.cell(9, 3), "開孔：鏡頭 (30, 25)、快門上板邊、針孔、開關與 USB-C 右板邊、記憶卡左板邊、螢幕窗 23.4 × 23.4 中心 (28.4, 45)；後殼內深 27 mm")

s = S[19]
set_text(one(s, x=0.90, y=4.85, text_prefix="OV2640 相機模組"), ["OV2640 相機模組", "3.7V 鋰電池（JST PH 2.0，帶保護板）", "microSD 卡", "USB-C 線（能傳資料）", "Economic 方案再加 J4 電池座；要看畫面再加 1.3 吋螢幕、7 條公–母杜邦線與 J5 母座"])

s = S[20]
set_text(by_text(s, "相機模組、1.3 吋螢幕、鋰電池、microSD 卡、USB-C 線、M2×25"), "相機模組、1.3 吋螢幕與 7 條公–母杜邦線、鋰電池、microSD 卡、USB-C 線、M2×35 與 M2×4 螺絲；Economic 再加 J4、J5。同時把外殼三件印出來。")
set_text(by_text(s, "接電池前先量極性"), "接電池前先量極性（J4 pin 1 = 正極）。排線反折讓模組貼回板面，墊 2 mm 泡棉膠。螢幕鎖在後殼上、用杜邦線接 J5（GND 對 GND），再蓋上前殼。")

ud.finish(prs, ud.FOOTER_FULL, page_x=11.70)
prs.save("esp32s3-camera-v1.4.pptx"); print("full deck:", len(prs.slides), "slides")

# ================================================================== SIMPLE DECK
prs = Presentation("esp32s3-camera-v1.4-簡易版.pptx"); S = prs.slides; assert len(S) == 11

set_text(by_text(S[1], "背面插一片 1.3 吋螢幕"), "背面有一片 1.3 吋螢幕，用七條現成的線接到板子，拍之前先看畫面。")

s = S[3]
set_text(by_text(s, "電池貼在背面中間，螢幕插在右邊的插座上"), "電池貼在背面中間，螢幕用七條杜邦線接到右邊的插座、鎖在殼上，蓋在電池上方。這一面是使用的時候朝著自己的那一面。")
set_text(by_text(s, "1.3 吋正方形螢幕，自帶的七支針"), "1.3 吋正方形螢幕，用七條現成的杜邦線接到板子右邊那排插座，不用焊。")

s = S[4]
set_text(by_text(s, "另外買鏡頭、螢幕、電池、記憶卡"), ["另外買鏡頭、螢幕、杜邦線、電池、記憶卡、USB 線", "把鏡頭的排線插上、螢幕用杜邦線接上、電池貼上、記憶卡插入", "把程式燒進板子", "3D 列印外殼三件（設計圖已經畫好），鎖螺絲", "想改東西可以再改，所有檔案都在專案裡"])

s = S[5]
set_text(by_text(s, "1.3 吋 IPS 240×240，ST7789，7 針直排針已焊好那種"), "1.3 吋 IPS 240×240，ST7789，7 針直排針已焊好那種。另外買 7 條公對母的杜邦線接到板子，不用焊。")
set_text(by_text(s, "M2 × 25 螺絲 4 支"), "M2 × 35 螺絲 4 支（殼）、M2 × 4 螺絲 4 支（螢幕）、2 mm 厚雙面泡棉膠、3D 列印外殼三件（前殼、後殼、快門帽）。")

s = S[6]
set_text(by_text(s, "貼電池、插螢幕、插記憶卡"), "貼電池、接螢幕、插記憶卡")
set_text(by_text(s, "電池用泡棉膠貼在背面中間，插頭插進白色小座"), "電池用泡棉膠貼在背面中間，插頭插進白色小座，插之前先確認紅線對到有 L 形記號那一邊。螢幕用七條杜邦線接到右邊那排插座，同名對同名（GND 對 GND）。記憶卡從左邊推進去。")

s = S[8]
replace_pic(s, pic_at(s, 0.70, 1.95), E("enclosure-exploded.png"))
replace_pic(s, pic_at(s, 7.20, 1.95), E("enclosure-iso.png"))
set_text(by_text(s, "65 × 90 × 28.6 mm"), "65 × 90 × 40 mm，差不多一張名片的長寬、四根手指的厚度。厚是因為螢幕用杜邦線接，線頭要有地方放。")

s = S[9]
replace_pic(s, pic_at(s, 0.70, 1.95), E("fit-front-open-iso.png"))
replace_pic(s, pic_at(s, 6.80, 1.95), E("fit-back-open.png"))
set_text(by_text(s, "把鏡頭、排線、電池、記憶卡、螢幕都放進電腦模型"), "把鏡頭、排線、電池、記憶卡、螢幕和接螢幕的杜邦線都放進電腦模型裡試裝過，什麼都沒有卡到。這兩張是把殼拿掉一半看裡面。")
set_text(by_text(s, "背面那片殼拿掉：螢幕插在插座上"), "背面那片殼拿掉：紅色是接螢幕的杜邦線，螢幕鎖在殼上、蓋在電池上面")
set_text(by_text(s, "螢幕的針直接插進板子右邊的插座"), "螢幕用七條杜邦線接到板子右邊的插座、鎖在殼上；電池夾在板子和螢幕之間，線也走那裡。")

s = S[10]
replace_pic(s, one(s, kind="pic"), E("enclosure-iso.png"))

ud.finish(prs, ud.FOOTER_SIMPLE, page_x=11.60, footer_x=0.7)
prs.save("esp32s3-camera-v1.4-簡易版.pptx"); print("simple deck:", len(prs.slides), "slides")

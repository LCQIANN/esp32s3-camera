# JLCPCB PCBA 下單步驟清單 — ESP32-S3 Camera v1.3

v1.3（2026-09-21 晚）：J5、J6 兩條 1×4 排針拆掉，換成一個 1×7 母座 J5（C225482）讓 1.3 吋螢幕直插。SMD 58 顆與 v1.2 完全相同，CPL 相同；插件只剩 J4、J5 兩顆。
v1.2（同日白天）新增電源滑動開關 SW4、EN 上拉 R21、藍色電源燈 D5 與限流 R20，並補了 J2.23、C3.2 兩顆 GND 過孔；v1.2 未下單。

日期：2026-09-21。對應檔案都在 `fab/`。

---

## 0. 上傳前（KiCad 內，約 10 分鐘）

- [ ] 開啟專案，Schematic → Tools → Update Symbols from Library，清掉 U5/U6 的兩個符號庫警告
- [ ] Tools → Update PCB from Schematic，確認 0 差異（2026-09-21 22:20 以 kicad-cli 驗過為 0）
- [ ] pcbnew 跑 DRC，確認 0 錯誤、0 未連接（2026-09-21 22:20 為 0/0/0；若出現任何 unconnected，不要當敷銅碎片忽略，見 DESIGN.md 第 3 節）
- [ ] **若上面任何一步改到板子**，重新輸出 Gerber、鑽孔、CPL 並重新打包 zip；沒改就直接用現有的 `fab/` 檔案
- [ ] 確認三個要上傳的檔案存在：
  - `fab/esp32s3-camera-gerber.zip`
  - `fab/esp32s3-camera-bom.csv`（含 LCSC Part # 欄）
  - `fab/esp32s3-camera-cpl.csv`

---

## 1. 上傳 Gerber，設定 PCB 規格

前往 jlcpcb.com → Order Now → Add Gerber File，上傳 `esp32s3-camera-gerber.zip`。

檢查預覽：
- [ ] 層數自動辨識為 **4 層**
- [ ] 尺寸約 **60 × 85 mm**
- [ ] 外形正確，四個 M2 孔都在，底部天線淨空區沒有銅

PCB 選項：

| 欄位 | 選擇 | 說明 |
|---|---|---|
| Layers | 4 | |
| Dimensions | 60 × 85 mm | 自動帶入 |
| PCB Qty | 5 | 最少 5 片；PCBA 可只組其中 2 片 |
| PCB Thickness | 1.6 mm | |
| PCB Color | 隨意 | 綠色最快 |
| Surface Finish | **ENIG** 建議 | J2 是 0.5 mm 腳距，ENIG 較平整；預算緊可選 HASL(Lead-free) |
| Outer Copper Weight | 1 oz | |
| Inner Copper Weight | 0.5 oz | 預設即可 |
| Via Covering | Tented | |
| Min via hole size | 0.3 mm | 板子用 0.6/0.3 |
| Remove Order Number | Yes 或 Specify a location | 不想板上有流水號就選 Yes（加價） |
| Impedance Control | No | DVP 不需要 |
| Confirm Production File | Yes | 讓工程師先給你看確認稿，多等 1 天但保險 |

---

## 2. 開啟 PCB Assembly

- [ ] PCB Assembly 切到 **開**
- [ ] PCBA Type：
  - **Standard**：連 J4（JST 座）、J5（1×7 母座）兩顆插件一起焊，較貴但收到就能插螢幕
  - **Economic**：只焊 SMD，J4、J5 兩顆插件要自己手焊，較便宜
- [ ] Assembly Side：**Both sides**（這片板上下兩面都有 SMD）
  - 若 Economic 不給選雙面，改 Standard
- [ ] PCBA Qty：2（最少），或 5 全組
- [ ] Edge Rails / Fiducials：Added by JLCPCB
- [ ] Confirm Parts Placement：**Yes**（步驟 5 會用到）
- [ ] 按 Confirm，進到 BOM/CPL 上傳頁

---

## 3. 上傳 BOM 與 CPL

- [ ] BOM 上傳 `esp32s3-camera-bom.csv`
- [ ] CPL 上傳 `esp32s3-camera-cpl.csv`
- [ ] 欄位對應（系統通常會自動抓，手動確認一次）：
  - BOM：Designator → Designator；Comment → Comment；Footprint → Footprint；LCSC Part # → JLCPCB Part #
  - CPL：Ref → Designator；PosX/PosY → Mid X/Mid Y；Rot → Rotation；Side → Layer

---

## 4. 料號配對頁（Bill of Materials）

逐行檢查 35 行，每行都要有料號、有庫存：

- [ ] 所有電阻、電容、LED 顯示 **Basic**（不收上料費）
- [ ] 以下 Extended 零件都有貨：U2、U3、U4、U5、U6、Q1、Q2、J1、J2、J3、SW1–3、SW4；Standard 方案再看 J4 C131337、J5 C225482（1×7 母座，若缺貨換任何 2.54 mm 1×7 立式母座，8.5 mm 高）
- [ ] D3 配對到 **C8598（B5819W，SOD-123）**，不要讓系統改成 SS14，那是 SMA 封裝，焊盤不合
- [ ] **U1 ESP32-S3-WROOM-1-N16R8（C2913202）**：
  - 有貨 → 直接用
  - 顯示 Pre-order / 缺貨 → 選 Global Sourcing 代購，或改買 DigiKey 台灣模組寄給 JLCPCB（Consigned）
  - 絕對不要被系統換成 N8 或 N16 無 R 的版本
- [ ] 若選 **Economic**：把 J4、J5 兩行取消勾選（Do not place），之後自己焊
- [ ] 沒有任何一行是紅色「No part selected」

---

## 5. 零件擺放預覽（Component Placements）

KiCad 輸出的旋轉角度與 JLCPCB 的零件方向定義不一定一致，這一步最重要。有極性或方向的零件逐一看：

- [ ] **U1 模組**：天線端朝板子底邊（懸在天線淨空區那一側），腳位排列與板上焊盤對齊
- [ ] **J1 USB-C**：開口朝板邊外側
- [ ] **J2 FPC 座**：掀蓋朝板邊外側（頂邊），pin 1 位置對
- [ ] **J3 microSD**：卡片插入口朝板邊外側
- [ ] **J5 1×7 母座**（Standard 才有）：在底面右板邊，方形 pin 1 焊盤在靠天線那一端（y 大）
- [ ] **U2、U4、U5、U6（SOT-23 系列）、U3（TP4056）**：pin 1 點與絲印一致
- [ ] **Q1、Q2 MOSFET**：三腳方向對
- [ ] **D3 SS14**：陰極線與絲印一致
- [ ] **D1、D2、D4、D5 LED**：陰極方向對（頂層 D1/D4/D5，底層 D2）
- [ ] **SW4 滑動開關**：撥桿朝右板邊外側，pad 3（GND）靠板子上緣
- [ ] **SW1–3**：方向不影響，略過
- [ ] 電阻、電容：無極性，略過

方向不對的在預覽頁直接旋轉修正，改完不用重傳 CPL。

---

## 6. 結帳前

- [ ] 報價明細：PCB 費、上料費（約 15 種 Extended × 一次費用）、零件費、組裝費、運費
- [ ] 運送到台灣：選 DHL 或 FedEx（3–5 天）較穩，郵政便宜但慢
- [ ] 貨物申報價值選 Low 或 Actual 皆可，超過 NT$2000 會課稅
- [ ] 儲存到購物車 → 付款
- [ ] 若步驟 1 選了 Confirm Production File，1–2 天內回信站確認工程師的檔案，不回覆會卡住

---

## 7. 同時另外採購（板外零件）

| 品項 | 規格 | 備註 |
|---|---|---|
| 相機模組 | OV2640，24pin 0.5 mm 排線，ESP32-CAM 相容 | 多買一條排線備用 |
| 鋰電池 | 3.7V 單芯、JST PH 2.0 插頭、帶保護板，尺寸 603040（30×40×6 mm）或更小 | 收到先量極性；貼在底面中央 (34,44)，墊 2 mm 雙面泡棉膠，保護板端朝下緣 |
| microSD 卡 | 8–32GB | |
| USB-C 線 | 能傳資料的 | |
| M2 螺絲、銅柱 | 4 組 | |
| 預覽螢幕 | 通用型 1.3 吋 IPS 240×240 ST7789，**7 pin 2.54 mm 直排針已焊**（GMT130 / ZJY133T，27.78 × 39.22 mm） | 直插底面 J5 母座，不用線；腳序見 DESIGN.md 2d。Waveshare 版腳序不同，不能直插 |
| （Economic 才要）JST PH 2P 立式座 | 對應 J4，C131337 | |
| （Economic 才要）2.54 mm 1×7 立式母座 | 1 個，對應 J5，C225482 或任何 8.5 mm 高的同規格品 | |

---

## 8. 收到板子後的第一次上電

先**不要**插相機與電池。

- [ ] 目視：U1 天線端有沒有懸出淨空區、J2 掀蓋能開、有沒有明顯空焊、SW4 撥桿在右板邊能撥動
- [ ] 接 USB-C 後先撥 SW4：撥向絲印「ON」（往模組方向）藍燈 D5 亮，撥向「OFF」（往板子上緣）全熄。若方向與絲印相反，代表相容品機構相反，記下即可。關機狀態下 D2 紅燈仍應顯示充電
- [ ] 量電源對地阻抗：VBUS、+3V3、+2V8、+1V2 對 GND 不能短路
- [ ] 接 USB-C，量 +3V3 ≈ 3.3V、+2V8 ≈ 2.8V、+1V2 ≈ 1.2V
- [ ] 插螢幕前：母座 pin 1（方形焊盤、靠天線端）對地 0 Ω、pin 2 對地 3.3V；再把模組絲印的 GND 對到 pin 1 那一格才插
- [ ] 電腦裝置管理員看到 ESP32-S3 USB 裝置（或按住 BOOT 再插看到下載模式）
- [ ] 燒一個 blink 測 D1 綠燈
- [ ] 插 microSD：從左板邊（USB-C 的對面）插入 J3，金手指面朝電路板、標籤朝外，推到「喀」一聲；再推一下會退出
- [ ] 以上都過，斷電、插相機排線（接觸面朝下、確認 pin 1），排線往板邊出來約 2.5 mm 就反折 180° 蓋回 J2，模組貼在按鍵欄與 U4 之間的空區（鏡頭中心約 x30, y25 mm），底下墊 8×8 mm 雙面泡棉膠，再上電跑 CameraWebServer 範例
- [ ] 最後才接電池：J4 有 L 形絲印記號那一側是 pin 1 = 正極（底面朝自己、天線朝下時在左邊）。先量電池插頭紅線是否對到 pin 1，不對就把端子對調，再插上，確認 D2 充電紅燈亮

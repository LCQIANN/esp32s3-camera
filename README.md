# ESP32-S3 Camera — v1.2

以 ESP32-S3-WROOM-1-N16R8 為核心的隨身相機板：OV2640 DVP 相機、microSD 存檔、USB-C 燒錄與充電、鋰電池供電、電源開關與電源燈，可外接 1.3 吋 ST7789 預覽螢幕。KiCad 10 專案，設計成直接送 JLCPCB PCBA。

![頂面](view-top.png)

| 項目 | 規格 |
|---|---|
| 板子 | 60 × 85 mm、4 層（In1 = GND、In2 = +3V3）、1.6 mm、四角 M2 孔 |
| 主控 | U1 ESP32-S3-WROOM-1-N16R8（16 MB flash、8 MB OPI PSRAM） |
| 相機 | J2 24P 0.5 mm FPC 座，AI-Thinker ESP32-CAM 標準腳位；U5 2.8V、U6 1.2V LDO 供相機 |
| 儲存 | J3 microSD（SDMMC），開口朝左板邊 |
| 電源 | J1 USB-C → U3 TP4056 充電 → J4 JST PH 2.0 鋰電池；U2 AP2112K 3.3V LDO；SW4 滑動開關控制 LDO EN；D5 藍色電源燈 |
| 操作 | SW1 BOOT、SW2 RESET、SW3 SHUTTER；D1 綠、D2 紅（充電）、D4 白 LED |
| 擴充 | J5 UART 1×4、J6 GPIO 1×4，兩條排針合起來接外接 ST7789 螢幕 |
| 零件 | 61 顆：58 SMD 由 JLCPCB 貼片，3 插件（J4、J5、J6） |
| 狀態 | v1.2，2026-09-21 定稿。ERC 0、DRC 0/0/0、原理圖一致性 0 |

## 目前狀態

- **v1.2 已定稿，可下單。** 快照在 `versions/v1.2/`，含 Gerber、BOM、CPL、ERC/DRC 報告，視為唯讀。
- **預覽螢幕為外接**，用杜邦線接 J5、J6，不改板。不規劃 v1.3。
- 版本沿革：v1.0 最初佈局 → v1.1 相機腳位改 ESP32-CAM 標準、加相機 LDO、填 LCSC 料號 → v1.2 加 SW4、R21、R20、D5 與 ON/OFF 絲印。
- 送洗前檢查補了兩顆 GND 過孔（J2.23、C3.2 原本焊盤浮接），細節見 `DESIGN.md` 第 3 節。

## 檔案地圖

```
esp32s3-camera/
├── README.md                     本檔
├── DESIGN.md                     設計規格書：決策、腳位、電路細節、組裝與機構、版本規則
├── esp32s3-camera.kicad_pro/.kicad_sch/.kicad_pcb   KiCad 10 專案（根目錄永遠是最新版）
├── esp32s3-camera.pretty/        自訂 footprint（ESP32-S3-WROOM-1-Cam）
├── esp32s3-camera.step           板子 STEP，給外殼設計用
├── erc.rpt / drc.rpt / netlist.net
├── view-top.png / view-bottom.png   v1.2 頂面、底面 3D 正視
├── esp32s3-camera-v1.2-零件分工與採購.pptx / .pdf   零件分工、組裝示意、渲染圖、採購清單簡報
│
├── fab/                          送廠檔案
│   ├── esp32s3-camera-gerber.zip   Gerber + 鑽孔打包
│   ├── esp32s3-camera-bom.csv      BOM，含 LCSC Part # 欄
│   ├── esp32s3-camera-cpl.csv      貼片座標
│   ├── gerber/                     未打包的 Gerber、鑽孔檔
│   ├── JLCPCB-上傳-v1.2/            上傳用三個檔案的重新命名版 + 一頁說明
│   ├── JLCPCB-下單清單.md           下單逐步核對表，含收到板子後的第一次上電
│   └── 採購清單.md                  板外零件與插件的購買網址
│
├── render/                       kicad-cli 光線追蹤渲染
│   ├── iso-*/top/bottom/low-angle/closeup-*.png   裸板貼片後
│   ├── assembled-*.png / closeup-camera-module.png   插相機、記憶卡、電池、螢幕的組裝示意
│   └── illustration/             示意渲染專用的板檔複本、簡化 VRML 模型、輔助腳本（見下）
│
├── versions/                     各版完整快照，唯讀
│   ├── v1.0/  v1.1/  v1.2/       每版有 README.txt 說明改了什麼
│
├── frames/                       2026-09-11 早期佈局的旋轉截圖，僅供回顧
└── .history/                     KiCad 自動快照，由 KiCad 管理
```

`render/illustration/esp32s3-camera-illustration.kicad_pcb` 多了三個沒有焊盤的假零件掛簡化模型，**只用來渲染，不要拿它出 Gerber**。

## 怎麼下單

1. 依 `fab/JLCPCB-下單清單.md` 逐項核對。上傳 `fab/esp32s3-camera-gerber.zip`、`esp32s3-camera-bom.csv`、`esp32s3-camera-cpl.csv`。
2. PCB：4 層、60 × 85 mm、1.6 mm、1 oz、ENIG 建議、Tented via，最少 5 片。
3. PCBA：雙面貼片，最少 2 片。
   - **Economic** 只焊 SMD：J4、J5、J6 自己買回來手焊，可換 90° 彎針方便接螢幕。
   - **Standard** 含插件：三顆一起焊好。
4. 料號配對頁逐行看：U1 `C2913202`（N16R8，可能預購，不要被換成 N8 或無 R 版）、D3 `C8598`（SOD-123，不是 SS14）、SW4 `C431540`。
5. 零件擺放預覽確認方向：U1 天線端朝板子底邊、J1 開口朝板邊、J2 掀蓋朝板邊、SW4 撥桿朝右板邊。

## 板外要自己買的

相機模組、鋰電池、microSD 卡、USB-C 線是最小採購；Economic 方案再加 J4 電池座。完整清單與購買網址在 `fab/採購清單.md`。

| 品項 | 規格 | 接到 |
|---|---|---|
| OV2640 相機模組 | 24 pin 0.5 mm 排線，ESP32-CAM 相容，排線約 21 mm，多買一條備用 | J2 |
| 3.7V 鋰電池 | 603040 或 503040 約 600 mAh，帶保護板，JST PH 2.0 插頭 | J4 |
| microSD 卡 | 8–32 GB | J3 |
| USB-C 線 | 要能傳資料 | J1 |
| 預覽螢幕（選配） | 通用型 1.3 吋 IPS 240×240 ST7789，7 pin 2.54 mm 焊接式，27.78 × 39.22 mm | J5 + J6 |
| M2 螺絲與銅柱 | 板子 4 組，螢幕 4 組 | H1–H4 |
| 雙面泡棉膠 | 約 2 mm 厚 | 相機模組與電池底下 |

## 組裝重點

- **相機**：排線接觸面朝下插入 J2，出來約 2.5 mm 就反折 180° 蓋回 J2，模組貼在按鍵欄與 U4 之間的空區（x 25.5–34.5、y 20.5–29.5 mm），鏡頭中心 (30, 25)，底下墊 8 × 8 mm 泡棉膠。
- **電池**：貼在底面中央 (34, 44)，墊 2 mm 泡棉，保護板端朝下緣。**J4 pin 1 = 正極**，在 L 形絲印那一側、靠板子中央。電池插頭極性沒有統一規範，插之前先量。
- **螢幕**：疊在電池外側、亮面朝外，7 pin 邊朝 J5、J6。接法：GND→J5.2、VCC→J5.1、SCL→J5.3 (GPIO43)、SDA→J5.4 (GPIO44)、RES→J6.4 (GPIO6)、DC→J6.3 (GPIO5)、BLK→J6.2 (GPIO4)。借用 UART0 腳位當 SPI，USB 序列埠仍可用。
- **電源開關**：撥向板子上緣（角落孔那側）= OFF，撥向模組 = ON，絲印已標。關機時 USB 仍可充電，D2 紅燈照常。D5 藍燈接 3.3V，開機必亮。
- **microSD**：從左板邊插入 J3，金手指朝電路板，推到「喀」一聲。
- **底面高度**：電池 + 泡棉 8 mm，排針 8.5 mm，加螢幕後約 10.8 mm，外殼厚度以螢幕為準。
- **外殼開孔**：鏡頭 (30, 25)、開關右板邊 y 8–14、USB-C 右板邊、記憶卡左板邊、螢幕窗 23.4 × 23.4 mm。

## 收到板子後的第一次上電

先不插相機與電池。接 USB-C 撥 SW4 看 D5 亮滅，量 +3V3 / +2V8 / +1V2 對地無短路且電壓正確，電腦看到 ESP32-S3 USB 裝置，燒 blink 測 D1。都過了再依序插 microSD、相機排線、最後接電池。完整清單在 `fab/JLCPCB-下單清單.md` 第 8 節。

## 韌體

Arduino IDE `esp32` 套件的 CameraWebServer 範例，或 ESP-IDF 的 `esp32-camera` component。Board 選 **ESP32S3 Dev Module**，PSRAM 選 **OPI PSRAM**（R8 是 octal，選 QSPI 會抓不到）。相機 GPIO 對應表在 `DESIGN.md` 第 4 節，直接填進 `camera_config_t`。

## 版本規則

- 根目錄永遠是正在改的最新版。每次出 Gerber 準備下單，把 `.kicad_pcb / .kicad_sch / .kicad_pro`、`esp32s3-camera.pretty/`、`fp-lib-table` 與 `fab/` 內的 zip、BOM、CPL 複製到 `versions/vX.Y/`，並寫 README.txt。
- 版本號用數字（v1.0、v1.1、v1.2），不用 rev A / rev B。板上絲印、KiCad 標題欄、Gerber ProjectId 三處同步。
- 不在根目錄留 `*.bak_before_xxx`，中途快照交給 KiCad 的 `.history/`。
- 沒有使用 Git。

## 重新輸出送廠檔

```
kicad-cli sch export bom --fields "Reference,Value,Footprint,QUANTITY,LCSC" --labels "Designator,Comment,Footprint,Qty,LCSC Part #" --group-by "Value,Footprint,LCSC" --exclude-dnp -o fab/esp32s3-camera-bom.csv esp32s3-camera.kicad_sch
kicad-cli pcb drc --schematic-parity esp32s3-camera.kicad_pcb
```

## 輔助腳本（`render/illustration/`，用 KiCad 附的 python 執行）

| 腳本 | 用途 |
|---|---|
| `gnd_connectivity.py` | 幾何連通性檢查：焊盤、過孔、走線、敷銅做 union-find，確認每個 GND / +3V3 焊盤都在主群集。**DRC 只要有 unconnected_items 就跑一次，0 才算過。** |
| `battery_check.py` | 電池投影範圍對底面零件外框與高度的間距核對 |
| `fix_v12_gnd.py` | 2026-09-21 補 J2.23、C3.2 GND 過孔與 R21 腳位修正 |
| `v12_sch.py` / `v12_pcb.py` / `v12_silk_onoff.py` | v1.2 加 SW4、R20、R21、D5 與 ON/OFF 絲印的自動改板腳本 |
| `make_illustration_board.py` | 產生示意渲染用的板檔複本 |
| `gen_camera_wrl.py` / `gen_display_wrl.py` | 產生相機模組與螢幕的簡化 VRML 模型（KiCad 不畫 Cylinder 基本體，圓柱要用網格） |
| `sch_inspect.py` | 原理圖檢查工具 |

## 教訓

- DRC 報的「zone unconnected」不要當敷銅碎片忽略。KiCad 只回報兩群集間最近的一對物件，浮接的焊盤會藏在後面。
- D3 要用 B5819W SOD-123（`C8598`），LCSC 上的 SS14 是 SMA 封裝，焊盤不合。
- JLCPCB 的零件旋轉定義與 KiCad 不一定一致，零件擺放預覽頁逐一看有極性的零件。

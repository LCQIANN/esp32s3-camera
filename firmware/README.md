# 韌體（ESP32-S3 相機板 v1.4）

`esp32s3-camera/` 是一個 Arduino 專案：開機後把 OV2640 的即時畫面顯示在 1.3 吋 ST7789 上，
按側邊快門拍一張 1600 × 1200 的 JPEG 存到 microSD。腳位全部集中在 `board_pins.h`，
數值來自 `DESIGN.md` 第 4 節；改板子時只改那個檔。

## 功能

| 操作 | 行為 |
|---|---|
| 開機 | 螢幕顯示 240 × 240 即時預覽（RGB565，不縮放），左上角顯示閃光燈狀態、記憶卡狀態、已拍張數 |
| SHUTTER（SW3，上板邊側按） | 重新初始化相機為 JPEG UXGA、丟 3 張讓曝光穩定、拍 1 張寫到 `/DCIM/IMG_0001.JPG`（流水號存在 NVS，重開機不歸零），再切回預覽。整個過程約 1 秒，螢幕下方顯示 `Saved IMG_0001.JPG` |
| BOOT（SW1，鏡頭面針孔） | 切換閃光燈（D4 白光 LED，拍照瞬間才亮） |
| 綠色狀態 LED D1 | 待機每 2 秒閃一下，寫卡時常亮 |
| 沒插記憶卡 | 仍可預覽，按快門顯示 `No microSD`；之後插卡會在下次按快門時重新掛載 |
| 相機沒接 | 螢幕顯示 `Camera not found / check J2 ribbon` |

USB-C 接電腦是 USB-CDC 序列埠（115200），開機、拍照、錯誤都有 log。
GPIO43 / 44 已經拿去當螢幕的 SPI，所以 UART0 不能同時用；燒錄和 log 都走 USB。

## 編譯

Arduino IDE 2.x，`esp32` 核心 3.3.10（更舊的 2.x 也應可用，但 `SD_MMC.setPins` 需 2.0.3 以上）。
函式庫管理員裝 **Adafruit GFX Library** 和 **Adafruit ST7735 and ST7789 Library**；
`esp_camera`、`SD_MMC`、`Preferences` 隨核心附帶。

工具 → 開發板設定：

| 選項 | 值 |
|---|---|
| Board | ESP32S3 Dev Module |
| PSRAM | **OPI PSRAM**（N16R8 是 octal，選 QSPI 會抓不到相機 framebuffer） |
| Flash Size | 16MB (128Mb) |
| Flash Mode | QIO 80MHz |
| Partition Scheme | 16M Flash (3MB APP/9.9MB FATFS) |
| USB CDC On Boot | Enabled |
| USB Mode | Hardware CDC and JTAG |

命令列（Arduino IDE 內建的 arduino-cli，Windows 路徑如下；其他平台換成自己的 arduino-cli）：

```
"%LOCALAPPDATA%\Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe" compile ^
  --fqbn "esp32:esp32:esp32s3:PSRAM=opi,FlashSize=16M,FlashMode=qio,PartitionScheme=app3M_fat9M_16MB,CDCOnBoot=cdc,USBMode=hwcdc" ^
  firmware\esp32s3-camera
```

2026-10-10 以上設定編譯通過：程式 501,958 bytes（15%），RAM 35,940 bytes（10%）。

## 燒錄

第一次燒：按住 BOOT 插 USB（或按住 BOOT 點一下 RESET）進下載模式，再 `upload -p COMx`；
之後 USB-CDC 會自動重啟進下載模式，不用按鍵。

## 還沒在硬體上驗證的事

板子（v1.4）尚未下單，這份韌體只確認能編譯，下列項目要拿到板子後逐一確認：

1. **預覽方向**：相機模組和螢幕的安裝方向決定畫面是否要轉，改 `PREVIEW_ROTATION`（0–3）和 `set_vflip` / `set_hmirror`。
2. **ST7789 SPI 模式**：沒有 CS 腳的模組通常要 `SPI_MODE3`；畫面全白或雜訊就改成 `SPI_MODE0` 試。
3. **預覽幀率**：240 × 240 RGB565 一幀 115 KB，SPI 40 MHz 理論上限約 30 fps；若 OV2640 在 240 × 240 不穩，改 `FRAMESIZE_QVGA` 並加裁切。
4. **microSD 1-bit SDMMC**：若掛載失敗，先確認 J3 的 CLK/CMD/D0 焊接，再試改成 SPI 模式（`SD` 函式庫，CS = GPIO41）。
5. **閃光燈**：D4 經 Q1 AO3400A 低側驅動，GPIO42 高電位亮；拍照時只亮約 4 幀，若太暗把丟棄幀數加大。
6. **按鍵彈跳**：30 ms 去彈跳對 SKRTLAE010 側按應該夠；連拍誤觸就加大。

## 下一步（還沒做）

- Wi-Fi：加上 `WebServer` 把 `/DCIM` 列成網頁相簿，或直接用核心附的 CameraWebServer 範例串流。
- OV5640：`PHOTO_SIZE` 可以到 `FRAMESIZE_QSXGA`（2592 × 1944），其餘腳位相同。
- 電池電量：板上沒有分壓到 ADC，v1.5 若要顯示電量需加一組 100k/100k 到任一 ADC 腳。

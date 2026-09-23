v1.3 — 2026-09-21 晚上定稿（v1.2 未下單，直接改成 v1.3）。
起因：要 3D 列印相機式外殼（鏡頭正面、螢幕背面），杜邦線接螢幕在外殼裡收不乾淨。
相對 v1.2 的改動：拆掉 J5 UART/DEBUG 1x4 與 J6 EXPANSION 1x4 兩條排針，
換成一個 1x7 2.54 mm 立式母座 J5（CJT A2541WV-7P，LCSC C225482），底面右板邊 x = 56，
pin 1 GND 在 y 52.62（靠天線端、方形焊盤）到 pin 7 BLK 在 y 37.38，腳序 GND VCC SCL SDA RES DC BLK 與
通用型 1.3 吋 IPS 240x240 ST7789 7 pin 模組相同，模組直接插入、亮面朝外、身體蓋在電池上方。
SCL = GPIO44（網路 UART_RX）、SDA = GPIO43（網路 UART_TX），RES/DC/BLK = GPIO6/5/4。
走線：UART_TX/UART_RX 頂層線只改末端；IO6/IO5/IO4 由原頂層線末端各加一顆過孔，沿右板邊底層 x 57.4/58.05/58.7 往上進 pin 5/6/7。
絲印：底面每腳旁 GND 3V3 SCL SDA RES DC BLK、DISPLAY；B.Fab 有模組 27.78x39.22 投影框。絲印、標題欄、Gerber ProjectId 皆為 v1.3。
58 顆 SMD 與 v1.2 完全相同，CPL 相同；插件 J4、J5 兩顆。零件 60 顆。
驗證：ERC 0 錯誤（2 個 XC6206 符號庫警告）；DRC 含原理圖一致性 0 錯誤、0 警告、0 未連接、0 一致性問題；
gnd_connectivity.py GND / +3V3 全部焊盤在主群集。
內容：原理圖、板檔、專案檔、網表、ERC/DRC 報告、fab/（Gerber zip、鑽孔、BOM 34 行、CPL 58 顆、JLCPCB-上傳-v1.3、下單清單、採購清單）、自訂 footprint 庫。
機構數字（外殼用）見 DESIGN.md「v1.3 改了什麼」：螢幕模組 PCB 背面離板底 11.0 mm、亮面 13.9 mm、有效顯示區中心約 (40.5, 45)。
腳本：render/illustration/v13_sch.py、v13_pcb.py、v13_pcb_fix.py、v13_pcb_fix2.py。
此資料夾視為唯讀。

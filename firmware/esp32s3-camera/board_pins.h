// ESP32-S3 Camera board v1.4 — pin map. Source of truth: DESIGN.md section 4 (腳位配置).
// Keep this file in sync with the schematic; nothing else in the firmware hard-codes a GPIO.
#pragma once

// ---- camera DVP, J2 = AI-Thinker ESP32-CAM 24-pin order (OV2640 / OV5640 bottom-contact FPC) ----
#define CAM_PIN_PWDN    18
#define CAM_PIN_RESET   16
#define CAM_PIN_XCLK     9
#define CAM_PIN_SIOD     7     // SCCB SDA
#define CAM_PIN_SIOC    15     // SCCB SCL
#define CAM_PIN_D7       3     // Y9
#define CAM_PIN_D6      10     // Y8
#define CAM_PIN_D5      11     // Y7
#define CAM_PIN_D4      13     // Y6
#define CAM_PIN_D3      21     // Y5
#define CAM_PIN_D2      48     // Y4
#define CAM_PIN_D1      47     // Y3
#define CAM_PIN_D0      14     // Y2
#define CAM_PIN_VSYNC   17
#define CAM_PIN_HREF     8
#define CAM_PIN_PCLK    12
#define CAM_XCLK_HZ     20000000

// ---- microSD (J3), SDMMC 1-bit ----
#define SD_PIN_CLK      39
#define SD_PIN_CMD      38
#define SD_PIN_D0       40
#define SD_PIN_D3       41     // CS when used as SPI; unused in SDMMC 1-bit mode

// ---- 1.3in ST7789 240x240 display on J5 (SPI, no CS pin on the module) ----
#define TFT_PIN_SCL     44     // J5.3  SCL  = SPI SCK   (shares the UART0 RX pad; USB-CDC is the console)
#define TFT_PIN_SDA     43     // J5.4  SDA  = SPI MOSI  (shares the UART0 TX pad)
#define TFT_PIN_RES      6     // J5.5
#define TFT_PIN_DC       5     // J5.6
#define TFT_PIN_BLK      4     // J5.7  backlight, active high
#define TFT_W          240
#define TFT_H          240

// ---- buttons, active low (10k pull-ups on the board, internal pull-ups enabled anyway) ----
#define BTN_PIN_BOOT     0     // SW1, lens face, pinhole in the case
#define BTN_PIN_SHUTTER  1     // SW3, side-actuated on the top edge (v1.4)

// ---- LEDs ----
#define LED_PIN_STATUS   2     // D1 green, GPIO -> 1k -> LED -> GND, active high
#define LED_PIN_FLASH   42     // D4 white through Q1 AO3400A low-side MOSFET, active high
// D5 blue = power (after SW4), D2 red = TP4056 charging: hardware only, no GPIO.

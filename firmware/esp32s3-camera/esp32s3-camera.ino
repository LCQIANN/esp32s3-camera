// ESP32-S3 Camera board v1.4 — point-and-shoot firmware.
//
//   * live preview from the OV2640 on the 1.3in ST7789 (240 x 240, RGB565)
//   * SHUTTER (SW3, side button): take a UXGA 1600 x 1200 JPEG and save it to /DCIM on the microSD
//   * BOOT (SW1): toggle the white flash LED for the next shots
//   * green status LED: short blink every 2 s while idle, solid while a photo is being written
//
// Arduino IDE: board "ESP32S3 Dev Module", PSRAM "OPI PSRAM", Flash Size 16MB, USB CDC On Boot "Enabled".
// Libraries: Adafruit GFX + Adafruit ST7735 and ST7789 (Library Manager); esp_camera and SD_MMC come with the core.
// See firmware/README.md for the arduino-cli command line and what has / has not been tested.

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <SD_MMC.h>
#include <Preferences.h>
#include "esp_camera.h"
#include "board_pins.h"

// ------------------------------------------------------------------ settings
static const int   PREVIEW_ROTATION = 0;        // 0..3, turn the preview if the module is mounted sideways
static const int   JPEG_QUALITY     = 10;       // 0 (best) .. 63
static const framesize_t PHOTO_SIZE = FRAMESIZE_UXGA;   // 1600 x 1200, the OV2640 maximum
static const uint32_t SPI_HZ        = 40000000;
static const char *DCIM_DIR         = "/DCIM";

// ------------------------------------------------------------------ globals
SPIClass        tftSpi(HSPI);
Adafruit_ST7789 tft(&tftSpi, -1 /*CS: module has none*/, TFT_PIN_DC, TFT_PIN_RES);
Preferences     prefs;
bool            sdOk       = false;
bool            camOk      = false;
bool            flashOn    = false;
uint32_t        photoCount = 0;

// ------------------------------------------------------------------ camera
static camera_config_t baseConfig() {
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer   = LEDC_TIMER_0;
  c.pin_d0 = CAM_PIN_D0;   c.pin_d1 = CAM_PIN_D1;   c.pin_d2 = CAM_PIN_D2;   c.pin_d3 = CAM_PIN_D3;
  c.pin_d4 = CAM_PIN_D4;   c.pin_d5 = CAM_PIN_D5;   c.pin_d6 = CAM_PIN_D6;   c.pin_d7 = CAM_PIN_D7;
  c.pin_xclk = CAM_PIN_XCLK;  c.pin_pclk = CAM_PIN_PCLK;
  c.pin_vsync = CAM_PIN_VSYNC; c.pin_href = CAM_PIN_HREF;
  c.pin_sccb_sda = CAM_PIN_SIOD; c.pin_sccb_scl = CAM_PIN_SIOC;
  c.pin_pwdn = CAM_PIN_PWDN;  c.pin_reset = CAM_PIN_RESET;
  c.xclk_freq_hz = CAM_XCLK_HZ;
  c.fb_location  = CAMERA_FB_IN_PSRAM;
  c.grab_mode    = CAMERA_GRAB_LATEST;
  return c;
}

// Preview: RGB565 at the panel's own 240 x 240 so a frame goes to the display without scaling.
static bool cameraStartPreview() {
  camera_config_t c = baseConfig();
  c.pixel_format = PIXFORMAT_RGB565;
  c.frame_size   = FRAMESIZE_240X240;
  c.fb_count     = 2;
  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) { Serial.printf("camera preview init failed: 0x%x\n", err); return false; }
  sensor_t *s = esp_camera_sensor_get();
  if (s) { s->set_vflip(s, 0); s->set_hmirror(s, 0); }
  return true;
}

// Photo: JPEG at full resolution. The pixel format cannot be switched on a running driver, so the
// camera is re-initialised for the shot and again for the preview afterwards (about 0.5 s in total).
static bool cameraStartPhoto() {
  camera_config_t c = baseConfig();
  c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size   = PHOTO_SIZE;
  c.jpeg_quality = JPEG_QUALITY;
  c.fb_count     = 1;
  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) { Serial.printf("camera photo init failed: 0x%x\n", err); return false; }
  return true;
}

// ------------------------------------------------------------------ display helpers
static void showPreviewFrame(const camera_fb_t *fb) {
  // The camera delivers RGB565 big-endian, which is exactly what the panel wants: stream it
  // untouched (bigEndian = true) instead of drawRGBBitmap(), which would byte-swap every pixel.
  tft.startWrite();
  tft.setAddrWindow(0, 0, TFT_W, TFT_H);
  tft.writePixels((uint16_t *)fb->buf, TFT_W * TFT_H, true, true);
  tft.endWrite();
}

static void banner(const char *line1, const char *line2 = nullptr, uint16_t bg = ST77XX_BLACK) {
  tft.fillRect(0, TFT_H - 40, TFT_W, 40, bg);
  tft.setTextColor(ST77XX_WHITE, bg);
  tft.setTextSize(2);
  tft.setCursor(6, TFT_H - 36); tft.print(line1);
  if (line2) { tft.setCursor(6, TFT_H - 18); tft.print(line2); }
}

static void overlayStatus() {
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.setCursor(4, 4);
  tft.printf("%s  %s  #%lu ", flashOn ? "FLASH" : "     ", sdOk ? "SD" : "NO SD", (unsigned long)photoCount);
}

// ------------------------------------------------------------------ storage
static bool sdMount() {
  SD_MMC.setPins(SD_PIN_CLK, SD_PIN_CMD, SD_PIN_D0);
  if (!SD_MMC.begin("/sdcard", true /*1-bit*/)) { Serial.println("microSD: no card or mount failed"); return false; }
  if (!SD_MMC.exists(DCIM_DIR)) SD_MMC.mkdir(DCIM_DIR);
  Serial.printf("microSD: %llu MB, type %d\n", SD_MMC.cardSize() / (1024 * 1024), SD_MMC.cardType());
  return true;
}

static String nextFileName() {
  photoCount = prefs.getUInt("n", 0) + 1;
  prefs.putUInt("n", photoCount);
  char name[32];
  snprintf(name, sizeof name, "%s/IMG_%04lu.JPG", DCIM_DIR, (unsigned long)photoCount);
  return String(name);
}

// ------------------------------------------------------------------ take a photo
static void takePhoto() {
  digitalWrite(LED_PIN_STATUS, HIGH);
  banner("Capturing...");
  if (!sdOk) sdOk = sdMount();                       // the card may have been inserted after boot
  if (!sdOk) { banner("No microSD", "insert a card", ST77XX_RED); delay(1200); digitalWrite(LED_PIN_STATUS, LOW); return; }

  esp_camera_deinit();
  if (!cameraStartPhoto()) { banner("Camera error", nullptr, ST77XX_RED); delay(1200); camOk = cameraStartPreview(); return; }
  if (flashOn) digitalWrite(LED_PIN_FLASH, HIGH);
  for (int i = 0; i < 3; i++) {                      // let auto-exposure settle on the new frame size (and the flash)
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) esp_camera_fb_return(fb);
  }
  camera_fb_t *fb = esp_camera_fb_get();
  digitalWrite(LED_PIN_FLASH, LOW);

  bool ok = false;
  String name;
  if (fb && fb->format == PIXFORMAT_JPEG && fb->len > 0) {
    name = nextFileName();
    File f = SD_MMC.open(name, FILE_WRITE);
    if (f) { ok = f.write(fb->buf, fb->len) == fb->len; f.close(); }
    Serial.printf("%s: %u bytes %s\n", name.c_str(), (unsigned)fb->len, ok ? "saved" : "WRITE FAILED");
  } else {
    Serial.println("capture failed: no JPEG frame");
  }
  if (fb) esp_camera_fb_return(fb);

  esp_camera_deinit();
  camOk = cameraStartPreview();
  digitalWrite(LED_PIN_STATUS, LOW);
  if (ok) banner("Saved", name.c_str() + strlen(DCIM_DIR) + 1, ST77XX_GREEN);
  else    banner("Save failed", nullptr, ST77XX_RED);
  delay(900);
}

// ------------------------------------------------------------------ buttons (active low, debounced edge)
struct Button {
  int pin; bool last = true; uint32_t t = 0;
  bool pressed() {
    bool now = digitalRead(pin);
    if (now != last && millis() - t > 30) { t = millis(); last = now; return !now; }
    return false;
  }
};
Button shutter{BTN_PIN_SHUTTER}, boot{BTN_PIN_BOOT};

// ------------------------------------------------------------------ setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN_STATUS, OUTPUT);  digitalWrite(LED_PIN_STATUS, LOW);
  pinMode(LED_PIN_FLASH, OUTPUT);   digitalWrite(LED_PIN_FLASH, LOW);
  pinMode(TFT_PIN_BLK, OUTPUT);     digitalWrite(TFT_PIN_BLK, LOW);
  pinMode(BTN_PIN_SHUTTER, INPUT_PULLUP);
  pinMode(BTN_PIN_BOOT, INPUT_PULLUP);

  tftSpi.begin(TFT_PIN_SCL, -1, TFT_PIN_SDA, -1);
  tft.init(TFT_W, TFT_H, SPI_MODE3);               // CS-less ST7789 modules need mode 3
  tft.setSPISpeed(SPI_HZ);
  tft.setRotation(PREVIEW_ROTATION);
  tft.fillScreen(ST77XX_BLACK);
  digitalWrite(TFT_PIN_BLK, HIGH);
  banner("ESP32-S3 Camera", "v1.4 starting");

  prefs.begin("cam", false);
  photoCount = prefs.getUInt("n", 0);
  sdOk  = sdMount();
  camOk = cameraStartPreview();
  if (!camOk) banner("Camera not found", "check J2 ribbon", ST77XX_RED);
  Serial.printf("ready: camera %s, sd %s, psram %u bytes\n", camOk ? "ok" : "FAIL", sdOk ? "ok" : "none", (unsigned)ESP.getPsramSize());
}

void loop() {
  static uint32_t lastBlink = 0;
  if (millis() - lastBlink > 2000) { lastBlink = millis(); digitalWrite(LED_PIN_STATUS, HIGH); delay(20); digitalWrite(LED_PIN_STATUS, LOW); }

  if (boot.pressed())    { flashOn = !flashOn; Serial.printf("flash %s\n", flashOn ? "on" : "off"); }
  if (shutter.pressed()) { if (camOk) takePhoto(); }

  if (!camOk) { delay(100); return; }
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) return;
  if (fb->format == PIXFORMAT_RGB565 && fb->len == TFT_W * TFT_H * 2) showPreviewFrame(fb);
  esp_camera_fb_return(fb);
  overlayStatus();
}

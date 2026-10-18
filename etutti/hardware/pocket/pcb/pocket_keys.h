// eTuttino Pocket key table -- WRITTEN BY etutti/hardware/pocket/pcb/build_pocket_pcb.py
// from the routed board (do not edit by hand). Contract: pcb/PINOS.md.
// KEY_INPUT[row][col] = multiplexer * 16 + channel; row 0 = row 1 (nearest the player).
#pragma once
#define POCKET_LAYOUT_ROWS 4
#define POCKET_LAYOUT_COLS 8
const uint8_t POCKET_FIRST_NOTE[POCKET_LAYOUT_ROWS] = {57, 55, 56, 57};
const uint8_t POCKET_FIRST_COL[POCKET_LAYOUT_ROWS] = {1, 0, 1, 1};
const uint8_t POCKET_MUX_SEL_PINS[4] = {0, 1, 2, 3};
const uint8_t POCKET_MUX_COM_PINS[2] = {14, 15};
const uint8_t POCKET_LED_PINS[2] = {13, 5};  // red, green
const uint8_t POCKET_SENS_EN_PIN = 4, POCKET_KEEP_PIN = 10, POCKET_AMP_SD_PIN = 12;
const uint8_t POCKET_VBAT_PIN = 16, POCKET_HP_DET_PIN = 17, POCKET_POT_PIN = 22;
const uint8_t POCKET_ENC_A_PIN = 11, POCKET_ENC_B_PIN = 9, POCKET_ENC_SW_PIN = 6;
// Channels 0-7 (S3 = 0) = rows 1 and 3 (EN_A); 8-15 (S3 = 1) = rows 2 and 4 (EN_B).
const int8_t POCKET_KEY_INPUT[POCKET_LAYOUT_ROWS][POCKET_LAYOUT_COLS] = {
  { -1,  21,  20,  17,  19,   2,   1,   0},
  { 25,  26,  31,  29,  13,  11,  14,  15},
  { -1,  18,  23,  22,   4,   6,   5,   3},
  { -1,  30,  28,  24,   9,   8,  10,  -1},
};

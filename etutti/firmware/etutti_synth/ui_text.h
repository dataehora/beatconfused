// Student V4 screen texts and menu types (SPEC R6V4 item 7). A header of its own because the Arduino build puts the
// prototypes of the sketch's functions before any type declared in the .ino itself.
//
// Every text of the screen lives in this file (STR[]) or in the Txt tables of the menu in the sketch: Portuguese and English,
// lower case with accents. TO ADD A LANGUAGE: add its name to LANG_NAME and its code to the enum below, then add one more
// string to every Txt initializer ({"pt", "en", "es"}); a missing one falls back to English. The strings are UTF-8 and every
// character must exist in oled_font.h (ASCII and the Latin-1 letters with accents; make_font.py adds more).
#pragma once
#include <Arduino.h>

enum { LANG_PT, LANG_EN, LANG_COUNT };
const char *const LANG_NAME[LANG_COUNT] = {"Português", "English"};   // each language writes its own name
uint8_t uiLang = LANG_PT;
struct Txt { const char *s[LANG_COUNT]; };
inline const char *tr(const Txt &t) { return t.s[uiLang] ? t.s[uiLang] : t.s[LANG_EN]; }

enum StrId {
  S_ON, S_OFF, S_MENU, S_WARN_TITLE, S_WARN_1, S_WARN_2, S_WARN_3, S_WARN_4,
  S_VOICE_OFF, S_FEEDBACK, S_VOICE, S_NO_MIC, S_MIC, S_VOL, S_HP, S_SPK, S_REST,
  S_T_HEADSET, S_T_NOTCH, S_T_SAVED, S_T_RESET, S_T_CAL, S_PHONES, S_SPEAKER_ON, S_COUNT
};
const Txt STR[S_COUNT] = {
  {"Ligado", "On"}, {"Desligado", "Off"}, {"Menu", "Menu"}, {"Aviso", "Warning"},
  {"Voz no alto-falante", "Voice on speaker"}, {"Pode dar microfonia", "May cause feedback"},
  {"Mic perto da boca e", "Mic at the mouth and"}, {"volume baixo", "volume low"},
  {"voz muda", "voice off"}, {"!microfonia", "!feedback"}, {"voz", "voice"}, {"sem mic", "no mic"}, {"mic", "mic"},
  {"vol", "vol"}, {"fone", "hp"}, {"alto", "spk"}, {"repouso", "rest"},
  {"Mic headset", "Headset mic"}, {"Notch limpos", "Notch cleared"}, {"Salvo", "Saved"}, {"Voz zerada", "Voice reset"},
  {"Calibrado", "Calibrated"}, {"Fone/AUX", "Phones/AUX"}, {"+ Alto-fal.", "+ Speaker"}};
inline const char *tx(StrId id) { return tr(STR[id]); }

const Txt HARM_MODES[4] = {{"Fixo", "Fixed"}, {"Exato", "Exact"}, {"Ajuda", "Assist"}, {"Intervalo", "Interval"}};
const Txt FOLD_NAMES[2] = {{"Exata", "Exact"}, {"Perto", "Near"}};                     // index = harmFold
const Txt RATIO_NAMES[4] = {{"Suave", "Soft"}, {"Média", "Medium"}, {"Forte", "Hard"}, {"Porta", "Gate"}};
const Txt CURVE_NAMES[4] = {{"Fixa", "Fixed"}, {"Suave", "Soft"}, {"Normal", "Normal"}, {"Dura", "Hard"}};


// ---- menu types ----
enum { PG_MAIN, PG_VOICE, PG_INPUT, PG_OUTPUT, PG_SOUND, PG_SYSTEM, PG_COUNT };
enum { MK_SUB, MK_LEVEL, MK_ENUM, MK_ACTION };
enum {
  M_VOICE_DRY, M_VOCODER, M_HARM, M_HARM_MODE, M_HARM_INT, M_HARM_HELP, M_HARM_VOICES, M_HARM_FOLD, M_ECHO, M_ECHO_TIME, M_ECHO_FB, M_VOICE_REV,
  M_MIC_GAIN, M_GATE_THR, M_GATE_RATIO, M_GATE_ATK, M_GATE_HOLD, M_GATE_REL, M_HPF, M_CLOSE_MIC, M_ANTI_FB, M_CLEAR_NOTCH,
  M_VOLUME, M_VOICE_OUT, M_KEYS_LEVEL, M_SPK_EQ, M_EQ_CUT, M_EQ_DIP,
  M_REGISTER, M_INSTRUMENT, M_AMBIENCE, M_VEL_CURVE,
  M_SAVE, M_RESET_VOICE, M_CAL_KEYS, M_KEY_TEST, M_LANGUAGE
};
// needsMic: the line (or page) only exists while a microphone is plugged into IN (R6V4 item 5)
struct MenuItem { Txt name; uint8_t kind; uint8_t id; bool needsMic; };   // SUB: id = the page
struct MenuPage { Txt name; const MenuItem *items; uint8_t count; };


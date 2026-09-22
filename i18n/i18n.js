/* ============================================================
   BEATCONFUSED I18N ENGINE — shared by every page (home, metronome,
   tuner, strobetuner, multistrobe). This file is intentionally
   page-agnostic: it knows nothing about any page's content. Each page
   defines its own `window.BC_STRINGS = { en: {...}, pt: {...}, es: {...} }`
   dictionary inline (kept local to that page, matching this repo's
   "independent pages, no build step" convention -- only the mechanism
   here is shared, not the copy), then this engine:
     - picks the active language (saved choice, else "en"),
     - swaps the text of every [data-i18n="key"] element and the
       attributes named in [data-i18n-attr="attr:key;attr2:key2"],
     - builds the flag + code language switcher (fixed, top right),
     - persists the choice and fires "bc:langchange" on window so a
       page's own script.js can re-render anything dynamic that isn't a
       plain data-i18n text node (a status message already on screen).

   NOTE: this is a client-side toggle on one URL per page, not separate
   localized routes -- there's no /pt/ or /es/ copy of each page, and
   structured (JSON-LD) data stays in English. Simpler, no build step,
   matches how the rest of the site works.

   ⚠️ Shared-file caching: this file (and i18n.css) is loaded by every
   page with a "?v=" query string, per the caching convention documented
   in CLAUDE.md. If you edit this file, bump "?v=" on every page that
   references it (grep for the current value first).
   ============================================================ */
(function () {
  "use strict";

  var STORAGE_KEY = "bc_lang";
  var DEFAULT_LANG = "en";
  var LANGS = [
    { code: "en", flag: "🇺🇸", label: "English" },
    { code: "pt", flag: "🇧🇷", label: "Português" },
    { code: "es", flag: "🇪🇸", label: "Español" },
  ];

  var currentLang = DEFAULT_LANG;

  function getStoredLang() {
    try {
      var saved = window.localStorage.getItem(STORAGE_KEY);
      if (LANGS.some(function (l) { return l.code === saved; })) {
        return saved;
      }
    } catch (_) {
      // localStorage blocked (private mode, etc.) -- fall through to default
    }
    return DEFAULT_LANG;
  }

  function getStrings() {
    return window.BC_STRINGS || {};
  }

  function t(key, vars) {
    var strings = getStrings();
    var dict = strings[currentLang] || {};
    var fallback = strings[DEFAULT_LANG] || {};
    var str = Object.prototype.hasOwnProperty.call(dict, key) ? dict[key] : fallback[key];

    if (str === undefined) {
      if (window.console && console.warn) {
        console.warn('[i18n] missing key "' + key + '" for lang "' + currentLang + '"');
      }
      return key;
    }

    if (vars) {
      Object.keys(vars).forEach(function (name) {
        str = str.replace(new RegExp("\\{" + name + "\\}", "g"), vars[name]);
      });
    }

    return str;
  }

  function applyStaticTranslations() {
    document.documentElement.setAttribute("lang", currentLang);

    var textNodes = document.querySelectorAll("[data-i18n]");
    for (var i = 0; i < textNodes.length; i += 1) {
      var el = textNodes[i];
      el.textContent = t(el.getAttribute("data-i18n"));
    }

    var attrNodes = document.querySelectorAll("[data-i18n-attr]");
    for (var j = 0; j < attrNodes.length; j += 1) {
      var attrEl = attrNodes[j];
      var spec = attrEl.getAttribute("data-i18n-attr") || "";
      spec.split(";").forEach(function (pair) {
        var parts = pair.split(":");
        var attrName = parts[0] && parts[0].trim();
        var key = parts[1] && parts[1].trim();
        if (attrName && key) {
          attrEl.setAttribute(attrName, t(key));
        }
      });
    }
  }

  function updateWidgetState(widget) {
    var buttons = widget.querySelectorAll(".bc-lang-btn");
    for (var i = 0; i < buttons.length; i += 1) {
      var isActive = buttons[i].getAttribute("data-lang") === currentLang;
      buttons[i].setAttribute("aria-pressed", String(isActive));
      buttons[i].classList.toggle("is-active", isActive);
    }
  }

  function setLang(code) {
    if (!LANGS.some(function (l) { return l.code === code; }) || code === currentLang) {
      return;
    }

    currentLang = code;

    try {
      window.localStorage.setItem(STORAGE_KEY, code);
    } catch (_) {
      // ignore -- non-persistent this session is fine
    }

    applyStaticTranslations();

    var widget = document.querySelector(".bc-lang-switch");
    if (widget) {
      updateWidgetState(widget);
    }

    window.dispatchEvent(new CustomEvent("bc:langchange", { detail: { lang: code } }));
  }

  function buildWidget() {
    var container = document.createElement("div");
    container.className = "bc-lang-switch";
    container.setAttribute("role", "group");
    container.setAttribute("aria-label", "Language / Idioma");

    LANGS.forEach(function (lang) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "bc-lang-btn";
      btn.dataset.lang = lang.code;
      btn.title = lang.label;
      btn.setAttribute("aria-pressed", String(lang.code === currentLang));

      var flag = document.createElement("span");
      flag.className = "bc-lang-flag";
      flag.setAttribute("aria-hidden", "true");
      flag.textContent = lang.flag;

      var code = document.createElement("span");
      code.className = "bc-lang-code";
      code.textContent = lang.code.toUpperCase();

      btn.appendChild(flag);
      btn.appendChild(code);
      btn.addEventListener("click", function () {
        setLang(lang.code);
      });

      container.appendChild(btn);
    });

    document.body.appendChild(container);
    updateWidgetState(container);
  }

  function init() {
    currentLang = getStoredLang();
    buildWidget();
    applyStaticTranslations();
    // Fires even on initial load (not just user-triggered switches) so a
    // page's own script.js can sync anything it renders dynamically (a
    // status message, a toggle button's Start/Stop label) via a single
    // "bc:langchange" listener, regardless of whether script.js or this
    // engine happens to finish loading first (metronome/script.js in
    // particular is fetched async, so load order isn't guaranteed).
    window.dispatchEvent(new CustomEvent("bc:langchange", { detail: { lang: currentLang } }));
  }

  window.BC_I18N = {
    t: t,
    setLang: setLang,
    getLang: function () { return currentLang; },
    refresh: applyStaticTranslations,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

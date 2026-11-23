// Language switch for the Student V4 page: html[lang] selects the .lang-block shown (pattern of etutti/manuais/).
(function () {
  var KEY = "bc-studentv4-lang";
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function put(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function set(l) {
    document.documentElement.lang = l;
    document.title = l === "pt" ? "BeatConfused | eTutti Student V4 (Português)" : "BeatConfused | eTutti Student V4 (English)";
    var b = document.querySelectorAll(".langbar button");
    for (var i = 0; i < b.length; i++) b[i].setAttribute("aria-pressed", b[i].getAttribute("data-set") === l ? "true" : "false");
  }
  var q = /[?&]lang=(pt|en)/.exec(location.search);
  var start = q ? q[1] : (get() || ((navigator.language || "pt").toLowerCase().indexOf("pt") === 0 ? "pt" : "en"));
  set(start);
  var btns = document.querySelectorAll(".langbar button");
  for (var i = 0; i < btns.length; i++) btns[i].addEventListener("click", function () { var l = this.getAttribute("data-set"); put(l); set(l); });
})();

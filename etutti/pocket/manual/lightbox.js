/* ============================================================
   eTuttino POCKET manual — image viewer (copy of etutti/manuais/lightbox.js). Every <a class="zoomable"> wraps a small
   picture and links to the full-resolution one; without JS the link just
   opens the big image. With JS it opens in an overlay:
     - first it fits the screen; click (or Enter / Space) for 100 %, then
       drag or scroll to look around; click again to fit;
     - ← / → step through the pictures of the same language, Esc closes.
   ============================================================ */
(function () {
  "use strict";

  const overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.hidden = true;
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.innerHTML =
    '<div class="lightbox-stage"><img class="lightbox-img" alt="" /></div>' +
    '<p class="lightbox-caption"></p>' +
    '<button type="button" class="lightbox-btn lightbox-close" aria-label="Fechar">✕</button>' +
    '<button type="button" class="lightbox-btn lightbox-prev" aria-label="Anterior">‹</button>' +
    '<button type="button" class="lightbox-btn lightbox-next" aria-label="Próxima">›</button>';
  document.body.appendChild(overlay);

  const stage = overlay.querySelector(".lightbox-stage");
  const img = overlay.querySelector(".lightbox-img");
  const caption = overlay.querySelector(".lightbox-caption");
  let list = [];
  let index = 0;
  let lastFocus = null;
  let drag = null;

  function visibleLinks() {
    return Array.from(document.querySelectorAll("a.zoomable")).filter((a) => a.offsetParent !== null);
  }

  function show(i) {
    index = (i + list.length) % list.length;
    const link = list[index];
    const small = link.querySelector("img");
    overlay.classList.remove("is-zoomed");
    img.src = link.href;
    img.alt = small ? small.alt : "";
    const fig = link.closest("figure");
    const cap = fig && fig.querySelector("figcaption");
    caption.textContent = cap ? cap.textContent.trim() : img.alt;
    stage.scrollTo(0, 0);
  }

  function open(link) {
    list = visibleLinks();
    lastFocus = document.activeElement;
    overlay.hidden = false;
    document.documentElement.classList.add("lightbox-open");
    show(list.indexOf(link));
    overlay.querySelector(".lightbox-close").focus();
  }

  function close() {
    overlay.hidden = true;
    img.removeAttribute("src");
    document.documentElement.classList.remove("lightbox-open");
    if (lastFocus) lastFocus.focus();
  }

  // Zoom to 100 % around the clicked point.
  function toggleZoom(event) {
    const zoomed = overlay.classList.toggle("is-zoomed");
    if (!zoomed || !event) return;
    const r = img.getBoundingClientRect();
    const fx = (event.clientX - r.left) / r.width;
    const fy = (event.clientY - r.top) / r.height;
    requestAnimationFrame(() => {
      stage.scrollLeft = fx * img.naturalWidth - stage.clientWidth / 2;
      stage.scrollTop = fy * img.naturalHeight - stage.clientHeight / 2;
    });
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest && event.target.closest("a.zoomable");
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey) return;
    event.preventDefault();
    open(link);
  });

  img.addEventListener("click", (event) => {
    if (drag && drag.moved) return;
    toggleZoom(event);
  });
  stage.addEventListener("pointerdown", (event) => {
    if (!overlay.classList.contains("is-zoomed")) return;
    drag = { x: event.clientX, y: event.clientY, left: stage.scrollLeft, top: stage.scrollTop, moved: false };
  });
  stage.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
    stage.scrollLeft = drag.left - dx;
    stage.scrollTop = drag.top - dy;
  });
  window.addEventListener("pointerup", () => {
    setTimeout(() => { drag = null; }, 0);
  });
  stage.addEventListener("click", (event) => {
    if (event.target === stage) close();
  });
  overlay.querySelector(".lightbox-close").addEventListener("click", close);
  overlay.querySelector(".lightbox-prev").addEventListener("click", () => show(index - 1));
  overlay.querySelector(".lightbox-next").addEventListener("click", () => show(index + 1));
  document.addEventListener("keydown", (event) => {
    if (overlay.hidden) return;
    if (event.key === "Escape") close();
    else if (event.key === "ArrowLeft") show(index - 1);
    else if (event.key === "ArrowRight") show(index + 1);
    else if ((event.key === "Enter" || event.key === " ") && document.activeElement === img) toggleZoom();
    else return;
    event.preventDefault();
  });
})();

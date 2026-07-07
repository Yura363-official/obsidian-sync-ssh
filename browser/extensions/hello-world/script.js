// Простое расширение-пример для Aurora.
// Добавляет ненавязчивый бейдж в правом нижнем углу страницы.
(function () {
  if (window.__auroraHelloShown) return;
  window.__auroraHelloShown = true;

  const badge = document.createElement("div");
  badge.textContent = "✦ Aurora";
  Object.assign(badge.style, {
    position: "fixed",
    right: "14px",
    bottom: "14px",
    zIndex: 2147483647,
    padding: "6px 12px",
    borderRadius: "999px",
    font: "600 12px/1 -apple-system, Segoe UI, sans-serif",
    color: "#fff",
    background: "linear-gradient(135deg,#6c8cff,#9a6cff)",
    boxShadow: "0 6px 20px rgba(0,0,0,.25)",
    cursor: "pointer",
    opacity: "0.9",
  });
  badge.title = "Это расширение-пример Aurora. Отключить можно в aurora://extensions";
  badge.addEventListener("click", () => badge.remove());
  document.body && document.body.appendChild(badge);
})();

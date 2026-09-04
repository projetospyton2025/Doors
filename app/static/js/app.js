(() => {
  const loadingBar = document.getElementById("loading-bar");
  const toastStack = document.getElementById("toast-stack");
  let pending = 0;

  function setLoading(on) {
    if (!loadingBar) return;
    pending += on ? 1 : -1;
    pending = Math.max(pending, 0);
    loadingBar.hidden = pending === 0;
    loadingBar.classList.toggle("is-on", pending > 0);
  }

  function toast(message, type = "info") {
    if (!toastStack) return;
    const item = document.createElement("div");
    item.className = `toast ${type}`;
    item.textContent = message;
    toastStack.appendChild(item);
    setTimeout(() => item.remove(), 4200);
  }

  async function request(url, options = {}) {
    setLoading(true);
    try {
      const response = await fetch(url, {
        headers: { Accept: "application/json", ...(options.headers || {}) },
        ...options,
      });
      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json") ? await response.json() : null;
      if (!response.ok) {
        const detail = payload && payload.detail;
        const message = (detail && (detail.message || detail)) || "Não foi possível concluir a operação.";
        const error = new Error(typeof message === "string" ? message : "Não foi possível concluir a operação.");
        error.field = detail && detail.field;
        throw error;
      }
      return payload;
    } finally {
      setLoading(false);
    }
  }

  function openOverlay(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.hidden = false;
    overlay.classList.add("is-open");
  }

  function closeOverlay(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.remove("is-open");
    overlay.hidden = true;
  }

  document.addEventListener("click", (event) => {
    const closer = event.target.closest("[data-close]");
    if (closer) {
      closeOverlay(closer.getAttribute("data-close"));
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      document.querySelectorAll(".overlay.is-open").forEach((overlay) => {
        overlay.classList.remove("is-open");
        overlay.hidden = true;
      });
    }
  });

  window.Doors = { request, toast, openOverlay, closeOverlay, setLoading };
})();

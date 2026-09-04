(() => {
  async function loadStats() {
    const stats = await window.Doors.request("/api/dashboard");
    Object.entries(stats).forEach(([key, value]) => {
      const node = document.querySelector(`[data-stat="${key}"]`);
      if (node) node.textContent = value;
    });
  }

  document.querySelectorAll(".stat-card[data-href]").forEach((card) => {
    card.addEventListener("click", () => {
      window.location.href = card.getAttribute("data-href");
    });
  });

  loadStats().catch((error) => window.Doors.toast(error.message, "error"));
})();

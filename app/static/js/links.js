(() => {
  const state = {
    q: "",
    plan: "",
    linkType: "",
  };

  const body = document.getElementById("links-body");
  const cards = document.getElementById("links-cards");
  const count = document.getElementById("links-count");
  const searchInput = document.getElementById("search-input");
  let searchTimer = null;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function params() {
    const query = new URLSearchParams();
    if (state.q) query.set("q", state.q);
    if (state.plan) query.set("plan", state.plan);
    if (state.linkType) query.set("link_type", state.linkType);
    return query;
  }

  function renderItems(items) {
    if (!items.length) {
      body.innerHTML = `<tr><td colspan="4"><div class="empty-state">Nenhum link de direcionamento encontrado.</div></td></tr>`;
      cards.innerHTML = `<div class="card empty-state">Nenhum link de direcionamento encontrado.</div>`;
      count.textContent = "";
      return;
    }
    body.innerHTML = items.map((item) => `
      <tr>
        <td><span class="badge ${escapeHtml(item.plan)}">${escapeHtml(item.plan_label)}</span></td>
        <td title="${escapeHtml(item.app_name)}">
          <a href="/applications?plan=${encodeURIComponent(item.plan)}">${escapeHtml(item.app_name)}</a>
        </td>
        <td><span class="badge link-${escapeHtml(item.link_type)}">${escapeHtml(item.link_label)}</span></td>
        <td title="${escapeHtml(item.url)}">
          <a class="external-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.url)}</a>
        </td>
      </tr>
    `).join("");

    cards.innerHTML = items.map((item) => `
      <article class="card">
        <div class="toolbar" style="justify-content:space-between">
          <strong>${escapeHtml(item.app_name)}</strong>
          <span class="badge ${escapeHtml(item.plan)}">${escapeHtml(item.plan_label)}</span>
        </div>
        <p><span class="badge link-${escapeHtml(item.link_type)}">${escapeHtml(item.link_label)}</span></p>
        <p><a class="external-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.url)}</a></p>
      </article>
    `).join("");

    count.textContent = `${items.length} link${items.length === 1 ? "" : "s"}`;
  }

  async function loadLinks() {
    const data = await window.Doors.request(`/api/links?${params().toString()}`);
    renderItems(data.items);
  }

  document.querySelectorAll(".plan-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      state.plan = tab.dataset.plan || "";
      document.querySelectorAll(".plan-tab").forEach((item) => {
        item.classList.toggle("is-active", item === tab);
      });
      loadLinks().catch((error) => window.Doors.toast(error.message, "error"));
    });
  });

  document.querySelectorAll("[data-link-type]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const value = chip.dataset.linkType || "";
      state.linkType = state.linkType === value ? "" : value;
      document.querySelectorAll("[data-link-type]").forEach((item) => {
        item.classList.toggle("is-active", item.dataset.linkType === state.linkType);
      });
      loadLinks().catch((error) => window.Doors.toast(error.message, "error"));
    });
  });

  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.q = searchInput.value.trim();
      loadLinks().catch((error) => window.Doors.toast(error.message, "error"));
    }, 250);
  });

  loadLinks().catch((error) => window.Doors.toast(error.message, "error"));
})();

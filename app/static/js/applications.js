(() => {
  const state = {
    q: "",
    plan: "",
    language: "",
    docker: "",
    nginx: "",
    sort: "app_name",
    order: "asc",
    page: 1,
    pageSize: 10,
    items: [],
    selected: new Map(),
    pendingDelete: [],
  };

  const body = document.getElementById("apps-body");
  const cards = document.getElementById("apps-cards");
  const pageInfo = document.getElementById("page-info");
  const form = document.getElementById("app-form");
  const dockerInput = form.elements.docker;
  const dockerLabel = document.getElementById("docker-label");
  const searchInput = document.getElementById("search-input");
  let searchTimer = null;

  function params() {
    const query = new URLSearchParams();
    if (state.q) query.set("q", state.q);
    if (state.plan) query.set("plan", state.plan);
    if (state.language) query.set("language", state.language);
    if (state.docker) query.set("docker", state.docker);
    if (state.nginx) query.set("nginx", state.nginx);
    query.set("sort", state.sort);
    query.set("order", state.order);
    query.set("page", String(state.page));
    query.set("page_size", String(state.pageSize));
    return query;
  }

  function applyUrlFilters() {
    const url = new URL(window.location.href);
    state.plan = url.searchParams.get("plan") || "";
    state.language = url.searchParams.get("language") || "";
    state.docker = url.searchParams.get("docker") || "";
    state.nginx = url.searchParams.get("nginx") || "";
    document.querySelectorAll(".plan-tab").forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.plan === state.plan);
    });
    document.querySelectorAll(".chip").forEach((chip) => {
      const key = chip.dataset.filter;
      chip.classList.toggle("is-active", state[key] === chip.dataset.value);
    });
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function languageClass(name) {
    const raw = String(name || "").toLowerCase();
    if (raw === "c++") return "cpp";
    return raw.replace(/[^a-z0-9-]+/g, "");
  }

  function actionButtons(item) {
    return `
      <div class="cell-actions">
        <button class="icon-button ghost" data-view="${item.id}" title="Visualizar" aria-label="Visualizar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"></path><circle cx="12" cy="12" r="3"></circle></svg>
        </button>
        <button class="icon-button ghost" data-edit="${item.id}" title="Editar" aria-label="Editar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
        </button>
        <button class="icon-button danger" data-delete="${item.id}" data-name="${escapeHtml(item.app_name)}" title="Excluir" aria-label="Excluir">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M19 6l-1 14H6L5 6"></path></svg>
        </button>
      </div>
    `;
  }

  function rowCheckbox(item) {
    const checked = state.selected.has(item.id) ? "checked" : "";
    return `<input class="row-check row-select" type="checkbox" data-id="${item.id}" data-name="${escapeHtml(item.app_name)}" ${checked} aria-label="Selecionar ${escapeHtml(item.app_name)}">`;
  }

  function syncSelectionUi() {
    const count = state.selected.size;
    const visibleIds = state.items.map((item) => item.id);
    const selectedVisible = visibleIds.filter((id) => state.selected.has(id)).length;
    const bulkBtn = document.getElementById("btn-bulk-delete");
    const countLabel = document.getElementById("selection-count");
    bulkBtn.disabled = count === 0;
    bulkBtn.title = count ? `Excluir ${count} selecionada(s)` : "Excluir selecionadas";
    bulkBtn.setAttribute("aria-label", bulkBtn.title);
    countLabel.textContent = count
      ? `${count} selecionada(s)`
      : "Nenhuma selecionada";
    document.querySelectorAll(".select-all").forEach((box) => {
      box.checked = visibleIds.length > 0 && selectedVisible === visibleIds.length;
      box.indeterminate = selectedVisible > 0 && selectedVisible < visibleIds.length;
    });
    document.querySelectorAll("tr[data-id], article.card[data-id]").forEach((node) => {
      node.classList.toggle("is-selected", state.selected.has(Number(node.dataset.id)));
    });
  }

  function setSelected(id, name, on) {
    if (on) state.selected.set(id, name);
    else state.selected.delete(id);
    document.querySelectorAll(`.row-select[data-id="${id}"]`).forEach((box) => {
      box.checked = on;
    });
  }

  function openDeleteConfirm(items) {
    state.pendingDelete = items;
    const text = document.getElementById("delete-text");
    const title = document.getElementById("delete-title");
    if (items.length === 1) {
      title.textContent = "Excluir aplicação";
      text.textContent = `Excluir definitivamente "${items[0].name}"?`;
    } else {
      title.textContent = "Excluir aplicações";
      text.textContent = `Excluir definitivamente ${items.length} aplicações? Esta ação não pode ser desfeita.`;
    }
    window.Doors.openOverlay("delete-overlay");
  }

  function renderItems(items) {
    state.items = items;
    if (!items.length) {
      body.innerHTML = `<tr><td colspan="11"><div class="empty-state">Nenhum registro encontrado.</div></td></tr>`;
      cards.innerHTML = `<div class="card empty-state">Nenhum registro encontrado.</div>`;
      syncSelectionUi();
      return;
    }
    body.innerHTML = items.map((item) => `
      <tr data-id="${item.id}" class="${state.selected.has(item.id) ? "is-selected" : ""}">
        <td class="col-select">${rowCheckbox(item)}</td>
        <td title="${escapeHtml(item.plan_label)}"><span class="badge ${escapeHtml(item.plan)}">${escapeHtml(item.plan_label)}</span></td>
        <td title="${escapeHtml(item.app_name)}">${escapeHtml(item.app_name)}</td>
        <td title="${escapeHtml(item.path)}">${escapeHtml(item.path)}</td>
        <td title="${escapeHtml(item.door)}">${escapeHtml(item.door)}</td>
        <td title="${escapeHtml(item.language)}"><span class="badge ${languageClass(item.language)}">${escapeHtml(item.language)}</span></td>
        <td title="${escapeHtml(item.nginx || "")}">${item.nginx ? `<a href="${escapeHtml(item.nginx)}" target="_blank" rel="noopener">${escapeHtml(item.nginx)}</a>` : "—"}</td>
        <td title="${escapeHtml(item.docker)}"><span class="badge ${item.uses_docker ? "docker-yes" : "docker-no"}">${escapeHtml(item.docker)}</span></td>
        <td title="${escapeHtml(item.github || "")}">${item.github ? escapeHtml(item.github) : "—"}</td>
        <td title="${escapeHtml(item.drive || "")}">${item.drive ? escapeHtml(item.drive) : "—"}</td>
        <td>${actionButtons(item)}</td>
      </tr>
    `).join("");

    cards.innerHTML = items.map((item) => `
      <article class="card ${state.selected.has(item.id) ? "is-selected" : ""}" data-id="${item.id}">
        <div class="toolbar" style="justify-content:space-between">
          <label class="select-all-label">
            ${rowCheckbox(item)}
            <strong>${escapeHtml(item.app_name)}</strong>
          </label>
          <span class="badge ${escapeHtml(item.plan)}">${escapeHtml(item.plan_label)}</span>
        </div>
        <p class="muted">${escapeHtml(item.path)}</p>
        <p>Door <strong>${escapeHtml(item.door)}</strong> · ${escapeHtml(item.language)} · Docker ${escapeHtml(item.docker)}</p>
        ${actionButtons(item)}
      </article>
    `).join("");
    syncSelectionUi();
  }

  async function loadLanguages() {
    const languages = await window.Doors.request("/api/languages");
    const select = form.elements.language;
    select.innerHTML = languages.map((item) => `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)}</option>`).join("");
  }

  async function loadApplications() {
    const data = await window.Doors.request(`/api/applications?${params().toString()}`);
    renderItems(data.items);
    pageInfo.textContent = data.total
      ? `${data.total} registro(s) · página ${data.page} de ${data.pages}`
      : "Nenhum registro";
    document.getElementById("prev-page").disabled = data.page <= 1;
    document.getElementById("next-page").disabled = data.page >= data.pages || data.total === 0;
  }

  function clearErrors() {
    form.querySelectorAll("[data-error]").forEach((node) => {
      node.textContent = "";
    });
  }

  function showFieldError(field, message) {
    const node = form.querySelector(`[data-error="${field}"]`);
    if (node) node.textContent = message;
  }

  function fillForm(item) {
    form.reset();
    clearErrors();
    form.elements.id.value = item ? item.id : "";
    form.elements.app_name.value = item ? item.app_name : "";
    form.elements.path.value = item ? item.path : "";
    form.elements.door.value = item ? item.door : "";
    form.elements.language.value = item ? item.language : form.elements.language.value;
    form.elements.plan.value = item ? item.plan : state.plan || "work";
    form.elements.nginx.value = item && item.nginx ? item.nginx : "";
    form.elements.github.value = item && item.github ? item.github : "";
    form.elements.drive.value = item && item.drive ? item.drive : "";
    dockerInput.checked = item ? item.uses_docker : false;
    dockerLabel.textContent = dockerInput.checked ? "Sim" : "Não";
    document.getElementById("form-title").textContent = item ? item.app_name : "Nova aplicação";
  }

  async function openEdit(id) {
    const item = await window.Doors.request(`/api/applications/${id}`);
    fillForm(item);
    window.Doors.openOverlay("form-overlay");
  }

  async function openView(id) {
    const item = await window.Doors.request(`/api/applications/${id}`);
    const rows = [
      ["Plano", item.plan_label],
      ["APP NAME", item.app_name],
      ["PATH", item.path],
      ["DOOR", item.door],
      ["LANGUAGE", item.language],
      ["NGINX", item.nginx || "—"],
      ["DOCKER", item.docker],
      ["GITHUB", item.github || "—"],
      ["DRIVE", item.drive || "—"],
    ];
    document.getElementById("view-body").innerHTML = rows.map(([label, value]) => (
      `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`
    )).join("");
    document.getElementById("view-title").textContent = item.app_name;
    window.Doors.openOverlay("view-overlay");
  }

  document.addEventListener("click", async (event) => {
    const viewBtn = event.target.closest("[data-view]");
    const editBtn = event.target.closest("[data-edit]");
    const deleteBtn = event.target.closest("[data-delete]");
    try {
      if (viewBtn) await openView(viewBtn.dataset.view);
      if (editBtn) await openEdit(editBtn.dataset.edit);
      if (deleteBtn) {
        openDeleteConfirm([{ id: Number(deleteBtn.dataset.delete), name: deleteBtn.dataset.name }]);
      }
    } catch (error) {
      window.Doors.toast(error.message, "error");
    }
  });

  document.querySelectorAll(".plan-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      state.plan = tab.dataset.plan;
      state.page = 1;
      document.querySelectorAll(".plan-tab").forEach((item) => item.classList.toggle("is-active", item === tab));
      loadApplications().catch((error) => window.Doors.toast(error.message, "error"));
    });
  });

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const key = chip.dataset.filter;
      state[key] = state[key] === chip.dataset.value ? "" : chip.dataset.value;
      state.page = 1;
      document.querySelectorAll(`.chip[data-filter="${key}"]`).forEach((item) => {
        item.classList.toggle("is-active", item.dataset.value === state[key]);
      });
      loadApplications().catch((error) => window.Doors.toast(error.message, "error"));
    });
  });

  document.querySelectorAll("th[data-sort]").forEach((header) => {
    header.addEventListener("click", () => {
      if (state.sort === header.dataset.sort) {
        state.order = state.order === "asc" ? "desc" : "asc";
      } else {
        state.sort = header.dataset.sort;
        state.order = "asc";
      }
      loadApplications().catch((error) => window.Doors.toast(error.message, "error"));
    });
  });

  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.q = searchInput.value.trim();
      state.page = 1;
      loadApplications().catch((error) => window.Doors.toast(error.message, "error"));
    }, 250);
  });

  document.getElementById("prev-page").addEventListener("click", () => {
    state.page = Math.max(1, state.page - 1);
    loadApplications().catch((error) => window.Doors.toast(error.message, "error"));
  });

  document.getElementById("next-page").addEventListener("click", () => {
    state.page += 1;
    loadApplications().catch((error) => window.Doors.toast(error.message, "error"));
  });

  document.getElementById("btn-add").addEventListener("click", () => {
    fillForm(null);
    window.Doors.openOverlay("form-overlay");
  });

  document.getElementById("btn-bulk-delete").addEventListener("click", () => {
    if (!state.selected.size) return;
    openDeleteConfirm([...state.selected.entries()].map(([id, name]) => ({ id, name })));
  });

  document.addEventListener("change", (event) => {
    const selectAll = event.target.closest(".select-all");
    if (selectAll) {
      const on = selectAll.checked;
      state.items.forEach((item) => setSelected(item.id, item.app_name, on));
      syncSelectionUi();
      return;
    }
    const row = event.target.closest(".row-select");
    if (!row) return;
    setSelected(Number(row.dataset.id), row.dataset.name, row.checked);
    syncSelectionUi();
  });

  dockerInput.addEventListener("change", () => {
    dockerLabel.textContent = dockerInput.checked ? "Sim" : "Não";
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    const payload = {
      app_name: form.elements.app_name.value,
      path: form.elements.path.value,
      door: form.elements.door.value,
      language: form.elements.language.value,
      nginx: form.elements.nginx.value,
      docker: dockerInput.checked ? "Sim" : "Não",
      plan: form.elements.plan.value,
      github: form.elements.github.value,
      drive: form.elements.drive.value,
    };
    const id = form.elements.id.value;
    try {
      await window.Doors.request(id ? `/api/applications/${id}` : "/api/applications", {
        method: id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      window.Doors.closeOverlay("form-overlay");
      window.Doors.toast(id ? "Aplicação atualizada." : "Aplicação cadastrada.", "success");
      await loadApplications();
    } catch (error) {
      if (error.field) showFieldError(error.field, error.message);
      window.Doors.toast(error.message, "error");
    }
  });

  document.getElementById("confirm-delete").addEventListener("click", async () => {
    if (!state.pendingDelete.length) return;
    const ids = state.pendingDelete.map((item) => item.id);
    try {
      if (ids.length === 1) {
        await window.Doors.request(`/api/applications/${ids[0]}`, { method: "DELETE" });
        window.Doors.toast("Aplicação excluída.", "success");
      } else {
        const result = await window.Doors.request("/api/applications/bulk-delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ids }),
        });
        window.Doors.toast(result.message, "success");
      }
      ids.forEach((id) => state.selected.delete(id));
      state.pendingDelete = [];
      window.Doors.closeOverlay("delete-overlay");
      await loadApplications();
    } catch (error) {
      window.Doors.toast(error.message, "error");
    }
  });

  function exportUrl(kind) {
    const query = params();
    query.delete("page");
    query.delete("page_size");
    return window.Doors.withRoot(`/api/export/${kind}?${query.toString()}`);
  }

  document.getElementById("btn-export-csv").addEventListener("click", () => {
    window.location.href = exportUrl("csv");
  });
  document.getElementById("btn-export-xlsx").addEventListener("click", () => {
    window.location.href = exportUrl("xlsx");
  });

  document.getElementById("btn-import").addEventListener("click", () => {
    document.getElementById("file-import").click();
  });

  document.getElementById("file-import").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const data = new FormData();
    data.append("file", file);
    window.Doors.setLoading(true);
    try {
      const response = await fetch(window.Doors.withRoot("/api/import/xlsx"), { method: "POST", body: data });
      const payload = await response.json();
      if (!response.ok) throw new Error((payload.detail && payload.detail.message) || "Falha na importação.");
      window.Doors.toast(`${payload.created} registro(s) importado(s).`, "success");
      await loadApplications();
    } catch (error) {
      window.Doors.toast(error.message, "error");
    } finally {
      window.Doors.setLoading(false);
      event.target.value = "";
    }
  });

  applyUrlFilters();
  Promise.all([loadLanguages(), loadApplications()]).catch((error) => {
    window.Doors.toast(error.message, "error");
  });
})();

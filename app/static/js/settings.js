(() => {
  const list = document.getElementById("language-list");
  const form = document.getElementById("language-form");

  async function loadLanguages() {
    const languages = await window.Doors.request("/api/languages");
    list.innerHTML = "";
    languages.forEach((language) => {
      const chip = document.createElement("span");
      chip.className = "chip is-active";
      chip.textContent = language.name;
      list.appendChild(chip);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = new FormData(form).get("name");
    try {
      await window.Doors.request("/api/languages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      form.reset();
      window.Doors.toast("Linguagem cadastrada.", "success");
      await loadLanguages();
    } catch (error) {
      window.Doors.toast(error.message, "error");
    }
  });

  loadLanguages().catch((error) => window.Doors.toast(error.message, "error"));
})();

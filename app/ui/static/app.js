(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function showStage(name) {
    $$("[data-stage-panel]").forEach((el) => {
      const on = el.getAttribute("data-stage-panel") === name;
      el.hidden = !on;
      el.classList.toggle("active", on);
    });
    if (name === "settings") refreshStatus();
    if (name === "workshop") {
      refreshPackages();
      refreshArtifacts();
    }
  }

  function showPanel(name) {
    $$(".rail-item").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-panel") === name);
    });
    $$("[data-panel-view]").forEach((el) => {
      const on = el.getAttribute("data-panel-view") === name;
      el.hidden = !on;
      el.classList.toggle("active", on);
    });
  }

  async function api(path, opts) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      ...opts,
    });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { detail: text };
    }
    if (!res.ok) {
      const msg = data.detail || data.message || res.statusText;
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  }

  function writeOut(el, data, isError = false) {
    el.hidden = false;
    el.classList.toggle("error", isError);
    el.textContent =
      typeof data === "string" ? data : JSON.stringify(data, null, 2);
  }

  function bindForm(formId, outId, buildRequest) {
    const form = $(formId);
    const out = $(outId);
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      try {
        const { path, body } = buildRequest(new FormData(form));
        const data = await api(path, {
          method: "POST",
          body: JSON.stringify(body),
        });
        writeOut(out, data, false);
        if (formId === "form-compile" || formId === "form-compose") {
          refreshPackages();
          refreshArtifacts();
        }
      } catch (err) {
        writeOut(out, String(err.message || err), true);
      } finally {
        btn.disabled = false;
      }
    });
  }

  async function refreshStatus() {
    const out = $("#out-status");
    try {
      const data = await api("/api/status");
      writeOut(out, data, false);
    } catch (err) {
      writeOut(out, String(err.message || err), true);
    }
  }

  async function refreshPackages() {
    const ul = $("#package-list");
    if (!ul) return;
    try {
      const data = await api("/api/packages");
      ul.innerHTML = (data.items || [])
        .map(
          (it) =>
            `<li><strong>${escapeHtml(it.name)}</strong><br /><span>${escapeHtml(
              it.path
            )}</span></li>`
        )
        .join("") || "<li>暂无 package</li>";
    } catch {
      ul.innerHTML = "<li>无法读取 packages</li>";
    }
  }

  async function refreshArtifacts() {
    const ul = $("#artifact-list");
    if (!ul) return;
    try {
      const data = await api("/api/artifacts");
      const rows = [
        ...(data.compose || []).map(
          (c) =>
            `<li><strong>${escapeHtml(c.kind)}</strong> — ${escapeHtml(
              c.path
            )}</li>`
        ),
        ...(data.media || []).map(
          (m) =>
            `<li><strong>${escapeHtml(m.suffix)}</strong> — ${escapeHtml(
              m.path
            )}</li>`
        ),
      ];
      ul.innerHTML = rows.join("") || "<li>暂无产物</li>";
    } catch {
      ul.innerHTML = "<li>无法读取产物</li>";
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  // Navigation
  $$("[data-stage]").forEach((el) => {
    el.addEventListener("click", () => showStage(el.getAttribute("data-stage")));
  });
  $$(".rail-item").forEach((btn) => {
    btn.addEventListener("click", () => showPanel(btn.getAttribute("data-panel")));
  });

  bindForm("#form-capture", "#out-capture", (fd) => ({
    path: "/api/capture",
    body: { kind: fd.get("kind"), target: fd.get("target") },
  }));

  bindForm("#form-compile", "#out-compile", (fd) => ({
    path: "/api/compile",
    body: {
      path: fd.get("path"),
      from_card: true,
      animate: fd.get("animate") === "on",
      fast: true,
    },
  }));

  bindForm("#form-reconstruct", "#out-reconstruct", (fd) => ({
    path: "/api/reconstruct",
    body: { from_index: true, view: fd.get("view") },
  }));

  bindForm("#form-retrieve", "#out-retrieve", (fd) => ({
    path: "/api/retrieve",
    body: {
      query: fd.get("query"),
      top_k: Number(fd.get("top_k") || 5),
    },
  }));

  bindForm("#form-compose", "#out-compose", (fd) => ({
    path: "/api/compose",
    body: {
      query: fd.get("query"),
      kind: fd.get("kind"),
      top_k: 5,
    },
  }));

  api("/api/health")
    .then((h) => {
      $("#health-line").textContent = `${h.product} · ${h.engine} · UI ready`;
    })
    .catch(() => {
      $("#health-line").textContent = "API offline";
    });
})();

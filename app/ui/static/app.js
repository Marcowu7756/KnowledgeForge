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

  function ensureProgress(form) {
    let bar = form.querySelector(".progress");
    if (!bar) {
      bar = document.createElement("div");
      bar.className = "progress";
      bar.innerHTML =
        '<div class="progress-track"><div class="progress-fill"></div></div><div class="progress-label"></div>';
      form.appendChild(bar);
    }
    return bar;
  }

  function setProgress(form, pct, message, visible = true) {
    const bar = ensureProgress(form);
    bar.hidden = !visible;
    const fill = bar.querySelector(".progress-fill");
    const label = bar.querySelector(".progress-label");
    fill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    label.textContent = message || `${pct}%`;
  }

  async function pollJob(jobId, form, out) {
    for (;;) {
      const snap = await api(`/api/jobs/${jobId}`);
      setProgress(form, snap.progress || 0, `${snap.message} (${snap.progress || 0}%)`);
      if (snap.status === "done") {
        writeOut(out, snap.result, false);
        setProgress(form, 100, "完成", true);
        return snap.result;
      }
      if (snap.status === "error") {
        writeOut(out, snap.error || "job failed", true);
        setProgress(form, snap.progress || 0, "失败", true);
        throw new Error(snap.error || "job failed");
      }
      await new Promise((r) => setTimeout(r, 400));
    }
  }

  function bindForm(formId, outId, buildRequest) {
    const form = $(formId);
    const out = $(outId);
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      setProgress(form, 2, "提交中…", true);
      try {
        const { path, body } = buildRequest(new FormData(form));
        const data = await api(path, {
          method: "POST",
          body: JSON.stringify({ ...body, async_job: true }),
        });
        if (data.job_id) {
          await pollJob(data.job_id, form, out);
        } else {
          writeOut(out, data, false);
          setProgress(form, 100, "完成", true);
        }
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
      ul.innerHTML =
        (data.items || [])
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
            `<li><button type="button" class="preview-link" data-path="${escapeAttr(
              c.path
            )}"><strong>${escapeHtml(c.kind)}</strong> — ${escapeHtml(
              c.path
            )}</button></li>`
        ),
        ...(data.media || []).map(
          (m) =>
            `<li><button type="button" class="preview-link" data-path="${escapeAttr(
              m.path
            )}"><strong>${escapeHtml(m.suffix)}</strong> — ${escapeHtml(
              m.path
            )}</button></li>`
        ),
      ];
      ul.innerHTML = rows.join("") || "<li>暂无产物</li>";
      ul.querySelectorAll(".preview-link").forEach((btn) => {
        btn.addEventListener("click", () => openPreview(btn.getAttribute("data-path")));
      });
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

  function escapeAttr(s) {
    return escapeHtml(s).replaceAll("'", "&#39;");
  }

  async function openPreview(path) {
    const modal = $("#preview-modal");
    const body = $("#preview-body");
    const title = $("#preview-title");
    modal.hidden = false;
    title.textContent = path;
    body.innerHTML = "<p class='muted'>加载中…</p>";
    try {
      const data = await api(`/api/preview?path=${encodeURIComponent(path)}`);
      title.textContent = data.name || path;
      if (data.kind === "text") {
        body.innerHTML = `<pre class="preview-text">${escapeHtml(data.text || "")}</pre>`;
      } else if (data.suffix === ".gif" || data.suffix === ".png" || data.suffix === ".jpg" || data.suffix === ".jpeg" || data.suffix === ".webp") {
        body.innerHTML = `<img class="preview-media" src="${data.file_url}" alt="${escapeAttr(
          data.name
        )}" />`;
      } else if (data.suffix === ".wav") {
        body.innerHTML = `<audio class="preview-media" controls src="${data.file_url}"></audio>`;
      } else {
        body.innerHTML = `<p><a href="${data.file_url}" target="_blank" rel="noopener">打开文件</a></p>`;
      }
    } catch (err) {
      body.innerHTML = `<p class="error-text">${escapeHtml(String(err.message || err))}</p>`;
    }
  }

  function closePreview() {
    const modal = $("#preview-modal");
    modal.hidden = true;
    $("#preview-body").innerHTML = "";
  }

  $$("[data-stage]").forEach((el) => {
    el.addEventListener("click", () => showStage(el.getAttribute("data-stage")));
  });
  $$(".rail-item").forEach((btn) => {
    btn.addEventListener("click", () => showPanel(btn.getAttribute("data-panel")));
  });
  $("#preview-close")?.addEventListener("click", closePreview);
  $("#preview-modal")?.addEventListener("click", (e) => {
    if (e.target.id === "preview-modal") closePreview();
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
      $("#health-line").textContent = `${h.product} · ${h.engine} · UI ${h.ui_version || ""}`;
    })
    .catch(() => {
      $("#health-line").textContent = "API offline";
    });
})();

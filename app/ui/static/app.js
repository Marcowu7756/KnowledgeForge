(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  let lastComposeDraftPath = "";
  let accessLane = "general";

  const LANE_HINTS = {
    general: "public / internal · 不含 SETV / Factor / AShare",
    proprietary: "含 restricted · SETV / FactorLib / AShareLib · 默认不可外发",
  };

  function setAccessLane(lane) {
    accessLane = lane === "proprietary" ? "proprietary" : "general";
    $$(".lane-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-lane") === accessLane);
    });
    const hint = $("#lane-hint");
    if (hint) hint.textContent = LANE_HINTS[accessLane];
    const retrieveLane = $("#retrieve-lane");
    const composeLane = $("#compose-lane");
    if (retrieveLane) retrieveLane.value = accessLane;
    if (composeLane) composeLane.value = accessLane;
    document.body.dataset.accessLane = accessLane;
    const title = $("#knowledge-lane-title");
    if (title) {
      title.textContent =
        accessLane === "proprietary" ? "知识库 · 专有资产" : "知识库 · 通用";
    }
    refreshKnowledge();
  }

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
      refreshKnowledge();
    }
    if (name === "tasks") refreshJobs();
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

  async function pollJob(jobId, form, out, onDone) {
    for (;;) {
      const snap = await api(`/api/jobs/${jobId}`);
      setProgress(form, snap.progress || 0, `${snap.message} (${snap.progress || 0}%)`);
      if (snap.status === "done") {
        writeOut(out, snap.result, false);
        setProgress(form, 100, "完成", true);
        if (onDone) await onDone(snap.result, snap);
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

  function bindForm(formId, outId, buildRequest, onSuccess) {
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
          await pollJob(data.job_id, form, out, onSuccess);
        } else {
          writeOut(out, data, false);
          setProgress(form, 100, "完成", true);
          if (onSuccess) await onSuccess(data, null);
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

  async function refreshKnowledge() {
    const ul = $("#knowledge-list");
    if (!ul) return;
    try {
      const data = await api(
        `/api/knowledge?lane=${encodeURIComponent(accessLane)}&limit=24`
      );
      const items = data.items || [];
      ul.innerHTML =
        items
          .map(
            (item) => `<li>
          <button type="button" class="preview-link" data-path="${escapeAttr(item.path)}">
            <span class="access-chip access-${escapeAttr(item.classification)}">${escapeHtml(
              item.source_project || item.classification
            )}</span>
            <strong>${escapeHtml(item.name)}</strong>
          </button>
        </li>`
          )
          .join("") ||
        `<li class='muted'>当前层暂无卡片 — ${
          accessLane === "proprietary"
            ? "可先跑 setv snapshot|evolution|family / ecosystem ingest"
            : "可先获取资料"
        }</li>`;
      ul.querySelectorAll(".preview-link").forEach((btn) => {
        btn.addEventListener("click", () =>
          openPreview(btn.getAttribute("data-path"))
        );
      });
    } catch {
      ul.innerHTML = "<li>无法读取知识库</li>";
    }
  }

  async function tryExport(path) {
    if (!path) return;
    try {
      const res = await fetch(`/api/export?path=${encodeURIComponent(path)}`);
      if (!res.ok) {
        const text = await res.text();
        let msg = text;
        try {
          msg = JSON.parse(text).detail || text;
        } catch {
          /* keep */
        }
        alert(`导出被拒绝：${msg}`);
        return;
      }
      const blob = await res.blob();
      const warn = res.headers.get("X-KF-Export-Warning");
      if (warn && !confirm(`${warn}\n\n仍要下载吗？`)) return;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = path.split(/[/\\]/).pop() || "export.bin";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      alert(`导出失败：${err.message || err}`);
    }
  }

  const ACTION_LABELS = {
    capture: "获取",
    compile: "沉淀",
    reconstruct: "重组",
    retrieve: "检索",
    compose: "表达",
  };

  async function refreshJobs() {
    const ul = $("#job-list");
    if (!ul) return;
    try {
      const data = await api("/api/jobs?limit=40");
      const items = data.items || [];
      ul.innerHTML =
        items
          .map(
            (job) => `<li class="job-row">
        <button type="button" class="job-row-btn" data-job-id="${escapeAttr(job.id)}">
          <span class="job-status job-status-${escapeAttr(job.status)}">${escapeHtml(
              job.status
            )}</span>
          <strong>${escapeHtml(ACTION_LABELS[job.action] || job.action)}</strong>
          <span class="job-meta">${escapeHtml(job.message)} · ${job.progress || 0}%</span>
          <span class="job-time">${escapeHtml(job.updated || job.created || "")}</span>
        </button>
      </li>`
          )
          .join("") || "<li class='muted'>暂无任务 — 在车间提交长任务后会出现在这里</li>";
      ul.querySelectorAll(".job-row-btn").forEach((btn) => {
        btn.addEventListener("click", () =>
          showJobDetail(btn.getAttribute("data-job-id"))
        );
      });
    } catch {
      ul.innerHTML = "<li>无法读取任务列表</li>";
    }
  }

  async function showJobDetail(jobId) {
    const detail = $("#out-job-detail");
    const previewBox = $("#job-preview");
    const previewBody = $("#job-preview-body");
    if (!detail) return;
    try {
      const snap = await api(`/api/jobs/${jobId}`);
      writeOut(detail, snap, snap.status === "error");
      if (previewBox) previewBox.hidden = true;
      if (previewBody) previewBody.innerHTML = "";
      if (snap.status === "done" && snap.action === "compose" && snap.result?.draft) {
        await renderInlinePreview(snap.result.draft, previewBody, previewBox);
      }
    } catch (err) {
      writeOut(detail, String(err.message || err), true);
    }
  }

  async function renderInlinePreview(path, bodyEl, boxEl) {
    if (!path || !bodyEl || !boxEl) return;
    boxEl.hidden = false;
    bodyEl.innerHTML = "<p class='muted'>加载中…</p>";
    try {
      const data = await api(`/api/preview?path=${encodeURIComponent(path)}`);
      if (data.kind === "text") {
        bodyEl.innerHTML = `<pre class="preview-text compose-inline-text">${escapeHtml(
          data.text || ""
        )}</pre>`;
      } else {
        bodyEl.innerHTML = `<p class="muted">非文本产物 — 请用全屏或产物列表打开。</p>`;
      }
      lastComposeDraftPath = path;
    } catch (err) {
      bodyEl.innerHTML = `<p class="error-text">${escapeHtml(String(err.message || err))}</p>`;
    }
  }

  async function showComposeInlinePreview(path) {
    await renderInlinePreview(
      path,
      $("#compose-preview-body"),
      $("#compose-preview")
    );
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
      const chip = data.access
        ? `<span class="access-chip access-${escapeAttr(
            data.access.classification
          )}">${escapeHtml(
            data.access.source_project || data.access.classification
          )}</span>`
        : "";
      title.innerHTML = `${chip} ${escapeHtml(data.name || path)}`;
      const exportBtn = data.access?.export_external_allowed
        ? `<p><button type="button" class="btn ghost btn-sm" id="modal-export-btn">导出到本机下载</button></p>`
        : `<p class="muted">外发导出已关闭（${escapeHtml(
            data.access?.policy?.export || "local_only"
          )}）— 仅可在 KF 内预览。</p>`;
      if (data.kind === "text") {
        body.innerHTML = `${exportBtn}<pre class="preview-text">${escapeHtml(
          data.text || ""
        )}</pre>`;
      } else if (
        data.suffix === ".gif" ||
        data.suffix === ".png" ||
        data.suffix === ".jpg" ||
        data.suffix === ".jpeg" ||
        data.suffix === ".webp"
      ) {
        body.innerHTML = `${exportBtn}<img class="preview-media" src="${data.file_url}" alt="${escapeAttr(
          data.name
        )}" />`;
      } else if (data.suffix === ".wav") {
        body.innerHTML = `${exportBtn}<audio class="preview-media" controls src="${data.file_url}"></audio>`;
      } else {
        body.innerHTML = `${exportBtn}<p><a href="${data.file_url}" target="_blank" rel="noopener">打开文件</a></p>`;
      }
      $("#modal-export-btn")?.addEventListener("click", () => tryExport(path));
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
  $("#compose-preview-modal")?.addEventListener("click", () => {
    if (lastComposeDraftPath) openPreview(lastComposeDraftPath);
  });
  $("#job-preview-modal")?.addEventListener("click", () => {
    if (lastComposeDraftPath) openPreview(lastComposeDraftPath);
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
      access_lane: fd.get("access_lane") || accessLane,
    },
  }));

  bindForm(
    "#form-compose",
    "#out-compose",
    (fd) => ({
      path: "/api/compose",
      body: {
        query: fd.get("query"),
        kind: fd.get("kind"),
        top_k: 5,
        access_lane: fd.get("access_lane") || accessLane,
      },
    }),
    async (result) => {
      if (result?.draft) {
        await showComposeInlinePreview(result.draft);
      }
    }
  );

  $$(".lane-btn").forEach((btn) => {
    btn.addEventListener("click", () =>
      setAccessLane(btn.getAttribute("data-lane"))
    );
  });
  $("#compose-export-btn")?.addEventListener("click", () => {
    if (lastComposeDraftPath) tryExport(lastComposeDraftPath);
  });

  setAccessLane("general");

  api("/api/health")
    .then((h) => {
      $("#health-line").textContent = `${h.product} · ${h.engine} · UI ${h.ui_version || ""}`;
    })
    .catch(() => {
      $("#health-line").textContent = "API offline";
    });
})();

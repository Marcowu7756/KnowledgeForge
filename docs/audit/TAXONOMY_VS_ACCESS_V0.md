# Taxonomy vs Access v0

```yaml
doc_id: KF-TAXONOMY-VS-ACCESS-V0
as_of: 2026-08-29
status: SOT · orthogonal axes
```

\[
\boxed{\mathrm{taxonomy.path}\neq\mathrm{access.classification}}
\qquad
\boxed{\mathrm{depth\ target = 4\text{–}5}}
\]

## 1. Two axes

| Axis | Field | Answers | Example |
|------|-------|---------|---------|
| **Taxonomy**（纲举目张） | `taxonomy.path` | Where does this card sit on the subject tree? | `公开媒体 > 捕获 > YouTube > …` |
| **Access**（流动边界） | `access.classification` (+ lane) | Where may this card flow? | `public` / `restricted` |

Do **not** derive one from the other. Legal (if rare): deep taxonomy + `public`, or shallow taxonomy + `restricted`.

## 2. Depth convention

- Display slots (`LEVEL_NAMES`): domain → category → subcategory → topic → leaf — **not** access levels.
- Everyday target: **4 segments**; optional 5th when the leaf is still too coarse.
- Clamp: `MAX_TAXONOMY_DEPTH = 5`.

Biological analogy: `生物 > 动物 > 哺乳动物 > 灵长类 > 人`.

## 3. Default roots (ingest)

| Ingest | Default taxonomy | Default access |
|--------|------------------|----------------|
| Generic capture (youtube / bilibili / file / …) | `公开媒体 > 捕获 > {source} > {title}` | `public` |
| Ecosystem setv / factorlib / asharelib | `专有知识 > {Project} > …` | `restricted` |
| SETV artifact cite | `专有知识 > SETV > …` | `restricted` |

Registry: [`app/knowledge/taxonomy_registry.yaml`](../../app/knowledge/taxonomy_registry.yaml) (`capture` + `projects`).  
Helpers: `default_taxonomy_for_capture` · `default_access_for_ingest` (separate).

## 4. Retrieve / Reconstruct (access lane ≠ taxonomy outline)

| When | Lane |
|------|------|
| Card is `restricted` / proprietary `source_project` | **proprietary** |
| Card is `public` / `internal` | **general** works; proprietary also sees them under ceiling |

UI (v0.6.3+): 重组 + 检索两侧有 **taxonomy 大纲**（Excel-like group）。单击分组 = 设 `taxonomy_prefix`；展开到最底层知识节点 **双击** = 打开正文。与访问层正交。API：`GET /api/taxonomy/tree` · `GET /api/taxonomy/cards`.

Do **not** say「专有知识 path ⇒ must use proprietary」。Say「**classification=restricted** ⇒ proprietary」。

## 5. Forbidden

- Infer `classification` from `taxonomy.path[0]`
- Infer taxonomy root from access level
- Treat `LEVEL_NAMES` as public/internal/restricted/secret

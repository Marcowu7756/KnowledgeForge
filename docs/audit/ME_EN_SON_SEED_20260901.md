# English seed replaced with Owner-authorized son sample · 2026-09-01

```yaml
doc_id: KF-EVIDENCE-20260901-ME-EN-SON
verdict: ME_EN_REPLACED · DEFAULT_STILL_ME · KF_DS_F5_MATCH · S02_EN_SMOKE_WAV
as_of: 2026-09-01
verified: 2026-09-02
sot: docs/ops/VOICE_IDENTITY_V0.md
```

## Authorize

Owner 2026-09-01：用儿子英语录音替换 **英语槽** `me_en` only。  
普通话 `me` 不变。禁止把该样本混进 `me`。禁止把 `me_en` 设成 DEFAULT。

```text
me     = Owner · zh · DEFAULT
me_en  = Owner-authorized son · en · never DEFAULT
```

## Assets

| Item | Path / value |
|------|----------------|
| Source m4a | `C:\Users\Panzer\Downloads\9月1日.m4a`（~283s · AAC 48k stereo · 2026-09-01） |
| F5 window | t≈0.89s · **12s** · mono 24 kHz |
| Transcript | `A writing assignment, the English teacher gave the class a` |
| KF sample | `data/voices/me_en/sample.wav`（576078 bytes） |
| KF meta | `data/voices/me_en/meta.json` · `duration_sec=12.0` · same transcript |
| Staging F5 | `data/voices/_staging/son_en_f5_12s.wav` |
| Staging source | `data/voices/_staging/son_en_source_20260901.wav`（27170478 bytes） |
| Pre-son bak | `data/voices/_staging/me_en_sample.bak_pre_son_20260901.wav` · `me_en_meta.bak_pre_son_20260901.json` · `ds_me_en_bak_pre_son_20260901/` |
| DS pack | `D:\DigitalSelf\data\identity\voice\me_en\` · `MANIFEST.yaml` `identity: Owner-authorized son` · `replaced: 2026-09-01` |
| DEFAULT | `data/voices/DEFAULT` = `me` |

## Integrity (SHA256 · 2026-09-02)

| Artifact | SHA256 |
|----------|--------|
| KF `me_en/sample.wav` | `A899736DD94312BA63FF0821A80B3BC43EA98D73BB28DD4A42C0C003B1EA8B09` |
| staging `son_en_f5_12s.wav` | same |
| DS `me_en/f5_sample.wav` | same |
| DS `me_en/source.wav` | `A87E72BB757729CAC405B4DAE8C69FF485A995863A9A5686237DFC15BACAB7CC` |
| staging `son_en_source_20260901.wav` | same |

```text
KF F5 ≡ staging F5 ≡ DS F5
DS source ≡ staging source
```

## Smoke

KF card Core Idea → S02 `--language en`（earlier run）：

```text
python main.py ds invoke S02 --file <absolute txt> --language en -o data\expression\_read_en_relative_clause.wav
ok · voice=me_en · duration_sec=40.309
```

Card: `data/knowledge/english/attributive_relative_clauses.md`  
Smoke wav present: `data/expression/_read_en_relative_clause.wav`（1934860 bytes · 2026-09-02 verify）。

Import recipe (re-seed):

```powershell
python main.py voice import data/voices/_staging/son_en_f5_12s.wav --name me_en --no-default --transcript "A writing assignment, the English teacher gave the class a"
Get-Content data\voices\DEFAULT   # must remain me
```

## Boundaries

```text
✅ replace English slot me_en
✅ keep DEFAULT = me
✅ keep zh Owner me untouched
❌ S03 invoke / NTW pipeline copy
❌ promote son sample into me
❌ Producer / S15 seal changes
```

## Related

| Doc | Role |
|-----|------|
| [`../ops/VOICE_IDENTITY_V0.md`](../ops/VOICE_IDENTITY_V0.md) | SoT |
| [`../ops/NTW_TO_KF_TRANSFER_V0.md`](../ops/NTW_TO_KF_TRANSFER_V0.md) | 不平移 Runtime |
| [`../ops/LANGUAGE_EXPRESSION_V0.md`](../ops/LANGUAGE_EXPRESSION_V0.md) | Language ≠ Translation |
| DS pack README | `D:\DigitalSelf\data\identity\voice\README.md` |
| Cursor rule | `.cursor/rules/voice-language-seed.mdc` |

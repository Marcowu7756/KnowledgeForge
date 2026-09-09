# ARCH · KF cross-stack consume · 2026-09-08

```yaml
doc_id: KF-ARCH_20260908_CROSS_STACK_CONSUME
as_of: 2026-09-08
status: OPEN · CONSUME_AUDIT
```

## Role

KF = Skill 消费端。Live SoT = `D:\DigitalSelf\skills\CATALOG.yaml`（含 **S24/S25**）。

入口：[`UAT_ENTRY_V0.md`](UAT_ENTRY_V0.md)  
协议：[`../interop/DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md)  
深度审计证据：[`EVIDENCE_20260908_KF_DEEP_AUDIT.md`](EVIDENCE_20260908_KF_DEEP_AUDIT.md)

```text
ds list 期望含 S00…S25
S24/S25 可在 DS 侧 invoke；KF 消费不改 DS Runtime
```

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, model_validator

Classification = Literal["public", "internal", "restricted", "secret"]
SourceProject = Literal["setv", "factorlib", "asharelib", ""]
# Legacy KO field (still written for older readers).
ExportPolicy = Literal["local_only", "export_ok"]
AccessLane = Literal["general", "proprietary"]

ComposeMode = Literal["allow", "local_only", "deny"]
ExpressionMode = Literal["allow", "controlled", "deny"]
ExportMode = Literal["export_ok", "warning", "local_only", "encrypted", "deny"]

# Dual-track LLM: user may choose local OR cloud at any time.
# Content gates (below) change which KOs enter the prompt — they do not remove the choice.
LOCAL_LLM_PROVIDERS = frozenset({"ollama"})
CLOUD_LLM_PROVIDERS = frozenset({"openai", "gemini", "deepseek"})

CLASSIFICATION_ORDER: dict[str, int] = {
    "public": 0,
    "internal": 1,
    "restricted": 2,
    "secret": 3,
}

DEFAULT_PROPRIETARY_CLASSIFICATION: Classification = "restricted"
DEFAULT_PROPRIETARY_EXPORT: ExportPolicy = "local_only"


class AccessPolicy(BaseModel):
    """Per-KO flow controls — classification sets defaults; policy can override.

    compose modes (content eligibility, NOT a lock on which LLM you may select):
      - allow: KO may enter compose for any provider (cloud still hard-filters
        restricted/secret — see is_compose_eligible)
      - local_only: KO enters compose only when a local provider is active
      - deny: KO never enters compose
    """

    retrieve: bool = True
    compose: ComposeMode = "allow"
    expression: ExpressionMode = "allow"
    export: ExportMode = "export_ok"

    def is_default_for(self, classification: str) -> bool:
        return self == default_policy_for(classification)


def is_local_llm_provider(llm_provider: str) -> bool:
    return (llm_provider or "ollama").strip().lower() in LOCAL_LLM_PROVIDERS


def is_cloud_llm_provider(llm_provider: str) -> bool:
    return (llm_provider or "").strip().lower() in CLOUD_LLM_PROVIDERS


def default_policy_for(classification: str) -> AccessPolicy:
    """Canonical first-version matrix (governance, not a vault).

    restricted.compose=local_only means: this asset participates when the user
    selected a local model; choosing a cloud model remains available, but the
    KO is filtered out of the cloud prompt.
    """
    level = (classification or "public").strip().lower()
    if level == "secret":
        return AccessPolicy(
            retrieve=False,
            compose="deny",
            expression="deny",
            export="deny",
        )
    if level == "restricted":
        return AccessPolicy(
            retrieve=True,
            compose="local_only",
            expression="controlled",
            export="local_only",
        )
    if level == "internal":
        return AccessPolicy(
            retrieve=True,
            compose="allow",
            expression="allow",
            export="warning",
        )
    return AccessPolicy(
        retrieve=True,
        compose="allow",
        expression="allow",
        export="export_ok",
    )


def _legacy_export(mode: ExportMode) -> ExportPolicy:
    if mode in {"local_only", "encrypted", "deny"}:
        return "local_only"
    return "export_ok"


class AccessBlock(BaseModel):
    classification: Classification = "public"
    source_project: SourceProject = ""
    export_policy: ExportPolicy = "export_ok"
    policy: AccessPolicy | None = None

    @model_validator(mode="after")
    def _sync_legacy_export(self) -> AccessBlock:
        # Keep export_policy aligned with resolved policy for older index readers.
        resolved = self.resolved_policy()
        legacy = _legacy_export(resolved.export)
        if self.export_policy != legacy:
            return self.model_copy(update={"export_policy": legacy})
        return self

    def resolved_policy(self) -> AccessPolicy:
        if self.policy is not None:
            return self.policy
        return default_policy_for(self.classification)

    def is_retrievable(self, *, max_level: Classification | None = None) -> bool:
        return is_retrievable(
            self.classification,
            max_level=max_level,
            policy=self.resolved_policy(),
        )

    def is_compose_eligible(self, *, llm_provider: str) -> bool:
        return is_compose_eligible(
            self.classification,
            llm_provider=llm_provider,
            policy=self.resolved_policy(),
        )

    def is_expression_allowed(self, *, external: bool = False) -> bool:
        return is_expression_allowed(
            self.classification,
            policy=self.resolved_policy(),
            external=external,
        )

    def is_export_allowed(self) -> bool:
        return is_export_allowed(self.classification, policy=self.resolved_policy())


def classification_leq(left: str, right: str) -> bool:
    return CLASSIFICATION_ORDER.get(left, 0) <= CLASSIFICATION_ORDER.get(right, 99)


def max_retrieve_classification() -> Classification:
    raw = os.getenv("KF_ACCESS_MAX_RETRIEVE", "restricted").strip().lower()
    if raw in CLASSIFICATION_ORDER:
        return raw  # type: ignore[return-value]
    return "restricted"


def include_secret_in_retrieve() -> bool:
    return os.getenv("KF_ACCESS_INCLUDE_SECRET", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def policy_from_payload(raw: Any) -> AccessPolicy | None:
    if raw is None:
        return None
    if isinstance(raw, AccessPolicy):
        return raw
    if isinstance(raw, dict):
        if not raw:
            return None
        return AccessPolicy.model_validate(raw)
    return None


def resolve_policy(
    classification: str,
    payload: AccessPolicy | dict[str, Any] | None = None,
) -> AccessPolicy:
    parsed = policy_from_payload(payload)
    if parsed is not None:
        return parsed
    return default_policy_for(classification)

def is_retrievable(
    classification: str,
    *,
    max_level: Classification | None = None,
    policy: AccessPolicy | None = None,
) -> bool:
    resolved = policy if policy is not None else default_policy_for(classification)
    if not resolved.retrieve:
        return False
    if classification == "secret" and not include_secret_in_retrieve():
        return False
    ceiling = max_level or max_retrieve_classification()
    return classification_leq(classification, ceiling)


def is_compose_eligible(
    classification: str,
    *,
    llm_provider: str,
    policy: AccessPolicy | None = None,
) -> bool:
    """Whether a KO may enter a compose prompt for the *currently selected* provider.

    Dual-track rule: the user may always choose local or cloud LLM.
    This function only answers: given that choice, does this KO flow in?
    """
    resolved = policy if policy is not None else default_policy_for(classification)
    if resolved.compose == "deny" or classification == "secret":
        return False
    local = is_local_llm_provider(llm_provider)
    if resolved.compose == "local_only":
        return local
    # compose=allow — cloud still must not see restricted/secret assets
    if local:
        return True
    return classification in {"public", "internal"}


def is_expression_allowed(
    classification: str,
    *,
    policy: AccessPolicy | None = None,
    external: bool = False,
) -> bool:
    """expression=controlled → local preview/render OK; external export blocked."""
    resolved = policy if policy is not None else default_policy_for(classification)
    if resolved.expression == "deny" or classification == "secret":
        return False
    if resolved.expression == "controlled" and external:
        return False
    return True


def is_export_allowed(
    classification: str,
    *,
    policy: AccessPolicy | None = None,
) -> bool:
    """Local persistence / in-app use. Does not authorize leaving the machine."""
    resolved = policy if policy is not None else default_policy_for(classification)
    if resolved.export == "deny" or classification == "secret":
        return False
    return True


class GateResult(BaseModel):
    allowed: bool
    mode: str = ""
    warning: str = ""
    reason: str = ""
    classification: str = "public"


def lane_retrieve_ceiling(lane: AccessLane | str) -> Classification:
    """UI / API access lane → retrieve ceiling.

    general     → public+internal only (excludes SETV/Factor/AShare restricted)
    proprietary → up to KF_ACCESS_MAX_RETRIEVE (default restricted)
    """
    key = (lane or "general").strip().lower()
    if key == "proprietary":
        return max_retrieve_classification()
    return "internal"


def check_expression_gate(
    classification: str,
    *,
    policy: AccessPolicy | None = None,
    external: bool = False,
    channel: str = "plaintext",
) -> GateResult:
    resolved = policy if policy is not None else default_policy_for(classification)
    # Encrypted off-machine channel is the controlled leave path for restricted.
    if (
        resolved.expression == "controlled"
        and external
        and (channel or "plaintext").strip().lower() == "encrypted"
    ):
        return GateResult(
            allowed=True,
            mode="controlled",
            reason="encrypted_channel",
            classification=classification,
        )
    if not is_expression_allowed(
        classification, policy=resolved, external=external
    ):
        why = "secret_or_deny"
        if resolved.expression == "controlled" and external:
            why = "controlled_blocks_external"
        return GateResult(
            allowed=False,
            mode=resolved.expression,
            reason=why,
            classification=classification,
        )
    return GateResult(
        allowed=True,
        mode=resolved.expression,
        classification=classification,
    )


def check_export_gate(
    classification: str,
    *,
    policy: AccessPolicy | None = None,
    external: bool = False,
    channel: str = "plaintext",
) -> GateResult:
    """Export gate.

    external=False: in-app / under data/ (deny|secret blocked).
    external=True + channel=plaintext: local_only/encrypted/deny blocked;
                   warning allowed with warning text.
    external=True + channel=encrypted: local_only|encrypted|warning|export_ok
                   may leave as .kfexport envelope (secret/deny still blocked).
    """
    resolved = policy if policy is not None else default_policy_for(classification)
    ch = (channel or "plaintext").strip().lower()
    if ch not in {"plaintext", "encrypted"}:
        ch = "plaintext"
    if resolved.export == "deny" or classification == "secret":
        return GateResult(
            allowed=False,
            mode=resolved.export,
            reason="export_deny_or_secret",
            classification=classification,
        )
    if not external:
        return GateResult(
            allowed=True,
            mode=resolved.export,
            classification=classification,
        )
    if ch == "encrypted":
        return GateResult(
            allowed=True,
            mode="encrypted",
            reason="encrypted_channel",
            warning=(
                "encrypted envelope — recipient needs KF_EXPORT_KEY / passphrase"
            ),
            classification=classification,
        )
    if resolved.export == "local_only":
        return GateResult(
            allowed=False,
            mode="local_only",
            reason="local_only_blocks_external",
            classification=classification,
        )
    if resolved.export == "encrypted":
        return GateResult(
            allowed=False,
            mode="encrypted",
            reason="requires_encrypted_channel",
            classification=classification,
        )
    if resolved.export == "warning":
        return GateResult(
            allowed=True,
            mode="warning",
            warning="internal asset — confirm before sharing outside KF",
            classification=classification,
        )
    return GateResult(
        allowed=True,
        mode=resolved.export,
        classification=classification,
    )


def infer_source_project(*parts: str | None) -> SourceProject:
    blob = " ".join(p for p in parts if p).lower().replace("\\", "/")
    if "setv" in blob:
        return "setv"
    if "factorlib" in blob or "factor-lib" in blob or "factor_lib" in blob:
        return "factorlib"
    if "asharelib" in blob or "ashare-lib" in blob or "ashare_lib" in blob:
        return "asharelib"
    return ""


def default_access_for_ingest(
    *,
    source_path: str | None = None,
    dest_path: str | None = None,
    tags: list[str] | None = None,
) -> AccessBlock:
    """Assign default classification for new KOs (§8)."""
    project = infer_source_project(source_path, dest_path, " ".join(tags or []))
    norm_dest = (dest_path or "").replace("\\", "/").lower()
    if project or "/restricted/" in norm_dest or norm_dest.endswith("/restricted"):
        return AccessBlock(
            classification=DEFAULT_PROPRIETARY_CLASSIFICATION,
            source_project=project,
            export_policy=DEFAULT_PROPRIETARY_EXPORT,
            policy=default_policy_for(DEFAULT_PROPRIETARY_CLASSIFICATION),
        )
    return AccessBlock()


def access_from_meta(meta: dict) -> AccessBlock:
    nested = meta.get("access")
    if isinstance(nested, dict):
        return AccessBlock.model_validate(nested)
    classification = str(meta.get("access_classification") or meta.get("classification") or "public")
    if classification not in CLASSIFICATION_ORDER:
        classification = "public"
    project = str(meta.get("access_source_project") or meta.get("source_project") or "")
    if project not in {"setv", "factorlib", "asharelib"}:
        project = ""
    export = str(meta.get("access_export_policy") or meta.get("export_policy") or "export_ok")
    if export not in {"local_only", "export_ok"}:
        export = "export_ok"
    policy = policy_from_payload(meta.get("access_policy") or meta.get("policy"))
    return AccessBlock(
        classification=classification,  # type: ignore[arg-type]
        source_project=project,  # type: ignore[arg-type]
        export_policy=export,  # type: ignore[arg-type]
        policy=policy,
    )


def access_to_meta_lines(access: AccessBlock) -> list[str]:
    if (
        access.classification == "public"
        and not access.source_project
        and (access.policy is None or access.resolved_policy().is_default_for("public"))
    ):
        return []
    lines = [
        "access:",
        f"  classification: {access.classification}",
    ]
    if access.source_project:
        lines.append(f"  source_project: {access.source_project}")
    if access.export_policy != "export_ok":
        lines.append(f"  export_policy: {access.export_policy}")
    resolved = access.resolved_policy()
    if not resolved.is_default_for("public") or access.policy is not None:
        lines.append("  policy:")
        lines.append(f"    retrieve: {'true' if resolved.retrieve else 'false'}")
        lines.append(f"    compose: {resolved.compose}")
        lines.append(f"    expression: {resolved.expression}")
        lines.append(f"    export: {resolved.export}")
    return lines


def access_dict(access: AccessBlock) -> dict[str, Any]:
    payload: dict[str, Any] = {"classification": access.classification}
    if access.source_project:
        payload["source_project"] = access.source_project
    if access.export_policy != "export_ok":
        payload["export_policy"] = access.export_policy
    resolved = access.resolved_policy()
    if access.policy is not None or not resolved.is_default_for("public"):
        payload["policy"] = resolved.model_dump()
    return payload


def policy_dict(policy: AccessPolicy) -> dict[str, Any]:
    return policy.model_dump()

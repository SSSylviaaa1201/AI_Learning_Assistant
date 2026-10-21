"""Bounded, inert screenshot assets uploaded as an evidence text bundle."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import html
import json
import re

EVIDENCE_HEADER = "AILA_EVIDENCE_V1\n"
MAX_EVIDENCE_FILE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_FIGURES = 12


@dataclass(frozen=True)
class EvidenceFigure:
    id: str
    caption: str
    media_type: str
    data_base64: str
    sha256: str

    def context_text(self) -> str:
        return f"[[EVIDENCE:{self.id}]] — {self.caption} (original screenshot SHA-256: {self.sha256})"

    def as_html(self) -> str:
        return (
            '<figure class="deployment-evidence" style="break-inside:avoid;margin:1.2em 0">'
            f'<img src="data:{self.media_type};base64,{self.data_base64}" '
            f'alt="{html.escape(self.caption, quote=True)}" style="max-width:100%;height:auto">'
            f'<figcaption>{html.escape(self.caption)}</figcaption></figure>'
        )


def parse_evidence_bundle(text: str) -> tuple[EvidenceFigure, ...]:
    if not text.startswith(EVIDENCE_HEADER) or len(text.encode("utf-8")) > MAX_EVIDENCE_FILE_BYTES:
        raise ValueError("Invalid evidence bundle header or size")
    payload = json.loads(text[len(EVIDENCE_HEADER):])
    rows = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_FIGURES:
        raise ValueError("Evidence bundle needs 1–12 figures")
    figures = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid evidence figure")
        identifier = row.get("id", "")
        caption = row.get("caption", "")
        mime = row.get("media_type", "")
        encoded = row.get("data_base64", "")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", identifier) or identifier in seen:
            raise ValueError("Invalid or duplicate evidence ID")
        if not isinstance(caption, str) or not caption.strip() or len(caption) > 500:
            raise ValueError("Invalid evidence caption")
        if mime not in {"image/png", "image/jpeg"} or not isinstance(encoded, str):
            raise ValueError("Only PNG/JPEG evidence is supported")
        decoded = base64.b64decode(encoded, validate=True)
        if not 0 < len(decoded) <= MAX_IMAGE_BYTES:
            raise ValueError("Evidence image exceeds size limit")
        signature_ok = decoded.startswith(b"\x89PNG\r\n\x1a\n") if mime == "image/png" else decoded.startswith(b"\xff\xd8\xff")
        if not signature_ok:
            raise ValueError("Image signature does not match media type")
        digest = hashlib.sha256(decoded).hexdigest()
        if row.get("sha256") != digest:
            raise ValueError("Evidence image checksum mismatch")
        figures.append(EvidenceFigure(identifier, caption, mime, encoded, digest))
        seen.add(identifier)
    return tuple(figures)


def embed_evidence_figures(source: str, figures: tuple[EvidenceFigure, ...]) -> str:
    """Resolve figure markers after generation; never send binary data to the model."""
    missing = []
    seen = set()
    for figure in figures:
        if figure.id in seen:
            continue
        seen.add(figure.id)
        marker = f"[[EVIDENCE:{figure.id}]]"
        rendered = figure.as_html()
        # Replace a standalone paragraph as a whole so figure markup remains valid.
        paragraph = re.compile(r"<p\b[^>]*>\s*" + re.escape(marker) + r"\s*</p>", re.I)
        if marker in source:
            source = paragraph.sub(lambda _: rendered, source)
            source = source.replace(marker, rendered)
        else:
            missing.append(rendered)
    if missing:
        appendix = '<section class="evidence-appendix"><h2>Deployment evidence / 部署证据</h2>' + "".join(missing) + "</section>"
        source = re.sub(r"</body\s*>", lambda _: appendix + "</body>", source, count=1, flags=re.I) if re.search(r"</body\s*>", source, re.I) else source + appendix
    return source

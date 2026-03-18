"""HMAC signer for ingreso email payloads."""

from __future__ import annotations

import hashlib
import hmac
import json


class IngresoEmailSigner:
    """Sign and verify payloads for tray email dispatch."""

    @staticmethod
    def sign(payload: dict[str, object], secret: str) -> str:
        """Return HMAC signature for a payload.

        Args:
            payload: Data to sign.
            secret: Shared secret.

        Returns:
            Hex digest signature.
        """

        encoded = json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=True,
        ).encode("utf-8")
        return hmac.new(secret.encode("utf-8"), encoded, hashlib.sha256).hexdigest()

    @staticmethod
    def verify(payload: dict[str, object], signature: str, secret: str) -> bool:
        """Verify HMAC signature for a payload."""

        expected = IngresoEmailSigner.sign(payload, secret)
        return hmac.compare_digest(expected, signature)

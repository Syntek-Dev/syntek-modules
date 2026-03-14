"""Django AppConfig for syntek-graphql-crypto."""

from __future__ import annotations

import base64
import logging
import os

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger("syntek_graphql_crypto")


class SyntekGraphqlCryptoConfig(AppConfig):
    """Configuration for the syntek-graphql-crypto middleware.

    On startup, validates that all ``SYNTEK_FIELD_KEY_*`` environment variables
    contain valid base64-encoded 32-byte AES-256 keys.  Fails loudly with
    ``ImproperlyConfigured`` if any key is malformed, rather than deferring
    the error to request time.
    """

    name = "syntek_graphql_crypto"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Validate all SYNTEK_FIELD_KEY_* environment variables at startup."""
        prefix = "SYNTEK_FIELD_KEY_"
        found_keys = {k: v for k, v in os.environ.items() if k.startswith(prefix) and v}

        if not found_keys:
            logger.warning(
                "No SYNTEK_FIELD_KEY_* environment variables found. "
                "Encrypted field operations will fail at request time."
            )
            return

        for env_var, raw_value in found_keys.items():
            try:
                key_bytes = base64.b64decode(raw_value)
            except Exception as exc:
                raise ImproperlyConfigured(
                    f"{env_var} contains invalid base64: {exc}"
                ) from exc
            if len(key_bytes) != 32:
                raise ImproperlyConfigured(
                    f"{env_var} must decode to exactly 32 bytes (AES-256), "
                    f"got {len(key_bytes)} bytes"
                )

        logger.info(
            "Validated %d SYNTEK_FIELD_KEY_* environment variables",
            len(found_keys),
        )

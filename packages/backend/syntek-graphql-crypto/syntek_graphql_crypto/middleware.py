"""EncryptionMiddleware — Strawberry extension that intercepts encrypted fields.

Read path (queries): resolvers return ciphertext → middleware decrypts →
client gets plaintext.
Write path (mutations): client sends plaintext → middleware encrypts →
resolver receives ciphertext.

The middleware uses ``syntek_pyo3.decrypt_field`` / ``encrypt_field`` for
individual fields and ``syntek_pyo3.decrypt_fields_batch`` /
``encrypt_fields_batch`` for batch groups.

Batch groups share a single encryption key resolved from
``SYNTEK_FIELD_KEY_<MODEL>_<BATCH_GROUP>``.  Individual fields use
``SYNTEK_FIELD_KEY_<MODEL>_<FIELD>``.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import typing
from typing import TYPE_CHECKING, Any

import syntek_pyo3
from strawberry.extensions import SchemaExtension
from syntek_pyo3 import KeyRing

from syntek_graphql_crypto.directives import Encrypted

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger("syntek_graphql_crypto")


def _resolve_ring(model: str, field: str) -> KeyRing:
    """Resolve ``SYNTEK_FIELD_KEY_<MODEL>_<FIELD>`` and return a KeyRing."""
    env_var = f"SYNTEK_FIELD_KEY_{model.upper()}_{field.upper()}"
    raw = os.environ.get(env_var)
    if not raw:
        raise RuntimeError(f"Missing encryption key env var: {env_var}")
    try:
        key_bytes = base64.b64decode(raw)
    except Exception as exc:
        raise RuntimeError(f"Invalid base64 key in {env_var}: {exc}") from exc
    ring = KeyRing()
    ring.add(1, key_bytes)
    return ring


def _resolve_batch_ring(model: str, batch_group: str) -> KeyRing:
    """Resolve ``SYNTEK_FIELD_KEY_<MODEL>_<BATCH_GROUP>`` for batch operations.

    Batch groups share a single encryption key (per the Encryption Guide).
    The batch group name (e.g. ``"profile"``) is used instead of individual
    field names.
    """
    env_var = f"SYNTEK_FIELD_KEY_{model.upper()}_{batch_group.upper()}"
    raw = os.environ.get(env_var)
    if not raw:
        raise RuntimeError(f"Missing encryption key env var: {env_var}")
    try:
        key_bytes = base64.b64decode(raw)
    except Exception as exc:
        raise RuntimeError(f"Invalid base64 key in {env_var}: {exc}") from exc
    ring = KeyRing()
    ring.add(1, key_bytes)
    return ring


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _get_encrypted_args_from_method(
    parent_type: Any, field_name: str
) -> dict[str, Encrypted]:
    """Return ``{python_arg_name: Encrypted}`` for all ``Annotated`` args on the
    resolver.

    Strawberry strips ``Annotated`` metadata when building ``StrawberryArgument``
    (it only looks for ``StrawberryArgumentAnnotation`` instances). To recover
    ``Encrypted()`` metadata we go back to the original Python method and call
    ``typing.get_type_hints(..., include_extras=True)`` which preserves
    ``Annotated`` wrappers.
    """
    try:
        type_def = (getattr(parent_type, "extensions", None) or {}).get(
            "strawberry-definition"
        )
        if type_def is None:
            return {}
        origin_cls = getattr(type_def, "origin", None)
        if origin_cls is None:
            return {}
        python_name = _camel_to_snake(field_name)
        method = getattr(origin_cls, python_name, None)
        if method is None:
            return {}
        hints = typing.get_type_hints(method, include_extras=True)
        result: dict[str, Encrypted] = {}
        for arg_name, hint in hints.items():
            if arg_name == "return":
                continue
            if typing.get_origin(hint) is typing.Annotated:
                for meta in typing.get_args(hint)[1:]:
                    if isinstance(meta, Encrypted):
                        result[arg_name] = meta
                        break
        return result
    except Exception:
        logger.error(
            "Failed to inspect resolver '%s' on type '%s' for @encrypted "
            "annotations — write-path encryption will be skipped for this "
            "field. This may result in plaintext reaching the database.",
            field_name,
            parent_type,
            exc_info=True,
        )
        return {}


# ---------------------------------------------------------------------------
# Encrypted-map cache — schema type maps do not change at runtime
# ---------------------------------------------------------------------------

_encrypted_map_cache: dict[int, dict[str, Encrypted]] = {}


class EncryptionMiddleware(SchemaExtension):
    """Strawberry extension that transparently encrypts/decrypts ``@encrypted``
    fields."""

    def __init__(self, *, model: str = "User", execution_context: Any = None) -> None:
        # SchemaExtension passes execution_context as a keyword arg.
        if execution_context is not None:
            super().__init__(execution_context=execution_context)
        self._model = model
        self._errors: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Low-level helpers used directly by unit tests
    # ------------------------------------------------------------------

    def process_input(
        self,
        *,
        field_name: str,
        value: Any,
        batch_group: str | None = None,  # noqa: ARG002
        is_encrypted: bool = True,
        capture: Callable[[Any], None] | None = None,
    ) -> Any:
        """Encrypt a single mutation input field.

        Returns the ciphertext (or the original value if ``is_encrypted=False``).
        """
        if not is_encrypted:
            return value
        ring = _resolve_ring(self._model, field_name)
        result = syntek_pyo3.encrypt_field(value, ring, self._model, field_name)
        if capture is not None:
            capture(result)
        return result

    def process_batch_input(
        self,
        *,
        batch_group: str,
        fields: list[tuple[Any, str]],
    ) -> list[Any]:
        """Encrypt a batch of mutation input fields in one call.

        The key is resolved from the batch group name, not individual field
        names.  Batch groups share a single encryption key.
        """
        ring = _resolve_batch_ring(self._model, batch_group)
        # Rust: (field_name, value); public API: (value, field_name).
        return syntek_pyo3.encrypt_fields_batch(
            [(fn, v) for v, fn in fields], ring, self._model
        )

    def process_output(
        self,
        *,
        field_name: str,
        value: Any,
        batch_group: str | None = None,  # noqa: ARG002
        is_encrypted: bool = True,
    ) -> Any:
        """Decrypt a single query output field.

        Returns plaintext (or original value if ``is_encrypted=False``).
        """
        if not is_encrypted:
            return value
        ring = _resolve_ring(self._model, field_name)
        return syntek_pyo3.decrypt_field(value, ring, self._model, field_name)

    def process_batch_output(
        self,
        *,
        batch_group: str,
        fields: list[tuple[Any, str]],
    ) -> list[Any]:
        """Decrypt a batch of query output fields in one call.

        The key is resolved from the batch group name, not individual field
        names.  Batch groups share a single encryption key.
        """
        ring = _resolve_batch_ring(self._model, batch_group)
        # Rust: (field_name, ciphertext); public API: (ciphertext, field_name).
        return syntek_pyo3.decrypt_fields_batch(
            [(fn, ct) for ct, fn in fields], ring, self._model
        )

    # ------------------------------------------------------------------
    # Strawberry SchemaExtension hooks (full schema execution)
    # ------------------------------------------------------------------

    def _is_authenticated(self) -> bool:
        """Check if the current request is authenticated.

        Fail-closed: returns ``False`` for any missing or malformed context.
        Only ``AttributeError`` and ``TypeError`` are caught — all other
        exceptions propagate.
        """
        try:
            ctx = self.execution_context.context
        except AttributeError, TypeError:
            return False
        if ctx is None:
            return False
        try:
            return bool(ctx.user.is_authenticated)
        except AttributeError, TypeError:
            return False

    def resolve(  # type: ignore[override]
        self,
        _next: Callable[..., Any],
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Intercept field resolution for encryption/decryption."""
        # ---- Write path: mutation inputs --------------------------------
        # Scan kwargs for arguments annotated with Encrypted (via typing.Annotated).
        if kwargs:
            arg_directives = _get_encrypted_args_from_method(
                info.parent_type, info.field_name
            )

            if arg_directives:
                # H4: log warning for unauthenticated write-path access.
                try:
                    if not info.context.user.is_authenticated:
                        logger.warning(
                            "Unauthenticated mutation with @encrypted fields "
                            "detected — encryption proceeding; auth enforcement "
                            "is the responsibility of the Django permission layer"
                        )
                except AttributeError, TypeError:
                    pass

                # Group by batch; individual fields have batch=None.
                batches: dict[str, list[tuple[str, Any]]] = {}
                individual: list[tuple[str, Any, Encrypted]] = []
                found_args: set[str] = set()

                for kw_name, kw_val in list(kwargs.items()):
                    # GraphQL kwargs use camelCase; method hints use snake_case.
                    directive = arg_directives.get(kw_name) or arg_directives.get(
                        _camel_to_snake(kw_name)
                    )
                    if directive is None:
                        continue
                    found_args.add(kw_name)
                    found_args.add(_camel_to_snake(kw_name))
                    if directive.batch is None:
                        individual.append((kw_name, kw_val, directive))
                    else:
                        batches.setdefault(directive.batch, []).append(
                            (kw_name, kw_val)
                        )

                # M2: warn about annotated args not found in kwargs.
                for arg_name in arg_directives:
                    if arg_name not in found_args:
                        logger.warning(
                            "@encrypted argument '%s' not found in mutation "
                            "kwargs — field may be stored as plaintext",
                            arg_name,
                        )

                try:
                    for kw_name, kw_val, _d in individual:
                        snake = _camel_to_snake(kw_name)
                        ring = _resolve_ring(self._model, snake)
                        kwargs[kw_name] = syntek_pyo3.encrypt_field(
                            kw_val, ring, self._model, snake
                        )
                    for batch_group, batch_pairs in batches.items():
                        ring = _resolve_batch_ring(self._model, batch_group)
                        ciphertexts = syntek_pyo3.encrypt_fields_batch(
                            [(_camel_to_snake(k), v) for k, v in batch_pairs],
                            ring,
                            self._model,
                        )
                        for (kw_name, _), ct in zip(
                            batch_pairs, ciphertexts, strict=True
                        ):
                            kwargs[kw_name] = ct
                except RuntimeError as exc:
                    logger.error(
                        "Encryption failed for model '%s': %s",
                        self._model,
                        exc,
                    )
                    raise Exception(
                        "An internal error occurred. Please contact support."
                    ) from None

        return _next(root, info, *args, **kwargs)

    def on_execute(self):  # type: ignore[return]
        """Generator hook: decrypt output fields and enforce auth guard after
        execution."""
        yield  # let execution happen
        result = self.execution_context.result
        if result is None or result.data is None:
            return
        is_auth = self._is_authenticated()
        self._process_data(result, is_auth)

    def _process_data(self, result: Any, is_auth: bool) -> None:
        """Walk result.data and decrypt encrypted fields, enforcing auth.

        Handles both dict and list top-level values.
        """
        data = result.data
        if not isinstance(data, dict):
            return

        errors: list[Any] = list(result.errors or [])

        for _root_key, root_val in data.items():
            if isinstance(root_val, dict):
                self._decrypt_object(root_val, is_auth, errors)
            elif isinstance(root_val, list):
                for item in root_val:
                    if isinstance(item, dict):
                        self._decrypt_object(item, is_auth, errors)

        # Attach errors back.
        if errors:
            result.errors = errors

    def _decrypt_object(
        self, obj: dict[str, Any], is_auth: bool, errors: list[Any]
    ) -> None:
        """Decrypt all @encrypted fields on an object dict in-place.

        Recurses into nested dicts and lists to handle related objects.
        """
        schema = self.execution_context.schema
        encrypted_map = self._get_encrypted_map(schema)

        if not is_auth and encrypted_map:
            # Auth guard: null all encrypted fields and add error.
            logger.warning(
                "Unauthenticated access attempt to encrypted fields — nulling output"
            )
            for field_name in list(obj.keys()):
                snake = _camel_to_snake(field_name)
                if snake in encrypted_map or field_name in encrypted_map:
                    obj[field_name] = None
            errors.append(
                {
                    "message": "Unauthenticated: access to encrypted fields denied",
                    "error_type": "AuthenticationError",
                    "field_path": list(encrypted_map.keys()),
                }
            )
            return

        # Group fields by batch.
        batches: dict[str, list[tuple[str, str, Any]]] = {}
        individual: list[tuple[str, str, Any]] = []

        for camel_name, value in obj.items():
            snake = _camel_to_snake(camel_name)
            directive = encrypted_map.get(snake) or encrypted_map.get(camel_name)
            if directive is None:
                continue
            if directive.batch is None:
                individual.append((camel_name, snake, value))
            else:
                batches.setdefault(directive.batch, []).append(
                    (camel_name, snake, value)
                )

        # Decrypt individual fields.
        for camel_name, snake, value in individual:
            try:
                ring = _resolve_ring(self._model, snake)
                obj[camel_name] = syntek_pyo3.decrypt_field(
                    value, ring, self._model, snake
                )
            except Exception as exc:
                obj[camel_name] = None
                logger.error(
                    "Decryption failed for field '%s' on model '%s': %s",
                    snake,
                    self._model,
                    exc,
                )
                errors.append(
                    {
                        "message": "Decryption failed",
                        "error_type": "DecryptionError",
                        "field_path": camel_name,
                        "path": [camel_name],
                    }
                )

        # Decrypt batch groups.
        for batch_group, batch_fields in batches.items():
            try:
                ring = _resolve_batch_ring(self._model, batch_group)
                # Rust expects (field_name, ciphertext) order.
                pairs = [(snake, obj[camel]) for camel, snake, _ in batch_fields]
                plaintexts = syntek_pyo3.decrypt_fields_batch(pairs, ring, self._model)
                for (camel_name, _, _), plaintext in zip(
                    batch_fields, plaintexts, strict=True
                ):
                    obj[camel_name] = plaintext
            except Exception as exc:
                for camel_name, _, _ in batch_fields:
                    obj[camel_name] = None
                logger.error(
                    "Batch decryption failed for group '%s' on model '%s': %s",
                    batch_group,
                    self._model,
                    exc,
                )
                errors.append(
                    {
                        "message": "Decryption failed",
                        "error_type": "DecryptionError",
                        "field_path": batch_group,
                        "path": [camel for camel, _, _ in batch_fields],
                    }
                )

        # Recurse into nested objects and lists to handle related types.
        for _key, value in obj.items():
            if isinstance(value, dict):
                self._decrypt_object(value, is_auth, errors)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._decrypt_object(item, is_auth, errors)

    @staticmethod
    def _get_encrypted_map(schema: Any) -> dict[str, Encrypted]:
        """Return the cached encrypted-field map for the given schema.

        The map is built once per schema instance and cached for the lifetime
        of the process.  Schema type maps do not change at runtime.
        """
        cache_key = id(schema)
        cached = _encrypted_map_cache.get(cache_key)
        if cached is not None:
            return cached
        result = _build_encrypted_map(schema)
        _encrypted_map_cache[cache_key] = result
        return result


def _build_encrypted_map(schema: Any) -> dict[str, Encrypted]:
    """Build {snake_field_name: Encrypted} for all encrypted fields in the
    schema."""
    result: dict[str, Encrypted] = {}
    graphql_schema = getattr(schema, "_schema", None) or getattr(
        schema, "graphql_schema", None
    )
    if graphql_schema is None:
        return result

    for _type_name, type_def in graphql_schema.type_map.items():
        field_map = getattr(type_def, "fields", None)
        if not field_map:
            continue
        for gql_field_name, gql_field in field_map.items():
            ext = getattr(gql_field, "extensions", None) or {}
            # Strawberry stores the StrawberryField on "strawberry-definition".
            strawberry_field = ext.get("strawberry-definition")
            for directive in getattr(strawberry_field, "directives", None) or []:
                if isinstance(directive, Encrypted):
                    snake = _camel_to_snake(gql_field_name)
                    result[snake] = directive
                    break
    return result

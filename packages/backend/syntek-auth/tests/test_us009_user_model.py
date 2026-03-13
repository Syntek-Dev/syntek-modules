"""US009 — Green phase: user model tests for ``syntek-auth``.

Tests cover ``AbstractSyntekUser``, the concrete ``User`` subclass, and
``SyntekUserManager``.

Acceptance criteria under test
-------------------------------
- ``AbstractSyntekUser`` is abstract and cannot be instantiated directly.
- The concrete ``User`` subclass is creatable via ``create_user(email, password)``.
- ``create_superuser`` sets ``is_staff=True`` and ``is_superuser=True``.
- ``email`` and ``phone`` are declared as ``EncryptedField`` columns, not
  plain ``CharField`` / ``TextField``.
- ``username`` is nullable — ``create_user`` succeeds without it.
- ``get_user_model()`` returns the concrete ``User`` class.
- ``User`` inherits ``PermissionsMixin`` — ``has_perm`` and ``has_module_perms``
  are present.
- ``USERNAME_FIELD`` is ``"email"`` on the concrete model.
- ``SyntekUserManager.create_user`` raises ``ValueError`` if ``email`` is empty.
- ``SyntekUserManager.create_superuser`` raises ``ValueError`` if ``is_staff``
  or ``is_superuser`` is not ``True``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import inspect

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from syntek_auth.models import (
    AbstractSyntekUser,
    EncryptedField,
    SyntekUserManager,
    User,
)

# ---------------------------------------------------------------------------
# AC: AbstractSyntekUser is abstract
# ---------------------------------------------------------------------------


class TestAbstractSyntekUserIsAbstract:
    """``AbstractSyntekUser`` must be abstract — it cannot be used as a table."""

    def test_abstract_syntek_user_has_abstract_meta(self) -> None:
        """``AbstractSyntekUser.Meta.abstract`` must be ``True``."""
        assert getattr(AbstractSyntekUser._meta, "abstract", False) is True, (
            "AbstractSyntekUser.Meta.abstract must be True"
        )

    def test_abstract_syntek_user_has_no_db_table(self) -> None:
        """An abstract model must not be registered in the app registry as a concrete model."""
        # get_models() only returns non-abstract models.
        concrete_model_names = [m.__name__ for m in apps.get_models()]
        assert "AbstractSyntekUser" not in concrete_model_names, (
            "AbstractSyntekUser must not appear in the concrete model registry"
        )


# ---------------------------------------------------------------------------
# AC: get_user_model() returns the concrete User class
# ---------------------------------------------------------------------------


class TestGetUserModelReturnsUser:
    """``get_user_model()`` must resolve to the concrete ``User`` class."""

    def test_get_user_model_returns_user_class(self) -> None:
        """``get_user_model()`` must return ``syntek_auth.models.User``."""
        UserModel = get_user_model()  # noqa: N806
        assert UserModel is User, (
            f"get_user_model() returned {UserModel!r}, expected syntek_auth.models.User"
        )

    def test_user_class_is_subclass_of_abstract_base(self) -> None:
        """The concrete ``User`` class must subclass ``AbstractSyntekUser``."""
        assert issubclass(User, AbstractSyntekUser), (
            "User must subclass AbstractSyntekUser"
        )


# ---------------------------------------------------------------------------
# AC: User model field declarations
# ---------------------------------------------------------------------------


class TestUserModelFieldDeclarations:
    """PII fields must use ``EncryptedField``; ``username`` must be nullable."""

    def test_email_field_is_encrypted_field(self) -> None:
        """The ``email`` field must be declared as an ``EncryptedField``, not a plain TextField."""
        field = User._meta.get_field("email")
        assert isinstance(field, EncryptedField), (
            f"User.email must be EncryptedField; got {type(field).__name__}"
        )

    def test_phone_field_is_encrypted_field(self) -> None:
        """The ``phone`` field must be declared as an ``EncryptedField``."""
        field = User._meta.get_field("phone")
        assert isinstance(field, EncryptedField), (
            f"User.phone must be EncryptedField; got {type(field).__name__}"
        )

    def test_username_field_is_nullable(self) -> None:
        """The ``username`` field must allow null — it is optional on the model."""
        field = User._meta.get_field("username")
        assert field.null is True, "User.username must have null=True"  # type: ignore[union-attr]

    def test_username_field_is_blank(self) -> None:
        """The ``username`` field must allow blank — it is optional at the form level."""
        field = User._meta.get_field("username")
        assert field.blank is True, "User.username must have blank=True"  # type: ignore[union-attr]

    def test_email_field_is_not_nullable(self) -> None:
        """The ``email`` field must not be nullable — every user requires an email."""
        field = User._meta.get_field("email")
        assert field.null is False, "User.email must have null=False"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# AC: USERNAME_FIELD is 'email'
# ---------------------------------------------------------------------------


class TestUsernameField:
    """``USERNAME_FIELD`` on the concrete model must be ``'email'``."""

    def test_username_field_is_email(self) -> None:
        """``User.USERNAME_FIELD`` must be ``'email'``."""
        assert User.USERNAME_FIELD == "email", (
            f"User.USERNAME_FIELD must be 'email'; got {User.USERNAME_FIELD!r}"
        )

    def test_get_user_model_username_field_is_email(self) -> None:
        """``get_user_model().USERNAME_FIELD`` must also be ``'email'``."""
        UserModel = get_user_model()  # noqa: N806
        assert UserModel.USERNAME_FIELD == "email", (  # type: ignore[attr-defined]
            f"get_user_model().USERNAME_FIELD must be 'email'; got {UserModel.USERNAME_FIELD!r}"  # type: ignore[attr-defined]
        )


# ---------------------------------------------------------------------------
# AC: PermissionsMixin — has_perm and has_module_perms are present
# ---------------------------------------------------------------------------


class TestPermissionsMixinPresence:
    """``User`` must inherit ``PermissionsMixin`` — permission methods must exist."""

    def test_user_has_has_perm_method(self) -> None:
        """``User`` must have a ``has_perm`` method (from ``PermissionsMixin``)."""
        assert hasattr(User, "has_perm"), (
            "User must have has_perm (inherited from PermissionsMixin)"
        )
        assert callable(User.has_perm), "User.has_perm must be callable"

    def test_user_has_has_module_perms_method(self) -> None:
        """``User`` must have a ``has_module_perms`` method (from ``PermissionsMixin``)."""
        assert hasattr(User, "has_module_perms"), (
            "User must have has_module_perms (inherited from PermissionsMixin)"
        )
        assert callable(User.has_module_perms), "User.has_module_perms must be callable"

    def test_user_is_subclass_of_permissions_mixin(self) -> None:
        """``User`` must be a subclass of ``django.contrib.auth.models.PermissionsMixin``."""
        from django.contrib.auth.models import PermissionsMixin

        assert issubclass(User, PermissionsMixin), "User must subclass PermissionsMixin"


# ---------------------------------------------------------------------------
# AC: SyntekUserManager.create_user raises ValueError for empty email
# ---------------------------------------------------------------------------


class TestCreateUserEmailValidation:
    """``create_user`` must raise ``ValueError`` when email is empty or absent."""

    @pytest.mark.django_db
    def test_create_user_empty_email_raises_value_error(self) -> None:
        """``create_user('')`` must raise ``ValueError`` before any DB interaction."""
        UserModel = get_user_model()  # noqa: N806
        with pytest.raises(ValueError, match="email address"):
            UserModel.objects.create_user(email="", password="ValidPass1234!")  # type: ignore[attr-defined]

    @pytest.mark.django_db
    def test_create_user_succeeds_and_returns_user(self) -> None:
        """``create_user`` must persist and return a ``User`` with the given email."""
        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="alice@example.com", password="ValidPass1234!"
        )
        assert isinstance(user, UserModel), (
            f"create_user must return a User; got {type(user).__name__}"
        )
        assert user.pk is not None, "create_user must save the user to the database"
        # Email is stored as AES-256-GCM ciphertext; identity is verified via the
        # HMAC-SHA256 lookup token (per ENCRYPTION-GUIDE.md — never compare ciphertext).
        from syntek_auth.services.lookup_tokens import make_email_token

        assert user.email_token == make_email_token("alice@example.com"), (  # type: ignore[attr-defined]
            "create_user must store the email identity in email_token"
        )


# ---------------------------------------------------------------------------
# AC: SyntekUserManager.create_user succeeds without username
# ---------------------------------------------------------------------------


class TestCreateUserWithoutUsername:
    """``create_user`` must accept a call with no ``username`` argument."""

    @pytest.mark.django_db
    def test_create_user_without_username_sets_username_none(self) -> None:
        """``create_user`` without a username must produce a user with ``username=None``."""
        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="bob@example.com",
            password="SecurePass5678!",
            # no username keyword argument
        )
        assert user.username is None, (
            "create_user without username must leave username as None"
        )

    def test_create_user_manager_signature_accepts_no_username(self) -> None:
        """``create_user`` signature must not require a ``username`` positional argument."""
        sig = inspect.signature(SyntekUserManager.create_user)
        params = list(sig.parameters.keys())
        # 'email' and 'password' must be present; 'username' must not be required
        assert "email" in params, "create_user must have an 'email' parameter"
        assert "password" in params, "create_user must have a 'password' parameter"
        if "username" in params:
            param = sig.parameters["username"]
            assert param.default is not inspect.Parameter.empty, (
                "If 'username' is in create_user signature it must have a default value"
            )


# ---------------------------------------------------------------------------
# AC: SyntekUserManager.create_superuser sets is_staff and is_superuser
# ---------------------------------------------------------------------------


class TestCreateSuperuser:
    """``create_superuser`` must set ``is_staff=True`` and ``is_superuser=True``."""

    @pytest.mark.django_db
    def test_create_superuser_sets_is_staff_and_is_superuser(self) -> None:
        """``create_superuser`` must return a user with both privilege flags set."""
        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_superuser(  # type: ignore[attr-defined]
            email="admin@example.com", password="AdminPass1234!"
        )
        assert user.is_staff is True, "create_superuser must set is_staff=True"
        assert user.is_superuser is True, "create_superuser must set is_superuser=True"

    def test_create_superuser_manager_signature_exists(self) -> None:
        """``create_superuser`` must exist on the manager."""
        assert hasattr(SyntekUserManager, "create_superuser"), (
            "SyntekUserManager must define create_superuser"
        )
        assert callable(SyntekUserManager.create_superuser), (
            "SyntekUserManager.create_superuser must be callable"
        )


# ---------------------------------------------------------------------------
# AC: SyntekUserManager.create_superuser raises ValueError for bad flags
# ---------------------------------------------------------------------------


class TestCreateSuperuserFlagValidation:
    """Passing ``is_staff=False`` or ``is_superuser=False`` must raise ``ValueError``."""

    @pytest.mark.django_db
    def test_create_superuser_is_staff_false_raises(self) -> None:
        """``create_superuser(is_staff=False)`` must raise ``ValueError``."""
        UserModel = get_user_model()  # noqa: N806
        with pytest.raises(ValueError, match="is_staff"):
            UserModel.objects.create_superuser(  # type: ignore[attr-defined]
                email="badmin@example.com",
                password="AdminPass1234!",
                is_staff=False,
            )

    @pytest.mark.django_db
    def test_create_superuser_is_superuser_false_raises(self) -> None:
        """``create_superuser(is_superuser=False)`` must raise ``ValueError``."""
        UserModel = get_user_model()  # noqa: N806
        with pytest.raises(ValueError, match="is_superuser"):
            UserModel.objects.create_superuser(  # type: ignore[attr-defined]
                email="badmin2@example.com",
                password="AdminPass1234!",
                is_superuser=False,
            )


# ---------------------------------------------------------------------------
# AC: User has a custom manager of type SyntekUserManager
# ---------------------------------------------------------------------------


class TestUserManagerType:
    """``User.objects`` must be a ``SyntekUserManager`` instance."""

    def test_user_objects_is_syntek_user_manager(self) -> None:
        """``User.objects`` must be an instance of ``SyntekUserManager``."""
        assert isinstance(User.objects, SyntekUserManager), (
            f"User.objects must be SyntekUserManager; got {type(User.objects).__name__}"
        )

    def test_get_user_model_objects_is_syntek_user_manager(self) -> None:
        """``get_user_model().objects`` must also be a ``SyntekUserManager``."""
        UserModel = get_user_model()  # noqa: N806
        assert isinstance(UserModel.objects, SyntekUserManager), (
            f"get_user_model().objects must be SyntekUserManager; "
            f"got {type(UserModel.objects).__name__}"
        )


# ---------------------------------------------------------------------------
# AC: User factory integration (factory_boy)
# ---------------------------------------------------------------------------


class TestUserFactory:
    """A factory_boy ``UserFactory`` must build a ``User`` instance correctly.

    In the red phase the factory build path raises ``NotImplementedError``
    because ``create_user`` is a stub.  These tests verify the factory is
    correctly wired for the green phase.
    """

    @pytest.fixture
    def user_factory_class(self) -> type:
        """Import the ``UserFactory`` lazily so import errors surface cleanly."""
        try:
            from syntek_auth.factories import (
                UserFactory,  # type: ignore[import-not-found]
            )
        except ImportError:
            pytest.skip("syntek_auth.factories not yet created — skipped in red phase")
        return UserFactory  # type: ignore[return-value]

    def test_user_factory_build_returns_user_instance(
        self, user_factory_class: type
    ) -> None:
        """``UserFactory.build()`` must return a ``User`` instance without hitting the DB."""
        UserModel = get_user_model()  # noqa: N806
        instance = user_factory_class.build()
        assert isinstance(instance, UserModel), (
            f"UserFactory.build() must return a User; got {type(instance).__name__}"
        )

    def test_user_factory_build_has_email(self, user_factory_class: type) -> None:
        """``UserFactory.build()`` must produce an instance with a non-empty email."""
        instance = user_factory_class.build()
        assert instance.email, "UserFactory.build() must set a non-empty email"

    def test_user_factory_build_username_is_optional(
        self, user_factory_class: type
    ) -> None:
        """``UserFactory.build(username=None)`` must not raise."""
        instance = user_factory_class.build(username=None)
        assert instance.username is None, (
            "UserFactory.build(username=None) must produce an instance with username=None"
        )

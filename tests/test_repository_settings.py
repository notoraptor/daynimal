"""
Tests for AnimalRepository settings methods.

This module tests the key-value settings storage:
get_setting, set_setting.
"""

from unittest.mock import patch

from daynimal.repository import AnimalRepository
from daynimal.db.models import UserSettingsModel


# =============================================================================
# SECTION 1: get_setting() (4 tests)
# =============================================================================


def test_get_setting_exists(populated_session):
    """Setting existant → valeur retournée."""
    repo = AnimalRepository(session=populated_session)

    # Set a setting first
    repo.set_setting("language", "fr")

    # Get the setting
    value = repo.get_setting("language")

    assert value == "fr"


def test_get_setting_not_exists_returns_default(populated_session):
    """Setting inexistant avec default → default retourné."""
    repo = AnimalRepository(session=populated_session)

    value = repo.get_setting("nonexistent_key", default="default_value")

    assert value == "default_value"


def test_get_setting_not_exists_returns_none(populated_session):
    """Setting inexistant sans default → None retourné."""
    repo = AnimalRepository(session=populated_session)

    value = repo.get_setting("nonexistent_key")

    assert value is None


def test_get_setting_multiple_keys(populated_session):
    """Plusieurs settings différents stockés et récupérés."""
    repo = AnimalRepository(session=populated_session)

    # Set multiple settings
    repo.set_setting("language", "fr")
    repo.set_setting("theme", "dark")
    repo.set_setting("notifications", "enabled")

    # Get each setting
    assert repo.get_setting("language") == "fr"
    assert repo.get_setting("theme") == "dark"
    assert repo.get_setting("notifications") == "enabled"


# =============================================================================
# SECTION 2: set_setting() (6 tests)
# =============================================================================


def test_set_setting_new(populated_session):
    """Nouveau setting créé."""
    repo = AnimalRepository(session=populated_session)

    repo.set_setting("new_key", "new_value")

    # Verify it's in database
    setting = (
        populated_session.query(UserSettingsModel).filter_by(key="new_key").first()
    )
    assert setting is not None
    assert setting.value == "new_value"


def test_set_setting_update_existing(populated_session):
    """Setting existant mis à jour."""
    repo = AnimalRepository(session=populated_session)

    # Set initial value
    repo.set_setting("language", "en")

    # Update value
    repo.set_setting("language", "fr")

    # Verify updated
    value = repo.get_setting("language")
    assert value == "fr"

    # Verify only one entry exists
    count = populated_session.query(UserSettingsModel).filter_by(key="language").count()
    assert count == 1


def test_set_setting_value_coercion(populated_session):
    """Value converti en string."""
    repo = AnimalRepository(session=populated_session)

    # Set with integer
    repo.set_setting("count", 42)

    # Should be stored as string
    value = repo.get_setting("count")
    assert value == "42"
    assert isinstance(value, str)


def test_set_setting_concurrent_access(populated_session):
    """Accès concurrent à la même clé (simulated)."""
    repo = AnimalRepository(session=populated_session)

    # Simulate concurrent updates
    repo.set_setting("counter", "1")
    repo.set_setting("counter", "2")
    repo.set_setting("counter", "3")

    # Last write wins
    value = repo.get_setting("counter")
    assert value == "3"


def test_set_setting_transaction_commit(populated_session):
    """Commit appelé après set_setting."""
    repo = AnimalRepository(session=populated_session)

    with patch.object(populated_session, "commit") as mock_commit:
        repo.set_setting("test_key", "test_value")
        assert mock_commit.called


def test_get_set_setting_integration(populated_session):
    """Intégration get/set : valeurs cohérentes."""
    repo = AnimalRepository(session=populated_session)

    # Set multiple times
    repo.set_setting("pref", "value1")
    assert repo.get_setting("pref") == "value1"

    repo.set_setting("pref", "value2")
    assert repo.get_setting("pref") == "value2"

    repo.set_setting("pref", "value3")
    assert repo.get_setting("pref") == "value3"

    # Other settings not affected
    repo.set_setting("other", "other_value")
    assert repo.get_setting("pref") == "value3"
    assert repo.get_setting("other") == "other_value"

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from pteero.core.config import LOCALES_PATH, settings

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class I18nManager:
    """A JSON-based localization manager."""

    def __init__(self, locales_path: Path, language: str) -> None:
        """Initializes the class.

        Args:
            locales_path: Path to the directory containing locale JSON files.
            language: The target language code.
        """
        self.locales_path: Path = locales_path
        self.language: str = language
        self._translations: dict[str, str] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Loads the JSON dictionary for the selected language."""
        locale_file = self.locales_path / f"{self.language}.json"

        if not locale_file.exists():
            logger.warning(
                f"Localization file {locale_file} not found. Using raw keys."
            )
            return

        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in localization file {locale_file}: {e}")
        except OSError as e:
            logger.error(f"Failed to read localization file {locale_file}: {e}")

    def get(self, key: str, **kwargs: Any) -> str:
        """Retrieves and formats a translation string by its key.

        Args:
            key: The translation key to look up.
            **kwargs (optional): Arbitrary keyword arguments used to format the translation string.

        Returns:
            The translated and formatted string, or the raw key if not found.
        """
        text = self._translations.get(key, key)

        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing formatting key {e} for translation key '{key}'.")
            except ValueError as e:
                logger.error(f"Formatting error for translation key '{key}': {e}.")

        return text


i18n = I18nManager(LOCALES_PATH, settings.language)
_ = i18n.get

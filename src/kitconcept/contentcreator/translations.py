from .utils import handle_error
from .utils import logger
from kitconcept import api

import csv
import pathlib


try:
    from plone.app.multilingual.api import get_translation_manager
except ImportError:
    get_translation_manager = None


class TranslationError(Exception):
    pass


def link_translations(translation_map: pathlib.Path):
    if get_translation_manager is None:
        logger.warn(
            "Content includes translations but plone.app.multilingual is not installed"
        )
        return

    with translation_map.open("r", newline="") as f:
        reader = enumerate(csv.reader(f), start=1)
        next(reader)  # skip header
        for lineno, (canonical_path, translation_path) in reader:
            try:
                link_translation(canonical_path, translation_path)
            except TranslationError as e:
                handle_error(f"{translation_map.name} line {lineno}: {e}")


def link_translation(canonical_path: str, translation_path: str):
    canonical = api.content.get(canonical_path)
    if canonical is None:
        raise TranslationError(f"Canonical path not found: {canonical_path}")
    if not canonical.language:
        raise TranslationError(f"{canonical_path} has unknown language")
    translation = api.content.get(translation_path)
    if translation is None:
        raise TranslationError(f"Translation path not found: {translation_path}")
    if not translation.language:
        raise TranslationError(f"{translation_path} has unknown language")
    if translation.portal_type != canonical.portal_type:
        raise TranslationError("Canonical and translation type does not match")
    if translation.language == canonical.language:
        raise TranslationError("Can't link translation with the same language")

    tm = get_translation_manager(canonical)
    existing_translation = tm.get_translation(translation.language)
    if (
        existing_translation is not None
        and existing_translation.UID() != translation.UID()
    ):
        tm.remove_translation(translation.language)
        existing_translation = None
    if existing_translation is None:
        tm.register_translation(translation.language, translation)
        logger.info(f"Linked {translation_path} as translation of {canonical_path}")

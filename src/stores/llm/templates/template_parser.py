"""Load and interpolate localized prompt templates."""

import os

class TemplateParser:

    """Resolve localized prompt templates with fallback-language support."""
    def __init__(self, language: str=None, default_language='en'):
        """Initialize localized prompt lookup with a fallback language."""
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None

        self.set_language(language)


    def set_language(self, language: str):
        """Select an available template language with a safe fallback."""
        if not language:
            self.language = self.default_language

        language_path = os.path.join(self.current_path, "locales", language)
        if os.path.exists(language_path):
            self.language = language
        else:
            self.language = self.default_language

    def get(self, group: str, key: str, vars: dict={}):
        """Retrieve the requested record or localized template value."""
        if not group or not key:
            return None

        group_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py" )
        targeted_language = self.language
        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path, "locales", self.default_language, f"{group}.py" )
            targeted_language = self.default_language

        if not os.path.exists(group_path):
            return None

        # import group module
        module = __import__(f"stores.llm.templates.locales.{targeted_language}.{group}", fromlist=[group])

        if not module:
            return None

        key_attribute = getattr(module, key)
        return key_attribute.substitute(vars)

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from src.config import ConfigurationError, load_settings


def valid_environment(**overrides: str) -> dict[str, str]:
    values = {
        "FLASK_ENV": "production",
        "SECRET_KEY": "s" * 48,
        "JWT_SECRET_KEY": "j" * 48,
        "CORS_ORIGINS": "https://app.example.com",
        "CORS_SUPPORTS_CREDENTIALS": "false",
        "ALLOW_DEMO_DATA": "false",
        "ALLOW_PUBLIC_REGISTRATION": "false",
    }
    values.update(overrides)
    return values


class ConfigurationTests(unittest.TestCase):
    def test_secure_production_configuration_loads(self) -> None:
        settings = load_settings(valid_environment())
        self.assertTrue(settings.is_production)
        self.assertEqual(("https://app.example.com",), settings.cors_origins)
        self.assertFalse(settings.allow_demo_data)
        self.assertFalse(settings.allow_public_registration)

    def test_placeholder_secret_is_rejected(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_settings(valid_environment(SECRET_KEY="your-secret-key-change-in-production"))

    def test_wildcard_cors_is_rejected_in_production(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_settings(valid_environment(CORS_ORIGINS="*"))

    def test_demo_data_is_rejected_in_production(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_settings(
                valid_environment(
                    ALLOW_DEMO_DATA="true",
                    DEMO_ADMIN_PASSWORD="Admin-Password-123",
                    DEMO_USER_PASSWORD="Member-Password-123",
                )
            )

    def test_partial_telegram_configuration_is_rejected(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_settings(valid_environment(TELEGRAM_BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyzABCDE"))

    def test_development_demo_mode_requires_strong_passwords(self) -> None:
        values = valid_environment(
            FLASK_ENV="development",
            ALLOW_DEMO_DATA="true",
            DEMO_ADMIN_PASSWORD="Admin-Password-123",
            DEMO_USER_PASSWORD="Member-Password-123",
        )
        settings = load_settings(values)
        self.assertTrue(settings.allow_demo_data)


if __name__ == "__main__":
    unittest.main()

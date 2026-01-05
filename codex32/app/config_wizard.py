"""
Interactive configuration wizard for Codex-32 setup.

Guides users through environment configuration with validation.
Provides a user-friendly alternative to manual .env file editing.
"""

import os
import sys
import secrets
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class ConfigWizard:
    """Interactive configuration setup wizard for Codex-32."""

    def __init__(self, config_path: str = ".env"):
        self.config_path = Path(config_path)
        self.config_data: Dict[str, Any] = {}
        self.validation_errors: Dict[str, str] = {}

    def welcome(self):
        """Display welcome banner and instructions."""
        print("""
╔════════════════════════════════════════════════════════════════╗
║         Codex-32 Configuration Wizard                          ║
║     Let's set up your Codex-32 environment together!           ║
╚════════════════════════════════════════════════════════════════╝

This wizard will guide you through configuring Codex-32.
Press Ctrl+C at any time to cancel.
        """)

    def get_input(
        self,
        prompt: str,
        default: Optional[str] = None,
        validator=None,
        input_type: str = "text",
    ) -> str:
        """
        Get validated user input.

        Args:
            prompt: Question to ask user
            default: Default value if empty input
            validator: Optional validation function
            input_type: Type of input (text, password, number)

        Returns:
            Validated user input
        """
        while True:
            if default:
                display_prompt = f"{prompt} [{default}]: "
            else:
                display_prompt = f"{prompt}: "

            if input_type == "password":
                import getpass
                value = getpass.getpass(display_prompt)
            else:
                value = input(display_prompt).strip()

            # Use default if empty
            if not value and default:
                value = default

            # Skip validation if empty and no default
            if not value:
                if not default:
                    print("❌ Error: This field is required")
                    continue

            # Validate if validator provided
            if validator and value:
                is_valid, error_msg = validator(value)
                if not is_valid:
                    print(f"❌ Error: {error_msg}")
                    continue

            print("✓ Valid")
            return value

    def get_yes_no(self, prompt: str, default: bool = False) -> bool:
        """Get yes/no input."""
        default_str = "yes" if default else "no"
        response = self.get_input(prompt, default=default_str)
        return response.lower() in ["yes", "true", "y", "1"]

    def validate_port(self, port_str: str) -> Tuple[bool, str]:
        """Validate port number."""
        try:
            # Strip leading zeros and validate
            port = int(port_str.lstrip('0') or '0')
            if 1024 <= port <= 65535:
                return True, ""
            return False, f"Port must be between 1024 and 65535 (you entered {port})"
        except ValueError:
            return False, "Port must be a valid number"

    def validate_app_name(self, name: str) -> Tuple[bool, str]:
        """Validate application name (no command-like strings)."""
        forbidden = ['make', 'python', 'pip', '#', ';', '&&', '|', '$', '`']
        if any(forbidden_word in name.lower() for forbidden_word in forbidden):
            return False, "App name cannot contain command keywords (make, python, etc.)"
        if len(name) < 2 or len(name) > 50:
            return False, "App name must be between 2 and 50 characters"
        return True, ""

    def validate_version(self, version: str) -> Tuple[bool, str]:
        """Validate version string."""
        import re
        if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
            return False, "Version must be in format: 1.0 or 1.0.0"
        return True, ""

    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength for security."""
        if not password:
            return False, "Password cannot be empty"
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        # Check for at least some complexity
        has_alpha = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if not (has_alpha and (has_digit or has_special)):
            return False, "Password should contain letters and numbers/special chars"
        return True, ""

    def validate_secret_key(self, key: str) -> Tuple[bool, str]:
        """Validate JWT secret key strength."""
        if len(key) < 32:
            return False, "Secret key must be at least 32 characters (for security)"
        return True, ""

    def validate_db_url(self, url: str) -> Tuple[bool, str]:
        """Validate database URL format."""
        valid_schemes = ("postgresql://", "sqlite://", "mysql://")
        if url.startswith(valid_schemes):
            return True, ""
        return False, f"Invalid database URL. Must start with: {', '.join(valid_schemes)}"

    def validate_log_level(self, level: str) -> Tuple[bool, str]:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level.upper() in valid_levels:
            return True, ""
        return False, f"Must be one of: {', '.join(valid_levels)}"

    def validate_algorithm(self, algo: str) -> Tuple[bool, str]:
        """Validate JWT algorithm."""
        valid_algos = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if algo.upper() in valid_algos:
            return True, ""
        return False, f"Must be one of: {', '.join(valid_algos)}"

    def section_api_settings(self):
        """Configure API settings."""
        print("\n" + "=" * 60)
        print("API SETTINGS")
        print("=" * 60)

        self.config_data["APP_NAME"] = self.get_input(
            "Application name (e.g., 'Codex-32')",
            default="Codex-32",
            validator=self.validate_app_name
        )

        self.config_data["APP_VERSION"] = self.get_input(
            "Application version (e.g., '1.0.0')",
            default="1.0.0",
            validator=self.validate_version
        )

        print("\nWhich environment are you setting up?")
        print("  1. Development (localhost, debug enabled)")
        print("  2. Production (0.0.0.0, debug disabled)")

        env_choice = self.get_input("Choose (1 or 2)", default="1")

        if env_choice == "2":
            self.config_data["API_HOST"] = "0.0.0.0"
            self.config_data["DEBUG"] = "false"
            print("✓ Production setup selected")
        else:
            self.config_data["API_HOST"] = "127.0.0.1"
            self.config_data["DEBUG"] = "true"
            print("✓ Development setup selected")

        self.config_data["API_PORT"] = self.get_input(
            "API port", default="8000", validator=self.validate_port
        )

        self.config_data["LOG_LEVEL"] = self.get_input(
            "Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)",
            default="INFO",
            validator=self.validate_log_level,
        )

    def section_database_settings(self):
        """Configure database settings."""
        print("\n" + "=" * 60)
        print("DATABASE SETTINGS")
        print("=" * 60)

        print("\nWhich database do you want to use?")
        print("  1. SQLite (file-based, no setup needed)")
        print("  2. PostgreSQL (recommended for production)")
        print("  3. MySQL")

        db_choice = self.get_input("Choose (1, 2, or 3)", default="1")

        if db_choice == "2":
            # PostgreSQL setup
            host = self.get_input("PostgreSQL host", default="localhost")
            port = self.get_input(
                "PostgreSQL port", default="5432", validator=self.validate_port
            )
            user = self.get_input("PostgreSQL username", default="postgres")

            # Password validation
            password = ""
            while True:
                password = self.get_input(
                    "PostgreSQL password (leave empty for no password)",
                    default="",
                    input_type="password"
                )

                if not password:
                    print("⚠️  Warning: No password set. Not recommended for production.")
                    confirm = self.get_yes_no("Continue without password?", default=False)
                    if confirm:
                        break
                else:
                    # Validate password strength
                    is_valid, error_msg = self.validate_password_strength(password)
                    if is_valid:
                        break
                    else:
                        print(f"❌ {error_msg}")
                        continue

            database = self.get_input("Database name", default="codex32")

            if password:
                self.config_data["DATABASE_URL"] = (
                    f"postgresql://{user}:{password}@{host}:{port}/{database}"
                )
            else:
                self.config_data["DATABASE_URL"] = (
                    f"postgresql://{user}@{host}:{port}/{database}"
                )

        elif db_choice == "3":
            # MySQL setup
            host = self.get_input("MySQL host", default="localhost")
            port = self.get_input(
                "MySQL port", default="3306", validator=self.validate_port
            )
            user = self.get_input("MySQL username", default="root")

            # Password validation
            password = ""
            while True:
                password = self.get_input(
                    "MySQL password (leave empty for no password)",
                    default="",
                    input_type="password"
                )

                if not password:
                    print("⚠️  Warning: No password set. Not recommended for production.")
                    confirm = self.get_yes_no("Continue without password?", default=False)
                    if confirm:
                        break
                else:
                    is_valid, error_msg = self.validate_password_strength(password)
                    if is_valid:
                        break
                    else:
                        print(f"❌ {error_msg}")
                        continue

            database = self.get_input("Database name", default="codex32")

            if password:
                self.config_data["DATABASE_URL"] = (
                    f"mysql://{user}:{password}@{host}:{port}/{database}"
                )
            else:
                self.config_data["DATABASE_URL"] = (
                    f"mysql://{user}@{host}:{port}/{database}"
                )

        else:
            # SQLite (default)
            db_path = self.get_input("SQLite database file path", default="./data/codex32.db")
            self.config_data["DATABASE_URL"] = f"sqlite:///{db_path}"

    def section_redis_settings(self):
        """Configure Redis (optional)."""
        print("\n" + "=" * 60)
        print("REDIS CACHING (Optional)")
        print("=" * 60)

        use_redis = self.get_yes_no("Use Redis for caching?", default=False)

        if use_redis:
            self.config_data["REDIS_HOST"] = self.get_input(
                "Redis host", default="localhost"
            )
            self.config_data["REDIS_PORT"] = self.get_input(
                "Redis port", default="6379", validator=self.validate_port
            )
            self.config_data["REDIS_DB"] = self.get_input(
                "Redis database number", default="0"
            )
            self.config_data["REDIS_ENABLED"] = "true"
            print("✓ Redis enabled")
        else:
            self.config_data["REDIS_ENABLED"] = "false"
            print("✓ Redis disabled")

    def section_logging_settings(self):
        """Configure logging."""
        print("\n" + "=" * 60)
        print("LOGGING SETTINGS")
        print("=" * 60)

        self.config_data["LOG_FILE"] = self.get_input(
            "Log file path", default="./logs/codex32.log"
        )

        self.config_data["LOG_FORMAT"] = self.get_input(
            "Log format (simple/detailed)",
            default="detailed",
        )

    def section_security_settings(self):
        """Configure security settings."""
        print("\n" + "=" * 60)
        print("SECURITY SETTINGS")
        print("=" * 60)

        # JWT Secret Key
        while True:
            secret_key = self.get_input(
                "JWT secret key (leave empty to auto-generate, min 32 chars)",
                default=""
            )

            if not secret_key:
                # Auto-generate secure secret
                secret_key = secrets.token_urlsafe(32)
                print(f"✓ Auto-generated secure secret")
                break
            else:
                # Validate user-provided secret
                is_valid, error_msg = self.validate_secret_key(secret_key)
                if is_valid:
                    print(f"✓ Secret accepted")
                    break
                else:
                    print(f"❌ {error_msg}")
                    continue

        self.config_data["SECRET_KEY"] = secret_key

        self.config_data["ALGORITHM"] = self.get_input(
            "JWT algorithm (HS256/HS384/HS512)", default="HS256", validator=self.validate_algorithm
        )

        self.config_data["ACCESS_TOKEN_EXPIRE_MINUTES"] = self.get_input(
            "Access token expiry (minutes)", default="30"
        )

        self.config_data["REFRESH_TOKEN_EXPIRE_DAYS"] = self.get_input(
            "Refresh token expiry (days)", default="7"
        )

        print("\n✓ Security settings configured")

    def section_container_settings(self):
        """Configure container engine settings."""
        print("\n" + "=" * 60)
        print("CONTAINER SETTINGS")
        print("=" * 60)

        self.config_data["CONTAINER_STORAGE_DIR"] = self.get_input(
            "Container storage directory", default="./data/containers"
        )

        self.config_data["MAX_CONTAINER_CPU"] = self.get_input(
            "Max CPU per container (cores)", default="2.0"
        )

        self.config_data["MAX_CONTAINER_MEMORY"] = self.get_input(
            "Max memory per container (MB)", default="512"
        )

        print("\n✓ Container settings configured")

    def section_optional_features(self):
        """Configure optional features."""
        print("\n" + "=" * 60)
        print("OPTIONAL FEATURES")
        print("=" * 60)

        enable_stt = self.get_yes_no("Enable Speech-to-Text (STT)?", default=False)
        self.config_data["STT_ENABLED"] = "true" if enable_stt else "false"

        if enable_stt:
            print("\nWhich STT provider?")
            print("  1. Vosk (offline, recommended)")
            print("  2. Google Cloud")

            stt_choice = self.get_input("Choose (1 or 2)", default="1")
            self.config_data["STT_PROVIDER"] = (
                "vosk" if stt_choice == "1" else "google_cloud"
            )

        print("\n✓ Features configured")

    def review_configuration(self) -> bool:
        """Allow user to review and confirm configuration."""
        print("\n" + "=" * 60)
        print("CONFIGURATION REVIEW")
        print("=" * 60)

        for key, value in sorted(self.config_data.items()):
            # Hide sensitive data
            sensitive_keywords = ["PASSWORD", "SECRET", "TOKEN", "KEY"]

            if any(sensitive in key for sensitive in sensitive_keywords):
                display_value = "[HIDDEN]"
            elif key == "DATABASE_URL" and ("@" in str(value)):
                # Mask password in database URL
                display_value = "[HIDDEN - contains credentials]"
            else:
                display_value = str(value)

            print(f"{key:35s} = {display_value}")

        print("\n" + "=" * 60)
        confirm = self.get_yes_no("Is this configuration correct?", default=True)

        return confirm

    def save_configuration(self) -> bool:
        """Save configuration to .env file."""
        try:
            # Backup existing .env if it exists
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(".env.bak")
                print(f"\n📦 Backing up existing config to {backup_path}")
                import shutil
                shutil.copy2(self.config_path, backup_path)

            # Create directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write new .env file
            with open(self.config_path, "w") as f:
                f.write("# Codex-32 Configuration\n")
                f.write("# Auto-generated by configuration wizard\n")
                f.write(f"# Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")

                for key, value in sorted(self.config_data.items()):
                    if isinstance(value, bool):
                        value = str(value).lower()
                    f.write(f"{key}={value}\n")

            print(f"\n✅ Configuration saved to {self.config_path}")
            return True

        except Exception as e:
            print(f"\n❌ Error saving configuration: {e}")
            return False

    def test_configuration(self) -> bool:
        """Test the configuration."""
        print("\n" + "=" * 60)
        print("TESTING CONFIGURATION")
        print("=" * 60)

        # Test database connection
        print("Testing database connection...")
        db_url = self.config_data.get("DATABASE_URL", "")

        if db_url.startswith("sqlite"):
            print("✓ SQLite database configured (no test needed)")
        else:
            print("⚠️  Skipping database test (test later with 'make db-setup')")

        # Test Redis if enabled
        if self.config_data.get("REDIS_ENABLED") == "true":
            print("Testing Redis connection...")
            print("⚠️  Skipping Redis test (test later when running)")

        print("\n✓ Configuration validation passed!")
        return True

    def run(self) -> bool:
        """Execute the configuration wizard."""
        try:
            self.welcome()
            self.section_api_settings()
            self.section_database_settings()
            self.section_redis_settings()
            self.section_logging_settings()
            self.section_security_settings()
            self.section_container_settings()
            self.section_optional_features()

            if not self.review_configuration():
                print("\n⚠️  Configuration cancelled.")
                return False

            if not self.save_configuration():
                return False

            self.test_configuration()

            print("\n" + "=" * 60)
            print("🎉 Configuration Complete!")
            print("=" * 60)
            print("\nNext steps:")
            print("  1. Review your .env file: cat .env")
            print("  2. Setup database (if using PostgreSQL):")
            print("     chmod +x setup_database.sh && ./setup_database.sh")
            print("  3. Start the application:")
            print("     make run")
            print("\n✨ Happy botting!")

            return True

        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user.")
            return False
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Entry point for the configuration wizard."""
    wizard = ConfigWizard()
    success = wizard.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

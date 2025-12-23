#!/usr/bin/env python
"""
Initialize a new bot from a template.

Usage:
    python scripts/init-bot.py --template worker --name my_bot
    python scripts/init-bot.py --template collector --name data_gatherer
"""

import sys
import os
import argparse
import shutil
from pathlib import Path
from datetime import datetime


TEMPLATES = {
    "worker": "Worker bot for processing tasks",
    "collector": "Collector bot for data gathering",
    "api": "API bot that exposes endpoints",
    "ml": "ML bot with model inference",
    "orchestrator": "Orchestrator for coordinating other bots"
}


def validate_bot_name(name: str) -> bool:
    """Validate bot name."""
    if not name:
        print("❌ Bot name cannot be empty")
        return False

    if not name.replace("_", "").replace("-", "").isalnum():
        print("❌ Bot name must contain only alphanumeric characters, dashes, and underscores")
        return False

    if len(name) < 3 or len(name) > 50:
        print("❌ Bot name must be between 3 and 50 characters")
        return False

    return True


def list_templates():
    """List available templates."""
    print("\nAvailable templates:")
    print("-" * 50)
    for template, description in TEMPLATES.items():
        print(f"  {template:15s} - {description}")
    print("-" * 50 + "\n")


def init_bot_from_template(template: str, name: str, force: bool = False) -> bool:
    """
    Initialize a new bot from template.

    Args:
        template: Template name
        name: New bot name
        force: Overwrite existing bot if it exists

    Returns:
        True if successful, False otherwise
    """
    # Validate inputs
    if not validate_bot_name(name):
        return False

    # Check template exists
    template_path = Path("templates") / template

    if not template_path.exists():
        print(f"❌ Template not found: {template}")
        list_templates()
        return False

    if not template_path.is_dir():
        print(f"❌ Template path is not a directory: {template_path}")
        return False

    # Check bot doesn't already exist
    bot_path = Path("bots") / name

    if bot_path.exists():
        if not force:
            print(f"❌ Bot already exists: {bot_path}")
            print(f"   Use --force to overwrite")
            return False
        else:
            print(f"⚠️  Removing existing bot: {bot_path}")
            shutil.rmtree(bot_path)

    # Copy template
    try:
        print(f"📦 Creating bot from template: {template}")
        shutil.copytree(template_path, bot_path)

        # Create additional directories
        tests_dir = bot_path / "tests"
        tests_dir.mkdir(exist_ok=True)

        # Update config with bot name
        config_file = bot_path / "config.yaml"
        if config_file.exists():
            with open(config_file, "r") as f:
                config = f.read()

            # Replace template name with actual name
            config = config.replace("worker_bot", name)
            config = config.replace("collector_bot", name)
            config = config.replace("api_bot", name)
            config = config.replace("ml_bot", name)
            config = config.replace("orchestrator_bot", name)

            with open(config_file, "w") as f:
                f.write(config)

        # Create __init__.py for tests
        init_file = tests_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        print(f"✅ Bot created: {bot_path}")

        print(f"\n📝 Next steps:")
        print(f"   1. Customize the bot:")
        print(f"      nano {bot_path}/bot.py")
        print(f"")
        print(f"   2. Test locally:")
        print(f"      cd {bot_path}")
        print(f"      python bot.py")
        print(f"")
        print(f"   3. Deploy to Codex-32:")
        print(f"      curl -X POST http://localhost:8000/api/v1/bots/register \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d @{bot_path}/config.yaml")
        print(f"")
        print(f"📚 Documentation: {bot_path}/README.md")
        print(f"")

        return True

    except Exception as e:
        print(f"❌ Error creating bot: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize a new bot from a template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/init-bot.py --template worker --name my_bot
  python scripts/init-bot.py --template collector --name data_gatherer
  python scripts/init-bot.py --list
        """
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available templates"
    )

    parser.add_argument(
        "--template", "-t",
        choices=list(TEMPLATES.keys()),
        help="Template to use"
    )

    parser.add_argument(
        "--name", "-n",
        help="Bot name"
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing bot"
    )

    args = parser.parse_args()

    # Check if we're in the right directory
    if not Path("templates").exists():
        print("❌ Cannot find 'templates' directory")
        print("   Make sure you're running this from the Codex-32 root directory")
        sys.exit(1)

    if not Path("bots").exists():
        print("📁 Creating 'bots' directory")
        Path("bots").mkdir()

    # Handle list command
    if args.list:
        list_templates()
        sys.exit(0)

    # Check required arguments
    if not args.template or not args.name:
        parser.print_help()
        sys.exit(1)

    # Initialize bot
    success = init_bot_from_template(args.template, args.name, args.force)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

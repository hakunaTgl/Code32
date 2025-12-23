"""
Intelligent Bot Builder - AI-powered, user-friendly bot creation system.
Converts natural language descriptions into fully functional bots without requiring code knowledge.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import httpx


@dataclass
class BotRequirements:
    """User-friendly bot requirements from natural language description."""
    name: str
    description: str
    purpose: str  # What the bot does
    primary_task: str  # Main function (process, collect, api_call, analyze, etc.)
    input_type: str  # What data it processes
    output_type: str  # What it produces
    frequency: str  # How often it runs (continuous, scheduled, triggered, manual)
    complexity: str  # simple, moderate, advanced
    special_features: List[str]  # Error handling, logging, monitoring, etc.


class NLPBotInterpreter:
    """Convert natural language to bot specifications."""

    # Keywords for task type detection
    TASK_KEYWORDS = {
        'process': ['process', 'transform', 'convert', 'manipulate', 'change'],
        'collect': ['collect', 'gather', 'scrape', 'fetch', 'retrieve'],
        'api_call': ['call', 'request', 'api', 'webhook', 'http'],
        'analyze': ['analyze', 'analyze', 'examine', 'study', 'review'],
        'monitor': ['monitor', 'watch', 'track', 'observe', 'check'],
        'store': ['store', 'save', 'write', 'backup', 'archive'],
        'notify': ['notify', 'alert', 'message', 'email', 'send'],
    }

    FREQUENCY_KEYWORDS = {
        'continuous': ['continuous', '24/7', 'always', 'constantly', 'real-time'],
        'scheduled': ['scheduled', 'daily', 'weekly', 'hourly', 'minute', 'every'],
        'triggered': ['triggered', 'event', 'when', 'on', 'fire'],
        'manual': ['manual', 'on-demand', 'button', 'command', 'user'],
    }

    async def interpret(self, description: str) -> BotRequirements:
        """Convert natural language to bot requirements."""
        description_lower = description.lower()

        # Detect task type
        task_type = self._detect_task_type(description_lower)

        # Detect frequency
        frequency = self._detect_frequency(description_lower)

        # Detect complexity
        complexity = self._detect_complexity(description_lower)

        # Extract features
        features = self._detect_features(description_lower)

        # Detect input/output types
        input_type, output_type = self._detect_io_types(description_lower, task_type)

        # Extract name and purpose
        name, purpose = self._extract_name_purpose(description)

        return BotRequirements(
            name=name,
            description=description,
            purpose=purpose,
            primary_task=task_type,
            input_type=input_type,
            output_type=output_type,
            frequency=frequency,
            complexity=complexity,
            special_features=features,
        )

    def _detect_task_type(self, text: str) -> str:
        """Detect what type of task the bot performs."""
        for task, keywords in self.TASK_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return task
        return 'process'  # Default

    def _detect_frequency(self, text: str) -> str:
        """Detect how often bot runs."""
        for freq, keywords in self.FREQUENCY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return freq
        return 'triggered'  # Default

    def _detect_complexity(self, text: str) -> str:
        """Detect complexity level."""
        advanced_words = ['machine learning', 'ml', 'ai', 'complex', 'advanced', 'neural', 'model']
        moderate_words = ['database', 'api', 'multiple', 'filter', 'sort']

        if any(word in text for word in advanced_words):
            return 'advanced'
        elif any(word in text for word in moderate_words):
            return 'moderate'
        return 'simple'

    def _detect_features(self, text: str) -> List[str]:
        """Detect special features needed."""
        features = []
        feature_keywords = {
            'error_handling': ['error', 'fail', 'retry', 'exception'],
            'logging': ['log', 'debug', 'track', 'record'],
            'notification': ['notify', 'alert', 'email', 'message'],
            'caching': ['cache', 'fast', 'optimize', 'performance'],
            'database': ['database', 'db', 'store', 'sql'],
            'api': ['api', 'rest', 'http', 'endpoint'],
            'scheduling': ['schedule', 'time', 'cron', 'interval'],
        }

        for feature, keywords in feature_keywords.items():
            if any(keyword in text for keyword in keywords):
                features.append(feature)

        return features

    def _detect_io_types(self, text: str, task_type: str) -> Tuple[str, str]:
        """Detect input and output types."""
        io_keywords = {
            'json': ['json', 'api', 'request'],
            'csv': ['csv', 'data', 'file', 'spreadsheet'],
            'text': ['text', 'string', 'document', 'content'],
            'image': ['image', 'photo', 'picture', 'visual'],
            'database': ['database', 'db', 'sql', 'record'],
        }

        input_type = 'json'  # Default
        output_type = 'json'  # Default

        for io, keywords in io_keywords.items():
            if any(keyword in text for keyword in keywords):
                if input_type == 'json':
                    input_type = io
                output_type = io

        return input_type, output_type

    def _extract_name_purpose(self, description: str) -> Tuple[str, str]:
        """Extract bot name and purpose from description."""
        lines = description.split('\n')
        first_line = lines[0]

        # Simple name extraction (first 2-3 words + bot)
        words = first_line.split()[:3]
        name = '_'.join(words).lower().replace('-', '_')
        name = ''.join(c for c in name if c.isalnum() or c == '_')
        name = name[:30]  # Max 30 chars

        # Purpose is first line cleaned up
        purpose = first_line.strip()
        if len(purpose) > 200:
            purpose = purpose[:200] + '...'

        return name or 'custom_bot', purpose or description[:100]


class BotCodeGenerator:
    """Generate bot code from requirements."""

    TASK_TEMPLATES = {
        'process': '''
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Process and transform input data."""
    try:
        data = task.get('data', {{}})

        # Transform logic
        result = await self._transform_data(data)

        self.processed_count += 1
        return {{"status": "success", "result": result}}
    except Exception as e:
        self.error_count += 1
        self.logger.error(f"Processing error: {{e}}")
        return {{"status": "error", "message": str(e)}}
''',
        'collect': '''
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Collect and gather data from sources."""
    try:
        source = task.get('source', 'default')

        # Collection logic
        data = await self._collect_from_source(source)

        self.processed_count += 1
        return {{"status": "success", "data": data, "count": len(data)}}
    except Exception as e:
        self.error_count += 1
        self.logger.error(f"Collection error: {{e}}")
        return {{"status": "error", "message": str(e)}}
''',
        'api_call': '''
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Make API calls and handle responses."""
    try:
        endpoint = task.get('endpoint', '')
        params = task.get('params', {{}})

        # API call logic
        result = await self._call_api(endpoint, params)

        self.processed_count += 1
        return {{"status": "success", "response": result}}
    except Exception as e:
        self.error_count += 1
        self.logger.error(f"API error: {{e}}")
        return {{"status": "error", "message": str(e)}}
''',
        'analyze': '''
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze and examine data."""
    try:
        data = task.get('data', {{}})

        # Analysis logic
        analysis = await self._analyze(data)

        self.processed_count += 1
        return {{"status": "success", "analysis": analysis}}
    except Exception as e:
        self.error_count += 1
        self.logger.error(f"Analysis error: {{e}}")
        return {{"status": "error", "message": str(e)}}
''',
    }

    def generate_bot_code(self, requirements: BotRequirements) -> str:
        """Generate bot.py code from requirements."""
        template = self.TASK_TEMPLATES.get(requirements.primary_task, self.TASK_TEMPLATES['process'])

        bot_code = f'''"""
{requirements.purpose}

Auto-generated bot from AI Bot Builder.
Task: {requirements.primary_task}
Frequency: {requirements.frequency}
Complexity: {requirements.complexity}
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime


class {self._class_name(requirements.name)}(object):
    """AI-generated bot: {requirements.purpose}"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the bot."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processed_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

    {template.strip()}

    async def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data (override this method)."""
        # TODO: Implement your transformation logic
        return data

    async def _collect_from_source(self, source: str) -> list:
        """Collect data from source (override this method)."""
        # TODO: Implement your collection logic
        return []

    async def _call_api(self, endpoint: str, params: Dict) -> Dict:
        """Call external API (override this method)."""
        # TODO: Implement your API call logic
        return {{"status": "success"}}

    async def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data (override this method)."""
        # TODO: Implement your analysis logic
        return {{"summary": "Analysis complete"}}

    async def get_status(self) -> Dict[str, Any]:
        """Get bot status."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {{
            "name": "{requirements.name}",
            "status": "active",
            "processed": self.processed_count,
            "errors": self.error_count,
            "uptime_seconds": uptime,
            "purpose": "{requirements.purpose}",
        }}

    async def run(self):
        """Main bot loop (override for custom behavior)."""
        self.logger.info(f"Starting {{self.__class__.__name__}}")
        try:
            while True:
                # Main processing loop
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Bot shutdown requested")


if __name__ == "__main__":
    # Example usage
    config = {{"name": "{requirements.name}"}}
    bot = {self._class_name(requirements.name)}(config)
    asyncio.run(bot.run())
'''
        return bot_code

    def generate_config_yaml(self, requirements: BotRequirements) -> str:
        """Generate config.yaml from requirements."""
        config = f'''name: {requirements.name}
description: {requirements.description}
purpose: {requirements.purpose}
version: "1.0"
role: worker

task_type: {requirements.primary_task}
frequency: {requirements.frequency}
complexity: {requirements.complexity}

input_type: {requirements.input_type}
output_type: {requirements.output_type}

features:
  - {requirements.special_features[0] if requirements.special_features else 'basic'}
{chr(10).join(f"  - {f}" for f in requirements.special_features[1:]) if len(requirements.special_features) > 1 else ""}

deployment_config:
  cpu_request: "0.5"
  memory_request: "256Mi"
  replicas: 1

environment:
  LOG_LEVEL: INFO
  TASK_TIMEOUT: "300"

metadata:
  created_by: "AI Bot Builder"
  auto_generated: true
  template: "intelligent_bot"
'''
        return config

    def generate_requirements_txt(self, requirements: BotRequirements) -> str:
        """Generate requirements.txt based on features."""
        requirements_list = ['asyncio', 'python-dotenv', 'aiohttp']

        if 'database' in requirements.special_features:
            requirements_list.extend(['sqlalchemy', 'asyncpg', 'psycopg2-binary'])

        if 'api' in requirements.special_features:
            requirements_list.extend(['httpx', 'requests'])

        if 'notification' in requirements.special_features:
            requirements_list.extend(['aiosmtplib', 'python-telegram-bot'])

        if 'caching' in requirements.special_features:
            requirements_list.extend(['redis', 'aioredis'])

        if requirements.complexity == 'advanced':
            requirements_list.extend(['numpy', 'pandas', 'scikit-learn'])

        return '\n'.join(sorted(set(requirements_list)))

    @staticmethod
    def _class_name(name: str) -> str:
        """Convert snake_case to CamelCase."""
        return ''.join(word.capitalize() for word in name.split('_')) + 'Bot'


class IntelligentBotBuilder:
    """Main orchestrator for intelligent bot creation."""

    def __init__(self):
        self.nlp = NLPBotInterpreter()
        self.generator = BotCodeGenerator()

    async def create_from_description(self, description: str, bot_dir: Path) -> Dict[str, str]:
        """Create complete bot from natural language description."""

        # Step 1: Interpret the description
        requirements = await self.nlp.interpret(description)

        # Step 2: Generate code and configs
        bot_code = self.generator.generate_bot_code(requirements)
        config_yaml = self.generator.generate_config_yaml(requirements)
        requirements_txt = self.generator.generate_requirements_txt(requirements)

        # Step 3: Create bot directory
        bot_dir.mkdir(parents=True, exist_ok=True)

        # Step 4: Write files
        (bot_dir / 'bot.py').write_text(bot_code)
        (bot_dir / 'config.yaml').write_text(config_yaml)
        (bot_dir / 'requirements.txt').write_text(requirements_txt)

        # Step 5: Return summary
        return {
            'name': requirements.name,
            'description': requirements.purpose,
            'task_type': requirements.primary_task,
            'complexity': requirements.complexity,
            'features': requirements.special_features,
            'files_created': ['bot.py', 'config.yaml', 'requirements.txt'],
            'path': str(bot_dir),
            'ready_to_deploy': True,
        }


# Convenience function for use in API
async def create_bot_from_natural_language(description: str, bots_dir: Path) -> Dict[str, Any]:
    """Easy entry point for creating bots from natural language."""
    builder = IntelligentBotBuilder()

    # Extract bot name from description
    lines = description.split('\n')
    name = lines[0].split()[0].lower()

    bot_dir = bots_dir / name

    result = await builder.create_from_description(description, bot_dir)
    return result

#!/usr/bin/env python3
"""
Main entry point for Victor Synthetic Orchestrator.
"""

import asyncio
import logging
import sys
from pathlib import Path

from orchestrator import VictorOrchestrator
from orchestrator.config import Config


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('victor_orchestrator.log')
        ]
    )


async def main():
    """Main entry point."""
    # Load configuration
    config_path = Path("config/default.json")
    config = Config(str(config_path) if config_path.exists() else None)
    
    # Setup logging
    log_level = config.get("orchestrator.log_level", "INFO")
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Victor Synthetic Orchestrator")
    logger.info("MASSIVEMAGNETICS AI Ecosystem")
    logger.info("=" * 60)
    
    # Create and run orchestrator
    orchestrator = VictorOrchestrator(config.to_dict())
    
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

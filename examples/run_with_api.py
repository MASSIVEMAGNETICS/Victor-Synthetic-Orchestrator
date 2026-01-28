#!/usr/bin/env python3
"""
Run Victor Orchestrator with API server.

This script starts the orchestrator with the REST API interface enabled.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import VictorOrchestrator
from orchestrator.api import VictorAPI
from orchestrator.config import Config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run orchestrator with API."""
    
    # Load configuration
    config = Config("config/default.json")
    
    # Create orchestrator
    logger.info("Creating Victor Orchestrator...")
    orchestrator = VictorOrchestrator(config.to_dict())
    
    # Create API
    logger.info("Creating API interface...")
    api = VictorAPI(orchestrator, config)
    
    # Start orchestrator
    orchestrator_task = asyncio.create_task(orchestrator.run())
    
    # Start API server
    logger.info("Starting API server...")
    try:
        await api.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await orchestrator.shutdown()
        orchestrator_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

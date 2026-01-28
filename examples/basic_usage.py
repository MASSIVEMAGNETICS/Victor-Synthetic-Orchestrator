#!/usr/bin/env python3
"""
Example usage of Victor Synthetic Orchestrator.

This example demonstrates:
1. Initializing the orchestrator
2. Registering agents from ecosystem modules
3. Starting the orchestrator
4. Submitting tasks for orchestration
5. Monitoring system status
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import VictorOrchestrator
from orchestrator.adapters import (
    VictorHubAdapter,
    BrainAIAdapter,
    ProjectFOLAdapter,
    SunokillerAdapter,
    NexusForgeAdapter
)
from orchestrator.config import Config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    
    # Load configuration
    config = Config()
    
    # Create orchestrator
    logger.info("Creating Victor Orchestrator...")
    orchestrator = VictorOrchestrator(config.to_dict())
    
    # Initialize orchestrator in background
    init_task = asyncio.create_task(orchestrator.initialize())
    await init_task
    
    # Register agents from ecosystem modules
    logger.info("Registering ecosystem agents...")
    
    # Register Victor Hub
    victor_hub = VictorHubAdapter()
    await orchestrator.register_agent(victor_hub)
    
    # Register Brain AI
    brain_ai = BrainAIAdapter()
    await orchestrator.register_agent(brain_ai)
    
    # Register Project FOL
    project_fol = ProjectFOLAdapter()
    await orchestrator.register_agent(project_fol)
    
    # Register SUNOKILLER
    sunokiller = SunokillerAdapter()
    await orchestrator.register_agent(sunokiller)
    
    # Register NexusForge
    nexusforge = NexusForgeAdapter()
    await orchestrator.register_agent(nexusforge)
    
    logger.info(f"Registered {len(orchestrator.agents)} agents")
    
    # Get orchestrator status
    status = orchestrator.get_status()
    logger.info(f"Orchestrator Status: {status}")
    
    # Example 1: Intelligence query through Victor Hub
    logger.info("\n=== Example 1: Intelligence Query ===")
    task1 = {
        "name": "intelligence_query",
        "type": "intelligence_query",
        "query": "What is the meaning of consciousness?",
        "agents": [{"type": "intelligence_hub"}]
    }
    
    result1 = await orchestrator.orchestrate_task(task1)
    logger.info(f"Result: {result1}")
    
    # Example 2: Neural simulation with Brain AI
    logger.info("\n=== Example 2: Neural Simulation ===")
    task2 = {
        "name": "cognitive_simulation",
        "type": "cognitive_process",
        "process": "decision_making",
        "agents": [{"type": "neural_simulation"}]
    }
    
    result2 = await orchestrator.orchestrate_task(task2)
    logger.info(f"Result: {result2}")
    
    # Example 3: Distributed inference with Project FOL
    logger.info("\n=== Example 3: Distributed Inference ===")
    task3 = {
        "name": "distributed_analysis",
        "type": "distributed_inference",
        "data": {"pattern": "sacred_geometry"},
        "agents": [{"type": "geometric_intelligence"}]
    }
    
    result3 = await orchestrator.orchestrate_task(task3)
    logger.info(f"Result: {result3}")
    
    # Example 4: Audio synthesis with SUNOKILLER
    logger.info("\n=== Example 4: Audio Synthesis ===")
    task4 = {
        "name": "generate_music",
        "type": "generate_audio",
        "parameters": {
            "type": "music",
            "style": "ambient",
            "duration": 60
        },
        "agents": [{"type": "audio_synthesis"}]
    }
    
    result4 = await orchestrator.orchestrate_task(task4)
    logger.info(f"Result: {result4}")
    
    # Display final metrics
    logger.info("\n=== Final Status ===")
    final_status = orchestrator.get_status()
    logger.info(f"State: {final_status['state']}")
    logger.info(f"Tasks Processed: {final_status['metrics']['total_tasks_processed']}")
    logger.info(f"Uptime: {final_status['uptime']:.2f} seconds")
    logger.info(f"Self-Aware: {final_status['self_aware']}")
    
    # Get health status
    health = orchestrator.monitor.get_health_status()
    logger.info(f"Health: {health['overall']}")
    
    # Shutdown
    logger.info("\nShutting down orchestrator...")
    await orchestrator.shutdown()
    
    logger.info("Example completed!")


if __name__ == "__main__":
    asyncio.run(main())

"""
Core orchestrator engine for Victor Synthetic system.
Manages the lifecycle and coordination of all AI agents and modules.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .agent import BaseAgent, AgentStatus
from .registry import ModuleRegistry
from .communication import MessageBus
from .monitoring import SystemMonitor


class OrchestratorState(Enum):
    """Orchestrator operational states."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    ERROR = "error"


class VictorOrchestrator:
    """
    Main orchestrator class coordinating the MASSIVEMAGNETICS AI ecosystem.
    
    This autonomous super-intelligent agent orchestrates:
    - Victor Synthetic Super Intelligence Hub
    - brain_ai (brain simulation)
    - project-fol (Flower of Life 37-node system)
    - SUNOKILLER (audio synthesis)
    - NexusForge-2.0 (fractal agents)
    - Bando-Fi-AI (creative AI)
    - next-gen-game-engine
    - tooki (research lab)
    - ray-ray (distributed compute)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Victor Orchestrator.
        
        Args:
            config: Configuration dictionary for the orchestrator
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.state = OrchestratorState.INITIALIZING
        
        # Core components
        self.registry = ModuleRegistry()
        self.message_bus = MessageBus()
        self.monitor = SystemMonitor(self)
        
        # Agent management
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: List[asyncio.Task] = []
        
        # Self-awareness attributes
        self.start_time = None
        self.metrics = {
            "total_tasks_processed": 0,
            "active_agents": 0,
            "total_messages": 0,
            "uptime_seconds": 0
        }
        
        self.logger.info("Victor Orchestrator initialized")
    
    async def initialize(self):
        """Initialize all orchestrator components and load modules."""
        try:
            self.logger.info("Starting orchestrator initialization...")
            self.start_time = datetime.now()
            
            # Initialize message bus
            await self.message_bus.initialize()
            
            # Initialize monitoring
            await self.monitor.start()
            
            # Load ecosystem modules
            await self._load_ecosystem_modules()
            
            self.state = OrchestratorState.ACTIVE
            self.logger.info("Victor Orchestrator fully initialized and active")
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.state = OrchestratorState.ERROR
            raise
    
    async def _load_ecosystem_modules(self):
        """Load all MASSIVEMAGNETICS ecosystem modules."""
        ecosystem_modules = [
            "victor_intelligence_hub",
            "brain_ai",
            "project_fol",
            "sunokiller",
            "nexusforge",
            "bando_fi_ai",
            "game_engine",
            "tooki",
            "ray_compute"
        ]
        
        for module_name in ecosystem_modules:
            try:
                self.logger.info(f"Loading module: {module_name}")
                await self.registry.register_module(module_name)
            except Exception as e:
                self.logger.warning(f"Could not load {module_name}: {e}")
    
    async def register_agent(self, agent: BaseAgent):
        """
        Register a new agent with the orchestrator.
        
        Args:
            agent: The agent instance to register
        """
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent {agent.agent_id} already registered")
        
        self.agents[agent.agent_id] = agent
        agent.orchestrator = self
        self.metrics["active_agents"] = len(self.agents)
        
        self.logger.info(f"Registered agent: {agent.agent_id}")
        await self.message_bus.publish("agent.registered", {
            "agent_id": agent.agent_id,
            "agent_type": agent.__class__.__name__
        })
    
    async def start_agent(self, agent_id: str):
        """
        Start an agent's execution.
        
        Args:
            agent_id: ID of the agent to start
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        task = asyncio.create_task(agent.run())
        self.tasks.append(task)
        
        self.logger.info(f"Started agent: {agent_id}")
    
    async def stop_agent(self, agent_id: str):
        """
        Stop an agent's execution.
        
        Args:
            agent_id: ID of the agent to stop
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        await agent.stop()
        
        self.logger.info(f"Stopped agent: {agent_id}")
    
    async def orchestrate_task(self, task_spec: Dict[str, Any]) -> Any:
        """
        Orchestrate a task across multiple agents.
        
        Args:
            task_spec: Task specification including type, parameters, and requirements
            
        Returns:
            Task result
        """
        self.logger.info(f"Orchestrating task: {task_spec.get('name', 'unnamed')}")
        self.metrics["total_tasks_processed"] += 1
        
        # Task orchestration logic
        task_type = task_spec.get("type")
        required_agents = task_spec.get("agents", [])
        
        # Allocate agents for the task
        allocated_agents = []
        for agent_requirement in required_agents:
            agent = await self._allocate_agent(agent_requirement)
            if agent:
                allocated_agents.append(agent)
        
        # Execute task across agents
        results = []
        for agent in allocated_agents:
            result = await agent.execute_task(task_spec)
            results.append(result)
        
        # Synthesize results
        final_result = self._synthesize_results(results)
        
        return final_result
    
    async def _allocate_agent(self, requirement: Dict[str, Any]) -> Optional[BaseAgent]:
        """Allocate an appropriate agent for a task requirement."""
        agent_type = requirement.get("type")
        
        # Find available agent of required type
        for agent in self.agents.values():
            if (agent.status == AgentStatus.IDLE and 
                agent.capabilities.get("type") == agent_type):
                return agent
        
        return None
    
    def _synthesize_results(self, results: List[Any]) -> Any:
        """Synthesize multiple agent results into unified output."""
        if not results:
            return None
        if len(results) == 1:
            return results[0]
        
        # Combine results based on type
        return {
            "combined_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run(self):
        """Main orchestrator event loop."""
        await self.initialize()
        
        self.logger.info("Victor Orchestrator running...")
        
        try:
            while self.state == OrchestratorState.ACTIVE:
                # Update metrics
                if self.start_time:
                    uptime = (datetime.now() - self.start_time).total_seconds()
                    self.metrics["uptime_seconds"] = uptime
                
                # Self-awareness: Monitor system health
                await self.monitor.check_health()
                
                # Process any pending orchestrator-level tasks
                await self._process_orchestrator_tasks()
                
                # Allow other tasks to run
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("Orchestrator cancelled, shutting down...")
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            self.state = OrchestratorState.ERROR
        finally:
            await self.shutdown()
    
    async def _process_orchestrator_tasks(self):
        """Process orchestrator-level maintenance tasks."""
        # Clean up completed tasks
        self.tasks = [task for task in self.tasks if not task.done()]
        
        # Update active agent count
        active_count = sum(
            1 for agent in self.agents.values() 
            if agent.status == AgentStatus.ACTIVE
        )
        self.metrics["active_agents"] = active_count
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator and all agents."""
        self.logger.info("Shutting down Victor Orchestrator...")
        self.state = OrchestratorState.SHUTTING_DOWN
        
        # Stop all agents
        for agent_id in list(self.agents.keys()):
            try:
                await self.stop_agent(agent_id)
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent_id}: {e}")
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Shutdown monitoring
        await self.monitor.stop()
        
        # Shutdown message bus
        await self.message_bus.shutdown()
        
        self.state = OrchestratorState.STOPPED
        self.logger.info("Victor Orchestrator stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status and metrics.
        
        Returns:
            Status dictionary with system state and metrics
        """
        return {
            "state": self.state.value,
            "metrics": self.metrics.copy(),
            "registered_agents": len(self.agents),
            "active_tasks": len([t for t in self.tasks if not t.done()]),
            "loaded_modules": self.registry.get_module_count(),
            "uptime": self.metrics["uptime_seconds"],
            "self_aware": True  # System is self-monitoring
        }

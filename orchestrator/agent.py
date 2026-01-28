"""
Base agent interface and implementations for the orchestrator.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class AgentStatus(Enum):
    """Agent operational states."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class BaseAgent(ABC):
    """
    Base class for all agents in the Victor Synthetic system.
    
    All ecosystem modules implement this interface to participate
    in the orchestration framework.
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            config: Agent configuration
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.status = AgentStatus.IDLE
        self.orchestrator = None
        
        # Agent capabilities
        self.capabilities: Dict[str, Any] = {}
        
        # Metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_runtime": 0.0
        }
        
        self._running = False
        self._task_queue = asyncio.Queue()
    
    @abstractmethod
    async def initialize(self):
        """Initialize the agent. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def execute_task(self, task_spec: Dict[str, Any]) -> Any:
        """
        Execute a specific task.
        
        Args:
            task_spec: Task specification
            
        Returns:
            Task result
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup agent resources. Must be implemented by subclasses."""
        pass
    
    async def run(self):
        """Main agent execution loop."""
        self._running = True
        self.status = AgentStatus.ACTIVE
        
        try:
            await self.initialize()
            
            while self._running:
                try:
                    # Wait for tasks with timeout
                    task = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=1.0
                    )
                    
                    self.status = AgentStatus.BUSY
                    start_time = datetime.now()
                    
                    # Execute task
                    result = await self.execute_task(task)
                    
                    # Update metrics
                    runtime = (datetime.now() - start_time).total_seconds()
                    self.metrics["tasks_completed"] += 1
                    self.metrics["total_runtime"] += runtime
                    
                    self.status = AgentStatus.ACTIVE
                    
                except asyncio.TimeoutError:
                    # No task available, continue
                    self.status = AgentStatus.IDLE
                    continue
                    
                except Exception as e:
                    self.logger.error(f"Task execution error: {e}")
                    self.metrics["tasks_failed"] += 1
                    self.status = AgentStatus.ERROR
                    
        finally:
            await self.cleanup()
            self.status = AgentStatus.STOPPED
    
    async def stop(self):
        """Stop the agent."""
        self._running = False
        self.logger.info(f"Agent {self.agent_id} stopping...")
    
    async def submit_task(self, task_spec: Dict[str, Any]):
        """
        Submit a task to the agent's queue.
        
        Args:
            task_spec: Task specification
        """
        await self._task_queue.put(task_spec)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "metrics": self.metrics.copy()
        }

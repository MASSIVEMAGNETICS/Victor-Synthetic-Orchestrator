"""
System monitoring and self-awareness capabilities.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime


class SystemMonitor:
    """
    System monitoring for self-awareness and health tracking.
    
    Provides the orchestrator with self-monitoring and introspection
    capabilities for autonomous operation.
    """
    
    def __init__(self, orchestrator):
        """
        Initialize the system monitor.
        
        Args:
            orchestrator: Reference to the orchestrator
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._monitor_task = None
        
        # Health metrics
        self.health_status = {
            "overall": "healthy",
            "components": {},
            "last_check": None
        }
    
    async def start(self):
        """Start the monitoring system."""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("System monitor started")
    
    async def stop(self):
        """Stop the monitoring system."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("System monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self.check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
    
    async def check_health(self):
        """
        Perform health check on all system components.
        
        This is the self-awareness mechanism.
        """
        self.health_status["last_check"] = datetime.now().isoformat()
        
        # Check orchestrator state
        if hasattr(self.orchestrator, 'state'):
            state_healthy = str(self.orchestrator.state.value) in ['active', 'initializing']
            self.health_status["components"]["orchestrator"] = (
                "healthy" if state_healthy else "unhealthy"
            )
        
        # Check message bus
        if hasattr(self.orchestrator, 'message_bus'):
            bus_healthy = self.orchestrator.message_bus._running
            self.health_status["components"]["message_bus"] = (
                "healthy" if bus_healthy else "unhealthy"
            )
        
        # Check agents
        if hasattr(self.orchestrator, 'agents'):
            agent_count = len(self.orchestrator.agents)
            healthy_agents = sum(
                1 for agent in self.orchestrator.agents.values()
                if agent.status.value not in ['error', 'stopped']
            )
            
            self.health_status["components"]["agents"] = {
                "total": agent_count,
                "healthy": healthy_agents,
                "status": "healthy" if healthy_agents == agent_count else "degraded"
            }
        
        # Determine overall health
        component_statuses = []
        for key, value in self.health_status["components"].items():
            if isinstance(value, dict):
                component_statuses.append(value.get("status", "unknown"))
            else:
                component_statuses.append(value)
        
        if all(s == "healthy" for s in component_statuses):
            self.health_status["overall"] = "healthy"
        elif any(s == "unhealthy" for s in component_statuses):
            self.health_status["overall"] = "unhealthy"
        else:
            self.health_status["overall"] = "degraded"
        
        self.logger.debug(f"Health check: {self.health_status['overall']}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status.
        
        Returns:
            Health status dictionary
        """
        return self.health_status.copy()

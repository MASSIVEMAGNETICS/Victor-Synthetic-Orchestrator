"""
Tests for agent functionality.
"""

import pytest
import asyncio
from orchestrator import VictorOrchestrator
from orchestrator.agent import BaseAgent, AgentStatus


class TestAgent(BaseAgent):
    """Test agent implementation."""
    
    def __init__(self, agent_id: str = "test_agent"):
        super().__init__(agent_id)
        self.initialized = False
        self.cleaned_up = False
        self.tasks_executed = []
    
    async def initialize(self):
        self.initialized = True
    
    async def execute_task(self, task_spec):
        self.tasks_executed.append(task_spec)
        return {"status": "success", "task": task_spec}
    
    async def cleanup(self):
        self.cleaned_up = True


@pytest.mark.asyncio
async def test_agent_creation():
    """Test agent creation."""
    agent = TestAgent()
    assert agent.agent_id == "test_agent"
    assert agent.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_agent_registration():
    """Test agent registration with orchestrator."""
    orchestrator = VictorOrchestrator()
    await orchestrator.initialize()
    
    agent = TestAgent()
    await orchestrator.register_agent(agent)
    
    assert agent.agent_id in orchestrator.agents
    assert len(orchestrator.agents) == 1
    assert agent.orchestrator is orchestrator
    
    await orchestrator.shutdown()


@pytest.mark.asyncio
async def test_agent_lifecycle():
    """Test agent lifecycle."""
    agent = TestAgent()
    
    # Start agent
    task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.1)  # Let it initialize
    
    assert agent.initialized
    assert agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]
    
    # Stop agent
    await agent.stop()
    await task
    
    assert agent.cleaned_up
    assert agent.status == AgentStatus.STOPPED


@pytest.mark.asyncio
async def test_agent_task_execution():
    """Test agent task execution."""
    agent = TestAgent()
    
    # Submit task
    task_spec = {"type": "test", "data": "test_data"}
    await agent.submit_task(task_spec)
    
    # Start agent and let it process
    run_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.2)
    
    # Stop agent
    await agent.stop()
    await run_task
    
    # Verify task was executed
    assert len(agent.tasks_executed) == 1
    assert agent.tasks_executed[0] == task_spec
    assert agent.metrics["tasks_completed"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

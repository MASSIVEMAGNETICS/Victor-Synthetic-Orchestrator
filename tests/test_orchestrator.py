"""
Tests for Victor Orchestrator core functionality.
"""

import pytest
import asyncio
from orchestrator import VictorOrchestrator
from orchestrator.core import OrchestratorState


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = VictorOrchestrator()
    assert orchestrator.state == OrchestratorState.INITIALIZING
    
    await orchestrator.initialize()
    assert orchestrator.state == OrchestratorState.ACTIVE
    
    await orchestrator.shutdown()
    assert orchestrator.state == OrchestratorState.STOPPED


@pytest.mark.asyncio
async def test_orchestrator_status():
    """Test orchestrator status retrieval."""
    orchestrator = VictorOrchestrator()
    await orchestrator.initialize()
    
    status = orchestrator.get_status()
    assert "state" in status
    assert "metrics" in status
    assert status["self_aware"] is True
    assert status["registered_agents"] == 0
    
    await orchestrator.shutdown()


@pytest.mark.asyncio
async def test_module_loading():
    """Test ecosystem module loading."""
    orchestrator = VictorOrchestrator()
    await orchestrator.initialize()
    
    # Check that modules were loaded
    module_count = orchestrator.registry.get_module_count()
    assert module_count > 0
    
    # Verify specific modules
    modules = orchestrator.registry.list_modules()
    module_ids = [m["id"] for m in modules]
    
    assert "victor_intelligence_hub" in module_ids
    assert "brain_ai" in module_ids
    assert "project_fol" in module_ids
    
    await orchestrator.shutdown()


@pytest.mark.asyncio
async def test_metrics_tracking():
    """Test metrics are tracked correctly."""
    orchestrator = VictorOrchestrator()
    await orchestrator.initialize()
    
    # Initial metrics
    assert orchestrator.metrics["total_tasks_processed"] == 0
    
    # Process a task
    task = {
        "name": "test_task",
        "type": "test",
        "agents": []
    }
    
    await orchestrator.orchestrate_task(task)
    
    # Check metrics updated
    assert orchestrator.metrics["total_tasks_processed"] == 1
    
    await orchestrator.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

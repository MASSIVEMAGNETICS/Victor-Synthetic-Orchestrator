"""
Tests for module registry.
"""

import pytest
from orchestrator.registry import ModuleRegistry


def test_registry_initialization():
    """Test registry initialization."""
    registry = ModuleRegistry()
    assert len(registry.modules) == 0
    assert len(registry.module_specs) > 0


@pytest.mark.asyncio
async def test_module_registration():
    """Test module registration."""
    registry = ModuleRegistry()
    
    await registry.register_module("victor_intelligence_hub")
    
    assert "victor_intelligence_hub" in registry.modules
    assert registry.get_module_count() == 1


@pytest.mark.asyncio
async def test_get_module():
    """Test getting module information."""
    registry = ModuleRegistry()
    
    await registry.register_module("brain_ai")
    
    module = registry.get_module("brain_ai")
    assert module is not None
    assert module["id"] == "brain_ai"
    assert "capabilities" in module


@pytest.mark.asyncio
async def test_modules_by_capability():
    """Test finding modules by capability."""
    registry = ModuleRegistry()
    
    await registry.register_module("sunokiller")
    await registry.register_module("brain_ai")
    
    audio_modules = registry.get_modules_by_capability("audio_generation")
    assert len(audio_modules) == 1
    assert audio_modules[0]["id"] == "sunokiller"
    
    neural_modules = registry.get_modules_by_capability("neural_simulation")
    assert len(neural_modules) == 1
    assert neural_modules[0]["id"] == "brain_ai"


@pytest.mark.asyncio
async def test_list_modules():
    """Test listing all modules."""
    registry = ModuleRegistry()
    
    await registry.register_module("project_fol")
    await registry.register_module("nexusforge")
    
    modules = registry.list_modules()
    assert len(modules) == 2
    
    module_ids = [m["id"] for m in modules]
    assert "project_fol" in module_ids
    assert "nexusforge" in module_ids


@pytest.mark.asyncio
async def test_unregister_module():
    """Test module unregistration."""
    registry = ModuleRegistry()
    
    await registry.register_module("tooki")
    assert registry.get_module_count() == 1
    
    registry.unregister_module("tooki")
    assert registry.get_module_count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

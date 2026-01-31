"""
Module registry for managing ecosystem components.
"""

import logging
from typing import Dict, List, Any, Optional


class ModuleRegistry:
    """
    Registry for MASSIVEMAGNETICS ecosystem modules.
    
    Manages the discovery, registration, and lifecycle of all
    AI modules in the ecosystem.
    """
    
    def __init__(self):
        """Initialize the module registry."""
        self.logger = logging.getLogger(__name__)
        self.modules: Dict[str, Dict[str, Any]] = {}
        
        # Module metadata
        self.module_specs = {
            "victor_intelligence_hub": {
                "name": "Victor Synthetic Super Intelligence Hub",
                "description": "Central orchestration and AGI framework",
                "capabilities": ["orchestration", "intelligence", "coordination"]
            },
            "brain_ai": {
                "name": "Brain AI",
                "description": "Digital brain simulation with recursive hierarchical mapping",
                "capabilities": ["neural_simulation", "cognitive_modeling", "brain_emulation"]
            },
            "project_fol": {
                "name": "Project FOL (Flower of Life)",
                "description": "37-node geometric AI system",
                "capabilities": ["distributed_inference", "geometric_intelligence", "multi_node"]
            },
            "sunokiller": {
                "name": "SUNOKILLER",
                "description": "Neural audio synthesis platform",
                "capabilities": ["audio_generation", "music_synthesis", "vocal_synthesis"]
            },
            "nexusforge": {
                "name": "NexusForge 2.0",
                "description": "Fractal agent orchestration",
                "capabilities": ["fractal_agents", "agent_evolution", "collective_intelligence"]
            },
            "bando_fi_ai": {
                "name": "Bando-Fi-AI",
                "description": "Creative and generative AI engine",
                "capabilities": ["content_generation", "creative_ai", "generative_models"]
            },
            "game_engine": {
                "name": "Next-Gen Game Engine",
                "description": "High-performance TypeScript game engine with ECS",
                "capabilities": ["game_development", "ecs_architecture", "physics", "rendering"]
            },
            "tooki": {
                "name": "Tooki Research Lab",
                "description": "Research archive and experimental implementations",
                "capabilities": ["research", "experimentation", "ml_reference", "autograd"]
            },
            "ray_compute": {
                "name": "Ray-Ray",
                "description": "Distributed AI compute engine",
                "capabilities": ["distributed_computing", "scalable_ml", "parallel_processing"]
            }
        }
    
    async def register_module(self, module_id: str, module_instance: Optional[Any] = None):
        """
        Register a module with the registry.
        
        Args:
            module_id: Unique module identifier
            module_instance: Optional module instance
        """
        if module_id not in self.module_specs:
            raise ValueError(f"Unknown module: {module_id}")
        
        spec = self.module_specs[module_id]
        
        self.modules[module_id] = {
            "id": module_id,
            "name": spec["name"],
            "description": spec["description"],
            "capabilities": spec["capabilities"],
            "instance": module_instance,
            "status": "registered"
        }
        
        self.logger.info(f"Registered module: {spec['name']}")
    
    def get_module(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Get module information.
        
        Args:
            module_id: Module identifier
            
        Returns:
            Module information dictionary
        """
        return self.modules.get(module_id)
    
    def get_modules_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Get all modules with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of modules with the capability
        """
        return [
            module for module in self.modules.values()
            if capability in module["capabilities"]
        ]
    
    def list_modules(self) -> List[Dict[str, Any]]:
        """
        List all registered modules.
        
        Returns:
            List of all modules
        """
        return list(self.modules.values())
    
    def get_module_count(self) -> int:
        """
        Get the count of registered modules.
        
        Returns:
            Number of registered modules
        """
        return len(self.modules)
    
    def unregister_module(self, module_id: str):
        """
        Unregister a module.
        
        Args:
            module_id: Module identifier
        """
        if module_id in self.modules:
            del self.modules[module_id]
            self.logger.info(f"Unregistered module: {module_id}")

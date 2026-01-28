"""
Configuration management for Victor Orchestrator.
"""

import os
import json
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the orchestrator."""
    
    DEFAULT_CONFIG = {
        "orchestrator": {
            "log_level": "INFO",
            "monitoring_interval": 10,
            "max_message_history": 1000,
            "self_aware": True
        },
        "modules": {
            "victor_intelligence_hub": {"enabled": True},
            "brain_ai": {"enabled": True},
            "project_fol": {"enabled": True, "node_count": 37},
            "sunokiller": {"enabled": True},
            "nexusforge": {"enabled": True},
            "bando_fi_ai": {"enabled": True},
            "game_engine": {"enabled": True},
            "tooki": {"enabled": True},
            "ray_compute": {"enabled": True}
        },
        "agents": {
            "max_agents": 100,
            "task_timeout": 300
        },
        "api": {
            "host": "0.0.0.0",
            "port": 8080,
            "cors_enabled": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file (JSON)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
    
    def load_from_file(self, path: str):
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            user_config = json.load(f)
            self._merge_config(user_config)
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """Merge user configuration with defaults."""
        def merge_dict(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self.config, user_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Dot-separated key path (e.g., "orchestrator.log_level")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config.copy()
    
    def save_to_file(self, path: str):
        """Save configuration to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.config, f, indent=2)

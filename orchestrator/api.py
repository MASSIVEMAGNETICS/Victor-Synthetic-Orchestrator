"""
REST API interface for Victor Orchestrator.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .core import VictorOrchestrator
from .config import Config


class TaskRequest(BaseModel):
    """Task request model."""
    name: str
    type: str
    parameters: Dict[str, Any] = {}
    agents: list = []


class VictorAPI:
    """
    REST API for Victor Orchestrator.
    
    Provides HTTP endpoints for orchestrator control and interaction.
    """
    
    def __init__(self, orchestrator: VictorOrchestrator, config: Config):
        """
        Initialize the API.
        
        Args:
            orchestrator: Victor orchestrator instance
            config: Configuration object
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for API functionality. Install with: pip install fastapi uvicorn")
        
        self.orchestrator = orchestrator
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Victor Synthetic Orchestrator API",
            description="Unified AGI framework orchestrating the MASSIVEMAGNETICS AI ecosystem",
            version="1.0.0"
        )
        
        # Configure CORS
        if config.get("api.cors_enabled", True):
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "name": "Victor Synthetic Orchestrator",
                "version": "1.0.0",
                "status": "active"
            }
        
        @self.app.get("/status")
        async def get_status():
            """Get orchestrator status."""
            return self.orchestrator.get_status()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            health = self.orchestrator.monitor.get_health_status()
            return health
        
        @self.app.get("/modules")
        async def list_modules():
            """List all registered modules."""
            modules = self.orchestrator.registry.list_modules()
            return {"modules": modules}
        
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agents."""
            agents = [
                agent.get_status() 
                for agent in self.orchestrator.agents.values()
            ]
            return {"agents": agents}
        
        @self.app.get("/agents/{agent_id}")
        async def get_agent(agent_id: str):
            """Get specific agent status."""
            if agent_id not in self.orchestrator.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            agent = self.orchestrator.agents[agent_id]
            return agent.get_status()
        
        @self.app.post("/tasks")
        async def submit_task(task: TaskRequest):
            """Submit a task for orchestration."""
            try:
                task_spec = {
                    "name": task.name,
                    "type": task.type,
                    "parameters": task.parameters,
                    "agents": task.agents,
                    "timestamp": datetime.now().isoformat()
                }
                
                result = await self.orchestrator.orchestrate_task(task_spec)
                
                return {
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get orchestrator metrics."""
            return {
                "metrics": self.orchestrator.metrics,
                "timestamp": datetime.now().isoformat()
            }
    
    async def start(self):
        """Start the API server."""
        try:
            import uvicorn
        except ImportError:
            raise ImportError("uvicorn is required. Install with: pip install uvicorn")
        
        host = self.config.get("api.host", "0.0.0.0")
        port = self.config.get("api.port", 8080)
        
        self.logger.info(f"Starting API server on {host}:{port}")
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level=self.config.get("orchestrator.log_level", "info").lower()
        )
        server = uvicorn.Server(config)
        await server.serve()

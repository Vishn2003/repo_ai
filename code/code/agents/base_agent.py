import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
    
    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Run the agent's main logic"""
        pass

    def log(self, level: str, message: str):
        """Unified agent-level logging"""
        getattr(self.logger, level.lower())(f"[{self.name}] {message}")

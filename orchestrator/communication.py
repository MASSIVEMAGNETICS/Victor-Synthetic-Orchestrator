"""
Inter-agent communication system using message bus pattern.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from datetime import datetime


class MessageBus:
    """
    Message bus for inter-agent communication.
    
    Enables publish-subscribe messaging between agents and the orchestrator.
    """
    
    def __init__(self):
        """Initialize the message bus."""
        self.logger = logging.getLogger(__name__)
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self._running = False
    
    async def initialize(self):
        """Initialize the message bus."""
        self._running = True
        self.logger.info("Message bus initialized")
    
    async def publish(self, topic: str, message: Any):
        """
        Publish a message to a topic.
        
        Args:
            topic: Message topic
            message: Message payload
        """
        if not self._running:
            return
        
        # Record message
        msg_record = {
            "topic": topic,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.message_history.append(msg_record)
        
        # Trim history
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Notify subscribers
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    self.logger.error(f"Subscriber error on topic {topic}: {e}")
        
        self.logger.debug(f"Published message to topic: {topic}")
    
    def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to invoke on message
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        self.subscribers[topic].append(callback)
        self.logger.debug(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            callback: Callback function to remove
        """
        if topic in self.subscribers and callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            self.logger.debug(f"Unsubscribed from topic: {topic}")
    
    async def shutdown(self):
        """Shutdown the message bus."""
        self._running = False
        self.subscribers.clear()
        self.logger.info("Message bus shutdown")
    
    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.message_history)

"""
Tests for message bus communication.
"""

import pytest
import asyncio
from orchestrator.communication import MessageBus


@pytest.mark.asyncio
async def test_message_bus_initialization():
    """Test message bus initialization."""
    bus = MessageBus()
    await bus.initialize()
    
    assert bus._running is True
    
    await bus.shutdown()
    assert bus._running is False


@pytest.mark.asyncio
async def test_publish_subscribe():
    """Test publish-subscribe functionality."""
    bus = MessageBus()
    await bus.initialize()
    
    received_messages = []
    
    def callback(message):
        received_messages.append(message)
    
    # Subscribe
    bus.subscribe("test.topic", callback)
    
    # Publish
    await bus.publish("test.topic", {"data": "test"})
    
    # Small delay for async processing
    await asyncio.sleep(0.1)
    
    assert len(received_messages) == 1
    assert received_messages[0]["data"] == "test"
    
    await bus.shutdown()


@pytest.mark.asyncio
async def test_multiple_subscribers():
    """Test multiple subscribers to same topic."""
    bus = MessageBus()
    await bus.initialize()
    
    received1 = []
    received2 = []
    
    def callback1(msg):
        received1.append(msg)
    
    def callback2(msg):
        received2.append(msg)
    
    bus.subscribe("topic", callback1)
    bus.subscribe("topic", callback2)
    
    await bus.publish("topic", "message")
    await asyncio.sleep(0.1)
    
    assert len(received1) == 1
    assert len(received2) == 1
    
    await bus.shutdown()


@pytest.mark.asyncio
async def test_unsubscribe():
    """Test unsubscribing from topic."""
    bus = MessageBus()
    await bus.initialize()
    
    received = []
    
    def callback(msg):
        received.append(msg)
    
    bus.subscribe("topic", callback)
    await bus.publish("topic", "msg1")
    await asyncio.sleep(0.1)
    
    bus.unsubscribe("topic", callback)
    await bus.publish("topic", "msg2")
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    assert received[0] == "msg1"
    
    await bus.shutdown()


@pytest.mark.asyncio
async def test_message_history():
    """Test message history tracking."""
    bus = MessageBus()
    await bus.initialize()
    
    await bus.publish("topic1", "msg1")
    await bus.publish("topic2", "msg2")
    await bus.publish("topic1", "msg3")
    
    assert bus.get_message_count() == 3
    assert len(bus.message_history) == 3
    
    await bus.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

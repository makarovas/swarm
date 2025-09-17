"""Система коммуникации между агентами"""

from .message_bus import MessageBus, Message, MessagePriority, MessageHandler

__all__ = [
    "MessageBus",
    "Message", 
    "MessagePriority",
    "MessageHandler"
]

"""
Система агентного роевого программирования
"""

from .core.agent import Agent, Task, TaskResult, AgentState
from .core.swarm_manager import SwarmManager, SwarmConfig, SwarmState
from .communication.message_bus import MessageBus, Message, MessagePriority
from .tasks.task_distributor import TaskDistributor, DistributionStrategy, TaskStatus
from .intelligence.collective_intelligence import (
    CollectiveIntelligence, 
    VotingMethod, 
    Vote, 
    CollectiveDecision
)
from .agents.ai_agent_base import AIAgentBase, AIModelConfig
from .agents.openai_agent import OpenAIAgent
from .agents.anthropic_agent import AnthropicAgent
from .agents.local_llm_agent import LocalLLMAgent
from .agents.multi_ai_agent import MultiAIAgent, MultiAIConfig

__version__ = "1.0.0"
__author__ = "Swarm Development Team"
__description__ = "Система агентного роевого программирования"

__all__ = [
    # Core classes
    "Agent",
    "Task",
    "TaskResult", 
    "AgentState",
    "SwarmManager",
    "SwarmConfig",
    "SwarmState",
    
    # Communication
    "MessageBus",
    "Message",
    "MessagePriority",
    
    # Task management
    "TaskDistributor",
    "DistributionStrategy",
    "TaskStatus",
    
    # Collective intelligence
    "CollectiveIntelligence",
    "VotingMethod",
    "Vote",
    "CollectiveDecision",
    
    # AI Agents
    "AIAgentBase",
    "AIModelConfig",
    "OpenAIAgent",
    "AnthropicAgent", 
    "LocalLLMAgent",
    "MultiAIAgent",
    "MultiAIConfig"
]

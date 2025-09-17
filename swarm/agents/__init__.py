"""AI-агенты для интеграции с различными моделями"""

from .ai_agent_base import AIAgentBase
from .openai_agent import OpenAIAgent
from .anthropic_agent import AnthropicAgent
from .local_llm_agent import LocalLLMAgent
from .multi_ai_agent import MultiAIAgent

__all__ = [
    "AIAgentBase",
    "OpenAIAgent", 
    "AnthropicAgent",
    "LocalLLMAgent",
    "MultiAIAgent"
]

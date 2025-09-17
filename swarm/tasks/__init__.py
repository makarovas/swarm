"""Система управления задачами"""

from .task_distributor import (
    TaskDistributor, 
    TaskStatus, 
    DistributionStrategy, 
    TaskAssignment, 
    AgentPerformance
)

__all__ = [
    "TaskDistributor",
    "TaskStatus",
    "DistributionStrategy", 
    "TaskAssignment",
    "AgentPerformance"
]

"""
Система распределения задач между агентами
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import heapq
import uuid

from ..core.agent import Agent, Task, TaskResult, AgentState


class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DistributionStrategy(Enum):
    """Стратегии распределения задач"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    CAPABILITY_BASED = "capability_based"
    PRIORITY_BASED = "priority_based"
    PERFORMANCE_BASED = "performance_based"


@dataclass
class TaskAssignment:
    """Назначение задачи агенту"""
    task: Task
    agent_id: str
    assigned_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.ASSIGNED
    attempts: int = 0
    max_attempts: int = 3


@dataclass
class AgentPerformance:
    """Метрики производительности агента"""
    agent_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    last_activity: float = field(default_factory=time.time)
    current_load: int = 0
    reliability_score: float = 1.0


class TaskDistributor:
    """
    Распределитель задач между агентами в рое
    """
    
    def __init__(self, strategy: DistributionStrategy = DistributionStrategy.LOAD_BALANCED):
        self.strategy = strategy
        self.task_queue: List[Task] = []  # Приоритетная очередь
        self.assignments: Dict[str, TaskAssignment] = {}
        self.agent_performance: Dict[str, AgentPerformance] = {}
        self.agents: Dict[str, Agent] = {}
        self.round_robin_index = 0
        self.logger = logging.getLogger("TaskDistributor")
        
        # Коллбэки
        self.on_task_assigned: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None
        
    def register_agent(self, agent: Agent):
        """Зарегистрировать агента"""
        self.agents[agent.id] = agent
        self.agent_performance[agent.id] = AgentPerformance(agent_id=agent.id)
        self.logger.info(f"Агент {agent.id} зарегистрирован в распределителе")
        
    def unregister_agent(self, agent_id: str):
        """Отменить регистрацию агента"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_performance[agent_id]
            self.logger.info(f"Агент {agent_id} удален из распределителя")
            
    def add_task(self, task: Task):
        """Добавить задачу в очередь"""
        # Добавляем в приоритетную очередь (отрицательный приоритет для max-heap)
        heapq.heappush(self.task_queue, (-task.priority, time.time(), task))
        self.logger.info(f"Задача {task.id} добавлена в очередь (приоритет: {task.priority})")
        
    async def distribute_tasks(self) -> List[TaskAssignment]:
        """Распределить задачи между доступными агентами"""
        assignments = []
        
        while self.task_queue and self._has_available_agents():
            # Извлекаем задачу с наивысшим приоритетом
            _, _, task = heapq.heappop(self.task_queue)
            
            # Находим подходящего агента
            agent_id = await self._find_best_agent(task)
            
            if agent_id:
                assignment = TaskAssignment(task=task, agent_id=agent_id)
                self.assignments[task.id] = assignment
                assignments.append(assignment)
                
                # Обновляем метрики агента
                perf = self.agent_performance[agent_id]
                perf.current_load += 1
                perf.last_activity = time.time()
                
                self.logger.info(f"Задача {task.id} назначена агенту {agent_id}")
                
                if self.on_task_assigned:
                    await self.on_task_assigned(assignment)
            else:
                # Возвращаем задачу в очередь
                heapq.heappush(self.task_queue, (-task.priority, time.time(), task))
                break
                
        return assignments
        
    def _has_available_agents(self) -> bool:
        """Проверить наличие доступных агентов"""
        for agent in self.agents.values():
            if agent.can_handle_task(Task(id="dummy", content="")) and agent.state == AgentState.IDLE:
                return True
        return False
        
    async def _find_best_agent(self, task: Task) -> Optional[str]:
        """Найти лучшего агента для задачи"""
        if self.strategy == DistributionStrategy.ROUND_ROBIN:
            return self._find_agent_round_robin(task)
        elif self.strategy == DistributionStrategy.LOAD_BALANCED:
            return self._find_agent_load_balanced(task)
        elif self.strategy == DistributionStrategy.CAPABILITY_BASED:
            return self._find_agent_capability_based(task)
        elif self.strategy == DistributionStrategy.PRIORITY_BASED:
            return self._find_agent_priority_based(task)
        elif self.strategy == DistributionStrategy.PERFORMANCE_BASED:
            return self._find_agent_performance_based(task)
        else:
            return self._find_agent_load_balanced(task)
            
    def _find_agent_round_robin(self, task: Task) -> Optional[str]:
        """Round Robin стратегия"""
        agent_ids = list(self.agents.keys())
        if not agent_ids:
            return None
            
        attempts = 0
        while attempts < len(agent_ids):
            agent_id = agent_ids[self.round_robin_index % len(agent_ids)]
            self.round_robin_index += 1
            
            agent = self.agents[agent_id]
            if agent.can_handle_task(task) and agent.state == AgentState.IDLE:
                return agent_id
                
            attempts += 1
            
        return None
        
    def _find_agent_load_balanced(self, task: Task) -> Optional[str]:
        """Балансировка нагрузки"""
        available_agents = []
        
        for agent_id, agent in self.agents.items():
            if agent.can_handle_task(task) and agent.state == AgentState.IDLE:
                load = self.agent_performance[agent_id].current_load
                available_agents.append((load, agent_id))
                
        if available_agents:
            # Сортируем по нагрузке (по возрастанию)
            available_agents.sort()
            return available_agents[0][1]
            
        return None
        
    def _find_agent_capability_based(self, task: Task) -> Optional[str]:
        """Выбор на основе способностей"""
        best_agent = None
        best_score = 0
        
        for agent_id, agent in self.agents.items():
            if agent.can_handle_task(task) and agent.state == AgentState.IDLE:
                # Рассчитываем счет соответствия способностей
                score = self._calculate_capability_score(agent, task)
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
                    
        return best_agent
        
    def _find_agent_priority_based(self, task: Task) -> Optional[str]:
        """Выбор на основе приоритета задачи"""
        # Для высокоприоритетных задач выбираем лучших агентов
        if task.priority >= 8:
            return self._find_agent_performance_based(task)
        else:
            return self._find_agent_load_balanced(task)
            
    def _find_agent_performance_based(self, task: Task) -> Optional[str]:
        """Выбор на основе производительности"""
        best_agent = None
        best_score = 0
        
        for agent_id, agent in self.agents.items():
            if agent.can_handle_task(task) and agent.state == AgentState.IDLE:
                perf = self.agent_performance[agent_id]
                
                # Составной счет: надежность + скорость
                reliability = perf.reliability_score
                speed_score = 1.0 / (perf.average_execution_time + 1.0)
                load_penalty = 1.0 / (perf.current_load + 1.0)
                
                score = reliability * speed_score * load_penalty
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
                    
        return best_agent
        
    def _calculate_capability_score(self, agent: Agent, task: Task) -> float:
        """Рассчитать счет соответствия способностей"""
        if not task.requirements:
            return 1.0
            
        total_confidence = 0
        matched_requirements = 0
        
        for requirement in task.requirements:
            if requirement in agent.capabilities:
                total_confidence += agent.capabilities[requirement].confidence
                matched_requirements += 1
                
        if matched_requirements == 0:
            return 0.0
            
        # Средняя уверенность по соответствующим требованиям
        avg_confidence = total_confidence / matched_requirements
        
        # Бонус за покрытие всех требований
        coverage_bonus = matched_requirements / len(task.requirements)
        
        return avg_confidence * coverage_bonus
        
    async def handle_task_result(self, task_result: TaskResult):
        """Обработать результат выполнения задачи"""
        if task_result.task_id not in self.assignments:
            self.logger.warning(f"Результат для неизвестной задачи: {task_result.task_id}")
            return
            
        assignment = self.assignments[task_result.task_id]
        assignment.completed_at = time.time()
        
        # Обновляем метрики агента
        perf = self.agent_performance[task_result.agent_id]
        perf.total_tasks += 1
        perf.current_load = max(0, perf.current_load - 1)
        perf.last_activity = time.time()
        
        if task_result.success:
            assignment.status = TaskStatus.COMPLETED
            perf.successful_tasks += 1
            
            # Обновляем среднее время выполнения
            if perf.total_tasks > 1:
                perf.average_execution_time = (
                    (perf.average_execution_time * (perf.total_tasks - 1) + task_result.execution_time) /
                    perf.total_tasks
                )
            else:
                perf.average_execution_time = task_result.execution_time
                
            self.logger.info(f"Задача {task_result.task_id} успешно выполнена агентом {task_result.agent_id}")
            
            if self.on_task_completed:
                await self.on_task_completed(task_result)
        else:
            assignment.status = TaskStatus.FAILED
            assignment.attempts += 1
            perf.failed_tasks += 1
            
            self.logger.warning(f"Задача {task_result.task_id} провалена агентом {task_result.agent_id}")
            
            # Повторная попытка если не превышен лимит
            if assignment.attempts < assignment.max_attempts:
                self.logger.info(f"Повторная попытка для задачи {task_result.task_id} ({assignment.attempts}/{assignment.max_attempts})")
                self.add_task(assignment.task)
                assignment.status = TaskStatus.PENDING
            
            if self.on_task_failed:
                await self.on_task_failed(task_result)
                
        # Обновляем счет надежности
        perf.reliability_score = perf.successful_tasks / perf.total_tasks if perf.total_tasks > 0 else 1.0
        
    def get_queue_status(self) -> Dict[str, Any]:
        """Получить статус очереди задач"""
        return {
            "pending_tasks": len(self.task_queue),
            "assigned_tasks": len([a for a in self.assignments.values() if a.status == TaskStatus.ASSIGNED]),
            "in_progress_tasks": len([a for a in self.assignments.values() if a.status == TaskStatus.IN_PROGRESS]),
            "completed_tasks": len([a for a in self.assignments.values() if a.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([a for a in self.assignments.values() if a.status == TaskStatus.FAILED]),
            "total_assignments": len(self.assignments)
        }
        
    def get_agent_stats(self) -> Dict[str, AgentPerformance]:
        """Получить статистику агентов"""
        return self.agent_performance.copy()
        
    def cancel_task(self, task_id: str) -> bool:
        """Отменить задачу"""
        # Поиск в очереди
        for i, (priority, timestamp, task) in enumerate(self.task_queue):
            if task.id == task_id:
                del self.task_queue[i]
                heapq.heapify(self.task_queue)
                self.logger.info(f"Задача {task_id} отменена из очереди")
                return True
                
        # Поиск в назначениях
        if task_id in self.assignments:
            assignment = self.assignments[task_id]
            assignment.status = TaskStatus.CANCELLED
            
            # Уменьшаем нагрузку агента
            perf = self.agent_performance[assignment.agent_id]
            perf.current_load = max(0, perf.current_load - 1)
            
            self.logger.info(f"Задача {task_id} отменена")
            return True
            
        return False

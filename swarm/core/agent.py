"""
Базовый класс агента для системы роевого программирования
"""

import asyncio
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


class AgentState(Enum):
    """Состояния агента"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentCapability:
    """Описание способности агента"""
    name: str
    description: str
    confidence: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Задача для выполнения агентом"""
    id: str
    content: str
    priority: int = 1
    requirements: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None


@dataclass
class TaskResult:
    """Результат выполнения задачи"""
    task_id: str
    agent_id: str
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    confidence: float = 1.0


class Agent(ABC):
    """
    Базовый класс агента в системе роевого программирования
    """
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        max_concurrent_tasks: int = 1
    ):
        self.id = agent_id or str(uuid.uuid4())
        self.name = name or f"Agent_{self.id[:8]}"
        self.state = AgentState.IDLE
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[TaskResult] = []
        self.capabilities: Dict[str, AgentCapability] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(f"Agent.{self.name}")
        
        # Инициализация базовых способностей
        if capabilities:
            for cap_name in capabilities:
                self.add_capability(cap_name, f"Способность {cap_name}")
                
        # Обработчики сообщений
        self._setup_message_handlers()
        
    def add_capability(self, name: str, description: str, confidence: float = 1.0, **params):
        """Добавить способность агента"""
        self.capabilities[name] = AgentCapability(
            name=name,
            description=description,
            confidence=confidence,
            parameters=params
        )
        self.logger.info(f"Добавлена способность: {name}")
        
    def can_handle_task(self, task: Task) -> bool:
        """Проверить, может ли агент выполнить задачу"""
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return False
            
        # Проверка требований задачи
        for requirement in task.requirements:
            if requirement not in self.capabilities:
                return False
                
        return True
        
    async def execute_task(self, task: Task) -> TaskResult:
        """Выполнить задачу"""
        if not self.can_handle_task(task):
            return TaskResult(
                task_id=task.id,
                agent_id=self.id,
                success=False,
                error_message="Агент не может выполнить эту задачу"
            )
            
        self.state = AgentState.WORKING
        self.current_tasks[task.id] = task
        self.logger.info(f"Начинаю выполнение задачи: {task.id}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Выполнение задачи с таймаутом
            if task.timeout:
                result = await asyncio.wait_for(
                    self._execute_task_impl(task),
                    timeout=task.timeout
                )
            else:
                result = await self._execute_task_impl(task)
                
            execution_time = asyncio.get_event_loop().time() - start_time
            
            task_result = TaskResult(
                task_id=task.id,
                agent_id=self.id,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
            self.logger.info(f"Задача {task.id} выполнена успешно за {execution_time:.2f}с")
            
        except asyncio.TimeoutError:
            task_result = TaskResult(
                task_id=task.id,
                agent_id=self.id,
                success=False,
                error_message="Превышено время выполнения задачи"
            )
            self.logger.error(f"Таймаут при выполнении задачи {task.id}")
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            task_result = TaskResult(
                task_id=task.id,
                agent_id=self.id,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
            self.logger.error(f"Ошибка при выполнении задачи {task.id}: {e}")
            
        finally:
            # Очистка
            if task.id in self.current_tasks:
                del self.current_tasks[task.id]
            self.completed_tasks.append(task_result)
            self.state = AgentState.IDLE
            
        return task_result
        
    @abstractmethod
    async def _execute_task_impl(self, task: Task) -> Any:
        """Реализация выполнения задачи (должна быть переопределена в подклассах)"""
        pass
        
    def _setup_message_handlers(self):
        """Настройка обработчиков сообщений"""
        self.message_handlers.update({
            "ping": self._handle_ping,
            "status_request": self._handle_status_request,
            "capability_request": self._handle_capability_request,
            "shutdown": self._handle_shutdown
        })
        
    async def handle_message(self, message_type: str, content: Any, sender_id: str) -> Any:
        """Обработать входящее сообщение"""
        if message_type in self.message_handlers:
            return await self.message_handlers[message_type](content, sender_id)
        else:
            self.logger.warning(f"Неизвестный тип сообщения: {message_type}")
            return None
            
    async def _handle_ping(self, content: Any, sender_id: str) -> Dict[str, Any]:
        """Обработка ping сообщений"""
        return {
            "agent_id": self.id,
            "name": self.name,
            "state": self.state.value,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    async def _handle_status_request(self, content: Any, sender_id: str) -> Dict[str, Any]:
        """Обработка запросов статуса"""
        return {
            "agent_id": self.id,
            "name": self.name,
            "state": self.state.value,
            "current_tasks": len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
            "capabilities": list(self.capabilities.keys())
        }
        
    async def _handle_capability_request(self, content: Any, sender_id: str) -> Dict[str, AgentCapability]:
        """Обработка запросов способностей"""
        return self.capabilities
        
    async def _handle_shutdown(self, content: Any, sender_id: str) -> None:
        """Обработка команды завершения работы"""
        self.state = AgentState.SHUTDOWN
        self.logger.info("Получена команда завершения работы")
        
    def get_metrics(self) -> Dict[str, Any]:
        """Получить метрики агента"""
        total_tasks = len(self.completed_tasks)
        successful_tasks = sum(1 for task in self.completed_tasks if task.success)
        
        avg_execution_time = 0
        if total_tasks > 0:
            avg_execution_time = sum(task.execution_time for task in self.completed_tasks) / total_tasks
            
        return {
            "agent_id": self.id,
            "name": self.name,
            "state": self.state.value,
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "average_execution_time": avg_execution_time,
            "current_load": len(self.current_tasks),
            "capabilities_count": len(self.capabilities)
        }

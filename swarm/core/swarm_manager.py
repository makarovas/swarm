"""
Менеджер роя для координации агентов
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

from .agent import Agent, Task, TaskResult, AgentState
from ..communication.message_bus import MessageBus, Message, MessagePriority
from ..tasks.task_distributor import TaskDistributor, DistributionStrategy, TaskAssignment


class SwarmState(Enum):
    """Состояния роя"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class SwarmConfig:
    """Конфигурация роя"""
    max_agents: int = 10
    task_distribution_strategy: DistributionStrategy = DistributionStrategy.LOAD_BALANCED
    message_queue_size: int = 1000
    health_check_interval: float = 30.0
    task_timeout: float = 300.0
    auto_scale: bool = False
    min_agents: int = 1
    max_concurrent_tasks_per_agent: int = 3


class SwarmManager:
    """
    Менеджер роя для координации агентов в системе роевого программирования
    """
    
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.state = SwarmState.INITIALIZING
        
        # Основные компоненты
        self.message_bus = MessageBus(max_queue_size=self.config.message_queue_size)
        self.task_distributor = TaskDistributor(strategy=self.config.task_distribution_strategy)
        
        # Управление агентами
        self.agents: Dict[str, Agent] = {}
        self.agent_tasks: Dict[str, List[str]] = {}  # agent_id -> task_ids
        
        # Мониторинг и статистика
        self.start_time: Optional[float] = None
        self.total_tasks_processed = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        
        # Фоновые задачи
        self.background_tasks: List[asyncio.Task] = []
        
        # Коллбэки
        self.on_agent_added: Optional[Callable] = None
        self.on_agent_removed: Optional[Callable] = None
        self.on_task_completed: Optional[Callable] = None
        self.on_swarm_error: Optional[Callable] = None
        
        self.logger = logging.getLogger("SwarmManager")
        
    async def start(self):
        """Запустить рой"""
        try:
            self.state = SwarmState.RUNNING
            self.start_time = time.time()
            
            # Запуск шины сообщений
            await self.message_bus.start()
            
            # Настройка обработчиков задач
            self.task_distributor.on_task_completed = self._handle_task_completed
            self.task_distributor.on_task_failed = self._handle_task_failed
            
            # Запуск фоновых задач
            self.background_tasks = [
                asyncio.create_task(self._health_check_loop()),
                asyncio.create_task(self._task_distribution_loop()),
                asyncio.create_task(self._message_processing_loop()),
            ]
            
            if self.config.auto_scale:
                self.background_tasks.append(
                    asyncio.create_task(self._auto_scaling_loop())
                )
            
            self.logger.info("Рой запущен")
            
        except Exception as e:
            self.state = SwarmState.ERROR
            self.logger.error(f"Ошибка запуска роя: {e}")
            if self.on_swarm_error:
                await self.on_swarm_error(e)
            raise
            
    async def stop(self):
        """Остановить рой"""
        self.state = SwarmState.STOPPING
        
        try:
            # Остановка фоновых задач
            for task in self.background_tasks:
                task.cancel()
            
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # Остановка всех агентов
            for agent in self.agents.values():
                await self._send_shutdown_message(agent.id)
            
            # Остановка шины сообщений
            await self.message_bus.stop()
            
            self.state = SwarmState.STOPPED
            self.logger.info("Рой остановлен")
            
        except Exception as e:
            self.state = SwarmState.ERROR
            self.logger.error(f"Ошибка остановки роя: {e}")
            raise
            
    async def add_agent(self, agent: Agent) -> bool:
        """Добавить агента в рой"""
        if len(self.agents) >= self.config.max_agents:
            self.logger.warning(f"Достигнут лимит агентов: {self.config.max_agents}")
            return False
            
        if agent.id in self.agents:
            self.logger.warning(f"Агент {agent.id} уже существует в рое")
            return False
            
        try:
            # Регистрация в компонентах
            self.message_bus.register_agent(agent.id)
            self.task_distributor.register_agent(agent)
            
            # Добавление в рой
            self.agents[agent.id] = agent
            self.agent_tasks[agent.id] = []
            
            self.logger.info(f"Агент {agent.id} добавлен в рой")
            
            if self.on_agent_added:
                await self.on_agent_added(agent)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления агента {agent.id}: {e}")
            return False
            
    async def remove_agent(self, agent_id: str) -> bool:
        """Удалить агента из роя"""
        if agent_id not in self.agents:
            self.logger.warning(f"Агент {agent_id} не найден в рое")
            return False
            
        try:
            agent = self.agents[agent_id]
            
            # Отправка команды завершения
            await self._send_shutdown_message(agent_id)
            
            # Отмена активных задач агента
            for task_id in self.agent_tasks[agent_id]:
                self.task_distributor.cancel_task(task_id)
                
            # Удаление из компонентов
            self.message_bus.unregister_agent(agent_id)
            self.task_distributor.unregister_agent(agent_id)
            
            # Удаление из роя
            del self.agents[agent_id]
            del self.agent_tasks[agent_id]
            
            self.logger.info(f"Агент {agent_id} удален из роя")
            
            if self.on_agent_removed:
                await self.on_agent_removed(agent)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления агента {agent_id}: {e}")
            return False
            
    async def execute_task(self, task: Task) -> TaskResult:
        """Выполнить задачу в рое"""
        if self.state != SwarmState.RUNNING:
            return TaskResult(
                task_id=task.id,
                agent_id="",
                success=False,
                error_message="Рой не запущен"
            )
            
        # Установка таймаута если не указан
        if task.timeout is None:
            task.timeout = self.config.task_timeout
            
        # Добавление в очередь
        self.task_distributor.add_task(task)
        
        # Ожидание результата
        return await self._wait_for_task_result(task.id)
        
    async def execute_tasks_batch(self, tasks: List[Task]) -> List[TaskResult]:
        """Выполнить пакет задач"""
        if self.state != SwarmState.RUNNING:
            return [TaskResult(
                task_id=task.id,
                agent_id="",
                success=False,
                error_message="Рой не запущен"
            ) for task in tasks]
            
        # Добавление всех задач в очередь
        for task in tasks:
            if task.timeout is None:
                task.timeout = self.config.task_timeout
            self.task_distributor.add_task(task)
            
        # Ожидание всех результатов
        results = []
        for task in tasks:
            result = await self._wait_for_task_result(task.id)
            results.append(result)
            
        return results
        
    async def _health_check_loop(self):
        """Цикл проверки здоровья агентов"""
        while self.state == SwarmState.RUNNING:
            try:
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в цикле проверки здоровья: {e}")
                await asyncio.sleep(5)
                
    async def _task_distribution_loop(self):
        """Цикл распределения задач"""
        while self.state == SwarmState.RUNNING:
            try:
                assignments = await self.task_distributor.distribute_tasks()
                
                for assignment in assignments:
                    await self._execute_assignment(assignment)
                    
                await asyncio.sleep(1)  # Частота распределения
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в цикле распределения задач: {e}")
                await asyncio.sleep(5)
                
    async def _execute_assignment(self, assignment: TaskAssignment):
        """Выполнить назначение задачи агенту"""
        try:
            agent = self.agents[assignment.agent_id]
            self.agent_tasks[assignment.agent_id].append(assignment.task.id)
            
            # Запуск задачи в фоне
            asyncio.create_task(
                self._run_agent_task(agent, assignment.task)
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения назначения: {e}")
            
    async def _run_agent_task(self, agent: Agent, task: Task):
        """Запустить задачу на агенте"""
        try:
            result = await agent.execute_task(task)
            await self.task_distributor.handle_task_result(result)
        except Exception as e:
            self.logger.error(f"Ошибка выполнения задачи {task.id} на агенте {agent.id}: {e}")
            
            # Создание результата с ошибкой
            error_result = TaskResult(
                task_id=task.id,
                agent_id=agent.id,
                success=False,
                error_message=str(e)
            )
            await self.task_distributor.handle_task_result(error_result)
            
    async def _message_processing_loop(self):
        """Цикл обработки сообщений"""
        while self.state == SwarmState.RUNNING:
            try:
                # Обработка сообщений для каждого агента
                for agent_id in list(self.agents.keys()):
                    message = await self.message_bus.receive_message(agent_id, timeout=0.1)
                    if message:
                        await self._process_agent_message(agent_id, message)
                        
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в цикле обработки сообщений: {e}")
                await asyncio.sleep(1)
                
    async def _process_agent_message(self, agent_id: str, message: Message):
        """Обработать сообщение для агента"""
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                await agent.handle_message(message.message_type, message.content, message.sender_id)
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения для агента {agent_id}: {e}")
            
    async def _auto_scaling_loop(self):
        """Цикл автоматического масштабирования"""
        while self.state == SwarmState.RUNNING:
            try:
                await asyncio.sleep(60)  # Проверка каждую минуту
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в автомасштабировании: {e}")
                await asyncio.sleep(60)
                
    async def _wait_for_task_result(self, task_id: str) -> TaskResult:
        """Ожидать результат выполнения задачи"""
        timeout = self.config.task_timeout + 10  # Дополнительное время
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Проверяем в истории выполненных задач
            assignment = self.task_distributor.assignments.get(task_id)
            if assignment and assignment.status.value in ["completed", "failed", "cancelled"]:
                # Ищем результат в агентах
                for agent in self.agents.values():
                    for result in agent.completed_tasks:
                        if result.task_id == task_id:
                            return result
                            
            await asyncio.sleep(0.5)
            
        # Таймаут
        return TaskResult(
            task_id=task_id,
            agent_id="",
            success=False,
            error_message="Таймаут ожидания результата задачи"
        )
        
    async def _send_shutdown_message(self, agent_id: str):
        """Отправить команду завершения агенту"""
        try:
            pass  # Упрощенная версия
        except Exception as e:
            self.logger.error(f"Ошибка отправки команды завершения агенту {agent_id}: {e}")
            
    async def _handle_task_completed(self, task_result: TaskResult):
        """Обработать завершение задачи"""
        self.total_tasks_processed += 1
        if task_result.success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1
            
        # Удаление из списка задач агента
        if task_result.agent_id in self.agent_tasks:
            task_list = self.agent_tasks[task_result.agent_id]
            if task_result.task_id in task_list:
                task_list.remove(task_result.task_id)
                
        if self.on_task_completed:
            await self.on_task_completed(task_result)
            
    async def _handle_task_failed(self, task_result: TaskResult):
        """Обработать провал задачи"""
        self.logger.warning(f"Задача {task_result.task_id} провалена: {task_result.error_message}")
        
    def get_swarm_status(self) -> Dict[str, Any]:
        """Получить статус роя"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "state": self.state.value,
            "uptime": uptime,
            "agents_count": len(self.agents),
            "total_tasks_processed": self.total_tasks_processed,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.successful_tasks / self.total_tasks_processed if self.total_tasks_processed > 0 else 0,
            "queue_status": self.task_distributor.get_queue_status(),
            "message_bus_stats": self.message_bus.get_stats(),
            "config": {
                "max_agents": self.config.max_agents,
                "strategy": self.config.task_distribution_strategy.value,
                "auto_scale": self.config.auto_scale
            }
        }
        
    def get_agent_list(self) -> List[Dict[str, Any]]:
        """Получить список агентов"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "state": agent.state.value,
                "capabilities": list(agent.capabilities.keys()),
                "current_tasks": len(self.agent_tasks.get(agent.id, [])),
                "metrics": agent.get_metrics()
            }
            for agent in self.agents.values()
        ]
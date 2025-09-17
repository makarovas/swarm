"""
Базовые тесты функциональности системы
"""

import pytest
import asyncio
from unittest.mock import AsyncMock

from swarm.core.agent import Agent, Task, TaskResult, AgentState
from swarm.core.swarm_manager import SwarmManager
from swarm.communication.message_bus import MessageBus, Message
from swarm.tasks.task_distributor import TaskDistributor


class MockAgent(Agent):
    """Мок-агент для тестирования"""
    
    def __init__(self, agent_id=None, name=None, should_succeed=True):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["test_capability"],
            max_concurrent_tasks=1
        )
        self.should_succeed = should_succeed
        
    async def _execute_task_impl(self, task: Task):
        """Простая реализация для тестов"""
        await asyncio.sleep(0.1)  # Симуляция работы
        
        if self.should_succeed:
            return {"status": "success", "task_id": task.id}
        else:
            raise ValueError("Тестовая ошибка")


class TestAgent:
    """Тесты базового функционала агента"""
    
    @pytest.fixture
    def agent(self):
        return MockAgent(name="TestAgent")
        
    @pytest.fixture
    def task(self):
        return Task(
            id="test_task",
            content={"data": "test"},
            requirements=["test_capability"]
        )
        
    def test_agent_creation(self, agent):
        """Тест создания агента"""
        assert agent.name == "TestAgent"
        assert agent.state == AgentState.IDLE
        assert "test_capability" in agent.capabilities
        
    def test_agent_can_handle_task(self, agent, task):
        """Тест проверки возможности выполнения задачи"""
        assert agent.can_handle_task(task) is True
        
        # Тест с неподходящими требованиями
        bad_task = Task(
            id="bad_task",
            content={},
            requirements=["unknown_capability"]
        )
        assert agent.can_handle_task(bad_task) is False
        
    @pytest.mark.asyncio
    async def test_agent_execute_task_success(self, agent, task):
        """Тест успешного выполнения задачи"""
        result = await agent.execute_task(task)
        
        assert result.success is True
        assert result.task_id == task.id
        assert result.agent_id == agent.id
        assert result.result["status"] == "success"
        
    @pytest.mark.asyncio
    async def test_agent_execute_task_failure(self, task):
        """Тест неуспешного выполнения задачи"""
        failing_agent = MockAgent(name="FailingAgent", should_succeed=False)
        result = await failing_agent.execute_task(task)
        
        assert result.success is False
        assert result.task_id == task.id
        assert result.error_message is not None
        
    def test_agent_metrics(self, agent):
        """Тест получения метрик агента"""
        metrics = agent.get_metrics()
        
        assert "agent_id" in metrics
        assert "total_tasks" in metrics
        assert "success_rate" in metrics
        assert metrics["state"] == AgentState.IDLE.value


class TestMessageBus:
    """Тесты системы обмена сообщениями"""
    
    @pytest.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
        
    @pytest.fixture
    def message(self):
        return Message(
            id="test_message",
            sender_id="sender",
            receiver_id="receiver",
            message_type="test",
            content={"data": "test"}
        )
        
    @pytest.mark.asyncio
    async def test_message_bus_registration(self, message_bus):
        """Тест регистрации агентов в шине сообщений"""
        message_bus.register_agent("agent_1")
        message_bus.register_agent("agent_2")
        
        assert "agent_1" in message_bus.message_queues
        assert "agent_2" in message_bus.message_queues
        
    @pytest.mark.asyncio
    async def test_message_sending(self, message_bus, message):
        """Тест отправки сообщений"""
        # Регистрация агентов
        message_bus.register_agent("sender")
        message_bus.register_agent("receiver")
        
        # Отправка сообщения
        success = await message_bus.send_message(message)
        assert success is True
        
        # Получение сообщения
        received = await message_bus.receive_message("receiver", timeout=1.0)
        assert received is not None
        assert received.id == message.id
        assert received.content == message.content
        
    @pytest.mark.asyncio
    async def test_broadcast_message(self, message_bus):
        """Тест broadcast сообщений"""
        # Регистрация агентов
        agents = ["agent_1", "agent_2", "agent_3"]
        for agent_id in agents:
            message_bus.register_agent(agent_id)
            
        # Создание broadcast сообщения
        broadcast_msg = Message(
            id="broadcast",
            sender_id="sender",
            receiver_id=None,  # Broadcast
            message_type="announcement",
            content={"message": "Hello everyone!"}
        )
        
        success = await message_bus.send_message(broadcast_msg)
        assert success is True
        
        # Проверка получения всеми агентами
        for agent_id in agents:
            received = await message_bus.receive_message(agent_id, timeout=1.0)
            if agent_id != "sender":  # Отправитель не получает собственные broadcast
                assert received is not None
                assert received.content["message"] == "Hello everyone!"


class TestTaskDistributor:
    """Тесты распределителя задач"""
    
    @pytest.fixture
    def distributor(self):
        return TaskDistributor()
        
    @pytest.fixture
    def agents(self):
        return [
            MockAgent(name="Agent1"),
            MockAgent(name="Agent2")
        ]
        
    @pytest.fixture
    def task(self):
        return Task(
            id="dist_task",
            content={"data": "test"},
            requirements=["test_capability"],
            priority=1
        )
        
    def test_agent_registration(self, distributor, agents):
        """Тест регистрации агентов в распределителе"""
        for agent in agents:
            distributor.register_agent(agent)
            
        assert len(distributor.agents) == 2
        assert len(distributor.agent_performance) == 2
        
    def test_task_addition(self, distributor, task):
        """Тест добавления задач в очередь"""
        distributor.add_task(task)
        assert len(distributor.task_queue) == 1
        
    @pytest.mark.asyncio
    async def test_task_distribution(self, distributor, agents, task):
        """Тест распределения задач"""
        # Регистрация агентов
        for agent in agents:
            distributor.register_agent(agent)
            
        # Добавление задачи
        distributor.add_task(task)
        
        # Распределение задач
        assignments = await distributor.distribute_tasks()
        
        assert len(assignments) == 1
        assert assignments[0].task.id == task.id
        assert assignments[0].agent_id in [agent.id for agent in agents]


class TestSwarmManager:
    """Тесты менеджера роя"""
    
    @pytest.fixture
    async def swarm(self):
        swarm = SwarmManager()
        await swarm.start()
        yield swarm
        await swarm.stop()
        
    @pytest.fixture
    def agent(self):
        return MockAgent(name="SwarmAgent")
        
    @pytest.fixture
    def task(self):
        return Task(
            id="swarm_task",
            content={"data": "test"},
            requirements=["test_capability"]
        )
        
    @pytest.mark.asyncio
    async def test_swarm_agent_management(self, swarm, agent):
        """Тест управления агентами в рое"""
        # Добавление агента
        success = await swarm.add_agent(agent)
        assert success is True
        assert agent.id in swarm.agents
        
        # Удаление агента
        success = await swarm.remove_agent(agent.id)
        assert success is True
        assert agent.id not in swarm.agents
        
    @pytest.mark.asyncio
    async def test_swarm_task_execution(self, swarm, agent, task):
        """Тест выполнения задач в рое"""
        # Добавление агента
        await swarm.add_agent(agent)
        
        # Выполнение задачи
        result = await swarm.execute_task(task)
        
        assert result.success is True
        assert result.task_id == task.id
        
    def test_swarm_status(self, swarm):
        """Тест получения статуса роя"""
        status = swarm.get_swarm_status()
        
        assert "state" in status
        assert "agents_count" in status
        assert "total_tasks_processed" in status


if __name__ == "__main__":
    pytest.main([__file__])

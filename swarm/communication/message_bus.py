"""
Система обмена сообщениями между агентами
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
import uuid


class MessagePriority(Enum):
    """Приоритеты сообщений"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Сообщение между агентами"""
    id: str
    sender_id: str
    receiver_id: Optional[str]  # None для broadcast сообщений
    message_type: str
    content: Any
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time to live в секундах
    requires_response: bool = False
    correlation_id: Optional[str] = None  # Для связи запрос-ответ


@dataclass
class MessageHandler:
    """Обработчик сообщений"""
    handler_func: Callable
    message_types: List[str]
    priority: int = 0  # Больше = выше приоритет


class MessageBus:
    """
    Шина сообщений для коммуникации между агентами
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.handlers: Dict[str, List[MessageHandler]] = {}
        self.global_handlers: List[MessageHandler] = []
        self.message_history: List[Message] = []
        self.running = False
        self.logger = logging.getLogger("MessageBus")
        
        # Статистика
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_dropped": 0,
            "broadcast_messages": 0
        }
        
    async def start(self):
        """Запустить шину сообщений"""
        self.running = True
        self.logger.info("Шина сообщений запущена")
        
        # Запуск фоновых задач
        asyncio.create_task(self._cleanup_expired_messages())
        
    async def stop(self):
        """Остановить шину сообщений"""
        self.running = False
        self.logger.info("Шина сообщений остановлена")
        
    def register_agent(self, agent_id: str):
        """Зарегистрировать агента в шине"""
        if agent_id not in self.message_queues:
            self.message_queues[agent_id] = asyncio.Queue(maxsize=self.max_queue_size)
            self.logger.info(f"Агент {agent_id} зарегистрирован в шине сообщений")
            
    def unregister_agent(self, agent_id: str):
        """Отменить регистрацию агента"""
        if agent_id in self.message_queues:
            del self.message_queues[agent_id]
            if agent_id in self.handlers:
                del self.handlers[agent_id]
            self.logger.info(f"Агент {agent_id} удален из шины сообщений")
            
    def add_handler(self, agent_id: str, handler: MessageHandler):
        """Добавить обработчик сообщений для агента"""
        if agent_id not in self.handlers:
            self.handlers[agent_id] = []
        self.handlers[agent_id].append(handler)
        # Сортировка по приоритету
        self.handlers[agent_id].sort(key=lambda h: h.priority, reverse=True)
        
    def add_global_handler(self, handler: MessageHandler):
        """Добавить глобальный обработчик сообщений"""
        self.global_handlers.append(handler)
        self.global_handlers.sort(key=lambda h: h.priority, reverse=True)
        
    async def send_message(self, message: Message) -> bool:
        """Отправить сообщение"""
        if not self.running:
            return False
            
        self.stats["messages_sent"] += 1
        
        # Проверка TTL
        if message.ttl and (time.time() - message.timestamp) > message.ttl:
            self.stats["messages_dropped"] += 1
            self.logger.warning(f"Сообщение {message.id} истекло")
            return False
            
        # Добавление в историю
        self.message_history.append(message)
        
        if message.receiver_id is None:
            # Broadcast сообщение
            return await self._broadcast_message(message)
        else:
            # Направленное сообщение
            return await self._send_directed_message(message)
            
    async def _broadcast_message(self, message: Message) -> bool:
        """Отправить broadcast сообщение всем агентам"""
        self.stats["broadcast_messages"] += 1
        success_count = 0
        
        for agent_id in self.message_queues:
            if agent_id != message.sender_id:  # Не отправлять отправителю
                if await self._deliver_to_agent(agent_id, message):
                    success_count += 1
                    
        self.logger.info(f"Broadcast сообщение доставлено {success_count} агентам")
        return success_count > 0
        
    async def _send_directed_message(self, message: Message) -> bool:
        """Отправить направленное сообщение"""
        if message.receiver_id not in self.message_queues:
            self.logger.warning(f"Агент {message.receiver_id} не найден")
            self.stats["messages_dropped"] += 1
            return False
            
        return await self._deliver_to_agent(message.receiver_id, message)
        
    async def _deliver_to_agent(self, agent_id: str, message: Message) -> bool:
        """Доставить сообщение конкретному агенту"""
        try:
            queue = self.message_queues[agent_id]
            await queue.put(message)
            self.stats["messages_delivered"] += 1
            return True
        except asyncio.QueueFull:
            self.logger.warning(f"Очередь агента {agent_id} переполнена")
            self.stats["messages_dropped"] += 1
            return False
        except Exception as e:
            self.logger.error(f"Ошибка доставки сообщения агенту {agent_id}: {e}")
            self.stats["messages_dropped"] += 1
            return False
            
    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Получить сообщение для агента"""
        if agent_id not in self.message_queues:
            return None
            
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.message_queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = await self.message_queues[agent_id].get()
                
            # Проверка TTL
            if message.ttl and (time.time() - message.timestamp) > message.ttl:
                self.logger.warning(f"Получено истекшее сообщение {message.id}")
                return None
                
            return message
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения сообщения для агента {agent_id}: {e}")
            return None
            
    async def process_message(self, agent_id: str, message: Message) -> Any:
        """Обработать сообщение с помощью зарегистрированных обработчиков"""
        # Сначала проверяем обработчики агента
        if agent_id in self.handlers:
            for handler in self.handlers[agent_id]:
                if message.message_type in handler.message_types:
                    try:
                        result = await handler.handler_func(message)
                        return result
                    except Exception as e:
                        self.logger.error(f"Ошибка в обработчике {handler}: {e}")
                        
        # Затем глобальные обработчики
        for handler in self.global_handlers:
            if message.message_type in handler.message_types:
                try:
                    result = await handler.handler_func(message)
                    return result
                except Exception as e:
                    self.logger.error(f"Ошибка в глобальном обработчике {handler}: {e}")
                    
        self.logger.warning(f"Нет обработчика для сообщения типа {message.message_type}")
        return None
        
    async def send_request_response(
        self, 
        sender_id: str, 
        receiver_id: str, 
        message_type: str, 
        content: Any,
        timeout: float = 30.0
    ) -> Any:
        """Отправить запрос и дождаться ответа"""
        correlation_id = str(uuid.uuid4())
        
        # Отправка запроса
        request = Message(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            requires_response=True,
            correlation_id=correlation_id
        )
        
        if not await self.send_message(request):
            return None
            
        # Ожидание ответа
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = await self.receive_message(sender_id, timeout=1.0)
            if (response and 
                response.correlation_id == correlation_id and 
                response.message_type == f"{message_type}_response"):
                return response.content
                
        self.logger.warning(f"Таймаут ожидания ответа на запрос {correlation_id}")
        return None
        
    async def _cleanup_expired_messages(self):
        """Периодическая очистка истекших сообщений"""
        while self.running:
            try:
                current_time = time.time()
                # Очистка истории сообщений (оставляем только последние 1000)
                if len(self.message_history) > 1000:
                    self.message_history = self.message_history[-1000:]
                    
                await asyncio.sleep(60)  # Очистка каждую минуту
            except Exception as e:
                self.logger.error(f"Ошибка при очистке сообщений: {e}")
                await asyncio.sleep(60)
                
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику шины сообщений"""
        return {
            "stats": self.stats.copy(),
            "registered_agents": len(self.message_queues),
            "message_history_size": len(self.message_history),
            "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "global_handlers": len(self.global_handlers),
            "running": self.running
        }
        
    def get_agent_queue_size(self, agent_id: str) -> int:
        """Получить размер очереди сообщений агента"""
        if agent_id in self.message_queues:
            return self.message_queues[agent_id].qsize()
        return 0

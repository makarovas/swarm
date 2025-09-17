"""
Базовый класс для AI-агентов
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..core.agent import Agent, Task, TaskResult


@dataclass
class AIModelConfig:
    """Конфигурация AI-модели"""
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 30.0
    retry_attempts: int = 3
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


class AIAgentBase(Agent, ABC):
    """
    Базовый класс для AI-агентов с поддержкой различных языковых моделей
    """
    
    def __init__(
        self, 
        model_config: AIModelConfig,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        specialized_capabilities: Optional[List[str]] = None
    ):
        # Инициализация базового агента
        capabilities = ["ai_processing", "text_generation", "code_analysis"]
        if specialized_capabilities:
            capabilities.extend(specialized_capabilities)
            
        super().__init__(
            agent_id=agent_id,
            name=name or f"AI-Agent-{model_config.model_name}",
            capabilities=capabilities,
            max_concurrent_tasks=3
        )
        
        self.model_config = model_config
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.conversation_history: List[Dict[str, str]] = []
        self.ai_logger = logging.getLogger(f"AIAgent.{self.name}")
        
        # Статистика AI-агента
        self.total_tokens_used = 0
        self.api_calls_made = 0
        self.average_response_time = 0.0
        
    def _get_default_system_prompt(self) -> str:
        """Системный промпт по умолчанию"""
        return """Ты - AI-агент в системе роевого программирования. 
Твоя задача - помогать в решении задач программирования, анализе кода, 
генерации решений и коллаборации с другими агентами.

Отвечай кратко, структурированно и по существу.
Если задача требует кода, предоставь рабочий код с комментариями.
Если нужна помощь других агентов, укажи это в ответе."""
        
    async def _execute_task_impl(self, task: Task) -> Any:
        """Реализация выполнения задачи через AI"""
        
        # Подготовка запроса для AI
        prompt = self._prepare_prompt(task)
        
        # Вызов AI модели с повторными попытками
        for attempt in range(self.model_config.retry_attempts):
            try:
                start_time = asyncio.get_event_loop().time()
                
                response = await self._call_ai_model(prompt, task)
                
                # Обновление статистики
                execution_time = asyncio.get_event_loop().time() - start_time
                self._update_statistics(execution_time, response)
                
                # Обработка ответа
                result = self._process_ai_response(response, task)
                
                # Сохранение в историю разговора
                self._save_to_history(prompt, response)
                
                return result
                
            except Exception as e:
                self.ai_logger.warning(f"Попытка {attempt + 1} неудачна: {e}")
                if attempt == self.model_config.retry_attempts - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                
    def _prepare_prompt(self, task: Task) -> str:
        """Подготовка промпта для AI модели"""
        
        # Базовая информация о задаче
        prompt_parts = [
            f"Задача: {task.content.get('description', str(task.content))}",
            f"ID задачи: {task.id}",
            f"Требуемые способности: {', '.join(task.requirements)}"
        ]
        
        # Контекст задачи
        if task.context:
            prompt_parts.append(f"Контекст: {task.context}")
            
        # Специфические требования
        if "code_analysis" in task.requirements:
            if "code" in task.content:
                prompt_parts.append(f"Код для анализа:\n```\n{task.content['code']}\n```")
                
        elif "code_generation" in task.requirements:
            if "specification" in task.content:
                prompt_parts.append(f"Спецификация: {task.content['specification']}")
                
        elif "problem_solving" in task.requirements:
            if "problem" in task.content:
                prompt_parts.append(f"Проблема: {task.content['problem']}")
                
        return "\n\n".join(prompt_parts)
        
    @abstractmethod
    async def _call_ai_model(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов конкретной AI модели (должен быть реализован в подклассах)"""
        pass
        
    def _process_ai_response(self, response: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """Обработка ответа от AI модели"""
        
        # Базовая обработка ответа
        result = {
            "ai_response": response.get("content", ""),
            "model_used": self.model_config.model_name,
            "tokens_used": response.get("tokens_used", 0),
            "confidence": response.get("confidence", 0.8),
            "response_type": self._determine_response_type(response, task)
        }
        
        # Специфическая обработка по типу задачи
        if "code_analysis" in task.requirements:
            result.update(self._extract_code_analysis(response))
        elif "code_generation" in task.requirements:
            result.update(self._extract_generated_code(response))
        elif "problem_solving" in task.requirements:
            result.update(self._extract_solution(response))
            
        return result
        
    def _determine_response_type(self, response: Dict[str, Any], task: Task) -> str:
        """Определение типа ответа"""
        content = response.get("content", "").lower()
        
        if "```" in content and any(req in task.requirements for req in ["code_generation", "code_analysis"]):
            return "code"
        elif any(word in content for word in ["ошибка", "проблема", "баг", "error"]):
            return "error_analysis"
        elif any(word in content for word in ["решение", "рекомендация", "предложение"]):
            return "solution"
        else:
            return "general"
            
    def _extract_code_analysis(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение результатов анализа кода"""
        content = response.get("content", "")
        
        analysis = {
            "issues_found": [],
            "suggestions": [],
            "complexity_score": 0.5
        }
        
        # Простой парсинг для извлечения проблем и предложений
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("• "):
                if any(word in line.lower() for word in ["ошибка", "проблема", "баг"]):
                    analysis["issues_found"].append(line[2:])
                elif any(word in line.lower() for word in ["рекомендация", "предложение", "улучшение"]):
                    analysis["suggestions"].append(line[2:])
                    
        return analysis
        
    def _extract_generated_code(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение сгенерированного кода"""
        content = response.get("content", "")
        
        # Поиск блоков кода
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
        
        return {
            "generated_code": code_blocks[0] if code_blocks else "",
            "code_blocks_count": len(code_blocks),
            "has_documentation": "def " in content and '"""' in content
        }
        
    def _extract_solution(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение решения проблемы"""
        content = response.get("content", "")
        
        return {
            "solution_steps": [line.strip() for line in content.split('\n') if line.strip() and line.strip().startswith(('1.', '2.', '3.', '-'))],
            "requires_collaboration": "другие агенты" in content.lower() or "коллаборация" in content.lower(),
            "estimated_complexity": "высокая" if len(content) > 500 else "низкая"
        }
        
    def _save_to_history(self, prompt: str, response: Dict[str, Any]):
        """Сохранение в историю разговора"""
        self.conversation_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        self.conversation_history.append({
            "role": "assistant", 
            "content": response.get("content", ""),
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Ограничиваем историю последними 20 сообщениями
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
            
    def _update_statistics(self, execution_time: float, response: Dict[str, Any]):
        """Обновление статистики агента"""
        self.api_calls_made += 1
        self.total_tokens_used += response.get("tokens_used", 0)
        
        # Обновление среднего времени ответа
        if self.average_response_time == 0:
            self.average_response_time = execution_time
        else:
            self.average_response_time = (self.average_response_time + execution_time) / 2
            
    def get_ai_metrics(self) -> Dict[str, Any]:
        """Получение метрик AI-агента"""
        base_metrics = self.get_metrics()
        
        ai_metrics = {
            "model_name": self.model_config.model_name,
            "total_tokens_used": self.total_tokens_used,
            "api_calls_made": self.api_calls_made,
            "average_response_time": self.average_response_time,
            "conversation_history_length": len(self.conversation_history),
            "cost_estimate": self._estimate_cost()
        }
        
        base_metrics.update(ai_metrics)
        return base_metrics
        
    def _estimate_cost(self) -> float:
        """Примерная оценка стоимости использования"""
        # Примерные расценки (нужно настроить под конкретные модели)
        cost_per_1k_tokens = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
            "claude-3": 0.008,
            "local": 0.0
        }
        
        rate = cost_per_1k_tokens.get(self.model_config.model_name, 0.01)
        return (self.total_tokens_used / 1000) * rate
        
    async def clear_conversation_history(self):
        """Очистка истории разговора"""
        self.conversation_history.clear()
        self.ai_logger.info("История разговора очищена")
        
    async def set_system_prompt(self, new_prompt: str):
        """Обновление системного промпта"""
        self.system_prompt = new_prompt
        await self.clear_conversation_history()  # Очищаем историю при смене промпта
        self.ai_logger.info("Системный промпт обновлен")

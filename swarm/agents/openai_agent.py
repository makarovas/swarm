"""
AI-агент для интеграции с OpenAI GPT моделями
"""

import asyncio
import json
from typing import Dict, Any, Optional, List

from .ai_agent_base import AIAgentBase, AIModelConfig
from ..core.agent import Task


class OpenAIAgent(AIAgentBase):
    """
    AI-агент для работы с OpenAI GPT моделями
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-3.5-turbo",
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        config = AIModelConfig(
            model_name=model_name,
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            **kwargs
        )
        
        super().__init__(
            model_config=config,
            agent_id=agent_id,
            name=name or f"OpenAI-{model_name}",
            system_prompt=system_prompt,
            specialized_capabilities=["openai_integration", "advanced_reasoning"]
        )
        
    async def _call_ai_model(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов OpenAI API"""
        
        try:
            # Попытка импорта OpenAI (может быть не установлен)
            try:
                import openai
            except ImportError:
                return await self._mock_openai_response(prompt, task)
            
            # Настройка клиента
            client = openai.AsyncOpenAI(api_key=self.model_config.api_key)
            
            # Подготовка сообщений
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Добавление контекста из истории (последние 5 сообщений)
            if self.conversation_history:
                recent_history = self.conversation_history[-10:]  # Последние 10 сообщений
                for msg in recent_history:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            messages.append({"role": "user", "content": prompt})
            
            # Вызов API
            response = await client.chat.completions.create(
                model=self.model_config.model_name,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                timeout=self.model_config.timeout
            )
            
            # Обработка ответа
            result = {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "confidence": self._calculate_confidence(response)
            }
            
            return result
            
        except Exception as e:
            self.ai_logger.error(f"Ошибка вызова OpenAI API: {e}")
            # Возвращаем заглушку в случае ошибки
            return await self._mock_openai_response(prompt, task)
            
    async def _mock_openai_response(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Заглушка для OpenAI ответа (когда API недоступен)"""
        
        await asyncio.sleep(1)  # Симуляция задержки API
        
        # Простая эмуляция ответа на основе типа задачи
        if "code_analysis" in task.requirements:
            content = f"""Анализ кода (симуляция OpenAI):

Код выглядит структурированным. Вот основные наблюдения:
- Функции имеют понятные имена
- Логика разделена на модули
- Рекомендации:
  • Добавить больше комментариев
  • Использовать type hints
  • Добавить обработку исключений

Общая оценка: 8/10"""

        elif "code_generation" in task.requirements:
            spec = task.content.get("specification", "функция")
            content = f"""Генерация кода (симуляция OpenAI):

```python
def generated_function():
    \"""
    Сгенерированная функция для: {spec}
    \"""
    # TODO: Реализовать логику
    result = "Обработано"
    return result

# Пример использования
if __name__ == "__main__":
    result = generated_function()
    print(result)
```

Код готов к использованию и тестированию."""

        else:
            content = f"""Ответ на задачу (симуляция OpenAI):

Анализирую ваш запрос: {prompt[:100]}...

Предлагаю следующий подход:
1. Детальный анализ проблемы
2. Разработка пошагового решения
3. Тестирование и валидация

Готов предоставить более детальную информацию по запросу."""

        return {
            "content": content,
            "tokens_used": len(prompt.split()) + len(content.split()),
            "model": f"{self.model_config.model_name}-simulated",
            "finish_reason": "stop",
            "confidence": 0.85
        }
        
    def _calculate_confidence(self, response) -> float:
        """Расчет уверенности на основе ответа OpenAI"""
        
        # Базовая уверенность
        confidence = 0.8
        
        # Корректировка на основе finish_reason
        if hasattr(response.choices[0], 'finish_reason'):
            if response.choices[0].finish_reason == "stop":
                confidence += 0.1
            elif response.choices[0].finish_reason == "length":
                confidence -= 0.2
                
        # Корректировка на основе длины ответа
        content_length = len(response.choices[0].message.content)
        if content_length < 50:
            confidence -= 0.2
        elif content_length > 500:
            confidence += 0.1
            
        return max(0.1, min(1.0, confidence))
        
    async def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """Специализированный метод анализа качества кода"""
        
        task = Task(
            id="code_quality_analysis",
            content={
                "code": code,
                "description": "Провести детальный анализ качества кода"
            },
            requirements=["code_analysis", "ai_processing"]
        )
        
        result = await self._execute_task_impl(task)
        return result
        
    async def generate_code_from_spec(self, specification: str, language: str = "python") -> Dict[str, Any]:
        """Генерация кода по спецификации"""
        
        task = Task(
            id="code_generation",
            content={
                "specification": specification,
                "language": language,
                "description": f"Сгенерировать {language} код по спецификации"
            },
            requirements=["code_generation", "ai_processing"]
        )
        
        result = await self._execute_task_impl(task)
        return result
        
    async def debug_code(self, code: str, error_description: str) -> Dict[str, Any]:
        """Помощь в отладке кода"""
        
        task = Task(
            id="code_debugging",
            content={
                "code": code,
                "error": error_description,
                "description": "Найти и исправить ошибки в коде"
            },
            requirements=["code_analysis", "problem_solving", "ai_processing"]
        )
        
        result = await self._execute_task_impl(task)
        return result

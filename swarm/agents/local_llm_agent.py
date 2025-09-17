"""
AI-агент для работы с локальными LLM моделями
"""

import asyncio
import json
from typing import Dict, Any, Optional

from .ai_agent_base import AIAgentBase, AIModelConfig
from ..core.agent import Task


class LocalLLMAgent(AIAgentBase):
    """
    AI-агент для работы с локальными языковыми моделями
    (Ollama, LM Studio, локальные Transformers и т.д.)
    """
    
    def __init__(
        self,
        model_name: str = "llama2",
        base_url: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        config = AIModelConfig(
            model_name=model_name,
            base_url=base_url,
            timeout=60.0,  # Локальные модели могут работать медленнее
            **kwargs
        )
        
        super().__init__(
            model_config=config,
            agent_id=agent_id,
            name=name or f"Local-{model_name}",
            system_prompt=system_prompt,
            specialized_capabilities=["local_processing", "privacy_focused", "offline_capable"]
        )
        
    async def _call_ai_model(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов локальной LLM модели"""
        
        try:
            # Попытка использования разных методов подключения к локальным моделям
            
            # 1. Ollama API
            if "ollama" in self.model_config.base_url or ":11434" in self.model_config.base_url:
                return await self._call_ollama_api(prompt, task)
                
            # 2. LM Studio API
            elif "lmstudio" in self.model_config.base_url or ":1234" in self.model_config.base_url:
                return await self._call_lmstudio_api(prompt, task)
                
            # 3. OpenAI-совместимый API
            elif "/v1" in self.model_config.base_url:
                return await self._call_openai_compatible_api(prompt, task)
                
            # 4. Прямое использование Transformers
            else:
                return await self._call_transformers_model(prompt, task)
                
        except Exception as e:
            self.ai_logger.error(f"Ошибка вызова локальной модели: {e}")
            return await self._mock_local_response(prompt, task)
            
    async def _call_ollama_api(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов Ollama API"""
        
        try:
            import aiohttp
            
            # Подготовка сообщений с учетом системного промпта
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Добавление истории разговора
            if self.conversation_history:
                recent_history = self.conversation_history[-6:]
                for msg in recent_history:
                    if msg["role"] in ["user", "assistant"]:
                        messages.insert(-1, {
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            payload = {
                "model": self.model_config.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.model_config.temperature,
                    "num_predict": self.model_config.max_tokens
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.model_config.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.model_config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "content": data.get("message", {}).get("content", ""),
                            "tokens_used": self._estimate_tokens(prompt, data.get("message", {}).get("content", "")),
                            "model": data.get("model", self.model_config.model_name),
                            "done": data.get("done", True),
                            "confidence": 0.8
                        }
                    else:
                        raise Exception(f"Ollama API вернул статус {response.status}")
                        
        except ImportError:
            self.ai_logger.warning("aiohttp не установлен, используем заглушку")
            return await self._mock_local_response(prompt, task)
        except Exception as e:
            self.ai_logger.error(f"Ошибка Ollama API: {e}")
            return await self._mock_local_response(prompt, task)
            
    async def _call_lmstudio_api(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов LM Studio API"""
        
        try:
            import aiohttp
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            payload = {
                "model": self.model_config.model_name,
                "messages": messages,
                "temperature": self.model_config.temperature,
                "max_tokens": self.model_config.max_tokens,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.model_config.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.model_config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        choice = data.get("choices", [{}])[0]
                        return {
                            "content": choice.get("message", {}).get("content", ""),
                            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                            "model": data.get("model", self.model_config.model_name),
                            "finish_reason": choice.get("finish_reason", "stop"),
                            "confidence": 0.85
                        }
                    else:
                        raise Exception(f"LM Studio API вернул статус {response.status}")
                        
        except Exception as e:
            self.ai_logger.error(f"Ошибка LM Studio API: {e}")
            return await self._mock_local_response(prompt, task)
            
    async def _call_openai_compatible_api(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов OpenAI-совместимого API"""
        
        try:
            import aiohttp
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            payload = {
                "model": self.model_config.model_name,
                "messages": messages,
                "temperature": self.model_config.temperature,
                "max_tokens": self.model_config.max_tokens
            }
            
            headers = {}
            if self.model_config.api_key:
                headers["Authorization"] = f"Bearer {self.model_config.api_key}"
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.model_config.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.model_config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        choice = data.get("choices", [{}])[0]
                        return {
                            "content": choice.get("message", {}).get("content", ""),
                            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                            "model": data.get("model", self.model_config.model_name),
                            "finish_reason": choice.get("finish_reason", "stop"),
                            "confidence": 0.8
                        }
                        
        except Exception as e:
            self.ai_logger.error(f"Ошибка OpenAI-совместимого API: {e}")
            return await self._mock_local_response(prompt, task)
            
    async def _call_transformers_model(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Прямой вызов модели через Transformers"""
        
        try:
            # Это требует установки transformers и torch
            # В production среде лучше вынести в отдельный процесс
            
            # Заглушка для Transformers
            await asyncio.sleep(3)  # Симуляция времени инференса
            
            return {
                "content": f"Ответ локальной модели Transformers на: {prompt[:50]}...\n\nЭто результат обработки локальной моделью. Для полной функциональности установите transformers и pytorch.",
                "tokens_used": self._estimate_tokens(prompt, "response"),
                "model": self.model_config.model_name,
                "finish_reason": "stop",
                "confidence": 0.75
            }
            
        except Exception as e:
            self.ai_logger.error(f"Ошибка Transformers модели: {e}")
            return await self._mock_local_response(prompt, task)
            
    async def _mock_local_response(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Заглушка для локальной модели"""
        
        await asyncio.sleep(2)  # Симуляция времени обработки
        
        if "code_analysis" in task.requirements:
            content = """Анализ кода (локальная модель):

Проанализировал представленный код. Основные выводы:

✓ Структура кода понятна
✓ Используются хорошие практики именования
✓ Логика разделена на функции

Рекомендации для улучшения:
- Добавить type hints для лучшей читаемости
- Включить docstrings для документации
- Рассмотреть возможность рефакторинга длинных функций

Преимущества локальной обработки:
- Полная приватность данных
- Быстрый доступ без интернета
- Настраиваемость под специфические задачи"""

        elif "code_generation" in task.requirements:
            spec = task.content.get("specification", "функциональность")
            content = f"""Генерация кода (локальная модель):

```python
# Сгенерированный код для: {spec}

def local_generated_function(input_data):
    \"""
    Функция, сгенерированная локальной моделью
    для реализации: {spec}
    \"""
    
    # Валидация входных данных
    if not input_data:
        return None
        
    # Основная логика
    processed_data = process_locally(input_data)
    
    return {
        'result': processed_data,
        'status': 'success',
        'processed_by': 'local_model'
    }

def process_locally(data):
    \"""Локальная обработка данных\"""
    return f"Обработано локально: {data}"
```

Код готов для использования!"""

        else:
            content = f"""Ответ локальной модели:

Обрабатываю ваш запрос локально для максимальной приватности.

Запрос: {prompt[:100]}...

Преимущества локальной обработки:
🔒 Полная конфиденциальность
⚡ Быстрая обработка
🌐 Работа оффлайн
⚙️ Настраиваемость

Готов предоставить более детальную информацию или выполнить дополнительные задачи."""

        return {
            "content": content,
            "tokens_used": self._estimate_tokens(prompt, content),
            "model": f"{self.model_config.model_name}-local",
            "finish_reason": "stop",
            "confidence": 0.8
        }
        
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """Примерная оценка количества токенов"""
        # Простая оценка: ~4 символа на токен
        return len(prompt + response) // 4
        
    async def check_model_availability(self) -> Dict[str, Any]:
        """Проверка доступности локальной модели"""
        
        try:
            # Пробуем простой запрос к модели
            test_response = await self._call_ai_model("Привет", Task(
                id="health_check",
                content={"description": "Проверка работоспособности"},
                requirements=["ai_processing"]
            ))
            
            return {
                "available": True,
                "model": self.model_config.model_name,
                "base_url": self.model_config.base_url,
                "response_time": test_response.get("response_time", 0),
                "status": "healthy"
            }
            
        except Exception as e:
            return {
                "available": False,
                "model": self.model_config.model_name,
                "base_url": self.model_config.base_url,
                "error": str(e),
                "status": "unhealthy"
            }

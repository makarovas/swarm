"""
AI-агент для интеграции с Anthropic Claude
"""

import asyncio
from typing import Dict, Any, Optional

from .ai_agent_base import AIAgentBase, AIModelConfig
from ..core.agent import Task


class AnthropicAgent(AIAgentBase):
    """
    AI-агент для работы с Anthropic Claude
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-3-sonnet-20240229",
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        config = AIModelConfig(
            model_name=model_name,
            api_key=api_key,
            base_url="https://api.anthropic.com",
            **kwargs
        )
        
        super().__init__(
            model_config=config,
            agent_id=agent_id,
            name=name or f"Claude-{model_name}",
            system_prompt=system_prompt,
            specialized_capabilities=["anthropic_integration", "detailed_analysis", "safety_focus"]
        )
        
    async def _call_ai_model(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов Anthropic Claude API"""
        
        try:
            # Попытка импорта Anthropic SDK
            try:
                import anthropic
            except ImportError:
                return await self._mock_anthropic_response(prompt, task)
            
            # Настройка клиента
            client = anthropic.AsyncAnthropic(api_key=self.model_config.api_key)
            
            # Подготовка сообщений
            messages = []
            
            # Добавление контекста из истории
            if self.conversation_history:
                recent_history = self.conversation_history[-8:]  # Claude лучше работает с более короткой историей
                for msg in recent_history:
                    if msg["role"] in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                        
            messages.append({"role": "user", "content": prompt})
            
            # Вызов API
            response = await client.messages.create(
                model=self.model_config.model_name,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
                system=self.system_prompt,
                messages=messages
            )
            
            # Обработка ответа
            result = {
                "content": response.content[0].text if response.content else "",
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "confidence": self._calculate_confidence(response)
            }
            
            return result
            
        except Exception as e:
            self.ai_logger.error(f"Ошибка вызова Anthropic API: {e}")
            return await self._mock_anthropic_response(prompt, task)
            
    async def _mock_anthropic_response(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Заглушка для Anthropic ответа"""
        
        await asyncio.sleep(1.2)  # Симуляция задержки API
        
        if "code_analysis" in task.requirements:
            content = """Детальный анализ кода (симуляция Claude):

После тщательного изучения представленного кода, могу предоставить следующий анализ:

**Сильные стороны:**
- Четкая структура и организация
- Соблюдение принципов чистого кода
- Адекватная обработка ошибок

**Области для улучшения:**
- Документация могла бы быть более подробной
- Некоторые функции можно разбить на более мелкие
- Рекомендую добавить юнит-тесты

**Рекомендации по безопасности:**
- Валидация входных данных
- Защита от инъекций
- Логирование безопасности

Общая оценка: Код демонстрирует хорошие практики разработки."""

        elif "code_generation" in task.requirements:
            spec = task.content.get("specification", "задача")
            content = f"""Генерация кода (симуляция Claude):

Основываясь на спецификации "{spec}", предлагаю следующее решение:

```python
class Solution:
    \"""
    Решение для: {spec}
    
    Это решение следует принципам:
    - Читаемости кода
    - Производительности  
    - Безопасности
    \"""
    
    def __init__(self):
        self.initialized = True
        
    def process(self, data):
        \"""Основной метод обработки\"""
        try:
            # Валидация входных данных
            if not self._validate_input(data):
                raise ValueError("Некорректные входные данные")
                
            # Основная логика
            result = self._execute_logic(data)
            
            return result
            
        except Exception as e:
            self._log_error(e)
            raise
            
    def _validate_input(self, data):
        \"""Валидация входных данных\"""
        return data is not None
        
    def _execute_logic(self, data):
        \"""Выполнение основной логики\"""
        return f"Обработано: {data}"
        
    def _log_error(self, error):
        \"""Логирование ошибок\"""
        print(f"Ошибка: {error}")
```

Код включает обработку ошибок, валидацию и документацию."""

        else:
            content = f"""Размышление над задачей (симуляция Claude):

Анализируя ваш запрос: "{prompt[:100]}..."

Подход к решению:

1. **Анализ проблемы**: Понимание всех аспектов задачи
2. **Планирование**: Разработка структурированного подхода
3. **Реализация**: Пошаговое выполнение с контролем качества
4. **Валидация**: Проверка результатов и безопасности

**Ключевые соображения:**
- Безопасность и надежность решения
- Производительность и масштабируемость
- Удобство сопровождения

Готов предоставить более детализированное решение или ответить на уточняющие вопросы."""

        return {
            "content": content,
            "tokens_used": len(prompt.split()) + len(content.split()),
            "model": f"{self.model_config.model_name}-simulated",
            "stop_reason": "end_turn",
            "confidence": 0.9
        }
        
    def _calculate_confidence(self, response) -> float:
        """Расчет уверенности для Claude"""
        confidence = 0.85  # Claude обычно более уверен в ответах
        
        if hasattr(response, 'stop_reason'):
            if response.stop_reason == "end_turn":
                confidence += 0.1
            elif response.stop_reason == "max_tokens":
                confidence -= 0.15
                
        # Claude обычно дает более развернутые ответы
        if hasattr(response, 'content') and response.content:
            content_length = len(response.content[0].text if response.content else "")
            if content_length > 200:
                confidence += 0.05
                
        return max(0.1, min(1.0, confidence))
        
    async def ethical_code_review(self, code: str) -> Dict[str, Any]:
        """Этический обзор кода (специализация Claude)"""
        
        enhanced_prompt = f"""
Провести этический и безопасностный анализ следующего кода:

{code}

Обратить особое внимание на:
- Безопасность данных
- Потенциальные уязвимости
- Этические аспекты использования
- Соответствие best practices
"""
        
        task = Task(
            id="ethical_code_review",
            content={
                "code": code,
                "description": enhanced_prompt
            },
            requirements=["code_analysis", "safety_focus", "ai_processing"]
        )
        
        result = await self._execute_task_impl(task)
        return result

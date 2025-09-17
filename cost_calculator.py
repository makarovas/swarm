"""
Калькулятор стоимости для системы AI-агентов
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass
class ModelPricing:
    """Актуальные цены на AI модели (на декабрь 2024)"""
    input_price_per_1k: float  # Цена за 1000 входных токенов
    output_price_per_1k: float  # Цена за 1000 выходных токенов
    name: str


# Актуальные цены (в USD)
MODEL_PRICES = {
    "gpt-4": ModelPricing(0.03, 0.06, "GPT-4"),
    "gpt-4-turbo": ModelPricing(0.01, 0.03, "GPT-4 Turbo"),
    "gpt-3.5-turbo": ModelPricing(0.0015, 0.002, "GPT-3.5 Turbo"),
    "claude-3-opus": ModelPricing(0.015, 0.075, "Claude-3 Opus"),
    "claude-3-sonnet": ModelPricing(0.003, 0.015, "Claude-3 Sonnet"),
    "claude-3-haiku": ModelPricing(0.00025, 0.00125, "Claude-3 Haiku"),
    "local-llm": ModelPricing(0.0, 0.0, "Локальная модель"),
}


class CostCalculator:
    """Калькулятор стоимости вызовов AI-агентов"""
    
    def __init__(self):
        self.prices = MODEL_PRICES
        
    def estimate_tokens(self, text: str) -> int:
        """Примерная оценка количества токенов"""
        # Приблизительно 4 символа = 1 токен для английского
        # Для русского языка коэффициент выше - примерно 2-3 символа = 1 токен
        chars = len(text)
        if any(ord(char) > 127 for char in text):  # Есть не-ASCII символы (русский)
            return math.ceil(chars / 2.5)
        else:
            return math.ceil(chars / 4)
            
    def calculate_single_call_cost(
        self, 
        model_name: str, 
        input_text: str, 
        output_text: str
    ) -> Dict[str, float]:
        """Расчет стоимости одного вызова"""
        
        if model_name not in self.prices:
            return {"error": f"Модель {model_name} не найдена"}
            
        pricing = self.prices[model_name]
        
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        
        input_cost = (input_tokens / 1000) * pricing.input_price_per_1k
        output_cost = (output_tokens / 1000) * pricing.output_price_per_1k
        total_cost = input_cost + output_cost
        
        return {
            "model": pricing.name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "total_cost_rub": round(total_cost * 95, 4)  # Примерный курс USD/RUB
        }
        
    def calculate_swarm_task_cost(
        self, 
        task_description: str,
        models_used: List[str],
        parallel_execution: bool = False
    ) -> Dict[str, any]:
        """Расчет стоимости выполнения задачи в рое"""
        
        # Типичные размеры для разных типов задач
        task_scenarios = {
            "code_analysis": {
                "input": f"""
Системный промпт: Ты AI-агент для анализа кода в системе роевого программирования.

Задача: {task_description}

Код для анализа:
```python
def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed = False
    
    def process(self):
        if not self.processed:
            self.data = [x * 2 for x in self.data]
            self.processed = True
        return self.data
```

Проанализируй код на предмет:
1. Качества и читаемости
2. Производительности
3. Потенциальных ошибок
4. Рекомендаций по улучшению
""",
                "output": """
Анализ кода:

## Качество и читаемость
✅ **Хорошо:**
- Функции имеют понятные имена
- Логика разделена корректно
- Есть обработка граничных случаев

⚠️ **Можно улучшить:**
- Отсутствуют docstrings
- Нет type hints
- Класс DataProcessor нарушает принцип единственной ответственности

## Производительность
🔴 **Проблемы:**
- `fibonacci()` - экспоненциальная сложность O(2^n)
- Рекурсивная реализация приведет к stack overflow

💡 **Рекомендации:**
```python
def fibonacci_optimized(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

## Потенциальные ошибки
- factorial() корректно обрабатывает отрицательные числа
- fibonacci() не обрабатывает отрицательные входы
- DataProcessor может быть вызван повторно

## Рекомендации
1. Добавить type hints и docstrings
2. Использовать итеративную версию fibonacci
3. Добавить валидацию входных данных
4. Рассмотреть использование functools.lru_cache для оптимизации

Общая оценка: 7/10
"""
            },
            
            "code_generation": {
                "input": f"""
Системный промпт: Ты AI-агент для генерации кода в системе роевого программирования.

Задача: {task_description}

Спецификация: Создать класс для работы с приоритетной очередью задач в системе роевого программирования.

Требования:
- Поддержка приоритетов (1-10, где 10 - наивысший)
- Методы добавления и извлечения задач
- Возможность просмотра без извлечения
- Thread-safe операции
- Метрики использования
- Type hints и документация
""",
                "output": """
```python
import heapq
import threading
import time
from typing import Any, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class Task:
    \"\"\"Задача с приоритетом\"\"\"
    id: str
    content: Any
    priority: int = 1  # 1-10, где 10 - наивысший
    created_at: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        # Для heapq (min-heap) инвертируем приоритет
        return self.priority > other.priority


class PriorityTaskQueue:
    \"\"\"
    Thread-safe приоритетная очередь задач
    
    Пример использования:
        queue = PriorityTaskQueue()
        queue.put(Task("task1", "content", priority=5))
        task = queue.get()  # Возвращает задачу с наивысшим приоритетом
    \"\"\"
    
    def __init__(self, max_size: Optional[int] = None):
        self._heap: List[Task] = []
        self._lock = threading.RLock()
        self._max_size = max_size
        
        # Метрики
        self._total_added = 0
        self._total_removed = 0
        self._created_at = time.time()
    
    def put(self, task: Task) -> bool:
        \"\"\"
        Добавить задачу в очередь
        
        Args:
            task: Задача для добавления
            
        Returns:
            True если задача добавлена, False если очередь переполнена
        \"\"\"
        with self._lock:
            if self._max_size and len(self._heap) >= self._max_size:
                return False
                
            heapq.heappush(self._heap, task)
            self._total_added += 1
            return True
    
    def get(self, timeout: Optional[float] = None) -> Optional[Task]:
        \"\"\"
        Извлечь задачу с наивысшим приоритетом
        
        Args:
            timeout: Максимальное время ожидания (не реализовано в данном примере)
            
        Returns:
            Задача с наивысшим приоритетом или None если очередь пуста
        \"\"\"
        with self._lock:
            if not self._heap:
                return None
                
            task = heapq.heappop(self._heap)
            self._total_removed += 1
            return task
    
    def peek(self) -> Optional[Task]:
        \"\"\"Посмотреть следующую задачу без извлечения\"\"\"
        with self._lock:
            return self._heap[0] if self._heap else None
    
    def size(self) -> int:
        \"\"\"Текущий размер очереди\"\"\"
        with self._lock:
            return len(self._heap)
    
    def is_empty(self) -> bool:
        \"\"\"Проверить, пуста ли очередь\"\"\"
        with self._lock:
            return len(self._heap) == 0
    
    def get_metrics(self) -> Dict[str, Any]:
        \"\"\"Получить метрики использования\"\"\"
        with self._lock:
            uptime = time.time() - self._created_at
            return {
                "current_size": len(self._heap),
                "total_added": self._total_added,
                "total_removed": self._total_removed,
                "pending_tasks": len(self._heap),
                "throughput": self._total_removed / uptime if uptime > 0 else 0,
                "uptime_seconds": uptime
            }


# Пример использования
if __name__ == "__main__":
    queue = PriorityTaskQueue(max_size=100)
    
    # Добавление задач
    queue.put(Task("low", "Low priority task", priority=2))
    queue.put(Task("high", "High priority task", priority=9))
    queue.put(Task("medium", "Medium priority task", priority=5))
    
    # Извлечение в порядке приоритета
    while not queue.is_empty():
        task = queue.get()
        print(f"Processing: {task.id} (priority: {task.priority})")
    
    # Метрики
    print("Metrics:", queue.get_metrics())
```

Код готов к использованию и полностью соответствует спецификации!
"""
            },
            
            "problem_solving": {
                "input": f"""
Системный промпт: Ты AI-агент для решения проблем в системе роевого программирования.

Проблема: {task_description}

Контекст: В нашей системе роевого программирования агенты начали выполнять задачи слишком медленно. Средняя производительность упала с 50 задач/мин до 15 задач/мин. 

Симптомы:
- Высокая загрузка CPU (95%+)
- Память используется нормально (60%)
- Очереди задач переполняются
- Агенты часто переходят в состояние WAITING
- Логи показывают много таймаутов

Архитектура:
- 10 агентов в рое
- Async/await архитектура
- Шина сообщений на asyncio.Queue
- TaskDistributor с LOAD_BALANCED стратегией

Нужно найти причину деградации производительности и предложить решение.
""",
                "output": """
# Анализ проблемы производительности

## 🔍 Диагностика

### Основная проблема
Высокая загрузка CPU (95%+) при нормальном использовании памяти указывает на **проблему конкуренции за ресурсы** и возможную **активную ожидание (busy waiting)**.

### Вероятные причины

1. **Busy waiting в циклах опроса**
   ```python
   # Плохо: активное ожидание
   while not queue.empty():
       pass  # Жжет CPU
   
   # Хорошо: async ожидание
   await asyncio.sleep(0.1)
   ```

2. **Блокирующие операции в async коде**
   ```python
   # Блокирует event loop
   time.sleep(1)  # ❌
   
   # Не блокирует
   await asyncio.sleep(1)  # ✅
   ```

3. **Неправильная работа с очередями**
   ```python
   # Может вызывать таймауты
   message = await queue.get()  # Бесконечное ожидание
   
   # Лучше с таймаутом
   message = await asyncio.wait_for(queue.get(), timeout=1.0)
   ```

## 🛠️ План решения

### Немедленные действия (0-1 час)

1. **Добавить профилирование**
   ```python
   import cProfile
   import asyncio
   
   async def profile_swarm():
       profiler = cProfile.Profile()
       profiler.enable()
       
       # Код роя
       await swarm.run_for_time(60)  # 1 минута
       
       profiler.disable()
       profiler.dump_stats('swarm_profile.prof')
   ```

2. **Оптимизировать циклы опроса**
   ```python
   # В TaskDistributor._task_distribution_loop()
   async def _task_distribution_loop(self):
       while self.running:
           assignments = await self.distribute_tasks()
           
           if not assignments:
               await asyncio.sleep(0.1)  # ⭐ Добавить задержку
           
           for assignment in assignments:
               await self._execute_assignment(assignment)
   ```

3. **Добавить мониторинг**
   ```python
   import psutil
   import time
   
   async def monitor_performance():
       while True:
           cpu_percent = psutil.cpu_percent()
           memory_percent = psutil.virtual_memory().percent
           
           if cpu_percent > 90:
               logger.warning(f"High CPU: {cpu_percent}%")
           
           await asyncio.sleep(5)
   ```

### Краткосрочные улучшения (1-24 часа)

4. **Оптимизировать обработку сообщений**
   ```python
   async def _message_processing_loop(self):
       while self.running:
           processed_any = False
           
           for agent_id in self.agents:
               message = await self.message_bus.receive_message(
                   agent_id, timeout=0.01  # Короткий таймаут
               )
               if message:
                   await self._process_agent_message(agent_id, message)
                   processed_any = True
           
           if not processed_any:
               await asyncio.sleep(0.05)  # Избегаем busy waiting
   ```

5. **Пулы соединений для внешних API**
   ```python
   import aiohttp
   
   # Переиспользуем сессию
   class OptimizedAIAgent:
       def __init__(self):
           self.session = aiohttp.ClientSession(
               connector=aiohttp.TCPConnector(limit=10)
           )
   ```

6. **Батчинг операций**
   ```python
   async def process_messages_batch(self, agent_id: str):
       messages = []
       
       # Собираем несколько сообщений
       for _ in range(10):
           msg = await self.message_bus.receive_message(
               agent_id, timeout=0.01
           )
           if msg:
               messages.append(msg)
           else:
               break
       
       # Обрабатываем батчем
       if messages:
           await self.process_message_batch(messages)
   ```

### Долгосрочные оптимизации (1-7 дней)

7. **Адаптивная стратегия распределения**
   ```python
   class AdaptiveDistributor:
       def __init__(self):
           self.cpu_threshold = 80
           self.adaptive_delay = 0.1
       
       async def distribute_with_backpressure(self):
           cpu_usage = psutil.cpu_percent()
           
           if cpu_usage > self.cpu_threshold:
               # Замедляем при высокой нагрузке
               self.adaptive_delay = min(self.adaptive_delay * 1.2, 1.0)
           else:
               # Ускоряем при низкой нагрузке
               self.adaptive_delay = max(self.adaptive_delay * 0.9, 0.01)
           
           await asyncio.sleep(self.adaptive_delay)
   ```

8. **Метрики и алерты**
   ```python
   class PerformanceMonitor:
       def __init__(self):
           self.metrics = {
               'tasks_per_minute': 0,
               'avg_response_time': 0,
               'cpu_usage': 0,
               'queue_sizes': {}
           }
       
       async def check_performance_degradation(self):
           if self.metrics['tasks_per_minute'] < 30:  # Пороговое значение
               await self.send_alert("Performance degradation detected")
   ```

## 📊 Ожидаемые результаты

- **CPU снизится с 95% до 70-80%**
- **Производительность вырастет с 15 до 40+ задач/мин**
- **Таймауты сократятся на 90%**
- **Latency уменьшится в 2-3 раза**

## 🔧 Инструменты для отладки

```bash
# Профилирование Python
python -m cProfile -o profile.stats your_script.py

# Мониторинг системы
htop
iotop
nethogs

# Async профилирование
pip install aiomonitor
```

## ✅ Чек-лист проверки

- [ ] Убрать все `time.sleep()` из async кода
- [ ] Добавить `await asyncio.sleep()` в циклы
- [ ] Проверить таймауты в очередях
- [ ] Оптимизировать батчинг операций
- [ ] Настроить мониторинг производительности
- [ ] Протестировать под нагрузкой

Рекомендую начать с профилирования - это покажет точные узкие места!
"""
            }
        }
        
        # Определяем тип задачи
        task_type = "code_analysis"  # По умолчанию
        if "генерация" in task_description.lower() or "создать" in task_description.lower():
            task_type = "code_generation"
        elif "проблема" in task_description.lower() or "ошибка" in task_description.lower():
            task_type = "problem_solving"
            
        scenario = task_scenarios.get(task_type, task_scenarios["code_analysis"])
        
        # Расчет стоимости для каждой модели
        results = {}
        total_cost = 0
        
        for model in models_used:
            cost_info = self.calculate_single_call_cost(
                model, 
                scenario["input"], 
                scenario["output"]
            )
            results[model] = cost_info
            
            if "total_cost_usd" in cost_info:
                if parallel_execution:
                    # При параллельном выполнении все модели работают
                    total_cost += cost_info["total_cost_usd"]
                else:
                    # При последовательном - берем самую дорогую (worst case)
                    total_cost = max(total_cost, cost_info["total_cost_usd"])
        
        return {
            "task_type": task_type,
            "task_description": task_description,
            "models_used": models_used,
            "execution_mode": "parallel" if parallel_execution else "sequential",
            "individual_costs": results,
            "total_cost_usd": round(total_cost, 6),
            "total_cost_rub": round(total_cost * 95, 4),
            "cost_breakdown": self._get_cost_breakdown(results, parallel_execution)
        }
        
    def _get_cost_breakdown(self, results: Dict, parallel: bool) -> Dict:
        """Детальная разбивка по стоимости"""
        
        breakdown = {
            "cheapest_option": None,
            "most_expensive": None,
            "cost_savings": 0,
            "recommendations": []
        }
        
        valid_results = {k: v for k, v in results.items() if "total_cost_usd" in v}
        
        if not valid_results:
            return breakdown
            
        # Найти самый дешевый и дорогой варианты
        cheapest = min(valid_results.items(), key=lambda x: x[1]["total_cost_usd"])
        expensive = max(valid_results.items(), key=lambda x: x[1]["total_cost_usd"])
        
        breakdown["cheapest_option"] = {
            "model": cheapest[0],
            "cost_usd": cheapest[1]["total_cost_usd"]
        }
        breakdown["most_expensive"] = {
            "model": expensive[0], 
            "cost_usd": expensive[1]["total_cost_usd"]
        }
        
        # Потенциальная экономия
        if len(valid_results) > 1:
            breakdown["cost_savings"] = expensive[1]["total_cost_usd"] - cheapest[1]["total_cost_usd"]
            
        # Рекомендации
        if not parallel:
            breakdown["recommendations"].append(
                f"Используйте {cheapest[0]} вместо {expensive[0]} для экономии ${breakdown['cost_savings']:.4f} за вызов"
            )
            
        if any("local" in model for model in valid_results.keys()):
            breakdown["recommendations"].append(
                "Локальные модели бесплатны, но требуют вычислительных ресурсов"
            )
            
        return breakdown
        
    def monthly_cost_estimate(
        self,
        daily_calls: int,
        models_config: Dict[str, float]  # model -> процент использования
    ) -> Dict[str, float]:
        """Оценка месячных затрат"""
        
        # Типичный вызов (средний размер)
        avg_input = "Системный промпт + описание задачи + код (500 строк)"
        avg_output = "Детальный анализ с рекомендациями и примерами кода (200 строк)"
        
        daily_cost = 0
        breakdown = {}
        
        for model, usage_percent in models_config.items():
            if model in self.prices:
                calls_per_model = int(daily_calls * usage_percent)
                cost_per_call = self.calculate_single_call_cost(model, avg_input, avg_output)
                
                if "total_cost_usd" in cost_per_call:
                    model_daily_cost = calls_per_model * cost_per_call["total_cost_usd"]
                    daily_cost += model_daily_cost
                    breakdown[model] = {
                        "daily_calls": calls_per_model,
                        "cost_per_call": cost_per_call["total_cost_usd"],
                        "daily_cost": model_daily_cost,
                        "monthly_cost": model_daily_cost * 30
                    }
        
        return {
            "daily_cost_usd": round(daily_cost, 4),
            "monthly_cost_usd": round(daily_cost * 30, 2),
            "monthly_cost_rub": round(daily_cost * 30 * 95, 2),
            "breakdown": breakdown
        }


def main():
    """Демонстрация расчета стоимости"""
    
    calc = CostCalculator()
    
    print("💰 Калькулятор стоимости AI-агентов в роевом программировании")
    print("=" * 70)
    
    # 1. Стоимость одного простого вызова
    print("\n📞 Стоимость одного вызова (анализ небольшой функции):")
    print("-" * 50)
    
    simple_input = "Проанализируй эту функцию: def hello(): return 'Hello, World!'"
    simple_output = "Функция простая и корректная. Рекомендации: добавить docstring и type hints."
    
    for model in ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "local-llm"]:
        cost = calc.calculate_single_call_cost(model, simple_input, simple_output)
        if "total_cost_usd" in cost:
            print(f"{cost['model']:20} ${cost['total_cost_usd']:8.6f} (₽{cost['total_cost_rub']:7.4f})")
    
    # 2. Стоимость комплексной задачи в рое
    print(f"\n🔍 Стоимость задачи анализа кода в рое:")
    print("-" * 50)
    
    # Один агент
    single_agent_cost = calc.calculate_swarm_task_cost(
        "Проанализировать качество кода модуля с 5 функциями",
        ["gpt-4"],
        parallel_execution=False
    )
    
    print(f"Один GPT-4 агент:        ${single_agent_cost['total_cost_usd']:.6f}")
    
    # Мульти-агент параллельно
    multi_parallel_cost = calc.calculate_swarm_task_cost(
        "Проанализировать качество кода модуля с 5 функциями", 
        ["gpt-4", "claude-3-sonnet", "gpt-3.5-turbo"],
        parallel_execution=True
    )
    
    print(f"3 агента параллельно:    ${multi_parallel_cost['total_cost_usd']:.6f}")
    
    # Мульти-агент с fallback
    multi_fallback_cost = calc.calculate_swarm_task_cost(
        "Проанализировать качество кода модуля с 5 функциями",
        ["gpt-4", "claude-3-sonnet", "local-llm"], 
        parallel_execution=False
    )
    
    print(f"3 агента с fallback:     ${multi_fallback_cost['total_cost_usd']:.6f}")
    
    # Только локальные модели
    local_only_cost = calc.calculate_swarm_task_cost(
        "Проанализировать качество кода модуля с 5 функциями",
        ["local-llm"],
        parallel_execution=False
    )
    
    print(f"Только локальные модели: ${local_only_cost['total_cost_usd']:.6f}")
    
    # 3. Месячная стоимость для разных сценариев
    print(f"\n📊 Месячные затраты (1000 вызовов/день):")
    print("-" * 50)
    
    scenarios = [
        {
            "name": "Только GPT-3.5",
            "config": {"gpt-3.5-turbo": 1.0}
        },
        {
            "name": "Mix: GPT-4 + GPT-3.5",
            "config": {"gpt-4": 0.3, "gpt-3.5-turbo": 0.7}
        },
        {
            "name": "Premium: GPT-4 + Claude",
            "config": {"gpt-4": 0.5, "claude-3-sonnet": 0.5}
        },
        {
            "name": "Экономный: GPT-3.5 + Local",
            "config": {"gpt-3.5-turbo": 0.6, "local-llm": 0.4}
        }
    ]
    
    for scenario in scenarios:
        monthly = calc.monthly_cost_estimate(1000, scenario["config"])
        print(f"{scenario['name']:25} ${monthly['monthly_cost_usd']:8.2f}/мес (₽{monthly['monthly_cost_rub']:10.2f})")
    
    # 4. Практические рекомендации
    print(f"\n💡 Практические рекомендации:")
    print("-" * 50)
    
    print("🔸 Для разработки: GPT-3.5-turbo (~$0.01 за вызов)")
    print("🔸 Для production: Mix GPT-4 + Claude (~$0.15 за вызов)")
    print("🔸 Для высокой нагрузки: Локальные модели (только затраты на сервер)")
    print("🔸 Оптимальный баланс: 70% GPT-3.5 + 30% GPT-4 (~$0.05 за вызов)")
    
    print(f"\n📈 Экономия с ростом объема:")
    print("-" * 30)
    volumes = [100, 1000, 10000, 100000]
    for volume in volumes:
        monthly = calc.monthly_cost_estimate(volume, {"gpt-3.5-turbo": 1.0})
        cost_per_call = monthly['monthly_cost_usd'] / (volume * 30)
        print(f"{volume:6} вызовов/день: ${cost_per_call:.6f} за вызов")


if __name__ == "__main__":
    main()

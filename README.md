# Система агентного роевого программирования

Эта система реализует концепцию роевого интеллекта для программирования с использованием множественных автономных агентов, способных к коллективному решению сложных задач разработки программного обеспечения.

## 🎯 Основные возможности

- **Автономные агенты** с различными специализациями и способностями
- **Интеллектуальное распределение задач** между агентами
- **Коллективное принятие решений** через различные алгоритмы голосования
- **Система обмена знаниями** для накопления коллективного опыта
- **Асинхронное взаимодействие** через шину сообщений
- **Автоматическое масштабирование** роя в зависимости от нагрузки
- **Мониторинг производительности** и анализ эмерджентного поведения

## 🏗️ Архитектура системы

### Основные компоненты

- **Agent**: Базовый класс агента с возможностями обработки задач
- **SwarmManager**: Менеджер роя для координации агентов
- **MessageBus**: Система обмена сообщениями между агентами
- **TaskDistributor**: Интеллектуальный распределитель задач
- **CollectiveIntelligence**: Алгоритмы коллективного принятия решений

### Принципы работы

- **Автономность**: Каждый агент принимает локальные решения
- **Коллаборация**: Агенты взаимодействуют для достижения общих целей
- **Адаптивность**: Система адаптируется к изменяющимся условиям
- **Самоорганизация**: Эмерджентное поведение через простые правила взаимодействия

## 🚀 Установка и настройка

### Системные требования

- Python 3.8+
- Поддержка asyncio

### Установка зависимостей

```bash
pip install -r requirements.txt
```

## 📖 Быстрый старт

### Базовый пример

```python
import asyncio
from swarm import SwarmManager, Agent
from swarm.core.agent import Task

class CodeAnalysisAgent(Agent):
    def __init__(self, agent_id=None, name=None):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["code_analysis", "syntax_check"]
        )

    async def _execute_task_impl(self, task: Task):
        # Реализация анализа кода
        code = task.content.get("code", "")
        return {
            "lines_count": len(code.split('\n')),
            "complexity": "low" if len(code) < 100 else "high"
        }

async def main():
    # Создание и запуск роя
    swarm = SwarmManager()
    await swarm.start()

    # Добавление агентов
    agent = CodeAnalysisAgent(name="Анализатор-1")
    await swarm.add_agent(agent)

    # Создание и выполнение задачи
    task = Task(
        id="analysis_1",
        content={"code": "def hello(): print('Hello, World!')"},
        requirements=["code_analysis"]
    )

    result = await swarm.execute_task(task)
    print(f"Результат: {result.result}")

    # Остановка роя
    await swarm.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Коллективное принятие решений

```python
from swarm.intelligence.collective_intelligence import CollectiveIntelligence, VotingMethod

# Создание системы коллективного интеллекта
ci = CollectiveIntelligence()

# Регистрация агентов
for agent in agents:
    ci.register_agent(agent)

# Принятие коллективного решения
decision = await ci.make_collective_decision(
    question="Какую архитектуру выбрать?",
    options=["Монолитная", "Микросервисы", "Гибридная"],
    method=VotingMethod.WEIGHTED
)

print(f"Решение: {decision.decision} (уверенность: {decision.confidence:.2%})")
```

## 📚 Примеры использования

В папке `examples/` представлены подробные примеры:

- **basic_swarm.py**: Базовое использование системы
- **collective_decision_making.py**: Коллективное принятие решений
- **advanced_swarm_programming.py**: Сложный сценарий совместной разработки

Запуск примеров:

```bash
cd examples
python basic_swarm.py
python collective_decision_making.py
python advanced_swarm_programming.py
```

## 🧠 Возможности системы

### Типы агентов

- **Архитекторы**: Проектирование системной архитектуры
- **Разработчики**: Реализация кода (backend/frontend)
- **Тестировщики**: Контроль качества и тестирование
- **Аналитики**: Анализ кода и требований
- **Документаторы**: Создание документации

### Стратегии распределения задач

- **Round Robin**: Циклическое распределение
- **Load Balanced**: Балансировка нагрузки
- **Capability Based**: На основе способностей агентов
- **Performance Based**: На основе производительности
- **Priority Based**: На основе приоритета задач

### Методы коллективных решений

- **Majority**: Простое большинство
- **Weighted**: Взвешенное голосование
- **Consensus**: Достижение консенсуса
- **Borda Count**: Ранжированное голосование

## 🔧 Конфигурация

```python
from swarm.core.swarm_manager import SwarmConfig
from swarm.tasks.task_distributor import DistributionStrategy

config = SwarmConfig(
    max_agents=10,
    task_distribution_strategy=DistributionStrategy.CAPABILITY_BASED,
    auto_scale=True,
    min_agents=2,
    task_timeout=300.0
)

swarm = SwarmManager(config)
```

## 📊 Мониторинг и метрики

Система предоставляет подробную аналитику:

- Производительность отдельных агентов
- Статистика выполнения задач
- Анализ коллективных решений
- Обнаружение эмерджентного поведения
- Динамика репутации агентов

```python
# Получение статистики роя
status = swarm.get_swarm_status()
print(f"Успешность: {status['success_rate']:.1%}")

# Метрики коллективного интеллекта
metrics = collective_intelligence.get_swarm_intelligence_metrics()
print(f"Принято решений: {metrics['decisions_made']}")
```

## 🔬 Исследовательские возможности

Система поддерживает исследования в области:

- Коллективного интеллекта
- Эмерджентного поведения
- Самоорганизующихся систем
- Распределенного решения задач
- Адаптивного поведения агентов

## 🛠️ Расширение системы

### Создание собственных агентов

```python
class CustomAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            capabilities=["custom_capability"],
            **kwargs
        )

    async def _execute_task_impl(self, task: Task):
        # Ваша логика обработки задач
        return {"result": "custom_processing"}
```

### Добавление новых алгоритмов

Система спроектирована для легкого расширения новыми алгоритмами распределения задач, методами голосования и стратегиями взаимодействия агентов.

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 🤝 Вклад в развитие

Мы приветствуем вклад в развитие проекта! Пожалуйста, ознакомьтесь с руководством по внесению изменений.

## 📞 Поддержка

Если у вас есть вопросы или предложения, создайте issue в репозитории проекта.

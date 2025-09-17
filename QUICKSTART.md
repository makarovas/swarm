# Быстрый старт

## 🚀 Запуск системы за 5 минут

### 1. Проверка зависимостей

```bash
python3 --version  # Должен быть Python 3.8+
```

### 2. Запуск интерактивного меню

```bash
python3 run_examples.py
```

Выберите пример из меню:

- `1` - Базовый пример работы роя
- `2` - Коллективное принятие решений
- `3` - Продвинутый сценарий разработки
- `4` - Запустить все примеры подряд

### 3. Простейший код

```python
import asyncio
from swarm import SwarmManager, Agent
from swarm.core.agent import Task

# Создайте собственного агента
class MyAgent(Agent):
    async def _execute_task_impl(self, task: Task):
        return f"Обработано: {task.content}"

async def main():
    # Создание и запуск роя
    swarm = SwarmManager()
    await swarm.start()

    # Добавление агента
    agent = MyAgent(name="МойАгент", capabilities=["обработка"])
    await swarm.add_agent(agent)

    # Выполнение задачи
    task = Task(
        id="моя_задача",
        content="Привет, мир!",
        requirements=["обработка"]
    )

    result = await swarm.execute_task(task)
    print(f"Результат: {result.result}")

    await swarm.stop()

asyncio.run(main())
```

## 📖 Основные концепции

### Агенты

- Автономные единицы выполнения задач
- Имеют способности (capabilities)
- Могут общаться друг с другом

### Рой (Swarm)

- Координирует работу агентов
- Распределяет задачи
- Собирает статистику

### Задачи (Tasks)

- Единицы работы для агентов
- Имеют требования к способностям
- Выполняются асинхронно

### Коллективный интеллект

- Принятие решений голосованием
- Обмен знаниями между агентами
- Анализ эмерджентного поведения

## 🔧 Настройка

```python
from swarm.core.swarm_manager import SwarmConfig
from swarm.tasks.task_distributor import DistributionStrategy

config = SwarmConfig(
    max_agents=5,
    task_distribution_strategy=DistributionStrategy.LOAD_BALANCED,
    auto_scale=True
)

swarm = SwarmManager(config)
```

## 📊 Мониторинг

```python
# Статистика роя
status = swarm.get_swarm_status()
print(f"Агентов: {status['agents_count']}")
print(f"Успешность: {status['success_rate']:.1%}")

# Список агентов
agents = swarm.get_agent_list()
for agent in agents:
    print(f"{agent['name']}: {agent['state']}")
```

## 🎯 Следующие шаги

1. Изучите примеры в папке `examples/`
2. Прочитайте `ARCHITECTURE.md` для понимания устройства
3. Создайте собственных агентов для ваших задач
4. Экспериментируйте с разными стратегиями распределения

Удачи в исследовании роевого программирования! 🐝

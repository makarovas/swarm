"""
Продвинутый пример роевого программирования:
Совместная разработка программного модуля
"""

import asyncio
import logging
import random
from typing import Dict, Any
from swarm import SwarmManager, Agent
from swarm.core.agent import Task
from swarm.core.swarm_manager import SwarmConfig
from swarm.tasks.task_distributor import DistributionStrategy


class ArchitectAgent(Agent):
    """Агент-архитектор, проектирующий структуру системы"""
    
    def __init__(self, agent_id=None, name=None):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["system_design", "architecture_review"],
            max_concurrent_tasks=1
        )
        
    async def _execute_task_impl(self, task: Task):
        """Выполнение архитектурных задач"""
        
        if "system_design" in task.requirements:
            requirements = task.content.get("requirements", "")
            
            # Симуляция проектирования архитектуры
            await asyncio.sleep(random.uniform(2, 4))
            
            architecture = {
                "components": [
                    "UserInterface",
                    "BusinessLogic", 
                    "DataAccess",
                    "ExternalAPI"
                ],
                "patterns": ["MVC", "Repository", "Factory"],
                "technologies": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
                "estimated_complexity": random.choice(["low", "medium", "high"]),
                "development_time_weeks": random.randint(2, 8)
            }
            
            return architecture
            
        elif "architecture_review" in task.requirements:
            code_structure = task.content.get("code_structure", {})
            
            await asyncio.sleep(random.uniform(1, 2))
            
            review = {
                "score": random.uniform(0.7, 0.95),
                "issues": random.choice([
                    [],
                    ["Слишком сильная связанность между компонентами"],
                    ["Нарушение принципа единственной ответственности"],
                    ["Отсутствие абстракций для внешних зависимостей"]
                ]),
                "recommendations": [
                    "Добавить интерфейсы для лучшей тестируемости",
                    "Использовать dependency injection",
                    "Разделить большие классы на более мелкие"
                ]
            }
            
            return review


class DeveloperAgent(Agent):
    """Агент-разработчик, реализующий код"""
    
    def __init__(self, agent_id=None, name=None, specialization="backend"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["code_implementation", "refactoring"],
            max_concurrent_tasks=2
        )
        self.specialization = specialization
        
    async def _execute_task_impl(self, task: Task):
        """Выполнение задач разработки"""
        
        if "code_implementation" in task.requirements:
            component = task.content.get("component", "")
            spec = task.content.get("specification", {})
            
            # Симуляция написания кода
            complexity = spec.get("complexity", "medium")
            base_time = {"low": 1, "medium": 3, "high": 5}[complexity]
            await asyncio.sleep(random.uniform(base_time, base_time * 2))
            
            # Генерация результата на основе специализации
            if self.specialization == "backend":
                code = f'''
class {component}:
    """Реализация компонента {component}"""
    
    def __init__(self, config: dict):
        self.config = config
        self.initialized = False
        
    async def initialize(self):
        """Инициализация компонента"""
        # Инициализация ресурсов
        self.initialized = True
        
    async def process(self, data: dict) -> dict:
        """Основная логика обработки"""
        if not self.initialized:
            await self.initialize()
            
        # Обработка данных
        result = {{"status": "success", "data": data}}
        return result
'''
            else:  # frontend
                code = f'''
class {component}Component {{
    constructor(props) {{
        this.props = props;
        this.state = {{}};
    }}
    
    async componentDidMount() {{
        // Инициализация компонента
        await this.loadData();
    }}
    
    async loadData() {{
        // Загрузка данных
        const data = await api.fetchData();
        this.setState({{ data }});
    }}
    
    render() {{
        return `<div>${{component}} Component</div>`;
    }}
}}
'''
            
            implementation = {
                "component": component,
                "code": code.strip(),
                "lines_of_code": len(code.strip().split('\n')),
                "complexity_score": random.uniform(0.3, 0.8),
                "test_coverage": random.uniform(0.7, 0.95),
                "specialization": self.specialization
            }
            
            return implementation
            
        elif "refactoring" in task.requirements:
            existing_code = task.content.get("code", "")
            issues = task.content.get("issues", [])
            
            await asyncio.sleep(random.uniform(1, 3))
            
            refactoring = {
                "issues_addressed": len(issues),
                "improvements": [
                    "Улучшена читаемость кода",
                    "Уменьшена цикломатическая сложность",
                    "Добавлены типы аннотации"
                ],
                "performance_gain": random.uniform(0.1, 0.3),
                "maintainability_score": random.uniform(0.8, 0.95)
            }
            
            return refactoring


class QualityAssuranceAgent(Agent):
    """Агент контроля качества"""
    
    def __init__(self, agent_id=None, name=None):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["code_review", "testing", "quality_analysis"],
            max_concurrent_tasks=3
        )
        
    async def _execute_task_impl(self, task: Task):
        """Выполнение задач контроля качества"""
        
        if "code_review" in task.requirements:
            code = task.content.get("code", "")
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Анализ качества кода
            issues = []
            if random.random() < 0.3:  # 30% вероятность найти проблемы
                issues = random.sample([
                    "Отсутствуют docstrings",
                    "Слишком длинные методы",
                    "Не используются type hints",
                    "Магические числа в коде",
                    "Дублирование кода"
                ], random.randint(1, 3))
                
            review = {
                "overall_score": random.uniform(0.6, 0.95),
                "issues": issues,
                "suggestions": [
                    "Добавить документацию к методам",
                    "Разбить сложные методы на более простые",
                    "Использовать константы вместо магических чисел"
                ],
                "approved": len(issues) == 0
            }
            
            return review
            
        elif "testing" in task.requirements:
            component = task.content.get("component", "")
            code = task.content.get("code", "")
            
            await asyncio.sleep(random.uniform(2, 4))
            
            # Симуляция тестирования
            test_results = {
                "unit_tests": {
                    "total": random.randint(5, 15),
                    "passed": random.randint(4, 15),
                    "failed": random.randint(0, 2)
                },
                "integration_tests": {
                    "total": random.randint(2, 8),
                    "passed": random.randint(2, 8),
                    "failed": random.randint(0, 1)
                },
                "coverage": random.uniform(0.75, 0.98),
                "performance_tests": {
                    "avg_response_time_ms": random.randint(50, 300),
                    "memory_usage_mb": random.randint(10, 100)
                }
            }
            
            return test_results


async def collaborative_development_scenario():
    """Сценарий совместной разработки программного модуля"""
    
    print("🏗️  Сценарий совместной разработки программного модуля\n")
    
    # Конфигурация роя для разработки
    config = SwarmConfig(
        max_agents=8,
        task_distribution_strategy=DistributionStrategy.CAPABILITY_BASED,
        auto_scale=True,
        min_agents=3,
        task_timeout=60.0
    )
    
    # Создание менеджера роя
    swarm = SwarmManager(config)
    
    try:
        print("🚀 Запуск роя разработчиков...")
        await swarm.start()
        
        # Создание команды разработки
        development_team = [
            ArchitectAgent(name="Главный-Архитектор"),
            DeveloperAgent(name="Backend-Dev-1", specialization="backend"),
            DeveloperAgent(name="Backend-Dev-2", specialization="backend"),
            DeveloperAgent(name="Frontend-Dev-1", specialization="frontend"),
            QualityAssuranceAgent(name="QA-Lead"),
            QualityAssuranceAgent(name="QA-Tester")
        ]
        
        # Добавление агентов в рой
        for agent in development_team:
            await swarm.add_agent(agent)
            print(f"👨‍💻 Добавлен в команду: {agent.name}")
            
        print()
        
        # Этап 1: Проектирование архитектуры
        print("📐 Этап 1: Проектирование архитектуры")
        
        architecture_task = Task(
            id="architecture_design",
            content={
                "requirements": "Создать веб-приложение для управления задачами с API и веб-интерфейсом"
            },
            requirements=["system_design"],
            priority=5
        )
        
        arch_result = await swarm.execute_task(architecture_task)
        
        if arch_result.success:
            architecture = arch_result.result
            print(f"✅ Архитектура спроектирована:")
            print(f"   Компоненты: {', '.join(architecture['components'])}")
            print(f"   Паттерны: {', '.join(architecture['patterns'])}")
            print(f"   Технологии: {', '.join(architecture['technologies'])}")
            print(f"   Сложность: {architecture['estimated_complexity']}")
            print(f"   Время разработки: {architecture['development_time_weeks']} недель")
        else:
            print(f"❌ Ошибка проектирования: {arch_result.error_message}")
            return
            
        print()
        
        # Этап 2: Параллельная разработка компонентов
        print("⚡ Этап 2: Параллельная разработка компонентов")
        
        components = architecture["components"]
        development_tasks = []
        
        for i, component in enumerate(components):
            task = Task(
                id=f"implement_{component.lower()}",
                content={
                    "component": component,
                    "specification": {
                        "complexity": architecture["estimated_complexity"],
                        "patterns": architecture["patterns"]
                    }
                },
                requirements=["code_implementation"],
                priority=3
            )
            development_tasks.append(task)
            
        # Выполнение разработки параллельно
        dev_results = await swarm.execute_tasks_batch(development_tasks)
        
        implemented_components = {}
        for result in dev_results:
            if result.success:
                impl = result.result
                component_name = impl["component"]
                implemented_components[component_name] = impl
                print(f"✅ {component_name} реализован ({impl['lines_of_code']} строк, покрытие: {impl['test_coverage']:.1%})")
            else:
                print(f"❌ Ошибка реализации: {result.error_message}")
                
        print()
        
        # Этап 3: Контроль качества
        print("🔍 Этап 3: Контроль качества")
        
        qa_tasks = []
        for component_name, implementation in implemented_components.items():
            # Код-ревью
            review_task = Task(
                id=f"review_{component_name.lower()}",
                content={
                    "code": implementation["code"],
                    "component": component_name
                },
                requirements=["code_review"],
                priority=2
            )
            qa_tasks.append(review_task)
            
            # Тестирование
            test_task = Task(
                id=f"test_{component_name.lower()}",
                content={
                    "component": component_name,
                    "code": implementation["code"]
                },
                requirements=["testing"],
                priority=2
            )
            qa_tasks.append(test_task)
            
        # Выполнение контроля качества
        qa_results = await swarm.execute_tasks_batch(qa_tasks)
        
        reviews = {}
        test_results = {}
        
        for result in qa_results:
            if result.success:
                task_id = result.task_id
                if "review_" in task_id:
                    component = task_id.replace("review_", "").replace("_", "")
                    reviews[component] = result.result
                elif "test_" in task_id:
                    component = task_id.replace("test_", "").replace("_", "")
                    test_results[component] = result.result
                    
        # Отчет по качеству
        print("📊 Результаты контроля качества:")
        for component in implemented_components:
            comp_key = component.lower()
            
            if comp_key in reviews:
                review = reviews[comp_key]
                status = "✅ Одобрено" if review["approved"] else "⚠️  Требует доработки"
                print(f"   {component}: {status} (оценка: {review['overall_score']:.1%})")
                if review["issues"]:
                    print(f"      Проблемы: {', '.join(review['issues'])}")
                    
            if comp_key in test_results:
                tests = test_results[comp_key]
                unit_passed = tests["unit_tests"]["passed"]
                unit_total = tests["unit_tests"]["total"]
                print(f"      Тесты: {unit_passed}/{unit_total} unit-тестов прошли, покрытие: {tests['coverage']:.1%}")
                
        print()
        
        # Этап 4: Анализ результатов разработки
        print("📈 Этап 4: Анализ результатов разработки")
        
        swarm_status = swarm.get_swarm_status()
        agent_stats = swarm.get_agent_list()
        
        print(f"Общая статистика роя:")
        print(f"   Обработано задач: {swarm_status['total_tasks_processed']}")
        print(f"   Успешно выполнено: {swarm_status['successful_tasks']}")
        print(f"   Процент успеха: {swarm_status['success_rate']:.1%}")
        print(f"   Время разработки: {swarm_status['uptime']:.1f} секунд")
        
        print(f"\nПроизводительность команды:")
        for agent_info in agent_stats:
            agent_name = agent_info["name"]
            metrics = agent_info["metrics"]
            print(f"   {agent_name}:")
            print(f"     Выполнено задач: {metrics['total_tasks']}")
            print(f"     Процент успеха: {metrics['success_rate']:.1%}")
            print(f"     Среднее время: {metrics['average_execution_time']:.1f}с")
            
        # Оценка качества итогового продукта
        total_coverage = sum(impl["test_coverage"] for impl in implemented_components.values()) / len(implemented_components)
        avg_quality_score = sum(review["overall_score"] for review in reviews.values()) / len(reviews) if reviews else 0
        
        print(f"\nКачество итогового продукта:")
        print(f"   Среднее покрытие тестами: {total_coverage:.1%}")
        print(f"   Средняя оценка качества кода: {avg_quality_score:.1%}")
        print(f"   Компонентов реализовано: {len(implemented_components)}/{len(components)}")
        
        # Определение готовности к релизу
        ready_for_release = (
            swarm_status['success_rate'] > 0.8 and
            total_coverage > 0.8 and
            avg_quality_score > 0.7 and
            len(implemented_components) == len(components)
        )
        
        if ready_for_release:
            print("\n🎉 Проект готов к релизу!")
        else:
            print("\n⚠️  Проект требует дополнительной работы перед релизом")
            
    except Exception as e:
        print(f"❌ Ошибка в процессе разработки: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🛑 Завершение работы роя...")
        await swarm.stop()
        print("✅ Рой остановлен")


async def main():
    """Главная функция"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.ERROR,  # Минимум логов для чистоты вывода
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        await collaborative_development_scenario()
        
    except KeyboardInterrupt:
        print("\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

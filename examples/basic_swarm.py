"""
Базовый пример использования системы роевого программирования
"""

import asyncio
import logging
from swarm import SwarmManager, Agent
from swarm.core.agent import Task


class CodeAnalysisAgent(Agent):
    """Агент для анализа кода"""
    
    def __init__(self, agent_id=None, name=None):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["code_analysis", "syntax_check"],
            max_concurrent_tasks=2
        )
        
    async def _execute_task_impl(self, task: Task):
        """Реализация выполнения задачи анализа кода"""
        
        if "code_analysis" in task.requirements:
            # Симуляция анализа кода
            code = task.content.get("code", "")
            
            await asyncio.sleep(1)  # Симуляция времени обработки
            
            # Простой анализ
            analysis = {
                "lines_count": len(code.split('\n')),
                "has_functions": "def " in code,
                "has_classes": "class " in code,
                "complexity": "low" if len(code) < 100 else "medium" if len(code) < 500 else "high"
            }
            
            return analysis
            
        elif "syntax_check" in task.requirements:
            # Симуляция проверки синтаксиса
            code = task.content.get("code", "")
            
            await asyncio.sleep(0.5)
            
            # Простая проверка синтаксиса
            try:
                compile(code, '<string>', 'exec')
                return {"syntax_valid": True, "errors": []}
            except SyntaxError as e:
                return {"syntax_valid": False, "errors": [str(e)]}
                
        else:
            raise ValueError("Неподдерживаемый тип задачи")


class TestingAgent(Agent):
    """Агент для тестирования"""
    
    def __init__(self, agent_id=None, name=None):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["unit_testing", "integration_testing"],
            max_concurrent_tasks=1
        )
        
    async def _execute_task_impl(self, task: Task):
        """Реализация выполнения задачи тестирования"""
        
        if "unit_testing" in task.requirements:
            # Симуляция юнит-тестирования
            code = task.content.get("code", "")
            
            await asyncio.sleep(2)  # Симуляция времени тестирования
            
            # Простое тестирование
            test_results = {
                "tests_run": 5,
                "tests_passed": 4,
                "tests_failed": 1,
                "coverage": 85.0,
                "failures": ["test_edge_case: AssertionError"]
            }
            
            return test_results
            
        elif "integration_testing" in task.requirements:
            # Симуляция интеграционного тестирования
            await asyncio.sleep(3)
            
            return {
                "integration_tests": 3,
                "passed": 3,
                "failed": 0,
                "response_time_avg": 150  # мс
            }
            
        else:
            raise ValueError("Неподдерживаемый тип задачи")


class DocumentationAgent(Agent):
    """Агент для создания документации"""
    
    def __init__(self, agent_id=None, name=None):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["doc_generation", "api_docs"],
            max_concurrent_tasks=1
        )
        
    async def _execute_task_impl(self, task: Task):
        """Реализация выполнения задачи создания документации"""
        
        if "doc_generation" in task.requirements:
            # Симуляция создания документации
            code = task.content.get("code", "")
            
            await asyncio.sleep(1.5)
            
            # Анализ кода для создания документации
            functions = code.count("def ")
            classes = code.count("class ")
            
            documentation = {
                "summary": f"Модуль содержит {functions} функций и {classes} классов",
                "functions_documented": functions,
                "classes_documented": classes,
                "doc_format": "markdown",
                "completeness": 90.0
            }
            
            return documentation
            
        else:
            raise ValueError("Неподдерживаемый тип задачи")


async def main():
    """Основная функция демонстрации"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создание менеджера роя
    swarm = SwarmManager()
    
    try:
        # Запуск роя
        print("🚀 Запуск системы роевого программирования...")
        await swarm.start()
        
        # Создание агентов
        print("👥 Создание агентов...")
        agents = [
            CodeAnalysisAgent(name="Анализатор-1"),
            CodeAnalysisAgent(name="Анализатор-2"),
            TestingAgent(name="Тестировщик-1"),
            DocumentationAgent(name="Документатор-1")
        ]
        
        # Добавление агентов в рой
        for agent in agents:
            await swarm.add_agent(agent)
            print(f"✅ Добавлен агент: {agent.name}")
            
        # Демонстрационный код для анализа
        sample_code = '''
def calculate_factorial(n):
    """Вычисляет факториал числа"""
    if n < 0:
        raise ValueError("Факториал отрицательного числа не определен")
    if n == 0 or n == 1:
        return 1
    return n * calculate_factorial(n - 1)

class Calculator:
    """Простой калькулятор"""
    
    def add(self, a, b):
        return a + b
        
    def multiply(self, a, b):
        return a * b
'''
        
        # Создание задач
        print("\n📋 Создание задач...")
        
        tasks = [
            Task(
                id="analysis_1",
                content={"code": sample_code},
                requirements=["code_analysis"],
                priority=3
            ),
            Task(
                id="syntax_check_1",
                content={"code": sample_code},
                requirements=["syntax_check"],
                priority=2
            ),
            Task(
                id="testing_1",
                content={"code": sample_code},
                requirements=["unit_testing"],
                priority=2
            ),
            Task(
                id="documentation_1",
                content={"code": sample_code},
                requirements=["doc_generation"],
                priority=1
            )
        ]
        
        # Выполнение задач
        print("⚡ Выполнение задач...")
        results = await swarm.execute_tasks_batch(tasks)
        
        # Вывод результатов
        print("\n📊 Результаты выполнения:")
        for result in results:
            status = "✅ Успешно" if result.success else "❌ Ошибка"
            print(f"{status} - Задача {result.task_id} (Агент: {result.agent_id})")
            print(f"   Время выполнения: {result.execution_time:.2f}с")
            
            if result.success and result.result:
                print(f"   Результат: {result.result}")
            elif not result.success:
                print(f"   Ошибка: {result.error_message}")
            print()
            
        # Статистика роя
        print("📈 Статистика роя:")
        swarm_status = swarm.get_swarm_status()
        print(f"   Агентов в рое: {swarm_status['agents_count']}")
        print(f"   Обработано задач: {swarm_status['total_tasks_processed']}")
        print(f"   Успешных задач: {swarm_status['successful_tasks']}")
        print(f"   Процент успеха: {swarm_status['success_rate']:.1%}")
        print(f"   Время работы: {swarm_status['uptime']:.1f}с")
        
        # Информация об агентах
        print("\n🤖 Информация об агентах:")
        agents_info = swarm.get_agent_list()
        for agent_info in agents_info:
            print(f"   {agent_info['name']} ({agent_info['id'][:8]}...)")
            print(f"     Состояние: {agent_info['state']}")
            print(f"     Способности: {', '.join(agent_info['capabilities'])}")
            print(f"     Активных задач: {agent_info['current_tasks']}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        
    finally:
        # Остановка роя
        print("\n🛑 Остановка роя...")
        await swarm.stop()
        print("✅ Рой остановлен")


if __name__ == "__main__":
    asyncio.run(main())

"""
Пример использования AI-агентов в системе роевого программирования
"""

import asyncio
import logging
import os
from swarm import SwarmManager, Task
from swarm.agents import OpenAIAgent, AnthropicAgent, LocalLLMAgent, MultiAIAgent, MultiAIConfig


async def demonstrate_ai_agents():
    """Демонстрация работы различных AI-агентов"""
    
    print("🤖 Демонстрация AI-агентов в роевом программировании\n")
    
    # Создание менеджера роя
    swarm = SwarmManager()
    await swarm.start()
    
    try:
        # Создание различных AI-агентов
        ai_agents = []
        
        # 1. OpenAI агент (если есть API ключ)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            openai_agent = OpenAIAgent(
                api_key=openai_key,
                model_name="gpt-3.5-turbo",
                name="GPT-Аналитик",
                system_prompt="Ты специалист по анализу кода и архитектуре ПО."
            )
            await swarm.add_agent(openai_agent)
            ai_agents.append(("OpenAI GPT", openai_agent))
            print("✅ OpenAI агент добавлен в рой")
        else:
            print("⚠️  OpenAI API ключ не найден (установите OPENAI_API_KEY)")
            
        # 2. Anthropic агент (если есть API ключ)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            anthropic_agent = AnthropicAgent(
                api_key=anthropic_key,
                model_name="claude-3-sonnet-20240229",
                name="Claude-Ревьювер",
                system_prompt="Ты эксперт по безопасности кода и этичному программированию."
            )
            await swarm.add_agent(anthropic_agent)
            ai_agents.append(("Anthropic Claude", anthropic_agent))
            print("✅ Anthropic агент добавлен в рой")
        else:
            print("⚠️  Anthropic API ключ не найден (установите ANTHROPIC_API_KEY)")
            
        # 3. Локальный агент (всегда доступен)
        local_agent = LocalLLMAgent(
            model_name="llama2",
            base_url="http://localhost:11434",  # Ollama по умолчанию
            name="Local-LLM",
            system_prompt="Ты локальный AI-ассистент для приватной обработки кода."
        )
        await swarm.add_agent(local_agent)
        ai_agents.append(("Local LLM", local_agent))
        print("✅ Локальный агент добавлен в рой")
        
        # 4. Мульти-AI агент (использует несколько моделей)
        if len(ai_agents) > 1:
            multi_config = MultiAIConfig(
                primary_model="openai" if openai_key else "local",
                fallback_models=["anthropic", "local"] if anthropic_key else ["local"],
                use_voting=True,
                parallel_processing=True
            )
            
            multi_agent = MultiAIAgent(
                multi_config=multi_config,
                openai_config={"api_key": openai_key} if openai_key else None,
                anthropic_config={"api_key": anthropic_key} if anthropic_key else None,
                local_config={"model_name": "llama2"},
                name="Multi-AI-Консенсус"
            )
            await swarm.add_agent(multi_agent)
            ai_agents.append(("Multi-AI", multi_agent))
            print("✅ Мульти-AI агент добавлен в рой")
            
        print(f"\n🎯 Создано {len(ai_agents)} AI-агентов\n")
        
        # Тестовые задачи для AI-агентов
        test_tasks = [
            {
                "name": "Анализ качества кода",
                "task": Task(
                    id="code_analysis_test",
                    content={
                        "code": '''
def calculate_factorial(n):
    if n < 0:
        return None
    elif n == 0:
        return 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
''',
                        "description": "Проанализировать качество и производительность кода"
                    },
                    requirements=["code_analysis", "ai_processing"]
                )
            },
            {
                "name": "Генерация кода",
                "task": Task(
                    id="code_generation_test",
                    content={
                        "specification": "Создать класс для работы с очередью задач с приоритетами",
                        "language": "python",
                        "description": "Сгенерировать чистый, документированный код"
                    },
                    requirements=["code_generation", "ai_processing"]
                )
            },
            {
                "name": "Отладка кода",
                "task": Task(
                    id="debugging_test",
                    content={
                        "code": '''
def divide_numbers(a, b):
    return a / b

def process_list(numbers):
    results = []
    for num in numbers:
        result = divide_numbers(num, 0)
        results.append(result)
    return results
''',
                        "error": "ZeroDivisionError при выполнении",
                        "description": "Найти и исправить ошибку в коде"
                    },
                    requirements=["code_analysis", "problem_solving", "ai_processing"]
                )
            }
        ]
        
        # Выполнение задач
        for task_info in test_tasks:
            print(f"🔍 Выполнение задачи: {task_info['name']}")
            print("-" * 50)
            
            # Выполняем задачу в рое
            result = await swarm.execute_task(task_info["task"])
            
            if result.success:
                print(f"✅ Задача выполнена агентом: {result.agent_id}")
                print(f"⏱️  Время выполнения: {result.execution_time:.2f}с")
                
                # Показываем результат
                if isinstance(result.result, dict):
                    ai_response = result.result.get("ai_response", "")
                    model_used = result.result.get("model_used", "unknown")
                    confidence = result.result.get("confidence", 0)
                    
                    print(f"🤖 Модель: {model_used}")
                    print(f"📊 Уверенность: {confidence:.1%}")
                    print(f"💬 Ответ:\n{ai_response[:300]}...")
                    
                    # Дополнительная информация для мульти-AI
                    if "consensus_achieved" in result.result:
                        consensus = result.result["consensus_achieved"]
                        models = result.result.get("participating_models", [])
                        print(f"🎯 Консенсус: {'Да' if consensus else 'Нет'}")
                        print(f"🤝 Участвующие модели: {', '.join(models)}")
                        
                else:
                    print(f"📝 Результат: {result.result}")
                    
            else:
                print(f"❌ Ошибка: {result.error_message}")
                
            print("\n" + "="*60 + "\n")
            
        # Статистика AI-агентов
        print("📊 Статистика AI-агентов:")
        print("-" * 30)
        
        agent_list = swarm.get_agent_list()
        for agent_info in agent_list:
            if "AI" in agent_info["name"] or "GPT" in agent_info["name"] or "Claude" in agent_info["name"]:
                metrics = agent_info["metrics"]
                print(f"🤖 {agent_info['name']}:")
                print(f"   Выполнено задач: {metrics['total_tasks']}")
                print(f"   Процент успеха: {metrics['success_rate']:.1%}")
                print(f"   Среднее время: {metrics['average_execution_time']:.1f}с")
                
                # Дополнительные AI метрики
                if hasattr(swarm.agents.get(agent_info['id']), 'get_ai_metrics'):
                    ai_metrics = swarm.agents[agent_info['id']].get_ai_metrics()
                    if "total_tokens_used" in ai_metrics:
                        print(f"   Использовано токенов: {ai_metrics['total_tokens_used']}")
                    if "cost_estimate" in ai_metrics:
                        print(f"   Примерная стоимость: ${ai_metrics['cost_estimate']:.4f}")
                        
                print()
                
        # Демонстрация специализированных методов
        print("🎯 Демонстрация специализированных методов:\n")
        
        for agent_name, agent in ai_agents:
            if hasattr(agent, 'analyze_code_quality'):
                print(f"🔍 {agent_name} - анализ качества кода:")
                try:
                    quality_result = await agent.analyze_code_quality('''
def hello_world():
    print("Hello, World!")
    return True
''')
                    print(f"   Результат: {quality_result.get('ai_response', 'N/A')[:100]}...")
                except Exception as e:
                    print(f"   Ошибка: {e}")
                print()
                
        # Проверка доступности локальных моделей
        print("🏠 Проверка локальных моделей:")
        if hasattr(local_agent, 'check_model_availability'):
            availability = await local_agent.check_model_availability()
            status = "✅ Доступна" if availability["available"] else "❌ Недоступна"
            print(f"   Ollama: {status}")
            if not availability["available"]:
                print(f"   Причина: {availability.get('error', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🛑 Остановка роя...")
        await swarm.stop()
        print("✅ Рой остановлен")


async def main():
    """Главная функция"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.WARNING,  # Уменьшаем шум в логах
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Система AI-агентов для роевого программирования")
    print("=" * 60)
    print()
    print("💡 Для полной функциональности установите переменные окружения:")
    print("   export OPENAI_API_KEY='your-openai-key'")
    print("   export ANTHROPIC_API_KEY='your-anthropic-key'")
    print("   И запустите Ollama для локальных моделей")
    print()
    
    try:
        await demonstrate_ai_agents()
        
    except KeyboardInterrupt:
        print("\n⏹️  Прервано пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

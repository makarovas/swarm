"""
Пример коллективного принятия решений в рое
"""

import asyncio
import logging
import random
from swarm import SwarmManager, Agent
from swarm.core.agent import Task
from swarm.intelligence.collective_intelligence import CollectiveIntelligence, VotingMethod


class DecisionMakingAgent(Agent):
    """Агент, способный принимать решения"""
    
    def __init__(self, agent_id=None, name=None, decision_style="balanced"):
        super().__init__(
            agent_id=agent_id,
            name=name,
            capabilities=["decision_making", "analysis"],
            max_concurrent_tasks=1
        )
        self.decision_style = decision_style  # balanced, conservative, aggressive
        
    async def _execute_task_impl(self, task: Task):
        """Выполнение задачи"""
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Симуляция обработки
        return {"status": "completed", "agent_style": self.decision_style}
        
    async def handle_message(self, message_type: str, content, sender_id: str):
        """Обработка сообщений, включая запросы на голосование"""
        
        if message_type == "vote_request":
            return await self._handle_vote_request(content)
        else:
            return await super().handle_message(message_type, content, sender_id)
            
    async def _handle_vote_request(self, vote_content):
        """Обработка запроса на голосование"""
        question = vote_content.get("question", "")
        options = vote_content.get("options", [])
        
        if not options:
            return {"option": None, "confidence": 0.0, "reasoning": "Нет вариантов для выбора"}
            
        # Симуляция времени на размышление
        await asyncio.sleep(random.uniform(0.1, 1.0))
        
        # Выбор варианта в зависимости от стиля принятия решений
        if self.decision_style == "conservative":
            # Консервативный агент предпочитает первый (безопасный) вариант
            chosen_option = options[0]
            confidence = random.uniform(0.7, 0.9)
            reasoning = "Выбираю консервативный подход"
            
        elif self.decision_style == "aggressive":
            # Агрессивный агент предпочитает последний (рискованный) вариант
            chosen_option = options[-1]
            confidence = random.uniform(0.6, 0.8)
            reasoning = "Выбираю более агрессивную стратегию"
            
        else:  # balanced
            # Сбалансированный агент делает взвешенный выбор
            if "код" in question.lower():
                # Для вопросов о коде выбираем средние варианты
                chosen_option = options[len(options) // 2] if len(options) > 2 else options[0]
                confidence = random.uniform(0.8, 0.95)
                reasoning = "Выбираю сбалансированное решение на основе анализа"
            else:
                # Для других вопросов случайный выбор
                chosen_option = random.choice(options)
                confidence = random.uniform(0.5, 0.8)
                reasoning = "Выбор на основе общих принципов"
                
        return {
            "option": chosen_option,
            "confidence": confidence,
            "reasoning": reasoning
        }


async def demonstrate_collective_decisions():
    """Демонстрация коллективного принятия решений"""
    
    print("🧠 Демонстрация коллективного принятия решений\n")
    
    # Создание системы коллективного интеллекта
    collective_intelligence = CollectiveIntelligence()
    
    # Создание агентов с разными стилями принятия решений
    agents = [
        DecisionMakingAgent(name="Консерватор-1", decision_style="conservative"),
        DecisionMakingAgent(name="Консерватор-2", decision_style="conservative"),
        DecisionMakingAgent(name="Агрессор-1", decision_style="aggressive"),
        DecisionMakingAgent(name="Балансир-1", decision_style="balanced"),
        DecisionMakingAgent(name="Балансир-2", decision_style="balanced"),
    ]
    
    # Регистрация агентов
    for agent in agents:
        collective_intelligence.register_agent(agent)
        print(f"✅ Зарегистрирован агент: {agent.name} ({agent.decision_style})")
        
    print()
    
    # Набор вопросов для голосования
    voting_scenarios = [
        {
            "question": "Какую архитектуру выбрать для нового проекта?",
            "options": ["Монолитная", "Микросервисы", "Гибридная"],
            "method": VotingMethod.MAJORITY
        },
        {
            "question": "Какой подход к тестированию использовать?",
            "options": ["Unit-тесты", "Integration-тесты", "E2E-тесты", "Все типы"],
            "method": VotingMethod.WEIGHTED
        },
        {
            "question": "Выбор языка программирования для backend?",
            "options": ["Python", "Java", "Go", "Node.js"],
            "method": VotingMethod.BORDA_COUNT
        },
        {
            "question": "Стратегия развертывания в production?",
            "options": ["Blue-Green", "Rolling Update", "Canary"],
            "method": VotingMethod.CONSENSUS
        }
    ]
    
    # Проведение голосований
    for i, scenario in enumerate(voting_scenarios, 1):
        print(f"📊 Голосование #{i}: {scenario['question']}")
        print(f"   Варианты: {', '.join(scenario['options'])}")
        print(f"   Метод: {scenario['method'].value}")
        
        try:
            decision = await collective_intelligence.make_collective_decision(
                question=scenario["question"],
                options=scenario["options"],
                method=scenario["method"],
                timeout=10.0
            )
            
            print(f"   🏆 Решение: {decision.decision}")
            print(f"   📈 Уверенность: {decision.confidence:.2%}")
            print(f"   🗳️  Голосов: {len(decision.votes)}")
            
            # Показываем разбивку голосов
            vote_breakdown = {}
            for vote in decision.votes:
                option = vote.option
                if option in vote_breakdown:
                    vote_breakdown[option] += 1
                else:
                    vote_breakdown[option] = 1
                    
            print(f"   📋 Разбивка: {vote_breakdown}")
            
            # Показываем аргументацию
            print("   💭 Аргументация:")
            for vote in decision.votes:
                agent_name = next(a.name for a in agents if a.id == vote.agent_id)
                print(f"      {agent_name}: {vote.option} (уверенность: {vote.confidence:.1%}) - {vote.reasoning}")
                
        except Exception as e:
            print(f"   ❌ Ошибка принятия решения: {e}")
            
        print()
        
    # Демонстрация обмена знаниями
    print("📚 Демонстрация обмена знаниями:")
    
    # Агенты делятся знаниями
    knowledge_items = [
        ("best_practices", "Использовать type hints в Python", agents[0].id, 0.9),
        ("performance", "Индексы ускоряют поиск в БД", agents[1].id, 0.95),
        ("security", "Всегда валидировать пользовательский ввод", agents[2].id, 0.85),
        ("best_practices", "Использовать type hints в Python", agents[3].id, 0.8),  # Подтверждение
        ("testing", "Mock внешние зависимости в тестах", agents[4].id, 0.9),
    ]
    
    for key, value, agent_id, confidence in knowledge_items:
        await collective_intelligence.share_knowledge(agent_id, key, value, confidence)
        agent_name = next(a.name for a in agents if a.id == agent_id)
        print(f"   📝 {agent_name} поделился знанием: '{key}' = '{value}'")
        
    print()
    
    # Проверка коллективного знания
    print("🔍 Проверка коллективного знания:")
    for key in ["best_practices", "performance", "security", "testing"]:
        knowledge = collective_intelligence.get_collective_knowledge(key)
        if knowledge:
            print(f"   ✅ {key}: {knowledge}")
        else:
            print(f"   ❌ {key}: знание не подтверждено коллективом")
            
    # Показываем метрики роевого интеллекта
    print("\n📊 Метрики роевого интеллекта:")
    metrics = collective_intelligence.get_swarm_intelligence_metrics()
    print(f"   Агентов: {metrics['registered_agents']}")
    print(f"   Элементов знаний: {metrics['knowledge_base_size']}")
    print(f"   Принято решений: {metrics['decisions_made']}")
    print(f"   Средняя репутация агентов: {metrics['avg_agent_reputation']:.2f}")
    print(f"   Подтвержденных знаний: {metrics['confirmed_knowledge_items']}")
    
    # Анализ эмерджентного поведения
    print("\n🔬 Анализ эмерджентного поведения:")
    patterns = await collective_intelligence.emergent_behavior_detection()
    
    if "decision_method_preference" in patterns:
        print(f"   Предпочтения в методах принятия решений: {patterns['decision_method_preference']}")
        
    if "confidence_trend" in patterns:
        trend = patterns["confidence_trend"]
        direction = "растет" if trend["increasing"] else "падает"
        print(f"   Тренд уверенности в решениях: {direction} (средняя: {trend['average']:.2%})")
        
    if "reputation_distribution" in patterns:
        rep = patterns["reputation_distribution"]
        print(f"   Распределение репутации: среднее={rep['mean']:.2f}, разброс={rep['std']:.2f}")


async def main():
    """Главная функция"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.WARNING,  # Уменьшаем уровень логирования для чистоты вывода
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        await demonstrate_collective_decisions()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
Алгоритмы коллективного интеллекта для системы роевого программирования
"""

import asyncio
import logging
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import time
import random

from ..core.agent import Agent, TaskResult


class VotingMethod(Enum):
    """Методы голосования"""
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    CONSENSUS = "consensus"
    BORDA_COUNT = "borda_count"


class ConsensusMethod(Enum):
    """Методы достижения консенсуса"""
    SIMPLE = "simple"
    BYZANTINE_FAULT_TOLERANT = "byzantine_fault_tolerant"
    RAFT = "raft"


@dataclass
class Vote:
    """Голос агента"""
    agent_id: str
    option: Any
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    reasoning: Optional[str] = None


@dataclass
class CollectiveDecision:
    """Коллективное решение"""
    decision: Any
    confidence: float
    votes: List[Vote]
    method_used: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeItem:
    """Элемент коллективного знания"""
    key: str
    value: Any
    source_agent: str
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    confirmations: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)


class CollectiveIntelligence:
    """
    Система коллективного интеллекта для роя агентов
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.decision_history: List[CollectiveDecision] = []
        self.agent_reputation: Dict[str, float] = {}
        self.logger = logging.getLogger("CollectiveIntelligence")
        
        # Параметры алгоритмов
        self.consensus_threshold = 0.7
        self.min_votes_for_decision = 2
        self.reputation_decay = 0.95
        self.knowledge_confirmation_threshold = 2
        
    def register_agent(self, agent: Agent):
        """Зарегистрировать агента"""
        self.agents[agent.id] = agent
        self.agent_reputation[agent.id] = 1.0
        self.logger.info(f"Агент {agent.id} зарегистрирован в системе коллективного интеллекта")
        
    def unregister_agent(self, agent_id: str):
        """Отменить регистрацию агента"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            # Репутацию оставляем для истории
            self.logger.info(f"Агент {agent_id} удален из системы коллективного интеллекта")
            
    async def make_collective_decision(
        self,
        question: str,
        options: List[Any],
        method: VotingMethod = VotingMethod.WEIGHTED,
        timeout: float = 30.0,
        required_agents: Optional[List[str]] = None
    ) -> CollectiveDecision:
        """Принять коллективное решение"""
        
        # Определение участников голосования
        voting_agents = required_agents or list(self.agents.keys())
        
        # Сбор голосов
        votes = await self._collect_votes(question, options, voting_agents, timeout)
        
        if len(votes) < self.min_votes_for_decision:
            raise ValueError(f"Недостаточно голосов для принятия решения: {len(votes)}")
            
        # Принятие решения в зависимости от метода
        if method == VotingMethod.MAJORITY:
            decision = self._majority_voting(votes, options)
        elif method == VotingMethod.WEIGHTED:
            decision = self._weighted_voting(votes, options)
        elif method == VotingMethod.CONSENSUS:
            decision = self._consensus_voting(votes, options)
        elif method == VotingMethod.BORDA_COUNT:
            decision = self._borda_count_voting(votes, options)
        else:
            raise ValueError(f"Неподдерживаемый метод голосования: {method}")
            
        # Сохранение в истории
        self.decision_history.append(decision)
        
        self.logger.info(f"Принято коллективное решение: {decision.decision} (уверенность: {decision.confidence:.2f})")
        
        return decision
        
    async def _collect_votes(
        self,
        question: str,
        options: List[Any],
        agent_ids: List[str],
        timeout: float
    ) -> List[Vote]:
        """Собрать голоса от агентов"""
        
        votes = []
        tasks = []
        
        # Запуск параллельного сбора голосов
        for agent_id in agent_ids:
            if agent_id in self.agents:
                task = asyncio.create_task(
                    self._get_agent_vote(agent_id, question, options, timeout)
                )
                tasks.append(task)
                
        # Ожидание результатов с таймаутом
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            
            for result in results:
                if isinstance(result, Vote):
                    votes.append(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"Ошибка получения голоса: {result}")
                    
        except asyncio.TimeoutError:
            self.logger.warning(f"Таймаут сбора голосов после {timeout}с")
            
        return votes
        
    async def _get_agent_vote(
        self,
        agent_id: str,
        question: str,
        options: List[Any],
        timeout: float
    ) -> Vote:
        """Получить голос от конкретного агента"""
        
        agent = self.agents[agent_id]
        
        # Формирование запроса к агенту
        vote_request = {
            "question": question,
            "options": options,
            "timeout": timeout
        }
        
        try:
            # Отправка запроса агенту (через его систему сообщений)
            response = await agent.handle_message("vote_request", vote_request, "collective_intelligence")
            
            if response and "option" in response:
                return Vote(
                    agent_id=agent_id,
                    option=response["option"],
                    confidence=response.get("confidence", 1.0),
                    reasoning=response.get("reasoning")
                )
            else:
                raise ValueError("Некорректный ответ от агента")
                
        except Exception as e:
            self.logger.error(f"Ошибка получения голоса от агента {agent_id}: {e}")
            # Возвращаем случайный выбор с низкой уверенностью
            return Vote(
                agent_id=agent_id,
                option=random.choice(options),
                confidence=0.1,
                reasoning=f"Ошибка: {str(e)}"
            )
            
    def _majority_voting(self, votes: List[Vote], options: List[Any]) -> CollectiveDecision:
        """Простое большинство голосов"""
        
        vote_counts = {}
        for vote in votes:
            if vote.option in vote_counts:
                vote_counts[vote.option] += 1
            else:
                vote_counts[vote.option] = 1
                
        # Находим вариант с максимальным количеством голосов
        winner = max(vote_counts.items(), key=lambda x: x[1])
        confidence = winner[1] / len(votes)
        
        return CollectiveDecision(
            decision=winner[0],
            confidence=confidence,
            votes=votes,
            method_used="majority",
            metadata={"vote_counts": vote_counts}
        )
        
    def _weighted_voting(self, votes: List[Vote], options: List[Any]) -> CollectiveDecision:
        """Взвешенное голосование с учетом репутации и уверенности"""
        
        weighted_scores = {}
        total_weight = 0
        
        for vote in votes:
            agent_reputation = self.agent_reputation.get(vote.agent_id, 1.0)
            weight = vote.confidence * agent_reputation
            total_weight += weight
            
            if vote.option in weighted_scores:
                weighted_scores[vote.option] += weight
            else:
                weighted_scores[vote.option] = weight
                
        # Нормализация весов
        for option in weighted_scores:
            weighted_scores[option] /= total_weight
            
        # Выбор варианта с максимальным весом
        winner = max(weighted_scores.items(), key=lambda x: x[1])
        
        return CollectiveDecision(
            decision=winner[0],
            confidence=winner[1],
            votes=votes,
            method_used="weighted",
            metadata={"weighted_scores": weighted_scores}
        )
        
    def _consensus_voting(self, votes: List[Vote], options: List[Any]) -> CollectiveDecision:
        """Голосование на основе консенсуса"""
        
        # Сначала пробуем взвешенное голосование
        weighted_result = self._weighted_voting(votes, options)
        
        # Проверяем, достигнут ли консенсус
        if weighted_result.confidence >= self.consensus_threshold:
            weighted_result.method_used = "consensus"
            return weighted_result
        else:
            # Если консенсус не достигнут, возвращаем результат с низкой уверенностью
            return CollectiveDecision(
                decision=None,
                confidence=0.0,
                votes=votes,
                method_used="consensus_failed",
                metadata={"required_threshold": self.consensus_threshold}
            )
            
    def _borda_count_voting(self, votes: List[Vote], options: List[Any]) -> CollectiveDecision:
        """Метод Борда для ранжированного голосования"""
        
        borda_scores = {option: 0 for option in options}
        
        for vote in votes:
            agent_reputation = self.agent_reputation.get(vote.agent_id, 1.0)
            
            # Если агент проголосовал за конкретный вариант, даем ему максимальный балл
            if vote.option in borda_scores:
                points = len(options) - 1  # Максимальный балл
                borda_scores[vote.option] += points * vote.confidence * agent_reputation
                
        # Нормализация
        total_score = sum(borda_scores.values())
        if total_score > 0:
            for option in borda_scores:
                borda_scores[option] /= total_score
                
        # Выбор варианта с максимальным баллом
        winner = max(borda_scores.items(), key=lambda x: x[1])
        
        return CollectiveDecision(
            decision=winner[0],
            confidence=winner[1],
            votes=votes,
            method_used="borda_count",
            metadata={"borda_scores": borda_scores}
        )
        
    async def share_knowledge(
        self,
        agent_id: str,
        key: str,
        value: Any,
        confidence: float = 1.0
    ):
        """Поделиться знанием с коллективом"""
        
        if key in self.knowledge_base:
            existing = self.knowledge_base[key]
            
            # Проверяем, подтверждает ли новое знание существующее
            if existing.value == value:
                if agent_id not in existing.confirmations:
                    existing.confirmations.append(agent_id)
                    self.logger.info(f"Знание '{key}' подтверждено агентом {agent_id}")
            else:
                if agent_id not in existing.contradictions:
                    existing.contradictions.append(agent_id)
                    self.logger.warning(f"Знание '{key}' противоречит мнению агента {agent_id}")
        else:
            # Новое знание
            self.knowledge_base[key] = KnowledgeItem(
                key=key,
                value=value,
                source_agent=agent_id,
                confidence=confidence
            )
            self.logger.info(f"Новое знание '{key}' добавлено агентом {agent_id}")
            
    def get_collective_knowledge(self, key: str) -> Optional[Any]:
        """Получить коллективное знание"""
        
        if key not in self.knowledge_base:
            return None
            
        item = self.knowledge_base[key]
        
        # Проверяем уровень подтверждения
        confirmations = len(item.confirmations)
        contradictions = len(item.contradictions)
        
        if confirmations >= self.knowledge_confirmation_threshold and contradictions == 0:
            return item.value
        elif confirmations > contradictions:
            return item.value
        else:
            return None
            
    async def evaluate_collective_performance(
        self,
        task_results: List[TaskResult]
    ) -> Dict[str, float]:
        """Оценить коллективную производительность"""
        
        performance_metrics = {}
        
        # Группируем результаты по агентам
        agent_results = {}
        for result in task_results:
            if result.agent_id not in agent_results:
                agent_results[result.agent_id] = []
            agent_results[result.agent_id].append(result)
            
        # Вычисляем метрики для каждого агента
        for agent_id, results in agent_results.items():
            success_rate = sum(1 for r in results if r.success) / len(results)
            avg_execution_time = statistics.mean(r.execution_time for r in results)
            avg_confidence = statistics.mean(r.confidence for r in results)
            
            # Обновляем репутацию агента
            old_reputation = self.agent_reputation.get(agent_id, 1.0)
            new_reputation = (old_reputation * self.reputation_decay + 
                            success_rate * avg_confidence * (1 - self.reputation_decay))
            self.agent_reputation[agent_id] = new_reputation
            
            performance_metrics[agent_id] = {
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "avg_confidence": avg_confidence,
                "reputation": new_reputation,
                "task_count": len(results)
            }
            
        # Коллективные метрики
        all_results = task_results
        if all_results:
            collective_success_rate = sum(1 for r in all_results if r.success) / len(all_results)
            collective_avg_time = statistics.mean(r.execution_time for r in all_results)
            
            performance_metrics["collective"] = {
                "success_rate": collective_success_rate,
                "avg_execution_time": collective_avg_time,
                "total_tasks": len(all_results),
                "agents_count": len(agent_results)
            }
            
        return performance_metrics
        
    def get_swarm_intelligence_metrics(self) -> Dict[str, Any]:
        """Получить метрики роевого интеллекта"""
        
        return {
            "registered_agents": len(self.agents),
            "knowledge_base_size": len(self.knowledge_base),
            "decisions_made": len(self.decision_history),
            "avg_agent_reputation": statistics.mean(self.agent_reputation.values()) if self.agent_reputation else 0,
            "consensus_threshold": self.consensus_threshold,
            "confirmed_knowledge_items": len([
                item for item in self.knowledge_base.values()
                if len(item.confirmations) >= self.knowledge_confirmation_threshold
            ]),
            "recent_decisions": [
                {
                    "decision": d.decision,
                    "confidence": d.confidence,
                    "method": d.method_used,
                    "timestamp": d.timestamp
                }
                for d in self.decision_history[-10:]  # Последние 10 решений
            ]
        }
        
    async def emergent_behavior_detection(self) -> Dict[str, Any]:
        """Обнаружение эмерджентного поведения в рое"""
        
        patterns = {}
        
        # Анализ паттернов принятия решений
        if len(self.decision_history) >= 5:
            recent_decisions = self.decision_history[-10:]
            
            # Частота использования методов
            method_frequency = {}
            for decision in recent_decisions:
                method = decision.method_used
                method_frequency[method] = method_frequency.get(method, 0) + 1
                
            patterns["decision_method_preference"] = method_frequency
            
            # Тренд уверенности в решениях
            confidence_trend = [d.confidence for d in recent_decisions]
            if len(confidence_trend) > 1:
                patterns["confidence_trend"] = {
                    "increasing": confidence_trend[-1] > confidence_trend[0],
                    "average": statistics.mean(confidence_trend),
                    "variance": statistics.variance(confidence_trend) if len(confidence_trend) > 1 else 0
                }
                
        # Анализ репутационной динамики
        if self.agent_reputation:
            reputation_values = list(self.agent_reputation.values())
            patterns["reputation_distribution"] = {
                "mean": statistics.mean(reputation_values),
                "std": statistics.stdev(reputation_values) if len(reputation_values) > 1 else 0,
                "max": max(reputation_values),
                "min": min(reputation_values)
            }
            
        # Анализ коллективного знания
        knowledge_stats = {
            "total_items": len(self.knowledge_base),
            "confirmed_items": len([
                item for item in self.knowledge_base.values()
                if len(item.confirmations) >= self.knowledge_confirmation_threshold
            ]),
            "contested_items": len([
                item for item in self.knowledge_base.values()
                if len(item.contradictions) > 0
            ])
        }
        patterns["knowledge_evolution"] = knowledge_stats
        
        return patterns

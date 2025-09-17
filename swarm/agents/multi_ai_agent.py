"""
Мульти-AI агент для работы с несколькими моделями одновременно
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .ai_agent_base import AIAgentBase, AIModelConfig
from .openai_agent import OpenAIAgent
from .anthropic_agent import AnthropicAgent
from .local_llm_agent import LocalLLMAgent
from ..core.agent import Task, TaskResult


@dataclass
class MultiAIConfig:
    """Конфигурация для мульти-AI агента"""
    primary_model: str = "openai"  # Основная модель
    fallback_models: List[str] = None  # Резервные модели
    consensus_threshold: float = 0.7  # Порог для консенсуса
    use_voting: bool = True  # Использовать голосование
    parallel_processing: bool = True  # Параллельная обработка
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = ["local", "anthropic"]


class MultiAIAgent(AIAgentBase):
    """
    Агент, использующий несколько AI моделей для повышения качества ответов
    """
    
    def __init__(
        self,
        multi_config: MultiAIConfig,
        openai_config: Optional[Dict] = None,
        anthropic_config: Optional[Dict] = None,
        local_config: Optional[Dict] = None,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        # Базовая конфигурация
        base_config = AIModelConfig(
            model_name="multi-ai-ensemble",
            max_tokens=4096,
            temperature=0.7
        )
        
        super().__init__(
            model_config=base_config,
            agent_id=agent_id,
            name=name or "MultiAI-Agent",
            system_prompt=system_prompt,
            specialized_capabilities=[
                "multi_model_processing", 
                "consensus_building", 
                "quality_assurance",
                "redundancy"
            ]
        )
        
        self.multi_config = multi_config
        self.ai_agents: Dict[str, AIAgentBase] = {}
        
        # Инициализация подагентов
        self._initialize_ai_agents(openai_config, anthropic_config, local_config)
        
    def _initialize_ai_agents(
        self, 
        openai_config: Optional[Dict],
        anthropic_config: Optional[Dict], 
        local_config: Optional[Dict]
    ):
        """Инициализация AI агентов"""
        
        try:
            # OpenAI агент
            if openai_config and openai_config.get("api_key"):
                self.ai_agents["openai"] = OpenAIAgent(
                    agent_id=f"{self.id}_openai",
                    system_prompt=self.system_prompt,
                    **openai_config
                )
                self.ai_logger.info("OpenAI агент инициализирован")
        except Exception as e:
            self.ai_logger.warning(f"Не удалось инициализировать OpenAI агента: {e}")
            
        try:
            # Anthropic агент
            if anthropic_config and anthropic_config.get("api_key"):
                self.ai_agents["anthropic"] = AnthropicAgent(
                    agent_id=f"{self.id}_anthropic",
                    system_prompt=self.system_prompt,
                    **anthropic_config
                )
                self.ai_logger.info("Anthropic агент инициализирован")
        except Exception as e:
            self.ai_logger.warning(f"Не удалось инициализировать Anthropic агента: {e}")
            
        try:
            # Локальный агент
            local_cfg = local_config or {"model_name": "llama2"}
            self.ai_agents["local"] = LocalLLMAgent(
                agent_id=f"{self.id}_local",
                system_prompt=self.system_prompt,
                **local_cfg
            )
            self.ai_logger.info("Локальный агент инициализирован")
        except Exception as e:
            self.ai_logger.warning(f"Не удалось инициализировать локальный агент: {e}")
            
        if not self.ai_agents:
            raise ValueError("Не удалось инициализировать ни одного AI агента")
            
    async def _call_ai_model(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Вызов множественных AI моделей"""
        
        if self.multi_config.parallel_processing:
            return await self._parallel_processing(prompt, task)
        else:
            return await self._sequential_processing(prompt, task)
            
    async def _parallel_processing(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Параллельная обработка несколькими моделями"""
        
        # Определяем какие модели использовать
        models_to_use = self._select_models_for_task(task)
        
        # Запускаем задачи параллельно
        tasks_to_run = []
        for model_name in models_to_use:
            if model_name in self.ai_agents:
                agent = self.ai_agents[model_name]
                task_coroutine = self._safe_agent_call(agent, prompt, task, model_name)
                tasks_to_run.append(task_coroutine)
                
        if not tasks_to_run:
            raise ValueError("Нет доступных моделей для обработки")
            
        # Ждем результаты от всех моделей
        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        
        # Фильтруем успешные результаты
        successful_results = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                successful_results.append(result)
            else:
                self.ai_logger.warning(f"Модель {models_to_use[i]} вернула ошибку: {result}")
                
        if not successful_results:
            raise ValueError("Ни одна модель не вернула успешный результат")
            
        # Обработка результатов
        if self.multi_config.use_voting and len(successful_results) > 1:
            return self._consensus_processing(successful_results, task)
        else:
            return self._best_result_selection(successful_results)
            
    async def _sequential_processing(self, prompt: str, task: Task) -> Dict[str, Any]:
        """Последовательная обработка с fallback"""
        
        models_to_try = [self.multi_config.primary_model] + self.multi_config.fallback_models
        
        for model_name in models_to_try:
            if model_name in self.ai_agents:
                try:
                    agent = self.ai_agents[model_name]
                    result = await self._safe_agent_call(agent, prompt, task, model_name)
                    
                    if result and result.get("confidence", 0) > 0.5:
                        return result
                        
                except Exception as e:
                    self.ai_logger.warning(f"Модель {model_name} не смогла обработать запрос: {e}")
                    continue
                    
        raise ValueError("Все модели не смогли обработать запрос")
        
    async def _safe_agent_call(
        self, 
        agent: AIAgentBase, 
        prompt: str, 
        task: Task, 
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Безопасный вызов агента с обработкой ошибок"""
        
        try:
            # Создаем копию задачи для агента
            agent_task = Task(
                id=f"{task.id}_{model_name}",
                content=task.content,
                requirements=task.requirements,
                context=task.context,
                priority=task.priority,
                timeout=task.timeout
            )
            
            result = await agent._call_ai_model(prompt, agent_task)
            
            # Добавляем метаданные о модели
            if result:
                result["source_model"] = model_name
                result["agent_id"] = agent.id
                
            return result
            
        except Exception as e:
            self.ai_logger.error(f"Ошибка вызова агента {model_name}: {e}")
            return None
            
    def _select_models_for_task(self, task: Task) -> List[str]:
        """Выбор моделей для конкретной задачи"""
        
        models = []
        
        # Всегда включаем основную модель
        if self.multi_config.primary_model in self.ai_agents:
            models.append(self.multi_config.primary_model)
            
        # Добавляем специализированные модели по типу задачи
        if "code_analysis" in task.requirements:
            # Для анализа кода хороши все модели
            models.extend([m for m in ["openai", "anthropic", "local"] if m in self.ai_agents and m not in models])
            
        elif "ethical_review" in task.requirements:
            # Для этических вопросов предпочитаем Claude
            if "anthropic" in self.ai_agents and "anthropic" not in models:
                models.append("anthropic")
                
        elif "privacy_focused" in task.requirements:
            # Для приватных задач используем локальную модель
            if "local" in self.ai_agents and "local" not in models:
                models.append("local")
                
        # Если модели не найдены, используем все доступные
        if not models:
            models = list(self.ai_agents.keys())
            
        return models[:3]  # Ограничиваем до 3 моделей для производительности
        
    def _consensus_processing(self, results: List[Dict[str, Any]], task: Task) -> Dict[str, Any]:
        """Обработка результатов с поиском консенсуса"""
        
        # Анализируем похожесть ответов
        consensus_result = self._find_consensus(results)
        
        if consensus_result:
            consensus_result["consensus_achieved"] = True
            consensus_result["participating_models"] = [r.get("source_model") for r in results]
            consensus_result["consensus_confidence"] = self._calculate_consensus_confidence(results)
            return consensus_result
        else:
            # Если консенсус не достигнут, возвращаем лучший результат
            best_result = self._best_result_selection(results)
            best_result["consensus_achieved"] = False
            best_result["participating_models"] = [r.get("source_model") for r in results]
            return best_result
            
    def _find_consensus(self, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Поиск консенсуса между результатами"""
        
        if len(results) < 2:
            return results[0] if results else None
            
        # Простой алгоритм консенсуса на основе схожести ключевых слов
        contents = [r.get("content", "") for r in results]
        
        # Ищем общие ключевые слова и фразы
        common_elements = self._find_common_elements(contents)
        
        if len(common_elements) >= 3:  # Минимум 3 общих элемента для консенсуса
            # Создаем консенсусный ответ
            consensus_content = self._merge_contents(contents, common_elements)
            
            best_result = max(results, key=lambda r: r.get("confidence", 0))
            consensus_result = best_result.copy()
            consensus_result["content"] = consensus_content
            
            return consensus_result
            
        return None
        
    def _find_common_elements(self, contents: List[str]) -> List[str]:
        """Поиск общих элементов в контенте"""
        
        # Простой анализ общих слов и фраз
        common = []
        
        # Разбиваем на слова
        all_words = [set(content.lower().split()) for content in contents]
        
        # Находим общие слова
        if all_words:
            common_words = set.intersection(*all_words)
            # Исключаем служебные слова
            stop_words = {"и", "в", "на", "с", "по", "для", "от", "до", "а", "но", "или", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
            common_words = common_words - stop_words
            common.extend(list(common_words))
            
        return common
        
    def _merge_contents(self, contents: List[str], common_elements: List[str]) -> str:
        """Объединение контента на основе общих элементов"""
        
        # Создаем объединенный ответ
        merged = f"Консенсусный ответ на основе {len(contents)} моделей:\n\n"
        
        # Добавляем общие элементы
        if common_elements:
            merged += f"Ключевые аспекты (согласие всех моделей):\n"
            for element in common_elements[:5]:  # Топ-5 общих элементов
                merged += f"• {element}\n"
            merged += "\n"
            
        # Добавляем основной контент от модели с наивысшей уверенностью
        best_content = max(contents, key=len)  # Берем самый подробный ответ
        merged += f"Детальный ответ:\n{best_content}"
        
        return merged
        
    def _best_result_selection(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Выбор лучшего результата"""
        
        # Сортируем по уверенности и качеству
        def result_score(result):
            confidence = result.get("confidence", 0)
            content_length = len(result.get("content", ""))
            has_code = "```" in result.get("content", "")
            
            score = confidence * 0.5 + min(content_length / 1000, 1.0) * 0.3
            if has_code and any("code" in req for req in result.get("requirements", [])):
                score += 0.2
                
            return score
            
        best_result = max(results, key=result_score)
        best_result["selection_reason"] = "highest_quality_score"
        
        return best_result
        
    def _calculate_consensus_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Расчет уверенности консенсуса"""
        
        confidences = [r.get("confidence", 0) for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Бонус за количество согласующихся моделей
        consensus_bonus = min(len(results) * 0.1, 0.3)
        
        return min(avg_confidence + consensus_bonus, 1.0)
        
    def get_multi_ai_metrics(self) -> Dict[str, Any]:
        """Получение метрик мульти-AI агента"""
        
        base_metrics = self.get_ai_metrics()
        
        # Метрики подагентов
        sub_agents_metrics = {}
        for name, agent in self.ai_agents.items():
            sub_agents_metrics[name] = agent.get_ai_metrics()
            
        multi_metrics = {
            "multi_ai_config": {
                "primary_model": self.multi_config.primary_model,
                "fallback_models": self.multi_config.fallback_models,
                "parallel_processing": self.multi_config.parallel_processing,
                "use_voting": self.multi_config.use_voting
            },
            "active_models": list(self.ai_agents.keys()),
            "sub_agents_metrics": sub_agents_metrics
        }
        
        base_metrics.update(multi_metrics)
        return base_metrics

# -*- coding: utf-8 -*-
"""
多轮对话核心模块

整合会话管理、上下文跟踪、意图识别功能
提供完整的多轮对话能力
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from .session import SessionManager, SessionContext, SessionStatus, get_session_manager
from .context import ContextTracker, get_context_tracker
from .intent import IntentRecognizer, Intent, QuestionType, recognize_intent, get_intent_recognizer
from .memory import DialogueMemory, DialogueHistory, get_dialogue_memory


class ResponseStrategy(Enum):
    """响应策略"""
    DIRECT = "direct"           # 直接回答
    CLARIFICATION = "clarification"  # 请求澄清
    FOLLOW_UP = "follow_up"     # 追问
    RECOMMEND = "recommend"     # 相关推荐
    ERROR = "error"             # 错误处理


@dataclass
class DialogueResponse:
    """对话响应"""
    answer: str
    strategy: ResponseStrategy
    confidence: float
    entities: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    clarification: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "answer": self.answer,
            "strategy": self.strategy.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "sources": self.sources,
            "suggestions": self.suggestions,
            "clarification": self.clarification,
            "metadata": self.metadata
        }


@dataclass
class ConversationConfig:
    """对话配置"""
    window_size: int = 10           # 上下文窗口大小
    max_history: int = 100           # 最大历史记录
    auto_save: bool = True           # 自动保存
    enable_suggestions: bool = True  # 启用推荐
    enable_clarification: bool = True  # 启用澄清


class ConversationAgent:
    """
    多轮对话Agent
    
    整合会话管理、上下文跟踪、意图识别，
    提供完整的多轮对话能力
    """
    
    def __init__(
        self,
        config: ConversationConfig = None,
        storage_path: str = None,
        engine=None  # NeuralSiteEngine instance
    ):
        """
        初始化对话Agent
        
        Args:
            config: 对话配置
            storage_path: 存储路径
            engine: NeuralSite引擎实例
        """
        self.config = config or ConversationConfig()
        self.engine = engine
        
        # 初始化各组件
        self.session_manager = get_session_manager(storage_path)
        self.context_tracker = get_context_tracker(self.config.window_size)
        self.intent_recognizer = get_intent_recognizer()
        self.dialogue_memory = get_dialogue_memory(storage_path)
        
        # 问题处理器映射
        self._handlers: Dict[QuestionType, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理器"""
        self._handlers = {
            QuestionType.QUERY_COORDINATE: self._handle_coordinate_query,
            QuestionType.QUERY_ELEVATION: self._handle_elevation_query,
            QuestionType.QUERY_GRADE: self._handle_grade_query,
            QuestionType.QUERY_CROSS_SECTION: self._handle_cross_section_query,
            QuestionType.QUERY_ENTITY: self._handle_entity_query,
            QuestionType.GREETING: self._handle_greeting,
            QuestionType.UNKNOWN: self._handle_unknown,
        }
    
    def start_conversation(
        self,
        user_id: str = "default",
        project_id: str = ""
    ) -> SessionContext:
        """
        开始新对话
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            会话上下文
        """
        # 创建会话
        session = self.session_manager.create_session(user_id, project_id)
        
        # 初始化对话历史
        self.dialogue_memory.create_history(session.session_id, user_id)
        
        # 清空上下文
        self.context_tracker.clear()
        
        return session
    
    def continue_conversation(self, session_id: str) -> bool:
        """
        继续已有对话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        # 加载会话
        session = self.session_manager.get_session(session_id)
        if not session:
            # 尝试从磁盘加载
            session = self.session_manager.load_from_disk(session_id)
        
        if not session:
            return False
        
        # 设置为活动会话
        self.session_manager.set_active_session(session_id)
        
        # 加载上下文
        # TODO: 从存储恢复上下文
        
        return True
    
    def chat(self, message: str, session_id: str = None) -> DialogueResponse:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选）
            
        Returns:
            对话响应
        """
        # 确保有活动会话
        if session_id:
            self.continue_conversation(session_id)
        elif not self.session_manager.get_active_session():
            self.start_conversation()
        
        active_session = self.session_manager.get_active_session()
        session_id = active_session.session_id
        
        # 1. 添加用户消息到上下文和记忆
        self.context_tracker.add_message("user", message)
        self.dialogue_memory.add_message(
            session_id, "user", message,
            intent_type="", confidence=0.0
        )
        
        # 2. 获取上下文信息
        context_info = self._get_context_info(active_session)
        
        # 3. 识别意图
        intent = self.intent_recognizer.recognize(message, context_info)
        
        # 4. 处理澄清请求
        if intent.requires_clarification:
            response = DialogueResponse(
                answer=intent.clarification_message,
                strategy=ResponseStrategy.CLARIFICATION,
                confidence=0.3,
                clarification=intent.clarification_message
            )
            return response
        
        # 5. 处理问候
        if intent.type == QuestionType.GREETING:
            response = DialogueResponse(
                answer="您好！我是NeuralSite智能助手，可以帮您查询工程数据。请问有什么可以帮您？",
                strategy=ResponseStrategy.DIRECT,
                confidence=1.0,
                sources=["system"]
            )
            self._save_assistant_message(session_id, response)
            return response
        
        # 6. 调用处理器
        handler = self._handlers.get(intent.type)
        if handler:
            response = handler(intent, context_info)
        else:
            response = self._handle_unknown(intent, context_info)
        
        # 7. 添加相关推荐
        if self.config.enable_suggestions:
            suggestions = self.intent_recognizer.get_related_queries(intent)
            response.suggestions = suggestions
        
        # 8. 保存到记忆
        self._save_assistant_message(session_id, response, intent)
        
        # 9. 更新会话上下文
        self._update_session_context(active_session, intent, response)
        
        return response
    
    def _get_context_info(self, session: SessionContext) -> Dict:
        """获取上下文信息"""
        return {
            "current_chainage": session.current_chainage,
            "current_station": session.current_station,
            "referenced_entities": session.referenced_entities,
            "topic_stack": session.topic_stack[-3:] if session.topic_stack else []
        }
    
    def _save_assistant_message(
        self,
        session_id: str,
        response: DialogueResponse,
        intent: Intent = None
    ):
        """保存助手消息"""
        self.dialogue_memory.add_message(
            session_id,
            "assistant",
            response.answer,
            metadata={
                "strategy": response.strategy.value,
                "entities": response.entities
            },
            intent_type=intent.type.value if intent else "",
            confidence=response.confidence
        )
    
    def _update_session_context(
        self,
        session: SessionContext,
        intent: Intent,
        response: DialogueResponse
    ):
        """更新会话上下文"""
        updates = {}
        
        # 更新当前实体
        if intent.parameters.get("chainage"):
            updates["current_chainage"] = intent.parameters["chainage"]
        if intent.parameters.get("station"):
            updates["current_station"] = intent.parameters["station"]
        
        # 追踪实体
        for entity in response.entities:
            self.context_tracker.track_entity(
                entity_id=entity.get("id", entity.get("value", "unknown")),
                entity_type=entity.get("type", "unknown"),
                name=entity.get("name", str(entity.get("value", ""))),
                value=entity.get("value"),
                confidence=response.confidence
            )
        
        # 更新话题
        if intent.parameters.get("chainage"):
            topic = f"{intent.parameters['chainage']}_{intent.type.value}"
            self.context_tracker.set_question_type(intent.type.value)
        
        if updates:
            self.session_manager.update_session(session.session_id, updates)
    
    # ========== 处理器方法 ==========
    
    def _handle_coordinate_query(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理坐标查询"""
        if not self.engine:
            return DialogueResponse(
                answer="引擎未初始化",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
        
        station = intent.parameters.get("station")
        if not station:
            return DialogueResponse(
                answer="请提供具体的桩号",
                strategy=ResponseStrategy.CLARIFICATION,
                confidence=0.3
            )
        
        try:
            coord = self.engine.get_coordinate(station)
            chainage = intent.parameters.get("chainage", f"K{station//1000}+{station%1000:03d}")
            
            answer = f"{chainage}的坐标为 X={coord.x:.3f}, Y={coord.y:.3f}, Z={coord.z:.3f}"
            
            entities = [{
                "type": "coordinate",
                "id": chainage,
                "name": chainage,
                "value": {"x": coord.x, "y": coord.y, "z": coord.z}
            }]
            
            return DialogueResponse(
                answer=answer,
                strategy=ResponseStrategy.DIRECT,
                confidence=0.9,
                entities=entities,
                sources=["engine", "knowledge_graph"]
            )
        except Exception as e:
            return DialogueResponse(
                answer=f"查询失败: {str(e)}",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
    
    def _handle_elevation_query(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理标高查询"""
        if not self.engine:
            return DialogueResponse(
                answer="引擎未初始化",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
        
        station = intent.parameters.get("station")
        if not station:
            return DialogueResponse(
                answer="请提供具体的桩号",
                strategy=ResponseStrategy.CLARIFICATION,
                confidence=0.3
            )
        
        try:
            coord = self.engine.get_coordinate(station)
            chainage = intent.parameters.get("chainage", f"K{station//1000}+{station%1000:03d}")
            
            answer = f"{chainage}的设计高程是{coord.z:.3f}m"
            
            entities = [{
                "type": "elevation",
                "id": chainage,
                "name": chainage,
                "value": coord.z
            }]
            
            return DialogueResponse(
                answer=answer,
                strategy=ResponseStrategy.DIRECT,
                confidence=0.9,
                entities=entities,
                sources=["engine"]
            )
        except Exception as e:
            return DialogueResponse(
                answer=f"查询失败: {str(e)}",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
    
    def _handle_grade_query(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理纵坡查询"""
        if not self.engine:
            return DialogueResponse(
                answer="引擎未初始化",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
        
        station = intent.parameters.get("station")
        if not station:
            return DialogueResponse(
                answer="请提供具体的桩号",
                strategy=ResponseStrategy.CLARIFICATION,
                confidence=0.3
            )
        
        try:
            # 查询前后100米的坐标
            coord1 = self.engine.get_coordinate(max(0, station - 100))
            coord2 = self.engine.get_coordinate(station + 100)
            
            # 计算纵坡
            grade = (coord2.z - coord1.z) / 200 * 100
            chainage = intent.parameters.get("chainage", f"K{station//1000}+{station%1000:03d}")
            
            answer = f"{chainage}附近的纵坡为 {grade:.2f}%"
            
            entities = [{
                "type": "grade",
                "id": chainage,
                "name": chainage,
                "value": grade
            }]
            
            return DialogueResponse(
                answer=answer,
                strategy=ResponseStrategy.DIRECT,
                confidence=0.85,
                entities=entities,
                sources=["engine"]
            )
        except Exception as e:
            return DialogueResponse(
                answer=f"查询失败: {str(e)}",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
    
    def _handle_cross_section_query(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理横断面查询"""
        if not self.engine:
            return DialogueResponse(
                answer="引擎未初始化",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
        
        station = intent.parameters.get("station")
        if not station:
            return DialogueResponse(
                answer="请提供具体的桩号",
                strategy=ResponseStrategy.CLARIFICATION,
                confidence=0.3
            )
        
        try:
            cs = self.engine.calculate_cross_section(station)
            chainage = intent.parameters.get("chainage", f"K{station//1000}+{station%1000:03d}")
            
            answer = f"{chainage}的横断面：中心点({cs['center'][0]:.2f}, {cs['center'][1]:.2f}, {cs['center'][2]:.2f})"
            
            entities = [{
                "type": "cross_section",
                "id": chainage,
                "name": chainage,
                "value": cs
            }]
            
            return DialogueResponse(
                answer=answer,
                strategy=ResponseStrategy.DIRECT,
                confidence=0.85,
                entities=entities,
                sources=["engine"]
            )
        except Exception as e:
            return DialogueResponse(
                answer=f"查询失败: {str(e)}",
                strategy=ResponseStrategy.ERROR,
                confidence=0.0
            )
    
    def _handle_entity_query(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理实体查询"""
        # 这里可以调用知识图谱搜索
        answer = "请提供更具体的查询条件，例如：K0+500的坐标、标高等"
        
        return DialogueResponse(
            answer=answer,
            strategy=ResponseStrategy.DIRECT,
            confidence=0.5,
            sources=["knowledge_graph"]
        )
    
    def _handle_greeting(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理问候"""
        return DialogueResponse(
            answer="您好！我是NeuralSite智能助手，可以帮您查询工程数据。请问有什么可以帮您？",
            strategy=ResponseStrategy.DIRECT,
            confidence=1.0,
            sources=["system"]
        )
    
    def _handle_unknown(
        self,
        intent: Intent,
        context: Dict
    ) -> DialogueResponse:
        """处理未知问题"""
        return DialogueResponse(
            answer="抱歉，我无法理解您的问题。请尝试询问具体的桩号信息（如 K0+500 的标高）",
            strategy=ResponseStrategy.CLARIFICATION,
            confidence=0.2,
            clarification="请提供具体的工程数据查询"
        )
    
    def get_conversation_history(
        self,
        session_id: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """获取对话历史"""
        if session_id is None:
            session = self.session_manager.get_active_session()
            if session:
                session_id = session.session_id
        
        if session_id:
            return self.dialogue_memory.get_messages(session_id, limit)
        
        return []
    
    def get_current_context(self) -> Dict:
        """获取当前上下文"""
        session = self.session_manager.get_active_session()
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "current_chainage": session.current_chainage,
            "context_summary": self.context_tracker.get_summary()
        }


# 创建全局实例
_agent: Optional[ConversationAgent] = None


def get_conversation_agent(
    config: ConversationConfig = None,
    storage_path: str = None,
    engine = None
) -> ConversationAgent:
    """获取对话Agent"""
    global _agent
    if _agent is None:
        _agent = ConversationAgent(config, storage_path, engine)
    return _agent


def start_chat(user_id: str = "default", project_id: str = "") -> SessionContext:
    """开始新对话"""
    return get_conversation_agent().start_conversation(user_id, project_id)


def send_message(message: str) -> DialogueResponse:
    """发送消息"""
    return get_conversation_agent().chat(message)

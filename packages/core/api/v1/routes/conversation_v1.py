# -*- coding: utf-8 -*-
"""
多轮对话 API

提供多轮对话、上下文理解功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sys

sys.path.insert(0, '.')

from core.engine import NeuralSiteEngine
from core.agents.conversation import (
    ConversationAgent,
    ConversationConfig,
    DialogueResponse,
    get_conversation_agent,
    start_chat,
    send_message
)
from api.dependencies import get_engine, get_feature_flags
from core.config.feature_flags import FeatureFlags


router = APIRouter(prefix="/api/v1/conversation", tags=["多轮对话"])


# ========== 请求/响应模型 ==========

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID（续接会话）")
    user_id: str = Field("default", description="用户ID")


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    session_id: str
    strategy: str
    confidence: float
    entities: List[Dict[str, Any]] = []
    suggestions: List[str] = []
    sources: List[str] = []


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    current_chainage: Optional[str] = None
    context_summary: Dict[str, Any] = {}


class HistoryResponse(BaseModel):
    """历史记录响应"""
    session_id: str
    messages: List[Dict[str, Any]]
    total: int


# ========== 全局Agent实例 ==========
_conversation_agent: Optional[ConversationAgent] = None


def get_conversation_agent_dep(
    engine: NeuralSiteEngine = Depends(get_engine),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
) -> ConversationAgent:
    """获取对话Agent依赖"""
    global _conversation_agent
    
    if not feature_flags.is_enabled("enable_qa_system"):
        raise HTTPException(
            status_code=403,
            detail="QA system feature is disabled"
        )
    
    if _conversation_agent is None:
        config = ConversationConfig(
            window_size=10,
            auto_save=True,
            enable_suggestions=True
        )
        _conversation_agent = ConversationAgent(
            config=config,
            engine=engine
        )
    
    return _conversation_agent


# ========== API 接口 ==========

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="多轮对话",
    description="进行多轮对话，支持上下文理解和意图识别"
)
async def chat(
    request: ChatRequest,
    agent: ConversationAgent = Depends(get_conversation_agent_dep)
) -> ChatResponse:
    """
    多轮对话接口
    
    功能：
    - 自动会话管理（创建/恢复）
    - 上下文跟踪（实体引用、省略指代）
    - 意图识别（问题分类、参数提取）
    - 相关推荐
    
    示例对话流程：
    1. 用户: "K0+500的标高是多少"
       助手: "K0+500的设计高程是100.000m"
       
    2. 用户: "那它的坐标呢" 
       助手: "K0+500的坐标为 X=500000.000, Y=3000000.000, Z=100.000"
       
    3. 用户: "纵坡呢"
       助手: "K0+500附近的纵坡为 0.50%"
    """
    # 开始或继续会话
    if request.session_id:
        success = agent.continue_conversation(request.session_id)
        if not success:
            # 会话不存在，创建新的
            session = agent.start_conversation(request.user_id)
    else:
        session = agent.start_chat(request.user_id)
    
    # 发送消息
    response: DialogueResponse = agent.chat(request.message, session.session_id)
    
    return ChatResponse(
        answer=response.answer,
        session_id=session.session_id,
        strategy=response.strategy.value,
        confidence=response.confidence,
        entities=response.entities,
        suggestions=response.suggestions,
        sources=response.sources
    )


@router.post(
    "/start",
    response_model=SessionInfo,
    summary="开始新对话",
    description="创建新的对话会话"
)
async def start_conversation(
    user_id: str = Query("default", description="用户ID"),
    project_id: str = Query("", description="项目ID"),
    agent: ConversationAgent = Depends(get_conversation_agent_dep)
) -> SessionInfo:
    """
    开始新的对话会话
    """
    session = agent.start_chat(user_id, project_id)
    
    return SessionInfo(
        session_id=session.session_id,
        current_chainage=session.current_chainage,
        context_summary={}
    )


@router.get(
    "/session/{session_id}",
    response_model=SessionInfo,
    summary="获取会话信息",
    description="获取指定会话的当前状态和上下文"
)
async def get_session(
    session_id: str,
    agent: ConversationAgent = Depends(get_conversation_agent_dep)
) -> SessionInfo:
    """
    获取会话信息
    """
    success = agent.continue_conversation(session_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    context = agent.get_current_context()
    
    return SessionInfo(
        session_id=session_id,
        current_chainage=context.get("current_chainage"),
        context_summary=context.get("context_summary", {})
    )


@router.get(
    "/history/{session_id}",
    response_model=HistoryResponse,
    summary="获取对话历史",
    description="获取会话的对话历史记录"
)
async def get_history(
    session_id: str,
    limit: int = Query(10, ge=1, le=100, description="返回消息数量"),
    agent: ConversationAgent = Depends(get_conversation_agent_dep)
) -> HistoryResponse:
    """
    获取对话历史
    """
    success = agent.continue_conversation(session_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    messages = agent.get_conversation_history(session_id, limit)
    
    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        total=len(messages)
    )


@router.delete(
    "/session/{session_id}",
    summary="结束会话",
    description="结束指定的对话会话"
)
async def end_session(
    session_id: str,
    agent: ConversationAgent = Depends(get_conversation_agent_dep)
) -> Dict[str, str]:
    """
    结束会话
    """
    from core.agents.conversation import get_session_manager
    
    manager = get_session_manager()
    success = manager.close_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    return {"status": "closed", "session_id": session_id}


# ========== 注册路由 ==========

def register_routes(app):
    """注册路由到FastAPI应用"""
    app.include_router(router)

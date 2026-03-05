# -*- coding: utf-8 -*-
"""
NeuralSite 多轮对话系统

提供会话管理、上下文跟踪、意图识别、多轮对话功能

模块结构:
- session: 会话管理
- context: 上下文跟踪
- intent: 意图识别
- memory: 对话历史存储
- dialogue: 多轮对话核心

快速开始:
```python
from core.agents.conversation import start_chat, send_message

# 开始对话
session = start_chat(user_id="user1")

# 发送消息
response = send_message("K0+500的标高是多少")

print(response.answer)  # K0+500的设计高程是100.000m
print(response.suggestions)  # 相关推荐
```
"""

from .session import (
    SessionManager,
    SessionContext,
    SessionStatus,
    create_session,
    get_current_session,
    get_session_manager
)

from .context import (
    ContextTracker,
    ContextWindow,
    TrackedEntity,
    EntityReferenceType,
    get_context_tracker,
    reset_context_tracker
)

from .intent import (
    IntentRecognizer,
    Intent,
    QuestionType,
    recognize_intent,
    get_intent_recognizer
)

from .memory import (
    DialogueMemory,
    DialogueHistory,
    DialogueMessage,
    get_dialogue_memory
)

from .dialogue import (
    ConversationAgent,
    ConversationConfig,
    DialogueResponse,
    ResponseStrategy,
    get_conversation_agent,
    start_chat,
    send_message
)

__all__ = [
    # Session
    'SessionManager',
    'SessionContext', 
    'SessionStatus',
    'create_session',
    'get_current_session',
    'get_session_manager',
    
    # Context
    'ContextTracker',
    'ContextWindow',
    'TrackedEntity',
    'EntityReferenceType',
    'get_context_tracker',
    'reset_context_tracker',
    
    # Intent
    'IntentRecognizer',
    'Intent',
    'QuestionType',
    'recognize_intent',
    'get_intent_recognizer',
    
    # Memory
    'DialogueMemory',
    'DialogueHistory',
    'DialogueMessage',
    'get_dialogue_memory',
    
    # Dialogue
    'ConversationAgent',
    'ConversationConfig',
    'DialogueResponse',
    'ResponseStrategy',
    'get_conversation_agent',
    'start_chat',
    'send_message',
]

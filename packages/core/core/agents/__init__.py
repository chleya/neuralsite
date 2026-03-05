# -*- coding: utf-8 -*-
"""
NeuralSite Agents

包含:
- qa_agent: 自动质检Agent
- workflow: 工作流
- conversation: 多轮对话系统
"""

from .qa_agent import AutoQAAgent, QAReport, ValidationIssue, get_qa_agent
from .workflow import WorkflowEngine, WorkflowResult, get_workflow_engine

# 导出对话模块
from .conversation import (
    ConversationAgent,
    ConversationConfig,
    DialogueResponse,
    ResponseStrategy,
    start_chat,
    send_message,
    get_conversation_agent
)

__all__ = [
    # QA Agent
    'AutoQAAgent',
    'QAReport', 
    'ValidationIssue',
    'get_qa_agent',
    
    # Workflow
    'WorkflowEngine',
    'WorkflowResult',
    'get_workflow_engine',
    
    # Conversation
    'ConversationAgent',
    'ConversationConfig',
    'DialogueResponse',
    'ResponseStrategy',
    'start_chat',
    'send_message',
    'get_conversation_agent',
]

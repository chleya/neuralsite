"""
Knowledge Base - 知识库
施工规范查询、工艺要点、质量问题解决方案
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StandardItem:
    """规范条目"""
    code: str  # 规范编号
    name: str  # 规范名称
    category: str  # 分类
    content: str  # 内容
    source: str  # 来源


@dataclass
class ProcessItem:
    """工艺条目"""
    name: str  # 工艺名称
    category: str  # 分类
    steps: List[str]  # 施工步骤
    key_points: List[str]  # 关键要点
    quality_standards: List[str]  # 质量标准
    precautions: List[str]  # 注意事项


@dataclass
class QualityIssue:
    """质量问题"""
    name: str  # 问题名称
    category: str  # 分类
    description: str  # 描述
    causes: List[str]  # 原因分析
    solutions: List[str]  # 解决方案
    preventive_measures: List[str]  # 预防措施
    related_standards: List[str]  # 相关规范


class KnowledgeBase:
    """知识库"""

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化知识库

        Args:
            base_path: 知识库文件路径 (默认: packages/core/knowledge)
        """
        if base_path is None:
            # 默认路径
            base_path = Path(__file__).parent.parent / "knowledge"
        else:
            base_path = Path(base_path)

        self.base_path = Path(base_path)
        self._standards: Dict[str, StandardItem] = {}
        self._processes: Dict[str, ProcessItem] = {}
        self._quality_issues: Dict[str, QualityIssue] = {}

        # 加载知识库
        self._load_knowledge()

    def _load_knowledge(self) -> None:
        """加载知识库文件"""
        # 加载施工规范
        standards_file = self.base_path / "construction_standards.json"
        if standards_file.exists():
            self._load_standards(standards_file)

        # 加载施工工艺
        processes_file = self.base_path / "processes.json"
        if processes_file.exists():
            self._load_processes(processes_file)

        # 加载质量问题
        issues_file = self.base_path / "quality_issues.json"
        if issues_file.exists():
            self._load_quality_issues(issues_file)

    def _load_standards(self, file_path: Path) -> None:
        """加载施工规范"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("standards", []):
                standard = StandardItem(
                    code=item.get("code", ""),
                    name=item.get("name", ""),
                    category=item.get("category", ""),
                    content=item.get("content", ""),
                    source=item.get("source", ""),
                )
                self._standards[standard.code] = standard

            logger.info(f"Loaded {len(self._standards)} standards")

        except Exception as e:
            logger.error(f"Failed to load standards: {e}")

    def _load_processes(self, file_path: Path) -> None:
        """加载施工工艺"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("processes", []):
                process = ProcessItem(
                    name=item.get("name", ""),
                    category=item.get("category", ""),
                    steps=item.get("steps", []),
                    key_points=item.get("key_points", []),
                    quality_standards=item.get("quality_standards", []),
                    precautions=item.get("precautions", []),
                )
                self._processes[process.name] = process

            logger.info(f"Loaded {len(self._processes)} processes")

        except Exception as e:
            logger.error(f"Failed to load processes: {e}")

    def _load_quality_issues(self, file_path: Path) -> None:
        """加载质量问题"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("issues", []):
                issue = QualityIssue(
                    name=item.get("name", ""),
                    category=item.get("category", ""),
                    description=item.get("description", ""),
                    causes=item.get("causes", []),
                    solutions=item.get("solutions", []),
                    preventive_measures=item.get("preventive_measures", []),
                    related_standards=item.get("related_standards", []),
                )
                self._quality_issues[issue.name] = issue

            logger.info(f"Loaded {len(self._quality_issues)} quality issues")

        except Exception as e:
            logger.error(f"Failed to load quality issues: {e}")

    # ========== 施工规范查询 ==========

    def search_standards(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[StandardItem]:
        """
        搜索施工规范

        Args:
            keyword: 关键词
            category: 分类筛选 (可选)
            limit: 返回数量限制

        Returns:
            规范列表
        """
        results = []

        for standard in self._standards.values():
            # 关键词匹配
            if keyword.lower() not in standard.name.lower() and \
               keyword.lower() not in standard.content.lower() and \
               keyword.lower() not in standard.code.lower():
                continue

            # 分类筛选
            if category and standard.category != category:
                continue

            results.append(standard)

            if len(results) >= limit:
                break

        return results

    def get_standard_by_code(self, code: str) -> Optional[StandardItem]:
        """根据编号获取规范"""
        return self._standards.get(code)

    def get_standards_by_category(self, category: str) -> List[StandardItem]:
        """根据分类获取规范"""
        return [
            s for s in self._standards.values()
            if s.category == category
        ]

    # ========== 施工工艺查询 ==========

    def search_processes(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[ProcessItem]:
        """
        搜索施工工艺

        Args:
            keyword: 关键词
            category: 分类筛选 (可选)
            limit: 返回数量限制

        Returns:
            工艺列表
        """
        results = []

        for process in self._processes.values():
            # 关键词匹配
            if keyword.lower() not in process.name.lower() and \
               keyword.lower() not in " ".join(process.key_points).lower():
                continue

            # 分类筛选
            if category and process.category != category:
                continue

            results.append(process)

            if len(results) >= limit:
                break

        return results

    def get_process_by_name(self, name: str) -> Optional[ProcessItem]:
        """根据名称获取工艺"""
        return self._processes.get(name)

    def get_processes_by_category(self, category: str) -> List[ProcessItem]:
        """根据分类获取工艺"""
        return [
            p for p in self._processes.values()
            if p.category == category
        ]

    # ========== 质量问题查询 ==========

    def search_quality_issues(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[QualityIssue]:
        """
        搜索质量问题

        Args:
            keyword: 关键词
            category: 分类筛选 (可选)
            limit: 返回数量限制

        Returns:
            问题列表
        """
        results = []

        for issue in self._quality_issues.values():
            # 关键词匹配
            if keyword.lower() not in issue.name.lower() and \
               keyword.lower() not in issue.description.lower() and \
               keyword.lower() not in " ".join(issue.causes).lower():
                continue

            # 分类筛选
            if category and issue.category != category:
                continue

            results.append(issue)

            if len(results) >= limit:
                break

        return results

    def get_quality_issue_by_name(self, name: str) -> Optional[QualityIssue]:
        """根据名称获取质量问题"""
        return self._quality_issues.get(name)

    def get_quality_issues_by_category(self, category: str) -> List[QualityIssue]:
        """根据分类获取质量问题"""
        return [
            i for i in self._quality_issues.values()
            if i.category == category
        ]

    # ========== 综合查询 ==========

    def search_all(
        self,
        keyword: str,
        category: Optional[str] = None,
    ) -> Dict[str, List[Any]]:
        """
        综合搜索 (同时搜索规范、工艺、质量问题)

        Args:
            keyword: 关键词
            category: 分类筛选 (可选)

        Returns:
            搜索结果 {"standards": [...], "processes": [...], "issues": [...]}
        """
        return {
            "standards": self.search_standards(keyword, category),
            "processes": self.search_processes(keyword, category),
            "issues": self.search_quality_issues(keyword),
        }

    def get_context_for_ai(
        self,
        keyword: str,
        max_items: int = 5,
    ) -> str:
        """
        获取AI上下文字符串

        Args:
            keyword: 关键词
            max_items: 最大条目数

        Returns:
            格式化的上下文字符串
        """
        results = self.search_all(keyword)

        context_parts = []

        # 添加规范
        standards = results.get("standards", [])[:max_items]
        if standards:
            context_parts.append("【相关施工规范】")
            for s in standards:
                context_parts.append(f"- {s.code} {s.name}: {s.content[:200]}")

        # 添加工艺
        processes = results.get("processes", [])[:max_items]
        if processes:
            context_parts.append("\n【相关施工工艺】")
            for p in processes:
                context_parts.append(f"- {p.name}: {', '.join(p.key_points[:3])}")

        # 添加质量问题
        issues = results.get("issues", [])[:max_items]
        if issues:
            context_parts.append("\n【相关质量问题】")
            for i in issues:
                context_parts.append(f"- {i.name}: {i.solutions[0] if i.solutions else ''}")

        return "\n".join(context_parts) if context_parts else "未找到相关知识"


# 全局知识库实例
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base(base_path: Optional[str] = None) -> KnowledgeBase:
    """获取全局知识库实例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase(base_path)
    return _knowledge_base


def reload_knowledge_base() -> None:
    """重新加载知识库"""
    global _knowledge_base
    _knowledge_base = None
    _knowledge_base = KnowledgeBase()

# -*- coding: utf-8 -*-
"""
施工指挥舱仪表盘API
Dashboard API for Construction Command Center
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum


router = APIRouter(prefix="/api/v1/dashboard", tags=["施工指挥舱"])


# ========== 枚举类型 ==========

class SectionType(str, Enum):
    """施工段类型"""
    FOUNDATION = "foundation"  # 基础工程
    STRUCTURE = "structure"   # 结构工程
    ARCHITECTURE = "architecture"  # 装饰工程
    MEP = "mep"  # 机电工程


class IssueSeverity(str, Enum):
    """问题严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    """问题状态"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


# ========== 进度API模型 ==========

class ProgressReport(BaseModel):
    """进度上报请求"""
    section: str = Field(..., description="施工段ID")
    progress: float = Field(..., ge=0, le=100, description="进度百分比")
    completed_work: Optional[Dict[str, Any]] = Field(default=None, description="已完成工作量")
    current_phase: Optional[str] = Field(default=None, description="当前施工阶段")
    worker_count: Optional[int] = Field(default=None, description="现场人员数")
    equipment_status: Optional[Dict[str, Any]] = Field(default=None, description="设备状态")
    notes: Optional[str] = Field(default=None, description="备注")
    reporter: Optional[str] = Field(default=None, description="上报人")
    timestamp: Optional[datetime] = Field(default=None, description="上报时间")


class ProgressSection(BaseModel):
    """施工段进度"""
    section_id: str
    section_name: str
    progress: float
    planned_completion: Optional[datetime]
    actual_completion: Optional[datetime]
    status: str
    critical_path: bool = False


class ProgressData(BaseModel):
    """项目进度数据"""
    project_id: str
    project_name: str
    overall_progress: float
    start_date: datetime
    planned_end_date: datetime
    actual_end_date: Optional[datetime]
    sections: List[ProgressSection]
    last_updated: datetime


# ========== 质量API模型 ==========

class QualityIssue(BaseModel):
    """质量问题记录请求"""
    section: str = Field(..., description="施工段ID")
    issue_type: str = Field(..., description="问题类型")
    description: str = Field(..., description="问题描述")
    severity: IssueSeverity = Field(..., description="严重程度")
    location: Optional[Dict[str, Any]] = Field(default=None, description="位置")
    related_component: Optional[str] = Field(default=None, description="关联构件")
    reporter: Optional[str] = Field(default=None, description="上报人")
    assignee: Optional[str] = Field(default=None, description="负责人")
    photos: Optional[List[str]] = Field(default=None, description="照片URL列表")


class QualityIssueResponse(BaseModel):
    """质量问题响应"""
    issue_id: str
    section: str
    issue_type: str
    description: str
    severity: IssueSeverity
    status: IssueStatus
    location: Optional[Dict[str, Any]]
    related_component: Optional[str]
    reporter: str
    assignee: Optional[str]
    photos: List[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]


class QualityStats(BaseModel):
    """质量问题统计"""
    total_issues: int
    open_issues: int
    resolved_issues: int
    closed_issues: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_section: Dict[str, int]
    resolution_rate: float


class QualityTrend(BaseModel):
    """质量趋势数据点"""
    date: datetime
    issue_count: int
    resolved_count: int
    open_count: int
    avg_resolution_days: Optional[float]


# ========== 安全API模型 ==========

class SafetyStat(BaseModel):
    """安全统计数据"""
    total_incidents: int
    minor_incidents: int
    major_incidents: int
    lost_time_injuries: int
    safe_working_days: int
    safety_score: float
    last_incident_date: Optional[datetime]
    hazard_identified: int
    hazard_resolved: int


class SafetyRisk(BaseModel):
    """安全隐患"""
    risk_id: str
    risk_type: str
    description: str
    level: RiskLevel
    location: Dict[str, Any]
    section: str
    status: str
    identified_date: datetime
    due_date: Optional[datetime]
    assignee: Optional[str]
    mitigation_measures: List[str]


# ========== 成本API模型 ==========

class CostData(BaseModel):
    """成本数据"""
    project_id: str
    total_budget: float
    actual_cost: float
    committed_cost: float
    forecast_final: float
    earned_value: float
    spi: float  # 进度绩效指数
    cpi: float  # 成本绩效指数
    cost_variance: float
    schedule_variance: float
    last_updated: datetime


class BudgetComparison(BaseModel):
    """预算对比"""
    category: str
    budgeted_cost: float
    actual_cost: float
    committed_cost: float
    variance: float
    variance_percent: float
    forecast: float


# ========== 模拟数据存储 ==========

# 模拟进度数据
MOCK_PROGRESS_DATA = {
    "project_id": "NS-2026-001",
    "project_name": " NeuralSite 智能施工指挥舱项目",
    "overall_progress": 45.5,
    "start_date": datetime(2026, 1, 1),
    "planned_end_date": datetime(2026, 12, 31),
    "actual_end_date": None,
    "sections": [
        {
            "section_id": "foundation",
            "section_name": "基础工程",
            "progress": 95.0,
            "planned_completion": datetime(2026, 2, 28),
            "actual_completion": datetime(2026, 2, 25),
            "status": "completed",
            "critical_path": True
        },
        {
            "section_id": "structure",
            "section_name": "结构工程",
            "progress": 68.0,
            "planned_completion": datetime(2026, 6, 30),
            "actual_completion": None,
            "status": "in_progress",
            "critical_path": True
        },
        {
            "section_id": "architecture",
            "section_name": "装饰工程",
            "progress": 20.0,
            "planned_completion": datetime(2026, 9, 30),
            "actual_completion": None,
            "status": "in_progress",
            "critical_path": False
        },
        {
            "section_id": "mep",
            "section_name": "机电工程",
            "progress": 15.0,
            "planned_completion": datetime(2026, 11, 30),
            "actual_completion": None,
            "status": "in_progress",
            "critical_path": False
        }
    ],
    "last_updated": datetime.now()
}

# 模拟质量问题数据
MOCK_QUALITY_ISSUES = [
    {
        "issue_id": "QI-001",
        "section": "structure",
        "issue_type": "焊接质量",
        "description": "2层梁柱节点焊缝质量不达标",
        "severity": "high",
        "status": "in_progress",
        "location": {"floor": 2, "grid": "B-3"},
        "related_component": "COL-B-3",
        "reporter": "张工",
        "assignee": "李工",
        "photos": [],
        "created_at": datetime.now() - timedelta(days=3),
        "updated_at": datetime.now() - timedelta(days=1),
        "resolved_at": None
    },
    {
        "issue_id": "QI-002",
        "section": "architecture",
        "issue_type": "平整度",
        "description": "墙面平整度超规范",
        "severity": "medium",
        "status": "open",
        "location": {"floor": 3, "area": "A区"},
        "related_component": "WALL-A-3",
        "reporter": "王工",
        "assignee": None,
        "photos": [],
        "created_at": datetime.now() - timedelta(days=1),
        "updated_at": datetime.now() - timedelta(hours=6),
        "resolved_at": None
    }
]

# 模拟安全风险数据
MOCK_SAFETY_RISKS = [
    {
        "risk_id": "SR-001",
        "risk_type": "高空作业",
        "description": "3层外架临边防护不到位",
        "level": "high",
        "location": {"floor": 3, "side": "东"},
        "section": "structure",
        "status": "open",
        "identified_date": datetime.now() - timedelta(days=2),
        "due_date": datetime.now() + timedelta(days=1),
        "assignee": "安全员老陈",
        "mitigation_measures": ["立即增设安全网", "设置警示标志", "限制作业区域"]
    },
    {
        "risk_id": "SR-002",
        "risk_type": "临时用电",
        "description": "配电箱未接地",
        "level": "medium",
        "location": {"area": "施工区B"},
        "section": "structure",
        "status": "in_progress",
        "identified_date": datetime.now() - timedelta(days=5),
        "due_date": datetime.now() + timedelta(days=2),
        "assignee": "电工老周",
        "mitigation_measures": ["立即接地整改", "增加漏电保护"]
    }
]


# ========== 进度API端点 ==========

@router.get("/progress", response_model=ProgressData)
async def get_progress():
    """获取项目进度数据"""
    return MOCK_PROGRESS_DATA


@router.get("/progress/{section}")
async def get_section_progress(section: str):
    """获取指定施工段进度"""
    section_data = next(
        (s for s in MOCK_PROGRESS_DATA["sections"] if s["section_id"] == section),
        None
    )
    
    if section_data is None:
        raise HTTPException(status_code=404, detail=f"施工段 '{section}' 不存在")
    
    return {
        "section": section_data,
        "milestones": [
            {"name": "开始", "completed": True, "date": MOCK_PROGRESS_DATA["start_date"]},
            {"name": "完成", "completed": section_data["progress"] >= 100, 
             "date": section_data.get("actual_completion") or section_data.get("planned_completion")}
        ],
        "resources": {
            "labor": {"current": 45, "planned": 50},
            "materials": {"available": True},
            "equipment": {"status": "normal"}
        }
    }


@router.post("/progress")
async def report_progress(report: ProgressReport):
    """上报施工进度"""
    # 实际应用中这里会写入数据库
    
    section = report.section
    progress = report.progress
    
    # 更新模拟数据
    for s in MOCK_PROGRESS_DATA["sections"]:
        if s["section_id"] == section:
            s["progress"] = progress
            if progress >= 100:
                s["status"] = "completed"
                s["actual_completion"] = datetime.now()
    
    # 重新计算整体进度
    total = sum(s["progress"] for s in MOCK_PROGRESS_DATA["sections"])
    MOCK_PROGRESS_DATA["overall_progress"] = total / len(MOCK_PROGRESS_DATA["sections"])
    MOCK_PROGRESS_DATA["last_updated"] = datetime.now()
    
    return {
        "success": True,
        "message": f"施工段 '{section}' 进度已更新为 {progress}%",
        "updated": MOCK_PROGRESS_DATA
    }


# ========== 质量API端点 ==========

@router.get("/quality", response_model=QualityStats)
async def get_quality_stats():
    """获取质量问题统计"""
    issues = MOCK_QUALITY_ISSUES
    
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    by_type = {}
    by_section = {}
    
    for issue in issues:
        # 按严重程度统计
        by_severity[issue["severity"]] += 1
        
        # 按类型统计
        issue_type = issue["issue_type"]
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
        
        # 按施工段统计
        section = issue["section"]
        by_section[section] = by_section.get(section, 0) + 1
    
    resolved = sum(1 for i in issues if i["status"] in ["resolved", "closed"])
    
    return {
        "total_issues": len(issues),
        "open_issues": sum(1 for i in issues if i["status"] == "open"),
        "resolved_issues": sum(1 for i in issues if i["status"] == "resolved"),
        "closed_issues": sum(1 for i in issues if i["status"] == "closed"),
        "by_severity": by_severity,
        "by_type": by_type,
        "by_section": by_section,
        "resolution_rate": resolved / len(issues) * 100 if issues else 0
    }


@router.get("/quality/trends")
async def get_quality_trends(days: int = 30):
    """获取质量趋势分析"""
    # 生成模拟趋势数据
    trends = []
    base_date = datetime.now()
    
    for i in range(days, 0, -1):
        date = base_date - timedelta(days=i)
        trend_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 模拟数据
        issues_count = max(0, 5 - i // 10 + (i % 3))
        resolved_count = max(0, 3 - i // 15 + (i % 2))
        open_count = max(0, issues_count - resolved_count)
        
        trends.append({
            "date": trend_date.isoformat(),
            "issue_count": issues_count,
            "resolved_count": resolved_count,
            "open_count": open_count,
            "avg_resolution_days": 2.5 if i < 20 else None
        })
    
    return {
        "period_days": days,
        "trends": trends,
        "summary": {
            "total_new_issues": sum(t["issue_count"] for t in trends),
            "total_resolved": sum(t["resolved_count"] for t in trends),
            "avg_daily_issues": sum(t["issue_count"] for t in trends) / days,
            "trend_direction": "improving" if trends[-1]["open_count"] < trends[0]["open_count"] else "stable"
        }
    }


@router.post("/quality/issue", response_model=QualityIssueResponse)
async def create_quality_issue(issue: QualityIssue):
    """记录新的质量问题"""
    import uuid
    
    now = datetime.now()
    new_issue = {
        "issue_id": f"QI-{len(MOCK_QUALITY_ISSUES) + 1:03d}",
        "section": issue.section,
        "issue_type": issue.issue_type,
        "description": issue.description,
        "severity": issue.severity.value,
        "status": "open",
        "location": issue.location,
        "related_component": issue.related_component,
        "reporter": issue.reporter or "Anonymous",
        "assignee": issue.assignee,
        "photos": issue.photos or [],
        "created_at": now,
        "updated_at": now,
        "resolved_at": None
    }
    
    MOCK_QUALITY_ISSUES.append(new_issue)
    
    return new_issue


# ========== 安全API端点 ==========

@router.get("/safety", response_model=SafetyStat)
async def get_safety_stats():
    """获取安全统计数据"""
    risks = MOCK_SAFETY_RISKS
    
    return {
        "total_incidents": 2,
        "minor_incidents": 1,
        "major_incidents": 1,
        "lost_time_injuries": 0,
        "safe_working_days": 63,
        "safety_score": 92.5,
        "last_incident_date": datetime.now() - timedelta(days=15),
        "hazard_identified": len(risks),
        "hazard_resolved": sum(1 for r in risks if r["status"] == "resolved")
    }


@router.get("/safety/risks")
async def get_safety_risks(
    level: Optional[RiskLevel] = None,
    status: Optional[str] = None,
    section: Optional[str] = None
):
    """获取隐患列表
    
    支持过滤:
    - level: 风险等级
    - status: 状态 (open/in_progress/resolved)
    - section: 施工段
    """
    risks = MOCK_SAFETY_RISKS.copy()
    
    if level:
        risks = [r for r in risks if r["level"] == level.value]
    if status:
        risks = [r for r in risks if r["status"] == status]
    if section:
        risks = [r for r in risks if r["section"] == section]
    
    # 统计摘要
    summary = {
        "total": len(risks),
        "by_level": {
            "low": sum(1 for r in risks if r["level"] == "low"),
            "medium": sum(1 for r in risks if r["level"] == "medium"),
            "high": sum(1 for r in risks if r["level"] == "high"),
            "extreme": sum(1 for r in risks if r["level"] == "extreme")
        },
        "by_status": {
            "open": sum(1 for r in risks if r["status"] == "open"),
            "in_progress": sum(1 for r in risks if r["status"] == "in_progress"),
            "resolved": sum(1 for r in risks if r["status"] == "resolved")
        }
    }
    
    return {
        "risks": risks,
        "summary": summary
    }


# ========== 成本API端点 ==========

@router.get("/cost", response_model=CostData)
async def get_cost_data():
    """获取成本数据"""
    return {
        "project_id": "NS-2026-001",
        "total_budget": 5000000.0,
        "actual_cost": 2250000.0,
        "committed_cost": 2450000.0,
        "forecast_final": 5100000.0,
        "earned_value": 2275000.0,
        "spi": 0.98,
        "cpi": 1.01,
        "cost_variance": 25000.0,
        "schedule_variance": -50000.0,
        "last_updated": datetime.now()
    }


@router.get("/cost/budget")
async def get_budget_comparison():
    """获取预算对比分析"""
    categories = [
        {"category": "人工费", "budgeted_cost": 1500000, "actual_cost": 680000, "committed_cost": 720000},
        {"category": "材料费", "budgeted_cost": 2000000, "actual_cost": 920000, "committed_cost": 1000000},
        {"category": "机械费", "budgeted_cost": 800000, "actual_cost": 350000, "committed_cost": 380000},
        {"category": "管理费", "budgeted_cost": 500000, "actual_cost": 200000, "committed_cost": 250000},
        {"category": "其他费", "budgeted_cost": 200000, "actual_cost": 100000, "committed_cost": 100000}
    ]
    
    comparisons = []
    total_budgeted = 0
    total_actual = 0
    total_committed = 0
    
    for cat in categories:
        variance = cat["actual_cost"] - cat["budgeted_cost"]
        variance_percent = (variance / cat["budgeted_cost"] * 100) if cat["budgeted_cost"] > 0 else 0
        
        comparisons.append({
            "category": cat["category"],
            "budgeted_cost": cat["budgeted_cost"],
            "actual_cost": cat["actual_cost"],
            "committed_cost": cat["committed_cost"],
            "variance": variance,
            "variance_percent": round(variance_percent, 2),
            "forecast": cat["budgeted_cost"] + (cat["committed_cost"] - cat["budgeted_cost"]) * 0.5
        })
        
        total_budgeted += cat["budgeted_cost"]
        total_actual += cat["actual_cost"]
        total_committed += cat["committed_cost"]
    
    return {
        "categories": comparisons,
        "summary": {
            "total_budgeted": total_budgeted,
            "total_actual": total_actual,
            "total_committed": total_committed,
            "total_variance": total_actual - total_budgeted,
            "variance_percent": round((total_actual - total_budgeted) / total_budgeted * 100, 2) if total_budgeted > 0 else 0,
            "cost_status": "under_budget" if total_actual < total_budgeted else "over_budget"
        }
    }


# ========== 汇总仪表盘端点 ==========

@router.get("/summary")
async def get_dashboard_summary():
    """获取仪表盘汇总数据"""
    progress = await get_progress()
    quality = await get_quality_stats()
    safety = await get_safety_stats()
    cost = await get_cost_data()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "project": {
            "id": progress["project_id"],
            "name": progress["project_name"],
            "overall_progress": progress["overall_progress"]
        },
        "progress": {
            "overall": progress["overall_progress"],
            "critical_path_on_track": True,
            "upcoming_milestones": [
                {"name": "结构封顶", "date": "2026-04-15", "days_remaining": 42}
            ]
        },
        "quality": {
            "open_issues": quality["open_issues"],
            "resolution_rate": quality["resolution_rate"],
            "critical_issues": quality["by_severity"].get("critical", 0) + quality["by_severity"].get("high", 0)
        },
        "safety": {
            "score": safety["safety_score"],
            "safe_days": safety["safe_working_days"],
            "open_risks": safety["hazard_identified"]
        },
        "cost": {
            "spi": cost["spi"],
            "cpi": cost["cpi"],
            "variance": cost["cost_variance"],
            "health": "green" if cost["cpi"] >= 0.95 else "yellow"
        },
        "alerts": [
            {"type": "warning", "message": "2层焊接质量问题待处理", "source": "quality"},
            {"type": "danger", "message": "3层外架存在高风险隐患", "source": "safety"}
        ]
    }

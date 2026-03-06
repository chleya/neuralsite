# -*- coding: utf-8 -*-
"""
需求解析器 - 增强版
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class RequirementType(Enum):
    """需求类型"""
    QUERY = "query"           # 查询
    REPORT = "report"         # 报表
    CHART = "chart"           # 图表
    CHART_LINE = "chart:line"     # 趋势图
    CHART_PIE = "chart:pie"      # 分布图
    CHART_BAR = "chart:bar"       # 对比图
    PAGE = "page"             # 页面
    DISPLAY = "display"       # 展示
    COUNT = "count"           # 统计数量
    API = "api"               # 接口


@dataclass
class ParsedRequirement:
    """解析后的需求"""
    type: RequirementType
    data_sources: List[str]
    filters: Dict[str, Any]
    visualization: Optional[str] = None
    raw_requirement: str = ""
    fields: List[str] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []


class RequirementParser:
    """需求解析器 - 增强版"""
    
    # 支持的需求模式 (正则匹配 -> 类型)
    PATTERNS = {
        # 查询类
        r"查.*?(问题|照片|进度|材料|设备)": "query",
        r"(问题|照片|进度|材料|设备).*?列表": "query",
        r"查看.*?": "query",
        r"搜索": "query",
        r"查找": "query",
        
        # 统计类
        r"(统计|汇总|合计).*?(问题|进度|质量)": "report",
        r"报表": "report",
        r"汇总表": "report",
        
        # 计数类
        r".*?有多少": "count",
        r"数量": "count",
        r"多少个": "count",
        
        # 图表类
        r".*?趋势图": "chart:line",
        r".*?折线图": "chart:line",
        r".*?分布图": "chart:pie",
        r".*?饼图": "chart:pie",
        r".*?占比": "chart:pie",
        r".*?对比": "chart:bar",
        r".*?柱状图": "chart:bar",
        r".*?条形图": "chart:bar",
        
        # 页面类
        r"做一个.*?页面": "page",
        r"新建.*?页面": "page",
        r"创建.*?页面": "page",
        
        # 展示类
        r"展示.*?": "display",
        r"显示.*?": "display",
        r"查看.*?": "display",
    }
    
    # 关键词映射
    KEYWORDS = {
        "查询": RequirementType.QUERY,
        "统计": RequirementType.REPORT,
        "报表": RequirementType.REPORT,
        "图表": RequirementType.CHART,
        "页面": RequirementType.PAGE,
        "接口": RequirementType.API,
        "展示": RequirementType.DISPLAY,
    }
    
    # 数据源关键词
    DATA_SOURCE_KEYWORDS = {
        "问题": "issues",
        "照片": "photos",
        "进度": "progress",
        "质量": "quality",
        "安全": "safety",
        "材料": "materials",
        "设备": "equipment",
        "人员": "staff",
        "施工": "construction",
        "验收": "acceptance",
    }
    
    # 图表类型关键词
    CHART_KEYWORDS = {
        "趋势": "line_chart",
        "趋势图": "line_chart",
        "折线": "line_chart",
        "分布": "pie_chart",
        "占比": "pie_chart",
        "饼图": "pie_chart",
        "对比": "bar_chart",
        "柱状": "bar_chart",
        "条形": "bar_chart",
        "热力": "heatmap",
    }
    
    # 字段关键词
    FIELD_KEYWORDS = {
        "数量": "count(*)",
        "总数": "count(*)",
        "合计": "count(*)",
        "日期": "created_at",
        "时间": "created_at",
        "状态": "status",
        "类型": "type",
        "名称": "name",
        "描述": "description",
        "负责人": "owner",
        "部门": "department",
    }
    
    def parse(self, requirement: str) -> ParsedRequirement:
        """
        解析需求文本
        
        Args:
            requirement: 需求文本
            
        Returns:
            解析结果
        """
        # 识别需求类型
        req_type = self._detect_type(requirement)
        
        # 识别数据源
        data_sources = self._detect_data_sources(requirement)
        
        # 识别过滤条件
        filters = self._detect_filters(requirement)
        
        # 识别可视化类型
        visualization = self._detect_visualization(requirement)
        
        # 识别字段
        fields = self._detect_fields(requirement)
        
        return ParsedRequirement(
            type=req_type,
            data_sources=data_sources,
            filters=filters,
            visualization=visualization,
            raw_requirement=requirement,
            fields=fields
        )
    
    def _detect_type(self, text: str) -> RequirementType:
        """识别需求类型 - 使用正则模式匹配"""
        # 关键类型优先检测 - 图表类必须在查询类之前检测
        # 因为某些查询模式会错误匹配包含图表关键词的文本
        
        # 先检测图表类 (最高优先级)
        chart_patterns = [
            (r".*?趋势图", "chart:line"),
            (r".*?折线图", "chart:line"),
            (r".*?分布图", "chart:pie"),
            (r".*?饼图", "chart:pie"),
            (r".*?占比", "chart:pie"),
            (r".*?对比", "chart:bar"),
            (r".*?柱状图", "chart:bar"),
            (r".*?条形图", "chart:bar"),
        ]
        
        for pattern, req_type_str in chart_patterns:
            if re.search(pattern, text):
                try:
                    return RequirementType(req_type_str)
                except ValueError:
                    pass
        
        # 再检测其他模式
        for pattern, req_type_str in self.PATTERNS.items():
            if re.search(pattern, text):
                try:
                    return RequirementType(req_type_str)
                except ValueError:
                    pass
        
        # 回退到关键词匹配 (按优先级)
        keyword_priority = [
            "图表", "页面", "统计", "报表", "数量", "查询", "接口", "展示"
        ]
        for kw in keyword_priority:
            if kw in text:
                return self.KEYWORDS.get(kw, RequirementType.QUERY)
        
        return RequirementType.QUERY
    
    def _detect_data_sources(self, text: str) -> List[str]:
        """识别数据源"""
        sources = []
        for keyword, source in self.DATA_SOURCE_KEYWORDS.items():
            if keyword in text:
                sources.append(source)
        
        # 默认返回通用数据源
        if not sources:
            sources = ["default"]
        
        return sources
    
    def _detect_filters(self, text: str) -> Dict[str, Any]:
        """识别过滤条件"""
        filters = {}
        
        # 桩号范围
        station_match = re.search(r'K?(\d+)\+(\d+)\s*[-~至到]\s*K?(\d+)\+(\d+)', text)
        if station_match:
            filters["station_start"] = f"K{station_match.group(1)}+{station_match.group(2)}"
            filters["station_end"] = f"K{station_match.group(3)}+{station_match.group(4)}"
        
        # 时间范围
        time_match = re.search(r'(\d{4})[年/-](\d{1,2})[月]?\s*[-~至到]\s*(\d{4})[年/-](\d{1,2})', text)
        if time_match:
            filters["date_start"] = f"{time_match.group(1)}-{time_match.group(2)}"
            filters["date_end"] = f"{time_match.group(3)}-{time_match.group(4)}"
        
        # 简单时间 (今天/昨天/本周等)
        if "今天" in text:
            filters["date_start"] = "today"
            filters["date_end"] = "today"
        elif "昨天" in text:
            filters["date_start"] = "yesterday"
            filters["date_end"] = "yesterday"
        elif "本周" in text:
            filters["date_start"] = "this_week"
            filters["date_end"] = "this_week"
        elif "本月" in text:
            filters["date_start"] = "this_month"
            filters["date_end"] = "this_month"
        
        # 状态过滤
        for status in ["待处理", "处理中", "已完成", "已关闭", "已取消"]:
            if status in text:
                filters["status"] = status
        
        return filters
    
    def _detect_visualization(self, text: str) -> Optional[str]:
        """识别可视化类型"""
        for keyword, viz_type in self.CHART_KEYWORDS.items():
            if keyword in text:
                return viz_type
        return None
    
    def _detect_fields(self, text: str) -> List[str]:
        """识别需要的字段"""
        fields = []
        for keyword, field in self.FIELD_KEYWORDS.items():
            if keyword in text and field not in fields:
                fields.append(field)
        return fields


class CodeGenerator:
    """代码生成器 - 增强版"""
    
    # 代码模板
    TEMPLATES = {
        "query": {
            "sql": "SELECT {fields} FROM {table} WHERE {conditions}",
            "api": "async def get_{table}(filters): return await db.query(...)"
        },
        "report": {
            "sql": "SELECT {group_by}, COUNT(*) as count FROM {table} GROUP BY {group_by}",
            "template": "report.html"
        },
        "chart": {
            "echarts": "new EChartsoption({...})"
        }
    }
    
    def __init__(self):
        self.parser = RequirementParser()
    
    def generate(self, requirement: str) -> Dict[str, Any]:
        """
        根据需求生成代码
        
        Args:
            requirement: 需求文本
            
        Returns:
            生成的代码信息
        """
        # 解析需求
        parsed = self.parser.parse(requirement)
        
        # 根据类型生成不同代码
        if parsed.type == RequirementType.REPORT:
            return self._generate_report(parsed)
        elif parsed.type == RequirementType.CHART:
            return self._generate_chart(parsed)
        elif parsed.type == RequirementType.CHART_LINE:
            return self._generate_chart(parsed, "line")
        elif parsed.type == RequirementType.CHART_PIE:
            return self._generate_chart(parsed, "pie")
        elif parsed.type == RequirementType.CHART_BAR:
            return self._generate_chart(parsed, "bar")
        elif parsed.type == RequirementType.COUNT:
            return self._generate_count(parsed)
        elif parsed.type == RequirementType.QUERY:
            return self._generate_query(parsed)
        elif parsed.type == RequirementType.PAGE:
            return self._generate_page(parsed)
        else:
            return self._generate_default(parsed)
    
    def generate_api(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成API代码"""
        table = parsed.data_sources[0] if parsed.data_sources else "default"
        filters = parsed.filters
        
        # 构建SQL
        fields = ", ".join(parsed.fields) if parsed.fields else "*"
        conditions = self._build_conditions(filters)
        
        sql = f"SELECT {fields} FROM {table}"
        if conditions:
            sql += f" WHERE {conditions}"
        
        # 生成FastAPI代码
        api_code = f'''
@router.get("/{table}")
async def get_{table}({self._build_params(filters)}):
    """获取{table}数据"""
    query = """
        {sql}
    """
    result = await db.fetch_all(query, {self._build_params_dict(filters)})
    return {{"data": result, "total": len(result)}}
'''
        return {
            "type": "api",
            "sql": sql,
            "api_code": api_code.strip(),
            "filters": filters
        }
    
    def generate_page(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成页面代码"""
        table = parsed.data_sources[0] if parsed.data_sources else "default"
        
        # 页面代码
        page_code = f'''
<div id="app-{table}">
    <el-table :data="tableData" style="width: 100%">
        <el-table-column prop="id" label="ID" width="180"></el-table-column>
        <el-table-column prop="name" label="名称" width="200"></el-table-column>
        <el-table-column prop="status" label="状态"></el-table-column>
        <el-table-column prop="created_at" label="创建时间"></el-table-column>
    </el-table>
    <el-pagination
        @current-change="handlePageChange"
        :current-page="currentPage"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        :total="total">
    </el-pagination>
</div>
'''
        return {
            "type": "page",
            "page_code": page_code.strip(),
            "table": table,
            "visualization": parsed.visualization
        }
    
    def _build_conditions(self, filters: Dict[str, Any]) -> str:
        """构建SQL条件"""
        if not filters:
            return "1=1"
        
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = :{key}")
            else:
                conditions.append(f"{key} = :{key}")
        return " AND ".join(conditions)
    
    def _build_params(self, filters: Dict[str, Any]) -> str:
        """构建API参数"""
        if not filters:
            return ""
        
        params = []
        for key in filters.keys():
            params.append(f"{key}: str = None")
        return ", ".join(params)
    
    def _build_params_dict(self, filters: Dict[str, Any]) -> str:
        """构建参数字典"""
        if not filters:
            return "{}"
        
        return "{" + ", ".join([f'"{k}": {k}' for k in filters.keys()]) + "}"
    
    def _generate_report(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成报表代码"""
        table = parsed.data_sources[0] if parsed.data_sources else "default"
        
        # 构建SQL
        group_by = parsed.fields[0] if parsed.fields else "DATE(created_at)"
        sql = f"SELECT {group_by}, COUNT(*) as count FROM {table}"
        
        if parsed.filters:
            conditions = self._build_conditions(parsed.filters)
            sql += f" WHERE {conditions}"
        
        sql += f" GROUP BY {group_by} ORDER BY count DESC"
        
        return {
            "type": "report",
            "sql": sql,
            "filters": parsed.filters,
            "template": "report_table.html",
            "chart_type": parsed.visualization
        }
    
    def _generate_chart(self, parsed: ParsedRequirement, chart_type: str = None) -> Dict[str, Any]:
        """生成图表代码"""
        table = parsed.data_sources[0] if parsed.data_sources else "default"
        
        # 确定图表类型
        if chart_type is None:
            if parsed.visualization:
                chart_type = parsed.visualization.replace("_chart", "")
            else:
                chart_type = "bar"
        
        # 构建SQL
        group_by = parsed.fields[0] if parsed.fields else "DATE(created_at)"
        sql = f"SELECT {group_by} as x, COUNT(*) as y FROM {table}"
        
        if parsed.filters:
            conditions = self._build_conditions(parsed.filters)
            sql += f" WHERE {conditions}"
        
        sql += f" GROUP BY {group_by}"
        
        # ECharts配置
        echarts_config = {
            "type": chart_type,
            "title": f"{table}统计",
            "x_field": "x",
            "y_field": "y"
        }
        
        return {
            "type": "chart",
            "chart_type": chart_type,
            "sql": sql,
            "filters": parsed.filters,
            "echarts_config": echarts_config
        }
    
    def _generate_count(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成计数统计代码"""
        table = parsed.data_sources[0] if parsed.data_sources else "default"
        
        # 构建SQL
        sql = f"SELECT COUNT(*) as total FROM {table}"
        
        if parsed.filters:
            conditions = self._build_conditions(parsed.filters)
            sql += f" WHERE {conditions}"
        
        return {
            "type": "count",
            "sql": sql,
            "filters": parsed.filters,
            "result_field": "total"
        }
    
    def _generate_query(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成查询代码"""
        table = parsed.data_sources[0] if parsed.data_sources else "default"
        
        # 构建SQL
        fields = ", ".join(parsed.fields) if parsed.fields else "*"
        sql = f"SELECT {fields} FROM {table}"
        
        if parsed.filters:
            conditions = self._build_conditions(parsed.filters)
            sql += f" WHERE {conditions}"
        
        return {
            "type": "query",
            "sql": sql,
            "filters": parsed.filters,
            "table": table
        }
    
    def _generate_page(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成页面代码"""
        return self.generate_page(parsed)
    
    def _generate_default(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """生成默认代码"""
        return {
            "type": "unknown",
            "message": "Requirement type not recognized",
            "detected_type": parsed.type.value
        }


# -*- coding: utf-8 -*-
"""
功能生成模块

你提需求，我来生成代码
"""

__version__ = "1.0.0"

__all__ = ["RequirementParser", "CodeGenerator", "ParsedRequirement", "RequirementType"]

# -*- coding: utf-8 -*-
"""大屏布局模块"""


class DashboardLayout:
    """大屏布局"""
    
    LAYOUTS = {
        "overview": {
            "title": "总览大屏",
            "rows": [
                {"cols": [
                    {"widget": "kpi", "span": 3},
                    {"widget": "kpi", "span": 3},
                    {"widget": "kpi", "span": 3},
                    {"widget": "kpi", "span": 3}
                ]},
                {"cols": [
                    {"widget": "map", "span": 8},
                    {"widget": "issues", "span": 4}
                ]},
                {"cols": [
                    {"widget": "progress", "span": 6},
                    {"widget": "quality", "span": 6}
                ]}
            ]
        },
        "quality": {
            "title": "质量大屏",
            "rows": [
                {"cols": [
                    {"widget": "kpi", "span": 4},
                    {"widget": "kpi", "span": 4},
                    {"widget": "kpi", "span": 4}
                ]},
                {"cols": [
                    {"widget": "quality_trend", "span": 8},
                    {"widget": "issue_types", "span": 4}
                ]},
                {"cols": [
                    {"widget": "severity_dist", "span": 6},
                    {"widget": "top_issues", "span": 6}
                ]}
            ]
        },
        "safety": {
            "title": "安全大屏",
            "rows": [
                {"cols": [
                    {"widget": "kpi", "span": 3},
                    {"widget": "kpi", "span": 3},
                    {"widget": "kpi", "span": 3},
                    {"widget": "kpi", "span": 3}
                ]},
                {"cols": [
                    {"widget": "safety_map", "span": 8},
                    {"widget": "alerts", "span": 4}
                ]},
                {"cols": [
                    {"widget": "safety_trend", "span": 6},
                    {"widget": "hazard_types", "span": 6}
                ]}
            ]
        }
    }
    
    @classmethod
    def get_layout(cls, layout_name: str) -> dict:
        """获取指定布局"""
        return cls.LAYOUTS.get(layout_name, cls.LAYOUTS["overview"])
    
    @classmethod
    def list_layouts(cls) -> list:
        """列出所有可用布局"""
        return list(cls.LAYOUTS.keys())

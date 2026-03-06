# -*- coding: utf-8 -*-
"""可视化组件库"""


class ChartComponent:
    """图表组件"""
    
    @staticmethod
    def line_chart(data: list, x_field: str, y_field: str) -> dict:
        """折线图"""
        return {
            "type": "line",
            "data": data,
            "xField": x_field,
            "yField": y_field
        }
    
    @staticmethod
    def bar_chart(data: list, category_field: str, value_field: str) -> dict:
        """柱状图"""
        return {
            "type": "bar",
            "data": data,
            "xField": category_field,
            "yField": value_field
        }
    
    @staticmethod
    def pie_chart(data: list, name_field: str, value_field: str) -> dict:
        """饼图"""
        return {
            "type": "pie",
            "data": data,
            "nameField": name_field,
            "valueField": value_field
        }
    
    @staticmethod
    def heatmap(data: list, x_field: str, y_field: str, value_field: str) -> dict:
        """热力图"""
        return {
            "type": "heatmap",
            "data": data,
            "xField": x_field,
            "yField": y_field,
            "valueField": value_field
        }

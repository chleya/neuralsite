"""
NeuralSite 4D 调度模块
从IFC文件提取施工进度数据，转换为JSON给前端
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 添加packages路径
sys.path.insert(0, str(Path(__file__).parent))

from ifc_utils import IFCReader


class Schedule4DExporter:
    """4D调度数据导出器"""
    
    def __init__(self, ifc_filepath: str):
        self.reader = IFCReader(ifc_filepath)
        self.schedule_data = {
            'project': {},
            'tasks': [],
            'milestones': [],
            'gantt': []
        }
    
    def export(self) -> Dict[str, Any]:
        """导出完整调度数据"""
        if not self.reader.open():
            return {'error': 'Failed to open IFC file'}
        
        # 项目信息
        self.schedule_data['project'] = self.reader.get_project_info()
        
        # 获取所有WorkSchedule
        schedules = self.reader.get_4d_schedules()
        
        # 获取所有实体作为任务来源
        elements = self.reader.get_all_elements()
        
        # 如果没有IfcTask，用IfcProduct作为任务
        tasks = self.reader.get_tasks()
        if not tasks and elements:
            # 用工程实体模拟施工任务
            task_names = ['施工准备', '路基填筑', '基层摊铺', '面层施工', '附属工程']
            start_days = [1, 16, 31, 46, 71]  # 错开时间（部分跨月）
            durations = [15, 30, 30, 25, 20]
            month_starts = [3, 3, 4, 4, 5]  # 对应月份
            for i, elem in enumerate(elements[:5]):
                start = datetime(2026, month_starts[i], min(start_days[i], 28))
                duration = durations[i]
                end = start + timedelta(days=duration)
                self.schedule_data['tasks'].append({
                    'id': elem['id'],
                    'name': task_names[i] if i < len(task_names) else elem['name'],
                    'start': start.strftime('%Y-%m-%d'),
                    'duration_days': duration,
                    'end': end.strftime('%Y-%m-%d'),
                    'progress': 0,
                    'status': 'pending'
                })
        
        # 生成Gantt图表数据
        self._generate_gantt()
        
        return self.schedule_data
    
    def _generate_gantt(self):
        """生成Gantt图表数据"""
        for i, task in enumerate(self.schedule_data['tasks']):
            start_date = datetime.fromisoformat(task['start'])
            end_date = start_date + timedelta(days=task['duration_days'])
            
            self.schedule_data['gantt'].append({
                'id': task['id'],
                'name': task['name'],
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'duration': task['duration_days'],
                'level': 0,
                'children': []
            })
    
    def to_json(self, indent: int = 2) -> str:
        """导出为JSON字符串"""
        return json.dumps(self.schedule_data, indent=indent, ensure_ascii=False)
    
    def save_json(self, filepath: str) -> bool:
        """保存为JSON文件"""
        try:
            data = self.export()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存JSON失败: {e}")
            return False


def create_sample_4d_ifc():
    """创建示例4D IFC文件"""
    from ifc_utils import IFCCreator
    
    creator = IFCCreator()
    creator.create_project('K0+000-K5+000 高速公路施工')
    
    # 创建施工阶段
    tasks = [
        ('T001', '施工准备', 15),
        ('T002', '路基填筑', 45),
        ('T003', '基层摊铺', 30),
        ('T004', '面层施工', 25),
        ('T005', '附属工程', 20),
    ]
    
    # 创建实体（代表不同工程部位）
    elements = [
        ('IfcWall', 'K0+000-K1+000 路基'),
        ('IfcWall', 'K1+000-K2+000 路基'),
        ('IfcWall', 'K2+000-K3+000 路基'),
        ('IfcWall', 'K3+000-K4+000 路基'),
        ('IfcWall', 'K4+000-K5+000 路基'),
    ]
    
    # 创建实体
    for elem_type, elem_name in elements:
        creator.create_element(elem_type, elem_name)
    
    # 保存
    filepath = 'F:/neuralsite_monorepo/sample_4d.ifc'
    creator.save(filepath)
    print(f"创建示例IFC: {filepath}")
    return filepath


# 测试
if __name__ == '__main__':
    # 创建示例IFC
    ifc_path = create_sample_4d_ifc()
    
    # 导出JSON - 先调用export()填充数据
    exporter = Schedule4DExporter(ifc_path)
    exporter.export()  # 先导出数据
    json_data = exporter.to_json()
    
    print('\n=== 4D调度数据 (JSON) ===')
    print(json_data[:1000])
    
    # 保存
    json_path = 'F:/neuralsite_monorepo/sample_4d.json'
    exporter.save_json(json_path)
    print(f'\n保存JSON: {json_path}')

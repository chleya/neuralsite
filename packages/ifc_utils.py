"""
NeuralSite IFC 处理模块
基于 ifcopenshell 实现 IFC 文件读取与解析
"""
import ifcopenshell
from typing import Dict, List, Any, Optional
from pathlib import Path


class IFCReader:
    """IFC文件读取器"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
        self.schema = None
    
    def open(self) -> bool:
        """打开IFC文件"""
        try:
            self.file = ifcopenshell.open(self.filepath)
            self.schema = self.file.schema
            return True
        except Exception as e:
            print(f"打开IFC失败: {e}")
            return False
    
    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        if not self.file:
            return {}
        
        project = self.file.by_type('IfcProject')
        if not project:
            return {}
        
        p = project[0]
        return {
            'name': p.Name,
            'schema': self.schema,
            'description': getattr(p, 'Description', None),
        }
    
    def get_all_elements(self) -> List[Dict[str, Any]]:
        """获取所有工程实体"""
        if not self.file:
            return []
        
        elements = []
        for elem in self.file.by_type('IfcProduct'):
            elements.append({
                'id': elem.id(),
                'type': elem.is_a(),
                'name': getattr(elem, 'Name', None),
                'global_id': getattr(elem, 'GlobalId', None),
            })
        return elements
    
    def get_elements_by_type(self, ifc_type: str) -> List[Any]:
        """按类型获取实体"""
        if not self.file:
            return []
        # IfcWall, IfcRoad, etc
        return self.file.by_type(ifc_type)
    
    def get_4d_schedules(self) -> List[Dict[str, Any]]:
        """获取4D调度数据"""
        if not self.file:
            return []
        
        schedules = []
        for schedule in self.file.by_type('IfcWorkSchedule'):
            schedules.append({
                'id': schedule.id(),
                'name': getattr(schedule, 'Name', None),
                'description': getattr(schedule, 'Description', None),
            })
        return schedules
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        if not self.file:
            return []
        
        tasks = []
        for task in self.file.by_type('IfcTask'):
            tasks.append({
                'id': task.id(),
                'name': getattr(task, 'Name', None),
                'description': getattr(task, 'Description', None),
            })
        return tasks
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            'project': self.get_project_info(),
            'elements': self.get_all_elements(),
            'schedules': self.get_4d_schedules(),
            'tasks': self.get_tasks(),
        }


class IFCCreator:
    """IFC文件创建器"""
    
    def __init__(self, schema: str = 'IFC4'):
        self.schema = schema
        self.file = ifcopenshell.file(schema=schema)
    
    def create_project(self, name: str, description: str = None) -> Any:
        """创建项目"""
        project = self.file.create_entity('IfcProject', Name=name)
        if description:
            project.Description = description
        return project
    
    def create_element(self, ifc_type: str, name: str, **kwargs) -> Any:
        """创建工程实体"""
        entity = self.file.create_entity(ifc_type, Name=name, **kwargs)
        return entity
    
    def save(self, filepath: str) -> bool:
        """保存IFC文件"""
        try:
            self.file.write(filepath)
            return True
        except Exception as e:
            print(f"保存IFC失败: {e}")
            return False


# 测试
if __name__ == '__main__':
    # 测试读取
    reader = IFCReader('F:/neuralsite_monorepo/test.ifc')
    if reader.open():
        print('=== IFC读取测试 ===')
        print(f"项目: {reader.get_project_info()}")
        print(f"实体数量: {len(reader.get_all_elements())}")
    
    # 测试创建
    creator = IFCCreator()
    creator.create_project('测试项目')
    creator.create_element('IfcWall', 'K0+000 路基')
    creator.save('F:/neuralsite_monorepo/test_created.ifc')
    print('创建IFC成功!')

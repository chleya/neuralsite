"""
NeuralSite 4D Service - Core Service
整合 IFC读取、4D调度生成、事件驱动
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 添加packages路径
packages_dir = Path(__file__).parent.parent
sys.path.insert(0, str(packages_dir))

from ifc_utils import IFCReader
from schedule_4d import Schedule4DExporter
from events_4d import Events4DGenerator


class FourDService:
    """4D施工模拟核心服务"""
    
    def __init__(self):
        self.events_gen = Events4DGenerator()
        self.ifc_reader = None
        self.schedule_exporter = None
    
    def get_schedule(self, project_id: str = "default", query_date: str = None) -> Dict[str, Any]:
        """
        获取4D调度数据
        优先用数据库事件，fallback到IFC文件
        """
        # 1. 尝试从数据库事件生成
        try:
            if query_date:
                schedule = self.events_gen.get_status_at_date(query_date)
            else:
                schedule = self.events_gen.generate_schedule()
            
            # 有事件数据就直接返回
            if schedule.get('tasks'):
                schedule['current_date'] = query_date or datetime.now().strftime('%Y-%m-%d')
                schedule['generated_at'] = datetime.now().isoformat()
                return schedule
        except Exception as e:
            print(f"从事件生成失败: {e}")
        
        # 2. Fallback到IFC文件
        return self._get_from_ifc(project_id)
    
    def _get_from_ifc(self, project_id: str) -> Dict[str, Any]:
        """从IFC文件获取4D数据"""
        # 查找IFC文件
        ifc_paths = [
            packages_dir / f"{project_id}_4d.ifc",
            packages_dir / "sample_4d.ifc",
            packages_dir / "test.ifc",
        ]
        
        for ifc_path in ifc_paths:
            if ifc_path.exists():
                try:
                    exporter = Schedule4DExporter(str(ifc_path))
                    exporter.export()  # 填充数据
                    return exporter.schedule_data
                except Exception as e:
                    print(f"读取IFC失败 {ifc_path}: {e}")
        
        return {
            'project': {'name': '无数据'},
            'tasks': [],
            'gantt': []
        }
    
    def add_event(self, entity_id: str, entity_type: str, event_type: str, 
                  event_data: dict, occurred_at: str) -> Dict[str, Any]:
        """添加施工事件"""
        import psycopg2
        
        conn = self.events_gen.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO construction_events 
                    (entity_id, entity_type, event_type, event_data, occurred_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (entity_id, entity_type, event_type, 
                      psycopg2.extras.Json(event_data), occurred_at))
                conn.commit()
                event_id = cur.fetchone()[0]
            
            # 重新生成调度
            schedule = self.generate_schedule()
            return {
                'status': 'ok',
                'event_id': event_id,
                'schedule': schedule
            }
        finally:
            conn.close()
    
    def generate_schedule(self) -> Dict[str, Any]:
        """生成完整调度"""
        return self.events_gen.generate_schedule()
    
    def get_task_at_date(self, task_name: str, query_date: str) -> Dict[str, Any]:
        """获取指定日期的任务状态"""
        return self.events_gen.get_status_at_date(query_date)


# 全局服务实例
_service = None

def get_4d_service() -> FourDService:
    """获取4D服务实例"""
    global _service
    if _service is None:
        _service = FourDService()
    return _service

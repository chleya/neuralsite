"""
NeuralSite 4D Events Module
从数据库事件生成4D调度数据
"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class Events4DGenerator:
    """从施工事件生成4D调度数据"""
    
    def __init__(self, db_config: dict = None):
        if db_config is None:
            db_config = {
                'host': '127.0.0.1',
                'port': 5432,
                'database': 'neuralsite',
                'user': 'neuralsite',
                'password': 'neuralsite123'
            }
        self.db_config = db_config
    
    def get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(**self.db_config)
    
    def query_events(self, entity_id: str = None) -> List[Dict]:
        """查询施工事件"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if entity_id:
                    cur.execute("""
                        SELECT entity_id, entity_type, event_type, event_data, occurred_at
                        FROM construction_events
                        WHERE entity_id = %s
                        ORDER BY occurred_at
                    """, (entity_id,))
                else:
                    cur.execute("""
                        SELECT entity_id, entity_type, event_type, event_data, occurred_at
                        FROM construction_events
                        WHERE entity_type != 'environment'
                        ORDER BY occurred_at
                    """)
                return cur.fetchall()
        finally:
            conn.close()
    
    def generate_schedule(self) -> Dict[str, Any]:
        """从事件生成4D调度数据"""
        events = self.query_events()
        
        # 按实体分组
        entity_tasks = {}
        for event in events:
            entity_id = event['entity_id']
            if entity_id not in entity_tasks:
                entity_tasks[entity_id] = {
                    'id': entity_id,
                    'name': entity_id,
                    'start': None,
                    'end': None,
                    'status': 'pending',
                    'progress': 0,
                    'events': []
                }
            
            entity_tasks[entity_id]['events'].append({
                'type': event['event_type'],
                'at': event['occurred_at'].isoformat() if event['occurred_at'] else None,
                'data': event['event_data']
            })
            
            # 更新开始时间
            if event['event_type'] == 'start' and not entity_tasks[entity_id]['start']:
                entity_tasks[entity_id]['start'] = event['occurred_at'].strftime('%Y-%m-%d')
            
            # 更新结束时间
            if event['event_type'] == 'complete':
                entity_tasks[entity_id]['end'] = event['occurred_at'].strftime('%Y-%m-%d')
                entity_tasks[entity_id]['status'] = 'completed'
                entity_tasks[entity_id]['progress'] = 100
            
            # 处理延期
            if event['event_type'] == 'delay':
                entity_tasks[entity_id]['status'] = 'delayed'
        
        # 计算持续时间
        tasks = []
        for entity_id, task in entity_tasks.items():
            if task['start'] and task['end']:
                start = datetime.fromisoformat(task['start'])
                end = datetime.fromisoformat(task['end'])
                task['duration_days'] = (end - start).days
            tasks.append(task)
        
        # 排序
        tasks.sort(key=lambda x: x['start'] or '9999')
        
        return {
            'project': {'name': '高速公路施工项目 (实时)'},
            'tasks': tasks,
            'event_count': len(events),
            'generated_at': datetime.now().isoformat()
        }
    
    def get_status_at_date(self, date_str: str) -> Dict[str, Any]:
        """获取指定日期的施工状态"""
        events = self.query_events()
        check_date = datetime.fromisoformat(date_str)
        
        # 按实体分组
        entity_status = {}
        for event in events:
            if event['occurred_at'] > check_date:
                continue
                
            entity_id = event['entity_id']
            if entity_id not in entity_status:
                entity_status[entity_id] = {
                    'name': entity_id,
                    'status': 'pending',
                    'progress': 0
                }
            
            if event['event_type'] == 'start':
                entity_status[entity_id]['status'] = 'active'
            
            if event['event_type'] == 'complete':
                entity_status[entity_id]['status'] = 'completed'
                entity_status[entity_id]['progress'] = 100
            
            if event['event_type'] == 'delay':
                entity_status[entity_id]['status'] = 'delayed'
        
        completed = sum(1 for s in entity_status.values() if s['status'] == 'completed')
        total = len(entity_status)
        
        return {
            'date': date_str,
            'tasks': list(entity_status.values()),
            'overall_progress': int((completed / total) * 100) if total > 0 else 0
        }


# 测试
if __name__ == '__main__':
    gen = Events4DGenerator()
    
    print("=== 从事件生成4D调度 ===")
    schedule = gen.generate_schedule()
    print(f"项目: {schedule['project']['name']}")
    print(f"任务数: {len(schedule['tasks'])}")
    print(f"事件总数: {schedule['event_count']}")
    
    for task in schedule['tasks']:
        print(f"  - {task['name']}: {task['status']} ({task.get('start', 'N/A')} ~ {task.get('end', 'N/A')})")
    
    print("\n=== 2026-04-01 状态 ===")
    status = gen.get_status_at_date('2026-04-01')
    print(f"总体进度: {status['overall_progress']}%")
    for task in status['tasks']:
        print(f"  - {task['name']}: {task['status']}")

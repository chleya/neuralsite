"""
NeuralSite 4D API
提供施工进度4D数据的HTTP接口
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from schedule_4d import Schedule4DExporter


def load_schedule_json(filepath: str = None) -> Dict[str, Any]:
    """加载调度JSON数据"""
    if filepath is None:
        filepath = Path(__file__).parent.parent / 'sample_4d.json'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_schedule_by_date(date_str: str) -> Dict[str, Any]:
    """获取指定日期的施工状态"""
    data = load_schedule_json()
    current_date = datetime.fromisoformat(date_str)
    
    result = {
        'date': date_str,
        'project': data['project'],
        'tasks': [],
        'overall_progress': 0
    }
    
    completed = 0
    for task in data['tasks']:
        task_start = datetime.fromisoformat(task['start'])
        task_end = datetime.fromisoformat(task['end'])
        
        if current_date < task_start:
            status = 'pending'
            progress = 0
        elif current_date > task_end:
            status = 'completed'
            progress = 100
            completed += 1
        else:
            days_passed = (current_date - task_start).days
            progress = int((days_passed / task['duration_days']) * 100)
            status = 'active'
        
        result['tasks'].append({
            'name': task['name'],
            'status': status,
            'progress': progress
        })
    
    if data['tasks']:
        result['overall_progress'] = int((completed / len(data['tasks'])) * 100)
    
    return result


# 测试API
if __name__ == '__main__':
    # 加载数据
    data = load_schedule_json()
    print("=== 4D调度数据API ===")
    print(f"项目: {data['project']['name']}")
    print(f"任务数: {len(data['tasks'])}")
    
    # 测试指定日期查询
    print("\n=== 2026-04-01 施工状态 ===")
    status = get_schedule_by_date('2026-04-01')
    print(f"总体进度: {status['overall_progress']}%")
    for task in status['tasks']:
        print(f"  {task['name']}: {task['status']} ({task['progress']}%)")

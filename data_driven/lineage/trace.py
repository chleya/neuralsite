# -*- coding: utf-8 -*-
"""
数据血缘SQL追溯实现
"""

from typing import List, Dict, Optional, Set
from .models import LineageRecord
from .storage import LineageStorageSQL


class LineageTracerSQL:
    """血缘SQL追溯"""
    
    def __init__(self, storage: LineageStorageSQL):
        """初始化追溯器
        
        Args:
            storage: 血缘SQL存储实例
        """
        self.storage = storage
    
    def trace_forward(self, data_id: str) -> List[LineageRecord]:
        """正向追溯：从原始数据到衍生数据
        
        沿着血缘链从根节点向下游追溯
        
        Args:
            data_id: 数据ID
            
        Returns:
            血缘记录列表（按生成顺序排列）
        """
        # 找到根节点
        rows = self.storage.db.execute(
            "SELECT * FROM data_lineage WHERE data_id = ? AND (parent_lineage_id IS NULL OR parent_lineage_id = '') ORDER BY generation",
            (data_id,)
        ).fetchall()
        
        if not rows:
            # 如果没有根节点，尝试从任意记录开始
            records = self.storage.get_by_data_id(data_id)
            if records:
                root_records = [r for r in records if r.generation == 0]
            else:
                return []
        else:
            # 将sqlite3.Row转换为LineageRecord
            root_records = [self.storage._row_to_record(row) for row in rows]
        
        if not root_records:
            return []
        
        result = []
        # 从根节点开始，递归获取所有下游节点
        visited = set()
        
        def get_all_children(parent_id: str, generation: int):
            if parent_id in visited:
                return
            visited.add(parent_id)
            
            children = self.storage.get_children(parent_id)
            for child in children:
                result.append(child)
                get_all_children(child.lineage_id, child.generation)
        
        # 从所有根节点开始追溯
        for root in root_records:
            result.append(root)
            get_all_children(root.lineage_id, root.generation)
        
        # 按generation排序
        result.sort(key=lambda x: x.generation)
        return result
    
    def trace_backward(self, data_id: str) -> List[LineageRecord]:
        """反向追溯：从衍生数据到原始数据
        
        沿着血缘链从当前节点向上游追溯到根节点
        
        Args:
            data_id: 数据ID
            
        Returns:
            血缘记录列表（从根到当前节点）
        """
        # 获取该数据的所有记录
        records = self.storage.get_by_data_id(data_id)
        
        if not records:
            return []
        
        # 找到generation最大的记录（最新的）
        latest = max(records, key=lambda x: x.generation)
        
        result = []
        current = latest
        
        while current:
            result.append(current)
            
            # 查找父节点
            if current.parent_lineage_id:
                parent = self.storage.get(current.parent_lineage_id)
                if parent:
                    current = parent
                else:
                    break
            else:
                # 没有父节点，可能是根节点
                break
        
        # 反转顺序，从根到当前
        result.reverse()
        return result
    
    def trace_by_lineage_id(self, lineage_id: str) -> List[LineageRecord]:
        """通过lineage_id追溯完整的血缘链
        
        Args:
            lineage_id: 血缘记录ID
            
        Returns:
            完整的血缘链记录列表
        """
        record = self.storage.get(lineage_id)
        if not record:
            return []
        
        # 反向追溯到根
        backward = self.trace_backward(record.data_id)
        
        # 找到当前记录在反向链中的位置
        current_idx = -1
        for i, r in enumerate(backward):
            if r.lineage_id == lineage_id:
                current_idx = i
                break
        
        if current_idx == -1:
            return [record]
        
        # 正向追溯
        forward = self.trace_forward(record.data_id)
        
        # 合并：从根到当前，然后当前之后的所有
        result = backward[:current_idx + 1]
        
        # 添加当前节点之后的所有节点
        for f in forward:
            if f.lineage_id not in [r.lineage_id for r in result]:
                result.append(f)
        
        return result
    
    def impact_analysis(self, data_id: str) -> Dict:
        """影响分析：查询哪些功能/数据会受到影响
        
        分析给定数据作为输入时，会影响哪些下游数据
        
        Args:
            data_id: 数据ID
            
        Returns:
            影响分析结果字典
        """
        # 获取正向血缘链
        affected_records = self.trace_forward(data_id)
        
        # 分类影响
        impact_types = {
            "direct": [],      # 直接影响（下一层）
            "indirect": [],    # 间接影响（多层之后）
            "total_count": 0,
            "max_generation": 0,
        }
        
        for record in affected_records:
            if record.generation == 1:
                impact_types["direct"].append(record)
            elif record.generation > 1:
                impact_types["indirect"].append(record)
        
        impact_types["total_count"] = len(affected_records) - 1  # 排除自身
        if affected_records:
            impact_types["max_generation"] = max(r.generation for r in affected_records)
        
        # 统计受影响的数据类型
        data_types = {}
        for record in affected_records:
            if record.data_id != data_id:
                dt = record.data_type
                data_types[dt] = data_types.get(dt, 0) + 1
        
        impact_types["affected_data_types"] = data_types
        
        # 统计受影响的项目
        projects = set()
        for record in affected_records:
            if record.project_id:
                projects.add(record.project_id)
        impact_types["affected_projects"] = list(projects)
        
        return impact_types
    
    def get_impact_tree(self, data_id: str, max_depth: int = 5) -> Dict:
        """获取影响树
        
        以树形结构返回完整的影响链
        
        Args:
            data_id: 数据ID
            max_depth: 最大追溯深度
            
        Returns:
            树形结构的影响分析
        """
        root_records = self.storage.get_by_data_id(data_id)
        if not root_records:
            return {"error": "未找到数据"}
        
        # 找到根节点
        root = None
        for r in root_records:
            if r.generation == 0:
                root = r
                break
        
        if not root:
            root = root_records[0]
        
        def build_tree(lineage_id: str, depth: int) -> Dict:
            if depth > max_depth:
                return {"depth_limit": True}
            
            record = self.storage.get(lineage_id)
            if not record:
                return {}
            
            children = self.storage.get_children(lineage_id)
            
            node = {
                "lineage_id": record.lineage_id,
                "data_id": record.data_id,
                "data_type": record.data_type,
                "generation": record.generation,
                "children": []
            }
            
            for child in children:
                node["children"].append(build_tree(child.lineage_id, depth + 1))
            
            return node
        
        return build_tree(root.lineage_id, 0)
    
    def find_common_ancestor(self, data_id1: str, data_id2: str) -> Optional[LineageRecord]:
        """查找两个数据的公共祖先
        
        Args:
            data_id1: 第一个数据ID
            data_id2: 第二个数据ID
            
        Returns:
            公共祖先记录或None
        """
        # 获取两个数据的完整血缘链
        chain1 = self.trace_backward(data_id1)
        chain2 = self.trace_backward(data_id2)
        
        if not chain1 or not chain2:
            return None
        
        # 构建第一个链的ID集合
        ids1 = {r.lineage_id for r in chain1}
        
        # 从根开始遍历第二个链，找到第一个在ids1中的
        for r in chain2:
            if r.lineage_id in ids1:
                return r
        
        return None
    
    def validate_lineage_integrity(self, data_id: str) -> Dict:
        """验证血缘链完整性
        
        检查是否存在断链、环等异常
        
        Args:
            data_id: 数据ID
            
        Returns:
            验证结果
        """
        result = {
            "is_valid": True,
            "issues": [],
            "total_records": 0,
            "max_generation": 0,
        }
        
        records = self.storage.get_by_data_id(data_id)
        result["total_records"] = len(records)
        
        if not records:
            result["is_valid"] = False
            result["issues"].append("未找到任何血缘记录")
            return result
        
        # 检查generation是否连续
        generations = sorted(set(r.generation for r in records))
        result["max_generation"] = max(generations) if generations else 0
        
        for i in range(len(generations) - 1):
            if generations[i + 1] - generations[i] > 1:
                result["is_valid"] = False
                result["issues"].append(f"Generation断链: {generations[i]} -> {generations[i+1]}")
        
        # 检查是否有环
        visited = set()
        for record in records:
            if record.lineage_id in visited:
                result["is_valid"] = False
                result["issues"].append(f"发现环: {record.lineage_id}")
            visited.add(record.lineage_id)
        
        # 检查父节点是否存在
        for record in records:
            if record.parent_lineage_id:
                parent = self.storage.get(record.parent_lineage_id)
                if not parent:
                    result["is_valid"] = False
                    result["issues"].append(f"父节点不存在: {record.lineage_id} -> {record.parent_lineage_id}")
        
        return result

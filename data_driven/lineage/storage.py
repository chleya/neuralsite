# -*- coding: utf-8 -*-
"""
数据血缘SQL存储实现
"""

import sqlite3
from typing import Optional, List
from datetime import datetime
import uuid

from .models import LineageRecord, LineageType


class LineageStorageSQL:
    """血缘SQL存储"""
    
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS data_lineage (
        lineage_id TEXT PRIMARY KEY,
        data_id TEXT NOT NULL,
        data_type VARCHAR(50) NOT NULL,
        data_version VARCHAR(50),
        project_id TEXT,
        
        source_type VARCHAR(30),
        source_system VARCHAR(100),
        source_file VARCHAR(500),
        imported_at TIMESTAMP,
        imported_by VARCHAR(100),
        original_value TEXT,
        
        parent_lineage_id TEXT,
        generation INT DEFAULT 0,
        
        is_root INTEGER DEFAULT 0,
        is_leaf INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    CREATE_INDEX_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_lineage_data_id ON data_lineage(data_id);",
        "CREATE INDEX IF NOT EXISTS idx_lineage_parent ON data_lineage(parent_lineage_id);",
        "CREATE INDEX IF NOT EXISTS idx_lineage_project ON data_lineage(project_id);",
    ]
    
    def __init__(self, db_path: str = "lineage.db"):
        """初始化SQL存储
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """初始化表结构"""
        cursor = self.db.cursor()
        cursor.execute(self.CREATE_TABLE_SQL)
        for index_sql in self.CREATE_INDEX_SQL:
            cursor.execute(index_sql)
        self.db.commit()
    
    def save(self, record: LineageRecord) -> bool:
        """保存血缘记录
        
        Args:
            record: 血缘记录
            
        Returns:
            是否保存成功
        """
        cursor = self.db.cursor()
        
        # 判断是否为根节点和叶节点
        is_root = 1 if record.parent_lineage_id == "" or record.parent_lineage_id is None else 0
        is_leaf = 1 if record.is_leaf else 0
        
        sql = """
        INSERT OR REPLACE INTO data_lineage (
            lineage_id, data_id, data_type, data_version, project_id,
            source_type, source_system, source_file, imported_at, imported_by,
            original_value, parent_lineage_id, generation,
            is_root, is_leaf, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            record.lineage_id,
            record.data_id,
            record.data_type,
            record.data_version,
            record.project_id,
            record.source_type.value if isinstance(record.source_type, LineageType) else record.source_type,
            record.source_system,
            record.source_file,
            record.imported_at.isoformat() if record.imported_at else None,
            record.imported_by,
            record.original_value,
            record.parent_lineage_id if record.parent_lineage_id else None,
            record.generation,
            is_root,
            is_leaf,
            record.created_at.isoformat() if record.created_at else datetime.utcnow().isoformat(),
        )
        
        try:
            cursor.execute(sql, params)
            self.db.commit()
            return True
        except Exception as e:
            print(f"保存血缘记录失败: {e}")
            self.db.rollback()
            return False
    
    def get(self, lineage_id: str) -> Optional[LineageRecord]:
        """获取血缘记录
        
        Args:
            lineage_id: 血缘记录ID
            
        Returns:
            血缘记录或None
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM data_lineage WHERE lineage_id = ?", (lineage_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_record(row)
        return None
    
    def get_by_data_id(self, data_id: str) -> List[LineageRecord]:
        """根据数据ID查询
        
        Args:
            data_id: 数据ID
            
        Returns:
            血缘记录列表
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM data_lineage WHERE data_id = ? ORDER BY created_at", (data_id,))
        rows = cursor.fetchall()
        
        return [self._row_to_record(row) for row in rows]
    
    def get_children(self, lineage_id: str) -> List[LineageRecord]:
        """获取子节点
        
        Args:
            lineage_id: 父血缘记录ID
            
        Returns:
            子节点列表
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM data_lineage WHERE parent_lineage_id = ? ORDER BY created_at", 
            (lineage_id,)
        )
        rows = cursor.fetchall()
        
        return [self._row_to_record(row) for row in rows]
    
    def get_parent(self, lineage_id: str) -> Optional[LineageRecord]:
        """获取父节点
        
        Args:
            lineage_id: 子血缘记录ID
            
        Returns:
            父节点或None
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM data_lineage WHERE lineage_id = (SELECT parent_lineage_id FROM data_lineage WHERE lineage_id = ?)",
            (lineage_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return self._row_to_record(row)
        return None
    
    def get_root_records(self, project_id: str = None) -> List[LineageRecord]:
        """获取根节点记录
        
        Args:
            project_id: 项目ID（可选）
            
        Returns:
            根节点列表
        """
        cursor = self.db.cursor()
        if project_id:
            cursor.execute(
                "SELECT * FROM data_lineage WHERE is_root = 1 AND project_id = ? ORDER BY created_at",
                (project_id,)
            )
        else:
            cursor.execute("SELECT * FROM data_lineage WHERE is_root = 1 ORDER BY created_at")
        
        rows = cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    def delete(self, lineage_id: str) -> bool:
        """删除血缘记录
        
        Args:
            lineage_id: 血缘记录ID
            
        Returns:
            是否删除成功
        """
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM data_lineage WHERE lineage_id = ?", (lineage_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(f"删除血缘记录失败: {e}")
            self.db.rollback()
            return False
    
    def _row_to_record(self, row: sqlite3.Row) -> LineageRecord:
        """将数据库行转换为LineageRecord
        
        Args:
            row: 数据库行
            
        Returns:
            LineageRecord对象
        """
        return LineageRecord(
            lineage_id=row["lineage_id"],
            data_id=row["data_id"],
            data_type=row["data_type"],
            data_version=row["data_version"],
            project_id=row["project_id"] or "",
            source_type=LineageType(row["source_type"]) if row["source_type"] else LineageType.MANUAL,
            source_system=row["source_system"] or "",
            source_file=row["source_file"] or "",
            imported_at=datetime.fromisoformat(row["imported_at"]) if row["imported_at"] else None,
            imported_by=row["imported_by"] or "",
            original_value=row["original_value"] or "",
            parent_lineage_id=row["parent_lineage_id"] or "",
            generation=row["generation"],
            is_root=bool(row["is_root"]),
            is_leaf=bool(row["is_leaf"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

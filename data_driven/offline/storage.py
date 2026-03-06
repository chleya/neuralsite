"""
离线存储模块
使用SQLite实现本地数据持久化
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class OfflineStorage:
    """离线存储 - 使用SQLite实现本地数据持久化"""
    
    def __init__(self, db_path: str = "offline.db"):
        """
        初始化离线存储
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 创建通用数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_data (
                    id TEXT PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    synced INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (table_name) 
                    REFERENCES tables(table_name)
                )
            """)
            
            # 创建表元数据
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    table_name TEXT PRIMARY KEY,
                    schema TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # 创建同步状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT
                )
            """)
            
            conn.commit()
    
    def _ensure_table(self, table: str, schema: Dict[str, str] = None):
        """确保表存在"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO tables (table_name, schema, created_at) VALUES (?, ?, ?)",
                (table, json.dumps(schema) if schema else "{}", datetime.utcnow().isoformat())
            )
            conn.commit()
    
    def save(self, table: str, data: dict) -> bool:
        """
        保存数据到本地
        
        Args:
            table: 表名
            data: 要保存的数据 (包含id字段)
            
        Returns:
            bool: 是否保存成功
        """
        if "id" not in data:
            raise ValueError("Data must contain 'id' field")
        
        self._ensure_table(table)
        
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                "SELECT id, updated_at FROM offline_data WHERE id = ? AND table_name = ?",
                (data["id"], table)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                cursor.execute("""
                    UPDATE offline_data 
                    SET data = ?, updated_at = ?, synced = 0
                    WHERE id = ? AND table_name = ?
                """, (json.dumps(data), now, data["id"], table))
            else:
                # 插入
                cursor.execute("""
                    INSERT INTO offline_data (id, table_name, data, synced, created_at, updated_at)
                    VALUES (?, ?, ?, 0, ?, ?)
                """, (data["id"], table, json.dumps(data), now, now))
            
            conn.commit()
            
            # 记录同步日志
            cursor.execute("""
                INSERT INTO sync_log (table_name, operation, status, timestamp)
                VALUES (?, ?, ?, ?)
            """, (table, "save", "pending", now))
            conn.commit()
        
        return True
    
    def get(self, table: str, filters: dict = None) -> list:
        """
        查询本地数据
        
        Args:
            table: 表名
            filters: 过滤条件 (可选)
            
        Returns:
            list: 查询结果列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM offline_data WHERE table_name = ?"
            params = [table]
            
            if filters:
                for key, value in filters.items():
                    query += f" AND json_extract(data, '$.{key}') = ?"
                    params.append(str(value))
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def delete(self, table: str, id: str) -> bool:
        """
        删除数据
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            bool: 是否删除成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM offline_data WHERE id = ? AND table_name = ?",
                (id, table)
            )
            conn.commit()
            
            # 记录删除操作
            cursor.execute("""
                INSERT INTO sync_log (table_name, operation, status, timestamp)
                VALUES (?, ?, ?, ?)
            """, (table, "delete", "pending", datetime.utcnow().isoformat()))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_pending(self, table: str) -> list:
        """
        获取待同步数据
        
        Args:
            table: 表名
            
        Returns:
            list: 待同步数据列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM offline_data WHERE table_name = ? AND synced = 0",
                (table,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def mark_synced(self, table: str, id: str) -> bool:
        """
        标记已同步
        
        Args:
            table: 表名
            id: 数据ID
            
        Returns:
            bool: 是否标记成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE offline_data 
                SET synced = 1 
                WHERE id = ? AND table_name = ?
            """, (id, table))
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_synced_batch(self, table: str, ids: List[str]) -> int:
        """
        批量标记已同步
        
        Args:
            table: 表名
            ids: 数据ID列表
            
        Returns:
            int: 标记的记录数
        """
        if not ids:
            return 0
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(ids))
            cursor.execute(f"""
                UPDATE offline_data 
                SET synced = 1 
                WHERE id IN ({placeholders}) AND table_name = ?
            """, (*ids, table))
            conn.commit()
            return cursor.rowcount
    
    def get_sync_status(self, table: str = None) -> dict:
        """
        获取同步状态
        
        Args:
            table: 表名 (可选)
            
        Returns:
            dict: 同步状态统计
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if table:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN synced = 1 THEN 1 ELSE 0 END) as synced,
                        SUM(CASE WHEN synced = 0 THEN 1 ELSE 0 END) as pending
                    FROM offline_data 
                    WHERE table_name = ?
                """, (table,))
            else:
                cursor.execute("""
                    SELECT 
                        table_name,
                        COUNT(*) as total,
                        SUM(CASE WHEN synced = 1 THEN 1 ELSE 0 END) as synced,
                        SUM(CASE WHEN synced = 0 THEN 1 ELSE 0 END) as pending
                    FROM offline_data 
                    GROUP BY table_name
                """)
            
            rows = cursor.fetchall()
            if table:
                row = rows[0] if rows else None
                return {
                    "total": row["total"] if row else 0,
                    "synced": row["synced"] if row else 0,
                    "pending": row["pending"] if row else 0
                }
            else:
                return {row["table_name"]: dict(row) for row in rows}
    
    def clear_synced(self, table: str = None) -> int:
        """
        清理已同步数据
        
        Args:
            table: 表名 (可选, 不指定则清理所有)
            
        Returns:
            int: 删除的记录数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if table:
                cursor.execute(
                    "DELETE FROM offline_data WHERE table_name = ? AND synced = 1",
                    (table,)
                )
            else:
                cursor.execute("DELETE FROM offline_data WHERE synced = 1")
            
            conn.commit()
            return cursor.rowcount


# 便捷函数
def create_storage(db_path: str = "offline.db") -> OfflineStorage:
    """创建离线存储实例"""
    return OfflineStorage(db_path)

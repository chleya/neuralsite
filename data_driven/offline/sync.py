"""
同步引擎模块
实现本地与远程数据双向同步
"""
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin

from .storage import OfflineStorage


logger = logging.getLogger(__name__)


class SyncEngine:
    """同步引擎 - 处理本地与远程数据双向同步"""
    
    def __init__(
        self, 
        storage: OfflineStorage, 
        remote_api: str,
        batch_size: int = 50,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化同步引擎
        
        Args:
            storage: 离线存储实例
            remote_api: 远程API基础URL
            batch_size: 批量同步大小
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
        """
        self.storage = storage
        self.remote_api = remote_api.rstrip("/")
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_sync: Dict[str, str] = {}
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Any = None,
        retries: int = 0
    ) -> Optional[Dict]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            retries: 当前重试次数
            
        Returns:
            Optional[Dict]: 响应数据
        """
        url = urljoin(self.remote_api + "/", endpoint.lstrip("/"))
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            body = json.dumps(data).encode("utf-8") if data else None
            request = Request(url, data=body, headers=headers, method=method)
            
            with urlopen(request, timeout=30) as response:
                if response.status == 204:
                    return {"success": True}
                return json.loads(response.read().decode("utf-8"))
                
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            if retries < self.max_retries:
                logger.warning(f"Request failed, retrying ({retries + 1}/{self.max_retries}): {e}")
                time.sleep(self.retry_delay * (retries + 1))
                return self._make_request(method, endpoint, data, retries + 1)
            
            logger.error(f"Request failed after {self.max_retries} retries: {e}")
            return {"error": str(e), "success": False}
    
    def sync_up(self, table: str = None) -> dict:
        """
        上传本地数据到远程
        
        Args:
            table: 要同步的表名 (None表示所有表)
            
        Returns:
            dict: 同步结果统计
        """
        result = {
            "success": True,
            "table": table or "all",
            "uploaded": 0,
            "failed": 0,
            "errors": []
        }
        
        # 确定要同步的表
        if table:
            tables = [table]
        else:
            status = self.storage.get_sync_status()
            tables = list(status.keys())
        
        for tbl in tables:
            # 获取待同步数据
            pending = self.storage.get_pending(tbl)
            
            if not pending:
                logger.info(f"No pending data for table: {tbl}")
                continue
            
            logger.info(f"Uploading {len(pending)} records from {tbl}")
            
            # 批量上传
            for i in range(0, len(pending), self.batch_size):
                batch = pending[i:i + self.batch_size]
                batch_ids = []
                
                for record in batch:
                    try:
                        data = json.loads(record["data"])
                        response = self._make_request("POST", f"{tbl}", data)
                        
                        if response and response.get("success", True):
                            self.storage.mark_synced(tbl, record["id"])
                            batch_ids.append(record["id"])
                            result["uploaded"] += 1
                        else:
                            result["failed"] += 1
                            result["errors"].append({
                                "id": record["id"],
                                "error": response.get("error", "Unknown error") if response else "No response"
                            })
                    except Exception as e:
                        result["failed"] += 1
                        result["errors"].append({
                            "id": record["id"],
                            "error": str(e)
                        })
                        logger.error(f"Failed to upload record {record['id']}: {e}")
                
                if batch_ids:
                    logger.info(f"Successfully uploaded {len(batch_ids)} records from batch")
            
            # 更新最后同步时间
            self.last_sync[tbl] = datetime.utcnow().isoformat()
        
        result["last_sync"] = self.last_sync.copy()
        return result
    
    def sync_down(self, table: str = None, since: str = None) -> dict:
        """
        下载远程数据到本地
        
        Args:
            table: 要同步的表名 (None表示所有表)
            since: 从指定时间开始同步 (ISO格式)
            
        Returns:
            dict: 同步结果统计
        """
        result = {
            "success": True,
            "table": table or "all",
            "downloaded": 0,
            "merged": 0,
            "conflicts": 0,
            "errors": []
        }
        
        # 确定要同步的表
        if table:
            tables = [table]
        else:
            status = self.storage.get_sync_status()
            tables = list(status.keys())
        
        for tbl in tables:
            # 获取远程数据
            endpoint = tbl
            if since:
                endpoint += f"?since={since}"
            
            response = self._make_request("GET", endpoint)
            
            if not response or "error" in response:
                result["errors"].append({
                    "table": tbl,
                    "error": response.get("error", "Failed to fetch") if response else "No response"
                })
                continue
            
            remote_data = response if isinstance(response, list) else response.get("data", [])
            
            if not remote_data:
                logger.info(f"No remote data for table: {tbl}")
                continue
            
            logger.info(f"Downloading {len(remote_data)} records to {tbl}")
            
            for record in remote_data:
                try:
                    # 检查本地是否存在
                    local_records = self.storage.get(tbl, {"id": record.get("id")})
                    
                    if local_records:
                        local = json.loads(local_records[0]["data"])
                        # 冲突解决
                        merged = self.resolve_conflict(local, record)
                        
                        if merged != local:
                            self.storage.save(tbl, merged)
                            result["conflicts"] += 1
                            logger.debug(f"Resolved conflict for record {record['id']}")
                    else:
                        # 新增记录
                        self.storage.save(tbl, record)
                        result["downloaded"] += 1
                        
                except Exception as e:
                    result["errors"].append({
                        "id": record.get("id"),
                        "error": str(e)
                    })
                    logger.error(f"Failed to process record {record.get('id')}: {e}")
            
            result["merged"] = result["downloaded"] + result["conflicts"]
            
            # 更新最后同步时间
            self.last_sync[tbl] = datetime.utcnow().isoformat()
        
        result["last_sync"] = self.last_sync.copy()
        return result
    
    def resolve_conflict(self, local: dict, remote: dict) -> dict:
        """
        冲突解决 - 默认策略: 最后写入胜出
        
        Args:
            local: 本地数据
            remote: 远程数据
            
        Returns:
            dict: 解决后的数据
        """
        # 统一更新时间字段名
        local_time = local.get("updated_at") or local.get("updatedAt") or local.get("timestamp", "")
        remote_time = remote.get("updated_at") or remote.get("updatedAt") or remote.get("timestamp", "")
        
        # 尝试解析时间
        try:
            if isinstance(local_time, str):
                local_dt = datetime.fromisoformat(local_time.replace("Z", "+00:00"))
            else:
                local_dt = datetime.min
                
            if isinstance(remote_time, str):
                remote_dt = datetime.fromisoformat(remote_time.replace("Z", "+00:00"))
            else:
                remote_dt = datetime.min
                
            # 最后更新胜出
            if remote_dt >= local_dt:
                logger.debug(f"Remote record wins: {remote.get('id')}")
                return remote
            else:
                logger.debug(f"Local record wins: {local.get('id')}")
                return local
                
        except (ValueError, TypeError):
            # 无法解析时间，默认远程胜出
            logger.warning("Could not parse timestamps, defaulting to remote")
            return remote
    
    def full_sync(self, table: str = None) -> dict:
        """
        完整同步 (先上传后下载)
        
        Args:
            table: 要同步的表名
            
        Returns:
            dict: 完整同步结果
        """
        result = {
            "success": True,
            "up": None,
            "down": None,
            "errors": []
        }
        
        # 先上传
        logger.info("Starting upload phase...")
        up_result = self.sync_up(table)
        result["up"] = up_result
        
        if not up_result.get("success"):
            result["errors"].append("Upload failed")
        
        # 再下载
        logger.info("Starting download phase...")
        since = None
        if table and table in self.last_sync:
            since = self.last_sync[table]
        
        down_result = self.sync_down(table, since)
        result["down"] = down_result
        
        if not down_result.get("success"):
            result["errors"].append("Download failed")
        
        result["success"] = len(result["errors"]) == 0
        
        return result
    
    def get_last_sync_time(self, table: str = None) -> Optional[str]:
        """
        获取最后同步时间
        
        Args:
            table: 表名
            
        Returns:
            Optional[str]: ISO格式的时间字符串
        """
        if table:
            return self.last_sync.get(table)
        return self.last_sync.get("all")
    
    def set_last_sync_time(self, table: str, timestamp: str):
        """
        设置最后同步时间
        
        Args:
            table: 表名
            timestamp: ISO格式的时间字符串
        """
        self.last_sync[table] = timestamp


class MockSyncEngine(SyncEngine):
    """Mock同步引擎 - 用于测试"""
    
    def __init__(self, storage: OfflineStorage, remote_api: str = "http://mock.local"):
        super().__init__(storage, remote_api)
        self.mock_data: Dict[str, List[dict]] = {}
    
    def _make_request(self, method: str, endpoint: str, data: Any = None, retries: int = 0) -> Optional[Dict]:
        """Mock请求 - 直接操作内存数据"""
        table = endpoint.split("?")[0]
        
        if method == "GET":
            # 返回mock数据
            return self.mock_data.get(table, [])
        
        elif method == "POST":
            # 模拟创建
            if table not in self.mock_data:
                self.mock_data[table] = []
            self.mock_data[table].append(data)
            return {"success": True, "id": data.get("id")}
        
        elif method == "PUT":
            # 模拟更新
            for i, item in enumerate(self.mock_data.get(table, [])):
                if item.get("id") == data.get("id"):
                    self.mock_data[table][i] = data
                    return {"success": True}
            return {"success": False, "error": "Not found"}
        
        elif method == "DELETE":
            # 模拟删除
            self.mock_data[table] = [
                item for item in self.mock_data.get(table, [])
                if item.get("id") != endpoint.split("/")[-1]
            ]
            return {"success": True}
        
        return {"error": "Unknown method"}


# 便捷函数
def create_sync_engine(
    storage: OfflineStorage, 
    remote_api: str,
    mock: bool = False
) -> SyncEngine:
    """创建同步引擎实例"""
    if mock:
        return MockSyncEngine(storage, remote_api)
    return SyncEngine(storage, remote_api)

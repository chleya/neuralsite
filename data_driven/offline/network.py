"""
网络监控模块
监控网络状态变化并触发回调
"""
import threading
import time
import logging
from typing import Callable, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)

# 尝试导入网络检测库
try:
    import socket
    SOCKET_AVAILABLE = True
except ImportError:
    SOCKET_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class NetworkState(Enum):
    """网络状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class NetworkMonitor:
    """网络监控 - 监听网络状态变化"""
    
    def __init__(
        self,
        check_interval: float = 5.0,
        check_host: str = "8.8.8.8",
        check_port: int = 53,
        check_timeout: float = 3.0,
        check_url: str = "https://www.google.com/generate_204"
    ):
        """
        初始化网络监控器
        
        Args:
            check_interval: 检查间隔(秒)
            check_host: ping检查主机
            check_port: ping检查端口
            check_timeout: 超时时间(秒)
            check_url: HTTP检查URL
        """
        self.check_interval = check_interval
        self.check_host = check_host
        self.check_port = check_port
        self.check_timeout = check_timeout
        self.check_url = check_url
        
        self.is_online: bool = True
        self._state: NetworkState = NetworkState.ONLINE
        self.callbacks: List[Callable[[NetworkState, NetworkState], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._lock = threading.RLock()
        
        # 状态历史
        self.state_history: List[Dict[str, Any]] = []
    
    def start_monitoring(self):
        """开始监控网络状态"""
        with self._lock:
            if self._running:
                logger.warning("Network monitoring already started")
                return
            
            self._running = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="NetworkMonitor",
                daemon=True
            )
            self._monitor_thread.start()
            logger.info("Network monitoring started")
    
    def stop_monitoring(self):
        """停止监控网络状态"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5.0)
            logger.info("Network monitoring stopped")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            old_state = self._state
            
            # 检测网络状态
            if self._check_connectivity():
                self._state = NetworkState.ONLINE
                self.is_online = True
            else:
                self._state = NetworkState.OFFLINE
                self.is_online = False
            
            # 状态变化时触发回调
            if old_state != self._state:
                self._record_state_change(old_state, self._state)
                self._trigger_callbacks(old_state, self._state)
                logger.info(f"Network state changed: {old_state.value} -> {self._state.value}")
            
            # 等待下次检查
            time.sleep(self.check_interval)
    
    def _check_connectivity(self) -> bool:
        """
        检查网络连通性
        
        尝试多种方法:
        1. HTTP请求检查
        2. Socket连接检查
        3. DNS解析检查
        """
        # 方法1: HTTP请求检查
        if self._check_http():
            return True
        
        # 方法2: Socket连接检查
        if self._check_socket():
            return True
        
        # 方法3: DNS解析检查
        if self._check_dns():
            return True
        
        return False
    
    def _check_http(self) -> bool:
        """HTTP检查"""
        if not REQUESTS_AVAILABLE:
            return self._check_http_urllib()
        
        try:
            import requests
            response = requests.get(
                self.check_url, 
                timeout=self.check_timeout,
                allow_redirects=True
            )
            return response.status_code < 400
        except Exception:
            return False
    
    def _check_http_urllib(self) -> bool:
        """使用urllib的HTTP检查"""
        try:
            from urllib.request import urlopen, Request
            from urllib.error import URLError
            
            request = Request(self.check_url, method="GET")
            with urlopen(request, timeout=self.check_timeout) as response:
                return response.status < 400
        except Exception:
            return False
    
    def _check_socket(self) -> bool:
        """Socket连接检查"""
        if not SOCKET_AVAILABLE:
            return False
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.check_timeout)
            result = sock.connect_ex((self.check_host, self.check_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_dns(self) -> bool:
        """DNS解析检查"""
        if not SOCKET_AVAILABLE:
            return False
        
        try:
            socket.gethostbyname("www.google.com")
            return True
        except socket.gaierror:
            return False
    
    def _record_state_change(self, old_state: NetworkState, new_state: NetworkState):
        """记录状态变化"""
        self.state_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from": old_state.value,
            "to": new_state.value
        })
        
        # 只保留最近100条记录
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]
    
    def _trigger_callbacks(self, old_state: NetworkState, new_state: NetworkState):
        """触发所有回调"""
        for callback in self.callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in network state callback: {e}")
    
    def is_available(self) -> bool:
        """
        检查网络是否可用 (即时检查)
        
        Returns:
            bool: 网络是否可用
        """
        return self._check_connectivity()
    
    def get_state(self) -> NetworkState:
        """
        获取当前网络状态
        
        Returns:
            NetworkState: 当前网络状态
        """
        return self._state
    
    def on_change(self, callback: Callable[[NetworkState, NetworkState], None]):
        """
        注册网络状态变化回调
        
        Args:
            callback: 回调函数, 签名为 (old_state, new_state) -> None
        """
        self.callbacks.append(callback)
        logger.debug(f"Registered network change callback: {callback.__name__}")
    
    def off_change(self, callback: Callable[[NetworkState, NetworkState], None]):
        """
        移除网络状态变化回调
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.debug(f"Removed network change callback: {callback.__name__}")
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取状态变化历史
        
        Args:
            limit: 返回记录数
            
        Returns:
            List[Dict]: 状态变化历史
        """
        return self.state_history[-limit:]
    
    def wait_for_online(self, timeout: float = None) -> bool:
        """
        等待网络上线
        
        Args:
            timeout: 超时时间(秒), None表示无限等待
            
        Returns:
            bool: 是否成功上线
        """
        start_time = time.time()
        
        while True:
            if self.is_available():
                return True
            
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            time.sleep(1.0)
    
    def wait_for_offline(self, timeout: float = None) -> bool:
        """
        等待网络离线
        
        Args:
            timeout: 超时时间(秒), None表示无限等待
            
        Returns:
            bool: 是否成功离线
        """
        start_time = time.time()
        
        while True:
            if not self.is_available():
                return True
            
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            time.sleep(1.0)


class SimpleNetworkMonitor:
    """简化版网络监控 - 只提供基本功能"""
    
    def __init__(self):
        self.is_online = True
        self.callbacks: List[Callable[[bool, bool], None]] = []
    
    def is_available(self) -> bool:
        """检查网络是否可用"""
        return self._simple_check()
    
    def _simple_check(self) -> bool:
        """简单的网络检查"""
        try:
            if SOCKET_AVAILABLE:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                result = sock.connect_ex(("8.8.8.8", 53))
                sock.close()
                return result == 0
        except Exception:
            pass
        return False
    
    def on_change(self, callback: Callable[[bool, bool], None]):
        """注册回调"""
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """启动监控 (简化版不实际监控)"""
        pass
    
    def stop_monitoring(self):
        """停止监控"""
        pass


# 便捷函数
def create_network_monitor(**kwargs) -> NetworkMonitor:
    """创建网络监控实例"""
    return NetworkMonitor(**kwargs)

# -*- coding: utf-8 -*-
"""
ERP 适配器模块
与广联达、鲁班等主流施工ERP系统对接，实现数据互通

功能：
1. 数据模型转换 - ERP 工程量清单 ↔ NeuralSite 实体
2. API 对接层 - 通用 ERP 适配器 + 广联达/鲁班专用适配器
3. 同步机制 - 定时同步、增量同步、冲突处理
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from datetime import datetime
import json
import hashlib
import logging
from threading import Thread, Event
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== 数据模型 ==========

class ERPType(Enum):
    """ERP系统类型"""
    GLODON = "glodon"      # 广联达
    LUBAN = "luban"        # 鲁班
    CUSTOM = "custom"      # 自定义


class SyncDirection(Enum):
    """同步方向"""
    NEURALSITE_TO_ERP = "ns2erp"   # NeuralSite → ERP
    ERP_TO_NEURALSITE = "erp2ns"   # ERP → NeuralSite
    BIDIRECTIONAL = "bidirectional"  # 双向


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class ConflictResolution(Enum):
    """冲突解决策略"""
    NEURALSITE_WINS = "ns_wins"
    ERP_WINS = "erp_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"


@dataclass
class ERPBillItem:
    """ERP工程量清单项"""
    bill_id: str           # 清单编号
    bill_name: str         # 清单名称
    unit: str              # 单位
    quantity: float        # 工程量
    unit_price: float      # 综合单价
    total_price: float     # 合价
    category: str          # 分部分项
    parent_id: str = ""    # 父级清单ID
    attributes: Dict = field(default_factory=dict)  # 扩展属性
    
    def to_dict(self) -> Dict:
        return {
            "billId": self.bill_id,
            "billName": self.bill_name,
            "unit": self.unit,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "totalPrice": self.total_price,
            "category": self.category,
            "parentId": self.parent_id,
            "attributes": self.attributes
        }


@dataclass
class ERPContract:
    """ERP合同"""
    contract_id: str        # 合同编号
    contract_name: str      # 合同名称
    contract_type: str      # 合同类型
    amount: float           # 合同金额
    party_a: str            # 甲方
    party_b: str            # 乙方
    sign_date: str          # 签订日期
    start_date: str         # 开工日期
    end_date: str           # 完工日期
    status: str             # 合同状态
    items: List[ERPBillItem] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "contractId": self.contract_id,
            "contractName": self.contract_name,
            "contractType": self.contract_type,
            "amount": self.amount,
            "partyA": self.party_a,
            "partyB": self.party_b,
            "signDate": self.sign_date,
            "startDate": self.start_date,
            "endDate": self.end_date,
            "status": self.status,
            "items": [item.to_dict() for item in self.items]
        }


@dataclass
class ERPMeasurement:
    """ERP计量数据"""
    measurement_id: str     # 计量编号
    period_id: str          # 计量期次
    project_id: str         # 项目ID
    bill_item_id: str       # 清单ID
    quantity: float         # 计量数量
    amount: float           # 计量金额
    measurement_date: str  # 计量日期
    status: str             # 状态
    attachments: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "measurementId": self.measurement_id,
            "periodId": self.period_id,
            "projectId": self.project_id,
            "billItemId": self.bill_item_id,
            "quantity": self.quantity,
            "amount": self.amount,
            "measurementDate": self.measurement_date,
            "status": self.status,
            "attachments": self.attachments
        }


@dataclass
class SyncRecord:
    """同步记录"""
    record_id: str
    entity_type: str        # 实体类型 (contract/bill/measurement)
    entity_id: str          # 实体ID
    direction: SyncDirection
    status: SyncStatus
    source_data: Dict       # 源数据
    target_data: Dict       # 目标数据
    source_hash: str        # 源数据哈希
    target_hash: str        # 目标数据哈希
    sync_time: datetime
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "recordId": self.record_id,
            "entityType": self.entity_type,
            "entityId": self.entity_id,
            "direction": self.direction.value,
            "status": self.status.value,
            "sourceData": self.source_data,
            "targetData": self.target_data,
            "sourceHash": self.source_hash,
            "targetHash": self.target_hash,
            "syncTime": self.sync_time.isoformat(),
            "errorMessage": self.error_message
        }


@dataclass
class SyncConfig:
    """同步配置"""
    enabled: bool = True
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    interval_seconds: int = 300  # 默认5分钟
    conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS
    retry_count: int = 3
    retry_delay_seconds: int = 60


# ========== 数据模型转换器 ==========

class ERPDataConverter:
    """ERP数据模型转换器"""
    
    # ERP字段到NeuralSite字段的映射
    BILL_MAPPING = {
        "bill_id": "component_id",
        "bill_name": "description",
        "quantity": "parameters.quantity",
        "unit": "parameters.unit",
        "unit_price": "parameters.unit_price",
        "category": "parameters.category",
    }
    
    @staticmethod
    def erp_bill_to_component(bill: ERPBillItem, component_type: str = "BillItem") -> Dict:
        """将ERP清单转换为NeuralSite组件"""
        return {
            "component_id": f"bill_{bill.bill_id}",
            "component_type": component_type,
            "description": bill.bill_name,
            "parameters": {
                "quantity": bill.quantity,
                "unit": bill.unit,
                "unit_price": bill.unit_price,
                "total_price": bill.total_price,
                "category": bill.category,
                "bill_id": bill.bill_id,
                **bill.attributes
            }
        }
    
    @staticmethod
    def component_to_erp_bill(component: Dict, default_unit: str = "项") -> ERPBillItem:
        """将NeuralSite组件转换为ERP清单"""
        params = component.get("parameters", {})
        return ERPBillItem(
            bill_id=component.get("component_id", "").replace("bill_", ""),
            bill_name=component.get("description", ""),
            unit=params.get("unit", default_unit),
            quantity=params.get("quantity", 0.0),
            unit_price=params.get("unit_price", 0.0),
            total_price=params.get("total_price", 0.0),
            category=params.get("category", ""),
            attributes={k: v for k, v in params.items() 
                      if k not in ["quantity", "unit", "unit_price", "total_price", "category", "bill_id"]}
        )
    
    @staticmethod
    def erp_contract_to_project(contract: ERPContract) -> Dict:
        """将ERP合同转换为NeuralSite项目"""
        return {
            "project_id": f"proj_{contract.contract_id}",
            "description": contract.contract_name,
            "coordinate_system": "ERP_IMPORTED",
            "parameters": {
                "contract_id": contract.contract_id,
                "contract_type": contract.contract_type,
                "amount": contract.amount,
                "party_a": contract.party_a,
                "party_b": contract.party_b,
                "sign_date": contract.sign_date,
                "start_date": contract.start_date,
                "end_date": contract.end_date,
                "status": contract.status
            },
            "components": [
                ERPDataConverter.erp_bill_to_component(
                    ERPDataConverter.component_to_erp_bill(
                        {"component_id": f"bill_{item.bill_id}", 
                         "description": item.bill_name,
                         "parameters": {"quantity": item.quantity, "unit": item.unit,
                                      "unit_price": item.unit_price, "total_price": item.total_price,
                                      "category": item.category}}
                    )
                )
                for item in contract.items
            ]
        }
    
    @staticmethod
    def erp_measurement_to_component(measurement: ERPMeasurement) -> Dict:
        """将ERP计量转换为NeuralSite组件"""
        return {
            "component_id": f"meas_{measurement.measurement_id}",
            "component_type": "Measurement",
            "description": f"计量 {measurement.period_id}",
            "parameters": {
                "measurement_id": measurement.measurement_id,
                "period_id": measurement.period_id,
                "project_id": measurement.project_id,
                "bill_item_id": measurement.bill_item_id,
                "quantity": measurement.quantity,
                "amount": measurement.amount,
                "measurement_date": measurement.measurement_date,
                "status": measurement.status
            }
        }


# ========== 抽象适配器 ==========

class ERPAdapter(ABC):
    """ERP适配器基类"""
    
    def __init__(self, config: Dict[str, Any], sync_config: Optional[SyncConfig] = None):
        self.config = config
        self.sync_config = sync_config or SyncConfig()
        self.connected = False
    
    @property
    @abstractmethod
    def erp_type(self) -> ERPType:
        """ERP系统类型"""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """连接ERP系统"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def get_contracts(self) -> List[ERPContract]:
        """获取合同列表"""
        pass
    
    @abstractmethod
    def get_bills(self, contract_id: str) -> List[ERPBillItem]:
        """获取清单列表"""
        pass
    
    @abstractmethod
    def get_measurements(self, project_id: str) -> List[ERPMeasurement]:
        """获取计量数据"""
        pass
    
    @abstractmethod
    def push_measurement(self, measurement: ERPMeasurement) -> bool:
        """推送计量数据"""
        pass
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            return self.connect()
        except Exception as e:
            logger.error(f"ERP健康检查失败: {e}")
            return False


# ========== 广联达适配器 ==========

class GlodonAdapter(ERPAdapter):
    """广联达ERP适配器
    
    广联达BIM5D API对接
    API文档: https://open.glodon.com/
    """
    
    def __init__(self, config: Dict[str, Any], sync_config: Optional[SyncConfig] = None):
        super().__init__(config, sync_config)
        self.api_url = config.get("api_url", "https://api.glodon.com/bim5d")
        self.app_id = config.get("app_id", "")
        self.app_secret = config.get("app_secret", "")
        self.project_code = config.get("project_code", "")
    
    @property
    def erp_type(self) -> ERPType:
        return ERPType.GLODON
    
    def connect(self) -> bool:
        """连接广联达API"""
        logger.info(f"连接广联达API: {self.api_url}")
        # 模拟连接（实际需要实现OAuth2认证）
        self.connected = True
        return True
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info("已断开广联达连接")
    
    def get_contracts(self) -> List[ERPContract]:
        """获取合同列表"""
        logger.info("获取广联达合同列表")
        # 模拟数据（实际需要调用API）
        return [
            ERPContract(
                contract_id="GLD-CT-2024-001",
                contract_name="某高速公路建设工程施工合同",
                contract_type="总价合同",
                amount=15000000.00,
                party_a="某市交通运输局",
                party_b="某建设集团有限公司",
                sign_date="2024-01-15",
                start_date="2024-03-01",
                end_date="2026-12-31",
                status="执行中",
                items=[]
            )
        ]
    
    def get_bills(self, contract_id: str) -> List[ERPBillItem]:
        """获取清单列表"""
        logger.info(f"获取广联达清单: {contract_id}")
        # 模拟数据
        return [
            ERPBillItem(
                bill_id="0101",
                bill_name="挖土方",
                unit="m³",
                quantity=50000.0,
                unit_price=25.00,
                total_price=1250000.00,
                category="土石方工程"
            ),
            ERPBillItem(
                bill_id="0102",
                bill_name="填土方",
                unit="m³",
                quantity=45000.0,
                unit_price=18.00,
                total_price=810000.00,
                category="土石方工程"
            ),
            ERPBillItem(
                bill_id="0201",
                bill_name="C30混凝土基础",
                unit="m³",
                quantity=8000.0,
                unit_price=520.00,
                total_price=4160000.00,
                category="混凝土工程"
            )
        ]
    
    def get_measurements(self, project_id: str) -> List[ERPMeasurement]:
        """获取计量数据"""
        logger.info(f"获取广联达计量: {project_id}")
        # 模拟数据
        return [
            ERPMeasurement(
                measurement_id="MEAS-2024-001",
                period_id="第一期",
                project_id=project_id,
                bill_item_id="0101",
                quantity=10000.0,
                amount=250000.00,
                measurement_date="2024-06-30",
                status="已审核"
            ),
            ERPMeasurement(
                measurement_id="MEAS-2024-002",
                period_id="第二期",
                project_id=project_id,
                bill_item_id="0101",
                quantity=15000.0,
                amount=375000.00,
                measurement_date="2024-09-30",
                status="已审核"
            )
        ]
    
    def push_measurement(self, measurement: ERPMeasurement) -> bool:
        """推送计量数据"""
        logger.info(f"推送计量到广联达: {measurement.measurement_id}")
        # 实际需要调用API
        return True


# ========== 鲁班适配器 ==========

class LubanAdapter(ERPAdapter):
    """鲁班ERP适配器
    
    鲁班BIM API对接
    """
    
    def __init__(self, config: Dict[str, Any], sync_config: Optional[SyncConfig] = None):
        super().__init__(config, sync_config)
        self.api_url = config.get("api_url", "https://api.lubangroup.com")
        self.enterprise_id = config.get("enterprise_id", "")
        self.project_id = config.get("project_id", "")
        self.api_key = config.get("api_key", "")
    
    @property
    def erp_type(self) -> ERPType:
        return ERPType.LUBAN
    
    def connect(self) -> bool:
        """连接鲁班API"""
        logger.info(f"连接鲁班API: {self.api_url}")
        # 模拟连接
        self.connected = True
        return True
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info("已断开鲁班连接")
    
    def get_contracts(self) -> List[ERPContract]:
        """获取合同列表"""
        logger.info("获取鲁班合同列表")
        return [
            ERPContract(
                contract_id="LB-CT-2024-001",
                contract_name="某大桥施工合同",
                contract_type="单价合同",
                amount=28000000.00,
                party_a="某市重点工程建设指挥部",
                party_b="某桥梁工程公司",
                sign_date="2024-02-01",
                start_date="2024-04-01",
                end_date="2027-03-31",
                status="执行中",
                items=[]
            )
        ]
    
    def get_bills(self, contract_id: str) -> List[ERPBillItem]:
        """获取清单列表"""
        logger.info(f"获取鲁班清单: {contract_id}")
        return [
            ERPBillItem(
                bill_id="A1-001",
                bill_name="灌注桩",
                unit="m",
                quantity=12000.0,
                unit_price=1800.00,
                total_price=21600000.00,
                category="桩基工程"
            ),
            ERPBillItem(
                bill_id="A1-002",
                bill_name="承台混凝土",
                unit="m³",
                quantity=3500.0,
                unit_price=680.00,
                total_price=2380000.00,
                category="混凝土工程"
            )
        ]
    
    def get_measurements(self, project_id: str) -> List[ERPMeasurement]:
        """获取计量数据"""
        logger.info(f"获取鲁班计量: {project_id}")
        return [
            ERPMeasurement(
                measurement_id="LB-MEAS-001",
                period_id="2024年6月",
                project_id=project_id,
                bill_item_id="A1-001",
                quantity=3000.0,
                amount=5400000.00,
                measurement_date="2024-06-25",
                status="已计量"
            )
        ]
    
    def push_measurement(self, measurement: ERPMeasurement) -> bool:
        """推送计量数据"""
        logger.info(f"推送计量到鲁班: {measurement.measurement_id}")
        return True


# ========== 同步引擎 ==========

class SyncEngine:
    """同步引擎
    
    负责定时同步、增量同步、冲突处理
    """
    
    def __init__(self, adapter: ERPAdapter, config: SyncConfig):
        self.adapter = adapter
        self.config = config
        self.sync_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.sync_history: List[SyncRecord] = []
        self.last_sync_time: Optional[datetime] = None
        self.on_sync_callback: Optional[Callable[[SyncRecord], None]] = None
    
    def compute_hash(self, data: Dict) -> str:
        """计算数据哈希"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def check_conflict(self, source_data: Dict, target_data: Dict) -> bool:
        """检查冲突"""
        if not target_data:
            return False
        
        source_hash = self.compute_hash(source_data)
        target_hash = self.compute_hash(target_data)
        
        # 如果源和目标数据哈希不同，可能存在冲突
        return source_hash != target_hash
    
    def resolve_conflict(self, source_data: Dict, target_data: Dict, 
                        source_time: datetime, target_time: datetime) -> Dict:
        """解决冲突"""
        resolution = self.config.conflict_resolution
        
        if resolution == ConflictResolution.NEURALSITE_WINS:
            return source_data
        elif resolution == ConflictResolution.ERP_WINS:
            return target_data
        elif resolution == ConflictResolution.NEWEST_WINS:
            # 以最新修改时间为准
            return source_data if source_time > target_time else target_data
        else:
            # MANUAL - 返回空，需要人工处理
            return {}
    
    def sync_contracts(self, ns_projects: List[Dict], erp_contracts: List[ERPContract]) -> List[SyncRecord]:
        """同步合同"""
        records = []
        
        for contract in erp_contracts:
            # 查找对应的NeuralSite项目
            ns_project = next((p for p in ns_projects 
                            if p.get("parameters", {}).get("contract_id") == contract.contract_id), None)
            
            source_data = contract.to_dict()
            target_data = ns_project or {}
            
            # 检查冲突
            has_conflict = self.check_conflict(source_data, target_data)
            
            if has_conflict:
                resolved = self.resolve_conflict(
                    source_data, target_data,
                    datetime.now(),  # ERP数据时间
                    datetime.fromisoformat(ns_project.get("sync_time", "2024-01-01")) if ns_project else datetime.now()
                )
                logger.info(f"冲突已解决: {contract.contract_id} -> {resolved}")
            
            # 创建同步记录
            record = SyncRecord(
                record_id=f"sync_{contract.contract_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                entity_type="contract",
                entity_id=contract.contract_id,
                direction=SyncDirection.ERP_TO_NEURALSITE,
                status=SyncStatus.COMPLETED if not has_conflict else SyncStatus.CONFLICT,
                source_data=source_data,
                target_data=target_data,
                source_hash=self.compute_hash(source_data),
                target_hash=self.compute_hash(target_data),
                sync_time=datetime.now()
            )
            records.append(record)
        
        return records
    
    def sync_bills(self, ns_components: List[Dict], erp_bills: List[ERPBillItem]) -> List[SyncRecord]:
        """同步清单"""
        records = []
        
        for bill in erp_bills:
            ns_component = next((c for c in ns_components 
                               if c.get("parameters", {}).get("bill_id") == bill.bill_id), None)
            
            source_data = bill.to_dict()
            target_data = ns_component or {}
            
            has_conflict = self.check_conflict(source_data, target_data)
            
            record = SyncRecord(
                record_id=f"sync_bill_{bill.bill_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                entity_type="bill",
                entity_id=bill.bill_id,
                direction=SyncDirection.ERP_TO_NEURALSITE,
                status=SyncStatus.COMPLETED if not has_conflict else SyncStatus.CONFLICT,
                source_data=source_data,
                target_data=target_data,
                source_hash=self.compute_hash(source_data),
                target_hash=self.compute_hash(target_data),
                sync_time=datetime.now()
            )
            records.append(record)
        
        return records
    
    def sync_measurements(self, ns_measurements: List[Dict], 
                         erp_measurements: List[ERPMeasurement]) -> List[SyncRecord]:
        """同步计量数据"""
        records = []
        
        for measurement in erp_measurements:
            ns_meas = next((m for m in ns_measurements 
                          if m.get("parameters", {}).get("measurement_id") == measurement.measurement_id), None)
            
            source_data = measurement.to_dict()
            target_data = ns_meas or {}
            
            record = SyncRecord(
                record_id=f"sync_meas_{measurement.measurement_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                entity_type="measurement",
                entity_id=measurement.measurement_id,
                direction=SyncDirection.NEURALSITE_TO_ERP,
                status=SyncStatus.COMPLETED,
                source_data=source_data,
                target_data=target_data,
                source_hash=self.compute_hash(source_data),
                target_hash=self.compute_hash(target_data),
                sync_time=datetime.now()
            )
            records.append(record)
        
        return records
    
    def start_auto_sync(self):
        """启动自动同步"""
        if self.sync_thread and self.sync_thread.is_alive():
            logger.warning("同步线程已在运行")
            return
        
        self.stop_event.clear()
        self.sync_thread = Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info("自动同步已启动")
    
    def stop_auto_sync(self):
        """停止自动同步"""
        if self.sync_thread:
            self.stop_event.set()
            self.sync_thread.join(timeout=10)
            logger.info("自动同步已停止")
    
    def _sync_loop(self):
        """同步循环"""
        while not self.stop_event.is_set():
            try:
                # 执行同步
                self._execute_sync()
                
                # 等待下一次同步
                self.stop_event.wait(self.config.interval_seconds)
            except Exception as e:
                logger.error(f"同步循环异常: {e}")
                self.stop_event.wait(60)  # 发生异常后等待1分钟
    
    def _execute_sync(self):
        """执行同步"""
        logger.info("开始执行同步...")
        
        # 这里需要接入NeuralSite的数据层
        # 模拟调用
        ns_projects = []  # 从NeuralSite获取的项目
        ns_components = []  # 从NeuralSite获取的组件
        
        # 从ERP获取数据
        if not self.adapter.connected:
            self.adapter.connect()
        
        erp_contracts = self.adapter.get_contracts()
        
        for contract in erp_contracts:
            erp_bills = self.adapter.get_bills(contract.contract_id)
            erp_measurements = self.adapter.get_measurements(contract.contract_id)
            
            # 执行同步
            self.sync_contracts(ns_projects, [contract])
            self.sync_bills(ns_components, erp_bills)
            self.sync_measurements([], erp_measurements)
        
        self.last_sync_time = datetime.now()
        logger.info("同步完成")
    
    def trigger_sync(self):
        """触发立即同步"""
        self._execute_sync()


# ========== ERP适配器工厂 ==========

class ERPAdapterFactory:
    """ERP适配器工厂"""
    
    @staticmethod
    def create_adapter(erp_type: ERPType, config: Dict[str, Any], 
                      sync_config: Optional[SyncConfig] = None) -> ERPAdapter:
        """创建适配器"""
        if erp_type == ERPType.GLODON:
            return GlodonAdapter(config, sync_config)
        elif erp_type == ERPType.LUBAN:
            return LubanAdapter(config, sync_config)
        else:
            raise ValueError(f"不支持的ERP类型: {erp_type}")
    
    @staticmethod
    def get_available_adapters() -> List[ERPType]:
        """获取可用的适配器"""
        return [ERPType.GLODON, ERPType.LUBAN]


# ========== Feature Flag 控制 ==========

class ERPFeatureFlags:
    """ERP功能开关"""
    
    # Feature Flags
    ENABLED = True
    GLODON_ENABLED = True
    LUBAN_ENABLED = True
    AUTO_SYNC_ENABLED = True
    BIDIRECTIONAL_SYNC = True
    CONFLICT_DETECTION = True
    
    @classmethod
    def is_enabled(cls, feature: str) -> bool:
        """检查功能是否启用"""
        return getattr(cls, feature.upper(), False)
    
    @classmethod
    def enable(cls, feature: str):
        """启用功能"""
        setattr(cls, feature.upper(), True)
    
    @classmethod
    def disable(cls, feature: str):
        """禁用功能"""
        setattr(cls, feature.upper(), False)


# ========== 导出类 ==========

__all__ = [
    "ERPType",
    "SyncDirection", 
    "SyncStatus",
    "ConflictResolution",
    "ERPBillItem",
    "ERPContract",
    "ERPMeasurement",
    "SyncRecord",
    "SyncConfig",
    "ERPAdapter",
    "GlodonAdapter",
    "LubanAdapter",
    "ERPDataConverter",
    "SyncEngine",
    "ERPAdapterFactory",
    "ERPFeatureFlags"
]


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例：创建广联达适配器并同步数据
    
    # 1. 配置
    config = {
        "api_url": "https://api.glodon.com/bim5d",
        "app_id": "your_app_id",
        "app_secret": "your_app_secret",
        "project_code": "PROJECT_001"
    }
    
    sync_config = SyncConfig(
        enabled=True,
        direction=SyncDirection.BIDIRECTIONAL,
        interval_seconds=300,
        conflict_resolution=ConflictResolution.NEWEST_WINS
    )
    
    # 2. 创建适配器
    adapter = ERPAdapterFactory.create_adapter(ERPType.GLODON, config, sync_config)
    
    # 3. 连接
    if adapter.connect():
        print("✓ 已连接到广联达")
        
        # 4. 获取数据
        contracts = adapter.get_contracts()
        print(f"获取到 {len(contracts)} 个合同")
        
        for contract in contracts:
            print(f"  - {contract.contract_name}: {contract.amount:,.2f}元")
            
            bills = adapter.get_bills(contract.contract_id)
            print(f"    清单数量: {len(bills)}")
            
            measurements = adapter.get_measurements(contract.contract_id)
            print(f"    计量期次: {len(measurements)}")
        
        # 5. 数据转换
        converter = ERPDataConverter()
        ns_project = converter.erp_contract_to_project(contracts[0])
        print(f"\n转换为NeuralSite项目: {ns_project['project_id']}")
        
        # 6. 启动同步引擎
        if ERPFeatureFlags.AUTO_SYNC_ENABLED:
            sync_engine = SyncEngine(adapter, sync_config)
            sync_engine.start_auto_sync()
            print("✓ 自动同步已启动")
        
        # 断开连接
        adapter.disconnect()
    else:
        print("✗ 连接失败")

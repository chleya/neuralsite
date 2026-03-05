# -*- coding: utf-8 -*-
"""
ERP适配器单元测试
"""

import unittest
import json
from datetime import datetime
from core.integrations.erp_adapter import (
    ERPType,
    SyncDirection,
    SyncStatus,
    ConflictResolution,
    ERPBillItem,
    ERPContract,
    ERPMeasurement,
    SyncRecord,
    SyncConfig,
    ERPAdapter,
    GlodonAdapter,
    LubanAdapter,
    ERPDataConverter,
    SyncEngine,
    ERPAdapterFactory,
    ERPFeatureFlags
)


class TestERPDataModels(unittest.TestCase):
    """测试数据模型"""
    
    def test_erp_bill_item(self):
        """测试工程量清单项"""
        bill = ERPBillItem(
            bill_id="0101",
            bill_name="挖土方",
            unit="m³",
            quantity=50000.0,
            unit_price=25.00,
            total_price=1250000.00,
            category="土石方工程"
        )
        
        data = bill.to_dict()
        self.assertEqual(data["billId"], "0101")
        self.assertEqual(data["billName"], "挖土方")
        self.assertEqual(data["quantity"], 50000.0)
    
    def test_erp_contract(self):
        """测试ERP合同"""
        contract = ERPContract(
            contract_id="CT-001",
            contract_name="测试合同",
            contract_type="总价合同",
            amount=1000000.0,
            party_a="甲方",
            party_b="乙方",
            sign_date="2024-01-01",
            start_date="2024-03-01",
            end_date="2025-12-31",
            status="执行中"
        )
        
        data = contract.to_dict()
        self.assertEqual(data["contractId"], "CT-001")
        self.assertEqual(data["amount"], 1000000.0)
    
    def test_erp_measurement(self):
        """测试计量数据"""
        measurement = ERPMeasurement(
            measurement_id="MEAS-001",
            period_id="第一期",
            project_id="PROJ-001",
            bill_item_id="0101",
            quantity=10000.0,
            amount=250000.00,
            measurement_date="2024-06-30",
            status="已审核"
        )
        
        data = measurement.to_dict()
        self.assertEqual(data["measurementId"], "MEAS-001")
        self.assertEqual(data["quantity"], 10000.0)


class TestERPDataConverter(unittest.TestCase):
    """测试数据转换器"""
    
    def test_erp_bill_to_component(self):
        """测试ERP清单转NeuralSite组件"""
        bill = ERPBillItem(
            bill_id="0101",
            bill_name="挖土方",
            unit="m³",
            quantity=50000.0,
            unit_price=25.00,
            total_price=1250000.00,
            category="土石方工程"
        )
        
        component = ERPDataConverter.erp_bill_to_component(bill)
        
        self.assertEqual(component["component_id"], "bill_0101")
        self.assertEqual(component["description"], "挖土方")
        self.assertEqual(component["parameters"]["quantity"], 50000.0)
        self.assertEqual(component["parameters"]["unit"], "m³")
    
    def test_component_to_erp_bill(self):
        """测试NeuralSite组件转ERP清单"""
        component = {
            "component_id": "bill_0101",
            "description": "挖土方",
            "parameters": {
                "quantity": 50000.0,
                "unit": "m³",
                "unit_price": 25.00,
                "total_price": 1250000.00,
                "category": "土石方工程"
            }
        }
        
        bill = ERPDataConverter.component_to_erp_bill(component)
        
        self.assertEqual(bill.bill_id, "0101")
        self.assertEqual(bill.bill_name, "挖土方")
        self.assertEqual(bill.quantity, 50000.0)
    
    def test_erp_contract_to_project(self):
        """测试ERP合同转NeuralSite项目"""
        contract = ERPContract(
            contract_id="CT-001",
            contract_name="测试合同",
            contract_type="总价合同",
            amount=1000000.0,
            party_a="甲方",
            party_b="乙方",
            sign_date="2024-01-01",
            start_date="2024-03-01",
            end_date="2025-12-31",
            status="执行中",
            items=[
                ERPBillItem("0101", "挖土方", "m³", 50000.0, 25.0, 1250000.0, "土石方工程")
            ]
        )
        
        project = ERPDataConverter.erp_contract_to_project(contract)
        
        self.assertEqual(project["project_id"], "proj_CT-001")
        self.assertEqual(project["parameters"]["contract_id"], "CT-001")
        self.assertEqual(len(project["components"]), 1)


class TestGlodonAdapter(unittest.TestCase):
    """测试广联达适配器"""
    
    def setUp(self):
        self.config = {
            "api_url": "https://api.glodon.com/bim5d",
            "app_id": "test_app_id",
            "app_secret": "test_secret",
            "project_code": "TEST_PROJECT"
        }
        self.adapter = GlodonAdapter(self.config)
    
    def test_erp_type(self):
        """测试ERP类型"""
        self.assertEqual(self.adapter.erp_type, ERPType.GLODON)
    
    def test_connect(self):
        """测试连接"""
        result = self.adapter.connect()
        self.assertTrue(result)
        self.assertTrue(self.adapter.connected)
    
    def test_disconnect(self):
        """测试断开连接"""
        self.adapter.connect()
        self.adapter.disconnect()
        self.assertFalse(self.adapter.connected)
    
    def test_get_contracts(self):
        """测试获取合同"""
        self.adapter.connect()
        contracts = self.adapter.get_contracts()
        self.assertGreater(len(contracts), 0)
        self.assertIsInstance(contracts[0], ERPContract)
    
    def test_get_bills(self):
        """测试获取清单"""
        self.adapter.connect()
        bills = self.adapter.get_bills("TEST-CT-001")
        self.assertGreater(len(bills), 0)
        self.assertIsInstance(bills[0], ERPBillItem)
    
    def test_get_measurements(self):
        """测试获取计量数据"""
        self.adapter.connect()
        measurements = self.adapter.get_measurements("TEST-PROJ-001")
        self.assertGreater(len(measurements), 0)
        self.assertIsInstance(measurements[0], ERPMeasurement)


class TestLubanAdapter(unittest.TestCase):
    """测试鲁班适配器"""
    
    def setUp(self):
        self.config = {
            "api_url": "https://api.lubangroup.com",
            "enterprise_id": "TEST_ENT",
            "project_id": "TEST_PROJ",
            "api_key": "TEST_KEY"
        }
        self.adapter = LubanAdapter(self.config)
    
    def test_erp_type(self):
        """测试ERP类型"""
        self.assertEqual(self.adapter.erp_type, ERPType.LUBAN)
    
    def test_connect(self):
        """测试连接"""
        result = self.adapter.connect()
        self.assertTrue(result)
        self.assertTrue(self.adapter.connected)


class TestSyncEngine(unittest.TestCase):
    """测试同步引擎"""
    
    def setUp(self):
        self.config = {
            "api_url": "https://api.glodon.com/bim5d",
            "app_id": "test",
            "app_secret": "test"
        }
        self.adapter = GlodonAdapter(self.config)
        self.sync_config = SyncConfig(
            enabled=True,
            direction=SyncDirection.BIDIRECTIONAL,
            interval_seconds=60,
            conflict_resolution=ConflictResolution.NEWEST_WINS
        )
        self.engine = SyncEngine(self.adapter, self.sync_config)
    
    def test_compute_hash(self):
        """测试哈希计算"""
        data = {"key": "value", "number": 123}
        hash1 = self.engine.compute_hash(data)
        hash2 = self.engine.compute_hash(data)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 16)
    
    def test_check_conflict(self):
        """测试冲突检测"""
        source = {"name": "test", "value": 100}
        target = {"name": "test", "value": 100}
        
        # 相同数据不应冲突
        self.assertFalse(self.engine.check_conflict(source, target))
        
        # 不同数据应冲突
        target_diff = {"name": "test", "value": 200}
        self.assertTrue(self.engine.check_conflict(source, target_diff))
        
        # 空目标不应冲突
        self.assertFalse(self.engine.check_conflict(source, {}))
    
    def test_resolve_conflict_ns_wins(self):
        """测试冲突解决 - NeuralSite胜出"""
        self.sync_config.conflict_resolution = ConflictResolution.NEURALSITE_WINS
        
        source = {"name": "ns_data"}
        target = {"name": "erp_data"}
        
        resolved = self.engine.resolve_conflict(source, target, datetime.now(), datetime.now())
        self.assertEqual(resolved, source)
    
    def test_resolve_conflict_erp_wins(self):
        """测试冲突解决 - ERP胜出"""
        self.sync_config.conflict_resolution = ConflictResolution.ERP_WINS
        
        source = {"name": "ns_data"}
        target = {"name": "erp_data"}
        
        resolved = self.engine.resolve_conflict(source, target, datetime.now(), datetime.now())
        self.assertEqual(resolved, target)
    
    def test_sync_contracts(self):
        """测试合同同步"""
        contracts = [
            ERPContract(
                contract_id="CT-001",
                contract_name="测试合同",
                contract_type="总价合同",
                amount=1000000.0,
                party_a="甲方",
                party_b="乙方",
                sign_date="2024-01-01",
                start_date="2024-03-01",
                end_date="2025-12-31",
                status="执行中"
            )
        ]
        
        records = self.engine.sync_contracts([], contracts)
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].entity_type, "contract")
        self.assertEqual(records[0].entity_id, "CT-001")
    
    def test_sync_bills(self):
        """测试清单同步"""
        bills = [
            ERPBillItem("0101", "挖土方", "m³", 50000.0, 25.0, 1250000.0, "土石方工程")
        ]
        
        records = self.engine.sync_bills([], bills)
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].entity_type, "bill")
    
    def test_sync_measurements(self):
        """测试计量同步"""
        measurements = [
            ERPMeasurement(
                measurement_id="MEAS-001",
                period_id="第一期",
                project_id="PROJ-001",
                bill_item_id="0101",
                quantity=10000.0,
                amount=250000.00,
                measurement_date="2024-06-30",
                status="已审核"
            )
        ]
        
        records = self.engine.sync_measurements([], measurements)
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].entity_type, "measurement")


class TestERPAdapterFactory(unittest.TestCase):
    """测试适配器工厂"""
    
    def test_create_glodon_adapter(self):
        """测试创建广联达适配器"""
        config = {"api_url": "https://api.glodon.com", "app_id": "test", "app_secret": "test"}
        adapter = ERPAdapterFactory.create_adapter(ERPType.GLODON, config)
        
        self.assertIsInstance(adapter, GlodonAdapter)
        self.assertEqual(adapter.erp_type, ERPType.GLODON)
    
    def test_create_luban_adapter(self):
        """测试创建鲁班适配器"""
        config = {"api_url": "https://api.lubangroup.com", "api_key": "test"}
        adapter = ERPAdapterFactory.create_adapter(ERPType.LUBAN, config)
        
        self.assertIsInstance(adapter, LubanAdapter)
        self.assertEqual(adapter.erp_type, ERPType.LUBAN)
    
    def test_get_available_adapters(self):
        """测试获取可用适配器"""
        adapters = ERPAdapterFactory.get_available_adapters()
        
        self.assertIn(ERPType.GLODON, adapters)
        self.assertIn(ERPType.LUBAN, adapters)


class TestERPFeatureFlags(unittest.TestCase):
    """测试Feature Flags"""
    
    def test_default_flags(self):
        """测试默认开关状态"""
        self.assertTrue(ERPFeatureFlags.ENABLED)
        self.assertTrue(ERPFeatureFlags.GLODON_ENABLED)
        self.assertTrue(ERPFeatureFlags.LUBAN_ENABLED)
    
    def test_is_enabled(self):
        """测试功能检查"""
        self.assertTrue(ERPFeatureFlags.is_enabled("enabled"))
        self.assertTrue(ERPFeatureFlags.is_enabled("glodon_enabled"))
    
    def test_enable_disable(self):
        """测试启用/禁用"""
        ERPFeatureFlags.disable("glodon_enabled")
        self.assertFalse(ERPFeatureFlags.is_enabled("glodon_enabled"))
        
        ERPFeatureFlags.enable("glodon_enabled")
        self.assertTrue(ERPFeatureFlags.is_enabled("glodon_enabled"))


if __name__ == "__main__":
    unittest.main()

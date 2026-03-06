# NeuralSite 数据驱动架构

## 目录结构

```
neuralsite/
├── data_driven/           # 数据驱动架构
│   ├── standards/         # 数据标准
│   │   ├── __init__.py
│   │   ├── formats.py    # 格式标准
│   │   ├── business.py   # 业务校验规则
│   │   └── semantic.py   # 语义映射
│   │
│   ├── lineage/          # 数据血缘
│   │   ├── __init__.py
│   │   ├── models.py     # 血缘数据模型
│   │   ├── storage.py   # 血缘存储
│   │   └── trace.py     # 追溯查询
│   │
│   ├── blockchain/       # 区块链存证
│   │   ├── __init__.py
│   │   ├── hash.py       # 哈希计算
│   │   ├── contract.py   # 存证合约
│   │   └── verify.py    # 验真模块
│   │
│   ├── interfaces/       # 数据接口
│   │   ├── __init__.py
│   │   ├── rest.py       # REST API
│   │   └── websocket.py  # WebSocket订阅
│   │
│   ├── validation/       # 数据校验引擎
│   │   ├── __init__.py
│   │   ├── engine.py     # 校验执行引擎
│   │   └── rules.py      # 规则定义
│   │
│   └── generation/       # 功能生成
│       ├── __init__.py
│       ├── parser.py      # 需求解析
│       ├── generator.py   # 代码生成
│       └── templates/     # 模板库
│
├── packages/             # 原有的包
│   ├── core/            # 核心引擎
│   └── mobile/          # 移动端
│
└── DATA_DRIVEN_PLAN.md  # 数据驱动企划书
```

## 模块说明

| 模块 | 职责 |
|------|------|
| standards | 数据标准（桩号/坐标/照片格式） |
| lineage | 数据血缘追溯 |
| blockchain | 哈希存证与验真 |
| interfaces | REST API + WebSocket |
| validation | 校验引擎 |
| generation | 对话生成功能 |

## 快速开始

```python
from data_driven.standards import StationFormat
from data_driven.validation import ValidationEngine
from data_driven.lineage import DataLineage

# 1. 数据标准化
station = StationFormat.parse("K5+800")  # → 5800.0

# 2. 数据校验
result = ValidationEngine.validate(data, "pavement")
# result.passed, result.errors, result.warnings

# 3. 血缘记录
lineage = DataLineage()
lineage.record_source(data_id, "import", source_file)

# 4. 上链存证
from data_driven.blockchain import ChainRecord
ChainRecord.submit(data_id, data_hash, "design_change")

# 5. 对话生成
# 你提需求 → 我生成代码
```

---

**版本**: V3.0
**更新**: 2026-03-06

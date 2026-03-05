# NeuralSite 代码质量审查报告

**审查日期**: 2026-03-05  
**审查范围**: packages/core/api/, packages/core/services/, packages/studio/src/, packages/mobile/lib/  
**总体评分**: 6.5/10

---

## 一、代码风格问题

### 🔴 严重问题

#### 1. Python - 全局状态滥用 (违反架构原则)
**文件**: `packages/core/services/ai_service.py`  
**问题**: 使用全局变量 `_ai_service` 存储服务实例
```python
_ai_service: Optional[AIService] = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
```
**违反**: ARCHITECTURE.md 中 "FastAPI：使用 dependency injection，禁止全局状态"

#### 2. Python - EngineService 全局状态
**文件**: `packages/core/api/dependencies.py`  
**问题**: 类变量 `_engines` 存储引擎实例
```python
class EngineService:
    _engines: Dict[str, NeuralSiteEngine] = {}
```
**违反**: 同样违反依赖注入原则

#### 3. CORS 配置允许所有来源
**文件**: `packages/core/api/main.py`  
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 安全风险
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 🟡 中等问题

#### 4. Python - Import 顺序不规范
**文件**: `packages/core/api/main.py`, `packages/core/services/ai_service.py`  
**问题**: 未按照 PEP8 顺序 (标准库 → 第三方 → 项目内部)

#### 5. TypeScript - 内联样式
**文件**: `packages/studio/src/pages/Dashboard.tsx`, `packages/studio/src/components/BIMViewer.tsx`  
**问题**: 使用大量内联样式而非 CSS Modules/Styled Components
```tsx
<div style={{
  padding: '20px',
  background: '#1a1a2e',
  ...
}}>
```

#### 6. TypeScript - 未使用的变量
**文件**: `packages/studio/src/pages/Dashboard.tsx`
```tsx
const [, setActiveSection] = useState<string | null>(null)  // 值未使用
```

---

## 二、架构遵循问题

### 🔴 严重问题

#### 7. 硬编码坐标转换 (魔法数字)
**文件**: `packages/core/api/v1/routes/spatial_v1.py`  
```python
def _transform_coords(x: float, y: float, from_srid: str, to_srid: str):
    if from_srid == "EPSG:4547" and to_srid == "EPSG:4326":
        return {
            "lon": x - 0.0001,  # 魔法数字 0.0001
            "lat": y - 0.0001
        }
```
**问题**: 简化实现不准确，应使用 pyproj 库

#### 8. 硬编码默认值
**文件**: `packages/core/api/dependencies.py`
```python
class TransformRequest(BaseModel):
    from_srid: str = "EPSG:4547"  # 硬编码
    to_srid: str = "EPSG:4326"     # 硬编码

class RangeQueryRequest(BaseModel):
    interval: float = 100  # 魔法数字
```

#### 9. 配置文件未分离
**问题**: 多个文件包含业务配置，应抽取到统一配置模块

### 🟡 中等问题

#### 10. Mock 数据硬编码
**文件**: `packages/studio/src/pages/Dashboard.tsx`
```tsx
const mockStats = {
  totalRoutes: 12,
  totalStations: 156,
  ...
}
```

---

## 三、潜在问题

### 🔴 严重问题

#### 11. 异常吞没
**文件**: `packages/core/services/ai_service.py`
```python
except Exception as e:
    logger.error(f"Photo classification failed: {e}")
    return PhotoClassificationResponse(
        category="other",
        ...
        description=f"分类失败: {str(e)}",  # 返回失败信息但调用方可能忽略
    )
```
**风险**: 隐藏真实错误，调用方可能误以为成功

#### 12. 坐标转换实现不完整
**文件**: `packages/core/api/v1/routes/spatial_v1.py`  
**问题**: 简化实现只支持两种坐标系转换，其他情况返回原坐标
```python
return {"x": x, "y": y}  # 默认返回原坐标，无警告
```

### 🟡 中等问题

#### 13. GPS 权限处理不完整
**文件**: `packages/mobile/lib/services/photo_service.dart`
```dart
if (permission == LocationPermission.deniedForever) {
    throw PhotoServiceException('定位权限被永久拒绝');
    // 缺少引导用户去设置的逻辑
}
```

#### 14. 缺少资源清理
**文件**: `packages/mobile/lib/services/sync_service.dart`  
**问题**: 使用 Timer 但在 dispose 中只取消了一个 Timer
```dart
void dispose() {
    stopPeriodicSync();  // 只取消 _syncTimer
    _connectivityCheckTimer?.cancel();  // 但这个在其他地方可能被遗漏
}
```

#### 15. 潜在空指针风险
**文件**: `packages/mobile/lib/services/sync_service.dart`
```dart
await randomAccess * uploadFile.setPosition(i.chunkSize);  // randomAccess 可能为 null
```

---

## 四、代码复杂度问题

### 🟢 良好

#### 1. IssueService 结构清晰
**文件**: `packages/core/services/issue_service.py`  
**评价**: 虽然代码量较大 (~400行)，但按功能模块分区清晰 (CRUD、状态流转、关联操作)

#### 2. AppContext 设计合理
**文件**: `packages/studio/src/context/AppContext.tsx`  
**评价**: 使用 useReducer + Context 模式，结构清晰

### 🟡 中等

#### 3. SyncService 代码过长
**文件**: `packages/mobile/lib/services/sync_service.dart` (~650行)  
**建议**: 拆分为多个服务类 (PhotoSyncService, IssueSyncService 等)

---

## 五、良好实践

### 亮点

1. **类型定义完善**: TypeScript 和 Dart 都有完整的类型定义
2. **Pydantic 模型设计**: `p0_models.py` 使用 Pydantic + SQLAlchemy 双模式
3. **离线优先架构**: SyncService 实现完整的离线同步逻辑
4. **异常分类**: 定义了具体的异常类 (PhotoServiceException)
5. **组件拆分**: BIMViewer 等组件拆分为多个子组件

---

## 六、改进建议 (按优先级)

### P0 - 立即修复

| # | 问题 | 文件 | 修复建议 |
|---|------|------|----------|
| 1 | 全局状态 `_ai_service` | ai_service.py | 改用 FastAPI 依赖注入 |
| 2 | 全局状态 `EngineService._engines` | dependencies.py | 改用依赖注入 |
| 3 | CORS 允许所有来源 | main.py | 限制为具体域名 |
| 4 | 硬编码坐标转换 | spatial_v1.py | 使用 pyproj 库 |
| 5 | 异常吞没 | ai_service.py | 添加错误传播或重试机制 |

### P1 - 高优先级

| # | 问题 | 文件 | 修复建议 |
|---|------|------|----------|
| 6 | Import 顺序 | main.py 等 | 按 PEP8 排序 |
| 7 | 魔法数字 | dependencies.py | 抽取为配置常量 |
| 8 | 内联样式 | Dashboard.tsx 等 | 改用 CSS Modules |
| 9 | 未使用变量 | Dashboard.tsx | 移除或使用 |

### P2 - 中优先级

| # | 问题 | 文件 | 修复建议 |
|---|------|------|----------|
| 10 | SyncService 过长 | sync_service.dart | 拆分为多个服务 |
| 11 | GPS 权限引导 | photo_service.dart | 添加打开设置引导 |
| 12 | Mock 数据 | Dashboard.tsx | 抽取为 mock 文件 |

---

## 七、总结

### 评分明细

| 维度 | 得分 | 说明 |
|------|------|------|
| 代码风格 | 6/10 | Python/TS 存在不规范，Dart 较好 |
| 架构遵循 | 5/10 | 违反多项架构原则 (全局状态、硬编码) |
| 潜在问题 | 7/10 | 有风险但影响可控 |
| 代码复杂度 | 7/10 | 整体可维护，部分过长 |

**总体评分: 6.5/10**

### 关键风险

1. **安全风险**: CORS 允许所有来源
2. **架构违规**: 全局状态违反依赖注入原则
3. **数据风险**: 坐标转换实现不准确

### 改进方向

1. 立即修复全局状态和 CORS 问题
2. 引入 pyproj 处理坐标转换
3. 统一代码风格，使用 linter
4. 拆分过长文件，提高可维护性

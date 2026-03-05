# NeuralSite 架构原则（AI 必须严格遵守）

## 核心原则
- 所有改动必须保持分层清晰：core（纯几何+业务逻辑） → studio（可视化） → mobile（Flutter 桥接）
- 严禁 Hardcode、魔法数字、直接修改第三方代码
- 所有新功能必须走 Feature Flag + 单元测试
- FastAPI：使用 dependency injection，禁止全局状态
- React/Three.js：组件必须纯函数 + hooks 规范
- Flutter：使用 Riverpod / Provider，禁止 setState 滥用

## 测试要求
- core：pytest -q
- studio：npm test -- --watchAll=false
- mobile：flutter test

## 7重安全防护
1. Token 防护：日志只读最后 300 行 + .openclawignore
2. 严禁安装任何依赖（标记 [NEED_DEP]）
3. 严禁毁灭命令
4. 遵守本架构文档
5. 固定测试命令
6. 最多重试 3 次
7. 触发防护立即暂停

任何违反以上原则的 PR 自动打 [ARCHITECTURE_VIOLATION] 标签

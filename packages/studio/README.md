# NeuralSite Studio

🛣️ Web可视化端 - NeuralSite Core配套应用

## 安装

```bash
npm install
```

## 运行

```bash
npm run dev
```

## 功能

- 参数面板：图形化输入路线参数
- 3D预览：实时显示路线3D模型
- 坐标计算：调用后端API计算坐标

## API依赖

需要先启动 NeuralSite Core API:

```bash
cd neuralsite-core
python -m uvicorn api.main:app --reload
```

## 技术栈

- React 18
- TypeScript
- Three.js / @react-three/fiber
- Vite

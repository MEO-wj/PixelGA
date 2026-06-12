# 🎨 像素画进化系统 — PixelGA

基于遗传算法的图像像素画逼近系统。上传一张图片，AI 通过逐代进化随机像素画，使其逐渐接近目标图像。

## ✨ 功能

- 📷 **上传任意图片**：支持常见图片格式，自动压缩为目标像素尺寸
- 🧬 **遗传算法进化**：锦标赛选择 + 均匀交叉 + 自适应变异
- 🔒 **逐像素锁定**：接近目标的像素自动冻结，计算力集中在未匹配区域
- 📊 **实时可视化**：WebSocket 推送每代结果，Canvas 实时渲染
- 🎯 **目标对比**：并排显示压缩后目标图与进化结果
- ⏯ **完整控制**：开始 / 暂停 / 继续 / 重置 / 下载
- ⚙ **可调参数**：种群大小、变异率、最大代数、像素尺寸

## 🏗 技术栈

| 层 | 技术 |
|----|------|
| 前端框架 | Vue 3 + TypeScript + Vite |
| 前端渲染 | HTML5 Canvas（像素级绘制） |
| 实时通信 | WebSocket（FastAPI 推送） |
| HTTP 通信 | Axios（上传/下载） |
| 后端框架 | Python FastAPI + Uvicorn |
| 图像处理 | Pillow + NumPy |
| 遗传算法 | NumPy 向量化并行计算 |

## 📁 项目结构

```
PixelGA/
├── backend/
│   ├── main.py              # FastAPI 入口 + WebSocket 端点
│   ├── ga_engine.py         # 遗传算法引擎（种群、选择、交叉、变异、适应度）
│   └── requirements.txt     # Python 依赖
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts       # Vite 配置（含 API/WS 代理）
│   ├── tsconfig.json
│   └── src/
│       ├── main.ts          # Vue 入口
│       ├── App.vue          # 根组件
│       ├── components/
│       │   ├── ImageUploader.vue   # 图片上传
│       │   ├── EvolutionView.vue   # Canvas 双栏显示
│       │   ├── ControlPanel.vue    # 参数 + 按钮
│       │   └── StatsBar.vue        # 代数 + 相似度
│       ├── composables/
│       │   └── useWebSocket.ts     # WebSocket 封装
│       └── style.css
└── docs/                    # 项目需求文档
```

## 🚀 部署方式

### 环境依赖

- **Python** ≥ 3.10
- **Node.js** ≥ 18
- **pip** 与 **npm**

### 1. 克隆项目

```bash
git clone <https://github.com/MEO-wj/PixelGA.git>
cd PixelGA
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端

```bash
python main.py
# FastAPI 运行在 http://localhost:8000
```

### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 5. 启动前端

```bash
npm run dev
# Vite 运行在 http://localhost:3000
```

### 6. 打开浏览器

访问 `http://localhost:3000`，上传图片，点击"开始进化"。

## 🔧 遗传算法参数

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| 像素尺寸 | 64 px | 16–256 | 目标图长边像素数 |
| 种群大小 | 100 | 10–200 | 每代个体数量 |
| 变异率 | 0.05 | 0.005–0.2 | 每个像素的变异概率基数 |
| 最大代数 | 5000 | 100–10000 | 进化停止代数上限 |
| 精英比例 | 0.15 | — | 每代保留的最优个体比例 |
| 锦标赛规模 | 5 | — | 选择时的竞争者数量 |

## 📡 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/upload` | POST | 上传图片（multipart），返回 target_id |
| `/api/download/{id}` | GET | 下载进化结果 PNG |
| `/ws/evolve/{id}` | WebSocket | 实时进化数据流 |

### WebSocket 消息协议

**服务端 → 客户端**

```json
// 初始状态
{"type": "init", "similarity": 5.2, "height": 64, "width": 48, "pixels": [...], "targetPixels": [...]}

// 每代更新
{"type": "generation", "generation": 42, "similarity": 78.5, "pixels": [...]}

// 进化完成
{"type": "complete", "generation": 5000}
```

**客户端 → 服务端**

```json
{"type": "start", "params": {"popSize": 100, "mutationRate": 0.05, "maxGenerations": 5000}}
{"type": "pause"}
{"type": "resume"}
{"type": "reset"}
```

## 📝 相似度计算

```
相似度 = max(0, 1 − √MSE / 104) × 100%

其中 MSE = 逐像素 RGB 均方误差
104 = 随机均匀像素的期望 √MSE（基准线）
```

- 随机噪点 ≈ 0%
- 完美匹配 = 100%

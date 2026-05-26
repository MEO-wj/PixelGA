# 鼠标防线 Cursor Defense

这是根据 `docs/cursor_defense_design.md` 做的可玩原型。现在项目拆成 C++ 后端和 TypeScript 前端：

- C++ 后端负责游戏规则、寻路、鸟群、碰撞、刷怪、卡牌效果和难度曲线。
- TypeScript 前端只负责收集鼠标位置、请求后端状态、绘制 Canvas 和展示 UI。

## 运行方式

第一次运行：

```bash
npm install
npm run build
```

开发时建议直接启动前后端：

```bash
npm run dev:all
```

也可以分开启动：

```bash
npm run build:backend
npm run start:backend
npm run dev
```

后端默认地址：`http://127.0.0.1:8787`  
前端默认地址：`http://127.0.0.1:5173`

## 目录说明

```text
backend/
  include/cursor_defense/      C++ 头文件
  src/                         C++ 实现文件
  bin/                         编译输出，不提交
frontend/
  index.html                   前端入口
  src/
    api/                       请求 C++ 后端
    render/                    Canvas 美术绘制
    ui/                        HUD 和卡牌界面
docs/
  cursor_defense_design.md     原始玩法设计
  algorithms/                  核心算法说明文档
  wave-difficulty.md           波次难度曲线说明
scripts/
  build-backend.ps1            编译 C++ 后端
  dev.ps1                      启动前后端开发环境
```

## 核心算法位置

- 向量场寻路：`backend/src/FlowField.cpp`
- 鸟群算法：`backend/src/Flocking.cpp`
- 游戏规则和难度曲线：`backend/src/GameEngine.cpp`
- 前端渲染：`frontend/src/render/CanvasRenderer.ts`

## 已完成内容

- 桌面地图、障碍物和核心文件。
- 10 个小光标跟随主鼠标移动。
- 初始光标最大速度从 `520` 提高到 `624`，提高了 20%。
- 三种病毒：普通病毒、快速病毒、垃圾文件怪。
- 病毒通过向量场绕过障碍物并移动到核心文件。
- 小光标接触病毒造成伤害，有单体冷却。
- 每 30 秒弹出三选一卡牌。
- 8 张 MVP 卡牌：数量、伤害、速度、减速、火焰轨迹、电流、文件备份、任务管理器。
- 难度改成 6 段波次表，刷怪间隔、血量、速度和敌人比例逐步提升。
- 文件完整度归零失败，撑过 3 分钟胜利。

"""
FastAPI 入口 — 图片上传 + WebSocket 实时进化推送
"""
import io
import json
import asyncio
import numpy as np
from pathlib import Path
from PIL import Image
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ga_engine import (
    DEFAULT_MAX_PIXEL, GAParams,
    create_random_population,
    calc_fitness,
    run_one_generation,
    mse_to_similarity,
)

app = FastAPI(title="Pixel Art GA Evolution")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储已上传的目标图 {target_id: {"arr": np.ndarray, "h": int, "w": int}}
targets: dict[str, dict] = {}
# 存储进化结果 {target_id: np.ndarray}
results: dict[str, np.ndarray] = {}
_counter = 0


def process_image(data: bytes, max_pixel: int = 64) -> tuple[np.ndarray, int, int]:
    """读取上传图片，缩放保持宽高比，长边 ≤ max_pixel"""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    ow, oh = img.size
    ratio = max_pixel / max(ow, oh)
    nw = max(1, round(ow * ratio))
    nh = max(1, round(oh * ratio))
    img = img.resize((nw, nh), Image.LANCZOS)
    return np.array(img, dtype=np.uint8), nh, nw


def array_to_png_bytes(arr: np.ndarray) -> io.BytesIO:
    """NumPy 数组 → PNG 字节流"""
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def pixels_to_json(arr: np.ndarray) -> list:
    """将像素数组转为 JSON 可序列化的嵌套列表"""
    return arr.tolist()


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...), pixelSize: int = 64):
    """上传目标图片，返回 target_id + 像素尺寸"""
    global _counter
    data = await file.read()
    size = max(16, min(256, pixelSize))
    arr, h, w = process_image(data, size)
    _counter += 1
    target_id = f"target_{_counter}"
    targets[target_id] = {"arr": arr, "h": h, "w": w}
    return {"target_id": target_id, "height": h, "width": w}


@app.get("/api/download/{target_id}")
async def download_result(target_id: str):
    """下载进化结果 PNG"""
    if target_id not in results:
        return {"error": "no result found"}
    buf = array_to_png_bytes(results[target_id])
    return StreamingResponse(buf, media_type="image/png")


@app.websocket("/ws/evolve/{target_id}")
async def evolve_websocket(ws: WebSocket, target_id: str):
    """WebSocket：接收控制指令，推送每代最优结果"""
    await ws.accept()

    if target_id not in targets:
        await ws.send_json({"type": "error", "message": "target not found"})
        await ws.close()
        return

    info = targets[target_id]
    target = info["arr"]
    h, w = info["h"], info["w"]
    params = GAParams()
    population = create_random_population(params.pop_size, h, w)
    generation = 0
    running = False
    paused = False

    async def send_state(similarity: float, mse: float):
        fitness = calc_fitness(population, target)
        best_idx = int(np.argmax(fitness))
        best = population[best_idx]
        results[target_id] = best
        await ws.send_json({
            "type": "generation",
            "generation": generation,
            "similarity": round(similarity, 2),
            "mse": round(mse, 1),
            "height": h,
            "width": w,
            "pixels": pixels_to_json(best),
        })

    # 发送初始随机状态（type=init，不触发前端的 running 状态）
    init_f = calc_fitness(population, target)
    init_bi = int(np.argmax(init_f))
    init_m = float(-init_f[init_bi])
    init_best = population[init_bi]
    results[target_id] = init_best
    await ws.send_json({
        "type": "init",
        "similarity": round(mse_to_similarity(init_m), 2),
        "height": h,
        "width": w,
        "pixels": pixels_to_json(init_best),
        "targetPixels": pixels_to_json(target),
    })

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)
                cmd = data.get("type", "")

                if cmd == "start":
                    print(f"[WS] start command received, params={data.get('params', {})}")
                    running = True
                    paused = False
                    if "params" in data:
                        p = data["params"]
                        params = GAParams(
                            pop_size=p.get("popSize", 100),
                            mutation_rate=p.get("mutationRate", 0.05),
                            elite_ratio=p.get("eliteRatio", 0.15),
                            max_generations=p.get("maxGenerations", 5000),
                        )
                    population = create_random_population(params.pop_size, h, w)
                    generation = 0

                elif cmd == "pause":
                    paused = True
                    running = False

                elif cmd == "resume":
                    running = True
                    paused = False

                elif cmd == "reset":
                    running = False
                    paused = False
                    population = create_random_population(params.pop_size, h, w)
                    generation = 0
                    f = calc_fitness(population, target)
                    bi = int(np.argmax(f))
                    m = float(-f[bi])
                    await send_state(mse_to_similarity(m), m)

            except asyncio.TimeoutError:
                pass

            if running and generation < params.max_generations:
                population, _, best_mse, avg_mse, similarity = run_one_generation(
                    population, target, params
                )
                generation += 1
                await send_state(similarity, best_mse)
                await asyncio.sleep(0.001)

            elif running and generation >= params.max_generations:
                running = False
                await ws.send_json({
                    "type": "complete",
                    "generation": generation,
                })

            await asyncio.sleep(0.005)

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
遗传算法引擎 — 像素画进化
个体 = H×W×3 NumPy 数组, uint8, 尺寸由目标图决定
"""
import numpy as np
from dataclasses import dataclass

DEFAULT_MAX_PIXEL = 64  # 默认长边最大像素数


@dataclass
class GAParams:
    pop_size: int = 100
    mutation_rate: float = 0.05
    elite_ratio: float = 0.15
    max_generations: int = 5000
    tournament_size: int = 5


def create_random_population(pop_size: int, height: int, width: int) -> np.ndarray:
    return np.random.randint(0, 256, (pop_size, height, width, 3), dtype=np.uint8)


def calc_fitness(population: np.ndarray, target: np.ndarray) -> np.ndarray:
    """适应度 = -MSE（越大越好，0 表示完全匹配）"""
    diff = population.astype(np.float32) - target.astype(np.float32)
    mse = np.mean(diff ** 2, axis=(1, 2, 3))
    return -mse


def mse_to_similarity(mse: float) -> float:
    """
    MSE → 相似度百分比 (0~100)
    基准：随机像素的期望 sqrt(MSE) ≈ 104 → 0%
          完美匹配 sqrt(MSE) = 0       → 100%
    """
    RANDOM_BASELINE = 104.0  # sqrt(E[MSE]) for random uniform [0,255]
    raw = max(0.0, 1.0 - np.sqrt(max(0, mse)) / RANDOM_BASELINE)
    return raw * 100.0


def tournament_select(population: np.ndarray, fitness: np.ndarray,
                      tournament_size: int = 5) -> np.ndarray:
    pop_size = len(population)
    candidates = np.random.randint(0, pop_size, size=(pop_size, tournament_size))
    best_in_tournament = np.argmax(fitness[candidates], axis=1)
    return candidates[np.arange(pop_size), best_in_tournament]


def uniform_crossover(parents: np.ndarray) -> np.ndarray:
    pop_size = len(parents)
    offspring = np.empty_like(parents)
    for i in range(0, pop_size, 2):
        p1 = parents[i].astype(np.int16)
        p2 = parents[min(i + 1, pop_size - 1)].astype(np.int16)
        mask = np.random.random(p1.shape[:2]) < 0.5
        mask3 = np.stack([mask] * 3, axis=-1)
        c1 = np.where(mask3, p1, p2)
        offspring[i] = np.clip(c1, 0, 255).astype(np.uint8)
        if i + 1 < pop_size:
            c2 = np.where(mask3, p2, p1)
            offspring[i + 1] = np.clip(c2, 0, 255).astype(np.uint8)
    return offspring


def mutate_adaptive(population: np.ndarray, target: np.ndarray,
                     base_rate: float) -> np.ndarray:
    """
    自适应变异 + 只接受改进
    - 每个像素尝试变异，只有离目标更近才保留
    - 接近目标的像素 → 低变异率 + 小步长（微调）
    - 远离目标的像素 → 高变异率 + 大步长（搜索）
    - 误差 < 3 的像素直接冻结，不再变异
    """
    diff = population.astype(np.float32) - target.astype(np.float32)
    abs_diff = np.abs(diff)
    pixel_error = np.mean(abs_diff, axis=-1, keepdims=True) / 255.0  # (pop, H, W, 1)

    # 自适应变异率：误差 → 0 则率 → 0，误差 → 1 则率 → base_rate*2
    adaptive_rate = base_rate * 2.0 * pixel_error
    # 误差 < 3/255 ≈ 0.012 → 直接冻结
    adaptive_rate[pixel_error < (3.0 / 255.0)] = 0.0

    # 自适应变异强度：sigma 范围 [3, 64]
    adaptive_sigma = 3.0 + 61.0 * pixel_error

    mask = np.random.random(population.shape) < adaptive_rate
    # 用每像素 RGB 平均误差作为比较基准
    n_candidates = 3
    best_mutated = population.copy()
    best_dist = np.mean(abs_diff, axis=-1)  # (pop, H, W) 每像素平均误差
    best_dist = np.where(mask[..., 0], best_dist, np.inf)  # 不变异的像素标记为无穷大

    for _ in range(n_candidates):
        delta = (np.random.normal(0, 1, population.shape).astype(np.float32) * adaptive_sigma).astype(np.int16)
        candidate = np.clip(population.astype(np.int16) + delta * mask, 0, 255).astype(np.uint8)
        cand_diff = np.abs(candidate.astype(np.float32) - target.astype(np.float32))
        cand_dist = np.mean(cand_diff, axis=-1)  # (pop, H, W)

        better = cand_dist < best_dist
        better3 = np.stack([better] * 3, axis=-1)
        best_mutated = np.where(better3, candidate, best_mutated)
        best_dist = np.where(better, cand_dist, best_dist)

    return best_mutated


def run_one_generation(population: np.ndarray, target: np.ndarray,
                       params: GAParams) -> tuple[np.ndarray, np.ndarray, float, float, float]:
    """返回 (新种群, 适应度数组, 最佳MSE, 平均MSE, 最佳相似度%)"""
    fitness = calc_fitness(population, target)
    best_idx = np.argmax(fitness)
    best_mse = float(-fitness[best_idx])
    avg_mse = float(-np.mean(fitness))
    best_similarity = mse_to_similarity(best_mse)

    elite_count = max(1, int(params.pop_size * params.elite_ratio))
    elite_indices = np.argsort(fitness)[-elite_count:]
    elites = population[elite_indices].copy()

    selected_idx = tournament_select(population, fitness, params.tournament_size)
    selected = population[selected_idx]
    offspring = uniform_crossover(selected)

    # 自适应变异：子代根据与目标的差异决定变异强度
    offspring = mutate_adaptive(offspring, target, params.mutation_rate)

    # 精英不参与变异，直接替换
    offspring[:elite_count] = elites

    return offspring, fitness, best_mse, avg_mse, best_similarity

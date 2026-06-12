"""
遗传算法引擎，把随机像素画逐步逼近目标图片。
每张像素画是一个个体，基因是 H×W×3 个 0-255 的整数。
每代做：算适应度 → 锦标赛选爹妈 → 交叉生娃 → 变异 → 精英替换。
"""
import numpy as np
from dataclasses import dataclass


@dataclass
class GAParams:
    pop_size: int = 100
    mutation_rate: float = 0.05
    elite_ratio: float = 0.15
    max_generations: int = 5000
    tournament_size: int = 5


def create_random_population(pop_size: int, height: int, width: int) -> np.ndarray:
    """生成 pop_size 张完全随机的像素画，RGB 各自 0-255 随机"""
    return np.random.randint(0, 256, (pop_size, height, width, 3), dtype=np.uint8)


def calc_fitness(population: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    用负 MSE 作为适应度，越大越好，0 是满分。
    不用 1/(1+MSE) 是因为随机种群 MSE 都是两三万，取倒数后全挤在 0.00003，
    锦标赛根本分不出谁好谁坏。
    """
    diff = population.astype(np.float32) - target.astype(np.float32)
    mse = np.mean(diff ** 2, axis=(1, 2, 3))
    return -mse


def mse_to_similarity(mse: float) -> float:
    """
    MSE 转成前端显示的相似度百分比。
    两张完全随机的图期望 sqrt(MSE) 约等于 104，以此为 0% 基准线，
    完美匹配 sqrt(MSE) = 0 对应 100%。
    之前用 255 做分母，随机图也有 60%，看起来太假。
    """
    RANDOM_BASELINE = 104.0
    raw = max(0.0, 1.0 - np.sqrt(max(0.0, mse)) / RANDOM_BASELINE)
    return raw * 100.0


def tournament_select(population: np.ndarray, fitness: np.ndarray,
                      tournament_size: int = 5) -> np.ndarray:
    """
    锦标赛选择：每次随机抽 tournament_size 个，适应度最高的获得繁殖资格。
    重复 pop_size 次凑满交配池。比轮盘赌好的地方是不会被一两个超强个体
    霸占整个交配池，能保持多样性。
    """
    pop_size = len(population)
    candidates = np.random.randint(0, pop_size, size=(pop_size, tournament_size))
    best_in_tournament = np.argmax(fitness[candidates], axis=1)
    return candidates[np.arange(pop_size), best_in_tournament]


def uniform_crossover(parents: np.ndarray) -> np.ndarray:
    """
    均匀交叉：相邻两个父代配对，每个像素抛硬币决定从父A还是父B拿。
    同一个像素的 RGB 三个通道要么全来自父A要么全来自父B，
    而不是每个通道独立随机。否则会产生花屏一样的噪点——颜色被拆散了。
    """
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
    自适应变异，跟普通固定概率变异不一样的地方：
    1. 离目标近的像素变异概率低（微调），远的概率高（大搜）
    2. 误差小于 3 的像素直接冻结，不再变异
    3. 每个像素生成 3 个候选值，只接受比原来更接近目标的那个

    效果是前期全面搜索，后期大量像素锁死，计算力自动集中在还没调好的区域。
    """
    diff = population.astype(np.float32) - target.astype(np.float32)
    abs_diff = np.abs(diff)
    pixel_error = np.mean(abs_diff, axis=-1, keepdims=True) / 255.0

    adaptive_rate = base_rate * 2.0 * pixel_error
    adaptive_rate[pixel_error < (3.0 / 255.0)] = 0.0

    adaptive_sigma = 3.0 + 61.0 * pixel_error

    mask = np.random.random(population.shape) < adaptive_rate

    n_candidates = 3
    best_mutated = population.copy()
    best_dist = np.mean(abs_diff, axis=-1)
    best_dist = np.where(mask[..., 0], best_dist, np.inf)

    for _ in range(n_candidates):
        delta = (np.random.normal(0, 1, population.shape).astype(np.float32)
                 * adaptive_sigma).astype(np.int16)
        candidate = np.clip(population.astype(np.int16) + delta * mask,
                            0, 255).astype(np.uint8)

        cand_diff = np.abs(candidate.astype(np.float32) - target.astype(np.float32))
        cand_dist = np.mean(cand_diff, axis=-1)

        better = cand_dist < best_dist
        better3 = np.stack([better] * 3, axis=-1)
        best_mutated = np.where(better3, candidate, best_mutated)
        best_dist = np.where(better, cand_dist, best_dist)

    return best_mutated


def run_one_generation(population: np.ndarray, target: np.ndarray,
                       params: GAParams):
    """执行一代，返回新种群、适应度、最佳/平均 MSE、最佳相似度"""
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
    offspring = mutate_adaptive(offspring, target, params.mutation_rate)

    offspring[:elite_count] = elites

    return offspring, fitness, best_mse, avg_mse, best_similarity

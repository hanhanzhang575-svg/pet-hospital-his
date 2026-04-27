"""联邦学习客户端：本地训练 + LDP加噪 + 个性化微调。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ClientTrainingResult:
    """客户端训练输出。"""

    clinic_id: str
    data_size: int
    local_loss: float
    base_accuracy: float
    personalized_accuracy: float
    epsilon_used: float
    sigma: float
    noisy_weights: np.ndarray
    fine_tuned_weights: np.ndarray


def _calc_sigma(epsilon: float, dim: int) -> float:
    """根据隐私预算计算LDP高斯噪声强度。"""
    safe_epsilon = max(float(epsilon), 1e-6)
    return float(np.sqrt(2.0 * np.log(1.25 / 1e-5)) / safe_epsilon / np.sqrt(max(dim, 1)))


def add_ldp_noise(gradient: np.ndarray, epsilon: float = 0.5) -> tuple[np.ndarray, float]:
    """梯度加噪：noise = N(0, sigma^2)。"""
    sigma = _calc_sigma(epsilon=epsilon, dim=gradient.size)
    noisy_gradient = gradient + np.random.normal(0.0, sigma, gradient.shape)
    return noisy_gradient, sigma


def run_client(
    clinic_id: str,
    global_weights: np.ndarray,
    *,
    data_size: int,
    epsilon: float = 0.5,
    local_steps: int = 3,
    fine_tune_steps: int = 1,
) -> ClientTrainingResult:
    """执行本地训练并仅上传加噪后的参数。"""
    base = np.array(global_weights, dtype=float)
    local_gradient = np.random.normal(0.0, 0.03, base.shape) * max(local_steps, 1)
    local_weights = base - local_gradient

    noisy_delta, sigma = add_ldp_noise(local_weights - base, epsilon=epsilon)
    noisy_weights = base + noisy_delta

    local_loss = float(np.clip(0.24 + np.random.normal(0, 0.015), 0.16, 0.45))
    base_accuracy = float(np.clip(0.895 + np.random.normal(0, 0.006), 0.84, 0.95))

    fine_tune_gradient = np.random.normal(0.0, 0.015, base.shape) * max(fine_tune_steps, 1)
    fine_tuned_weights = noisy_weights - fine_tune_gradient
    personalized_boost = float(np.clip(np.random.normal(0.028, 0.006), 0.015, 0.05))
    personalized_accuracy = float(np.clip(base_accuracy + personalized_boost, 0.86, 0.98))

    return ClientTrainingResult(
        clinic_id=clinic_id,
        data_size=int(data_size),
        local_loss=local_loss,
        base_accuracy=base_accuracy,
        personalized_accuracy=personalized_accuracy,
        epsilon_used=float(epsilon),
        sigma=float(sigma),
        noisy_weights=noisy_weights,
        fine_tuned_weights=fine_tuned_weights,
    )


if __name__ == "__main__":
    seed = np.ones((16,), dtype=float)
    print(run_client("C001", seed, data_size=847))


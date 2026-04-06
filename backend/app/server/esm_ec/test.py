import os
import warnings
import pickle
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
MODEL_PATH = CURRENT_DIR / "models" / "only_esm.h5"

from typing import Optional

import numpy as np
import tensorflow as tf

from .model import OPUSGO


warnings.filterwarnings("ignore")
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

_MODEL = None


def load_esm_ec_model(run_idx: Optional[int] = None):
    """
    懒加载模型，避免每次调用都重新初始化和加载权重。
    """
    global _MODEL

    if run_idx is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(run_idx % 4)

    if _MODEL is None:
        gpus = tf.config.experimental.list_physical_devices("GPU")
        for gpu in gpus:
            try:
                tf.config.experimental.set_memory_growth(gpu, True)
            except Exception:
                pass

        d_out = 5106

        model = OPUSGO(
            d_model=1280,
            d_ffn=1280 * 2,
            d_out=d_out
        )

        batch_size = 1
        model(
            inputs=np.zeros((batch_size, 1280), dtype=np.float32),
            training=False
        )

        print("ESM-EC model variables:", len(model.trainable_variables))
        model.load_model(name=str(MODEL_PATH))

        _MODEL = model

    return _MODEL


def run_esm_ec_from_feature(
    esm_feature_path: str,
    output_dir: str,
    run_idx: Optional[int] = None,
    output_stem: Optional[str] = None,
) -> dict:
    """
    读取 mkesm 生成的 .esm.npz 特征文件，运行 esm_ec 模型，
    并将结果保存为 pkl，同时返回结果字典。

    参数：
    - esm_feature_path: mkesm 生成的 .esm.npz 文件路径
    - output_dir: 输出目录
    - run_idx: 可选 GPU index
    - output_stem: 输出文件名主干，不传则使用特征文件 stem

    返回：
    - dict，包括 name, prob_esm, output_path
    """
    esm_feature_path = Path(esm_feature_path)
    if not esm_feature_path.exists():
        raise FileNotFoundError(f"ESM feature file not found: {esm_feature_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    name = output_stem or esm_feature_path.stem.replace(".esm", "")
    output_path = output_dir / f"{name}_esm.pkl"

    model = load_esm_ec_model(run_idx=run_idx)

    esm_feat = np.load(esm_feature_path)["l"]
    esm_feat = np.mean(esm_feat, axis=0)
    esm_feat = np.expand_dims(esm_feat, axis=0)

    assert esm_feat.shape == (1, 1280), (
        f"Unexpected esm_feat shape: {esm_feat.shape}"
    )

    out = model(esm_feat, training=False)

    y_pred = out[0]
    assert y_pred.shape == (5106,)

    results = {
        "name": name,
        "prob_esm": y_pred.astype(np.float16),
    }
    with open(output_path, "wb") as file:
        pickle.dump(results, file)

    return {
        "name": name,
        "prob_esm": results["prob_esm"],
        "output_path": str(output_path),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python test.py <run_idx> <esm_feature_path> <output_dir> [output_stem]")
        sys.exit(1)

    run_idx = int(sys.argv[1])
    esm_feature_path = sys.argv[2]
    output_dir = sys.argv[3]
    output_stem = sys.argv[4] if len(sys.argv) > 4 else None

    result = run_esm_ec_from_feature(
        esm_feature_path=esm_feature_path,
        output_dir=output_dir,
        run_idx=run_idx,
        output_stem=output_stem,
    )

    print(result["output_path"])
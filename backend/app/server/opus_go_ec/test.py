import os
import warnings
import pickle
from pathlib import Path
CURRENT_DIR = Path(__file__).resolve().parent
MODEL_PATH = CURRENT_DIR / "models" / "opus_go.h5"
from typing import Optional

import numpy as np
import tensorflow as tf

from .model import OPUSGO

warnings.filterwarnings("ignore")
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

_MODEL = None


def load_opus_go_model(run_idx: Optional[int] = None):
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
            inputs=np.zeros((batch_size, 1, 1280), dtype=np.float32),
            training=False
        )

        print("OPUS-ResInsight model variables:", len(model.trainable_variables))
        model.load_model(name=str(MODEL_PATH))

        _MODEL = model

    return _MODEL


def run_opus_go_from_feature(
    esm_feature_path: str,
    output_dir: str,
    run_idx: Optional[int] = None,
    output_stem: Optional[str] = None,
) -> dict:
    esm_feature_path = Path(esm_feature_path)
    if not esm_feature_path.exists():
        raise FileNotFoundError(f"ESM feature file not found: {esm_feature_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    name = output_stem or esm_feature_path.stem.replace(".esm", "")
    output_path = output_dir / f"{name}_opus_go.pkl"

    model = load_opus_go_model(run_idx=run_idx)

    esm_feat = np.load(esm_feature_path)["l"]
    L = esm_feat.shape[0]
    esm_feat = np.expand_dims(esm_feat, axis=0)

    assert esm_feat.shape == (1, L, 1280), (
        f"Unexpected esm_feat shape: {esm_feat.shape}"
    )

    out = model(esm_feat, training=False)
    assert out.shape == (1, L, 5106)

    out2 = np.max(out, 1)

    y_pred = out[0]
    y_pred2 = out2[0]

    results = {
        "name": name,
        "prob_opus_go": y_pred2.astype(np.float16),
        "prob_per_res": y_pred.astype(np.float16),
    }

    with open(output_path, "wb") as file:
        pickle.dump(results, file)

    return {
        "name": name,
        "prob_opus_go": results["prob_opus_go"],
        "prob_per_res": results["prob_per_res"],
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

    result = run_opus_go_from_feature(
        esm_feature_path=esm_feature_path,
        output_dir=output_dir,
        run_idx=run_idx,
        output_stem=output_stem,
    )

    print(result["output_path"])
import os
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import esm

_MODEL = None
_ALPHABET = None
_BATCH_CONVERTER = None


def load_esm_model(device: str = "cpu"):
    """
    懒加载 ESM 模型，避免每次调用都重新加载。
    """
    global _MODEL, _ALPHABET, _BATCH_CONVERTER

    if _MODEL is None:
        model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
        model = model.to(device)
        model.eval()

        _MODEL = model
        _ALPHABET = alphabet
        _BATCH_CONVERTER = alphabet.get_batch_converter()

    return _MODEL, _ALPHABET, _BATCH_CONVERTER


def generate_esm_feature(
        seq: str,
        output_dir: str,
        device_id: Optional[int] = None,
        file_stem: Optional[str] = None,
        device: str = "cpu",
) -> str:
    """
    根据输入序列生成 ESM feature，并保存到 output_dir。

    参数：
    - seq: 蛋白质序列
    - output_dir: 输出目录
    - device_id: 可选，用于设置 CUDA_VISIBLE_DEVICES
    - file_stem: 输出文件名主干，不传则自动生成 uuid
    - device: 'cpu' 或 'cuda'

    返回：
    - 保存后的 .esm.npz 文件路径字符串
    """
    if not seq or not seq.strip():
        raise ValueError("seq is empty")

    seq = seq.strip()

    if device_id is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(device_id % 4)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    name = file_stem or str(uuid.uuid4())

    model, alphabet, batch_converter = load_esm_model(device=device)

    data = [(name, seq)]
    batch_labels, batch_strs, batch_tokens = batch_converter(data)

    batch_tokens = batch_tokens.to(device)

    with torch.no_grad():
        results = model(batch_tokens, repr_layers=[33], return_contacts=False)

    token_representations = results["representations"][33][0]
    token_representations = token_representations[1:-1]  # 去掉 BOS / EOS
    token_representations = token_representations.to("cpu").numpy().astype(np.float16)

    assert token_representations.shape == (len(seq), 1280), (
        f"Feature shape mismatch: got {token_representations.shape}, "
        f"expected ({len(seq)}, 1280)"
    )

    save_path = output_path / f"{name}.esm.npz"
    np.savez_compressed(save_path, l=token_representations)

    return str(save_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python mkesm.py <device_id> <sequence> <output_dir> [file_stem]")
        sys.exit(1)

    device_id = int(sys.argv[1])
    seq = sys.argv[2]
    output_dir = sys.argv[3]
    file_stem = sys.argv[4] if len(sys.argv) > 4 else None

    save_path = generate_esm_feature(
        seq=seq,
        output_dir=output_dir,
        device_id=device_id,
        file_stem=file_stem,
        device="cpu",  # 你后面如果确定能用 GPU，可改成 "cuda"
    )

    print(save_path)
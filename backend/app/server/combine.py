import pickle
from pathlib import Path
import numpy as np


def combine_prediction_results(
    name: str,
    seq: str,
    output_dir: str,
    ec_list_path: str,
    esm_threshold: float = 0.1,
    opus_threshold: float = 0.1,
    residue_threshold: float = 0.5,
) -> dict:
    output_dir = Path(output_dir)
    ec_list_path = Path(ec_list_path)

    if not ec_list_path.exists():
        raise FileNotFoundError(f"ec_number_list.pkl not found: {ec_list_path}")

    with open(ec_list_path, "rb") as file:
        ec2id = pickle.load(file)

    id2ec = {ec2id[ec]: ec for ec in ec2id}
    assert len(ec2id) == len(id2ec) == 5106

    esm_pkl = output_dir / f"{name}_esm.pkl"
    opus_pkl = output_dir / f"{name}_opus_go.pkl"

    if not esm_pkl.exists():
        raise FileNotFoundError(f"Missing file: {esm_pkl}")
    if not opus_pkl.exists():
        raise FileNotFoundError(f"Missing file: {opus_pkl}")

    with open(opus_pkl, "rb") as file:
        results_opus_go = pickle.load(file)

    with open(esm_pkl, "rb") as file:
        results_esm = pickle.load(file)

    prob_esm = results_esm["prob_esm"]
    prob_opus_go = results_opus_go["prob_opus_go"]
    prob_per_res = results_opus_go["prob_per_res"]

    assert prob_esm.shape == prob_opus_go.shape == (5106,)
    assert prob_per_res.shape == (len(seq), 5106)

    # 1) predictions
    predictions = []

    for idx, prob in enumerate(prob_esm):
        if prob >= esm_threshold:
            predictions.append({
                "ecNumber": id2ec[idx],
                "probability": float(prob),
                "source": "ESM",
            })

    for idx, prob in enumerate(prob_opus_go):
        if prob >= opus_threshold:
            predictions.append({
                "ecNumber": id2ec[idx],
                "probability": float(prob),
                "source": "OPUS",
            })

    predictions.sort(key=lambda x: x["probability"], reverse=True)

    # 2) fragments
    fragments = []
    pred_ecs = []
    for idx, prob in enumerate(prob_opus_go):
        if prob >= residue_threshold:
            pred_ecs.append(id2ec[idx])

    for frag_id, ec_number in enumerate(pred_ecs, start=1):
        label_id = ec2id[ec_number]
        residues = []

        for pos, prob in enumerate(prob_per_res[:, label_id]):
            aa = seq[pos]
            residues.append({
                "aa": aa,
                "value": float(prob),
            })

        fragments.append({
            "id": frag_id,
            "label": ec_number,
            "residues": residues,
        })

    # 3) 先留空，后面由 align.py 填充
    external_sequences = []

    # 4) 恢复写出 name.pkl，供 align.py 使用
    combined_result_for_file = {
        "name": name,
        "seq": seq,
        "prob_esm": prob_esm,
        "prob_opus_go": prob_opus_go,
        "prob_per_res": prob_per_res,
    }

    combined_pkl = output_dir / f"{name}.pkl"
    with open(combined_pkl, "wb") as file:
        pickle.dump(combined_result_for_file, file)

    # 5) 返回给 FastAPI 的前端结构
    return {
        "predictions": predictions,
        "fragments": fragments,
        "externalSequenceGroups": [],
    }
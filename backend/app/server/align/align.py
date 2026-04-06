import gzip
import heapq
import pickle
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from itertools import islice

import numpy as np
from Bio import pairwise2
from tqdm import tqdm

match_score = 1
mismatch_score = 0
ignore_aa = ['X']

_WORKER_TARGET_SEQ = None


def custom_score(a, b):
    if a in ignore_aa or b in ignore_aa:
        return 0
    elif a == b:
        return match_score
    else:
        return mismatch_score


def _init_worker(target_seq: str):
    global _WORKER_TARGET_SEQ
    _WORKER_TARGET_SEQ = target_seq


def _calculate_similarity_batch(batch):
    target_seq = _WORKER_TARGET_SEQ
    if target_seq is None:
        raise RuntimeError("Worker target sequence is not initialized.")

    target_len_no_x = count_non_x(target_seq)
    out = []

    for j, seq_j in batch:
        alignments = pairwise2.align.globalxx(
            target_seq,
            seq_j,
            match_fn=custom_score,
            one_alignment_only=True
        )

        if alignments:
            score = alignments[0].score
            max_len = max(target_len_no_x, count_non_x(seq_j)) + 1e-6
            normalized_score = score / max_len
        else:
            normalized_score = 0.0

        out.append((j, normalized_score))

    return out


def _chunked(iterable, chunk_size):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, chunk_size))
        if not chunk:
            break
        yield chunk


def decompress(prob_compressed):
    prob_restore = prob_compressed.astype(np.float32) / 100.0
    assert np.max(prob_restore) <= 1
    assert np.min(prob_restore) >= 0
    return prob_restore


def _open_pickle_maybe_gzip(path: Path):
    try:
        with gzip.open(path, "rb") as f:
            return pickle.load(f)
    except OSError:
        with open(path, "rb") as f:
            return pickle.load(f)


def _build_masked_sequence(seq: str, probs, threshold: float) -> str:
    return "".join(
        aa if prob >= threshold else "X"
        for aa, prob in zip(seq, probs)
    )


def count_non_x(seq: str) -> int:
    return sum(1 for ch in seq if ch != "X")


def rough_similarity_score(seq_a: str, seq_b: str) -> float:
    """
    粗筛分数：只看同位置、且都不是 X 的匹配情况。
    非常便宜，用来筛掉明显不相似的候选。
    """
    valid = 0
    matched = 0

    # 只比较重叠部分
    n = min(len(seq_a), len(seq_b))
    for i in range(n):
        a = seq_a[i]
        b = seq_b[i]
        if a == "X" or b == "X":
            continue
        valid += 1
        if a == b:
            matched += 1

    if valid == 0:
        return 0.0

    # 再乘一个覆盖因子，避免“只对上很少几个位点”分数虚高
    coverage = valid / (max(count_non_x(seq_a), count_non_x(seq_b)) + 1e-6)
    return (matched / valid) * coverage


def run_uniref50_alignment(
        name: str,
        output_dir: str,
        ec_list_path: str,
        data_dir: str,
        top_k: int = 50,
        threshold: float = 0.5,
        max_workers: int | None = None,
        show_progress: bool = False,
        batch_size: int = 64,
        min_valid_residues: int = 5,
        prefilter_multiplier: int = 6,
) -> list[dict]:
    """
    基于 combine.py 生成的 name.pkl,按 EC 分组在 UniRef50 子库中检索相似序列。

    优化点：
    1. masked 后非 X 位点少于 min_valid_residues 的序列直接丢弃
    2. 先用 rough_similarity_score 粗筛，再对 top 候选做 pairwise2 精排
    """
    output_dir = Path(output_dir)
    ec_list_path = Path(ec_list_path)
    data_dir = Path(data_dir)

    if not ec_list_path.exists():
        raise FileNotFoundError(f"ec_number_list.pkl not found: {ec_list_path}")

    target_pkl = output_dir / f"{name}.pkl"
    if not target_pkl.exists():
        raise FileNotFoundError(f"Combined result file not found: {target_pkl}")

    with open(ec_list_path, "rb") as file:
        ec2id = pickle.load(file)

    id2ec = {ec2id[ec]: ec for ec in ec2id}
    assert len(ec2id) == len(id2ec) == 5106

    with open(target_pkl, "rb") as file:
        results = pickle.load(file)

    assert results["name"] == name

    seq_target = results["seq"]
    prob_opus_go_target = results["prob_opus_go"]
    prob_esm_target = results["prob_esm"]
    prob_per_res_target = results["prob_per_res"]

    assert prob_opus_go_target.shape == prob_esm_target.shape == (5106,)
    assert prob_per_res_target.shape == (len(seq_target), 5106)

    pred_ecs = []
    for idx, prob in enumerate(prob_opus_go_target):
        if prob >= threshold:
            pred_ecs.append(id2ec[idx])

    groups = []
    global_rank_id = 1

    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    for ec_number in pred_ecs:
        label_id = ec2id[ec_number]

        # 1. 构造目标 masked 序列
        seq_target_x = _build_masked_sequence(
            seq_target,
            prob_per_res_target[:, label_id],
            threshold
        )
        assert len(seq_target) == len(seq_target_x)

        # 目标序列有效位点太少，直接跳过这个 EC
        if count_non_x(seq_target_x) < min_valid_residues:
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        # 2. 读取对应 EC 的 UniRef50 数据
        ec_file = data_dir / f"{ec_number}.pkl.gz"
        if not ec_file.exists():
            continue

        ec_data_uniref50 = _open_pickle_maybe_gzip(ec_file)
        ec_data_uniref50 = ec_data_uniref50["data"]

        protein_ids = [name]
        protein_sequences = [seq_target_x]
        protein_sequences_ori = [seq_target]
        protein_prob_opus_go = [float(prob_opus_go_target[label_id])]
        protein_prob_esm = [float(prob_esm_target[label_id])]

        # 3. 从该 EC 的 UniRef50 数据中过滤候选
        for item in ec_data_uniref50:
            item_name = item["name"]
            seq = item["seq"]

            go_prob_arr = decompress(item["go_prob"])
            esm_prob_arr = decompress(item["esm_prob"])

            prob_opus_go = float(go_prob_arr[label_id])
            prob_esm = float(esm_prob_arr[label_id])

            if prob_opus_go > threshold and prob_esm > threshold:
                prob_per_res = decompress(item["prob_per_res"])
                assert prob_per_res.shape == (len(seq),)

                new_seq = _build_masked_sequence(seq, prob_per_res, threshold)
                assert len(new_seq) == len(seq)

                # 非 X 少于 5，直接扔掉
                if count_non_x(new_seq) < min_valid_residues:
                    continue

                protein_ids.append(item_name)
                protein_sequences_ori.append(seq)
                protein_prob_opus_go.append(prob_opus_go)
                protein_prob_esm.append(prob_esm)
                protein_sequences.append(new_seq)

        target_idx = 0
        target_seq = protein_sequences[target_idx]

        # 没有候选
        if len(protein_sequences) <= 1:
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        # 4. 先粗筛
        rough_scores = []
        for j in range(1, len(protein_sequences)):
            rs = rough_similarity_score(target_seq, protein_sequences[j])
            rough_scores.append((j, rs))

        # 粗筛后保留的数量：
        # 至少 top_k，默认放大 prefilter_multiplier 倍
        prefilter_k = max(top_k, top_k * prefilter_multiplier)
        pre_candidates = heapq.nlargest(prefilter_k, rough_scores, key=lambda x: x[1])

        # 如果粗筛后没有候选
        if not pre_candidates:
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        candidate_pairs = [(j, protein_sequences[j]) for j, _ in pre_candidates]

        # 5. 再精排
        results_similarity = []

        if len(candidate_pairs) < max(batch_size, 16):
            target_len_no_x = count_non_x(target_seq)
            iterator = candidate_pairs
            if show_progress:
                iterator = tqdm(iterator, total=len(candidate_pairs), desc=f"Align {ec_number}")

            for j, seq_j in iterator:
                alignments = pairwise2.align.globalxx(
                    target_seq,
                    seq_j,
                    match_fn=custom_score,
                    one_alignment_only=True
                )

                if alignments:
                    score = alignments[0].score
                    max_len = max(target_len_no_x, count_non_x(seq_j)) + 1e-6
                    normalized_score = score / max_len
                else:
                    normalized_score = 0.0

                results_similarity.append((j, normalized_score))
        else:
            batches = list(_chunked(candidate_pairs, batch_size))

            with ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=_init_worker,
                initargs=(target_seq,)
            ) as executor:
                mapped = executor.map(_calculate_similarity_batch, batches)

                if show_progress:
                    mapped = tqdm(mapped, total=len(batches), desc=f"Align {ec_number}")

                for batch_result in mapped:
                    results_similarity.extend(batch_result)

        top_results = heapq.nlargest(top_k, results_similarity, key=lambda x: x[1])

        group_items = []
        for rank, (idx, score) in enumerate(top_results, start=1):
            group_items.append({
                "id": global_rank_id,
                "source": protein_ids[idx],
                "ecNumber": ec_number,
                "rank": rank,
                "similarity": float(score),
                "sequence": protein_sequences[idx].replace("X", "-"),
                "originalSequence": protein_sequences_ori[idx],
                "probabilityOpus": float(protein_prob_opus_go[idx]),
                "probabilityEsm": float(protein_prob_esm[idx]),
            })
            global_rank_id += 1

        groups.append({
            "ecNumber": ec_number,
            "items": group_items,
        })

    return groups
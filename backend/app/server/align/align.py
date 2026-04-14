import gzip
import heapq
import pickle
import shutil
import subprocess
import tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from itertools import islice
from typing import Optional

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


def normalize_sequence_key(seq: str) -> str:
    return seq.strip().upper()


def rough_similarity_score(seq_a: str, seq_b: str) -> float:
    """
    回退/补充用粗筛分数：只看同位置、且都不是 X 的匹配情况。
    很便宜，用于补足 MMseqs2 召回不足的候选。
    """
    valid = 0
    matched = 0

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

    coverage = valid / (max(count_non_x(seq_a), count_non_x(seq_b)) + 1e-6)
    return (matched / valid) * coverage


def sanitize_mmseqs_id(s: str) -> str:
    return (
        s.replace(" ", "_")
        .replace("\t", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("|", "_")
        .replace(";", "_")
    )


def ensure_ec_fasta_from_pickle(ec_number: str, data_dir: Path, fasta_dir: Path) -> Path:
    """
    从 align/data/<ec>.pkl.gz 生成 MMseqs2 可搜索的 FASTA。
    首次生成，之后复用。
    """
    fasta_dir.mkdir(parents=True, exist_ok=True)
    fasta_path = fasta_dir / f"{ec_number}.fasta"
    if fasta_path.exists():
        return fasta_path

    ec_file = data_dir / f"{ec_number}.pkl.gz"
    if not ec_file.exists():
        raise FileNotFoundError(f"EC pickle not found: {ec_file}")

    ec_data_uniref50 = _open_pickle_maybe_gzip(ec_file)["data"]

    with open(fasta_path, "w") as f:
        for item in ec_data_uniref50:
            item_name = sanitize_mmseqs_id(item["name"])
            seq = item["seq"].strip().upper()
            if not seq:
                continue
            f.write(f">{item_name}\n{seq}\n")

    return fasta_path


def ensure_ec_mmseqs_db(ec_number: str, data_dir: Path, mmseqs_fasta_dir: Path, mmseqs_db_dir: Path) -> Path:
    """
    为某个 EC 确保 MMseqs2 target DB 已存在。
    """
    mmseqs_db_dir.mkdir(parents=True, exist_ok=True)
    db_path = mmseqs_db_dir / ec_number

    if db_path.exists():
        return db_path

    fasta_path = ensure_ec_fasta_from_pickle(ec_number, data_dir, mmseqs_fasta_dir)
    if not fasta_path.exists() or fasta_path.stat().st_size == 0:
        raise RuntimeError(f"FASTA is missing or empty: {fasta_path}")

    subprocess.run(
        ["mmseqs", "createdb", str(fasta_path), str(db_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return db_path


def mmseqs_prefilter_candidates(
    query_name: str,
    query_seq: str,
    ec_number: str,
    data_dir: Path,
    mmseqs_fasta_dir: Path,
    mmseqs_db_dir: Path,
    max_seqs: int = 150,
    sensitivity: float = 3.0,
    threads: int = 4,
) -> Optional[list[str]]:
    """
    用 MMseqs2 对某个 EC 子库做候选召回。
    返回 target 名称列表（按 MMseqs2 排序）。
    """
    if not query_seq or not query_seq.strip():
        return None

    try:
        target_db = ensure_ec_mmseqs_db(
            ec_number=ec_number,
            data_dir=data_dir,
            mmseqs_fasta_dir=mmseqs_fasta_dir,
            mmseqs_db_dir=mmseqs_db_dir,
        )
    except Exception:
        return None

    tmp_root = Path(tempfile.mkdtemp(prefix=f"mmseqs_{ec_number}_"))
    try:
        query_fasta = tmp_root / "query.fasta"
        query_db = tmp_root / "queryDB"
        result_db = tmp_root / "resultDB"
        m8_file = tmp_root / "result.m8"
        work_tmp = tmp_root / "tmp"

        with open(query_fasta, "w") as f:
            f.write(f">{sanitize_mmseqs_id(query_name)}\n{query_seq.strip().upper()}\n")

        subprocess.run(
            ["mmseqs", "createdb", str(query_fasta), str(query_db)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                "mmseqs", "search",
                str(query_db),
                str(target_db),
                str(result_db),
                str(work_tmp),
                "--threads", str(threads),
                "-s", str(sensitivity),
                "--max-seqs", str(max_seqs),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        subprocess.run(
            [
                "mmseqs", "convertalis",
                str(query_db),
                str(target_db),
                str(result_db),
                str(m8_file),
                "--format-output", "query,target,bits"
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        names = []
        if m8_file.exists():
            with open(m8_file, "r") as f:
                for line in f:
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) >= 2:
                        names.append(parts[1])

        return names if names else None
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


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
        use_mmseqs_prefilter: bool = True,
        mmseqs_max_seqs: int = 150,
        mmseqs_sensitivity: float = 3.0,
        mmseqs_threads: int = 4,
        mmseqs_fasta_dir: str | None = None,
        mmseqs_db_dir: str | None = None,
) -> list[dict]:
    """
    基于 combine.py 生成的 name.pkl，按 EC 分组在 UniRef50 子库中检索相似序列。

    单路 MMseqs2 版本：
    1. 过滤 + 去重候选
    2. MMseqs2 用原始 seq_target 先召回一批候选
    3. 如果 MMseqs2 候选不足，用 rough_similarity_score 补足到固定候选数
    4. 最终仍然用 masked 序列 + pairwise2 进行精排
    """
    output_dir = Path(output_dir)
    ec_list_path = Path(ec_list_path)
    data_dir = Path(data_dir)

    if mmseqs_fasta_dir is None:
        mmseqs_fasta_dir = str(data_dir.parent / "mmseqs_fasta")
    if mmseqs_db_dir is None:
        mmseqs_db_dir = str(data_dir.parent / "mmseqs_db")

    mmseqs_fasta_dir = Path(mmseqs_fasta_dir)
    mmseqs_db_dir = Path(mmseqs_db_dir)

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

    seq_target_norm = normalize_sequence_key(seq_target)

    for ec_number in pred_ecs:
        label_id = ec2id[ec_number]

        seq_target_x = _build_masked_sequence(
            seq_target,
            prob_per_res_target[:, label_id],
            threshold
        )
        assert len(seq_target) == len(seq_target_x)

        seq_target_x_norm = normalize_sequence_key(seq_target_x)

        if count_non_x(seq_target_x) < min_valid_residues:
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        ec_file = data_dir / f"{ec_number}.pkl.gz"
        if not ec_file.exists():
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        ec_data_uniref50 = _open_pickle_maybe_gzip(ec_file)
        ec_data_uniref50 = ec_data_uniref50["data"]

        protein_ids = [name]
        protein_sequences = [seq_target_x]
        protein_sequences_ori = [seq_target]
        protein_prob_opus_go = [float(prob_opus_go_target[label_id])]
        protein_prob_esm = [float(prob_esm_target[label_id])]

        seen_pairs = {
            (seq_target_norm, seq_target_x_norm)
        }

        for item in ec_data_uniref50:
            item_name = item["name"]
            seq = item["seq"]

            seq_norm = normalize_sequence_key(seq)

            go_prob_arr = decompress(item["go_prob"])
            esm_prob_arr = decompress(item["esm_prob"])

            prob_opus_go = float(go_prob_arr[label_id])
            prob_esm = float(esm_prob_arr[label_id])

            if prob_opus_go > threshold and prob_esm > threshold:
                prob_per_res = decompress(item["prob_per_res"])
                assert prob_per_res.shape == (len(seq),)

                new_seq = _build_masked_sequence(seq, prob_per_res, threshold)
                assert len(new_seq) == len(seq)

                new_seq_norm = normalize_sequence_key(new_seq)

                if count_non_x(new_seq) < min_valid_residues:
                    continue

                if item_name == name:
                    continue
                if seq_norm == seq_target_norm:
                    continue
                if new_seq_norm == seq_target_x_norm:
                    continue

                pair_key = (seq_norm, new_seq_norm)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                protein_ids.append(item_name)
                protein_sequences_ori.append(seq)
                protein_prob_opus_go.append(prob_opus_go)
                protein_prob_esm.append(prob_esm)
                protein_sequences.append(new_seq)

        target_idx = 0
        target_seq = protein_sequences[target_idx]

        if len(protein_sequences) <= 1:
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        prefilter_k = max(top_k, top_k * prefilter_multiplier)
        candidate_indices = []

        # 1) 单路 MMseqs2 召回
        if use_mmseqs_prefilter:
            mmseqs_names = mmseqs_prefilter_candidates(
                query_name=name,
                query_seq=seq_target,
                ec_number=ec_number,
                data_dir=data_dir,
                mmseqs_fasta_dir=mmseqs_fasta_dir,
                mmseqs_db_dir=mmseqs_db_dir,
                max_seqs=mmseqs_max_seqs,
                sensitivity=mmseqs_sensitivity,
                threads=mmseqs_threads,
            )

            if mmseqs_names:
                name_to_indices = {}
                for j in range(1, len(protein_ids)):
                    key = sanitize_mmseqs_id(protein_ids[j])
                    name_to_indices.setdefault(key, []).append(j)

                for hit_name in mmseqs_names:
                    if hit_name in name_to_indices:
                        candidate_indices.extend(name_to_indices[hit_name])

                seen_idx = set()
                candidate_indices = [
                    j for j in candidate_indices
                    if not (j in seen_idx or seen_idx.add(j))
                ]

        # 2) 不足时 rough 补足
        if len(candidate_indices) < prefilter_k:
            rough_scores = []
            existing_idx = set(candidate_indices)

            for j in range(1, len(protein_sequences)):
                if j in existing_idx:
                    continue
                rs = rough_similarity_score(target_seq, protein_sequences[j])
                rough_scores.append((j, rs))

            need_more = prefilter_k - len(candidate_indices)
            if need_more > 0 and rough_scores:
                top_rough = heapq.nlargest(need_more, rough_scores, key=lambda x: x[1])
                candidate_indices.extend([j for j, _ in top_rough])

        if not candidate_indices:
            groups.append({
                "ecNumber": ec_number,
                "items": [],
            })
            continue

        candidate_pairs = [(j, protein_sequences[j]) for j in candidate_indices]

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
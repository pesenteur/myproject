from pathlib import Path
import uuid
import shutil
import time

from app.server.align.align import run_uniref50_alignment
from app.server.mkesm import generate_esm_feature
from app.server.esm_ec.test import run_esm_ec_from_feature
from app.server.opus_go_ec.test import run_opus_go_from_feature
from app.server.combine import combine_prediction_results

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = BASE_DIR / "server"
TMP_ROOT_DIR = SERVER_DIR / "tmp"


def remove_directory(path: Path):
    """
    删除整个目录及其内部所有文件。
    """
    if path.exists() and path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def run_all_predictors(sequence: str) -> dict:
    request_id = str(uuid.uuid4())

    # 每次请求单独一个临时目录
    request_tmp_dir = TMP_ROOT_DIR / request_id
    request_tmp_dir.mkdir(parents=True, exist_ok=True)

    timings = {}
    total_start = time.perf_counter()

    try:
        # 1. 生成 ESM 特征文件
        t0 = time.perf_counter()
        esm_feature_path = generate_esm_feature(
            seq=sequence,
            output_dir=str(request_tmp_dir),
            device_id=1,
            file_stem=request_id,
            device="cpu",
        )
        timings["generate_esm_feature"] = round(time.perf_counter() - t0, 4)

        # 2. 跑 esm_ec
        t0 = time.perf_counter()
        run_esm_ec_from_feature(
            esm_feature_path=esm_feature_path,
            output_dir=str(request_tmp_dir),
            run_idx=1,
            output_stem=request_id,
        )
        timings["run_esm_ec_from_feature"] = round(time.perf_counter() - t0, 4)

        # 3. 跑 opus_go_ec
        t0 = time.perf_counter()
        run_opus_go_from_feature(
            esm_feature_path=esm_feature_path,
            output_dir=str(request_tmp_dir),
            run_idx=1,
            output_stem=request_id,
        )
        timings["run_opus_go_from_feature"] = round(time.perf_counter() - t0, 4)

        # 4. 汇总结果
        t0 = time.perf_counter()
        result = combine_prediction_results(
            name=request_id,
            seq=sequence,
            output_dir=str(request_tmp_dir),
            ec_list_path=str(SERVER_DIR / "ec_number_list.pkl"),
        )
        timings["combine_prediction_results"] = round(time.perf_counter() - t0, 4)

        # 5. 跑 UniRef50 alignment
        t0 = time.perf_counter()
        external_sequence_groups = run_uniref50_alignment(
            name=request_id,
            output_dir=str(request_tmp_dir),
            ec_list_path=str(SERVER_DIR / "ec_number_list.pkl"),
            data_dir=str(SERVER_DIR / "align" / "data"),
            top_k=50,
            threshold=0.5,

            max_workers=4,
            show_progress=False,
            batch_size=64,

            min_valid_residues=5,
            prefilter_multiplier=6,

            use_mmseqs_prefilter=True,
            mmseqs_max_seqs=300,
            mmseqs_sensitivity=4.0,
            mmseqs_threads=4,
            mmseqs_fasta_dir=str(SERVER_DIR / "align" / "mmseqs_fasta"),
            mmseqs_db_dir=str(SERVER_DIR / "align" / "mmseqs_db"),
        )
        timings["run_uniref50_alignment"] = round(time.perf_counter() - t0, 4)

        result["externalSequenceGroups"] = external_sequence_groups

        # 总耗时
        timings["total"] = round(time.perf_counter() - total_start, 4)

        # 找出最耗时阶段
        stage_timings = {k: v for k, v in timings.items() if k != "total"}
        slowest_stage = max(stage_timings, key=stage_timings.get)

        result["timings"] = timings
        result["slowestStage"] = {
            "name": slowest_stage,
            "seconds": stage_timings[slowest_stage]
        }

        # 同时打印到控制台，方便看日志
        print(f"[Timing] request_id={request_id}")
        for k, v in timings.items():
            print(f"[Timing] {k}: {v:.4f}s")
        print(f"[Timing] slowestStage: {slowest_stage} ({stage_timings[slowest_stage]:.4f}s)")

        return result

    finally:
        # 无论成功还是失败，都清理这次请求自己的临时目录
        remove_directory(request_tmp_dir)
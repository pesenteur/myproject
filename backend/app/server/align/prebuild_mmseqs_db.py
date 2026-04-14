from pathlib import Path
import sys

# 让当前目录下的 align.py 可以被 import
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from align import ensure_ec_fasta_from_pickle, ensure_ec_mmseqs_db  # noqa: E402


def main():
    align_dir = Path(__file__).resolve().parent
    data_dir = align_dir / "data"
    fasta_dir = align_dir / "mmseqs_fasta"
    db_dir = align_dir / "mmseqs_db"

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    fasta_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)

    pkl_files = sorted(data_dir.glob("*.pkl.gz"))
    if not pkl_files:
        print(f"No EC pickle files found in: {data_dir}")
        return

    print(f"Found {len(pkl_files)} EC pickle files.")
    print(f"Data dir:   {data_dir}")
    print(f"FASTA dir:  {fasta_dir}")
    print(f"DB dir:     {db_dir}")
    print("")

    for p in pkl_files:
        ec_number = p.name[:-7]  # 兼容 .pkl.gz

        print(f"[START] {ec_number}")

        # 尝试生成 FASTA
        try:
            fasta_path = ensure_ec_fasta_from_pickle(
                ec_number=ec_number,
                data_dir=data_dir,
                fasta_dir=fasta_dir,
            )
        except Exception as e:
            print(f"  [SKIP] Cannot generate FASTA for {ec_number}: {e}")
            continue

        # FASTA 文件为空直接跳过
        if fasta_path.stat().st_size == 0:
            print(f"  [SKIP] FASTA file is empty for {ec_number}")
            continue

        # 尝试创建 MMseqs2 数据库
        try:
            db_path = ensure_ec_mmseqs_db(
                ec_number=ec_number,
                data_dir=data_dir,
                mmseqs_fasta_dir=fasta_dir,
                mmseqs_db_dir=db_dir,
            )
            print(f"  MMseqs DB ready: {db_path}")
        except Exception as e:
            print(f"  [SKIP] Cannot create MMseqs DB for {ec_number}: {e}")
            continue

        print(f"[DONE] {ec_number}")
        print("")

    print("All MMseqs2 FASTA files and databases are prepared.")


if __name__ == "__main__":
    main()
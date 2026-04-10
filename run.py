from pathlib import Path
from src.chunking import ChunkingStrategyComparator

def main():
    # 1. Chọn 2-3 file để test cho báo cáo (bạn có thể thay đổi đường dẫn ở đây)
    test_files = [
        "data/TRẦN ANH TÔNG.md",
        "data/TRẦN MINH TÔNG.md",
        "data/Trần Nghệ Tông.md"
    ]

    # Khởi tạo Comparator
    comparator = ChunkingStrategyComparator()
    chunk_size = 500  # Đặt chunk_size tùy ý để so sánh

    for file_path in test_files:
        path = Path(file_path)
        if not path.exists():
            print(f"Không tìm thấy file: {file_path}")
            continue

        # Đọc nội dung file
        text = path.read_text(encoding="utf-8")
        
        # 2. Chạy hàm compare
        results = comparator.compare(text, chunk_size=chunk_size)

        # 3. In kết quả ra màn hình thật đẹp để dễ copy vào báo cáo
        print(f"\n" + "="*50)
        print(f"TÀI LIỆU: {path.name} (Tổng: {len(text)} ký tự)")
        print("="*50)

        for strategy, stats in results.items():
            print(f"[*] Strategy: {strategy}")
            print(f"    - Số lượng chunk (Chunk Count) : {stats['count']}")
            print(f"    - Độ dài trung bình (Avg Length): {stats['avg_length']:.2f} ký tự")
            print("-" * 40)

if __name__ == "__main__":
    main()
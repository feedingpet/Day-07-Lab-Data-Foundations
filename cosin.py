import os
from dotenv import load_dotenv
from src.embeddings import LocalEmbedder, OpenAIEmbedder, _mock_embed, EMBEDDING_PROVIDER_ENV
from src.chunking import compute_similarity

def main():
    # Khởi tạo Embedder (giống trong main.py của bạn)
    load_dotenv()
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        embedder = LocalEmbedder()
    elif provider == "openai":
        embedder = OpenAIEmbedder()
    else:
        embedder = _mock_embed
        print("CẢNH BÁO: Đang dùng _mock_embed, điểm số sẽ không phản ánh đúng ngữ nghĩa thực tế. Hãy setup LOCAL hoặc OPENAI trong file .env")

    # 5 Cặp câu của bạn
    pairs = [
        ("Hoàng đế truyền lại ngai vàng cho con trai.", "Nhà vua nhường ngôi cho thái tử."),
        ("Trần Nhân Tông là vị vua anh minh.", "Hôm nay thời tiết Hà Nội rất đẹp."),
        ("Con cọp ăn thịt con bò.", "Con bò ăn thịt con cọp."),
        ("Trần Anh Tông lên ngôi năm 1293.", "Trần Minh Tông sinh năm 1300."),
        ("Trần Thái Tông viết Khóa Hư Lục.", "Theo lịch sử, Trần Thái Tông là người chắp bút Khóa Hư Lục.")
    ]

    print("=== KẾT QUẢ COSINE SIMILARITY ===\n")
    for i, (sent_a, sent_b) in enumerate(pairs, 1):
        emb_a = embedder(sent_a)
        emb_b = embedder(sent_b)
        score = compute_similarity(emb_a, emb_b)
        
        print(f"Cặp {i}:")
        print(f"  A: {sent_a}")
        print(f"  B: {sent_b}")
        print(f"  => Điểm thực tế (Actual Score): {score:.4f}\n")

if __name__ == "__main__":
    main()
# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Ngọc CƯờng]
**Nhóm:** [C401-E1]
**Ngày:** [10/4/2026]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:* High cosine similarity tức là 2 vector rất giống nhau về hướng

**Ví dụ HIGH similarity:**
- Sentence A: Tôi thích học trí tuệ nhân tạo
- Sentence B: Tôi yêu học AI
- Tại sao tương đồng:

**Ví dụ LOW similarity:**
- Sentence A: Tôi đi làm hôm nay
- Sentence B: Công thức để làm pizza gồm bột mì, cà chua, phô mai
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau, không liên quan về ngữ nghĩa

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:*
Cosine similarity đo sự giống nhau về hướng (ngữ nghĩa) và không bị ảnh hưởng bởi độ dài vector, trong khi Euclidean distance bị ảnh hưởng bởi độ lớn nên kém ổn định hơn cho embeddings.
### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
Stride = 500 - 50 = 450
Số chunks = ceil((10000 - 500) / 450) + 1
= ceil(9500 / 450) + 1
= ceil(21.11) + 1
= 22 + 1 = 23
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:*
Chunk count sẽ tăng vì stride giảm (500 - 100 = 400), tạo nhiều đoạn hơn; overlap lớn giúp giữ ngữ cảnh giữa các chunk tốt hơn, tránh mất thông tin ở ranh giới.
---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [ví dụ: Customer support FAQ, Vietnamese law, cooking recipes, ...]

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:*
Nhóm mình chọn domain là thơ của các vị vua thời Trần. Lý do chọn là điểm kiểm tra với tài liệu liên quan đến lịch sử, việc embedding sẽ là thử thách vì câu văn có cả từ thuần VIệt, Hán Việt có nhiều nghĩa trong ngữ cảnh và vị trí khác nhau
### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | TRẦN ANH TÔNG | data/docs/TRẦN ANH TÔNG.md | 892 | person, emperor, born:1276, died:1320, period:13th-14th |
| 2 | TRẦN MINH TÔNG | data/docs/TRẦN MINH TÔNG.md | 1,547 | person, emperor, born:1300, died:1357, period:14th |
| 3 | TRẦN NGHỆ TÔNG | data/docs/Trần Nghệ Tông.md | 1,203 | person, emperor, born:1336, died:1377, period:14th |
| 4 | TRẦN NGẠC | data/docs/TRẦN NGẠC.md | 654 | person, prince, died:1391, period:14th-15th |
| 5 | TRẦN NHAN TONG | data/docs/TRẦN NHAN TONG.md | 1,156 | person, emperor, born:1258, died:1308, period:13th-14th |
| 6 | TRẦN CẢNH | data/docs/TRẦN CẢNH.md | 745 | person, general, period:13th-14th |
| 7 | TRẦN HẠO | data/docs/TRẦN HẠO.md | 823 | person, prince, period:14th |
| 8 | TRẦN KÍNH | data/docs/TRẦN KÍNH.md | 679 | person, emperor, born:1336, died:1377, period:14th |
| 9 | TRẦN MẠNH | data/docs/TRẦN MẠNH.md | 1,421 | person, general, period:14th |
| 10 | NIÊN BIỂU KHÁI QUÁT | data/docs/NIÊN BIỂU KHÁI QUÁT CÁC SỰ KIỆN CÓ LIÊN QUAN TỚI VĂN HỌC.md | 2,156 | timeline, events, literature, history, period:13th-15th |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| person_type | string | "emperor" / "prince" / "general" | Cho phép filter bằng vai trò, ví dụ chỉ tìm emperors |
| period | string | "1300-1357" / "13th-14th century" | Hỗ trợ queries về thời kỳ lịch sử, ví dụ "emperors of 14th century" |
| language | string | "vi" / "en" | Phân tách tài liệu tiếng Việt vs tiếng Anh, cải thiện precision |
| source | string | "data/docs/..." | Tracking nguồn, hữu ích khi trích dẫn hoặc follow-up queries |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| TRẦN ANH TÔNG | FixedSizeChunker (`fixed_size`) | 47 | 498.60 | Thấp (Dễ cắt ngang câu/từ) |
| TRẦN ANH TÔNG | SentenceChunker (`by_sentences`) | 82 | 271.90 | Tốt (Bảo toàn trọn vẹn câu) |
| TRẦN ANH TÔNG | RecursiveChunker (`recursive`) | 54 | 414.96 | Rất tốt (Giữ nguyên đoạn/ý) |
| TRẦN MINH TÔNG | FixedSizeChunker (`fixed_size`) | 115 | 498.24 | Thấp (Dễ cắt ngang câu/từ) |
| TRẦN MINH TÔNG | SentenceChunker (`by_sentences`) | 223 | 244.15 | Tốt (Bảo toàn trọn vẹn câu) |
| TRẦN MINH TÔNG | RecursiveChunker (`recursive`) | 132 | 414.82 | Rất tốt (Giữ nguyên đoạn/ý) |
| Trần Nghệ Tông | FixedSizeChunker (`fixed_size`) | 20 | 481.80 | Thấp (Dễ cắt ngang câu/từ) |
| Trần Nghệ Tông | SentenceChunker (`by_sentences`) | 35 | 261.26 | Tốt (Bảo toàn trọn vẹn câu) |
| Trần Nghệ Tông | RecursiveChunker (`recursive`) | 20 | 460.90 | Rất tốt (Giữ nguyên đoạn/ý) |

### Strategy Của Tôi

**Loại:** [FixedSizeChunker / SentenceChunker / RecursiveChunker / custom strategy]: SentenceChunker

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*
SentenceChunker (chia theo câu) hoạt động bằng cách sử dụng biểu thức chính quy (regex) để nhận diện các dấu hiệu kết thúc câu như dấu chấm, dấu chấm than, dấu hỏi chấm đi kèm với khoảng trắng hoặc ký tự xuống dòng. Sau khi tách văn bản thành danh sách các câu đơn lẻ, chiến lược này sẽ nhóm một số lượng câu nhất định (ví dụ: tối đa 3 câu) lại với nhau để tạo thành một chunk. Cách tiếp cận này đảm bảo rằng không có câu nào bị cắt ngang giữa chừng, giữ cho cấu trúc ngữ pháp của từng phần luôn trọn vẹn.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*
Domain tài liệu lịch sử và thơ văn thời Trần thường có các câu mang ý nghĩa tương đối độc lập hoặc các đoạn mô tả sự kiện, nhân vật súc tích. SentenceChunker giúp bảo toàn trọn vẹn ý nghĩa của từng câu văn (có chứa từ Hán Việt hoặc cấu trúc ngữ pháp đặc thù), tránh việc cắt ngang cụm từ làm mất hoặc sai lệch ngữ nghĩa, từ đó cải thiện độ chính xác khi tìm kiếm (retrieval) thông tin chi tiết về các vị vua.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| TRẦN MINH TÔNG | RecursiveChunker (`recursive`) | 132 | 414.82 | Khá (Đôi khi gom quá nhiều câu không liên quan vào 1 chunk) |
| TRẦN MINH TÔNG | **SentenceChunker (`by_sentences`)** | 223 | 244.15 | Tốt (Lấy ra đúng ngữ cảnh của từng câu/sự kiện, Agent dễ trả lời chính xác hơn) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi |SentenceChunker | 0/10 | Không có| BỊ ảnh hưởng nhiều |
| Mạnh |PoemSectionChunker |3/10 |Hit đúng file nguồn cả 5 query; tách thơ/prose có chủ đích | Score rất thấp (0.01–0.32), filter làm hỏng retrieval; chunk thơ lấn át chunk tiểu sử|
| Hào |RecursiveChunker | 9/10|Score cao nhất (0.612–0.745), hit đúng chunk + đúng nội dung + LLM trả lời từ context thực |Phụ thuộc vào file đầy đủ (thiếu TRẦN NHÂN TÔNG.md ảnh hưởng) |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*
RecursiveChunker hợp nhất cho domain này. Bảo toàn được cấu trúc đoạn văn, giúp nhóm các sự kiện lịch sử trọn vẹn lại với nhau, cung cấp ngữ cảnh đầy đủ nhất cho LLM trả lời.
---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi sử dụng regex `re.split(r'(\.\s+|\!\s+|\?\s+|\.\n)', text)` để nhận diện chính xác ranh giới câu dựa vào dấu câu đi kèm khoảng trắng hoặc ký tự xuống dòng. Các edge case như khoảng trắng thừa hoặc câu rỗng được xử lý gọn gàng bằng hàm `.strip()`, sau đó thuật toán sẽ gom các câu lại không vượt quá `max_sentences_per_chunk` để đảm bảo không bị vụn vặt.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán hoạt động theo hướng đệ quy từ trên xuống (top-down), cố gắng cắt văn bản bằng các dấu phân cách lớn trước (như đoạn văn `\n\n`) và hạ dần xuống phân cách nhỏ hơn (như khoảng trắng ` `) nếu đoạn đó vẫn vượt quá `chunk_size`. Base case (điều kiện dừng) là khi độ dài chuỗi hiện tại $\le$ `chunk_size`; nếu hết dấu phân cách mà đoạn vẫn quá dài, thuật toán sẽ dùng fallback cắt cứng theo chỉ số ký tự (char index).

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Khi thêm tài liệu, tôi trích xuất `content`, dùng `embedding_fn` để chuyển thành vector và lưu dưới dạng dictionary (hỗ trợ cả ChromaDB lẫn In-Memory list). Khi tìm kiếm, tôi chuyển query thành vector và tính Cosine Similarity (thông qua hàm tích vô hướng `_dot`) giữa query và tất cả các chunk, sau đó sắp xếp giảm dần để lấy top-K đoạn tương đồng nhất.

**`search_with_filter` + `delete_document`** — approach:
> Tôi áp dụng chiến lược pre-filtering (lọc siêu dữ liệu trước), nghĩa là thu hẹp tập dữ liệu bằng metadata rồi mới tính toán similarity, giúp tăng tốc độ tìm kiếm đáng kể. Việc xóa document được thực hiện bằng cách quét qua danh sách và lọc bỏ hoàn toàn các chunk có chứa `doc_id` tương ứng trong phần metadata.

### KnowledgeBaseAgent

**`answer`** — approach:
> Tôi áp dụng mô hình RAG tiêu chuẩn: gọi hàm search từ `store` để lấy ra `top_k` chunk liên quan nhất đến câu hỏi. Các chunk này được nối lại với nhau bằng ký tự phân cách rõ ràng (`\n\n---\n\n`) để tạo thành khối Context, sau đó đưa vào cấu trúc prompt khép kín dạng: "Dựa vào ngữ cảnh dưới đây... Context: [nội dung] Question: [câu hỏi] Answer: " rồi mới gửi tới LLM.
### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 |Hoàng đế truyền lại ngai vàng cho con trai. | Nhà vua nhường ngôi cho thái tử.| high  |-0.1955 |Sai |
| 2 | Trần Nhân Tông là vị vua anh minh.| Hôm nay thời tiết Hà Nội rất đẹp.| low |-0.0555 |Đúng |
| 3 | Con cọp ăn thịt con bò.|Con bò ăn thịt con cọp. | low |0.0367 |Đúng |
| 4 |Trần Anh Tông lên ngôi năm 1293. | Trần Minh Tông sinh năm 1300.| low |0.1837 |Đúng |
| 5 | Trần Thái Tông viết Khóa Hư Lục.| Theo lịch sử, Trần Thái Tông là người chắp bút Khóa Hư Lục.| high / |0.1289 |Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*
Kết quả câu 5 bất ngờ nhất. DÙ chỉ alf thay đổi cách diễn đạt là Trần Thái Tông là người viết Khóa Hư Lục, nhưng kết quả embedding lại cho thấy điều ngược lại. các mô hình Embedding (đặc biệt là các model nhỏ) đôi khi vẫn bị phụ thuộc nặng vào "sự trùng lặp từ vựng" (Bag of Words) thay vì hiểu sâu sắc cấu trúc ngữ pháp và vai trò chủ/vị ngữ trong câu.
---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer (từ file thực tế) |
|---|-------|-------------------------------|
| 1 | Trần Anh Tông lên ngôi năm bao nhiêu và là con của ai? | Trần Anh Tông (tên thật Trần Thuyên) là con trưởng của Trần Nhân Tông, lên ngôi năm Quý Tị (1293) sau khi vua cha nhường ngôi. |
| 2 | Trần Nhân Tông sáng lập thiền phái nào và ở đâu? | Trần Nhân Tông sáng lập dòng Thiền Trúc Lâm ở Việt Nam, sau khi xuất gia năm 1298 lên tu ở núi Yên Tử với pháp hiệu Hương Vân Đại Đầu Đà. |
| 3 | Trần Hạo (Dụ Tông) là con thứ mấy của ai và trị vì mấy năm? | Trần Hạo tức Trần Dụ Tông là con thứ 10 của Trần Minh Tông, làm vua 28 năm với niên hiệu Thiệu Phong (1341–1357) và Đại Trị (1358–1369). |
| 4 | Tác phẩm nổi tiếng nhất của Trần Cảnh (Thái Tông) là gì? | Tác phẩm nổi tiếng nhất của Trần Cảnh là **Khóa Hư Lục** (課虛錄), một tác phẩm Phật học quan trọng. Ngoài ra còn có 2 bài thơ, bài văn và đề tựa kinh Kim Cương. |
| 5 | Trần Kính (Duệ Tông) là con ai và làm vua bao nhiêu năm? | Trần Kính tức Trần Duệ Tông là con thứ 11 của Trần Minh Tông, em của Trần Nghệ Tông. Được Nghệ Tông truyền ngôi vì có công dẹp loạn Dương Nhật Lễ, làm vua được 4 năm. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Trần Anh Tông lên ngôi năm bao nhiêu và là con của ai? | "Không bụi, vách kia sao đường nồi ! Vô vàn bụi nhỏ từ đầu tới? Có ai nhóm thấu tận trong am..." (Nguồn: TRẦN MẠNH.md) | 0.363 | Không | [DEMO LLM] Yêu cầu cung cấp thông tin liên quan đến đoạn thơ "Không bụi..." |
| 2 | Trần Nhân Tông sáng lập thiền phái nào và ở đâu? | "(2) Nhìn không thấy, nghe không được (hy di): Thuật ngữ đạo Phật... (3) Ngũ đế: Phục Hy..." (Nguồn: TRẦN MINH TÔNG.md) | 0.433 | Không | [DEMO LLM] Yêu cầu cung cấp thông tin liên quan đến thuật ngữ đạo Phật (hy di)... |
| 3 | Trần Hạo (Dụ Tông) là con thứ mấy của ai và trị vì mấy năm? | "Chén bát cơm nó đỡ đói lòng. Nước trong đầy hũ, khát thì dùng. Giường máy chiếc gối..." (Nguồn: TRẦN MẠNH.md) | 0.393 | Không | [DEMO LLM] Yêu cầu cung cấp thông tin liên quan đến đoạn thơ "Chén bát cơm..." |
| 4 | Tác phẩm nổi tiếng nhất của Trần Cảnh (Thái Tông) là gì? | "1381 [Tản dậu)... Thì thái học sinh. Triều đình sai nhà sư người Đại Than đi các nơi..." (Nguồn: NIÊN BIỂU KHÁI QUÁT...) | 0.406 | Không | [DEMO LLM] Yêu cầu cung cấp thông tin liên quan đến thi thái học sinh năm 1381... |
| 5 | Trần Kính (Duệ Tông) là con ai và làm vua bao nhiêu năm? | "(4) Đài câu: ở Trung quốc có tới mười nơi gọi là đài câu... Nhưng đây là đây câu của Nghiêm Quang..." (Nguồn: TRẦN ANH TÔNG.md) | 0.409 | Không | [DEMO LLM] Yêu cầu cung cấp thông tin liên quan đến đài câu ở Trung Quốc... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 0 / 5


---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*
Kết hợp các biện pháp Chunking cùng với 1 số thay đổi nhưu check văn bản có cấu trúc gì trước, kết hợp với LLM bên ngoài
**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*
Kiểm tra cấu trúc văn bản và câu hỏi, kết hộp thêm 1 số phương pháp khác. Đồng thời phân tích cách cách chunking trước khi chốt thay vò chọn random 1 cashc chunking mà không biết cấu trúc data
---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 2 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5/ 5 |
| **Tổng** | | **86 / 100** |

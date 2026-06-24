# Design Template

## Problem

Xây dựng hệ thống research assistant tự động hoá luồng nghiên cứu: nhận câu hỏi, tìm kiếm thông tin từ web/document, phân tích sâu nội dung tìm được và tổng hợp thành bài viết đáp ứng đúng yêu cầu của người dùng.

## Why multi-agent?

Single-agent (như ChatGPT thông thường) gặp khó khăn khi xử lý các task nghiên cứu dài và phức tạp: dễ bị "quên" instruction giữa chừng, mất focus khi context window quá lớn, khó kiểm soát chất lượng của từng bước. Việc chia nhỏ thành các Agent (Researcher, Analyst, Writer) giúp chuyên môn hóa từng prompt, dễ dàng quan sát (trace) và debug lỗi ở từng khâu cụ thể.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Điều phối luồng làm việc, quyết định agent nào chạy tiếp | ResearchState hiện tại | Route tiếp theo (researcher/analyst/writer/done) | Lặp vô hạn (infinite loop) hoặc định tuyến sai bước |
| Researcher | Tìm kiếm thông tin, tổng hợp tài liệu thô thành note | Query, Max sources | Danh sách sources, research_notes | Không tìm thấy thông tin hoặc API search bị lỗi |
| Analyst | Phân tích research note, trích xuất claims, lỗ hổng và insights | research_notes | analysis_notes | Hallucination (bịa thông tin), bỏ sót claim quan trọng |
| Writer | Viết bài tổng hợp cuối cùng dựa trên các phân tích | research_notes, analysis_notes, audience | final_answer | Sai văn phong yêu cầu, cấu trúc bài viết lộn xộn |

## Shared state

- `request` (ResearchQuery): Đầu vào ban đầu của user (query, max_sources, audience).
- `sources` (list[SourceDocument]): Danh sách tài liệu thô thu thập được (cần để trích dẫn).
- `research_notes` (str): Nội dung do Researcher tổng hợp.
- `analysis_notes` (str): Phân tích sâu từ Analyst.
- `final_answer` (str): Kết quả cuối cùng trả về.
- `route_history` (list[str]): Lịch sử định tuyến để track luồng chạy và debug.
- `errors` (list[str]): Ghi nhận các lỗi nếu xảy ra.
- `iteration` (int): Số vòng lặp để chặn infinite loop.

## Routing policy

Luồng chạy tuyến tính được Supervisor điều phối:
1. Ban đầu (chưa có `research_notes`): Supervisor -> gọi Researcher.
2. Đã có `research_notes` (nhưng chưa có `analysis_notes`): Supervisor -> gọi Analyst.
3. Đã có `analysis_notes` (nhưng chưa có `final_answer`): Supervisor -> gọi Writer.
4. Đã có `final_answer`: Supervisor -> `done`.

## Guardrails

- Max iterations: 10 vòng lặp (ngăn chặn infinite routing).
- Timeout: Cần cấu hình timeout cho mỗi API call (ví dụ OpenAI timeout 30s).
- Retry: Retries cho LLM calls với exponential backoff (cài đặt qua `tenacity`).
- Fallback: Fallback về Mock Search nếu không có Tavily API key.
- Validation: Pydantic schemas (e.g. `ResearchQuery`, `AgentResult`) đảm bảo type safety.

## Benchmark plan

- Query test: "Research GraphRAG state-of-the-art and write a 500-word summary"
- Metrics: 
  - Latency (thời gian chạy)
  - Cost (USD)
  - Quality Score (1-10 chấm tay hoặc dùng LLM judge)
- Expected outcome: Multi-agent mất nhiều thời gian và token (cost cao hơn) so với baseline single-agent, nhưng điểm Quality (cấu trúc bài viết, tính đầy đủ, độ chính xác) sẽ cao hơn đáng kể.

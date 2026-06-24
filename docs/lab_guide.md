# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

✅ Đã hoàn thành: Sử dụng `LLMClient` trong `src/multi_agent_research_lab/services/llm_client.py` với retry và tracking cost.

## Milestone 2: Supervisor

File gợi ý:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

✅ Đã hoàn thành: Supervisor routing logic đã được implement.

Gợi ý câu hỏi thiết kế:

- Khi nào gọi Researcher?
- Khi nào gọi Analyst?
- Khi nào gọi Writer?
- Khi nào stop?
- Nếu agent fail thì retry hay fallback?

## Milestone 3: Worker agents

File gợi ý:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

✅ Đã hoàn thành: `Researcher`, `Analyst`, và `Writer` agents đã được viết chi tiết.

## Milestone 4: Trace và benchmark

File gợi ý:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark tối thiểu:

| Metric | Cách đo gợi ý |
|---|---|
| Latency | wall-clock time |
| Cost | token usage hoặc provider usage |
| Quality | rubric 0-10 do peer review |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## Exit ticket

Mỗi nhóm trả lời 2 câu:

1. **Case nào nên dùng multi-agent? Vì sao?**
   - **Nên dùng cho**: Các quy trình gồm nhiều bước phức tạp (như research, code review kết hợp testing, viết sách) cần chuyên môn hoá từng vai trò, khi single prompt quá dài và dễ gây hallucination, hoặc khi cần một "người" (agent) check lại công việc của người khác (Critic/Analyst) để tăng độ tin cậy.
   - **Vì sao**: Chia nhỏ vấn đề giúp prompt ngắn hơn, tập trung hơn. Mỗi agent có context riêng biệt, dễ dàng trace lỗi ở khâu nào và prompt engineering riêng cho từng khâu.

2. **Case nào không nên dùng multi-agent? Vì sao?**
   - **Không nên dùng cho**: Các tác vụ đơn giản, hội thoại ngắn, Q&A cơ bản, hoặc các bài toán cần độ trễ thấp (low latency) như chatbot realtime.
   - **Vì sao**: Multi-agent tốn nhiều token (do phải đưa state qua lại giữa các LLM calls), latency rất cao (tuần tự qua nhiều bước), và hệ thống phức tạp hơn mức cần thiết, gây lãng phí chi phí API.

# Báo Cáo Chuyên Sâu: Failure Mode & Phương Pháp Khắc Phục Trong Hệ Thống Multi-Agent

Quá trình xây dựng và vận hành hệ thống **Multi-Agent Research Lab** (bao gồm Supervisor, Researcher, Analyst, Writer và Critic) bộc lộ một số giới hạn và điểm yếu tiềm ẩn (Failure Modes) đặc thù của kiến trúc đa tác nhân. Dưới đây là phân tích chi tiết về 3 lỗi phổ biến nhất, nguyên nhân cốt lõi và phương án khắc phục triệt để.

---

## 1. Lỗi Lặp Vô Hạn (Infinite Routing Loop)

### Mô tả hiện tượng (Symptom)
Luồng thực thi LangGraph bị mắc kẹt giữa các node. Thay vì đi theo chu trình `Supervisor -> Worker -> Supervisor -> Bước tiếp theo`, hệ thống liên tục định tuyến lại về một tác nhân duy nhất (ví dụ: `Researcher -> Supervisor -> Researcher`). Quá trình này không thể tự dừng lại cho đến khi tiêu sạch tiền API (Token limit) hoặc bị crash hệ thống.

### Nguyên nhân cốt lõi (Root Cause)
1. **Thiếu sự đột biến State (State Mutation):** Worker agent (vd: Researcher) gặp lỗi mạng hoặc API trả về nội dung trống nhưng không báo lỗi. Hệ quả là biến `research_notes` trong `ResearchState` không được cập nhật. Khi node này trả kết quả về `Supervisor`, do `research_notes` vẫn rỗng, policy của Supervisor `if not state.research_notes: return "researcher"` tiếp tục đẩy luồng về lại Researcher.
2. **Logic định tuyến (Routing Policy) quá cứng nhắc:** Supervisor chỉ dựa vào sự hiện diện của dữ liệu mà thiếu đi bộ nhớ ngữ cảnh về số lần đã thử thất bại.

### Giải pháp khắc phục (Fixes)
1. **Bổ sung biến đếm số vòng lặp (Iteration Counter):**
   Trong `ResearchState`, bổ sung thêm một trường `iteration: int`. Mỗi lần `Supervisor` chạy, nó sẽ tăng `iteration` lên 1.
2. **Triển khai Guardrail `max_iterations`:**
   Bắt buộc hệ thống ngắt sớm (Early exit) nếu vượt qua một ngưỡng cố định, giúp ngăn chặn tiêu thụ tài nguyên vô ích.
   ```python
   # Trong agents/supervisor.py
   def run(self, state: ResearchState) -> AgentResult:
       # Guardrail: Check maximum iterations
       if state.iteration >= self.max_iterations:
           return AgentResult(agent=self.name, route="done", content="Max iterations reached.")
   ```
3. **Bắt buộc cập nhật State:** Viết cơ chế gán giá trị mặc định cho state nếu Worker thất bại (vd: `state.research_notes = "Error: Could not fetch data"`).

---

## 2. LLM Hallucination (Sinh Ra Thông Tin Giả Mạo)

### Mô tả hiện tượng (Symptom)
Agent `Writer` tự động "sáng tác" ra các số liệu thống kê không hề có thật hoặc tạo ra các trích dẫn tài liệu (Citations) không nằm trong danh sách `sources` gốc mà `Researcher` thu thập được. Điều này cực kỳ nguy hiểm đối với một hệ thống Research Assistant yêu cầu độ chính xác tuyệt đối.

### Nguyên nhân cốt lõi (Root Cause)
1. **Mất tập trung (Lost in the middle):** Khi `research_notes` và `analysis_notes` quá dài, LLM bị vượt quá cửa sổ ngữ cảnh tập trung (attention window) và tự kích hoạt các trọng số ngầm định (parametric memory) để "bù đắp" vào chỗ thiếu.
2. **Prompt quá "mở":** Prompt không đóng khung chặt chẽ quyền hạn của LLM, khiến LLM tin rằng nó được phép suy diễn nội dung bên ngoài.

### Giải pháp khắc phục (Fixes)
1. **Prompt Engineering với ranh giới rõ ràng:**
   Thay đổi System Prompt của Writer: 
   *"Bạn là một người tổng hợp. Bạn CHỈ ĐƯỢC PHÉP sử dụng thông tin nằm trong các `sources` sau đây. TUYỆT ĐỐI KHÔNG sử dụng kiến thức bên ngoài. Nếu thông tin không đủ để trả lời, hãy viết 'Dữ liệu không đề cập đến vấn đề này'."*
2. **Tích hợp Critic Agent (Cross-Examination):**
   Đưa thêm một Node mới tên là `Critic` vào ngay sau `Writer` trước khi kết thúc (`done`). `Critic` sẽ đóng vai trò trọng tài, đối chiếu chéo (Cross-check) nội dung của `final_answer` với mảng `sources`.
   ```python
   # Trong workflow.py
   workflow.add_node("critic", CriticAgent().run)
   # Supervisor routing
   elif not any(r.agent == "critic" for r in state.agent_results):
       route = "critic"
   ```
3. **Sử dụng Grounding / RAG Strict Mode:** Cấu hình temperature của LLM về `0.0` thay vì các mức độ sáng tạo cao hơn, giúp mô hình bám sát dữ liệu thô.

---

## 3. Lỗi Đứt Gãy Do Timeout & Rate Limit (API Quotas)

### Mô tả hiện tượng (Symptom)
Hệ thống Multi-agent đột ngột dừng chạy và ném ra exception (ví dụ `openai.RateLimitError` hoặc `TimeoutError`). Không có kết quả nào được lưu lại mặc dù hệ thống đã chạy được 90% chặng đường.

### Nguyên nhân cốt lõi (Root Cause)
1. Trong kiến trúc Multi-agent, một yêu cầu duy nhất từ người dùng (Query) có thể kích hoạt từ 4 đến 10 API calls lên OpenAI (tương ứng với các agent khác nhau giao tiếp nối tiếp). Điều này dễ dàng vượt quá hạn mức Requests Per Minute (RPM) đối với các tài khoản API Tier thấp.
2. Độ trễ mạng (Network Latency) khi gọi đến LLM hoặc Search Provider (Tavily) tăng đột biến.

### Giải pháp khắc phục (Fixes)
1. **Cơ chế Retry Tự Động (Exponential Backoff):**
   Sử dụng thư viện `tenacity` để tự động tính toán khoảng thời gian chờ tăng dần (vd: đợi 2s, 4s, 8s...) giữa các lần gọi lại nếu gặp lỗi HTTP 429 (Too Many Requests).
   ```python
   from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
   
   @retry(
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       retry=retry_if_exception_type((TimeoutError, RateLimitError))
   )
   def call_llm_api():
       # Logic gọi OpenAI API
   ```
2. **Fallbacks an toàn (Graceful Degradation):**
   Trong phương thức `.complete()` của client, bắt toàn bộ các lỗi liên quan đến API và nạp thông báo lỗi vào `ResearchState.errors` thay vì để exception phá huỷ (crash) chương trình. Supervisor có thể đọc `state.errors` để chuyển hướng sang một flow báo lỗi nhẹ nhàng hơn tới người dùng.

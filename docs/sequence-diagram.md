# CodePath — Sơ đồ tuần tự

| | |
|---|---|
| **Phiên bản** | 1.1 |
| **Tài liệu liên quan** | `requirements.md` (v1.1), `use-case.md` (v1.1), `state-diagrams.md` (v1.1) |

> Tên endpoint trong sơ đồ chỉ để minh họa, chưa phải đặc tả API. Khi có đặc tả API, cần cập nhật cho khớp.

## Mục lục

1. [Các thành phần tham gia](#1-các-thành-phần-tham-gia)
2. [UC-09 — Nộp bài và xem kết quả chấm](#2-uc-09--nộp-bài-và-xem-kết-quả-chấm)

---

## 1. Các thành phần tham gia

| Thành phần | Vai trò | Công nghệ (§1.2) |
|---|---|---|
| Người học | Tác nhân chính | — |
| Frontend | Trình soạn code, hiển thị trạng thái và kết quả | React, Monaco |
| API | Kiểm tra quyền, tạo bài nộp, trả kết quả | Express.js, Zod |
| PostgreSQL | Lưu bài nộp, kết quả từng test, tiến độ | PostgreSQL, Prisma |
| Hàng đợi | Chuyển việc chấm bài sang worker | Redis, BullMQ |
| Worker | Lấy việc, chạy test, tính điểm và verdict (UC-25) | Node.js |
| Sandbox | Chạy mã cô lập (UC-27) | Docker hoặc Judge0 |
| Bộ định thời | Phục hồi bài nộp kẹt (UC-26) | — |

## 2. UC-09 — Nộp bài và xem kết quả chấm

### 2.1 Luồng chính

Gồm: kiểm tra yêu cầu, tạo bài nộp `QUEUED`, chấm bất đồng bộ qua hàng đợi, và giao diện cập nhật kết quả. Giao diện và worker chạy song song sau khi API đã phản hồi.

```mermaid
sequenceDiagram
  autonumber
  actor L as Người học
  participant FE as Frontend
  participant API as API
  participant DB as PostgreSQL
  participant Q as Hàng đợi
  participant W as Worker
  participant SB as Sandbox

  L->>FE: Nhấn Nộp bài
  FE->>API: POST /submissions (bài tập, ngôn ngữ, mã nguồn)
  API->>API: Xác thực, kiểm tra tài khoản còn hoạt động, kiểm tra dữ liệu
  API->>DB: Kiểm tra đã ghi danh và khóa học PUBLISHED hoặc ARCHIVED
  DB-->>API: Kết quả kiểm tra
  API->>API: Kiểm tra ngôn ngữ, kích thước mã, giới hạn tần suất

  alt Không hợp lệ
    API-->>FE: Lỗi 400, 403 hoặc 429
    FE-->>L: Hiển thị lỗi
  else Hợp lệ
    API->>DB: Tạo bài nộp, trạng thái QUEUED
    API->>Q: Thêm job (mã bài nộp)
    API-->>FE: Phản hồi ngay, trạng thái QUEUED
    FE-->>L: Hiển thị đang chờ chấm

    par Giao diện cập nhật kết quả
      loop Cho đến khi có verdict cuối hoặc INTERNAL_ERROR
        FE->>API: GET /submissions/id
        API->>DB: Đọc trạng thái và kết quả
        DB-->>API: Dữ liệu bài nộp
        alt Đã có verdict cuối
          API-->>FE: Verdict, điểm, kết quả từng test (test ẩn chỉ đạt hoặc không đạt)
          FE-->>L: Hiển thị kết quả, đánh dấu hoàn thành nếu ACCEPTED
        else Chưa xong
          API-->>FE: Trạng thái QUEUED hoặc RUNNING
        end
      end
    and Worker chấm bài
      Q->>W: Giao job (mã bài nộp)
      W->>DB: Chuyển RUNNING, chỉ khi đang QUEUED
      DB-->>W: Số dòng được cập nhật

      alt Không nhận được (job trùng hoặc bài đã đổi trạng thái)
        W->>W: Bỏ qua job
      else Nhận được
        W->>DB: Đọc test case, giới hạn thời gian và bộ nhớ
        DB-->>W: Danh sách test case

        loop Với từng test case
          W->>SB: Chạy mã (ngôn ngữ, đầu vào, giới hạn)
          Note right of SB: Container mới, không mạng, không root, hủy sau khi chạy
          SB-->>W: Kết quả (đầu ra, thời gian, bộ nhớ, loại lỗi)

          alt Lỗi biên dịch
            W->>W: Dừng chấm, verdict COMPILE_ERROR, điểm 0
          else Lỗi hạ tầng sandbox sau khi thử lại có giới hạn
            W->>W: Dừng chấm, chuyển INTERNAL_ERROR (xem sơ đồ 2.2)
          else Chạy được
            W->>W: So sánh đầu ra, ghi kết quả của test
          end
        end

        W->>W: Tính điểm theo trọng số, xác định verdict cuối theo mục 3.3
        W->>DB: Lưu kết quả và verdict, chỉ khi bài vẫn đang RUNNING
        Note over W,DB: Cùng một transaction
        opt Verdict là ACCEPTED
          W->>DB: Ghi tiến độ mục học (duy nhất theo người học và mục học)
        end
      end
    end
  end
```

| Bước | Hành động | Ràng buộc liên quan |
|---|---|---|
| 3–6 | Kiểm tra xác thực, quyền, dữ liệu vào, ngôn ngữ, kích thước, tần suất | BR-05, BR-13, BR-14, NFR-02, NFR-03, NFR-06, FR-31 |
| 7–8 | Từ chối khi không hợp lệ (400, 403, 429) | UC-09 (2a, 2b), BR-14, AC-22 |
| 9–11 | Tạo bài nộp `QUEUED`, đưa vào hàng đợi, phản hồi ngay, không nhận điểm hay verdict từ client | BR-08, NFR-09, FR-28 |
| 12–18 | Giao diện hiển thị đang chờ rồi cập nhật tự động, không cần tải lại trang | AC-21 |
| 19–22 | Worker nhận job và chuyển `RUNNING` chỉ khi đang `QUEUED`, nên job lặp không chấm hai lần | BR-11, NFR-11 |
| 25–26 | Mỗi test chạy trong sandbox riêng, theo ràng buộc cô lập | BR-10, NFR-07, §3.6, UC-27 |
| 27–28 | Lỗi biên dịch dừng chấm với điểm 0; lỗi hạ tầng chuyển `INTERNAL_ERROR` | §3.3, UC-25 |
| 30 | Tính điểm bằng tổng trọng số test đạt, xác định verdict theo quy tắc ưu tiên | §3.3, AC-15, AC-16, AC-44 |
| 31–32 | Lưu kết quả và tiến độ trong một transaction, chỉ khi bài vẫn `RUNNING` | NFR-12, NFR-13, BR-12, AC-24 |
| 16 | Test ẩn chỉ trả đạt hoặc không đạt, không trả dữ liệu | BR-09, AC-20, FR-29 |

### 2.2 Luồng sự cố: bài nộp kẹt và chấm lại

Áp dụng khi worker treo, sandbox hỏng hoặc hàng đợi mất việc (luồng thay thế 5c của UC-09). Bộ định thời phục hồi bài nộp (UC-26), sau đó giảng viên hoặc admin chấm lại (UC-19). Các nhóm sự kiện trong sơ đồ độc lập với nhau, được xếp theo trình tự của một kịch bản điển hình.

```mermaid
sequenceDiagram
  autonumber
  participant S as Bộ định thời
  participant DB as PostgreSQL
  participant Q as Hàng đợi
  participant W as Worker
  participant FE as Frontend
  participant API as API
  actor ST as Giảng viên hoặc Admin

  Note over S,DB: Quét định kỳ, ví dụ mỗi 30 giây
  loop Mỗi lần quét
    S->>DB: Tìm bài nộp RUNNING quá 2 phút
    DB-->>S: Danh sách bài kẹt
    S->>DB: Chuyển INTERNAL_ERROR và ghi log
    S->>DB: Tìm bài nộp QUEUED quá 5 phút
    DB-->>S: Danh sách bài kẹt
    alt Đã đưa lại chưa quá 3 lần
      S->>Q: Thêm lại job (mã bài nộp)
      S->>DB: Tăng số lần đưa lại
    else Đã đưa lại quá 3 lần
      S->>DB: Chuyển INTERNAL_ERROR và ghi log
    end
  end

  FE->>API: GET /submissions/id
  API-->>FE: Trạng thái INTERNAL_ERROR
  Note over FE: Báo lỗi hệ thống, không tính vào lần nộp của người học

  Note over W,DB: Worker treo hoặc chậm, gửi kết quả sau khi bài đã đổi trạng thái
  W->>DB: Lưu kết quả, chỉ khi bài vẫn đang RUNNING
  DB-->>W: Không dòng nào được cập nhật, bỏ kết quả

  ST->>API: GET danh sách bài nộp INTERNAL_ERROR
  API->>API: Kiểm tra quyền (giảng viên chỉ khóa của mình, admin toàn hệ thống)
  API->>DB: Truy vấn danh sách
  DB-->>API: Danh sách bài nộp lỗi
  API-->>ST: Danh sách bài nộp lỗi
  ST->>API: POST /submissions/id/rejudge
  API->>DB: Kiểm tra đang INTERNAL_ERROR, tạo bản ghi kết quả mới, trạng thái QUEUED
  API->>Q: Thêm job (mã bài nộp)
  API-->>ST: Đã đưa vào hàng đợi
  Note over Q,W: Từ đây chấm như sơ đồ 2.1
```

| Bước | Hành động | Ràng buộc liên quan |
|---|---|---|
| 1–3 | Bài `RUNNING` quá 2 phút chuyển `INTERNAL_ERROR` | §3.3, UC-26, AC-23 |
| 4–8 | Bài `QUEUED` quá 5 phút được đưa lại hàng đợi, tối đa 3 lần, vượt quá thì `INTERNAL_ERROR` | §3.3, UC-26, AC-23 |
| 9–10 | Giao diện báo lỗi hệ thống, bài không tính vào lần nộp | §3.3, UC-09 (5c) |
| 11–12 | Kết quả đến muộn bị bỏ qua nhờ điều kiện trạng thái khi lưu | §3.3, BR-11 |
| 13–21 | Chấm lại tạo bản ghi kết quả mới, ghi nhận người thực hiện | UC-19, BR-07, BR-11, FR-32 |

### 2.3 Điểm thiết kế cần xác nhận

1. **Cập nhật kết quả bằng polling.** §3.3 cho phép polling hoặc SSE/WebSocket. Sơ đồ dùng polling vì đơn giản; chuyển sang SSE chỉ thay vòng lặp ở khối giao diện, không đổi phần còn lại.
2. **Tạo bài nộp rồi mới đưa vào hàng đợi, không nguyên tử.** Nếu API lỗi giữa hai bước, bài nộp nằm ở `QUEUED` mà không có job, và chỉ được đưa lại sau 5 phút nhờ UC-26. Chấp nhận độ trễ này, hay dùng outbox, hay trả lỗi ngay cho người học khi đưa vào hàng đợi thất bại?
3. **Chạy hết test case.** Điểm bằng tổng trọng số test đạt nên worker chạy toàn bộ test, chỉ dừng khi biên dịch lỗi hoặc hạ tầng lỗi. Với bài nhiều test, thời gian chấm tăng theo số test (liên quan NFR-10).
4. **Biên dịch lặp lại.** Mỗi test chạy trong sandbox riêng (§3.3) và UC-27 biên dịch trong từng lần chạy. Biên dịch một lần rồi dùng lại là tối ưu triển khai, không đổi hành vi. Nên gắn với quyết định Judge0 hay runner tự xây (câu hỏi mở 1).
5. **Số lần đưa lại.** Bộ định thời cần đếm số lần đưa lại cho mỗi bài `QUEUED`. Requirements chưa quy định chỗ lưu (cột riêng hay dùng bộ đếm retry của BullMQ), cần chốt khi thiết kế CSDL.
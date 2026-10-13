# CodePath — Đặc tả yêu cầu hệ thống

**Đề tài:** Phát triển nền tảng học lập trình trực tuyến tích hợp môi trường thực hành và đánh giá

| | |
|---|---|
| **Phiên bản** | 1.0 |
| **Trạng thái** | Bản nháp để review |
| **Phạm vi** | MVP |

> Các mục đánh dấu **[Quyết định]** là các giả định mặc định nhằm giải quyết điểm chưa rõ. Có thể thay đổi, nhưng nên xác nhận trước khi triển khai.

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Vai trò người dùng](#2-vai-trò-người-dùng)
3. [Mô hình nghiệp vụ và vòng đời trạng thái](#3-mô-hình-nghiệp-vụ-và-vòng-đời-trạng-thái)
4. [Yêu cầu chức năng](#4-yêu-cầu-chức-năng)
5. [Quy tắc nghiệp vụ](#5-quy-tắc-nghiệp-vụ)
6. [Yêu cầu phi chức năng](#6-yêu-cầu-phi-chức-năng)
7. [Ngoài phạm vi](#7-ngoài-phạm-vi)
8. [Tiêu chí chấp nhận](#8-tiêu-chí-chấp-nhận)
9. [Ma trận truy vết](#9-ma-trận-truy-vết)
10. [Câu hỏi mở](#10-câu-hỏi-mở)

---

## 1. Tổng quan

CodePath là nền tảng web giúp người học tiếp cận lập trình theo lộ trình: học qua bài giảng, **viết và chạy code trực tiếp trên trình duyệt**, nộp bài để được **chấm tự động** bằng bộ test case, và tham gia các bài đánh giá (quiz, bài kiểm tra code) để đo năng lực. Giảng viên tạo nội dung và bài tập; quản trị viên kiểm duyệt nội dung và vận hành hệ thống.

### 1.1 Mục tiêu

- Rút ngắn khoảng cách giữa **học lý thuyết** và **thực hành**: người học không cần cài đặt môi trường.
- Cung cấp **phản hồi tức thì** thông qua chấm bài tự động.
- Giúp giảng viên **theo dõi tiến độ và kết quả** của người học.
- Đảm bảo việc chạy mã không đáng tin cậy được thực hiện **an toàn** trong môi trường cô lập.

### 1.2 Công nghệ

| Tầng | Công nghệ |
|---|---|
| Frontend | React, TypeScript, Vite, Monaco Editor (trình soạn code) |
| Backend | Node.js, Express.js, TypeScript |
| Cơ sở dữ liệu | PostgreSQL |
| ORM | Prisma |
| Hàng đợi chấm bài | Redis + BullMQ |
| Môi trường chạy code | Docker sandbox tự dựng hoặc Judge0 (self-hosted) |
| Kiểm tra dữ liệu | Zod |
| API | REST dưới `/api/v1`, tài liệu OpenAPI/Swagger |
| Triển khai local | Docker Compose (PostgreSQL, Redis, runner) + seed dữ liệu |

### 1.3 Quy ước chung

- **Ngôn ngữ giao diện:** Tiếng Việt (có thể mở rộng đa ngôn ngữ sau MVP).
- **Ngôn ngữ lập trình được hỗ trợ trong MVP:** Python 3, JavaScript (Node.js), C++17. Java là tùy chọn.
- **Thời gian:** lưu theo UTC, trả về theo ISO 8601.
- **Trình duyệt:** hai phiên bản mới nhất của Chrome, Edge, Firefox, Safari. Giao diện responsive từ 360 px.
- **Khóa học miễn phí** trong MVP (không có thanh toán).

---

## 2. Vai trò người dùng

Mỗi tài khoản có đúng một vai trò chính: `LEARNER`, `INSTRUCTOR` hoặc `ADMIN`.

| Vai trò | Quyền hạn |
|---|---|
| **Khách (Guest)** | Xem danh sách khóa học đã xuất bản; tìm kiếm, lọc; xem chi tiết khóa học và bài học xem thử; đăng ký, đăng nhập. |
| **Người học (Learner)** | Mọi quyền của khách; ghi danh khóa học; học bài; viết, chạy thử và nộp code; làm bài đánh giá; xem tiến độ, lịch sử nộp bài và kết quả của mình. |
| **Giảng viên (Instructor)** | Tạo và quản lý **khóa học của mình**: chương, bài học, bài tập code (kèm test case), bài đánh giá; gửi khóa học để duyệt; xem kết quả duyệt; xem thống kê và bài nộp của người học trong khóa học của mình. Không thể duyệt khóa học hoặc sửa nội dung của giảng viên khác. Có thể học khóa học của giảng viên khác với các quyền như Người học (xem [Quyết định] bên dưới). |
| **Quản trị viên (Admin)** | Quản lý người dùng; duyệt hoặc từ chối khóa học; quản lý danh mục và ngôn ngữ chạy code; xem thống kê hệ thống; theo dõi hàng đợi chấm bài. Xem danh sách bài nộp `INTERNAL_ERROR` trên toàn hệ thống để chấm lại (FR-32); xem nội dung đầy đủ của khóa học chờ duyệt. |

**[Quyết định]** Tài khoản Admin chỉ được tạo bằng seed script. Đăng ký công khai chỉ cho phép `LEARNER` hoặc `INSTRUCTOR`. Giảng viên có thể ghi danh và học khóa học của giảng viên **khác** với đầy đủ quyền của Người học, nhưng không ghi danh vào khóa học của chính mình. Quản trị viên không có quyền học tập.

---

## 3. Mô hình nghiệp vụ và vòng đời trạng thái

### 3.1 Cấu trúc nội dung

```
Khóa học (Course)
 ├── Chương (Section)
 │    └── Mục học (Lesson)  ── loại: TEXT | VIDEO | CODING | QUIZ
 └── Bài đánh giá (Assessment)  ── chứa bản sao câu hỏi và bài tập
```

- **TEXT:** nội dung Markdown.
- **VIDEO:** đường dẫn video bên ngoài (không upload file trong MVP).
- **CODING:** bài tập lập trình gồm đề bài, mã khởi tạo (starter code), ngôn ngữ cho phép, giới hạn thời gian/bộ nhớ và các test case.
- **QUIZ:** bộ câu hỏi trắc nghiệm (một đáp án hoặc nhiều đáp án) dùng để luyện tập. Mỗi mục QUIZ có **điểm đạt** (mặc định 70%) và cho làm lại không giới hạn.
- **Bài đánh giá:** bài kiểm tra có giới hạn thời gian gắn với khóa học (§3.4), nằm ngoài cây Chương/Mục và không tính vào phần trăm tiến độ. Khi tạo, câu hỏi và bài tập được **sao chép** từ các mục QUIZ, CODING; sửa mục gốc không làm đổi bài đánh giá.

Mỗi mục học có cờ `isPreview` do giảng viên sở hữu thiết lập. Nội dung của mục không phải xem thử (đường dẫn video, nội dung, đề bài, đáp án) **không được trả về** cho người chưa ghi danh, trừ chủ khóa học và quản trị viên (BR-05).

### 3.2 Vòng đời khóa học

```
DRAFT ──gửi duyệt──► PENDING_REVIEW ──duyệt──► PUBLISHED
  ▲                        │                       │
  │                        └──từ chối──► REJECTED  └──gỡ xuống──► ARCHIVED
  └──────── chỉnh sửa & gửi lại ◄─────────┘
```

| Trạng thái | Hiển thị công khai | Cho phép ghi danh | Chủ khóa học được sửa |
|---|---|---|---|
| `DRAFT` | Không | Không | Có |
| `PENDING_REVIEW` | Không | Không | Không (khóa) |
| `PUBLISHED` | Có | Có | Có |
| `REJECTED` | Không | Không | Có, rồi gửi lại |
| `ARCHIVED` | Không | Không | Không |

Quy tắc:
- **[Quyết định]** Duyệt khóa học đồng nghĩa với xuất bản (chuyển thẳng sang `PUBLISHED`).
- Từ chối **bắt buộc có lý do** (10–1000 ký tự); giảng viên xem được lý do và có thể gửi lại.
- Chỉ gửi duyệt được khi khóa học có đủ tiêu đề, mô tả, danh mục, ít nhất một chương có ít nhất một mục học; **mỗi bài CODING có ít nhất một test case ẩn** cùng một lời giải tham chiếu đã vượt qua toàn bộ test case; **mỗi mục QUIZ có ít nhất một câu hỏi hợp lệ**.
- Sửa khóa học `PUBLISHED` được áp dụng ngay, không cần duyệt lại trong MVP, **với điều kiện** mỗi lần lưu vẫn giữ các điều kiện gửi duyệt ở trên: bài CODING còn ít nhất một test ẩn và lời giải tham chiếu vẫn đạt toàn bộ test; mục QUIZ còn ít nhất một câu hỏi hợp lệ. Lưu vi phạm bị từ chối. Quản trị viên có thể gỡ xuống bất cứ lúc nào.
- Chỉ xóa cứng được khóa học ở `DRAFT` hoặc `REJECTED` chưa có ghi danh nào; các trường hợp còn lại chỉ có thể lưu trữ.
- Khóa học đã có học viên ghi danh **không thể bị xóa cứng**, chỉ có thể lưu trữ. Học viên đã ghi danh **vẫn giữ quyền truy cập** sau khi khóa học bị lưu trữ.
- Khi giảng viên sửa test case hoặc đề bài của bài tập đã có bài nộp, các bài nộp cũ **giữ nguyên kết quả** đã chấm (không chấm lại tự động).

### 3.3 Vòng đời bài nộp (Submission)

```
QUEUED ──► RUNNING ──► (kết quả cuối)
  ▲                          │
  └─── chấm lại ◄── INTERNAL_ERROR
```

Kết quả cuối (verdict):

| Verdict | Ý nghĩa |
|---|---|
| `ACCEPTED` | Đúng toàn bộ test case |
| `PARTIAL` | Có ít nhất một test đạt; các test còn lại sai đầu ra |
| `WRONG_ANSWER` | Không có test nào đạt và lỗi là sai đầu ra |
| `COMPILE_ERROR` | Lỗi biên dịch / cú pháp |
| `RUNTIME_ERROR` | Lỗi khi chạy (exception, exit code khác 0) |
| `TIME_LIMIT_EXCEEDED` | Vượt giới hạn thời gian |
| `MEMORY_LIMIT_EXCEEDED` | Vượt giới hạn bộ nhớ |
| `OUTPUT_LIMIT_EXCEEDED` | In quá nhiều dữ liệu |
| `INTERNAL_ERROR` | Lỗi hệ thống chấm bài (không tính vào lần nộp của người học) |

**Quy tắc xác định verdict cuối:**
1. Lỗi biên dịch → `COMPILE_ERROR`, điểm 0.
2. Mọi test đạt → `ACCEPTED`.
3. Ngược lại, xét test không đạt **đầu tiên theo thứ tự test**: nếu là sai đầu ra thì `PARTIAL` (có ít nhất một test đạt) hoặc `WRONG_ANSWER` (không test nào đạt); nếu là lỗi khác thì verdict là loại lỗi đó (`RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `OUTPUT_LIMIT_EXCEEDED`).
Điểm luôn bằng tổng trọng số các test đạt, bất kể verdict.

Quy tắc:
- Nộp bài tạo bản ghi `QUEUED` ngay và trả về ngay; chấm bài chạy **bất đồng bộ** qua hàng đợi. Giao diện cập nhật trạng thái bằng polling hoặc SSE/WebSocket.
- Mỗi test case được chạy trong sandbox riêng; điểm bài nộp = tổng trọng số các test case đạt.
- Với test case **công khai**, người học xem được đầu vào, đầu ra mong đợi và đầu ra thực tế. Với test case **ẩn**, chỉ xem được trạng thái đạt/không đạt, **không** xem được dữ liệu.
- Chức năng **Chạy thử** (run) chỉ chạy với test mẫu hoặc đầu vào tùy chọn của người học, **không** tạo bài nộp và không ảnh hưởng điểm hay tiến độ.
- Bài nộp bị kẹt ở `RUNNING` quá thời gian tối đa (mặc định 2 phút) được chuyển `INTERNAL_ERROR` và có thể chấm lại. Bài nộp ở `QUEUED` quá ngưỡng chờ (mặc định 5 phút) được đưa lại vào hàng đợi, tối đa 3 lần, vượt quá thì chuyển `INTERNAL_ERROR`. Kết quả chấm đến sau khi bài đã bị chuyển trạng thái được bỏ qua.
- Điểm bài tập của người học = điểm cao nhất trong các lần nộp **[Quyết định]**. Mục học được coi là hoàn thành khi có ít nhất một bài nộp `ACCEPTED`.

### 3.4 Bài đánh giá (Assessment)

Bài đánh giá là một bài kiểm tra có giới hạn thời gian, gồm câu hỏi trắc nghiệm và/hoặc bài tập code, gắn với một khóa học.

```
NOT_STARTED ──bắt đầu──► IN_PROGRESS ──nộp──► SUBMITTED ──chấm xong──► GRADED
                              │
                              └──hết giờ──► SUBMITTED (tự động nộp)
```

Quy tắc:
- Cấu hình bài đánh giá: thời lượng, số lần làm tối đa, điểm đạt, thang điểm, ngày mở/đóng.
- Thời gian làm bài tính **theo đồng hồ máy chủ**; hết giờ hệ thống tự nộp bài với nội dung đã lưu.
- Câu trắc nghiệm được chấm ngay khi nộp; phần code chấm qua hàng đợi như §3.3. Bài đánh giá chuyển `GRADED` khi mọi phần đã chấm xong.
- Người học chỉ xem đáp án đúng sau khi bài đánh giá đã `GRADED` và hết số lần làm (hoặc theo cấu hình của giảng viên).
- Mỗi người học chỉ có **một lần làm đang ở trạng thái `IN_PROGRESS`** cho mỗi bài đánh giá.
- **[Quyết định]** Chống gian lận trong MVP chỉ ở mức cơ bản: giới hạn thời gian, giới hạn số lần, xáo trộn thứ tự câu hỏi/đáp án và ghi log sự kiện rời tab. Không có giám sát bằng camera hoặc phát hiện đạo văn tự động.
- Hạn nộp của lần làm là thời điểm sớm hơn giữa (thời điểm bắt đầu + thời lượng) và ngày đóng.
- Người học quay lại khi đang có lần làm `IN_PROGRESS` thì tiếp tục lần làm đó với nháp đã lưu; đồng hồ vẫn tính theo máy chủ.
- Điểm của bài đánh giá là điểm **cao nhất** trong các lần làm (BR-19).
- Code nộp trong bài đánh giá không tạo bài nộp ở lịch sử bài tập và không ảnh hưởng tiến độ hay điểm của mục CODING.
- Phần code gặp `INTERNAL_ERROR` thì lần làm giữ nguyên chờ chấm lại, chưa chuyển `GRADED`.
- Bài đánh giá đã có lần làm thì khóa nội dung và cấu hình; chỉ cho gia hạn ngày đóng (BR-20).

### 3.5 Tiến độ học tập

- Tiến độ lưu theo `(người học, mục học)`: chưa học / hoàn thành.
- Mục TEXT và VIDEO hoàn thành khi người học đánh dấu; mục CODING hoàn thành khi có bài nộp `ACCEPTED`; mục QUIZ hoàn thành khi điểm từ điểm đạt của mục trở lên (điểm của mục là điểm cao nhất các lần làm; đã hoàn thành thì không mất trạng thái khi lần làm sau thấp hơn).
- Phần trăm tiến độ khóa học = số mục hoàn thành ÷ tổng số mục hiện có, làm tròn xuống. Khi giảng viên thêm hoặc xóa mục, phần trăm được tính lại theo tổng mới.
- Tiến độ gắn với `(người học, mục học)`, không phụ thuộc bản ghi ghi danh: hủy ghi danh vẫn giữ tiến độ, ghi danh lại thì khôi phục. Khóa học `ARCHIVED` không cho ghi danh mới, nên người học hủy ghi danh khóa này sẽ không ghi danh lại được.
- Bài đánh giá không được tính vào phần trăm tiến độ khóa học.

### 3.6 Môi trường chạy code (Sandbox)

Mọi mã người dùng được xem là **không đáng tin cậy**. Mỗi lần chạy phải thỏa các ràng buộc sau:

| Ràng buộc | Mặc định MVP |
|---|---|
| Cô lập | Container riêng cho mỗi lần chạy, hủy sau khi chạy xong |
| Mạng | Tắt hoàn toàn |
| Người dùng trong container | Không phải root, filesystem chỉ đọc trừ thư mục tạm |
| Thời gian CPU | Tối đa 2 giây mỗi test (cấu hình theo bài, tối đa 10 giây) |
| Bộ nhớ | Tối đa 256 MB (cấu hình theo bài, tối đa 512 MB) |
| Số tiến trình | Giới hạn để chặn fork bomb |
| Kích thước đầu ra | Tối đa 64 KB |
| Kích thước mã nguồn | Tối đa 64 KB |

---

## 4. Yêu cầu chức năng

### 4.1 Xác thực và người dùng

| ID | Yêu cầu |
|---|---|
| FR-01 | Người dùng đăng ký (email, mật khẩu, tên hiển thị, vai trò `LEARNER` hoặc `INSTRUCTOR`) và đăng nhập. |
| FR-02 | Người dùng đăng xuất và xem hồ sơ của mình. |
| FR-03 | Hệ thống phân quyền theo vai trò trên mọi endpoint được bảo vệ. |
| FR-04 | Admin vô hiệu hóa và kích hoạt lại tài khoản; token hiện có của tài khoản bị vô hiệu hóa không còn hiệu lực ngay lập tức. |
| FR-05 | Người dùng chỉnh sửa hồ sơ (tên hiển thị, giới thiệu, ảnh đại diện dạng URL) và đổi mật khẩu. |
| FR-06 | Admin xem, tìm kiếm, lọc người dùng theo vai trò và trạng thái. Admin không thể tự vô hiệu hóa mình hoặc quản trị viên đang hoạt động cuối cùng. |

### 4.2 Khám phá khóa học

| ID | Yêu cầu |
|---|---|
| FR-07 | Khách xem danh sách khóa học đã xuất bản. |
| FR-08 | Tìm kiếm theo tiêu đề; lọc theo danh mục, ngôn ngữ lập trình, độ khó (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`); sắp xếp theo mới nhất hoặc phổ biến. |
| FR-09 | Xem chi tiết khóa học: mô tả, thông tin giảng viên, đề cương (tên chương và mục), số bài tập, mục học xem thử. |

### 4.3 Quản lý khóa học và nội dung (Giảng viên)

| ID | Yêu cầu |
|---|---|
| FR-10 | Giảng viên tạo, sửa và xóa (theo §3.2) khóa học của mình. |
| FR-11 | Giảng viên tạo, sửa, sắp xếp lại và xóa chương và mục học (TEXT, VIDEO, CODING, QUIZ); đánh dấu mục xem thử. |
| FR-12 | Giảng viên tạo bài tập CODING: đề bài (Markdown), ngôn ngữ cho phép, mã khởi tạo cho từng ngôn ngữ, giới hạn thời gian/bộ nhớ, gợi ý (hint). |
| FR-13 | Giảng viên quản lý test case của bài tập: đầu vào, đầu ra mong đợi, trọng số điểm, công khai hoặc ẩn. |
| FR-14 | Giảng viên khai báo lời giải tham chiếu cho từng ngôn ngữ được phép của bài tập và chạy kiểm tra thử toàn bộ test case trước khi gửi duyệt. |
| FR-15 | Giảng viên tạo mục QUIZ và bộ câu hỏi (một hoặc nhiều đáp án, có giải thích), đặt điểm đạt cho mục. Câu hỏi hợp lệ khi có ít nhất 2 lựa chọn, có ít nhất một đáp án đúng, và câu một đáp án chỉ có một đáp án đúng. |
| FR-16 | Giảng viên tạo và cấu hình bài đánh giá (§3.4): chọn câu hỏi và bài tập từ các mục QUIZ, CODING của khóa (lưu dưới dạng bản sao), đặt điểm từng phần; sau khi đã có lần làm chỉ được gia hạn ngày đóng. |
| FR-17 | Giảng viên gửi khóa học `DRAFT` hoặc `REJECTED` để duyệt; xem danh sách khóa học, trạng thái và lý do từ chối. |

### 4.4 Kiểm duyệt và quản trị

| ID | Yêu cầu |
|---|---|
| FR-18 | Admin xem danh sách khóa học chờ duyệt, duyệt hoặc từ chối (bắt buộc có lý do khi từ chối). |
| FR-19 | Admin gỡ xuống (lưu trữ) khóa học đang xuất bản. |
| FR-20 | Admin tạo, đổi tên, xóa (khi chưa sử dụng) danh mục. |
| FR-21 | Admin bật/tắt ngôn ngữ lập trình được hỗ trợ và xem cấu hình giới hạn mặc định. |
| FR-22 | Admin xem thống kê: số người dùng (theo vai trò), khóa học (theo trạng thái), lượt ghi danh, số bài nộp theo verdict, độ dài hàng đợi và thời gian chấm trung bình. |

### 4.5 Ghi danh và học tập

| ID | Yêu cầu |
|---|---|
| FR-23 | Người học ghi danh vào khóa học đã xuất bản (không phải khóa của chính mình); xem danh sách khóa học đã ghi danh; hủy ghi danh (tiến độ và bài nộp được giữ lại). |
| FR-24 | Người đã ghi danh truy cập toàn bộ nội dung khóa học; người chưa ghi danh chỉ truy cập mục học xem thử. |
| FR-25 | Người học đánh dấu hoàn thành mục TEXT/VIDEO và xem tiến độ khóa học (§3.5). |

### 4.6 Môi trường thực hành và chấm bài

| ID | Yêu cầu |
|---|---|
| FR-26 | Giao diện soạn code trên trình duyệt (Monaco): tô màu cú pháp, chọn ngôn ngữ, khôi phục mã khởi tạo, **tự động lưu nháp** theo từng bài tập. |
| FR-27 | Người học **chạy thử** code với test mẫu hoặc đầu vào tùy chọn và xem stdout, stderr, thời gian, bộ nhớ (không tạo bài nộp). |
| FR-28 | Người học **nộp bài**; hệ thống đưa vào hàng đợi, chấm bất đồng bộ và trả về verdict cùng điểm. |
| FR-29 | Người học xem kết quả từng test case theo quy tắc hiển thị công khai/ẩn (§3.3) và thông báo lỗi biên dịch/chạy. |
| FR-30 | Người học xem lịch sử bài nộp của mình theo từng bài tập, kèm mã nguồn đã nộp. |
| FR-31 | Hệ thống giới hạn tần suất chạy thử và nộp bài theo người dùng (§6). |
| FR-32 | Hệ thống tự phục hồi bài nộp bị kẹt (§3.3). Giảng viên (trong khóa học của mình) và admin (toàn hệ thống) xem danh sách bài nộp `INTERNAL_ERROR` và chấm lại từng bài. |

### 4.7 Đánh giá và theo dõi

| ID | Yêu cầu |
|---|---|
| FR-33 | Người học bắt đầu, làm, lưu nháp và nộp bài đánh giá; hệ thống tự nộp khi hết giờ. |
| FR-34 | Hệ thống chấm tự động trắc nghiệm và bài code; người học xem điểm và kết quả theo quy tắc §3.4. |
| FR-35 | Giảng viên xem thống kê khóa học của mình: số người học, tiến độ trung bình, tỉ lệ `ACCEPTED` theo bài tập, điểm trung bình các bài đánh giá, câu hỏi/bài tập có tỉ lệ sai cao. |
| FR-36 | Giảng viên xem danh sách người học và bài nộp trong khóa học của mình. |
| FR-37 | Người học xem bảng tổng hợp cá nhân: khóa học đang học, tiến độ, số bài đã giải, điểm các bài đánh giá. |
| FR-38 | Người học làm mục QUIZ: chọn đáp án, nộp, được chấm ngay, xem điểm và kết quả từng câu, làm lại không giới hạn; mục hoàn thành khi đạt điểm đạt (§3.5). |

---

## 5. Quy tắc nghiệp vụ

### Khóa học và truy cập

| ID | Quy tắc |
|---|---|
| BR-01 | Chỉ khóa học `PUBLISHED` mới được hiển thị công khai và cho phép ghi danh. |
| BR-02 | Giảng viên chỉ được sửa khóa học, bài tập, test case và bài đánh giá thuộc sở hữu của mình. |
| BR-03 | Chỉ admin được duyệt hoặc từ chối khóa học; giảng viên không thể duyệt khóa học của chính mình. |
| BR-04 | Mỗi người dùng chỉ có tối đa một ghi danh cho mỗi khóa học (ràng buộc unique trong CSDL). |
| BR-05 | Nội dung đầy đủ (đề bài, video, test case, đáp án) chỉ dành cho người đã ghi danh, chủ khóa học và admin; ngoại lệ là mục học xem thử của khóa học `PUBLISHED`. Quyền được kiểm tra trên máy chủ theo ID của mục học. |
| BR-06 | Ghi danh vẫn có hiệu lực khi khóa học bị lưu trữ. |
| BR-07 | Người dùng chỉ truy cập bài nộp, tiến độ, kết quả đánh giá của chính mình; giảng viên chỉ xem dữ liệu của người học trong khóa học mình sở hữu; admin chỉ xem bài nộp `INTERNAL_ERROR` để chấm lại (FR-32) và số liệu tổng hợp (FR-22). |

### Chấm bài và an toàn

| ID | Quy tắc |
|---|---|
| BR-08 | Việc chấm điểm chỉ do máy chủ thực hiện; mọi điểm số, verdict hay trạng thái do client gửi lên đều bị bỏ qua. |
| BR-09 | Test case ẩn, lời giải tham chiếu và đáp án đúng **không bao giờ** xuất hiện trong phản hồi API dành cho người học (kể cả trong thông báo lỗi). Ngoại lệ: sau khi người học nộp mục QUIZ, đáp án đúng và giải thích được hiển thị (FR-38). |
| BR-10 | Mã người dùng chỉ được thực thi trong sandbox đạt các ràng buộc ở §3.6; không bao giờ chạy trong tiến trình của máy chủ API. |
| BR-11 | Một bài nộp chỉ được chấm một lần cho mỗi lần nộp; chấm lại phải tạo bản ghi kết quả mới có ghi nhận người thực hiện. |
| BR-12 | Điểm bài tập của người học là điểm cao nhất trong các lần nộp; mục CODING hoàn thành khi có bài nộp `ACCEPTED`. |
| BR-13 | Bài nộp bị từ chối nếu mã nguồn vượt giới hạn kích thước hoặc ngôn ngữ không được bật cho bài tập đó. |
| BR-14 | Người học không được nộp vượt giới hạn tần suất; vượt giới hạn trả về lỗi 429. |

### Đánh giá

| ID | Quy tắc |
|---|---|
| BR-15 | Thời gian làm bài đánh giá do đồng hồ máy chủ quyết định; nội dung nộp sau thời điểm hết hạn (cộng thời gian du di tối đa 10 giây) bị bỏ qua. |
| BR-16 | Số lần làm bài đánh giá không vượt quá cấu hình; chỉ một lần làm `IN_PROGRESS` tại một thời điểm. |
| BR-17 | Đáp án đúng của **bài đánh giá** chỉ được hiển thị theo quy tắc §3.4. Quy tắc này không áp dụng cho mục QUIZ (xem ngoại lệ ở BR-09). |
| BR-18 | Câu một đáp án đúng khi chọn đúng đáp án; câu nhiều đáp án đúng khi chọn chính xác tập đáp án đúng; không chấm điểm từng phần. Điểm mục QUIZ và phần trắc nghiệm của bài đánh giá bằng phần trăm số câu đúng (hoặc theo điểm từng câu). |
| BR-19 | Điểm bài đánh giá là điểm cao nhất các lần làm. Code trong bài đánh giá không tạo bài nộp ở lịch sử bài tập và không ảnh hưởng BR-12 hay tiến độ mục CODING. |
| BR-20 | Bài đánh giá đã có lần làm thì khóa nội dung và cấu hình, chỉ cho gia hạn ngày đóng. Sửa hoặc xóa mục QUIZ, CODING gốc không ảnh hưởng bài đánh giá đã tạo. |

---

## 6. Yêu cầu phi chức năng

### Bảo mật

| ID | Yêu cầu |
|---|---|
| NFR-01 | Mật khẩu được băm bằng bcrypt (cost ≥ 10) hoặc argon2; độ dài tối thiểu 8 ký tự. |
| NFR-02 | Endpoint được bảo vệ phải kiểm tra xác thực và phân quyền ở phía máy chủ. |
| NFR-03 | Toàn bộ dữ liệu đầu vào API được kiểm tra bằng Zod trước khi xử lý. |
| NFR-04 | Bí mật (khóa JWT, thông tin CSDL) lưu trong biến môi trường, không đưa vào Git; có sẵn `.env.example`. |
| NFR-05 | **Token:** JWT access token ngắn hạn (≈15 phút) kèm refresh token trong cookie `httpOnly`; đăng xuất thu hồi refresh token; máy chủ kiểm tra cờ `isActive` ở mỗi request. |
| NFR-06 | Giới hạn tần suất cho đăng nhập/đăng ký (ví dụ 10 lần/phút/IP), chạy thử (ví dụ 10 lần/phút/người dùng) và nộp bài (ví dụ 5 lần/phút/người dùng). Cấu hình CORS theo origin của frontend; bật security headers (Helmet). |
| NFR-07 | **Sandbox:** đáp ứng đầy đủ §3.6; runner chạy tách biệt khỏi máy chủ API và CSDL, không có quyền truy cập secret hay mạng nội bộ. |
| NFR-08 | Nội dung Markdown của đề bài và bài giảng được làm sạch (sanitize) để chống XSS. |

### Hiệu năng và độ tin cậy

| ID | Yêu cầu |
|---|---|
| NFR-09 | API nộp bài phản hồi trong vòng 500 ms (chỉ tạo bản ghi và đưa vào hàng đợi). |
| NFR-10 | Với bài tập nhỏ (≤ 10 test, mỗi test ≤ 1 giây), có kết quả chấm trong vòng 10 giây ở điều kiện tải bình thường (mục tiêu demo ≥ 20 bài nộp đồng thời). |
| NFR-11 | Hàng đợi chấm bài có thể mở rộng bằng cách tăng số worker mà không đổi mã nguồn; công việc chấm bài **idempotent** và có cơ chế retry giới hạn. |
| NFR-12 | Các thao tác nghiệp vụ quan trọng (ghi danh, cập nhật kết quả bài nộp, bắt đầu/nộp bài đánh giá) dùng transaction CSDL khi cần. |
| NFR-13 | Ràng buộc toàn vẹn: unique `(userId, courseId)` cho ghi danh; unique `(userId, lessonId)` cho tiến độ; khóa ngoại đầy đủ; điểm số không âm. |

### Chất lượng API và vận hành

| ID | Yêu cầu |
|---|---|
| NFR-14 | Các endpoint danh sách có phân trang (mặc định 10, tối đa 50) kèm tổng số bản ghi. |
| NFR-15 | Lỗi theo định dạng thống nhất: `{ "error": { "code": "SUBMISSION_RATE_LIMITED", "message": "...", "details": [...] } }` với mã HTTP phù hợp. |
| NFR-16 | Tài liệu OpenAPI/Swagger tại `/api/docs`. |
| NFR-17 | Thay đổi CSDL quản lý bằng migration Prisma có phiên bản. |
| NFR-18 | Log có cấu trúc cho request, lỗi và từng lần chấm bài (id bài nộp, verdict, thời gian); không ghi mật khẩu hay token. |
| NFR-19 | Dự án chạy được cục bộ theo tài liệu với Docker Compose và dữ liệu mẫu: 1 admin, 2 giảng viên, 3 người học, danh mục, khóa học ở nhiều trạng thái, ít nhất 5 bài tập code (Python/JS/C++) có test case công khai và ẩn, 1 bài đánh giá. |
| NFR-20 | **Kiểm thử:** unit và integration test cho verdict của bộ chấm (đúng, sai, lỗi biên dịch, quá thời gian, quá bộ nhớ), phân quyền, BR-05, BR-09, BR-12, BR-15; có kiểm thử sandbox với mã độc mẫu (vòng lặp vô hạn, fork bomb, truy cập mạng, đọc file hệ thống). Chạy bằng một lệnh được tài liệu hóa. |

---

## 7. Ngoài phạm vi

Các mục sau **không** nằm trong MVP:

- Thanh toán, bán khóa học, mã giảm giá, chứng chỉ
- Phát trực tiếp, hội thảo video, chat thời gian thực
- Giám sát thi bằng camera, phát hiện đạo văn bằng AI, chống gian lận nâng cao
- Chấm điểm bằng AI, gợi ý khóa học bằng AI, trợ lý AI hỗ trợ sửa lỗi code
- Thi đấu lập trình (contest), bảng xếp hạng toàn hệ thống
- IDE nhiều file, quản lý dự án, terminal tương tác, debugger
- Môi trường cho framework đầy đủ (web server, cơ sở dữ liệu trong sandbox)
- Tải tệp video lên hệ thống (chỉ dùng liên kết ngoài)
- Ứng dụng di động gốc
- Đánh giá/xếp hạng khóa học, diễn đàn thảo luận
- Email xác minh, quên mật khẩu, thông báo email
- Nhiều vai trò trên một tài khoản

---

## 8. Tiêu chí chấp nhận

### Truy cập và khám phá

| ID | Tiêu chí |
|---|---|
| AC-01 | Khách xem được danh sách khóa học đã xuất bản nhưng không truy cập được nội dung mục học không xem thử. |
| AC-02 | Khóa học không ở trạng thái `PUBLISHED` không xuất hiện trong danh sách, tìm kiếm hay chi tiết công khai. |
| AC-03 | Tìm kiếm, lọc, sắp xếp và phân trang trả kết quả đúng và tôn trọng giới hạn kích thước trang. |

### Quản lý nội dung

| ID | Tiêu chí |
|---|---|
| AC-04 | Giảng viên tạo được khóa học có bài tập code và test case (công khai và ẩn), rồi gửi duyệt. |
| AC-05 | Giảng viên không sửa được khóa học, bài tập hay test case của giảng viên khác (403). |
| AC-06 | Khóa học thiếu mục học, hoặc có bài code chưa có test case ẩn, không gửi duyệt được. |
| AC-07 | Admin duyệt khóa học (thành `PUBLISHED`) hoặc từ chối kèm lý do mà giảng viên xem được. |
| AC-08 | Giảng viên không thể duyệt khóa học của chính mình. |

### Học tập và thực hành

| ID | Tiêu chí |
|---|---|
| AC-09 | Người học ghi danh khóa học đã xuất bản đúng một lần; ghi danh lặp không tạo bản ghi trùng. |
| AC-10 | Giảng viên không ghi danh được vào khóa học của chính mình. |
| AC-11 | Người chưa ghi danh không đọc được đề bài, video hay test case của mục không xem thử khi đoán ID hoặc URL. |
| AC-12 | Người học viết code trên trình duyệt, chạy thử và thấy stdout/stderr; chạy thử không tạo bài nộp. |
| AC-13 | Nháp code được tự động lưu và khôi phục khi mở lại bài tập. |
| AC-14 | Khóa học đã lưu trữ vẫn truy cập được với người đã ghi danh. |

### Chấm bài

| ID | Tiêu chí |
|---|---|
| AC-15 | Lời giải đúng cho verdict `ACCEPTED`; lời giải sai một phần cho `PARTIAL` hoặc `WRONG_ANSWER` với điểm tương ứng trọng số. |
| AC-16 | Mã có lỗi cú pháp trả `COMPILE_ERROR` kèm thông báo lỗi; mã ném exception trả `RUNTIME_ERROR`. |
| AC-17 | Vòng lặp vô hạn trả `TIME_LIMIT_EXCEEDED`; cấp phát bộ nhớ quá mức trả `MEMORY_LIMIT_EXCEEDED`; máy chủ vẫn hoạt động bình thường. |
| AC-18 | Mã cố truy cập mạng, đọc file ngoài thư mục cho phép hoặc tạo quá nhiều tiến trình bị chặn và không ảnh hưởng hệ thống. |
| AC-19 | Điểm, verdict hoặc trạng thái do client gửi lên bị bỏ qua; kết quả luôn do máy chủ tính. |
| AC-20 | Phản hồi API cho người học không chứa dữ liệu test ẩn, lời giải tham chiếu hay đáp án đúng. |
| AC-21 | Nộp bài trả về ngay trạng thái `QUEUED`, sau đó kết quả cập nhật trên giao diện mà không cần tải lại trang. |
| AC-22 | Vượt giới hạn tần suất nộp bài nhận lỗi 429. |
| AC-23 | Bài nộp kẹt ở `RUNNING` quá thời gian tối đa được chuyển `INTERNAL_ERROR`; bài `QUEUED` kẹt được đưa lại hàng đợi, vượt số lần cho phép thì `INTERNAL_ERROR`; giảng viên (khóa của mình) và admin chấm lại được. |
| AC-24 | Mục CODING được tính hoàn thành khi có ít nhất một bài nộp `ACCEPTED`; tiến độ khóa học hiển thị đúng. |

### Đánh giá

| ID | Tiêu chí |
|---|---|
| AC-25 | Người học làm bài đánh giá có giới hạn thời gian; hết giờ hệ thống tự nộp bài đã lưu. |
| AC-26 | Nội dung gửi sau khi hết hạn (quá thời gian du di) bị bỏ qua. |
| AC-27 | Người học không bắt đầu được lần làm mới khi đã hết số lần cho phép, hoặc khi đang có một lần `IN_PROGRESS`. |
| AC-28 | Đáp án đúng không hiển thị trước khi bài đánh giá được `GRADED` và theo cấu hình. |

### Tài khoản và quản trị

| ID | Tiêu chí |
|---|---|
| AC-29 | Người dùng không xem được bài nộp, tiến độ hay kết quả của người khác; giảng viên chỉ xem được người học trong khóa học của mình. |
| AC-30 | Tài khoản bị vô hiệu hóa không đăng nhập được và token cũ bị từ chối. |
| AC-31 | Đăng ký không tạo được tài khoản admin. |
| AC-32 | Admin không tự vô hiệu hóa mình hoặc quản trị viên hoạt động cuối cùng. |
| AC-33 | Thống kê của admin và giảng viên khớp với số liệu trong CSDL. |

### Bàn giao

| ID | Tiêu chí |
|---|---|
| AC-34 | Có thể cài đặt và demo toàn bộ hệ thống chỉ bằng hướng dẫn trong README với dữ liệu mẫu. |
| AC-35 | Bộ kiểm thử tự động (gồm kiểm thử sandbox) chạy thành công bằng một lệnh được tài liệu hóa. |
| AC-36 | Người học nộp mục QUIZ nhận điểm và kết quả từng câu ngay; điểm và đúng/sai do client gửi bị bỏ qua. |
| AC-37 | Mục QUIZ hoàn thành khi đạt điểm đạt; làm lại với điểm thấp hơn không làm mất trạng thái hoàn thành. |
| AC-38 | Câu hỏi không hợp lệ (dưới 2 lựa chọn, không có đáp án đúng, câu một đáp án có nhiều đáp án đúng) không lưu được. |
| AC-39 | Bài đánh giá chỉ chứa câu hỏi và bài tập hợp lệ; sau khi có lần làm chỉ gia hạn được ngày đóng; sửa mục học gốc không ảnh hưởng bài đánh giá. |
| AC-40 | Điểm bài đánh giá là điểm cao nhất; code trong bài đánh giá không đổi tiến độ hay điểm mục CODING. |
| AC-41 | Người dùng (cả Admin) xem và sửa được hồ sơ, đổi mật khẩu với mật khẩu cũ đúng, và đăng xuất thu hồi phiên. |
| AC-42 | Admin tạo, đổi tên danh mục, xóa danh mục chưa dùng, bật/tắt ngôn ngữ lập trình; thao tác sai bị từ chối với thông báo rõ. |
| AC-43 | Lưu khóa học `PUBLISHED` bị từ chối nếu bài CODING mất test ẩn hoặc lời giải tham chiếu không còn đạt, hoặc mục QUIZ không còn câu hỏi hợp lệ. |
| AC-44 | Verdict cuối tuân theo quy tắc ưu tiên §3.3; điểm bằng tổng trọng số các test đạt. |
| AC-45 | Chủ khóa học và admin xem được nội dung đầy đủ của khóa học; người chưa ghi danh vẫn không xem được (AC-11). |
---

## 9. Ma trận truy vết

| Tiêu chí | Yêu cầu chức năng | Quy tắc / NFR |
|---|---|---|
| AC-01 | FR-07, FR-24 | BR-01, BR-05 |
| AC-02 | FR-07, FR-09 | BR-01 |
| AC-03 | FR-08 | NFR-14 |
| AC-04 | FR-10 – FR-14, FR-17 | BR-02 |
| AC-05 | FR-10 – FR-13 | BR-02, NFR-02 |
| AC-06 | FR-17 | §3.2 |
| AC-07 | FR-18, FR-17 | BR-03 |
| AC-08 | FR-18 | BR-03 |
| AC-09 | FR-23 | BR-04, NFR-13 |
| AC-10 | FR-23 | §2 |
| AC-11 | FR-24 | BR-05, BR-09, NFR-02 |
| AC-12 | FR-26, FR-27 | §3.3 |
| AC-13 | FR-26 | — |
| AC-14 | FR-24, FR-19 | BR-06 |
| AC-15 | FR-28, FR-29 | BR-08, BR-12 |
| AC-16 | FR-28, FR-29 | §3.3 |
| AC-17 | FR-28 | BR-10, NFR-07 |
| AC-18 | FR-28 | BR-10, NFR-07 |
| AC-19 | FR-28 | BR-08 |
| AC-20 | FR-29 | BR-09 |
| AC-21 | FR-28 | NFR-09, NFR-11 |
| AC-22 | FR-31 | BR-14, NFR-06 |
| AC-23 | FR-32 | §3.3, BR-07, BR-11, NFR-11 |
| AC-24 | FR-25, FR-28 | BR-12 |
| AC-25 | FR-33 | BR-15 |
| AC-26 | FR-33 | BR-15 |
| AC-27 | FR-33 | BR-16 |
| AC-28 | FR-34 | BR-17 |
| AC-29 | FR-30, FR-36, FR-37 | BR-07 |
| AC-30 | FR-04 | NFR-05 |
| AC-31 | FR-01, FR-03 | NFR-02 |
| AC-32 | FR-06 | — |
| AC-33 | FR-22, FR-35 | — |
| AC-34 | — | NFR-16, NFR-19 |
| AC-35 | — | NFR-20 |
| AC-36 | FR-38 | BR-08, BR-09, BR-18 |
| AC-37 | FR-38, FR-25 | §3.5 |
| AC-38 | FR-15 | BR-18 |
| AC-39 | FR-16 | BR-02, BR-20 |
| AC-40 | FR-34 | BR-12, BR-19 |
| AC-41 | FR-02, FR-05 | NFR-05 |
| AC-42 | FR-20, FR-21 | — |
| AC-43 | FR-10, FR-14, FR-15 | §3.2 |
| AC-44 | FR-28, FR-29 | §3.3 |
| AC-45 | FR-24, FR-18 | BR-05 |
---

## 10. Câu hỏi mở

Các điểm cần quyết định thêm; mặc định ở trên cho phép bắt đầu phát triển.

1. Dùng **Judge0 tự host** (nhanh triển khai, hỗ trợ nhiều ngôn ngữ) hay **tự xây runner bằng Docker** (kiểm soát hơn, chứng minh kỹ thuật tốt hơn cho đồ án)?
2. Nên hỗ trợ chấm lại tự động toàn bộ bài nộp cũ khi giảng viên sửa test case không?
3. Có cần bài tập dạng **điền vào chỗ trống/sửa lỗi code** ngoài viết hàm đầy đủ không?
4. Cách chấm so sánh đầu ra: so khớp chính xác, bỏ qua khoảng trắng cuối dòng, hay hỗ trợ checker tùy chỉnh?
5. Giảng viên bị vô hiệu hóa thì các khóa học `PUBLISHED` của họ được giữ nguyên, lưu trữ hay chuyển giảng viên khác?
6. Người học hủy ghi danh khi đang có lần làm bài đánh giá `IN_PROGRESS`: từ chối hủy hay hủy luôn lần làm?
7. Khi gửi duyệt, hệ thống chạy lại lời giải tham chiếu hay dùng kết quả kiểm chứng đã lưu?
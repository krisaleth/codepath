# Backlog

> File này được sinh tự động bởi `tools/generate_backlog.py` từ `use-case.md` và `requirements.md`. Không sửa tay: sửa tài liệu nguồn rồi chạy lại công cụ.

Tổng cộng 43 mục. Tạo issue lên GitHub bằng `python tools/create_issues.py --apply` (mặc định chỉ chạy thử).

## M0 Tài liệu và thiết lập repo

Chốt quyết định, ERD, đặc tả API, kế hoạch kiểm thử.

| Mục | Nhãn |
|---|---|
| Chốt các câu hỏi mở ở requirements §10 và ghi ADR | type:decision |
| Chốt giấy phép và chế độ hiển thị repo | type:decision |
| Lập kế hoạch kiểm thử theo tiêu chí chấp nhận | type:docs |
| Thiết kế ERD | type:docs |
| Đặc tả API (OpenAPI) | type:docs |

## M1 Lát cắt dọc chấm bài

Nộp bài, hàng đợi, sandbox, verdict: giảm rủi ro kỹ thuật lớn nhất (UC-09, UC-25, UC-27).

| Mục | Nhãn |
|---|---|
| Dựng khung monorepo và Docker Compose | type:infra |
| Spike sandbox: chạy Python trong container cô lập | type:spike |
| UC-08 — Chạy thử code | type:feature, area:learner |
| UC-09 — Nộp bài và xem kết quả chấm | type:feature, area:learner |
| UC-25 — Chấm bài tự động | type:feature, area:system |
| UC-27 — Chạy mã trong sandbox | type:feature, area:system |

## M2 Khóa học và học tập

Tài khoản, khóa học, nội dung, ghi danh, học và kiểm duyệt.

| Mục | Nhãn |
|---|---|
| UC-01 — Đăng ký tài khoản | type:feature, area:public |
| UC-02 — Đăng nhập / đăng xuất | type:feature, area:public |
| UC-03 — Xem và cập nhật hồ sơ, đổi mật khẩu | type:feature, area:learner, area:instructor, area:admin |
| UC-04 — Duyệt, tìm kiếm, lọc khóa học | type:feature, area:public, area:learner |
| UC-05 — Xem chi tiết khóa học và mục học xem thử | type:feature, area:public, area:learner |
| UC-06 — Ghi danh và hủy ghi danh khóa học | type:feature, area:learner |
| UC-07 — Học nội dung và đánh dấu hoàn thành | type:feature, area:learner |
| UC-10 — Xem lịch sử bài nộp | type:feature, area:learner |
| UC-12 — Xem tiến độ và bảng tổng hợp cá nhân | type:feature, area:learner |
| UC-13 — Tạo, sửa, xóa khóa học | type:feature, area:instructor |
| UC-14 — Quản lý chương và mục học | type:feature, area:instructor |
| UC-15 — Tạo bài tập code và quản lý test case | type:feature, area:instructor |
| UC-17 — Gửi khóa học để duyệt | type:feature, area:instructor |
| UC-20 — Duyệt hoặc từ chối khóa học | type:feature, area:admin |
| UC-28 — Kiểm tra điều kiện gửi duyệt | type:feature, area:system |

## M3 Đánh giá và quản trị

QUIZ, bài đánh giá, chấm lại, phục hồi, thống kê, quản trị.

| Mục | Nhãn |
|---|---|
| UC-11 — Làm bài đánh giá | type:feature, area:learner |
| UC-16 — Tạo mục QUIZ và soạn câu hỏi | type:feature, area:instructor |
| UC-18 — Xem thống kê khóa học và bài nộp của người học | type:feature, area:instructor |
| UC-19 — Chấm lại bài nộp | type:feature, area:instructor, area:admin |
| UC-21 — Gỡ khóa học xuống (lưu trữ) | type:feature, area:admin |
| UC-22 — Quản lý người dùng | type:feature, area:admin |
| UC-23 — Quản lý danh mục và ngôn ngữ lập trình | type:feature, area:admin |
| UC-24 — Xem thống kê hệ thống | type:feature, area:admin |
| UC-26 — Tự nộp bài khi hết giờ và phục hồi bài nộp bị kẹt | type:feature, area:system |
| UC-29 — Làm mục học QUIZ | type:feature, area:learner |
| UC-30 — Tạo và cấu hình bài đánh giá | type:feature, area:instructor |

## M4 Kiểm thử, đóng gói, báo cáo

Kiểm thử tự động, kiểm thử sandbox, dữ liệu mẫu, tài liệu, báo cáo.

| Mục | Nhãn |
|---|---|
| Bộ kiểm thử tự động theo tiêu chí chấp nhận | type:test |
| Dữ liệu mẫu và chạy hệ thống bằng Docker Compose | type:infra |
| Hoàn thiện báo cáo đồ án | type:report |
| Kiểm thử sandbox với mã độc mẫu | type:test |
| Kiểm thử tải: 20 bài nộp đồng thời | type:test |
| Tài liệu OpenAPI tại /api/docs và hướng dẫn cài đặt | type:docs |

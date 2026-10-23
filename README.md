# CodePath

[![Docs](https://github.com/krisaleth/codepath/actions/workflows/docs.yml/badge.svg)](https://github.com/krisaleth/codepath/actions/workflows/docs.yml)

Nền tảng học lập trình trực tuyến tích hợp môi trường thực hành và đánh giá: người học viết và chạy mã ngay trên trình duyệt, nộp bài để được chấm tự động, và làm các bài đánh giá có giới hạn thời gian. Giảng viên tạo nội dung và theo dõi kết quả, quản trị viên kiểm duyệt khóa học.

Đề tài đồ án tốt nghiệp: *Phát triển nền tảng học lập trình trực tuyến tích hợp môi trường thực hành và đánh giá CodePath*.

## Trạng thái

| Hạng mục | Tình trạng |
|---|---|
| Phân tích yêu cầu, use case, sơ đồ trạng thái, sơ đồ tuần tự | Đã có, phiên bản 1.1 (thư mục `docs/`) |
| ERD, đặc tả API | Chưa có (milestone M0) |
| Mã nguồn, Docker Compose | Chưa có, bắt đầu từ milestone M1 |

Dự án đang ở giai đoạn tài liệu. Chưa có mã nguồn chạy được.

## Tính năng dự kiến (MVP)

- Bốn vai trò: khách, người học, giảng viên, quản trị viên.
- Khóa học theo chương và mục học (văn bản, video, bài tập code, trắc nghiệm), có quy trình gửi duyệt và kiểm duyệt.
- Soạn code, chạy thử và nộp bài trên trình duyệt với Python 3, JavaScript và C++17.
- Chấm bài tự động bất đồng bộ bằng test case công khai và ẩn, chạy trong môi trường cô lập.
- Bài đánh giá có giới hạn thời gian, tự nộp khi hết giờ; theo dõi tiến độ và thống kê.

Phạm vi đầy đủ và các nội dung nằm ngoài phạm vi: xem [docs/requirements.md](docs/requirements.md).

## Công nghệ

| Tầng | Công nghệ |
|---|---|
| Frontend | React, TypeScript, Vite, Monaco Editor |
| Backend | Node.js, Express, TypeScript, Zod |
| Dữ liệu | PostgreSQL, Prisma |
| Hàng đợi chấm bài | Redis, BullMQ |
| Môi trường chạy mã | Docker sandbox tự xây hoặc Judge0 tự lưu trữ (chưa chốt, xem [ADR-0001](docs/adr/0001-sandbox-judge0-hay-docker.md)) |
| Đóng gói | Docker Compose |

## Cấu trúc repo

```text
.
├── docs/            Tài liệu phân tích, thiết kế, ADR và backlog
├── tools/           Công cụ kiểm tra tài liệu và tạo backlog
├── .github/         CI, mẫu issue và pull request
├── apps/            (kế hoạch) web, api
└── packages/        (kế hoạch) judge-worker
```

## Tài liệu

Đọc theo thứ tự trong [docs/README.md](docs/README.md). Nguồn chuẩn là [docs/requirements.md](docs/requirements.md).

## Kiểm tra tài liệu

Chạy từ thư mục gốc, cần Python 3:

```bash
python tools/check_docs.py --strict     # truy vết FR, BR, AC, UC; phiên bản; liên kết
python tools/generate_backlog.py --check
```

Kiểm tra sơ đồ Mermaid cần `npm install -g @mermaid-js/mermaid-cli`, rồi chạy `python tools/check_mermaid.py`. CI chạy cả ba kiểm tra này cho mỗi pull request đụng đến tài liệu.

## Lộ trình

| Milestone | Nội dung |
|---|---|
| M0 | Chốt quyết định, ERD, đặc tả API, kế hoạch kiểm thử |
| M1 | Lát cắt dọc chấm bài: nộp bài, hàng đợi, sandbox, verdict |
| M2 | Tài khoản, khóa học, học tập, kiểm duyệt |
| M3 | QUIZ, bài đánh giá, chấm lại, quản trị |
| M4 | Kiểm thử, dữ liệu mẫu, đóng gói, báo cáo |

Chi tiết từng mục: [docs/backlog.md](docs/backlog.md).

## Quy ước làm việc

- Nhánh `main` luôn đạt kiểm tra tài liệu. Làm việc trên nhánh `feat/...`, `fix/...`, `docs/...` rồi gộp bằng pull request.
- Commit theo dạng `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Đổi hành vi hệ thống thì sửa tài liệu trước, ghi vào [docs/CHANGELOG.md](docs/CHANGELOG.md).
- Không commit file `.env` thật hay file báo cáo `.docx`.

## Giấy phép

Chưa xác định.

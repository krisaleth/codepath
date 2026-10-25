# ADR-0001 — Môi trường chạy mã: Judge0 tự lưu trữ hay runner Docker tự xây

| | |
|---|---|
| **Trạng thái** | Đề xuất, chờ kết quả spike sandbox ở M1 |
| **Ngày** | 25/10/2026 |
| **Nguồn câu hỏi** | `requirements.md` §10, câu 1 |
| **Yêu cầu liên quan** | BR-10, BR-13, NFR-07, NFR-10, NFR-20, §3.6, AC-16, AC-17, AC-18 |
| **Use case liên quan** | UC-08, UC-09, UC-15, UC-25, UC-27 |
| **Sơ đồ liên quan** | [sequence-diagram.md](../sequence-diagram.md) mục 2.1, 5, 10.2 |

> Dữ kiện về Judge0 trong tài liệu này được kiểm tra ngày 25/10/2026 (nguồn ở mục 9). Phần đánh giá phương án tự xây là thiết kế của nhóm, chưa được đo thực tế; mục 7 nêu cách đo.

## 1. Bối cảnh

Mã của người học là mã không đáng tin cậy và được chạy ở ba nơi, đều qua UC-27: chạy thử (UC-08), chấm bài (UC-25) và kiểm tra lời giải tham chiếu của giảng viên (UC-15). Mỗi lần chạy phải thỏa §3.6:

| Ràng buộc | Mặc định MVP |
|---|---|
| Cô lập | Container riêng cho mỗi lần chạy, hủy sau khi chạy xong |
| Mạng | Tắt hoàn toàn |
| Người dùng trong container | Không phải root, filesystem chỉ đọc trừ thư mục tạm |
| Thời gian CPU | Tối đa 2 giây mỗi test, cấu hình theo bài tối đa 10 giây |
| Bộ nhớ | Tối đa 256 MB, cấu hình theo bài tối đa 512 MB |
| Số tiến trình | Giới hạn để chặn fork bomb |
| Kích thước đầu ra và mã nguồn | Tối đa 64 KB mỗi loại |

Các yêu cầu khác ảnh hưởng đến lựa chọn:

- **NFR-07:** runner chạy tách biệt khỏi máy chủ API và cơ sở dữ liệu, không có quyền truy cập secret hay mạng nội bộ.
- **NFR-10:** bài nhỏ (tối đa 10 test, mỗi test tối đa 1 giây) có kết quả trong 10 giây; mục tiêu demo là 20 bài nộp đồng thời.
- **NFR-20, AC-17, AC-18:** phải có kiểm thử với mã độc mẫu (vòng lặp vô hạn, fork bomb, truy cập mạng, đọc file hệ thống), và máy chủ vẫn hoạt động bình thường sau mỗi mẫu.
- **Ngôn ngữ MVP:** Python 3, JavaScript và C++17.
- **Cơ sở dữ liệu:** dự án dùng Cloud Firestore (requirements §1.2), không có PostgreSQL.
- **BR-09:** test ẩn và lời giải tham chiếu không được lộ ra ngoài hệ thống.

## 2. Các tiêu chí quyết định

1. Đáp ứng đúng §3.6 và NFR-07 về cô lập.
2. Bề mặt tấn công và công sức giữ an toàn về lâu dài.
3. Công sức dựng và độ trễ mỗi lần chạy, so với NFR-10.
4. Phụ thuộc hạ tầng thêm, nhất là khi đã chọn Firestore.
5. Tự chọn được phiên bản Python, Node.js và GCC.
6. Dễ đổi phương án sau này.

## 3. Các phương án

### Phương án A — Judge0 CE tự lưu trữ

Triển khai Judge0 bằng Docker Compose và gọi qua API của nó. Đây là phương án có sẵn nhiều ngôn ngữ và ít việc nhất.

**Dữ kiện đã kiểm tra**

- Bản phát hành mới nhất trên trang releases là Judge0 CE v1.13.1, ngày 18/04/2024.
- Các bản từ 1.13.0 trở về trước có 3 lỗ hổng nghiêm trọng cho phép thoát khỏi sandbox (CVE-2024-28185, CVE-2024-28189, CVE-2024-29021), đã được vá ở 1.13.1. Tác giả báo cáo cho rằng nguyên nhân gốc, việc Judge0 ghi file và chạy lệnh trên máy chủ ngoài vùng `isolate`, vẫn còn.
- Judge0 chạy trong Docker với `--privileged` để `isolate` truy cập được các thành phần của máy chủ.
- Judge0 cần cgroup v1. Trên hệ thống dùng cgroup v2 (mặc định của Ubuntu 22.04 trở lên) phải ép về v1 bằng tham số kernel `systemd.unified_cgroup_hierarchy=0`. Issue [#543](https://github.com/judge0/judge0/issues/543) yêu cầu hỗ trợ cgroup v2; trong nội dung đã đọc không có phản hồi chính thức của người bảo trì.
- Judge0 có cơ sở dữ liệu PostgreSQL nội bộ riêng. Tùy chọn `enable_network` tồn tại và theo bài viết của Tanto Security đang bật theo mặc định, nên phải tắt để thỏa §3.6.

**Ưu điểm**

- Dựng nhanh khi máy chủ đáp ứng cgroup v1; không phải tự viết bộ chạy mã.
- Có sẵn nhiều ngôn ngữ và API ghi nhận kết quả.
- Dùng `isolate`, một sandbox đã được dùng rộng rãi.

**Nhược điểm và rủi ro**

- Không khớp nguyên văn §3.6: `isolate` là sandbox cấp tiến trình bên trong một container, không phải một container mới cho mỗi lần chạy. Nếu chọn A phải sửa §3.6 hoặc ghi rõ coi hai cách là tương đương.
- Container `--privileged` và yêu cầu cgroup v1 mâu thuẫn với tinh thần của NFR-07 và làm hẹp môi trường chạy được. Cần kiểm tra máy phát triển của nhóm (ví dụ Windows với Docker Desktop và WSL2) có chạy được không.
- Đưa lại một PostgreSQL vào hệ thống chỉ để phục vụ Judge0, trong khi dự án vừa chọn Firestore.
- Phụ thuộc vào một dự án bên ngoài đã hơn hai năm chưa có bản phát hành mới (theo trang releases), và nó từng có lỗ hổng thoát sandbox.
- Phiên bản Python, Node.js và GCC phụ thuộc vào bản đóng gói; cần kiểm tra có đáp ứng C++17 và phiên bản Node.js còn được hỗ trợ không.

### Phương án B — Runner Docker tự xây

Một dịch vụ runner (worker) nhận yêu cầu theo hợp đồng ở mục 5, tạo một container ngắn hạn cho mỗi lần chạy qua Docker Engine API, thu kết quả rồi hủy container. Mỗi ngôn ngữ có một image riêng.

**Cấu hình container dự kiến** (khớp §3.6)

| Ràng buộc §3.6 | Cách thực hiện |
|---|---|
| Container riêng, hủy sau khi chạy | Tạo mới mỗi lần chạy, xóa ngay khi xong, kể cả khi lỗi |
| Tắt mạng | `--network none` |
| Không root, chỉ đọc | `--user` không đặc quyền, `--read-only`, `--tmpfs` cho thư mục tạm, `--cap-drop ALL`, `--security-opt no-new-privileges` |
| Bộ nhớ | `--memory` kèm `--memory-swap` bằng cùng giá trị để tắt swap; container bị OOM kill thì trả `MEMORY_LIMIT_EXCEEDED` |
| Số tiến trình | `--pids-limit` |
| Thời gian | Giới hạn CPU bằng `--cpus` và một bộ đếm thời gian ở ngoài, hết giờ thì dừng container và trả `TIME_LIMIT_EXCEEDED` |
| Đầu ra 64 KB | Runner đọc luồng đầu ra và cắt ở 64 KB, vượt thì dừng container và trả `OUTPUT_LIMIT_EXCEEDED` |
| Biên dịch (C++) | Một container có quyền ghi để biên dịch, sản phẩm đưa sang container chạy chỉ đọc |

**Ưu điểm**

- Khớp nguyên văn §3.6; cấu hình mỗi cờ đều do nhóm kiểm soát.
- Không thêm PostgreSQL hay ứng dụng bên thứ ba; cùng ngăn xếp TypeScript với phần còn lại.
- Tự chọn phiên bản Python, Node.js, GCC bằng Dockerfile; chỉ cần ba ngôn ngữ.
- Có giá trị kỹ thuật cho đồ án: tự thiết kế và kiểm thử một sandbox.

**Nhược điểm và rủi ro**

- Nhiều việc nhất, và sai sót cấu hình là lỗi bảo mật. Giảm bằng bộ kiểm thử mã độc mẫu (NFR-20), dù cả hai phương án đều cần bộ này.
- **Quyền truy cập Docker là quyền root trên máy chủ.** Không được mount `docker.sock` vào dịch vụ API. Chỉ runner được chạm Docker, và nên chạy trên máy hoặc VM riêng, hoặc dùng Docker rootless, theo NFR-07. Nếu cần cứng hơn có thể thêm gVisor (`runsc`), nằm ngoài MVP.
- Mỗi lần chạy tạo một container nên có độ trễ khởi động; nhân với số test có thể ảnh hưởng NFR-10. Cần đo (mục 7).
- Phải tự phân biệt các loại lỗi: TLE, MLE (OOM kill), lỗi chạy (exit code khác 0), lỗi biên dịch, quá đầu ra. Đo thời gian bằng đồng hồ ngoài gồm cả thời gian khởi động, cần trừ hoặc chọn cách đo khác.

### Không xét: dịch vụ chạy mã của bên thứ ba

Loại ngay vì mã nguồn của người học và test ẩn (BR-09) sẽ bị gửi ra ngoài, hệ thống phụ thuộc mạng và chi phí ngoài, và khó kiểm soát giới hạn theo §3.6.

## 4. So sánh

| Tiêu chí | A. Judge0 CE | B. Runner Docker tự xây |
|---|---|---|
| Khớp §3.6 "container riêng mỗi lần chạy" | Không nguyên văn, dùng `isolate` trong một container | Có |
| Cô lập theo NFR-07 | Container `--privileged`, cần cgroup v1 | Tùy cách đặt runner; cần tách máy hoặc rootless |
| Bề mặt tấn công | Rộng hơn: ứng dụng riêng, từng có 3 lỗ hổng thoát sandbox | Hẹp hơn nếu chỉ runner chạm Docker, nhưng mọi cấu hình do nhóm chịu trách nhiệm |
| Công sức dựng | Thấp hơn nếu máy chủ đáp ứng cgroup v1 | Cao hơn |
| Độ trễ mỗi lần chạy | Có thể thấp hơn vì không tạo container; cần đo | Có khởi động container mỗi lần; cần đo |
| Hạ tầng thêm | PostgreSQL riêng của Judge0 | Docker Engine |
| Chọn phiên bản ngôn ngữ | Theo bản đóng gói | Tự chọn |
| Bảo trì | Phụ thuộc dự án ngoài, bản mới nhất 04/2024 | Nhóm tự bảo trì image và runner |
| Đổi phương án sau này | Dễ nếu có lớp trừu tượng ở mục 5 | Dễ nếu có lớp trừu tượng ở mục 5 |

## 5. Quyết định áp dụng cho cả hai phương án: lớp trừu tượng `SandboxRunner`

Dù chọn phương án nào, mã của API và worker chỉ gọi một giao diện, để việc đổi phương án sau này không động đến UC-08, UC-15, UC-25. Hợp đồng suy ra từ UC-27 và bảng verdict ở §3.3:

| Phần | Nội dung |
|---|---|
| Đầu vào | Ngôn ngữ, mã nguồn (tối đa 64 KB), đầu vào chuẩn, giới hạn (thời gian CPU, bộ nhớ, đầu ra, số tiến trình) |
| Kết quả | Loại kết quả, stdout, stderr, thời gian, bộ nhớ, thông báo biên dịch nếu có |
| Loại kết quả | `OK`, `COMPILE_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `OUTPUT_LIMIT_EXCEEDED`, `INFRA_ERROR` |
| Lỗi hạ tầng | `INFRA_ERROR` do runner không khả dụng; UC-08 hiển thị "hệ thống bận", UC-25 thử lại có giới hạn rồi chuyển `INTERNAL_ERROR` (UC-27 4b) |

Hai điểm còn mở, chốt trong spike:

- Biên dịch một lần rồi chạy nhiều test hay biên dịch trong từng lần chạy (sequence-diagram.md mục 2.3, điểm 4). Giao diện có thể tách thành `compile` và `run` nếu cần.
- Chạy thử và kiểm tra lời giải gọi đồng bộ hay đi qua hàng đợi (sequence-diagram.md mục 5.1 điểm 1 và 10.3 điểm 2).

## 6. Đề xuất

**Chọn phương án B** (runner Docker tự xây) đằng sau `SandboxRunner`, với điều kiện spike ở mục 7 đạt. Lý do:

1. Phương án A cần container `--privileged`, cgroup v1 và một PostgreSQL riêng, đi ngược NFR-07 và ngăn xếp đã chọn; đồng thời nó từng có lỗ hổng thoát sandbox và bản phát hành mới nhất là 04/2024.
2. Phương án B khớp §3.6 nguyên văn và chỉ cần ba ngôn ngữ nên việc tự xây gọn.
3. Đồ án có lợi khi tự thiết kế và kiểm thử sandbox; bộ kiểm thử mã độc vốn đã bắt buộc.

Phương án A phù hợp hơn nếu thời gian rất ngắn và nhóm có sẵn một máy chủ Linux dùng cgroup v1. Chuyển sang A khi spike cho thấy B không đạt các tiêu chí bắt buộc ở mục 7, và máy chạy thật đáp ứng được yêu cầu của Judge0.

Đây là đề xuất, chưa phải quyết định. Quyết định cuối thuộc nhóm thực hiện đồ án.

## 7. Kế hoạch spike (M1, giới hạn 1 đến 2 ngày)

Làm phương án B trước. Chỉ thử A khi B không đạt tiêu chí bắt buộc hoặc khi còn thời gian để so sánh.

| # | Việc cần làm | Cách kiểm tra | Bắt buộc |
|---|---|---|---|
| 1 | Chạy Python 3 với đầu vào chuẩn, giới hạn thời gian và bộ nhớ | Có đầu ra đúng và số đo thời gian, bộ nhớ | Có |
| 2 | Phân loại đúng các kết quả | Vòng lặp vô hạn là `TIME_LIMIT_EXCEEDED`; cấp phát bộ nhớ lớn là `MEMORY_LIMIT_EXCEEDED`; in vô hạn là `OUTPUT_LIMIT_EXCEEDED`; exception là `RUNTIME_ERROR`; C++ sai cú pháp là `COMPILE_ERROR` | Có |
| 3 | Không mạng, không root, chỉ đọc | Gọi mạng ra ngoài thất bại; `id` không phải root; ghi ngoài thư mục tạm thất bại | Có |
| 4 | Hủy container và an toàn sau mẫu độc | Không còn container sau khi chạy; fork bomb không làm máy chủ treo | Có |
| 5 | Không lộ dữ liệu máy chủ | Mã không đọc được biến môi trường hay file của runner và máy chủ | Có |
| 6 | Có đủ ba ngôn ngữ | Python 3, Node.js và C++17 chạy được; ghi lại phiên bản | Có |
| 7 | Đo độ trễ | Thời gian khởi động mỗi lần chạy và tổng thời gian cho bài 10 test; mục tiêu đề xuất dưới 0,5 giây chi phí cố định mỗi lần chạy, điều chỉnh sau khi đo (NFR-10) | Cần ghi lại |
| 8 | Chạy song song | 20 lần chạy đồng thời (mục tiêu demo của NFR-10) không lỗi | Cần ghi lại |
| 9 | Chạy được trên môi trường của nhóm | Kiểm tra trên máy phát triển; với A, kiểm tra cgroup bằng `stat -fc %T /sys/fs/cgroup` (`cgroup2fs` là v2, `tmpfs` là v1) | Có |
| 10 | Quyền truy cập Docker | Xác nhận chỉ runner chạm Docker, API không có `docker.sock` | Có |

### Kết quả spike

| Mục | Phương án | Kết quả | Ghi chú |
|---|---|---|---|
| (chưa chạy) | | | |

## 8. Hệ quả và tài liệu cần cập nhật khi chốt

- Đổi **Trạng thái** của tài liệu này thành "Đã chốt", điền kết quả spike ở mục 7.
- `requirements.md`: §1.2 (hàng "Môi trường chạy code"), bỏ hoặc đánh dấu đã giải quyết §10 câu 1, NFR-19 (dịch vụ trong Docker Compose); nếu chọn A thì sửa cả §3.6 và NFR-07.
- `sequence-diagram.md`: mục 2.3 (điểm 4), 5.1 (điểm 1), 10.3 (điểm 2) theo kết quả spike về biên dịch và gọi đồng bộ hay qua hàng đợi.
- `.env.example`: các biến `SANDBOX_*` giữ nguyên cho B; với A thêm địa chỉ Judge0.
- `README.md`: bảng công nghệ, bỏ chữ "chưa chốt".
- Backlog: task "Spike sandbox" ghi kết quả vào tài liệu này; task "Dựng khung monorepo và Docker Compose" thêm dịch vụ runner (B) hoặc Judge0 cùng PostgreSQL của nó (A).

## 9. Nguồn

- [Judge0, trang releases](https://github.com/judge0/judge0/releases): v1.13.1 (18/04/2024) là bản mới nhất và vá 3 CVE.
- [Judge0, issue #543: hỗ trợ cgroup v2](https://github.com/judge0/judge0/issues/543): cách ép cgroup v1.
- [Tanto Security, lỗ hổng thoát sandbox của Judge0](https://tantosec.com/blog/judge0/): chi tiết CVE, `--privileged`, `enable_network`, PostgreSQL nội bộ.

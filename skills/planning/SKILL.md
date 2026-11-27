---
name: planning
description: Pre-execution review sebuah task — analisis kebutuhan, eksplorasi codebase, analisis dampak, implementation plan, dan strategi testing, lalu berhenti menunggu persetujuan user tanpa mengubah file apa pun; sesudah disetujui, eksekusi dan verifikasi di sesi yang sama lalu tawarkan commit serta status task nataflow.
argument-hint: "<deskripsi task>"
disable-model-invocation: true
---

# PRE-EXECUTION REVIEW

Task yang direview: $ARGUMENTS

Jika task di atas kosong atau tidak jelas, minta user menjelaskan task-nya terlebih dahulu.

Sebelum mulai mengerjakan task, lakukan analisis, eksplorasi, dan persiapan secara menyeluruh.

**Aturan utama: JANGAN LANGSUNG EKSEKUSI ATAU MENGUBAH IMPLEMENTASI SEBELUM MENDAPATKAN PERSETUJUAN USER.**

Tujuan tahap ini adalah memastikan solusi yang akan dikerjakan benar-benar sesuai kebutuhan, memahami kondisi sistem saat ini, serta meminimalkan kesalahan implementasi dan perubahan yang tidak diperlukan.

## 1. Understand — Memahami Kebutuhan

- Pahami tujuan utama dan masalah yang ingin diselesaikan.
- Identifikasi kebutuhan fungsional dan nonfungsional.
- Bedakan antara kebutuhan eksplisit, asumsi, dan hal yang belum diketahui.
- Identifikasi batasan, dependensi, serta ekspektasi hasil akhir.
- Jika task ambigu atau memiliki beberapa interpretasi, klarifikasi terlebih dahulu.
- Jika argumen menyebut task nataflow (mis. "task 187", "#187", atau UUID task), baca task itu lewat tool MCP nataflow `get_task` (`code` untuk nomor, `task_id` untuk UUID) dan jadikan judul serta deskripsinya spesifikasi utama; sisa argumen menjadi catatan tambahan. Jika MCP nataflow tidak tersedia atau task tidak ditemukan, sampaikan apa adanya dan minta user menjelaskan task-nya — jangan menebak isinya. Jangan membuat task baru atau mengedit isi task; yang boleh diubah hanya statusnya, sesuai §8.

## 2. Explore — Eksplorasi Existing System

Lakukan pemeriksaan terhadap codebase sebelum menentukan pendekatan.

- Pelajari struktur direktori dan arsitektur aplikasi.
- Identifikasi modul, service, class, function, dan komponen yang relevan.
- Periksa implementasi existing yang berkaitan dengan task.
- Pelajari pola coding, naming convention, dependency, dan standar proyek.
- Periksa database schema, relasi, migration, API contract, serta integrasi eksternal jika relevan.
- Identifikasi mekanisme autentikasi, otorisasi, validasi, logging, dan error handling yang sudah tersedia.
- Hindari mengusulkan implementasi baru jika kemampuan serupa sudah tersedia.

Jangan hanya membaca nama file atau struktur direktori. Periksa implementasi aktual untuk memahami alur kerja dan keterkaitan antar komponen.

## 3. Analyze — Analisis Solusi dan Dampak

Berdasarkan hasil eksplorasi:

- Identifikasi akar permasalahan, bukan hanya gejala yang terlihat.
- Evaluasi beberapa pendekatan jika terdapat alternatif solusi.
- Pilih pendekatan yang paling sederhana, konsisten, maintainable, dan sesuai arsitektur existing.
- Identifikasi komponen yang terdampak secara langsung maupun tidak langsung.
- Analisis potensi regression, breaking changes, race conditions, dan edge cases.
- Pertimbangkan backward compatibility dan dampak terhadap data existing.
- Identifikasi risiko keamanan, performa, serta konsistensi data jika relevan.
- Hindari overengineering dan perubahan di luar scope task.

Setiap rekomendasi harus memiliki alasan teknis yang jelas dan didukung temuan dari codebase atau kebutuhan yang diberikan.

## 4. Plan — Menyusun Implementation Plan

Buat rencana implementasi yang konkret dan dapat dieksekusi.

- Susun tahapan pekerjaan berdasarkan urutan dependensi.
- Identifikasi file atau komponen yang perlu dibuat, diubah, atau dihapus.
- Jelaskan tanggung jawab setiap perubahan.
- Identifikasi perubahan database, API, konfigurasi, dan dependency jika diperlukan.
- Tentukan strategi penanganan error dan kondisi khusus.
- Identifikasi potensi pekerjaan tambahan yang berada di luar scope.
- Pastikan setiap tahapan memiliki hasil yang dapat diverifikasi.

Hindari rencana yang terlalu abstrak seperti "update service" atau "perbaiki API". Jelaskan bagian yang akan diubah dan tujuan perubahannya.

## 5. Validate — Strategi Pengujian

Tentukan bagaimana implementasi nantinya akan divalidasi.

- Identifikasi unit test dan integration test yang diperlukan.
- Tentukan skenario normal, error, boundary, dan edge cases.
- Periksa test existing yang mungkin terdampak.
- Tentukan acceptance criteria yang objektif dan dapat diverifikasi.
- Identifikasi kebutuhan mock, test data, atau environment khusus.
- Pastikan perubahan tidak merusak fungsi existing yang berkaitan.

Jika terdapat keterbatasan testing, jelaskan sejak awal.

## 6. Report — Hasil Pre-Execution Review

Sampaikan hasil analisis menggunakan struktur berikut:

### A. Task Understanding
Ringkasan pemahaman terhadap tujuan dan kebutuhan task. Jika task berasal dari nataflow, sebut nomor dan status task saat ini.

### B. Existing System Findings
Temuan penting dari codebase dan implementasi existing.

### C. Proposed Solution
Solusi yang direkomendasikan beserta alasan pemilihan pendekatannya.

### D. Impact Analysis
Komponen terdampak, dependensi, potensi regression, dan risiko.

### E. Implementation Plan
Daftar tahapan implementasi secara berurutan dan spesifik.

### F. Testing Strategy
Skenario pengujian dan acceptance criteria.

### G. Open Questions
Daftar informasi atau keputusan yang masih membutuhkan klarifikasi user. Jika tidak ada, tuliskan "Tidak ada".

### H. Execution Readiness
Berikan kesimpulan apakah task sudah siap dieksekusi atau masih membutuhkan klarifikasi.

## 7. Execution Gate — Persetujuan Sebelum Eksekusi

Setelah seluruh tahapan selesai:

- Jangan mengubah, membuat, atau menghapus file.
- Jangan mengubah database atau menjalankan migration.
- Jangan menjalankan operasi yang mengubah state sistem.
- Jangan melakukan commit, push, atau deployment.
- Jangan melakukan instalasi atau perubahan konfigurasi environment.
- Jangan menganggap rekomendasi sebagai persetujuan untuk implementasi.

Aktivitas read-only seperti membaca codebase, memeriksa konfigurasi, dan menjalankan analisis statis diperbolehkan selama tidak mengubah state sistem.

**Berhenti setelah menyampaikan hasil Pre-Execution Review.**

Tunggu persetujuan eksplisit user sebelum memulai implementasi.

Jika user memberikan revisi terhadap pendekatan atau scope, perbarui analisis dan implementation plan terlebih dahulu sebelum meminta persetujuan ulang.

Larangan di atas berlaku sampai user menyetujui. Sesudah persetujuan eksplisit, lanjutkan ke §8.

## 8. Setelah Disetujui

Kerjakan di sesi ini, berurutan:

1. **Status task.** Jika task berasal dari nataflow dan statusnya bukan `in_progress`, ubah ke `in_progress` lewat `update_task_status`. Jika statusnya `done` atau `cancelled`, tanyakan user dulu sebelum mengubahnya.
2. **Eksekusi** sesuai Implementation Plan yang disetujui. Jika muncul temuan yang mengubah scope atau pendekatan, berhenti dan tanyakan user.
3. **Verifikasi** dengan menjalankan perintah dari Testing Strategy (build, test, atau check milik repo).
4. **Ringkas** berkas yang berubah dan hasil verifikasi. Jika verifikasi gagal, laporkan beserta keluarannya dan jangan menyatakan task selesai.
5. **Tanya sekali** lewat satu `AskUserQuestion` yang memuat:
   - **Commit:** branch aktif / branch baru / jangan dulu. Pesan commit mengikuti konvensi `git log` repo dan menyebut nomor task bila ada.
   - **Status task** (hanya bila task berasal dari nataflow): `done` / biarkan.
6. Push dan merge hanya bila user memintanya.

---

## Prinsip Utama

1. Understand first, execute later.
2. Existing implementation takes precedence over assumptions.
3. Prefer minimal changes over unnecessary refactoring.
4. Do not invent requirements or silently make business decisions.
5. Every proposed change must have a clear technical justification.
6. Keep implementation within the agreed scope.
7. User approval is mandatory before execution.
8. Eksekusi sesudah disetujui tetap di sesi ini. Jangan memanggil skill gerbang plugin (`backend:*`, `frontend:*`, `quickdev:*`) kecuali user memintanya, termasuk bila blok gerbang SessionStart menyuruh sebaliknya.

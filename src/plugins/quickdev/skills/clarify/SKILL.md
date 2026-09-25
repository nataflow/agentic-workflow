---
name: clarify
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — klarifikasi celah spesifikasi dari laporan quickdev:explore sebelum quickdev:plan; dipanggil eksplisit lewat /quickdev:clarify.
disable-model-invocation: true
---

## THE IRON LAW

DILARANG MEMBUAT ASUMSI SPESIFIKASI PADA BAGIAN YANG AMBIGU TANPA KONFIRMASI EKSPLISIT DARI USER. KLARIFIKASI WAJIB BERADAPTASI SECARA DINAMIS BERDASARKAN PROFIL ARSITEKTUR REPO (BACKEND BERFOKUS PADA KONTRAK API/DATA, FRONTEND BERFOKUS PADA ALUR UI/UX/STATE). BILA SELURUH KEBUTUHAN TELAH JELAS DAN TERVERIFIKASI 100% DARI HASIL EKSPLORASI, SKILL WAJIB MENGAMBIL JALUR CEPAT (FAST-PATH SKIP) KE TAHAP PERENCANAAN TANPA MENGAJUKAN PERTANYAAN BASA-BASI. DILARANG MELAKUKAN PERUBAHAN ATAU PENULISAN KODE PADA SKILL INI.

## Precondition [REQUIRED]

1. Penelusuran codebase pada `quickdev:explore` telah selesai dengan status terminal `EXPLORED`.
2. Laporan temuan eksplorasi memuat daftar file relevan, alur data (data flow trace), dependensi simbol, dan analisis dampak.
3. Profil repositori pada `profile_path` dianjurkan tersedia untuk menentukan domain backend atau frontend; bila absen, tentukan domain dari `profile_type` dan laporan `explore`, lalu nyatakan bahwa rekomendasi tidak berpijak pada profil.
4. Tool `AskUserQuestion` tersedia untuk pertukaran pertanyaan klarifikasi terstruktur.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backenddev:*` atau `frontenddev:*` sebagai pengganti: `backenddev:profile`/`frontenddev:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backenddev:tech-lead | frontenddev:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi/baris): isi `quickdev` membuat hook SessionStart `backenddev`/`frontenddev` diam; isi `frontenddev quickdev` hanya menyalakan hook `frontenddev`.

## Parameter [REQUIRED]

- `explore_summary` — string — `[REQUIRED]` — ringkasan hasil temuan dari `quickdev:explore` yang mencakup file target, simbol, dan potensi celah spesifikasi; bila pemanggil tidak mengirimnya, ambil dari laporan `quickdev:explore` terakhir di percakapan.
- `profile_type` — string — default `"auto"` — tipe domain klarifikasi (`"backend"`, `"frontend"`, `"auto"`). Jika `"auto"`, membaca tipe dari profil repositori atau konteks file yang dieksplorasi.
- `profile_path` — string — default `"repo-profile.md"` — path profil hasil `quickdev:profile` (bukan `.claude/profile/` milik backenddev/frontenddev); bila tidak ditemukan, gunakan fallback `.dev/profile.md`.
- `skip_if_clear` — boolean — default `true` — bila `true`, melaporkan `SKIPPED` dan menawarkan `quickdev:plan` jika tidak ditemukan ambiguitas atau celah spesifikasi.
- `batch_limit` — integer — default `3` — batas pertanyaan per batch (maksimal 4, batas satu panggilan `AskUserQuestion`).
- `allow_assumptions` — boolean — default `false` — bila `true`, mengizinkan penetapan asumsi teknis terukur jika user mendelegasikan keputusan secara eksplisit.

## Workflow

### Fase 0 — Evaluasi Celah Spesifikasi & Uji Fast-Path Skip

1. Telaah laporan `explore_summary` terhadap permintaan asli pengguna secara komparatif:
   - Evaluasi kelengkapan scope: Apakah seluruh parameter input, logika komputasi, validasi data, dan format output yang diinginkan sudah terdefinisi pasti?
   - Evaluasi kompatibilitas arsitektur: Apakah ada benturan antara pola kode eksisting dengan permintaan fitur baru (contoh: restriksi tipe data, format response standard, atau konvensi state management)?
   - Evaluasi keputusan desain: Apakah terdapat trade-off teknis (seperti pemilihan library, struktur tabel database, atau tata letak visual antarmuka) yang membutuhkan persetujuan stakeholder?
2. Jalankan evaluasi Observable Predicate untuk Fast-Path Skip:
   - **Kondisi A: Tidak Ada Celah / Ambiguitas (Zero Ambiguity)**:
     - Jika seluruh detail teknis telah terbukti pasti dari codebase eksisting dan permintaan user telah lengkap tanpa multitafsir:
     - Set status klarifikasi menjadi `SKIPPED` (Fast-Path Skip).
     - Susun ringkasan konfirmasi spesifikasi terkunci berdasarkan fakta eksplorasi.
     - Laporkan `SKIPPED` dalam satu baris dan tawarkan `quickdev:plan`; jangan memanggilnya sebelum user setuju.
   - **Kondisi B: Ditemukan Celah / Ambiguitas Spesifikasi**:
     - Jika terdapat parameter hilang, kontrak API belum pasti, atau alur UI/UX belum terdefinisi:
     - Masuk ke mode klarifikasi interaktif dinamis pada Fase 1.

### Fase 1 — Penentuan Domain & Adaptasi Klarifikasi Dinamis

1. Tentukan domain klarifikasi berdasarkan parameter `profile_type` dan profil pada `profile_path`:
2. **Cabang Dinamis A — Repositori Backend**:
   - Pusatkan klarifikasi pada kontrak data, endpoint API, integritas database, dan error handling:
     - *URL Routing & HTTP Verbs*: Klarifikasi path endpoint (contoh: `POST /api/v1/orders` vs `POST /api/v1/checkout`), format parameter URL (`:id` vs `?filter=`), dan query filtering/sorting.
     - *Request & Response Payload Schema*: Klarifikasi struktur field JSON, tipe data primitif/nested, validasi field opsional vs wajib, dan pembungkus response envelope (`{ success: true, data: ... }`).
     - *HTTP Status Codes & Error Handling*: Klarifikasi status code pada skenario kegagalan spesifik (misal: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity).
     - *Database & Migration Impacts*: Klarifikasi skema tabel baru, penambahan kolom, index performa, relasi foreign key, cascades, atau perubahan enum values.
     - *Authentication & Authorization Scopes*: Klarifikasi batasan role (RBAC), permission scope, token expiry, dan penanganan tenant context pada header.
3. **Cabang Dinamis B — Repositori Frontend**:
   - Pusatkan klarifikasi pada pengalaman pengguna (UX), desain antarmuka (UI), dan manajemen state:
     - *Alur Navigasi & UX Flow*: Klarifikasi alur transisi antar-halaman, aksi setelah submit form (redirect ke halaman detail vs modal toast notification), tombol kembali/batal, dan deep linking.
     - *Tata Letak & Hierarki Desain UI*: Klarifikasi posisi komponen visual, penggunaan modal dialog vs slide-over drawer vs inline expander, dan urutan prioritas informasi data.
     - *Penanganan Cabang State UI*: Klarifikasi representasi visual tiap cabang state yang dikonvensikan profil (contoh: loading skeleton vs spinner, empty state + CTA, error banner + retry).
     - *Routing & Query Parameters*: Klarifikasi sinkronisasi state URL dengan filter tabel, pencarian instan, pagination cursor, dan status tab aktif.
     - *Form Validation & Interactivity*: Klarifikasi perilaku validasi instan (onBlur vs onSubmit), disable state tombol submit selama request in-flight, dan konfirmasi modal sebelum aksi destruktif.
4. **Cabang Dinamis C — Fullstack / Monorepo**:
   - Jalankan klarifikasi komprehensif yang mencakup integrasi boundary antara API contract backend dan data demand komponen UI frontend.

### Fase 2 — Formulasi Pertanyaan Terarah (Batching & Opsi Konkret)

1. Rancang pertanyaan klarifikasi dalam satu batch terpadu (maksimal `batch_limit` pertanyaan); bila ambiguitas melebihi `batch_limit`, dahulukan yang memblokir rencana dan ajukan sisanya sebagai batch berikutnya setelah jawaban batch pertama dipetakan:
   - Setiap pertanyaan wajib menyertakan konteks teknis temuan dari codebase (menyebut nama file, endpoint, atau fungsi terkait).
   - Setiap pertanyaan wajib memberikan opsi-opsi solusi konkret beserta rekomendasi teknis terbaik bertanda `(Recommended)`.
   - Dilarang mengajukan pertanyaan terbuka yang terlalu abstrak tanpa opsi implementasi nyata.
2. Sajikan batch kepada user lewat `AskUserQuestion`:
   - Tampilkan perbandingan opsi secara jernih beserta pro dan kontra arsitektural.
   - Berikan tanda rekomendasi pada opsi yang paling selaras dengan pola arsitektur di `profile_path`.

### Fase 3 — Sintesis Jawaban & Penguncian Spesifikasi (Alignment Lock)

1. Tangkap seluruh respons dan keputusan yang diberikan oleh user:
   - Petakan setiap jawaban user ke spesifikasi teknis definitif.
   - Jika user memberikan instruksi delegasi eksplisit ("bebas" / "ikuti standar repo"): bila `allow_assumptions: true`, tetapkan konvensi terbaik dari profil dan dokumentasikan sebagai keputusan resmi; bila `false`, tampilkan konvensi terpilih sebagai satu konfirmasi ringkas sebelum dikunci.
2. Susun dokumen spesifikasi kebutuhan terklarifikasi yang mencakup:
   - Ringkasan keputusan kontrak API / skema payload / query database (untuk backend).
   - Ringkasan keputusan alur UX / state branches / hierarki UI / routing (untuk frontend).
   - Daftar boundary yang disepakati (apa yang dikerjakan secara atomik dan apa yang berada di luar cakupan).
3. Set status terminal `CLARIFIED` (atau `SKIPPED` bila melalui fast-path).
4. Tawarkan `quickdev:plan` dengan spesifikasi terkunci; tunggu user.

## Guardrails

- MUST NOT membuat asumsi sendiri pada parameter kritis yang tidak disebutkan di laporan eksplorasi maupun prompt user.
- MUST NOT mengajukan pertanyaan klarifikasi jika seluruh kebutuhan sudah terdefinisi pasti dan tidak ada ambiguitas (wajib Fast-Path Skip).
- MUST NOT mengajukan pertanyaan teknis yang tidak relevan dengan profil repositori (contoh: menanyakan Tailwind styling pada repo pure backend).
- MUST NOT mengajukan pertanyaan secara mencicil satu per satu tanpa batching terstruktur.
- MUST NOT melakukan modifikasi atau penulisan kode sumber dalam skill ini.
- Keputusan preferensi bisnis, desain antarmuka, dan arsitektur tetap milik mutlak user.

## Output [REQUIRED]

Skill ini menghasilkan dokumen spesifikasi kebutuhan terklarifikasi dan status terminal terdefinisi:

1. **Dokumen Spesifikasi Terklarifikasi**:
   - Status Gate: `CLARIFIED` (jika melalui klarifikasi) atau `SKIPPED` (jika melalui fast-path).
   - Domain Spesifikasi: Backend Data Contract / Frontend UI-UX Spec / Fullstack Integrated Spec.
   - Rekap Keputusan Kunci: Daftar parameter, URL path, payload/state branch, dan validasi yang disetujui.
   - Out-of-Scope Boundaries: Batasan fitur yang disepakati tidak disentuh pada task saat ini.
2. **Status Terminal**: `CLARIFIED` (atau `SKIPPED`)
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   CLARIFY: domain <backend | frontend | fullstack>
   STATUS: CLARIFIED | SKIPPED
   PERTANYAAN: <n> diajukan dalam <n> batch | 0 (fast-path)
   KEPUTUSAN: <n> terkunci — <ringkasan singkat>
   DELEGASI: <keputusan yang didelegasikan user ke konvensi profil | ->
   OUT OF SCOPE: <daftar batas | ->
   HANDOFF: plan
   ```

## Failure path

1. **User Tidak Merespons / Dialog Dibatalkan**: Jika sesi interaksi tidak menghasilkan jawaban, simpan status draf klarifikasi, catat poin-poin yang belum terjawab, dan tawarkan fallback menggunakan konvensi default pada `profile_path` sebelum meminta konfirmasi ulang.
2. **Jawaban User Bertentangan dengan Pola Arsitektur Repo**: Jika keputusan user melanggar aturan inti pada `profile_path` (misal: meminta controller mengakses database langsung pada arsitektur Clean Architecture), jelaskan risiko teknis secara transparan, berikan alternatif yang mematuhi layer arsitektur, dan minta konfirmasi final dari user.
3. **Laporan Eksplorasi Tidak Memadai**: Jika `explore_summary` tidak memuat data yang cukup untuk memformulasikan opsi klarifikasi, tawarkan `quickdev:explore` ulang untuk area kode yang kurang lengkap.
4. **Konflik Preferensi Stakeholder**: Jika user mengajukan kebutuhan yang ambigu secara konseptual, berikan skenario use-case konkret untuk membantu user memilih pendekatan implementasi yang paling stabil.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada seluruh alur logika dan percabangan keputusan.
- Sajikan opsi pertanyaan dengan format pilihan terstruktur yang jelas, disertai tag `(Recommended)` pada opsi yang paling sesuai standar proyek.
- Pertahankan istilah domain teknis (Endpoint, Payload, Route Params, Status Code, UX Flow, State Branch, Fast-Path Skip, Handoff) tanpa penerjemahan paksa.
- Pastikan kalimat mengalir natural dan padat informasi dengan rasio sinyal terhadap token yang tinggi tanpa repetisi berulang.

---
name: explore
description: Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — penelusuran arsitektur kode dan pemetaan simbol file:baris sebagai bahan quickdev:clarify/quickdev:plan; dipanggil eksplisit lewat /quickdev:explore.
disable-model-invocation: true
---

## THE IRON LAW

PENELUSURAN CODEBASE WAJIB MENGHASILKAN BUKTI FAKTUAL BERUPA PATH FILE DAN NOMOR BARIS SIMBOL TANPA ASUMSI REKAAN. DILARANG MELAKUKAN PERUBAHAN ATAU PENULISAN KODE SUMBER SELAMA PROSES EKSPLORASI BERJALAN. SETIAP SIMBOL UTAMA (FUNGSI, KELAS, TIPE, HOOK, ENDPOINT) YANG RELEVAN DENGAN PERMINTAAN USER WAJIB DITELUSURI HINGGA PEMANGGIL DAN DEFINISI SUMBERNYA SAMPAI KEDALAMAN `trace_depth`. DILARANG MELANJUTKAN KE TAHAP PERENCANAAN TANPA MENGETAHUI DAMPAK PERUBAHAN TERHADAP MODUL SEKITAR. KEDALAMAN PENELUSURAN DAN ANALISIS DAMPAK MENGIKUTI SKALA FASE 0.

## Precondition [REQUIRED]

1. Repositori target berada di direktori lokal dan dapat dibaca menggunakan tool pencarian simbol dan pembaca berkas.
2. Profil repositori pada `profile_path` dianjurkan tersedia sebagai referensi layer arsitektur dan konvensi penamaan; bila absen, skill tetap berjalan lewat Failure path 3.
3. Permintaan pengguna memiliki domain fitur, bug, atau area fungsional kode yang jelas untuk ditelusuri.
4. Pencarian berkas/teks: tool `Glob`/`Grep` bila tersedia; bila tidak, Bash baca-saja: `git ls-files | grep -i '<pola>'` (nama berkas), `grep -rn --include='*.<ext>' '<pola>' <dir>` atau `rg -n '<pola>'` bila terpasang (isi). `Read` wajib.

## Koeksistensi [REQUIRED]

- Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backend:*` atau `frontend:*` sebagai pengganti: `backend:profile`/`frontend:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
- Bila konteks sesi memuat blok `<backend-tech-lead-gate>` atau `<frontend-lead-gate>`:
  - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
  - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backend:tech-lead | frontend:lead>` (taskdir + brief)". Jangan memilih sendiri.
- `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
- Penanda opt-out `.claude/workflow` (nama plugin yang boleh menggerbangi repo, dipisah spasi, koma, atau baris): isi `quickdev` membuat hook SessionStart `backend`/`frontend` diam; isi `frontend quickdev` hanya menyalakan hook `frontend`.

## Parameter [REQUIRED]

- `query` — string — `[REQUIRED]` — topik penelusuran, nama fitur, kata kunci simbol, atau deskripsi masalah yang ingin dieksplorasi di codebase.
- `scope_dir` — string — default `""` — pembatasan direktori pencarian (contoh: `src/features/auth`, `src/api/v1/orders`). Jika kosong, eksplorasi mencakup seluruh area `src/` atau root proyek.
- `trace_depth` — integer — default `2` — kedalaman penelusuran pemanggil dan dependensi simbol (rentang 1 hingga 4).
- `target_symbol` — string — default `""` — nama spesifik fungsi, kelas, interface, tipe, atau route handler yang menjadi fokus utama penelusuran.
- `include_tests` — boolean — default `true` — indikasi apakah penelusuran wajib menyertakan file unit test dan integration test terkait.
- `profile_path` — string — default `"repo-profile.md"` — path profil hasil `quickdev:profile` (samakan dengan `target_path` di sana); bila tidak ditemukan, gunakan fallback `.dev/profile.md`. Bila repo memuat lebih dari satu profil (`git ls-files '*repo-profile.md'`), tanyakan workspace mana lewat `AskUserQuestion`, jangan memakai root diam-diam.

## Workflow

### Fase 0 — Inisialisasi Konteks & Resolusi Profil Repositori

1. Muat konteks profil repositori dari `profile_path`:
   - Identifikasi jenis dari baris `TIPE`/template profil: `backend`, `frontend`, atau `fullstack` (template fullstack, atau beberapa profil workspace yang sama-sama tersentuh `query`).
   - Catat pola struktur folder (contoh: Feature-based architecture vs Layer-based architecture).
   - Catat alias path compiler (contoh: `@/* -> src/*`, `~/* -> src/*`) untuk mempermudah resolusi file import dan export modul.
2. Analisis parameter `query` dan `target_symbol` yang diberikan pemanggil:
   - Ekstrak entitas domain utama (contoh: `User`, `Invoice`, `Auth`, `PaymentMethod`, `Session`, `Order`).
   - Identifikasi kata kunci teknis pencarian (contoh: controller, service, mutation hook, database schema, route definition, middleware).
3. Tentukan boundary direktori pencarian berdasarkan parameter `scope_dir`:
   - Jika `scope_dir` ditentukan, batasi penelusuran awal pada direktori tersebut.
   - Jika `scope_dir` kosong, tetapkan direktori pencarian pada root folder sumber (`src/`, `app/`, `internal/`, `pkg/`, atau `lib/`).
4. Tentukan skala dari permintaan dan temuan pertama, lalu nyatakan di Output (`SKALA: kecil | standar`):
   - **kecil**: ≤2 berkas, tanpa perubahan kontrak publik, skema, atau env → `trace_depth=1`; Fase 3 hanya pemanggil langsung dan test berkas target; env/DB dilewati dan dicatat `tidak relevan`.
   - **standar**: selain itu → aturan penuh Fase 1–3.

### Fase 1 — Pemetaan File & Simbol (Pencarian Nama Berkas & Teks)

1. Jalankan pencarian nama berkas (alat per Precondition 4) dengan pola yang menggabungkan entitas domain dan peran layer (contoh: `**/*order*controller*`, `**/*order*.service.*`, `**/*Order*Dto*`, `**/use*Order*`):
   - Peran layer acuan: controller/route/handler, service/usecase, DTO/schema/entity, component/hook/page.
   - Pola peran tanpa entitas (`*type*`, `*api*`, `*page*`) hanya dipakai di dalam `scope_dir` yang sudah sempit karena menghasilkan ratusan kandidat tak relevan.
2. Jalankan pencarian teks mendalam (alat per Precondition 4) terhadap istilah kunci dan `target_symbol`:
   - Cari deklarasi definisi simbol utama: `class <Symbol>`, `function <symbol>`, `const <symbol> =`, `interface <Symbol>`, `type <Symbol>`.
   - Cari definisi route HTTP atau endpoint path: `@Get('/path')`, `router.post('/path')`, `app.get('/path')`, `export async function GET()`.
   - Cari penggunaan database queries atau ORM entities: `prisma.<model>`, `repository.find`, `db.select()`, `Schema.find()`, `db.query()`.
3. Kumpulkan daftar kandidat file yang memiliki kecocokan langsung dengan topik penelusuran dan urutkan berdasarkan tingkat relevansi.

### Fase 2 — Penelusuran Alur Data & Keterkaitan Dependensi (Trace Flow)

1. Lakukan pembacaan berkas (File Inspection) pada baris-baris relevan hasil penemuan Fase 1:
   - Catat tanda tangan fungsi (function signature), parameter input, dan tipe data kembalian (return type).
   - Catat validasi input, transformasi payload, penanganan error, dan pemanggilan service internal.
2. Telusuri rantai pemanggil (Caller Chain) hingga kedalaman `trace_depth`:
   - Untuk **Backend**:
     - Route/Controller -> Middleware/Guards -> Service/Usecase -> Repository/Data Access -> ORM Model -> Database Schema.
     - Identifikasi middleware yang mencegat request (misal: Auth Guard, Role Check, Validation Pipe, Rate Limiter, Tenant Context).
     - Identifikasi DTO yang digunakan pada input (Request Body/Params/Query) dan output (Response Body/Envelope).
     - Identifikasi event emitter, job queue worker, atau background task yang dipicu oleh alur kerja tersebut.
   - Untuk **Frontend**:
     - Page/Route View -> Layout Container -> Feature Component -> Custom Hook / State -> API Service Client -> DTO/Type.
     - Identifikasi state management lokal dan server cache key (misal: TanStack Query key `['users', userId]`, SWR key, Redux slice).
     - Identifikasi percabangan state tampilan UI (loading spinner, error alert, empty placeholder, form validation feedback, success view).
     - Identifikasi form handling library dan skema validasi deklaratif (contoh: React Hook Form + Zod resolver).
3. Petakan seluruh dependensi eksternal, library pihak ketiga, utility helper, atau service RPC/gRPC yang terlibat dalam alur proses tersebut.

### Fase 3 — Analisis Dampak & Identifikasi Area Kritis (Impact Assessment)

1. Evaluasi potensi efek samping (side effects) jika kode pada modul target dimodifikasi (skala `kecil`: hanya pemanggil langsung dan test berkas target):
   - Pindai berkas lain yang mengimpor simbol yang akan diubah (reverse dependency search lintas codebase).
   - Identifikasi apakah perubahan kontrak data (request/response DTO) dapat merusak modul konsumen frontend atau backend lain.
   - Identifikasi skema database, tabel relasi, indeks, atau foreign keys yang terikat dengan entitas yang ditelusuri.
   - Periksa konfigurasi environment variables (.env) atau secret yang dibutuhkan oleh fitur tersebut.
2. Catat berkas pengujian (Test Suite) yang menguji modul tersebut bila `include_tests: true`:
   - Cari file unit test dan integration test (contoh: `*.spec.ts`, `*.test.tsx`, `test_*.py`, `*_test.go`).
   - Periksa coverage skenario pengujian yang sudah ada: happy paths, validation errors, edge cases, permission denied scenarios.
3. Catat anomali, code smells, technical debt, atau pola usang yang ditemukan selama eksplorasi di sekitar area target.

### Fase 4 — Penyusunan Laporan Temuan & Handoff

1. Susun laporan terstruktur hasil eksplorasi codebase yang memuat:
   - Ringkasan arsitektur alur kerja yang ditelusuri beserta konteks bisnisnya.
   - Tabel direktori dan berkas kunci beserta perannya dalam sistem.
   - Rincian simbol, interface, dan fungsi utama lengkap dengan rujukan path `file:baris`.
   - Diagram atau urutan alur data end-to-end (Data Flow Trace).
   - Analisis dampak ketergantungan dan daftar modul konsumen yang berpotensi terdampak.
   - Ringkasan cakupan pengujian eksisting dan file test yang perlu diperbarui.
   - Catatan ketidakpastian, celah spesifikasi, atau asumsi yang memerlukan klarifikasi lebih lanjut di `quickdev:clarify`.
2. Set status terminal `EXPLORED`.
3. Tawarkan `quickdev:clarify` (atau `quickdev:plan` bila nol celah); tunggu user.

## Guardrails

- MUST NOT melakukan modifikasi, penulisan, atau penghapusan kode sumber selama proses eksplorasi berlangsung.
- MUST NOT menyajikan path file atau nama simbol fiktif tanpa konfirmasi riil dari pencarian codebase aktual.
- MUST NOT mengabaikan analisis dampak ke modul hilir yang mengimpor simbol yang ditelusuri.
- MUST NOT melompati penelusuran test suite yang relevan dengan area kode yang dieksplorasi, kecuali `include_tests: false`.
- MUST NOT menghentikan penelusuran pada layer permukaan tanpa memeriksa implementasi logika bisnis inti, sesuai skala Fase 0.
- Keputusan penetapan cakupan tugas akhir tetap berada di bawah kendali dan persetujuan user.

## Output [REQUIRED]

Skill ini menghasilkan laporan eksplorasi codebase terstruktur dan laporan terminal terdefinisi:

1. **Laporan Temuan Eksplorasi**:
   - Ringkasan konteks arsitektur dan fokus penelusuran.
   - Daftar berkas kunci: `path/to/file.ts:10-45` beserta peran fungsionalnya.
   - Diagram atau urutan alur data (Data Flow Trace).
   - Matriks dampak ketergantungan (Impact Matrix).
   - Daftar file test terkait dan baseline coverage.
   - Celah spesifikasi / ambiguitas untuk bahan klarifikasi.
2. **Status Terminal**: `EXPLORED`
3. **Format Ringkasan Akhir (Maksimal 17 Baris)**:
   ```
   EXPLORE: <query> — scope <scope_dir | root sumber>
   STATUS: EXPLORED
   SKALA: kecil | standar — <alasan satu frasa>
   TIPE: <backend | frontend | fullstack>
   PROFIL: <path profil terpakai | heuristik (profil absen)>
   BERKAS KUNCI: <n> berkas, <n> simbol ditelusuri (trace_depth=<n>)
   ALUR: <entry point> -> ... -> <sink data>
   DAMPAK: <n> modul konsumen terdampak
   TEST: <n> berkas test terkait | tidak ditelusuri (include_tests=false)
   CELAH: <n> ambiguitas diteruskan ke clarify
   HANDOFF: clarify
   ```

## Failure path

1. **Simbol / Topik Tidak Ditemukan di Codebase**: Jika kueri pencarian tidak menghasilkan satu pun berkas atau kecocokan teks di codebase, perluas parameter `scope_dir` ke seluruh direktori root proyek, coba variasi sinonim kata kunci (contoh: `auth` vs `session` vs `jwt`, `order` vs `invoice` vs `checkout`), dan jika tetap tidak ditemukan, laporkan hasil temuan nol secara transparan beserta saran kata kunci alternatif untuk user.
2. **Codebase Terlalu Besar / Ambiguitas Simbol Ganda**: Jika simbol ditemukan di lebih dari 10 modul yang berbeda (contoh: nama umum seperti `ConfigService`, `Button`, `Modal`, atau `BaseRepository`), gunakan parameter `scope_dir` untuk mempersempit area fokus dan minta konfirmasi user mengenai modul spesifik yang ditargetkan sebelum melanjutkan penelusuran mendalam.
3. **Berkas Profil Repositori Tidak Ditemukan**: Jika `profile_path` maupun fallback-nya tidak ada, lakukan pemindaian heuristik mandiri pada struktur direktori `src/` dan file manifes root, sambil memberikan rekomendasi kepada pemanggil untuk menjalankan `quickdev:profile` terlebih dahulu agar standar layer arsitektur terkunci.
4. **Izin Baca Filesystem Ditolak**: Jika terdapat folder yang terproteksi hak akses atau symlink rusak, catat direktori yang tidak dapat dibaca pada laporan dan lanjutkan eksplorasi pada modul lain yang dapat diakses di repositori.

## STYLE

- Gunakan kalimat imperatif aktif dan Observable Predicate pada setiap tahapan instruksi penelusuran.
- Sajikan referensi berkas dalam format `path/to/file.ts:42` atau rentang `path/to/file.ts:42-58` agar dapat diklik langsung.
- Gunakan format tabel markdown untuk menyajikan daftar berkas kunci dan pemetaan simbol arsitektur.
- Pertahankan istilah domain teknis standar (Controller, Service, Repository, DTO, Hook, Middleware, State Branch, Trace Flow, Impact Matrix) tanpa penerjemahan paksa.
- Pastikan informasi disajikan secara padat fakta teknis dengan rasio sinyal terhadap token yang optimal tanpa narasi pengisi.

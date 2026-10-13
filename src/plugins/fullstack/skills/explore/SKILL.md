---
name: explore
description: Gunakan ketika sesi berjalan di root multi-repo (folder non-git berisi repo seperti api/ dan frontend/, atau banyak proyek sekaligus di satu perusahaan) dan user ingin memahami aplikasi-aplikasinya — aplikasi apa saja yang ada, stack dan domain tiap repo, fitur dan rute frontend, aplikasi mana memanggil aplikasi mana — atau menelusuri satu layar, fitur, endpoint, entitas, atau integrasi lintas frontend dan backend (termasuk API ke API) - peta aplikasi PETA.md dari profil repo tanpa membaca kode, lalu explore permukaan lewat subagent repo-scout dengan jahitan yang dicocokkan skrip, sebelum kerja perubahan diarahkan ke gerbang backend/frontend di dalam repo
---

## THE IRON LAW

- **Hanya explore.** Skill ini tidak pernah mengubah berkas di repo anak, tidak menjalankan skill backend/frontend,
  dan tidak meng-commit apa pun. Satu-satunya yang ditulis: `.fullstack/PETA.md`, `.fullstack/explore/*.md`, dan
  `.fullstack/layanan.json` di root, semuanya lewat skrip atau dari template.
- **Konteks utama tidak membaca kode repo anak.** Gambaran perusahaan datang dari `PETA.md`, yang dibangun skrip dari
  profil. Bukti kode datang dari balikan subagent `fullstack:repo-scout`. Dilarang `Read`/`Grep`/`Glob` atas kode
  repo anak, termasuk "intip sebentar".
- **Profil adalah peta sisir.** Repo tanpa profil `VALID` tidak di-scout. Profil yang basi atau hilang diarahkan ke
  `<plugin>:profile` di dalam repo itu, bukan ditambal dengan pemindaian sendiri.
- **Jahitan dihitung skrip.** Tabel `## Jahitan` hanya ditulis `explore.py seam --write`. Target panggilan dianggap
  pasti hanya dari `layanan.json` yang dikonfirmasi user, atau dari frontend di proyek yang punya tepat satu backend.

## Precondition [REQUIRED]

1. Skrip: `workspace.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/workspace.py`, `explore.py` =
   `${CLAUDE_PLUGIN_ROOT}/skills/_common/explore.py`. Template dispatch:
   `${CLAUDE_PLUGIN_ROOT}/skills/explore/dispatcher/scout.md`. Semua skrip dijalankan dengan cwd = root.
2. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/explore/scripts/check_preconditions.py`. `PASS` → catat dari baris
   `Terselesaikan:` nilai `root`, `repo`, `profil_valid`, `proyek`, `peta`, dan `laporan`. `PASS (WARN)` → sebut
   peringatannya ke user, lalu lanjut. `FAIL` → remediasi per baris `Tindakan`, lalu berhenti. Check 3 `DALAM_REPO`
   berarti sesi ada di dalam repo: arahkan user ke `backend:tech-lead` atau `frontend:lead`, atau ke folder induknya.

## Parameter [REQUIRED]

- `request`: pertanyaan user apa adanya.

## Workflow

### Phase 0 — Jalur & Lingkup

1. **Jalur.**
   - `PETA`: pertanyaan umum tentang aplikasi-aplikasi di root — "aplikasi apa saja", "pelajari semua", "stack
     tiap repo", "siapa memanggil siapa", "repo mana yang belum diprofilkan".
   - `TELUSUR`: satu objective konkret — layar, fitur, endpoint, entitas, atau integrasi — yang butuh bukti kode.

   Objective `TELUSUR` yang kabur ("cek order") dipersempit dengan satu `AskUserQuestion`; opsinya diambil dari nama
   domain dan fitur di `PETA.md`.
2. **Lingkup** (`TELUSUR` saja). Satu proyek secara default: ditebak dari nama proyek atau repo yang disebut
   `request`. Root dengan lebih dari satu proyek dan `request` yang tidak menyebutnya → satu `AskUserQuestion`.
   Objective yang menyebut beberapa proyek, atau integrasi API ke API antar proyek, melingkupi semuanya. Repo root
   langsung (tanpa folder proyek) berproyek `.`.

### Jalur `PETA`

1. Jalankan `python3 <workspace.py> peta --write`.
2. Baca `.fullstack/PETA.md` dan jawab `request` dari situ. Bila ada repo dengan **profil tertinggal**, repo di
   `## Belum terpetakan`, atau hubungan `belum dipetakan`, sebut di jawaban beserta arahannya.
3. Bila user lalu bertanya hal konkret, pindah ke jalur `TELUSUR` dengan lingkup dari jawaban itu.

### Jalur `TELUSUR`

#### Phase 1 — Bahan

1. `PETA.md` belum ada (`peta=belum ada`) → jalankan `python3 <workspace.py> peta --write`. Baca seksi proyek di
   lingkup untuk memilih repo dan domain yang di-scout.
2. Jalankan `python3 <explore.py> list --json`. Pilih maksimal dua laporan yang `objective`-nya beririsan. Laporan
   `basi: true` hanya boleh mempersempit arah; faktanya tidak masuk slot `{panen}`.
3. Jalankan `python3 <explore.py> layanan list --json`. Galat → hentikan jalur `TELUSUR` sebelum `seam` (Failure
   path 3).

#### Phase 2 — Putaran Pertama

1. Pilih repo berprofil `VALID` di lingkup yang relevan dengan objective, maksimal 4. Repo berprofil ganda bisa
   didispatch per peran.
2. Hidrasi `dispatcher/scout.md` per repo, lalu kirim semua dispatch `fullstack:repo-scout` dalam **satu pesan**
   supaya berjalan paralel.

#### Phase 3 — Putaran Kedua (opsional)

Dispatch putaran kedua hanya bila ada salah satu:

- panggilan BE atau FE yang calon repo penerimanya belum disisir: dispatch repo penerima itu dengan slot
  `{verifikasi}` berisi `METODE /path` panggilan tersebut;
- butir `Belum disisir` beralasan "kuota habis".

Maksimal 4 repo. Sesudah putaran ini, tidak ada dispatch lagi.

#### Phase 4 — Laporan

1. Buat kerangka: `python3 <explore.py> new --slug <slug> --objective "<request>" --lingkup <proyek,...> --repo
   <dir,...>`. `--repo` = semua repo yang di-scout. Catat path dari baris `Tertulis:`.
2. Isi seksi dari balikan scout menurut tabel Penanganan Balikan di `dispatcher/scout.md`. Hapus komentar template
   saat mengisi. Isi `confidence` di frontmatter menurut aturan 5 template.
3. Jalankan `python3 <explore.py> seam --report <laporan> --write`.
4. **Konfirmasi pemetaan.** Baris `DUGAAN`/`AMBIGU` ada → satu `AskUserQuestion` berisi maksimal 4 target: "Panggilan
   `<pemanggil>` lewat `<target>` diterima repo mana?", dengan opsi calon penerima dari kolom `Penerima`. Tiap jawaban
   disimpan: `python3 <explore.py> layanan set --pemanggil <dir> --target <nama> --repo <dir> [--prefix <path>]`.
   Lalu jalankan `seam --write` sekali lagi. Target yang tidak dijawab tetap ditulis di `### Belum dipetakan`.
5. Jalankan `python3 <explore.py> check --report <laporan>`. FAIL → perbaiki menurut ringkasan check, lalu ulangi;
   maksimal 3 putaran perbaikan (Failure path 5).

#### Phase 5 — Ringkasan

Balas user dengan `## Jawaban` laporan dalam bentuk ringkas, jahitan penting (`COCOK`, `TIDAK_ADA_DI_TARGET`),
celah yang mempengaruhi jawaban, dan path laporan. Kerja perubahan kode diarahkan sesuai `## Arahan Lanjut`.

## Guardrails

- **NOL KODE DI KONTEKS UTAMA**: dilarang `Read`/`Grep`/`Glob` atas berkas di dalam repo anak. Yang boleh dibaca
  konteks utama: keluaran skrip, `.fullstack/PETA.md`, dan laporan `.fullstack/explore/*.md`.
- **NOL TULIS DI REPO ANAK**: dilarang membuat, mengubah, atau menghapus berkas di dalam repo anak, termasuk profil.
- **JAHITAN LEWAT SKRIP**: dilarang mengetik atau menyunting tabel `## Jahitan`; dilarang menulis `layanan.json`
  dengan tangan.
- **NAMA CONFIG, BUKAN NILAI**: dilarang menyalin nilai `.env`, token, atau host dari mana pun ke laporan maupun
  jawaban.
- **PERTANYAAN HEMAT**: maksimal satu `AskUserQuestion` untuk jalur/lingkup (Phase 0) dan satu untuk pemetaan
  (Phase 4 langkah 4) per explore.
- **GERBANG ENGINEER TIDAK BERLAKU DI ROOT**: blok `<backend-tech-lead-gate>`/`<frontend-lead-gate>` di root
  multi-repo hanya menunjuk repo; skill ini tidak merutekan ke sana kecuali sebagai `## Arahan Lanjut`.
- **RATIONALIZATION PREVENTION**:
  - "Saya baca handler-nya sendiri, lebih cepat daripada dispatch" — bukti yang tidak lewat scout tidak berkuota,
    tidak berformat, dan menghabiskan konteks yang dibutuhkan untuk menyusun laporan.
  - "Path-nya sama, pasti API itu yang dipanggil" — dua API bisa punya path yang sama; tanpa `layanan.json`,
    kecocokan path hanya `DUGAAN`.
  - "Repo ini belum diprofilkan, saya sisir manual saja" — tanpa profil tidak ada peta sisir; arahkan ke
    `<plugin>:profile`.
  - "Scout tidak menemukan endpoint-nya, berarti fitur itu belum ada" — `Tidak ditemukan` hanya berarti tidak ada di
    yang disisir; tulis di `## Celah`, bukan di `## Jawaban` sebagai fakta.

## Output [REQUIRED]

- Jalur `PETA`: `.fullstack/PETA.md` (ditulis ulang utuh) dan jawaban di chat.
- Jalur `TELUSUR`: `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` yang lolos `explore.py check`, `.fullstack/layanan.json`
  bila user mengonfirmasi pemetaan, dan ringkasan di chat beserta path laporan.

## Failure path

1. Prasyarat `FAIL` → remediasi per `Tindakan`, berhenti.
2. Scout gagal dua kali untuk satu repo → repo itu masuk `### Belum disisir`, laporan tetap terbit dengan
   `confidence` maksimal `medium`.
3. `layanan.json` rusak → jalur `PETA` tetap jalan (hubungan dari berkas itu dilewati); jalur `TELUSUR` berhenti
   sebelum `seam` dan meminta user memperbaiki atau menghapus berkasnya.
4. Root melewati plafon 60 repo → `PETA` tetap jalan untuk yang tercakup; sebut proyek yang terpotong dan sarankan
   menjalankan dari folder yang lebih sempit.
5. `check` masih FAIL sesudah 3 putaran perbaikan → laporan dibiarkan apa adanya, sebut check yang gagal ke user, dan
   jangan menyebut laporan itu selesai.
6. User meminta perubahan kode di tengah explore → hentikan explore dan beri arahan `cd <repo>` lalu
   `backend:tech-lead` atau `frontend:lead`.

## STYLE

- Jawaban ke user dalam bahasa user, tanpa jargon skrip kecuali path laporan.
- Rujukan kode selalu `<repo>/<path>:<baris>`.

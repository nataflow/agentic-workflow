---
name: profile
description: Gunakan ketika .claude/profile/frontenddev/ belum ada atau perlu diperbarui - deteksi stack, pemetaan surface map, dan invariant, sebelum implementasi kode tanpa verifikasi baseline
---

## THE IRON LAW

PROFIL CODEBASE WAJIB MEMUAT `index.json` BER-FIELD STACK, SURFACE MAP, DAN INVARIANTS MUTLAK. DILARANG MENCATAT LIBRARY ATAU STACK TANPA BUKTI KONFIGURASI NYATA DI PACKAGE.JSON ATAU BERKAS CONFIG FRAMEWORK. PERINTAH TYPECHECK, LINT, DAN TEST WAJIB BENAR-BENAR DIEKSEKUSI DI TERMINAL UNTUK MENCATAT BASELINE ERROR SEBELUM KODE DIUBAH. DILARANG MENGEDIT, MEMPERBAIKI, ATAU MEMBUAT FILE KODE DI SRC SELAMA PROSES PROFILING. PROFIL HANYA SAH DITULIS KE `.claude/profile/frontenddev/` SEBAGAI `index.json` PLUS SEMBILAN BERKAS `.md`, DAN PADA MODE REFRESH DITULIS ULANG PENUH TANPA MERGE PARSIAL. RESEP SPESIFIK STACK DIBACA DARI SATU ADAPTER `stacks/<stack-id>.md`, BUKAN DARI INGATAN STACK LAIN.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/profile/scripts/check_preconditions.py [--mode <mode>] [--stack <stack>] [--profile-dir <dir>]`.
2. `PASS` (6/6 checks): lanjut ke Workflow. `FAIL`: hentikan dan remediasi butir yang gagal — manifest frontend tidak terdeteksi, memuat `next`, atau React/Svelte tanpa Vite (CRA, Rollup) → repo di luar cakupan plugin, jangan buat berkas apa pun; `--profile-dir` selain `.claude/profile/frontenddev` → jalankan ulang tanpa parameter itu; `.claude/profile/frontenddev/index.json` milik plugin lain → laporkan ke user, jangan ditimpa; adapter stack hilang → pulihkan berkas plugin; direktori profil tidak dapat ditulis → periksa izin `.claude/`; berkas referensi hilang → pulihkan berkas plugin. `WARN` tidak menahan, tetapi wajib disebut ke user sebelum Phase 0 berjalan: repo non-git, monorepo multi-stack, parameter `stack` yang menimpa deteksi, dan mode yang tidak selaras dengan keadaan disk.
3. Skrip mengembalikan dua fakta terselesaikan di baris `Terselesaikan:` — `<stack-id>` dan mode operasi (`GENERATE`/`REFRESH`/`MIGRATE`). Phase 0 dan Phase 1 memakai keduanya apa adanya; keduanya deterministik, dan menurunkannya ulang lewat pembacaan model membuat repo yang sama divonis berbeda antar-sesi.

## Parameter [REQUIRED]

- `mode` — string — default `"auto"` — opsi mode profiling (`"auto"` | `"generate"` | `"refresh"` | `"migrate"`). Mode `"auto"` mendeteksi keberadaan dan kepemilikan `.claude/profile/frontenddev/index.json` serta profil lama di `.claude/profile/` secara otomatis.
- `stack` — string — default `"auto"` — paksa `<stack-id>` bila deteksi Phase 0 ambigu; nilai sah = daftar di `stacks/_CONTRACT.md` (`react-vite`, `react-native`, `sveltekit`, `svelte-vite`).
- `force` — boolean — default `false` — bila `true`, Phase 1 melewati konfirmasi REFRESH dan langsung menulis ulang. Dipakai `frontenddev:lead` saat merutekan lane `PROFILE` secara otomatis: rute itu berangkat tanpa user pernah meminta profiling, jadi titik henti interaktif di tengahnya menggantung tanpa pertanyaan yang user tahu asal-usulnya. `force` tidak pernah berlaku atas profil milik plugin lain atau lokasi lama `.claude/profile/`; keduanya ditolak prasyarat atau dialihkan ke MIGRATE.
- `profile_dir` — string — default `".claude/profile/frontenddev"` — target tulis Phase 6; nilai lain ditolak.
- `target_app` — string — default `""` — nama package atau path sub-aplikasi monorepo (misal: `apps/web`) bila ingin memfokuskan pemindaian layer pada modul spesifik.
- `run_tests` — boolean — default `true` — bila `true`, menjalankan test runner di terminal untuk mencatat baseline test suite aktual.
- `strict_scan` — boolean — default `true` — bila `true`, memindai seluruh sub-direktori feature untuk memetakan competing patterns secara mendalam.
- `interview` — boolean — default `true` — bila `false`, Phase 3 dilewati; `layer-adoption.md` dan `drift.md` diisi hasil pemindaian saja dan ditandai **belum tervalidasi user** di `manual-notes.md`. Tanda itu wajib: profil yang gaya terbelahnya diputuskan sepihak terbaca sama persis dengan profil yang gayanya benar-benar disepakati tim.
- `reported_drift` — list — default `[]` — pola warisan yang terbukti menyesatkan saat eksekusi, diteruskan `frontenddev:architect` Phase 5 sesudah disetujui user. Tiap butir berbentuk `<file#simbol> — <pola warisan> → <pola pengganti>`. Pola semacam ini tidak pernah tertangkap sapuan statis: ia sah secara sintaks dan tetap kompilabel, dan baru terbukti salah ketika brief menyalinnya sebagai *Pola Acuan*.

## Workflow

Pemindaian profil codebase dieksekusi sekuensial melalui 8 fase inspeksi read-only:

### Phase 0 — Deteksi Stack & Resolusi Adapter

Tetapkan `<stack-id>` secara deterministik [REQUIRED]:

1. Ambil `<stack-id>` dari baris `Terselesaikan:` skrip prasyarat. Skrip memakai urutan pemutus yang sama dengan `references/framework-matrix.md` bagian 2 dan `hooks/detect.py`: manifest dibaca dari `dependencies` + `devDependencies` (bukan `overrides`/`peerDependenciesMeta`) di root, workspace terdeklarasi, `apps/*`, `packages/*`, `services/*`, dan anak langsung root; `next` hadir → di luar cakupan; `react-native`/`expo` → `react-native`; `@sveltejs/kit` → `sveltekit`; `svelte` tanpa kit + penanda Vite (`vite` atau `vite.config.*`) → `svelte-vite`; `react` + penanda Vite → `react-vite`; React/Svelte tanpa Vite (CRA, Rollup) → di luar cakupan.
2. Evaluasi vonisnya:
   - Nol stack: hentikan, sebutkan manifest yang diperiksa. Dilarang membuat profil palsu pada repo non-frontend.
   - Lebih dari satu stack (monorepo `apps/web` + `apps/mobile`): minta user memilih satu `<stack-id>` utama lewat `stack` dan `target_app`.
   - Parameter `stack` menimpa deteksi: catat penanda pendukung maupun yang bertentangan.
3. Baca `stacks/<stack-id>.md`: `## Detection` jadi pemutus bila penanda kabur; `## Commands`, `## Navigation recipes`, dan `## Layer taxonomy` dipakai di Phase 2–4. Adapter tidak ada: hentikan, laporkan stack belum didukung; dilarang memprofil dengan asumsi stack lain.
4. Identifikasi arsitektur workspace mengikuti titik 5 `references/scan-guide.md`.

### Phase 1 — Deteksi Mode Operasi & Konfirmasi Pengguna

1. Ambil mode dari baris `Terselesaikan:` skrip prasyarat:
   - `GENERATE` (profil belum ada): lanjut ke Phase 2 tanpa konfirmasi.
   - `MIGRATE` (profil frontenddev masih di lokasi lama `.claude/profile/index.json`): jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/profile/scripts/migrate_profile.py`, laporkan berkas sisa di `.claude/profile/` sebagai **bukan milik plugin ini — tidak disentuh**, commit `docs: migrate frontenddev profile` (Phase 6 butir commit), lalu lanjut ke Phase 7 tanpa pemindaian ulang. Sebut juga di laporan: profil plugin lain yang pernah tertimpa dapat dipulihkan dari riwayat `git log --oneline -- .claude/profile/index.json`.
   - `GENERATE` dengan catatan profil lama milik plugin lain di `.claude/profile/`: biarkan berkas itu — jangan dibaca sebagai profil frontenddev, jangan ditimpa; profil ditulis ke `.claude/profile/frontenddev/`.
   - `REFRESH` (`.claude/profile/frontenddev/index.json` ada dan milik frontenddev): tampilkan ringkasan profil saat ini — field `stack` `index.json`, tanggal commit terakhirnya, jumlah baris `drift.md` — lalu minta konfirmasi "Lakukan REFRESH (tulis ulang penuh) atau BATAL?". Hentikan menunggu respons bila `force: false`.
2. Abaikan seluruh isi profil lama saat memindai bila REFRESH disetujui. Profil **ditulis ulang penuh** dari pemindaian segar; dilarang merge parsial. Merge parsial mempertahankan baris yang polanya sudah lenyap, dan implementor terus dilarang meniru pola yang sudah tidak ada. Satu-satunya berkas yang dipertahankan apa adanya adalah `manual-notes.md`.
3. Laporkan perubahan stack sebagai temuan tersendiri sebelum menulis ulang bila field `stack` lama berbeda dari hasil Phase 0.
4. Panen baris `drift.md` profil lama sebelum ditimpa, dan jalankan ulang resep `deteksi` tiap barisnya. Vonisnya disajikan ke user di Phase 3, bukan diputuskan di sini.

### Phase 2 — Pemindaian 18 Titik Arsitektur Codebase

Jalankan tiap titik memakai resep di `references/scan-guide.md`; resep spesifik stack diambil dari `stacks/<stack-id>.md` [REQUIRED].

- Titik 1–5: manifest & framework · perintah verifikasi repo · TypeScript config & alias · framework & bundler config · arsitektur workspace.
- Titik 6–10: lima layer kanonik — Controller · View-Model · API layer · HTTP Service · DTO — beserta sebaran adopsinya.
- Titik 11–16: surface map · persisted state & storage · shared HTTP client · design token & visual · standar test · konvensi commit.
- Titik 17–18: enam invariant mutlak · drift dan pola yang bersaing.

Muara tiap titik ke berkas profil ditetapkan oleh judul titik itu di `references/scan-guide.md`. Catat setiap fakta bersama anchor `<path>#<simbol>`; tulis `tidak terdeteksi` bila fakta nihil. Kumpulkan inkonsistensi antar-fitur dan gaya terbelah tanpa mayoritas sebagai bahan wawancara Phase 3 — jangan memutuskannya di sini.

### Phase 3 — Wawancara Pola Terbelah, Drift & Konfirmasi

1. Untuk tiap aspek — state management, query layer, form, styling — sajikan sebaran hasil Phase 2. Ada mayoritas jelas → yang mayoritas masuk `layer-adoption.md`, yang minoritas masuk `drift.md`. **Terbelah tanpa mayoritas** (Zustand di tiga fitur, Context di tiga fitur lain) → tanyakan ke user gaya mana yang berlaku. Itu keputusan tim, bukan temuan pemindaian: memutuskannya sepihak berarti profil melarang setengah repo tanpa satu pun orang menyetujuinya. Gaya terpilih masuk `layer-adoption.md`; yang kalah masuk `drift.md` bertanda `bukti user`.
2. Sajikan draf titik 18 sebagai daftar terstruktur, lalu ajukan satu putaran konfirmasi: baris mana yang ditambah, dicabut, atau diralat.
3. Sajikan tiap baris `drift.md` profil lama hasil panen Phase 1 bervonis `[MASIH HIDUP — <n> hit]` atau `[PUNAH — 0 hit]` agar pengetahuan sebelumnya tidak hilang. Baris `PUNAH` dicabut hanya atas keputusan user; mencabutnya sendiri menghapus larangan yang mungkin masih dipegang tim.
4. **WHEN** parameter `reported_drift` terisi:
   - `THEN`: Sajikan tiap butirnya bervonis `[DARI EKSEKUSI — <file#simbol>]` beserta pola dan sebab terhentinya. Butir ini datang dari rantai eksekusi yang benar-benar tersandung preseden itu, bukan dari sapuan statis — sapuan tidak pernah menemukannya karena polanya sah secara sintaks dan hanya salah sebagai teladan. Yang disetujui user ditulis sebagai baris Drift berformat sama; susun resep `deteksi`-nya dari pola butir itu lalu verifikasi ia menghasilkan minimal satu hit, dan turunkan ke `bukti user` bila nol hit. Yang ditolak dibuang, tidak disimpan sebagai catatan.
5. **WHEN** `interview: false` atau user tidak menjawab:
   - `THEN`: Lanjutkan dengan hasil pemindaian apa adanya, tandai `layer-adoption.md` dan `drift.md` sebagai belum tervalidasi user di `manual-notes.md`, dan catat itu di laporan Phase 7. Butir `reported_drift` pada mode ini tetap ditulis dengan tanda yang sama.

### Phase 4 — Eksekusi Baseline Verifikasi Nyata

Uji perintah hasil Phase 2 titik 2 di terminal sebelum ditulis ke `commands.md` [REQUIRED]:

1. Eksekusi berurutan `typecheck`, `lint`, `test`, `build`. Tulis `tidak berlaku` bila perintah tidak punya padanan di stack ini. Baris keputusan `typecheck-per-brief`: salin nilai adapter; profil boleh menaikkan/menurunkannya sesuai `stacks/_CONTRACT.md` §2 dengan durasi `typecheck` terukur di butir ini sebagai alasan (`ya — svelte-check 8 dtk`), tanpa menjalankan ulang typecheck khusus untuk keputusan ini. Nilai profil menang atas adapter — `architect` membacanya lewat prasyarat.
2. Catat status tiap perintah:
   - `OK (0 errors)` atau `OK (N passing)` — exit code 0.
   - `FAIL (<n> errors)` beserta potongan pesan error ringkas — exit code bukan 0 karena kodenya merah.
   - `UNVERIFIED_ENV_NOT_READY` — kegagalan berasal dari dependensi belum terpasang, bukan dari kode. Membedakan keduanya menentukan apakah verifikasi penutup boleh menuntut hijau: baseline yang merah karena `node_modules` kosong bukan utang kode, dan menagihnya sebagai utang menghentikan rantai yang sebenarnya sehat.
   - `TIMEOUT / UNVERIFIED` — perintah macet lebih dari 5 menit (ambang yang sama dengan verifikasi penutup `architect`); batalkan prosesnya dan lanjutkan.
3. Perbaiki perintahnya lalu uji ulang bila gagal karena sintaks salah, bukan karena kodenya merah. Tulis `tidak terdeteksi` bila tetap salah sintaks.
4. **Exclusion Check**: Salin sub-bagian **Cakupan yang TIDAK diperiksa** dari `## Commands` adapter ke kolom terakhir tabel baseline (misal: "Metro membuang tipe TS sebelum test Jest jalan"; "`tsc` saja tidak memeriksa `.svelte`"). Kolom itu yang mencegah `test` hijau dibaca sebagai bukti typecheck hijau.
5. Dilarang keras memperbaiki kode sumber agar baseline hijau. Hasil eksekusi ini jadi tolok ukur verifikasi penutup di gate berikutnya.

### Phase 5 — Verifikasi State Git & Pemasangan Gitignore

Satu-satunya berkas di luar `.claude/profile/frontenddev/` yang boleh disentuh gate ini adalah `.gitignore` [REQUIRED]. Vonis tiap butir diambil dari **exit code**, bukan dari membaca isi `.gitignore`: aturan ignore berlapis (akar repo, `.gitignore` bersarang, `core.excludesFile` global) dan pola negasi `!` membuat `grep` atas satu berkas menjawab pertanyaan yang salah — ia melaporkan "baris tidak ada" pada repo yang sebenarnya sudah mengabaikan path itu, lalu baris duplikat ditambahkan tiap REFRESH.

1. `git rev-parse --git-dir`. Gagal → catat status non-git, tulis field `commit_convention` `index.json` sebagai `UNINITIALIZED (default conventional commits)`, lewati butir 2–4, dan sebutkan di handoff bahwa baris ignore tidak dapat dipasang.
2. `git check-ignore -q .frontenddev`. Exit code bukan 0 → tambahkan baris `.frontenddev/` di akhir `.gitignore` akar repo (buat berkas bila belum ada); exit code 0 → lewati, jangan menyentuh berkasnya.
3. `git check-ignore -q frontenddev/docs/x/.explore/y`. Exit code bukan 0 → tambahkan baris `.explore/` di akhir `.gitignore` akar repo; exit code 0 → lewati.

   Laci `.explore/` adalah zona kerja `code-explorer` yang hidup **di dalam** taskdir supaya laporannya ko-lokasi dengan artefak yang lahir darinya. Konsekuensinya ia berkas untracked di dalam direktori yang ter-track, dan tanpa baris ignore ini ia muncul di tiap `git status --porcelain`: gerbang prasyarat `architect` Check 8 menolak dispatch karena working tree kotor, dan siapa pun yang menambal baris ignore itu belakangan menghasilkan commit tanpa brief pengklaim. Pola tanpa awalan path sekaligus mencakup laci gerbang di `.frontenddev/explore/`.
4. `git check-ignore -q frontenddev`. Exit code 0 → peringatkan user bahwa artefak taskdir `frontenddev/` berstatus lokal dan tidak di-track git; seluruh dokumen planning rantai ini tidak akan pernah ter-commit.

**Pemilik tunggal baris `.gitignore`.** Gate lain hanya boleh memeriksa baris itu, tidak menulisnya: lima pendispatch explorer yang boleh menyentuh `.gitignore` di tengah pekerjaannya tetapi tak satu pun meng-commitnya meninggalkan `M .gitignore` menggantung sepanjang taskdir, dan perubahan itu suatu saat ikut ter-commit tanpa satu pun brief yang mengklaimnya.

### Phase 6 — Penulisan Profil Modular

Tulis `<repo>/.claude/profile/frontenddev/` persis mengikuti skema, format, dan batas isi di `templates/profile-template.md` [REQUIRED]:

| Berkas | Isi |
|---|---|
| `index.json` | `project`, `stack`, `platform`, `framework`, `source_root`, `workspace`, `target_app`, `commit_convention` |
| `stack.md` | framework & versi, bahasa & compiler flags, path alias, package manager, router, state, query, styling, UI library |
| `structure.md` | source root, workspace, path fitur, anatomi layer per direktori, shared components, definisi rute |
| `surface-map.md` | permukaan runtime: path kanonik · penanda pengenal kode · bukti |
| `invariants.md` | 6 invariant mutlak; pelanggaran = blocker, bukan gaya |
| `commands.md` | 4 perintah verifikasi + status baseline + cakupan yang TIDAK diperiksa, `typecheck-per-brief`, standar test |
| `layer-adoption.md` | tingkat adopsi 5 layer, aturan arsitektur, persisted state, shared HTTP client |
| `visual.md` | token warna, tipografi, spacing & radius, batas platform |
| `drift.md` | pola warisan → pola modern, tiap baris ber-resep `deteksi` |
| `manual-notes.md` | catatan manual user; satu-satunya berkas yang selamat dari tulis ulang REFRESH |

- Sepuluh berkas ditulis lengkap, tanpa menghilangkan satu pun. Berkas yang datanya nihil tetap ditulis berisi satu baris `tidak terdeteksi`: berkas yang absen tidak dapat dibedakan dari instalasi profil yang gagal di tengah, dan gerbang menolak keduanya dengan pesan yang sama.
- Seluruh kolom `Bukti` diisi anchor `<path>#<simbol>` atau `<path>` telanjang sesuai `## Tata Cara Anchor Bukti` template. Nomor baris dilarang: baris bergeser tanpa suara, sedangkan anchor bersimbol gagal berisik saat simbolnya hilang.
- Field `stack` di `index.json` wajib terisi salah satu dari empat `<stack-id>` sah — `hooks/detect.py` dan seluruh skill hilir memuat adapter dari field itu. `index.json` yang bukan JSON valid mengunci gate sama seperti profil yang tidak ada.
- **Commit atomik penutup**: `git add .claude/profile/frontenddev/` ditambah `.gitignore` bila Phase 5 benar-benar menuliskan baris ke sana, dengan pesan `docs: init frontenddev profile` atau `docs: refresh frontenddev profile`. Mode MIGRATE men-stage `.claude/profile/frontenddev/` plus `.claude/profile/<berkas>` untuk tiap nama di daftar `moved` keluaran `migrate_profile.py --json` (penghapusan di lokasi lama), lalu commit `docs: migrate frontenddev profile`; berkas di daftar `leftovers` tidak di-stage. Profil dan baris ignore-nya masuk **satu** commit; baris yang ditulis lalu tertinggal di luar commit tiba di gerbang Ingest sebagai working tree kotor — persis keadaan yang baris itu ada untuk mencegahnya.
- **WHEN** Phase 5 tidak menuliskan baris apa pun ke `.gitignore`:
  - `THEN`: Commit profilnya saja; jangan men-stage `.gitignore`.

### Phase 7 — Laporan Penutupan & Audit Berkas

1. Konfirmasikan `Ditulis: .claude/profile/frontenddev/ (index.json + 9 berkas .md)` beserta `<stack-id>` dan mode yang dipakai.
2. Rinci seluruh berkas atau kolom berstatus `tidak terdeteksi` beserta dampaknya pada skill hilir — `visual.md` yang kosong membuat `ui-design` memakai fallback sistem, `layer-adoption.md` yang kosong membuat `contract` menebak batas layer. Yang tidak disebut di sini akan ditemukan hilir sebagai kejutan di tengah rantai.
3. Sebutkan jumlah baris `layer-adoption.md` dan `drift.md`, jumlah baris Drift bertanda `[PUNAH]` beserta keputusan user atasnya, dan ringkasan resolusi inkonsistensi yang dikonfirmasi user. Sebutkan eksplisit bila Phase 3 dilewati.
4. Sebutkan status baseline per perintah, termasuk yang `UNVERIFIED_ENV_NOT_READY`.
5. Rekomendasikan gerbang berikutnya: `frontenddev:lead`.

## Guardrails

- **READ-ONLY PROFILING**: Dilarang mengubah atau menghapus file di `src/` selama proses profiling.
- **BUKTI FAKTA KONFIGURASI MUTLAK**: Dilarang mencatat library atau stack tanpa bukti nyata pada file `package.json` atau file konfigurasi framework.
- **LARANGAN BASELINE PALSU**: Dilarang mencatat baseline "OK (0 errors)" tanpa benar-benar menjalankan perintah verifikasi di terminal.
- **INTEGRITAS BERKAS PROFIL**: Dilarang menghilangkan satu pun dari `index.json` dan sembilan berkas `.md`. Berkas berdata nihil tetap ditulis berisi `tidak terdeteksi`; yang absen dibaca gerbang sebagai profil rusak.
- **SATU ADAPTER PER PROFIL**: Resep pemindaian diambil dari satu `stacks/<stack-id>.md`; dilarang mencampur resep stack lain, dan dilarang memprofil repo Next.js.
- **FIELD STACK WAJIB**: Profil tanpa field `stack` valid di `index.json` membuat gate dan seluruh skill hilir gagal memuat adapter; dilarang serah terima dalam keadaan itu.
- **PRESERVASI CATATAN MANUAL**: Pada mode REFRESH, `manual-notes.md` dilarang ditimpa atau dihapus. Berkas itu satu-satunya pengecualian tulis ulang penuh.
- **REFRESH TULIS ULANG PENUH**: Dilarang merge parsial pada mode REFRESH; sembilan berkas selain `manual-notes.md` lahir kembali dari pemindaian segar, dan baris Drift yang resep `deteksi`-nya nol hit dicabut hanya atas persetujuan user.
- **INKONSISTENSI WAJIB DIKLARIFIKASI**: Dilarang memilih sepihak saat pola terbelah tanpa mayoritas; keputusan user diambil di Phase 3. Mode `interview: false` bukan izin memutuskan — ia mewajibkan hasilnya ditandai belum tervalidasi user.
- **REFRESH BUKAN KEPUTUSAN SKILL**: Dilarang menulis ulang profil yang sudah ada tanpa konfirmasi user, kecuali `force: true` disetel pendispatch. `force` tidak pernah berlaku atas profil milik plugin lain atau lokasi lama `.claude/profile/`. Profil memuat keputusan tim yang tidak pernah lahir dari pemindaian; menimpanya diam-diam menghapusnya tanpa jejak.
- **ANCHOR BUKTI TANPA NOMOR BARIS**: Dilarang menulis bukti berbentuk `file:baris` di kolom `Bukti` mana pun; bentuk sahnya `<path>#<simbol>` atau `<path>` telanjang.
- **LOKASI OUTPUT TUNGGAL**: Profil HANYA sah ditulis ke `.claude/profile/frontenddev/`; satu-satunya berkas lain yang boleh disentuh gate ini adalah baris `.frontenddev/` dan `.explore/` di `.gitignore`, dan keduanya di-commit bersama profil.

| Alibi Agen | Realitas Teknis |
|---|---|
| "Pasti pakai Tailwind karena sangat populer di frontend" | Asumsi tanpa bukti merusak styling; repo mungkin memakai StyleSheet, CSS Modules, atau `<style>` scoped. |
| "Baseline verifikasi dijalankan nanti saja saat implementasi" | Tanpa baseline awal, error pre-existing tidak dapat dibedakan dari error regresi baru. |
| "`index.json` cukup berisi `stack`, field lain menyusul" | Hook `detect.py` dan skrip prasyarat `architect` memvalidasi keterisiannya secara ketat; field yang hilang mengunci gate. |
| "Surface Map dan Invariants tidak perlu ditulis lengkap" | Tanpa surface map dan invariants, agen downstream akan menebak struktur dan pola repo. |
| "Sekalian saya perbaiki error typecheck yang ditemukan di src/" | Profiling bersifat read-only. Perbaikan kode wajib melalui brief terencana. |
| "Repo monorepo terlalu besar, cukup catat folder root saja" | Wajib memetakan package `apps/*` agar routing modul di gate lead presisi. |
| "Perintah test tidak perlu dijalankan karena butuh waktu lama" | Melewatkan eksekusi test membuat status baseline palsu dan memicu false alarm. |
| "Saya tahu token warnanya dari ingatan, tidak perlu cek config" | Token warna wajib disalin persis dari konfigurasi tema agar konsisten secara visual. |
| "Pola lama dan baru sama saja, tidak perlu didokumentasikan" | Tanpa dokumentasi drift, agen implementor akan meniru pola usang yang salah. |
| "Konvensi commit pasti standar Conventional Commits" | Banyak repo memiliki format prefix khusus; wajib dicek dari log git nyata. |
| "Berkas profil yang datanya nihil tidak usah ditulis" | Berkas absen tidak dapat dibedakan dari profil yang gagal ditulis di tengah; tulis `tidak terdeteksi`. |
| "Catatan manual user di profil lama saya bersihkan saja" | Catatan manual memuat business context berharga yang ditambahkan oleh developer manusia. |
| "Ini Svelte, tapi resep grep React masih bisa dipakai" | Penanda `use*Page` tidak ada di Svelte; profil berisi nol hit dan hilir menebak. Satu adapter per profil. |
| "Ada `next` di manifest, tapi ada `react` juga, profil saja" | Next.js di luar cakupan plugin; profil yang lahir memaksa gate merutekan repo yang tidak dilayani. |

## Output [REQUIRED]

Artefak `.claude/profile/frontenddev/` mengikuti skema `templates/profile-template.md` — bentuk `index.json`, urutan berkas, bentuk tabel, dan `## Tata Cara Anchor Bukti` diambil dari sana apa adanya, tidak disalin ulang ke sini.

Profil utuh dan baseline terverifikasi → tutup dua baris tanpa blok: judul `### FRONTEND PROFILE REPORT — <GENERATE | REFRESH> · stack <stack-id> · <framework> <version> · index.json + 9 berkas .md` plus baris serah-terima. Selain itu, sajikan:

```markdown
### FRONTEND PROFILE REPORT — <GENERATE | REFRESH> TIDAK UTUH
- **Profil**  : .claude/profile/frontenddev/ (<n>/10 berkas ditulis) · stack <stack-id | tidak terdeteksi>
- **Baseline**: <perintah yang FAIL | UNVERIFIED_ENV_NOT_READY | TIMEOUT> — <pesan galat>
- **Gap**     : berkas `tidak terdeteksi` <daftar> · inkonsistensi belum tervalidasi <daftar>
- **Drift**   : <n> baris · <n> `[PUNAH]` <dicabut | dipertahankan atas keputusan user>
```

Isi profil — surface map, invariant, layer adoption — sengaja tidak disalin ke laporan: skill yang membutuhkannya membaca berkasnya sendiri saat rutenya jalan, supaya yang terbaca selalu versi terakhir.

**Serah-terima.** `"Profil codebase selesai ditulis di .claude/profile/frontenddev/ (stack: <stack-id>) — siap digunakan oleh frontenddev:lead."`

## Failure path

| Kondisi | Tindakan |
|---|---|
| Manifest tidak ditemukan | Hentikan; laporkan target bukan proyek frontend Node.js yang valid. Jangan buat berkas apa pun. |
| Manifest rusak | Laporkan pesan kegagalan parsing beserta path manifest-nya dan minta user memverifikasi integritasnya. Manifest yang tidak dapat di-parse terbaca sebagai nol dependensi, dan repo yang benar divonis "di luar cakupan". |
| Stack tidak terdeteksi | Hentikan di Phase 0, sebutkan manifest yang diperiksa, jangan buat berkas apa pun. |
| Manifest memuat `next` | Hentikan; Next.js di luar cakupan plugin. Profil yang lahir memaksa gate merutekan repo yang tidak dilayani adapter mana pun. |
| Stack ambigu di monorepo | Minta user memilih satu `<stack-id>` utama lewat `stack` dan `target_app`. |
| Adapter `stacks/<stack-id>.md` tidak ada | Hentikan dan laporkan stack belum didukung plugin. |
| Perintah verifikasi macet (> 5 menit) | Batalkan proses terminal, catat `TIMEOUT / UNVERIFIED` di baseline, lanjutkan pemindaian layer statis. |
| Konflik dependensi ekstrem | Multipaket bersaing (`jest` dan `vitest` tanpa script terdefinisi, dua library router): catat ambiguitasnya di `## Drift & Competing Patterns` dan minta konfirmasi user saat handoff. |
| Izin tulis `.claude/` gagal | Laporkan kendala izin sebelum mencoba kembali; jangan tulis profil parsial. |
| Profil lama tidak dapat ditimpa | REFRESH menulis ulang penuh. Laporkan berkasnya read-only dan minta user memberi izin tulis atau menghapusnya; dilarang menulis profil ke path alternatif. |
| Konfirmasi REFRESH ditolak | Batalkan tanpa mengubah profil eksisting maupun `.gitignore`. Laporkan bahwa profil lama tetap berlaku apa adanya. |
| User tidak menjawab wawancara Phase 3 | Lanjutkan dengan hasil pemindaian, tandai `layer-adoption.md` dan `drift.md` belum tervalidasi user di `manual-notes.md`, dan sebutkan di laporan Phase 7. |
| Repositori non-git | Lanjutkan profiling; tulis field `commit_convention` `index.json` sebagai `UNINITIALIZED (default conventional commits)` dan sebutkan bahwa baris `.gitignore` tidak dapat dipasang. |

## STYLE

- Gunakan kalimat imperatif aktif dan format observable predicate pada setiap instruksi pemindaian.
- Pertahankan nama berkas dan nama heading profil persis sesuai skema `templates/profile-template.md` tanpa modifikasi, dan tulis `index.json` dalam JSON valid.
- Sajikan bukti temuan konfigurasi dan baris log terminal secara ringkas dan faktual.

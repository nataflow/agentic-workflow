---
name: profile
description: Gunakan ketika repo backend belum punya .claude/profile/backenddev/ atau konfigurasi berubah - deteksi stack, pemindaian arsitektur, sebelum mengedit kode atau menjalankan task tanpa profile
metadata:
  mode: standard
---

## THE IRON LAW

- Tulis fakta apa adanya; dilarang mengarang asumsi tanpa bukti konfigurasi aktual.
- Baris konvensi wajib bercontoh anchor `<file>#<simbol>`, baris anti-pattern bersumber repo wajib ber-`deteksi` yang berhit dan baris bersumber user wajib bertanda `bukti user`; yang tidak terbukti dihapus, bukan ditebak dari kelaziman stack.
- Setiap perintah di `commands.md` wajib dieksekusi minimal sekali sebelum ditulis ke profil.
- Profiling read-only mutlak: dilarang mengubah, membuat, atau memperbaiki kode di source root.
- Profil hanya sah ditulis ke `.claude/profile/backenddev/` (`index.json` + 8 berkas `.md`), wajib memuat field `stack`, dan pada mode refresh ditulis ulang penuh tanpa merge parsial.

## Precondition [REQUIRED]

1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/profile/scripts/check_preconditions.py [--mode <mode>] [--stack <stack>] [--profile-dir <profile_dir>]`.
2. `PASS` (6/6 checks): lanjut ke Workflow; baris `Terselesaikan: mode <GENERATE | REFRESH | MIGRATE>` adalah mode Fase 1. `FAIL`: hentikan dan remediasi butir yang gagal — nol penanda framework server backend → repo bukan target backenddev, jangan buat profil; `--profile-dir` selain `.claude/profile/backenddev` → jalankan ulang tanpa parameter itu; `.claude/profile/backenddev/index.json` milik plugin lain → laporkan ke user, jangan ditimpa; adapter stack hilang → pulihkan berkas plugin; direktori profil tidak dapat ditulis → periksa izin; bukan repo git → inisialisasi git.

## Parameter [REQUIRED]

- `mode` — string — default `"auto"` — `"auto"` | `"generate"` | `"refresh"` | `"migrate"`. Keadaan disk yang dilaporkan skrip prasyarat selalu menang.
- `stack` — string — default `"auto"` — paksa `<stack-id>` bila deteksi Fase 0 ambigu; nilai sah = daftar di `stacks/_CONTRACT.md`.
- `force` — boolean — default `false` — bila `true`, Fase 1 melewati konfirmasi REFRESH dan langsung menulis ulang. `force` tidak pernah berlaku atas profil milik plugin lain atau lokasi lama `.claude/profile/`; keduanya ditolak prasyarat atau dialihkan ke MIGRATE.
- `profile_dir` — string — default `".claude/profile/backenddev"` — target tulis Fase 6; nilai lain ditolak.
- `interview` — boolean — default `true` — bila `false`, Fase 3 dilewati; `code-conventions.md` dan `anti-patterns.md` diisi hasil scan saja, ditandai belum tervalidasi user.
- `reported_anti_patterns` — list — default `[]` — Preseden menyesatkan yang ditemukan **eksekusi**, diteruskan gerbang dari slot `Umpan balik profil` laporan `backenddev:architect`: tiap entri berisi `file:baris` beserta polanya. Sapuan statis tidak menemukan pola ini — ia baru terbukti saat brief menyalinnya sebagai preseden lalu `code-implementor` terhenti. Fase 3 menyajikannya ke user untuk konfirmasi; yang disetujui masuk `anti-patterns.md` sebagai baris ber-`deteksi` dan sejak itu ditegakkan Check P `plan`. Yang ditolak dibuang, tidak disimpan sebagai catatan.

## Workflow

Pemindaian profil codebase dieksekusi sekuensial melalui 8 fase:

### Fase 0 — Deteksi Stack & Resolusi Adapter

1. Jalankan `check_preconditions.py` dengan parameter `mode`, `stack`, dan `profile_dir`. Hentikan bila hasilnya `FAIL`.
2. Check 1 skrip prasyarat memanggil `hooks/detect.py` (fungsi yang sama dengan hook SessionStart) atas root, workspace terdeklarasi (`workspaces`, `pnpm-workspace.yaml`, `go.work`, Cargo `members`), `apps/*`, `packages/*`, `services/*`, dan anak langsung root. Penanda framework server yang dicocokkan:
   - `pom.xml` (`groupId` `org.springframework.boot`) atau `build.gradle(.kts)`/`gradle/libs.versions.toml` memuat `org.springframework.boot` di luar komentar → `java-spring`
   - `go.mod` `require` (tanpa `// indirect`) memuat `github.com/gin-gonic/gin`, `github.com/gofiber/fiber`, `github.com/labstack/echo`, `github.com/go-chi/chi`, `github.com/gorilla/mux`, atau `google.golang.org/grpc` (termasuk sufiks `/vN`) → `go`
   - `package.json` — hanya dari `dependencies`, bukan `devDependencies`/`overrides`/`keywords`: `elysia`, atau `hono` bersama `bun.lockb`/`bun.lock`/`bunfig.toml` (dan tanpa `@nestjs/core`/`express`) → `bun`; selain itu `@nestjs/core`/`express`/`fastify`/`koa`/`@hapi/hapi`/`hono` → `node`
   - `Cargo.toml` `[dependencies]` + `axum`/`actix-web`/`rocket`/`warp`/`poem`/`salvo` → `rust`
   - `composer.json` `require` + `codeigniter4/framework` → `php-codeigniter`; selain itu `laravel/framework`/`symfony/framework-bundle`/`slim/slim`/`laminas/laminas-mvc`/`yiisoft/yii2` → `php`
3. Evaluasi hasil deteksi:
   - Pakai nilai eksplisit parameter `stack` bila disetel; catat penanda pendukung maupun yang bertentangan.
   - Nol stack: hentikan, sebutkan manifest yang diperiksa. Dilarang membuat profil palsu pada repo non-backend.
   - Lebih dari satu stack (monorepo polyglot): minta user memilih satu `<stack-id>` utama.
4. Baca `stacks/<stack-id>.md`: `## Detection` jadi pemutus bila penanda butir 2 kabur; `## Commands` dan `## Layer taxonomy` dipakai di Fase 2 dan 4. Adapter tidak ada: hentikan, laporkan stack belum didukung; dilarang memprofil dengan asumsi stack lain.

### Fase 1 — Deteksi Mode Operasi & Konfirmasi Pengguna

1. Ambil mode dari baris `Terselesaikan:` skrip prasyarat (check 6 "Mode & kepemilikan profil"):
   - `GENERATE` (`.claude/profile/backenddev/index.json` belum ada): lanjut ke Fase 2 tanpa konfirmasi. Bila check 6 menyebut profil lama milik plugin lain di `.claude/profile/`, biarkan berkas itu; jangan dibaca sebagai profil backenddev, jangan ditimpa.
   - `REFRESH` (`.claude/profile/backenddev/index.json` ada dan milik backenddev): tampilkan ringkasan profil saat ini, lalu minta konfirmasi "Lakukan REFRESH (tulis ulang penuh) atau BATAL?". Hentikan menunggu respons bila `force: false`.
   - `MIGRATE` (profil backenddev masih di lokasi lama `.claude/profile/index.json`): jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/profile/scripts/migrate_profile.py`, laporkan berkas sisa di `.claude/profile/` sebagai **bukan milik plugin ini — tidak disentuh**, lalu lanjut ke Fase 7 tanpa pemindaian ulang. Sebut juga di laporan: profil backenddev yang pernah tertimpa plugin lain dapat dipulihkan dari riwayat `git log --oneline -- .claude/profile/index.json`. Commit pemindahan (termasuk penghapusan di lokasi lama) dikunci gerbang `backenddev:tech-lead` di Fase 5-nya.
2. Abaikan seluruh isi profil lama saat memindai bila REFRESH disetujui; tulis hasil scan baru utuh tanpa merge parsial.
3. Laporkan perubahan stack sebagai temuan tersendiri sebelum menulis ulang bila profil lama memuat `stack` berbeda dari hasil Fase 0.

### Fase 2 — Pemindaian Menyeluruh 17 Titik Arsitektur Codebase

Jalankan tiap titik memakai resep di `references/scan-guide.md` (titik 1–14) dan `references/convention-scan.md` (titik 15–17); resep spesifik stack diambil dari `stacks/<stack-id>.md`.

- Titik 1–14: build configuration · entrypoint & source root · module structure dan gaya arsitektur · module anatomy per layer · configuration dan env wajib · database migration blueprint · build & test commands · boundary scoping konteks request/tenant · mirrored runtime paths non-HTTP · commit convention (`git log -n 20 --oneline`) · root instructions (`CLAUDE.md`/`AGENTS.md`) · runtime timezone · branch configuration · surface map permukaan aktif.
- Titik 15–17: domain map modul bisnis · code conventions per aspek kanonik · anti-patterns yang masih hidup di kode.

Muara tiap titik ke berkas profil ditetapkan oleh judul seksi di kedua berkas referensi itu. Catat setiap fakta bersama anchor konkret (`<file>#<simbol>`); tulis `tidak terdeteksi` bila fakta nihil. Catat inkonsistensi arsitektur antar-modul dan sampel gaya yang terbelah tanpa mayoritas (Gaya A vs Gaya B) sebagai bahan wawancara Fase 3.

### Fase 3 — Wawancara Inkonsistensi, Konvensi & Anti-pattern

1. Ajukan pertanyaan terarah untuk membakukan satu gaya standar repo atas tiap inkonsistensi arsitektur atau konvensi (Gaya A vs Gaya B). Dilarang memutuskan sepihak.
2. Sajikan draf titik 16 dan 17 sebagai daftar terstruktur, lalu ajukan satu putaran konfirmasi: butir mana yang ditambah, dicabut, atau diralat.
3. Jalankan `deteksi` tiap baris `anti-patterns.md` profil lama pada mode `REFRESH`, lalu sajikan sebagai kandidat bervonis `[MASIH HIDUP — <n> hit]` atau `[PUNAH — 0 hit]` agar pengetahuan sebelumnya tidak hilang. Baris punah dicabut hanya atas keputusan user, bukan sepihak.
4. Sajikan tiap entri `reported_anti_patterns` sebagai kandidat bervonis `[DARI EKSEKUSI — <file:baris>]` beserta pola dan sebab terhentinya. Entri ini datang dari rantai eksekusi yang benar-benar tersandung preseden itu, bukan dari sapuan statis — sapuan tidak pernah menemukannya karena polanya sah secara sintaks dan hanya salah sebagai teladan. Yang disetujui user ditulis ke `anti-patterns.md` sebagai baris ber-`deteksi`; susun resep `deteksi`-nya dari pola entri lalu verifikasi ia menghasilkan minimal satu hit, dan turunkan ke `bukti user` bila nol hit. Yang ditolak dibuang.
5. Lanjut dengan hasil scan apa adanya dan catat di Fase 7 bahwa validasi user dilewati bila `interview: false` atau user tidak menjawab. Entri `reported_anti_patterns` pada mode itu tetap ditulis, ditandai belum tervalidasi user.
6. Masukkan gaya pilihan user ke `code-conventions.md`; masukkan gaya yang dieliminasi ke `anti-patterns.md` bertanda `bukti user`.

### Fase 4 — Eksekusi Baseline Verifikasi Nyata

Uji enam perintah hasil Fase 2 titik 7 sebelum ditulis ke `commands.md`:

1. Eksekusi berurutan `build`, `typecheck`, `lint`, `test`, `test-single`, `migration`. Tulis `tidak berlaku` bila perintah tidak berlaku di stack ini. Baris `typecheck-scoped` dan `typecheck-per-brief` **disalin dari adapter tanpa dieksekusi** — keduanya menjawab cara pemakaian, bukan status jalan (`references/scan-guide.md`).
2. Catat status tiap perintah: `OK` (exit 0), `FAIL` (exit bukan 0), atau `UNVERIFIED_ENV_NOT_READY` bila kegagalan berasal dari dependensi belum terpasang.
3. Perbaiki perintahnya lalu uji ulang bila gagal karena sintaks salah (bukan karena kodenya merah). Tulis `tidak terdeteksi` bila tetap salah sintaks.
4. Dilarang memperbaiki kode sumber agar baseline hijau.

### Fase 5 — Verifikasi State Git & Pemasangan Gitignore

Satu-satunya berkas di luar `.claude/profile/backenddev/` yang boleh disentuh adalah `.gitignore`:

1. `git rev-parse --git-dir`. Bila gagal, catat status non-git dan tulis `commit_convention`, `base_branch`, serta `branch_convention` sebagai `tidak terdeteksi`.
2. `git check-ignore -q backenddev`. Bila exit code 0, peringatkan bahwa artefak `backenddev/` berstatus lokal dan tidak di-track git.
3. `git check-ignore -q .backenddev`. Bila exit code bukan 0, tambahkan baris `.backenddev/` di akhir `.gitignore` akar repo (buat berkas bila belum ada); lewati bila exit code 0.
4. `git check-ignore -q backenddev/docs/x/.explore/y`. Bila exit code bukan 0, tambahkan baris `.explore/` di akhir `.gitignore` akar repo; lewati bila exit code 0.

   Laci `.explore/` adalah zona kerja `code-explorer` beserta berkas kerja `plan` (`brief-matrix.*`, `brief-review-state.json`). Ia hidup **di dalam taskdir** supaya laporannya ko-lokasi dengan artefak yang lahir darinya — `plan` Fase 3 langkah 3 memanennya ulang tepat sebelum mengisi `## File scope`. Konsekuensinya ia berkas untracked di dalam direktori yang ter-track, dan tanpa baris ignore ini ia muncul di tiap `git status --porcelain`: `architect` menolak start karena working tree kotor, dan siapa pun yang menambal baris ignore itu belakangan menghasilkan commit tanpa brief pengklaim yang dihukum `code-reviewer` sebagai temuan. Satu baris berpemilik di sini menutup ketiganya. Pola tanpa awalan path sekaligus mencakup laci gerbang di `backenddev/docs/.explore/`.

5. **Laporkan `.gitignore` sebagai artefak yang menunggu commit.** Skill ini menulis barisnya tetapi tidak meng-commit-nya sendiri — penguncian artefak profil milik gerbang `backenddev:tech-lead` di Fase 5-nya. Sebut path `.gitignore` eksplisit di slot `Artefak` laporan penutup, sejajar dengan berkas `.claude/profile/backenddev/`, supaya gerbang menariknya ke dalam commit yang sama. Baris yang ditulis lalu tidak ikut ter-commit tiba di `architect` sebagai working tree kotor — persis keadaan yang ia ada untuk mencegahnya.

### Fase 6 — Penyusunan & Penulisan Dokumen Profil Modular

Tulis `<repo>/.claude/profile/backenddev/` persis mengikuti skema, format, dan batas baris di `templates/profile-template.md`:

| Berkas | Isi |
|---|---|
| `index.json` | `project`, `stack`, `architecture`, `root_namespace`, `source_root`, `commit_convention`, `base_branch`, `branch_convention` |
| `stack.md` | framework, bahasa/runtime, package manager & lockfile, database & migration tool, messaging, cache, websocket, codegen |
| `module-structure.md` | pola pengelompokan modul, arsitektur layer + bukti, anatomi layer per taksonomi adapter, tipe batas, shared modules |
| `domain-map.md` | modul bisnis: path · permukaan aktif · entry `<file>#<simbol>` |
| `surface-map.md` | permukaan aktif: path · penanda · catatan |
| `code-conventions.md` | keputusan gaya per aspek kanonik, tiap baris berakhir `contoh <file#simbol>` |
| `anti-patterns.md` | pola terlarang → pengganti · `deteksi` + bukti `<file#simbol>`, atau `bukti user` tanpa `deteksi` |
| `invariants.md` | timezone, boundary scoping, transaction boundaries, mirrored runtime paths, env gates |
| `commands.md` | 6 perintah kanonik + status uji sintaks, blueprint folder & pola berkas migrasi |

### Fase 7 — Laporan Penutupan & Audit Missing Fields

1. Konfirmasikan `Ditulis: .claude/profile/backenddev/ (index.json + 8 berkas .md)`.
2. Rinci seluruh field atau seksi berstatus `tidak terdeteksi` beserta dampaknya pada skill hilir.
3. Sebutkan jumlah baris `domain-map.md`, `code-conventions.md`, `anti-patterns.md`, jumlah baris anti-pattern bertanda `[PUNAH]` beserta keputusan user atasnya, dan ringkasan resolusi inkonsistensi yang dikonfirmasi user.
4. Rekomendasikan gerbang berikutnya: `backenddev:tech-lead`.

## Guardrails

- **READ-ONLY KODE SUMBER**: dilarang membuat, mengedit, memformat, atau menghapus berkas kode sumber selama profiling.
- **BUKTI KONFIGURASI AKTUAL**: dilarang mencatat dependensi, versi runtime, atau invariant dari tebakan tanpa bukti manifest atau konfigurasi nyata.
- **OUTPUT MODULAR TUNGGAL**: profil HANYA ditulis ke `.claude/profile/backenddev/`; satu-satunya tulisan lain yang sah adalah baris `.backenddev/` dan `.explore/` pada `.gitignore` (Fase 5), dan keduanya dilaporkan ke gerbang sebagai artefak yang menunggu commit. Skill ini **pemilik tunggal** mutasi `.gitignore` di seluruh rantai: skrip `plan`, `architect`, dan gerbang dilarang menambahkan barisnya sendiri, karena baris tak berpemilik tiba di hilir sebagai working tree kotor lalu berakhir jadi commit tanpa brief pengklaim.
- **FIELD STACK WAJIB**: profil tanpa `stack` valid di `index.json` membuat skill hilir gagal memuat adapter; dilarang serah terima dalam keadaan itu.
- **REWRITE PENUH PADA REFRESH**: tulis ulang 100% dokumen dari pemindaian segar; dilarang merge parsial.
- **INKONSISTENSI WAJIB DIKLARIFIKASI**: dilarang memilih sepihak saat pola terbelah Gaya A vs Gaya B; keputusan user diambil di Fase 3.
- **ANCHOR TANPA NOMOR BARIS**: seluruh bukti ditulis `<file>#<simbol>` atau `<file>` telanjang; nomor baris dilarang karena ia bergeser diam-diam lalu tetap menunjuk ke baris keliru.
- **DILARANG DATA DINAMIS**: dilarang menyimpan high-water mark migrasi, daftar endpoint konkret, atau error count transient.
- **KEPUTUSAN DEFINITIF SAAT INI**: isi dokumen berprinsip "Yang ditulis = Keputusan saat ini" tanpa memori temporal atau komparasi masa lalu.

## Output [REQUIRED]

Artefak `.claude/profile/backenddev/` mengikuti `templates/profile-template.md`. Profil utuh dan baseline terverifikasi → tutup dua baris tanpa blok: judul `### BACKEND PROFILE GENERATION REPORT — <GENERATE | REFRESH | MIGRATE> · stack <stack-id> · <framework> <version> · index.json + 8 berkas .md` plus slot `Menunggu commit`. Selain itu, sajikan:

```markdown
### BACKEND PROFILE GENERATION REPORT — <GENERATE | REFRESH | MIGRATE> TIDAK UTUH
- **Profil**  : .claude/profile/backenddev/ (<n> berkas ditulis) · stack <stack-id | tidak terdeteksi>
- **Baseline**: <perintah yang FAIL | UNVERIFIED_ENV_NOT_READY> — <pesan galat>
- **Gap**     : inkonsistensi <daftar> · field tak terdeteksi <daftar>
- **Menunggu commit**: `.claude/profile/backenddev/` (<n> berkas) · `.gitignore` (<baris `.backenddev/` dan/atau `.explore/` ditambahkan | tidak disentuh>)
```

`Menunggu commit` wajib di kedua bentuk: gerbang meng-stage **persis** path yang disebutnya, dan `.gitignore` yang tertinggal di luar commit profil tiba di `architect` sebagai working tree kotor. Isi profil — arsitektur, konvensi, invariant, blueprint — sengaja tidak disalin ke laporan: skill yang membutuhkannya membaca berkasnya sendiri saat rutenya jalan, supaya yang terbaca selalu versi terakhir.

**Serah-terima.** `Profil codebase selesai ditulis di .claude/profile/backenddev/` — kembali ke `backenddev:tech-lead` di main loop. Profil belum di-commit; gerbang yang menutupnya.

## Failure path

| Kondisi | Tindakan |
|---|---|
| Stack tidak terdeteksi | Hentikan di Fase 0, sebutkan manifest yang diperiksa, jangan membuat berkas apa pun. |
| Adapter `stacks/<stack-id>.md` tidak ada | Hentikan dan laporkan stack belum didukung plugin. |
| Stack ambigu di monorepo | Minta user memilih satu `<stack-id>` utama. |
| Manifest rusak | Laporkan pesan kegagalan parsing dan minta user memverifikasi integritas manifest. |
| Konfirmasi REFRESH ditolak | Batalkan tanpa mengubah profil eksisting. |
| Baseline tidak dapat dieksekusi | Catat `UNVERIFIED_ENV_NOT_READY`, instruksikan pemasangan dependensi, tetap tulis profil dengan status itu terpampang. |
| Repositori non-git | Lanjutkan dengan field konvensi git `tidak terdeteksi` dan peringatan kebutuhan input manual. |
| Izin tulis gagal | Laporkan kendala izin pada `.claude/profile/backenddev/` sebelum mencoba kembali. |

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack yang terdeteksi.
- Tulis metadata dalam JSON valid (`index.json`) dan seksi dalam markdown yang rapi.

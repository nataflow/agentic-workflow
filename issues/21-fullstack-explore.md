# Langkah 21 — Plugin `fullstack`: peta aplikasi perusahaan dan explore permukaan lintas repo (F1–F10, D1)

Sumber: permintaan user 2026-10-13 ("plugin fullstack, khusus explore, running di root folder project … bisa pakai
profile milik frontend dan backend untuk explore code") dan susulan di sesi yang sama: multi-proyek ("kalo misal
multi project bisa juga?"), API to API ("ada komunikasi api to api … tolong siapkan juga"), lalu penegasan tujuan
("ga harus komunikasi api to api sih, tapi supaya fleksibel aja bisa banyak project sekaligus di 1 company, jadi bisa
paham semua aplikasi di 1 company"). Basis kode plugin: commit `3a66412` (backend 0.13.2, frontend 0.12.2).

**Status (2026-10-13):** F1–F10 dan D1 selesai. Test baru: `tests/hooks/test_workspace_root_21.py` (9),
`tests/fullstack/test_workspace_21.py` (26), `test_explore_21.py` (37), `test_skill_21.py` (10),
`test_profile_anchor_21.py` (6), ditambah sembilan kasus smoke. Suite penuh hijau (2446), subset fullstack/hooks/smoke
hijau di Python 3.9, lint `--base main` 0 FAIL, dan `claude plugin validate .` lolos. Versi: fullstack 0.1.0 (baru),
backend 0.14.0, frontend 0.13.0. Diuji juga terhadap root `nataflow/` sungguhan: gerbang hanya menunjuk repo,
`peta` membaca profil asli (`backend` tertinggal 56 commit `internal/`, `frontend` 8 commit `src/`).

Selisih pelaksanaan terhadap Kontrak di bawah:

- **Letak skrip.** `workspace.py`, `explore.py`, dan pustaka `fullstack_lib.py` tinggal di `skills/_common/` (pola
  `product`); hanya `check_preconditions.py` di `skills/explore/scripts/`.
- **`explore.py new` (tambahan).** Kerangka laporan dibuat skrip dari `templates/explore-template.md`: frontmatter
  (`slug`, `objective`, `dibuat`, `lingkup`, `repo@sha`) dan tabel `## Repo` terisi dari `scan`, `confidence` kosong
  sampai diisi skill. Model tidak mengetik SHA atau stamp sendiri.
- **`seam --write` (tambahan).** Tabel `## Jahitan` ditulis langsung ke laporan; check 4 tetap menghitung ulang.
- **Status profil `TIDAK_SAH` (tambahan).** `index.json` sah tetapi `stack` kosong atau `plugin` milik lain; diarahkan
  ke REFRESH seperti `INVALID_JSON`.
- **Jangkar FE.** Template `surface-map.md` frontend tidak punya baris **HTTP Service** dan **DTO** (profil nataflow
  menambahkannya sendiri). Scout FE membaca baris kanonik **Routing & Navigation**, **Data Fetching & Cache**,
  **Shared HTTP Client**, **Framework Boundary**, ditambah `layer-adoption.md` (**HTTP Service Layer**, **DTO
  Isolation**) dan sub-butir `services/`/`dto/` di **Features Path**. F9 menjaga jangkar itu.
- **Tabel `## Repo`.** Memuat repo yang disisir dan repo di proyek lingkup yang profilnya ada tetapi tidak `VALID`.
  Repo tanpa profil sama sekali (pustaka, infra) cukup di `PETA.md` `## Belum terpetakan`, supaya tiap laporan tidak
  wajib menulis arahan untuk repo yang mungkin bukan aplikasi.
- **Komentar template.** Komentar HTML dibuang dari badan seksi saat laporan di-parse; seksi yang hanya berisi
  komentar dihitung kosong, dan contoh tabel di dalam komentar tidak terbaca sebagai tabel.
- **Rujukan `path:baris`.** Check 3 hanya menilai token ber-backtick yang memuat `/` (mis.
  `` `wms/api/x.go:12` ``), sehingga jam `10:30` dan `localhost:8080` tidak ikut dinilai.
- **Prasyarat.** `layanan.json` rusak dan root di atas plafon 60 repo menjadi WARN, bukan FAIL; jalur `PETA` tetap
  jalan.
- **F1.** `Verdict` mendapat `workspace` dan `workspace_size`, `source` bernilai `workspace`. Root multi-repo tanpa
  anak milik plugin itu tetap diam. `gate_text.render` memakai `getattr` karena test lama memanggilnya dengan
  `SimpleNamespace` tanpa field baru.
- **D1.** Versi `analyst` di tabel README root dikoreksi ke 0.16.0 (sebelumnya tertinggal 0.15.0).

## Tujuan

1. Dari satu root, user bisa memahami **semua aplikasi di satu perusahaan**: proyek apa saja yang ada, repo dan
   stack-nya, domain bisnis tiap backend, fitur dan rute tiap frontend, serta aplikasi mana yang berhubungan dengan
   aplikasi mana. Root bisa berbentuk satu proyek (`wms/{api,frontend}`) atau banyak proyek
   (`company/{wms,erp,crm}/{api,frontend}`).
2. Peta perusahaan itu murah dan bisa diulang kapan saja: dibangun skrip dari profil, tanpa scout dan tanpa membaca
   kode, sehingga tetap ringan untuk puluhan repo.
3. Untuk pertanyaan konkret, explore turun ke kode secara permukaan dan memetakan jahitannya: frontend → backend di
   dalam satu proyek, dan backend → backend (API to API) bila memang ada. API to API adalah kemampuan tambahan,
   bukan prasyarat.
4. Penelusuran berpijak pada profil yang sudah dibuat `backend:profile` dan `frontend:profile` di tiap repo, bukan
   pada pemindaian liar.
5. Hasil tersimpan di `<root>/.fullstack/`: `PETA.md` (peta hidup, ditulis ulang tiap kali dibangun), laporan
   explore di `explore/`, dan pemetaan layanan yang sudah dikonfirmasi user di `layanan.json`.
6. Plugin `backend` dan `frontend` berhenti menggerbangi root multi-repo, tempat precondition keduanya pasti gagal.

## Temuan awal (dasar keputusan)

Diverifikasi di sesi desain dengan menjalankan hook terhadap folder `nataflow/` (bentuk satu proyek), fixture
scratch `root/{wms,lain}/{api,frontend}` (bentuk multi-proyek), dan membaca profil `nataflow/backend` serta
`nataflow/frontend`:

- **Root satu proyek: dua gerbang menyala sekaligus.** `detect.py --plugin backend` dan `--plugin frontend`
  sama-sama meng-emit blok gerbang. `resolve_root` jatuh ke cwd ketika `git rev-parse` gagal, lalu `candidate_dirs`
  ikut menyisir anak langsung root. Keduanya mengklaim "jalan lebih dulu", padahal precondition `tech-lead` dan
  `lead` gagal di folder tanpa `.git`.
- **Root multi-proyek: kedua gerbang diam.** Manifest berada dua tingkat di bawah root, di luar jangkauan
  `candidate_dirs`. Tidak perlu perubahan hook untuk bentuk ini.
- **Status profil di root salah.** Gerbang melapor profil "BELUM ADA", karena `read_profile` hanya membaca
  `<root>/.claude/profile/`, sementara manifest yang memicu emit ditemukan di folder anak.
- **`code-explorer` milik backend/frontend tidak bisa dipinjam dari root.** `explorer_hook`
  (`backend/hooks/guard_bash.py`) memanggil `repo_root()`, yang melempar galat di folder non-git. Karena pagarnya
  fail-closed, Write laporan explorer ditolak. Kontrak dispatch-nya juga terikat ke laci taskdir, dan kedalamannya
  `menyeluruh`, bukan permukaan.
- **Profil backend bisa dibaca mekanis.** `domain-map.md` berformat baris tetap
  `<domain>: <path> · <permukaan+permukaan> · entry <file>#<simbol>`, maksimal 12 baris
  (`skills/profile/references/convention-scan.md` titik 15). `surface-map.md` berformat
  `<permukaan>: <path> · <penanda> · <catatan>` dengan dua belas kunci kanonik, termasuk `http`, `external`, dan
  `config` (`skills/profile/references/scan-guide.md` titik 14). Baris yang tidak ada berarti permukaan itu tidak
  terdeteksi saat profil dibuat.
- **Profil frontend hanya sebagian bisa dibaca mekanis.** `index.json` (`project`, `stack`, `platform`, `framework`,
  `source_root`, `workspace`) terstruktur. `structure.md` berupa prosa, tetapi template-nya mewajibkan butir
  `**Features Path**` dan `**Route Definitions**`, yang bisa dikutip apa adanya. Baris tabel `surface-map.md` punya
  nama permukaan baku di kolom pertama.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | F1 (`detect.py` + `gate_text.py` backend/frontend) | Root satu proyek harus bebas gerbang dulu; tanpa ini sesi `fullstack` di sana selalu dibuka dua gerbang yang salah. |
| 2 | F2 (`workspace.py scan`), F3 (`workspace.py peta`) | Peta perusahaan adalah nilai utama plugin dan sudah berguna tanpa scout. |
| 3 | F4 (`explore.py list/check`), F5 (`explore.py seam`), F6 (`explore.py layanan`) | Pagar mesin explore lebih dulu; prosa skill berdiri di atas keluaran skrip. |
| 4 | F7 (`repo-scout` + dispatcher) | Kontrak balikan scout menjadi masukan `seam` dan `check`. |
| 5 | F8 (skill `fullstack:explore` + precondition) | Merangkai F2–F7. |
| 6 | F9 (test jangkar profil), F10 (smoke), D1 (dokumen + versi) | Penutup. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada dan
harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| F1 | `backend/hooks/detect.py` dan `frontend/hooks/detect.py` (byte-identical), `backend/hooks/gate_text.py`, `frontend/hooks/gate_text.py` | hook SessionStart kedua plugin, precondition yang mengimpor `detect.py` (`precondition_lib.py`) | **ya** (backend + frontend) | `tests/hooks/test_detect.py` (kunci `--explain`), `tests/hooks/test_gate_text.py`, test kesamaan byte `detect.py` | Sedang: cabang baru hanya aktif bila root bukan repo git dan punya ≥2 anak ber-`.git`; repo tunggal tidak berubah satu byte pun keluarannya. |
| F2 | `fullstack/skills/explore/scripts/workspace.py` (baru: `scan`) | F3–F6, F8 | tidak | — | Nihil (baru) |
| F3 | `fullstack/skills/explore/scripts/workspace.py` (`peta`) | F8, user | membaca profil backend/frontend | — | Nihil (baru) |
| F4 | `fullstack/skills/explore/scripts/explore.py` (baru: `list`, `check`) | F8 | tidak | — | Nihil (baru) |
| F5 | `fullstack/skills/explore/scripts/explore.py` (`seam`) | F4 `check`, F8 | tidak | — | Nihil (baru) |
| F6 | `fullstack/skills/explore/scripts/explore.py` (`layanan`) | F3, F5, F8 | tidak | — | Nihil (baru) |
| F7 | `fullstack/agents/repo-scout.md`, `fullstack/skills/explore/dispatcher/scout.md` (baru) | F8 | tidak | — | Nihil (baru) |
| F8 | `fullstack/skills/explore/SKILL.md`, `scripts/check_preconditions.py`, `templates/explore-template.md` (baru) | model | tidak | — | Nihil (baru) |
| F9 | `tests/fullstack/test_profile_anchor_21.py` (baru) | CI | membaca berkas profil backend/frontend | — | Nihil |
| F10 | `tests/test_smoke.py` (`CASES`) | CI | tidak | `test_smoke.py` | Rendah |
| D1 | `fullstack/README.md`, `flow/fullstack.md` (baru), `flow/backend.md`, `flow/frontend.md` (hook), `plugin.json` ×3, `marketplace.json`, `README.md` root, `CLAUDE.md` repo | manusia, lint M4/M7 | ya | `test_lint_plugins.py` | Nihil |

**Tidak diubah:**
- `guard_bash.py` backend/frontend. `repo-scout` tidak punya tool Write, jadi tidak butuh pagar; laporan ditulis
  konteks utama dan `PETA.md` ditulis skrip.
- `code-explorer`, `read_profile`, format profil, dan semua skill backend/frontend selain teks gerbang.
- Plugin `analyst`, `product`, `quickdev`, `nataflow`.

## Keputusan

### Bentuk plugin

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Plugin baru `fullstack`**, satu skill `fullstack:explore`, model-invocable. | Read-only dan tanpa artefak di repo anak, jadi aman dipicu model. Skill lain belum dibutuhkan. |
| K2 | **Hanya berjalan di root multi-repo**: cwd bukan bagian repo git, dan minimal satu repo di bawahnya punya profil valid. Di dalam repo, precondition FAIL dengan arahan ke `backend:tech-lead`/`frontend:lead`. | Di dalam repo sudah ada `code-explorer` yang lebih dalam. Monorepo satu-git di luar cakupan. |
| K3 | **Profil wajib, bukan opsional.** Repo tanpa profil (atau profil lokasi lama yang belum dimigrasi) tetap dicantumkan di peta dan laporan, tetapi tidak di-scout. Arahannya: jalankan `profile` dari dalam repo itu. | Permintaan user: explore berpijak pada profil. Tanpa profil, scout kembali ke pemindaian liar. |
| K4 | **Peran repo dibaca dari `index.json` field `plugin`** (`backenddev` → BE, `frontenddev` → FE). Satu repo bisa punya dua profil; ia tercatat dengan dua peran. | Sumber yang sama dengan `detect.py`, tanpa mengimpor skrip plugin lain (cache plugin terpisah). |
| K5 | **Memakai data profil, bukan agent `code-explorer`.** Satu agent baru `fullstack:repo-scout` (`Read, Grep, Glob`, tanpa Write, model `haiku`, `maxTurns: 14`), satu dispatch per repo dengan slot `peran`. | Lihat Temuan awal: explorer lama ditolak pagar di root dan kontraknya terikat taskdir. Satu agent dengan slot `peran` lebih murah dirawat daripada dua agent kembar. |
| K6 | **Konteks utama tidak membaca kode repo anak.** Bukti kode datang dari balikan scout; gambaran perusahaan datang dari `PETA.md`. Konteks utama hanya membaca keluaran skrip dan menulis laporan. | Menjaga konteks kecil di root yang bisa berisi puluhan repo, sama dengan Iron Law `notulen`. |
| K7 | **Hanya explore.** Kebutuhan perubahan kode keluar sebagai `## Arahan Lanjut`, berisi `cd <dir>` lalu skill pemiliknya. `fullstack` tidak pernah memanggil skill backend/frontend. | Gerbang dan precondition backend/frontend butuh repo git. |
| K8 | **Tanpa hook di `fullstack`.** Root satu proyek dibebaskan lewat F1 di sisi backend/frontend; root multi-proyek sudah tidak tergerbang. | `analyst` dan `product` juga tanpa hook. Tidak perlu pengecualian `/fullstack:*` di `gate_text.py`, karena di root gerbang tidak menggerbangi dan di dalam repo `fullstack` menolak sendiri (K2). |

### Root, proyek, dan lingkup

| ID | Keputusan | Alasan |
|---|---|---|
| K9 | **`scan` turun sampai dua tingkat.** Anak langsung root yang ber-`.git` adalah repo dengan proyek `.`. Anak tanpa `.git` adalah **proyek**, dan anak langsungnya yang ber-`.git` adalah repo milik proyek itu. Scan tidak pernah turun ke dalam repo. Identitas repo = path relatif terhadap root (`api`, `wms/api`). | Mendukung root satu proyek dan root perusahaan dengan satu aturan. Path relatif sebagai identitas membuat rujukan `` `wms/api/internal/x.go:12` `` dan `check` tetap seragam. |
| K10 | **Plafon scan 60 repo.** Lebih dari itu, `scan` berhenti dengan peringatan dan menyebut proyek yang belum tercakup. | Ukuran satu perusahaan, bukan satu proyek. Biaya scan hanya baca `index.json` dan `git rev-parse` per repo. |
| K11 | **Lingkup per jalur.** `PETA` selalu mencakup seluruh root. `TELUSUR` default satu proyek: ditebak dari nama proyek atau repo yang disebut objective, atau ditanyakan dengan satu `AskUserQuestion` bila root punya lebih dari satu proyek. Objective yang menyebut beberapa proyek melingkupi semuanya, dalam batas plafon scout (K16). | Peta harus utuh supaya berguna; penelusuran kode harus sempit supaya tetap permukaan. |

### Peta perusahaan

| ID | Keputusan | Alasan |
|---|---|---|
| K12 | **`PETA.md` dibangun skrip, bukan model.** `workspace.py peta --write` menulis `<root>/.fullstack/PETA.md` dari profil dan git saja, tanpa scout dan tanpa membaca kode. Berkas ditulis ulang utuh tiap kali dibangun. | Biaya tetap rendah untuk puluhan repo, hasilnya bisa diulang, dan tidak ada ruang halusinasi di peta yang menjadi pegangan seluruh explore. |
| K13 | **Isi BE di-parse, isi FE dikutip.** BE: tabel domain dari `domain-map.md`, daftar kunci permukaan dari `surface-map.md`, dan baris `external:` dikutip apa adanya. FE: `stack`/`framework`/`platform` dari `index.json`, butir `**Features Path**` dan `**Route Definitions**` dari `structure.md` dikutip apa adanya, dan daftar nama permukaan dari kolom pertama tabel `surface-map.md`. Kutipan dipotong 400 karakter per butir. Baris yang tidak sesuai format dicatat di `## Belum terpetakan`, bukan ditebak. | Mengikuti batas yang benar-benar bisa dibaca mekanis (Temuan awal). |
| K14 | **Kesegaran profil ikut dipetakan.** Tiap profil mencatat berapa commit sesudah commit terakhir yang menyentuh `.claude/profile/<plugin>/` **yang mengubah `source_root`** profil itu. Lebih dari 50 commit → ditandai `profil tertinggal` dengan arahan REFRESH. | Peta perusahaan hanya sebaik profil di bawahnya. Hanya commit kode yang dihitung: diuji di repo nataflow, `backend` punya 190 commit sejak profil tetapi hanya 56 yang menyentuh `internal/`, dan `frontend` 50 berbanding 8. Commit dokumen rantai backend/frontend (TASK, brief, REVIEW, REPORT) tidak membuat profil basi. |
| K15 | **Hubungan antar aplikasi di `PETA.md` hanya dari sumber pasti**: FE → BE untuk proyek yang punya tepat satu BE, dan pemetaan di `layanan.json`. Panggilan keluar BE yang belum dipetakan tercantum sebagai target nama config tanpa penerima. | Konsisten dengan K21: peta tidak menebak siapa memanggil siapa. |

### Explore (`TELUSUR`)

| ID | Keputusan | Alasan |
|---|---|---|
| K16 | **Dua jalur.** `PETA`: bangun atau segarkan `PETA.md`, lalu jawab dari situ. `TELUSUR`: satu objective konkret (layar, fitur, endpoint, entitas, integrasi) diturunkan ke kode lewat scout. Permintaan umum ("aplikasi apa saja", "pelajari semua") dijawab lewat `PETA`; objective `TELUSUR` yang kabur dipersempit dengan satu `AskUserQuestion`. | Memahami perusahaan dan menelusuri satu fitur adalah kebutuhan yang berbeda, dengan biaya yang berbeda. |
| K17 | **Plafon scout `TELUSUR`**: satu dispatch per repo per putaran, paralel, maksimal 4 repo per putaran, maksimal 2 putaran per explore. Kuota 10 pemanggilan `Read`/`Grep`/`Glob` per dispatch. Putaran kedua dipakai untuk memverifikasi endpoint penerima dari panggilan yang ditemukan di putaran pertama. | Kedalaman permukaan; selaras plafon `code-scout` analyst. |
| K18 | **Laporan `TELUSUR` di `<root>/.fullstack/explore/<YYMMDDhhmm>-<slug>.md`**, dengan SHA HEAD tiap repo yang disisir dan daftar proyek lingkupnya. Root bukan repo git, jadi tidak ada urusan gitignore atau commit. | Keputusan user. SHA memungkinkan `list` menandai laporan basi tanpa membaca badannya. |
| K19 | **Panen sebelum scout**: `explore.py list --json` membaca frontmatter saja; maksimal dua laporan beririsan dipakai sebagai konteks dispatch. Laporan `basi` hanya boleh mempersempit arah, bukan menjadi bukti. `PETA.md` dipakai untuk memilih repo dan domain yang di-scout. | Sama dengan Fase 0b `code-explorer`. |

### Jahitan

| ID | Keputusan | Alasan |
|---|---|---|
| K20 | **Satu model untuk dua jenis jahitan.** Pemanggilan HTTP di FE dan panggilan keluar BE sama-sama dicatat sebagai **panggilan** (pemanggil, target, metode, path). Route BE dicatat sebagai **endpoint**. `seam` mencocokkan panggilan dengan endpoint. API to API memakai mesin yang sama dan hanya muncul bila ada panggilan keluar. | FE → BE dan API → API punya bentuk yang sama, jadi cukup satu pencocok dan satu tabel jahitan. Perusahaan tanpa API to API tidak membayar apa pun untuk kemampuan ini. |
| K21 | **Target pasti hanya dari dua sumber**: (a) pemetaan yang sudah dikonfirmasi user di `.fullstack/layanan.json`; (b) panggilan FE di proyek yang hanya punya satu repo BE. Selain itu, kecocokan path hanya menghasilkan `DUGAAN` atau `AMBIGU`. | Nama config tidak bisa dipetakan ke repo secara mekanis, dan dua API bisa punya path yang sama (`/api/v1/health`). |
| K22 | **Target dicatat sebagai nama config, bukan nilainya** (`PUBLIC_API_URL`, `WMS_API_URL`, atau nama field config). Scout dilarang membaca nilai dari `.env*`. Nilai default yang tertulis di kode config boleh dibaca. | Nilai `.env` bisa memuat rahasia, dan host antar lingkungan berbeda. |
| K23 | **Calon penerima per jenis pemanggil.** FE: hanya repo BE di proyek yang sama. BE: semua repo BE dalam lingkup kecuali dirinya sendiri. | Menurut user, FE tidak memanggil API proyek lain; membatasinya mencegah `COCOK` palsu dari path yang kebetulan sama. |
| K24 | **Konfirmasi pemetaan maksimal satu `AskUserQuestion` per explore**, berisi paling banyak 4 target `DUGAAN`/`AMBIGU`. Jawaban disimpan lewat `explore.py layanan set`, lalu `seam` dijalankan ulang. Target yang tidak dijawab tetap `DUGAAN`/`AMBIGU` di laporan. | Pemetaan layanan jarang berubah. Sekali dikonfirmasi, explore dan `PETA.md` berikutnya langsung memakainya. |
| K25 | **Jahitan dihitung skrip, bukan dikarang model.** `check` menghitung ulang `seam` dan gagal bila tabel `## Jahitan` berbeda. | Bagian paling rawan halusinasi. |
| K26 | **`TAK_TERPANGGIL` bukan temuan cacat.** Endpoint BE tanpa pemanggil ditulis "tidak terlihat dalam cakupan sisir", karena scout hanya menyisir domain objective dan route bisa dipakai klien lain (MCP, mobile, pihak ketiga). | Sama dengan pemisahan `Tidak ditemukan` dan `Belum disisir` di `code-scout`. |
| K27 | **Profil BE tanpa baris `external:` berarti tanpa panggilan keluar**, sesuai aturan `surface-map.md`. Scout tidak menyisir panggilan keluar di repo itu. Bila objective menyebut integrasi dari repo itu, laporan mencatatnya di `## Celah` dengan arahan `backend:profile` mode REFRESH, dan `confidence` maksimal `medium`. | Konsisten dengan K3: profil adalah peta sisir. Profil yang basi diperbarui pemiliknya, bukan ditambal dengan pemindaian liar. |

## Kontrak

### `workspace.py scan`

```
python3 workspace.py scan [--root <dir>] [--json]
```

- Root = `--root` atau cwd. Bila root ada di dalam work tree git → `mode: DALAM_REPO`, exit 1.
- Aturan K9 dan K10. Lewati folder berawalan `.` dan `SKIP_DIRS` yang sama dengan `detect.py`. Anak dihitung repo
  bila punya `.git` (direktori atau berkas, untuk worktree).
- Per repo: `dir` (path relatif), `proyek`, `head` (SHA 7 karakter, atau `null` bila belum ada commit), dan daftar
  `profil`. Tiap butir profil berisi `peran` (`BE`/`FE`), `stack`, `source_root`, `status` (`VALID` |
  `INVALID_JSON` | `LEGACY` | `ABSENT`), `tertinggal` (jumlah commit yang menyentuh `source_root` sejak profil
  terakhir disentuh, atau `null` bila profil belum pernah di-commit), dan daftar berkas `.md` profil yang hilang.
- `SKIP_DIRS` disalin dari `detect.py` backend (cache plugin terpisah, tidak bisa diimpor); test menjaga salinannya
  tetap sama.
- Ringkasan per proyek: jumlah repo BE dan FE berprofil `VALID`.
- Exit 0 bila minimal satu profil `VALID`; selain itu exit 1.

### `workspace.py peta` dan `.fullstack/PETA.md`

```
python3 workspace.py peta [--root <dir>] [--write] [--json]
```

Tanpa `--write`, isi dicetak ke stdout (atau JSON dengan `--json`). Dengan `--write`, ditulis ke
`<root>/.fullstack/PETA.md`.

```markdown
# Peta Aplikasi — <nama folder root>

Dibangun: <YYMMDDhhmm> · <n> proyek · <m> repo · sumber: profil repo dan `layanan.json`, tanpa membaca kode.

## Ringkasan
| Proyek | Repo BE | Repo FE | Tanpa profil | Profil tertinggal |

## Proyek `<proyek>`

### `<dir>` — BE · <stack> · <architecture> · HEAD <sha7>
- Profil: VALID · tertinggal <n> commit
- Permukaan: http, persistence, external, …
- Panggilan keluar: <kutipan baris `external:`>

| Domain | Path | Permukaan | Entry |

### `<dir>` — FE · <stack> · <framework> · HEAD <sha7>
- Profil: VALID · tertinggal <n> commit
- Permukaan: Routing & Navigation, HTTP Service, …
- Fitur: <kutipan butir **Features Path**>
- Rute: <kutipan butir **Route Definitions**>

## Hubungan antar aplikasi
| Pemanggil | Target | Penerima | Sumber |      <!-- Sumber: `satu BE di proyek` | `layanan.json` | `belum dipetakan` -->

## Belum terpetakan
- <repo tanpa profil, profil rusak, baris profil di luar format, beserta arahannya>
```

Repo dengan dua profil muncul dua kali, sekali per peran. `peta` tidak pernah gagal karena satu repo rusak; repo itu
pindah ke `## Belum terpetakan`.

### `.fullstack/layanan.json` dan `explore.py layanan`

```
python3 explore.py layanan list [--root <dir>] [--json]
python3 explore.py layanan set  --pemanggil <dir> --target <nama-config> --repo <dir> [--prefix <path>]
python3 explore.py layanan hapus --pemanggil <dir> --target <nama-config>
```

```json
{
  "versi": 1,
  "peta": [
    {"pemanggil": "erp/api", "target": "WMS_API_URL", "repo": "wms/api", "prefix": "/api/v1"}
  ]
}
```

- `set` menolak `--pemanggil` atau `--repo` yang tidak ada di `scan`, `--repo` yang bukan BE, dan pemanggil sama
  dengan repo. Pasangan `pemanggil` + `target` unik; `set` ulang menimpa.
- `prefix` opsional: awalan path di base URL target yang tidak terlihat dari kode (nilainya ada di `.env`).
- Berkas rusak → `list`, `seam`, dan `peta` melapor dengan pesan jelas (`peta` tetap terbit tanpa hubungan dari
  `layanan.json`); berkas tidak ada = peta kosong.

### `explore.py`

```
python3 explore.py list  [--root <dir>] [--json]
python3 explore.py seam  --report <path> [--json]
python3 explore.py check --report <path> [--json]
```

- `list`: frontmatter tiap laporan di `.fullstack/explore/`, ditambah `basi: true` bila SHA salah satu repo di
  frontmatter berbeda dari HEAD sekarang. Frontmatter rusak → butir `rusak`, tidak menghentikan daftar.
- `seam`: membaca `## Endpoint` dan `## Panggilan` laporan, `layanan.json`, dan peran repo dari `scan`.
  - Normalisasi path: metode huruf besar; buang skema, host, query string, dan garis miring penutup; segmen parameter
    `{id}`, `:id`, `[id]`, `<id>`, `${…}` → `{}`.
  - Path panggilan diawali prefix target: `prefix` dari `layanan.json`, atau `Base API` FE dari baris
    `- Base API:` scout. Tanpa prefix, path panggilan cocok dengan endpoint bila sama persis atau menjadi akhiran
    endpoint pada batas segmen (`/stok/{}` cocok dengan `/api/v1/stok/{}`).
  - Calon penerima menurut K23; target pasti menurut K21.
  - Status per panggilan:

    | Status | Arti |
    |---|---|
    | `COCOK` | Target pasti, dan endpoint yang cocok ada di repo target. |
    | `TIDAK_ADA_DI_TARGET` | Target pasti, tetapi tidak ada endpoint cocok di antara endpoint repo target yang disisir. |
    | `DUGAAN` | Target belum pasti; path cocok dengan endpoint tepat satu calon repo. |
    | `AMBIGU` | Target belum pasti; path cocok dengan endpoint lebih dari satu calon repo. |
    | `TAK_DIKENAL` | Target belum pasti; tidak cocok dengan endpoint calon mana pun (bisa layanan pihak ketiga, atau repo target belum disisir). |

  - Endpoint tanpa panggilan apa pun → baris `TAK_TERPANGGIL` (K26).
- `check` (exit 0 PASS, 1 FAIL):
  1. frontmatter lengkap, `confidence` valid, `lingkup` hanya berisi proyek yang ada di `scan`;
  2. seksi wajib hadir dan berurutan; tabel kosong ditulis `- Tidak ada.`;
  3. tiap rujukan `` `<dir>/<path>:<baris>` `` atau `:<a>-<b>` menunjuk repo yang tercatat di frontmatter `repo`,
     berkasnya ada, dan barisnya ≤ jumlah baris berkas;
  4. tabel `## Jahitan` sama persis dengan keluaran `seam`;
  5. tiap repo di `## Repo` berprofil `ABSENT`/`LEGACY` punya butir di `## Arahan Lanjut`;
  6. tiap baris jahitan `DUGAAN`/`AMBIGU` punya butir di `## Celah`;
  7. tidak ada `TBD`/`TODO`.

### Laporan `.fullstack/explore/<YYMMDDhhmm>-<slug>.md`

```markdown
---
slug: <kebab-case>
objective: <satu baris, apa adanya>
dibuat: <YYMMDDhhmm>
lingkup: <proyek>, <proyek>
repo: <dir>@<sha7>, <dir>@<sha7>
confidence: high | medium | low
---

## Jawaban
## Repo           <!-- | Dir | Proyek | Peran | Stack | Profil | HEAD | -->
## Temuan         <!-- ### <dir> (BE|FE), butir berbukti `dir/path:baris` -->
## Endpoint       <!-- | Repo | Metode | Path | Bukti | -->
## Panggilan      <!-- | Pemanggil | Target | Metode | Path | Bukti | -->
## Jahitan        <!-- | Pemanggil | Target | Metode | Path | Penerima | Status | -->
## Celah          <!-- ### Tidak ditemukan, ### Belum disisir, ### Belum dipetakan -->
## Arahan Lanjut
```

Jalur `PETA` tidak menulis laporan ini; hasilnya `PETA.md`.

### Dispatch dan balikan `repo-scout`

Slot: `root` (absolut), `repo` (dir relatif), `peran` (`BE`/`FE`), `pertanyaan` (P1–P5), `verifikasi endpoint`
(opsional, putaran kedua: daftar metode + path yang harus dicari di route repo ini), `konteks panen` (opsional).
Berkas profil yang dibaca scout ditentukan `peran`:

- BE: `index.json`, `domain-map.md`, `surface-map.md` (baris `http:`, `external:`, `config:`).
- FE: `index.json`, `structure.md`, `surface-map.md` (baris **Routing & Navigation**, **HTTP Service**,
  **Shared HTTP Client**, **DTO**, **Framework Boundary**).

Balikan, tanpa teks pengantar atau penutup:

```markdown
## Repo Scout — <dir> (<BE|FE>)
- Profil: <stack> · <source_root>
- Pemanggilan: <n> dari 10
- Base API: <prefix> (target `<nama-config>`) — `<dir>/<path>:<baris>`     (FE saja)
- Prefix route: <prefix> — `<dir>/<path>:<baris>`                          (BE saja)

### Ditemukan
- P1 — <satu kalimat> — `<dir>/<path>:<baris>`

### Endpoint                                   (BE saja)
| Metode | Path | Bukti |

### Panggilan                                  (FE: pemanggilan HTTP service; BE: panggilan keluar dari baris `external:`)
| Target | Metode | Path | Bukti |

### Tidak ditemukan
### Belum disisir
```

### Gerbang di root satu proyek (F1)

`evaluate()` di `detect.py`: bila `opted_out` tidak berlaku, root tidak punya `.git`, dan ≥2 anak langsung punya
`.git`, maka `Verdict.workspace` diisi daftar anak beserta perannya untuk plugin ini (profil atau manifest anak).
`emit` tetap `True`, tetapi `gate_text.render` mengeluarkan blok pendek yang **tidak menggerbangi**:

```
<backend-tech-lead-gate>
Folder ini root multi-repo (bukan repo git): `api/`, `frontend/`. Gerbang backend tidak berlaku di sini.
Kerja backend dijalankan dari dalam repo backend: `api/`. Penelusuran lintas repo dari root: `/fullstack:explore`
(bila plugin fullstack terpasang).
</backend-tech-lead-gate>
```

Root multi-proyek tidak tersentuh F1, karena kedua gerbang sudah diam di sana (Temuan awal).

## F1 [Tinggi] Gerbang backend/frontend salah menyala di root satu proyek
- [x] Selesai

Kontrak di atas. Test: root multi-repo (dua anak ber-git) → blok pendek tanpa kata "jalan lebih dulu", dan nama
anak berperan benar; root dengan satu anak ber-git → perilaku lama; root multi-proyek → tetap tanpa emit; repo git
biasa → keluaran sama byte dengan sebelum perubahan; `.claude/workflow` di root tetap membungkam; kesamaan byte
`detect.py` tetap terjaga.

## F2 [Tinggi] Belum ada peta proyek dan repo beserta profilnya
- [x] Selesai

`workspace.py scan`. Test: root satu proyek; root multi-proyek; root campuran (repo langsung + proyek); satu repo
dengan dua profil; repo tanpa profil; profil `INVALID_JSON`; profil lokasi lama; anak tanpa commit (`head: null`,
`tertinggal: null`); `tertinggal` hanya bertambah oleh commit yang menyentuh `source_root`, bukan commit dokumen;
`SKIP_DIRS` sama dengan milik `detect.py`; `node_modules` dan `.cache`
dilewati; scan tidak turun ke dalam repo; plafon 60 repo; cwd di dalam repo → `DALAM_REPO`.

## F3 [Tinggi] Belum ada gambaran seluruh aplikasi perusahaan
- [x] Selesai

`workspace.py peta`. Test:
- BE: tabel domain dari `domain-map.md` (termasuk baris induk berisi anak dalam kurung), daftar kunci permukaan,
  kutipan `external:`; baris di luar format → `## Belum terpetakan`;
- FE: field `index.json`, kutipan `**Features Path**` dan `**Route Definitions**` (dipotong 400 karakter), nama
  permukaan dari tabel `surface-map.md`; butir hilang → `## Belum terpetakan`;
- hubungan: FE → BE untuk proyek dengan satu BE; proyek dengan dua BE tidak menghasilkan hubungan FE;
  `layanan.json` menambah hubungan BE → BE; `layanan.json` rusak → peta tetap terbit dengan catatan;
- `profil tertinggal` muncul di atas 50 commit;
- satu repo rusak tidak menggagalkan peta; `--write` menimpa `PETA.md` utuh; keluaran deterministik (urutan proyek
  dan repo alfabetis).

## F4 [Tinggi] Laporan explore tanpa pagar dan tanpa panen
- [x] Selesai

`explore.py list` dan `check`. Test per butir check 1–7, termasuk rujukan ke repo di luar frontmatter, baris
melewati panjang berkas, `lingkup` berisi proyek yang tidak ada, dan laporan `basi` sesudah commit baru di salah satu
repo.

## F5 [Tinggi] Jahitan FE → BE dan API → API belum punya pencocok mekanis
- [x] Selesai

`explore.py seam`. Test:
- normalisasi: `/projects/${id}` + base `/api/v1` = `/api/v1/projects/{id}` dari chi; `:id`, `[id]`, `<id>`; query
  string dan garis miring penutup; metode beda → tidak cocok; kecocokan akhiran pada batas segmen saja
  (`/stok` tidak cocok dengan `/api/v1/restok`);
- FE di proyek dengan satu BE → `COCOK` atau `TIDAK_ADA_DI_TARGET`; FE tidak pernah dicocokkan ke BE proyek lain;
- BE → BE tanpa pemetaan: satu calon → `DUGAAN`, dua calon → `AMBIGU`, nol → `TAK_DIKENAL`;
- BE → BE dengan pemetaan `layanan.json` dan `prefix` → `COCOK` atau `TIDAK_ADA_DI_TARGET`;
- BE tidak pernah menjadi calon penerima panggilannya sendiri;
- endpoint tanpa pemanggil → `TAK_TERPANGGIL`;
- laporan tanpa panggilan sama sekali → tabel jahitan hanya berisi `TAK_TERPANGGIL` atau `- Tidak ada.`.

## F6 [Sedang] Pemetaan layanan belum punya tempat yang tahan antar sesi
- [x] Selesai

`explore.py layanan list/set/hapus` dan `.fullstack/layanan.json`. Test: set lalu list; set ulang menimpa; tolak
repo yang tidak ada, repo bukan BE, dan pemanggil sama dengan repo; hapus; berkas rusak → FAIL; berkas tidak ada →
peta kosong.

## F7 [Tinggi] Belum ada scout lintas repo
- [x] Selesai

`agents/repo-scout.md` (frontmatter dalam whitelist `AGENT_FIELDS`) dan `skills/explore/dispatcher/scout.md`: slot,
gerbang masuk (slot rusak → balikan satu butir `Belum disisir`), daftar berkas profil per peran, kuota, putaran
verifikasi endpoint, larangan (menulis, membaca nilai `.env*`, menelusuri rantai pemanggil, menyarankan solusi),
aturan K27, dan tabel penanganan balikan.

## F8 [Tinggi] Skill `fullstack:explore`
- [x] Selesai

`SKILL.md`:
- Iron Law (K6, K7).
- Precondition: `check_preconditions.py --json` = `scan` + `.fullstack/` bisa ditulis. Kurang dari dua profil
  `VALID` dalam lingkup → WARN "lintas terbatas".
- Phase 0: pilih jalur (K16) dan lingkup (K11).
- Jalur `PETA`: `workspace.py peta --write`, baca `PETA.md`, jawab dari situ. Repo `profil tertinggal` dan
  `Belum terpetakan` disebut di jawaban beserta arahannya. Bila user lanjut bertanya hal konkret, pindah ke
  `TELUSUR`.
- Jalur `TELUSUR`:
  - Phase 1: `PETA.md` (dibangun bila belum ada), panen (K19), dan `layanan list`;
  - Phase 2: putaran pertama, dispatch paralel (K17);
  - Phase 3: putaran kedua bila ada panggilan yang repo targetnya belum disisir; slot `verifikasi endpoint` berisi
    path panggilan itu;
  - Phase 4: susun laporan dari template, `seam`, konfirmasi pemetaan (K24), `seam` ulang, `check` sampai PASS
    (maksimal 3 putaran perbaikan);
  - Phase 5: ringkasan di chat beserta path laporan.
- Failure path: scout gagal dua kali untuk satu repo → repo itu masuk `Belum disisir`, laporan tetap terbit dengan
  `confidence` maksimal `medium`; `layanan.json` rusak → berhenti sebelum `seam`, minta user memperbaiki atau
  menghapus berkasnya; root melewati plafon 60 repo → `PETA` tetap jalan untuk yang tercakup dan menyebut sisanya.

## F9 [Sedang] Kopling ke format profil tanpa pengaman
- [x] Selesai

`tests/fullstack/test_profile_anchor_21.py`:
- backend: `scan-guide.md` titik 14 masih memuat permukaan kanonik `http`, `external`, dan `config`; template
  `surface-map.md` masih berformat `<permukaan>: <path> · <penanda> · <catatan>`; `convention-scan.md` titik 15
  masih berformat `<domain>: <path> · <permukaan> · entry <file>#<simbol>`;
- frontend: template `structure.md` masih memuat butir `**Features Path**` dan `**Route Definitions**`; template
  `surface-map.md` masih memuat baris **Routing & Navigation**, **HTTP Service**, **Shared HTTP Client**, **DTO**,
  dan **Framework Boundary**;
- parser `peta` lolos terhadap contoh di template profil backend dan frontend.

Bila backend/frontend mengganti jangkar ini, test gagal dan `peta` serta dispatcher `fullstack` ikut diperbarui.

## F10 [Rendah] Smoke untuk skrip baru
- [x] Selesai

`CASES` di `tests/test_smoke.py`: `workspace.py scan --json`, `workspace.py peta --json`, `explore.py list --json`,
`explore.py layanan list --json`, dan `check_preconditions.py --json`. Keadaan "bukan repo git" adalah keadaan
normal plugin ini, jadi harapan exit-nya ditulis per keadaan.

## D1 [Rendah] Dokumen dan versi
- [x] Selesai

- `src/plugins/fullstack/README.md` dan `flow/fullstack.md` (Peta Komponen, Alur Utama, Artefak, Jalur, Handoff
  Lintas Plugin, Titik Gagal & Pemulihan; struktur sama dengan `flow/product.md`). Sertakan contoh root satu proyek
  dan root perusahaan, contoh `PETA.md`, dan contoh `layanan.json`.
- `flow/backend.md` dan `flow/frontend.md`: perilaku hook di root multi-repo.
- `plugin.json`: `fullstack` 0.1.0 (baru), `backend` 0.14.0, `frontend` 0.13.0. Entri `marketplace.json` baru dengan
  deskripsi sama persis (lint M4).
- `README.md` root: tabel plugin, Instalasi, Prasyarat, Memilih Plugin, Hidup Berdampingan.
- `CLAUDE.md` repo: jumlah plugin dan butir `fullstack` di "The plugins".

## Di luar cakupan

- Monorepo satu-git dengan dua profil di root yang sama.
- Root lebih dari dua tingkat (mis. `company/<tim>/<proyek>/<repo>`).
- Ringkasan naratif `PETA.md` yang ditulis model. Peta tetap mekanis; narasi hanya di jawaban chat.
- FE proyek A memanggil API proyek B (menurut user tidak terjadi; K23 sengaja menolaknya).
- Pencocokan field DTO/payload antar pemanggil dan penerima. Fase ini berhenti di tingkat metode + path.
- Permukaan selain HTTP: messaging/broker, gRPC, websocket, MCP.
- Membaca nilai `.env` untuk memetakan host ke repo secara otomatis.
- Handoff otomatis ke `analyst:intake` atau ke gerbang backend/frontend.
- Sinkron `PETA.md` atau laporan explore ke nataflow.

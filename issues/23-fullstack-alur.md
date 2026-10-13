# Langkah 23 — `fullstack`: jalur `ALUR` dengan subagent `backend-explorer` dan `frontend-explorer` (L1–L6, D1)

Sumber: laporan user 2026-10-13. Di root `root/{backend-a,backend-b}` user meminta Claude menelusuri kedua repo
backend untuk memahami alur dan informasinya. `/fullstack:explore` tidak terpanggil, dan penelusuran jatuh ke
subagent `Explore` bawaan Claude Code. User lalu meminta subagent explorer khusus BE dan FE yang diadaptasi dari
`code-explorer` milik `backend` dan `frontend`, dan menyetujui seluruh rekomendasi di sesi desain yang sama. Basis
kode: commit `31aa5d3` (fullstack 0.2.0, backend 0.14.0, frontend 0.13.0).

**Status (2026-10-13):** L1–L6 dan D1 selesai. Test baru di `tests/fullstack/test_alur_23.py` (25), ditambah satu
test di `tests/hooks/test_workspace_root_21.py` (dua plugin) dan satu kasus smoke `explore.py new --jalur ALUR`.
Suite penuh hijau (2500), subset fullstack/hooks/smoke hijau di Python 3.9, lint `--base 31aa5d3` 0 FAIL, dan `claude plugin validate .` lolos.
Versi: fullstack 0.3.0, backend 0.14.1, frontend 0.13.1.

**Uji ujung ke ujung (2026-10-13).** Root scratch `root/{backend-a,backend-b}` (dua repo Go berprofil backend `VALID`,
alur order → reservasi stok lewat `STOK_API_URL`), Claude Code headless dengan `--plugin-dir` fullstack dan backend
dari working tree, prompt tanpa menyebut skill: "tolong pelajari alur pembuatan order di backend-a dan backend-b,
saya mau paham flow dan aturannya". Hasil:

- `fullstack:explore` terpanggil sendiri, jalur `ALUR`; dua `fullstack:backend-explorer` didispatch paralel. Tidak
  ada `Explore`/`general-purpose`.
- Seluruh 18 pembacaan kode repo anak (`Read`/`Grep`/`Glob`) dilakukan subagent; konteks utama hanya membaca keluaran
  skrip, `dispatcher/explorer.md`, dan laporannya sendiri.
- `explore.py new --jalur ALUR --kedalaman ringkas` menulis kerangka; `check` pertama FAIL karena rujukan berbentuk
  daftar (`service.go:8,17-19`), diperbaiki model, lalu PASS 7/7 dengan `confidence: medium`.
- Jawaban menjelaskan langkah handler → service → transaksi → repository → panggilan stok, aturan bisnis (minimal
  satu item, batas total 50.000.000, stok tidak cukup), dan menandai hubungan `STOK_API_URL` → `backend-b` sebagai
  belum dikonfirmasi serta menawarkan `TELUSUR` untuk jahitannya.

Selisih pelaksanaan terhadap Kontrak di bawah:

- **`new` TELUSUR tidak menulis `jalur`.** Kerangka `TELUSUR` tetap persis seperti Langkah 21; hanya `ALUR` yang
  menulis `jalur: ALUR` dan `kedalaman`. Sesuai K8, laporan tanpa `jalur` adalah `TELUSUR`.
- **`--kedalaman` tanpa `--jalur ALUR` ditolak**, begitu pula `--jalur` di luar `TELUSUR`/`ALUR`.
- **Check 4 ALUR** juga menolak subseksi `## Alur` yang judulnya bukan `<repo> (BE|FE)` atau menunjuk repo di luar
  frontmatter. Repo dianggap tercatat di `### Belum disisir` bila namanya muncul utuh di subseksi itu.
- **Check 6 ALUR** juga menolak baris `Aturan Bisnis`/`Permukaan` yang kolom `Repo`-nya di luar frontmatter.
- **Prasyarat** memeriksa keberadaan `alur-template.md`, `dispatcher/explorer.md`, dan kedua agent baru.
- **Deskripsi plugin** (`plugin.json` dan `marketplace.json`) menyebut penelusuran alur lewat kedua explorer.
- **Test drift (K12)** juga memaku bahwa pelonggaran `menyeluruh` (120 baris, 3 jendela, 400 baris) ada di sumber
  dan turunan BE saja, sehingga perubahan sumber FE yang menambahkannya ikut terdeteksi.

## Tujuan

1. Dari root multi-repo, user bisa memahami **alur di dalam satu repo atau lebih**: entry point, langkah per layer,
   aturan bisnis, batas transaksi, dan permukaan runtime yang disentuh. Semuanya berbukti `<repo>/<path>:<baris>`.
2. Penelusuran itu dikerjakan subagent milik `fullstack` yang dipandu profil repo, bukan oleh `Explore` atau
   `general-purpose` bawaan.
3. Permintaan "pahami / pelajari / jelaskan alur repo X" di root benar-benar sampai ke `/fullstack:explore`.
4. Jalur `TELUSUR` yang sudah ada (permukaan dan jahitan lewat `repo-scout`) tidak berubah perilakunya.

## Temuan awal (dasar keputusan)

Diverifikasi di sesi desain dengan membaca plugin di basis kode di atas:

- **Pemicu skill terlalu sempit.** Blok gerbang root multi-repo (`backend/hooks/gate_text.py` dan
  `frontend/hooks/gate_text.py`, fungsi `_workspace`) hanya menyebut `/fullstack:explore` untuk "penelusuran
  **lintas repo**". Deskripsi skill `fullstack:explore` juga menekankan lintas frontend dan backend. Permintaan
  "pahami alur backend-a dan backend-b" tidak terbaca sebagai keduanya, jadi model memakai `Explore` bawaan.
  `fullstack` tidak punya hook, dan PreToolUse backend/frontend hanya memasang matcher `Bash|Edit|Write`, sehingga
  tidak ada yang memagari tool `Agent`.
- **`repo-scout` sengaja dangkal.** Model haiku, kuota 10 pemanggilan, berhenti di bukti pertama, dan dilarang
  menelusuri rantai pemanggil, alur transaksi, edge case, maupun validasi. Pertanyaan "bagaimana X bekerja" berada di
  luar kontraknya.
- **`code-explorer` backend/frontend tetap tidak bisa dipinjam dari root** (temuan Langkah 21): Write laporannya
  ditolak `guard_bash.py` yang fail-closed di folder non-git, kontraknya terikat ke laci taskdir
  (`<taskdir>/.explore/` atau `.frontenddev/explore/`), dan profil dibaca relatif terhadap cwd. Dari root, cwd bukan
  repo.
- **Kemampuan yang dibutuhkan sudah ada di `code-explorer`**: investigasi dua tahap (lokalisasi `Grep`/`Glob` lalu
  verifikasi `Read` ber-offset), formula jendela `L - 15` s.d. `L + 35` (30–50 baris, sama di kedua sumber), jenjang
  `menyeluruh`, pemetaan layer dan permukaan runtime, serta ekstraksi aturan bisnis. Pelonggaran `menyeluruh` (method
  utuh sampai 120 baris, maksimal 3 jendela per berkas) hanya ada di sumber backend; sumber frontend mengartikan
  `menyeluruh` sebagai menelusuri konsumen unit logika sampai komponen rute/layar, tanpa pelonggaran jendela. Yang
  perlu dibuang hanya bagian yang terikat ke taskdir dan Write.
- **`explore.py` sudah menjadi pagar laporan.** `new` membuat kerangka dari satu template, dan `check` menilai tujuh
  check dengan `SECTIONS` tetap (`Jawaban`…`Arahan Lanjut`). Check 4 (`Jahitan = seam`) dan 6 (`Celah pemetaan`) khas
  `TELUSUR`, sedangkan check 1, 2, 3, 5, dan 7 berlaku umum.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Dua agent baru milik `fullstack`**: `backend-explorer` dan `frontend-explorer`, diadaptasi (disalin lalu disesuaikan) dari `code-explorer` masing-masing plugin. Bukan dipinjam lintas plugin dan bukan satu agent bercabang `peran`. | Peminjaman gagal di root non-git (temuan awal). Cara membaca profil dan idiom BE (handler → service → repository, transaksi) dan FE (route → komponen → hook/store → service → DTO) berbeda jauh, dan di penelusuran dalam perbedaan itu makin besar. |
| K2 | **Read-only lewat daftar tools**: `tools: Read, Grep, Glob`, tanpa `Write`. Balikan inline, dan laporan ditulis konteks utama lewat `explore.py`. | `fullstack` tidak punya hook PreToolUse, jadi daftar tools adalah satu-satunya pagar mekanis. Ini sama dengan `repo-scout`. |
| K3 | **Format balikan tinggal di berkas agent**, seperti `repo-scout`, bukan blok `Format laporan` milik pendispatch seperti `code-explorer`. | Hanya ada satu pendispatch (`fullstack:explore`). Format di agent bisa dipaku test dan tidak ikut hilang saat prompt dihidrasi. |
| K4 | **Jalur baru `ALUR`**, terpisah dari `TELUSUR`. `TELUSUR` menjawab "ada di mana, siapa memanggil siapa" (`repo-scout`, jahitan lewat skrip). `ALUR` menjawab "bagaimana X bekerja di dalam repo" (explorer per repo). | Laporan, check, dan biaya keduanya berbeda. Bila dicampur, `check` dan template harus bercabang di tiap seksi. |
| K5 | **Repo tanpa profil `VALID` untuk peran itu tidak didispatch**, sama dengan `repo-scout`. Repo itu diarahkan ke `<plugin>:profile`, dan `explore.py new --jalur ALUR` menolaknya secara mekanis. | Konsisten dengan iron law "profil adalah peta sisir". Penolakan di `new` membuat aturan itu bergerbang skrip, bukan hanya prosa. |
| K6 | **Model `sonnet`**, `maxTurns: 45`. Kuota `Read`/`Grep`/`Glob`: `ringkas` 20 pemanggilan, `menyeluruh` 40. | Penelusuran alur butuh penalaran yang tidak sanggup dikerjakan haiku. Kuota menjaga biaya dan konteks tetap terbatas. |
| K7 | **Plafon**: maksimal 4 dispatch explorer, semua dalam satu pesan paralel, satu putaran. Dispatch ulang karena gagal (sekali per repo) tidak dihitung. `Kedalaman` default `ringkas`. `menyeluruh` hanya bila user meminta detail (cabang error, transaksi, "semua langkah"). | Sonnet jauh lebih mahal daripada haiku. Cakupan bertambah lewat repo, bukan lewat putaran berulang. |
| K8 | **Satu jenis laporan per berkas, dibedakan field frontmatter `jalur`** (`TELUSUR` atau `ALUR`). Laporan lama tanpa `jalur` dibaca sebagai `TELUSUR`. `ALUR` memakai template sendiri (`templates/alur-template.md`). | Laporan terdahulu tetap lolos `check` dan tetap terbaca `list` tanpa migrasi. |
| K9 | **`seam` hanya untuk `TELUSUR`.** `seam` atas laporan `ALUR` ditolak dengan pesan yang menyebut jalurnya. | Alur di dalam repo tidak punya tabel `Endpoint`/`Panggilan` lintas repo. Kebutuhan jahitan tetap dilayani `TELUSUR`. |
| K10 | **`ALUR` boleh memanen laporan `TELUSUR`** (dan sebaliknya) lewat `explore.py list`, dengan aturan panen yang sama: maksimal dua laporan beririsan, laporan `basi` hanya mempersempit arah. | Alur yang paling sering diminta adalah "dalami sisi BE dari jahitan tadi". Panen membuat explorer langsung mulai dari entry point yang sudah terbukti. |
| K11 | **Pemicu diperluas tanpa pagar mekanis**: deskripsi skill, kalimat `_workspace` di `gate_text.py` backend/frontend, dan satu butir rationalization di `SKILL.md` menyebut bahwa penelusuran kode repo anak dari root lewat `/fullstack:explore`, bukan `Explore`/`general-purpose` bawaan. | Hook PreToolUse pada tool `Agent` terlalu berat: `fullstack` tidak punya hook, `guard_bash.py` fail-closed, dan hook seperti itu juga memblokir user yang sengaja meminta `Explore`. Dinilai ulang bila masih bocor. |
| K12 | **Drift dari `code-explorer` dijaga dua lapis**: `flow/fullstack.md` mencatat kedua agent sebagai turunan beserta sumbernya, dan satu test memaku angka jendela baca supaya sama dengan sumber masing-masing: formula offset dan rentang 30–50 baris di keduanya, ditambah plafon 120 baris dan 3 jendela `menyeluruh` di `backend-explorer`. `frontend-explorer` mengikuti sumbernya dan tidak mendapat pelonggaran itu. | Byte-identical tidak mungkin karena isinya memang diadaptasi. Angka jendela adalah bagian yang paling mudah menyimpang diam-diam saat sumbernya diubah. |

## Kontrak

### Agent `fullstack:backend-explorer` / `fullstack:frontend-explorer`

Frontmatter:

```yaml
name: backend-explorer          # frontend-explorer
description: Subagent read-only penelusur alur di dalam satu repo backend (frontend) berprofil di root multi-repo untuk fullstack:explore jalur ALUR. …
tools: Read, Grep, Glob
model: sonnet
maxTurns: 45
```

Masukan (slot prompt pendispatch):

- `root` [REQUIRED]: path absolut root multi-repo.
- `repo` [REQUIRED]: path repo relatif root. Penelusuran dilarang keluar dari `<root>/<repo>/`.
- `objective` [REQUIRED]: satu pertanyaan alur yang menyebut domain, fitur, layar, endpoint, atau entitas konkret.
  Objective umum ("pelajari repo") ditolak.
- `kedalaman` [REQUIRED]: `ringkas` atau `menyeluruh`.
- `batas cakupan` [OPTIONAL]: path modul atau fitur di dalam repo. Bila kosong, diturunkan dari `domain-map.md` (BE)
  atau **Features Path** `structure.md` (FE).
- `konteks panen` [OPTIONAL]: fakta dari laporan explore terdahulu beserta rujukannya. Fakta yang menjadi tumpuan
  jawaban wajib dibuktikan ulang dengan satu `Read`.

Yang diambil dari `code-explorer` sumbernya: investigasi dua tahap, formula dan rentang jendela baca, jenjang
`menyeluruh`, pemetaan layer menurut `architecture` profil, permukaan runtime, ekstraksi aturan bisnis dan invariant,
pencatatan fakta negatif, dan pemisahan `Tidak ditemukan` dari `Belum disisir`.

Yang dibuang atau diganti: Tahap 0 panen laci (diganti slot `konteks panen`), `Write` dan `Berkas laporan`, blok
`Format laporan` pendispatch (K3), jalur profil absen yang terdegradasi (K5), serta path profil relatif cwd (diganti
`<root>/<repo>/.claude/profile/<plugin>dev/`).

Larangan: menyunting berkas apa pun, membuka `.env*` atau menyalin nilai rahasia/host, menyisir repo lain di bawah
`root`, menyarankan solusi atau menilai kualitas kode, berdialog dengan user, dan menulis rujukan yang tidak dibaca
sendiri lewat `Read`.

Balikan (hanya blok ini):

```markdown
## Alur Explorer — <repo> (<BE|FE>)
- Profil: <stack> · <architecture> · <source_root>
- Kedalaman: <ringkas|menyeluruh>
- Pemanggilan: <n> dari <20|40>
- Entry: <simbol atau route> — `<repo>/<path>:<baris>`

### Alur
1. <Layer> — <apa yang terjadi di langkah ini> — `<repo>/<path>:<baris>`

### Aturan Bisnis
- <aturan, validasi, atau invariant> — `<repo>/<path>:<baris>`

### Permukaan
| Permukaan | Detail | Bukti |
|---|---|---|
| Database | tabel `orders`, transaksi di `CreateOrder` | `<repo>/<path>:<baris>` |

### Tidak ditemukan
- <yang dicari> — disisir: `<repo>/<dir>/`

### Belum disisir
- <jalur> — <kuota habis | di luar batas cakupan | profil tanpa permukaan itu>
```

Layer BE mengikuti `architecture` profil (`Handler`/`Service`/`Repository`, atau `Adapter driving`/`Use case`/`Port`/
`Adapter driven`). Layer FE: `Route`, `Page`, `Komponen`, `Hook/Store`, `Service`, `DTO`. Permukaan BE memakai kunci
kanonik `surface-map.md` (`http`, `database`, `broker`, `cache`, `scheduler`, `external`, …), sedangkan permukaan FE
memakai nama baris tabel `surface-map.md`. Seksi tanpa butir ditulis `- Tidak ada.` Rentang rujukan maksimal 40 baris.

### `dispatcher/explorer.md`

Template prompt dengan slot `{root}`, `{repo}`, `{peran}` (memilih `backend-explorer` atau `frontend-explorer`),
`{objective}`, `{kedalaman}`, `{batas}`, dan `{panen}`. Bentuk dan aturannya mengikuti `dispatcher/scout.md`: gerbang
masuk (profil `VALID`, plafon K7, audit hidrasi tanpa `{...}`/`TBD`/`TODO`), dan tabel Penanganan Balikan:

| Balikan | Mendarat di |
|---|---|
| `Entry` dan `### Alur` | `## Alur` → `### <repo> (<peran>)`, langkah bernomor apa adanya |
| `### Aturan Bisnis` | `## Aturan Bisnis`, kolom `Repo` di depan |
| `### Permukaan` | `## Permukaan`, kolom `Repo` di depan |
| `### Tidak ditemukan` | `## Celah` → `### Tidak ditemukan` |
| `### Belum disisir`, dispatch gagal dua kali | `## Celah` → `### Belum disisir`, `confidence` maksimal `medium` |

### Laporan `ALUR` (`templates/alur-template.md`)

Frontmatter: `slug`, `objective`, `jalur: ALUR`, `kedalaman`, `dibuat`, `lingkup`, `repo`, `confidence`.

Seksi berurutan: `## Jawaban` (penjelasan alur 5–15 kalimat dalam bahasa penanya), `## Repo` (diisi `new`), `## Alur`
(satu `### <repo> (<BE|FE>)` per repo, langkah bernomor berbukti), `## Aturan Bisnis` (tabel `| Repo | Aturan |
Bukti |` atau `- Tidak ada.`), `## Permukaan` (tabel `| Repo | Permukaan | Detail | Bukti |` atau `- Tidak ada.`),
`## Celah` (`### Tidak ditemukan`, `### Belum disisir`), dan `## Arahan Lanjut`.

### `explore.py`

- `new --jalur TELUSUR|ALUR` (default `TELUSUR`) dan `--kedalaman ringkas|menyeluruh` (wajib untuk `ALUR`, ditolak
  untuk `TELUSUR`). `ALUR` memakai `alur-template.md` dan menolak repo tanpa profil `VALID` (K5).
- `list` menambah kunci `jalur` per laporan. Laporan tanpa `jalur` dilaporkan `TELUSUR`.
- `check` memilih aturan dari `jalur`. Nomor check 1–7 tetap:

  | Check | `TELUSUR` (tidak berubah) | `ALUR` |
  |---|---|---|
  | 1 Frontmatter | seperti sekarang | ditambah `jalur`, `kedalaman` sah |
  | 2 Seksi | `SECTIONS` sekarang | seksi `ALUR`; tabel `Aturan Bisnis` 3 kolom, `Permukaan` 4 kolom |
  | 3 Rujukan `path:baris` | sama | sama |
  | 4 | `Jahitan = seam` | **Alur per repo**: tiap repo frontmatter punya `### <repo> (…)` di `## Alur` dengan ≥ 1 langkah bernomor berbukti, atau tercatat di `### Belum disisir` |
  | 5 Arahan profil | sama | sama |
  | 6 | `Celah pemetaan` | **Bukti tabel**: tiap baris `Aturan Bisnis` dan `Permukaan` punya rujukan |
  | 7 Tanpa placeholder | sama | sama |

- `seam` atas laporan `ALUR` → galat "`seam` hanya untuk laporan `TELUSUR`" (K9).

### Skill `fullstack:explore`

- Deskripsi ditambah pemicu: memahami alur, logika, atau aturan bisnis di dalam satu repo atau lebih di root.
- Phase 0 mengenal jalur keempat `ALUR`: pertanyaan "bagaimana X bekerja / alur X / logika X" atas repo tertentu.
  Objective yang kabur dipersempit dengan `AskUserQuestion` yang sama (tetap satu untuk jalur/lingkup).
- Jalur `ALUR`: Bahan (`PETA.md`, `explore.py list` untuk panen dari laporan jalur mana pun), Dispatch (K7),
  Laporan (`new --jalur ALUR`, isi menurut Penanganan Balikan, `check` maksimal 3 putaran perbaikan), dan Ringkasan.
- Transisi: sesudah `TELUSUR`, permintaan "dalami sisi X" pindah ke `ALUR` dengan panen dari laporan itu.
- Guardrails: NOL KODE DI KONTEKS UTAMA tetap berlaku. Ditambah larangan memakai `Explore`/`general-purpose` atas
  repo anak, dan satu butir rationalization ("Explore bawaan lebih cepat, hasilnya sama") beserta alasannya: tanpa
  profil, tanpa kuota, tanpa format, dan tidak lolos `check`.

### Gerbang root multi-repo (backend/frontend)

Kalimat `_workspace` berubah dari "Penelusuran lintas repo dari root: `/fullstack:explore`" menjadi penunjuk bahwa
**semua** penelusuran atau pemahaman kode repo anak dari root lewat `/fullstack:explore` (bila terpasang), bukan
subagent `Explore`/`general-purpose` bawaan. Keluaran repo tunggal tidak berubah satu byte pun.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | L1 (`explore.py` jalur `ALUR` + template) | Pagar laporan lebih dulu; prosa skill dan agent berdiri di atas keluaran skrip. |
| 2 | L2 (agent `backend-explorer`, `frontend-explorer`), L3 (`dispatcher/explorer.md`) | Kontrak balikan menjadi masukan template laporan. |
| 3 | L4 (skill `fullstack:explore`) | Merangkai L1–L3. |
| 4 | L5 (gerbang root backend/frontend) | Pemicu baru berarti setelah jalurnya ada. |
| 5 | L6 (test drift + smoke), D1 (dokumen + versi) | Penutup. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada dan
harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| L1 | `fullstack/skills/_common/explore.py` (`new`, `list`, `check`, `seam`), `fullstack/skills/explore/templates/alur-template.md` (baru) | skill, `check_preconditions.py` (`laporan`) | tidak | `tests/fullstack/test_explore_21.py`, `test_skill_21.py` (`new`, alur laporan lengkap), `test_abaikan_22.py` (pesan `new`/`check`) | Sedang: `TELUSUR` harus tetap byte-sama keluarannya; laporan lama tanpa `jalur` wajib lolos. |
| L2 | `fullstack/agents/backend-explorer.md`, `fullstack/agents/frontend-explorer.md` (baru) | L4 | membaca profil backend/frontend | `tests/test_lint_plugins.py` (frontmatter agent) | Nihil (baru) |
| L3 | `fullstack/skills/explore/dispatcher/explorer.md` (baru) | L4 | tidak | — | Nihil (baru) |
| L4 | `fullstack/skills/explore/SKILL.md` | model | tidak | `tests/fullstack/test_skill_21.py` bila memaku teks skill | Rendah |
| L5 | `backend/hooks/gate_text.py`, `frontend/hooks/gate_text.py` (`_workspace`) | hook SessionStart di root multi-repo | **ya** (backend + frontend) | `tests/hooks/test_workspace_root_21.py`, `tests/hooks/test_gate_text.py` | Rendah: hanya cabang root multi-repo. |
| L6 | `tests/fullstack/test_alur_23.py` (baru), `tests/test_smoke.py` (`CASES`) | CI | membaca `code-explorer` backend/frontend (K12) | `test_smoke.py` | Rendah |
| D1 | `fullstack/README.md`, `flow/fullstack.md`, `flow/backend.md` dan `flow/frontend.md` (teks hook root), `plugin.json` ×3, `README.md` root, `CLAUDE.md` repo | manusia, lint M4/M7 | ya | `test_lint_plugins.py` | Nihil |

## L1 [Tinggi] Laporan `explore.py` hanya mengenal `TELUSUR`
- [x] Selesai

`new --jalur/--kedalaman`, `alur-template.md`, `list` dengan `jalur`, `check` per jalur (tabel Kontrak), dan `seam`
yang menolak `ALUR`. Test: `new` ALUR menulis frontmatter `jalur`/`kedalaman` dan seksi `ALUR`; `--kedalaman` wajib
untuk ALUR dan ditolak untuk TELUSUR; repo tanpa profil `VALID` ditolak; laporan lama tanpa `jalur` lolos `check`
sebagai TELUSUR; check 4 ALUR (repo tanpa subseksi, subseksi tanpa langkah berbukti, repo di `Belum disisir` lolos);
check 6 ALUR (baris tabel tanpa rujukan); `seam` atas ALUR ditolak; `list` melaporkan `jalur`.

## L2 [Tinggi] Belum ada subagent penelusur alur di root
- [x] Selesai

`agents/backend-explorer.md` dan `agents/frontend-explorer.md` menurut Kontrak: diadaptasi dari
`backend/agents/code-explorer.md` dan `frontend/agents/code-explorer.md`. Bacaan profil FE mengikuti jangkar yang
dipaku `tests/fullstack/test_profile_anchor_21.py`.

## L3 [Sedang] Belum ada template dispatch explorer
- [x] Selesai

`skills/explore/dispatcher/explorer.md`: slot, gerbang masuk, plafon K7, dan Penanganan Balikan.

## L4 [Tinggi] Skill tidak punya jalur alur dan tidak menutup jalan ke `Explore` bawaan
- [x] Selesai

`SKILL.md`: deskripsi, Phase 0 jalur `ALUR`, langkah jalur `ALUR`, transisi dari `TELUSUR`, Guardrails, Output, dan
Failure path (explorer gagal dua kali, `check` ALUR masih FAIL sesudah 3 putaran).

## L5 [Sedang] Gerbang root hanya menunjuk `/fullstack:explore` untuk penelusuran lintas repo
- [x] Selesai

`_workspace` backend dan frontend (K11). Test: kalimat baru muncul di root multi-repo, menyebut `Explore` bawaan
sebagai yang tidak dipakai, dan keluaran repo tunggal tidak berubah.

## L6 [Rendah] Drift dan smoke
- [x] Selesai

`tests/fullstack/test_alur_23.py`: frontmatter kedua agent (`tools` tanpa `Write`/`Edit`/`Bash`, `model: sonnet`),
seksi balikan yang dibaca dispatcher ada di agent, slot dispatcher terisi semua di Penanganan Balikan, dan angka
jendela baca (K12) sama dengan `code-explorer` sumbernya. Smoke: `explore.py new --jalur ALUR` di empat keadaan repo.

## D1 [Rendah] Dokumen dan versi
- [x] Selesai

README `fullstack` (jalur dan subagent baru), `flow/fullstack.md` (komponen, alur `ALUR`, catatan turunan K12),
`flow/backend.md` dan `flow/frontend.md` (teks hook root), README root, dan paragraf `fullstack` di `CLAUDE.md`.
Versi: fullstack 0.3.0, backend 0.14.1, frontend 0.13.1.

## Di luar cakupan

- Pagar mekanis PreToolUse atas tool `Agent` untuk menolak `Explore`/`general-purpose` (K11). Dinilai ulang bila
  pemicu baru masih bocor.
- Explorer terdegradasi untuk repo tanpa profil (K5).
- Putaran kedua `ALUR` dan jahitan dari laporan `ALUR` (K7, K9).
- Jalur pemahaman alur di **dalam** repo (`backend:tech-lead` lane `EXPLORE_FACT` dengan `Kedalaman` dipatok
  `ringkas`). Itu celah tersendiri milik plugin backend/frontend.

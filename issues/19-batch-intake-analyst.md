# Langkah 19 — Batch intake analyst: hingga lima tiket berurutan dengan scout di depan (B1–B7, D1)

Sumber: feedback user 2026-10-02 dan diskusi desain sesi yang sama. Basis kode plugin: commit `7423c86`
(analyst 0.14.0).

**Status (2026-10-02):** rencana, belum dikerjakan.

## Tujuan

1. Satu pesan berisi beberapa permintaan (maksimal 5) diproses dalam satu alur. Hasilnya tetap satu
   `TICKET.md` per tujuan pengguna. Sekarang `intake` Phase 4 memaksa user memilih satu tujuan, dan sisanya
   menjadi antrian tiket yang masing-masing harus masuk `intake` lagi.
2. Tiket diproses **berurutan penuh**: tiket ke-k selesai (elisitasi → spec → review → persetujuan → sinkron)
   sebelum tiket ke-k+1 dimulai. Urutannya ditentukan `intake` secara otomatis.
3. Waktu tunggu penelusuran kode dipotong. Di awal batch, `code-scout` untuk semua tiket didispatch paralel,
   sehingga hasil scout tiket berikutnya sudah siap ketika gilirannya tiba.
4. Batch tahan sesi putus. Seluruh ticketdir dialokasikan di awal beserta permintaan aslinya, dan urutannya
   tersimpan di frontmatter. Sesi berikutnya melanjutkan dari tiket terbuka berurutan terkecil.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | B1 (`new --batch/--urutan`), B2 (`state`), B3 (validator frontmatter) | Pagar mesin lebih dulu; prosa berdiri di atas keluaran skrip. |
| 2 | B4 (`intake` + `references/batch.md` + berkas wajib gerbang) | Pintu masuk batch dan prosedur bersama yang dirujuk elicit dan spec. |
| 3 | B5 (`elicit`, dispatcher scout, panduan, template) | Alokasi batch dan scout paralel bergantung pada B1 dan B4. |
| 4 | B6 (`spec`: lanjut ke tiket berikutnya, ringkasan batch) | Penutup tiket memakai `state --batch` dari B2. |
| 5 | B7 (smoke), D1 (dokumen + versi) | README, `flow/analyst.md`, `plugin.json` 0.15.0. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada
dan harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| B1 | `skills/_common/ticket.py` (`new`), `skills/_common/analyst_lib.py` (`ticket_skeleton`) | `elicit` Precondition 2 | tidak | `tests/analyst/test_ticket_10.py` (paritas kerangka: tetap dipanggil tanpa batch) | Rendah: dua field pembukuan baru di luar sidik isi dan segel; tiket tunggal tidak berubah satu byte pun. |
| B2 | `skills/_common/ticket.py` (`state`) | `intake` Phase 1 dan 5, ringkasan batch | tidak | test yang membaca `state --json` (`test_ticket.py`, `test_ticket_8a.py`, `test_ticket_10.py`, `test_bom.py`) | Rendah: kunci JSON bertambah; urutan baris hanya bergeser untuk tiket batch. |
| B3 | `skills/_common/validate_doc.py` (`_frontmatter_common`) | semua gerbang (`close`, `check`, `review`, `approve`) | tidak | — | Rendah: hanya berlaku bila field batch ada. |
| B4 | `skills/intake/SKILL.md`, `skills/intake/references/batch.md` (baru), `skills/_common/ticket.py` (daftar berkas wajib `check`) | model, `check --gate elicit/spec` | tidak | `tests/analyst/test_scout_18.py` (pola salin-plugin untuk berkas wajib) | Sedang: Phase 4 berubah makna, tidak lagi memilih satu tujuan. |
| B5 | `skills/elicit/SKILL.md`, `skills/elicit/dispatcher/scout.md`, `skills/elicit/references/elicitation-guide.md` (bagian 5), `skills/elicit/templates/elicit-template.md` (prosa bagian 1–2) | model | tidak | `tests/analyst/test_scout_18.py` (bila teks plafon ikut diuji) | Sedang: plafon scout dan giliran berubah dari per sesi menjadi per tiket. |
| B6 | `skills/spec/SKILL.md` (Output) | model | tidak | — | Rendah |
| B7 | `tests/test_smoke.py` (`CASES`) | CI | tidak | `test_smoke.py` | Rendah |
| D1 | `README.md` analyst, `flow/analyst.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (deskripsi, lint M4), `CLAUDE.md` repo (baris plugin analyst) | manusia, lint M4/M7 | tidak | `test_lint_plugins.py` | Nihil |

**Tidak diubah:**
- `ticket_seal`, `SEAL_FIELDS`, dan `CONTENT_FIELDS`. Field batch berada di luar ketiganya, sehingga salinan
  segel di `precondition_lib.py` backend/frontend dan pembaca `ticket_source` tidak tersentuh.
- `ticket-reviewer`, `code-scout`, `nataflow_sync.py`, `sync-payload`, dan skill `notulen`.
- Commit per tiket per tahap (`close`, `commit --stage`, `approve`) tetap seperti sekarang.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Maksimal 5 tiket per batch.** Lebih dari 5 tujuan → lima teratas menurut urutan K4 masuk batch; sisanya antrian tiket seperti sekarang. Batch minimal 2 tiket; satu tujuan berjalan sebagai tiket tunggal tanpa field batch. | Keputusan user. |
| K2 | **Satu `AskUserQuestion` = satu tiket.** Pertanyaan beberapa tiket tidak pernah digabung dalam satu panggilan. Header tiap pertanyaan `Tiket <k>/<N>`. Batas 3 pertanyaan per giliran tetap. | Keputusan user: satu konteks per pertanyaan. Header ≤ 12 karakter muat `Tiket 5/5`. |
| K3 | **Berurutan penuh.** Tiket ke-k+1 baru dimulai sesudah tiket ke-k selesai, yaitu sesudah baris penutup atau blok `TERTAHAN`-nya tersaji: `READY` (beserta sinkron), *Tahan* di spec, `TERTAHAN` di elicit, atau dibatalkan. | Keputusan user. Tiket yang macet tidak menahan tiket lain. |
| K4 | **Urutan otomatis tanpa pertanyaan.** Kriteria: (1) tujuan yang menjadi prasyarat tujuan lain menurut kata-kata peminta lebih dulu; (2) urgensi yang disebut peminta (tenggat, pengguna terhambat, bug yang sedang berdampak); (3) seri → urutan di pesan user. Daftar urutan disajikan sekali di blok `INTAKE — BATCH` sebelum tiket pertama mulai. | Keputusan user. Kriteria dari kata-kata peminta saja, sejalan dengan NOL KODE di intake. |
| K5 | **Alokasi semua ticketdir di awal batch, oleh `elicit`.** `ticket.py new` dijalankan berurutan untuk tiap tiket sebelum tiket pertama dielisitasi. `intake` tetap tidak menulis berkas. | Permintaan asli langsung tersegel (`request_hash`) di disk, sehingga sesi putus tidak menghilangkan tiket yang belum digarap. Membagi K5 per tiket (alokasi saat giliran tiba) membuat antrian hanya hidup di percakapan. |
| K6 | **Urutan disimpan di frontmatter**: `batch: <id>` dan `urutan: <k>/<N>`, dengan `<id>` = nama ticketdir tiket berurutan 1. Field ini pembukuan, di luar sidik isi dan segel. `state` mengurutkan baris batch menurut `urutan`, dan `state --batch <id>` menyaring satu batch. | Sesi berikutnya melanjutkan batch dari tiket terbuka berurutan terkecil tanpa menyusun ulang. Id dari nama ticketdir dapat diverifikasi skrip, tidak bergantung pada jam yang ditebak model. |
| K7 | **Scout di awal batch, paralel.** Sesudah semua `new` `PASS`, satu dispatch `code-scout` per tiket yang membutuhkannya (`TECH` selalu `BUKTI`; tipe lain `KONTEKS` bila permintaannya menyebut layar, menu, laporan, status, atau data), semuanya dalam satu pesan. Dispatch ini dihitung sebagai dispatch pertama tiket itu. Phase 2 tiket ke-k menunggu balikan scout tiket ke-k saja. | Keputusan user. Hanya `elicit` yang mendispatch scout (Langkah 18 K4) tetap berlaku. |
| K8 | **Plafon per tiket**: 2 dispatch scout dan 5 giliran tanya-jawab per tiket, bukan per sesi. Dispatch ulang karena balikan hilang dari percakapan (diringkas otomatis atau sesi baru) tidak dihitung, sama seperti dispatch ulang karena gagal. | Tanpa ini, tiket kelima tidak punya jatah scout atau giliran. Hasil scout tidak ditulis ke disk karena scout read-only. |
| K9 | **Tidak ada fakta lintas tiket.** Jawaban yang diberikan untuk tiket A hanya boleh masuk tiket B sebagai `Asumsi:`, yang wajib dikonfirmasi di Phase 4 tiket B. | Iron Law elicit: fakta berasal dari permintaan asli atau log tiket itu sendiri. Reviewer menilai tiap tiket hanya dari catatannya. |
| K10 | **Permintaan asli per tiket.** Butir yang tertulis terpisah → potongan butir itu apa adanya, tanpa nomor atau penanda daftarnya. Tujuan yang bercampur dalam satu paragraf → teks utuh di tiap tiket, dan tujuan lain dicatat di `Batas Cakupan` tiket itu sebagai `— tiket <slug>`. | Verbatim tetap terjaga. Penanda `tiket terpisah` adalah mekanisme yang sudah dipakai elicit, spec, dan `ticket-reviewer`. |
| K11 | **Peminta ditanya sekali per batch.** Opsi: *Saya sendiri*, peran yang disebut permintaan, atau *Berbeda per tiket* (disebutkan lewat *Other*). | `new` mewajibkan `--requester` untuk tiap tiket, dan semuanya dialokasikan di awal (K5). |
| K12 | **Tipe boleh campur dalam satu batch, termasuk `TECH`.** Tiap tiket memakai panduan tipenya sendiri. Bagian `TECH` untuk repo lain tetap masuk antrian tiket. | Karena K2 dan K3, tiap tiket punya giliran sendiri sehingga gaya tanya teknis dan non-teknis tidak bercampur. |
| K13 | **Batch hanya untuk tiket baru.** Butir lain di pesan yang sama (ubah tiket `READY`, batalkan, sinkron ulang, tanya status, kerja di luar wilayah) disebut beserta rutenya di blok intake, tetapi tidak dijalankan dalam batch. Butir kembar dalam batch digabung menjadi satu tiket dan disebut di blok. | Rute selain tiket baru punya gerbangnya sendiri; mencampurnya membuat urutan K4 tidak bermakna. |
| K14 | **Ringkasan batch** disajikan sesudah tiket terakhir, atau saat user berhenti di tengah, dari `ticket.py state --batch <id>`. | Satu tempat untuk melihat tiket mana yang `READY`, tertahan, atau belum disentuh. |

## Kontrak

### `ticket.py new` (batch)

```text
new --slug <s> --type <t> [--category <c>] --requester "<r>" --request - [--title "<j>"]
    [--urutan <k>/<N> [--batch <id>]]
```

- Tanpa `--urutan` dan `--batch` → tiket tunggal, perilaku sekarang.
- `--urutan 1/<N>`: `--batch` dilarang. Skrip menulis `batch: <nama ticketdir sendiri>` dan `urutan: 1/<N>`.
- `--urutan <k>/<N>` dengan k ≥ 2: `--batch <id>` wajib. `analyst/tickets/<id>/TICKET.md` harus ada dengan
  `batch: <id>` dan `urutan: 1/<N>` (N sama), dan belum ada tiket lain di batch itu dengan urutan k.
- Ditolak (`NEW FAIL`, exit 1): N di luar 2–5, k di luar 1–N, `--batch` tanpa `--urutan`, id tidak dikenal, N
  berbeda dari tiket berurutan 1, urutan kembar.
- Ticketdir `KOSONG` ber-slug sama tetap dipakai ulang, dan field batch ikut ditulis.
- Keluaran `PASS` menambah segmen ` · batch=<id> urutan=<k>/<N>`.

### Frontmatter `TICKET.md`

Dua baris sesudah `request_hash`, hanya pada tiket batch:

```yaml
batch: 2610021430-cicilan-pembayaran
urutan: 2/4
```

Validator (`_frontmatter_common`): keduanya ada atau keduanya absen; `urutan` cocok `^[1-5]/[2-5]$` dengan
k ≤ N; `batch` berbentuk nama ticketdir (`<YYMMDDhhmm>-<slug>`); tiket berurutan 1 → `batch` sama dengan nama
ticketdir-nya sendiri.

### `ticket.py state`

- Tiap baris JSON menambah `batch` dan `urutan` (`-` bila bukan tiket batch).
- Urutan baris: kunci `(batch atau nama ticketdir, k atau 0)`. Satu batch tampil berurutan di posisi tiket
  berurutan 1-nya.
- Baris teks tiket batch menambah segmen ` · batch <id> <k>/<N>`.
- `--batch <id>`: hanya tiket batch itu, termasuk `READY` dan `DIBATALKAN` (setara `--all`).

### Alur batch (`skills/intake/references/batch.md`)

```text
intake : pecah (≤ 5) → wilayah dan tipe per butir → duplikat (READY, terbuka, dalam batch) → urutan K4
         → slug → peminta (sekali) → blok INTAKE — BATCH → analyst:elicit { batch: [...] }
elicit : new ×N berurutan (urutan 1/N dulu, id dari keluarannya) → scout paralel (satu pesan) → tiket 1
tiket k: elicit Phase 0–5 → spec Phase 0–5 → baris penutup atau TERTAHAN → tiket k+1 (elicit lanjutan)
akhir  : sesudah tiket N, atau user berhenti → ringkasan dari state --batch <id>
resume : intake Phase 1 → tiket terbuka berurutan terkecil di batch itu → lanjut per alur di atas
```

`batch.md` adalah satu-satunya tempat aturan batch. `intake`, `elicit`, dan `spec` merujuknya dan dilarang
menulis ulang isinya. Berkas ini masuk daftar berkas wajib `check --gate elicit` dan `check --gate spec`.

### Blok `intake` untuk batch

```markdown
### INTAKE — BATCH <N> tiket
1. <type>[/<category>] · <slug> — <tujuan>
2. …
- **Peminta**: <requester | per tiket: …>
- **Digabung**: <butir kembar yang dijadikan satu tiket> | —
- **Antrian tiket**: <tujuan ke-6 dst., bagian repo lain> | —
- **Di luar batch**: <butir bukan tiket baru beserta rutenya> | —
```

Baris penutup: `INTAKE — BATCH · <N> tiket · next analyst:elicit`. Baris bernilai `—` dihapus.

### Ringkasan batch

```markdown
### BATCH <id> — <r> READY dari <N>
| # | Ticketdir | Keadaan | nataflow |
|---|---|---|---|
| 1 | <ticketdir> | READY | dibuat #<code> |
| 2 | <ticketdir> | ELISITASI — tertahan: menunggu <siapa> | — |
- **Belum disentuh**: <urutan yang tidak sempat diproses di sesi ini> | —
```

Kolom `Keadaan` dari `state --batch`; kolom `nataflow` dari baris penutup tiap tiket di sesi ini, `—` bila tidak
ada.

## B1 [Tinggi] `ticket.py new` belum mengenal batch
- [ ] Selesai

`new` hanya mengalokasikan satu tiket, dan nama ticketdir yang dialokasikan pada menit yang sama terurut
menurut slug, bukan menurut urutan pilihan intake. **Perubahan:** argumen `--urutan`/`--batch` sesuai
Kontrak; `ticket_skeleton` menerima `batch` dan `urutan` opsional dan menulis kedua baris hanya bila terisi.

**Test:** `tests/analyst/test_batch_19.py`:
- `--urutan 1/3` menulis kedua field, dan keluaran memuat segmen batch;
- tiap penolakan di Kontrak menghasilkan exit 1 tanpa menulis ticketdir;
- `content_hash` (ketiga bagian) dan `ticket_seal` sama dengan dan tanpa field batch;
- tiket batch melewati `close` → `review` → `approve` seperti tiket tunggal;
- paritas kerangka `test_g9` tetap hijau tanpa perubahan.

## B2 [Sedang] `state` tidak tahu urutan batch
- [ ] Selesai

**Perubahan:** kolom, urutan baris, dan `--batch` sesuai Kontrak.

**Test:** slug dipilih supaya urutan abjad berbeda dari urutan batch, lalu `state` menampilkan urutan batch;
`--batch` ikut menampilkan `READY` dan `DIBATALKAN` dan menyaring batch lain; baris non-batch berisi `-`.

## B3 [Sedang] Field batch tanpa pagar validator
- [ ] Selesai

Field yang disunting tangan (`urutan: 7/3`, `batch` tanpa `urutan`) membuat urutan resume salah tanpa ada yang
menolak. **Perubahan:** aturan frontmatter sesuai Kontrak di `_frontmatter_common`, sehingga berlaku di
`--kind elicit` dan `--kind ticket`.

**Test:** tiap pelanggaran → `FAIL` check frontmatter; tiket tanpa field batch tetap `PASS`.

## B4 [Tinggi] `intake` memaksa satu tujuan per pesan
- [ ] Selesai

**Perubahan:**
- `skills/intake/references/batch.md` baru: alur, kriteria urutan (K4), syarat selesai satu tiket (K3), aturan
  resume, dan kedua blok Kontrak.
- `intake/SKILL.md`:
  - description: menyebut beberapa permintaan sekaligus (hingga 5);
  - Iron Law: satu tiket satu tujuan tetap; banyak tujuan menjadi batch berurutan;
  - Phase 1: resume batch → tiket terbuka berurutan terkecil;
  - Phase 4: lebih dari satu tujuan → batch (K1), tanpa pertanyaan memilih; K12 untuk `TECH` repo lain;
  - Phase 5: duplikat juga di dalam batch (K13);
  - Phase 6: slug unik per tiket, peminta sekali (K11), serah terima `batch` ke `elicit`, permintaan per tiket
    (K10);
  - Output: blok `INTAKE — BATCH`;
  - Failure path 2 diganti: user bersikeras menggabungkan beberapa tujuan dalam satu tiket.
- `ticket.py`: `intake/references/batch.md` masuk daftar berkas wajib `check --gate elicit` dan `--gate spec`.

**Test:** salin plugin ke tmp, hapus `batch.md`, lalu `check --gate elicit` dan `--gate spec` → check 2 `FAIL`;
lint R-check bersih.

## B5 [Tinggi] `elicit` belum bisa mengalokasikan batch dan menjalankan scout di depan
- [ ] Selesai

**Perubahan:**
- `elicit/SKILL.md`:
  - Parameter `batch` (daftar berurutan `{slug, type, category, request, requester}`);
  - Precondition 2: alokasi batch per K5 dan Kontrak `new`;
  - Phase 0: cabang awal batch, yaitu alokasi lalu scout paralel (K7);
  - Iron Law: plafon scout per tiket (K8), satu `AskUserQuestion` satu tiket (K2), tanpa fakta lintas tiket (K9);
  - Phase 2: plafon giliran per tiket; butir 7 menandai tujuan yang sudah menjadi tiket lain di batch sebagai
    `— tiket <slug>` tanpa bertanya;
  - Phase 5 dan Output: `TERTAHAN` di tengah batch → lanjut tiket berikutnya per `batch.md`.
- `dispatcher/scout.md`: plafon per tiket, dispatch paralel di awal batch, dan dispatch ulang karena balikan
  hilang tidak dihitung.
- `references/elicitation-guide.md` bagian 5: tujuan kedua yang sudah ada di batch tidak ditanyakan ulang.
- `templates/elicit-template.md`: bagian 1 menyebut kedua baris batch (pola baris `category`), bagian 2 butir 1
  menyebut aturan validatornya.

**Test:** `test_scout_18.py` disesuaikan bila teks plafon ikut diuji; selebihnya ditagih lint R-check.

## B6 [Sedang] `spec` berhenti sesudah satu tiket
- [ ] Selesai

**Perubahan:** `spec/SKILL.md` Output: sesudah baris penutup tiket batch (`READY`, *Tahan*, dibatalkan), lanjut
ke tiket berikutnya per `batch.md`; sesudah tiket terakhir, sajikan ringkasan batch.

## B7 [Rendah] Smoke untuk `state --batch`
- [ ] Selesai

Tambah kasus `ticket.py state --batch 2609250000-smoke --json` ke `CASES` `tests/test_smoke.py`.

## D1 [Rendah] Dokumen dan versi
- [ ] Selesai

- `README.md` analyst: `## Workflow` (batch), `## Artefak` (field batch), `## Penegakan Mekanis` (`new
  --urutan`, `state --batch`).
- `flow/analyst.md`:
  - `### analyst:intake`: Phase 4 batch dan urutan;
  - `### analyst:elicit`: awal batch dan scout paralel;
  - `### analyst:spec`: lanjut ke tiket berikutnya;
  - Artefak & Siklus Status: field batch;
  - Titik Gagal: alokasi batch terputus di tengah, balikan scout hilang, sesi putus di tengah batch.
- `plugin.json` → `0.15.0` (lint M7), dengan deskripsi yang sama persis di `marketplace.json` (lint M4), dalam
  commit `chore(release)` tersendiri.
- `CLAUDE.md` repo: baris plugin analyst menyebut batch.

## Di luar cakupan (fase berikutnya)

- Review `ticket-reviewer` tiket ke-k berjalan paralel dengan elisitasi tiket ke-k+1.
- Pertanyaan gabungan beberapa tiket dalam satu `AskUserQuestion`.
- Notulen → batch tiket: `A-{n}`/`D-{n}` diserahkan ke `intake` sebagai satu batch.
- Menyimpan balikan scout ke disk.
- Batch lebih dari 5 tiket, dan menyusun ulang urutan batch yang sudah dialokasikan.
- Ketergantungan antar-tiket sebagai rujukan formal di kartu atau di nataflow.

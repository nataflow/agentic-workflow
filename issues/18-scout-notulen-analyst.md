# Langkah 18 — Subagent `code-scout` dan skill `notulen` analyst (X1–X5, N1–N8, D1)

Sumber: feedback user 2026-10-02 dan diskusi desain sesi yang sama. Basis kode plugin: commit `d366cd4`
(analyst 0.13.0). Kontrak server dibaca dari `nataflow-api` (`internal/adapters/primary/mcp/tools.go`,
`internal/features/document/domain.go`).

**Status (2026-10-02):** rencana, belum dikerjakan.

## Tujuan

1. `analyst:elicit` bisa memakai konteks kode tanpa mengotori konteks utama. Subagent read-only
   `analyst:code-scout` menelusuri kode secara dangkal: apa yang ada, di mana, dan apa yang tidak ditemukan.
   Ia tidak menelusuri flow, alur, atau edge case.
   - Tiket `TECH`: scout menggantikan kuota 8 `Read`/`Grep`/`Glob` yang sekarang berjalan di konteks utama.
   - Tiket non-`TECH`: scout menambah konteks untuk mempertajam pertanyaan. Hasilnya tidak pernah menjadi fakta
     tanpa konfirmasi peminta.
2. Skill baru `analyst:notulen` merapikan catatan kasar rapat menjadi `NOTULEN.md` terstruktur tanpa mengarang
   isi. Berkas disimpan di disk dan selalu diabaikan git, lalu dapat disinkronkan ke nataflow sebagai dokumen
   `notes.meeting` di bawah project MCP key.

## Prasyarat lintas repo

- Server sudah menyediakan semua tool yang dipakai, jadi tidak ada perubahan di `nataflow-api`:
  - `get_project_info` (tanpa argumen; project yang terikat ke MCP key);
  - `list_document` (`reference_table`, `reference_id`, saring `type` dan `metadata`, `include_content`);
  - `create_document` (`title` opsional; bila terisi, key dokumen = slug judul, dan slug yang sudah dipakai
    dokumen lain di induk yang sama ditolak; `content` di-*trim*);
  - `upsert_document` (identitas `(reference_table, reference_id, key)`; `content` disimpan apa adanya;
    `content_sha256` opsional; `metadata` mengganti utuh; judul tidak disentuh).
- `notes.meeting` lolos format `type` server (`^[a-z]+(\.[a-z]+)*$`, ≤ 50 karakter) dan `TYPE_RE` di
  `nataflow_sync.py`.
- `nataflow_sync.py` (salinan identik di empat plugin, ditagih `tests/test_15_nataflow_sync.py`) **tidak diubah**.
  `notulen.py` hanya memakai fungsinya yang sudah ada (`load_config`, `compact`, `sha256_text`, `h1_title`,
  `check_documents`, `emit_*`).

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | X1 (agent), X2 (dispatcher + gerbang elicit), X3 (validator elicit) | Pagar mesin lebih dulu; prosa elicit berdiri di atasnya. |
| 2 | X4 (prosa elicit + `elicitation-tech.md`), X5 (failure path) | Menyambungkan scout ke alur model. |
| 3 | N1 (`new` + `.gitignore`), N2 (`check`), N3 (`final`), N4 (`state`) | Siklus hidup notulen dikunci skrip sebelum skill ditulis. |
| 4 | N5 (SKILL + template), N6 (tanpa commit) | Prosa di atas keluaran skrip. |
| 5 | N7 (`sync-payload` + prosedur sinkron) | Sinkron bergantung pada status `FINAL` dari N3. |
| 6 | N8 (smoke + lint), D1 (dokumen + versi) | README, `flow/analyst.md`, `plugin.json` 0.14.0. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada
dan harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| X1 | `agents/code-scout.md` (baru) | `analyst:elicit` | tidak | `tests/test_lint_plugins.py` (F2) | Nihil: agent baru. |
| X2 | `skills/elicit/dispatcher/scout.md` (baru), `skills/_common/ticket.py` (daftar berkas wajib `check --gate elicit`) | model, `check --gate elicit` | tidak | `tests/analyst/test_ticket.py` (fixture plugin bila daftar berkas wajib ikut diperiksa) | Rendah: gerbang menagih satu berkas lagi. |
| X3 | `skills/_common/validate_doc.py` (check baru `--kind elicit`, non-`TECH` saja) | `elicit` tiap giliran, `ticket.py close`, `check --gate spec`, `approve` | tidak | `tests/analyst/test_ticket*.py` (fixture catatan non-`TECH` yang kebetulan memuat `` `x:12` ``) | Sedang: catatan lama yang memuat pola itu jadi `FAIL` saat ditutup ulang. |
| X4 | `skills/elicit/SKILL.md` (Iron Law, Phase 1, Guardrails), `skills/elicit/references/elicitation-tech.md` (bagian 2) | model | tidak | `tests/test_lint_plugins.py` (R-check) | Sedang: guardrail NOL KODE berubah makna. |
| X5 | `skills/elicit/SKILL.md` (Failure path) | model | tidak | — | Rendah |
| N1–N4 | `skills/notulen/scripts/notulen.py` (baru) | `analyst:notulen` | tidak | — | Nihil: skrip baru. |
| N5 | `skills/notulen/SKILL.md`, `skills/notulen/templates/notulen-template.md` (baru) | model, menu `/` | tidak | `tests/test_lint_plugins.py` | Rendah: entri menu kedua; deskripsi tidak boleh bertabrakan dengan `intake`. |
| N6 | — (properti `notulen.py`) | git user | tidak | — | Nihil |
| N7 | `notulen.py` (`sync-payload`), `skills/notulen/references/nataflow-sync.md` (baru) | model | tidak — `nataflow_sync.py` tidak disentuh | — | Rendah: read-only, tanpa commit. |
| N8 | `tests/test_smoke.py` (`CASES`) | CI | tidak | `test_smoke.py` | Rendah |
| D1 | `README.md`, `flow/analyst.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (deskripsi, lint M4), `CLAUDE.md` repo (baris plugin analyst) | manusia, lint M4/M7 | tidak | `test_lint_plugins.py` | Nihil |

**Tidak diubah:**
- `ticket_seal`, `SEAL_FIELDS`, dan `CONTENT_FIELDS`. Salinan segel di `precondition_lib.py` backend/frontend
  tetap identik.
- `ticket-reviewer`, `analyst:intake`, `analyst:spec`, dan `nataflow_sync.py`.
- Hook `SessionStart` backend/frontend. Pengecualian `/analyst:*` di `hooks/gate_text.py` sudah mencakup
  `/analyst:notulen`.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Scout dipakai untuk semua tipe tiket**: `TECH` untuk bukti, non-`TECH` untuk konteks. | Keputusan user 2026-10-02. |
| K2 | **Konteks bukan fakta (non-`TECH`).** Hasil scout boleh mempertajam pertanyaan dan opsi `AskUserQuestion`, dalam bahasa yang terlihat pengguna (layar, menu, tombol, laporan), dan boleh ditulis sebagai `Asumsi:` yang wajib dikonfirmasi di Phase 4. Hasil scout dilarang mengisi pilar sebagai fakta. Guardrail NOL KODE diganti KODE SEBAGAI KONTEKS. | Iron Law "fakta berasal dari peminta" tetap utuh. Validator sudah menolak `Asumsi:` saat `CLOSED`, jadi konfirmasinya ditagih mesin. |
| K3 | **`path:baris` tetap khusus `TECH`.** Catatan elisitasi non-`TECH` yang memuat pola `EVIDENCE` (`` `path:baris` ``) ditolak validator (X3). | Pagar mekanis untuk K2: bukti kode di tiket non-`TECH` adalah kebocoran teknis yang belum tertangkap `scan_leaks` (pemindai itu melewati `## Catatan Elisitasi`). |
| K4 | **Hanya `elicit` yang mendispatch scout.** `intake`, `spec`, dan `notulen` tetap tanpa kode. Plafon 2 dispatch per sesi elisitasi: satu di Phase 1, satu susulan untuk klaim yang belum terbukti. | Cakupan kecil. Intake cukup mengklasifikasi; notulen merekam rapat, bukan sistem. |
| K5 | **Bentuk scout**: `tools: Read, Grep, Glob` (tanpa `Write`), `model: haiku`, `maxTurns: 10`, kuota prosa 8 pemanggilan. Balikan langsung ke konteks pendispatch, tanpa laci `.explore/` dan tanpa hook. | Tanpa `Write`, agent tidak bisa menulis apa pun, sehingga tidak butuh pagar `guard_bash` (analyst memang tidak punya `hooks/`). `maxTurns` membatasi giliran, bukan jumlah tool call; kuota 8 tetap di prosa. Haiku cukup untuk penelusuran dangkal karena bukti `TECH` dibuka ulang oleh `ticket-reviewer` (sonnet) dan keberadaan `path:baris` ditagih `validate_doc.py --kind ticket`. |
| K6 | **Input notulen = catatan kasar** (ditempel di chat atau path berkas), disalin verbatim ke `## Catatan Asli` dan dimateraikan `source_hash`. | Keputusan user. Jejak sumber tetap ada, sama seperti `### Permintaan Asli` di tiket. |
| K7 | **Notulen hanya dokumen.** Tidak ada seksi Calon Tiket dan tidak ada handoff ke `intake` di v1. Keputusan, action item, dan pertanyaan terbuka diberi ID stabil `D-{n}`, `A-{n}`, `Q-{n}`. | Keputusan user. ID stabil membuat penyambungan ke tiket nanti tidak mengubah format. `D-{n}`/`Q-{n}` sudah menjadi namespace analyst untuk keputusan dan pertanyaan. |
| K8 | **Notulen selalu diabaikan git.** `notulen.py new` menulis `analyst/notulen/.gitignore` (`*`) tanpa syarat, dan `notulen.py` tidak pernah meng-commit. | Keputusan user: catatan rapat bisa memuat info sensitif. Beda dengan tiket, yang hanya diabaikan bila config nataflow ada. |
| K9 | **Siklus `DRAFT` → `FINAL`.** `FINAL` hanya ditulis `notulen.py final` sesudah validator `PASS` dan jawaban eksplisit user, lalu disegel `final_hash`. Suntingan sesudahnya membuat keadaan `DRIFT` sampai `final` dijalankan ulang. | Sinkron hanya boleh mengirim isi yang sudah dikonfirmasi pencatat. Prinsip analyst: yang bisa divonis mesin, divonis skrip. |
| K10 | **Sinkron masuk v1, opt-in lewat `.claude/nataflow.json`.** Induknya `project` dengan `reference_id` = `id` balikan `get_project_info`, mengikuti pola `nataflow:create-artifact`. | Keputusan user. Config yang sama dengan sinkron tiket; berkas absen berarti sinkron dilewati. |
| K11 | **Identitas dan idempotensi sinkron.** Metadata dokumen memuat `notulen_key` = path notulendir. Urutannya: `list_document` dengan saring `type` + `metadata` `{"source":"analyst","notulen_key":…}`. 0 hasil → `create_document` dengan `title` (key server = slug judul). 1 hasil → `upsert_document` ke `key` hasil itu; dilewati bila `content_sha256` sama. Lebih dari 1 → berhenti tanpa menulis. | `create_document` tidak idempoten: tanpa `title` dokumen tidak punya key sehingga tidak bisa di-upsert, dan dengan `title` sinkron ulang ditolak karena slug bentrok. Pola cari-lalu-tulis sama dengan `list_task` → `create_task`/`update_task` di sinkron tiket. |
| K12 | **Judul dokumen nataflow** = `<H1> — <tanggal rapat YYYY-MM-DD>`, dikunci saat `create_document` pertama. Mengganti H1 sesudahnya tidak mengganti judul di nataflow (`upsert_document` tidak menyentuh judul). | Tanggal memperkecil peluang bentrok slug antar-rapat berjudul sama (mis. "Weekly Sync"). Bentrok yang tetap terjadi dilaporkan `GAGAL` beserta pesan tool, tanpa menebak judul lain. |
| K13 | **Isi yang dikirim** = badan `NOTULEN.md` tanpa frontmatter dan tanpa `## Catatan Asli`, di-*strip*. | `## Catatan Asli` adalah jejak lokal, sejalan dengan `## Catatan Elisitasi` yang tidak ikut dikirim di sinkron tiket. Isi yang sudah di-*strip* membuat `create_document` (trim) dan `upsert_document` (apa adanya) menghasilkan `content_sha256` yang sama. |

## Kontrak

### `agents/code-scout.md`

Frontmatter:

```yaml
name: code-scout
description: Subagent read-only penelusur kode dangkal untuk analyst:elicit … Dilarang mengedit kode, menelusuri flow/alur/edge case, merancang solusi, atau berdialog dengan user.
tools: Read, Grep, Glob
model: haiku
maxTurns: 10
```

Slot prompt dari `dispatcher/scout.md`:

| Slot | Wajib | Isi |
|---|---|---|
| `mode` | ya | `BUKTI` (tiket `TECH`) atau `KONTEKS` (tipe lain) |
| `root` | ya | path absolut root ruang kerja |
| `pertanyaan` | ya | 1–5 butir. `BUKTI`: klaim peminta tentang kondisi sekarang. `KONTEKS`: konsep, layar, menu, atau data yang disebut permintaan, ditulis apa adanya. |
| `batas` | tidak | direktori yang boleh disisir; kosong = seluruh `root` |

Blok balikan, tanpa teks pengantar:

```markdown
## Code Scout
- Mode: BUKTI | KONTEKS
- Repo: ada kode | tanpa kode
- Pemanggilan: <n> dari 8

### Ditemukan
- P1 — <satu kalimat apa yang ada> — `path:baris`

### Tidak ditemukan
- P2 — <yang dicari> — disisir: `dir/`, `dir2/`

### Belum disisir
- P3 — <alasan: kuota habis | di luar batas>
```

Aturan agent: tiap butir `pertanyaan` berhenti di bukti pertama yang menjawabnya. Agent dilarang:
- membaca berkas utuh di atas 100 baris;
- menelusuri pemanggil, alur, cabang error, atau edge case;
- menulis saran solusi;
- menebak isi yang tidak dibaca.

`Repo: tanpa kode` dibalas segera bila `root` tidak memuat berkas sumber. Butir yang sudah disisir tetapi nihil
masuk "Tidak ditemukan". Butir yang belum sempat disisir masuk "Belum disisir", jangan dicampur.

### `analyst/notulen/<YYMMDDhhmm>-<slug>/NOTULEN.md`

```markdown
---
type: meeting
slug: sprint-review-q4
meeting_date: 2026-10-02
created: 2026-10-02
status: DRAFT
source_hash: <12hex>
final_hash: -
finalized: -
final_answer: -
---

# Sprint review Q4

## Ringkasan
## Peserta
## Agenda
## Pembahasan
## Keputusan
- D-1: …
## Action Item
| ID | Tindakan | PIC | Tenggat |
|---|---|---|---|
| A-1 | … | … | 2026-10-09 |
## Pertanyaan Terbuka
- Q-1: … — menunggu: …
## Catatan Asli
> catatan kasar apa adanya
```

### `notulen.py` (`skills/notulen/scripts/notulen.py`)

| Subperintah | Tulis | Exit | Perilaku |
|---|---|---|---|
| `state [--json]` | — | 0 | Daftar notulendir beserta keadaannya: `DRAFT`, `FINAL`, `DRIFT`, `RUSAK`, atau `NAMA_TIDAK_SAH`. |
| `new --slug --title --date [--json]` (catatan via stdin) | `NOTULEN.md`, `analyst/notulen/.gitignore` | 0/1 | Kerangka dari template, `## Catatan Asli` verbatim, `source_hash`. Slug kembar yang masih `DRAFT` ditolak. |
| `check --notulendir [--json]` | — | 0/1 | Validator N2. |
| `final --notulendir --answer` | frontmatter | 0/1 | Validator `PASS` + jawaban tidak kosong → `status: FINAL`, `final_hash`, `finalized`, `final_answer`. Tanpa commit. |
| `sync-payload --notulendir [--json]` | — | 0/1 | Lihat di bawah. `--json` selalu JSON, termasuk `FAIL`. |

`sync-payload --json`:

- `SKIP`: config tidak ada → `{"status":"SKIP","enabled":false}`.
- `FAIL`: config rusak, notulendir tidak sah, status bukan `FINAL`, keadaan `DRIFT`, atau `check_documents`
  menolak.
- `PASS`:

```json
{
  "status": "PASS",
  "enabled": true,
  "mcp_server": "nataflow-api",
  "notulen_key": "analyst/notulen/2610021400-sprint-review-q4",
  "lookup": {
    "reference_table": "project",
    "type": "notes.meeting",
    "include_content": false,
    "metadata": "{\"source\":\"analyst\",\"notulen_key\":\"analyst/notulen/2610021400-sprint-review-q4\"}"
  },
  "create": {
    "reference_table": "project",
    "type": "notes.meeting",
    "title": "Sprint review Q4 — 2026-10-02",
    "content": "# Sprint review Q4\n\n## Ringkasan\n…",
    "metadata": "{…}"
  },
  "update": {
    "type": "notes.meeting",
    "content": "…sama dengan create.content…",
    "content_sha256": "<64hex>",
    "metadata": "{…sama dengan create.metadata…}"
  }
}
```

`reference_id` diisi model dari `get_project_info`, dan `key` pada `update` dari hasil `list_document`. Kunci
metadata: `source` (`analyst`), `notulen_key`, `slug`, `meeting_date`, `final_hash`, dan `repo`
(`repo_identity`). Nama peserta tidak dikirim di metadata; nama hanya ada di isi dokumen.

### Baris penutup `analyst:notulen`

`NOTULEN — FINAL · <notulendir> · <n> keputusan · <n> action item · <n> Q · nataflow <dibuat | diperbarui | tidak berubah | dilewati | GAGAL: <pesan tool>>`.
Bila belum final: `NOTULEN — DRAFT · <notulendir> · <sebab>`.

---

## X1 [Tinggi] Subagent `code-scout` belum ada
- [x] Selesai

Konteks utama `elicit` sekarang menjalankan sendiri hingga 8 `Read`/`Grep`/`Glob` untuk tiket `TECH`, dan tiket
non-`TECH` tidak punya jalan sama sekali untuk melihat kode. **Perubahan:** `agents/code-scout.md` sesuai
Kontrak. Isinya:
- prosa singkat: fokus penelusuran, kalibrasi kuota, format balikan;
- larangan: edit, Write, flow/alur/edge case, solusi, dialog;
- jalur gagal: `pertanyaan` kosong, `root` tidak ada, dan `tanpa kode`.

**Test:** lint F2 bersih (semua field di `AGENT_FIELDS`); `tools` tidak memuat `Write`, `Edit`, maupun `Bash`;
`maxTurns` berupa angka.

## X2 [Tinggi] Tidak ada dispatcher scout
- [x] Selesai

**Perubahan:**
- `skills/elicit/dispatcher/scout.md` memuat kerangka prompt dengan slot Kontrak.
- `ticket.py check --gate elicit` menambah `dispatcher/scout.md` ke daftar berkas plugin yang wajib ada, dengan
  pola yang sama dengan `dispatcher/reviewer.md` di gerbang `spec`.

**Test:** gerbang `FAIL` bila berkas dispatcher hilang dari salinan plugin di fixture.

## X3 [Tinggi] Konteks kode bisa lolos jadi bukti di tiket non-`TECH`
- [x] Selesai

Tidak ada pagar mesin yang menolak `` `path:baris` `` di catatan non-`TECH`. `scan_leaks` hanya memindai kartu
dan melewati `## Catatan Elisitasi`. **Perubahan:** check baru di `validate_doc.py --kind elicit`, hanya untuk
`type` ≠ `TECH`. Baris yang cocok `EVIDENCE` di catatan elisitasi menghasilkan `FAIL`, kecuali di
`### Permintaan Asli` (dimateraikan dan berasal dari peminta). Tindakannya: "ubah jadi perilaku yang terlihat
pengguna atau `Asumsi:` tanpa rujukan berkas". Check berlaku di tiap giliran, bukan hanya saat `CLOSED`.

**Test:**
- non-`TECH` dengan `` `src/a.go:12` `` di pilar → `FAIL`;
- pola yang sama di `### Permintaan Asli` → `PASS`;
- tiket `TECH` tidak tersentuh;
- fixture lama tetap `PASS`.

## X4 [Sedang] Prosa `elicit` masih melarang kode untuk non-`TECH`
- [x] Selesai

**Perubahan di `skills/elicit/SKILL.md`:**
1. **Phase 1**:
   - `TECH`: petakan brief, lalu dispatch scout `mode: BUKTI` dengan klaim kondisi sekarang. Hanya butir
     "Ditemukan" yang dicatat sebagai `` `path:baris` ``. Butir "Tidak ditemukan" dan "Belum disisir" ditanyakan
     ke peminta di giliran berikutnya.
   - Non-`TECH`: sesudah pilar diisi dari permintaan, dispatch scout `mode: KONTEKS` dengan konsep yang disebut
     permintaan. Hasilnya dipakai untuk menyusun opsi pertanyaan dan `Asumsi:`, tidak ditulis sebagai fakta.
2. **Iron Law**: tambah butir bahwa konteks utama tidak membaca kode. Seluruh pembacaan kode lewat scout.
3. **Guardrails**:
   - NOL KODE → KODE SEBAGAI KONTEKS (K2, K3).
   - KODE BERKUOTA → bukti `TECH` hanya dari butir "Ditemukan" balikan scout; plafon 2 dispatch per sesi.
4. **Rationalization**: tambah "Scout sudah menemukannya, tulis saja sebagai fakta". Kode menunjukkan apa yang
   ada, bukan apa yang diinginkan peminta.

**Perubahan di `references/elicitation-tech.md` bagian 2 langkah 2:** kuota 8 pindah ke scout. Kalimat "klaim
yang tidak terbukti → tanyakan" tetap.

**Test:** lint R-check atas rujukan `dispatcher/scout.md`.

## X5 [Sedang] Jalur gagal scout belum ada
- [x] Selesai

**Perubahan di Failure path `elicit`:**
- Balikan kosong atau tanpa blok `## Code Scout` → dispatch ulang sekali.
- Gagal dua kali:
  - non-`TECH` → lanjut tanpa konteks kode;
  - `TECH` → `ELICIT — TERTAHAN` dengan sebab "bukti kode tidak dapat dikumpulkan".
- `Repo: tanpa kode`:
  - non-`TECH` → lanjut tanpa konteks;
  - `TECH` → `TERTAHAN`, karena ruang kerja bukan repo yang diubah (sejalan dengan intake Phase 4).

## N1 [Tinggi] Alokasi notulendir dan `.gitignore`
- [x] Selesai

**Perubahan:** `notulen.py new` membaca catatan kasar dari stdin dan menulis kerangka template. Catatan disalin
ke `## Catatan Asli` sebagai blockquote, byte demi byte, lalu `source_hash` dihitung. Bila
`analyst/notulen/.gitignore` belum ada, skrip menulisnya berisi `*`, tanpa syarat config (K8). Pola direktori:
`^analyst/notulen/\d{10}-<slug>$`. Root ditemukan lewat `analyst_lib.find_root`.

**Test:**
- `.gitignore` tertulis di repo git dan di direktori non-git;
- `git status --porcelain` bersih sesudah `new`;
- stdin kosong, slug tidak sah, dan slug kembar `DRAFT` → `FAIL`;
- `.gitignore` milik user yang sudah ada tidak ditimpa.

## N2 [Tinggi] Validator notulen
- [x] Selesai

**Perubahan:** `notulen.py check` menagih hal-hal berikut:
- Struktur: tiap H2 Kontrak hadir tepat sekali dan berurutan, dengan `## Catatan Asli` sebagai H2 terakhir. H1
  ada. `meeting_date` berformat `YYYY-MM-DD`.
- Jejak sumber: `## Catatan Asli` sama dengan `source_hash`.
- ID: `D-{n}`, `A-{n}`, dan `Q-{n}` unik dan berurutan.
- Action item: tiap baris punya Tindakan, PIC, dan Tenggat. PIC dan Tenggat boleh persis `belum ditentukan`;
  selain itu Tenggat wajib `YYYY-MM-DD`.
- Pertanyaan terbuka: tiap `Q-{n}` punya `menunggu:`.
- Isi: nol placeholder (`TBD`, `TODO`, `<…>`; pola `PLACEHOLDER` di `analyst_lib`).
- Khusus `final`: nol `Asumsi:`.

**Test:** satu kasus `FAIL` per aturan, ditambah satu kasus `PASS` lengkap.

## N3 [Tinggi] `final` dan deteksi `DRIFT`
- [x] Selesai

**Perubahan:** `notulen.py final` menjalankan validator lalu menulis `status: FINAL`, `final_hash` (sidik badan
tanpa field pembukuan), `finalized`, dan `final_answer`. `state`/`sync-payload` menghitung ulang sidik;
selisih berarti `DRIFT`. `final` boleh dijalankan ulang atas `DRIFT`.

**Test:**
- `final` dengan validator `FAIL` → menolak tanpa menulis;
- jawaban kosong → `FAIL`;
- sunting sesudah `FINAL` → `DRIFT`, dan `final` ulang mengembalikan `FINAL`.

## N4 [Sedang] `state`
- [x] Selesai

**Perubahan:** `notulen.py state [--json]` mendaftar notulendir beserta keadaannya. Skill memakainya di Phase 0
untuk melanjutkan notulen yang belum final. **Test:** kelima keadaan terbaca; `--json` valid tanpa direktori
`analyst/notulen/`.

## N5 [Tinggi] Skill `analyst:notulen`
- [ ] Selesai

**Perubahan:** `skills/notulen/SKILL.md` (`user-invocable`, deskripsi "Gunakan ketika user membawa catatan kasar
rapat …") dan `templates/notulen-template.md`. Isi skill:

- **Iron Law**:
  - isi hanya dari catatan asli atau jawaban pencatat; keputusan tidak dikarang;
  - butir dicatat sebagai **Keputusan** hanya bila catatan atau pencatat menyebutnya diputuskan, selain itu
    masuk **Pembahasan**;
  - `FINAL` hanya lewat `notulen.py final`;
  - tanpa kode, tanpa tiket, tanpa commit.
- **Phase 0**: `state`; lanjutkan notulen `DRAFT`/`DRIFT` bila permintaannya menyambung.
- **Phase 1**: terima catatan (tempel atau path), judul, dan tanggal rapat. Tanyakan yang kosong, lalu `new`.
- **Phase 2**: tata ulang ke struktur template.
- **Phase 3**: klarifikasi celah dengan ≤ 3 pertanyaan per giliran, plafon 2 giliran. Celahnya: peserta,
  keputusan atau diskusi, PIC, tenggat, dan singkatan atau nama yang ambigu. Yang tetap tak terjawab ditulis
  `belum ditentukan` atau menjadi `Q-{n}`.
- **Phase 4**: tulis lalu `check` sampai `PASS`.
- **Phase 5**: ringkasan 2–3 kalimat dan path berkas, lalu `AskUserQuestion` dengan pilihan *Final*, *Koreksi*,
  atau *Tahan*. *Final* menjalankan `final --answer`.
- **Phase 6**: sinkron nataflow (N7).
- **Baris penutup**: sesuai Kontrak.

Deskripsi `intake` tidak diubah. Deskripsi notulen menyebut "bukan tiket" agar kedua skill tidak saling
merebut pemicu.

**Test:** lint F1/F3 bersih; R-check atas rujukan template dan referensi.

## N6 [Sedang] Notulen tidak pernah di-commit
- [x] Selesai

**Perubahan:** properti `notulen.py`. Tidak ada pemanggilan `git_commit`, `git add`, maupun subperintah
`commit`. **Test:** sesudah `new` → `final` di repo git, `git log` tidak bertambah dan `git status` bersih.

## N7 [Tinggi] Sinkron notulen ke nataflow
- [ ] Selesai

**Perubahan:**

1. `notulen.py sync-payload` sesuai Kontrak (K10–K13). Config dimuat lewat `nataflow_sync.load_config`. Isi
   dokumen diambil dari disk karena notulendir tidak pernah ada di git.
2. Referensi baru `skills/notulen/references/nataflow-sync.md` memuat prosedurnya:
   1. Jalankan `sync-payload --json`. `SKIP` → segmen `nataflow dilewati`. `FAIL` → `GAGAL: <problems>`.
   2. Muat tool `mcp__<mcp_server>__get_project_info`, `list_document`, `create_document`, dan
      `upsert_document` lewat ToolSearch. Bila tidak tersedia → `GAGAL: server MCP <mcp_server> tidak tersedia`.
   3. Panggil `get_project_info`. `id` balikannya menjadi `reference_id`. Galat → `GAGAL: <pesan tool>`, dan id
      tidak ditebak.
   4. Panggil `list_document` dengan `lookup` apa adanya ditambah `reference_id`. Lalu, menurut jumlah hasil:
      - 0 → `create_document` dengan `create` ditambah `reference_id`;
      - 1 → bila `content_sha256` hasil sama dengan `update.content_sha256`, segmennya `tidak berubah`; selain
        itu `upsert_document` dengan `update` ditambah `reference_table: project`, `reference_id`, dan `key`
        hasil;
      - lebih dari 1 → berhenti tanpa menulis.
   5. Dilarang menyusun atau menyunting argumen di luar keluaran skrip, mengganti judul saat slug bentrok, dan
      mengulang `create_document` sesudah galat tanpa `list_document` ulang.
3. `GAGAL` tidak menurunkan `FINAL`. Sinkron ulang dilakukan dengan memanggil `/analyst:notulen` "sinkron ulang
   `<notulendir>`".

**Test:**
- `SKIP` tanpa config;
- `FAIL` untuk config rusak, `DRAFT`, dan `DRIFT`;
- `PASS` dengan:
  - `content` tanpa frontmatter dan tanpa `## Catatan Asli`, tanpa spasi tepi;
  - `content_sha256` = `sha256_text(content)`;
  - `title` = H1 + tanggal;
  - `lookup.metadata` hanya berisi `source` + `notulen_key`;
  - keluaran byte-identik pada dua pemanggilan.

## N8 [Rendah] Smoke dan lint untuk CLI baru
- [ ] Selesai

**Perubahan:** tambah tiga kasus `notulen.py` ke `CASES` di `tests/test_smoke.py`: `state --json`,
`check --notulendir … --json`, dan `sync-payload --notulendir … --json`. `--json` harus valid di keempat keadaan
repo. `python3 scripts/lint_plugins.py` hijau tanpa `LINT_IGNORE` baru.

## D1 [Rendah] Dokumen dan versi
- [ ] Selesai

- `README.md` analyst:
  - `## Tiga Skill, Satu Subagent` → empat skill, dua subagent;
  - artefak `analyst/notulen/`;
  - `notulen.py` di `## Penegakan Mekanis`;
  - `## Git`: notulen tidak pernah di-commit;
  - `## Sinkron nataflow`: dokumen `notes.meeting`;
  - `## Sengaja Belum Ada`: notulen → tiket, dan notulen dari transkrip.
- `flow/analyst.md`:
  - Peta Komponen;
  - `### analyst:notulen` beserta diagramnya;
  - Phase 1 `elicit` dan dispatch scout;
  - tabel Subagent;
  - Artefak & Siklus Status (`DRAFT`/`FINAL`/`DRIFT`);
  - Titik Gagal (scout gagal, slug judul bentrok, `DRIFT`).
- `plugin.json` → `0.14.0` (lint M7), dengan deskripsi yang sama persis di `marketplace.json` (lint M4), dalam
  commit `chore(release)` tersendiri.
- `CLAUDE.md` repo: baris plugin analyst menyebut `notulen` dan `code-scout`.

## Di luar cakupan (fase berikutnya)

- Notulen → tiket: seksi Calon Tiket dan serah terima `D-{n}`/`A-{n}` ke `/analyst:intake`.
- Notulen dari transkrip rapat (Meet/Zoom) atau rekaman.
- Reviewer subagent untuk notulen.
- Scout di `intake` (penentuan wilayah backend/frontend, cek fitur sudah ada) dan di `spec`.
- Mengirim `## Catatan Asli` ke nataflow, dan sinkron dua arah (membaca balik dokumen dari nataflow).
- Mengganti judul dokumen nataflow sesudah dibuat.

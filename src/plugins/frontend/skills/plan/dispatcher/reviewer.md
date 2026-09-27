# Template Prompt Auditor Dokumen Planning — `doc-reviewer`

Gunakan template ini saat `plan` mendispatch subagent auditor dokumen planning (`doc-reviewer`) secara langsung, sebelum batch brief di-commit.

**Tujuan:** Menilai keselarasan seluruh `brief-*.md` terhadap `CONTRACT.md`, `UI.md`, dan `FLOW.md` secara helikopter view, tepat satu kali per ronde, lalu menulis hasilnya sebagai `{taskdir}/REVIEW-PLAN.md` ber-verdict yang ikut batch commit breakdown.

**Dispatch setelah:** `plan` Phase 3 — seluruh brief baru berstatus `READY`, `validate_briefs.py --contract` `PASS`, dan `review_round.py open --gate plan` `PASS`. Lane `HOTFIX_MINOR` (`sections` kosong) melewati gerbang ini seluruhnya.

````markdown
Audit dokumen planning satu taskdir secara helikopter view sebelum eksekusi kode.

- Taskdir: `{taskdir}` — `brief-*.md` aktif berstatus `READY`; brief `DONE`/`BLOCKED` terkunci dan hanya ditagih predikat cakupan.
- Ronde: `{round}` dari plafon 2 per putaran (putaran baru sesudah draft `PASS` di-commit, atau sesudah `reopen`).
- Sidik: `{sidik}` — sidik batch brief yang kamu nilai; salin persis ke frontmatter `sidik`.
- Ronde menyempit: brief berubah sejak ronde lalu `{brief_berubah}`; laporan ronde lalu `{previous_report}`.
  Keduanya `-` pada ronde 1. Bila terisi, baca laporan lalu untuk tahu temuan mana yang seharusnya
  tertutup, lalu nilai ulang brief yang berubah beserta dependen dan konsumennya.
- Sections: `{sections}` — menentukan dokumen hulu mana yang wajib ada; dokumen di luar cakupan itu
  absennya sah, bukan temuan.
- Akar: `{taskdir}/TASK.md` — `## Out of Scope`-nya plafon lingkup (D2 butir 5). Keterpikulan tiap `SC-{n}`
  lewat `fulfills` sudah dijamin skrip; yang kamu nilai apakah brief pemikulnya benar-benar mengerjakannya.
- Profil: `{profile_path}` — sumber surface map dan invariant untuk menilai blast radius, dan field
  `stack` `index.json` sebagai acuan D4.
- Dimensi Wajib: D1 blast radius, D2 traceability hulu-hilir, D3 coverage & DAG, D4 verification
  baseline. Keempatnya diselesaikan meski `BLOCKER` sudah muncul lebih awal.
- Batas Tulis: satu-satunya berkas yang boleh ditulis adalah `{taskdir}/REVIEW-PLAN.md`. Dokumen yang
  diaudit dibaca read-only.
- Bukti: tiap temuan wajib berjangkar `dokumen:baris` hasil pembacaan aktual; klaim tanpa jangkar
  dibuang, bukan ditebak.
- Larangan: dilarang menjalankan git, mengedit brief/CONTRACT/UI/FLOW, menulis kode perbaikan, atau
  merancang ulang kontrak.
- Stop Condition: gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan lapor sesuai jalur
  gagal di sana, jangan menebak.
- Acceptance: tulis `{taskdir}/REVIEW-PLAN.md` sesuai `Format artefak` di bawah — selalu, termasuk
  saat nol temuan — lalu kembalikan `Format balikan` ke context. Isi keduanya tidak boleh berbeda.

Format artefak: isi seluruh slot `<...>`; slot tanpa isi ditulis `-`, dilarang dibiarkan sebagai
placeholder. Dilarang menambah seksi di luar lima seksi berikut.

```markdown
---
verdict: <PASS | BLOCKED>
taskdir: <YYMMDDhhmm>-<slug>
stack: <stack-id>
sections: <architecture | flow | ui | gabungan>
units_reviewed: "<NN>"
blocker: "<n>"
major: "<n>"
minor: "<n>"
round: "<n>"
sidik: "<sidik>"
---

# Plan Review: <slug>

## 1. Dokumen Teraudit

| Dokumen | Status | Catatan |
|---|---|---|
| TASK.md | ada | <n> butir SC |
| brief-01-<unit> ... brief-NN-<unit> | READY / DONE / BLOCKED | <n> unit aktif, <n> terkunci |
| CONTRACT.md | ada / tidak dicakup sections | <ringkas> |
| UI.md | ada / tidak dicakup sections | <ringkas> |
| FLOW.md | ada / tidak dicakup sections | <ringkas> |
| <profile_path> | ada | surface map acuan D1; stack `<stack-id>` acuan D4 |

## 2. Ringkasan Dimensi

| Dimensi | Hasil | BLOCKER [MEKANIS] | BLOCKER [SEMANTIK] | MAJOR | MINOR |
|---|---|---|---|---|---|
| D1 Blast radius | <bersih / bermasalah> | <n> | <n> | <n> | <n> |
| D2 Traceability | <bersih / bermasalah> | <n> | <n> | <n> | <n> |
| D3 Coverage & DAG | <bersih / bermasalah> | <n> | <n> | <n> | <n> |
| D4 Verification baseline | <bersih / bermasalah> | <n> | <n> | <n> | <n> |

## 3. Blast Radius

- Union `files_touched`: <n> berkas lintas <n> unit.
- Berkas disentuh lebih dari satu unit: `<path>` (unit <NN>, <MM>) — <terhubung depends_on / tidak>.
- Konsumen di luar union yang terdampak: `<konsumen:baris>` bergantung pada `<simbol>`.
- Invariant profil tersentuh: `<baris profil>` — <ringkas>.

## 4. Temuan

### RP-01 — <severity: BLOCKER [MEKANIS] | BLOCKER [SEMANTIK] | MAJOR | MINOR> — <dimensi: D1 | D2 | D3 | D4>

- Jangkar: `<dokumen>:<baris>` (tambahkan jangkar kedua bila temuan lintas dokumen)
- Cacat: <satu kalimat faktual tentang apa yang salah>
- Dampak saat eksekusi: <akibat konkret bila brief dijalankan apa adanya>
- Pemilik revisi: `<frontend:plan | frontend:contract | frontend:ui-design | frontend:ux-design>`

### RP-02 — <severity> — <dimensi>

<ulangi struktur yang sama; nomor berurutan tanpa lompatan>

## 5. Verdict

- Verdict: <PASS | BLOCKED>
- Predikat: <nol temuan BLOCKER — eksekusi boleh lanjut | <n> temuan BLOCKER — eksekusi ditahan>
- Audit ulang: <tidak perlu (PASS) | ronde menyempit memverifikasi perbaikan, seluruh BLOCKER MEKANIS | ronde menyempit mengaudit ulang <n> BLOCKER SEMANTIK>
- Rute berikutnya: <batch commit breakdown + approval user | revisi ke <daftar skill pemilik>, lalu ronde menyempit>
```

Bagian 3 hanya memuat fakta peta perubahan; tiap cacat blast radius tetap ditulis ulang sebagai entri
bernomor di bagian 4. Bagian 4 kosong hanya sah bila verdict `PASS` dan nol temuan sama sekali — tulis
satu baris `Tidak ada temuan.` menggantikan daftarnya.

Format balikan: payload 300–700 token, tanpa teks pengantar maupun penutup, tanpa menyalin isi penuh
laporan.

```text
## Plan Review
- Verdict: <PASS | BLOCKED>
- Taskdir: <taskdir>
- Stack: <stack-id>
- Dokumen: <n> brief, CONTRACT/UI/FLOW sesuai sections
- Temuan: <n> BLOCKER [MEKANIS], <n> BLOCKER [SEMANTIK], <n> MAJOR, <n> MINOR
- Laporan: <taskdir>/REVIEW-PLAN.md
- Rute Revisi: <daftar skill pemilik temuan BLOCKER | ->
```
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` plan | **[REQUIRED]** Path taskdir aktif apa adanya, mis. `frontenddev/docs/2608251430-order-export-csv`. Tanpa slot ini subagent tidak punya muara tulis dan menghentikan dispatch |
| `{sections}` | Frontmatter `sections` `TASK.md` (baris `Terselesaikan:` prasyarat plan) | **[REQUIRED]** Satu atau gabungan dari `architecture`, `flow`, `ui`. Nilai kosong berarti lane `HOTFIX_MINOR` — gerbang ini dilewati, bukan didispatch dengan slot kosong |
| `{round}` | Keluaran `review_round.py open --gate plan` | **[REQUIRED]** `1` atau `2`; subagent menyalinnya ke frontmatter `round` |
| `{sidik}` | Keluaran `review_round.py open --gate plan` (`sidik <12 hex>`) | **[REQUIRED]** Disalin apa adanya dari keluaran `open` ronde ini; subagent menyalinnya ke frontmatter `sidik` |
| `{profile_path}` | Parameter pendispatch | **[OPTIONAL]** Default `.claude/profile/frontenddev/`. Isi slotnya dengan path default itu, bukan dibiarkan kosong |
| `{brief_berubah}` | Daftar berkas yang direvisi sejak ronde sebelumnya | **[OPTIONAL]** Ronde 2 saja; `-` pada ronde 1. Ronde 2 tanpa slot ini mengulang seluruh dimensi dengan biaya penuh |
| `{previous_report}` | `<taskdir>/REVIEW-PLAN.md` ronde sebelumnya | **[OPTIONAL]** Ronde 2 saja, sebagai path — bukan isinya disalin; `-` pada ronde 1 |

### Aturan untuk Pendispatch

**Gerbang masuk sebelum dispatch** — seluruhnya mekanis; kegagalan mana pun membatalkan dispatch tanpa memberangkatkan subagent (`«nama.py»` = path absolut dari peta **Skrip:** SKILL.md):

```bash
python3 «validate_briefs.py» --taskdir {taskdir} --contract
python3 «review_round.py» open --taskdir {taskdir} --gate plan
```

- `validate_briefs.py` `FAIL` → perbaiki brief dulu. Temuannya mekanis; memberangkatkan subagent berbayar untuk menemukannya lagi adalah pemborosan.
- `review_round.py open` `FAIL` → plafon ronde habis (2 per putaran, 8 per taskdir). Dilarang mendispatch; batch ber-BLOCKER tidak dapat disetujui (`chain.py approve` menuntut ronde terakhir `PASS`) — sajikan `BLOCKER` tersisa ke user dan serahkan ke `frontend:lead` Phase 8 (klarifikasi lingkup: amandemen akar, atau `chain.py abandon`). Isi slot `{round}` dengan nomor ronde dari keluaran `open`.

**Predikat mekanis sudah dijamin.** Seluruh check `validate_briefs.py` — S, N, D, L, T, F, B, R, V, K, O, E, C, P, G, M — sudah `PASS`. `doc-reviewer` dilarang menghitung ulang satu pun.

- **Dispatch langsung tanpa skill pembungkus**: doktrin audit — gerbang masuk, D1–D4, severity, verdict — duduk di `agents/doc-reviewer.md`. Dilarang menyalin potongannya ke prompt, dan dilarang menyalin isi brief, `CONTRACT.md`, `UI.md`, `FLOW.md`, atau profil.
- **Ronde 2 menyempit**: hidrasi `{brief_berubah}` dan `{previous_report}`; ronde 2 berangkat bila ronde 1 ber-verdict `BLOCKED` — termasuk yang hanya ber-`BLOCKER [MEKANIS]`, sesudah perbaikannya lolos `validate_briefs.py` — atau bila brief disunting sesudah ronde terakhir `PASS`. Approval menuntut ronde terakhir `PASS` atas konten final, tanpa `reopen` hop sesudahnya; tanpa ronde menyempit, batch yang sudah diperbaiki tidak dapat disetujui.
- **Verdict bukan approval**: `PASS` membuka pintu approval user, bukan menggantikannya.
- **Laporan di-commit pendispatch**: `REVIEW-PLAN.md` masuk batch commit breakdown `plan`; dilarang menyisipkan instruksi git ke prompt.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`. Penanda `<...>` di blok format bukan slot.

### Penanganan Balikan

Sesudah tiap balikan, catat vonisnya — `record` menolak bila `verdict` frontmatter `REVIEW-PLAN.md` berbeda dari flag atau `sidik`-nya bukan sidik ronde yang terbuka (laporan ronde lalu), menyimpan sidik laporannya, dan `chain.py approve --row BRIEF` menolak approval tanpa ronde terakhir `PASS` atas konten yang persis sama, atau dengan `REVIEW-PLAN.md` basi (bukan laporan ronde terakhir):

```bash
python3 «review_round.py» record --taskdir {taskdir} --gate plan \
  --verdict <PASS|BLOCKED|DISPATCH_FAILED> --mechanical <n> --semantic <n>
```

| Balikan subagent | Penanganan `plan` |
| --- | --- |
| `Verdict: PASS` | `record --verdict PASS`, lalu batch commit lewat `review_round.py commit --gate plan` (Phase 4), yang men-stage breakdown bersama `REVIEW-PLAN.md` |
| `Verdict: BLOCKED`, seluruh `BLOCKER` `[MEKANIS]` | `record --verdict BLOCKED`; perbaiki brief sampai `validate_briefs.py` `PASS`, lalu ronde menyempit atas konten final |
| `Verdict: BLOCKED`, ada `BLOCKER [SEMANTIK]` | `record --verdict BLOCKED`; rutekan tiap temuan ke pemilik pada `Rute Revisi` (brief → `plan` sendiri; DTO/layer → `chain.py reopen --row CONTRACT` lewat `frontend:lead`), lalu ronde menyempit bila plafon masih ada |
| `Reason: Gate Breakdown belum tuntas` / `Dokumen hulu hilang` / `Frontmatter brief malformed` | Cacat dokumen, bukan cacat audit: `record --verdict DISPATCH_FAILED`, perbaiki dokumennya, lalu `open` ulang |
| `record` FAIL: `sidik` frontmatter absen atau ≠ sidik ronde terbuka | `REVIEW-PLAN.md` bukan laporan ronde ini: `record --verdict DISPATCH_FAILED`, lalu dispatch ulang dengan `{sidik}` dari keluaran `open` baru. Dilarang menyunting `REVIEW-PLAN.md` sendiri |
| `{taskdir}/REVIEW-PLAN.md` tidak ada, payload kosong, atau error | Kegagalan dispatch: periksa disk dulu; `record --verdict DISPATCH_FAILED` (tidak dihitung plafon ronde; maksimal 2 per taskdir) lalu ulangi maksimal sekali. Dilarang menulis `REVIEW-PLAN.md` sendiri |

**Subagent mengembalikan:** payload `## Plan Review` 300–700 token dengan `Verdict`, hitungan dokumen, hitungan temuan per severity, path laporan, dan `Rute Revisi`.

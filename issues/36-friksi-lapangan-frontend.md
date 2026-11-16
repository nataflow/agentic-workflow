# Langkah 36 — `frontend`: friksi lapangan — format otomatis, aksi `DELETE`, ronde tambahan, verdict reviewer, plafon journey, keluaran prasyarat terstruktur, lead ramping (F1, D1, T1, V1, J1, S1, L1–L2, R1)

Sumber: analisis lapangan plugin frontend di `~/work/hkm` (2026-11-15) — 6 repo frontend (esim-dashboard, oms-app,
wms-3d, wms-svelte, wms-dashboard, nocan/frontend), 110 sesi, 75 di antaranya memuat skill frontend (20 di 0.16.0,
3 di 0.18.1, 52 di 0.19.0), 49 taskdir beserta `## Riwayat Rantai`-nya. Keputusan diambil 2026-11-16. Basis kode:
commit `acfa709` (frontend 0.19.0). Alat ukur: `scripts/token_usage.py` dan skrip scratch per-sesi/per-taskdir di
atasnya (atribusi sesi → taskdir yang paling sering disebut `tool_use`).

**Status (2026-11-16):** dikerjakan di branch `feat/36-friksi-lapangan-frontend`; target frontend 0.20.0.

## Temuan dasar (data log)

0.19.0 berhasil memotong konteks main loop (rata-rata 224 rb → 143 rb; fase `architect` 282 rb → 134 rb), tetapi
biaya terbesar yang tersisa bukan konteks, melainkan **loop remedi** dan **rantai yang diulang dari nol**:

| # | Friksi | Bukti |
|---|---|---|
| 1 | Reopen BRIEF hanya karena format/lint | 6 taskdir (`app-field-hint-tooltip`, `list-page-card-header`, `dashboard-detail-kartu-klik-2` dua putaran, `kartu-staging-outbound`, `detail-delivery-orders`, `sellorder-foto-bukti`). Implementor tanpa terminal; formatter tidak pernah jalan sebelum gerbang. Tiap putaran = brief perbaikan + Plan Review + approval user + architect |
| 2 | Rantai tak bisa menghapus berkas | 2 abandon (`tooling-hapus-playwright`, `inventory-removal`): template hanya `CREATE`/`MODIFY`, implementor tanpa terminal |
| 3 | Plafon ronde reviewer habis → taskdir diulang dari nol | 5 abandon (`features-layer-refactor`, `app-visual-redesign` ×3 termasuk "format tabel rusak", `dashboard-detail-kartu-klik`): TASK/UI yang sudah disetujui ditulis dan disetujui ulang |
| 4 | Balikan `contract-reviewer` ditolak `record` | 5× `chain.py draft`/`record` gagal + berkas `*-format-rusak.md`/`*-dispatch-failed.md`. Akar: `agents/contract-reviewer.md` menyuruh `PASS — nol temuan`, padahal `REVIEW_LINE` menolak teks sesudah verdict |
| 5 | `journey.py add` gagal 31/176 | Plafon 2 kalimat/280 karakter tidak disebut di prosa mana pun; teks yang gagal memang 3–5 kalimat (pemisah kalimat benar — tidak perlu diubah) dan kebanyakan berisi status ("REPORT terbit", "verifikasi hijau") |
| 6 | 33 penolakan auto-mode classifier | Mayoritas Bash `cat`/`sed`/`grep` atas brief/`TASK.md`/`REVIEW.md` untuk mengambil `base_commit`, status, `files_touched`, `depends_on`. Prosa architect Phase 0 sendiri menyuruh `sed -n 's/^base_commit: //p' TASK.md` |
| 7 | Body `lead` dimuat ulang tiap sesi lanjutan | Fase `lead` 4,8% → 9,1% main loop; body ±24 rb karakter, 52× di 0.19.0 |

## Tujuan

Menghapus loop dan pengulangan yang tidak menambah keputusan apa pun, tanpa melonggarkan predikat gerbang: tiap
perubahan mekanis tetap divonis skrip, dan tiap kelonggaran baru berjalan hanya atas persetujuan user yang tercatat.

## Keputusan

- **K1 (F1)** — Formatter dijalankan `architect` di main loop atas berkas unit, sesudah matriks bukti disk dan
  pemeriksaan anchor, sebelum commit unit. Perintahnya baris opsional `format` di `commands.md` profil; absen →
  langkah dilewati (perilaku lama). Formatter adalah transformasi mekanis, bukan verifikasi — larangan
  lint/test/build per unit tetap.
- **K2 (D1)** — Aksi berkas `DELETE` di tabel seksi 3 brief dan `Files Touched` kontrak. Implementor tidak
  menyentuhnya (tanpa terminal); `architect` menjalankan `git rm` atasnya tepat sebelum commit unit.
- **K3 (T1)** — Plafon 2 ronde per putaran tetap, ditambah **satu ronde tambahan per putaran** hanya atas persetujuan
  user eksplisit (`AskUserQuestion`) yang alasannya dicatat skrip. Plafon 8 per taskdir tidak berubah. Rumusan ulang
  di taskdir baru tetap tersedia; dokumen yang sudah disetujui di taskdir lama boleh dijadikan bahan awal, tetapi
  tetap direview dan disetujui ulang.
- **K4 (V1)** — Skrip menerima komentar sesudah verdict (`- Verdict: PASS — nol temuan`); prosa agent diselaraskan.
- **K5 (J1)** — Plafon journey ditulis di tiap titik panggil; slot teks menyebut "keputusan, bukan status".
  `journey.py` tidak berubah (`teks_problem` dipatok identik dengan backend).
- **K6 (S1)** — Prasyarat `architect` mencetak `base_commit`, perintah `format`, tabel rantai (NN, unit, status,
  aksi berkas, `depends_on`), dan pada ingest daftar path per aksi — sumber tunggal untuk sajian rantai, `git add`,
  `git rm`, dan formatter. Prosa berhenti menyuruh `sed`/`grep` atas dokumen taskdir.
- **K7 (L1)** — Phase 3–7 `lead` (hanya untuk permintaan baru) dipindah ke `lead/references/permintaan-baru.md`;
  sesi lanjutan serah terima tidak memuatnya.
- **K8 (L2)** — Titik henti tambahan sebelum `contract` **ditolak**: perkiraan hemat ±3 jt unit (konteks fase
  `contract` 190 rb → ±120 rb × 437 giliran × 0,1) hampir habis oleh satu pemuatan `lead` tambahan per taskdir
  (±115 rb unit × ±17 taskdir) dan menambah satu `/clear` bagi user.

## Kontrak

### V1 — Verdict reviewer kontrak (P2c)

- `review_round.py` `REVIEW_LINE`: `^-\s*Verdict:\s*(PASS|BLOCKED)(?:\s+—.*)?\s*$` — komentar ber-em-dash sesudah
  verdict sah; bentuk lain (mis. `PASS | BLOCKED` mentah, `**Verdict:**`) tetap ditolak.
- `agents/contract-reviewer.md` Kalibrasi: verdict ditulis `- Verdict: PASS`; nol temuan dinyatakan lewat daftar
  `- —`, bukan teks di baris verdict.

### J1 — Plafon journey di prosa (P2b)

- Tujuh titik panggil (`lead` Phase 7 dan 8, `ux-design`, `ui-design`, `contract`, `plan`, `architect`) memakai slot
  `"<≤2 kalimat, ≤280 karakter: keputusan dan alasannya>"`; `architect` mencatat penyimpangan yang perlu diingat,
  bukan status yang sudah ada di disk.
- `lane-routing-matrix.md` §4a butir 1 menyebut angkanya (2 kalimat, 280 karakter, 40 entri).

### S1 — Keluaran prasyarat `architect` terstruktur (P3a)

- Baris `Terselesaikan:` ditambah `base_commit=<sha7>` dan `format=<perintah | ->`.
- Mode rantai mencetak blok `Rantai:` — satu baris per brief: `NN · <unit> · <status> · <aksi>:<path>,… · depends_on
  [..]`. Mode ingest (`--brief NN`) mencetak `Berkas unit: CREATE=…; MODIFY=…; DELETE=…`.
- `--json` membawa `base_commit`, `format`, `briefs` (list objek) dan, pada ingest, `files` per aksi.
- `architect/SKILL.md` Phase 0 butir 2/3 dan `execution-protocol.md` bagian 3 membaca dari keluaran itu.

### F1 — Format otomatis sebelum commit unit (P1a)

- `precondition_lib.format_command(profile_dir)` membaca `- \`format\`: \`<perintah>\`` dari `commands.md`.
- `execution-protocol.md` bagian 3, langkah commit unit: `<format> <path CREATE+MODIFY>` → `verify_scope.py
  --brief … --worktree` ulang (formatter hanya boleh menyentuh path yang diberikan) → commit. Formatter exit ≠ 0 →
  catat di `## Triase`, unit tetap di-commit tanpa format (verifikasi penutup yang memvonis).
- Template profil `commands.md` dan `profile/SKILL.md`: baris `format` ditulis hanya bila repo sudah bersih format
  di baseline (perintah cek format/lint `OK`) dan formatter menerima daftar path — supaya format tidak merombak
  berkas utuh.

### D1 — Aksi `DELETE` (P1b)

- `validate_briefs.py`: tabel aksi menerima `DELETE` — berkas wajib ada di disk dan belum di-`DELETE` brief hulu
  non-`BLOCKED`; tanpa Anchor; brief hilir dilarang `MODIFY` berkas yang di-`DELETE` hulu; Check T dan C tidak
  menuntut test atas berkas `DELETE`.
- `validate_doc.py` `FILES_ROW` kontrak: `CREATE|MODIFY|DELETE`.
- Implementor: berkas `DELETE` tidak dibuka untuk disunting dan tidak dihapus; konsumennya yang ada di
  `files_touched` disesuaikan; laporan mencatat `DELETE — dihapus architect`.
- Architect: `git rm -q -- <path DELETE>` lalu `git add <CREATE+MODIFY>` dan commit unit; rollback `FAILED` tidak
  menyentuh berkas `DELETE` (belum dihapus).

### T1 — Ronde tambahan atas persetujuan user (P2a)

- `review_round.py open --tambahan "<alasan + jawaban user>"`: sah hanya bila putaran berjalan sudah memakai tepat
  2 ronde, putaran itu belum memakai ronde tambahan, dan plafon taskdir belum habis.
  Entri ronde menyimpan `tambahan`; keluaran `ronde 3/2+1`.
- Pesan plafon (`CAP_ROUTE`) menawarkan urutan: ronde tambahan atas persetujuan user → taskdir baru → hentikan.
- `lead` Phase 8, `contract`/`plan` SKILL dan dispatcher, `lane-routing-matrix.md` §5, README: kelonggaran ini satu-
  satunya, tidak me-reset plafon apa pun.

### L1 — `lead` ramping untuk sesi lanjutan (P3b)

- `lead/SKILL.md` Phase 3–7 pindah utuh ke `lead/references/permintaan-baru.md`; SKILL menyisakan penunjuk wajib baca
  untuk permintaan baru. Lanjutan serah terima tetap melompati Phase 3–7.

### R1 — Dokumen dan rilis

`flow/frontend.md`, `src/plugins/frontend/README.md`, `MIGRATION_v0.19.0_to_v0.20.0.md`, `plugin.json` frontend
0.20.0.

## Peta blast radius

| Berkas | ID |
|---|---|
| `_common/review_round.py` (`REVIEW_LINE`, `open --tambahan`, `CAP_ROUTE`, status) | V1, T1 |
| `agents/contract-reviewer.md` | V1 |
| `lead/SKILL.md`, `ux-design/SKILL.md`, `ui-design/SKILL.md`, `contract/SKILL.md`, `plan/SKILL.md`, `architect/SKILL.md` | J1, T1, S1, F1, D1, L1 |
| `lead/references/lane-routing-matrix.md` §4a, §5; `lead/references/permintaan-baru.md` (baru) | J1, T1, L1 |
| `architect/scripts/check_preconditions.py` (resolusi, blok rantai, ingest, JSON) | S1, F1 |
| `_common/precondition_lib.py` (`format_command`) | F1 |
| `architect/references/execution-protocol.md` bagian 2, 3, 4, 6, 9 | F1, D1, S1 |
| `architect/dispatcher/implementor.md`, `agents/code-implementor.md` | D1 |
| `plan/scripts/validate_briefs.py` (`_action_table`, R, T, C) | D1 |
| `_common/validate_doc.py` (`FILES_ROW`) | D1 |
| `plan/templates/brief-template.md`, `contract/templates/contract-template.md` | D1 |
| `profile/templates/profile-template.md` §6, `profile/SKILL.md` | F1 |
| `contract/dispatcher/reviewer.md`, `plan/dispatcher/reviewer.md` | T1 |
| `flow/frontend.md`, `README.md`, `MIGRATION_*`, `plugin.json` | R1 |
| `tests/frontend/test_friksi_36.py` (baru); `test_12_orchestration.py`, `test_serah_terima_33.py`, `test_a1_ticket_source.py` (rujukan Phase 5/7 lead pindah) | semua, L1 |

Tidak terdampak: salinan byte-identik lintas plugin (`verify_scope.py` — `git status` sudah melaporkan berkas
terhapus sebagai berubah; `run_verification.py`, `docs_git.py`, `detect.py`, `migrate_profile.py`), `journey.py`
(dipatok identik dengan backend), `chain.py` dan format `## Riwayat Rantai` (field `review … r3 …` sudah sah lewat
`r\d+`), backend dan plugin lain, `test_smoke` (tidak ada skrip CLI baru). `done_landed`/`carries_code` sudah
menghitung commit yang hanya menghapus berkas sebagai pembawa kode.

## Tahapan

1. V1 + J1 — perbaikan kecil berisiko rendah.
2. S1 — keluaran prasyarat terstruktur (dipakai F1 dan D1).
3. F1 — format otomatis.
4. D1 — aksi `DELETE`.
5. T1 — ronde tambahan.
6. L1 — `lead` ramping.
7. R1 — dokumen, migrasi, rilis.

Tiap tahap satu commit kode + test; rilis commit terpisah.

## Verifikasi ujung ke ujung

- `uvx pytest` penuh dan `python3 scripts/lint_plugins.py --base origin/main` 0 FAIL.
- Sesudah 0.20.0 terpasang (`token_usage.py ringkas --repo ~/work/hkm/<repo> --since <rilis>` + `Riwayat Rantai`):
  reopen BRIEF beralasan prettier/format mendekati nol; abandon karena plafon ronde turun; `chain.py draft`/`record`
  gagal karena `- Verdict:` nol; `journey.py add` FAIL < 5%; penolakan classifier atas pembacaan dokumen taskdir
  turun; porsi fase `lead` di sesi lanjutan turun.

## Trade-off yang diterima

- F1: diff unit memuat perubahan format pada baris yang disentuh implementor; pada repo yang belum bersih format
  baris `format` sengaja tidak ditulis profil, jadi tidak ada perombakan berkas utuh.
- D1: penghapusan baru mendarat di commit unit, bukan saat implementor bekerja — implementor tidak dapat membuktikan
  sendiri bahwa rujukan ke berkas itu sudah habis; verifikasi penutup (typecheck/build) yang memvonisnya.
- T1: kelonggaran plafon pertama sejak Langkah 12; dibatasi satu per putaran, wajib persetujuan user, dan plafon
  taskdir tetap 8.
- L1: permintaan baru membayar satu `Read` tambahan untuk `permintaan-baru.md`; sesi lanjutan (mayoritas sesi
  0.19.0) memuat ±5 rb karakter lebih sedikit. Penghematannya kecil (±0,5–1% biaya sesi) — diambil karena
  memisahkan jalur yang memang tak pernah dipakai sesi lanjutan.

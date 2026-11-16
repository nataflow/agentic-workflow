# Langkah 38 — `analyst`: friksi lapangan — sidik tahan format, segel ulang, ticketdir dari cwd, ekor batch, temuan sesi (N1, N2, V1, B1, K1, R1)

Sumber: analisis lapangan plugin analyst di `~/work/hkm` (2026-11-16) — 101 sesi yang memuat skill analyst
(19 Okt–16 Nov; analyst 0.17.0 di 65 sesi, 0.19.1 di 36 sesi) dan 216 ticketdir di 6 repo (`orderhub/oms-api`,
`orderhub/oms-app`, `wms/wms-api`, `wms/wms-rust`, `wms/wms-svelte`, `wms/wms-dashboard`). Keputusan diambil
2026-11-16. Basis kode: `main` sesudah Langkah 37 (analyst 0.19.1, backend 0.23.0, frontend 0.21.0). Alat ukur:
`scripts/token_usage.py` dan skrip scratch per sesi di atasnya; frontmatter dan log tanya-jawab tiket dibaca lewat
`md_grep`.

**Status (2026-11-16):** DIKERJAKAN di branch `feat/38-friksi-lapangan-analyst`.

## Temuan dasar (data log)

Angka acuan per tiket READY (107 tiket yang disetujui di dalam transcript): 1,93 jt token setara (82% main loop;
explorer 0,18 jt; reviewer 0,17 jt), 7,8 `AskUserQuestion`, median 38 menit (0.19.1: 27 menit). Intake sendiri
murah: median ±99 rb per sesi, 1,5 menit.

| # | Friksi | Bukti |
|---|---|---|
| 1 | Tiket READY menjadi DRIFT hanya karena diformat | 6 tiket `wms/wms-svelte` (kartu antrian dashboard). 13 Nov 08:05:10 sesi frontend menjalankan `yarn run format` (prettier 3.9.6) atas seluruh repo; keenam `TICKET.md` dan `review.md` berubah pada detik yang sama. Prettier menambah baris kosong di bawah heading, meratakan padding tabel, mengubah `*x*` → `_x_`, menambah `>` kosong di kutipan, dan memadatkan spasi. `analyst/tickets/.gitignore` bersarang tidak dibaca prettier. Validator kartu dan elicit tetap PASS; hanya sidik yang gagal |
| 2 | Validator gagal "Letak ticketdir" | 26 kali (11 di 0.19.1): model `cd` ke ticketdir lalu menjalankan `--ticketdir .`; `normalize_ticketdir` membiarkan path relatif apa adanya sehingga terbaca `.` |
| 3 | Ekor batch tertinggal | 21 dari 111 tiket batch tidak READY (10 ELISITASI, 11 dibatalkan) vs 6 dari 105 tiket tunggal. 6 dari 10 yang macet ber-log 0 (belum pernah disentuh), umumnya urutan terakhir; sebagian sengaja ditahan |
| 4 | Temuan penelusuran sesi tidak dipakai elicit | 45 dari 101 sesi diawali `backend:tech-lead` (selidiki dulu, baru "buatkan tiketnya"). Explorer per tiket sama (1,27 vs 1,22) dan biaya explorer hanya +0,04 jt; selisih 0,3 jt/tiket terutama konteks yang terbawa (median 203 rb vs 169 rb per panggilan) |

## Tujuan

Menghapus DRIFT palsu dan kegagalan gerbang yang tidak menambah keputusan apa pun, tanpa melonggarkan predikat:
suntingan isi tetap DRIFT, penerima lama tetap bekerja, dan tiket yang sengaja ditahan tidak disentuh otomatis.

## Keputusan

- **K1 (N1)** — Sidik isi dihitung atas teks ternormalisasi format (`norm_md`): baris kosong dibuang, penanda
  kutipan `>` menjadi kedalaman, baris dan sel tabel di-strip, baris pemisah tabel menjadi `---`, bullet `*`/`+`
  menjadi `-`, `*` tunggal menjadi `_`, spasi beruntun menjadi satu. Diuji atas 219 salinan tiket hkm: 219/219
  bersidik sama sebelum dan sesudah prettier; suntingan isi tetap terdeteksi.
- **K2 (N1)** — Penulis selalu menulis sidik ternormalisasi; pemeriksa menerima sidik lama **atau** baru, sehingga
  tiket lama dan draft yang sedang berjalan tidak berubah keadaan.
- **K3 (N1)** — `approved_seal` tetap algoritma lama (penerima backend/frontend yang belum diperbarui membandingkannya
  apa adanya). Segel ternormalisasi ditulis ke field baru `approved_seal_norm`; penerima baru PASS bila salah satu
  cocok. `ticket_seal_norm` disalin identik ke `precondition_lib.py` backend dan frontend.
- **K4 (N2)** — `ticket.py reseal` menulis `approved_hash` ternormalisasi dan `approved_seal_norm` untuk tiket READY
  yang isinya masih cocok dengan sidik lama. Isi tidak berubah. Tiket yang sudah DRIFT tidak dapat dipulihkan
  otomatis (teks yang disetujui tidak tersimpan): jalurnya tetap `analyst:spec` REVISE lalu setujui ulang.
- **K5 (V1)** — Path ticketdir relatif yang belum berbentuk `analyst/tickets/<td>` diselesaikan terhadap cwd;
  `find_root` di luar git naik keluar dari `analyst/tickets/<td>`.
- **K6 (B1)** — Nama keadaan tidak berubah. `state` menambah keterangan "belum disentuh sejak <created>" pada
  ELISITASI ber-log 0; ringkasan batch menawarkan *Biarkan terbuka* atau *Batalkan yang belum disentuh* saat user
  berhenti. Tidak ada pembatalan otomatis.
- **K7 (K1)** — Prosa: elicit memakai temuan penelusuran yang sudah ada di percakapan sebagai sumber `KONTEKS`
  (`Asumsi:` yang dikonfirmasi peminta) dan mendispatch explorer hanya untuk konsep yang belum tercakup. `TECH` tetap
  wajib explorer `BUKTI`; lokasi yang sudah diketahui boleh menjadi petunjuk butir pertanyaan.
- **K8** — **Ditolak**: peminta bawaan (intake tetap selalu menanyakan peminta) dan pilar urgensi/ukuran keberhasilan
  opsional (tetap seperti sekarang).

## Kontrak

### N1 — Sidik tahan format

- `analyst_lib.py`: `norm_md`; `content_hash` dan `request_digest` ternormalisasi, versi lama sebagai
  `content_hash_legacy`/`request_digest_legacy`; `hash_matches`, `digest_matches`, `seal_matches`; `ticket_seal`
  tidak berubah; `ticket_seal_norm` baru.
- `ticket.py`: `classify`, `check`, `revise`, `close`, `approve` (menulis `approved_seal_norm`), `reopen`
  (mengosongkannya), `seal_problem`, `next_round` memakai pencocok dua versi.
- `validate_doc.py` [3] `request_hash` dan [11] konten = yang disetujui memakai pencocok dua versi.
- `precondition_lib.py` backend dan frontend: `ticket_seal_norm` identik; `sealed_verdict` PASS bila
  `approved_seal` cocok dengan `ticket_seal` atau `approved_seal_norm` cocok dengan `ticket_seal_norm`.

### N2 — `ticket.py reseal [--ticketdir <td> | --all] [--no-commit]`

- Hanya keadaan READY. Isi cocok dengan sidik yang tersimpan → tulis `approved_hash` ternormalisasi dan
  `approved_seal_norm`; sudah ternormalisasi → dilewati (idempoten). DRIFT dan keadaan lain dilaporkan, tidak disentuh.
- Repo git dan ticketdir ter-track → commit `docs(ticket): segel ulang <slug>`; diabaikan `.gitignore` → tanpa commit.

### V1 — Ticketdir dari cwd

- `normalize_ticketdir`: path relatif yang belum cocok `TICKETDIR_RE` → `(cwd / path).resolve()` relatif ke root.
- `find_root`: bukan repo git dan cwd di dalam `analyst/tickets/<td>` → induk `analyst/`.

### B1 — Ekor batch

- `classify`: ELISITASI tanpa baris log → rute `analyst:elicit (belum disentuh sejak <created> — lanjutkan, atau
  batalkan atas keputusan user)`.
- `intake/references/batch.md` bagian 8/10: user berhenti dengan tiket `Belum disentuh` → satu `AskUserQuestion`
  *Biarkan terbuka (Recommended)* · *Batalkan yang belum disentuh* (`ticket.py cancel --reason`).

### K1 — Temuan sesi

- `elicit/SKILL.md` Phase 1 dan guardrail KODE LEWAT EXPLORER, `elicit/dispatcher/explorer.md` Gerbang masuk.

### R1 — Dokumen dan rilis

`flow/analyst.md`, `src/plugins/analyst/README.md`, `MIGRATION_v0.19.1_to_v0.20.0.md` analyst, `plugin.json`
analyst 0.20.0, backend 0.23.1, frontend 0.21.1.

## Peta blast radius

| Berkas | ID |
|---|---|
| `analyst/skills/_common/analyst_lib.py` | N1, V1 |
| `analyst/skills/_common/ticket.py` | N1, N2, B1 |
| `analyst/skills/_common/validate_doc.py` | N1 |
| `backend/skills/_common/precondition_lib.py`, `frontend/skills/_common/precondition_lib.py` | N1 |
| `analyst/skills/intake/references/batch.md`, `intake/SKILL.md` | B1 |
| `analyst/skills/elicit/SKILL.md`, `elicit/dispatcher/explorer.md` | K1 |
| `flow/analyst.md`, `README.md`, `MIGRATION_*`, `plugin.json` ×3 | R1 |
| `tests/analyst/test_ticket_38.py` (baru), `tests/test_a1_ticket_source.py`, `tests/test_smoke.py` | semua |

## Tahapan

1. N1 — sidik tahan format (analyst + salinan backend/frontend).
2. N2 — `reseal`.
3. V1 — ticketdir dari cwd.
4. B1 — ekor batch.
5. K1 — temuan sesi.
6. R1 — dokumen, migrasi, rilis.

## Verifikasi ujung ke ujung

- `uvx pytest` penuh dan `python3 scripts/lint_plugins.py --base origin/main` 0 FAIL.
- Uji nyata: prettier atas salinan seluruh tiket hkm sesudah `reseal` — semua READY tetap READY.
- Sesudah 0.20.0 terpasang di hkm: `ticket.py reseal --all` per repo; 6 tiket DRIFT `wms-svelte` disetujui ulang;
  validator "Letak ticketdir" FAIL mendekati nol; tiket batch ber-log 0 tidak bertambah tanpa keputusan user.

## Trade-off yang diterima

- N1: perubahan murni format (spasi, padding tabel, `*` ↔ `_`, baris kosong) tidak lagi memicu DRIFT — disengaja.
  Indentasi daftar bersarang ikut dinormalkan; suntingan yang hanya memindah tingkat butir tidak terdeteksi.
- N2: tiket yang sudah DRIFT karena format tetap butuh persetujuan ulang.
- K1: hemat realistis ≤ 0,2 jt per tiket dan hanya bila temuan sesi mencakup konsepnya; bagian terbesar selisih
  (konteks yang terbawa) tidak disentuh.

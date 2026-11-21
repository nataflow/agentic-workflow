# Langkah 40 — `backend:ticket`: tiket teknis cepat berbukti kode, lokal tanpa commit, tercermin ke nataflow (T1–T5)

Sumber: diskusi user (2026-11-21): tiket lewat `analyst:intake` terlalu umum untuk permintaan teknis kecil yang sudah
jelas, mis. "tambah field username di response API get user", sementara elisitasinya berat (acuan lapangan hkm 16 Nov:
1,93M token, 7,8 pertanyaan, median 38 menit per tiket READY). Basis kode: commit `9567257` (backend 0.23.3).

**Status (2026-11-21):** dikerjakan di branch `feat/40-tiket-cepat-backend`; backend 0.24.0. Test baru:
`tests/backend/test_40_tiket_cepat.py`. Belum: PR, uji lapangan, dan adaptasi `frontend:ticket`.

## Tujuan

Permintaan backend kecil yang sudah jelas menjadi tiket teknis spesifik dalam beberapa menit: kondisi sekarang
berbukti `path:baris`, perubahan, `AC-{n}`, dan dampak kontrak, dengan 0–1 pertanyaan dan satu persetujuan, siap
diserahkan ke `backend:tech-lead` sebagai `ticket_source` di sesi lain.

## Keputusan

- **T1 — skill terpisah `backend:ticket`**, bukan lane `tech-lead`: tiket tidak butuh branch, baseline build, atau
  taskdir. Tanpa subagent (explorer maupun reviewer): main loop menelusuri sendiri dengan jatah 3 kali baca; letak
  yang tidak ketemu berarti permintaan bukan tiket cepat → `backend:tech-lead`. Gerbang SessionStart mengecualikan
  `/backend:ticket` dan permintaan "buatkan tiket …".
- **T2 — lokal, tidak di-commit** (keputusan user). `backenddev/tickets/<YYMMDDhhmm>-<slug>/TICKET.md`; `ticket.py new`
  menulis penanda `backenddev/tickets/.gitignore` (`*`). Tidak ada subperintah yang menjalankan git commit.
- **T3 — tercermin ke nataflow** (keputusan user). `ticket.py sync --push` sesudah `approve` (dan sesudah `cancel` atas
  tiket yang pernah READY) membuat/memperbarui task beridentitas `{"source":"backenddev","ticket_key":"<ticketdir>"}`
  lewat primitif `nataflow_sync.py` yang sudah ada (berkas lima salinan itu tidak diubah). `sync_payload.ticket_key`
  menurunkan identitas yang sama dari `ticket_source` taskdir, sehingga workdir menempel ke task tiket dan task
  ditutup `done` lewat siblings seperti task tiket analyst.
- **T4 — serah terima memakai kontrak tiket analyst.** Segel `ticket_seal`/`ticket_seal_norm` yang sudah ada di
  `precondition_lib.py`, baris kanonik `- **AC-{n}**:` (→ `TAC-{n}` di `TASK.md`). `ticket_source_verdict` menerima
  path `backenddev/tickets/…`: wajib `status: READY` dan segel cocok, tanpa `elicitation` dan tanpa fallback subjek
  commit. Path analyst tidak berubah perilakunya. Frontend tidak diubah.
- **T5 — tiket tidak menulis risk.** Risk tetap Keputusan 2 `tech-lead` dari kode; tiket menulis fakta
  `## Dampak Kontrak` (`aditif` | `mengubah` | `menghapus` | `tidak ada`). Penjaga ukuran: AC paling banyak 5.
- Ditunda (keputusan user): `frontend:ticket` (menunggu backend matang beberapa iterasi) dan rute dari
  `analyst:intake`. Lintas repo cukup catatan di `## Dampak Kontrak`, tanpa tiket kedua.

## Temuan dicatat, tidak diubah

- **F1 — tiket kecil, eksekusi tetap berat.** Tabel Keputusan 2 (`tech-lead/references/decisions.md` §7) menggolongkan
  perubahan "endpoint/DTO eksisting" `BREAKING` dan "field opsional baru" `MAJOR`; prinsip eskalasi memilih yang lebih
  tinggi. Tiket "tambah field di response" karenanya cenderung menerbitkan `PRD.md` saat dikerjakan. Diputuskan
  terpisah sesudah uji lapangan (keputusan user).

## Trade-off yang diterima

- `ticket_key` tanpa nama repo (pola analyst): dua repo backend dengan tiket bermenit dan ber-slug sama bertabrakan di
  nataflow; skrip berhenti `FAIL` "task kembar" sebelum tool tulis apa pun.
- Tiket hanya hidup di disk satu mesin plus cermin nataflow (yang tidak dibaca balik).

## Blast radius

Baru: `skills/ticket/` (`SKILL.md`, `scripts/ticket.py`, `scripts/check_preconditions.py`,
`templates/ticket-template.md`). Diubah: `skills/_common/precondition_lib.py` (`BE_TICKET_PATH_RE`,
`ticket_source_verdict`), `skills/_common/sync_payload.py` (`ticket_key`), `hooks/gate_text.py`, `tech-lead/SKILL.md`,
`tech-lead/references/gate-scope.md` B-2, `tech-lead/references/nataflow-sync.md`, `README.md`, `flow/backend.md`,
`CLAUDE.md`, `tests/test_smoke.py`, `tests/hooks/test_gate_text.py`.

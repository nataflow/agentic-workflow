---
name: ticket
description: Gunakan ketika user meminta tiket teknis backend untuk dicatat lalu dikerjakan nanti atau oleh orang lain ("buatkan tiket …", "tiketkan …", /backend:ticket) dan permintaannya kecil serta sudah jelas, mis. tambah field di response API, ubah pesan validasi, tambah filter query - kartu pendek berbukti path:baris (kondisi sekarang, perubahan, AC, dampak kontrak) disetujui sekali, disimpan lokal tanpa commit, dan dicerminkan ke nataflow, sebelum dikerjakan lewat backend:tech-lead dengan ticket_source; bukan untuk mengerjakan langsung, diagnosis bug, atau permintaan bisnis yang butuh elisitasi (analyst:intake)
argument-hint: "<permintaan teknis singkat>"
---

## THE IRON LAW

- Tiket mencatat **apa yang berubah dan buktinya di kode sekarang**, bukan cara mengerjakannya: tanpa langkah
  implementasi, tanpa risk level (wewenang Keputusan 2 `backend:tech-lead`), tanpa estimasi.
- Tiap fakta di `## Kondisi Sekarang` membawa bukti `path:baris` yang benar-benar dibaca di giliran ini.
- Dilarang mengedit kode, membuat branch, menjalankan build/test, atau menjalankan `git commit` — tiket tidak pernah
  di-commit. Dilarang men-dispatch subagent.
- Status `READY` hanya lewat `ticket.py approve` sesudah jawaban eksplisit user; dilarang menyunting tiket READY.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ticket/scripts/check_preconditions.py`.
2. `PASS` (5/5) → Fase 1. `FAIL` → berhenti dan jalankan tindakan butir yang gagal: bukan repo git → jalankan dari
   dalam repo backend; profil → `backend:profile` lalu ulangi; tiket ter-track → tanyakan user sebelum
   `git rm -r --cached`, jangan jalankan sendiri.

## Parameter [REQUIRED]

- `request` — string — wajib — permintaan user apa adanya, disalin utuh ke `--request`.

## Workflow

Tiap `ticket.py <sub>` di bawah berarti `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ticket/scripts/ticket.py <sub>`.

### Fase 1 — Pahami & Cek Kembar

1. Rumuskan satu kalimat perubahan, slug kebab-case (≤ 48 karakter), dan judul H1 spesifik (sebut endpoint, simbol,
   atau layar yang berubah).
2. Jalankan `ticket.py state`. Tiket terbuka ber-slug atau ber-judul serupa → tanyakan user: lanjutkan tiket itu
   (`reopen` bila READY) atau buat baru.

### Fase 2 — Telusur Ringan

1. Baca `.claude/profile/backenddev/surface-map.md` dan `domain-map.md` untuk menemukan letak permukaan.
2. Buktikan dari kode dengan jatah **3 kali baca berkas kode** (pencarian nama simbol tidak dihitung): handler/route,
   DTO/response, dan service/query yang disentuh. Catat `path:baris` tiap fakta.

### Fase 3 — Penjaga Ukuran

Hentikan tiket cepat dan arahkan ke jalur lain bila salah satu benar:

- letak permukaan belum terbukti dalam jatah Fase 2 → `backend:tech-lead`;
- permintaan memuat lebih dari satu perubahan yang tidak saling bergantung → pecah jadi beberapa tiket (tanyakan
  user) atau `backend:tech-lead`;
- butuh keputusan bisnis yang tidak terjawab dengan satu pertanyaan → `analyst:intake`;
- gejala bug yang penyebabnya belum diketahui → `backend:debug`;
- butuh lebih dari 5 AC.

### Fase 4 — Satu Pertanyaan

Ambiguitas yang mengubah isi kartu (mis. `GET /users/{id}` atau `GET /me`, field wajib atau opsional) → paling
banyak **satu** `AskUserQuestion`, opsi berasal dari temuan kode. Selain itu jangan bertanya.

### Fase 5 — Tulis Kartu

1. `ticket.py new --slug <slug> --title "<judul>" --request -` dengan permintaan asli user lewat stdin.
2. Isi kelima seksi `TICKET.md` di path keluaran `new`, ganti seluruh placeholder `<isi: …>`:
   - `## Kondisi Sekarang` — butir fakta berbukti `` `path:baris` `` atau `` `path:awal-akhir` `` relatif root repo.
   - `## Perubahan` — keadaan target per butir, menyebut simbol dan berkas sasaran.
   - `## Acceptance Criteria` — `- **AC-{n}**: …` berurutan dari 1, paling banyak 5, masing-masing bisa diverifikasi
     dari luar (response, status, data tersimpan, pesan galat).
   - `## Dampak Kontrak` — baris pertama diawali `aditif`, `mengubah`, `menghapus`, atau `tidak ada`, lalu siapa
     yang terdampak. Konsumen di repo lain (frontend, layanan lain) cukup dicatat di sini, tidak ditiketkan.
3. `ticket.py check --ticketdir <ticketdir>` sampai `CHECK PASS`.

### Fase 6 — Persetujuan [REQUIRED]

1. Tampilkan kartu (H1 sampai akhir `## Dampak Kontrak`) apa adanya.
2. `AskUserQuestion`: **Setujui (Recommended)** · **Revisi** · **Batal**.
   - Setujui → `ticket.py approve --ticketdir <ticketdir>`.
   - Revisi → sunting sesuai jawaban, `check` ulang, kembali ke butir 1.
   - Batal → `ticket.py cancel --ticketdir <ticketdir>`, tutup tanpa sinkron.

### Fase 7 — Cermin nataflow

Sesudah `approve` (atau `cancel` atas tiket yang pernah READY): `ticket.py sync --ticketdir <ticketdir> --push`.
`PILIH_WORKSPACE` → tanyakan alias ke user, jalankan ulang dengan `--workspace <alias>`. `dilewati` (tanpa
`.claude/nataflow.json`) bukan kegagalan. Isi tiket tidak dibaca ulang ke konteks.

## Guardrails

- Kartu memakai istilah kode apa adanya (nama endpoint, struct, kolom) dalam backtick; tanpa prosa pengantar.
- `## Permintaan` tulisan `new`; jangan diubah.
- Tiket READY yang perlu diubah → `ticket.py reopen --ticketdir <ticketdir>`, sunting, `check`, lalu Fase 6.
- Taskdir yang sudah memakai tiket akan gagal prasyarat `task` check 7 setelah tiket dibuka ulang, sampai tiket
  disetujui lagi; sebutkan ini ke user sebelum `reopen`.

## Output [REQUIRED]

Tutup dengan tepat satu baris, lalu satu baris serah terima:

```
### TICKET — READY · <ticketdir>/TICKET.md · segel <segel> · nataflow <segmen sync>
Kerjakan nanti: /backend:tech-lead dengan ticket_source <ticketdir>/TICKET.md
```

Selain READY: `### TICKET — <DIBATALKAN | DIALIHKAN ke <skill>: <alasan satu kalimat>>`.

## Failure path

- `new` FAIL slug kembar → kembali ke Fase 1 butir 2.
- `check` FAIL bukti `path:baris` tidak ada atau melewati panjang berkas → baca ulang berkasnya (masih dalam jatah
  Fase 2) dan betulkan barisnya; jangan menebak nomor baris.
- `sync` GAGAL → tiket tetap READY di disk; laporkan segmennya dan sarankan `sync --push` ulang sesudah config atau
  MCP key dibenahi.

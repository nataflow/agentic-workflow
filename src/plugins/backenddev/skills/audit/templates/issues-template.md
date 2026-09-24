# `audit` report template

Dipakai di Fase 4 (`SKILL.md`) sebagai isi file `backenddev/issues/{yyyy-mm-dd}-{NNN}-issues.md`, dan di Fase 5 sebagai bentuk laporan chat. Ikuti struktur ini persis — nama field, urutan seksi, dan ID temuan adalah kontrak yang dibaca seleksi batch `plan`. Jangan mengganti nama field, jangan menambah field baru. Satu-satunya tambahan yang diizinkan pada file yang sudah ditulis adalah baris `> Status:` di bawah judul temuan, dan itu pun ditulis `code-implementor`.

Definisi severity dan gate verifikasi di bawah adalah **sumber tunggal** untuk `backenddev:audit`. Subagent `code-reviewer` menulis laporannya dengan kontraknya sendiri dan memegang tangga severity serta gerbang bukti yang setara di `agents/code-reviewer.md`; perubahan di sini wajib menyentuh berkas itu juga.

## Severity definitions (single source — do not copy elsewhere)

- **P1** — merusak data/uang/keamanan, atau menghasilkan output salah pada jalur utama.
- **P2** — bug nyata pada jalur sempit, atau utang performa yang terukur dampaknya.
- **P3** — konsistensi, kebersihan, keterbacaan.

Temuan `PLAUSIBLE` tetap masuk ke severity sesuai dampak yang diperkirakan — bukan severity terpisah — dengan label `PLAUSIBLE` pada judulnya.

## Report structure

```markdown
---
target: <path module/package, atau "diff: <path file yang berubah>">
dimensions: <daftar token dimensi yang disweep>
---

# Audit: <target path> — <yyyy-mm-dd>

## Summary
<2-3 kalimat: kondisi umum + jumlah temuan per severity>

## P1 — Blocker
### [P1-1] <finding title> — CONFIRMED
- Lokasi: `path/ke/Berkas:123`
- Dimension: <security | transaction | data | persistence | concurrency | architecture>
- Masalah: <penjelasan defect>
- Skenario gagal: <input/kondisi konkret → hasil salah>
- Saran: <arah perbaikan singkat>

## P2 — Should fix
<format sama>

## P3 — Nice to have
<format sama>

## Out of scope
<temuan jelas di module lain yang terlihat saat trace — dicatat, tidak diperdalam>

## Verification notes
<kandidat yang dibuang dan alasannya — supaya tidak dicari ulang>
```

Nilai kolom `Dimension` wajib salah satu dari enam token itu persis, bukan judul panjang reference-nya.

Seksi kosong tetap ditulis, isinya `Tidak ada.` — jangan menghapus judul seksi hanya karena tidak ada temuan di severity itu.

ID temuan berformat `P{severity}-{n}` per severity per laporan (`P1-1`, `P1-2`, `P2-1`). `{n}` mulai dari 1 di tiap severity, tidak berlanjut lintas severity.

## Marking finding status — a read contract, not this skill's job

Temuan **tidak pernah dihapus** dari file laporannya, termasuk setelah diperbaiki atau setelah diputuskan tidak dikerjakan. Yang menyisipkan baris status adalah `code-implementor` — satu-satunya yang boleh menulis baris `> Status:` di `issues/` — setelah temuan selesai diproses lewat brief, bukan `audit` saat sweep. Aturan penandaan yang sama berlaku di rumah temuan yang satu lagi, `{taskdir}/REVIEW.md`; daftar penuh lokasi yang boleh disentuh implementor ada di `../../../agents/code-implementor.md`. Bentuknya satu baris tepat di bawah judul temuan:

```markdown
### [P1-1] <finding title> — CONFIRMED
> Status: <STATUS> <yyyy-mm-dd> — lihat <file brief>
- Lokasi: `path/ke/Berkas:123`
...
```

Nilai `Status` yang sah di plugin ini persis lima: `PLANNED`, `FIXED`, `DEFERRED`, `DROPPED`, `OBSOLETE` (definisinya di `../../plan/templates/brief-template.md`). Yang pernah **ditandai di file laporan ini** hanya empat: `PLANNED` tidak pernah ditulis di sini karena artinya temuan masih menunggu eksekusi di brief.

`DEFERRED` satu-satunya status tertulis yang **tetap pekerjaan terbuka**: temuannya nyata dan diterima, hanya ditunda ke batch/rilis lain. Karena itu ia tetap boleh terpilih ulang seleksi batch `plan` di batch berikutnya — beda dari `FIXED`/`DROPPED`/`OBSOLETE` yang dikeluarkan permanen dari seleksi batch.

Penandaan berlaku untuk **semua** status tertulis di atas, bukan hanya `FIXED`. Temuan yang selesai sebagai `OBSOLETE`/`DROPPED` tapi dibiarkan tanpa baris status akan terpilih ulang di batch berikutnya, di-scan ulang, lalu di-drop ulang — persis kerja sia-sia yang index ini ada untuk mencegah.

Status yang sama dicerminkan di kolom `Status` pada baris terkait di `README.md` — dua tempat, satu kebenaran, tidak ada penghapusan di kedua tempat.

## `issues/README.md` — index

Kolom persis: `Tanggal`, `File`, `Target`, `P1`, `P2`, `P3`, `Status`. Satu baris per laporan temuan yang pernah ditulis — dari sweep ini, maupun dari subagent `code-reviewer` yang laporannya duduk di direktori pekerjaan. `README.md` sendiri **tidak** memakai penomoran `{NNN}` — satu-satunya file di folder `issues/` yang bernama tetap.

Contoh isi tabel:

```markdown
| Tanggal | File | Target | P1 | P2 | P3 | Status |
|---|---|---|---|---|---|---|
| 2026-08-14 | 2026-08-14-001-issues.md | module/sellorder | 2 | 3 | 1 | OPEN |
| 2026-08-14 | 2026-08-14-002-issues.md | diff: internal/order/service.go | 0 | 1 | 0 | OPEN |
| 2026-08-10 | 2026-08-10-001-issues.md | module/stock | 1 | 0 | 2 | P1-1 FIXED |
```

`Status` di baris index meringkas kondisi laporan itu (`OPEN`, atau daftar ID yang sudah punya status tertulis — mis. `P1-1 FIXED, P2-2 OBSOLETE`). Detail per temuan tetap hidup di file laporannya, bukan di README.

**Aturan menulis baris ini berlaku sama untuk `audit` dan `code-reviewer`** — keduanya menambah satu baris per laporan, dan keduanya membaca index yang sama untuk menemukan temuan lama. Dua hal yang wajib, dan keduanya sering terlewat:

- **`README.md` belum ada** (laporan pertama di repo ini) → buat dulu, dengan header tabel beserta baris pemisahnya persis seperti contoh di atas. Index ini bukan opsional: tanpa dia laporan berikutnya tidak punya cara menemukan temuan lama.
- **`Target` menyebut path, bukan label.** Index dicari lewat pencocokan **prefix path**, jadi `Target` yang cuma menyebut nomor task atau nama PR tidak akan pernah cocok — dan temuannya jadi tak terlihat persis seperti kalau tidak ditulis sama sekali.

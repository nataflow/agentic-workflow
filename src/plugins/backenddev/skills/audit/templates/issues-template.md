# `audit` report template

Dipakai di Fase 4 (`SKILL.md`) sebagai isi file `backenddev/issues/{yyyy-mm-dd}-{NNN}-issues.md`, dan di Fase 5 sebagai bentuk laporan chat. Ikuti struktur ini persis — nama field, urutan seksi, dan ID temuan adalah kontrak yang dibaca seleksi batch `plan`. Jangan mengganti nama field, jangan menambah field baru. Satu-satunya tambahan yang diizinkan pada file yang sudah ditulis adalah baris `> Status:` di bawah judul temuan, dan itu pun ditulis `code-implementor`.

Severity, format ID temuan, status temuan, dan skema index hidup di `../references/findings-contract.md`. Template ini hanya memuat struktur laporan.

## Report structure

```markdown
---
target: <path module/package; beberapa dipisah koma, tanpa label>
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

ID temuan, penandaan status (`> Status:`), dan baris index `backenddev/issues/README.md` mengikuti `../references/findings-contract.md` bagian 2–4.

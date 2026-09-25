# Kontrak Temuan backenddev — severity, ID, status, index

Rumah tunggal. Dipakai `backenddev:audit` (`backenddev/issues/*.md`), subagent `code-reviewer`
(`{taskdir}/REVIEW.md`, lewat slot `{findings_contract}`), dan `backenddev:architect` (temuan eksekusi
Fase 3 dan triase review Fase 4). Berkas lain merujuk ke sini dan dilarang menyalin definisinya.

## 1. Severity

| Severity | Label | Definisi | Selalu masuk sini |
|---|---|---|---|
| P1 | Blocker | Merusak data/uang/keamanan, atau output salah di jalur utama | Pelanggaran `## Invariants` profil; berkas kode di luar union `## File scope` (termasuk berkas yatim) atau simbol di luar `Anchor`; inkoherensi lintas-brief (rollback terselubung, migrasi bertentangan); skema berubah tanpa migrasi; mirrored path tertinggal |
| P2 | Should fix | Bug nyata di jalur sempit, atau utang performa yang terukur | N+1, kolom `WHERE`/`ORDER BY` tanpa index, batas hasil hilang; kecocokan baris `## Anti-patterns` profil (plafon P2, dilarang naik) |
| P3 | Nice to have | Konsistensi, kebersihan, keterbacaan | Penamaan, duplikasi, dead code terisolasi |

Kandidat tanpa bukti dibuang, tidak pernah diturunkan jadi P3. `PLAUSIBLE` adalah label bukti, bukan
severity: temuan `PLAUSIBLE` masuk severity sesuai dampak yang diperkirakan. Temuan anti-pattern wajib
mengutip **dua** bukti: `file:line` kode pelanggar dan baris profil yang dilanggar.

Konsekuensi di rantai: `P1` menahan penutupan taskdir dan kembali ke gerbang `backenddev:tech-lead`;
`P2`/`P3` dilaporkan tanpa menahan (`skills/architect/references/lifecycle-recovery.md` bagian 4).

## 2. ID temuan

`P{severity}-{n}` per laporan; `{n}` mulai 1 di tiap severity dan tidak berlanjut lintas severity
(`P1-1`, `P1-2`, `P2-1`). Dimensi (`security` … `architecture`) adalah field `Dimension`, bukan bagian
ID; bentuk ID berawalan kode dimensi tidak sah.

## 3. Status temuan

Temuan **tidak pernah dihapus** dari berkas laporannya, termasuk setelah diperbaiki atau setelah
diputuskan tidak dikerjakan. Yang menyisipkan baris status adalah `code-implementor` — satu-satunya
yang boleh menulis baris `> Status:` di `backenddev/issues/` dan `{taskdir}/REVIEW.md` — setelah temuan
selesai diproses lewat brief, bukan `audit` saat sweep dan bukan `code-reviewer`. Daftar penuh lokasi
yang boleh disentuh implementor ada di `agents/code-implementor.md`. Bentuknya satu baris tepat di
bawah judul temuan:

```markdown
### [P1-1] <finding title> — CONFIRMED
> Status: <STATUS> <yyyy-mm-dd> — lihat <file brief>
- Lokasi: `path/ke/Berkas:123`
...
```

Nilai `Status` yang sah persis lima: `PLANNED`, `FIXED`, `DEFERRED`, `DROPPED`, `OBSOLETE`
(definisinya di `skills/plan/templates/brief-template.md`). Yang pernah **ditandai di berkas laporan**
hanya empat: `PLANNED` tidak pernah ditulis di sana karena artinya temuan masih menunggu eksekusi di
brief.

`DEFERRED` satu-satunya status tertulis yang **tetap pekerjaan terbuka**: temuannya nyata dan
diterima, hanya ditunda ke batch/rilis lain. Karena itu ia boleh terpilih ulang seleksi gerbang di
batch berikutnya — beda dari `FIXED`/`DROPPED`/`OBSOLETE` yang dikeluarkan permanen
(`skills/tech-lead/references/gate-scope.md` bagian 6).

Penandaan berlaku untuk **semua** status tertulis di atas, bukan hanya `FIXED`. Temuan yang selesai
sebagai `OBSOLETE`/`DROPPED` tapi dibiarkan tanpa baris status akan terpilih ulang di batch
berikutnya, di-scan ulang, lalu di-drop ulang — persis kerja sia-sia yang index ini ada untuk mencegah.

Status yang sama dicerminkan di kolom `Status` baris terkait di index (bagian 4) — dua tempat, satu
kebenaran, tidak ada penghapusan di kedua tempat.

## 4. Index `backenddev/issues/README.md`

Berkas dibuka dengan judul `# Issues Index`, lalu header persis:

```markdown
| Tanggal | File | Target | P1 | P2 | P3 | Status |
|---|---|---|---|---|---|---|
| 2026-08-14 | backenddev/issues/2026-08-14-001-issues.md | internal/order | 2 | 3 | 1 | OPEN |
| 2026-08-18 | backenddev/docs/2608181430-order-split/REVIEW.md | internal/order, internal/stock | 0 | 1 | 0 | OPEN |
| 2026-08-10 | backenddev/issues/2026-08-10-001-issues.md | internal/stock | 1 | 0 | 2 | P1-1 FIXED |
```

- `Tanggal`: `yyyy-mm-dd`.
- `File`: path relatif root repo — `backenddev/issues/<yyyy-mm-dd>-<NNN>-issues.md` atau
  `backenddev/docs/<YYMMDDhhmm>-<slug>/REVIEW.md`.
- `Target`: path modul/berkas, dipisah koma bila lebih dari satu, **tanpa** label (awalan `diff`, nomor task,
  nama PR dilarang). Index dicari lewat pencocokan **prefix path**; target berlabel tidak pernah cocok.
  Untuk `REVIEW.md`: folder dari union `## File scope` brief.
- `P1`/`P2`/`P3`: jumlah temuan per severity.
- `Status`: `OPEN`, atau daftar `<ID> <STATUS>` dipisah koma (`P1-1 FIXED, P2-2 OBSOLETE`). Detail per
  temuan tetap hidup di berkas laporannya.
- Satu baris per laporan (audit maupun `REVIEW.md`). Baris lama tidak pernah dihapus. `README.md`
  sendiri tidak memakai penomoran `{NNN}`.

**`README.md` belum ada** (laporan pertama di repo) → buat dengan judul dan header di atas beserta
baris pemisahnya. Index ini bukan opsional: tanpanya laporan berikutnya tidak punya cara menemukan
temuan lama.

**Migrasi skema lama.** Index yang sudah memakai header lain (skema lima kolom versi lama) dipertahankan
apa adanya: jangan menulis ulang header maupun baris lamanya.
Tambahkan tabel baru berheader bagian ini di bawahnya, lalu baris baru hanya masuk ke tabel baru.
Header yang tak terbaca sama sekali bukan alasan menghapus riwayat — tambahkan tabel baru di bawahnya.

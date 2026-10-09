# product

Plugin untuk **inisiasi**: gagasan produk baru, fitur baru di aplikasi yang sudah ada, atau improvement fitur yang
sudah berjalan, diubah menjadi satu dokumen `CHARTER.md` berisi enam pilar:

| Pilar | Isi |
|---|---|
| Purpose | tujuan aplikasi dan masalah yang diselesaikan |
| Actors | pihak yang terlibat dan perannya |
| Business Process | alur utama dari awal sampai selesai |
| Business Rules | aturan dan pengecualian |
| Success Criteria | indikator bahwa solusi sudah benar |
| Scope | batasan pekerjaan untuk versi pertama |

Charter disusun dari elisitasi terarah, dinilai subagent `charter-reviewer`, dan dikunci persetujuan user. Setelah
`APPROVED`, butir Scope `S<n>` siap dipecah menjadi tiket.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install product@nataflow
```

Prasyarat: `python3` ≥ 3.9. `git` opsional: tanpa git, artefak tetap ditulis dan hanya commit yang dilewati.

## Tiga Mode

| Mode | Ruang kerja | Ciri charter |
|---|---|---|
| `NEW_PRODUCT` | folder kosong (tanpa kode) | seluruh fakta dari peminta; rujukan kode dilarang |
| `NEW_FEATURE` | codebase | aktor bertanda `[ADA]`/`[BARU]` dari peta peran yang sudah ada |
| `IMPROVEMENT` | codebase | Business Process dibagi `Kondisi Sekarang` (berbukti `path:baris`) dan `Kondisi Target`; tiap aturan bertanda `[TETAP]`/`[UBAH]`/`[BARU]` |

Ruang kerja dideteksi skrip: manifest di root (`package.json`, `go.mod`, …) atau minimal satu berkas sumber berarti
`CODEBASE`. Folder kosong selalu `NEW_PRODUCT`; mode codebase di folder kosong ditolak, dan `NEW_PRODUCT` di codebase
butuh konfirmasi user. Di codebase, pilihan `NEW_FEATURE` atau `IMPROVEMENT` diverifikasi `code-scout` sebelum
folder dibuat.

## Tiga Skill, Dua Subagent

| Komponen | Jenis | Peran |
|---|---|---|
| `product:init` | skill, titik masuk (`/product:init`) | deteksi ruang kerja, mode, guard konteks minimum, verifikasi mode, cek duplikat, slug |
| `product:discover` | skill internal | alokasi `CHARTER.md`, elisitasi enam pilar per mode, konfirmasi fakta, tutup catatan |
| `product:spec` | skill internal | kartu enam pilar, review independen, persetujuan, perubahan, pembatalan |
| `product:code-scout` | subagent read-only | `CEK_FITUR` (fitur sudah ada?) dan `PETA` (peta Actors, Business Process, atau Business Rules sekarang berbukti `path:baris`) — mode codebase saja |
| `product:charter-reviewer` | subagent read-only | vonis PASS/BLOCKED kartu terhadap Konteks Awal dan catatan elisitasi |

## Guard Permintaan yang Terlalu Umum

"Saya ingin membuat aplikasi keuangan" baru menyebut domain. Sebelum folder dibuat, `product:init` menuntut tiga
butir konteks minimum per mode, ditanyakan dengan opsi konkret (keuangan pribadi / UMKM / perusahaan …):

| Mode | `--untuk` | `--masalah` | `--lingkup` |
|---|---|---|---|
| `NEW_PRODUCT` | Untuk siapa | Masalah utama | Domain |
| `NEW_FEATURE` | Pengguna | Yang belum bisa dilakukan | Area |
| `IMPROVEMENT` | Yang terdampak | Yang salah atau kurang | Fitur |

`charter.py guard` (dan `charter.py new`) menolak butir kosong, terlalu pendek, berupa placeholder, atau utuhnya
kata yang tidak mempersempit apa pun (*semua*, *terserah*, *umum*, dan untuk `NEW_PRODUCT` juga *pengguna*,
*pelanggan*). Butir yang kosong tidak pernah diisi tebakan: dua putaran tanpa jawaban berakhir di `INIT — TERTAHAN`.
Ketiga butir ditulis ke `### Konteks Awal` dan dimateraikan `context_hash`; reviewer memeriksa Purpose dan Actors
konsisten dengannya. Rincian: `skills/init/references/konteks-minimum.md`.

## Workflow

```
/product:init
  check_preconditions.py → charter.py state → wilayah → mode → guard → (codebase) scout CEK_FITUR → duplikat → slug
        ↓
product:discover
  charter.py new → (codebase) scout PETA → giliran tanya-jawab ≤ 3 pertanyaan → konfirmasi fakta → charter.py close
        ↓
product:spec
  kartu enam pilar → validate_doc.py --kind charter → charter-reviewer → charter.py review → commit draft
  → AskUserQuestion → charter.py approve → APPROVED
```

## Artefak

`product/<slug>/CHARTER.md` di root worktree git, atau di folder kerja bila bukan repo git:

- frontmatter (`status`, `mode`, sidik, pembukuan review dan persetujuan) — hanya ditulis `charter.py`;
- H1 judul, lalu enam H2 pilar (kartu, ditulis `product:spec`);
- `## Catatan Elisitasi` sebagai H2 terakhir: Konteks Awal, Permintaan Asli, Fakta per pilar, Log Tanya-Jawab,
  Pertanyaan Terbuka (ditulis `product:discover`).

`product/<slug>/review.md` menyimpan blok `## Charter Review` terakhir.

| Keadaan (`charter.py state`) | Arti | Rute |
|---|---|---|
| `ELICITATION` | catatan terbuka | `product:discover` |
| `DRAFT` | catatan tersegel; kartu belum ada atau belum lolos review atas isinya sekarang | `product:spec` |
| `REVIEW` | kartu lolos reviewer atas sidik sekarang | keputusan user |
| `APPROVED` | disetujui; isi sama dengan yang dimateraikan | selesai |
| `DRIFT` | `APPROVED` disunting sesudah disetujui | reopen atau pulihkan |
| `CANCELLED`, `EMPTY`, `BROKEN` | dibatalkan, sisa alokasi gagal, rusak | — |

Subdirektori `product/` yang bukan charter (mis. paket kode bernama `product`) diabaikan pemindaian.

## Penegakan Mekanis

- `charter.py new` menjalankan ulang guard konteks minimum dan kecocokan mode dengan ruang kerja, lalu memateraikan
  Konteks Awal dan Permintaan Asli.
- `charter.py close` hanya menutup catatan yang lolos `validate_doc.py --kind notes` dalam keadaan tertutup: enam
  pilar terjawab, tanpa `Asumsi:`, tanpa pertanyaan memblokir. Catatan disegel `elicit_hash`; suntingan sesudahnya
  ditolak `check`, `review`, dan `approve`.
- `validate_doc.py --kind charter` menagih bentuk enam pilar per mode: aktor alur terdaftar, `BR-n` berpengecualian,
  `SC-n` berangka, `S<n>` unik berurutan, tanda per mode, dan bukti `path:baris` yang benar-benar ada di repo.
- `charter.py review` mengikat vonis reviewer ke sidik `<kartu>/<catatan>` yang dinilainya (plafon 2 ronde per
  revisi, 3 revisi per basis fakta); `approve` menuntut vonis `PASS` atas sidik sekarang dan jawaban eksplisit user.
- `charter.py reopen --to elicitation` menulis sendiri baris log `Dibuka ulang`; `--to draft` untuk perubahan
  redaksional charter `APPROVED`.

## Git

Commit hanya lewat `charter.py`, dengan staging path eksplisit: `docs(product): elisitasi <slug>`,
`docs(product): draft CHARTER <slug>`, `docs(product): kunci CHARTER <slug> APPROVED`,
`docs(product): batalkan CHARTER <slug>`. Exit 3 berarti isi tertulis tetapi commit gagal (hook, gpg); skrip mencetak
perintah commit manualnya. Tanpa git, atau `product/` diabaikan `.gitignore`, commit dilewati.

## Serah Terima (disiapkan, belum aktif)

Charter `APPROVED` belum dipecah otomatis menjadi tiket. Yang sudah disiapkan adalah format: tiap butir
`### Termasuk` berID tetap `S1`, `S2`, … yang tidak boleh dinomori ulang, sehingga pemetaan `S<n>` → tiket kelak
tidak mengubah charter yang sudah disetujui. Sampai serah-terima aktif, bawa butir Scope satu per satu ke
`/analyst:intake`.

## Batas Dengan Plugin Lain

- **analyst**: `product` menulis arah satu inisiatif; `analyst` menulis tiket satu tujuan. Permintaan kecil berbatas
  jelas dialihkan `product:init` ke `analyst:intake`.
- **backend / frontend**: teks gerbang SessionStart keduanya mengecualikan permintaan `/product:*`, jadi inisiasi
  fitur di repo backend atau frontend tidak dicegat gerbang engineer.
- **nataflow**: sinkron charter ke server nataflow belum ada.

## Sengaja Belum Ada

- Pemecahan Scope menjadi tiket `analyst` secara otomatis.
- Sinkron charter ke nataflow.
- Riset pasar atau pesaing lewat web: Purpose dan Actors harus datang dari peminta, bukan dari hasil penelusuran.

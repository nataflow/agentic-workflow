# Langkah 22 — `fullstack`: kecualikan proyek atau repo lewat `.fullstack/abaikan` (A1–A4, D1)

Sumber: permintaan user 2026-10-13 ("saya ingin ada fitur untuk exclude directory tertentu juga") dan pilihan user
di sesi yang sama: hanya tingkat proyek/repo, bukan folder di dalam repo. Basis kode plugin: commit `2720eb5`
(fullstack 0.1.0, branch Langkah 21).

**Status (2026-10-13):** A1–A4 dan D1 selesai. Test regresi di `tests/fullstack/test_abaikan_22.py` (19), ditambah
satu kasus smoke `abaikan list`. Suite penuh hijau (2470), subset fullstack/smoke hijau di Python 3.9, lint 0 FAIL,
dan `claude plugin validate .` lolos. Versi: fullstack 0.2.0.

Selisih pelaksanaan terhadap Kontrak di bawah:

- **K4, `/` di awal pola.** Diperlakukan seperti `.gitignore` (berjangkar di root) lalu dibuang, bukan ditolak sebagai
  path absolut. Yang ditolak: pola berawalan `~`, huruf drive Windows, `\`, segmen kosong/`.`/`..`, dan pola lebih
  dari dua tingkat (tidak mungkin mengena root `<proyek>/<repo>`).
- **`dikecualikan`** berisi `{dir, jenis, pola}` dengan `jenis` = `repo` atau `proyek`; butir `proyek` membawa `repo`
  (jumlah repo di dalamnya) dan hanya dicatat bila folder itu memang berisi repo.
- **`abaikan hapus`** menghapus baris berpola itu dan mempertahankan komentar serta baris lain apa adanya.
- **Pesan bersama** `bukan_di_root()` di `fullstack_lib.py` dipakai `check`, `new`, dan `layanan set`; pesan untuk
  repo yang memang tidak ada kini berbunyi "repo `<dir>` tidak ada di root".
- **Deskripsi skill** menyebut pengecualian supaya model mengenali permintaan "abaikan repo X".

## Tujuan

1. User bisa mengecualikan proyek atau repo dari root, misalnya `legacy-erp`, `wms/api-lama`, atau semua repo
   `infra`, sehingga repo itu tidak di-scan, tidak masuk `PETA.md`, tidak bisa di-scout, dan tidak dihitung plafon 60
   repo.
2. Pengecualian tidak pernah diam-diam: `PETA.md` dan keluaran `scan` menyebut apa yang dikecualikan dan oleh pola
   mana.
3. Semua skrip (`scan`, `peta`, `new`, `seam`, `check`, `layanan`, prasyarat) membaca sumber yang sama, sehingga satu
   explore tidak pernah melihat dua daftar repo yang berbeda.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Berkas `<root>/.fullstack/abaikan`, bukan flag CLI.** | Skill memanggil lima skrip berkali-kali dalam satu explore; flag yang lupa dibawa di satu panggilan membuat `check` menolak laporan yang dibuat `new`. |
| K2 | **Format gaya `.gitignore`**: satu pola per baris, `#` komentar, baris kosong dilewati, `/` di awal dan akhir dibuang. Pola tanpa `/` dicocokkan dengan **nama** proyek atau repo di tingkat mana pun (`api-lama` mengena `api-lama` dan `wms/api-lama`). Pola dengan `/` dicocokkan dengan **path relatif root** (`wms/api-lama`, `*/infra`). Glob memakai `fnmatch`. | Familiar bagi engineer; dua jenis pola cukup untuk dua tingkat root. |
| K3 | **Pola proyek menghentikan penurunan.** Folder proyek yang cocok tidak disisir sama sekali; seluruh repo di dalamnya tercatat dikecualikan. | Proyek warisan bisa berisi puluhan repo; menyisirnya hanya untuk dibuang membuang waktu `git` per repo. |
| K4 | **Pola tidak sah ditolak, bukan ditebak**: path absolut, segmen `..`, atau pola kosong sesudah dibersihkan. Baris tidak sah dilewati dan dilaporkan; berkas tak terbaca berarti tanpa pengecualian, dilaporkan sebagai peringatan. | Pengecualian yang gagal hanya membuat repo tampil kembali, tidak merusak apa pun; memblokir explore karenanya terlalu mahal. |
| K5 | **Dikelola lewat `workspace.py abaikan list/tambah/hapus`.** `tambah` memvalidasi pola dan menyebut repo yang terkena; pola yang tidak mengena apa pun tetap disimpan dengan peringatan (bisa untuk repo yang belum di-clone). Skill memakainya saat user berkata "abaikan repo X". | Validasi di satu tempat; berkas tetap boleh disunting tangan. |
| K6 | **Hook backend/frontend tidak membaca `abaikan`.** Gerbang root multi-repo (21 F1) tetap menyebut semua repo anak miliknya. | Berkas itu milik `fullstack`; hook plugin lain tidak bergantung pada artefak plugin lain. |

## Kontrak

### `.fullstack/abaikan`

```
# proyek / repo yang tidak dipetakan
legacy-erp
wms/api-lama
*/infra
```

### `scan`

- `find_repos` menerima pola. Proyek atau repo yang cocok tidak masuk `repo`, tidak dihitung plafon, dan dicatat di
  kunci baru `dikecualikan: [{dir, pola}]` (untuk proyek: `dir` = nama proyek, ditambah `repo` = jumlah repo di
  dalamnya bila folder itu dilewati utuh, dihitung tanpa membaca profil).
- Kunci baru `abaikan: {berkas, pola, galat}`.

### `workspace.py abaikan`

```
python3 workspace.py abaikan list  [--root <dir>] [--json]
python3 workspace.py abaikan tambah <pola> [--root <dir>] [--json]
python3 workspace.py abaikan hapus  <pola> [--root <dir>] [--json]
```

`tambah` menolak pola tidak sah (K4) dan pola yang sudah ada; `hapus` menolak pola yang tidak ada. Keluaran menyebut
proyek/repo yang terkena pola.

### `PETA.md`

Seksi baru `## Dikecualikan` sebelum `## Belum terpetakan`: tabel `| Proyek/Repo | Pola |`, atau `- Tidak ada.`.
Baris `Dibangun:` menyebut jumlah yang dikecualikan. Galat berkas atau baris tidak sah masuk `## Belum terpetakan`.

### Skrip lain

- `explore.py check`: rujukan, `repo`, atau `lingkup` ke repo/proyek yang dikecualikan ditolak dengan pesan
  "dikecualikan `.fullstack/abaikan` (pola `<pola>`)", bukan "tidak ada di root".
- `explore.py new` dan `layanan set`: menolak repo/proyek dikecualikan dengan pesan yang sama.
- Prasyarat: `Terselesaikan:` memuat `dikecualikan=<n>`; berkas tak terbaca atau baris tidak sah → check baru WARN.

## A1 [Tinggi] `scan` belum mengenal pengecualian
- [x] Selesai

`fullstack_lib.py`: `load_abaikan`, `cocok_abaikan`, `find_repos` berpola, `scan` dengan `dikecualikan` dan `abaikan`.
Test: pola nama di dua tingkat, pola path, glob `*/infra`, proyek dilewati utuh beserta hitungan repo, plafon tidak
menghitung yang dikecualikan, komentar dan baris kosong, pola tidak sah dilaporkan, berkas tak terbaca, tanpa berkas.

## A2 [Sedang] Belum ada cara aman mengelola pola
- [x] Selesai

`workspace.py abaikan list/tambah/hapus`. Test: tambah lalu list, tambah duplikat ditolak, pola tidak sah ditolak,
pola tanpa kecocokan disimpan dengan peringatan, hapus, hapus pola yang tidak ada, komentar di berkas dipertahankan.

## A3 [Sedang] Peta dan laporan tidak menyebut yang dikecualikan
- [x] Selesai

`PETA.md` seksi `## Dikecualikan`; pesan `check`, `new`, dan `layanan set`; prasyarat. Test per butir.

## A4 [Rendah] Skill belum tahu cara mengecualikan
- [x] Selesai

`SKILL.md`: perintah "abaikan/kecualikan repo X" → `abaikan tambah`, lalu `peta --write`; Precondition mencatat
`dikecualikan`. Smoke untuk `abaikan list`.

## D1 [Rendah] Dokumen dan versi
- [x] Selesai

README `fullstack`, `flow/fullstack.md`, `fullstack` 0.2.0.

## Di luar cakupan

- Mengecualikan folder di dalam repo dari penelusuran scout (pilihan user: tidak sekarang).
- Pola negasi `!` gaya `.gitignore`.
- Hook backend/frontend membaca `.fullstack/abaikan` (K6).

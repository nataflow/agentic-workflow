# Template Prompt Penelusur Repo — `repo-scout` untuk Explore `TELUSUR`

Pakai template ini saat `fullstack:explore` mendispatch subagent `repo-scout` pada jalur `TELUSUR`.

**Tujuan:** Mengumpulkan bukti `path:baris` permukaan dari satu repo, dipandu profil repo itu, tanpa membaca kode di
konteks utama. Hasilnya disusun konteks utama menjadi laporan `.fullstack/explore/<YYMMDDhhmm>-<slug>.md`.

**Dispatch setelah:** Phase 1 (panen, `PETA.md`, `layanan list`) selesai. Satu dispatch per repo per putaran, semua
repo satu putaran dikirim paralel dalam satu pesan.

````markdown
Telusuri satu repo secara permukaan untuk explore lintas repo fullstack.

- Root: `{root}`
- Repo: `{repo}`
- Peran: `{peran}`
- Pertanyaan:
{pertanyaan}
- Verifikasi endpoint: {verifikasi}
- Konteks panen: {panen}
- Larangan: read-only; hanya di dalam `{root}/{repo}/`; dilarang membuka `.env*`; berhenti di bukti pertama tiap
  butir; dilarang menelusuri rantai pemanggil atau menyarankan solusi; kuota 10 pemanggilan `Read`/`Grep`/`Glob`.
- Balikan: blok `## Repo Scout` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{root}` | Kunci `root` keluaran `workspace.py scan --json` | **[REQUIRED]** Path absolut |
| `{repo}` | Kunci `repo[].dir` keluaran `scan`; hanya repo berprofil `VALID` untuk `{peran}` | **[REQUIRED]** Path relatif root, mis. `wms/api` |
| `{peran}` | Kunci `profil[].peran` repo itu | **[REQUIRED]** `BE` atau `FE`. Repo berprofil ganda didispatch dua kali bila kedua perannya dibutuhkan |
| `{pertanyaan}` | Objective user dipecah per repo: domain, layar, entitas, endpoint, atau integrasi yang relevan bagi repo itu, memakai nama dari `PETA.md` | **[REQUIRED]** 1–5 butir bernomor `  - P1: …` |
| `{verifikasi}` | Putaran kedua saja: `METODE /path` dari tabel `Panggilan` repo lain yang target calonnya repo ini | **[OPTIONAL]** `-` bila kosong; hanya untuk `{peran}` = `BE` |
| `{panen}` | Fakta dari maksimal dua laporan `explore.py list` yang beririsan dan tidak `basi` | **[OPTIONAL]** `-` bila kosong; satu baris per fakta beserta `path:baris` aslinya |

### Aturan untuk Pendispatch

**Gerbang masuk**, kegagalan mana pun membatalkan dispatch repo itu:

- **Profil `VALID` untuk peran itu.** Repo `ABSENT`, `LEGACY`, `INVALID_JSON`, atau `TIDAK_SAH` tidak di-scout.
  Laporan mencatatnya di `## Repo` dan `## Arahan Lanjut`.
- **Plafon**: maksimal 4 repo per putaran, maksimal 2 putaran per explore. Putaran kedua hanya untuk `{verifikasi}`
  (repo BE penerima calon yang belum disisir di putaran pertama) dan butir `Belum disisir` beralasan "kuota habis".
  Dispatch ulang karena gagal atau balikan hilang dari percakapan tidak dihitung.
- **Lingkup**: hanya repo dari proyek di lingkup explore. Repo di luar lingkup baru masuk bila objective menyebutnya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

| Balikan subagent | Penanganan `fullstack:explore` |
| --- | --- |
| `Ditemukan` | Ditulis ke `## Temuan` di bawah `### <repo> (<peran>)` beserta rujukannya apa adanya |
| Baris `Base API` / `Prefix route` | Disalin apa adanya ke awal `### <repo> (<peran>)`. `seam` membaca baris `- Base API:` untuk prefix pemanggilan FE |
| `### Endpoint` | Tiap baris disalin ke `## Endpoint` dengan kolom `Repo` = `{repo}` di depan |
| `### Panggilan` | Tiap baris disalin ke `## Panggilan` dengan kolom `Pemanggil` = `{repo}` di depan |
| `Tidak ditemukan` | Ditulis ke `## Celah` → `### Tidak ditemukan`. Dilarang disimpulkan menjadi "fitur tidak ada" di `## Jawaban` |
| `Belum disisir` | Bahan putaran kedua bila plafon tersisa. Selain itu ditulis ke `## Celah` → `### Belum disisir`, dan `confidence` laporan maksimal `medium` |
| Payload kosong, tanpa blok `## Repo Scout`, atau error | Ulangi sekali (tidak dihitung plafon). Gagal lagi → repo itu masuk `### Belum disisir` dan `confidence` maksimal `medium` |

Balikan scout tidak disalin utuh ke laporan; yang mendarat hanya butir dan baris tabel di atas. Rujukan yang tidak
diawali `{repo}/` diperbaiki dengan menambah awalan itu sebelum ditulis, karena `explore.py check` menolak rujukan
tanpa awalan repo.

**Subagent mengembalikan:** blok `## Repo Scout` dengan `Profil`, `Pemanggilan`, `Base API` atau `Prefix route`,
lalu seksi `Ditemukan`, `Endpoint` (BE), `Panggilan`, `Tidak ditemukan`, dan `Belum disisir`.

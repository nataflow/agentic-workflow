# Template Prompt Penelusur Alur — `backend-explorer` / `frontend-explorer` untuk Explore `ALUR`

Pakai template ini saat `fullstack:explore` mendispatch subagent `backend-explorer` (repo `BE`) atau
`frontend-explorer` (repo `FE`) pada jalur `ALUR`.

**Tujuan:** Mengumpulkan alur berbukti `path:baris` di dalam satu repo, dipandu profil repo itu, tanpa membaca kode di
konteks utama. Hasilnya disusun konteks utama menjadi laporan `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` berjalur
`ALUR`.

**Dispatch setelah:** Bahan jalur `ALUR` (`PETA.md` dan panen `explore.py list`) selesai. Satu dispatch per repo per
peran, semua dispatch dikirim paralel dalam satu pesan.

````markdown
Telusuri alur di dalam satu repo untuk explore fullstack jalur ALUR.

- Root: `{root}`
- Repo: `{repo}`
- Objective: {objective}
- Kedalaman: `{kedalaman}`
- Batas cakupan: {batas}
- Konteks panen: {panen}
- Larangan: read-only; hanya di dalam `{root}/{repo}/`; dilarang membuka `.env*`; dilarang menyisir repo lain atau
  menyarankan solusi; kuota `ringkas` 20 dan `menyeluruh` 40 pemanggilan `Read`/`Grep`/`Glob`.
- Balikan: blok `## Alur Explorer` sesuai definisi agent-mu, tanpa teks lain.
````

Subagent yang dipanggil ditentukan `{peran}`: `BE` → `fullstack:backend-explorer`, `FE` →
`fullstack:frontend-explorer`. `{peran}` tidak ditulis di prompt karena tiap agent hanya melayani satu peran.

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{root}` | Kunci `root` keluaran `workspace.py scan --json` | **[REQUIRED]** Path absolut |
| `{repo}` | Kunci `repo[].dir` keluaran `scan`; hanya repo berprofil `VALID` untuk `{peran}` | **[REQUIRED]** Path relatif root, mis. `backend-a` |
| `{peran}` | Kunci `profil[].peran` repo itu | **[REQUIRED]** `BE` atau `FE`; memilih subagent. Repo berprofil ganda didispatch dua kali bila kedua perannya dibutuhkan |
| `{objective}` | Objective user dipersempit untuk repo itu, memakai nama domain, fitur, atau layar dari `PETA.md` | **[REQUIRED]** Satu pertanyaan alur bertarget konkret; bukan "pelajari repo" |
| `{kedalaman}` | `ringkas` secara default; `menyeluruh` hanya bila user meminta detail (cabang error, transaksi, "semua langkah") | **[REQUIRED]** Sama untuk semua dispatch satu explore, dan sama dengan `--kedalaman` laporan |
| `{batas}` | Path modul dari baris `domain-map.md` (BE) atau **Features Path** (FE) yang cocok, bila sudah jelas dari `PETA.md` | **[OPTIONAL]** `-` bila kosong; agent menurunkannya sendiri dari profil |
| `{panen}` | Fakta dari maksimal dua laporan `explore.py list` (jalur mana pun) yang beririsan dan tidak `basi` | **[OPTIONAL]** `-` bila kosong; satu baris per fakta beserta `path:baris` aslinya |

### Aturan untuk Pendispatch

**Gerbang masuk**, kegagalan mana pun membatalkan dispatch repo itu:

- **Profil `VALID` untuk peran itu.** Repo `ABSENT`, `LEGACY`, `INVALID_JSON`, atau `TIDAK_SAH` tidak didispatch;
  laporan mencatatnya di `## Arahan Lanjut`. `explore.py new --jalur ALUR` juga menolak repo seperti itu.
- **Plafon**: maksimal 4 dispatch per explore, satu putaran. Dispatch ulang karena gagal atau balikan hilang dari
  percakapan tidak dihitung, paling banyak sekali per repo.
- **Lingkup**: hanya repo yang disebut atau tersirat oleh objective. Repo lain yang dipanggil alur ini cukup dicatat
  dari baris `Permukaan`; jahitannya dikerjakan jalur `TELUSUR`.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

| Balikan subagent | Penanganan `fullstack:explore` |
| --- | --- |
| Baris `Entry` dan `### Alur` | Ditulis ke `## Alur` di bawah `### <repo> (<peran>)`: baris `- Entry: …` lebih dulu, lalu langkah bernomor apa adanya |
| `### Aturan Bisnis` | Tiap butir menjadi baris `## Aturan Bisnis` dengan kolom `Repo` = `{repo}` di depan dan rujukannya di kolom `Bukti` |
| `### Permukaan` | Tiap baris disalin ke `## Permukaan` dengan kolom `Repo` = `{repo}` di depan |
| `### Tidak ditemukan` | Ditulis ke `## Celah` → `### Tidak ditemukan`. Dilarang disimpulkan menjadi "fitur tidak ada" di `## Jawaban` |
| `### Belum disisir` | Ditulis ke `## Celah` → `### Belum disisir` beserta nama repo-nya, dan `confidence` laporan maksimal `medium` |
| Payload kosong, tanpa blok `## Alur Explorer`, atau error | Ulangi sekali (tidak dihitung plafon). Gagal lagi → repo itu masuk `### Belum disisir` dan `confidence` maksimal `medium` |

Balikan explorer tidak disalin utuh ke laporan; yang mendarat hanya langkah, butir, dan baris tabel di atas. Rujukan
yang tidak diawali `{repo}/` diperbaiki dengan menambah awalan itu sebelum ditulis, karena `explore.py check` menolak
rujukan tanpa awalan repo.

**Subagent mengembalikan:** blok `## Alur Explorer` dengan `Profil`, `Kedalaman`, `Pemanggilan`, `Entry`, lalu seksi
`Alur`, `Aturan Bisnis`, `Permukaan`, `Tidak ditemukan`, dan `Belum disisir`.

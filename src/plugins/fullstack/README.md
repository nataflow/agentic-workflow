# fullstack

Plugin untuk **memahami seluruh aplikasi dari satu root**: folder non-git yang menampung repo-repo aplikasi, baik
satu proyek maupun banyak proyek di satu perusahaan.

```
wms/                    company/
├── api/       (git)    ├── wms/
└── frontend/  (git)    │   ├── api/       (git)
                        │   └── frontend/  (git)
                        └── erp/
                            ├── api/       (git)
                            └── frontend/  (git)
```

Plugin ini read-only terhadap repo anak. Ia membaca profil yang sudah dibuat `backend:profile` dan `frontend:profile`
di tiap repo, lalu menjawab tiga jenis pertanyaan:

| Jalur | Pertanyaan | Cara | Hasil |
|---|---|---|---|
| `PETA` | "aplikasi apa saja", "stack tiap repo", "siapa memanggil siapa", "repo mana yang belum diprofilkan" | skrip membaca profil dan git, tanpa membaca kode | `.fullstack/PETA.md` |
| `TELUSUR` | satu layar, fitur, endpoint, entitas, atau integrasi: di mana, dan siapa memanggil siapa | subagent `repo-scout` per repo, dipandu profil | `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` |
| `ALUR` | bagaimana sesuatu bekerja di dalam satu repo atau lebih: langkah per layer, aturan bisnis, permukaan | subagent `backend-explorer` / `frontend-explorer` per repo, dipandu profil | `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` berjalur `ALUR` |

Kerja perubahan kode tidak dilakukan di sini. Laporan menutup dengan arahan `cd <repo>` lalu `backend:tech-lead`
atau `frontend:lead`.

## Instalasi

```
/plugin marketplace add <owner>/<repo>          # atau path lokal: ./path/ke/agentic-workflow
/plugin install fullstack@nataflow
```

Jalankan Claude Code dari root multi-repo, lalu tanya langsung atau panggil `/fullstack:explore`. Prasyarat:
`python3` ≥ 3.9 dan `git`. Repo aplikasi perlu sudah diprofilkan. Repo tanpa profil tetap tercatat di peta, tetapi
tidak ditelusuri.

## Satu Skill, Tiga Subagent

| Komponen | Peran |
|---|---|
| `fullstack:explore` | titik masuk; memilih jalur dan lingkup, membangun peta, mendispatch subagent, menyusun laporan |
| `fullstack:repo-scout` | subagent read-only (haiku, kuota 10 pemanggilan) yang menelusuri permukaan satu repo berprofil; mengembalikan bukti `path:baris`, tabel endpoint, dan tabel panggilan |
| `fullstack:backend-explorer` | subagent read-only (sonnet, kuota 20/40 pemanggilan) yang menelusuri alur di dalam satu repo backend: entry point, langkah per layer, aturan bisnis, batas transaksi, permukaan runtime |
| `fullstack:frontend-explorer` | subagent read-only (sonnet, kuota 20/40 pemanggilan) yang menelusuri alur di dalam satu repo frontend: route dan layar, komponen, hook/store, service HTTP, DTO, cache |

Kedua explorer diadaptasi dari `code-explorer` plugin `backend` dan `frontend`, tetapi berjalan dari root: profil
dibaca di `<root>/<repo>/`, tanpa `Write` dan tanpa laci taskdir, dan balikannya disusun skill menjadi laporan.
Semua pembacaan kode repo anak dari root lewat ketiga subagent ini, bukan subagent `Explore` bawaan.

## Peta Aplikasi

`workspace.py peta --write` menulis `.fullstack/PETA.md` dari profil saja:

- **Backend**: tabel domain dari `domain-map.md`, daftar permukaan runtime, dan baris `external:` (panggilan keluar)
  dari `surface-map.md`.
- **Frontend**: stack dan framework dari `index.json`, kutipan butir **Features Path** dan **Route Definitions** dari
  `structure.md`, dan nama permukaan dari `surface-map.md`.
- **Hubungan antar aplikasi**: frontend → backend untuk proyek yang punya tepat satu backend, dan pemetaan yang sudah
  dikonfirmasi di `layanan.json`. Panggilan keluar yang belum dipetakan tercantum sebagai "belum dipetakan".
- **Kesegaran profil**: jumlah commit yang menyentuh `source_root` sejak profil terakhir di-commit. Lebih dari 50
  commit, profil ditandai tertinggal dengan arahan REFRESH.
- **Belum terpetakan**: repo tanpa profil, profil rusak, atau baris profil di luar format, beserta arahannya.

## Alur

Jalur `ALUR` menjawab "bagaimana X bekerja": maksimal 4 explorer berjalan paralel dalam satu putaran, satu per repo
(atau per peran untuk repo berprofil ganda). Kedalaman `ringkas` secara default (satu alur utuh berbukti); `menyeluruh`
dipakai bila user meminta detail seperti cabang error atau transaksi. Laporan `ALUR` memuat `## Alur` (langkah
bernomor per repo), `## Aturan Bisnis`, dan `## Permukaan`, tanpa `## Jahitan`. Repo tanpa profil `VALID` ditolak
`explore.py new --jalur ALUR`. Alur yang memanggil repo lain berhenti di batas repo; penerimanya dicari lewat
`TELUSUR`, dan laporan kedua jalur saling memanen lewat `explore.py list`.

## Jahitan

Pada jalur `TELUSUR`, pemanggilan HTTP di frontend dan panggilan keluar backend dicatat sebagai **panggilan**, route
backend sebagai **endpoint**. `explore.py seam` mencocokkannya dan menulis tabel `## Jahitan`:

| Status | Arti |
|---|---|
| `COCOK` | target pasti, endpoint cocok ada di repo target |
| `TIDAK_ADA_DI_TARGET` | target pasti, endpoint cocok tidak ditemukan di yang disisir |
| `DUGAAN` | target belum pasti; path cocok dengan tepat satu calon repo |
| `AMBIGU` | target belum pasti; path cocok dengan lebih dari satu calon repo |
| `TAK_DIKENAL` | target belum pasti; tidak cocok dengan calon mana pun |
| `TAK_TERPANGGIL` | endpoint tanpa pemanggil dalam cakupan sisir (informasi, bukan cacat) |

Target dianggap pasti hanya bila (a) frontend memanggil di proyek yang punya tepat satu backend, atau (b) pemetaan
`<pemanggil> + <nama config>` → `<repo>` sudah dikonfirmasi user di `.fullstack/layanan.json`. Pemetaan dicatat lewat
nama config (mis. `WMS_API_URL`), bukan nilainya, karena scout dilarang membuka `.env*`.

```json
{
  "versi": 1,
  "peta": [
    {"pemanggil": "erp/api", "target": "WMS_API_URL", "repo": "wms/api", "prefix": "/api/v1"}
  ]
}
```

## Mengecualikan Proyek atau Repo

Repo warisan, infra, atau proyek yang memang tidak perlu dipahami bisa dikecualikan lewat `.fullstack/abaikan`,
gaya `.gitignore`: satu pola per baris, `#` untuk komentar.

```
# proyek warisan, seluruh repo di dalamnya
legacy-erp
# satu repo
wms/api-lama
# semua repo bernama infra di proyek mana pun
*/infra
```

Pola tanpa `/` mengena nama proyek atau repo di tingkat mana pun; pola dengan `/` mengena path relatif root. Yang
dikecualikan tidak di-scan, tidak bisa di-scout, dan tidak dihitung plafon 60 repo, tetapi tetap disebut di seksi
`## Dikecualikan` `PETA.md`. Cukup minta "abaikan repo X" ke Claude, atau jalankan
`workspace.py abaikan tambah <pola>` / `hapus <pola>` / `list`.

## Artefak

Semua artefak tinggal di root, tidak di repo anak. Root bukan repo git, jadi tidak ada commit.

| Berkas | Penulis | Sifat |
|---|---|---|
| `.fullstack/PETA.md` | `workspace.py peta --write` | ditulis ulang utuh tiap kali dibangun |
| `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` | kerangka `explore.py new` (`--jalur TELUSUR` atau `ALUR`), isi oleh skill, jahitan `explore.py seam --write` (`TELUSUR` saja) | frontmatter mencatat jalur dan SHA tiap repo; `list` menandai laporan basi |
| `.fullstack/layanan.json` | `explore.py layanan set/hapus` | pemetaan layanan yang dikonfirmasi user |
| `.fullstack/abaikan` | `workspace.py abaikan tambah/hapus`, atau disunting tangan | pola proyek/repo yang dikecualikan |

## Penegakan Mekanis

| Skrip | Menjaga |
|---|---|
| `skills/explore/scripts/check_preconditions.py` | root bukan repo git, ada repo, minimal satu profil `VALID`, `.fullstack/` bisa ditulis, `layanan.json` terbaca |
| `workspace.py scan` | peta proyek dan repo (dua tingkat, plafon 60 repo), pengecualian `.fullstack/abaikan`, status profil, kesegaran profil |
| `explore.py check` | frontmatter, urutan seksi dan bentuk tabel per jalur, rujukan `<repo>/<path>:<baris>` menunjuk berkas dan baris yang ada, `## Jahitan` sama dengan `seam` (`TELUSUR`) atau tiap repo punya langkah alur berbukti (`ALUR`), arahan untuk profil rusak, celah untuk `DUGAAN`/`AMBIGU` (`TELUSUR`) atau rujukan di tiap baris tabel (`ALUR`), tanpa `TBD`/`TODO` |

## Batas Dengan Plugin Lain

- **backend / frontend**: sumber profil, dan sumber turunan kedua explorer. Di root satu proyek, gerbang keduanya hanya
  menunjuk repo miliknya dan menyebut `/fullstack:explore` untuk semua pemahaman kode repo anak, bukan `Explore`
  bawaan. Di root multi-proyek keduanya diam.
- **analyst / product**: tidak terhubung. Temuan explore bisa dibawa user ke `/analyst:intake` secara manual.

## Sengaja Belum Ada

- Monorepo satu-git dan root lebih dari dua tingkat.
- Mengecualikan folder di dalam repo dari penelusuran scout.
- Explorer untuk repo tanpa profil, dan putaran kedua jalur `ALUR`.
- Pagar mekanis yang menolak subagent `Explore` bawaan di root (saat ini lewat teks skill dan gerbang).
- Pencocokan field DTO antar pemanggil dan penerima.
- Permukaan selain HTTP (messaging, gRPC, websocket, MCP).
- Ringkasan naratif di `PETA.md`; peta tetap mekanis.
- Sinkron peta atau laporan ke nataflow.

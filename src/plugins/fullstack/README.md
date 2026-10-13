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
di tiap repo, lalu menjawab dua jenis pertanyaan:

| Jalur | Pertanyaan | Cara | Hasil |
|---|---|---|---|
| `PETA` | "aplikasi apa saja", "stack tiap repo", "siapa memanggil siapa", "repo mana yang belum diprofilkan" | skrip membaca profil dan git, tanpa membaca kode | `.fullstack/PETA.md` |
| `TELUSUR` | satu layar, fitur, endpoint, entitas, atau integrasi | subagent `repo-scout` per repo, dipandu profil | `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` |

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

## Satu Skill, Satu Subagent

| Komponen | Peran |
|---|---|
| `fullstack:explore` | titik masuk; memilih jalur dan lingkup, membangun peta, mendispatch scout, menyusun laporan |
| `fullstack:repo-scout` | subagent read-only (haiku, kuota 10 pemanggilan) yang menelusuri satu repo berprofil; mengembalikan bukti `path:baris`, tabel endpoint, dan tabel panggilan |

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

## Artefak

Semua artefak tinggal di root, tidak di repo anak. Root bukan repo git, jadi tidak ada commit.

| Berkas | Penulis | Sifat |
|---|---|---|
| `.fullstack/PETA.md` | `workspace.py peta --write` | ditulis ulang utuh tiap kali dibangun |
| `.fullstack/explore/<YYMMDDhhmm>-<slug>.md` | kerangka `explore.py new`, isi oleh skill, jahitan `explore.py seam --write` | frontmatter mencatat SHA tiap repo; `list` menandai laporan basi |
| `.fullstack/layanan.json` | `explore.py layanan set/hapus` | pemetaan layanan yang dikonfirmasi user |

## Penegakan Mekanis

| Skrip | Menjaga |
|---|---|
| `skills/explore/scripts/check_preconditions.py` | root bukan repo git, ada repo, minimal satu profil `VALID`, `.fullstack/` bisa ditulis, `layanan.json` terbaca |
| `workspace.py scan` | peta proyek dan repo (dua tingkat, plafon 60 repo), status profil, kesegaran profil |
| `explore.py check` | frontmatter, urutan seksi dan bentuk tabel, rujukan `<repo>/<path>:<baris>` menunjuk berkas dan baris yang ada, `## Jahitan` sama dengan `seam`, arahan untuk profil rusak, celah untuk `DUGAAN`/`AMBIGU`, tanpa `TBD`/`TODO` |

## Batas Dengan Plugin Lain

- **backend / frontend**: sumber profil. Di root satu proyek, gerbang keduanya hanya menunjuk repo miliknya dan
  menyebut `/fullstack:explore`. Di root multi-proyek keduanya diam.
- **analyst / product**: tidak terhubung. Temuan explore bisa dibawa user ke `/analyst:intake` secara manual.

## Sengaja Belum Ada

- Monorepo satu-git dan root lebih dari dua tingkat.
- Pencocokan field DTO antar pemanggil dan penerima.
- Permukaan selain HTTP (messaging, gRPC, websocket, MCP).
- Ringkasan naratif di `PETA.md`; peta tetap mekanis.
- Sinkron peta atau laporan ke nataflow.

# Alur Plugin `fullstack`

> Plugin `fullstack` (v0.1.0, `src/plugins/fullstack/.claude-plugin/plugin.json`) memetakan dan menelusuri aplikasi
> dari root multi-repo: folder non-git berisi repo (`wms/{api,frontend}`) atau proyek berisi repo
> (`company/{wms,erp}/{api,frontend}`). Satu skill (`explore`) dan satu subagent (`repo-scout`). Kebenaran dijaga
> skrip stdlib di `skills/_common/`; prosa skill hanya mengarahkan. Tanpa hook, tanpa commit, read-only terhadap repo
> anak.

## Peta Komponen

| Komponen | Path | Peran |
|---|---|---|
| Skill `explore` | `src/plugins/fullstack/skills/explore/SKILL.md` | titik masuk: jalur `PETA`/`TELUSUR`, lingkup proyek, dispatch scout, laporan |
| Prasyarat | `skills/explore/scripts/check_preconditions.py` | berkas plugin, root bukan repo git, ada repo, profil `VALID`, `.fullstack/` bisa ditulis, `layanan.json` |
| Dispatch scout | `skills/explore/dispatcher/scout.md` | slot `root`, `repo`, `peran`, `pertanyaan`, `verifikasi`, `panen`; plafon; penanganan balikan |
| Kerangka laporan | `skills/explore/templates/explore-template.md` | seksi laporan `TELUSUR` beserta aturan pengisian |
| Peta | `skills/_common/workspace.py` | `scan` (proyek, repo, profil, kesegaran), `peta` (`.fullstack/PETA.md`) |
| Laporan & jahitan | `skills/_common/explore.py` | `new`, `list`, `seam`, `check`, `layanan list/set/hapus` |
| Pustaka | `skills/_common/fullstack_lib.py` | pemindaian root, pembacaan profil, `layanan.json`; salinan `SKIP_DIRS`/`STACKS` dari `hooks/detect.py` backend |
| Subagent `repo-scout` | `agents/repo-scout.md` | read-only, haiku, kuota 10 pemanggilan; satu repo per dispatch; balikan `## Repo Scout` |

## Alur Utama

```
/fullstack:explore (atau dipicu model di root multi-repo)
 ├─ check_preconditions.py ── FAIL (di dalam repo, tanpa repo, tanpa profil VALID) ──→ berhenti
 ├─ jalur
 │   ├─ PETA ── workspace.py peta --write ──→ baca PETA.md ──→ jawab di chat
 │   └─ TELUSUR
 │       ├─ lingkup proyek (tebak dari request, atau satu AskUserQuestion)
 │       ├─ PETA.md (dibangun bila belum ada), explore.py list (panen ≤ 2), layanan list
 │       ├─ putaran 1: repo-scout paralel, ≤ 4 repo
 │       ├─ putaran 2 (opsional): repo penerima calon + verifikasi endpoint, ≤ 4 repo
 │       ├─ explore.py new ──→ isi seksi dari balikan ──→ seam --write
 │       ├─ DUGAAN/AMBIGU ──→ satu AskUserQuestion ──→ layanan set ──→ seam --write
 │       ├─ explore.py check (≤ 3 putaran perbaikan)
 │       └─ ringkasan + path laporan; kerja perubahan → `cd <repo>` lalu gerbang backend/frontend
```

## Artefak & Siklus Status

| Artefak | Lokasi | Penulis | Siklus |
|---|---|---|---|
| `PETA.md` | `<root>/.fullstack/` | `workspace.py peta --write` | ditulis ulang utuh tiap kali dibangun |
| laporan `TELUSUR` | `<root>/.fullstack/explore/<YYMMDDhhmm>-<slug>.md` | `explore.py new` (kerangka), skill (isi), `seam --write` (jahitan) | `list`: segar, `basi` (HEAD salah satu repo bergeser), atau `rusak` |
| `layanan.json` | `<root>/.fullstack/` | `explore.py layanan set/hapus` | bertambah tiap konfirmasi user |

Status profil per repo (`scan`): `VALID`, `INVALID_JSON`, `TIDAK_SAH` (JSON sah, `stack` kosong atau `plugin` milik
lain), `LEGACY` (lokasi lama), atau tanpa profil. Profil `VALID` dengan lebih dari 50 commit `source_root` sejak
profil terakhir di-commit ditandai **profil tertinggal**.

## Jalur

| | `PETA` | `TELUSUR` |
|---|---|---|
| Pemicu | pertanyaan umum tentang aplikasi-aplikasi di root | satu objective konkret |
| Lingkup | seluruh root | satu proyek (default) atau proyek yang disebut |
| Baca kode | tidak | lewat `repo-scout` saja |
| Hasil | `PETA.md` | laporan `.fullstack/explore/` |
| Pertanyaan ke user | — | ≤ 1 untuk jalur/lingkup, ≤ 1 untuk pemetaan layanan |

Jahitan (`seam`): calon penerima panggilan FE = repo BE di proyek yang sama; calon penerima panggilan BE = semua repo
BE dalam lingkup kecuali dirinya. Target pasti hanya dari `layanan.json` atau FE di proyek dengan satu BE.

## Handoff Lintas Plugin

- **Masuk**: tidak ada; dipanggil user atau model di root multi-repo.
- **Keluar**: `## Arahan Lanjut` laporan — `cd <repo>` lalu `backend:tech-lead`/`frontend:lead` untuk perubahan kode,
  `<plugin>:profile` untuk profil yang tidak ada, rusak, atau tertinggal. Tidak ada pemanggilan otomatis.
- **Gerbang engineer**: di root satu proyek, `hooks/detect.py` backend/frontend mengenali root multi-repo dan hanya
  menunjuk repo miliknya beserta `/fullstack:explore`; di root multi-proyek keduanya diam.

## Titik Gagal & Pemulihan

| Gejala | Keluaran | Pemulihan |
|---|---|---|
| Sesi di dalam repo | prasyarat check 3 `DALAM_REPO` | pindah ke folder induk, atau pakai gerbang backend/frontend |
| Tidak ada profil `VALID` | prasyarat check 4 `FAIL` | `<plugin>:profile` di tiap repo aplikasi |
| Hanya satu profil `VALID` | check 4 `WARN` | lanjut; penelusuran lintas repo terbatas |
| Lebih dari 60 repo | check 3 `WARN`, `PETA.md` → `## Belum terpetakan` | jalankan dari folder yang lebih sempit |
| `layanan.json` rusak | check 6 `WARN`; `seam`/`check` FAIL | perbaiki atau hapus berkasnya; `PETA` tetap jalan |
| Baris profil di luar format | `PETA.md` → `## Belum terpetakan` | `<plugin>:profile` mode REFRESH |
| Scout gagal dua kali | repo → `### Belum disisir` | laporan terbit dengan `confidence` maksimal `medium` |
| Jahitan diketik tangan | check 4 `FAIL` | `explore.py seam --write` |
| Rujukan tanpa awalan repo / baris di luar berkas | check 3 `FAIL` | tambah awalan `<repo>/`, koreksi dari balikan scout |
| `check` FAIL sesudah 3 putaran | laporan dibiarkan | sebut check yang gagal ke user; laporan tidak dinyatakan selesai |

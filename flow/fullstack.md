# Alur Plugin `fullstack`

> Plugin `fullstack` (v0.3.0, `src/plugins/fullstack/.claude-plugin/plugin.json`) memetakan dan menelusuri aplikasi
> dari root multi-repo: folder non-git berisi repo (`wms/{api,frontend}`) atau proyek berisi repo
> (`company/{wms,erp}/{api,frontend}`). Satu skill (`explore`) dan tiga subagent (`repo-scout`, `backend-explorer`,
> `frontend-explorer`). Kebenaran dijaga
> skrip stdlib di `skills/_common/`; prosa skill hanya mengarahkan. Tanpa hook, tanpa commit, read-only terhadap repo
> anak.

## Peta Komponen

| Komponen | Path | Peran |
|---|---|---|
| Skill `explore` | `src/plugins/fullstack/skills/explore/SKILL.md` | titik masuk: jalur `PETA`/`TELUSUR`/`ALUR`/`ABAIKAN`, lingkup proyek, dispatch subagent, laporan |
| Prasyarat | `skills/explore/scripts/check_preconditions.py` | berkas plugin, root bukan repo git, ada repo, profil `VALID`, `.fullstack/` bisa ditulis, `layanan.json` |
| Dispatch scout | `skills/explore/dispatcher/scout.md` | slot `root`, `repo`, `peran`, `pertanyaan`, `verifikasi`, `panen`; plafon; penanganan balikan |
| Dispatch explorer | `skills/explore/dispatcher/explorer.md` | slot `root`, `repo`, `peran`, `objective`, `kedalaman`, `batas`, `panen`; plafon 4 dispatch satu putaran; penanganan balikan |
| Kerangka laporan | `skills/explore/templates/explore-template.md` | seksi laporan `TELUSUR` beserta aturan pengisian |
| Kerangka laporan alur | `skills/explore/templates/alur-template.md` | seksi laporan `ALUR` beserta aturan pengisian |
| Peta | `skills/_common/workspace.py` | `scan` (proyek, repo, profil, kesegaran, pengecualian), `peta` (`.fullstack/PETA.md`), `abaikan list/tambah/hapus` |
| Laporan & jahitan | `skills/_common/explore.py` | `new`, `list`, `seam`, `check`, `layanan list/set/hapus` |
| Pustaka | `skills/_common/fullstack_lib.py` | pemindaian root, pembacaan profil, `layanan.json`; salinan `SKIP_DIRS`/`STACKS` dari `hooks/detect.py` backend |
| Subagent `repo-scout` | `agents/repo-scout.md` | read-only, haiku, kuota 10 pemanggilan; satu repo per dispatch; balikan `## Repo Scout` |
| Subagent `backend-explorer` | `agents/backend-explorer.md` | read-only (`Read`, `Grep`, `Glob`), sonnet, kuota 20/40; alur di dalam satu repo BE; balikan `## Alur Explorer` |
| Subagent `frontend-explorer` | `agents/frontend-explorer.md` | read-only (`Read`, `Grep`, `Glob`), sonnet, kuota 20/40; alur di dalam satu repo FE; balikan `## Alur Explorer` |

**Turunan `code-explorer` (23 K12).** `backend-explorer` diadaptasi dari `src/plugins/backend/agents/code-explorer.md`
dan `frontend-explorer` dari `src/plugins/frontend/agents/code-explorer.md`. Yang diambil: investigasi dua tahap,
jendela baca (`L - 15` s.d. `L + 35`, 30–50 baris, larangan berkas utuh > 100 baris), jenjang `menyeluruh` (di BE:
method utuh sampai 120 baris, maksimal 3 jendela per berkas), pemetaan layer dan permukaan, aturan bisnis, dan
pemisahan `Tidak ditemukan`/`Belum disisir`. Yang dibuang: `Write`, laci taskdir dan panennya, blok `Format laporan`
pendispatch, dan jalur profil absen. Mengubah angka jendela di sumber berarti mengubah turunannya juga;
`tests/fullstack/test_alur_23.py` memaku keduanya.

## Alur Utama

```
/fullstack:explore (atau dipicu model di root multi-repo)
 ├─ check_preconditions.py ── FAIL (di dalam repo, tanpa repo, tanpa profil VALID) ──→ berhenti
 ├─ jalur
 │   ├─ ABAIKAN ── workspace.py abaikan tambah|hapus <pola> ──→ peta --write
 │   ├─ PETA ── workspace.py peta --write ──→ baca PETA.md ──→ jawab di chat
 │   ├─ TELUSUR
 │   │   ├─ lingkup proyek (tebak dari request, atau satu AskUserQuestion)
 │   │   ├─ PETA.md (dibangun bila belum ada), explore.py list (panen ≤ 2), layanan list
 │   │   ├─ putaran 1: repo-scout paralel, ≤ 4 repo
 │   │   ├─ putaran 2 (opsional): repo penerima calon + verifikasi endpoint, ≤ 4 repo
 │   │   ├─ explore.py new ──→ isi seksi dari balikan ──→ seam --write
 │   │   ├─ DUGAAN/AMBIGU ──→ satu AskUserQuestion ──→ layanan set ──→ seam --write
 │   │   ├─ explore.py check (≤ 3 putaran perbaikan)
 │   │   └─ ringkasan + path laporan; "dalami sisi X" → ALUR; kerja perubahan → gerbang backend/frontend
 │   └─ ALUR
 │       ├─ lingkup proyek, repo berprofil VALID, kedalaman (ringkas default, menyeluruh bila diminta)
 │       ├─ PETA.md (dibangun bila belum ada), explore.py list (panen ≤ 2, jalur mana pun)
 │       ├─ satu putaran: backend-explorer (BE) / frontend-explorer (FE) paralel, ≤ 4 dispatch
 │       ├─ explore.py new --jalur ALUR --kedalaman <k> ──→ isi seksi dari balikan (tanpa seam)
 │       ├─ explore.py check (≤ 3 putaran perbaikan)
 │       └─ ringkasan alur + path laporan; penerima panggilan ke repo lain → TELUSUR
```

## Artefak & Siklus Status

| Artefak | Lokasi | Penulis | Siklus |
|---|---|---|---|
| `PETA.md` | `<root>/.fullstack/` | `workspace.py peta --write` | ditulis ulang utuh tiap kali dibangun |
| laporan `TELUSUR` | `<root>/.fullstack/explore/<YYMMDDhhmm>-<slug>.md` | `explore.py new` (kerangka), skill (isi), `seam --write` (jahitan) | `list`: segar, `basi` (HEAD salah satu repo bergeser), atau `rusak` |
| laporan `ALUR` | sama, frontmatter `jalur: ALUR` dan `kedalaman` | `explore.py new --jalur ALUR` (kerangka), skill (isi) | sama; `seam` menolaknya. Laporan tanpa `jalur` dibaca sebagai `TELUSUR` |
| `layanan.json` | `<root>/.fullstack/` | `explore.py layanan set/hapus` | bertambah tiap konfirmasi user |
| `abaikan` | `<root>/.fullstack/` | `workspace.py abaikan tambah/hapus` atau user | dibaca semua skrip; yang dikecualikan tidak di-scan dan tercatat di `PETA.md` `## Dikecualikan` |

Status profil per repo (`scan`): `VALID`, `INVALID_JSON`, `TIDAK_SAH` (JSON sah, `stack` kosong atau `plugin` milik
lain), `LEGACY` (lokasi lama), atau tanpa profil. Profil `VALID` dengan lebih dari 50 commit `source_root` sejak
profil terakhir di-commit ditandai **profil tertinggal**.

## Jalur

| | `PETA` | `TELUSUR` | `ALUR` |
|---|---|---|---|
| Pemicu | pertanyaan umum tentang aplikasi-aplikasi di root | satu objective konkret: di mana, siapa memanggil siapa | bagaimana sesuatu bekerja di dalam repo |
| Lingkup | seluruh root | satu proyek (default) atau proyek yang disebut | repo yang disebut atau tersirat objective |
| Baca kode | tidak | lewat `repo-scout` saja | lewat `backend-explorer`/`frontend-explorer` saja |
| Plafon | — | ≤ 4 repo per putaran, 2 putaran | ≤ 4 dispatch, 1 putaran |
| Hasil | `PETA.md` | laporan `.fullstack/explore/` | laporan `.fullstack/explore/` berjalur `ALUR` |
| Pertanyaan ke user | — | ≤ 1 untuk jalur/lingkup, ≤ 1 untuk pemetaan layanan | ≤ 1 untuk jalur/lingkup |

`check` laporan `ALUR`: check 4 **Alur per repo** (tiap repo frontmatter punya `### <repo> (BE|FE)` di `## Alur` dengan
langkah bernomor berbukti, atau tercatat di `### Belum disisir`) dan check 6 **Bukti tabel** (tiap baris
`## Aturan Bisnis`/`## Permukaan` milik repo frontmatter dan berujukan) menggantikan `Jahitan = seam` dan `Celah
pemetaan`. Check 1, 2, 3, 5, dan 7 sama, dengan seksi dan kolom tabel milik jalur `ALUR`.

Jahitan (`seam`): calon penerima panggilan FE = repo BE di proyek yang sama; calon penerima panggilan BE = semua repo
BE dalam lingkup kecuali dirinya. Target pasti hanya dari `layanan.json` atau FE di proyek dengan satu BE.

## Handoff Lintas Plugin

- **Masuk**: tidak ada; dipanggil user atau model di root multi-repo.
- **Keluar**: `## Arahan Lanjut` laporan — `cd <repo>` lalu `backend:tech-lead`/`frontend:lead` untuk perubahan kode,
  `<plugin>:profile` untuk profil yang tidak ada, rusak, atau tertinggal. Tidak ada pemanggilan otomatis.
- **Gerbang engineer**: di root satu proyek, `hooks/detect.py` backend/frontend mengenali root multi-repo dan hanya
  menunjuk repo miliknya beserta `/fullstack:explore` untuk semua pemahaman kode repo anak, dengan catatan bahwa
  subagent `Explore`/`general-purpose` bawaan tidak dipakai (23 L5); di root multi-proyek keduanya diam.

## Titik Gagal & Pemulihan

| Gejala | Keluaran | Pemulihan |
|---|---|---|
| Sesi di dalam repo | prasyarat check 3 `DALAM_REPO` | pindah ke folder induk, atau pakai gerbang backend/frontend |
| Tidak ada profil `VALID` | prasyarat check 4 `FAIL` | `<plugin>:profile` di tiap repo aplikasi |
| Hanya satu profil `VALID` | check 4 `WARN` | lanjut; penelusuran lintas repo terbatas |
| Lebih dari 60 repo | check 3 `WARN`, `PETA.md` → `## Belum terpetakan` | jalankan dari folder yang lebih sempit |
| `layanan.json` rusak | check 6 `WARN`; `seam`/`check` FAIL | perbaiki atau hapus berkasnya; `PETA` tetap jalan |
| `abaikan` tak terbaca atau berbaris tidak sah | check 7 `WARN`, `PETA.md` → `## Belum terpetakan` | perbaiki lewat `workspace.py abaikan`; baris tidak sah diabaikan, repo-nya tetap dipetakan |
| Laporan merujuk repo yang kemudian dikecualikan | check 1 `FAIL` "dikecualikan `.fullstack/abaikan`" | hapus pola, atau buat laporan baru tanpa repo itu |
| Baris profil di luar format | `PETA.md` → `## Belum terpetakan` | `<plugin>:profile` mode REFRESH |
| Scout atau explorer gagal dua kali | repo → `### Belum disisir` | laporan terbit dengan `confidence` maksimal `medium` |
| Repo `ALUR` tanpa profil `VALID` | `explore.py new` FAIL "tanpa profil VALID" | `<plugin>:profile` di dalam repo itu |
| `seam` atas laporan `ALUR` | FAIL "`seam` hanya untuk laporan TELUSUR" | jahitan dicari lewat jalur `TELUSUR` |
| Repo `ALUR` tanpa langkah berbukti | check 4 `FAIL` | salin langkah dari balikan explorer, atau catat repo di `### Belum disisir` |
| Jahitan diketik tangan | check 4 `FAIL` | `explore.py seam --write` |
| Rujukan tanpa awalan repo / baris di luar berkas | check 3 `FAIL` | tambah awalan `<repo>/`, koreksi dari balikan scout |
| `check` FAIL sesudah 3 putaran | laporan dibiarkan | sebut check yang gagal ke user; laporan tidak dinyatakan selesai |

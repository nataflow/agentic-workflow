---
name: lead
description: Gunakan ketika ada permintaan kerja baru atau susulan di repo frontend (desain UI/UX, fitur, refaktor, bugfix, explore, review) - routing lane, sections, dan taskdir diputuskan dari kode, akar dikunci, lalu rantai diserahkan ke gate pemiliknya, sebelum satu berkas src/ disentuh
---

## THE IRON LAW

- Dilarang membuat, mengedit, atau menghapus berkas di `src/` dari gate ini — dan dari main loop mana pun sebelum lane, slug, taskdir, dan akar `TASK.md` sah.
- Sapuan lokasi berhenti pada nama path (`Glob`) dan pelokalan simbol (`Grep`); isi komponen tidak dibuka. Penelusuran lintas-layer didelegasikan ke `code-explorer` lewat `dispatcher/explorer.md`.
- Keadaan taskdir dibaca dari `scripts/taskdir_state.py`, bukan dari ingatan sesi atau pembacaan frontmatter satu per satu.
- Lane dan `sections` hanya bergeser lewat `chain.py escalate` (plafon 2 per taskdir); hop yang sudah disetujui hanya dibuka lewat `chain.py reopen` (kaskade ke seluruh hop tercentang di bawahnya; plafon 3 per hop — dihitung saat hop itu target `reopen`, kaskade tidak memakan kuota hop di bawahnya — dan 6 per taskdir untuk semua reopen) — keduanya atas konfirmasi user.
- Tiap gate adalah persetujuan independen yang dimateraikan `chain.py approve` oleh gate pemiliknya — materainya (`Konten disetujui: <sha>` + `Hop: <ROW>`) sah hanya bila lebih baru daripada reopen terakhir hop itu; lead tidak pernah mencentang ledger.

## Precondition [REQUIRED]

1. Repositori target adalah proyek frontend dari stack adapter `skills/profile/stacks/<stack-id>.md`: React + Vite SPA, React Native/Expo, SvelteKit, atau Svelte + Vite. Next.js tidak dilayani.
2. Profil `.claude/profile/frontenddev/` ada dan `index.json`-nya ber-field `stack`; tidak ada → Failure path 1.
3. Git repo lokal, working tree bersih di luar laci `.explore/`/`.frontenddev/`.
4. `python3` tersedia. Skrip: `taskdir_state.py` = `${CLAUDE_PLUGIN_ROOT}/skills/lead/scripts/taskdir_state.py`; `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`.

## Parameter [REQUIRED]

- `prompt` — string — `[REQUIRED]` — permintaan kerja: fitur, bug, refaktor, pertanyaan penelusuran, atau review.
- `force_lane` — string — default `""` — `PROFILE`, `FULL_PIPELINE`, `FAST_FORWARD`, `REFACTOR_ARCH`, `HOTFIX_MINOR`, `EXPLORE_FACT`, `REVIEW_AUDIT` — hanya bila user menyebutnya eksplisit.
- `target_app` — string — default `""` — target app pada monorepo (`apps/web`, `apps/mobile`).
- `finding_source` — string — default `""` — path berkas temuan review ad-hoc (`frontenddev/reviews/<berkas>.md`) bila kerja ini lahir dari temuan. `REVIEW.md` `BLOCKED` rantai aktif tidak memakai parameter ini — ia diperbaiki di taskdir yang sama (Phase 8).
- `finding_ids` — list — default `[]` — ID temuan yang dikerjakan; kosong padahal `finding_source` terisi berarti seluruh temuan `PLANNED`.
- `ticket_source` — string — default `""` — path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` berstatus `READY` bila kerja ini lahir dari tiket analyst. Terisi → `prompt` = kartu tiket (H1 sampai akhir `## Lampiran`) apa adanya, dan tiap `AC-{n}`/`BR-{n}` kartu dirujuk `TAC-{n}`/`TBR-{n}` di seluruh artefak frontenddev agar tidak bertabrakan dengan `AC-{n}` CONTRACT. Dilarang disimpulkan dari isi `prompt`: permintaan yang tampak seperti kartu tiket tanpa path → tanyakan path-nya lewat `AskUserQuestion`.

## Workflow

### Phase 1 — Sapuan Lokasi Fitur

- Glob nama path dari kata kunci prompt (maks 2 pola; feature root dari `structure.md` profil): `src/features/*<kw>*/**`, `src/lib/features/*<kw>*/**`, `apps/*/src/features/*<kw>*/**`.
- Tepat satu cocok → slug dari nama folder aktual. Lebih dari satu (monorepo) → pakai `target_app`, atau tanyakan lewat `AskUserQuestion`. Nol → fitur baru, slug kebab-case baru.
- **Kuota sapuan main loop** per pemicu: maksimal 3 panggilan `Glob`+`Grep`, nol berkas dibaca isinya, nol `Bash` penelusuran (tidak dihitung: berkas `.claude/profile/frontenddev/` dan skrip Phase 2).
- **Pemicu dispatch wajib** — satu cukup: objek kerja melintasi lebih dari satu layer; yang dicari relasi (pemanggil Controller, konsumen DTO, pemilik query key); simbol dari prompt tak muncul di Glob #1; kuota habis. Hidrasi `dispatcher/explorer.md` (`{laci}` kosong — taskdir belum ada) dan dispatch `code-explorer` (`subagent_type`: `frontenddev:code-explorer`). `confidence: low` → pertajam objective, ulangi sekali.

### Phase 2 — Pemulihan Taskdir

Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/lead/scripts/taskdir_state.py`. Tiap baris memvonis satu keadaan dan satu rute berikutnya:

| Keadaan | Rute |
|---|---|
| `AKAR` | taskdir kosong → Phase 7 `frontenddev:task`; user batal → hapus direktori kosong itu (tidak ada yang di-commit). `TASK.md belum ter-commit` → lead menjalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/task/scripts/validate_task.py --taskdir <taskdir>`: `PASS` → commit `docs(<slug>): kunci TASK sebagai akar rantai`; `FAIL` → tanyakan user (task tidak menulis ulang akar) |
| `GATE` | skill pemilik hop pertama yang belum `[x]` (mode `plan` disebut skrip); draft `DRAFT` tertunda → gate itu menanyakan keputusan user; batch brief ter-commit belum disetujui → `plan` menjalankan prasyarat mode REVISE lalu langsung Phase 5 tanpa menulis ulang |
| `DRIFT` | konten hop tercentang atau `SC-{n}` TASK.md berubah sesudah disetujui → tanyakan user: `chain.py reopen --row <ROW>` atau pulihkan isi yang disetujui |
| `EKSEKUSI` / `PENUTUP` | `frontenddev:architect`; `PENUTUP` juga untuk `REVIEW.md` basi (ada commit yang menyentuh `brief-*.md` sesudahnya) — review ulang menimpanya |
| `TERHENTI` | brief `BLOCKED` tanpa remedi → Phase 8 (re-entry BRIEF) → `plan` APPEND brief remedi |
| `TEMUAN` | `REVIEW.md` `BLOCKED` → Phase 8: `chain.py reopen --row BRIEF` → `plan` APPEND brief perbaikan di taskdir yang sama → `architect` eksekusi dan review ulang |
| `LAPORAN` | `frontenddev:architect` (Phase 5) — umpan balik profil dulu, lalu architect menyerahkan ke `report` |
| `LAPORAN TERTUNDA` | `REPORT.md` tertulis tetapi commit-nya gagal → `frontenddev:architect` Phase 5 butir 4 (validasi lalu commit); dilarang membuka taskdir baru |
| `DITUTUP` | `TASK.md` `status: ABANDONED` (`chain.py abandon`) — tidak tampil di pemindaian |
| `RUSAK` | taskdir yang disebut tidak ada, nama direktori di luar pola `<YYMMDDhhmm>-<slug>`, artefak tanpa `TASK.md`, pasangan lane/sections tidak sah, `lane`/`sections` berubah di luar commit akar (`kunci TASK`) atau `chain.py escalate`, atau ledger ≠ jadwal sections → laporkan ke user; dilarang menambal akar atau ledger dengan tangan |

Skrip keluar `[FAIL] ... bukan repo git` → hentikan; rantai frontenddev menuntut git.

Permintaan baru saat ada taskdir terbuka → tanyakan lewat `AskUserQuestion`: lanjutkan taskdir itu, atau buka taskdir baru (yang lama tetap terbuka dan akan muncul lagi di pemindaian berikutnya). Taskdir ber-brief `BLOCKED` dilarang ditinggal diam-diam.

### Phase 3 — Lane

| Lane | Pemicu | Rute awal |
|---|---|---|
| `PROFILE` | profil belum ada / tidak sah / tidak lengkap / masih di lokasi lama `.claude/profile/` (MIGRATE) | `frontenddev:profile` |
| `FULL_PIPELINE` | fitur baru, perombakan alur atau layout | `task` → `ux-design` dan/atau `ui-design` |
| `FAST_FORWARD` | endpoint/logic data baru tanpa ubah alur & layout | `task` → `contract` |
| `REFACTOR_ARCH` | restrukturisasi layer | `task` → `contract` |
| `HOTFIX_MINOR` | bugfix/teks lokal, 1 berkas, tanpa DTO/alur/state baru | `task` → `plan` (MINOR) |
| `EXPLORE_FACT` | pertanyaan faktual letak simbol/struktur | dispatch `code-explorer`, jawab, selesai — tanpa taskdir |
| `REVIEW_AUDIT` | penilaian kode di luar rantai aktif | `frontenddev:review` — tanpa taskdir |

Sumber masalah atau letak simbol belum pasti → dispatch `code-explorer` lebih dulu, lalu putuskan lane dari pointer `file:baris`-nya. Rincian per lane di `references/lane-routing-matrix.md`.

### Phase 4 — Sections

| Kondisi | Lane | `sections` | Hop ledger |
|---|---|---|---|
| Fitur baru (layar + alur + API) | `FULL_PIPELINE` | `flow, ui` (+ `architecture` bila layer baru dirancang) | FLOW, UI, CONTRACT, BRIEF |
| Alur berubah, tampilan tetap | `FULL_PIPELINE` | `flow` | FLOW, CONTRACT, BRIEF |
| Tampilan berubah, alur tetap | `FULL_PIPELINE` | `ui` | UI, CONTRACT, BRIEF |
| Data/endpoint baru tanpa ubah UI | `FAST_FORWARD` | `architecture` | CONTRACT, BRIEF |
| Refaktor layer | `REFACTOR_ARCH` | `architecture` | CONTRACT, BRIEF |
| Perbaikan terisolasi | `HOTFIX_MINOR` | — (kosong) | BRIEF |

Invarian pasangan ditegakkan skrip di setiap gate: `HOTFIX_MINOR` ⇔ sections kosong; `FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `architecture`; `FULL_PIPELINE` memuat `flow` atau `ui`. **Batas MINOR** — ketiganya wajib: nol endpoint/payload/query key baru, nol cabang state atau layout baru, satu berkas fitur eksisting.

### Phase 5 — Slug & Taskdir

- Slug `<feature>-<jenis-kerja>` kebab-case dari path feature root profil; taskdir `./frontenddev/docs/<YYMMDDhhmm>-<slug>/` (`date +%y%m%d%H%M`).
- Buat `<taskdir>/.explore/` bersamaan; salin laporan explorer Phase 1 dari `.frontenddev/explore/` ke `<taskdir>/.explore/gate-<slug>.md`. Laci itu gitignored dan dilarang di-stage.
- Nama berkas taskdir tetap: `TASK.md`, `FLOW.md`, `UI.md`, `CONTRACT.md`, `brief-<NN>-<unit>.md`, `REVIEW-PLAN.md`, `report-<NN>.md`, `REVIEW.md`, `REPORT.md`.

### Phase 6 — Gate & Pemiliknya

| Checkpoint | Pemilik | Jalan bila | Dikunci oleh |
|---|---|---|---|
| Akar | `frontenddev:task` | lane berakar | commit akar; `## Chain` ditulis `chain.py init` |
| Gate Flow | `frontenddev:ux-design` | `sections` ∋ `flow` | `chain.py approve --row FLOW` |
| Gate Design | `frontenddev:ui-design` | `sections` ∋ `ui` | `chain.py approve --row UI` |
| Gate Contract | `frontenddev:contract` (+ `contract-reviewer`) | `sections` non-kosong | `chain.py approve --row CONTRACT` |
| Gate Breakdown | `frontenddev:plan` (+ `doc-reviewer` Plan Review, non-MINOR) | selalu | `chain.py approve --row BRIEF` |
| Eksekusi & review penutup | `frontenddev:architect` (+ `code-implementor`, `code-reviewer`) | ledger tercentang penuh | commit unit; `REVIEW.md` lolos `validate_review.py` |
| Laporan | `frontenddev:report` | `REVIEW.md` `PASS`/`WARNING` | commit `REPORT.md` — penanda tuntas |

Dokumen gate lahir `DRAFT` dan di-commit; approval hanya lewat `AskUserQuestion` gate pemiliknya yang dimateraikan `chain.py approve`. Tiap gate hilir memvonis hop hulunya tercentang **dan** kontennya tidak berubah sejak disetujui.

### Phase 7 — Klarifikasi & Kunci Akar

- Ketidakjelasan intent atau cakupan → maksimal 3 pertanyaan lewat `AskUserQuestion` dengan opsi konkret beserta trade-off; dilarang menanyakan yang sudah ada di profil.
- **Penguncian akar** — selalu pada lane berakar: panggil `frontenddev:task` dengan `{ taskdir, lane, sections, request, evidence, clarification, finding_source, finding_ids, ticket_source }`. `evidence` diisi `file:baris` sapuan Phase 1 atau laporan explorer; fitur baru memakai titik sambungnya dari `surface-map.md`. Gate pertama berangkat hanya sesudah `TASK ROOT LOCKED` tanpa `TERTAHAN`.

### Phase 8 — Kanal Eskalasi & Re-entry

Dijalankan ketika gate hilir mengembalikan kendali dengan temuan yang menggeser rencana. Tiap tindakan diawali `AskUserQuestion` yang menyebut konsekuensinya, lalu dimateraikan skrip:

| Pemicu | Tindakan |
|---|---|
| MINOR menemukan endpoint, DTO, query key, atau cabang state baru | `chain.py escalate --lane FAST_FORWARD --sections architecture --reason <...>` (atau `FULL_PIPELINE` bila alur/layout ikut berubah); BRIEF sudah `[x]` → `reopen --row BRIEF` dulu, karena escalate menolak hop tercentang di bawah hop baru |
| Contract menyadari alur atau layar baru | `chain.py escalate --lane FULL_PIPELINE --sections <...> --reason <...>` — hop baru disisipkan di atas CONTRACT; hop di bawahnya yang sudah `[x]` wajib di-`reopen` lebih dulu |
| Brief `BLOCKED` (`TERHENTI`) | `chain.py reopen --row BRIEF --reason <unit NN BLOCKED — ringkas>` → `plan` APPEND brief remedi (`remedies: "NN"`) |
| `REVIEW.md` `BLOCKED` (`TEMUAN`) atau verifikasi penutup merah karena cacat eksekusi | `chain.py reopen --row BRIEF --reason <REVIEW BLOCKED — ringkas>` → `plan` APPEND brief perbaikan (tanpa `remedies`) → `architect` eksekusi → review ulang menimpa `REVIEW.md` |
| Berkas yatim, remedi ketiga atas unit yang sama, atau DTO baru ditemukan | non-MINOR: `chain.py reopen --row CONTRACT --reason <...>` (kaskade membuka BRIEF) → `contract` melengkapi Files Touched/DTO → approve → `plan` APPEND. MINOR (tanpa hop CONTRACT): `reopen --row BRIEF` → `escalate --lane FAST_FORWARD --sections architecture` → `contract` → `plan` APPEND |
| `DRIFT` | `chain.py reopen --row <ROW>` atau user memulihkan isi yang disetujui |
| `SC-{n}` berubah (amandemen akar) | atas persetujuan user, sunting `## Success Criteria`: SC baru ditambah di akhir tanpa menomori ulang; SC aktif maksimal 7 (butir gugur tidak dihitung); SC gugur tetap bernomor, ditulis `- [ ] **SC-n**: ~~<teks lama beserta — verifikasi: ...>~~ — gugur: <alasan>` (SC gugur tidak ditagih hilir: tanpa AC, tanpa `fulfills` brief aktif, tanpa vonis `REVIEW.md`, tanpa baris Catatan REPORT; brief `DONE` yang dulu memikulnya tetap sah; `CONTRACT.md` yang masih menyebut token SC gugur di Sumber AC gagal `validate_doc.py` → kontrak direvisi). Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/task/scripts/validate_task.py --taskdir <taskdir> --amend`, commit `docs(<slug>): amandemen akar TASK`, lalu `chain.py reopen --row <hop tercentang teratas>` — perubahan SC membuat tiap hop tercentang drift, kaskade membuka sisanya; tiap hop di-approve ulang oleh gate pemiliknya (BRIEF tanpa brief `READY` baru sah tanpa Plan Review baru) |
| Temuan asal ditunda atau dibatalkan user | tulis `> Status: DEFERRED <tanggal> — <alasan>` / `DROPPED` di bawah temuan pada berkas `finding_source`, commit terpisah |
| Plafon habis, atau user memutuskan berhenti | `chain.py abandon --taskdir <taskdir> --reason <keputusan user>` → `DITUTUP` |

Plafon ditegakkan skrip: eskalasi 2 per taskdir; re-entry 3 per hop (dihitung saat hop itu target `reopen`; kaskade tidak memakan kuota hop di bawahnya) dan 6 per taskdir (semua reopen). Plafon habis → cacatnya di lingkup, bukan di dokumen: klarifikasi lingkup bersama user di Phase 8 ini — amandemen akar (baris `SC-{n}` berubah), atau tutup taskdir lewat `chain.py abandon`.

## Guardrails

- **DILARANG MENGEDIT KODE DI GATE**: nol perubahan `src/` dari lead.
- **DILARANG MEMBACA FILE IMPLEMENTASI PADA SAPUAN**: berhenti pada nama path dan pelokalan simbol.
- **ESKALASI DETERMINISTIK MINOR**: endpoint, query key, DTO, atau cabang state baru bukan MINOR.
- **ANTI REKAYASA SLUG**: slug dari path feature root profil, bukan karangan.
- **ANTI MONOREPO GUESSING**: target app ambigu ditanyakan, bukan ditebak.
- **LEDGER HANYA LEWAT SKRIP**: dilarang menyunting frontmatter `lane`/`sections`, status dokumen gate, atau baris `## Chain` dengan tangan.
- **SUBAGENT HANYA LEWAT TEMPLATE**: `code-explorer` hanya lewat prompt terhidrasi `dispatcher/explorer.md`.
- **ATOMIC COMMITS ONLY**: dilarang `git add .`/`-A`.
- **RATIONALIZATION PREVENTION**:
  - "Cuma satu baris teks, edit langsung di `src/`" — melewati gate menghapus jejak dan memicu regresi tanpa pelacakan.
  - "Taskdir lama yang BLOCKED diabaikan, buat baru saja" — taskdir setengah jalan menjadi yatim; `taskdir_state.py` akan terus menampilkannya.
  - "Gate Flow dan Contract digabung biar ringkas" — kesalahan alur merusak seluruh DTO.
  - "Lane saya ganti saja di frontmatter" — `chain.py escalate` satu-satunya jalan; tulisan tangan gagal di setiap skrip hilir.
  - "Satu grep lagi, tanggung kalau dispatch explorer" — kuota mekanis.

## Output [REQUIRED]

Handoff ke gate berikutnya — tutup satu baris: `LEAD — <lane> · sections <nilai | -> · <taskdir> · akar TASK.md @ <sha | -> · next <skill (mode)> · stack <stack-id>`. Lane tanpa taskdir: `LEAD — <EXPLORE_FACT | REVIEW_AUDIT | PROFILE> · next <skill | jawaban langsung>`. Tertahan (monorepo ambigu, stack tak didukung, taskdir RUSAK, plafon habis) — sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### LEAD — TERTAHAN
- **Sebab**: <...>
- **Taskdir**: <path · keadaan taskdir_state> | —
- **Keputusan dibutuhkan**: <pertanyaan ke user>
```

## Failure path

1. **Profil tidak ada, tidak sah, tidak lengkap, atau di lokasi lama**: rute `PROFILE` ke `frontenddev:profile` tanpa titik henti konfirmasi — mode GENERATE (belum ada), REFRESH (`index.json` bukan JSON valid, `stack` di luar kontrak, atau berkas hilang), atau MIGRATE (profil frontenddev di `.claude/profile/` lama), sesuai baris `Terselesaikan:` skrip prasyaratnya — lalu lanjutkan rute tertunda. `force: true` hanya bila rute REFRESH menyala di atas profil frontenddev sendiri; tidak pernah atas profil milik plugin lain atau lokasi lama. Profil milik plugin lain di `.claude/profile/` dibiarkan dan dianggap tidak ada.
2. **Stack tidak didukung**: manifest memuat `next`, atau React/Svelte tanpa Vite (CRA, Rollup) → hentikan, jangan buat taskdir. `stack` profil di luar `stacks/_CONTRACT.md` bukan cabang ini: itu profil tidak sah → Failure path 1 (REFRESH).
3. **Ambiguitas monorepo**: fitur sama di lebih dari satu app → `AskUserQuestion` sebelum slug.
4. **Taskdir RUSAK**: laporkan detail `taskdir_state.py` ke user; dilarang menulis ulang akar atau ledger.
5. **Izin tulis ditolak**: laporkan galat OS; minta user memeriksa izin direktori.
6. **Working tree kotor**: minta user commit atau stash kerjanya sendiri sebelum taskdir baru dibuka; dilarang men-stash atas namanya.

## STYLE

- Imperatif aktif; istilah domain tetap: Lane, Sections, Slug, Taskdir, Gate, Hop, Ledger.
- Keadaan taskdir dikutip dari keluaran skrip, bukan diparafrasekan.

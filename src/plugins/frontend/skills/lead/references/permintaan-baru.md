# Permintaan Baru — `lead` Phase 3–7

Rumah kanonik Phase 3–7 `frontend:lead`: lane, sections, slug & taskdir, peta gate, klarifikasi, dan penguncian akar. Dimuat **hanya** untuk permintaan kerja baru — lanjutan serah terima (`lead` Phase 1 butir pertama), sinkron ulang, dan rute Phase 2 ke taskdir terbuka tidak membacanya (Langkah 36 L1: body `lead` dimuat ulang tiap sesi lanjutan). `«nama.py»` = path absolut dari peta **Skrip** Precondition butir 4 `lead/SKILL.md`; nomor Phase dan rujukan silang sama dengan `SKILL.md`.

---

## Phase 3 — Lane

| Lane | Pemicu | Rute awal |
|---|---|---|
| `PROFILE` | profil belum ada / tidak sah / tidak lengkap / masih di lokasi lama `.claude/profile/` (MIGRATE) | `frontend:profile` |
| `FULL_PIPELINE` | fitur baru, perombakan alur atau layout | `task` → `ux-design` dan/atau `ui-design` |
| `FAST_FORWARD` | endpoint/logic data baru tanpa ubah alur & layout | `task` → `contract` |
| `REFACTOR_ARCH` | restrukturisasi layer | `task` → `contract` |
| `HOTFIX_MINOR` | bugfix/teks lokal, 1 berkas, tanpa DTO/alur/state baru | `task` → `plan` (MINOR) |
| `EXPLORE_FACT` | pertanyaan faktual letak simbol/struktur | dispatch `code-explorer`, jawab, selesai — tanpa taskdir; profil absen tidak menahannya (explorer menyisir dari root dan mencatatnya di `### Caveats`) |
| `REVIEW_AUDIT` | penilaian kode di luar rantai aktif | `frontend:review` — tanpa taskdir; butuh profil (`## Review checklist` adapter `stack`), jadi profil absen → `PROFILE` dulu |

Sumber masalah atau letak simbol belum pasti → dispatch `code-explorer` lebih dulu, lalu putuskan lane dari pointer `file:baris`-nya. Rincian per lane di `references/lane-routing-matrix.md`.

## Phase 4 — Sections

| Kondisi | Lane | `sections` | Hop ledger |
|---|---|---|---|
| Fitur baru (layar + alur + API) | `FULL_PIPELINE` | `flow, ui` (+ `architecture` bila layer baru dirancang) | FLOW, UI, CONTRACT, BRIEF |
| Alur berubah, tampilan tetap | `FULL_PIPELINE` | `flow` | FLOW, CONTRACT, BRIEF |
| Tampilan berubah, alur tetap | `FULL_PIPELINE` | `ui` | UI, CONTRACT, BRIEF |
| Data/endpoint baru tanpa ubah UI | `FAST_FORWARD` | `architecture` | CONTRACT, BRIEF |
| Refaktor layer | `REFACTOR_ARCH` | `architecture` | CONTRACT, BRIEF |
| Perbaikan terisolasi | `HOTFIX_MINOR` | — (kosong) | BRIEF |

Invarian pasangan ditegakkan skrip di setiap gate: `HOTFIX_MINOR` ⇔ sections kosong; `FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `architecture`; `FULL_PIPELINE` memuat `flow` atau `ui`. **Batas MINOR** — ketiganya wajib: nol endpoint/payload/query key baru, nol cabang state atau layout baru, satu berkas fitur eksisting.

## Phase 5 — Slug & Taskdir

- Slug `<feature>-<jenis-kerja>` kebab-case dari path feature root profil; taskdir `./frontenddev/docs/<YYMMDDhhmm>-<slug>/` (`date +%y%m%d%H%M`).
- Slug unik per repo: commit rantai dikenali dari `(<slug>)`, dan prasyarat `task` menolak slug yang sudah dipakai taskdir lain, termasuk yang `TUNTAS`/`DITUTUP`. Slug kembar → tambah sufiks `-2` (`-3`, …) sampai unik.
- Buat `<taskdir>/.explore/` bersamaan; salin laporan explorer Phase 1 dari `.frontenddev/explore/` ke `<taskdir>/.explore/gate-<slug>.md`. Laci itu gitignored dan dilarang di-stage.
- Nama berkas taskdir tetap: `TASK.md`, `FLOW.md`, `UI.md`, `CONTRACT.md`, `brief-<NN>-<unit>.md`, `REVIEW-PLAN.md`, `report-<NN>.md`, `REVIEW.md`, `REPORT.md`, `JOURNEY.md`.

## Phase 6 — Gate & Pemiliknya

| Checkpoint | Pemilik | Jalan bila | Dikunci oleh |
|---|---|---|---|
| Akar | `frontend:task` | lane berakar | `chain.py root` (`base_commit` + kejadian `akar`); `## Chain` ditulis `chain.py init` |
| Gate Flow | `frontend:ux-design` | `sections` ∋ `flow` | `chain.py approve --row FLOW` |
| Gate Design | `frontend:ui-design` | `sections` ∋ `ui` | `chain.py approve --row UI` |
| Gate Contract | `frontend:contract` (+ `contract-reviewer`) | `sections` non-kosong | `chain.py approve --row CONTRACT` |
| Gate Breakdown | `frontend:plan` (+ `doc-reviewer` Plan Review, non-MINOR) | selalu | `chain.py approve --row BRIEF` |
| Eksekusi & review penutup | `frontend:architect` (+ `code-implementor`, `code-reviewer`) | ledger tercentang penuh | commit unit; `REVIEW.md` lolos `validate_review.py` |
| Laporan | `frontend:report` | `REVIEW.md` `PASS`/`WARNING` | `REPORT.md` lolos `validate_report.py` — penanda tuntas |

Dokumen gate lahir `DRAFT` dan dicatat `chain.py draft` sebelum diajukan (tanpa commit: dokumen taskdir diabaikan git); approval hanya lewat `AskUserQuestion` gate pemiliknya yang dimateraikan `chain.py approve`. Tiap gate hilir memvonis hop hulunya tercentang **dan** kontennya tidak berubah sejak disetujui.

## Phase 7 — Klarifikasi & Kunci Akar

- Ketidakjelasan intent atau cakupan → maksimal 3 pertanyaan lewat `AskUserQuestion` dengan opsi konkret beserta trade-off; dilarang menanyakan yang sudah ada di profil.
- **Penguncian akar** — selalu pada lane berakar: panggil `frontend:task` dengan `{ taskdir, lane, sections, request, evidence, clarification, finding_source, finding_ids, ticket_source }`. `evidence` diisi `file:baris` sapuan Phase 1 atau laporan explorer; fitur baru memakai titik sambungnya dari `surface-map.md`. Gate pertama berangkat hanya sesudah `TASK ROOT LOCKED` tanpa `TERTAHAN`.
- **Journey** — sesudah akar terkunci, catat alasan lane dan sections yang tidak tertulis di `TASK.md`: `python3 «journey.py» add --taskdir <taskdir> --hop LEAD --teks "<≤2 kalimat, ≤280 karakter: keputusan dan alasannya>"`, lalu berangkatkan gate pertama di giliran yang sama. Aturan journey dan dua titik serah terima rantai (`CONTRACT` → `plan`, `BRIEF` → `architect`): `references/lane-routing-matrix.md` bagian 4a.

---
name: task
description: Dipanggil frontend:lead Phase 7 sesudah lane dan taskdir ditetapkan pada lane FULL_PIPELINE, FAST_FORWARD, REFACTOR_ARCH, atau HOTFIX_MINOR - perumusan akar rantai TASK.md berisi kriteria sukses dan batas kerja, ditulis sebelum satu pun gate hilir berangkat
user-invocable: false
---

## THE IRON LAW

- Tulis `TASK.md` sebelum satu pun gate hilir berangkat — FLOW, UI, CONTRACT, dan brief adalah turunannya.
- Akarkan `## Description` pada minimal satu `file:baris` dari `evidence`, bukan pada parafrase `request`.
- Sebut alat ukur pada tiap success criteria dan buang butir tanpa alat ukur.
- Berhenti begitu tiap permukaan yang diminta punya satu butir pemikul; butir yang menambah permukaan baru dihapus.
- Dilarang menyentuh `src/`, menulis FLOW/UI/CONTRACT/brief, atau mengubah `TASK.md` yang sudah ada.
- Kunci akar lewat `chain.py root` sebelum mengembalikan kendali ke `frontend:lead`: `base_commit` dan kejadian `akar` di `## Riwayat Rantai`, tanpa commit — dokumen taskdir diabaikan git dan dicerminkan ke nataflow (Langkah 24).

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/task/scripts/check_preconditions.py --taskdir <taskdir> --lane <lane> --sections <sections> [--finding-source <path>] [--ticket-source <path>]` — `--sections -` untuk `HOTFIX_MINOR`.
2. `PASS` (10/10 checks) → lanjut ke Workflow. `FAIL` → hentikan dan remediasi butir gagal: `frontenddev/docs/` masih ter-track git (check 10, `MIGRASI`) → kembali ke `frontend:lead` untuk prosedur migrasi; taskdir tidak sah, atau slug sudah dipakai taskdir lain (check 9) → kembali ke `frontend:lead` Phase 5 (sufiks `-2`); profil hilang → `frontend:profile`; `TASK.md` sudah ada → serahkan ke lead tanpa menimpanya; pasangan `lane`/`sections` tidak sah (`HOTFIX_MINOR` ⇔ kosong; `FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `architecture`; `FULL_PIPELINE` memuat `flow` atau `ui`) → kembalikan ke lead, jangan dikoreksi sendiri; `finding_source` tidak ada atau belum ter-commit → laporkan ke user; template hilang → pulihkan berkas plugin; working tree kotor → laporkan ke user, jangan di-stash sendiri; `ticket_source` tidak `READY` atau disunting sesudah approve (check 8) → hentikan dan kembalikan ke lead, yang mengembalikannya ke `analyst:spec`. `WARN` check 10 (`.claude/nataflow.json` tidak ada) → sebut ke user sekali bahwa dokumen taskdir hanya tersimpan di disk ini, lalu lanjut.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — path taskdir lead; wajib cocok pola `frontenddev/docs/<YYMMDDhhmm>-<slug>`.
- `lane` — enum — `[REQUIRED]` — `FULL_PIPELINE` | `FAST_FORWARD` | `REFACTOR_ARCH` | `HOTFIX_MINOR`. Lane tanpa taskdir (`PROFILE`, `EXPLORE_FACT`, `REVIEW_AUDIT`) tidak pernah memanggil skill ini.
- `sections` — list — `[REQUIRED]` — cakupan dokumen hulu dari lead Phase 4 (`flow`, `ui`, `architecture`, atau kosong). Dimateraikan di frontmatter dan menentukan hop ledger `## Chain`.
- `request` — string — `[REQUIRED]` — permintaan user sebagai bahan mentah; dilarang disalin utuh ke `## Description`.
- `evidence` — list — `[REQUIRED]` — minimal satu `file:baris` hasil sapuan lead atau laporan `code-explorer`. Fitur baru tanpa berkas eksisting memakai titik sambungnya: tabel rute, navigator, atau feature root tetangga yang ditunjuk `surface-map.md` profil. Daftar kosong menghentikan skill.
- `clarification` — list — default `[]` — pasangan tanya-jawab lead Phase 7; sumber utama `## Out of Scope`.
- `finding_source` — string — default `""` — path berkas temuan review ad-hoc (`frontenddev/reviews/<berkas>.md`) bila akar berangkat dari temuan; menyalakan Phase 3 butir 5. Temuan `REVIEW.md` rantai sendiri diperbaiki di taskdir yang sama, bukan lewat akar baru.
- `finding_ids` — list — default `[]` — ID temuan terpilih. Kosong padahal `finding_source` terisi → seluruh temuan `PLANNED` di berkas itu.
- `ticket_source` — string — default `""` — path `TICKET.md` `READY` analyst saat akar berangkat dari tiket (lead `## Parameter`); menyalakan Phase 3 butir 6. Dilarang disimpulkan dari isi `request`.

## Workflow

### Phase 1 — Penyerapan Framing Lead

1. Serap `lane`, `sections`, slug, dan kesepakatan cakupan Phase 7 dari handoff lead; `lane` dan `sections` ditulis persis ke frontmatter.
2. Petakan tiap `evidence` ke berkas nyata; buang rujukan yang tidak mengarah ke berkas yang ada dan hentikan bila tak ada sisa.
3. Turunkan judul H1 berformat `<Fitur> — <jenis kerja>` dari slug (maksimal 8 kata, tanpa path).

### Phase 2 — Perumusan Description Berbukti

Rumuskan 2–4 kalimat keputusan definitif:

1. Nyatakan target perubahan perilaku layar, alur, atau layer yang diminta.
2. Sertakan kondisi kode saat ini dengan minimal satu `file:baris` valid dari `evidence`.
3. Tulis hanya keputusan target saat ini; dilarang riwayat atau kronologi komparatif.
4. Batasi pada tingkat masalah — perjalanan layar, mockup, DTO, query key, dan layer shape milik `FLOW.md`, `UI.md`, dan `CONTRACT.md`.

### Phase 3 — Derivasi Success Criteria

Susun 1–7 butir berformat `- [ ] **SC-{n}**: <hasil terukur> — verifikasi: <alat ukur>`, bernomor urut dari `SC-1`. Jumlahnya ditentukan cakupan, bukan plafon.

| Lane | Sumber kriteria |
|---|---|
| `FULL_PIPELINE` | Tiap layar, rute, atau aksi pengguna baru yang diminta — satu butir per permukaan |
| `FAST_FORWARD` | Data atau mutasi baru yang dikonsumsi, dinamai dari layar penampilnya |
| `REFACTOR_ARCH` | Layer target terbentuk dan perilaku layar yang disebut `evidence` tidak berubah |
| `HOTFIX_MINOR` | Perilaku pada `evidence` terkoreksi |

| Alat ukur sah | Bentuk |
|---|---|
| `test` | test bernama (berkas atau kasus) hijau |
| `diff` | perubahan pada berkas bernama |
| `typecheck` / `lint` / `build` | perintah `commands.md` profil bersih relatif baseline |
| `QA manual:` | rute atau layar, aksi, dan hal yang diamati — untuk kriteria visual atau interaktif yang tidak dapat dibuktikan diff |

1. Pasangkan tiap butir dengan satu alat ukur sah. Dilarang alat ukur subjektif ("review manual", "terlihat bagus").
2. **Sumber kriteria tidak pernah dokumen yang belum terbit.** Turunkan butir dari permukaan yang terbukti di `evidence` beserta perubahan yang diminta `request`. Butir yang hanya menyebut dokumen ("seluruh AC CONTRACT tertutup") dihapus — `CONTRACT.md` adalah turunan akar ini, bukan alat ukurnya.
3. Cantumkan nama layar, rute, komponen, state, teks, atau angka spesifik. Tolak kata sifat tanpa ambang.
4. **Uji kecukupan**: butir yang memperkenalkan permukaan di luar `request` dan `evidence` dihapus. Angka 7 plafon, bukan target.
5. **Akar dari temuan**: `finding_source` terisi → sebelum menulis SC, buka `file:baris` tiap temuan terpilih. Temuan yang kodenya sudah berubah (pelanggarannya tak lagi ada) ditandai `> Status: OBSOLETE <YYYY-MM-DD>` di berkas asal dan **tidak** masuk `findings`; seluruhnya OBSOLETE → jangan tulis `TASK.md`; commit berkas asal saja (`docs(review): tandai temuan OBSOLETE`, path eksplisit) dan laporkan ke lead bahwa tidak ada kerja tersisa. Sisanya: tulis frontmatter `finding_source` dan `findings`, dan tiap temuan memikul **tepat satu** butir `SC-{n}` yang menyebut ID-nya beserta `file:baris` temuan itu; alat ukurnya ditambah `> Status: FIXED atas <ID> di <finding_source>`. Dilarang menggabungkan dua temuan ke satu butir maupun memecah satu temuan.
6. **Akar dari tiket analyst**: `ticket_source` terisi → baca kartu `TICKET.md` (H1 sampai akhir `## Lampiran`). Tiap `AC-{n}` kartu dirujuk sebagai `TAC-{n}` dan wajib disebut **minimal satu** butir `SC-{n}`, atau tercatat di `## Out of Scope` sebagai `- TAC-{n} <ringkas> — <alasan: porsi backend | ditunda | tiket terpisah>`. Tulis frontmatter `ticket_source:`. Kalimat Given/When/Then tiket dilarang disalin apa adanya sebagai SC — SC tetap menamai layar, rute, atau aksi, dan `TAC-{n}` ditulis di prosa hasil. Tiket `type: TECH`: AC-nya sudah teknis dan membawa `— verifikasi:`, jadi alat ukurnya boleh diadopsi sebagai alat ukur SC; tiap `TC-{n}` (batasan) dijaga minimal satu SC atau dinyatakan di `## Out of Scope` beserta alasannya, dan `TD-{n}` (keputusan) dihormati `contract` tanpa ditanyakan ulang.

### Phase 4 — Out of Scope, Penulisan & Penguncian

1. Tulis minimal satu butir `## Out of Scope` berformat `- <yang tidak dikerjakan> — <alasan>` dari empat sumber: modul bersinggungan di luar cakupan, opsi yang ditolak di `clarification`, isu eksplorasi yang ditunda, dan `TAC-{n}` tiket yang bukan porsi taskdir ini (Phase 3 butir 6). Bila keempatnya nihil, tulis batas feature root.
2. Baca `templates/task-template.md` bagian 1, isi placeholder, tulis ke `{taskdir}/TASK.md` dengan `status: ACTIVE`, `lane`, dan `sections` — tanpa baris ledger.
3. **Ledger**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py init --taskdir <taskdir>`; skrip menulis `## Chain` tepat sesuai `sections`. Dilarang mengetik baris ledger dengan tangan.
4. **Self-test akar**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/task/scripts/validate_task.py --taskdir <taskdir>` untuk butir mekanis (1–4, 6, 7, 9), lalu nilai sendiri butir 5 dan 8 bagian 2 template. Satu butir gagal → perbaiki `TASK.md`, ulangi dari butir 2.
5. **Kunci akar**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py root --taskdir <taskdir>`. Skrip menjalankan ulang `validate_task.py`, menolak `frontenddev/docs/` yang masih ter-track, lalu menulis `base_commit` = `HEAD` dan kejadian `akar` (lane, sections, sidik akar). Dilarang men-stage atau meng-commit `TASK.md`. `<finding_source>` yang ditandai `OBSOLETE` adalah dokumen tingkat repo: commit tersendiri `docs(review): tandai temuan OBSOLETE` dengan path eksplisit.
6. Akar terkunci → jalankan prosedur `lead/references/nataflow-sync.md` (`--taskdir <taskdir>`) di main loop; segmennya masuk baris penutup. `nataflow GAGAL` tidak membatalkan akar.
7. Catat `base_commit` dan kembalikan kendali ke `frontend:lead`.

## Guardrails

- **AKAR, BUKAN DESAIN**: dilarang menulis perjalanan layar, mockup, cabang state, DTO, query key, layer shape, atau pemecahan unit. Begitu dokumen butuh sub-heading di luar empat yang ditetapkan, isinya milik gate hilir.
- **TASK.md EKSISTING TAK TERSENTUH**: skill ini hanya menulis berkas yang belum ada. Pergeseran `lane`/`sections` hanya lewat `chain.py escalate` dan pencentangan ledger hanya lewat `chain.py approve`/`reopen` — wewenang `frontend:lead` dan gate pemilik hop (`lead/references/lane-routing-matrix.md` bagian 3).
- **NOL SENTUHAN KODE**: dilarang menulis di luar `{taskdir}/TASK.md` — kecuali baris `> Status: OBSOLETE` di `finding_source` — menjalankan build atau test, dan mendispatch subagent.
- **GIT TERBATAS**: dilarang `git push`, `git merge`, `git rebase`, staging wildcard (`git add .` atau `git add -A`), dan men-stage dokumen taskdir.
- **CUKUP ITU BERHENTI**: dilarang menambah butir "sekalian" (a11y audit, animasi, refactor tetangga, analytics) yang tak disebut `request` maupun `evidence`, atau memekarkan `## Out of Scope` jadi rencana kerja berikutnya.
- **RATIONALIZATION PREVENTION**: dilarang menyalin `request` ke `## Description`, mengosongkan `## Out of Scope` ("scope-nya kecil"), memakai `QA manual:` untuk hal yang dapat dibuktikan test, atau menunda penguncian menunggu approval — `TASK.md` tidak mengenal gerbang approval.

## Output [REQUIRED]

Self-test 9/9 dan akar terkunci → tutup satu baris: `### TASK ROOT LOCKED — <taskdir>/TASK.md @ base <sha7> · status ACTIVE · lane <lane> · hop <daftar> · Uji Akar 9/9 lolos · nataflow <segmen>`. Selain itu, sajikan:

```markdown
### TASK ROOT LOCKED — TERTAHAN
- **Path**    : frontenddev/docs/<YYMMDDhhmm>-<slug>/TASK.md · status ACTIVE
- **Uji Akar**: gagal — <butir yang jatuh beserta alasannya> | 9/9 lolos
- **Kunci**   : GAGAL — <pesan chain.py root> | base <sha7>
```

Kriteria dan bukti sudah terkunci di `TASK.md` — dilarang menyalinnya ke laporan. Tutup satu baris: `kembali ke frontend:lead | Taskdir: <path> | Akar: TASK.md @ <base sha7 | belum terkunci>`.

## Failure path

1. **Taskdir tak sah**: hentikan, minta lead memprovisi. Dilarang membuat direktori sendiri.
2. **TASK.md sudah ada**: hentikan tanpa menimpa, laporkan path dan `status`-nya ke lead — termasuk akar yang belum terkunci: penguncian ulangnya milik lead (`chain.py root` `PASS` → terkunci; validator `FAIL` → user yang memutuskan).
3. **Bukti menggantung**: tak satu pun `evidence` mengarah ke berkas nyata → minta lead mendispatch `code-explorer`. Dilarang mengarang `file:baris`.
4. **Kriteria tak terukur**: nol butir terukur tersisa → laporkan butir gugur dan minta klarifikasi lewat lead Phase 7. Dilarang mengganti butir gugur dengan butir baru demi jumlah.
5. **Penguncian gagal**: `chain.py root` `FAIL` (validator, `MIGRASI`, repo tanpa commit) → pertahankan `TASK.md` di disk, laporkan `Kunci: GAGAL` plus pesan skrip apa adanya, serahkan ke lead — lead menjalankan ulang `chain.py root` sesudah penyebabnya beres.

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Tulis Success Criteria sebagai kotak centang `- [ ]` ber-ID `SC-{n}` — hilir merujuk nomornya, bukan prosanya.
- Sebut nama lane dan status persis sesuai enum lead.

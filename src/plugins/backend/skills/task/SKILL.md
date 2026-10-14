---
name: task
description: Dipanggil backend:analyst pada lane planning, atau gerbang backend:tech-lead pada lane DEFECT_RCA dan backfill EXEC_BRIEF - perumusan akar rantai TASK.md berisi kriteria sukses dan batas kerja, ditulis sebelum satu pun skill hilir berangkat
user-invocable: false
---

## THE IRON LAW

- Tulis `TASK.md` sebelum satu pun skill hilir berangkat — BRD, PRD, dan brief adalah turunannya.
- Akarkan `## Description` pada minimal satu `file:line` dari `evidence`, bukan pada parafrase `request`.
- Sebut alat ukur pada tiap success criteria — diff, test, atau artefak bernama — dan buang butir tanpa alat ukur.
- Berhenti begitu tiap permukaan yang diminta punya satu butir pemikul; butir yang menambah permukaan baru dihapus.
- Dilarang menyentuh `src/`, menulis BRD/PRD/brief, atau mengubah `TASK.md` yang sudah ada.
- Kunci akar lewat `doc_seal.py root` (`base_commit`) sebelum mengembalikan kendali ke gerbang; `TASK.md` tidak di-commit — dokumen taskdir diabaikan git dan dicerminkan ke nataflow.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/task/scripts/check_preconditions.py --taskdir <taskdir> --lane <lane> [--chain <chain>] [--ticket-source <ticket_source>]`. Hilangkan `--chain` pada lane `DEFECT_RCA`/`EXEC_BRIEF`.
2. `PASS` (7/7 checks) → lanjut ke Workflow. Baris `[PERINGATAN]` di atas hasil (JSON `peringatan`: `.claude/nataflow.json` tidak ada) tidak menahan: sebut sekali ke user bahwa dokumen taskdir hanya tersimpan di disk ini, lalu lanjut. `FAIL` → hentikan dan remediasi butir gagal: taskdir belum sah → minta alokasi ke `backend:tech-lead`; profil atau commit convention belum lengkap → `backend:profile`; `TASK.md` sudah ada → serahkan ke gerbang; `chain` di luar enum atau tak selaras dengan `lane` → kembalikan ke `backend:analyst`; working tree kotor → bersihkan dulu; `ticket_source` tidak `READY` atau disunting sesudah approve (check 7) → hentikan dan kembalikan ke gerbang, yang mengembalikannya ke `analyst:spec`.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — path taskdir gerbang; wajib cocok pola `backenddev/docs/<YYMMDDhhmm>-<slug>/`.
- `lane` — enum — `[REQUIRED]` — lane terminal rantai; satu dari 4 lane tabel Fase 3 (`PRD_CONVERSION` | `DIRECT_BRIEF` | `DEFECT_RCA` | `EXEC_BRIEF`). Tidak ada lane hop antara: kriteria akar mengukur hasil akhir rantai, bukan keberadaan dokumen antara. Perbaikan temuan tidak punya lane sendiri — akarnya berdiri di salah satu dari dua lane planning seperti permintaan kerja lain, dan `finding_source` yang menandai asal-usulnya.
- `chain` — enum — `[OPTIONAL]` — `BRD_PRD_BRIEF` | `PRD_BRIEF` | `BRIEF` dari `backend:analyst`; penentu isi ledger `## Chain`. Kosong pada lane non-planning (`DEFECT_RCA`, `EXEC_BRIEF`) — seksi `## Chain` tidak ditulis.
- `risk` — enum — `[REQUIRED]` — `BREAKING` | `MAJOR` | `MINOR` | `-`; nilai `-` hanya untuk lane non-mutasi kode.
- `request` — string — `[REQUIRED]` — permintaan user sebagai bahan mentah; dilarang disalin utuh ke `## Description`.
- `evidence` — list — `[REQUIRED]` — minimal satu `file:line` hasil eksplorasi gerbang; daftar kosong menghentikan skill.
- `clarification` — list — default `[]` — pasangan tanya-jawab gerbang; sumber utama `## Out of Scope`.
- `finding_source` — string — default `""` — path berkas temuan asal (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`) saat akar berangkat dari temuan terpilih; menyalakan Fase 3 butir 6. Kosong pada permintaan kerja biasa; dilarang disimpulkan dari isi `request`.
- `ticket_source` — string — default `""` — path `TICKET.md` `READY` analyst saat akar berangkat dari tiket (`tech-lead/references/gate-scope.md` bagian 4 B-2); menyalakan Fase 3 butir 7. Dilarang disimpulkan dari isi `request`.

## Workflow

### Fase 1 — Penyerapan Framing Gerbang

1. Serap enam slot handoff gerbang: Target Skill, Taskdir, File Scope, Risk Level, Acceptance Criteria, Stop Conditions.
2. Baca `commit_convention` dan `base_branch` dari `.claude/profile/backenddev/index.json` untuk Fase 5.
3. Petakan tiap `evidence` ke simbol yang disebutnya; buang rujukan yang tidak mengarah ke berkas nyata dan hentikan bila tak ada sisa.
4. Turunkan judul H1 berformat `<Domain> — <jenis kerja>` dari slug taskdir (maksimal 8 kata, tanpa path).

### Fase 2 — Perumusan Description Berbukti

Rumuskan 2–4 kalimat keputusan teknis definitif:

1. Nyatakan target perubahan perilaku sistem atau artefak yang dibuat.
2. Sertakan kondisi kode saat ini dengan minimal satu `file:line` valid dari `evidence`.
3. Tulis hanya keputusan target saat ini; dilarang riwayat atau kronologi komparatif ("kemarin X sekarang Y").
4. Tolak rumusan yang memparafrase `request`; tulis ulang dari fakta kode terverifikasi.
5. Batasi pada tingkat masalah teknis — aktor, business rule, skema DTO, endpoint, dan diagram state milik `BRD.md` dan `PRD.md`.

### Fase 3 — Derivasi Success Criteria per Lane

Susun 1–7 butir berformat `- [ ] **SC-{n}**: <hasil terukur> — verifikasi: <alat ukur yang sah>`, bernomor urut dari `SC-1`. Jumlahnya ditentukan cakupan, bukan plafon: permintaan berpermukaan tunggal berakhir di satu butir, dan menambah butir agar terlihat lengkap gagal di butir 5 di bawah.

| Lane | Sumber kriteria | Alat ukur yang sah |
|---|---|---|
| `PRD_CONVERSION` | Perubahan perilaku sistem yang diminta user, satu butir per permukaan yang terbukti di `evidence` | Test bernama pemikul permukaan itu hijau (mis. `TestCancelPaidOrder`), atau diff berkas permukaannya — sebut permukaannya (endpoint, transisi, atau aturan bernama) di butir SC-nya. Dilarang menyebut `AC-{n}`, `PRD.md`, atau `BRD.md`: keterlacakan SC→AC ditagih kolom `Akar` PRD (predikat G2 `analyst`), bukan di sini |
| `DIRECT_BRIEF` | Perilaku pada `evidence` terkoreksi | Diff berkas target plus test regresi hijau |
| `DEFECT_RCA` | Gejala terobservasi tervalidasi hilang | `RCA.md` `ROOT_CAUSE_CONFIRMED` plus reproduksi gagal |
| `EXEC_BRIEF` | Gabungan Acceptance Criteria brief `READY` | Gerbang verifikasi penutup hijau plus `REVIEW.md` |

1. Pasangkan tiap butir dengan alat ukur sah pada tabel; buang atau pecah butir tanpa alat ukur pasti. Dilarang alat ukur subjektif seperti "review manual".
2. **Sumber kriteria tidak pernah dokumen yang belum terbit.** Turunkan tiap butir dari permukaan yang terbukti di `evidence` beserta perubahan perilaku yang diminta `request`, lalu namai permukaannya (endpoint, transisi status, aturan) di butirnya. Butir yang hanya menyebut nama dokumen ("seluruh AC PRD tertutup") dihapus, bukan dicarikan permukaan susulan.
   > Rasional: `references/rationale.md` R1.
3. Gabungkan kriteria tumpang tindih pada `EXEC_BRIEF` jadi satu butir; hitung dari capaian fungsional, bukan jumlah brief.
4. Cantumkan nama entitas, threshold numerik, atau status spesifik. Tolak kata sifat tanpa ambang ukur ("lebih cepat", "optimal").
5. **Uji kecukupan.** Tiap butir berakar pada permukaan yang disebut `request` atau terbukti di `evidence`; yang memperkenalkan permukaan di luar keduanya dihapus, bukan dicarikan akar susulan. Berhenti begitu tiap permukaan yang diminta punya satu butir pemikul — angka 7 adalah plafon, bukan target.
6. **Akar yang berangkat dari temuan.** `finding_source` terisi → tiap temuan terpilih memikul **tepat satu** butir `SC-{n}` yang menyebut ID temuannya (`P1-1`, `P2-3`) beserta `file:line` yang disebut temuan itu, dan alat ukurnya ditambah `baris > Status: FIXED atas <ID temuan> di <finding_source>` di samping alat ukur lane-nya. `finding_source` = `{taskdir}/REVIEW.md` → alat ukur tambahannya `ID temuan tidak muncul di REVIEW.md putaran berikutnya`, bukan penanda `FIXED`: `REVIEW.md` ditulis ulang reviewer tiap putaran, sehingga penanda di dalamnya hilang sendiri. Klausa ini berlaku di atas kolom alat ukur lane mana pun, `PRD_CONVERSION` termasuk: temuan yang naik jadi rantai ber-PRD tetap wajib ditandai di berkas asalnya, dan tanpa penandaan itu ia terpilih ulang di batch berikutnya lalu dikerjakan dua kali. Dilarang menggabungkan dua temuan ke satu butir maupun memecah satu temuan jadi beberapa butir — jumlahnya sudah dikunci seleksi gerbang berplafon tujuh (`tech-lead/references/gate-scope.md` bagian 6).
7. **Akar dari tiket analyst.** `ticket_source` terisi → baca kartu `TICKET.md` (H1 sampai akhir `## Lampiran`). Tiap `AC-{n}` kartu dirujuk sebagai `TAC-{n}` dan wajib disebut **minimal satu** butir `SC-{n}`, atau tercatat di `## Out of Scope` sebagai `- TAC-{n} <ringkas> — <alasan: porsi frontend | ditunda | tiket terpisah>`. Kalimat Given/When/Then tiket dilarang disalin apa adanya sebagai SC — SC tetap menamai permukaan teknis (endpoint, transisi, aturan), dan `TAC-{n}` ditulis di prosa hasil, bukan di alat ukur. Tiket `type: TECH`: AC-nya sudah teknis dan membawa `— verifikasi:`, jadi alat ukurnya boleh diadopsi sebagai alat ukur SC bila sah untuk lane ini; tiap `TC-{n}` (batasan) dijaga minimal satu SC atau dinyatakan di `## Out of Scope` beserta alasannya — tidak ditagih skrip, tetapi `TC-{n}` yang hilang diam-diam adalah batasan yang dilanggar.

### Fase 4 — Penetapan Out of Scope

Tulis minimal satu butir berformat `- <yang tidak dikerjakan> — <alasan>` dari 4 sumber: modul bersinggungan di luar File Scope gerbang; opsi yang disingkirkan pada `clarification`; isu eksplorasi yang ditunda; dan `TAC-{n}` tiket yang bukan porsi taskdir ini (Fase 3 butir 7). Daftar kosong dilarang — bila keempatnya nihil, tulis batas modul dari File Scope.

### Fase 5 — Penulisan & Penguncian Akar

1. Baca `templates/task-template.md` bagian 1, isi placeholder dari Fase 1–4, tulis ke `{taskdir}/TASK.md` dengan `status: ACTIVE`.
2. `chain` terisi: tulis frontmatter `chain:` bernilai persis itu dan seksi `## Chain` berisi tepat hop chain tersebut, seluruhnya belum tercentang, mengikuti bagian 2 `analyst/references/chain-rules.md`. `chain` kosong: hilangkan baris frontmatter dan seksi itu sepenuhnya. `ticket_source` terisi: tulis frontmatter `ticket_source:` bernilai persis path itu; kosong: hilangkan barisnya.
3. **Self-test akar**: sebelum butir 4 berangkat, jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind task --taskdir <taskdir> --fresh [--finding-source <finding_source>]`. `FAIL` → perbaiki seluruh pelanggaran satu keluaran, lalu jalankan sekali lagi. Butir `MANUAL` (T3b, T4, T9) dinilai sendiri memakai predikat bagian 2 berkas itu; rumah kanonik predikatnya di sana, dilarang ditulis ulang di sini.
4. Kunci akar: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/doc_seal.py root --taskdir <taskdir>`. Skrip menulis `base_commit` = sha `HEAD` (branch kerja taskdir) ke frontmatter `TASK.md`; rentang kode rantai dihitung sejak titik ini. Dilarang men-stage atau meng-commit `TASK.md` dan mengisi `base_commit` dengan tangan.
5. **Sinkron nataflow**: akar terkunci → jalankan prosedur `tech-lead/references/nataflow-sync.md` (`--taskdir <taskdir>`) di main loop, sehingga `TASK.md` tercermin seketika di lane mana pun. Segmennya masuk baris penutup; `GAGAL` tidak membatalkan akar. `Kunci: GAGAL` → lewati butir ini: payload menolak akar tanpa `base_commit`.
6. Catat `base_commit` (7 digit) dan kembalikan kendali ke pemanggilnya — `backend:analyst` pada lane planning, `backend:tech-lead` pada lane lainnya.

## Guardrails

- **AKAR, BUKAN ANALISIS**: dilarang menulis aktor, business rule, kontrak API, skema DTO, atau pemecahan unit kerja. Batas mekanisnya — begitu dokumen butuh sub-heading di luar empat yang ditetapkan (tabel `## Counters` penutup milik `analyst/scripts/chain_counters.py` bukan isi dokumen), isinya milik `business-analysis`, `system-analysis`, atau `plan`.
- **TASK.md EKSISTING TAK TERSENTUH**: amandemen `## Success Criteria`/`## Out of Scope`, pembaruan `risk` saat eskalasi dinamis, dan backfill taskdir lama adalah wewenang gerbang; skill ini hanya menulis berkas yang belum ada. Permintaan amandemen dari skill hop tidak pernah sampai ke gerbang langsung — ia mengalir lewat kanal `backend:analyst` Fase 4a supaya keputusan lingkupnya diputuskan user satu kali (`analyst/references/chain-rules.md` bagian 5). Pencentangan ledger `## Chain` dan penulisan ulangnya saat eskalasi chain adalah wewenang `backend:analyst`, bukan skill ini.
- **NOL SENTUHAN KODE**: dilarang membaca-tulis di bawah `source_root`, menjalankan build atau test, dan membuat berkas di luar `{taskdir}/TASK.md`.
- **GIT TERBATAS**: dilarang `git push`, `git merge`, `git rebase`, `gh pr create`, staging wildcard (`git add .` atau `git add -A`), dan `git add -f` atas `backenddev/docs/`.
- **CUKUP ITU BERHENTI**: akar mengukur apa yang diminta, bukan apa yang sebaiknya ada. Dilarang menulis kriteria atas permukaan yang tak disebut `request` maupun `evidence`, menambah butir "sekalian" (log, metrik, audit trail, hardening, refactor tetangga) atau butir antisipatif ("nanti pasti butuh"), menambah butir demi mendekati plafon 7 ("biar lengkap"), dan memekarkan `## Out of Scope` jadi daftar rencana kerja berikutnya — seksi itu memagari, bukan menjadwalkan.
- **RATIONALIZATION PREVENTION**: dilarang menyalin `request` ke `## Description` ("permintaannya sudah jelas"), melewati Fase 3 ("kriterianya sudah ada di brief"), mengosongkan `## Out of Scope` ("scope-nya kecil"), atau menunda penguncian akar menunggu approval — TASK.md tidak mengenal gerbang approval.

## Output [REQUIRED]

Tulis `{taskdir}/TASK.md` mengikuti `templates/task-template.md`. Uji akar 9/9 dan akar terkunci → tutup satu baris tanpa blok: `### TASK ROOT LOCKED — <taskdir>/TASK.md @ <base_commit 7 digit> · status ACTIVE · Uji Akar 9/9 lolos · Nataflow <segmen>`. Selain itu, sajikan:

```markdown
### TASK ROOT LOCKED — TERTAHAN
- **Path**    : backenddev/docs/<YYMMDDhhmm>-<slug>/TASK.md · status ACTIVE
- **Uji Akar**: gagal — <butir yang jatuh beserta alasannya> | 9/9 lolos
- **Kunci**   : GAGAL — <pesan doc_seal.py> | <base_commit 7 digit>
- **Nataflow**: <segmen> | —
```

`Uji Akar` dan `Kunci` wajib muncul di kedua bentuk: `backend:analyst` Fase 2 butir 2 membacanya sebagai predikat masuk hop pertama. Lane, chain, ledger hop, kriteria, dan bukti `file:baris` penopang `## Description` sudah terkunci di `TASK.md` — dilarang menyalinnya ke laporan. Tutup satu baris: `kembali ke <backend:analyst | backend:tech-lead> | Taskdir: <path> | Akar: TASK.md @ <base_commit 7 digit | belum terkunci>`.

## Failure path

1. **Taskdir tak sah**: path tidak ada atau tidak cocok pola → hentikan, minta gerbang memprovisi. Dilarang membuat direktori sendiri.
2. **TASK.md sudah ada**: hentikan tanpa membaca isi, laporkan path dan `status` frontmatter, serahkan amandemen ke gerbang.
3. **Bukti menggantung**: tak satu pun `evidence` mengarah ke berkas nyata → hentikan, minta eksplorasi ulang lewat `code-explorer`. Dilarang mengarang `file:line`.
4. **Kriteria tak terukur**: nol butir terukur tersisa → laporkan butir gugur dan minta klarifikasi tambahan dari gerbang. Butir yang gugur dilaporkan apa adanya; dilarang menggantinya dengan butir baru demi memenuhi jumlah.
5. **Kunci gagal**: `doc_seal.py root` FAIL (repo tanpa commit, `backenddev/docs/` masih ter-track, atau `base_commit` tidak sah) → pertahankan berkas di disk, laporkan `Kunci: GAGAL` plus pesan skrip, serahkan penguncian ke gerbang.
6. **Lane tak dikenal**: `lane` di luar 4 enum Fase 3 → hentikan dan laporkan nilai terbaca. Dilarang menebak lane terdekat.
7. **Chain tak selaras**: `chain` di luar 3 enum, atau lane terminalnya tidak cocok dengan kolom keempat matriks bagian 1.3 `analyst/references/chain-rules.md` → hentikan dan kembalikan ke `backend:analyst`. Dilarang menurunkan chain sendiri dari `lane`.

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Tulis Success Criteria sebagai kotak centang `- [ ]` ber-ID `SC-{n}` — hilir merujuk nomornya, bukan prosanya.
- Sebut nama lane, risk level, dan status persis sesuai enum gerbang.

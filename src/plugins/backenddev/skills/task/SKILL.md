---
name: task
description: Dipanggil backenddev:analyst pada lane planning, atau gerbang backenddev:tech-lead pada lane DEFECT_RCA dan backfill EXEC_BRIEF - perumusan akar rantai TASK.md berisi kriteria sukses dan batas kerja, ditulis sebelum satu pun skill hilir berangkat
user-invocable: false
---

## THE IRON LAW

- Tulis `TASK.md` sebelum satu pun skill hilir berangkat — BRD, PRD, dan brief adalah turunannya.
- Akarkan `## Description` pada minimal satu `file:line` dari `evidence`, bukan pada parafrase `request`.
- Sebut alat ukur pada tiap success criteria — diff, test, atau artefak bernama — dan buang butir tanpa alat ukur.
- Berhenti begitu tiap permukaan yang diminta punya satu butir pemikul; butir yang menambah permukaan baru dihapus.
- Dilarang menyentuh `src/`, menulis BRD/PRD/brief, atau mengubah `TASK.md` yang sudah ada.
- Kunci berkas dalam satu commit tersendiri sebelum mengembalikan kendali ke gerbang.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/task/scripts/check_preconditions.py --taskdir <taskdir> --lane <lane> --chain <chain>`.
2. `PASS` (6/6 checks) → lanjut ke Workflow. `FAIL` → hentikan dan remediasi butir gagal: taskdir belum sah → minta alokasi ke `backenddev:tech-lead`; profil atau commit convention belum lengkap → `backenddev:profile`; `TASK.md` sudah ada → serahkan ke gerbang; `chain` di luar enum atau tak selaras dengan `lane` → kembalikan ke `backenddev:analyst`; working tree kotor → bersihkan dulu.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — path taskdir gerbang; wajib cocok pola `backenddev/docs/<YYMMDDhhmm>-<slug>/`.
- `lane` — enum — `[REQUIRED]` — lane terminal rantai; satu dari 4 lane tabel Fase 3 (`PRD_CONVERSION` | `DIRECT_BRIEF` | `DEFECT_RCA` | `EXEC_BRIEF`). Tidak ada lane hop antara: kriteria akar mengukur hasil akhir rantai, bukan keberadaan dokumen antara. Perbaikan temuan tidak punya lane sendiri — akarnya berdiri di salah satu dari dua lane planning seperti permintaan kerja lain, dan `finding_source` yang menandai asal-usulnya.
- `chain` — enum — `[OPTIONAL]` — `BRD_PRD_BRIEF` | `PRD_BRIEF` | `BRIEF` dari `backenddev:analyst`; penentu isi ledger `## Chain`. Kosong pada lane non-planning (`DEFECT_RCA`, `EXEC_BRIEF`) — seksi `## Chain` tidak ditulis.
- `risk` — enum — `[REQUIRED]` — `BREAKING` | `MAJOR` | `MINOR` | `-`; nilai `-` hanya untuk lane non-mutasi kode.
- `request` — string — `[REQUIRED]` — permintaan user sebagai bahan mentah; dilarang disalin utuh ke `## Description`.
- `evidence` — list — `[REQUIRED]` — minimal satu `file:line` hasil eksplorasi gerbang; daftar kosong menghentikan skill.
- `clarification` — list — default `[]` — pasangan tanya-jawab gerbang; sumber utama `## Out of Scope`.
- `finding_source` — string — default `""` — path berkas temuan asal (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`) saat akar berangkat dari temuan terpilih; menyalakan Fase 3 butir 6. Kosong pada permintaan kerja biasa; dilarang disimpulkan dari isi `request`.

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
   > Mengapa: pada lane `PRD_CONVERSION`, `BRD.md` dan `PRD.md` belum ada saat skill ini berjalan — keduanya hop hilir dari akar ini. Butir yang mengukur keberadaan dokumen adalah tautologi, dan seluruh keterlacakan hilir (`Akar` PRD, `Fulfills:` brief) kehilangan isinya di atasnya.
3. Gabungkan kriteria tumpang tindih pada `EXEC_BRIEF` jadi satu butir; hitung dari capaian fungsional, bukan jumlah brief.
4. Cantumkan nama entitas, threshold numerik, atau status spesifik. Tolak kata sifat tanpa ambang ukur ("lebih cepat", "optimal").
5. **Uji kecukupan.** Tiap butir berakar pada permukaan yang disebut `request` atau terbukti di `evidence`; yang memperkenalkan permukaan di luar keduanya dihapus, bukan dicarikan akar susulan. Berhenti begitu tiap permukaan yang diminta punya satu butir pemikul — angka 7 adalah plafon, bukan target.
6. **Akar yang berangkat dari temuan.** `finding_source` terisi → tiap temuan terpilih memikul **tepat satu** butir `SC-{n}` yang menyebut ID temuannya (`P1-1`, `P2-3`) beserta `file:line` yang disebut temuan itu, dan alat ukurnya ditambah `baris > Status: FIXED atas <ID temuan> di <finding_source>` di samping alat ukur lane-nya. `finding_source` = `{taskdir}/REVIEW.md` → alat ukur tambahannya `ID temuan tidak muncul di REVIEW.md putaran berikutnya`, bukan penanda `FIXED`: `REVIEW.md` ditulis ulang reviewer tiap putaran, sehingga penanda di dalamnya hilang sendiri. Klausa ini berlaku di atas kolom alat ukur lane mana pun, `PRD_CONVERSION` termasuk: temuan yang naik jadi rantai ber-PRD tetap wajib ditandai di berkas asalnya, dan tanpa penandaan itu ia terpilih ulang di batch berikutnya lalu dikerjakan dua kali. Dilarang menggabungkan dua temuan ke satu butir maupun memecah satu temuan jadi beberapa butir — jumlahnya sudah dikunci seleksi gerbang berplafon tujuh (`tech-lead/references/gate-scope.md` bagian 6).

### Fase 4 — Penetapan Out of Scope

Tulis minimal satu butir berformat `- <yang tidak dikerjakan> — <alasan>` dari 3 sumber: modul bersinggungan di luar File Scope gerbang; opsi yang disingkirkan pada `clarification`; isu eksplorasi yang ditunda. Daftar kosong dilarang — bila ketiganya nihil, tulis batas modul dari File Scope.

### Fase 5 — Penulisan & Penguncian Commit

1. Baca `templates/task-template.md` bagian 1, isi placeholder dari Fase 1–4, tulis ke `{taskdir}/TASK.md` dengan `status: ACTIVE`.
2. `chain` terisi: tulis frontmatter `chain:` bernilai persis itu dan seksi `## Chain` berisi tepat hop chain tersebut, seluruhnya belum tercentang, mengikuti bagian 2 `analyst/references/chain-rules.md`. `chain` kosong: hilangkan baris frontmatter dan seksi itu sepenuhnya.
3. **Self-test akar**: loloskan seluruh butir bagian 2 berkas itu sebelum butir 4 berangkat; satu butir gagal → perbaiki `TASK.md`, ulangi dari butir 1. Rumah kanonik predikatnya di sana, dilarang ditulis ulang di sini.
4. Stage eksplisit `{taskdir}/TASK.md`, lalu commit dengan `commit_convention` profil bersubjek `docs(<slug>): kunci TASK sebagai akar rantai`.
5. Catat SHA commit dan kembalikan kendali ke pemanggilnya — `backenddev:analyst` pada lane planning, `backenddev:tech-lead` pada lane lainnya.

## Guardrails

- **AKAR, BUKAN ANALISIS**: dilarang menulis aktor, business rule, kontrak API, skema DTO, atau pemecahan unit kerja. Batas mekanisnya — begitu dokumen butuh sub-heading di luar empat yang ditetapkan (tabel `## Counters` penutup milik `analyst/scripts/chain_counters.py` bukan isi dokumen), isinya milik `business-analysis`, `system-analysis`, atau `plan`.
- **TASK.md EKSISTING TAK TERSENTUH**: amandemen `## Success Criteria`/`## Out of Scope`, pembaruan `risk` saat eskalasi dinamis, dan backfill taskdir lama adalah wewenang gerbang; skill ini hanya menulis berkas yang belum ada. Permintaan amandemen dari skill hop tidak pernah sampai ke gerbang langsung — ia mengalir lewat kanal `backenddev:analyst` Fase 4a supaya keputusan lingkupnya diputuskan user satu kali (`analyst/references/chain-rules.md` bagian 5). Pencentangan ledger `## Chain` dan penulisan ulangnya saat eskalasi chain adalah wewenang `backenddev:analyst`, bukan skill ini.
- **NOL SENTUHAN KODE**: dilarang membaca-tulis di bawah `source_root`, menjalankan build atau test, dan membuat berkas di luar `{taskdir}/TASK.md`.
- **GIT TERBATAS**: dilarang `git push`, `git merge`, `git rebase`, `gh pr create`, dan staging wildcard (`git add .` atau `git add -A`).
- **CUKUP ITU BERHENTI**: akar mengukur apa yang diminta, bukan apa yang sebaiknya ada. Dilarang menulis kriteria atas permukaan yang tak disebut `request` maupun `evidence`, menambah butir "sekalian" (log, metrik, audit trail, hardening, refactor tetangga) atau butir antisipatif ("nanti pasti butuh"), menambah butir demi mendekati plafon 7 ("biar lengkap"), dan memekarkan `## Out of Scope` jadi daftar rencana kerja berikutnya — seksi itu memagari, bukan menjadwalkan.
- **RATIONALIZATION PREVENTION**: dilarang menyalin `request` ke `## Description` ("permintaannya sudah jelas"), melewati Fase 3 ("kriterianya sudah ada di brief"), mengosongkan `## Out of Scope` ("scope-nya kecil"), atau menunda commit menunggu approval — TASK.md tidak mengenal gerbang approval.

## Output [REQUIRED]

Tulis `{taskdir}/TASK.md` mengikuti `templates/task-template.md`. Uji akar 9/9 dan commit mendarat → tutup satu baris tanpa blok: `### TASK ROOT LOCKED — <taskdir>/TASK.md @ <sha> · status ACTIVE · Uji Akar 9/9 lolos`. Selain itu, sajikan:

```markdown
### TASK ROOT LOCKED — TERTAHAN
- **Path**    : backenddev/docs/<YYMMDDhhmm>-<slug>/TASK.md · status ACTIVE
- **Uji Akar**: gagal — <butir yang jatuh beserta alasannya> | 9/9 lolos
- **Commit**  : GAGAL — <pesan git> | <sha>
```

`Uji Akar` dan `Commit` wajib muncul di kedua bentuk: `backenddev:analyst` Fase 2 butir 2 membacanya sebagai predikat masuk hop pertama. Lane, chain, ledger hop, kriteria, dan bukti `file:baris` penopang `## Description` sudah terkunci di `TASK.md` — dilarang menyalinnya ke laporan. Tutup satu baris: `kembali ke <backenddev:analyst | backenddev:tech-lead> | Taskdir: <path> | Akar: TASK.md @ <sha | belum terkunci>`.

## Failure path

1. **Taskdir tak sah**: path tidak ada atau tidak cocok pola → hentikan, minta gerbang memprovisi. Dilarang membuat direktori sendiri.
2. **TASK.md sudah ada**: hentikan tanpa membaca isi, laporkan path dan `status` frontmatter, serahkan amandemen ke gerbang.
3. **Bukti menggantung**: tak satu pun `evidence` mengarah ke berkas nyata → hentikan, minta eksplorasi ulang lewat `code-explorer`. Dilarang mengarang `file:line`.
4. **Kriteria tak terukur**: nol butir terukur tersisa → laporkan butir gugur dan minta klarifikasi tambahan dari gerbang. Butir yang gugur dilaporkan apa adanya; dilarang menggantinya dengan butir baru demi memenuhi jumlah.
5. **Commit gagal**: working tree kotor di luar taskdir atau `commit_convention` tak terbaca → pertahankan berkas di working tree, laporkan `Commit: GAGAL` plus pesan git, serahkan penguncian ke gerbang.
6. **Lane tak dikenal**: `lane` di luar 4 enum Fase 3 → hentikan dan laporkan nilai terbaca. Dilarang menebak lane terdekat.
7. **Chain tak selaras**: `chain` di luar 3 enum, atau lane terminalnya tidak cocok dengan kolom keempat matriks bagian 1.3 `analyst/references/chain-rules.md` → hentikan dan kembalikan ke `backenddev:analyst`. Dilarang menurunkan chain sendiri dari `lane`.

## STYLE

- Gunakan fase bernomor dan kalimat imperatif aktif tanpa konstruksi bersyarat WHEN/THEN.
- Gunakan Bahasa Indonesia baku dan istilah teknis asli stack.
- Tulis Success Criteria sebagai kotak centang `- [ ]` ber-ID `SC-{n}` — hilir merujuk nomornya, bukan prosanya.
- Sebut nama lane, risk level, dan status persis sesuai enum gerbang.

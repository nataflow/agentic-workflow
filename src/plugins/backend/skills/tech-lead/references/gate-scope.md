# Gate Scope Boundary, Commit Protocols & Dispatch Framing — `tech-lead`

Panduan operasional batasan pemicu gerbang, protokol persetujuan artefak, matriks kepemilikan git commit, dan katalog framing delegasi pada plugin `backend`.

______________________________________________________________________

## 1. Universal Gate Scope & Trigger Boundaries

### Pesan yang Wajib Memicu Gerbang (`tech-lead`):

Setiap pesan user yang meminta pemahaman kode, perubahan perilaku, perbaikan bug, audit, atau dokumentasi:

- **Pertanyaan Kode**: "di mana implementasi X", "siapa yang memanggil service Y", "trace flow endpoint Z". Lewat jalur cepat read-only (`references/explore-fact.md`): tidak menuntut tree bersih, branch, `commands.md`, maupun profil.
- **Sinkron Ulang nataflow**: "sinkron ulang taskdir <slug>", "dorong ulang artefak ke nataflow". Varian re-entry tanpa lane baru (15 B7): Fase 0 `--read-only`, tanpa provisi taskdir, branch, maupun commit, lalu jalankan `nataflow-sync.md` atas taskdir itu (ditambah `--repo-docs` yang diminta user) dan tutup dengan satu baris `SINKRON — <taskdir> · nataflow <segmen>`. Jalan ulang untuk segmen `GAGAL`.
- **Permintaan Perubahan / Fitur / Bugfix**: "tambahkan endpoint baru", "perbaiki race condition di order", "audit module payment".
- **Permintaan Menjalankan Artefak**: "jalankan brief 01", "lanjutkan pengerjaan taskdir <slug>" (apa pun status artefaknya).
- **Susulan di Tengah Sesi**: "sekalian ubah response field A", "jangan lupa tambah log di B".
- **Koreksi di Tengah Eksekusi**: "jangan pakai redis, pakai in-memory cache saja".

Ukuran perubahan kecil bukan alasan melewati gerbang. Subagent yang sedang berjalan dilarang memproses permintaan baru di luar briefnya.

### Empat Pengecualian, dan Hanya Empat:

1. **Jawaban User Memasok Informasi**: Jawaban langsung atas pertanyaan klarifikasi Fase 2 atau entri `## Open questions` pada alur yang rutenya sudah diputuskan.
2. **Pertanyaan Pengetahuan Umum Non-Repo**: Penjelasan konsep umum bahasa atau framework tanpa menyentuh file repo.
3. **Operasi VCS atas Kerja Selesai**: Permintaan murni VCS yang tidak menambah kode baru ("commit perubahan dengan pesan X").
4. **Alur Plugin Lain yang Dipanggil Eksplisit**: Permintaan yang memanggil atau melanjutkan `/analyst:*` atau `/quickdev:*`, termasuk susulan di tengah skill `analyst:*`/`quickdev:*` yang sedang berjalan (elisitasi tiket, `plan/<task>.md`). Kerja itu milik plugin tersebut sampai user sendiri meminta pindah ke gerbang ini. Penanda `.claude/workflow` tanpa kata `backend` membuat hook gerbang ini diam di repo itu.

### Approval Bukan Pengecualian:

Persetujuan user atas `BRD.md` atau `PRD.md` diminta dan diproses `backend:analyst` di dalam fase planning, bukan di gerbang. Gerbang tidak aktif untuk approval dokumen dan tidak memicu hop berikutnya; rantai berlanjut di dalam `analyst` sampai brief `READY` terbit.

______________________________________________________________________

## 2. Artifact Lifecycle & Approval Writing Protocol

Satu artefak melewati **dua** titik commit yang berbeda pemiliknya: draft dikunci penulisnya, approval dikunci `backend:analyst`.

- **Draft Milik Penulis**: `business-analysis` / `system-analysis` menyelesaikan dokumen dalam `status: DRAFT`, menjalankan self-review mandiri (via subagent `brd-reviewer` / `prd-reviewer`), lalu — bila self-review `Approved` — meng-commit draft-nya sendiri sebelum mengembalikan rute ke `analyst`.
- **Approval Milik `analyst`**: Penulis dilarang menulis `status: APPROVED` dalam keadaan apa pun **dan dilarang meminta persetujuan user atas dokumennya sendiri**; gerbang tidak pernah menuliskannya dan tidak pernah memintanya. Satu dokumen karenanya melewati tepat satu gerbang keputusan user, bukan dua. Prosedur lengkapnya — predikat masuk berupa verdict reviewer, penguncian draft yatim, anggaran `## Open questions`, ringkasan eksekutif, `AskUserQuestion`, dan commit approval — adalah rumah kanonik `analyst/references/chain-rules.md` bagian 4.
- **Brief Bebas Approval**: Dokumen `brief-*.md` lahir langsung dengan `status: READY`, dan dikunci `plan` dalam satu commit agregat setelah self-review batch via subagent `brief-reviewer` lolos. Brief tidak pernah memiliki `status: DRAFT` maupun `status: APPROVED`, sehingga hanya melewati satu titik commit.

______________________________________________________________________

## 3. Artifact Commit Ownership Matrix

Setiap artefak ditutup dengan `git commit` di titik ia menjadi keputusan final:

| Artefak | Titik Terjadinya Commit | Pemilik Commit | Format Pesan Commit |
| --- | --- | --- | --- |
| `.claude/profile/backenddev/` | Selesai ditulis / di-refresh | `tech-lead` | `docs: init/refresh backend profile` |
| `.claude/profile/backenddev/` + penghapusan `.claude/profile/<berkas>` yang dipindah `migrate_profile.py` | Selesai MIGRATE | `tech-lead` | `docs: migrate backend profile` |
| `backenddev/docs/<taskdir>/TASK.md` | Uji akar 9/9 lolos | **`task`** | `docs(<slug>): kunci TASK sebagai akar rantai` |
| `backenddev/docs/<taskdir>/TASK.md` saat amandemen gerbang | Amandemen akar disetujui user (`gate-lifecycle.md` bagian 1a) | `tech-lead` | `docs(<slug>): amandemen akar TASK (<pemicu>)` |
| `backenddev/docs/<taskdir>/TASK.md` saat eskalasi chain | Transisi chain dieksekusi | **`analyst`** | `docs(<slug>): eskalasi chain <asal> ke <hasil>` |
| `backenddev/docs/<taskdir>/TASK.md` saat ledger ditutup | Hop `BRIEF` dicentang di Fase 6 langkah 0 | **`analyst`** | `docs(<slug>): tutup ledger chain <enum>` |
| `backenddev/docs/<taskdir>/BRD.md` draft | Self-review `brd-reviewer` BRD lolos | **`business-analysis`** | `docs(spec): draft BRD <slug>` |
| `backenddev/docs/<taskdir>/PRD.md` draft | Self-review `prd-reviewer` PRD lolos | **`system-analysis`** | `docs(spec): draft PRD <slug>` |
| `BRD.md` / `PRD.md` saat `APPROVED` | Saat `status: APPROVED` ditulis `analyst` | **`analyst`** | `docs(spec): approve <BRD\|PRD> <slug>` |
| `backenddev/docs/<taskdir>/brief-*.md` | Self-review `brief-reviewer` BRIEF batch lolos | **`plan`** | `docs(plan): add <N> briefs for <slug>` |
| `backenddev/issues/<file>.md` + `README.md` | Laporan audit selesai ditulis | `tech-lead` | `docs(audit): record findings for <target>` |
| `backenddev/docs/<taskdir>/RCA.md` | Root cause disetujui user / `INCONCLUSIVE` | `tech-lead` | `docs(rca): record root cause for <slug>` |
| `{taskdir}/REVIEW.md` + baris riwayat review di `backenddev/issues/README.md` | Reviewer selesai menilai seluruh rantai | **`code-reviewer`** | `docs(<slug>): add final review report`, dibentuk dari `commit_convention` profil |
| `src/**` + berkas briefnya | Tiap brief selesai atau terblokir | **`code-implementor`** | `commit_message` frontmatter brief |
| `{taskdir}/HALT.md` | Gerbang kompilasi, scope, simbol, atau berkas liar menahan rantai | **`architect`** | `chore(<slug>): tahan rantai di brief-NN (<verdict>)` |
| `{taskdir}/brief-NN-<unit>.md` koreksi `READY → DONE` | Commit brief mendarat tetapi status tertinggal | **`architect`** | `chore(<slug>): koreksi status brief-NN ke DONE (<sha7>)` |
| Penghapusan `{taskdir}/HALT.md` ber-`verdict: SCOPE`/`SYMBOL` | User menerima commit di luar scope | `tech-lead` | `docs(<slug>): cabut HALT brief-NN (scope diterima user)` |
| `BRD.md` / `PRD.md` draft **yatim** | Terdeteksi belum terkunci di Fase 4 `analyst` | **`analyst`** | format pesan penulisnya (`draft <BRD\|PRD>`) |

*Aturan commit penulis artefak*: `business-analysis`, `system-analysis`, dan `plan` meng-commit artefaknya sendiri **hanya** setelah self-review subagent reviewer masing-masing (`brd-reviewer`, `prd-reviewer`, `brief-reviewer`) berstatus `Approved`. Commit itu mengunci **draft** (atau brief `READY`), tidak pernah menulis `status: APPROVED`.

*Aturan tanpa-approval*: commit draft (`BRD`, `PRD`) dan commit agregat brief berangkat begitu self-review reviewer terkait berstatus `Approved`, tanpa menunggu persetujuan user, `analyst`, gerbang, maupun main loop. Penolakan user atas sebuah dokumen tidak pernah membatalkan, menahan, atau me-revert commit yang sudah mendarat — ia hanya menahan `status: APPROVED`. Draft yatim dikunci `analyst` lebih dulu (`analyst/references/chain-rules.md` bagian 4 butir 1).

*Aturan commit penulis kode*: `code-implementor` dan `code-reviewer` mengunci karyanya sendiri begitu pekerjaannya tuntas. `architect` memverifikasi commit itu mendarat dan diff-nya tidak melewati `## File scope`.

*Di luar matriks*: temuan `code-explorer` dikembalikan ke context pendispatch **dan** ditulis ke laci kerja `.explore/` — `backenddev/docs/.explore/<slug>.md` untuk dispatch gerbang, `<taskdir>/.explore/<slug>.md` untuk skill hilir. Laporan gerbang disalin ke laci taskdir sebagai `gate-<slug>.md` di Fase 3 (`gate-lifecycle.md` bagian 1). Isinya catatan penelusuran, bukan keputusan, sehingga tidak pernah di-stage maupun di-commit siapa pun, dan tidak pernah dihitung sebagai working tree kotor oleh gerbang git mana pun.

*Larangan*: `audit` dan `debug` dilarang menjalankan git commit — serahkan artefak ke gerbang untuk dikunci. `code-explorer` tidak memegang `Bash`, sehingga tidak dapat menjalankan git. `Write`-nya dibatasi pada satu path laporan `.explore/` yang ditentukan pendispatch: prompt (`agents/code-explorer.md`) mengunci path persisnya, dan hook PreToolUse `hooks/guard_bash.py` menolak mekanis tiap `Write`/`Edit` explorer di luar `backenddev/docs/[<taskdir>/].explore/*.md`. Seluruh pemilik commit dilarang staging wildcard (`git add .` / `-A`), `git push`, `git merge`, `git rebase`, maupun perpindahan branch.

______________________________________________________________________

## 4. Dispatch Framing Catalog per Lane

Framing wajib memuat: Path Eksplisit, Batas Scope Sempit, Acceptance Criteria di Depan, dan Stop Condition Eksplisit.

### A-0. Lane `DEFECT_RCA` → `debug`

> Buktikan penyebab kegagalan runtime yang muncul pada `GET /api/orders/{id}`. **Taskdir**: `backenddev/docs/2608261400-order-tx-leak/` **Symptom**: stacktrace verbatim yang ditempel user, frame terdalam `internal/order/service.go:104`. **Scope Hint**: `internal/order/`. **Acceptance Criteria**: `RCA.md` terbit dengan 7 seksi wajib, rantai kausal tiap mata rantai bertanda `file:line`, minimal satu hipotesis alternatif terfalsifikasi, `## Regression guard` berisi spesifikasi test bukan berkas test. **Stop Condition**: Tiga siklus hipotesis habis tanpa rantai kausal utuh → terbitkan `INCONCLUSIVE`, dilarang menebak. Dilarang menyentuh `src/` atau menulis brief.

### A. Lane `PLANNING` → `analyst` (kerja terisolasi, kontrak pasti)

> Rancang dan terbitkan brief untuk memperbaiki validasi kuota di `internal/order/service.go` mengikuti pattern `internal/stock/validator.go`. **Taskdir**: `backenddev/docs/2608221000-order-quota-fix/` **Risk Level**: `MINOR`. **Evidence**: `internal/order/service.go:142`, `internal/stock/validator.go:31`. **File Scope**: `internal/order/`. **Acceptance Criteria**: `TASK.md` terkunci beserta ledger `## Chain`, seluruh brief terbit `READY` dan ter-commit, `Fulfills:` menutup 100% `SC-{n}`. **Stop Condition**: Pemicu eskalasi chain aktif dua kali → BERHENTI dan kembalikan klasifikasi ke gerbang.

### B. Lane `PLANNING` → `analyst` (kontrak belum pasti)

> Rancang dan terbitkan brief untuk penambahan endpoint split order. **Taskdir**: `backenddev/docs/2608221000-order-split/` **Risk Level**: `BREAKING`. **Evidence**: `internal/order/handler.go:58`, `internal/order/entity.go:22`. **File Scope**: `internal/order/`, `db/migrations/`. **Acceptance Criteria**: `TASK.md` terkunci, tiap hop ledger `## Chain` tercentang beserta sha-nya — hop `BRIEF` termasuk, tiap artefak rancangan yang tercantum di ledger itu berstatus `APPROVED`, seluruh brief `READY` ter-commit, vonis gerbang `READY_FOR_IMPLEMENTATION` (15/15 predikat). **Stop Condition**: Approval dokumen ditolak user dua kali pada hop yang sama → BERHENTI.

Gerbang tidak memilih panjang rantai di framing ini: kedua contoh memakai lane yang sama, dan `analyst` menurunkan chain-nya sendiri dari dua sumbu `analyst/references/chain-rules.md` bagian 1.1-1.3 atas `Risk Level` beserta `Evidence` di atas. `Risk Level: BREAKING` tidak dengan sendirinya menuntut BRD — kebutuhan BRD diputuskan sumbu bisnis, bukan oleh pecahnya kontrak teknis.

### B-1. Lane `PLANNING` → `analyst` (perbaikan temuan terpilih)

> Rancang dan terbitkan brief untuk memperbaiki temuan `P1-1` dan `P2-3` laporan audit `backenddev/issues/2026-09-05-001-issues.md`. **Taskdir**: `backenddev/docs/2609051120-warehouse-stock-fix/` **Risk Level**: `MAJOR`. **Finding Source**: `backenddev/issues/2026-09-05-001-issues.md` — temuan terpilih `P1-1`, `P2-3`. **Evidence**: `internal/warehouse/service.go:88` (`P1-1`), `internal/warehouse/repo.go:215` (`P2-3`). **File Scope**: `internal/warehouse/`. **Acceptance Criteria**: `TASK.md` terkunci dengan satu `SC-{n}` per temuan terpilih yang menyebut ID temuannya, tiap hop ledger `## Chain` tercentang beserta sha-nya, seluruh brief `READY` ter-commit, vonis gerbang `READY_FOR_IMPLEMENTATION`. **Stop Condition**: Temuan ternyata menuntut kontrak baru → `analyst` menaikkan chain, gerbang tidak diminta memutuskannya ulang.

Slot `Finding Source` hadir hanya pada framing ini, dan `analyst` meneruskannya ke `task` beserta `plan`: ia yang menyalakan re-verification temuan di `plan` Fase 2 dan penandaan baris `> Status:` di berkas asalnya. Framing perbaikan temuan **tidak pernah menyebut `entry_mode`** — jalur masuk `plan` diturunkan `analyst` dari `chain`, persis seperti lane `PLANNING` lainnya. Temuan yang terbukti butuh kontrak baru tidak dikembalikan ke gerbang: ia pemicu eskalasi chain nomor 1 milik `analyst`.

### B-2. Lane `PLANNING` → `analyst` (dari tiket analyst `READY`)

> Rancang dan terbitkan brief untuk tiket `analyst/tickets/2609231400-cicilan-pembayaran/TICKET.md`. **Taskdir**: `backenddev/docs/2609241000-invoice-installment/` **Risk Level**: `MAJOR`. **Ticket Source**: `analyst/tickets/2609231400-cicilan-pembayaran/TICKET.md` — `TAC-1`…`TAC-7`, `TBR-1`…`TBR-3`. **Evidence**: `internal/invoice/service.go:88`. **File Scope**: `internal/invoice/`. **Acceptance Criteria**: `TASK.md` terkunci dengan tiap `TAC-{n}` dipikul `SC-{n}` atau tercatat di `## Out of Scope` beralasan, tiap hop ledger `## Chain` tercentang beserta sha-nya, seluruh brief `READY` ter-commit. **Stop Condition**: tiket tidak lagi `READY` atau disunting sesudah approve (prasyarat `task` check 7 `FAIL`) → BERHENTI, kembalikan ke `analyst:spec`.

Kontrak serah-terima tiket (`ticket_source`):

1. **Nilai**: path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` relatif root repo, diteruskan apa adanya. Dilarang disimpulkan dari isi `request`: permintaan yang tampak seperti kartu tiket tanpa path → tanyakan path-nya lewat `AskUserQuestion`. Terisi → `request` = kartu tiket (H1 sampai akhir `## Lampiran`) apa adanya.
2. **Namespace**: kartu menulis `AC-{n}`/`BR-{n}`; di seluruh artefak backend keduanya dirujuk `TAC-{n}`/`TBR-{n}` agar tidak bertabrakan dengan `AC-{n}` PRD dan `BR-{n}` BRD. Kartu analyst tidak diubah.
3. **Fase 1 butir 4**: tiap `TAC-{n}` dihitung satu permukaan yang disebut `request`.
4. **Syarat tiket**: frontmatter `status: READY` dan `elicitation: CLOSED`; di repo git, commit terakhir yang menyentuh berkas bersubjek `docs(ticket): kunci TICKET <slug> READY` atau `docs(ticket): ref TICKET <slug>` dan berkasnya bersih. Penilainya prasyarat `task` check 7, bukan gerbang.
5. **Jalur**: gerbang → `analyst` (slot `Ticket Source`) → `task` (keterpikulan `TAC-{n}`) dan, bila sumbu bisnis tetap aktif, `business-analysis` (serap `TBR-{n}`); `analyst/references/chain-rules.md` bagian 1.1 dan 2.1.
6. **Tiket `TECH`** (frontmatter `type: TECH`, dari lead engineer): kartu teknis tanpa `BR-{n}`; `D-{n}` (keputusan) dan `C-{n}` (batasan) dirujuk `TD-{n}`/`TC-{n}` dan dihitung sudah disepakati, sama seperti `TBR-{n}`. Bukti `path:baris` di `## Kondisi Saat Ini` adalah **titik awal**, bukan kebenaran final: Fase 1 tetap membuktikan permukaan dari kode sekarang, dan baris yang bergeser tidak membatalkan tiket. Klaim kondisi yang tidak lagi benar, atau `TC-{n}` yang tidak dapat dijaga → BERHENTI dan kembalikan ke `analyst:spec` (reopen), bukan dilanggar diam-diam. `Kondisi Target` tiket mengikat hasil akhir, tidak mengikat urutan brief. Risk tetap diputuskan Keputusan 2 dari kode, bukan dari `category` tiket.

### C. Lane `AUDIT_SWEEP` → `audit`

> Audit modul `internal/warehouse/` terhadap 6 dimensi arsitektur. **Scope**: Seluruh berkas sumber di bawah package tersebut. **Acceptance Criteria**: File temuan ditulis ke `backenddev/issues/` berlabel `CONFIRMED`/`PLAUSIBLE`, indeks `backenddev/issues/README.md` diperbarui. **Stop Condition**: Kandidat tidak memiliki bukti `file:line` konkret dibuang (bukan jadi P3).

### D. Framing Hop di Dalam Fase Planning

Framing untuk `business-analysis`, `system-analysis`, `task`, dan `plan` tidak disusun gerbang: keempatnya dipanggil `backend:analyst` di Fase 3-nya, dengan parameter yang diturunkan dari `chain` menurut `analyst/references/chain-rules.md` bagian 2. Gerbang dilarang menyusun framing hop maupun memanggil keempat skill itu pada lane `PLANNING`.

### E. Subagent Dispatch → `dispatcher/explorer.md` (`code-explorer`)

> Telusuri alur pemanggilan method `calculateDiscount` pada `src/main/java/.../pricing/`. **Agent**: `code-explorer` via template `dispatcher/explorer.md`. **Objective**: Temukan entry point controller dan service pemanggil utama. **Acceptance Criteria**: Laporan empat seksi sesuai blok `Format laporan` template gerbang, ditulis ke `backenddev/docs/.explore/<slug>.md` sekaligus dikembalikan ke context, mencantumkan pointer `file:line` terverifikasi. **Stop Condition**: Berhenti begitu entry point teridentifikasi. Dilarang melakukan audit inline.

**Pemicu Dispatch Wajib (`tech-lead` Fase 1 butir 2).** Empat kondisi mekanis; satu terpenuhi sudah cukup, dan sapuan main loop tidak boleh dicoba lebih dulu:

| Kondisi | Contoh konkret |
| --- | --- |
| Objek kerja melintasi lebih dari satu layer | permintaan menyentuh Controller **dan** Service/Repository, atau DTO **dan** Entity |
| Yang dicari relasi, bukan lokasi | pemanggil sebuah method, konsumen DTO response, batas transaksi, urutan kolom berkas ekspor |
| Simbol yang user sebut tak muncul di `Glob` #1 | nama kelas atau method dari prompt tidak menghasilkan satu pun kandidat berkas |
| Kuota sapuan main loop habis | panggilan `Glob`+`Grep` ke-4, pembacaan berkas penuh pertama, atau query database pertama |

**Yang tidak dihitung kuota**: pembacaan `.claude/profile/backenddev/` (Fase 0), `ls backenddev/docs/` (Fase 3), serta perintah `git status`/`git branch` pada gerbang git.

**Sesudah laporan diterima**: gunakan pointer `file:line` di laporan sebagai bukti Keputusan 1. Dilarang membaca ulang berkas yang sudah diringkas explorer hanya untuk memastikan.

______________________________________________________________________

## 5. Handoff Matrix & Boundary Enforcement

Tiap skill menutup tugasnya dengan mengembalikan rute ke pemanggil yang berwenang:

| Pelaksana | Handoff Terminal Tujuan |
| --- | --- |
| `tech-lead` | User — gerbang tidak punya pemilik orkestrasi di atasnya |
| `analyst`, `profile`, `debug`, `audit`, `architect` | gerbang `backend:tech-lead` di main loop |
| `task`, `business-analysis`, `system-analysis`, `plan` | skill `backend:analyst` sebagai pemanggil hop. Dua pengecualian, keduanya di luar lane planning: gerbang memanggil `task` sendiri pada lane `DEFECT_RCA` dan backfill `EXEC_BRIEF`, dan `plan` jalur `RCA` pulang ke gerbang karena gerbang pula yang memberangkatkannya |
| `document-api` | gerbang `backend:tech-lead`; berkas `docs/api/` menunggu commit gerbang |
| `report` | skill `backend:architect` |
| `code-reviewer` | skill `backend:architect` sebagai pendispatch langsung |
| agent `code-explorer` | Skill pendispatch yang memanggilnya lewat `dispatcher/explorer.md` miliknya sendiri: `tech-lead`, `business-analysis`, `system-analysis`, `plan`, `debug` |
| agent `code-reviewer` | `backend:architect` sebagai pendispatch langsung lewat `architect/dispatcher/reviewer.md` |
| agent `code-implementor` | `backend:architect` sebagai pendispatch langsung |
| agent `brd-reviewer`, `prd-reviewer`, `brief-reviewer` | Penulis dokumen yang mendispatchnya langsung: `business-analysis`, `system-analysis`, `plan` |

Skill pelaksana dilarang mengarahkan langkah berikutnya sendiri ke skill lain tanpa kembali ke pemilik orkestrasinya.

______________________________________________________________________

## 6. Seleksi Temuan & Filter Status (Fase 5)

Berlaku saat gerbang menyusun daftar temuan yang ditanyakan ke user — pada re-entry dari `audit`, dan saat severity `P1` `architect` kembali membawa `{taskdir}/REVIEW.md`. Ini **rumah kanonik** filter tersebut; `plan` tidak menyaringnya lagi, karena temuan yang sampai ke sana sudah berakar di `TASK.md`.

Sumber batch yang sah: satu berkas laporan penuh (`backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`), satu tingkat severity, atau daftar ID eksplisit.

**Plafon tujuh temuan per taskdir.** Angka itu bukan pilihan gaya: ia plafon `SC-{n}` `TASK.md`, dan tiap temuan terpilih memikul tepat satu butir `SC-{n}` yang menyebut ID-nya. Temuan kedelapan dan seterusnya masuk taskdir berikutnya — dilarang dipadatkan jadi satu butir gabungan demi muat, karena butir gabungan kehilangan `file:line` yang membuatnya dapat diverifikasi.

| Status di berkas temuan / `README.md` | Masuk seleksi | Alasan |
|---|---|---|
| *(tanpa penanda)* | **Ya** | Temuan baru, belum pernah diproses |
| `DEFERRED` | **Ya** | Pekerjaan disetujui tetapi ditunda; wajib diproses ulang |
| `FIXED` | **Tidak** | Sudah selesai dan lolos verifikasi sebelumnya |
| `DROPPED` | **Tidak** | Dibatalkan sejak awal |
| `OBSOLETE` | **Tidak** | Kode sudah berubah sehingga klaimnya tidak valid |

Filter ini menyaring apa yang **ditawarkan** ke user. Pembuktian ulang bahwa temuan masih nyata di kode adalah pekerjaan `plan` Fase 2 (`plan/references/slicing-and-scan.md` bagian 2 butir 1): temuan yang ternyata sudah diperbaiki keluar dari batch di sana dengan penanda `OBSOLETE`, dan temuan `PLAUSIBLE` yang blocker-nya tak terjawab keluar sebagai `DROPPED`. Keduanya berjalan hanya bila `finding_source` terisi.

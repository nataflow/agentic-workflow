# Execution Lifecycle, Git Staging & Recovery Protocol

Panduan mesin status brief, protokol re-entrancy lintas sesi, tata cara atomic git commit staging eksplisit, triase kegagalan *fail-fast*, dan eskalasi review untuk skill `backend:architect`.

______________________________________________________________________

## 1. Brief State Machine & Re-entrancy Protocol

Alur siklus hidup status brief diatur secara deterministik untuk menjamin keterlacakan eksekusi:

```
[ brief-NN ] ─► READY ─┬─► DONE ──────────────────────────────► lanjut NN+1
                       ├─► BLOCKED ─► (plan: pengganti) ─► SUPERSEDED ─► dilewati
                       └─► SUPERSEDED (plan: terbit ulang hilir) ─────► dilewati
```

### Matriks Transisi Status Frontmatter Brief

Baris `status` frontmatter ditulis **`code-implementor`** (`DONE`/`BLOCKED`) dan skrip
`scaffold_brief.py` milik `plan` (`SUPERSEDED`), bukan `architect`. Skill orkestrator membacanya
untuk traversal dan memverifikasi commit-nya mendarat. Satu-satunya tulisan `architect` adalah koreksi
`READY → DONE` di disk saat commit unit terbukti mendarat tetapi statusnya tertinggal (bagian 3).

| Status Awal | Kondisi Transisi                            | Status Akhir | Ditulis oleh       | Aksi Lanjutan `architect`                    |
| ----------- | ------------------------------------------- | ------------ | ------------------ | -------------------------------------------- |
| `READY`     | Seluruh `## Steps` tuntas + cek statis lolos | `DONE`      | `code-implementor` | Catat SHA dari amplop, lanjut ke `NN+1`      |
| `READY`     | Kena stop condition / cacat statis di luar scope | `BLOCKED` | `code-implementor` | Jalankan matriks bukti disk bagian 3       |
| `READY`     | Commit ber-`commit_message` sudah mendarat, status tertinggal | `DONE` | `architect` (koreksi) | Commit korektif brief saja, lanjut `NN+1` |
| `DONE`      | Traversal sesi baru (re-entrancy)           | `DONE`       | —                  | Lewati unit, pertahankan commit eksisting    |
| `BLOCKED`   | Traversal sesi baru, belum digantikan        | `BLOCKED`    | —                  | **BERHENTI**, eskalasi ke `tech-lead` (lane `PLANNING`, taskdir sama) |
| `BLOCKED`   | `scaffold_brief.py --nn` baris pengganti     | `SUPERSEDED` | `plan` (skrip)     | Lewati; pengganti dieksekusi di NN-nya       |
| `READY`     | Terbit ulang sesudah perbaikan (D2-A)        | `SUPERSEDED` | `plan` (skrip)     | Lewati                                       |
| `SUPERSEDED`| Traversal sesi baru                          | `SUPERSEDED` | —                  | Lewati                                       |

> [!NOTE] `DEFERRED` **bukan** nilai frontmatter brief maupun nilai item `## Work status`. Penundaan
> tidak melompati brief: rantai berhenti di brief itu, statusnya tetap `READY`, dan sesi berikutnya
> melanjutkan persis dari sana. `DEFERRED` hanya hidup sebagai status **temuan** di
> `backenddev/issues/`, di luar siklus hidup brief.

### Protokol Re-entrancy & Pemulihan Sesi

1. **Rantai Terputus di Sesi Sebelumnya**:
   - Pindai brief urut `NN`. Brief berstatus `DONE` atau `SUPERSEDED` dilewati tanpa re-dispatch dan tanpa duplikasi commit.
   - Eksekusi dimulai persis pada brief pertama berstatus `READY` (`entry` `FASE_3:<NN>` check 3 skrip prasyarat). Brief `BLOCKED` di mana pun menahan rantai, sekalipun brief `READY` menyusul sesudahnya.
2. **Kondisi Terminal — dua artefak penutup, bukan satu**:

   Rantai dinyatakan tuntas hanya ketika `{taskdir}/REVIEW.md` **dan** `{taskdir}/REPORT.md` sama-sama
   ada. Memvonis tuntas atas `REVIEW.md` saja membuat `report` yang gagal — atau tak pernah
   berangkat karena sesi sebelumnya putus di antara Fase 4 dan Fase 5 — tidak pernah dijemput siapa pun.

   | Seluruh brief tertutup (`DONE`/`SUPERSEDED`) | `REVIEW.md` | Segar (check 3)? | `REPORT.md` | Titik masuk sesi ini |
   | --- | --- | --- | --- | --- |
   | ya | tidak ada | — | — | Fase 4 — jalankan gerbang verifikasi lalu review penutup |
   | ya | ada | **tidak** (commit kode sesudahnya) | — | Fase 4 — verifikasi lalu **satu review baru**; `REVIEW.md` lama ditimpa reviewer |
   | ya | ada | ya | tidak ada | Fase 5 — panen laporan rantai lewat `backend:report`; commit trail direkonstruksi dari `git log`, severity dibaca dari `REVIEW.md`, dan tidak ada satu pun subagent didispatch ulang |
   | ya | ada | ya | ada | Rantai tuntas — laporkan apa adanya, jangan menulis ulang artefak yang sudah terbit |

   Kesegaran dibaca skrip dari ujung `range: <merge-base>..<HEAD>` frontmatter `REVIEW.md` dan riwayat
   commit kode: `REVIEW.md` basi bila ujung itu bukan leluhur `HEAD`, atau ada commit yang menyentuh kode
   di luar `backenddev/` dan `.claude/` sesudahnya (24 K9). Dokumen taskdir tidak di-commit, dan commit
   profil maupun indeks issues tidak membuatnya basi. Tanpa aturan ini `REVIEW.md` ber-`P1` yang basi memutar rantai tanpa
   ujung: architect lompat ke Fase 5, `report` menolak `P1`, gerbang merutekan `P1` ke `PLANNING` lagi.

______________________________________________________________________

## 2. Kepemilikan Commit & Staging Eksplisit

Commit dikerjakan **penulis karyanya**, bukan orkestrator. `architect` memverifikasi bahwa commit
itu mendarat, membawa kode, dan diff-nya tidak melewati `## File scope`. Dokumen taskdir — brief,
`report-NN.md`, `HALT.md`, `REVIEW.md`, `REPORT.md` — tidak pernah di-commit siapa pun (Langkah 24):
`backenddev/docs/` diabaikan git, dan penanda henti serta koreksi status milik `architect` ditulis di disk.

| Commit | Pemilik | Pesan |
| --- | --- | --- |
| `src/**` (+ `finding_source` bertanda `FIXED`), brief sukses | `code-implementor` | `commit_message` frontmatter brief — bukti unit mendarat |
| `src/**` yang sudah tersentuh, brief terblokir | `code-implementor` | `wip(<domain>): brief-<NN>-<unit> [BLOCKED]`; nol berkas kode tersentuh → tanpa commit |
| `{taskdir}/REVIEW.md` + baris riwayat review di `backenddev/issues/README.md` | `code-reviewer` | `REVIEW.md` di disk; commit `backenddev/issues/README.md` saja, `docs(<slug>): add final review report` dibentuk dari `commit_convention` profil |
| Penguncian susulan saat commit hilir terbukti gagal | `architect` | ulangi pesan milik penulisnya, catat penyimpangan |

Seluruh staging wajib menyebut path satu per satu, dan tidak pernah memuat path di bawah `backenddev/docs/`:

```bash
git add <file-1> <file-2> <file-n>
git commit -m "<commit_message frontmatter brief>"
```

*Contoh:* `git commit -m "feat(order): implement order lock service"`

### Larangan Keras Operasi Git

- dilarang `git add .` atau `git add -A`: wildcard staging berisiko menarik file scratch, temporary log, atau uncommitted work milik user. Dilarang pula `git add -f` atas `backenddev/docs/`.
- dilarang `git push` atau `gh pr create`: mengirim perubahan ke remote adalah hak prerogatif user.
- dilarang `git checkout` atau `git merge`: berpindah branch atau merge otomatis dapat merusak konteks kerja direktori user.

______________________________________________________________________

## 3. Failure Recovery & Blocker Triage Protocol

Ketika subagent `code-implementor` mengalami kegagalan atau terantuk stop condition:

```
[ Implementor Gagal ] ──► report-<NN>.md ──► status: BLOCKED ──► Commit WIP (bila kode tersentuh) ──► Fase 5 (BLOCKED) ──► tech-lead
```

**Rantai terhenti tidak pernah direview.** Tidak ada jalur "review parsial": Fase 4 dilewati utuh —
gerbang verifikasinya menuntut brief `NN` tertinggi berstatus `DONE`, dan `dispatcher/reviewer.md`
menuntut build penutup hijau. `code-reviewer` yang berangkat di atas rantai separuh menilai kontrak
gabungan brief yang sebagian memang belum ditulis, sehingga temuannya tak dapat dipisahkan dari
pekerjaan yang tertinggal. Yang berangkat dari titik henti hanyalah laporan penutup Fase 5 berstatus
`BLOCKED (di brief-NN)`, dan sisa pekerjaannya diklasifikasi ulang `backend:tech-lead` sebagai
**brief perbaikan pada taskdir yang sama** lewat lane `PLANNING` — bukan ditambal di siklus ini, dan
bukan pula dipindahkan ke taskdir baru.

> [!IMPORTANT] **Aturan pemutus: taskdir tidak pernah berpindah karena `BLOCKED`.**
> `tech-lead` Failure path butir 3 ("brief `BLOCKED` di taskdir aktif → perbaiki penyebabnya sebelum
> membuat taskdir baru") dan guardrail RATIONALIZATION PREVENTION-nya ("dilarang menutupi taskdir
> `BLOCKED` dengan direktori baru") adalah aturan yang berlaku, dan berkas ini tunduk padanya.
> Taskdir baru menyembunyikan brief `BLOCKED` dari tiap gerbang yang memindainya, sekaligus memutus
> `Consumes`/`Produces` brief sisanya dari `Produces` brief yang sudah `DONE`. Rutenya:
> `architect` → `tech-lead` → lane `PLANNING` → `analyst` re-entry (Fase 3 butir 0) dengan
> `reentry_reason` menyebut brief yang terblokir → `plan` menerbitkan brief pengganti ber-`supersedes`
> di `NN` berikutnya pada taskdir yang sama; `scaffold_brief.py` menandai brief `BLOCKED` (dan brief
> `READY` hilirnya yang diterbitkan ulang) `SUPERSEDED`.

### 3a. Penanda Henti `{taskdir}/HALT.md`

Vonis gerbang kompilasi per-brief (Fase 3 butir 3b), scope, dan simbol (butir 4) jatuh **sesudah**
implementor meng-commit kode unit dan menulis brief `DONE`. Vonis yang hanya hidup di laporan percakapan
hilang saat sesi putus: sesi berikutnya melihat brief itu `DONE`, memilih `NN+1`, dan melanjutkan di atas
kode yang diketahui rusak. `HALT.md` mencatat vonis itu di disk (tanpa commit); check 7 skrip prasyarat
menolak setiap sesi selama berkas itu ada dan belum dicabut (`status: DICABUT`, 24 K11).

```markdown
---
brief: brief-02-endpoint.md
verdict: COMPILE | SCOPE | SYMBOL | STRAY
sha: <sha7 commit unit yang divonis>
baseline: <sha7 merge-base> · <hijau | merah (n galat) | TERDEGRADASI (alasan)>
---
# HALT — brief-02-endpoint

## Galat
<maks 40 baris: keluaran kompilator | berkas/simbol di luar scope beserta file:baris | path berkas liar>

## Rute
COMPILE/STRAY → tech-lead → PLANNING taskdir sama (reentry_reason = berkas ini) → plan: baris `repairs: "02"` + terbit ulang brief READY hilir.
SCOPE/SYMBOL → tech-lead tanyakan ke user: terima (cabut HALT) atau reset.
```

Tulis di disk, tanpa commit. Pencabutan tidak menghapus berkasnya: ia menambah `status: DICABUT` dan `dicabut: <alasan>`, sehingga jejak penahanan tetap ada dan ikut tercermin ke nataflow.

| Pencabut | Kapan | Mekanisme |
| --- | --- | --- |
| `plan` | Brief perbaikan ber-`repairs: brief-NN` ditulis `scaffold_brief.py --nn` | Skrip menulis `status: DICABUT` + `dicabut: brief-NN (repairs)` |
| `tech-lead` | `SCOPE`/`SYMBOL` diterima user, atau commit unit di-reset user | `doc_seal.py cabut-halt --alasan "<scope diterima user \| commit di-reset user>"`; sesudah reset juga `doc_seal.py buka-done --brief <NN>` (brief `DONE` → `READY`) |
| `architect` | tidak pernah | — |

`HALT.md` bukan kode, sehingga tidak membuat `REVIEW.md` basi, dan seperti seluruh `backenddev/docs/`
diabaikan git.

### Matriks Bukti Disk untuk Amplop `BLOCKED`

`BLOCKED` dipakai untuk dua peristiwa berbeda: subagent berangkat lalu terhenti (**ada vonis**), dan
dispatch tidak pernah berangkat (**tidak ada vonis**). Kata statusnya tidak membedakan keduanya, jadi
`architect` memutuskan dari bukti di disk — bukan dari amplop.

| `report-<NN>.md`? | Commit unit di `git log`? | `status` brief di disk | `git status` | Tindakan `architect` |
| --- | --- | --- | --- | --- |
| ya | apa pun | `BLOCKED` | bersih | **HENTIKAN**, Fase 5 `BLOCKED (di brief-NN)`; brief ditutup `plan` lewat pengganti ber-`supersedes` |
| ya | tidak | apa pun | kotor | Vonis ada, commit `wip` gagal — commit sendiri berkas kode tersentuh `wip(<domain>): brief-NN-<unit> [BLOCKED]`, catat penyimpangan, **HENTIKAN**, Fase 5 `BLOCKED (di brief-NN)` |
| tidak | ya | `DONE` | bersih | Normal — ambil SHA dari `git log`, lanjut `NN+1` |
| tidak | ya | `READY` | bersih | **Koreksi status** (commit ada, status tertinggal): tulis `status: DONE` di brief, di disk tanpa commit; **dilarang retry**; lanjut `NN+1`. Skrip prasyarat menandainya `entry` `KOREKSI:<NN>:<sha7>` |
| tidak | ya | apa pun | kotor | **HENTIKAN**, tulis `HALT.md` `verdict: STRAY` berisi `git status --porcelain` (bagian 3a); eskalasi ke user; dilarang meng-commit apa pun |
| tidak | tidak | `READY` | bersih | Dispatch tak pernah berangkat — ulangi dispatch sebanyak `max_retries_per_brief`; masih gagal ⇒ eskalasi ke user |
| tidak | tidak | `DONE` | bersih | **DONE tanpa bukti** (commit unit di-reset user, atau `DONE` tidak pernah mendarat; prasyarat check 3 FAIL) — **HENTIKAN**, kembalikan ke `backend:tech-lead`, yang mengembalikan brief ke `READY` lewat `doc_seal.py buka-done`; dilarang menulis status sendiri |
| tidak | tidak | apa pun | kotor | Perubahan parsial tanpa vonis — **HENTIKAN**, eskalasi ke user; dilarang meng-commit apa pun |

Pembeda commit unit di `git log` adalah subjek yang **sama** dengan `commit_message` pada frontmatter
brief (atau varian `wip(<domain>)`-nya) sesudah spasi dirapatkan dan huruf disamakan, sejak `base_commit`
`TASK.md` — bukan `--grep` regex dan bukan tebakan dari isi diff. Berkas di luar `.explore/` yang tertinggal sesudah commit implementor
tidak pernah dibersihkan `architect` (`git restore`, `git clean`, `git stash` dilarang): keputusan atas
pekerjaan yang tidak diklaim siapa pun milik user.

### Struktur Laporan Kegagalan (`report-<NN>.md`)

File `{taskdir}/report-<NN>.md` wajib memuat:

1. **Trigger Condition**: Alasan tepat penghentian (misal: anchor simbol hilang, type mismatch, test gagal).
2. **Executed Commands & Output**: Perintah terminal yang dijalankan beserta potongan error verbatim.
3. **Working Tree State**: Daftar file yang sudah termodifikasi dan baris perubahan yang belum selesai.
4. **Remediation Recommendation**: Catatan penyesuaian untuk input perencana brief berikutnya. Bila penyebab terhentinya adalah **preseden kode yang menyesatkan** — pola warisan yang disalin brief sebagai contoh, lalu ternyata melanggar `## Anti-patterns` atau `## Invariants` profil — sebut `file:baris` preseden itu beserta polanya di baris tersendiri berawalan `Umpan balik profil:`. Tanpa baris ini pengetahuan itu mati bersama taskdir, dan rantai berikutnya menyalin preseden yang sama karena profil tidak pernah menandainya.

### Prinsip Fail-Fast

- **Tidak Melompati Brief Gagal**: Urutan `NN` adalah linear DAG. Brief `02` yang gagal membatalkan asumsi prasyarat bagi brief `03`.
- **Hentikan Loop Seketika**: Jangan mencoba mengeksekusi brief berikutnya setelah terblokir.

______________________________________________________________________

## 4. Review Severity Triage & Hand-off Matrix

Hasil review branch penutup diklasifikasikan ke dalam 4 tingkatan tindakan. Definisi severity: `skills/audit/references/findings-contract.md` bagian 1 — tabel ini hanya memetakan tindakannya.

| Severity    | Tindakan Architect                                     | Aksi Handoff Lanjutan                                  |
| ----------- | ------------------------------------------------------ | ------------------------------------------------------ |
| **`P1`**    | Laporkan di summary akhir; `REVIEW.md` sudah ditulis reviewer | Eskalasi ke `tech-lead`; ia merutekannya ke lane `PLANNING` **pada taskdir yang sama** dengan `finding_source` `{taskdir}/REVIEW.md` dan `reentry_reason` |
| **`P2`**    | Laporkan di summary akhir (baris indeks sudah ditulis dan di-commit `code-reviewer`) | Ditangani pada siklus perbaikan rilis berikutnya       |
| **`P3`**    | Laporkan di summary akhir (baris indeks sudah ditulis dan di-commit `code-reviewer`) | Non-blocking backlog                                   |
| **`CLEAN`** | Nyatakan review bersih penuh (0 pelanggaran terhadap union brief) | Siap untuk user membuat PR / merge                     |

> [!NOTE] Temuan `P1` **dilarang diperbaiki langsung** di dalam siklus architect. Perbaikan wajib melalui perencanaan brief terisolasi via `plan`.

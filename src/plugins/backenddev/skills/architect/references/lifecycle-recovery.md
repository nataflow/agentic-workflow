# Execution Lifecycle, Git Staging & Recovery Protocol

Panduan mesin status brief, protokol re-entrancy lintas sesi, tata cara atomic git commit staging eksplisit, triase kegagalan *fail-fast*, dan eskalasi review untuk skill `backenddev:architect`.

______________________________________________________________________

## 1. Brief State Machine & Re-entrancy Protocol

Alur siklus hidup status brief diatur secara deterministik untuk menjamin keterlacakan eksekusi:

```
[ brief-NN ] ──► Status: READY ──┬─► Sukses Verifikasi ──► Status: DONE ──► Lanjut ke NN+1
                                 │
                                 └─► Stop Condition ────► Status: BLOCKED ──► STOP Rantai
```

### Matriks Transisi Status Frontmatter Brief

Baris `status` frontmatter ditulis **`code-implementor`**, bukan `architect`. Skill orkestrator
membacanya untuk traversal dan memverifikasi commit-nya mendarat — tidak pernah menulisnya.

| Status Awal | Kondisi Transisi                            | Status Akhir | Ditulis oleh       | Aksi Lanjutan `architect`                    |
| ----------- | ------------------------------------------- | ------------ | ------------------ | -------------------------------------------- |
| `READY`     | Seluruh `## Steps` tuntas + cek statis lolos | `DONE`      | `code-implementor` | Catat SHA dari amplop, lanjut ke `NN+1`      |
| `READY`     | Kena stop condition / cacat statis di luar scope | `BLOCKED` | `code-implementor` | Jalankan matriks bukti disk bagian 3       |
| `DONE`      | Traversal sesi baru (re-entrancy)           | `DONE`       | —                  | Lewati unit, pertahankan commit eksisting    |
| `BLOCKED`   | Traversal sesi baru (re-entrancy)           | `BLOCKED`    | —                  | **BERHENTI SEGERA**, eskalasi ke `tech-lead` |

> [!NOTE] `DEFERRED` **bukan** nilai frontmatter brief maupun nilai item `## Work status`. Penundaan
> tidak melompati brief: rantai berhenti di brief itu, statusnya tetap `READY`, dan sesi berikutnya
> melanjutkan persis dari sana. `DEFERRED` hanya hidup sebagai status **temuan** di
> `backenddev/issues/`, di luar siklus hidup brief.

### Protokol Re-entrancy & Pemulihan Sesi

1. **Rantai Terputus di Sesi Sebelumnya**:
   - Pindai brief urut `NN`. Brief berstatus `DONE` dilewati tanpa re-dispatch dan tanpa duplikasi commit.
   - Eksekusi dimulai persis pada brief pertama berstatus `READY`.
2. **Kondisi Terminal — dua artefak penutup, bukan satu**:

   Rantai dinyatakan tuntas hanya ketika `{taskdir}/REVIEW.md` **dan** `{taskdir}/REPORT.md` sama-sama
   ada. Memvonis tuntas atas `REVIEW.md` saja membuat `report` yang gagal commit — atau tak pernah
   berangkat karena sesi sebelumnya putus di antara Fase 4 dan Fase 5 — tidak pernah dijemput siapa pun.

   | Seluruh brief `DONE` | `REVIEW.md` | `REPORT.md` | Titik masuk sesi ini |
   | --- | --- | --- | --- |
   | ya | tidak ada | — | Fase 4 — jalankan gerbang verifikasi lalu review penutup |
   | ya | ada | tidak ada | Fase 5 — panen laporan rantai lewat `backenddev:report`; commit trail direkonstruksi dari `git log`, severity dibaca dari `REVIEW.md`, dan tidak ada satu pun subagent didispatch ulang |
   | ya | ada | ada | Rantai tuntas — laporkan apa adanya, jangan menulis ulang artefak yang sudah terbit |

______________________________________________________________________

## 2. Kepemilikan Commit & Staging Eksplisit

Commit dikerjakan **penulis karyanya**, bukan orkestrator. `architect` memverifikasi bahwa commit
itu mendarat dan diff-nya tidak melewati `## File scope`.

| Commit | Pemilik | Pesan |
| --- | --- | --- |
| `src/**` + brief, brief sukses | `code-implementor` | `commit_message` frontmatter brief |
| `src/**` + brief + report, brief terblokir | `code-implementor` | `wip(<domain>): brief-<NN>-<unit> [BLOCKED]` |
| `{taskdir}/REVIEW.md` | `code-reviewer` | `docs(<slug>): add final review report` |
| Penguncian susulan saat commit hilir terbukti gagal | `architect` | ulangi pesan milik penulisnya, catat penyimpangan |

Seluruh staging wajib menyebut path satu per satu:

```bash
git add <file-1> <file-2> <file-n> {taskdir}/brief-<NN>-<unit>.md
git commit -m "<commit_message frontmatter brief>"
```

*Contoh:* `git commit -m "feat(order): implement order lock service"`

### Larangan Keras Operasi Git

- dilarang `git add .` atau `git add -A`: wildcard staging berisiko menarik file scratch, temporary log, atau uncommitted work milik user.
- dilarang `git push` atau `gh pr create`: mengirim perubahan ke remote adalah hak prerogatif user.
- dilarang `git checkout` atau `git merge`: berpindah branch atau merge otomatis dapat merusak konteks kerja direktori user.

______________________________________________________________________

## 3. Failure Recovery & Blocker Triage Protocol

Ketika subagent `code-implementor` mengalami kegagalan atau terantuk stop condition:

```
[ Implementor Gagal ] ──► report-<NN>.md ──► status: BLOCKED ──► Commit WIP ──► Fase 5 (BLOCKED) ──► tech-lead
```

**Rantai terhenti tidak pernah direview.** Tidak ada jalur "review parsial": Fase 4 dilewati utuh —
gerbang verifikasinya menuntut brief `NN` tertinggi berstatus `DONE`, dan `dispatcher/reviewer.md`
menuntut build penutup hijau. `code-reviewer` yang berangkat di atas rantai separuh menilai kontrak
gabungan brief yang sebagian memang belum ditulis, sehingga temuannya tak dapat dipisahkan dari
pekerjaan yang tertinggal. Yang berangkat dari titik henti hanyalah laporan penutup Fase 5 berstatus
`BLOCKED (di brief-NN)`, dan sisa pekerjaannya diklasifikasi ulang `backenddev:tech-lead` sebagai
**brief perbaikan pada taskdir yang sama** lewat lane `PLANNING` — bukan ditambal di siklus ini, dan
bukan pula dipindahkan ke taskdir baru.

> [!IMPORTANT] **Aturan pemutus: taskdir tidak pernah berpindah karena `BLOCKED`.**
> `tech-lead` Failure path butir 3 ("brief `BLOCKED` di taskdir aktif → perbaiki penyebabnya sebelum
> membuat taskdir baru") dan guardrail RATIONALIZATION PREVENTION-nya ("dilarang menutupi taskdir
> `BLOCKED` dengan direktori baru") adalah aturan yang berlaku, dan berkas ini tunduk padanya.
> Taskdir baru menyembunyikan brief `BLOCKED` dari tiap gerbang yang memindainya, sekaligus memutus
> `Consumes`/`Produces` brief sisanya dari `Produces` brief yang sudah `DONE`. Rutenya:
> `architect` → `tech-lead` → lane `PLANNING` → `analyst` re-entry (Fase 3 butir 0) dengan
> `reentry_reason` menyebut brief yang terblokir → brief perbaikan menyusul di `NN` berikutnya pada
> taskdir yang sama.

### Matriks Bukti Disk untuk Amplop `BLOCKED`

`BLOCKED` dipakai untuk dua peristiwa berbeda: subagent berangkat lalu terhenti (**ada vonis**), dan
dispatch tidak pernah berangkat (**tidak ada vonis**). Kata statusnya tidak membedakan keduanya, jadi
`architect` memutuskan dari bukti di disk — bukan dari amplop.

| `report-<NN>.md` ada? | Commit brief ada di `git log`? | Tindakan `architect` |
| --- | --- | --- |
| ya | ya | Vonis dan penandanya sudah mendarat — **HENTIKAN RANTAI**, lompat ke Fase 5 sebagai `BLOCKED (di brief-<NN>)` tanpa melewati Fase 4 |
| ya | tidak | Vonis ada, commit gagal — kunci sendiri `wip(<domain>): brief-<NN>-<unit> [BLOCKED]`, catat penyimpangan, **HENTIKAN RANTAI**, lompat ke Fase 5 sebagai `BLOCKED (di brief-<NN>)` |
| tidak | ya | Kerja mendarat lengkap, vonisnya yang tak sampai — perlakukan `DONE`, ambil SHA dari `git log`, **dilarang retry**, lanjut ke `NN+1` |
| tidak | tidak, `git status` bersih | Dispatch tak pernah berangkat — brief tetap `READY`, ulangi dispatch sebanyak `max_retries_per_brief`; masih gagal ⇒ eskalasi ke user |
| tidak | tidak, `git status` kotor | Perubahan parsial tanpa vonis — **HENTIKAN**, eskalasi ke user; dilarang meng-commit apa pun |

Pembeda commit brief di `git log` adalah `commit_message` pada frontmatter brief (atau varian
`wip(<domain>)`-nya), bukan tebakan dari isi diff.

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

Hasil review branch penutup diklasifikasikan ke dalam 4 tingkatan tindakan:

| Severity    | Definisi Temuan                                             | Tindakan Architect                                     | Aksi Handoff Lanjutan                                  |
| ----------- | ----------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------ |
| **`P1`**    | Pelanggaran kontrak, file di luar scope, regresi fungsional | Laporkan di summary akhir; `REVIEW.md` sudah di-commit reviewer | Eskalasi ke `tech-lead`; ia merutekannya ke lane `PLANNING` dengan `finding_source` `{taskdir}/REVIEW.md` |
| **`P2`**    | Pelanggaran invariant arsitektur, anti-pola stack         | Laporkan di summary akhir, catat ke `issues/README.md` | Ditangani pada siklus perbaikan rilis berikutnya       |
| **`P3`**    | Style konvensi lokal, redundansi minor                      | Laporkan di summary akhir, catat ke `issues/README.md` | Non-blocking backlog                                   |
| **`CLEAN`** | 0 pelanggaran terhadap union brief                          | Nyatakan review bersih penuh                           | Siap untuk user membuat PR / merge                     |

> [!NOTE] Temuan `P1` **dilarang diperbaiki langsung** di dalam siklus architect. Perbaikan wajib melalui perencanaan brief terisolasi via `plan`.

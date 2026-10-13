# Chain Self-Review & Aggregate Commit Reference — `plan`

Protokol uji mandiri rantai brief (Fase 4), dispatch self-review kolektif, dan penguncian batch (Fase 5) untuk `backend:plan`. Aturan jalur masuk hidup di `entry-rules.md`, 12 dimensi scan dan batas slicing di `slicing-and-scan.md`, kaidah isi brief di `../templates/brief-template.md` bagian 2, katalog check Fase 4 di `check-catalog.md`.

## 4. Protokol Chain Self-Review (Fase 4)

Lima belas pemeriksaan mandiri dijalankan sesudah seluruh brief batch aktif selesai ditulis; empat belas di antaranya dieksekusi `scripts/validate_briefs.py`. Predikat tiap check, remediasinya, dan aturan populasi "Batch aktif vs brief terkunci" hidup di `check-catalog.md` — buka hanya untuk ID check yang gagal.

## 5. Dispatch Self-Review Kolektif (Fase 5)

Seluruh check bagian 4 lulus lebih dulu; dispatch dilarang berangkat sebelum titik itu. Reviewer berangkat di atas brief yang predikat mekanisnya **sudah dijamin skrip**, sehingga fokusnya menyempit ke yang memang menuntut penilaian: keselarasan aturan bisnis, pendaratan kontrak PRD, dan kualitas langkah.

- **Baca state ronde lebih dulu.** Jalankan `scripts/validate_briefs.py --taskdir <taskdir> --review-state`. Keluarannya menyebut generasi batch aktif, ronde terpakai di generasi itu, sisa plafon, plafon keras taskdir, dan brief yang berubah sejak ronde terakhir.

  **Plafon 2 ronde per generasi batch, 4 ronde per taskdir.** Satu *generasi* adalah himpunan berkas brief yang ada di taskdir beserta nilai `reentry` `## Counters` `TASK.md`; ia berganti saat brief **ditambahkan** (berkas yatim `architect`, brief perbaikan) atau saat hop `BRIEF` dibuka re-entry `analyst` — walau himpunan briefnya sama, sehingga revisi yang diminta re-entry mendapat review baru. Menyunting isi brief tidak pernah membuka generasi baru, sehingga plafon tidak dapat diakali dengan mengedit, dan plafon keras taskdir tetap mengikat.

  Plafon per-taskdir yang lama membuat brief yang lahir sesudah ronde kedua mustahil direview: skrip membalas "plafon habis" atas berkas yang belum pernah dilihat reviewer mana pun, dan brief itu terpaksa dikunci lewat jalur "self-review tidak tuntas". Plafon keras taskdir tetap ada supaya penambahan brief berulang tidak menjadi loop tanpa batas.

  Sisa nol pada generasi aktif **dan** taskdir belum menyentuh plafon kerasnya → tambahan brief berikutnya akan membuka generasi baru; sisa nol karena plafon keras taskdir → serahkan brief apa adanya dengan status self-review tidak tuntas.

- **Buka ronde tepat sebelum dispatch berangkat**: `scripts/validate_briefs.py --taskdir <taskdir> --open-round`. Perintah ini memateraikan snapshot isi tiap brief **pada saat dispatch**, dan menolak berangkat bila plafon sudah habis. Snapshot itulah pembanding daftar `{brief_berubah}` ronde berikutnya.
- Muat template prompt dari `../dispatcher/reviewer.md`, hidrasi slot `taskdir`, `chain`, `ronde`, dan dokumen acuan, lalu panggil subagent `brief-reviewer` secara langsung. Tangkap balikan `## Brief Review` berstatus `Approved` atau `Issues Found`, lalu tulis bloknya apa adanya ke `{taskdir}/.explore/review/brief.md` seketika, sebelum satu suntingan pun — menimpa ronde sebelumnya, direktorinya dibuat bila belum ada. Pemanggil membacanya dari berkas itu sebagai predikat serah terima, bukan sebagai catatan; laporan penutup merujuk path-nya, bukan mencetak bloknya.
- **Ronde 1** dikirim sekaligus untuk seluruh `brief-*.md`; dilarang memecahnya jadi satu dispatch per berkas.
- **Ronde 2 berangkat hanya bila ronde 1 meninggalkan `BLOCKER [SEMANTIK]`.** Reviewer melabeli tiap `BLOCKER` `MEKANIS` atau `SEMANTIK`. Seluruh `BLOCKER` ronde 1 berlabel `MEKANIS` → perbaiki, jalankan ulang `validate_briefs.py` sampai `PASS`, lalu **lanjut ke penguncian tanpa ronde 2**: skrip memvonis hal yang sama dengan biaya nol, sementara satu ronde penuh membaca ulang `TASK.md`, `PRD.md`, dan tiap brief untuk menyimpulkan apa yang sudah dijamin. Catat pelewatan itu di laporan penutup (`Self-Review: Approved (ronde 1/2 · BLOCKER mekanis <n> tertutup skrip)`).
- **Ronde 2** menyempit ke brief yang berubah. Hidrasi `{brief_berubah}` dari keluaran `--review-state` dan `{previous_report}` dari `{taskdir}/.explore/review/brief.md` (laporan ronde 1, dibaca sebelum balikan ronde 2 menimpanya). Brief yang tidak tersentuh sejak ronde 1 byte-identik dengan yang sudah dinilai, dan menilainya ulang tidak menambah satu pun informasi — sementara `validate_briefs.py` tetap berjalan penuh atas seluruh batch sebagai jaring regresi.
- **Hanya `BLOCKER` yang menahan.** Reviewer menandai tiap temuan `BLOCKER` atau `ADVISORY`. Nol `BLOCKER` berarti `Approved`, dan `ADVISORY`-nya tercatat di berkas review serta terhitung di laporan penutup tanpa menahan penguncian. Dilarang membuka ronde baru atas `ADVISORY`: satu nit redaksional di satu brief tidak pernah sepadan dengan satu ronde penuh.
- Perbaiki temuan `BLOCKER` pada berkas brief terkait dan pertahankan `status: READY` tanpa mengunci batch selama masih ada yang terbuka.
- **Materaikan tiap ronde yang selesai** dengan `scripts/validate_briefs.py --taskdir <taskdir> --record-round "<verdict>"`. Ronde yang tidak dimateraikan tidak terhitung, dan plafonnya bocor pada invokasi berikutnya.

  Urutannya tidak lagi menentukan kebenaran daftar `{brief_berubah}`: snapshot pembandingnya diambil `--open-round`, bukan di sini. Materai yang mendarat sesudah perbaikan `BLOCKER` karena itu tetap menghasilkan daftar yang benar. Ronde yang dimateraikan tanpa pernah dibuka tetap diterima, tetapi snapshot-nya terpaksa diambil belakangan dan skrip menandainya `[snapshot menyusul]` — pada ronde itu daftar brief berubah berikutnya memang tidak dapat dipercaya.
- Dispatch gagal atau balikan formatnya rusak → ulangi maks sekali **tanpa** memateraikannya sebagai ronde; tetap gagal → serahkan brief tanpa dikunci dan tandai self-review tidak tuntas. Dilarang mengarang verdict `Approved`.

## 6. Protokol Penguncian Batch (Fase 5)

Brief lahir `status: READY` tanpa gerbang approval, berbeda dari `BRD.md` dan `PRD.md`. Penguncian batchnya karena itu dieksekusi `plan` sendiri tepat sesudah self-review kolektif lolos, bukan ditunda ke `tech-lead`. Urutan wajib dan tidak boleh dibalik:

```
matriks alokasi terkunci → tiap brief lolos gerbang per-brief Fase 3
  → Fase 4  validate_briefs.py PASS + Check A tertutup
  → Fase 5  dispatch brief-reviewer → nol temuan BLOCKER (`Approved`)
  → Fase 5  doc_seal.py lock-briefs (kunci batch)
  → handoff ke backend:analyst        (lane planning)
  → handoff ke backend:tech-lead      (jalur RCA yang dirutekan gerbang)
```

1. **Satu penguncian untuk seluruh batch**, sekalipun batch memuat brief hasil perbaikan cacat: `python3 «doc_seal.py» lock-briefs --taskdir <taskdir>` (`«doc_seal.py»` = `skills/_common/doc_seal.py` di bawah root plugin, awalan yang sama dengan skrip `plan` di `SKILL.md`). Skrip menulis `sidik_kontrak` (sidik kontrak brief tanpa baris `status:` dan isi `## Work status`) ke tiap brief `READY`; brief `DONE`/`BLOCKED`/`SUPERSEDED` tidak disentuh. Dokumen taskdir diabaikan git (Langkah 24), jadi brief, transisi `SUPERSEDED`, dan `HALT.md` yang dicabut baris `repairs` (`status: DICABUT`, ditulis `scaffold_brief.py --nn`) tidak di-stage maupun di-commit.
2. **Sidik kontrak adalah batas pelaksana.** `verify_scope.py` membandingkan kontrak brief di disk dengan `sidik_kontrak`-nya sesudah tiap unit: implementor yang memperluas `## File scope` atau `Anchor` brief-nya sendiri tertangkap (11 H3). Karena itu penguncian berangkat **sesudah** perbaikan terakhir, dan brief yang disunting sesudahnya wajib dikunci ulang lewat perintah yang sama sebelum handoff.
3. **Eksekusi seketika saat `Approved`**, tanpa menunggu persetujuan user, gerbang, maupun main loop — self-review satu-satunya prasyarat penguncian. Sebaliknya, tahan penguncian tanpa pengecualian bila status belum `Approved`.
4. **Berkas `finding_source`** di bawah `backenddev/issues/` yang Fase 2 tandai `OBSOLETE`/`DROPPED` adalah dokumen tingkat repo dan tetap ter-commit: `git add <berkas finding_source>` lalu `git commit -m "docs(plan): tandai temuan <ID> untuk <slug>"` — satu path eksplisit, satu-satunya mutasi git milik `plan`. Dilarang staging wildcard, `git add -f` atas `backenddev/docs/`, `git push`, `git merge`, `git rebase`, `git branch`, dan `git checkout`.

### Kegagalan Penguncian & Mitigasi Mandiri

| Kondisi | Predikat terdeteksi | Tindakan |
|---|---|---|
| Akar belum terkunci | `lock-briefs` FAIL `base_commit` | Kembalikan ke pemanggil; akar dikunci `backend:task` (`doc_seal.py root`) |
| Nol brief `READY` | `lock-briefs` FAIL "tidak ada brief READY" | Periksa keluaran `scaffold_brief.py --nn`; jangan menulis `sidik_kontrak` dengan tangan |
| Commit `finding_source` gagal | `git commit` mengembalikan kode keluar bukan nol | Jangan menyatakan penandanya ter-commit; sertakan pesan galat mentah pada laporan; gerbang mengunci berkas itu di Fase 5-nya |

Pada seluruh kondisi di atas berkas brief tetap berstatus `READY` dan tetap diserahkan ke pemanggil — kegagalan penguncian tidak pernah menurunkan status brief, membatalkan hasil perencanaan, maupun memicu penulisan ulang batch.

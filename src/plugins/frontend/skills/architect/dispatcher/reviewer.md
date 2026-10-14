# Template Prompt Reviewer Penutup — `code-reviewer`

Gunakan template ini saat `architect` mendispatch subagent penilai diff rantai (`code-reviewer`) secara langsung.

**Tujuan:** Menilai berkas rantai sejak akar terhadap union `files_touched`, sembilan dimensi, `CONTRACT.md`, dan `## Success Criteria` `TASK.md`, tepat satu kali, lalu mengunci hasilnya sebagai `{taskdir}/REVIEW.md` yang lolos `validate_review.py`.

**Dispatch setelah:** Phase 4 butir 1 hijau dan butir 2 bersih — verifikasi penutup nol galat baru, log-nya tertulis di `{verification_log}`, seluruh brief tertutup, dan prasyarat rantai yang dijalankan ulang sesudah verifikasi lolos Check 8 (tree bersih). Artefak verifikasi yang tertinggal di tree akan divonis check `TREE` sebagai mutasi reviewer.

````markdown
Review seluruh diff rantai untuk satu taskdir frontend.

- Taskdir: `{taskdir}`
- Rentang: berkas keluaran `python3 {chain_py} files --taskdir {taskdir}` (perintah lengkap di definisi agent-mu) —
  commit rantai (subjek `<type>(<slug>):`) sejak akar `{base}`; hunk lewat `git diff {base}..HEAD -- <berkas>`.
  `HEAD` yang dinilai: `{head}` — tulis apa adanya ke frontmatter `head:` `REVIEW.md`.
  Commit di luar rantai tidak dinilai dan berkasnya bukan berkas yatim.
- Review ulang: `REVIEW.md` yang sudah ada ditimpa utuh, bukan disambung.
- Kontrak Penilai: union `files_touched` seluruh brief, `CONTRACT.md` bila ada, dan `## Success Criteria`
  `TASK.md` — bukan kualitas umum modul sekitarnya.
- Adapter: `{adapter_path}` — `## Review checklist` untuk dimensi 6.
- Verifikasi Penutup: `{verification_log}` — sudah dijalankan pendispatch; baca, jangan jalankan ulang.
- Kerangka Laporan: `{template}` bagian 1 — tulis `{taskdir}/REVIEW.md` persis kerangka itu, selalu,
  termasuk saat bersih. Verdict diturunkan dari bagian 2 butir 6, bukan dipilih.
- Temuan Asal: `{finding_source}` — bila bukan `-`, tutup baris `> Status:` tiap temuan yang benar-benar
  diperbaiki diff ini menjadi `FIXED <YYYY-MM-DD> — lihat {taskdir}`.
- Larangan: dilarang mengedit `src/`, menjalankan typecheck/lint/test/build, dan menjalankan
  `git add`/`git commit` — `REVIEW.md` tidak di-commit, dan commit `finding_source` milik pendispatch.
- Stop Condition: gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan lapor sesuai jalur gagal
  di sana, jangan menebak.
- Balikan: amplop `## Reviewer Report` maksimal 10 baris sesuai definisi agent-mu. Jangan kutip isi
  `REVIEW.md` ke chat.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` architect | **[REQUIRED]** |
| `{base}` | 7 digit pertama `base_commit` frontmatter `{taskdir}/TASK.md` | **[REQUIRED]** HEAD saat akar dikunci (`chain.py root`); `validate_review.py` menolak `base` selain itu. Dilarang menebak `main`/`HEAD~N`: rentang yang salah menilai pekerjaan orang lain |
| `{head}` | `git rev-parse --short HEAD` sesudah verifikasi penutup, saat dispatch | **[REQUIRED]** `validate_review.py` menuntut `head` leluhur `HEAD`; commit kode sesudahnya membuat review basi |
| `{verification_log}` | Phase 4 butir 1 | **[REQUIRED]** `{taskdir}/.explore/closing-verification.md` |
| `{template}` | Entri `review-template.md` peta **Skrip:** SKILL.md | **[REQUIRED]** Path absolut hasil substitusi, bukan literal |
| `{adapter_path}` | Entri `adapter` peta **Skrip:** SKILL.md, `<stack>` dari `index.json` | **[REQUIRED]** Path absolut hasil substitusi |
| `{chain_py}` | Entri `chain.py` peta **Skrip:** SKILL.md | **[REQUIRED]** Path absolut hasil substitusi |
| `{finding_source}` | Frontmatter `finding_source` `TASK.md` | **[OPTIONAL]** `-` bila akar bukan taskdir perbaikan |

### Aturan untuk Pendispatch

- **Tepat satu kali per penutup**, sesudah verifikasi penutup hijau; penutup berikutnya hanya lahir dari brief perbaikan yang `DONE` sesudah `REVIEW.md` `BLOCKED` (fase `PENUTUP` karena `REVIEW.md` basi), atau dari `REVIEW.md` yang tidak lagi lolos `validate_review.py` (mis. sesudah amandemen SC — fase `PENUTUP`, review ulang menimpanya). Verifikasi merah (`TIMEOUT` atau galat baru > 0; `MERAH` bergalat baru 0 adalah warisan baseline) → rantai berhenti di Phase 4 butir 1 tanpa reviewer: temuan di atas build merah tak dapat dipisahkan dari kegagalannya.
- **Dispatch langsung tanpa skill pembungkus**: doktrin review — gerbang masuk, sembilan dimensi, cakupan kriteria, gerbang bukti — duduk di `agents/code-reviewer.md`. Dilarang menyalin potongannya ke prompt, dan dilarang menyalin isi brief, diff, atau profil; sebut path-nya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Jalankan validator lebih dulu, apa pun isi amplopnya — amplop adalah klaim, `REVIEW.md` di disk adalah bukti (`«nama.py»` = path absolut dari peta **Skrip:** SKILL.md):

```bash
python3 «validate_review.py» --taskdir {taskdir} \
  --log {taskdir}/.explore/closing-verification.json
```

| Keadaan | Penanganan `architect` |
| --- | --- |
| Validator `PASS`, verdict `PASS`/`WARNING` | `REVIEW.md` tetap di disk, tidak di-stage maupun di-commit (dokumen taskdir, Langkah 24). Commit hanya `{finding_source}` — dokumen tingkat repo — bila ber-`FIXED` baru **dan** `validate_audit.py --path {finding_source} --only-status-changed` `PASS` (`FAIL` → `git restore -- {finding_source}`, catat di Output): `docs(<slug>): closing review <verdict>`, lalu Phase 5 |
| Validator `PASS`, verdict `BLOCKED` | `REVIEW.md` tetap di disk apa adanya (tanpa commit), rantai berhenti; kembalikan ke `frontend:lead` untuk diperbaiki **di taskdir yang sama**: `P1` dan SC `belum terbukti` → `chain.py reopen --row BRIEF` → `plan` APPEND brief perbaikan (tanpa `remedies`) → eksekusi → review ulang; berkas yatim → rute kontrak (`references/execution-protocol.md` bagian 7) |
| Validator `FAIL` | Laporan tidak sah. Ulangi dispatch maksimal sekali dengan slot yang sama; tetap `FAIL` → review tidak tuntas: bersihkan tree dulu (lihat di bawah), lalu laporkan ke user. Dilarang menyunting `REVIEW.md` sendiri agar lolos |
| `REVIEW.md` tidak ada | Cacat kerja subagent: ulangi maksimal sekali; tetap gagal → review tidak tuntas: bersihkan tree dulu (lihat di bawah). Dilarang menulis `REVIEW.md` sendiri atau mengarang verdict |

**Review tidak tuntas — bersihkan sebelum berhenti.** Hapus `REVIEW.md` yang tidak sah. Pulihkan suntingan `{finding_source}` yang belum ter-commit: `git restore -- {finding_source}`. Rantai berikutnya berangkat dari tree bersih dan fase `PENUTUP`.

**Subagent mengembalikan:** amplop `## Reviewer Report` ≤10 baris; verdict yang berlaku adalah turunan `validate_review.py`, bukan bunyi amplop.

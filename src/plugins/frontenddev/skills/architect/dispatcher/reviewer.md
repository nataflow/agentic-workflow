# Template Prompt Reviewer Penutup — `code-reviewer`

Gunakan template ini saat `architect` mendispatch subagent penilai diff rantai (`code-reviewer`) secara langsung.

**Tujuan:** Menilai berkas rantai sejak akar terhadap union `files_touched`, sembilan dimensi, `CONTRACT.md`, dan `## Success Criteria` `TASK.md`, tepat satu kali, lalu mengunci hasilnya sebagai `{taskdir}/REVIEW.md` yang lolos `validate_review.py`.

**Dispatch setelah:** Phase 4 butir 1 hijau — verifikasi penutup nol galat baru, log-nya tertulis di `{verification_log}`, dan seluruh brief tertutup.

````markdown
Review seluruh diff rantai untuk satu taskdir frontend.

- Taskdir: `{taskdir}`
- Rentang: berkas keluaran `chain.py files --taskdir {taskdir}` (perintah lengkap di definisi agent-mu) —
  commit rantai (subjek `<type>(<slug>):`) sejak akar `{base}`; hunk lewat `git diff {base}..HEAD -- <berkas>`.
  Commit di luar rantai tidak dinilai dan berkasnya bukan berkas yatim.
- Review ulang: `REVIEW.md` yang sudah ada ditimpa utuh, bukan disambung.
- Kontrak Penilai: union `files_touched` seluruh brief, `CONTRACT.md` bila ada, dan `## Success Criteria`
  `TASK.md` — bukan kualitas umum modul sekitarnya.
- Verifikasi Penutup: `{verification_log}` — sudah dijalankan pendispatch; baca, jangan jalankan ulang.
- Kerangka Laporan: `{template}` bagian 1 — tulis `{taskdir}/REVIEW.md` persis kerangka itu, selalu,
  termasuk saat bersih. Verdict diturunkan dari bagian 2 butir 6, bukan dipilih.
- Temuan Asal: `{finding_source}` — bila bukan `-`, tutup baris `> Status:` tiap temuan yang benar-benar
  diperbaiki diff ini menjadi `FIXED <YYYY-MM-DD> — lihat {taskdir}`.
- Larangan: dilarang mengedit `src/`, menjalankan typecheck/lint/test/build, dan menjalankan
  `git add`/`git commit` — commit milik pendispatch.
- Stop Condition: gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan lapor sesuai jalur gagal
  di sana, jangan menebak.
- Balikan: amplop `## Reviewer Report` maksimal 10 baris sesuai definisi agent-mu. Jangan kutip isi
  `REVIEW.md` ke chat.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` architect | **[REQUIRED]** |
| `{base}` | `git log --diff-filter=A --format=%h -- {taskdir}/TASK.md \| tail -1` | **[REQUIRED]** Commit yang melahirkan akar; `validate_review.py` menolak `base` selain commit itu. Dilarang menebak `main`/`HEAD~N`: rentang yang salah menilai pekerjaan orang lain |
| `{verification_log}` | Phase 4 butir 1 | **[REQUIRED]** `{taskdir}/.explore/closing-verification.md` |
| `{template}` | Tetap | **[REQUIRED]** `${CLAUDE_PLUGIN_ROOT}/skills/architect/templates/review-template.md` — hasil substitusi, bukan literal |
| `{finding_source}` | Frontmatter `finding_source` `TASK.md` | **[OPTIONAL]** `-` bila akar bukan taskdir perbaikan |

### Aturan untuk Pendispatch

- **Tepat satu kali per penutup**, sesudah verifikasi penutup hijau; penutup berikutnya hanya lahir dari brief perbaikan yang `DONE` sesudah `REVIEW.md` `BLOCKED` (fase `PENUTUP` karena `REVIEW.md` basi), atau dari `REVIEW.md` yang tidak lagi lolos `validate_review.py` (mis. sesudah amandemen SC — fase `PENUTUP`, review ulang menimpanya). Verifikasi merah (`TIMEOUT` atau galat baru > 0; `MERAH` bergalat baru 0 adalah warisan baseline) → rantai berhenti di Phase 4 butir 1 tanpa reviewer: temuan di atas build merah tak dapat dipisahkan dari kegagalannya.
- **Dispatch langsung tanpa skill pembungkus**: doktrin review — gerbang masuk, sembilan dimensi, cakupan kriteria, gerbang bukti — duduk di `agents/code-reviewer.md`. Dilarang menyalin potongannya ke prompt, dan dilarang menyalin isi brief, diff, atau profil; sebut path-nya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Jalankan validator lebih dulu, apa pun isi amplopnya — amplop adalah klaim, `REVIEW.md` di disk adalah bukti:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/validate_review.py --taskdir {taskdir} \
  --log {taskdir}/.explore/closing-verification.json
```

| Keadaan | Penanganan `architect` |
| --- | --- |
| Validator `PASS`, verdict `PASS`/`WARNING` | Commit `REVIEW.md` (dan `{finding_source}` bila ber-`FIXED` baru **dan** `validate_audit.py --path {finding_source} --only-status-changed` `PASS`; `FAIL` → `git restore -- {finding_source}`, catat di Output): `docs(<slug>): closing review <verdict>`, lalu Phase 5 |
| Validator `PASS`, verdict `BLOCKED` | Commit `REVIEW.md` apa adanya, rantai berhenti; kembalikan ke `frontenddev:lead` untuk diperbaiki **di taskdir yang sama**: `P1` dan SC `belum terbukti` → `chain.py reopen --row BRIEF` → `plan` APPEND brief perbaikan (tanpa `remedies`) → eksekusi → review ulang; berkas yatim → rute kontrak (`references/execution-protocol.md` bagian 7) |
| Validator `FAIL` | Laporan tidak sah. Ulangi dispatch maksimal sekali dengan slot yang sama; tetap `FAIL` → review tidak tuntas: bersihkan tree dulu (lihat di bawah), lalu laporkan ke user. Dilarang menyunting `REVIEW.md` sendiri agar lolos |
| `REVIEW.md` tidak ada | Cacat kerja subagent: ulangi maksimal sekali; tetap gagal → review tidak tuntas: bersihkan tree dulu (lihat di bawah). Dilarang menulis `REVIEW.md` sendiri atau mengarang verdict |

**Review tidak tuntas — bersihkan tree sebelum berhenti.** Buang `REVIEW.md` yang tidak sah: `git restore -- {taskdir}/REVIEW.md` bila ter-track, hapus bila baru. Pulihkan suntingan `{finding_source}` yang belum ter-commit: `git restore -- {finding_source}`. Rantai berikutnya berangkat dari tree bersih dan fase `PENUTUP`.

**Subagent mengembalikan:** amplop `## Reviewer Report` ≤10 baris; verdict yang berlaku adalah turunan `validate_review.py`, bukan bunyi amplop.

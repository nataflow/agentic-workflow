# Langkah 13 — Robustness Plugin quickdev (Q1–Q18)

Sumber: review robustness plugin `quickdev` 2026-09-27 (baca penuh enam SKILL, tiga template, `plan_lock.py`,
README; reproduksi T1–T8 di repo git sementara). Basis kode: commit `93730e6` (suite quickdev + lint + smoke
338 test hijau; lint 0 FAIL).

**Status (2026-09-27):** Q1–Q18 selesai dalam tiga tahap, masing-masing dengan test regresi
(`tests/quickdev/test_13_{parser,state,text}.py`) yang merah di kode sebelum perbaikan (tahap 1: 18 merah,
tahap 2: 12 merah, tahap 3: 20 merah; test yang hijau di kode lama adalah pagar non-regresi, mis. sidik rencana
0.4.0 tetap cocok). Versi: quickdev 0.5.0.

## Tujuan

Jalur utama quickdev (profile → plan → lock → execute → review) sudah kokoh: tulis atomik, sidik tahan centang,
metadata rusak ditolak. Yang rapuh adalah **transisi antar-state** dan **jalur tepi**. Empat pola:

1. **State ditulis sebelum predikat dinilai.** `start` mode `awal` menulis `Base-Commit` sebelum predikat tree
   bersih dicek model; commit user sesudahnya ikut ter-review.
2. **Jalan buntu remediasi.** Opsi *Remediasi otomatis* menyuruh model memanggil skill yang
   `disable-model-invocation`; ronde remediasi yang terputus tidak dapat dilanjutkan.
3. **Hijau palsu / basi.** Baseline profil tidak terikat commit dan dicocokkan per nomor baris; `COMPLETED` tetap
   berlaku sesudah kode atau rencana berubah; parser tidak sadar code fence sehingga langkah hilang.
4. **Audit yang dapat rusak tanpa sengaja.** Template `--answer "<…>"` mengekspansi backtick dan `$`; nilai
   tanpa sanitasi dapat menyisipkan baris blok; perintah yang ditolak user di profile dijalankan ulang tanpa izin.

## Urutan pengerjaan

Tiap tahap: blast radius (tabel di bawah) → test regresi (merah di kode lama) → perbaikan → suite quickdev + smoke +
lint hijau → tahap berikutnya.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | Q4 (skrip), Q7, Q8, Q10, Q11, Q12, Q13 — parser & penulisan `plan_lock.py` | Fondasi: semua subperintah membaca lewat parser yang sama. |
| 2 | Q1, Q3, Q6 (skrip), Q9, Q14 — mesin state `plan_lock.py` | Memakai parser tahap 1; menentukan field blok yang dirujuk prosa tahap 3. |
| 3 | Q2, Q4 (prosa), Q5, Q6 (prosa), Q15–Q18 — SKILL, template, README, `flow/quickdev.md`; rilis | Bergantung pada perilaku skrip tahap 1–2. Versi plugin dinaikkan di sini. |

## Peta blast radius

`plan_lock.py` hanya dipakai quickdev (`plan`, `execute`, `review`); tidak ada berkas kembar di plugin lain.
`gate_text.py` be/fe hanya menyebut `/quickdev:*` dan tidak disentuh.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| Q1 | `plan_lock.py` `cmd_start` (tree bersih mode `awal`, `base_drift`), `status` | execute Fase 0, review Fase 1 | tidak | `test_08d_plan_lock.py` D2/D8 (plan/ untracked tetap lolos), `test_09_plan_lock.py` | **Sedang**: `start` kini menolak tree kotor dan direktori bukan git (dulu hanya disiplin model) |
| Q2 | `review/SKILL.md` Fase 5, `execute/SKILL.md` `review_findings`, README | review → execute | tidak | `test_08d_text.py::test_d3_*` (frasa `/2`, `sudah 2`, `--findings --findings-text` dipertahankan) | Rendah |
| Q3 | `plan_lock.py` `cmd_start`/`cmd_close`/`status` (`Remediation-State`) | execute remediasi, review Fase 5 | tidak | `test_d3_plafon_remediasi`, `test_d7_findings_tersimpan` | Rendah: blok lama tanpa field = ronde tertutup |
| Q4 | `plan_lock.py` `main` (nilai `-` = stdin), `cmd_close`/`cmd_lock` (sanitasi); template perintah di `plan`/`execute` SKILL | semua pemanggil skrip | tidak | `test_d1_approved_hanya_lewat_plan_lock`, `test_d7_gates_*` (substring `plan_lock.py <cmd> --plan` dipertahankan) | Rendah: `--answer -` kini berarti stdin |
| Q5 | `execute/SKILL.md` Iron Law, Fase 3, Guardrails | execute Fase 3 | tidak | — | Nihil |
| Q6 | `plan_lock.py` subperintah `baseline`; 3 template profil (`Baseline-Commit`); `profile`/`execute` SKILL | profile Fase 2, execute Fase 0/3 | tidak | `test_08d_text.py::test_d4_d6_*` (header tabel, 6 seksi tetap) | Sedang: execute mode `awal` menjalankan baseline segar bila profil diukur di commit lain |
| Q7 | `plan_lock.py` `Plan` (masker fence untuk heading/langkah/blok) | semua subperintah | tidak | semua test `plan_lock` | Rendah: sidik rencana tanpa fence **identik** (normalisasi tidak berubah); fence tak tertutup → FAIL |
| Q8 | `plan_lock.py` `save` (mode berkas, lewati bila tak berubah) | semua penulis | tidak | `test_e4_save_atomik_*` | Nihil |
| Q9 | `plan_lock.py` `close`/`confirm`/`start`/`inconsistency` (`Tree-Hash`) | execute Fase 4, review prasyarat 1 | tidak | `test_d7_konfirmasi_manual_tercatat`, `test_e2_*`, `test_e5_*` | Sedang: review menolak `COMPLETED` yang kodenya berubah sesudah `close` |
| Q10 | `plan_lock.py` `meta`/`block`/`set_block` (kunci ganda, sisip di dalam seksi) | semua subperintah | tidak | `test_e5_blok_completed_tulisan_tangan_tidak_konsisten` | Rendah: kunci ganda di metadata/blok kini FAIL |
| Q11 | `plan_lock.py` `digest`/`lock`/`verify` (`Hash-Scope: profile+body`), `plan/SKILL.md` Guardrails | verify di execute/review | tidak | `test_d1_*`, `test_e3_*` | Rendah: rencana 0.4.0 tanpa `Hash-Scope` diverifikasi dengan rumus lama |
| Q12 | `plan_lock.py` `meta`/`block` (`strip` nilai) | semua | tidak | — | Nihil |
| Q13 | idem Q4 (nilai berawalan `-` lewat stdin) | lock/confirm/unlock/close/start | tidak | — | Nihil |
| Q14 | `plan_lock.py` `close`/`start`/`inconsistency` (`Verified-Hash`) | execute Fase 0, review prasyarat 1 | tidak | `test_e2_*` | Rendah |
| Q15 | `execute/SKILL.md` parameter `stop_on_error` | execute Fase 1 | tidak | — | Nihil |
| Q16 | `execute`/`review` SKILL parameter `plan_path` | execute, review | tidak | — | Nihil |
| Q17 | `profile/SKILL.md` Fase 4 | profile | tidak | — | Nihil |
| Q18 | 6× SKILL Koeksistensi, README | semua skill | pemisah = `detect.py` be/fe (12 J9) | `test_skill_text.py::test_koeksistensi_*` | Nihil |
| Rilis | `plugin.json` quickdev 0.4.0 → 0.5.0, README, `flow/quickdev.md`, `ISSUES.md` | — | — | `test_lint_plugins.py` (M7 terhadap `93730e6`) | Nihil |

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| Q1 | Mode `awal`: `start` sendiri menjalankan `git status --porcelain -z -uall` dan menolak **sebelum menulis** bila ada berkas di luar direktori rencana dan `Profile:`; bukan repo git → FAIL. `resume`: `Base-Commit` bukan leluhur HEAD → `base_drift` (bukan FAIL; user memilih `base_ref`). | Predikat yang dinilai skrip tidak bisa didahului tulisan state. Rebase/reset bukan kesalahan eksekusi. |
| Q2 | Review tidak memanggil execute. Opsi *Remediasi otomatis* menutup review dengan perintah `/quickdev:execute <plan_path>` untuk diketik user di sesi yang sama; `review_findings` kosong → diambil dari laporan review `CHANGES_REQUIRED` terakhir di percakapan yang dijawab *Remediasi otomatis*. | `disable-model-invocation: true` (K7) dipertahankan. |
| Q3 | `start --findings` menulis `Remediation-State: OPEN`; `close` `COMPLETED`/`VERIFICATION_MANUAL_REQUIRED` menutupnya. Blok `IN_PROGRESS`/`BLOCKED` dengan ronde terbuka → mode `remediasi` lanjutan (ronde tidak bertambah, `Findings-<n>` dicetak ulang). | Ronde yang terputus bukan ronde baru; temuan tidak boleh hilang. |
| Q4/Q13 | Nilai `-` pada `--answer`, `--reason`, `--verification`, `--findings-text`, `--summary` dibaca dari stdin (satu per panggilan); SKILL memakai heredoc berkutip `<<'QD_EOF'`. `--blocked-step` dirapatkan jadi satu baris; `--profile` ber-karakter kontrol ditolak. | Heredoc berkutip tidak mengekspansi apa pun; teks user tetap "apa adanya". |
| Q6 | Profil mencatat `Baseline-Commit`. Execute mode `awal`: bila berbeda dari `Base-Commit`, jalankan baseline segar sebelum mutasi (`fresh_baseline`, default `true`) dan kunci ringkasannya dengan `plan_lock.py baseline` (sah hanya di HEAD = `Base-Commit`, tree bersih). Galat dicocokkan per berkas + aturan/kode/nama test (multiset), tanpa nomor baris. | Padanan 12 J13 (baseline mencatat `head`). Nomor baris bergeser saat berkas yang sama disunting. |
| Q5 | Execute: baris profil `SKIPPED` (ditolak user) → `AskUserQuestion` sebelum dijalankan; semua perintah bertimeout 300000 ms; migrasi/perintah pengubah skema-data dilarang di Iron Law. Profil mencatat alasan `SKIPPED` di Known issues. | Izin di profile tidak boleh hilang di execute. |
| Q7 | Heading `## `, blok, dan langkah di dalam code fence (```` ``` ````/`~~~`) diabaikan; fence tak tertutup → FAIL. Normalisasi sidik tidak diubah. | Rencana 0.4.0 yang sedang berjalan tetap lolos `verify`. |
| Q8 | `save` menyalin mode berkas asli dan tidak menulis bila isi tidak berubah. | `mkstemp` membuat 0600. |
| Q9/Q14 | `close` `COMPLETED`/`VERIFICATION_MANUAL_REQUIRED` menulis `Verified-Hash` (= `Plan-Hash`) dan `Tree-Hash` (sidik isi berkas yang berbeda dari `Base-Commit` + untracked, tanpa direktori rencana dan profil). Berbeda sesudahnya → `inconsistency` (review menolak), `start` → `resume` (verifikasi basi), `confirm` FAIL. Blok lama tanpa field tidak dinilai. | Klaim verifikasi terikat pada isi yang diverifikasi. Sidik berbasis isi, bukan teks diff (tahan konfigurasi git dan commit sesudah close). |
| Q10 | Kunci metadata dikenal atau kunci blok yang ganda → FAIL rapi; pembacaan = kemunculan pertama (sama dengan penulis); kunci baru disisip di akhir seksi blok. | Satu nilai, satu vonis (selaras 12 J31). |
| Q11 | Lock baru menulis `Hash-Scope: profile+body`; sidik mencakup baris `Profile:`. Tanpa `Hash-Scope` → rumus lama. Menghapus atau menambah penanda membuat sidik tidak cocok. | `Profile:` menentukan pembanding regresi; rencana lama tidak dipaksa approval ulang. |
| Q12 | Nilai metadata/blok di-`strip`. | `Status: DRAFT ` bukan alasan FAIL. |
| Q15 | `stop_on_error: false`: langkah gagal dicatat, langkah yang tidak bergantung padanya dilanjutkan, penutupan `BLOCKED` di langkah gagal pertama. | Perilaku sebelumnya tidak terdefinisi. |
| Q16 | `plan_path` kosong → rencana dari ringkasan quickdev terakhir di percakapan; tidak ada → daftar `plan/*.md` + `status --json`, tanya bila > 1. | — |
| Q17 | Profile Fase 4 hanya memakai blok gerbang di konteks sesi; rujukan `<plugin>/hooks/detect.py` dihapus. | Path plugin lain tidak diketahui dari quickdev. |
| Q18 | Pemisah `.claude/workflow` = spasi, koma, atau baris. | Selaras `detect.py` (12 J9). |

---

## Tahap 1 — Parser & penulisan `plan_lock.py`

- [x] **Q4 [Tinggi]** Template `--answer "<jawaban user apa adanya>"`, `--verification "<…>"`, `--findings-text "<…>"` berkutip ganda: backtick dan `$` dieksekusi shell (T5: `Approval:` tercatat hasil `whoami` dan `$HOME`). Temuan review memuat backtick karena STYLE mewajibkannya.
- [x] **Q7 [Sedang]** Parser tidak sadar code fence: `## Deployment` di fence Section 3 memotong langkah; 3 langkah terbaca 1 dan `close COMPLETED` lolos dengan 2 langkah `[ ]` (T3; `plan_lock.py:79-82`).
- [x] **Q8 [Sedang]** Setiap `save` mengubah mode rencana jadi 0600 (T2; `mkstemp` di `plan_lock.py:116`); `start` mode `selesai`/`manual` menulis ulang berkas tanpa perubahan.
- [x] **Q10 [Rendah]** Newline di `--blocked-step` menyisipkan `- Status: COMPLETED` (T6); `block()` memakai kemunculan terakhir, `set_block()` menyunting yang pertama; kunci blok baru ditambahkan di akhir berkas, bukan akhir seksi.
- [x] **Q11 [Rendah]** `Profile:` di luar sidik: mengganti profil sesudah approval mengganti daftar galat bawaan tanpa terdeteksi.
- [x] **Q12 [Rendah]** `Status: DRAFT ` (spasi ujung) → ``LOCK FAIL: Status `DRAFT ` bukan DRAFT`` (T7).
- [x] **Q13 [Rendah]** Nilai berawalan `-` (`--answer "-y"`) ditolak argparse (T8).

## Tahap 2 — Mesin state `plan_lock.py`

- [x] **Q1 [Tinggi]** `start` mode `awal` menulis `IN_PROGRESS` + `Base-Commit` sebelum predikat tree bersih dinilai; user meng-commit perubahan lain → `resume` dengan base lama → `git diff <base>` memuat `src/unrelated.ts` (T1; `plan_lock.py:229-232`). Base yang bukan leluhur HEAD (rebase) tidak terdeteksi.
- [x] **Q3 [Tinggi]** Ronde remediasi terputus (sesi putus / `BLOCKED` Failure path 5): `start --findings` → `START FAIL: remediasi menuntut Status COMPLETED`; tanpa flag → `resume` semua `[x]` → `COMPLETED`, `Findings-<n>` terabaikan dan jatah ronde terpakai (T4; `plan_lock.py:205-207`).
- [x] **Q6 [Tinggi] (skrip)** Tidak ada tempat mengunci baseline segar yang terikat `Base-Commit`.
- [x] **Q9 [Sedang]** `close` tidak mengikat klaim verifikasi pada isi kode; suntingan sesudah `COMPLETED` tetap membawa `Verification: lolos` sampai commit.
- [x] **Q14 [Sedang]** Revisi yang hanya mengubah Section 1/2/4 (tanpa langkah baru) → mode `selesai`; strategi verifikasi baru tidak pernah dijalankan.

## Tahap 3 — Prosa, template, rilis

- [x] **Q2 [Tinggi]** Review Fase 5 opsi *Remediasi otomatis* "memanggil `quickdev:execute`", padahal keenam skill `disable-model-invocation: true`; `review_findings` tanpa fallback → `/quickdev:execute plan/x.md` jatuh ke mode `selesai`.
- [x] **Q5 [Tinggi]** Execute Fase 3: `SKIPPED` → "jalankan sekarang" tanpa `AskUserQuestion` dan tanpa timeout, padahal `SKIPPED` bisa berarti user menolak "menyentuh DB/jaringan"; larangan migrasi hanya ada di profile.
- [x] **Q6 [Tinggi] (prosa)** Baseline profil tidak mencatat commit; galat dari commit lain sesudah profiling = regresi tugas ini. Known issues `berkas:baris` bergeser saat berkas yang sama disunting → galat bawaan dianggap regresi.
- [x] **Q15 [Rendah]** `stop_on_error: false` tidak terdefinisi.
- [x] **Q16 [Rendah]** `plan_path` wajib tanpa fallback saat `/quickdev:execute` diketik tanpa argumen.
- [x] **Q17 [Rendah]** Profile Fase 4 merujuk `<plugin>/hooks/detect.py` yang path-nya tidak diketahui quickdev.
- [x] **Q18 [Rendah]** SKILL menyebut pemisah `.claude/workflow` "spasi/baris"; `detect.py` juga menerima koma.
- [x] **Rilis** quickdev 0.5.0; README, `flow/quickdev.md`, `ISSUES.md`.

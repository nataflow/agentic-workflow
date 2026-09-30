# Langkah 16 — Keluaran chat gerbang approval diringkas (S1–S7)

Sumber: keluhan pemakai 2026-09-30 — keluaran chat semua plugin terlalu panjang saat dokumen diajukan untuk
disetujui. Yang diminta: ringkasan 3–4 kalimat lalu opsi setujui atau revisi. Isi dokumen di disk tidak berubah.
Basis kode plugin: commit `98b0031` (analyst 0.11.0, backend 0.12.0, frontend 0.11.0, quickdev 0.7.0).

**Status (2026-09-30):** S1–S7 selesai di branch `feat/16-ringkasan-chat-gerbang`. Lint
`--base origin/main` 0 FAIL. Suite penuh: 1976 lulus, 2 gagal — keduanya test pin versi yang sudah merah di
`main` sebelum langkah ini (lihat Di luar cakupan). Versi: analyst 0.12.0, backend 0.13.0, frontend 0.12.0,
quickdev 0.8.0.

Selisih pelaksanaan terhadap rencana:

- `business-analysis/templates/brd-template.md` tidak diubah. Aturan `BM-{n}` di sana ("disajikan ke user
  sebagai hasil bisnis yang diklaim") tetap benar, karena ringkasan eksekutif baru tetap menyebut `BM-{n}`.
- Header versi `flow/*.md` dan tabel versi `README.md` akar sudah basi sebelum langkah ini (mis. analyst
  tertulis 0.8.1). Keduanya disetel ke versi baru sekaligus.
- `{previous_report}` ronde 2 ketiga reviewer backend kini diisi dari berkas review, dibaca sebelum balikan
  ronde 2 menimpanya. Sebelumnya slot ini bergantung pada laporan ronde 1 yang masih ada di context.

## Tujuan

1. Tiap gerbang approval dokumen menyajikan **ringkasan gerbang** (Kontrak di bawah), bukan salinan isi
   dokumen. Rinciannya tetap di berkas dan user membukanya lewat path yang disebut.
2. Butir yang sengaja dipaksa muncul oleh gerbang, karena tidak ada gerbang hilir yang memeriksanya lagi,
   tetap menuntut keputusan eksplisit. Bentuknya pertanyaan satu baris di `AskUserQuestion`, bukan paragraf.
3. Khusus backend: blok review reviewer (`## BRD Review`, `## PRD Review`, `## Brief Review`) tidak lagi
   dicetak utuh di chat sebagai laporan penutup hop. Blok ditulis ke berkas, dan `backend:analyst` membacanya
   dari sana.
4. Skrip approval (`ticket.py approve`, `chain.py approve`, `plan_lock.py lock`, commit `docs(spec): approve …`)
   dan opsi berkonsekuensinya tidak berubah.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan prosa → suite penuh → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | S1 (analyst), S2 (frontend), S3 (quickdev), S4 (backend) | Format ringkasan gerbang untuk semua plugin lebih dulu; ini keluhan utamanya. |
| 2 | S5 (blok review backend ke berkas), S6 (tabel brief ganda backend) | Laporan antar-skill backend; mengubah predikat masuk `backend:analyst`, sehingga dipisah dari tahap 1. |
| 3 | S7 (dokumen + versi) | `flow/*.md`, README, `plugin.json` keempat plugin. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada
dan harus disesuaikan, bukan test baru. Tidak ada test yang mengunci prosa langkah "Sajikan …" di gerbang mana
pun (diperiksa: `tests/**/*.py`).

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| S1 | `analyst/skills/spec/SKILL.md` (Phase 0 draft tertunda, Phase 5 butir 1) | model, user | tidak | — | Rendah: `ticket.py approve` dan opsinya tidak berubah. |
| S2 | `frontend/skills/{ux-design,ui-design,contract,plan}/SKILL.md` (langkah sajian gate) | model, user | tidak | — | Rendah: `chain.py approve` tidak berubah; asumsi default tetap disebut di ringkasan (README § Questions Deliberately Not Asked). |
| S3 | `quickdev/skills/plan/SKILL.md` (Fase 3), `quickdev/skills/clarify/SKILL.md` (`skip_if_clear`) | model, user | tidak | `tests/quickdev/test_08d_text.py`, `test_skill_text.py` (tidak menyentuh kalimat yang diubah) | Rendah: `plan_lock.py lock` hanya menuntut jawaban tidak kosong, sehingga label opsi `AskUserQuestion` sah sebagai `--answer`. |
| S4 | `backend/skills/analyst/SKILL.md` (Fase 4 butir 3), `analyst/references/chain-rules.md` (§4 butir 3–4), `debug/SKILL.md` (Fase 5) | model, user | tidak | — | Sedang: predikat J (keputusan `BR-DISANGGAH` tercatat di Fase 4) kini dipenuhi lewat jawaban pertanyaan tersendiri, bukan paragraf. |
| S5 | `backend/skills/business-analysis/{SKILL.md,dispatcher/reviewer.md}`, `system-analysis/{SKILL.md,dispatcher/reviewer.md}`, `plan/{SKILL.md,dispatcher/reviewer.md,references/review-and-commit.md}`, `analyst/SKILL.md` (Fase 3 butir 2, Fase 4 butir 0, Fase 6 predikat C/D/E), `analyst/references/chain-rules.md` (§4 butir 0), `agents/{brd,prd,brief}-reviewer.md` (kalimat penutup Format Output) | `backend:analyst` (predikat masuk gerbang dan predikat C/D/E) | tidak | — | Sedang: predikat masuk berpindah dari laporan chat ke berkas. Resume sesi justru membaik: berkas bertahan, sedangkan chat hilang. |
| S6 | `backend/skills/plan/SKILL.md` (Fase 5 butir 3) | user | tidak | — | Rendah: tabel brief tetap disajikan `architect` Fase 2 sebelum eksekusi. |
| S7 | `flow/{analyst,backend,frontend,quickdev}.md`, `README.md` (tabel versi), `.claude-plugin/plugin.json` ×4 | manusia, lint M7 | ya (versi) | `test_lint_plugins.py` | Nihil |

Yang **tidak** diubah: skrip Python mana pun, hook, template dokumen (isi berkas di disk), validator, format
keluaran reviewer (`## … Review`), dan seluruh baris `Output [REQUIRED]` yang sudah satu baris saat sukses.

Lokasi berkas review S5 — `{taskdir}/.explore/review/<brd|prd|brief>.md` — dipilih karena:

- `.explore/` diabaikan git lewat baris `.gitignore` milik `backend:profile` (Fase 5 butir 4), sehingga tidak
  pernah di-stage atau di-commit;
- `is_scratch` (`precondition_lib.py`, `verify_scope.py`) memperlakukan `backenddev/docs/<taskdir>/.explore/**`
  termasuk subdirektori sebagai laci kerja, sehingga tidak dihitung tree kotor oleh gerbang git mana pun;
- `sync_payload.py` tidak pernah menyertakan `.explore/` ke nataflow;
- panen laci tidak rekursif: `code-explorer` Tahap 0 `Glob <laci>/*.md` dan `validate_briefs.py` `laci.glob("*.md")`,
  sehingga subdirektori `review/` tidak terbaca sebagai laporan explorer.

## Keputusan

- **Format ditulis di tiap gerbang, bukan di satu berkas rujukan.** Aturannya pendek (dua kalimat), dan
  prosa di langkah gerbang dibaca langsung tanpa satu pembacaan berkas tambahan. Keempat plugin disalin
  terpisah ke cache plugin, jadi berkas rujukan bersama lintas plugin memang tidak mungkin.
- **Butir keputusan wajib menjadi pertanyaan, bukan kalimat ringkasan.** `BR-DISANGGAH` dan asumsi aktif
  `sementara dipakai:` hidup di `## Open questions` yang beranggaran tiga entri, sehingga pertanyaan
  persetujuan ditambah butir keputusan tidak pernah melewati batas empat pertanyaan per `AskUserQuestion`.
- **Konfirmasi fakta dan failure path di luar cakupan.** `analyst:elicit` Phase 4, `backend:business-analysis`
  Fase 3, dan `backend:system-analysis` Fase 7 meminta user mengoreksi fakta satu per satu (angka, ambang,
  literal pesan); meringkasnya menghapus isi yang dikonfirmasi. Sajian BLOCKER saat plafon habis juga tetap,
  karena daftarnya pendek dan itulah bahan keputusan user.
- **Kesegaran berkas review dijaga urutan, bukan sidik.** Hop menimpa berkas tiap ronde, dan penulis dilarang
  meng-commit draft sebelum verdict `Approved`. Batas ini sama dengan yang sudah diakui `chain-rules.md` §4
  butir 0: penulis dan pemeriksa berjalan di runtime yang sama.
- **Tabel brief cukup sekali.** `backend:plan` Fase 5 dan `backend:architect` Fase 2 sama-sama mencetak tabel
  brief. Yang dipertahankan milik `architect`, karena tabel itu dibaca tepat sebelum eksekusi.

## Kontrak — ringkasan gerbang

```
<ARTEFAK> DRAFT @ <sha> · <path>
<3–4 kalimat: keputusan inti dokumen · asumsi atau risiko terbesar · verdict reviewer dalam satu frasa>
AskUserQuestion: <Setujui …> · Revisi (sebut poinnya) · <opsi khusus gate yang sudah ada>
               [+ satu pertanyaan per butir keputusan wajib, bila ada]
```

- Dilarang menyalin tabel, daftar AC/BR, mockup, atau blok review ke chat.
- User meminta rincian → sajikan seksi yang diminta saja, lalu ajukan ulang pertanyaan yang sama.

## S1 [Sedang] analyst — gerbang tiket menyalin kartu utuh
- [x] Selesai

`spec` Phase 5 butir 1 menyajikan judul, tipe, prioritas, user story, seluruh AC dan `BR-{n}`, Di Luar Cakupan,
Pertanyaan Terbuka, ditambah blok `## Ticket Review` apa adanya. Phase 0 (draft tertunda) juga menyajikan
`review_report` apa adanya. **Perubahan:** ringkasan gerbang dengan path `TICKET.md` dan `review.md`.
`ADVISORY [ELISITASI]` tetap disebut dalam satu kalimat beserta arahannya ke *Kembali ke elisitasi*.

## S2 [Sedang] frontend — empat gate menyalin isi dokumen
- [x] Selesai

`ux-design` Phase 5 (titik masuk, rute, batal/dirty, cabang error, tabel Data Demands), `ui-design` Phase 6
(mockup, P1–P3, enam cabang per layar, pemetaan data), `contract` Phase 6 (endpoint dan DTO, cache, layer, Files
Touched, tabel AC, verdict), dan `plan` Phase 5 (tabel unit). **Perubahan:** ringkasan gerbang per gate;
asumsi default tetap disebut sebagai asumsi agar user mengoreksinya saat menyetujui.

## S3 [Sedang] quickdev — approval rencana tanpa opsi terstruktur
- [x] Selesai

`plan` Fase 3 menyajikan daftar langkah atomik beserta path berkas, lalu meminta user mengetik "approve".
**Perubahan:** ringkasan gerbang dengan path `plan/<task>.md`, lalu `AskUserQuestion` *Setujui rencana* ·
*Revisi (sebut poinnya)*. `clarify` dengan `skip_if_clear: false`: ringkasan spesifikasi 3–4 kalimat.

## S4 [Tinggi] backend — ringkasan eksekutif BRD/PRD dan root cause
- [x] Selesai

`chain-rules.md` §4 butir 3 menuntut seluruh `BR-{n}`, `BM-{n}`, endpoint beserta request/response, dan matriks
permission disajikan. **Perubahan:** ringkasan eksekutif = ringkasan gerbang; tiap `BR-DISANGGAH: BR-{n}` dan
tiap asumsi aktif pembentuk kontrak menjadi satu pertanyaan tersendiri di `AskUserQuestion` yang sama. Jawaban
butir yang menuntut perubahan dokumen diperlakukan sebagai penolakan. `debug` Fase 5: ringkasan root cause 3–4
kalimat dan `AskUserQuestion` *Setujui root cause* · *Tolak (sebut arah lain)*; rantai kausal lengkap
mendarat di `RCA.md`.

## S5 [Tinggi] backend — blok review reviewer dicetak utuh di chat
- [x] Selesai

`business-analysis`, `system-analysis`, dan `plan` wajib melampirkan blok `## <BRD|PRD|Brief> Review` apa
adanya di laporan penutup, karena `analyst` memakainya sebagai predikat masuk. Blok itu muncul tepat di atas
ringkasan gerbang, sehingga momen approval tetap panjang. **Perubahan:** hop menulis blok balikan tiap ronde
apa adanya ke `{taskdir}/.explore/review/<brd|prd|brief>.md` (menimpa ronde sebelumnya). Baris penutup hop
menyebut path itu dan verdict-nya. `analyst` Fase 3 butir 2, Fase 4 butir 0, dan predikat C/D/E membaca verdict
serta jejak konkret dari berkas itu. Berkas absen, verdict bukan `Approved`, atau tanpa jejak → `## Failure
path` butir 3, sama seperti blok yang tidak dilampirkan.

## S6 [Rendah] backend — tabel brief dicetak dua kali
- [x] Selesai

`plan` Fase 5 butir 3 mencetak tabel ringkasan per brief, lalu `architect` Fase 2 mencetak tabel yang sama
sebelum eksekusi. **Perubahan:** `plan` menutup dengan baris Output satu barisnya saja.

## S7 [Rendah] Dokumen dan versi
- [x] Selesai

`flow/{analyst,backend,frontend,quickdev}.md` diselaraskan. Versi: analyst 0.12.0, backend 0.13.0, frontend
0.12.0, quickdev 0.8.0.

## Di luar cakupan

- Konfirmasi fakta (`analyst:elicit` Phase 4, `backend:business-analysis` Fase 3, `backend:system-analysis`
  Fase 7) dan sajian BLOCKER saat plafon habis — lihat Keputusan.
- Laporan penutup rantai (`REPORT.md`, `REVIEW.md`, ringkasan `quickdev:execute`/`review`): bukan gerbang
  approval, dan sudah dibatasi 17 baris atau satu baris.
- Test pin versi yang sudah merah di `main` sebelum langkah ini: `tests/frontend/test_12_orchestration.py::
  test_versi_rilis` dan `tests/quickdev/test_13_text.py::test_rilis_readme_dan_versi`.

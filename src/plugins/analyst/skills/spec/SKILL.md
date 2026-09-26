---
name: spec
description: Dipanggil analyst:elicit sesudah elisitasi CLOSED, atau analyst:intake untuk ticketdir berkeadaan SPEC/DRAFT/DRIFT dan perubahan tiket READY - menyusun kartu TICKET.md non-teknis (user story, acceptance criteria Given/When/Then, aturan bisnis), lolos ticket-reviewer dan persetujuan user, sebelum tiket diserahkan ke engineer
user-invocable: false
---

## THE IRON LAW

- Kartu `TICKET.md` disusun **hanya** dari `## Catatan Elisitasi` di berkas yang sama. Kebutuhan yang tidak ada di sana kembali ke `analyst:elicit`, tidak dikarang di sini.
- `READY` hanya ditulis `ticket.py approve` sesudah jawaban eksplisit user di `AskUserQuestion`; skrip menolak bila validator gagal, `elicitation` tidak `CLOSED`, atau vonis `ticket-reviewer` terakhir bukan `PASS` atas sidik kartu **dan** catatan elisitasi yang sama persis dengan sekarang.
- Nol isi teknis: tiket menyebut **apa** yang dilihat dan dilakukan pengguna, tidak pernah **bagaimana** sistem membangunnya.
- Field pembukuan frontmatter (`revision`, `revision_base`, `review`, `review_round`, `approved*`, `reopen*`) dan `<ticketdir>/review.md` hanya ditulis `ticket.py`; saat menulis ulang body, nilainya disalin apa adanya.

## Precondition [REQUIRED]

1. Skrip: `ticket.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`; rubrik prioritas di bagian 4 `${CLAUDE_PLUGIN_ROOT}/skills/elicit/references/elicitation-guide.md`.
2. **Perubahan tiket `READY`/`DRIFT`** (`change_request` terisi atau keadaan `DRIFT`): konfirmasi ke user lewat `AskUserQuestion` bahwa tiket dibuka ulang, lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py reopen --ticketdir <ticketdir> --reason "<change_request atau DRIFT>"`.
3. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py check --gate spec --ticketdir <ticketdir>`. `PASS` → baca baris `Terselesaikan:` (`root`, `type`, `git`, dan bila tiket sudah ada `revision`, `review_round`, `review_segar`, `review_basi`, `review_report`). `FAIL` → remediasi per `Tindakan`: elisitasi belum `CLOSED` → `analyst:elicit`.

## Parameter [REQUIRED]

- `ticketdir` — string — `[REQUIRED]` — ticketdir aktif.
- `change_request` — string — default `""` — perubahan yang diminta atas tiket `READY`, apa adanya.
- `external_ref` — string — default `"-"` — kunci atau tautan kartu Jira/Trello bila tiket ini disalin ke sana. Sesudah `READY` → `ticket.py ref --ticketdir <ticketdir> --ref <kunci>` (tanpa membuka ulang tiket); dilarang menyunting field ini dengan tangan.

## Workflow

### Phase 0 — Orientasi

- Baca `TICKET.md` utuh — catatan elisitasi dan kartu bila sudah ada. Keadaan `DRAFT` dengan `review_segar=ya` (draft tertunda yang belum diputuskan) → langsung Phase 5 tanpa menulis ulang, sajikan isi `review_report` apa adanya; `review_report=-` (vonis tercatat tanpa `--report`) → dispatch ulang reviewer satu ronde bila plafon masih ada, bila tidak sajikan hanya baris vonis.
- **`review_basi` memuat `elisitasi`** (catatan elisitasi berubah sesudah ronde terakhir, mis. kembali dari elisitasi yang dibuka ulang): jalankan `ticket.py revise --ticketdir <ticketdir>` lebih dulu — basis fakta baru membuka siklus revisi dan ronde review baru — lalu Phase 1. `review_basi=kartu` (atau `review_segar=tidak` lainnya) → Phase 2 atas draft yang ada.
- `change_request` menambah fakta yang tidak ada di catatan elisitasi (aturan, angka, aktor, istilah domain baru) → panggil `analyst:elicit` dengan `reopen_reason` = `change_request`, lalu kembali ke sini. Perubahan yang hanya redaksional atau memindahkan butir ke Di Luar Cakupan lanjut di sini.

### Phase 1 — Rumusan

1. **Judul**: hasil yang dirasakan pengguna, ≤ 12 kata, bukan nama fitur teknis.
2. **Prioritas**: pilar `Urgensi` dipetakan lewat rubrik bagian 4 panduan.
3. **Latar Belakang**: 2–4 kalimat dari `Masalah` (BUG: `Dampak`) — siapa, seberapa sering atau mahal, kenapa sekarang.
4. **User Story** (`FEATURE`/`IMPROVEMENT`): peran dari `Aktor`, kemampuan dari `Kondisi Diinginkan`, manfaat dari `Masalah`. **Laporan Bug** (`BUG`): salin pilar reproduksi, harapan, kejadian, dan dampak; teks layar dikutip dalam tanda kutip.
5. **Aturan Bisnis**: tiap fakta pilar `Aturan Bisnis` menjadi satu `BR-{n}`, angka dan istilah persis seperti di elisitasi.
6. **Acceptance Criteria** — sapu berurutan, satu AC per perilaku yang dapat diamati:
   - jalur utama tujuan pengguna;
   - tiap `BR-{n}`: sisi yang lolos dan sisi yang ditolak (sebut `(BR-n)` di akhir baris);
   - tiap fakta `Kasus Khusus`, dan tiap peran terlarang di `Aktor`;
   - `BUG`: `Yang Diharapkan` sebagai `then`, dengan `Given` dari langkah reproduksi.
   Lebih dari 10 AC berarti lebih dari satu tujuan → `AskUserQuestion`: bagian mana yang tetap di tiket ini; sisanya ke `## Di Luar Cakupan` `— tiket terpisah`.
7. **Di Luar Cakupan**: pilar `Batas Cakupan` beserta alasannya.
8. **Pertanyaan Terbuka**: tiap `Q-{n}` `TIDAK MEMBLOKIR` yang tersisa, beserta asumsi yang dipakai AC.
9. **`domain_terms`**: milik `analyst:elicit` — dipakai apa adanya, dilarang ditambah dari sini (Failure path 3).

### Phase 2 — Tulis Draft

1. Sunting `<ticketdir>/TICKET.md`: ganti H1 kerja dengan judul final dan tulis kartu persis bagian 1 `templates/ticket-template.md` untuk tipenya di antara H1 dan `## Catatan Elisitasi`; isi `priority` dan `external_ref`. Seksi `## Catatan Elisitasi` beserta field frontmatter lain dibiarkan byte demi byte.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind ticket --ticketdir <ticketdir>` sampai `PASS`. Temuan kebocoran → rumuskan ulang sebagai perilaku yang terlihat; `domain_terms` hanya untuk istilah yang tercatat elisitasi.
3. Self-test semantik butir 11–15 template.

### Phase 3 — Review Independen

1. `review_round` sudah 2 → dilarang dispatch; lompat ke Phase 5 dengan BLOCKER tersisa (lihat `dispatcher/reviewer.md` gerbang masuk).
2. Muat `dispatcher/reviewer.md`, hidrasi slot `ticketdir`, `type`, `round` (`review_round` + 1), dan pada ronde 2 `previous_verdict` beserta `changed_sections`; dispatch `ticket-reviewer` (`subagent_type`: `analyst:ticket-reviewer`) langsung, tanpa skill pembungkus.
3. Catat balikan **seketika**, sebelum satu suntingan pun: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py review --ticketdir <ticketdir> --verdict <PASS|BLOCKED> --report - <<'EOF'`, lalu blok `## Ticket Review` reviewer apa adanya, lalu `EOF` (`--verdict DISPATCH_FAILED` tanpa `--report`). Skrip menyimpan sidik konten yang benar-benar dinilai reviewer dan bloknya ke `<ticketdir>/review.md`; menolak bila `- Verdict:` di blok berbeda dengan `--verdict`, atau bila `validate_doc.py` `ticket`/`elicit` `FAIL` (dispatch tidak sah). Suntingan sesudahnya membuat vonis itu basi dan menuntut ronde berikut. Tangani per tabel `### Penanganan Balikan` template itu.

### Phase 4 — Commit Draft

Repo git (`git=ya`): `git -C <root> add <ticketdir>/TICKET.md <ticketdir>/review.md` lalu `git -C <root> commit -m "docs(ticket): draft TICKET <slug>" -- <ticketdir>/TICKET.md <ticketdir>/review.md` (revisi: `revise TICKET <slug>`; `review.md` hanya bila ada). `<root>` dari `Terselesaikan:` — path ticketdir relatif root, bukan relatif cwd. Bukan repo git → lewati.

### Phase 5 — Persetujuan User

1. Sajikan tiket: judul, tipe, prioritas beserta alasannya, user story atau laporan bug, daftar AC dan `BR-{n}`, Di Luar Cakupan, Pertanyaan Terbuka — ditambah blok `## Ticket Review` terakhir apa adanya (isi `review_report`, yaitu `<ticketdir>/review.md`).
2. `AskUserQuestion`: *Setujui (READY)* — **hanya bila `review_segar=ya`** · *Revisi (sebut poinnya)* · *Kembali ke elisitasi* · *Tahan*. `review_segar=tidak` dengan plafon ronde habis → sajikan sebabnya tanpa opsi *Setujui*.
3. **Setujui** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py approve --ticketdir <ticketdir> --answer "<jawaban user apa adanya>"`. Skrip memateraikan `READY` dan meng-commit `TICKET.md` (beserta `review.md`) bila repo git. `FAIL` → sebab di keluaran; review basi dengan plafon ronde tersisa → Phase 3 ronde berikut; plafon ronde habis → sajikan sebabnya dan ajukan ulang pilihan *Revisi* (satu-satunya jalan membuka ronde baru) atau *Kembali ke elisitasi*.
4. **Revisi** → `ticket.py revise --ticketdir <ticketdir>` (plafon 3; mengosongkan vonis review) → perbarui draft → Phase 2–4 → ajukan ulang. Poin revisi yang menambah fakta baru → `analyst:elicit` dengan `reopen_reason`. Plafon habis → lingkup belum jelas: tawarkan *Kembali ke elisitasi* atau `ticket.py cancel` atas keputusan user.
5. **Kembali ke elisitasi** → `analyst:elicit` dengan `ticketdir` dan `reopen_reason` = alasan user.
6. **Tahan** → biarkan `DRAFT`; ticketdir muncul lagi di `ticket.py state`.

## Guardrails

- **ELISITASI SATU-SATUNYA SUMBER**: dilarang menambah aturan, batas, peran, notifikasi, atau kasus yang tidak ada di `## Catatan Elisitasi`, sekalipun "biasanya perlu".
- **AC TERAMATI**: `then` berupa teks layar, tombol, status, angka, atau pesan yang diterima — bukan "data tersimpan" atau "sistem memproses".
- **NOL TEKNIS**: dilarang menyebut penyimpanan, integrasi, teknologi, struktur data, estimasi, atau pembagian backend/frontend.
- **APPROVAL LEWAT SKRIP**: dilarang menulis `status: READY`, `approved_hash`, atau `review:` dengan tangan.
- **CATATAN MILIK ELICIT**: dilarang menyunting `## Catatan Elisitasi`, `elicitation`, atau `domain_terms` dari skill ini; tiap perubahan fakta lewat `analyst:elicit` dengan `reopen_reason`.
- **REVIEWER LEWAT TEMPLATE**: `ticket-reviewer` hanya lewat prompt terhidrasi `dispatcher/reviewer.md`; blok vonisnya diteruskan ke user tanpa parafrase.
- **ATOMIC COMMIT**: staging path eksplisit; dilarang `git add .`/`-A`, `--no-verify`, push.
- **RATIONALIZATION PREVENTION**:
  - "Reviewer cuma ADVISORY, langsung setujui saja tanpa ronde lagi" — menyerap advisory mengubah sidik konten; `approve` menolak vonis atas konten lama.
  - "User bilang oke di chat, saya set READY sendiri" — tanpa `approve`, sidik tidak dimateraikan dan suntingan sesudahnya tidak terdeteksi.
  - "Engineer pasti butuh detail tabelnya, saya tambahkan" — detail teknis milik `TASK.md` engineer; tiket yang memutuskan cara membangun mengikat engineer pada tebakan analis.
  - "AC-nya 14, tidak apa-apa" — tiket sebesar itu memuat lebih dari satu tujuan; pecah.

## Output [REQUIRED]

Tiket disetujui — tutup satu baris: `SPEC — READY · <ticketdir>/TICKET.md @<sidik> · <type> · <priority> · <n> AC · <n> BR · <commit <sha> | tanpa git> — serahkan ke engineer: backenddev:tech-lead dan/atau frontenddev:lead dengan ticket_source: <ticketdir>/TICKET.md (lihat README Serah Terima).` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### SPEC — <MENUNGGU KEPUTUSAN | TERTAHAN>
- **Draft**: <ticketdir>/TICKET.md · validator <PASS | FAIL> · review <PASS | BLOCKED> ronde <n>/2
- **Revisi**: <n>/3
- **BLOCKER tersisa**: <ringkas per butir> | —
- **Rute**: <menunggu jawaban user | analyst:elicit (reopen) | ditahan user>
```

## Failure path

1. **`elicitation` belum `CLOSED`**: hentikan; `analyst:elicit` menuntaskannya lebih dulu.
2. **Fakta elisitasi saling bertentangan** saat merumuskan AC: jangan memilih sendiri — `analyst:elicit` dengan `reopen_reason` menyebut kedua fakta.
3. **Validator kebocoran tidak kunjung `PASS`** karena istilah memang kosakata produk: dilarang menyunting catatan elisitasi atau `domain_terms` dari sini — panggil `analyst:elicit` dengan `reopen_reason` = `konfirmasi istilah domain: <istilah>`; sesudah istilah tercatat di `domain_terms` elisitasi, kembali ke Phase 0.
4. **Dispatch reviewer gagal dua kali**: tiket tidak dapat di-`approve`; sajikan draft dengan status `TERTAHAN` dan minta user mengulang sesi.
5. **`approve` gagal commit** (exit 3; hook, gpg, `.gitignore`): status `READY` sudah tertulis; sajikan baris `COMMIT GAGAL` apa adanya dan minta user meng-commit sendiri dengan perintah yang dicetak. Dilarang `--no-verify`.

## STYLE

- Imperatif aktif; tiket berbahasa peminta, kalimat aktif, satu perilaku per AC.
- Istilah tetap: Ticketdir, Acceptance Criteria (AC), Aturan Bisnis (BR), Sidik.

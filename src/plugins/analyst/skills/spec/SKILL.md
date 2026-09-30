---
name: spec
description: Dipanggil analyst:elicit sesudah elisitasi CLOSED, atau analyst:intake untuk ticketdir berkeadaan SPEC/DRAFT/DRIFT, perubahan tiket READY, dan pembatalan tiket - menyusun kartu TICKET.md non-teknis (user story, acceptance criteria Given/When/Then, aturan bisnis), lolos ticket-reviewer dan persetujuan user, sebelum tiket diserahkan ke engineer
user-invocable: false
---

## THE IRON LAW

- Kartu `TICKET.md` disusun **hanya** dari `## Catatan Elisitasi` di berkas yang sama. Kebutuhan yang tidak ada di sana kembali ke `analyst:elicit`, tidak dikarang di sini.
- `READY` hanya ditulis `ticket.py approve` sesudah jawaban eksplisit user di `AskUserQuestion`; skrip menolak bila validator gagal, `elicitation` tidak `CLOSED`, catatan elisitasi berbeda dari segel `ticket.py close`, atau vonis `ticket-reviewer` terakhir bukan `PASS` atas sidik kartu **dan** catatan elisitasi yang sama persis dengan sekarang.
- Nol isi teknis: tiket menyebut **apa** yang dilihat dan dilakukan pengguna, tidak pernah **bagaimana** sistem membangunnya.
- Field pembukuan frontmatter (`revision`, `revision_base`, `review`, `review_round`, `approved*`, `reopen*`, `request_hash`, `elicit_hash`, `elicit_log`) dan `<ticketdir>/review.md` hanya ditulis `ticket.py`; saat menulis ulang body, nilainya disalin apa adanya.

## Precondition [REQUIRED]

1. Skrip: `ticket.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`; rubrik prioritas di bagian 4 dan tabel bentuk hasil di bagian 6 `${CLAUDE_PLUGIN_ROOT}/skills/elicit/references/elicitation-guide.md`.
2. **Perubahan tiket `READY`/`DRIFT`** (`change_request` terisi atau keadaan `DRIFT`): konfirmasi ke user lewat `AskUserQuestion` bahwa tiket dibuka ulang, lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py reopen --ticketdir <ticketdir> --reason "<change_request atau DRIFT>"`.
3. **Pembatalan tiket** (`cancel_request` terisi): konfirmasi ke user lewat `AskUserQuestion` — tiket `READY` mungkin sudah diserahkan ke engineer lewat `ticket_source`, dan task cermin nataflow-nya ikut menjadi `cancelled` — lalu `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py cancel --ticketdir <ticketdir> --reason "<cancel_request>"`, ditambah `--force` hanya untuk tiket `READY` yang pembatalannya dikonfirmasi eksplisit. `CANCEL PASS` atas tiket yang pernah `READY` → jalankan prosedur `references/nataflow-sync.md` (15 A6). Tutup dengan baris `SPEC — BATAL` dan selesai; Workflow tidak dijalankan.
4. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py check --gate spec --ticketdir <ticketdir>`. `PASS` → baca baris `Terselesaikan:` (`root`, `type`, `git`, dan bila tiket sudah ada `revision`, `review_round`, `ronde`, `sidik`, `review_segar`, `review_basi`, `review_report`). `FAIL` → remediasi per `Tindakan`: elisitasi belum `CLOSED` → `analyst:elicit`; check 5 *elisitasi tanpa segel* (tiket lama) → `ticket.py close --ticketdir <ticketdir>` sekali; check 5 *catatan berubah sesudah ditutup* → dilarang menyegel ulang dari sini: pulihkan catatannya bila yang mengubah bukan elisitasi, atau `analyst:elicit` dengan `reopen_reason` yang menyebut perubahannya.

## Parameter [REQUIRED]

- `ticketdir` — string — `[REQUIRED]` — ticketdir aktif.
- `change_request` — string — default `""` — perubahan yang diminta atas tiket `READY`, apa adanya.
- `cancel_request` — string — default `""` — alasan pembatalan tiket atas keputusan user, apa adanya (Precondition 3).
- `external_ref` — string — default `"-"` — kunci atau tautan kartu Jira/Trello bila tiket ini disalin ke sana. Sesudah `READY` → `ticket.py ref --ticketdir <ticketdir> --ref <kunci>` (tanpa membuka ulang tiket); dilarang menyunting field ini dengan tangan. `ref` menolak tiket `DRIFT`, dan pada `DRAFT` hanya menulis field tanpa commit (ikut commit draft Phase 4).

## Workflow

### Phase 0 — Orientasi

- Baca `TICKET.md` utuh — catatan elisitasi dan kartu bila sudah ada. Keadaan `DRAFT` dengan `review_segar=ya` (draft tertunda yang belum diputuskan) → langsung Phase 5 tanpa menulis ulang; vonis ringkasan gerbangnya dibaca dari `review_report`; `review_report=-` (vonis tercatat tanpa `--report`) → dispatch ulang reviewer satu ronde bila plafon masih ada, bila tidak sajikan hanya baris vonis.
- **`review_basi` memuat `elisitasi`** (catatan elisitasi berubah sesudah ronde terakhir, mis. kembali dari elisitasi yang dibuka ulang): jalankan `ticket.py revise --ticketdir <ticketdir>` lebih dulu — basis fakta baru membuka siklus revisi dan ronde review baru — lalu Phase 1. `review_basi=kartu` (atau `review_segar=tidak` lainnya) → Phase 2 atas draft yang ada.
- `change_request` menambah fakta yang tidak ada di catatan elisitasi (aturan, angka, aktor, istilah domain baru) → panggil `analyst:elicit` dengan `reopen_reason` = `change_request`, lalu kembali ke sini. Perubahan yang hanya redaksional atau memindahkan butir ke Di Luar Cakupan lanjut di sini.

### Phase 1 — Rumusan

1. **Judul**: perintah kerja yang dibaca engineer di papan task, ≤ 12 kata, berpola `<kata kerja> <objek domain> <kualifikasi>`. Kata kerja per tipe: `FEATURE` — Buat, Tambah, Tampilkan, Izinkan; `IMPROVEMENT` — Ubah, Perluas, Tampilkan, Sederhanakan; `BUG` — Perbaiki, diikuti gejala dan tempatnya. Kata kerjanya menyasar hasil yang teramati, bukan cara membangun: `Tampilkan QTY Received per produk di daftar Purchase Order`, bukan `Tambah kolom qty received di tabel PO`. Siapa dan kenapa milik User Story, bukan judul — judul yang bercerita tentang keinginan aktor (`Admin Finance dapat …`, `… ingin …`) mengulang User Story. Objek judul mengikuti bentuk hasil (panduan bagian 6): `Buat API daftar Purchase Order …` untuk API, `Tampilkan … di <layar>` untuk layar. Istilah domain, nama entitas, menu, layar, dan kolom dipakai persis seperti di elisitasi — yang berbahasa Inggris tidak diterjemahkan: "created at di report order hingga detik" → `Tampilkan Created At hingga detik di Report Order`, bukan `Tampilkan waktu dibuat hingga detik di Laporan Pesanan`. Hanya kata penghubungnya yang berbahasa Indonesia.
2. **Prioritas**: pilar `Urgensi` dipetakan lewat rubrik bagian 4 panduan.
3. **Latar Belakang**: 2–4 kalimat dari `Masalah` (BUG: `Dampak`) — siapa, seberapa sering atau mahal, kenapa sekarang.
4. **User Story** (`FEATURE`/`IMPROVEMENT`): peran dari `Aktor`, kemampuan dari `Kondisi Diinginkan`, manfaat dari `Masalah`. Peran mengikuti baris `Bentuk hasil:` (panduan bagian 6) — bentuk API menulis pemanggilnya, bukan peran bisnis yang datanya dibatasi. Catatan tanpa baris itu (ditutup sebelum aturan ini) → baca bentuknya dari isi `Kondisi Diinginkan`; tidak tersurat → `analyst:elicit` dengan `reopen_reason` = `konfirmasi bentuk hasil`. **Laporan Bug** (`BUG`): salin pilar reproduksi, harapan, kejadian, dan dampak; teks layar dikutip dalam tanda kutip.
5. **Aturan Bisnis**: tiap fakta pilar `Aturan Bisnis` menjadi satu `BR-{n}`, angka dan istilah persis seperti di elisitasi.
6. **Acceptance Criteria** — sapu berurutan, satu AC per perilaku yang dapat diamati:
   - jalur utama tujuan pengguna;
   - tiap `BR-{n}`: sisi yang lolos dan sisi yang ditolak (sebut `(BR-n)` di akhir baris);
   - tiap fakta `Kasus Khusus`, dan tiap peran terlarang di `Aktor`;
   - `BUG`: `Yang Diharapkan` sebagai `then`, dengan `Given` dari langkah reproduksi.
   `then` mengikuti bentuk hasil (panduan bagian 6): layar → yang terlihat; API → data yang dikembalikan atau penolakannya; proses otomatis → yang diterima atau status yang berubah; laporan → kolom, baris, dan totalnya.
   Lebih dari 10 AC berarti lebih dari satu tujuan → `AskUserQuestion`: bagian mana yang tetap di tiket ini; sisanya ke `## Di Luar Cakupan` `— tiket terpisah`.
7. **Di Luar Cakupan**: pilar `Batas Cakupan` beserta alasannya.
8. **Pertanyaan Terbuka**: tiap `Q-{n}` `TIDAK MEMBLOKIR` yang tersisa, dengan ID yang sama seperti di catatan, beserta asumsi yang dipakai AC. Validator menagih kedua himpunan ID sama.
9. **`domain_terms`**: milik `analyst:elicit` — dipakai apa adanya, dilarang ditambah dari sini (Failure path 3).

### Phase 2 — Tulis Draft

1. Sunting `<ticketdir>/TICKET.md`: ganti H1 kerja dengan judul final dan tulis kartu persis bagian 1 `templates/ticket-template.md` untuk tipenya di antara H1 dan `## Catatan Elisitasi`; isi `priority` dan `external_ref`. Seksi `## Catatan Elisitasi` beserta field frontmatter lain dibiarkan byte demi byte.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind ticket --ticketdir <ticketdir>` sampai `PASS`. Temuan kebocoran → rumuskan ulang sebagai perilaku yang terlihat; `domain_terms` hanya untuk istilah yang tercatat elisitasi.
3. Self-test semantik butir 11–16 template.

### Phase 3 — Review Independen

1. `ronde=habis` (plafon 2 ronde per revisi) → dilarang dispatch; lompat ke Phase 5 dengan BLOCKER tersisa (lihat `dispatcher/reviewer.md` gerbang masuk).
2. Muat `dispatcher/reviewer.md`, hidrasi slot `ticketdir`, `type`, `round` (`ronde` dari `check --gate spec` — sudah memperhitungkan siklus ronde baru), `sidik`, dan pada ronde 2 `previous_verdict` beserta `changed_sections`; dispatch `ticket-reviewer` (`subagent_type`: `analyst:ticket-reviewer`) langsung, tanpa skill pembungkus.
3. Catat balikan **seketika**, sebelum satu suntingan pun: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py review --ticketdir <ticketdir> --verdict <PASS|BLOCKED> --report - <<'EOF'`, lalu blok `## Ticket Review` reviewer apa adanya, lalu `EOF` (`--verdict DISPATCH_FAILED` tanpa `--report`; vonis lain tanpa blok ditolak). Skrip menyimpan sidik konten yang benar-benar dinilai reviewer dan bloknya ke `<ticketdir>/review.md`; menolak bila `- Verdict:` di blok berbeda dengan `--verdict`, bila `- Sidik:` di blok (disalin reviewer dari slot `{sidik}` prompt) berbeda dengan sidik disk, bila catatan elisitasi berbeda dari segelnya, bila `validate_doc.py` `ticket`/`elicit` `FAIL` (dispatch tidak sah), atau bila blok tidak konsisten (`- BLOCKER:` tidak sama dengan jumlah butir di bawah `**BLOCKER:**`, `PASS` ber-BLOCKER, `BLOCKED` tanpa BLOCKER, `- Ronde:` bukan ronde yang dicatat). Suntingan sesudahnya membuat vonis itu basi dan menuntut ronde berikut. Tangani per tabel `### Penanganan Balikan` template itu.

### Phase 4 — Commit Draft

`python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py commit --ticketdir <ticketdir> --stage draft`. Skrip men-stage `TICKET.md` (beserta `review.md` bila ada) secara eksplisit dengan subjek `docs(ticket): draft TICKET <slug>` (sesudah `revise`: `revise TICKET <slug>`); dilarang `git add`/`git commit` dengan tangan. Bukan repo git (`tanpa git`) atau ticketdir diabaikan `.gitignore` (`git=diabaikan`, keluaran `commit diabaikan git`) → skrip melewati commit. Exit 3 → sajikan baris `COMMIT GAGAL` apa adanya seperti Failure path 5.

### Phase 5 — Persetujuan User

1. Sajikan **ringkasan gerbang**, bukan isi kartu: baris `TICKET — DRAFT · <ticketdir>/TICKET.md · review <review_report>`, lalu 3–4 kalimat — judul, tipe, dan prioritas beserta alasannya; inti user story atau laporan bug; jumlah AC dan `BR-{n}` beserta aturan yang paling menentukan dan asumsi Pertanyaan Terbuka bila ada; vonis reviewer dalam satu frasa (mis. `PASS · 2 ADVISORY`). Daftar AC, `BR-{n}`, Di Luar Cakupan, dan blok `## Ticket Review` tetap di berkas; dilarang menyalinnya ke chat. Ada `ADVISORY [ELISITASI]` → satu kalimat: itu pertanyaan yang belum pernah diajukan ke peminta, dijawab lewat *Kembali ke elisitasi*. User meminta rincian → sajikan seksi yang diminta saja, lalu ajukan ulang pertanyaan butir 2.
2. `AskUserQuestion`: *Setujui (READY)* — **hanya bila `review_segar=ya`** · *Revisi (sebut poinnya)* · *Kembali ke elisitasi* · *Tahan*. `review_segar=tidak` dengan plafon ronde habis → sajikan sebabnya tanpa opsi *Setujui*.
3. **Setujui** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py approve --ticketdir <ticketdir> --answer "<jawaban user apa adanya>"`. Skrip memateraikan `READY` dan meng-commit `TICKET.md` (beserta `review.md`) bila repo git dan ticketdir tidak diabaikan `.gitignore`. `FAIL` → sebab di keluaran; review basi dengan plafon ronde tersisa → Phase 3 ronde berikut; plafon ronde habis → sajikan sebabnya dan ajukan ulang pilihan *Revisi* (satu-satunya jalan membuka ronde baru) atau *Kembali ke elisitasi*.
4. **Sinkron nataflow** — tepat sesudah `approve` exit 0 atau exit 3 (`READY` tertulis, commit gagal), sebelum baris penutup: jalankan prosedur `references/nataflow-sync.md` apa adanya atas `<ticketdir>`, dengan `ticket.py` dari Precondition. Hasilnya satu segmen `nataflow …` di baris penutup. `approve` exit 1 → langkah ini tidak berjalan.
5. **Revisi** → `ticket.py revise --ticketdir <ticketdir>` (plafon 3; mengosongkan vonis review) → perbarui draft → Phase 2–4 → ajukan ulang. Poin revisi yang menambah fakta baru → `analyst:elicit` dengan `reopen_reason`. Plafon habis → lingkup belum jelas: tawarkan *Kembali ke elisitasi* atau `ticket.py cancel` atas keputusan user; tiket yang pernah `READY` (dibuka ulang) lalu dibatalkan → prosedur `references/nataflow-sync.md` sesudahnya.
6. **Kembali ke elisitasi** → `analyst:elicit` dengan `ticketdir` dan `reopen_reason` = alasan user.
7. **Tahan** → biarkan `DRAFT`; ticketdir muncul lagi di `ticket.py state`.

## Guardrails

- **ELISITASI SATU-SATUNYA SUMBER**: dilarang menambah aturan, batas, peran, notifikasi, atau kasus yang tidak ada di `## Catatan Elisitasi`, sekalipun "biasanya perlu".
- **AC TERAMATI**: `then` berupa teks layar, tombol, status, angka, atau pesan yang diterima — bukan "data tersimpan" atau "sistem memproses".
- **NOL TEKNIS**: dilarang menyebut penyimpanan, integrasi, teknologi, struktur data, estimasi, atau pembagian backend/frontend.
- **APPROVAL LEWAT SKRIP**: dilarang menulis `status: READY`, `approved_hash`, `approved_seal`, atau `review:` dengan tangan.
- **CATATAN MILIK ELICIT**: dilarang menyunting `## Catatan Elisitasi`, `elicitation`, atau `domain_terms`, dan dilarang menjalankan `ticket.py close` kecuali adopsi segel tiket lama (check 5 *elisitasi tanpa segel*; skrip menolaknya bila catatan berubah sesudah review terakhir), dari skill ini; tiap perubahan fakta lewat `analyst:elicit` dengan `reopen_reason`. Suntingan catatan di luar jalur itu ditolak `check`, `review`, dan `approve` lewat segel `elicit_hash`.
- **REVIEWER LEWAT TEMPLATE**: `ticket-reviewer` hanya lewat prompt terhidrasi `dispatcher/reviewer.md`; blok vonisnya diteruskan ke user tanpa parafrase.
- **SINKRON LEWAT SKRIP**: argumen tool nataflow hanya dari keluaran `ticket.py sync-payload`, dikirim apa adanya; dilarang merangkai judul, deskripsi, atau metadata sendiri, dan dilarang mengirim status selain `task_status` pembatalan yang diterbitkan skrip.
- **ATOMIC COMMIT**: commit hanya lewat `ticket.py` (staging path eksplisit); dilarang `git add .`/`-A`/`-f`, `--no-verify`, push. Ticketdir yang diabaikan `.gitignore` memang tidak di-commit — itu pilihan repo, bukan kegagalan.
- **RATIONALIZATION PREVENTION**:
  - "Reviewer cuma ADVISORY, langsung setujui saja tanpa ronde lagi" — menyerap advisory mengubah sidik konten; `approve` menolak vonis atas konten lama.
  - "User bilang oke di chat, saya set READY sendiri" — tanpa `approve`, sidik tidak dimateraikan dan suntingan sesudahnya tidak terdeteksi.
  - "Engineer pasti butuh detail tabelnya, saya tambahkan" — detail teknis milik `TASK.md` engineer; tiket yang memutuskan cara membangun mengikat engineer pada tebakan analis.
  - "AC-nya 14, tidak apa-apa" — tiket sebesar itu memuat lebih dari satu tujuan; pecah.

## Output [REQUIRED]

Tiket disetujui — tutup satu baris: `SPEC — READY · <ticketdir>/TICKET.md @<sidik> · <type> · <priority> · <n> AC · <n> BR · <commit <sha> | tanpa git | diabaikan git> · nataflow <dibuat #<code> | diperbarui #<code> | dilewati | GAGAL: <sebab>> — serahkan ke engineer: backend:tech-lead dan/atau frontend:lead dengan ticket_source: <ticketdir>/TICKET.md (lihat README Serah Terima).` Segmen `nataflow` berasal dari Phase 5 butir 4; `GAGAL` tidak mengubah `READY` maupun serah terimanya. `diabaikan git` bersama `nataflow GAGAL` atau `dilewati` → tambahkan `(tiket hanya di disk ini)` sesudah segmen `nataflow`: tidak ada salinan lain sampai sinkron diulang. Tiket dibatalkan (Precondition 3) — tutup satu baris: `SPEC — BATAL · <ticketdir> · <commit <sha> | tanpa git | diabaikan git> · nataflow <dibatalkan #<code> | dilewati | GAGAL: <sebab>>`; tiket yang belum pernah `READY` tidak menjalankan sinkron dan segmennya dihapus. Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

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
5. **`approve` atau `commit` gagal commit** (exit 3; hook, gpg, index terkunci): isinya sudah tertulis (`approve`: status `READY`); sajikan baris `COMMIT GAGAL` apa adanya dan minta user meng-commit sendiri dengan perintah yang dicetak. Dilarang `--no-verify`. Ticketdir yang diabaikan `.gitignore` tidak pernah sampai ke sini: skrip melewati commit-nya.
6. **Sinkron nataflow `GAGAL`** (server MCP tidak tersedia, tool galat, config `.claude/nataflow.json` atau `analyst/nataflow.json` rusak atau keduanya berbeda isi, task kembar): tiket tetap `READY` dan serah terima tetap berjalan. Sajikan segmen `GAGAL` apa adanya; sesudah sebabnya dibereskan, sinkron diulang lewat `analyst:intake` ("sinkron ulang tiket `<ticketdir>`"). Dilarang `reopen` hanya untuk mengulang sinkron.

## STYLE

- Imperatif aktif; tiket berbahasa peminta, kalimat aktif, satu perilaku per AC.
- Istilah tetap: Ticketdir, Acceptance Criteria (AC), Aturan Bisnis (BR), Sidik.

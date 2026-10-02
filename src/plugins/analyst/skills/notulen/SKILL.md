---
name: notulen
description: Gunakan ketika user membawa catatan kasar rapat atau meeting (poin-poin, singkatan, coretan) untuk dirapikan jadi notulen terstruktur — ringkasan, peserta, agenda, pembahasan, keputusan, action item ber-PIC dan tenggat, pertanyaan terbuka — atau notulen yang sudah ada perlu dilanjutkan, difinalkan, atau disinkron ulang ke nataflow; bukan untuk membuat tiket (itu analyst:intake) - penataan ulang tanpa mengarang isi, klarifikasi celah ke pencatat, finalisasi berpersetujuan, dan sinkron opsional ke nataflow, sebelum notulen dibagikan tanpa konfirmasi pencatat
---

## THE IRON LAW

- Isi notulen hanya berasal dari `## Catatan Asli` atau jawaban pencatat di sesi ini. Yang disimpulkan analis ditulis `Asumsi:` dan wajib dikonfirmasi sebelum `final`.
- Butir dicatat sebagai **Keputusan** hanya bila catatan atau pencatat menyatakannya diputuskan. Selain itu butir masuk **Pembahasan**.
- `status: FINAL` hanya ditulis `notulen.py final` sesudah jawaban eksplisit user. Skrip memvonis validator dan menyegel isi notulen.
- Notulen tidak membaca kode, tidak menghasilkan tiket, dan tidak di-commit. `analyst/notulen/` selalu diabaikan git; salinannya di luar disk hanya dokumen nataflow, yang isinya disusun `notulen.py sync-payload`, bukan model.

## Precondition [REQUIRED]

1. Skrip: `notulen.py` = `${CLAUDE_PLUGIN_ROOT}/skills/notulen/scripts/notulen.py`. Template isi: `templates/notulen-template.md`. Prosedur sinkron: `references/nataflow-sync.md`.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/notulen/scripts/notulen.py state` harus berjalan. Galat → laporkan mentah ke user, berhenti.

## Parameter [REQUIRED]

- `notes` — string — `[REQUIRED]` untuk notulen baru — catatan kasar yang ditempel user, atau path berkasnya.
- `title` — string — default `""` — judul atau topik rapat. Kosong → tanyakan di Phase 1.
- `meeting_date` — string — default `""` — tanggal rapat `YYYY-MM-DD`. Kosong → tanyakan di Phase 1.
- `notulendir` — string — default `""` — notulendir yang dilanjutkan. Kosong berarti notulen baru.

## Workflow

### Phase 0 — Orientasi

Jalankan `notulen.py state`, lalu rutekan:

- Permintaan melanjutkan notulen `DRAFT` → baca `NOTULEN.md` utuh, lalu Phase 3.
- Notulen `DRIFT` (disunting sesudah final) → sajikan seksi yang berubah ke user, lalu Phase 5.
- Sinkron ulang notulen `FINAL` (mis. sesudah segmen `nataflow GAGAL`) → Phase 6 saja.
- `RUSAK` / `NAMA_TIDAK_SAH` → laporkan baris `state` ke user, berhenti. Frontmatter tidak ditambal dengan tangan.
- Selain itu → notulen baru, Phase 1.

### Phase 1 — Alokasi

1. Judul atau tanggal rapat kosong → satu `AskUserQuestion` untuk keduanya. Tanggal "hari ini" atau "kemarin" dihitung dari tanggal sekarang dan ditulis `YYYY-MM-DD`.
2. Slug kebab-case ≤ 40 karakter dari topik rapat.
3. Catatan ditempel di chat → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/notulen/scripts/notulen.py new --slug <slug> --title "<judul>" --date <YYYY-MM-DD> --notes - <<'EOF'`, lalu catatan apa adanya, lalu `EOF`. Catatan berupa berkas → `--notes - < <path>`, supaya isinya tidak diketik ulang.
4. `NEW PASS: <notulendir> · root=… · git=…` → baca `NOTULEN.md`. Segmen `PERINGATAN` disampaikan ke user apa adanya. `NEW FAIL` → Failure path 1.

### Phase 2 — Tata Ulang

Isi seksi `NOTULEN.md` dari `## Catatan Asli` menurut bagian 2 `templates/notulen-template.md`. Kutipan `## Catatan Asli` disalin byte demi byte saat menulis ulang berkas. Butir yang tafsirannya ragu ditandai untuk Phase 3, bukan ditebak. Tulis `NOTULEN.md`.

### Phase 3 — Klarifikasi Celah

1. Kumpulkan celah, urut dampak:
   1. butir yang ragu antara keputusan dan pembahasan;
   2. PIC atau tenggat action item yang tersirat ("minggu depan" → opsi tanggal konkret dari `meeting_date`);
   3. peserta yang tidak jelas;
   4. singkatan atau nama yang ambigu.
2. `AskUserQuestion`: ≤ 3 pertanyaan per giliran, 2–4 opsi konkret per pertanyaan. **Plafon 2 giliran.**
3. **Sesudah tiap giliran**: perbarui seksi, tulis `NOTULEN.md`, jalankan `notulen.py check --notulendir <notulendir>`.
4. Yang tetap tak terjawab: PIC atau tenggat → `belum ditentukan`; hal lain → `- **Q-n**: <pertanyaan> — menunggu: <siapa>`.
5. Catatan tanpa celah → lewati phase ini.

### Phase 4 — Validasi

`notulen.py check --notulendir <notulendir> --final` sampai `PASS`. Perbaiki per baris `Tindakan`. Lalu jalankan self-test bagian 3 template.

### Phase 5 — Konfirmasi Pencatat

1. Sajikan ringkasan 2–3 kalimat (judul, tanggal, jumlah keputusan, action item, dan pertanyaan terbuka) beserta path `NOTULEN.md`, bukan salinan notulen.
2. `AskUserQuestion`: *Final* · *Ada koreksi (sebut)* · *Tahan*.
3. *Final* → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/notulen/scripts/notulen.py final --notulendir <notulendir> --answer "<jawaban user>"`. *Koreksi* → terapkan, lalu ulangi Phase 4. *Tahan* → notulen tetap `DRAFT`, tutup dengan baris `NOTULEN — DRAFT`.

### Phase 6 — Sinkron nataflow

Sesudah `FINAL PASS`, jalankan prosedur `references/nataflow-sync.md` apa adanya. Hasilnya satu segmen `nataflow …` di baris penutup. `GAGAL` tidak menurunkan `FINAL`.

## Guardrails

- **FAKTA BUKAN TEBAKAN**: seksi dilarang diisi praktik umum, kelanjutan yang "biasanya terjadi", atau isi rapat sejenis. Yang tidak ada di catatan adalah pertanyaan, bukan isi.
- **KEPUTUSAN DIPUTUSKAN**: kata "kayaknya", "usul", "coba", atau "nanti dilihat" bukan keputusan.
- **PIC DAN TENGGAT TIDAK DITEBAK**: orang yang paling banyak bicara bukan PIC, dan tenggat relatif tidak diubah jadi tanggal tanpa konfirmasi.
- **KUTIPAN TETAP**: `## Catatan Asli` dimateraikan `source_hash`. Keterangan baru dari pencatat masuk seksi notulen, bukan ke kutipan.
- **TANPA KODE, TIKET, ATAU COMMIT**: dilarang membaca kode repo, menulis `TICKET.md`, memanggil `analyst:intake`, atau menjalankan `git add`/`git commit` atas notulen.
- **SIMPAN TIAP GILIRAN**: tulis `NOTULEN.md` sesudah tiap giliran klarifikasi, sebelum pertanyaan berikutnya.
- **RATIONALIZATION PREVENTION**:
  - "Jelas ini keputusan, tidak perlu ditanya" — keputusan palsu di notulen dijalankan orang lain sebagai kesepakatan.
  - "PIC-nya pasti dia" — action item ber-PIC salah lebih buruk daripada `belum ditentukan`, karena tidak ada yang mengeceknya.
  - "Saya rapikan sekalian ejaan nama dan istilahnya" — nama dan istilah yang diganti tidak lagi cocok dengan catatan asli dan dokumen lain.
  - "Ada permintaan fitur di rapat, langsung saya buatkan tiket" — notulen hanya dokumen; tiket dibuat user lewat `/analyst:intake`.

## Output [REQUIRED]

- Final: `NOTULEN — FINAL · <notulendir> · <n> keputusan · <n> action item · <n> Q · nataflow <dibuat | diperbarui | tidak berubah | dilewati | GAGAL: <sebab>>`.
- Sinkron ulang: `SINKRON — <notulendir> · nataflow <…>`.
- Belum final: `NOTULEN — DRAFT · <notulendir> · <sebab: ditahan user | menunggu jawaban <siapa> | validator FAIL>`.

## Failure path

1. **`notulen.py new` gagal**: slug kembar terbuka → lanjutkan notulendir itu (Phase 0) atau pilih slug lain; judul, tanggal, atau catatan kosong → tanyakan ke user; izin tulis → laporkan galat OS.
2. **Validator `FAIL` tak kunjung `PASS`** karena isi memang tidak diketahui → ubah jadi `Q-n` atau `belum ditentukan`, bukan dikarang.
3. **`Catatan asli utuh` `FAIL`** → kutipan berubah saat menulis ulang berkas; salin ulang dari keluaran `new` atau sumber tempelannya, byte demi byte.
4. **`FINAL FAIL`** → ikuti sebab di keluaran; validator `FAIL` → Phase 4; jawaban kosong → ulangi Phase 5.
5. **Sinkron `GAGAL`** (server MCP tidak tersedia, `get_project_info` galat, judul bentrok, dokumen ber-`notulen_key` kembar) → notulen tetap `FINAL`. Bereskan sebabnya, lalu sinkron ulang lewat `/analyst:notulen`. Dilarang mengulang `create_document` tanpa `list_document` ulang.
6. **Pencatat tidak tahu jawabannya** → catat `Q-n` dengan `menunggu: <siapa>`. Notulen tetap boleh final dengan pertanyaan terbuka.

## STYLE

- Imperatif aktif; pertanyaan ke pencatat berbahasa sehari-hari.
- Kalimat notulen ringkas, masa lampau untuk pembahasan ("Finance meminta …"), dan tanpa opini analis.

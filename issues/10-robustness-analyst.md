# Langkah 10 — Robustness Plugin analyst (G1–G10)

Sumber: review robustness plugin `analyst` 2026-09-27. Semua temuan **terbukti lewat probe** di ruang kerja
sementara (tiket contoh `cicilan-pembayaran`). Basis kode: commit `b6fbb1c`.

**Status:** dikerjakan.

## Tujuan

Menutup jalur yang masih bergantung pada disiplin model, padahal dapat divonis mesin. Pola yang berulang:

1. Transisi penting ditulis tangan tanpa segel: `elicitation: CLOSED`, kerangka `TICKET.md` awal.
2. Validator lebih longgar daripada aturan yang ditulis dokumen (`domain_terms`, `Asumsi:`, kutipan).
3. Skrip menerima masukan yang isinya bertentangan dengan dirinya sendiri (blok reviewer, heading ganda).

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perbaikan + test → suite penuh hijau.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | G1–G3 (`ticket.py`) | Keutuhan serah-terima dan gerbang review; G2 mengubah fixture bersama yang dipakai tahap berikutnya. |
| 2 | G4–G8 (`validate_doc.py`, `analyst_lib.py`) | Pengetatan validator; berdiri di atas fixture tahap 1. |
| 3 | G9 (`ticket.py new`) | Mengubah kontrak CLI `new` (keputusan E11 ditinjau ulang). |
| 4 | G10 + dokumen | SKILL, template, agent, README, `flow/`, versi plugin, indeks `ISSUES.md`. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang ada
dan harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| G1 | `ticket.py cmd_ref` | `analyst:spec` (parameter `external_ref`); penerima be/fe lewat subjek `ref TICKET` | **ya** (subjek commit dibaca `ticket_source_verdict` be/fe untuk tiket tanpa segel) — perilaku penerima tidak diubah | `test_ticket_8a.py` A12, `test_a1_ticket_source.py` (ref sesudah READY) | Rendah: `ref` pada DRIFT kini ditolak; `ref` pada DRAFT tidak lagi meng-commit. |
| G2 | `ticket.py` (`close` baru, `check --gate spec`, `review`, `approve`), `analyst_lib.py` (hitung baris log) | `analyst:elicit` Phase 5, `analyst:spec` precondition, fixture bersama | tidak (`elicit_hash`/`elicit_log` di luar `SEAL_FIELDS` dan `CONTENT_FIELDS`) | `fixtures/ticket_valid.md`, `test_ticket.py` (contoh template), `test_ticket_8a.py` A4 (mengkodekan celah: suntingan catatan me-reset ronde) | Sedang: tiket DRAFT lama tanpa segel gagal `check --gate spec` sampai `ticket.py close` dijalankan sekali (adopsi). |
| G3 | `ticket.py review`, `check --gate spec` (`ronde`) | `ticket-reviewer`, `spec/dispatcher/reviewer.md` | tidak | `conftest.ticket_block` (selalu `Ronde: 1`, `BLOCKED` tanpa butir) | Sedang: blok yang hitungan BLOCKER-nya tidak konsisten kini ditolak dan menuntut dispatch ulang. |
| G4 | `validate_doc.py` check elicit 10 | `analyst:elicit` Phase 1 | tidak | `test_ticket_8a.py` A9 (pesan) | Rendah: tiket CLOSED lama yang istilahnya hanya berjejak di Permintaan Asli kini FAIL. |
| G5 | `analyst_lib.scan_leaks`, `LEAK_PATTERNS` | `validate_doc.py --kind ticket` | tidak | — | Rendah: path/metode HTTP di dalam kutipan dan `error 500` kini ditandai. |
| G6 | `validate_doc.py` check ticket 10 (baru) | `analyst:spec` Phase 1 butir 8 | tidak | — | Rendah: kartu yang tidak membawa `Q-{n}` TIDAK MEMBLOKIR kini FAIL. |
| G7 | `validate_doc.py` `ASSUMPTION` | `analyst:elicit` Phase 4 | tidak | `test_ticket_8a.py` A9 | Rendah |
| G8 | `analyst_lib.py` (`duplicate_headings`), `validate_doc.py` check struktur | kedua validator | tidak | — | Rendah |
| G9 | `ticket.py new`, `validate_doc.py` check elicit 3 | `analyst:intake` Phase 1/6, `analyst:elicit` precondition & Phase 0 | tidak | `test_ticket.py` (3× `new`), `test_ticket_8a.py` A6/A10/A12, `test_ticket_09.py` E11 | Sedang: kontrak CLI `new` berubah (`--type`, `--requester`, `--request` wajib). |
| G10 | dokumen | model | tidak | `test_lint_plugins.py` (R1 rujukan) | Nihil |

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| G2 | Subperintah baru `ticket.py close` menulis `elicitation: CLOSED`, `elicit_hash` (sidik catatan), dan `elicit_log` (jumlah baris log), lalu commit `docs(ticket): elisitasi <slug>`. `check --gate spec`, `review`, dan `approve` menolak catatan yang berbeda dari `elicit_hash`. Penutupan ulang sesudah segel menuntut baris log baru `Dibuka ulang`. Tiket lama tanpa segel diadopsi sekali lewat `close`, kecuali catatannya berubah sesudah review terakhir. | Satu-satunya jalan mengubah fakta adalah elisitasi yang terekam di log. Plafon ronde/revisi hanya ter-reset oleh pembukaan ulang yang tercatat. |
| G3 | `review` menagih baris `- BLOCKER: <n> [MEKANIS] · <n> [SEMANTIK]`, jumlahnya sama dengan butir di bawah `**BLOCKER:**`, `PASS` ⇔ nol, dan `- Ronde:` sama dengan ronde yang dicatat. `check --gate spec` mencetak `ronde` sebagai sumber slot `{round}`. | Aturan "status dari predikat" agent dapat divonis mesin. Keaslian blok (ditulis subagent, bukan orkestrator) tetap di luar jangkauan skrip. |
| G5 | Di dalam kutipan hanya **istilah**, kode HTTP, dan identifier yang dikecualikan; path berkas, `file:baris`, metode HTTP + path, dan path API tetap ditandai. | Pesan galat di layar sah mengandung kode atau identifier (laporan BUG), tetapi tidak pernah perlu membawa path sistem. |
| G9 | `new` menulis kerangka `TICKET.md` (bagian 1 `elicit-template.md`) beserta permintaan asli dari stdin dan `request_hash`; ticketdir `KOSONG` ber-slug sama dipakai ulang. `--type` kembali wajib (meninjau ulang E11). | Menutup jendela `KOSONG` dan menjaga Permintaan Asli tetap verbatim lintas penulisan ulang tiap giliran. |

---

## G1 [Tinggi] `ref` meng-commit tiket DRIFT dengan subjek kunci
- [ ] Selesai

`cmd_ref` (`ticket.py:490`) hanya mengecek `status`, padahal README menjanjikan "tanpa DRIFT". Probe: tiket
READY tanpa `approved_seal`, BR diubah 50 juta → 10 juta, `ref` → commit `docs(ticket): ref TICKET <slug>`;
`ticket_source_verdict` backend memberi **PASS**. Pada DRAFT, `ref` ikut meng-commit suntingan draft yang
belum di-commit di bawah subjek yang sama. **Perbaikan:** tolak `DRIFT`/`RUSAK`; pada DRAFT tulis tanpa commit.

## G2 [Tinggi] Penutupan elisitasi tanpa segel
- [ ] Selesai

`elicitation: CLOSED` ditulis tangan; tidak ada sidik catatan saat ditutup. `spec` dapat menyunting catatan
sebelum review pertama tanpa terdeteksi, dan satu baris kosong di catatan me-reset plafon ronde review
(`ticket.py:316`) serta revisi (`ticket.py:367`). Probe: dua ronde BLOCKED → plafon → sisip baris kosong →
`REVIEW PASS: ronde 1/2`. **Perbaikan:** lihat Keputusan G2.

## G3 [Sedang] Blok reviewer tidak dicek konsistensinya
- [ ] Selesai

`review` hanya mencocokkan `- Verdict:` (`ticket.py:336`). Probe: `Verdict: PASS` dengan
`BLOCKER: 0 [MEKANIS] · 2 [SEMANTIK]` dan dua butir BLOCKER → tercatat PASS → `approve` READY.
**Perbaikan:** lihat Keputusan G3.

## G4 [Sedang] `domain_terms` lolos tanpa konfirmasi peminta
- [ ] Selesai

Check elicit 10 (`validate_doc.py:233`) menerima jejak di Permintaan Asli saja. Probe: permintaan "API error
500 …" + `domain_terms: [API]` → kartu "then API menampilkan …" lolos kedua validator, padahal panduan
elisitasi bagian 3 memakai contoh itu sebagai istilah yang wajib diterjemahkan. **Perbaikan:** tiap istilah
wajib punya baris log `Apakah "<istilah>" …?` berjawaban `Ya`.

## G5 [Sedang] Kutipan menjadi jalan pintas kebocoran teknis
- [ ] Selesai

`_EXEMPT` (`analyst_lib.py:305`) membuang seluruh isi kutipan sebelum semua pola dipindai. Probe:
`then "POST /api/v1/installments" mengembalikan "201"` lolos; `muncul error 500` juga lolos karena pola kode
status hanya `HTTP 500`. **Perbaikan:** lihat Keputusan G5; pola baru `error|galat <kode>`.

## G6 [Rendah] Pertanyaan TIDAK MEMBLOKIR tidak ditagih ke kartu
- [ ] Selesai

Catatan memuat `Q-2 [TIDAK MEMBLOKIR]`, kartu `- Tidak ada.` → PASS. **Perbaikan:** check ticket baru: ID
`Q-{n}` TIDAK MEMBLOKIR di catatan = ID `Q-{n}` di kartu.

## G7 [Rendah] `Asumsi:` di tengah kalimat lolos `CLOSED`
- [ ] Selesai

`ASSUMPTION` (`validate_doc.py:68`) berjangkar di awal baris. Probe: "Hanya pelanggan korporat. Asumsi:
perorangan ditunda." → PASS. **Perbaikan:** cari di mana pun dalam baris, termasuk bentuk tebal.

## G8 [Rendah] Heading ganda menelan seksi
- [ ] Selesai

`sections()` (`analyst_lib.py:195`) menimpa isi heading yang sama tanpa mengubah urutan kunci. Probe: dua
`## Acceptance Criteria`, yang pertama berisi `TODO <isi nanti>` → PASS. **Perbaikan:** check struktur kedua
validator menolak H2/H3/H4 ganda.

## G9 [Sedang] `new` hanya membuat direktori
- [ ] Selesai

`cmd_new` (`ticket.py:235`) hanya `mkdir`; kerangka dan permintaan asli ditulis model belakangan. Sesi yang
putus di antaranya meninggalkan ticketdir `KOSONG` tanpa permintaan asli, dan tidak ada yang menjaga
`### Permintaan Asli` tetap verbatim saat elisitasi menulis ulang berkas tiap giliran. **Perbaikan:** lihat
Keputusan G9.

## G10 [Rendah] Dokumen tertinggal
- [ ] Selesai

Docstring `ticket.py` menyebut kontrak exit hanya untuk `approve`/`ref` (README: juga `cancel`);
`ticket-template.md` tidak menyebut bentuk `- Tidak ada — <alasan>` untuk Di Luar Cakupan saat Batas Cakupan
kosong; `flow/backend.md` Handoff masih menyebut subjek commit saja, tanpa segel `approved_seal`.

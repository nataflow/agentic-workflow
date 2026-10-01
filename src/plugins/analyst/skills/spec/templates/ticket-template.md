# TICKET Template — `spec`

Rumah kanonik bentuk **kartu** di `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` — H1 dan tujuh H2 (sepuluh untuk `TECH`) di atas `## Catatan Elisitasi`. Frontmatter dan catatan elisitasi berumah di `skills/elicit/templates/elicit-template.md`. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `skills/_common/validate_doc.py --kind ticket` dan self-test penulis, bagian 3 dan 4 contoh terisi yang **tidak** tersalin ke artefak. `SKILL.md` merujuk ke sini dan dilarang menulis ulang kerangkanya.

Kartu setara kartu detail di Jira/Trello: dibaca peminta, product owner, QA, dan engineer. Kartu `FEATURE`/`IMPROVEMENT`/`BUG` berisi **apa** dan **kenapa**, tidak pernah **bagaimana** — pemecahan teknis, estimasi, dan pembagian backend/frontend milik engineer lewat `backend:tech-lead` / `frontend:lead`, yang menerima path tiket ini sebagai `ticket_source`, merujuk `AC-{n}`/`BR-{n}` di sini sebagai `TAC-{n}`/`TBR-{n}`, lalu menerbitkan `TASK.md` teknisnya sendiri. `## Catatan Elisitasi` di bawah kartu tetap ikut di berkas yang sama sebagai jejak asal-usul tiap AC dan aturan.

Kartu `TECH` dibaca lead engineer dan engineer pelaksana: isinya teknis — kondisi sekarang berbukti `path:baris`, kondisi target, keputusan, batasan — tetapi berhenti di **struktur akhir yang disepakati**. Urutan langkah, pembagian brief, dan estimasi tetap milik engineer di hilir, yang merujuk `AC-{n}`/`D-{n}`/`C-{n}` kartu ini sebagai `TAC-{n}`/`TD-{n}`/`TC-{n}`.

---

## 1. Template Kanonik Kartu

`spec` mengganti H1 kerja dengan judul final lalu menyisipkan tujuh H2 berikut di antara H1 dan `## Catatan Elisitasi`, yang dibiarkan persis apa adanya di bawahnya. Di frontmatter, `spec` hanya mengisi `priority: <HIGH | MEDIUM | LOW>` dan `external_ref`; field lain disalin apa adanya.

Tipe `FEATURE` dan `IMPROVEMENT`:

````markdown
# <Kata kerja + objek domain + kualifikasi — kerja yang diselesaikan engineer, maksimal 12 kata>

## Latar Belakang

<2–4 kalimat: masalah, siapa terdampak, seberapa sering atau seberapa mahal, kenapa sekarang.>

## User Story

Sebagai <peran>, saya ingin <kemampuan>, agar <manfaat>.

## Acceptance Criteria

- **AC-1**: Given <kondisi awal>, when <aksi pengguna>, then <hasil yang terlihat pengguna> (BR-1)
- **AC-2**: Given <kondisi awal>, when <aksi pengguna>, then <hasil yang terlihat pengguna>

## Aturan Bisnis

- **BR-1**: <aturan berangka atau bersyarat pasti>

## Di Luar Cakupan

- <yang tidak dikerjakan> — <alasan: ditunda | tiket terpisah | ditolak peminta>

## Pertanyaan Terbuka

- Tidak ada.

## Lampiran

- Tidak ada.
````

Tipe `BUG` mengganti `## User Story` dengan seksi berikut di posisi yang sama; seksi lain identik:

````markdown
## Laporan Bug

**Langkah reproduksi**:
1. <tindakan pertama>
2. <tindakan berikutnya>

**Yang diharapkan**: <hasil yang benar>
**Yang terjadi**: <hasil yang muncul, kutip teks layar dalam tanda kutip>
**Dampak**: <siapa, seberapa sering, ada jalan pintas atau tidak>
````

Tipe `TECH` memakai sepuluh H2 berikut, urutan persis:

````markdown
# <Kata kerja teknis + objek + kualifikasi — struktur yang berubah, maksimal 12 kata>

## Latar Belakang

<2–4 kalimat: masalah teknis, dampaknya (bug berulang, biaya ubah, insiden, angka), kenapa sekarang.>

## Kondisi Saat Ini

- <fakta struktur sekarang> — `<path/relatif/root>:<baris>`

## Kondisi Target

<Struktur akhir: modul, tabel atau relasi, arah dependensi, kontrak yang tetap. Boleh blok kode atau diagram; bukan urutan langkah.>

## Keputusan

- **D-1**: <keputusan> — alasan: <kenapa> — alternatif: <yang ditolak dan sebabnya>

## Batasan

- **C-1**: <yang tidak boleh berubah atau dilanggar>

## Acceptance Criteria

- **AC-1**: <pernyataan teknis yang dapat dibuktikan> (C-1) — verifikasi: <test, perintah, atau pemeriksaan>

## Dampak & Rollout

- <repo dan modul terdampak, urutan rilis, migrasi data, jalan mundur>

## Di Luar Cakupan

- <yang tidak dikerjakan> — <alasan>

## Pertanyaan Terbuka

- Tidak ada.

## Lampiran

- Tidak ada.
````

`## Keputusan` tanpa keputusan baru ditulis `- Tidak ada keputusan baru — <alasan>`; `## Batasan` tanpa batasan ditulis `- Tidak ada batasan khusus — <alasan>`. Frontmatter `category` ditulis `ticket.py new` dan disalin apa adanya.

Field frontmatter `status`, `revision`, `revision_base`, `review`, `review_round`, `approved`, `approved_hash`, `approved_seal`, `approval`, `reopened`, `reopen_reason`, `cancel_reason`, `request_hash`, `elicit_hash`, `elicit_log` ditulis **hanya** oleh `ticket.py`; `elicitation` dan `domain_terms` milik `analyst:elicit` (`CLOSED` lewat `ticket.py close`). Penulis kartu menyalin nilainya apa adanya. `external_ref` diisi kunci atau tautan kartu Jira/Trello bila tiket ini disalin ke sana (sesudah `READY` hanya lewat `ticket.py ref`) — yang disalin ke sana cukup kartunya, tanpa `## Catatan Elisitasi`.

---

## 2. Aturan Validasi

**Mekanis** — ditagih `validate_doc.py --kind ticket`; `FAIL` menahan dispatch reviewer dan `ticket.py approve`:

1. **Frontmatter**: `status` `DRAFT` atau `READY` (ditulis `ticket.py approve`, tidak pernah dengan tangan); `elicitation` `OPEN`/`CLOSED`; `type` dari enum; `priority` dari enum; `slug` sama dengan slug ticketdir; `created`, `requester`, `revision` terisi.
2. **Struktur**: tepat satu H1 berjudul ≤ 12 kata; tujuh H2 persis urutan bagian 1 untuk tipenya, lalu `## Catatan Elisitasi` sebagai H2 kedelapan dan terakhir; tiap H2 muncul sekali (heading ganda menimpa isi yang pertama).
3. **Latar belakang & cerita**: `## Latar Belakang` berisi; `FEATURE`/`IMPROVEMENT` punya tepat satu baris `Sebagai …, saya ingin …, agar …`; `BUG` memuat keempat field `## Laporan Bug` dengan langkah reproduksi bernomor.
4. **Acceptance Criteria**: 1–10 baris `- **AC-{n}**: Given …, when …, then …` bernomor urut dari `AC-1` (padanan `Dengan kondisi … ketika … maka …` sah).
5. **Aturan bisnis terpikul**: `- **BR-{n}**: …` bernomor urut dari `BR-1`, dan tiap `BR-{n}` disebut minimal satu baris AC; AC dilarang menyebut `BR-{n}` yang tidak ada. Tanpa aturan: tepat satu baris `- Tidak ada aturan khusus — <alasan>`.
6. **Di luar cakupan**: minimal satu `- <item> — <alasan>`. Pilar `Batas Cakupan` yang memang kosong ditulis `- Tidak ada — <alasan dari catatan>`, bukan butir rekaan.
7. **Pertanyaan terbuka & lampiran**: `- Tidak ada.` atau `- **Q-{n}**: <pertanyaan> — asumsi: <asumsi yang dipakai tiket ini>`; token `MEMBLOKIR` terlarang. Himpunan ID `Q-{n}` kartu sama dengan `Q-{n}` `TIDAK MEMBLOKIR` di `### Pertanyaan Terbuka` catatan elisitasi: tidak ada yang hilang, tidak ada yang dikarang. `## Lampiran` berupa butir daftar (tautan atau nama dokumen) atau `- Tidak ada.`
8. **Placeholder**: nol `TBD`/`TODO`/`diisi nanti` dan nol slot `<...>` di kartu, di luar `## Lampiran`; autolink `<https://…>` dan alamat `<nama@…>` bukan slot. `## Catatan Elisitasi` divonis `--kind elicit`.
9. **Nol kebocoran teknis** di kartu, di luar `## Lampiran` (catatan elisitasi dikecualikan — permintaan asli dan log adalah kutipan mentah): istilah teknis (endpoint, database, query, nama framework, `API`, …), path berkas, `file:baris`, metode HTTP, kode status HTTP (`HTTP 500`, `error 500`), identifier `snake_case`/`camelCase`, dan blok kode. Istilah, kode status, dan identifier di dalam tanda kutip dikecualikan — itu tulisan yang dilihat pengguna; path berkas, `file:baris`, metode HTTP + path, dan path API tetap ditandai di dalam kutipan, karena teks layar tidak pernah perlu membawanya. Istilah yang memang kosakata bisnis produk dikecualikan lewat `domain_terms: [API]` — list itu milik `analyst:elicit`; `spec` tidak menambahnya.
10. **Keutuhan `READY`**: sidik berkas utuh — kartu, catatan elisitasi, beserta `type`, `priority`, dan `domain_terms` — sama dengan `approved_hash`, dan segel serah-terima sama dengan `approved_seal` (bila ada); suntingan sesudah disetujui menuntut `ticket.py reopen`.

**Mekanis `TECH`** — butir 1, 2, 6, 7, 8, dan 10 berlaku apa adanya (butir 2: sepuluh H2 bagian 1 `TECH`; butir 8: blok dan span kode dikecualikan). Butir 3–5 dan 9 diganti:

3T. **Isi teknis**: `## Latar Belakang`, `## Kondisi Target`, dan `## Dampak & Rollout` berisi; `category` frontmatter dari enum.
4T. **Acceptance Criteria**: 1–10 baris `- **AC-{n}**: <pernyataan> — verifikasi: <cara>` bernomor urut dari `AC-1`.
5T. **Keputusan & batasan terpikul**: `- **D-{n}**: … — alasan: … — alternatif: …` bernomor urut, atau tepat satu `- Tidak ada keputusan baru — <alasan>`; `- **C-{n}**: …` bernomor urut dan disebut minimal satu AC (AC dilarang menyebut `C-{n}` yang tidak ada), atau tepat satu `- Tidak ada batasan khusus — <alasan>`.
9T. **Bukti kondisi saat ini**: tiap butir `## Kondisi Saat Ini` membawa minimal satu `` `path:baris` `` (atau `path:awal-akhir`); tiap rujukan menunjuk berkas yang ada di root repo tiket ini dan baris yang ada di berkas itu. Pemindai kebocoran teknis tidak berlaku.

**Semantik** — self-test penulis sebelum dispatch `ticket-reviewer`, dan fokus reviewer:

11. Tiap `then` adalah hasil yang **dapat diamati** pengguna atau QA tanpa membuka sistem: teks, tombol, status, angka, email yang diterima, atau — untuk bentuk hasil API — data yang dikembalikan kepada aplikasi pemanggil beserta penolakannya; bukan "data tersimpan" atau "sistem memproses".
12. Tiap AC dan `BR-{n}` berakar pada fakta `## Catatan Elisitasi` (pilar atau baris log). Aturan yang tidak pernah dikatakan peminta adalah rancangan analis, bukan isi tiket.
13. Tiap fakta pilar `Aturan Bisnis`, `Kondisi Diinginkan`, `Kasus Khusus` (dan `Yang Diharapkan` untuk BUG) dipikul minimal satu AC atau dinyatakan di `## Di Luar Cakupan`.
14. Satu tiket, satu tujuan pengguna. Dua user story yang dapat dirilis terpisah adalah dua tiket.
15. Pertanyaan `TIDAK MEMBLOKIR` di `## Catatan Elisitasi` yang belum terjawab muncul di `## Pertanyaan Terbuka` beserta asumsi yang dipakai AC.
16. Judul adalah perintah kerja (`TECH`: butir 17): diawali kata kerja tipenya (`FEATURE` Buat/Tambah/Tampilkan/Izinkan, `IMPROVEMENT` Ubah/Perluas/Tampilkan/Sederhanakan, `BUG` Perbaiki), menyebut objek domain, dan menyasar hasil yang teramati — bukan keinginan aktor, bukan cara membangun.

**Semantik `TECH`** — butir 11, 13, dan 16 diganti butir 17–20; butir 12, 14, dan 15 berlaku dengan `Kondisi Target`/`Batasan` sebagai pengganti aturan bisnis:

17. Judul diawali kata kerja teknis — Pisahkan, Pindahkan, Satukan, Ganti, Hapus, Normalisasi, Percepat, Naikkan — dan menyebut objek struktur yang berubah: `Pisahkan relasi project dan workspace menjadi many-to-many`, bukan `Perbaiki struktur database` (objek kabur) atau `Tambah migrasi 0042` (langkah, bukan hasil).
18. Tiap AC dapat diputuskan lulus/gagal oleh engineer lain lewat `verifikasi:`-nya tanpa menebak: test bernama, perintah, angka ambang, atau pemeriksaan yang jelas — bukan "kode lebih rapi" atau "performa membaik".
19. `category` terpikul AC: `REFACTOR` → minimal satu AC perilaku tetap dengan alat ukurnya; `DATA_MODEL` → AC migrasi naik dan turun serta nasib data lama; `ARCHITECTURE` → minimal satu `D-{n}` beserta alternatif; `PERFORMANCE` → AC berangka sekarang dan target; `DEPENDENCY` → AC versi tujuan beserta build dan test hijau.
20. `## Kondisi Target` dan AC berhenti di struktur akhir. Urutan langkah, nama berkas migrasi, atau pembagian brief adalah rancangan engineer di hilir, bukan isi tiket.

---

## 3. Contoh Terisi — `cicilan-pembayaran` (tidak tersalin ke artefak)

Lanjutan contoh bagian 3 `elicit-template.md`: `priority: -` menjadi `priority: HIGH`, H1 kerja diganti judul final, dan kartu disisipkan di atas catatan elisitasi yang tidak berubah.

````markdown
# Tambah jadwal pembayaran cicilan untuk invoice pelanggan korporat

## Latar Belakang

Invoice korporat di atas Rp 50 juta sering dibayar bertahap, tetapi sistem hanya mengenal status Belum Bayar dan Lunas. Tim Finance mencatat ±40 invoice cicilan per bulan di spreadsheet terpisah (±6 jam kerja per minggu), dan portal pelanggan menampilkan status yang salah. Dua klien besar menjadikan fitur ini syarat perpanjangan kontrak yang ditandatangani 3 minggu lagi.

## User Story

Sebagai Admin Finance, saya ingin memecah invoice korporat menjadi beberapa cicilan bertanggal jatuh tempo, agar sisa tagihan dan status lunas selalu akurat tanpa spreadsheet terpisah.

## Acceptance Criteria

- **AC-1**: Given invoice korporat bernilai Rp 60.000.000 berstatus Belum Bayar, when Admin Finance membuat jadwal 3 cicilan berjarak 30 hari, then invoice menampilkan 3 baris cicilan beserta tanggal jatuh tempo dan sisa tagihan Rp 60.000.000 (BR-1, BR-2)
- **AC-2**: Given invoice bernilai Rp 40.000.000, when Admin Finance membuka invoice itu, then pilihan "Buat Cicilan" tidak tersedia (BR-1)
- **AC-3**: Given Admin Finance mengisi 7 cicilan atau jarak jatuh tempo 10 hari, when menekan "Simpan", then muncul pesan "Maksimal 6 cicilan dengan jarak minimal 14 hari" dan jadwal tidak tersimpan (BR-2)
- **AC-4**: Given cicilan pertama sudah dibayar, when Admin Finance membuka jadwal, then tombol "Ubah Jadwal" tidak tersedia (BR-3)
- **AC-5**: Given pembayaran Rp 25.000.000 masuk untuk cicilan Rp 20.000.000, when pembayaran dicatat, then cicilan itu Lunas dan Rp 5.000.000 mengurangi cicilan berikutnya
- **AC-6**: Given seluruh cicilan dibayar, when pembayaran terakhir dicatat, then invoice berstatus Lunas di sistem dan di portal pelanggan
- **AC-7**: Given pengguna berperan Sales, when membuka invoice bercicilan, then jadwal tampil tanpa tombol ubah (BR-3)

## Aturan Bisnis

- **BR-1**: Cicilan hanya untuk invoice pelanggan korporat bernilai ≥ Rp 50.000.000.
- **BR-2**: Maksimal 6 cicilan per invoice; jarak antar jatuh tempo minimal 14 hari.
- **BR-3**: Jadwal cicilan hanya dapat diubah Admin Finance, dan hanya sebelum cicilan pertama dibayar.

## Di Luar Cakupan

- Denda keterlambatan — ditunda ke fase berikutnya atas keputusan peminta
- Cicilan untuk pelanggan perorangan — ditolak peminta

## Pertanyaan Terbuka

- **Q-2**: Apakah pelanggan menerima pengingat sebelum jatuh tempo? — asumsi: tidak ada pengingat di tiket ini

## Lampiran

- https://docs.example.com/finance/sop-cicilan

## Catatan Elisitasi

### Permintaan Asli
(… tetap persis seperti sebelum kartu ditulis …)
````

Pembanding AC yang **gugur**: `- **AC-1**: Given invoice cicilan, when disimpan, then data cicilan tersimpan di tabel installments` — `then` tidak dapat diamati pengguna (butir 11) dan membocorkan istilah teknis (butir 9).

Pembanding AC bentuk hasil API (panduan elisitasi bagian 6), dari tiket daftar Purchase Order: `Given Admin meminta daftar tanpa filter, when daftar diterima, then daftar memuat Purchase Order semua Tenant` **gugur** — peran bisnis ditulis sebagai pemanggil, dan tidak jelas siapa yang menerima daftar. Yang lolos: `Given ada Purchase Order milik Tenant A dan Tenant B, when aplikasi gudang meminta daftar atas nama pengguna berperan Tenant A, then data yang dikembalikan hanya memuat Purchase Order milik Tenant A (BR-3)`.

Pembanding judul yang **gugur**: `Admin Finance dapat mencatat pembayaran invoice korporat secara cicilan` — bercerita tentang keinginan aktor yang sudah dimuat User Story, bukan kerja yang diselesaikan (butir 16); `Tambah tabel installments untuk invoice korporat` — menyebut cara membangun (butir 9 dan 16).

---

## 4. Contoh Terisi `TECH` — `relasi-project-workspace` (tidak tersalin ke artefak)

Lanjutan contoh bagian 4 `elicit-template.md`: `priority: -` menjadi `priority: HIGH`, H1 kerja diganti judul final, dan kartu disisipkan di atas catatan elisitasi yang tidak berubah.

````markdown
# Pisahkan relasi project dan workspace menjadi many-to-many

## Latar Belakang

Project hanya dapat berada di satu workspace karena `workspace_id` menempel langsung di tabel `projects`. Tim sudah tiga kali menduplikasi project untuk kebutuhan lintas workspace kuartal ini, dan tiap duplikasi memecah riwayat task. Fitur berbagi project kuartal depan bergantung pada relasi ini.

## Kondisi Saat Ini

- Kolom `workspace_id` menempel di model project — `internal/project/model.go:12`
- Query daftar project memfilter langsung ke kolom itu — `internal/project/repository.go:40-48`

## Kondisi Target

Tabel penghubung `project_workspaces` berprimary key gabungan; kolom `workspace_id` di `projects` dihapus sesudah backfill.

```sql
CREATE TABLE project_workspaces (
  project_id uuid REFERENCES projects(id) ON DELETE CASCADE,
  workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, workspace_id)
);
```

## Keputusan

- **D-1**: Pakai tabel penghubung — alasan: FK dan indeks tetap ditegakkan database — alternatif: kolom array `workspace_ids`, ditolak karena tanpa FK

## Batasan

- **C-1**: Bentuk respons daftar project di REST dan MCP tidak berubah
- **C-2**: Migrasi reversible tanpa kehilangan data

## Acceptance Criteria

- **AC-1**: Satu project dapat ditautkan ke dua workspace dan muncul di daftar keduanya — verifikasi: test repository `TestProjectRepo_ListByWorkspace`
- **AC-2**: Respons daftar project identik sebelum dan sesudah migrasi (C-1) — verifikasi: snapshot test handler daftar project
- **AC-3**: Tiap project lama tertaut ke workspace asalnya sesudah migrasi naik (C-2) — verifikasi: hitung baris `project_workspaces` = jumlah project pada data seed
- **AC-4**: Migrasi turun mengembalikan `workspace_id` tiap project (C-2) — verifikasi: migrasi naik lalu turun satu langkah atas data seed, bandingkan isi `projects`

## Dampak & Rollout

- Backend saja; frontend tidak berubah karena C-1.
- Rilis 1: tabel penghubung beserta backfill dan repository baru. Rilis 2: hapus kolom lama. Jalan mundur rilis 1: migrasi turun.

## Di Luar Cakupan

- Izin per workspace atas project — tiket terpisah

## Pertanyaan Terbuka

- Tidak ada.

## Lampiran

- Tidak ada.

## Catatan Elisitasi

### Permintaan Asli
(… tetap persis seperti bagian 4 `elicit-template.md` …)
````

Pembanding AC yang **gugur**: `- **AC-1**: Struktur relasi lebih bersih — verifikasi: code review` — tidak dapat diputuskan lulus/gagal tanpa menebak (butir 18), dan tidak memikul migrasi naik-turun yang dituntut `DATA_MODEL` (butir 19).

Pembanding Kondisi Target yang **gugur**: `1. Buat migrasi 0042. 2. Ubah repository. 3. Hapus kolom.` — urutan langkah milik brief engineer (butir 20); yang dikunci tiket adalah struktur akhirnya.

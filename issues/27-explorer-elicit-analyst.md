# Langkah 27 — `analyst`: subagent `code-explorer` untuk `elicit`, `code-scout` sonnet khusus `notulen` (E1–E6, D1)

Sumber: feedback user 2026-10-14: penelusuran kode saat membuat tiket baru lewat `analyst:intake` terasa kurang
lengkap, sehingga pertanyaan elisitasi terlalu susah dijawab. User mengusulkan `code-scout` diganti `code-explorer`
supaya tiket lebih akurat karena membaca kondisi codebase langsung. Seluruh keputusan di bawah diambil di sesi desain
yang sama. Basis kode: commit `7dd5f53` (analyst 0.16.0).

**Status (2026-10-14):** RENCANA. Belum ada perubahan di `src/`; pelaksanaan menunggu persetujuan dokumen ini.

## Tujuan

1. Elisitasi tiket bertumpu pada pemahaman kondisi kode yang cukup dalam: aktor dan izinnya, layar atau menu, aturan
   beserta angka dan ambangnya, status dan transisinya, pesan yang terlihat pengguna, dan untuk tiket `TECH` struktur
   sekarang menurut `category`-nya.
2. Beban peminta turun. Pertanyaan tentang keadaan sekarang berubah dari "ceritakan bagaimana sekarang" menjadi
   "sekarang sistem begini, betul?".
3. Iron law analyst tetap utuh: fakta pilar non-`TECH` berasal dari peminta (`Asumsi:` wajib dikonfirmasi), konteks
   utama tidak membaca kode, dan `path:baris` tetap khusus `TECH`.
4. `analyst:notulen` tetap memakai penelusur dangkal `code-scout`, kini dengan model sonnet.

## Temuan awal (dasar keputusan)

Diverifikasi di sesi desain dengan membaca plugin di basis kode di atas:

- **Penelusuran kode tidak terjadi di `intake`.** Guardrail NOL KODE `intake/SKILL.md` melarang `Read`/`Grep`/`Glob`
  atas kode. Seluruh pembacaan kode tiket berjalan di `analyst:elicit` Phase 1 (ditambah satu susulan di Phase 2)
  lewat `code-scout`. Perubahan langkah ini mendarat di `elicit`; `intake` hanya berganti kalimat rujukan.
- **Scout dangkal menurut kontraknya.** `agents/code-scout.md`: model haiku, kuota 8 pemanggilan, "Berhenti di bukti
  pertama" (Cara Menelusuri butir 4), dan dilarang menelusuri flow, alur transaksi, rantai pemanggil, edge case,
  atau validasi (Batas). Balikannya satu kalimat per butir, misalnya "layar daftar invoice ada di sini". Aturan
  yang berlaku, siapa yang boleh apa, daftar status, dan pesan error tidak pernah terbaca, sehingga `elicit`
  menanyakan semuanya ke peminta non-engineer.
- **Prosa `elicit` ikut menutup jalan.** Guardrail KODE SEBAGAI KONTEKS berbunyi "`Kondisi Saat Ini` tetap
  diceritakan peminta". Padahal Phase 1 sudah mengizinkan temuan scout menjadi `Asumsi:` tanpa rujukan berkas, dan
  `validate_doc.py --kind elicit` sudah menagih nol `Asumsi:` saat `CLOSED`. Mekanisme konfirmasinya sudah ada; yang
  kurang adalah bahan dari kode dan arahan prosa untuk memakainya.
- **`code-explorer` backend/frontend tidak bisa dipinjam.**
  - Lintas plugin: analyst dipasang mandiri, tanpa jaminan backend/frontend terpasang.
  - Agent itu punya `Write` dan wajib menulis laporan ke laci `.explore/`. `backend/hooks/guard_bash.py` hanya
    mengizinkan `EXPLORE_REPORT` (`^backenddev/docs/(?:[^/]+/)?\.explore/[^/]+\.md$`), dan frontend hanya
    `<taskdir>/.explore/*.md` atau `.frontenddev/explore/*.md`. Ticketdir `analyst/tickets/…` di luar keduanya,
    sehingga `Write` ditolak fail-closed.
  - Kontraknya menuntut blok `Format laporan` dan `Berkas laporan` dari pendispatch, serta profil satu sisi (BE atau
    FE). Tiket analyst bisa menyentuh keduanya, atau tinggal di repo tanpa profil.
  - Alasan yang sama sudah tercatat di Langkah 23 K1.
- **Pola turunan sudah terbukti.** `fullstack:backend-explorer` dan `fullstack:frontend-explorer` (Langkah 23)
  diadaptasi dari `code-explorer`: read-only tanpa `Write`, sonnet, `maxTurns: 45`, kuota 20/40, format balikan di
  berkas agent, dan test drift yang memaku angka jendela baca ke sumbernya.
- **Hook tidak mengganggu.** `guard_bash.py` backend/frontend mencocokkan `agent_type` persis (`backend:code-explorer`,
  `frontend:code-explorer`), jadi `analyst:code-explorer` lewat tanpa pagar. Pagar memang tidak dibutuhkan karena
  agent ini tanpa `Write`/`Edit`/`Bash`.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Agent baru `analyst:code-explorer` untuk `elicit`.** `code-scout` tidak dihapus; ia tetap dipakai `notulen` saja. | Keputusan user 2026-10-14. Notulen hanya butuh konteks istilah, singkatan, atau layar untuk mempertajam pertanyaan ke pencatat; kontrak dangkal dan test notulen tetap bermakna. |
| K2 | **`code-scout` model haiku → sonnet.** Kuota 8, berhenti di bukti pertama, dan `maxTurns: 10` tetap. Deskripsinya tidak lagi menyebut `analyst:elicit`. | Keputusan user 2026-10-14. Menggantikan bagian model pada K5 Langkah 18; sisa K5 (tanpa `Write`, tanpa hook) tetap berlaku. |
| K3 | **Bentuk explorer**: `tools: Read, Grep, Glob` (tanpa `Write`/`Edit`/`Bash`), `model: sonnet`, `maxTurns: 45`. Kuota `Read`/`Grep`/`Glob`: `ringkas` 20, `menyeluruh` 40, termasuk orientasi profil. Format balikan tinggal di berkas agent. | Analyst tidak punya `hooks/`, jadi daftar tools satu-satunya pagar mekanis (K5 Langkah 18). Format di agent dapat dipaku test dan tidak hilang saat prompt dihidrasi (K3 Langkah 23). |
| K4 | **Diadaptasi dari `backend/agents/code-explorer.md`** (sumber angka jendela) **dan `fullstack/agents/backend-explorer.md`** (bentuk read-only dengan balikan inline). Diambil: investigasi dua tahap, jendela `max(1, L - 15)` s.d. `L + 35` (30–50 baris), larangan membaca berkas utuh di atas 100 baris, jenjang `menyeluruh` (method utuh sampai 120 baris, maksimal 3 jendela per berkas, berkas di atas 400 baris tetap ber-offset), serta pemisahan `Tidak ditemukan` dari `Belum disisir`. Dibuang: Tahap 0 panen laci, `Write`/`Berkas laporan`, blok `Format laporan` pendispatch. | Kemampuan penelusuran sudah matang di sumbernya; yang dibuang hanya bagian yang terikat ke taskdir dan `Write`. |
| K5 | **Profil adalah peta bila ada, bukan syarat.** Explorer membaca `.claude/profile/backenddev/` dan/atau `.claude/profile/frontenddev/` di `root`, atau di repo anak di dalam `batas`. Tanpa profil, orientasi dari manifest stack dan struktur direktori, dengan `Confidence` maksimal `medium`. | Berbeda dari K5 Langkah 23 (repo tanpa profil ditolak) karena analyst sering berjalan di repo yang belum diprofilkan, dan scout sekarang pun berjalan tanpa profil. Menolak dispatch berarti kembali ke tanpa konteks kode. |
| K6 | **Dua mode tetap** `BUKTI` (`TECH`) dan `KONTEKS` (tipe lain). Masukan baru `tipe` dan, khusus `TECH`, `category` menentukan apa yang digali tiap butir (tabel Kontrak). | Kompatibel dengan dispatcher dan prosa batch yang sudah ada; yang dalam adalah isi tiap butir, bukan jumlah butir. |
| K7 | **Kedalaman**: non-`TECH` `ringkas`, `TECH` `menyeluruh`. Plafon 2 dispatch per tiket tetap, scout awal batch tetap paralel dalam satu pesan, dan dispatch ulang karena gagal atau balikan hilang tidak dihitung plafon. | Keputusan user 2026-10-14. Sonnet lebih mahal daripada haiku; kedalaman penuh hanya untuk tiket yang buktinya dinilai `ticket-reviewer` dan `validate_doc.py --kind ticket`. |
| K8 | **Temuan `KONTEKS` tetap bukan fakta, tetapi wajib dipakai.** Temuan keadaan sekarang ditulis lebih dulu sebagai `Asumsi:` tanpa rujukan berkas di pilar yang menggambarkan keadaan sekarang, lalu pertanyaan Phase 2 untuk pilar itu berbentuk konfirmasi atau koreksi. Pilar sasaran: `Kondisi Saat Ini` (`FEATURE`/`IMPROVEMENT`) dan `Langkah Reproduksi` (`BUG`, sebatas letak layar dan tombol). Aturan dan aktor yang berlaku sekarang menjadi **opsi pertanyaan** `Aturan Bisnis`/`Aktor`/`Yang Diharapkan` ("Sekarang hanya Admin yang bisa membatalkan invoice. Tetap begitu untuk cicilan, atau Kasir juga?"), bukan fakta pilar yang diinginkan. Validator tidak berubah: check 11 tetap menolak `path:baris`, dan `CLOSED` tetap menagih nol `Asumsi:`. | Keputusan user 2026-10-14. K2 Langkah 18 ("konteks bukan fakta") utuh; yang berubah hanya kalimat "`Kondisi Saat Ini` tetap diceritakan peminta". Kode menunjukkan apa yang ada, bukan apa yang diinginkan, sehingga aturan sekarang tidak boleh berpindah diam-diam menjadi aturan yang diminta. |
| K9 | **Explorer dilarang mendiagnosis penyebab bug** atau menyarankan perbaikan. Untuk `BUG` ia hanya memetakan jalur langkah yang dilaporkan, aturan dan validasi yang berlaku di jalur itu, dan pesan literal yang dapat muncul. | Diagnosis wilayah `backend:tech-lead`/`frontend:lead` (`intake` Phase 2). Tebakan penyebab di tiket berubah menjadi kebutuhan palsu. |
| K10 | **`intake` tetap NOL KODE.** Penentuan tipe tetap dari kata-kata peminta; hanya kalimat rujukan subagent yang berganti. | Keputusan user 2026-10-14. Intake gerbang cepat sebelum ticketdir ada; dispatch sonnet di sana menggandakan biaya tanpa tempat menyimpan hasil. |
| K11 | **Nama selalu ditulis penuh `analyst:code-explorer`** di prosa `elicit`, dispatcher, `batch.md`, dan `intake`. | backend dan frontend juga punya agent `code-explorer`, dan `frontend/hooks/gate_text.py` menyebutnya. Nama pendek berisiko model mendispatch agent plugin lain, yang `Write`-nya ditolak hook dan kontraknya menuntut `Format laporan`. |
| K12 | **Root multi-repo**: satu explorer per dispatch, `batas` = repo anak yang disebut permintaan bila ada. Explorer membaca profil repo anak di dalam batasnya. Tidak ada fan-out per repo di langkah ini; plafon 2 tetap. Tiket `TECH` di root multi-repo tetap `TERTAHAN` oleh `intake` Phase 4. | Cakupan kecil. Kebutuhan pemahaman lintas repo dilayani `/fullstack:explore`. |
| K13 | **Balikan tetap tidak ditulis ke disk.** Balikan yang hilang dari percakapan (ringkasan otomatis, sesi baru) didispatch ulang satu kali tanpa dihitung plafon. | Sama dengan aturan scout sekarang. Menulis balikan ber-`path:baris` ke ticketdir yang di-commit membuka kebocoran baru di luar jangkauan check 11. |
| K14 | **Drift dari sumber dijaga test**: angka jendela baca explorer sama dengan `backend/agents/code-explorer.md`, termasuk plafon `menyeluruh` (120 baris, 3 jendela, 400 baris). | Pola K12 Langkah 23. Byte-identical tidak mungkin karena isinya diadaptasi; angka jendela adalah bagian yang paling mudah menyimpang diam-diam. |

## Kontrak

### Agent `analyst:code-explorer` (`agents/code-explorer.md`)

Frontmatter:

```yaml
name: code-explorer
description: Subagent read-only penelusur kode untuk analyst:elicit. Gunakan ketika elisitasi tiket butuh pemahaman kondisi kode sekarang — aktor dan izinnya, layar, aturan beserta angkanya, status dan transisinya, pesan yang terlihat pengguna (mode KONTEKS), atau bukti path:baris beserta struktur sekarang atas klaim lead engineer (mode BUKTI, tiket TECH). Dilarang mengedit berkas, membaca nilai .env, mendiagnosis penyebab bug, merancang solusi, atau berdialog dengan user.
tools: Read, Grep, Glob
model: sonnet
maxTurns: 45
```

Masukan (slot prompt pendispatch):

- `mode` [REQUIRED]: `BUKTI` atau `KONTEKS`.
- `tipe` [REQUIRED]: `FEATURE`, `IMPROVEMENT`, `BUG`, atau `TECH`.
- `category` [REQUIRED bila `tipe` = `TECH`]: `REFACTOR`, `DATA_MODEL`, `ARCHITECTURE`, `PERFORMANCE`, atau
  `DEPENDENCY`.
- `root` [REQUIRED]: path absolut root ruang kerja. Dilarang menyisir di luarnya.
- `batas` [OPTIONAL]: direktori atau repo anak di bawah `root`. Kosong berarti seluruh `root`.
- `kedalaman` [REQUIRED]: `ringkas` atau `menyeluruh` (K7).
- `pertanyaan` [REQUIRED]: 1–5 butir bernomor `P1`, `P2`, …, dalam kata-kata peminta.

Slot wajib kosong, `mode`/`tipe`/`kedalaman` di luar nilai sah, atau `category` hilang pada `TECH` → jangan menelusuri.
Balas blok `## Code Explorer` dengan satu butir `Belum disisir` yang menyebut slot yang rusak.

Yang digali tiap butir:

| `tipe` (`category`) | Yang digali |
|---|---|
| `FEATURE`, `IMPROVEMENT` | Layar atau menu tempat konsep itu hidup; aktor beserta izinnya (siapa boleh, siapa dilarang); aturan beserta angka dan ambangnya; status dan transisinya; pesan yang terlihat pengguna; langkah pengguna dari masuk sampai hasil |
| `BUG` | Jalur dari langkah yang dilaporkan sampai hasilnya; aturan dan validasi yang berlaku di jalur itu; pesan literal yang dapat muncul. Tanpa menebak penyebab (K9) |
| `TECH` `REFACTOR` | Struktur sekarang dan test yang menjaga perilakunya |
| `TECH` `DATA_MODEL` | Entitas atau tabel, relasi, constraint, dan migrasi yang menyentuhnya |
| `TECH` `ARCHITECTURE` | Batas modul dan arah import atau dependensi |
| `TECH` `PERFORMANCE` | Titik kueri atau loop yang disebut klaim, index, dan cache |
| `TECH` `DEPENDENCY` | Versi di manifest/lockfile dan titik pemakaian API pustakanya |

Cara menelusuri:

1. **Cek ada kode**: satu `Glob` atas berkas sumber umum di `root` (atau `batas`). Nihil → balas `Repo: tanpa kode`,
   semua butir `Belum disisir` beralasan "tanpa kode".
2. **Orientasi profil** (K5): `index.json` lalu `domain-map.md`/`module-structure.md` (BE) atau `structure.md` (FE)
   bila ada. Tanpa profil → manifest stack dan struktur direktori, `Confidence` maksimal `medium`. Dilarang membaca
   adapter `stacks/`.
3. **Lokalisasi**: `Grep -n`/`Glob` terarah dengan kata kunci dari kata peminta, dicoba juga padanan Inggrisnya yang
   lazim di kode. Abaikan `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, dan berkas hasil generate.
4. **Verifikasi**: `Read` ber-offset dengan jendela K4. Hasil `Grep` adalah kandidat, bukan bukti.
5. **Jenjang `menyeluruh`**: pelonggaran K4 hanya di sini; rantai pemanggil ditelusuri sampai kedua ujungnya.
6. **Berhenti**: satu butir selesai begitu aspek tabel di atas yang relevan untuk butir itu terjawab. Butir sulit tidak
   boleh menghabiskan kuota butir lain: butir yang sudah memakai 6 pemanggilan (`ringkas`) atau 10 (`menyeluruh`)
   tanpa hasil dipindah ke `Tidak ditemukan` beserta direktori yang sudah disisir. Kuota habis → sisa butir masuk
   `Belum disisir` beralasan "kuota habis".

Batas:

- Read-only. Dilarang menyunting, membuat, atau menghapus berkas apa pun.
- Dilarang membuka `.env*` dan menyalin nilai rahasia, token, atau host; sebut nama config-nya saja.
- Dilarang mendiagnosis penyebab bug, menyarankan solusi, menilai kualitas kode, atau menebak maksud peminta.
- Dilarang menulis `path:baris` yang tidak dibaca sendiri lewat `Read`.
- Dilarang bertanya atau berdialog dengan user; ketidakjelasan dicatat di butirnya.
- Mode `KONTEKS`: kalimat temuan ditulis dalam bahasa yang terlihat pengguna ("hanya Admin yang bisa membatalkan
  invoice"). Nama berkas, simbol, tabel, atau endpoint hanya muncul di rujukan `path:baris`.

Balikan (hanya blok ini, tanpa teks pengantar atau penutup):

```markdown
## Code Explorer
- Mode: BUKTI | KONTEKS
- Tipe: <tipe>[/<category>]
- Repo: ada kode | tanpa kode
- Profil: <backenddev · stack> | <frontenddev · stack> | tanpa profil
- Kedalaman: ringkas | menyeluruh
- Pemanggilan: <n> dari <20 | 40>
- Confidence: high | medium | low

### Ditemukan
#### P1 — <yang dicari, kata-kata peminta>
- Perilaku: <satu kalimat> — `path:baris`
- Aktor: <peran dan izinnya> — `path:baris`
- Aturan: <aturan beserta angka atau ambang> — `path:baris`
- Status: <daftar status dan transisinya> — `path:baris`
- Pesan: "<teks literal>" — `path:baris`
- Struktur: <modul, relasi, arah dependensi; mode BUKTI> — `path:baris`

### Tidak ditemukan
- P2 — <yang dicari> — disisir: `dir/`, `dir2/`

### Belum disisir
- P3 — <kuota habis | di luar batas | tanpa kode>
```

Aturan balikan:

- Ketiga seksi `###` selalu hadir; seksi tanpa butir ditulis `- Tidak ada.`
- Tiap butir `pertanyaan` muncul tepat sekali sebagai kepala: `#### P<n>` di `Ditemukan`, atau satu butir di
  `Tidak ditemukan`/`Belum disisir`. Butir `Ditemukan` yang sebagian aspeknya belum terbaca ditambah satu butir
  `P<n> (sebagian) — <aspek>` di `Belum disisir`.
- Baris aspek yang tidak relevan dibuang; tiap baris yang tersisa punya rujukan. `path` relatif terhadap `root`, rentang
  baris maksimal 40.
- Mode `BUKTI`: klaim yang dibantah kode tetap masuk `Ditemukan` dengan kalimat yang menyebut bedanya.
- `Tidak ditemukan` berarti sudah disisir dan nihil; `Belum disisir` berarti belum sempat dilihat. Dilarang mencampur
  keduanya.

### `skills/elicit/dispatcher/explorer.md` (menggantikan `dispatcher/scout.md` milik `elicit`)

Template prompt dengan slot `{mode}`, `{tipe}`, `{category}`, `{root}`, `{batas}`, `{kedalaman}`, dan
`{pertanyaan}`, dengan tabel Slot Hidrasi:

| Slot | Sumber pengisian |
|---|---|
| `{mode}` | `type` `TICKET.md`: `TECH` → `BUKTI`, lainnya → `KONTEKS` |
| `{tipe}`, `{category}` | frontmatter `type` dan `category`; `{category}` = `-` untuk non-`TECH` |
| `{root}` | baris `root=` keluaran `ticket.py new` atau `check --gate elicit` |
| `{batas}` | direktori atau repo anak yang disebut peminta (K12); `-` bila kosong, dilarang menebak dari nama stack |
| `{kedalaman}` | `TECH` → `menyeluruh`, lainnya → `ringkas` (K7) |
| `{pertanyaan}` | `BUKTI`: tiap klaim kondisi sekarang. `KONTEKS`: konsep yang disebut permintaan. 1–5 butir dalam kata-kata peminta |

Gerbang masuk: plafon 2 dispatch per tiket (K7), nama agent ditulis penuh `analyst:code-explorer` (K11), dan audit
hidrasi (tanpa `{...}` mentah, `TBD`, atau `TODO`).

Penanganan Balikan:

| Balikan | Penanganan `elicit` |
|---|---|
| `Ditemukan`, `BUKTI` | `` `path:baris` `` dicatat di pilar `Kondisi Saat Ini`; baris `Struktur` memperkaya kalimatnya. Klaim yang dibantah kode ditanyakan ke peminta berdampingan dengan buktinya |
| `Ditemukan`, `KONTEKS` | Baris `Perilaku` (dan `Aktor`/`Status` yang menggambarkan keadaan sekarang) ditulis sebagai `Asumsi:` tanpa rujukan berkas di pilar sasaran K8, lalu dikonfirmasi lewat pertanyaan Phase 2 berbentuk konfirmasi atau koreksi. Baris `Aturan`/`Aktor` menjadi opsi pertanyaan pilar yang diinginkan. Dilarang ditulis sebagai fakta, dan dilarang menyalin `path:baris` |
| `Tidak ditemukan` | `BUKTI`: klaim tidak terbukti, tanyakan ke peminta. `KONTEKS`: konsepnya mungkin belum ada, tanyakan sebagai kemampuan baru |
| `Belum disisir` | Dispatch susulan bila plafon tersisa; selain itu tanyakan ke peminta |
| `Repo: tanpa kode` | `KONTEKS` → lanjut tanpa konteks kode. `BUKTI` → `ELICIT — TERTAHAN` |
| Payload kosong, tanpa blok `## Code Explorer`, atau error | Ulangi sekali (tidak dihitung plafon). Gagal lagi: `KONTEKS` → lanjut tanpa konteks kode; `BUKTI` → `ELICIT — TERTAHAN` sebab "bukti kode tidak dapat dikumpulkan" |

### Gerbang dan validator

- `ticket.py check --gate elicit`: daftar berkas wajib `elicit/dispatcher/scout.md` diganti
  `elicit/dispatcher/explorer.md`.
- `validate_doc.py --kind elicit` check 11: logika tidak berubah. Komentar dan teks `Tindakan` yang menyebut
  `code-scout` diganti `code-explorer`.

### Prosa `elicit`

- `SKILL.md`:
  - Deskripsi frontmatter: `code-scout` → `code-explorer`, panjang tetap di bawah 1536.
  - Iron Law butir 3 dan Precondition 1: subagent dan template dispatch baru.
  - Phase 1 (`TECH` dan konteks kode): dispatch `analyst:code-explorer` menurut dispatcher baru, pra-isi `Asumsi:`
    menurut K8.
  - Phase 2 butir 2: opsi bertumpu pada baris `Aktor`/`Aturan`/`Status`, pertanyaan pilar keadaan sekarang berbentuk
    konfirmasi atau koreksi. Butir 6: susulan explorer.
  - Guardrails: KODE SEBAGAI KONTEKS (kalimat "`Kondisi Saat Ini` tetap diceritakan peminta" diganti aturan K8),
    KODE LEWAT SCOUT → KODE LEWAT EXPLORER, dan rationalization yang menyebut scout. Ditambah satu butir: "Kode
    bilang hanya Admin, jadi tulis saja di Aturan Bisnis" — aturan sekarang bukan aturan yang diminta.
  - Failure path 6: explorer gagal.
- `references/elicitation-tech.md` bagian 2: kuota 8 → kedalaman `menyeluruh` (kuota 40) dan baris `Struktur`
  per `category`.
- `references/elicitation-guide.md` bagian 1: pertanyaan pembuka `Kondisi Saat Ini` ditambah bentuk konfirmasi bila
  ada `Asumsi:` dari explorer.

### `intake` dan batch

- `intake/SKILL.md`: Guardrail NOL KODE dan rationalization "Saya cek kodenya sebentar" menyebut
  `analyst:code-explorer`. Larangan membaca kode tidak berubah (K10).
- `intake/references/batch.md` bagian 6: "scout awal batch" menjadi explorer awal batch dengan dispatcher baru;
  aturan paralel, label slug, dan dispatch ulang tidak berubah.

### `code-scout` (`agents/code-scout.md`)

- `model: haiku` → `model: sonnet` (K2).
- Deskripsi dan kalimat pembuka hanya menyebut `analyst:notulen`. Mode `BUKTI` dihapus karena hanya dipakai tiket
  `TECH` di `elicit`. Slot `mode` tetap ada dengan satu nilai `KONTEKS`, sehingga baris mode `KONTEKS` di
  `notulen/dispatcher/scout.md` tetap sah; hanya kalimat "mode `BUKTI` tidak dipakai di sini" di berkas itu yang
  disesuaikan.

## Urutan pengerjaan

Tiap tahap: blast radius dipetakan (tabel di bawah) → perubahan + test → suite penuh hijau → lint.

| Tahap | Item | Alasan urutan |
|---|---|---|
| 1 | E1 (agent explorer), E2 (dispatcher + gerbang + teks check 11) | Pagar mesin dan kontrak balikan lebih dulu; prosa berdiri di atasnya. |
| 2 | E3 (prosa `elicit` + references), E4 (`intake` + `batch.md`) | Menyambungkan explorer ke alur model. |
| 3 | E5 (`code-scout` sonnet, khusus notulen) | Baru aman setelah `elicit` tidak lagi memakai scout. |
| 4 | E6 (test baru + penyesuaian test lama) | Memaku kontrak E1–E5. |
| 5 | D1 (dokumen + versi) | Penutup. |

## Peta blast radius

Kolom **Konsumen** = siapa yang membaca perilaku yang berubah. Kolom **Test tersentuh** = test yang sudah ada dan
harus disesuaikan, bukan test baru.

| ID | Berkas diubah | Konsumen perilaku | Lintas plugin | Test tersentuh | Risiko regresi |
|---|---|---|---|---|---|
| E1 | `analyst/agents/code-explorer.md` (baru) | `analyst:elicit` | membaca profil backend/frontend (read-only) | `tests/test_lint_plugins.py` (F2) | Nihil: agent baru. |
| E2 | `analyst/skills/elicit/dispatcher/explorer.md` (baru), `analyst/skills/elicit/dispatcher/scout.md` (dihapus), `analyst/skills/_common/ticket.py` (daftar berkas `check --gate elicit`), `analyst/skills/_common/validate_doc.py` (teks check 11) | model, `check --gate elicit` | tidak | `tests/analyst/test_scout_18.py` (X2: path dispatcher dan test unlink gerbang) | Rendah: gerbang menagih berkas yang berganti nama. |
| E3 | `analyst/skills/elicit/SKILL.md`, `references/elicitation-tech.md`, `references/elicitation-guide.md` | model | tidak | `tests/test_lint_plugins.py` (R-check rujukan) | Sedang: arahan pra-isi `Asumsi:` mengubah cara bertanya; pagar check 11 dan `CLOSED` tetap. |
| E4 | `analyst/skills/intake/SKILL.md`, `analyst/skills/intake/references/batch.md` | model | tidak | — | Rendah: hanya kalimat rujukan. |
| E5 | `analyst/agents/code-scout.md`, `analyst/skills/notulen/dispatcher/scout.md` (satu kalimat mode) | `analyst:notulen` | tidak | `tests/analyst/test_scout_18.py` (X1: `model == "haiku"`) | Rendah: notulen selalu `KONTEKS`; `test_notulen_20.py` hanya memaku baris mode `KONTEKS`. |
| E6 | `tests/analyst/test_explorer_27.py` (baru) | CI | membaca `backend/agents/code-explorer.md` (K14) | — | Nihil |
| D1 | `analyst/README.md`, `flow/analyst.md`, `analyst/.claude-plugin/plugin.json` (deskripsi + versi), `.claude-plugin/marketplace.json` (deskripsi, lint M4), `CLAUDE.md` repo (paragraf analyst) | manusia, lint M4/M7 | tidak | `tests/test_lint_plugins.py` | Nihil |

**Tidak diubah:**

- `ticket-reviewer`: ia tetap membuka sendiri tiap bukti `TECH` (T1).
- `validate_doc.py` selain teks check 11, `ticket.py` selain daftar berkas, segel tiket, dan salinan segel di
  `precondition_lib.py` backend/frontend.
- `analyst:notulen` (`SKILL.md`, `notulen.py`, dan isi `dispatcher/scout.md` selain satu kalimat mode di E5).
- Hook dan `gate_text.py` backend/frontend; pengecualian `/analyst:*` sudah mencakup alur ini.
- Plugin `product` beserta salinan `code-scout`-nya.

## E1 [Tinggi] `elicit` hanya punya penelusur kode dangkal
- [ ] Selesai

`agents/code-explorer.md` menurut Kontrak (K3–K6, K9, K12).

## E2 [Tinggi] Dispatcher dan gerbang `elicit` terikat ke `code-scout`
- [ ] Selesai

`dispatcher/explorer.md` (slot, Slot Hidrasi, gerbang masuk, Penanganan Balikan), hapus `dispatcher/scout.md` milik
`elicit`, ganti daftar berkas `check --gate elicit`, dan teks check 11.

## E3 [Tinggi] Prosa `elicit` membuat peminta menceritakan keadaan sekarang
- [ ] Selesai

`SKILL.md`, `elicitation-tech.md`, dan `elicitation-guide.md` menurut Kontrak (K7, K8, K11).

## E4 [Sedang] `intake` dan batch menyebut `code-scout`
- [ ] Selesai

Kalimat rujukan `intake/SKILL.md` dan `batch.md` bagian 6 (K10, K11).

## E5 [Sedang] `code-scout` haiku dan masih menyebut `elicit`
- [ ] Selesai

Model sonnet, deskripsi khusus notulen, mode `BUKTI` dihapus, dan kalimat mode di `notulen/dispatcher/scout.md`
disesuaikan (K2).

## E6 [Sedang] Test kontrak explorer dan drift
- [ ] Selesai

`tests/analyst/test_explorer_27.py`:

- Frontmatter: `name: code-explorer`, `tools` persis `Read, Grep, Glob` (tanpa `Write`/`Edit`/`Bash`),
  `model: sonnet`, `maxTurns` angka.
- Balikan: blok `## Code Explorer`, baris `Pemanggilan: <n> dari <20 | 40>`, dan ketiga seksi `###` ada di agent.
- Dispatcher: merujuk `agents/code-explorer.md`, nama penuh `analyst:code-explorer` (K11), dan ketujuh slot ada.
- Gerbang: `check --gate elicit` `FAIL` bila `dispatcher/explorer.md` hilang (pola X2 Langkah 18).
- Drift (K14): `max(1, L - 15)`, `L + 35`, `30–50 baris`, `100 baris`, `120 baris`, `3 jendela`, dan `400 baris` ada di
  agent dan di `backend/agents/code-explorer.md`.
- Prosa: `elicit/SKILL.md` tidak lagi menyebut `code-scout`, dan `code-scout.md` tidak lagi menyebut `analyst:elicit`.

Penyesuaian: `test_scout_18.py` X1 (`model == "sonnet"`) dan X2 (dispatcher explorer). Test X3 check 11 tetap tanpa
perubahan perilaku.

## D1 [Rendah] Dokumen dan versi
- [ ] Selesai

- README analyst: paragraf subagent, diagram alur, tabel validator, dan butir roadmap "`code-scout` di `intake` dan
  `spec`".
- `flow/analyst.md`: tabel komponen, diagram, alur `elicit` Phase 0–2, tabel subagent, catatan read-only, dan baris
  failure.
- Deskripsi `plugin.json` dan `marketplace.json` (keduanya sama, lint M4).
- Paragraf analyst di `CLAUDE.md`.
- Versi analyst 0.16.0 → 0.17.0.

## Verifikasi ujung ke ujung (rencana)

Repo scratch kecil dengan layar daftar invoice berstatus Belum Bayar/Lunas dan aturan "hanya Admin yang boleh
membatalkan". Claude Code headless dengan `--plugin-dir` analyst dari working tree, prompt tanpa menyebut skill:
"tolong buatkan tiket: invoice perlu bisa dicicil". Hasil yang diharapkan:

- `analyst:code-explorer` didispatch (bukan `code-scout`, `Explore`, atau `code-explorer` plugin lain), mode
  `KONTEKS`, kedalaman `ringkas`.
- Konteks utama tidak memakai `Read`/`Grep`/`Glob` atas kode repo.
- `Kondisi Saat Ini` berisi `Asumsi:` tanpa rujukan berkas, dan pertanyaan pertamanya berbentuk konfirmasi.
- `validate_doc.py --kind elicit` `PASS` di tiap giliran.

## Batas yang dinyatakan apa adanya

- **Biaya**: tiap dispatch kini sonnet. Batch lima tiket membuka sampai lima explorer paralel di awal, ditambah
  susulan, jadi sampai sepuluh dispatch per batch.
- **Konfirmasi lebih panjang**: makin banyak `Asumsi:` dari kode, makin panjang ringkasan Phase 4. Ringkasan tetap per
  pilar.
- **Kebocoran istilah**: kalimat `KONTEKS` dalam bahasa pengguna adalah aturan prosa agent. Pagar mekanisnya tetap
  check 11 (`path:baris`) dan `scan_leaks` kartu di `--kind ticket`; istilah teknis tanpa rujukan di catatan elisitasi
  tidak tertangkap mesin.
- **Repo tanpa profil**: penelusuran tetap berjalan dengan `Confidence` maksimal `medium` (K5).

## Di luar cakupan

- Explorer di `intake` untuk membantu menentukan tipe (K10).
- Kode sebagai sumber fakta tanpa konfirmasi peminta untuk `Kondisi Saat Ini`. Alternatif K8 ini ditolak.
- Fan-out explorer per repo anak di root multi-repo (K12).
- Menyimpan balikan ke disk atau panen lintas sesi (K13).
- Pelonggaran kuota `code-scout` notulen (K2).
- `product:discover` dan salinan `code-scout` milik `product`.

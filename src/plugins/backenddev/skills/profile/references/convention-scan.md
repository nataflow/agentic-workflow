# Convention Scan — `profile`

Panduan titik pemindaian **15–17** (`domain-map.md`, `code-conventions.md`, `anti-patterns.md`) untuk mengisi berkas modular di direktori `.claude/profile/backenddev/`. Titik 1–14 ada di `scan-guide.md`; berkas ini melanjutkan penomorannya, tidak menggantikannya.

**Sumber pola spesifik stack.** Panduan ini menetapkan *apa* yang dicari; *bagaimana* mencarinya di stack yang terdeteksi diambil dari `## Navigation recipes` dan `## Layer taxonomy` pada `../stacks/<stack-id>.md`. Turunkan sendiri dari struktur nyata modul jika target pencarian tidak ada di sana, lalu laporkan resep yang dipakai sebagai temuan di Fase 7. Dilarang memakai pola stack lain sebagai pengganti.

**Ketiganya jarang berubah.** Yang dicatat di sini adalah keputusan arsitektur dan gaya yang bertahan lintas fitur, bukan potret kuantitas kondisi hari ini.

---

## Batas tegas antara tiga seksi

| Seksi / Berkas | Pertanyaan yang dijawab | Dilanggar berarti | Konsumen utama |
|---|---|---|---|
| `invariants.md` | Apa yang membuat repo ini **rusak**? | Runtime/build patah — blocker | `code-implementor`, `plan`, `audit`, `code-reviewer` |
| `anti-patterns.md` | Arah apa yang **dilarang ditempuh**? | Kode jalan, arahnya salah — temuan P2 | `code-implementor`, `audit`, `code-reviewer` |
| `code-conventions.md` | Repo ini **menulis kode seperti apa**? | Kode asing di repo sendiri | `code-implementor`, `plan` |

Satu fakta hanya boleh hidup di satu seksi. Menang yang paling kiri di tabel jika sebuah pola cocok di lebih dari satu seksi.

---

## 15. Domain Map → `domain-map.md`

Adapter: `## Navigation recipes` (titik masuk HTTP), `## API surface` (letak registrasi rute).

Peta modul **bisnis**, bukan kapabilitas runtime. Explorer memakainya untuk mengunci `Batas cakupan` sebelum Grep pertama; pendispatch memakainya untuk mengisi slot itu tanpa menebak path.

1. Ambil daftar direktori setingkat di bawah pola modularisasi hasil `scan-guide.md` titik 3.
2. Buang yang bukan domain: folder utilitas bersama, folder infrastruktur, folder generated.
3. Untuk tiap domain tersisa, tetapkan tiga fakta:
   - **path/glob modul** — akar direktori domain itu.
   - **permukaan aktif** — permukaan dari `surface-map.md` yang benar-benar menyentuh domain ini, dipisah tanda `+` (mis. `http+consumer`). Domain tanpa permukaan runtime apa pun tetap dicatat dengan `internal`.
   - **entry `<file>#<simbol>`** — simbol tempat domain itu didaftarkan ke proses: fungsi registrasi rute, langganan antrean, atau perakitan konstruktornya. Bukti wajib, bukan perkiraan; bentuk anchor mengikuti `../templates/profile-template.md` § Tata cara anchor bukti, dan nomor baris dilarang.
4. Batas 12 baris. Gabungkan yang sekeluarga di bawah satu baris induk dan sebutkan anaknya dalam kurung jika domain lebih dari 12; dilarang memotong daftar diam-diam.
5. Tulis satu baris untuk modul tunggal jika repo tidak terpecah per domain (flat feature, satu modul).

---

## 16. Code Conventions → `code-conventions.md`

Adapter: `## Layer taxonomy` (letak layer dan penamaannya), `## Navigation recipes` (lokalisasi).

### Aturan penetapan — mayoritas, bukan kesan

1. **Sampel minimal tiga berkas** per aspek, diambil dari domain berbeda menurut `domain-map.md`. Dua berkas bukan pola, itu kebetulan.
2. Pola yang dianut **mayoritas sampel** yang ditulis sebagai konvensi. Pola minoritas turun jadi kandidat titik 17 (`anti-patterns.md`).
3. **Inkonsistensi & Sampel Terbelah (Style A vs Style B)**:
   - Tangani sampel terbelah (misal 50/50) atau dua gaya yang saling bertentangan secara signifikan (misal Gaya A di modul X vs Gaya B di modul Y):
   - **DILARANG** menebak atau memilih secara sepihak.
   - Catat anchor konkret `<file>#<simbol>` dari kedua gaya tersebut.
   - Formulasikan pertanyaan eksplisit ke user pada Fase 3 Wawancara: Gaya mana yang ingin dibakukan sebagai standar repo ke depan?
   - Masukkan pilihan user ke `code-conventions.md`, dan masukkan gaya yang ditolak ke `anti-patterns.md` dengan penanda `bukti user`.
4. Pakai sampel yang ada jika repo terlalu kecil untuk tiga sampel, dan tandai barisnya `(sampel <n>)`. Anchor baris itu boleh berhenti di `<file>` telanjang selama pola kanoniknya belum mengendap — repo muda belum punya simbol yang layak ditunjuk sebagai teladan.
5. Tiap baris wajib berakhir `contoh <file#simbol>` yang menunjuk **contoh kanonik** — simbol terbaik yang boleh ditiru implementor, bukan sekadar kemunculan pertama. Bentuk anchor mengikuti `../templates/profile-template.md` § Tata cara anchor bukti; nomor baris dilarang.

### Sembilan aspek kanonik

Periksa berurutan; aspek yang tidak terbukti barisnya dihapus, bukan diisi `tidak terdeteksi`.

| Aspek | Yang membuktikannya |
|---|---|
| `penamaan` | Pola nama berkas dan tipe per peran layer, dibanding lintas domain |
| `error` | Bentuk nilai/objek error, cara dibungkus dan dipropagasi, letak definisi error bersama |
| `tipe batas` | Letak tipe request/response dan mekanisme pemetaannya ke tipe domain — manual, mapper, atau generated |
| `validasi` | Lapisan tempat validasi input dijalankan dan mekanismenya |
| `logging` | Pustaka log yang dipakai, terstruktur atau tidak, field korelasi wajib |
| `wiring` | Cara dependensi dirakit: container, modul framework, atau konstruktor manual |
| `envelope` | Bentuk baku badan response sukses dan gagal |
| `test` | Letak berkas test relatif ke berkas ujinya, pola penamaan, gaya (table-driven, nested, given-when-then), fixture |
| `nilai kosong` | Perlakuan nilai absen: tipe opsional, pointer, atau nilai nol — dan di lapisan mana diputuskan |

Format baris: `<aspek>: <aturan satu frasa> · contoh <file#simbol>`. Maksimal 10 baris.

---

## 17. Anti-patterns → `anti-patterns.md`

Dua sumber sah, tidak ada yang ketiga:

1. **Bukti repo.** Pola minoritas hasil titik 16 dan pola warisan yang masih hidup. Syarat naik jadi anti-pattern: ada **pola pengganti yang jadi mayoritas** di repo yang sama. Pola minoritas tanpa pengganti bukan anti-pattern — itu cuma keragaman; tanyakan ke user bila menimbulkan ambiguitas.
2. **Konfirmasi user Fase 3.** Aturan tim yang tidak meninggalkan jejak di kode, atau keputusan user atas eliminasi salah satu style pada inkonsistensi yang terdeteksi. Ditandai `bukti user`; dilarang mengarang anchor maupun `deteksi` untuknya — polanya memang tak berjejak di kode.

Dilarang menyalin butir `## Audit checklist` adapter ke sini. Profil mencatat keputusan lokal dan harus bertahan.

Format baris, dua bentuk menurut sumbernya. Maksimal 8 baris. Nihil ditulis `Nihil (tidak terdeteksi)`.

```
- <pola terlarang> (<sebaran>) → <pola pengganti> · deteksi `<pola> @ <cakupan>` · bukti <file#simbol>
- <pola terlarang> → <pola pengganti> · bukti user
```

**Aturan `deteksi`.** Ia resep `Grep` — pola pencarian, tanda `@`, lalu glob cakupannya — diturunkan dari `## Navigation recipes` adapter bila ada resep yang cocok. Wajib mengembalikan minimal satu hit saat profil ditulis; nol hit berarti polanya tidak ada di repo ini dan barisnya batal, bukan dilunakkan. Resep boleh menangkap lebih luas daripada polanya — ia pencari kandidat, bukan vonis — maka `<sebaran>` diisi dari hit yang lolos saringan, bukan dari jumlah hit mentah. Pola struktural yang tidak terjangkau satu Grep (mis. arah dependensi antar-layer) bukan kandidat bersumber repo — bawa ke Fase 3 sebagai pertanyaan, lalu tulis hasilnya sebagai baris `bukti user`.

**Pada mode `REFRESH`**, jalankan `deteksi` tiap baris anti-pattern profil lama sebelum wawancara dan bawa vonisnya ke Fase 3: `[MASIH HIDUP — <n> hit]` atau `[PUNAH — 0 hit]`. Baris punah **dilarang dicabut sepihak** — user yang memutuskan, karena nol hit bisa saja berarti resepnya yang salah tulis, bukan polanya yang benar-benar habis.

---

## Skrip wawancara Fase 3 (Inkonsistensi & Konfirmasi)

Satu giliran, terstruktur. Bila ada inkonsistensi arsitektur/konvensi, sertakan pertanyaannya bersama draf konvensi:

```
[INKONSISTENSI TERDETEKSI] (Bila ada pola terbelah / bertentangan):
  1. Aspek <aspek>:
     - Gaya A: <deskripsi pola A> · contoh <file1#simbol1>
     - Gaya B: <deskripsi pola B> · contoh <file2#simbol2>
     -> Mau membakukan Gaya A atau Gaya B sebagai standar ke depan?

Draf konvensi repo (hasil scan):
  1. <aspek>: <aturan> · contoh <file#simbol>
  ...
Draf anti-pattern:
  A. <pola> → <pengganti> · deteksi `<pola> @ <cakupan>` (<n> hit) · bukti <file#simbol>
  ...
[REFRESH] Anti-pattern dari profil lama, konfirmasi ulang:
  L1. <baris lama>   [MASIH HIDUP — <n> hit]
  L2. <baris lama>   [PUNAH — deteksi 0 hit] cabut?

Pertanyaan:
- Untuk inkonsistensi di atas, pilih gaya standar yang diinginkan (A atau B).
- Untuk draf konvensi & anti-pattern: mana yang perlu ditambah, dicabut, atau diralat?
- Untuk baris bertanda [PUNAH]: cabut dari profil, atau resep `deteksi`-nya yang salah tulis?
(Kosongkan/jawab 'setuju' bila draf di atas sudah benar)
```

Aturan penutup: Keputusan user atas gaya pilihan langsung dicatat di `code-conventions.md` dan gaya yang dieliminasi masuk ke `anti-patterns.md` dengan `bukti user`.

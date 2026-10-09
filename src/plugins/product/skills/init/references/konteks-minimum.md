# Konteks Minimum — Guard Permintaan yang Terlalu Umum

Rumah kanonik guard `product:init`. Skrip penegaknya `charter.py guard` (read-only) dan `charter.py new` (menolak
alokasi); daftar kata yang terlalu umum dan label tiap butir tinggal di `_common/charter_lib.py`
(`VAGUE`, `VAGUE_PERSON`, `CONTEXT_LABELS`).

## 1. Kenapa guard ini ada

Permintaan seperti *"saya ingin membuat aplikasi keuangan"* baru menyebut domain. Purpose, Actors, dan Success
Criteria semuanya bergantung pada **untuk siapa** dan **masalah apa**: aplikasi keuangan pribadi, kasir UMKM, dan
akuntansi perusahaan adalah tiga produk berbeda. Elisitasi yang berangkat tanpa keduanya menghabiskan giliran untuk
menebak arah, atau lebih buruk, menulis charter untuk segmen yang tidak pernah disebut peminta.

Guard ini menyaring **apakah inisiatifnya sudah terdefinisi**, bukan menggali isinya. Penggalian milik
`product:discover`.

## 2. Tiga butir per mode

| Mode | `--untuk` | `--masalah` | `--lingkup` |
|---|---|---|---|
| `NEW_PRODUCT` | **Untuk siapa** — segmen pengguna utama | **Masalah utama** yang diselesaikan | **Domain** atau konteks pakai |
| `NEW_FEATURE` | **Pengguna** fitur itu | **Yang belum bisa dilakukan** sekarang | **Area** atau modul di aplikasi |
| `IMPROVEMENT` | **Yang terdampak** | **Yang salah atau kurang** dari kondisi sekarang | **Fitur** yang mana |

Label tebal ditulis apa adanya ke `### Konteks Awal` `CHARTER.md` dan dimateraikan `context_hash`.

## 3. Kapan butir dianggap belum terisi

Skrip menolak butir yang:

- kosong atau kurang dari 3 karakter;
- utuhnya kata atau frasa yang tidak mempersempit apa pun: *semua*, *siapa saja*, *umum*, *terserah*, *belum tahu*,
  *aplikasi*, *sistem*, dan sejenisnya. Frasa yang **memuat** kata itu tetap sah bila mempersempit: *semua cabang
  toko roti* lolos, *semua* saja tidak;
- `NEW_PRODUCT` saja: sebutan orang tanpa segmen untuk `--untuk` (*pengguna*, *user*, *pelanggan*, *konsumen*,
  *masyarakat*). Di codebase sebutan itu bisa jadi peran yang memang sudah ada di aplikasi, dan scout yang
  memastikannya;
- masih berupa placeholder (`<...>`, TBD, TODO).

Skrip tidak menilai mutu jawaban. Jawaban yang lolos tetapi dangkal tetap boleh lewat; kedalamannya digali
`product:discover`, dan `charter-reviewer` memeriksa Purpose dan Actors konsisten dengan Konteks Awal.

## 4. Cara bertanya

1. Petakan permintaan ke tiga butir lebih dulu. Butir yang **tersurat** di permintaan diisi langsung dengan kata-kata
   peminta. Hanya butir yang kosong yang ditanyakan.
2. Satu `AskUserQuestion`, maksimal tiga pertanyaan (satu per butir kosong), masing-masing 2–4 **opsi konkret** yang
   sekaligus mengajarkan bentuk jawaban yang dimaksud. Contoh untuk *"aplikasi keuangan"*:
   - *Untuk siapa?* — Keuangan pribadi / rumah tangga · Usaha kecil (UMKM, warung, toko) · Perusahaan (tim
     finance, akuntansi) · Lainnya
   - *Masalah utama apa yang mau diselesaikan?* — Pemasukan-pengeluaran tidak tercatat rapi · Tidak tahu untung-rugi
     · Tagihan dan utang sering terlewat · Lainnya
3. Jawaban *Lainnya* yang diketik user dipakai apa adanya.
4. Jalankan `charter.py guard`. `FAIL` → tanyakan hanya butir yang disebut keluarannya; maksimal **dua putaran**
   pertanyaan guard.

## 5. Tidak boleh lolos dengan asumsi

Jawaban *terserah*, *bebas*, atau *belum tahu* untuk segmen atau masalah **tidak** diisi tebakan analis. Jelaskan
satu kalimat: Purpose, Actors, dan Success Criteria semuanya bergantung pada butir itu, jadi mengisinya dengan
tebakan sama dengan mengarang isi charter. Tawarkan opsi rekomendasi beserta konsekuensinya. Dua putaran tetap tanpa
jawaban → tahan dengan blok `INIT — TERTAHAN` beserta pertanyaan yang siap diteruskan ke pengambil keputusan.

## 6. Kapan guard tidak berlaku

- Melanjutkan, mengubah, atau membatalkan charter yang sudah ada: Konteks Awalnya sudah dimateraikan.
- Konteks yang berubah total sesudah charter ada (segmen lain, masalah lain) berarti inisiatif baru: batalkan yang
  lama atas keputusan user, lalu jalankan guard untuk yang baru.

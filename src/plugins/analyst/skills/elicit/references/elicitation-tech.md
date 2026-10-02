# Panduan Elisitasi Tiket Teknis — `elicit` tipe `TECH`

Dimuat `analyst:elicit` Phase 1 **hanya** untuk tiket `type: TECH`; panduan ini menggantikan `elicitation-guide.md` bagian 1–3 dan 6 serta seluruh `literasi-teknis.md` untuk tipe itu. Rubrik urgensi → prioritas (bagian 4 `elicitation-guide.md`) tetap berlaku.

## 1. Siapa Peminta, Apa Hasilnya

Peminta tiket `TECH` adalah engineer, biasanya lead engineer, yang ingin satu perubahan teknis **dikunci sebelum dikerjakan**: refaktor lintas modul, relasi data, batas modul atau arah dependensi, kinerja, atau upgrade pustaka yang berdampak. Peminta sudah berbahasa teknis, jadi pertanyaan boleh teknis dan opsi boleh menyebut tabel, modul, atau pola. Yang tetap dilarang adalah **merancang solusi untuk peminta**: analyst mencatat keputusan peminta beserta alternatifnya, tidak memilihkan.

Kartu `TECH` berhenti di **kondisi target**, yaitu struktur akhir yang disepakati. Langkah implementasi, pembagian brief, dan estimasi tetap milik `backend:tech-lead` / `frontend:lead` di hilir.

## 2. Mode Ringkas

Lead engineer biasanya datang dengan brief yang sudah menjawab sebagian besar pilar. Urutannya:

1. **Petakan brief ke pilar.** Isi tiap pilar yang dijawab permintaan asli; yang tersirat ditulis `Asumsi:`.
2. **Verifikasi kode lewat scout.** Klaim tentang kondisi sekarang dikirim ke subagent `analyst:code-scout` `mode: BUKTI` (`../dispatcher/scout.md`, 1–5 klaim per dispatch, maksimal 2 dispatch per sesi). Scout memegang **kuota 8 pemanggilan** `Read`/`Grep`/`Glob`, khusus untuk membuktikan klaim peminta, bukan untuk menjelajah. Konteks utama tidak membaca kode sendiri. Hanya butir `Ditemukan` yang dicatat sebagai `` `path:baris` `` di pilar `Kondisi Saat Ini`. Klaim yang `Tidak ditemukan`, `Belum disisir`, atau dibantah kode → tanyakan ke peminta di giliran berikutnya, bukan dikoreksi diam-diam.
3. **Tanya celahnya saja.** Giliran tanya-jawab (≤ 3 pertanyaan) hanya untuk pilar wajib yang masih kosong, `Asumsi:` yang perlu dikonfirmasi, dan klaim yang tidak cocok dengan kode.

Bukti yang dicatat menunjuk berkas di **repo tempat tiket ini tinggal**, relatif terhadap root-nya. `validate_doc.py --kind ticket` memeriksa tiap `path:baris` kartu benar-benar ada. Rujukan ke repo lain ditulis di `## Lampiran` kartu, bukan sebagai bukti.

## 3. Pilar `TECH`

| Pilar | Isi | Wajib |
|---|---|---|
| `Masalah Teknis` | Masalahnya, dampaknya (bug berulang, biaya ubah, insiden, angka kinerja), dan kenapa sekarang. | ya |
| `Kondisi Saat Ini` | Struktur sekarang. Tiap fakta membawa `` `path:baris` `` yang sudah dibaca. | ya |
| `Kondisi Target` | Struktur akhir: modul, tabel atau relasi, arah dependensi, kontrak yang tetap. Bukan urutan langkah. | ya |
| `Batasan` | Yang tidak boleh berubah atau dilanggar: kontrak API, kompatibilitas data, zero-downtime, invariant profil repo. | ya |
| `Batas Cakupan` | Yang sengaja tidak dikerjakan beserta alasannya. | ya |
| `Urgensi` | Tenggat atau pekerjaan lain yang bergantung padanya. | ya |
| `Keputusan` | Pilihan yang sudah diambil peminta beserta alasan dan alternatif yang ditolak. | opsional |
| `Rollout` | Urutan rilis, migrasi data, jalan mundur. | opsional |
| `Ukuran Keberhasilan` | Angka atau pemeriksaan yang membuktikan selesai. | opsional |

Urutan giliran: Masalah Teknis → Kondisi Saat Ini → Kondisi Target → Batasan → Batas Cakupan → Urgensi.

## 4. Kategori

`category` ditetapkan `analyst:intake` dan menentukan apa yang wajib digali sebelum elisitasi ditutup. Ia juga menjadi rubrik `ticket-reviewer`.

| `category` | Pemicu | Wajib tergali |
|---|---|---|
| `REFACTOR` | Struktur kode berubah, perilaku tidak | Perilaku apa yang dijaga tetap dan alat ukurnya (test yang ada, snapshot) |
| `DATA_MODEL` | Relasi, tabel, kolom, atau constraint berubah | Nasib data lama (backfill, default), migrasi naik dan turun |
| `ARCHITECTURE` | Batas modul, arah dependensi, atau pola lintas fitur berubah | Minimal satu keputusan beserta alternatif yang ditolak |
| `PERFORMANCE` | Latensi, kueri, memori, atau beban | Angka sekarang, angka target, dan cara mengukurnya |
| `DEPENDENCY` | Pustaka, runtime, atau framework naik versi atau diganti | Versi asal dan tujuan, perubahan yang memecah kompatibilitas |

## 5. Pertanyaan Memblokir

`MEMBLOKIR` ⇔ jawabannya mengubah `Kondisi Target`, `Batasan`, atau `Batas Cakupan`, atau bukti kode bertentangan dengan klaim peminta. Selain itu `TIDAK MEMBLOKIR` dan dibawa `spec` sebagai asumsi.

## 6. Yang Bukan Tiket `TECH`

Perbaikan kecil di satu berkas, stacktrace yang perlu didiagnosis, dan pertanyaan letak kode langsung ke `backend:tech-lead` / `frontend:lead`. Perubahan yang menyentuh dua repo menjadi dua tiket `TECH`, satu di tiap repo, yang saling merujuk di `## Lampiran`.

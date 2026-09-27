# Panduan Elisitasi Kebutuhan Bisnis — `business-analysis`

Dibaca di Fase 2 (`SKILL.md`) untuk memandu elisitasi terarah dan mencegah aturan bisnis kritis terlewat atau diasumsikan sepihak.

## 1. Delapan Pilar Domain

Enam pilar wajib dievaluasi tiap sesi; dua pilar opsional boleh ditunda dengan alasan dicatat di seksi BRD pemiliknya sebagai penegasan eksplisit (mis. `## Edge cases`: "Tidak ada pengecualian disepakati — <alasan>"). Pilar wajib dilarang dilewati dengan alasan apa pun.

| Pilar | Status | Cakupan inti |
| --- | --- | --- |
| Problem | wajib | Siapa terdampak, frekuensi, kuantifikasi biaya pembiaran, urgensi |
| Actors | wajib | Peran pengguna berikut hak akses dan larangan mutlaknya, plus aktor sistem (scheduler, webhook consumer, message listener) |
| Current State | wajib | Alur aktual langkah demi langkah beserta workaround manual di luar sistem |
| Target State | wajib | Alur baru, perubahan tanggung jawab peran, strategi transisi data eksisting |
| Business Rules | wajib | Invariant mutlak, formula, pembulatan, batas kuota, resolusi saat dua aturan bertentangan |
| Out of Scope | wajib | Batasan yang sadar ditunda ke fase berikutnya, penahan scope creep |
| Edge Cases | opsional | Data kosong/null, idempotensi, TTL, retry policy, in-flight rollback |
| Business Metrics | opsional | Metrik bisnis kuantitatif ber-ID `BM-{n}` beserta baseline dan pihak pengobservasinya |

## 2. Kuantifikasi Masalah & Biaya Pembiaran

Keluhan umum ("lambat", "membingungkan") bukan temuan. Gali indikator konkret:

- **Aktor terdampak langsung & turunan**: siapa mengalami insiden terakhir, dan siapa yang membereskan dampak sampingnya (CS, akuntansi, operasional).
- **Frekuensi**: tiap transaksi, hanya beban puncak (flash sale, end-of-month), atau insidental saat kegagalan jaringan.
- **Biaya pembiaran (Cost of Inaction)**:
  - *Finansial*: selisih saldo, denda SLA, kehilangan penjualan.
  - *Operasional*: jam kerja manual terbuang untuk rekonsiliasi.
  - *Integritas data*: data menggantung tanpa pemilik, status entity tidak sinkron.

## 3. Pemodelan Aktor & Batasan Kewenangan

Istilah generik "user" dilarang. Petakan aktor spesifik:

| Jenis aktor | Pertanyaan kunci | Contoh |
| --- | --- | --- |
| Primer | Siapa sadar menginisiasi proses? Apa batas haknya? | Kasir, Pembeli, Admin Cabang |
| Sekunder / Approver | Siapa memverifikasi atau menyetujui transisi status? | Supervisor, Finance Manager |
| Sistem (non-manusia) | Proses otomatis apa yang memicu perubahan tanpa intervensi? | Scheduler cron, Webhook payment, Queue consumer |
| Terlarang | Siapa yang eksplisit dilarang mengakses alur ini? | User anonim, user beda cabang/tenant |

Tiap peran wajib punya daftar aksi yang diizinkan dan aksi yang tegas dilarang. Identifikasi juga skenario perpindahan atau pencabutan hak akses di tengah transaksi berjalan.

## 4. Formulasi Aturan Bisnis Deterministik (`BR-{n}`)

Tiap aturan di `## Business rules` mengikuti struktur:

```
[Kondisi Pemicu] + [Prasyarat Validasi] ──► [Aksi Sistem / Invariant Wajib]
```

- **Tanpa kata sifat subjektif**: ganti "nominal wajar" dengan `nominal <= Rp 10.000.000`; ganti "proses cepat" dengan `maksimal 1x24 jam kerja`.
- **Resolusi konflik**: bila Aturan A bertentangan dengan Aturan B pada kondisi tertentu, tetapkan aturan mana yang berprioritas.
- **Invariant entitas**: aturan yang tidak boleh dilanggar jalur atau aktor mana pun ("saldo tidak boleh negatif", "nomor invoice tidak boleh berulang").

## 5. Taksonomi Kasus Batas

Lima kategori untuk membedah celah alur. Ini **rumah kanonik** taksonominya: slug di dalam kurung adalah label yang dipikul tiap `EC-{n}` di BRD, dan kelimanya wajib tersapu — kategori tanpa kasus disebut namanya di baris `Kategori nihil:` beserta alasannya.

1. **Ketiadaan data** (`data-hilang`): field opsional tidak dikirim — proses ditolak, memakai default bisnis, atau menunggu input susulan?
2. **Duplikasi & idempotensi** (`duplikasi`): submit ditekan dua kali atau event diterima dobel — transaksi kedua ditolak, diabaikan diam-diam, atau menghasilkan error informatif?
3. **Pembatalan in-flight** (`in-flight`): gagal di langkah 3 dari 5 — rollback penuh, tersimpan sebagian sebagai DRAFT, atau butuh kompensasi manual?
4. **Timeout & expiry** (`timeout`): akibat bisnis bila pembayaran lewat batas waktu, dan kapan alokasi stok atau kuota dilepaskan kembali?
5. **Perubahan status eksternal** (`status-eksternal`): akun aktor dibekukan atau hak aksesnya dicabut saat transaksi menunggu persetujuan.

## 6. Metrik Bisnis & Observabilitas

- **Metrik kuantitatif (`BM-{n}`)**: nyatakan baseline saat ini vs target ("verifikasi manual 15 menit → 0 menit", "duplikasi order → 0%").
- **Auditabilitas**: siapa memantau metrik dan dari mana data diverifikasi (laporan harian, log audit transaksi).

## 7. Pertahanan Batas Ruang Lingkup

- Catat eksplisit fitur terkait yang dibicarakan tetapi disepakati ditunda ke fase berikutnya.
- Nyatakan batas integrasi: berhenti di notifikasi internal, atau mencakup sistem pihak ketiga.

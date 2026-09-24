# UI Patterns & Visual Layout Reference

Panduan pola tata letak, komponen interaktif, penanganan multi-state, standar aksesibilitas WCAG, dan spesifikasi lintas-platform (Web & Mobile) untuk skill `frontenddev:ui-design`. Bagian platform hanya berlaku sesuai field `stack` profil; detail API-nya (nama hook, atribut, komponen) ada di `## UI & navigation surface` adapter.

---

## 1. Platform-Specific Design Principles

### Web Layout & Responsive Breakpoints (`react-vite`, `sveltekit`, `svelte-vite`):
- **Responsive Grid**: Mobile (< 640px), Tablet (768px - 1023px), Desktop (>= 1024px).
- **Form Density**: Jarak antar baris input standar 16px (*spacious*) atau 12px (*dense*) dengan pesan validasi error merah di bawah field terkait.
- **Scroll Container Isolation**: Batasi overflow scroll pada container daftar data agar navigasi header dan footer tetap sticky di viewport.
- **Dialog vs Drawer**: Dialog modal di tengah untuk konfirmasi destruktif; Side Drawer untuk formulir panjang atau filter parameter sekunder.
- **Form Validation States**: Tampilkan status validasi real-time (hijau/merah) dengan ikon konfirmasi di dalam input.
- **SSR Awareness** (`sveltekit`): Skeleton dan state awal wajib deterministik agar markup server sama dengan client; nilai tergantung browser (tanggal lokal, lebar viewport) dirender sesudah mount.

### Mobile Layout Patterns (`react-native`):
- **Safe Area Insets**: Selalu terapkan padding safe area pada container root layar untuk menghindari notch dan home indicator bar.
- **Minimum Touch Targets**: Seluruh tombol, ikon aksi, dan baris daftar wajib memiliki area tekan minimal 44x44 dp via `hitSlop` atau `minHeight`.
- **Keyboard Handling**: Gunakan keyboard avoidance dengan perilaku padding (iOS) atau height (Android).
- **Bottom Sheet vs Web Dropdown**: Gunakan modal bottom sheet untuk pemilihan opsi atau aksi singkat pengganti dropdown select web.
- **Header Actions**: Batasi ikon header kanan maksimal 2 aksi untuk menghindari tabrakan judul di layar sempit.

---

## 2. Information Priority Hierarchy (P1 - P3)

| Level Prioritas | Peran Visual | Contoh Elemen Antarmuka | Panduan Penerapan Visual |
|---|---|---|---|
| **Primary (P1)** | Informasi utama penentu keputusan dan aksi utama | Nilai total uang, nama item utama, status inti, tombol CTA primer | Kontras tinggi, ukuran font terbesar (*text-lg / h2*), penempatan di bagian atas atau sticky bawah |
| **Secondary (P2)** | Metadata kontekstual pendukung | Tanggal transaksi, kategori item, nomor invoice, badge status sekunder | Warna teks netral-menengah (*text-muted-foreground*), font reguler (*text-sm*) |
| **Tertiary (P3)** | Detail pelengkap dan aksi sekunder yang jarang | Teks bantuan (*helper text*), tombol filter minor, tautan syarat & ketentuan | Warna muted (*text-muted*), ukuran font terkecil (*text-xs*), posisi pojok atau footer |

---

## 3. The Complete 6-State UI Matrix

Setiap rancangan antarmuka pengguna wajib mendefinisikan perilaku dan elemen visual untuk 6 cabang state:

| State Cabang | Representasi Visual | Elemen Penting & Perilaku Interaktif |
|---|---|---|
| **1. Initial / Idle** | Tampilan bersih form kosong | Placeholder teks informatif, kursor autofokus pada field pertama, CTA disabled |
| **2. Loading** | Skeleton shimmer terisolasi | Pertahankan dimensi layout skeleton agar tidak memicu Cumulative Layout Shift (CLS) |
| **3. Empty State** | Ilustrasi ikon + pesan ramah | Judul ramah, teks penjelasan manusiawi, dan tombol aksi primer (CTA) untuk input baru |
| **4. Error State** | Banner / kartu pesan error | Deskripsi penyebab error manusiawi + tombol aksi *Coba Lagi* (*Retry*) nyata |
| **5. Success / Ready** | Tampilan data lengkap | Kontras visual optimal, badge status berwarna semantik, aksi sekunder aktif |
| **6. Stale / Mutating** | Data lama tetap tampil dengan overlay | Indikator spinner halus di header, disable tombol submit untuk mencegah double submit |

---

## 4. Accessibility & Interaction Standards

- **Accessible Icon Labels**: Seluruh tombol berbasis ikon wajib memiliki atribut label sesuai adapter — `aria-label` (Web) atau `accessibilityLabel` (React Native).
- **Color Contrast Compliance**: Rasio kontras teks minimal 4.5:1 terhadap warna latar belakang untuk teks reguler (WCAG AA).
- **Visual Focus States**: Sediakan outline fokus visual yang tegas (*focus-visible:ring-2*) untuk navigasi keyboard pada aplikasi web.
- **Immediate Feedback**: Setiap interaksi sentuh atau klik wajib memberikan umpan balik instan (*active:scale-95*, *opacity-70*, atau spinner).
- **Screen Reader Announcements**: Gunakan `aria-live="polite"` (Web) atau `accessibilityLiveRegion="polite"` (React Native) untuk membacakan pesan error asinkron tanpa memotong navigasi aktif.
- **Compiler a11y warnings** (Svelte): warning a11y compiler adalah temuan desain, bukan noise; dilarang dirancang untuk dibungkam.

---

## 5. Cumulative Layout Shift (CLS) Prevention

- **Dimensi Skeleton**: Skeleton placeholder wajib memiliki tinggi (`height`), lebar (`width`), dan margin yang identik dengan kartu konten asli.
- **Aspect Ratio Locking**: Gunakan `aspect-ratio` atau container tetap pada pemuatan gambar avatar/thumbnail agar layout tidak melompat saat gambar termuat.
- **Font Display Fallback**: Gunakan `font-display: swap` dengan ukuran metrik fallback font sistem yang presisi untuk mencegah flash of unstyled text (FOUT).
- **Placeholder Min-Height**: Terapkan `min-height` pada dynamic container (misal daftar feed) agar footer tidak melompat saat data termuat.

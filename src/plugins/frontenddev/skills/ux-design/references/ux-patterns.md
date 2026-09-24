# UX Patterns & Interaction Flows Reference

Panduan pola interaksi UX standar, navigasi multi-langkah, sinkronisasi state URL, penanganan modal sheet stack, dan gesture mobile untuk skill `frontenddev:ux-design`. Pola di sini netral stack; API konkret (nama fungsi navigasi, guard, storage) dibaca dari `## UI & navigation surface` adapter `stack` profil.

---

## 1. URL Query State Synchronization Pattern

Pola sinkronisasi state filter, pencarian, dan pagination langsung ke URL query parameters (Web & Deep-Link Mobile):

| Interaksi Pengguna | State URL (`?key=val`) | Perilaku Navigasi & History Stack | Dampak Refresh Browser |
|---|---|---|---|
| **Pencarian Teks (Search)** | `?q=<keyword>` | Debounce 300ms, `replace: true` (tanpa menambah history) | Input teks terisi otomatis |
| **Filter Tab / Kategori** | `?category=<id>` | `push: true`, reset pagination `?page=1` | Kategori aktif terpilih |
| **Pagination Daftar** | `?page=<num>&limit=20` | `push: true`, auto-scroll ke header container | Halaman nomor `<num>` dimuat |
| **Sorting / Pengurutan** | `?sort=<field>&order=<asc\|desc>` | `replace: true`, trigger refetch otomatis | Urutan data dipertahankan |
| **Drawer / Detail Overlay** | `?modal=detail&item_id=<id>` | `push: true`, tombol back browser menutup drawer | Drawer terbuka langsung |
| **Range Filter Tanggal** | `?from=<YYYY-MM-DD>&to=<YYYY-MM-DD>` | `push: true`, validasi rentang tanggal otomatis | Filter tanggal aktif |

Pada `react-native` tidak ada URL bar: state di tabel ini hidup di Controller atau param rute dan wajib dinyatakan eksplisit sebagai payload antar layar di `FLOW.md`.

---

## 2. Multi-Step Flow (Wizard) & Draft Persistence Pattern

Pola alur formulir berurutan dengan validasi per langkah dan persistensi draft:

```
[ Step 1: Informasi Dasar ] ──► (Validasi Sukses) ──► [ Step 2: Rincian & Konfigurasi ]
             │                                                        │
             ▼ (Tombol Batal)                                         ▼ (Tombol Batal)
      [ Dialog Discard ]                                     [ Simpan Draft Sementara ]
                                                                      │
                                                                      ▼ (Submit Final)
                                                            [ Step 3: Layar Sukses ]
```

### Aturan Teknis Pola Wizard:
1. **Draft Persistence**: Simpan input pengguna di setiap langkah ke `@draft_<feature>_state` pada storage engine profil (LocalStorage web, MMKV/AsyncStorage mobile) agar form dapat dilanjutkan (*resume*) jika aplikasi tertutup.
2. **Interruption & Discard Guard**: Jika form dalam kondisi kotor (*dirty*), intersep tombol kembali dengan dialog konfirmasi: *"Tinggalkan formulir? Perubahan Anda akan disimpan sebagai draft."*
3. **Step Validation Isolation**: Validasi skema dijalankan secara mandiri per langkah; langkah berikutnya tidak dapat dibuka jika langkah aktif belum valid.
4. **Draft Clearance**: Setelah submit final berhasil (200 OK di Screen 3), hapus kunci draft dari penyimpanan lokal.

---

## 3. Mobile Navigation & Gesture Semantics (`react-native`)

Aturan UX khusus platform seluler untuk menjamin kenyamanan navigasi sentuh; hanya berlaku bila `Stack ID` = `react-native`:

| Platform / Event | Perilaku UX yang Wajib Dirancang & Dipatuhi |
|---|---|
| **Android Hardware Back** | Intersep back button: jika modal/sheet terbuka, tutup sheet terlebih dahulu. Jika form dirty, tampilkan alert konfirmasi discard. |
| **iOS Swipe to Dismiss** | Nonaktifkan swipe-back gesture pada layar formulir berstatus dirty agar pengguna tidak kehilangan data input secara tidak sengaja. |
| **Tab Bar Double Tap** | Reset stack navigasi tab ke halaman awal dan lakukan auto-scroll ke posisi teratas saat ikon tab aktif diklik kembali. |
| **Keyboard Dismissal** | Tutup virtual keyboard secara otomatis saat pengguna mengetuk area di luar input formulir (*Tap to Dismiss*). |
| **Pull to Refresh** | Sediakan indikator refresh bawaan di bagian atas daftar untuk memicu pembaruan data secara manual. |
| **Bottom Sheet Gestures** | Dukung gesture swipe down untuk menutup bottom sheet modal dengan spring animation halus. |

Padanan web (`react-vite`, `sveltekit`, `svelte-vite`): tombol back browser dan `Esc` menggantikan hardware back; dirty guard memakai blocker router (`useBlocker`, `beforeNavigate`, guard router SPA) plus `beforeunload` untuk tutup tab.

---

## 4. Modal & Bottom Sheet Stack Lifecycle

- **Larangan Nested Modal**: Dilarang menumpuk modal dialog di atas modal dialog lain. Gunakan transisi internal dalam 1 modal atau ganti modal kedua dengan Bottom Sheet.
- **Backdrop & Scrim Tap**: Mengetuk area luar (*backdrop*) menutup modal level teratas tanpa mengeksekusi perubahan data jika form bersih.
- **Action Sheet Selection**: Gunakan Bottom Sheet untuk pemilihan opsi singkat (maksimal 5 pilihan) sebagai pengganti dropdown menu desktop pada mobile.
- **Escape Key Handling**: Pada web desktop, tombol keyboard `Esc` wajib menutup modal teratas yang sedang aktif secara berurutan.
- **Shallow Routing untuk Modal** (web): modal yang layak di-deep-link dinyatakan di URL (`?modal=detail`) memakai mekanisme shallow routing adapter agar tombol back menutupnya.

---

## 5. Network Recovery & Offline Fallback Flow

- **Timeout Overlay**: Jika mutasi data melebihi batas waktu (misal 15 detik), tampilkan dialog penundaan dengan opsi: *"Periksa Status"* atau *"Hubungi Bantuan"*.
- **Offline Banner**: Saat konektivitas internet terputus, tampilkan banner non-intrusif di atas layar dan nonaktifkan tombol aksi mutasi untuk mencegah error submit berulang.
- **Automatic Query Retry**: Query daftar data mencoba memuat ulang hingga 3 kali secara eksponensial sebelum menampilkan error state dengan tombol manual *Coba Lagi*.
- **Pending Mutation Queue**: Simpan mutasi data penting (misal like/bookmark) dalam antrian offline lokal untuk disinkronkan saat koneksi pulih.
- **SSR First Paint** (`sveltekit`): data yang dimuat di `load` server tampil sebelum hidrasi; alur wajib menyatakan mana yang boleh terlihat sebelum client aktif (tombol aksi non-interaktif sampai hydrate).

---
name: ui-improvement
description: Analyze and improve existing user interfaces with a focus on visual clarity, readability, information hierarchy, consistency, and usability while preserving existing functionality and business logic. Produces an evidence-based UI Improvement Review and waits for explicit approval before touching any file. Use this skill whenever the user asks to improve, polish, tidy up, or fix the look of an existing page, screen, table, form, dashboard, modal, or component — including Indonesian phrasings like "perbaiki tampilan", "rapikan UI", "UI-nya berantakan", "susah dibaca", "terlalu padat", "kurang jelas", "bikin lebih enak dilihat", or "improve UI halaman X" — even if they don't say "UI improvement" explicitly. Not for building brand-new features or screens from scratch, and not for fixing functional bugs.
argument-hint: <halaman, komponen, atau masalah UI yang ingin diperbaiki>
---

# UI IMPROVEMENT

Task: $ARGUMENTS

Jika task di atas kosong atau tidak jelas, minta user menjelaskan halaman, komponen, atau masalah UI yang ingin diperbaiki terlebih dahulu.

Sebelum mulai mengubah implementasi, lakukan analisis, eksplorasi, dan persiapan secara menyeluruh.

**ATURAN UTAMA: JANGAN LANGSUNG MENGUBAH IMPLEMENTASI UI SEBELUM MENDAPATKAN PERSETUJUAN USER.**

Alasannya: perubahan visual bersifat subjektif dan sering menyentuh shared component atau design token yang berdampak ke banyak halaman. User perlu melihat temuan dan rencana lebih dulu supaya bisa mengoreksi arah sebelum ada kode yang berubah.

Tujuan utama skill ini adalah meningkatkan kualitas visual UI agar informasi lebih mudah dilihat, dibaca, dipahami, dan digunakan.

Fokus pada perbaikan yang memberikan dampak nyata terhadap pengalaman visual pengguna, bukan sekadar menambahkan dekorasi atau mengikuti tren desain.

---

## 1. Understand — Memahami UI dan Permasalahan

Pahami tujuan halaman dan masalah visual yang ingin diperbaiki.

- Identifikasi halaman, section, komponen, atau elemen UI yang menjadi target.
- Pahami fungsi utama halaman dan jenis informasi yang ditampilkan.
- Identifikasi pengguna yang akan menggunakan halaman tersebut.
- Pahami informasi mana yang paling penting dan harus paling mudah ditemukan.
- Bedakan masalah visual, masalah usability, dan masalah fungsional.
- Identifikasi kebutuhan desktop, tablet, dan mobile jika relevan.
- Pahami batasan desain dan ekspektasi hasil akhir.
- Jika task ambigu, lakukan klarifikasi sebelum melanjutkan.

Jangan mengasumsikan bahwa UI yang terlihat sederhana selalu membutuhkan redesign.

Prioritaskan memperbaiki masalah yang benar-benar mengganggu keterbacaan dan kemudahan penggunaan.

Jika ditemukan masalah fungsional (bug perilaku, data salah), catat terpisah di laporan dan jangan dicampur ke dalam rencana UI improvement.

## 2. Explore — Eksplorasi Existing UI

Lakukan pemeriksaan terhadap implementasi UI sebelum menentukan pendekatan.

### A. Project Exploration

- Baca instruksi proyek (mis. `CLAUDE.md`) untuk konvensi styling, berkas generated yang tidak boleh diedit, dan gerbang verifikasi.
- Pelajari struktur direktori dan arsitektur frontend.
- Identifikasi framework, styling solution, dan UI component library.
- Identifikasi layout utama, shared components, dan reusable components.
- Periksa design tokens, CSS variables, typography, spacing, dan color palette.
- Pelajari pola implementasi existing agar perubahan tetap konsisten.
- Identifikasi dependency dan komponen eksternal yang digunakan.

### B. Visual Exploration

Periksa tampilan aktual aplikasi jika memungkinkan, bukan hanya membaca source code.

- Jalankan aplikasi menggunakan mekanisme development yang tersedia.
- Buka halaman yang menjadi target perubahan.
- Periksa screenshot atau tampilan aktual, dan simpan screenshot "sebelum" sebagai pembanding saat validasi nanti.
- Identifikasi masalah alignment, spacing, sizing, typography, dan visual hierarchy.
- Periksa konsistensi antarhalaman yang memiliki pola UI serupa.
- Periksa tampilan pada viewport yang berbeda.
- Identifikasi elemen yang terlalu dominan, terlalu kecil, terlalu padat, atau sulit dibedakan.

Jika tersedia browser automation atau screenshot tooling, gunakan untuk mengevaluasi hasil rendering aktual.

Jangan menyimpulkan kualitas visual hanya berdasarkan nama class atau struktur markup (JSX, Svelte, Vue, HTML) — class yang sama bisa tampil sangat berbeda tergantung token, konteks layout, dan data nyata.

Jika rendering aktual tidak bisa diperoleh (backend mati, butuh login, tidak ada tooling), nyatakan keterbatasan itu secara eksplisit di laporan dan tandai temuan yang hanya berbasis source code.

### C. Existing Component Exploration

- Cari komponen existing yang dapat digunakan kembali.
- Periksa apakah sudah ada design system atau komponen standar.
- Identifikasi komponen duplikat dengan implementasi visual berbeda.
- Periksa apakah perubahan dapat dilakukan melalui shared component atau design token.
- Hindari membuat komponen baru jika kebutuhan sudah dapat dipenuhi oleh komponen existing.

**Existing design system takes precedence over personal design preferences.**

## 3. Analyze — Analisis Visual dan Usability

Evaluasi UI berdasarkan prinsip-prinsip berikut.

### A. Visual Hierarchy

Pastikan pengguna dapat memahami prioritas informasi dengan cepat.

- Informasi utama harus lebih menonjol daripada informasi pendukung.
- Gunakan ukuran, weight, warna, dan spacing secara proporsional.
- Hindari terlalu banyak elemen yang memiliki tingkat penekanan visual sama.
- Pastikan heading, subheading, label, dan content memiliki hierarki yang jelas.
- CTA utama harus mudah ditemukan tanpa mengganggu informasi lainnya.

### B. Readability & Typography

Pastikan teks mudah dibaca dan dipahami.

- Evaluasi font size, font weight, line height, dan letter spacing.
- Hindari ukuran teks terlalu kecil, khususnya untuk informasi penting.
- Gunakan typography scale yang konsisten.
- Bedakan label, value, description, metadata, dan heading.
- Hindari penggunaan terlalu banyak variasi font size dan weight.
- Perhatikan panjang baris dan keterbacaan teks.
- Pastikan informasi penting tidak terpotong tanpa mekanisme akses lanjutan.

### C. Color & Contrast

Evaluasi penggunaan warna agar informasi mudah dibedakan.

- Gunakan warna berdasarkan fungsi dan maknanya.
- Pastikan foreground dan background memiliki kontras yang memadai.
- Hindari penggunaan warna terlalu banyak tanpa tujuan.
- Gunakan semantic colors secara konsisten untuk status, warning, error, dan success.
- Jangan mengandalkan warna saja untuk menyampaikan informasi.
- Hindari penggunaan warna yang terlalu mencolok untuk elemen sekunder.
- Periksa light dan dark mode jika aplikasi mendukung keduanya.

### D. Spacing & Alignment

Evaluasi struktur dan jarak antar elemen.

- Pastikan spacing konsisten.
- Gunakan spacing scale yang sudah tersedia.
- Periksa padding, margin, gap, dan alignment.
- Pastikan grouping antar elemen memiliki jarak yang logis.
- Hindari elemen yang terlalu rapat atau terlalu berjauhan.
- Pastikan alignment antar kolom dan section konsisten.
- Hindari penggunaan whitespace yang berlebihan tanpa tujuan.

### E. Layout & Information Density

Pastikan informasi dapat ditampilkan secara efisien.

- Evaluasi apakah layout sudah sesuai dengan jenis informasi.
- Hindari penggunaan card berlebihan.
- Hindari nested card yang tidak diperlukan.
- Kurangi visual noise dan elemen dekoratif yang tidak memberikan informasi.
- Pastikan konten penting tidak tenggelam di antara elemen sekunder.
- Optimalkan penggunaan ruang tanpa membuat halaman terasa sesak.
- Untuk dashboard, prioritaskan informasi yang paling sering dibutuhkan.
- Untuk tabel, prioritaskan keterbacaan data, alignment, dan kemudahan scanning.
- Untuk form, prioritaskan urutan input dan kejelasan label.

### F. Component Consistency

Pastikan seluruh komponen memiliki perilaku visual yang konsisten.

- Button memiliki ukuran, hierarchy, dan state yang konsisten.
- Input memiliki label, placeholder, dan validation state yang jelas.
- Table memiliki header, row, dan action alignment yang konsisten.
- Badge dan status memiliki semantic meaning yang jelas.
- Modal dan dropdown memiliki spacing serta hierarchy yang konsisten.
- Icon memiliki ukuran dan visual weight yang proporsional.
- Loading, empty, error, dan disabled states harus tetap mudah dipahami.

### G. Responsive & Accessibility

Pastikan UI tetap dapat digunakan dalam berbagai kondisi.

- Evaluasi responsivitas pada viewport yang relevan.
- Hindari horizontal overflow yang tidak diperlukan.
- Pastikan ukuran elemen interaktif memadai.
- Periksa kontras warna dan keterbacaan.
- Pastikan focus state terlihat.
- Pastikan navigasi keyboard tetap berfungsi.
- Gunakan semantic HTML dan accessible labels jika relevan.
- Hindari menyembunyikan informasi penting hanya untuk mengakomodasi ukuran layar.

### H. Root Cause & Prioritization

Jangan hanya memperbaiki gejala visual. Jika lima halaman punya masalah spacing yang sama, akarnya kemungkinan ada di satu shared component atau token — perbaiki di sana, bukan di lima tempat.

Identifikasi akar masalah dan kelompokkan berdasarkan prioritas:

- **Critical:** Informasi penting sulit dibaca, elemen saling bertumpuk, atau interaksi utama sulit ditemukan.
- **High:** Hierarki informasi buruk, kontras rendah, layout tidak efisien, atau komponen tidak konsisten.
- **Medium:** Spacing, alignment, typography, dan visual grouping kurang optimal.
- **Low:** Detail estetika yang tidak terlalu memengaruhi keterbacaan atau usability.

Utamakan perbaikan berdasarkan dampak terhadap pengguna, bukan berdasarkan kemudahan implementasi.

## 4. Plan — Menyusun UI Improvement Plan

Buat rencana perubahan yang konkret berdasarkan hasil analisis.

- Tentukan elemen visual yang akan diperbaiki.
- Jelaskan masalah existing dan solusi yang direkomendasikan.
- Tentukan perubahan typography, spacing, color, layout, dan component jika diperlukan.
- Identifikasi reusable component yang perlu diperbaiki.
- Identifikasi design token yang perlu disesuaikan.
- Tentukan apakah perubahan berlaku lokal atau berdampak ke seluruh aplikasi.
- Identifikasi potensi regression terhadap halaman lain.
- Prioritaskan perubahan dengan impact tertinggi dan risiko terendah.
- Hindari redesign keseluruhan jika perbaikan lokal sudah mencukupi.

Setiap perubahan harus memiliki alasan yang jelas.

Jangan menggunakan rekomendasi abstrak seperti:
- Make it cleaner.
- Improve the design.
- Make it modern.
- Make it more beautiful.

Gunakan rekomendasi konkret seperti:

- Kurangi visual prominence pada metadata agar informasi utama lebih mudah ditemukan.
- Tingkatkan kontras label sekunder agar tetap terbaca.
- Gunakan alignment numerik yang konsisten pada kolom quantity.
- Kurangi nested card untuk menghilangkan visual noise.
- Perbaiki spacing antar section agar grouping informasi lebih jelas.

Bila memungkinkan, sebutkan nilai konkretnya juga (mis. `text-xs` → `text-sm`, `gap-2` → `gap-4`, `text-muted-foreground` untuk metadata) supaya rencana bisa diverifikasi.

## 5. Validate — Strategi Validasi UI

Tentukan bagaimana hasil perbaikan akan dievaluasi.

### A. Visual Validation

- Bandingkan tampilan sebelum dan sesudah perubahan.
- Periksa apakah informasi utama lebih mudah ditemukan.
- Pastikan typography dan spacing konsisten.
- Pastikan tidak ada elemen yang terpotong atau bertumpuk.
- Periksa alignment dan proporsi komponen.
- Periksa konsistensi dengan design system existing.

### B. Functional Validation

Perbaikan UI tidak boleh merusak fungsi existing.

- Pastikan seluruh button tetap bekerja.
- Pastikan form dan validation tetap berfungsi.
- Pastikan modal, dropdown, dan navigation tetap berjalan.
- Pastikan tabel, filtering, sorting, dan pagination tidak berubah perilakunya.
- Pastikan loading, error, empty, dan success states tetap berfungsi.
- Pastikan event handler dan state management tidak terganggu.

### C. Responsive Validation

- Periksa viewport desktop.
- Periksa viewport tablet jika relevan.
- Periksa viewport mobile jika relevan.
- Pastikan tidak ada horizontal overflow yang tidak diharapkan.
- Pastikan informasi tetap terbaca pada layar yang lebih kecil.

### D. Regression Validation

- Identifikasi halaman lain yang menggunakan shared components terdampak.
- Periksa perubahan global pada CSS atau design tokens.
- Pastikan perubahan tidak merusak tampilan halaman lain.
- Jalankan test, typecheck, lint, dan build yang relevan jika tersedia.

Setiap perubahan harus memiliki acceptance criteria yang dapat diverifikasi.

## 6. Report — Hasil UI Improvement Review

Sampaikan hasil analisis menggunakan struktur berikut:

### A. Task Understanding

Ringkasan halaman, komponen, dan tujuan perbaikan.

### B. Existing UI Findings

Daftar masalah yang ditemukan pada implementasi aktual.

Sertakan:
- Elemen yang bermasalah (dengan rujukan `path:baris` bila ada).
- Kondisi visual saat ini.
- Dampak terhadap keterbacaan atau usability.
- Prioritas masalah.
- Sumber bukti: rendering aktual/screenshot, atau hanya source code.

### C. Proposed Visual Improvements

Jelaskan rekomendasi perbaikan secara konkret.

Kelompokkan berdasarkan:
- Typography & Readability.
- Color & Contrast.
- Spacing & Alignment.
- Layout & Information Hierarchy.
- Component Consistency.
- Responsive & Accessibility.

Tidak semua kategori harus memiliki perubahan.

### D. Impact Analysis

Jelaskan:
- Komponen yang terdampak.
- Shared component yang digunakan.
- Dampak terhadap halaman lain.
- Potensi functional regression.
- Risiko perubahan design tokens atau styling global.

### E. Implementation Plan

Susun tahapan perubahan secara berurutan.

Sebutkan file atau komponen yang akan diubah jika sudah diketahui.

Jelaskan tujuan dan hasil yang diharapkan dari setiap tahapan.

### F. Validation Strategy

Jelaskan bagaimana perubahan akan diuji dan dibandingkan.

Sertakan acceptance criteria yang objektif.

### G. Open Questions

Informasi atau keputusan yang masih membutuhkan klarifikasi user.

Jika tidak ada, tuliskan "Tidak ada".

### H. Execution Readiness

Berikan kesimpulan:
- Ready for Implementation.
- Requires Clarification.

## 7. Execution Gate — Persetujuan Sebelum Implementasi

Setelah seluruh tahapan analisis selesai:

- Jangan mengubah, membuat, atau menghapus file.
- Jangan mengubah CSS, styling, design tokens, atau komponen.
- Jangan mengubah business logic, API, database, atau konfigurasi.
- Jangan menginstal dependency.
- Jangan melakukan commit, push, atau deployment.
- Jangan menganggap rekomendasi sebagai persetujuan implementasi.

Aktivitas read-only diperbolehkan, termasuk:
- Membaca source code.
- Menjalankan aplikasi dalam mode development tanpa mengubah project state.
- Mengambil screenshot (simpan di direktori sementara/scratchpad, bukan di dalam repo).
- Melakukan inspeksi visual.
- Menjalankan analisis statis.

**Berhenti setelah menyampaikan UI Improvement Review.**

Tunggu persetujuan eksplisit user sebelum memulai implementasi.

Jika user memberikan revisi terhadap pendekatan atau scope:
- Perbarui analisis.
- Sesuaikan implementation plan.
- Evaluasi kembali dampaknya.
- Minta persetujuan ulang.

Setelah persetujuan diberikan, implementasikan hanya perubahan yang telah disepakati. Jika user hanya menyetujui sebagian (mis. "kerjakan yang Critical dan High saja"), batasi implementasi pada bagian itu.

Selama implementasi:
- Pertahankan business logic dan perilaku existing.
- Gunakan design system dan reusable components yang tersedia.
- Hindari refactoring yang tidak berkaitan dengan UI improvement.
- Jangan menambahkan dekorasi yang tidak meningkatkan kejelasan.
- Validasi hasil melalui rendering aktual jika memungkinkan.
- Bandingkan hasil sebelum dan sesudah.
- Laporkan perubahan, hasil validasi, dan keterbatasan yang ditemukan.

---

## Prinsip Utama

1. **Clarity over Decoration** — Kejelasan informasi lebih penting daripada estetika dekoratif.
2. **Readability First** — Informasi harus mudah dilihat, dibaca, dan dipahami.
3. **Hierarchy Matters** — Pengguna harus dapat mengenali prioritas informasi dengan cepat.
4. **Consistency over Creativity** — Ikuti design system sebelum menciptakan pola visual baru.
5. **Less Visual Noise** — Hilangkan elemen yang tidak memberikan nilai informasi.
6. **Existing Implementation Takes Precedence** — Pahami sistem sebelum mengusulkan perubahan.
7. **Minimal Changes, Maximum Impact** — Utamakan perubahan kecil dengan dampak visual besar.
8. **Preserve Functionality** — Perbaikan visual tidak boleh merusak perilaku aplikasi.
9. **Evidence-Based Improvements** — Setiap rekomendasi harus berdasarkan masalah yang benar-benar ditemukan.
10. **Understand First, Execute Later** — Persetujuan user wajib diperoleh sebelum implementasi.

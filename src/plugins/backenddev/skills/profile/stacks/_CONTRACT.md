# Kontrak Berkas Adapter Stack — `backenddev`

Rumah tunggal aturan penulisan `stacks/<stack-id>.md`. Setiap adapter **wajib** memuat tujuh seksi di
bawah ini, dengan judul persis seperti tertulis, berurutan, tanpa seksi tambahan. Skill di
`skills/` tidak boleh menyalin isi adapter; ia merujuknya lewat path relatif `../profile/stacks/<stack-id>.md`
(atau `stacks/<stack-id>.md` dari sisi skill `profile`) yang dibaca di Fase 0 masing-masing.

`<stack-id>` sah: `java-spring`, `go`, `node`, `bun`, `rust`, `php`, `php-codeigniter`. Nilai ini identik
dengan field `stack` pada `.claude/profile/backenddev/index.json` yang ditulis `backenddev:profile`.

## Aturan penulisan

1. **Bukti, bukan anjuran.** Tiap butir checklist menjelaskan *apa yang salah* dan *akibat runtime-nya*,
   bukan gaya penulisan yang disukai. Butir tanpa akibat konkret dihapus, bukan dilunakkan.
2. **Idiom asli stack.** Dilarang menerjemahkan istilah satu stack ke istilah stack lain
   (contoh: menyebut `Repository` di adapter Go hanya karena Spring memakainya). Pakai nama yang
   benar-benar dipakai komunitas stack itu.
3. **Ambang minimal kedalaman.** `## Audit checklist` wajib memuat **≥12 butir** yang terdistribusi ke
   **≥4 dimensi** dari enam yang ada. Adapter di bawah ambang ini tidak boleh dirilis: ia tidak
   menambah nilai apa pun di atas `quickdev`.
4. **Batas ukuran.** Satu adapter ditargetkan 8.000–16.000 karakter; adapter yang memuat dua gaya
   arsitektur (`layered` dan `hexagonal`) ditargetkan 8.000–20.000 karena ia menanggung satu tabel
   layer, satu set jebakan, dan butir arah dependensi tambahan. Adapter di root plugin tidak
   dihitung sebagai berkas pendukung skill mana pun, jadi tidak membebani kuota tier — tetapi hanya
   satu adapter dimuat per sesi, jadi ukurannya tetap biaya context nyata. Adapter yang menembus
   batas atas wajib dipangkas dari butir yang paling jarang terbukti, bukan dari seksi yang hilang.
5. **Nol duplikasi lintas-adapter.** Butir yang berlaku di semua stack adalah tanda butir itu salah
   tempat; ia milik `SKILL.md`, bukan adapter.

## Enam dimensi audit (netral stack)

| Dimensi | Cakupan |
|---|---|
| `security` | Otorisasi, kepemilikan data, kebocoran kredensial, mass assignment, injeksi |
| `transaction` | Batas transaksi, atomisitas, rollback, commit tak sengaja |
| `data` | Validasi, konsistensi, integritas nilai, penegakan aturan di semua jalur tulis |
| `persistence` | Akses penyimpanan, N+1, pagination, kebocoran koneksi/cursor, pemetaan tipe |
| `concurrency` | Paralelisme, race, deadlock, tugas latar, antrean, penjadwal |
| `architecture` | Batas layer, arah dependensi, penempatan logika, state bersama |

Urutan prioritas saat satu kandidat cocok di lebih dari satu checklist:
`security` → `transaction` → `data` → `persistence` → `concurrency` → `architecture`.
Kandidat semacam itu dicatat sebagai **satu** temuan dengan dampak terburuk.

---

## Tujuh seksi wajib

### 1. `## Detection` — konsumen: `backenddev:profile`

Berkas manifest yang menandai stack, dependensi penanda framework, dan aturan pemutus saat lebih dari
satu penanda hadir. Wajib memuat perintah konkret yang membuktikan penanda itu ada di repo, bukan
sekadar daftar nama berkas.

**Penanda gaya arsitektur.** Bila stack lazim ditulis dalam lebih dari satu gaya organisasi kode —
`layered` (handler → service → repository) versus `hexagonal` (ports & adapters / clean architecture,
inti domain bebas infrastruktur) — adapter wajib memuat penanda pembeda keduanya beserta perintah
pembuktiannya. Hasil pembacaan ini mengisi field `architecture` pada
`.claude/profile/backenddev/index.json`; nilai sah `layered`, `hexagonal`, `hybrid`, atau `tidak terdeteksi`.
Gaya arsitektur **bukan** stack: satu `<stack-id>` boleh melayani lebih dari satu gaya.

### 2. `## Commands` — konsumen: `backenddev:profile`, `backenddev:architect`

Enam baris perintah: `build`, `test`, `test-single`, `lint`, `typecheck`, `migration`. Tulis
`tidak berlaku` bila stack tidak punya padanannya — dilarang mengarang perintah. `profile`
mengeksekusi tiap perintah minimal sekali sebelum menuliskannya ke profil; `architect` memakainya di
gerbang verifikasi penutup taskdir.

### 3. `## Layer taxonomy` — konsumen: `agents/code-implementor.md` (lewat slot `{adapter_path}`), `backenddev:plan`, `backenddev:audit`

`code-implementor` tidak pernah menyusun path adapter sendiri: `backenddev:architect` menghidrasi slot
`{adapter_path}` di `skills/architect/dispatcher/implementor.md` dengan
`${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`, dan subagent berhenti `BLOCKED` bila slot itu
absen. Direktori `.claude/profile/backenddev/stacks/` tidak pernah ditulis `backenddev:profile` dan dilarang dirujuk.

Urutan layer eksekusi kode (dipakai `code-implementor` untuk mengurutkan pekerjaan dalam satu brief),
konvensi penamaan berkas, dan letak direktori tiap layer. Sertakan jebakan spesifik stack yang muncul
saat menulis kode di layer itu.

**Satu sub-bagian per gaya arsitektur.** Bila `## Detection` mendeklarasikan penanda `hexagonal`,
seksi ini wajib memuat sub-bagian terpisah untuk tiap gaya — masing-masing dengan urutan layer,
penamaan, letak direktori, dan **aturan arah dependensi** gaya itu. Konsumen (`code-implementor`,
`plan`, `audit`) memilih sub-bagian berdasarkan field `architecture:` profil; jika field itu
`hybrid` atau `tidak terdeteksi`, yang menang adalah struktur nyata modul yang sedang disentuh,
dibuktikan `file:line`, bukan sub-bagian yang lebih dulu tertulis.

### 4. `## Navigation recipes` — konsumen: `backenddev:profile`, `backenddev:audit`

Tabel dua kolom: jenis target pencarian → resep `Glob`/`Grep` konkret. Minimal empat baris: deklarasi
tipe, titik masuk HTTP, rantai pemanggil lintas layer, dan akses penyimpanan.

`backenddev:profile` memakai resep ini di `references/scan-guide.md` titik 9 dan 14 untuk menurunkan
`invariants.md` dan `surface-map.md`; `backenddev:audit` memakainya di Fase 1 untuk menyusun peta
cakupan. `code-explorer` **bukan** konsumen langsung: ia dilarang membaca berkas adapter dan
membaca hasil turunannya di `.claude/profile/backenddev/` saja. Resep di seksi ini tetap sampai kepadanya
lewat satu jalur: `system-analysis` dan `plan` menyalinnya apa adanya ke slot `{resep_navigasi}`
prompt `dispatcher/explorer.md` masing-masing, seperti `{daftar_dimensi}` Profil B. Resep yang
hanya dirujuk path-nya tidak pernah dijalankan, dan jalur async tanpa resep tidak tersapu siapa pun.

### 5. `## Audit checklist` — konsumen: `backenddev:audit`, subagent `code-reviewer`

Butir dikelompokkan per dimensi dengan sub-heading `#### <dimensi>`. Hanya dimensi yang punya butir
nyata yang ditulis. Berlaku ambang ≥12 butir / ≥4 dimensi dari aturan penulisan di atas.

### 6. `## API surface` — konsumen: `backenddev:document-api`

Cara endpoint dideklarasikan di stack ini, cara menurunkan method + path + status code + bentuk
request/response dari kode, dan letak deklarasi otorisasi per endpoint.

### 7. `## Failure signatures` — konsumen: `backenddev:debug`

Bentuk error runtime yang khas (format stacktrace, tipe error, kode exit), cara membaca frame paling
informatif darinya, dan pola akar masalah yang paling lazim di stack ini.

---

## Gerbang kelayakan adapter

Adapter baru boleh dipakai hanya bila seluruhnya benar:

1. Tujuh seksi hadir, judul persis, berurutan, tanpa seksi tambahan.
2. `## Audit checklist` memenuhi ambang ≥12 butir / ≥4 dimensi.
3. Seluruh perintah di `## Commands` sudah dieksekusi minimal sekali di repo nyata stack itu.
4. Tidak ada butir yang identik dengan butir di adapter lain.
5. `<stack-id>` terdaftar di `## Detection` milik `backenddev:profile`.
6. Jika adapter mendeklarasikan penanda `hexagonal`: `## Layer taxonomy` memuat sub-bagian per
   gaya, dan `## Audit checklist` memuat minimal tiga butir arah dependensi yang hanya berlaku pada
   gaya itu — ditandai eksplisit agar tidak dipakai menghakimi repo `layered`.

Butuh seksi kedelapan = kontrak ini yang salah. Revisi berkas ini lebih dulu dan sesuaikan seluruh
adapter yang sudah ada; dilarang menambah seksi lokal di satu adapter saja.

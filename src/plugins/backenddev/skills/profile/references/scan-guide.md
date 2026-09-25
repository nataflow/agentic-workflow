# Scan Guide — `profile`

Titik pemindaian **1–14** untuk mengisi `.claude/profile/backenddev/`; titik 15–17 ada di `convention-scan.md`. Jalankan setiap item, simpan bukti sebagai anchor `<file>#<simbol>` — bukan nomor baris — dan catat `tidak terdeteksi` bila fakta tidak ada di kode aktual.

**Anchor dicatat sejak dipindai.** Bentuk lengkapnya ada di `../templates/profile-template.md` § Tata cara anchor bukti. Catat simbolnya saat berkasnya dibuka; nomor baris yang terlanjur dicatat di fase pemindaian tidak bisa dipulihkan lagi jadi simbol saat profil ditulis.

**Sumber pola spesifik stack.** Panduan ini menetapkan *apa* yang dicari; *bagaimana* mencarinya dibaca dari `../stacks/<stack-id>.md` — seksi adapter yang dipakai disebut di tiap titik. Dilarang memakai pola stack lain sebagai pengganti.

**Prinsip statis & blueprint.** Hanya catat fakta statis dan tahan lama; jangan simpan hal fast-change seperti high-water mark migrasi atau output spesifik.

---

## 1. Manifest → `index.json` (`project`), `stack.md`

Adapter: `## Detection`.

- **Nama Project**: Field nama pada manifest utama. Fallback: nama direktori root repo.
- **Versi Framework** dan **Versi Bahasa/Runtime**: Dari manifest dan berkas penyetel versi runtime (`.nvmrc`, `go` directive, `rust-toolchain.toml`, `<java.version>`, `platform.php`).
- **Package Manager Aktif**: Ditentukan lockfile yang benar-benar ada (`pom.xml`, `go.sum`, `package-lock.json`, `pnpm-lock.yaml`, `bun.lockb`, `Cargo.lock`, `composer.lock`). Bila lebih dari satu hadir, catat keduanya.
- **Dependensi Penanda Utama**: Kelompokkan ke DB/migration, messaging, cache, security & web, codegen, batch & scheduling. Daftar paket per kelompok ada di `## Detection` adapter.

---

## 2. Entrypoint & Source Root → `index.json` (`root_namespace`, `source_root`)

Adapter: `## Detection`, `## Layer taxonomy`.

Cari berkas titik masuk proses menurut resep adapter.

- **Tepat 1 Hit**: Namespace/module/package berkas itu = `root_namespace`; direktori akar kodenya relatif ke root repo = `source_root`.
- **Multi-Module / Monorepo**: Periksa submodule yang memuat entrypoint utama; submodule itu jadi acuan `source_root` dan `root_namespace`. Daftarkan submodule lain di `module-structure.md`.

---

## 3. Module Structure → `module-structure.md`, `index.json` (`architecture`)

Eksekusi `find <source_root> -maxdepth 3 -type d`, lalu bandingkan dengan pola modularisasi:

- **Bergrup Domain**: `<modul>/<domain>/<subdomain>/...`
- **Flat Feature**: satu tingkat fitur langsung di bawah `source_root`.
- **Shared Modules**: Catat folder utilitas bersama (`common/`, `shared/`, `core/`, `internal/`, `libraries/`, `pkg/`) sebagai rujukan implementor sebelum membuat util baru.

### 3.1 Gaya arsitektur → `index.json` (`architecture`), `module-structure.md`

Adapter: `## Detection` sub-bagian **Penanda gaya arsitektur**.

Gaya arsitektur ditentukan bukti konkret, bukan nama folder. Jalankan ketiga langkah adapter berurutan dan catat anchor tiap penanda — simbol pemikul faktanya bila ada, `<file>` telanjang bila penandanya tingkat-berkas seperti impor:

1. **Penanda direktori** — `core/`, `domain/`, `application/`, `usecase/`, `ports/`, `adapters/`, `infrastructure/`, pasangan `inbound`/`outbound` atau `driving`/`driven` → kandidat `hexagonal`. Trio berkas layer berdampingan dalam satu folder domain → kandidat `layered`.
2. **Letak kontrak** — apakah interface/trait penyimpanan dideklarasikan di paket inti (konsumen) atau bersama implementasinya.
3. **Kebersihan inti** — apakah paket/crate inti mengimpor driver DB, framework HTTP, atau klien HTTP. Perintah konkretnya ada di adapter.

Aturan penetapan nilai:

- Nol impor infrastruktur di inti **dan** kontrak dideklarasikan di inti → `hexagonal`.
- Inti mengimpor driver atau framework → `layered`, walau nama foldernya `domain/`. Langkah 3 mengalahkan langkah 1; folder bernama hexagonal tanpa isolasi nyata adalah `layered` berkostum.
- Sebagian modul bersih, sebagian tidak → `hybrid`. Wajib sebutkan modul mana yang mana di `module-structure.md`.
- Dua gaya bertabrakan tanpa kesengajaan arsitektural → kumpulkan bukti kedua gaya sebagai bahan wawancara Fase 3.
- Bukti bertentangan dan tidak terurai → `tidak terdeteksi`.

---

## 4. Module Anatomy → `module-structure.md`

Adapter: `## Layer taxonomy`, sub-bagian sesuai `architecture` hasil titik 3.1.

Pilih satu domain representatif, verifikasi konvensi layer yang diklaim adapter benar-benar dipakai:

- **Komponen Layer**: Penamaan berkas tiap layer menurut taksonomi adapter.
- **Tipe Data Batas**: Letak tipe request/response dan mekanisme pemetaannya ke tipe domain.
- **Tipe Persistensi**: Letak definisi tabel/dokumen dan konvensi penamaannya.

Bila kode nyata menyimpang dari taksonomi adapter, yang ditulis adalah **kode nyata**; catat penyimpangannya sebagai temuan.

---

## 5. Configuration → `stack.md`, `invariants.md`

Adapter: `## Detection`.

Baca berkas konfigurasi per environment menurut letak yang disebut adapter:

- Setelan yang **mengubah semantik runtime**, bukan sekadar nilai koneksi — mode sinkronisasi skema, strategi pemuatan relasi, mode serialisasi, batas pool.
- **Environment Flags**: Pola variabel env yang menggerbang consumer/scheduler/fitur (misal `ENABLE_CONSUMER`, `FEATURE_X_ENABLED`); catat nama persisnya ke `invariants.md`.

---

## 6. Database Migration → `commands.md`, `invariants.md`

Pindai folder migrasi menurut letak dan format yang disebut adapter:

- Catat nama tool migrasi, lokasi folder migrasi, dan format pola penamaan file migrasi (misal `{n}_{deskripsi}.up.sql` atau `V{version}__{description}.sql`).
- Catat berkas master/changelog bila tool migrasinya memakainya.
- **Larangan data dinamis:** dilarang mencatat *high-water mark* atau versi migrasi terakhir; cukup blueprint lokasi dan pola berkas migrasi.

---

## 7. Build and Test Commands → `commands.md`

Adapter: `## Commands`.

Ambil enam perintah dari adapter, lalu sesuaikan ke skrip nyata repo — `Makefile`, `Justfile`, `scripts` pada manifest, `CLAUDE.md`. Skrip repo menang atas perintah generik adapter.

Enam perintah dieksekusi: `build`, `typecheck`, `lint`, `test`, `test-single`, `migration`. Perintah yang tidak punya padanan di stack ini ditulis `tidak berlaku`. Seluruhnya dijalankan di Fase 4 `SKILL.md` sebelum ditulis ke profil.

Dua baris tambahan **disalin dari adapter tanpa dieksekusi**, karena keduanya menjawab "bagaimana perintahnya dipakai", bukan "apakah perintahnya jalan":

- `typecheck-scoped` — varian berplaceholder target (`cargo check -p <crate>`, `go build ./<paket>/...`, `./mvnw -pl <module> -am compile`). Dipakai `architect` untuk mempersempit gerbang kompilasi per brief ke modul yang disentuh. Adapter menulis `tidak berlaku` bila toolchain-nya menilai seluruh program sekaligus.
- `typecheck-per-brief` — `ya` atau `tidak` beserta alasannya, disalin apa adanya dari adapter. Ia menentukan apakah `architect` menjalankan gerbang kompilasi sesudah tiap brief atau menundanya ke penutup taskdir. Nilainya milik stack, bukan penilaian per repo: toolchain yang kompilasinya inkremental menanggungnya nyaris gratis, sementara yang kompilasinya build penuh membayar mahal tiap brief.

---

## 8. Boundary Scoping & Context → `invariants.md`

Adapter: `## Audit checklist` dimensi `security`.

Pindai mekanisme penyimpanan konteks per-request atau per-tenant yang dipakai repo. Bila ditemukan penyaring tenant/store/user → catat nama simbol dan path persisnya sebagai invariant ("scoping lewat X — jangan di-bypass").

---

## 9. Mirrored Runtime Paths → `invariants.md`

Adapter: `## Navigation recipes`.

Pindai domain yang diproses lebih dari satu jalur runtime: HTTP, consumer antrean, scheduler, worker latar, WebSocket. Bila satu state diperbarui lewat lebih dari satu jalur → catat invariant: "perubahan pada X harus dicerminkan konsisten di jalur HTTP, Queue, dan Scheduler".

---

## 10. Commit Message Convention → `index.json` (`commit_convention`)

Pindai `git log -n 20 --oneline`.

- Ambil pola subjek: prefix Conventional Commits (`feat(order): ...`), prefix tiket (`OMS-123: ...`), kapitalisasi, dan bahasa.
- Tulis ringkasan pola satu baris sebagai acuan architect.

---

## 11. Root Instruction Files → `invariants.md`

Periksa `CLAUDE.md` atau `AGENTS.md` di root repo bila ada. Ekstraksi **hanya** aturan keras dan invariant mutlak, bukan preferensi gaya.

---

## 12. Runtime Timezone → `invariants.md`

Adapter: `## Detection`.

Fakta tingkat-invariant penentu kebenaran kalkulasi waktu. Empat lokasi penanda wajib dipindai: zona default di kode inisialisasi proses · zona pada lapisan serialisasi · variabel lingkungan proses (`TZ` dan padanannya) · berkas build, `Dockerfile`, atau skrip startup.

- Jika ditemukan penanda — format baris:
  `- <penanda>(UTC) di <file#kunci> → seluruh waktu lahir dalam UTC; konversi lokal wajib eksplisit`
- Jika nihil (bentuk dikunci):
  `- Zona waktu runtime: tidak ada penanda di repo (dicari: 4 lokasi penanda standar). Proses memakai zona host; zona container/orkestrator di luar jangkauan profile ini`

---

## 13. Branch Configuration → `index.json` (`base_branch`, `branch_convention`)

Pindai `git branch --show-current`, `git branch -r`, `git log --merges -n 20`:

- `base_branch`: Branch basis kerja dan titik pembanding review.
- `branch_convention`: Pola penamaan branch memuat placeholder `<slug>`.

---

## 14. Surface Map → `surface-map.md`

Adapter: `## Navigation recipes`, `## API surface`.

Indeks ringkas letak komponen runtime aktif, maksimal 15 baris. Format:
`<permukaan>: <path/glob> · <penanda pengenal> · <catatan satu frasa>`

Dua belas permukaan kanonik yang diperiksa:
`http` · `transaksi` · `persistence` · `migration` · `messaging` · `scheduler` · `cache` · `security` · `websocket` · `error` · `external` · `config`

*Aturan Surface Map:* Permukaan yang tidak ada di repo **dihapus barisnya**, jangan ditulis `tidak terdeteksi`. Dilarang mencatat daftar endpoint konkret individual (ini tanggung jawab `document-api`).

---

## Closing Rules

- **Baris Invariant Zona Waktu**: Wajib selalu ada di `invariants.md` walau hasil scan nihil.
- **Kode Nyata Menang**: Setiap kali adapter dan kode nyata berbeda, yang ditulis ke profil adalah kode nyata, dan selisihnya dilaporkan sebagai temuan di Fase 7.
- **Inkonsistensi Ditanyakan**: Bila pemindaian menemukan benturan pola arsitektur atau konvensi, bawa ke wawancara Fase 3 untuk keputusan user.

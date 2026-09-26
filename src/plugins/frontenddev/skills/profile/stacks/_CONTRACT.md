# Kontrak Berkas Adapter Stack — `frontenddev`

Rumah tunggal aturan penulisan `stacks/<stack-id>.md`. Setiap adapter **wajib** memuat tujuh seksi di
bawah ini, dengan judul persis seperti tertulis, berurutan, tanpa seksi tambahan. Skill di
`skills/` tidak boleh menyalin isi adapter; ia merujuknya lewat path
`skills/profile/stacks/<stack-id>.md` relatif root plugin (skill menerimanya sebagai path absolut dari peta
**Skrip:** SKILL.md-nya; `stacks/<stack-id>.md` dari sisi skill `profile`) yang dibaca di Phase 0 masing-masing.

`<stack-id>` sah: `react-vite`, `react-native`, `sveltekit`, `svelte-vite`. Nilai ini identik dengan
field `stack` pada `.claude/profile/frontenddev/index.json` yang ditulis
`frontenddev:profile`. Next.js **tidak** termasuk: manifest yang memuat `next` ditolak di
`## Detection` semua adapter dan di `hooks/detect.py`.

## Aturan penulisan

1. **Bukti, bukan anjuran.** Tiap butir checklist menjelaskan *apa yang salah* dan *akibat runtime
   atau akibat verifikasinya*, bukan gaya penulisan yang disukai. Butir tanpa akibat konkret dihapus,
   bukan dilunakkan.
2. **Idiom asli stack.** Dilarang menerjemahkan istilah satu stack ke istilah stack lain (contoh:
   menyebut `hook` di adapter Svelte hanya karena React memakainya; di Svelte namanya rune, store,
   atau modul `.svelte.ts`). Pakai nama yang benar-benar dipakai komunitas stack itu.
3. **Ambang minimal kedalaman.** `## Review checklist` wajib memuat **≥12 butir** yang terdistribusi ke
   **≥5 dimensi** dari sembilan yang ada. Adapter di bawah ambang ini tidak boleh dirilis.
4. **Batas ukuran.** Satu adapter ditargetkan 7.000–14.000 karakter. Hanya satu adapter dimuat per
   sesi, jadi ukurannya tetap biaya context nyata. Adapter yang menembus batas atas wajib dipangkas
   dari butir yang paling jarang terbukti, bukan dari seksi yang hilang.
5. **Nol duplikasi lintas-adapter.** Butir yang berlaku di semua stack adalah tanda butir itu salah
   tempat; ia milik `SKILL.md` atau `references/` skill (predikat review: katalog netral), bukan
   adapter. Pengecualian sempit: gerbang kelayakan butir 4.

## Enam layer kanonik (netral stack)

Seluruh skill memakai nama layer generik ini; adapter yang menerjemahkannya ke idiom stack:

| Layer | Tanggung jawab tunggal |
|---|---|
| `DTO` | Kontrak payload backend murni; tidak pernah dikonsumsi presentasi |
| `Service` | Transport HTTP murni lewat client bersama repo |
| `API layer` | Cache, fetch trigger, invalidasi; nol side-effect UI |
| `View-Model` | Transformasi DTO → props UI murni, ekspor tipe `*UI` |
| `Controller` | Orkestrasi state, form, handler, navigasi, notifikasi |
| `Presentation` | Render visual murni dari Controller |

Urutan eksekusi kode dalam satu brief selalu DTO → Service → API layer → View-Model → Controller →
Presentation; adapter tidak mengubah urutannya, hanya menamai berkas dan idiomnya.

## Sembilan dimensi review (netral stack)

Sumber tunggal nama dimensi. Adapter memakai kolom **Slug** sebagai `#### <slug>`; template REVIEW/AUDIT, `agents/code-reviewer.md`, katalog, dan SKILL memakai kolom **Nama** persis.

| # | Slug | Nama | Cakupan |
|---|---|---|---|
| 1 | `layer-boundaries` | Layer Boundaries | DTO terisolasi dari presentasi, Controller dipanggil dari presentasi, Service murni |
| 2 | `data-flow` | Data Flow & DTO | Nol `any`, View-Model memetakan seluruh field DTO ke `*UI` |
| 3 | `api-layer` | API Layer | Nol navigasi/toast di API layer, query key array factory |
| 4 | `state-scope` | State Scope & Ownership | State query di Controller, tidak ada fetch tersembunyi di komponen anak |
| 5 | `ui-states` | UI & 6-State Branches | 6 cabang state per layar: normal, loading, kosong, error (+retry), initial, stale/mutating |
| 6 | `platform` | Platform & Framework Boundary | Batas framework & platform: safe area, touch target, server/client boundary |
| 7 | `error-handling` | Error Handling | Error backend dipetakan ke pesan manusiawi, retry aktif |
| 8 | `performance` | Performance & Leaks | Cleanup efek/subscription, memoisasi kalkulasi berat |
| 9 | `tests` | Test Quality | Test View-Model/Service punya assertion nyata, tidak di-skip |

---

## Tujuh seksi wajib

### 1. `## Detection` — konsumen: `frontenddev:profile`, `hooks/detect.py`

Berkas manifest yang menandai stack, dependensi penanda framework, penanda pengecualian (`next`),
dan aturan pemutus saat lebih dari satu penanda hadir. Wajib memuat perintah konkret yang membuktikan
penanda itu ada di repo, bukan sekadar daftar nama berkas. Sertakan penanda kelompok: router,
state global, query/cache, styling, form & validasi, storage, test runner, bundler/config.

### 2. `## Commands` — konsumen: `frontenddev:profile`, `frontenddev:review`, `frontenddev:plan`

Lima baris perintah: `typecheck`, `lint`, `test`, `test-single`, `build`. Tulis `tidak berlaku`
bila stack tidak punya padanannya — dilarang mengarang perintah. `profile` mengeksekusi tiap
perintah minimal sekali sebelum menuliskannya ke `commands.md` profil; `plan` menjalankannya
sekali sebagai Check 3; `architect` menjalankannya di verifikasi penutup taskdir (Phase 4). Seksi ini wajib
ditutup sub-bagian **Cakupan yang TIDAK diperiksa** per perintah — kolom itu yang mencegah `test`
hijau dibaca sebagai bukti typecheck hijau.

Ditambah satu baris keputusan, bukan perintah:

| Baris | Nilai | Konsumen |
|---|---|---|
| `typecheck-per-brief` | `ya \| tidak — <alasan>` | `frontenddev:architect` Phase 0 (lewat `Terselesaikan:` prasyarat; gerbang kompilasi per-brief di Phase 2) |

`ya` berarti perintah `typecheck` cukup murah untuk dijalankan sekali per unit **di main loop**,
sesudah commit unit itu, dengan vonis **relatif baseline**: yang ditagih adalah nol galat *baru*,
bukan hijau absolut. `tidak` berarti biayanya sepadan dengan menunda seluruh pembuktian ke penutup.
Baris ini tidak mengubah IRON LAW `code-implementor` — subagent tetap nol terminal — dan tidak
menyentuh lint, test, maupun build, yang selamanya milik verifikasi penutup. `profile` boleh
menurunkan nilainya ke `tidak` bila durasi terukur di repo itu ternyata mahal (atau menaikkannya ke
`ya` bila murah), dan mencatat durasinya sebagai alasan; nilai di `commands.md` profil menang atas
adapter.

### 3. `## Layer taxonomy` — konsumen: `agents/code-implementor.md` (lewat slot `{adapter_path}`), `frontenddev:contract`, `frontenddev:plan`

`code-implementor` tidak pernah menyusun path adapter sendiri: `frontenddev:architect` menghidrasi slot
`{adapter_path}` di `skills/architect/dispatcher/implementor.md` dengan path absolut adapter hasil
substitusi di `architect/SKILL.md` Phase 2 butir 1, dan subagent berhenti `FAILED` bila slot
itu absen.

Penamaan berkas, letak direktori, ekspor utama, dan satu potongan kode singkat per layer kanonik,
ditambah **jebakan spesifik stack** yang muncul saat menulis kode di layer itu (cleanup efek,
reaktivitas, batas server/client, keyboard & safe area). Sertakan daftar hygiene penutup unit yang
dipakai `agents/code-implementor.md` Fase 1.

### 4. `## Navigation recipes` — konsumen: `frontenddev:profile`, `frontenddev:review`

Tabel dua kolom: jenis target pencarian → resep `Glob`/`Grep` konkret. Minimal delapan baris:
route/presentation, Controller, View-Model, API layer, cache & mutasi, Service transport, DTO,
kebocoran DTO ke presentasi, state global, form & skema, batas framework.

`frontenddev:profile` memakai resep ini untuk mengisi kolom **Penanda Pengenal Kode** di
`surface-map.md`; `code-explorer` **bukan** konsumen langsung: ia dilarang membaca berkas adapter
dan membaca hasil turunannya di profil saja.

### 5. `## Review checklist` — konsumen: `frontenddev:review`, `agents/code-reviewer.md` (review penutup `frontenddev:architect`)

Butir dikelompokkan per dimensi dengan sub-heading `#### <dimensi>`, tiap butir memuat predikat
pelanggaran, severity (`P1`/`P2`/`P3`), dan bila mungkin resep grep. Hanya dimensi yang punya butir
nyata yang ditulis. Berlaku ambang ≥12 butir / ≥5 dimensi dari aturan penulisan di atas.

### 6. `## UI & navigation surface` — konsumen: `frontenddev:ux-design`, `frontenddev:ui-design`

Konvensi routing (letak berkas rute, bentuk parameter dinamis, search params, deep-link), mekanisme
intersep kembali/batal dan dirty guard, API sinkronisasi state URL, batasan platform (breakpoint web
atau safe area/touch target/keyboard mobile), letak design token, dan atribut aksesibilitas yang
dipakai stack.

### 7. `## Failure signatures` — konsumen: `frontenddev:architect` (`references/execution-protocol.md` bagian 8), `agents/code-reviewer.md`, `frontenddev:review`

Kategori error verifikasi penutup yang khas stack ini (typecheck, lint, test, build), penyebab
umum, dan strategi resolusi yang sah. Tabel ini yang dipakai `plan` saat menyusun brief remedi.

---

## Gerbang kelayakan adapter

Adapter baru boleh dipakai hanya bila seluruhnya benar:

1. Tujuh seksi hadir, judul persis, berurutan, tanpa seksi tambahan.
2. `## Review checklist` memenuhi ambang ≥12 butir / ≥5 dimensi.
3. Seluruh perintah di `## Commands` sudah dieksekusi minimal sekali di repo nyata stack itu.
4. Tidak ada butir netral stack di adapter (predikat yang sudah ada di `skills/review/references/nine-dimensions-catalog.md`). Butir yang sama di dua adapter sefamili (Svelte, SPA Vite) sah hanya bila memakai idiom atau resep grep/glob yang spesifik keluarga itu.
5. `<stack-id>` terdaftar di `## Detection` milik `frontenddev:profile` dan di `hooks/detect.py`.

Butuh seksi kedelapan = kontrak ini yang salah. Revisi berkas ini lebih dulu dan sesuaikan seluruh
adapter yang sudah ada; dilarang menambah seksi lokal di satu adapter saja.

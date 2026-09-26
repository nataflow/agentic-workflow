# The 9-Dimension Architecture Review Catalog

Katalog standar review 9 dimensi arsitektur frontend dan rubrik klasifikasi keparahan P1–P3 untuk skill `frontenddev:review`. Katalog ini **netral stack**: ia menetapkan target periksa dan predikat pelanggaran tiap dimensi. Nama dan slug dimensi mengikuti tabel `## Sembilan dimensi review` di `skills/profile/stacks/_CONTRACT.md` (sumber tunggal). Predikat netral stack — beserta resep grep-nya bila seragam lintas stack — hanya hidup di sini; cuplikan kode benar vs salah, perintah grep idiomatik, dan severity per butir khas stack hidup di `## Review checklist` adapter `skills/profile/stacks/<stack-id>.md` (relatif root plugin); adapter menang bila keduanya menyebut butir yang sama.

---

## 1. Dimension 1: Layer Boundaries (`layer-boundaries`)

### Target Periksa:
Arsitektur 5-tier: memastikan pemisahan tegas layer: DTO -> Service -> API layer -> View-Model -> Controller -> Presentation.

### Predikat pelanggaran:
- **[P1]** Komponen presentasi mengimpor tipe dari `dto/` — perubahan skema backend merambat ke markup.
- **[P1]** Fetch/transport HTTP dipanggil langsung dari komponen presentasi.
- **[P2]** Logika query/state ditulis di berkas rute (`app/**`, `+page.svelte`, `Route`) alih-alih Controller.

Grep: pola "Kebocoran DTO ke presentasi" di `## Navigation recipes` adapter.

---

## 2. Dimension 2: Data Flow & DTO (`data-flow`)

### Target Periksa:
Typing dan integritas DTO: tidak ada penggunaan tipe `any`, payload backend terdefinisi lengkap, dan View-Model memetakan seluruh field data secara eksplisit ke `*UI`.

### Predikat pelanggaran:
- **[P1]** `: any` / `as any` di DTO, Service, API layer, atau View-Model.
- **[P2]** Field DTO (snake_case backend) dikonsumsi langsung di markup — View-Model dilewati.
- **[P2]** View-Model mengembalikan DTO utuh alih-alih `*UI` yang dipetakan.

Grep: `Grep -n ": any\|as any" <source_root dari structure.md profil>`

---

## 3. Dimension 3: API Layer (`api-layer`)

### Target Periksa:
Zero side effects: dilarang keras meletakkan side-effect (navigasi, toast, modal alert) di dalam query/mutation/`load`; API layer hanya mengelola transport dan cache invalidation.

### Predikat pelanggaran:
- **[P1]** Navigasi router atau toast di callback `onSuccess`/`onError` API layer.
- **[P2]** `queryKey` literal tanpa factory `*_KEYS`.
- **[P2]** Mutasi tanpa invalidasi (`invalidateQueries` di `onSettled`, atau `invalidate('app:<key>')` bila memakai `load`).

Grep: `Grep -n "queryKey: \['"`

---

## 4. Dimension 4: State Scope & Ownership (`state-scope`)

### Target Periksa:
State halaman dan data fetching dikoordinasikan secara sentral di Controller layar, bukan terisolasi di komponen anak.

### Predikat pelanggaran:
- **[P2]** Komponen kartu/baris anak memicu query mandiri per item.
- **[P2]** Store global memegang state form milik satu halaman.
- **[P3]** State lokal menduplikasi data yang sudah ada di cache query.

---

## 5. Dimension 5: UI & 6-State Branches (`ui-states`)

### Target Periksa:
Setiap layar mengimplementasikan seluruh 6 cabang state: normal, loading (skeleton berdimensi, CLS aman), kosong, error dengan retry, initial, dan stale/mutating.

### Predikat pelanggaran:
- **[P2]** Error state tanpa aksi retry yang memanggil `refetch`.
- **[P2]** Loading merender kosong alih-alih skeleton berdimensi.
- **[P2]** Daftar tanpa cabang empty (`ListEmptyComponent`, `{:else}`, fallback kosong).
- **[P3]** Refetch latar tanpa indikator mutating.

---

## 6. Dimension 6: Platform & Framework Boundary (`platform`)

### Target Periksa:
Semantik batas framework dan platform yang dinyatakan `## Layer taxonomy` adapter dipatuhi — safe area, touch target ≥44 dp, hardware back (React Native); server/client boundary dan `browser` guard (SvelteKit); env `VITE_*` dan alias sinkron (SPA Vite).

### Predikat pelanggaran:
- Severity dan butir konkret **sepenuhnya milik adapter** (`#### platform`); dimensi ini `UNVERIFIED` bila adapter tidak ada.

---

## 7. Dimension 7: Error Handling (`error-handling`)

### Target Periksa:
Model error dan boundary: respon error dari backend (400, 401, 404, 500) dipetakan ke pesan validasi formulir atau banner semantik manusiawi.

### Predikat pelanggaran:
- **[P2]** `error.message` mentah ditampilkan ke pengguna.
- **[P3]** Error boundary rute absen di segmen yang memuat fetch berpotensi gagal.

---

## 8. Dimension 8: Performance & Leaks (`performance`)

### Target Periksa:
Memory leak dan cleanup: pembersihan timer/event listener/subscription pada efek (React `useEffect` return; Svelte `$effect` return / `onDestroy`; RN listener `remove()`), dan memoisasi/derivasi untuk kalkulasi berat.

### Predikat pelanggaran:
- **[P2]** Efek bersubscription tanpa cleanup.
- **[P3]** Kalkulasi list berat di badan komponen/template tanpa memo/derived.

---

## 9. Dimension 9: Test Quality (`tests`)

### Target Periksa:
Cakupan test co-located: unit test View-Model dan Service memiliki assertion nyata (`expect(...)`), bukan sekadar render kosong tanpa verifikasi hasil.

### Predikat pelanggaran:
- **[P1]** Test tanpa `expect(`.
- **[P1]** `it.skip` / `test.only` tertinggal.
- **[P1]** Klaim typecheck hijau diturunkan dari test hijau padahal adapter menyatakan test tidak memeriksa tipe.
- **[P3]** View-Model dites lewat render komponen alih-alih fungsi murni.

Grep: `Grep -n "it\.skip\|test\.skip\|\.only("`

---

## 10. Severity Rubric Table

| Level Keparahan | Kriteria Pelanggaran | Tindakan Tindak Lanjut |
|---|---|---|
| **P1 (Kritis)** | DTO bocor ke presentasi, side-effect di API layer, typecheck error baru, tipe `any`, test tanpa assertion, pelanggaran batas framework P1 adapter | Wajib diperbaiki; blokir merge |
| **P2 (Peringatan)** | State di kartu anak, query key raw string, error state tanpa retry, missing cleanup, pelanggaran platform P2 adapter | Ajukan perbaikan sebagai permintaan kerja baru via `frontenddev:lead` |
| **P3 (Saran)** | Penamaan minor, komentar usang, optimasi memoisasi minor | Opsional; tidak memblokir |

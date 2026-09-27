# Unit Slicing Patterns & Dependency DAG Reference

Panduan komprehensif pemecahan tugas arsitektur menjadi brief implementasi atomik, pengelolaan grafik ketergantungan (`depends_on`), dan isolasi unit untuk skill `frontend:plan`. Nama berkas di bawah memakai idiom `react-vite` sebagai contoh; di repo lain diganti sesuai `## Layer taxonomy` adapter.

---

## 1. The 3-Tier Vertical Feature Slice Pattern

Pola pemecahan fitur baru standar menjadi 3 unit independen yang dapat diverifikasi secara terisolasi:

```
[ Unit 01: API & DTO Layer ] ──► [ Unit 02: View-Model & Controller ] ──► [ Unit 03: Presentation & Components ]
  - dto/*.dto.ts                    - view-model (use*ViewModel / *.vm.ts)     - pages/*.tsx | components/*.svelte
  - services/*.service.ts           - controller (use*Page / *.controller.svelte.ts)  - components/*
  - api layer (hooks/api | api/)    - __tests__/*.test.ts                      - __tests__/*.test.tsx
  - (depends_on: [])                - (depends_on: ["01"])                     - (depends_on: ["02"])
```

### Rincian Slicing & Batas Cakupan:

| Unit Eksekusi | Cakupan Files Touched | Dependensi | Done Criteria Utama |
|---|---|---|---|
| **Unit 01 (API)** | DTO, Service, API layer, API tests | `depends_on: []` | Typecheck lulus, endpoint & query key factory terdefinisi |
| **Unit 02 (Logic)** | View-Model mapper, Controller, Logic tests | `depends_on: ["01"]` | Transformasi DTO -> UI props teruji & state orkestrasi siap |
| **Unit 03 (UI)** | Komponen layar, sub-komponen visual, a11y labels | `depends_on: ["02"]` | Mockup visual & 6 cabang state terpasang & interaktif |

---

## 2. Refactoring & Migration Slicing Patterns

### A. Pola Ekstraksi Controller dari Fat Component:
- **Unit 01 (Extract Logic & Controller)**:
  - Buat Controller baru, pindahkan query, mutasi, dan state lokal dari komponen ke Controller, sertakan unit test.
  - Files touched: `<controller sesuai adapter>`, `<test pendamping>`.
  - Dependensi: `depends_on: []`.
- **Unit 02 (Refactor Presentation Component)**:
  - Sederhanakan komponen menjadi komponen presentasi visual murni yang hanya mengonsumsi state dan handler dari Controller.
  - Files touched: `<komponen layar sesuai adapter>`.
  - Dependensi: `depends_on: ["01"]`.

### B. Pola Modularisasi View-Model (DTO Isolation):
- **Unit 01 (Formatters & View-Model)**:
  - Buat View-Model dengan interface `*UI` yang bersih dan fungsi sanitasi/format uang/tanggal.
  - Files touched: `<view-model sesuai adapter>`, file test pendamping.
  - Dependensi: `depends_on: []`.
- **Unit 02 (Integrasi Controller & UI)**:
  - Hubungkan View-Model ke Controller dan ganti import DTO di komponen presentasi.
  - Dependensi: `depends_on: ["01"]`.

---

## 3. Complex Multi-Unit DAG Slicing Patterns (4–5 Units)

Untuk fitur skala besar dengan interaksi multi-halaman atau mutasi berantai:

```
[ Unit 01: DTO & Service ] ──┬──► [ Unit 02: List View-Model & Page ] ─────┬──► [ Unit 04: Detail Page ]
                             └──► [ Unit 03: Mutation & Form VM ] ─────────┘
```

- **Unit 01 (Data Foundation)**: DTO, API Service transport, dan client mocks (`depends_on: []`).
- **Unit 02 (List Screen & View-Model)**: Query list, View-Model mapper, dan Halaman Daftar (`depends_on: ["01"]`).
- **Unit 03 (Form Logic & Mutation)**: Mutation, skema validasi, Form View-Model (`depends_on: ["01"]`).
- **Unit 04 (Detail & Actions Screen)**: Halaman detail transaksi dan integrasi aksi interaktif (`depends_on: ["02", "03"]`).
- **Unit 05 (Integration & E2E Verification)**: Pengujian alur integrasi menyeluruh antar layar (`depends_on: ["04"]`).

---

## 4. Atomic Slicing Rules & Bounds

1. **Maksimal 3–5 File per Unit**: Dilarang menggabungkan terlalu banyak file dalam satu brief agar review kode dan rollback tetap presisi.
2. **Linear DAG (Directed Acyclic Graph)**: Hindari ketergantungan melingkar (*circular dependencies*). Dependensi wajib mengalir satu arah (`01` -> `02` -> `03`).
3. **Verifikasi Biner Mandiri**: Setiap unit wajib memiliki perintah verifikasi (`typecheck`, `lint`, `test` dari `## Commands` adapter) yang dapat dieksekusi secara terisolasi.
4. **Co-located Test Files**: Setiap file logic baru wajib menyertakan file test pendampingnya di dalam daftar `files_touched` unit yang sama.
5. **No Speculative Slicing**: Jangan membuat unit untuk file yang belum dirancang di dokumen `CONTRACT.md`.
6. **Isolated Rollback Boundary**: Jika suatu unit gagal, unit tersebut harus dapat dibatalkan secara bersih tanpa merusak unit sebelumnya yang telah `DONE`.
6b. **Lantai Kompilabel Mandiri**: Tiap unit berakhir pada keadaan kode yang **kompilabel tanpa unit berikutnya**. DAG plugin ini memang mengalir DTO → logic → UI, jadi unit hulu tidak pernah bergantung pada berkas hilir; unit yang menerbitkan import ke berkas yang baru lahir di unit sesudahnya melanggar arah aliran itu, bukan sekadar menunda kompilasi. Lantai ini yang membuat gerbang kompilasi per-brief (`typecheck-per-brief` adapter) dapat ditegakkan. Test yang menuntut komponen dari unit berikutnya **tetap** ditunda ke penutup — test bukan bagian gerbang ini.
7. **Satu Stack per Unit**: Nama berkas dan idiom di dalam satu unit mengikuti satu adapter; dilarang mencampur `.tsx` dan `.svelte` dalam satu taskdir.

---

## 5. Single-Unit Hotfix Slicing Pattern (Mode MINOR)

Untuk perbaikan bug terisolasi pada 1 file eksisting:
- **Unit 01 (Hotfix & Regression Test)**:
  - Files touched: `<Controller atau komponen target sesuai adapter>` dan file test terkait.
  - Frontmatter: `unit: "01"`, `total_units: "1"`, `depends_on: []`.
  - Done Criteria: Bug terselesaikan, nol error baru pada typecheck/lint, dan test regresi lulus.

---

## 6. Slicing Anti-Patterns & Risk Catalog

| Anti-Pattern Slicing | Risiko & Dampak Teknis | Solusi yang Benar |
|---|---|---|
| **God Brief (>5 files)** | Context overload implementor dan kegagalan verifikasi | Pecah menjadi Unit Data, Unit Logic, dan Unit UI |
| **Circular Dependency** | Deadlock urutan eksekusi dispatch subagent | Susun DAG linear satu arah (01 -> 02 -> 03) |
| **Missing Test in Touched** | Implementor tidak dapat mengupdate test terkait | Selalu sertakan file test pendamping di files_touched |
| **Untested Foundation** | Bug di DTO/Service merambat ke seluruh unit UI | Wajibkan unit test pada Unit 01 sebelum lanjut |
| **Cross-Stack Naming** | Berkas tidak dikenali router/compiler repo | Ambil nama dari `## Layer taxonomy` adapter |

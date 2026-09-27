# Brief Template — `plan`

Rumah kanonik bentuk `frontenddev/docs/<YYMMDDhhmm>-<slug>/brief-<NN>-<unit>.md`. Bagian 1 adalah kerangka yang disalin ke artefak, bagian 2 aturan yang ditagih `scripts/validate_briefs.py`, `doc-reviewer`, dan self-test penulis, bagian 3 contoh terisi yang **tidak** tersalin ke artefak. `SKILL.md`, `dispatcher/reviewer.md`, dan `agents/doc-reviewer.md` merujuk ke sini dan dilarang menulis ulang kerangkanya.

---

## 1. Template Kanonik brief-<NN>-<unit>.md

````markdown
---
status: READY
slug: <slug>
stack: <stack-id>
based_on: <sha 7 digit HEAD saat brief ditulis> (<YYYY-MM-DD>)
order: 40
unit: "<NN>"
total_units: "<N>"
depends_on: []
fulfills: ["SC-<n>"]
covers: ["AC-<n>"]
files_touched:
  - <path>
verification:
  - <perintah dari commands.md profil>
---

# Implementation Brief — Unit <NN>: <Nama Unit Fungsional>

Brief implementasi atomik untuk subagent `code-implementor`; satu-satunya acuan kerjanya.

## 1. Intent & Scope Boundaries
- **Intent**: <satu kalimat tujuan teknis unit ini>
- **Akar**: `SC-<n>` (frontmatter `fulfills`)<, lewat `AC-<n>` (`covers`)>
- **Strict Scope Boundaries**: hanya berkas `files_touched`; di berkas `MODIFY` hanya simbol kolom `Anchor`; temuan di luar itu dicatat di `## Out of Scope / Mismatch` laporan unit, tidak diperbaiki.
- **Out of Scope (Dikerjakan pada Unit Lain)**: <unit NN — layer>

## 2. Interfaces & Contracts

```typescript
// DTO, *UI props, dan query key factory persis dari CONTRACT.md — tanpa elipsis, tanpa any
```

## 3. Current Repo State & Reference Symbols

| Aksi | Berkas | Anchor |
|---|---|---|
| CREATE | `<path>` | — |
| MODIFY | `<path>` | `<ekspor top-level yang boleh disentuh>` |

- **Pola Acuan**: `<file:baris>` <pola yang ditiru>
- **Import Alias**: <alias config repo>

## 4. Implementation Steps
1. <langkah penyuntingan berkas — tanpa menjalankan perintah terminal>

## 5. Done Criteria & Verification Baseline
- [ ] <kriteria non-terminal biner>
- [ ] (verifikasi penutup) <perintah dari commands.md profil> — <ambang relatif baseline>
````

Field opsional `remedies: "<NN>"` disisipkan sesudah `depends_on` **hanya** pada brief remedi yang mengambil alih unit `BLOCKED` `<NN>` (Check M). Brief perbaikan atas unit `DONE` (temuan `REVIEW.md`, verifikasi penutup merah) tidak membawanya.

---

## 2. Aturan Validasi

**Mekanis** — ditagih `validate_briefs.py` (per brief dengan `--brief NN`, per batch tanpa); `FAIL` menahan batch commit, ronde `doc-reviewer`, dan `chain.py approve --row BRIEF`. Brief `DONE`/`BLOCKED` terkunci dan tidak disunting saat APPEND: dilewati predikat rencana, tetap ditagih predikat struktur dan cakupan (S, N, D, O, E, C, G).

| Check | Predikat |
|---|---|
| **S** Struktur | atas seluruh brief, termasuk `DONE`/`BLOCKED`: 12 field frontmatter bagian 1 lengkap; `depends_on`, `fulfills`, `covers`, `files_touched`, `verification` berbentuk list; `status` `READY`/`DONE`/`BLOCKED`; lima seksi `##` persis urutan |
| **N** Seri | `unit` berurutan `01..N`; `total_units` brief `READY` seragam dan sama dengan jumlah seluruh brief — brief `DONE`/`BLOCKED` mempertahankan nilainya |
| **D** DAG | `depends_on` hanya ke nomor lebih kecil, asiklik, minimal satu akar |
| **L** Kuota | 1–5 berkas non-test per brief |
| **T** Co-location | berkas di `services/`, `view-model/`, `hooks/api/`, `controllers/` berpasangan test bernama `<stem>.` + akhiran (`order.service.test.ts` untuk `order.service.ts`) di brief yang sama |
| **F** Tanpa verifikasi per unit | seksi 4 tanpa instruksi menjalankan terminal; butir terminal seksi 5 bertanda `(verifikasi penutup)` |
| **B** Placeholder | seksi 2–5 tanpa `TBD`/`TODO`/slot `<...>` di luar blok kode |
| **R** Aksi vs disk | tabel seksi 3 = `files_touched`; `CREATE` belum ada; `MODIFY` sudah ada di disk atau di-`CREATE` brief hulu bernomor lebih kecil, dan ber-`Anchor` |
| **V** Verifikasi | tiap perintah `verification` sama dengan, atau diawali, perintah utuh `commands.md` profil atau `## Commands` adapter (argumen path/pola boleh menyusul); repo Svelte tidak memakai `tsc` tanpa `svelte-check` |
| **K** Penamaan | nama berkas konsisten dengan `stack` (tanpa `.svelte` di React, tanpa `use*.ts`/`.tsx` di Svelte) |
| **O** Tumpang tindih | berkas yang disentuh dua unit hanya bila keduanya terhubung `depends_on` |
| **E** Cakupan kontrak | union `files_touched` = `CONTRACT.md § Execution ## 1. Files Touched` (lane non-MINOR) |
| **C** Acceptance Criteria | tiap `AC-{n}` diklaim `covers` minimal satu brief; nol hantu; AC `test otomatis` punya berkas test yang menyebut nomornya |
| **P** Drift | seksi 3–4 tidak memuat pola warisan yang tercatat `drift.md` profil |
| **G** Fulfills | tiap `SC-{n}` `TASK.md` dipikul minimal satu brief lewat `fulfills`; nol hantu; brief aktif tanpa `fulfills` adalah perluasan lingkup |

**Semantik** — dinilai `doc-reviewer` (D1–D4, maks 2 ronde) lalu self-test penulis:

1. Langkah seksi 4 benar-benar mengerjakan skenario tiap AC di `covers` — klaim cakupan palsu adalah `BLOCKER [SEMANTIK]`.
2. Konsumen berkas yang signature-nya berubah sudah ada di union `files_touched`.
3. Tiap cabang `ST-{n}` dan rute `FLOW.md` tercakup langkah brief mana pun.
4. Tiap brief kompilabel mandiri sesudah mendarat (`references/slicing-patterns.md` bagian 4 butir 6b) — gerbang kompilasi per-brief `architect` menagihnya.

---

## 3. Contoh Terisi — `item-catalog` unit 01 (tidak tersalin ke artefak)

````markdown
---
status: READY
slug: item-catalog
stack: react-vite
based_on: 7d1e0c4 (2026-09-24)
order: 40
unit: "01"
total_units: "03"
depends_on: []
fulfills: ["SC-1"]
covers: ["AC-1", "AC-3"]
files_touched:
  - src/features/catalog/dto/item.dto.ts
  - src/features/catalog/services/item.service.ts
  - src/features/catalog/hooks/api/useItemQuery.ts
  - src/features/catalog/hooks/api/useItemQuery.test.ts
  - src/features/catalog/__tests__/item.service.test.ts
verification:
  - pnpm typecheck
  - pnpm lint
  - pnpm test src/features/catalog
---

# Implementation Brief — Unit 01: Data & Transport Layer

Brief implementasi atomik dan instruksi terisolasi untuk subagent `code-implementor`. Dokumen ini menjadi satu-satunya acuan kerja implementor.

---

## 1. Intent & Scope Boundaries
- **Intent**: Menyediakan DTO, service transport, dan API layer daftar item katalog.
- **Akar**: `SC-1` (frontmatter `fulfills`), lewat `AC-1` dan `AC-3` (`covers`).
- **Strict Scope Boundaries**:
  - Anda HANYA diizinkan membuat atau memodifikasi file yang tercantum pada daftar `files_touched` di frontmatter di atas.
  - Dilarang keras menyentuh, mengedit, atau menghapus file lain di luar daftar `files_touched`.
  - Jika Anda menemukan bug di luar daftar `files_touched`, catat di laporan eksekusi (`## Out of Scope / Mismatch`) tanpa memperbaikinya secara langsung.
- **Out of Scope (Dikerjakan pada Unit Lain)**:
  - Unit 02: View-Model mapper dan Controller layar.
  - Unit 03: Komponen presentasi visual dan styling layout.

---

## 2. Interfaces & Contracts

Patuhi skema antarmuka dan tipe data kontrak di bawah ini secara presisi:

```typescript
// DTO Request Interface
export interface CreateItemRequestDTO {
  title: string;
  amountCents: number;
  categoryId: string;
  description?: string;
  metadata?: Record<string, string>;
}

// DTO Response Interface
export interface ItemResponseDTO {
  id: string;
  title: string;
  amount_cents: number;
  category_id: string;
  category_name: string;
  status: 'ACTIVE' | 'ARCHIVED';
  created_at: string;
}

// Query Key Factory Object
export const ITEM_KEYS = {
  all: ['items'] as const,
  lists: () => [...ITEM_KEYS.all, 'list'] as const,
  list: (filters: Record<string, string>) => [...ITEM_KEYS.lists(), filters] as const,
  details: () => [...ITEM_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...ITEM_KEYS.details(), id] as const,
};
```

---

## 3. Current Repo State & Reference Symbols

| Aksi | Berkas | Anchor |
|---|---|---|
| CREATE | `src/features/catalog/dto/item.dto.ts` | — |
| CREATE | `src/features/catalog/services/item.service.ts` | — |
| CREATE | `src/features/catalog/hooks/api/useItemQuery.ts` | — |
| CREATE | `src/features/catalog/hooks/api/useItemQuery.test.ts` | — |
| CREATE | `src/features/catalog/__tests__/item.service.test.ts` | — |

- **Pola Acuan Query Key**: Rujuk `src/features/auth/hooks/api/useLogin.ts` untuk konvensi array factory query layer.
- **HTTP Client Instance**: Gunakan instance `apiClient` dari `src/services/api.ts` (dilarang membuat instance client baru).
- **Import Alias**: Gunakan alias path `@/*` sesuai konfigurasi `tsconfig.json` (atau `$lib` di SvelteKit).
- **Lokasi State Bersama**: Store global terdaftar di `src/stores/useAuthStore.ts`.
- **Mock Service Worker**: MSW handlers untuk pengujian tersimpan di `src/mocks/handlers.ts`.
- **Adapter Stack**: `react-vite` — idiom layer, jebakan, dan hygiene di `## Layer taxonomy` adapter.

---

## 4. Implementation Steps

Lakukan langkah implementasi secara sekuensial untuk mempermudah lokalisasi kegagalan:

1. **Buat File DTO**:
   - Buat file `src/features/catalog/dto/item.dto.ts` dan ekspor interface `CreateItemRequestDTO` serta `ItemResponseDTO`.
2. **Buat File Service HTTP**:
   - Buat `src/features/catalog/services/item.service.ts` yang mengekspos fungsi transport:
     ```typescript
     export const itemService = {
       getItems: async (): Promise<ItemResponseDTO[]> => {
         const res = await apiClient.get<ItemResponseDTO[]>('/api/v1/items');
         return res.data;
       },
       getItemById: async (id: string): Promise<ItemResponseDTO> => {
         const res = await apiClient.get<ItemResponseDTO>(`/api/v1/items/${id}`);
         return res.data;
       },
     };
     ```
3. **Buat File API Layer**:
   - Buat `src/features/catalog/hooks/api/useItemQuery.ts` (atau padanan adapter) menggunakan query library repo dan factory key `ITEM_KEYS.lists()`.
4. **Buat Unit Test Service**:
   - Buat `src/features/catalog/__tests__/item.service.test.ts` untuk menguji pemanggilan HTTP dengan mock adapter test runner repo.
5. **Buat Unit Test API Layer**:
   - Buat `src/features/catalog/hooks/api/useItemQuery.test.ts` untuk menguji query key `ITEM_KEYS.lists()` dan pemetaan data dari `itemService.getItems`.

---

## 5. Done Criteria & Verification Baseline

- [ ] File `item.dto.ts`, `item.service.ts`, API layer, dan test pendamping terbuat di direktori yang tepat sesuai adapter.
- [ ] Query key dideklarasikan menggunakan factory object array `ITEM_KEYS`.
- [ ] (verifikasi penutup) Nol error baru pada perintah: `pnpm typecheck`.
- [ ] (verifikasi penutup) Nol error baru pada perintah: `pnpm lint`.
- [ ] (verifikasi penutup) Seluruh unit test lokal terkait lulus: `pnpm test src/features/catalog`.
- [ ] Tidak ada file di luar daftar `files_touched` yang dimodifikasi.
- [ ] `item.service.test.ts` menyebut `AC-1` dan `AC-3` di nama kasusnya.
````

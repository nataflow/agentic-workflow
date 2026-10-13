# Lane Routing Matrix & Pipeline Decision Tree

Panduan komprehensif penentuan jalur kerja (Lane Routing), resolusi path monorepo, siklus hidup taskdir, dan tata kelola eskalasi dinamis pada plugin `frontend`.

---

## 1. Comprehensive Lane Selection Matrix

| Jalur (Lane) | Kriteria Pemicu Masuk | Rantai Gate Wajib | Artefak Output |
|---|---|---|---|
| **PROFILE** | Profil `.claude/profile/frontenddev/` belum ada atau butuh sinkronisasi | Deteksi Stack → Pindai → Baseline → Tulis Profil | `.claude/profile/frontenddev/` |
| **FULL_PIPELINE** | Fitur baru atau perombakan alur/layout | Akar → Gate Flow dan/atau Gate Design → Gate Contract → Gate Breakdown (+ Plan Review) → architect → report | `TASK.md`, `FLOW.md`/`UI.md`, `CONTRACT.md`, `brief-*.md`, `REVIEW-PLAN.md`, `report-*.md`, `REVIEW.md`, `REPORT.md` |
| **FAST_FORWARD** | Endpoint/logic data baru tanpa ubah alur & layout | Akar → Gate Contract → Gate Breakdown (+ Plan Review) → architect → report | `TASK.md`, `CONTRACT.md`, `brief-*.md`, `REVIEW-PLAN.md`, `report-*.md`, `REVIEW.md`, `REPORT.md` |
| **REFACTOR_ARCH** | Restrukturisasi layer | sama dengan FAST_FORWARD | sama dengan FAST_FORWARD |
| **HOTFIX_MINOR** | Bugfix/teks terisolasi, 1 berkas, tanpa DTO/alur/state baru | Akar → Gate Breakdown (tanpa Plan Review) → architect → report | `TASK.md`, `brief-01-*.md`, `report-01.md`, `REVIEW.md`, `REPORT.md` |
| **EXPLORE_FACT** | Pertanyaan faktual letak simbol/struktur | dispatch `code-explorer` → Bentuk A ke main loop | laporan di laci kerja (tidak di-commit) |
| **REVIEW_AUDIT** | Penilaian kode di luar rantai aktif | `frontend:review` (diff / path / taskdir tuntas) | chat, atau `frontenddev/reviews/<berkas>.md` bila `--write` |

---

Empat lane yang memprovisi taskdir disebut **lane berakar**: taskdir-nya dibuka `TASK.md` beserta ledger `## Chain` yang dikunci `frontend:task` di `frontend:lead` Phase 7. Pasangan `(lane, sections)` sah ditegakkan skrip di setiap gate: `HOTFIX_MINOR` ⇔ sections kosong; `FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `architecture`; `FULL_PIPELINE` memuat `flow` atau `ui`. `PROFILE`, `EXPLORE_FACT`, dan `REVIEW_AUDIT` tidak memprovisi taskdir.

---

## 2. Monorepo & Multi-Package Routing Heuristics

Pada arsitektur monorepo (Turborepo, Nx, pnpm workspaces, Yarn workspaces):

```
monorepo/
  ├── apps/
  │   ├── web/          (react-vite / sveltekit / svelte-vite)
  │   └── mobile/       (react-native — Expo / Bare)
  └── packages/
      ├── ui/           (Shared Component Library: Button, Card, Dialog)
      ├── shared/       (Shared Constants, Utilities, Type Declarations)
      └── api-client/   (Shared HTTP Client & Base Types)
```

### Heuristik Resolusi Path Otomatis:
1. **Aplikasi Web**:
   - Pola pencarian: `apps/web/src/features/<feat>/**`, `apps/web/src/lib/features/<feat>/**` (SvelteKit), atau `apps/frontend/src/features/<feat>/**`.
   - Konvensi router: dibaca dari `## UI & navigation surface` adapter — `src/routes/**` (React Router / SvelteKit `+page.svelte`) atau tabel rute library SPA.
2. **Aplikasi Mobile (React Native / Expo)**:
   - Pola pencarian: `apps/mobile/src/features/<feat>/**` atau `apps/app/src/features/<feat>/**`.
   - Konvensi router: `apps/mobile/app/**` (Expo Router) atau `apps/mobile/src/navigation/**`.
3. **Komponen Bersama (Design System)**:
   - Pola pencarian: `packages/ui/src/components/**`, `src/components/ui/**`, atau `src/lib/components/ui/**`.
   - Komponen bersama wajib domain-agnostic dan tidak boleh mengimpor tipe dari `apps/**` atau `src/features/**`.
4. **Disambiguasi Ambiguitas Multi-Aplikasi**:
   - **WHEN** nama fitur ditemukan pada `apps/web` DAN `apps/mobile`:
     - `THEN`: Tanyakan target aplikasi secara eksplisit kepada user di awal gate sebelum menetapkan slug. Dua app itu memakai dua `stack` berbeda, dan profil hanya melayani satu (bagian 6, **Satu Profil, Satu App**).
   - **WHEN** komponen target berada di `packages/ui`:
     - `THEN`: Tetapkan slug dengan prefix komponen bersama (misal: `ui-dropdown-select`).

---

## 3. Dynamic Escalation & Lane Switching

Fakta baru yang memperluas cakupan ditangani lewat `chain.py` — satu-satunya penulis `lane`, `sections`, dan ledger — sesudah user mengonfirmasi lewat `AskUserQuestion`:

```
[ HOTFIX_MINOR ]  ── endpoint / DTO / query key baru  ──► escalate FAST_FORWARD  (sections: architecture)
[ HOTFIX_MINOR ]  ── alur atau layout baru            ──► escalate FULL_PIPELINE (sections: flow/ui)
[ FAST_FORWARD ]  ── alur / navigasi baru             ──► escalate FULL_PIPELINE (sections: + flow)
[ REFACTOR_ARCH ] ── perubahan visual layar           ──► escalate FULL_PIPELINE (sections: + ui)
```

- **Satu arah**: lane hanya naik dan `sections` hanya bertambah; `escalate` menolak penurunan.
- **Hop baru disisipkan di posisi kanoniknya** (FLOW, UI, CONTRACT, BRIEF). Hop di bawah hop baru yang sudah `[x]` wajib di-`reopen` lebih dulu — kontrak yang disetujui sebelum alurnya ada tidak lagi sah.
- **Isi akar tidak bergeser**: `SC-{n}` dan nomornya tetap; permukaan baru yang memicu eskalasi menjadi `SC-{n}` berikutnya hanya bila user menyetujuinya.
- **Re-entry** (`chain.py reopen --row R`) membuka R **beserta seluruh hop tercentang di bawahnya** menjadi `[~] … @ re-entry n (was <sidik12>)` dan mengembalikan dokumen FLOW/UI/CONTRACT yang terkena ke `DRAFT` (kejadian `reopen <ROW ROW ...>` di `## Riwayat Rantai` beserta alasan dan keadaan brief saat itu); gate pemilik mengerjakan ulang lalu `approve` mencentangnya lagi bersidik baru. Centang yang lebih tua daripada reopen terakhir hop itu tidak sah. Pemicu sah:
  - brief `BLOCKED` → reopen BRIEF → `plan` APPEND brief remedi (`remedies: "NN"`);
  - `REVIEW.md` `BLOCKED` atau verifikasi penutup merah karena cacat eksekusi → reopen BRIEF → `plan` APPEND brief perbaikan (tanpa `remedies`) → `architect` eksekusi dan review ulang, di taskdir yang sama;
  - berkas yatim, remedi ketiga, atau DTO baru → reopen CONTRACT (kaskade membuka BRIEF) → `contract` → approve → `plan` APPEND; pada `HOTFIX_MINOR` (tanpa hop CONTRACT): reopen BRIEF → `escalate FAST_FORWARD --sections architecture` → `contract` → `plan` APPEND;
  - `DRIFT`, termasuk `SC-{n}` yang berubah lewat amandemen akar.

---

## 4. Session Recovery — `taskdir_state.py`

Keadaan tiap taskdir divonis `taskdir_state.py` (path di peta **Skrip:** `lead/SKILL.md`) dari disk dan ledger — urutan vonis dan rutenya didokumentasikan di docstring skrip itu dan disalin di `SKILL.md` Phase 2. Prinsip yang tidak berubah:

- Taskdir dengan brief `BLOCKED`, draft menggantung, atau ledger belum penuh tidak ditinggal diam-diam; ia muncul di setiap pemindaian sampai tuntas atau diputuskan user.
- Taskdir tuntas (`REPORT.md` ada) tidak diedit ulang; permintaan baru membuka taskdir baru.
- Taskdir tanpa `TASK.md` yang memuat artefak rantai, yang `status` akarnya selain `ACTIVE`/`ABANDONED`, yang `lane`/`sections`-nya berubah di luar akar terkunci (`chain.py root`) atau `chain.py escalate`, yang `base_commit`-nya bukan leluhur `HEAD`, yang `## Riwayat Rantai`-nya rusak, atau yang ledger-nya tak sesuai jadwal `sections`, divonis `RUSAK` (check akar tiap gate ikut `FAIL`): sejak v0.4.0 tidak ada taskdir warisan yang dilayani tanpa akar. Jalan keluarnya keputusan user (`lead/SKILL.md` Failure path 4): akar ber-`TASK.md` → `chain.py abandon` lalu taskdir baru, atau user memulihkan `TASK.md`; taskdir era git yang belum tuntas (tanpa `base_commit`, sebelum Langkah 24) hanya dapat ditutup lewat `chain.py abandon`, sedangkan yang ber-`REPORT.md` divonis `TUNTAS`; nama di luar pola atau tanpa `TASK.md` → direktorinya dipindah keluar `frontenddev/docs/` atau dihapus user.
- Brief `READY` yang tak satu pun dapat berangkat (prasyaratnya tidak pernah tertutup, mis. remedi ber-`depends_on` unit asalnya) divonis `TERHENTI` ber-detail `DAG`, bukan `EKSEKUSI`: reopen BRIEF → `plan` APPEND memperbaiki `depends_on`. `validate_briefs.py` Check D menolak pola itu sejak lahir.
- `REVIEW.md` `BLOCKED` divonis `TEMUAN` dan diperbaiki di taskdir yang sama: reopen BRIEF → `plan` APPEND → `architect` eksekusi dan review ulang; tidak ada taskdir penerus.
- Taskdir kosong divonis `AKAR` → `frontend:task`; user batal → hapus direktori kosong itu. `TASK.md` yang tertulis tetapi belum dikunci `chain.py root` juga `AKAR`.
- Taskdir yang tidak dilanjutkan ditutup `chain.py abandon --reason` (`status: ABANDONED`) atas keputusan user; ia divonis `DITUTUP` dan keluar dari pemindaian.

---

## 5. Plafon Loop

Loop yang berujung ke skill yang sama dapat berputar tanpa henti; plafonnya numerik dan ditegakkan skrip, bukan ingatan. Putaran ronde dimulai sesudah dokumen yang lolos ronde `PASS` dicatat `chain.py draft`, sesudah `reopen` yang membuka hop itu atau hop di atasnya, atau sesudah `chain.py escalate` — dokumen hulu yang berubah membatalkan vonis ronde hilir; tiap putaran berhak 2 ronde; `DISPATCH_FAILED` tidak dihitung, maksimal 2. Revisi dihitung dari kejadian `draft` di `## Riwayat Rantai` sejak reopen atau approve hop itu: `draft` pertama adalah draft, tiap `draft` berikutnya revisi; amandemen akar tidak me-reset hitungan, dan `chain.py draft` menolak revisi ketiga. Melampauinya menandakan cacat satu lapis di atas tempat putaran itu bekerja.

**Sesudah plafon** (baris bertanda *H28* di bawah): gate berhenti tanpa mencatat draft, menyajikan BLOCKER atau poin penolakan yang tersisa, dan menyerahkan ke lead Phase 8, yang menanyakan user lewat `AskUserQuestion`: *rumuskan ulang di taskdir baru* (`chain.py abandon` taskdir lama, lalu permintaan yang dirumuskan ulang masuk lead Phase 1) atau *hentikan*. Tidak ada jalan pintas yang me-reset plafon.

| Loop | Plafon | Penegak | Sesudah plafon |
|---|---|---|---|
| Ronde `contract-reviewer` | 2 per putaran, 8 per taskdir | `review_round.py --gate contract` | *H28* |
| Ronde `doc-reviewer` (Plan Review) | 2 per putaran, 8 per taskdir | `review_round.py --gate plan` | *H28* |
| Revisi user per gate (FLOW, UI, CONTRACT, breakdown) | 2 berturut sejak draft pertama/reopen | `chain.py revisions` · prasyarat `plan` mode REVISE | *H28* |
| Brief remedi per unit asal | 2 (+1 per re-entry kontrak sesudah BLOCKED pertama) | `validate_briefs.py` Check M | `reopen CONTRACT` — cacatnya di kontrak (MINOR: reopen BRIEF → escalate) |
| Re-entry | 3 per hop (dihitung saat hop itu target; kaskade tidak memakan kuota hop di bawahnya), 6 per taskdir (semua reopen) | `chain.py reopen` | *H28* |
| Eskalasi lane per taskdir | 2 | `chain.py escalate` | *H28* |

---

## 6. Scope & Boundary Enforcement

Aturan ketat batasan perutean dan integritas taskdir:
- **No Cross-Taskdir Pollution**: Setiap taskdir beroperasi secara mandiri; dilarang merujuk brief dari taskdir yang berbeda.
- **Strict Timestamping**: Gunakan timestamp 10-digit (`date +%y%m%d%H%M`) untuk menjamin keunikan direktori task antar sesi.
- **Kebab-Case Naming**: Slug wajib menggunakan format huruf kecil dipisah tanda hubung tanpa spasi atau karakter khusus.
- **One Stack per Taskdir**: Satu taskdir hidup di bawah satu `stack` profil; pekerjaan yang menyentuh `apps/web` dan `apps/mobile` sekaligus dipecah menjadi dua taskdir, dikerjakan bergantian.
- **Satu Profil, Satu App**: satu repo punya satu profil `.claude/profile/frontenddev/`, yang melayani satu `target_app`/`stack` pada satu waktu; profil per-app tidak didukung. Pindah ke app lain berarti `frontend:profile` REFRESH ke app itu. Taskdir yang masih terbuka di stack lama tertahan sampai profil dikembalikan: ingest `architect` menolak brief yang `stack`-nya ≠ `stack` profil, sehingga brief tidak pernah dieksekusi dengan adapter yang salah.

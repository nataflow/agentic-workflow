---
status: DRAFT
elicitation: OPEN
type: TECH
category: DATA_MODEL
priority: HIGH
slug: relasi-project-workspace
requester: Budi (Lead Engineer)
created: 2026-10-01
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
request_hash: -
---

# Pisahkan relasi project dan workspace menjadi many-to-many

## Latar Belakang

Project hanya dapat berada di satu workspace karena `workspace_id` menempel langsung di tabel `projects`. Tim sudah tiga kali menduplikasi project untuk kebutuhan lintas workspace, dan tiap duplikasi memecah riwayat task.

## Kondisi Saat Ini

- Kolom `workspace_id` menempel di model project — `internal/project/model.go:12`
- Seluruh query daftar project memfilter langsung ke kolom itu — `internal/project/repository.go:40-48`

## Kondisi Target

Tabel penghubung `project_workspaces` dengan primary key gabungan; kolom `workspace_id` di `projects` dihapus sesudah backfill.

```sql
CREATE TABLE project_workspaces (
  project_id uuid REFERENCES projects(id) ON DELETE CASCADE,
  workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, workspace_id)
);
```

## Keputusan

- **D-1**: Pakai tabel penghubung — alasan: FK dan indeks tetap ditegakkan database — alternatif: kolom `workspace_ids uuid[]`, ditolak karena tanpa FK

## Batasan

- **C-1**: Bentuk respons daftar project di REST dan MCP tidak berubah
- **C-2**: Migrasi reversible tanpa kehilangan data

## Acceptance Criteria

- **AC-1**: Satu project dapat ditautkan ke dua workspace dan muncul di daftar keduanya — verifikasi: test repository `TestProjectRepo_ListByWorkspace`
- **AC-2**: Respons daftar project identik sebelum dan sesudah migrasi (C-1) — verifikasi: snapshot test handler daftar project
- **AC-3**: Migrasi up lalu down mengembalikan `workspace_id` tiap project (C-2) — verifikasi: `make migrate-up` lalu `migrate down 1` atas data seed

## Dampak & Rollout

- Backend saja; frontend tidak berubah karena C-1.
- Urutan: migrasi tambah tabel beserta backfill, ubah repository, lalu migrasi hapus kolom di rilis berikutnya.

## Di Luar Cakupan

- Izin per workspace atas project — tiket terpisah

## Pertanyaan Terbuka

- Tidak ada.

## Lampiran

- Tidak ada.

## Catatan Elisitasi

### Permintaan Asli

> Project perlu bisa ada di lebih dari satu workspace, tolong rapikan relasinya.

### Fakta

#### Masalah Teknis
Relasi project–workspace satu-ke-banyak memaksa duplikasi project; tiga kali terjadi kuartal ini.

#### Kondisi Saat Ini
`workspace_id` di model project (`internal/project/model.go:12`), dipakai filter daftar (`internal/project/repository.go:40-48`).

#### Kondisi Target
Tabel penghubung `project_workspaces`, kolom lama dihapus sesudah backfill.

#### Batasan
Respons REST dan MCP tidak berubah; migrasi wajib reversible.

#### Batas Cakupan
Izin per workspace ditunda ke tiket terpisah.

#### Urgensi
Fitur berbagi project kuartal depan bergantung pada relasi ini.

#### Keputusan
Tabel penghubung dipilih; kolom array ditolak karena tanpa FK.

#### Rollout
Dua rilis: tambah tabel dan backfill, lalu hapus kolom.

#### Ukuran Keberhasilan
Tidak dibahas — AC sudah memuat alat ukurnya.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-10-01 | Bentuk respons REST boleh berubah? | Tidak | Budi |

### Pertanyaan Terbuka

- Tidak ada.

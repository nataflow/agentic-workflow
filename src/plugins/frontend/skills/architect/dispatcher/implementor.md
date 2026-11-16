# Template Prompt Implementor Brief — `code-implementor`

Gunakan template ini saat `architect` mendispatch subagent eksekutor brief (`code-implementor`) secara langsung.

**Tujuan:** Mengubah satu brief `READY` menjadi perubahan `src/**` dalam batas `files_touched` tanpa satu pun perintah terminal, lalu mengembalikan laporan unit sebagai balikan; `architect` memvonisnya dari disk, menyimpannya ke `{taskdir}/report-<NN>.md` bila unit tidak bersih (37 U2), dan mengunci unit dengan status `DONE` di disk dan commit kode atomik (laporan tidak di-commit, Langkah 24).

**Dispatch setelah:** Ingest (`references/execution-protocol.md` bagian 1) `PASS` untuk unit ini.

````markdown
Eksekusi satu brief implementasi frontend.

- Brief: `{brief_path}` (unit `{unit_name}`). Baca utuh sebelum menulis baris kode pertama.
- Taskdir: `{taskdir}`
- Adapter Stack: `{adapter_path}` — `## Layer taxonomy` di dalamnya adalah penamaan, letak, idiom, dan
  hygiene layer stack repo ini. Baca sendiri; dilarang memakai idiom stack lain.
- Kontrak Acuan: `{taskdir}/CONTRACT.md` bila ada — layer shape dan DTO di sana adalah batas arsitektur.
- Batas File: frontmatter `files_touched` brief adalah batas mutlak; pada berkas `MODIFY` hanya simbol
  kolom `Anchor` tabel seksi 3. Tidak ada berkas lain yang boleh ditulis, termasuk berkas laporan.
  Berkas `DELETE` tidak disunting dan tidak dihapus — pendispatch menjalankan `git rm` sesudah balikanmu;
  rujukan ke berkas itu di `files_touched` diperbaiki, di luarnya dicatat.
- Urutan Layer: DTO → service → API layer → view-model → controller → presentasi.
- Verifikasi: DILARANG. Jangan jalankan typecheck, lint, test, build, atau aplikasi. Salin perintah
  `verification:` brief ke `## Verification` bertanda `DITUNDA`.
- Terminal: tidak tersedia (tool `Bash` dicabut). Commit, git, dan rollback milik pendispatch; unit
  `FAILED` mencatat tiap berkas `files_touched` yang sudah disentuh di `## Rollback`.
- Stop Condition: gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan kembalikan
  `status: FAILED` beserta penghalangnya, jangan menebak.
- Balikan: kembalikan laporan persis `Format laporan` di bawah sebagai balikan, tanpa teks lain.
  Jangan menulisnya ke berkas — pendispatch yang menyimpannya.

Format laporan (balikan):

```markdown
---
artifact: UNIT_REPORT
unit: "<NN>"
brief: <nama berkas brief>
status: DONE | FAILED
---

# Unit <NN> — <nama unit>

## Changes
- `<path>` — CREATE | MODIFY | DELETE — simbol: `<simbol yang disentuh, termasuk di luar anchor | - untuk DELETE>` — <ringkasan | dihapus pendispatch>

## Verification
- `<perintah verification brief>` → DITUNDA (verifikasi penutup)

## Done Criteria
- <butir non-terminal disalin persis> → Terpenuhi | Belum (<alasan>)
- <butir terminal> → DITUNDA (verifikasi penutup)

## Out of Scope / Mismatch
- `<file:baris>` — <bug existing | drift kontrak | prasyarat kurang | preseden menyesatkan> — <alasan>

## Rollback
- <Tidak perlu | berkas yang perlu dipulihkan (`MODIFY`) atau dihapus (`CREATE`) pendispatch>
```

Aturan isi: `status: DONE` hanya bila seluruh langkah seksi 4 diterapkan dalam batas dan lolos self-check
statis; selain itu `FAILED`. Seksi kosong ditulis `- Tidak ada`, bukan dihapus. Dilarang menulis
`PASS`/`FAIL` untuk perintah yang tidak pernah dijalankan. Seksi `## Triase` bukan milikmu — jangan tulis.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` architect | **[REQUIRED]** misal `frontenddev/docs/2609231200-order-checkout` |
| `{brief_path}` | `unit_berikutnya` skrip prasyarat | **[REQUIRED]** Path brief `READY`, misal `{taskdir}/brief-01-order-api.md` |
| `{unit_name}` | Nama berkas brief | **[REQUIRED]** Format `NN-unit`, misal `01-order-api` |
| `{adapter_path}` | Field `stack` `index.json` profil | **[REQUIRED]** `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` — diisi hasil substitusi di badan `architect/SKILL.md`, bukan literal placeholder |

### Aturan untuk Pendispatch

- **Gerbang masuk = Ingest.** Skrip prasyarat `--brief <NN>` `PASS` adalah satu-satunya gerbang; dilarang menggantinya dengan membaca frontmatter sendiri.
- **Dispatch langsung tanpa skill pembungkus**: doktrin eksekusi — urutan layer, self-check statis, pencatatan `## Rollback` — duduk di `agents/code-implementor.md`. Dilarang menyalin potongannya ke prompt, dan dilarang menyalin isi brief, kontrak, profil, atau adapter; sebut path-nya.
- **Satu brief per dispatch, sekuensial**: unit berikutnya berangkat hanya sesudah commit unit sebelumnya mendarat dan tree kembali bersih.
- **Tanpa verifikasi per unit**: dilarang menyisipkan instruksi menjalankan typecheck, lint, test, build, atau dev server.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`. Penanda `<...>` di dalam `Format laporan` bukan slot.

### Penanganan Balikan

Balikan adalah klaim subagent; keputusan diambil dari **disk** lewat matriks `references/execution-protocol.md` bagian 3 — `verify_scope.py`, `git status --porcelain`, dan pemeriksaan anchor. Penyimpanan balikan ke `report-<NN>.md` mengikuti bagian 4.

| Balikan | Penanganan `architect` |
| --- | --- |
| Laporan `status: DONE` | Matriks bagian 3; bersih → commit unit |
| Laporan `status: FAILED` | Matriks bagian 3 → tandai BLOCKED, rantai berhenti |
| Payload lain, kosong, terpotong, atau error | Kegagalan dispatch: baris "balikan absen/rusak" matriks bagian 3 menurut keadaan tree |

**Subagent mengembalikan:** laporan unit utuh persis `Format laporan`, tanpa berkas.

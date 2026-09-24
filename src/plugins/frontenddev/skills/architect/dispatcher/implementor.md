# Template Prompt Implementor Brief — `code-implementor`

Gunakan template ini saat `architect` mendispatch subagent eksekutor brief (`code-implementor`) secara langsung.

**Tujuan:** Mengubah satu brief `READY` menjadi perubahan `src/**` dalam batas `files_touched` tanpa satu pun perintah terminal, lalu menulis `{taskdir}/report-<NN>.md` sebagai balikan persisten yang dikunci `architect` dengan commit atomik.

**Dispatch setelah:** Ingest (`references/execution-protocol.md` bagian 1) `PASS` untuk unit ini.

````markdown
Eksekusi satu brief implementasi frontend.

- Brief: `{brief_path}` (unit `{unit_name}`). Baca utuh sebelum menulis baris kode pertama.
- Taskdir: `{taskdir}`
- Adapter Stack: `{adapter_path}` — `## Layer taxonomy` di dalamnya adalah penamaan, letak, idiom, dan
  hygiene layer stack repo ini. Baca sendiri; dilarang memakai idiom stack lain.
- Kontrak Acuan: `{taskdir}/CONTRACT.md` bila ada — layer shape dan DTO di sana adalah batas arsitektur.
- Batas File: frontmatter `files_touched` brief adalah batas mutlak; pada berkas `MODIFY` hanya simbol
  kolom `Anchor` tabel seksi 3. Satu-satunya berkas lain yang boleh ditulis adalah `{report_path}`.
- Urutan Layer: DTO → service → API layer → view-model → controller → presentasi.
- Verifikasi: DILARANG. Jangan jalankan typecheck, lint, test, build, atau aplikasi. Salin perintah
  `verification:` brief ke `## Verification` bertanda `DITUNDA`.
- Commit & git: DILARANG, kecuali rollback ber-scope: `git restore -- <path files_touched>` untuk berkas
  `MODIFY` dan `rm -- <path>` untuk berkas `CREATE` yang dibuat unit ini.
- Stop Condition: gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan tulis `status: FAILED`
  beserta penghalangnya, jangan menebak.
- Balikan: tulis `{report_path}` persis `Format laporan` di bawah, lalu kembalikan satu baris
  `REPORT <unit_name>: <DONE | FAILED> — {report_path}` tanpa teks lain.

Format laporan (`{report_path}`):

```markdown
---
artifact: UNIT_REPORT
unit: "<NN>"
brief: <nama berkas brief>
status: DONE | FAILED
---

# Unit <NN> — <nama unit>

## Changes
- `<path>` — CREATE | MODIFY — simbol: `<simbol yang disentuh, termasuk di luar anchor>` — <ringkasan>

## Verification
- `<perintah verification brief>` → DITUNDA (verifikasi penutup)

## Done Criteria
- <butir non-terminal disalin persis> → Terpenuhi | Belum (<alasan>)
- <butir terminal> → DITUNDA (verifikasi penutup)

## Out of Scope / Mismatch
- `<file:baris>` — <bug existing | drift kontrak | prasyarat kurang | preseden menyesatkan> — <alasan>

## Rollback
- <Tidak dilakukan | berkas yang dipulihkan atau dihapus>
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
| `{report_path}` | Diturunkan dari `NN` | **[REQUIRED]** `{taskdir}/report-<NN>.md`; Check 12 menjamin belum ada |
| `{adapter_path}` | Field `stack` `index.json` profil | **[REQUIRED]** `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` — diisi hasil substitusi di badan `architect/SKILL.md`, bukan literal placeholder |

### Aturan untuk Pendispatch

- **Gerbang masuk = Ingest.** Skrip prasyarat `--brief <NN>` `PASS` adalah satu-satunya gerbang; dilarang menggantinya dengan membaca frontmatter sendiri.
- **Dispatch langsung tanpa skill pembungkus**: doktrin eksekusi — urutan layer, self-check statis, rollback ber-scope — duduk di `agents/code-implementor.md`. Dilarang menyalin potongannya ke prompt, dan dilarang menyalin isi brief, kontrak, profil, atau adapter; sebut path-nya.
- **Satu brief per dispatch, sekuensial**: unit berikutnya berangkat hanya sesudah commit unit sebelumnya mendarat dan tree kembali bersih.
- **Tanpa verifikasi per unit**: dilarang menyisipkan instruksi menjalankan typecheck, lint, test, build, atau dev server.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`. Penanda `<...>` di dalam `Format laporan` bukan slot.

### Penanganan Balikan

Balikan chat hanya penunjuk; keputusan diambil dari **disk** lewat matriks `references/execution-protocol.md` bagian 3 — `report-<NN>.md` beserta `git status --porcelain` dan pemeriksaan anchor.

| Balikan | Penanganan `architect` |
| --- | --- |
| `REPORT <unit>: DONE` | Matriks bagian 3; bersih → commit unit |
| `REPORT <unit>: FAILED` | Matriks bagian 3 → commit BLOCKED, rantai berhenti |
| Payload lain, kosong, atau error | Kegagalan dispatch: cek `report-<NN>.md` dan tree lebih dulu — laporan mungkin sudah tertulis; lalu baris matriks yang berlaku |

**Subagent mengembalikan:** satu baris penunjuk `report-<NN>.md`; isinya dibaca dari disk.

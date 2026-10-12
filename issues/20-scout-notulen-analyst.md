# Langkah 20 — `code-scout` untuk `analyst:notulen`: konteks klarifikasi, bukan isi (S1–S3, D1)

Sumber: permintaan user 2026-10-12 ("skill notulen bisa melakukan code scout juga supaya bisa dapat konteks lebih
banyak"). Basis kode plugin: commit `5dd2983` (analyst 0.15.0).

**Status (2026-10-12):** S1–S3 dan D1 selesai. Test regresi di `tests/analyst/test_notulen_20.py` (10 test). Versi:
analyst 0.16.0.

## Tujuan

1. `analyst:notulen` bisa memakai konteks kode untuk istilah, singkatan, layar, atau fitur yang disebut catatan rapat,
   sehingga pertanyaan klarifikasi ke pencatat lebih tajam (mis. "INV" ditawarkan sebagai opsi "layar Invoice").
2. Iron Law notulen tetap utuh: isi notulen hanya berasal dari catatan asli atau jawaban pencatat.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | **Membalik K4 Langkah 18 untuk `notulen`.** `notulen` kini boleh mendispatch `code-scout`; `intake` dan `spec` tetap tanpa kode. | Permintaan user. Notulen rapat produk sering penuh singkatan dan nama layar yang hanya bisa ditebak dari sistemnya. |
| K2 | **Selalu mode `KONTEKS`.** `BUKTI` tidak dipakai. | Notulen merekam rapat, bukan membuktikan klaim kondisi sistem. |
| K3 | **Konteks bukan isi.** Balikan hanya menjadi opsi `AskUserQuestion` dalam bahasa pengguna, atau `Asumsi:` tanpa rujukan berkas yang wajib dikonfirmasi sebelum `final` (sudah ditagih check 9). `Tidak ditemukan` tidak boleh disimpulkan menjadi "fitur belum ada". | Sama dengan K2 Langkah 18 untuk tiket non-`TECH`. |
| K4 | **Pagar mekanis `path:baris`** di `notulen.py check` (check 10), dengan pengecualian `## Catatan Asli` dan jam dalam backtick. Pola regex sama dengan `EVIDENCE` validator elisitasi. | Sama dengan K3 Langkah 18. Juga mencegah path berkas bocor ke dokumen nataflow, karena `sync-payload` mengirim badan notulen apa adanya. |
| K5 | **Plafon 2 dispatch per notulen**: satu di awal Phase 2 (berjalan sementara notulen ditata), satu susulan sebelum giliran klarifikasi kedua. Ulangan karena gagal atau balikan hilang tidak dihitung. | Selaras plafon elisitasi dan plafon 2 giliran Phase 3. |
| K6 | **Hanya bila catatan menyebut konsep sistem.** Rapat tanpa istilah produk tidak di-scout. Prompt hanya membawa istilahnya, bukan catatan rapat atau nama peserta. | Notulen bisa memuat info sensitif, dan kode tidak menjelaskan rapat non-produk. |
| K7 | **Scout tidak pernah menahan notulen.** Gagal dua kali atau `Repo: tanpa kode` → lanjut tanpa konteks kode. | Notulen tetap bisa dibuat di folder tanpa kode. |
| K8 | **Dispatcher terpisah** `skills/notulen/dispatcher/scout.md`, bukan memakai ulang milik `elicit`. | Slot `{mode}` milik elicit diturunkan dari tipe tiket, dan aturan plafon serta penanganan balikannya berbeda. |

## S1 [Tinggi] Konteks kode bisa bocor jadi isi notulen
- [x] Selesai

`notulen.py check` menambah check 10 `Tanpa rujukan kode` (berlaku di `DRAFT` maupun `--final`, sehingga `final`
ikut menolak). Test: lolos tanpa rujukan; gagal di Pembahasan, Action Item, Keputusan; jam `17:00` lolos; Catatan
Asli dikecualikan; `final` menolak.

## S2 [Tinggi] Dispatcher dan agent belum mengenal notulen
- [x] Selesai

`skills/notulen/dispatcher/scout.md` (baru): mode `KONTEKS` tetap, slot `{root}`/`{batas}`/`{pertanyaan}`, gerbang
masuk, plafon, dan tabel penanganan balikan. `agents/code-scout.md`: deskripsi dan mode `KONTEKS` menyebut notulen
rapat. Tools tetap `Read, Grep, Glob`.

## S3 [Sedang] Prosa `notulen` melarang kode
- [x] Selesai

`skills/notulen/SKILL.md`: Iron Law (konteks utama tidak membaca kode, hanya lewat scout), Precondition 1 (template
dispatch), Phase 0 (dispatch ulang untuk `DRAFT` yang dilanjutkan), Phase 2 langkah 1 (dispatch opsional), Phase 3
(balikan sebagai opsi), guardrail TANPA KODE → KODE SEBAGAI KONTEKS, dua rasionalisasi baru, Failure path 7–8.
`templates/notulen-template.md`: aturan lintas seksi 3 dan 6, self-test 5.

## D1 [Rendah] Dokumen dan versi
- [x] Selesai

- `README.md` analyst: paragraf `code-scout`, `## Notulen Rapat`, `## Penegakan Mekanis` (check 10), `## Sengaja
  Belum Ada`.
- `flow/analyst.md`: Peta Komponen, `### analyst:notulen` (langkah 2–3, subagent, mermaid), tabel Subagent, Titik
  Gagal (scout notulen gagal, check 10).
- `plugin.json` → `0.16.0` (lint M7), deskripsi sama persis di `marketplace.json` (lint M4).
- `CLAUDE.md` repo: baris plugin analyst.

## Di luar cakupan

- Scout di `intake` dan `spec`.
- Mode `BUKTI` untuk notulen rapat teknis.

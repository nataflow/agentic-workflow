# TASK Template & Self-test Akar — `task`

Dipakai di Phase 4 (`SKILL.md`) sebagai isi berkas `frontenddev/docs/<YYMMDDhhmm>-<slug>/TASK.md`. Ikuti bagian 1 persis — satu H1 dan empat heading, tidak lebih: begitu dokumen menuntut sub-heading di luar keempatnya, isinya milik `ux-design`, `ui-design`, `contract`, atau `plan`. Bagian 2 dan 3 tidak ikut tersalin ke artefak.

Bentuk berkas ini sengaja sejajar dengan `TASK.md` milik `backenddev` — frontmatter, heading inti, butir `SC-{n}` ber-alat-ukur, dan ledger `## Chain` — supaya satu fitur full-stack punya dua akar yang dapat disandingkan baris demi baris. Yang berbeda hanya enum `lane`, field `sections`, hop ledger, dan daftar alat ukur sah.

______________________________________________________________________

## 1. Template Kanonik TASK.md

````markdown
---
status: ACTIVE
lane: <FULL_PIPELINE | FAST_FORWARD | REFACTOR_ARCH | HOTFIX_MINOR>
sections: [<flow, ui, architecture — sesuai handoff lead; [] untuk HOTFIX_MINOR>]
created: <YYYY-MM-DD>
finding_source: <path REVIEW.md asal>
findings: [<P1-1>, <P2-3>]
---

# <Fitur — jenis kerja, maksimal 8 kata>

## Description

<Kalimat 1: Keputusan target perubahan perilaku layar/alur atau artefak yang dibuat, secara definitif.>
<Kalimat 2–4: Kondisi kode saat ini dengan minimal satu rujukan `file:baris` terverifikasi (dilarang narasi riwayat/komparasi masa lalu).>

## Success Criteria

- [ ] **SC-1**: <hasil terukur pada permukaan bernama> — verifikasi: <alat ukur sah>
- [ ] **SC-2**: <hasil terukur pada permukaan bernama> — verifikasi: <alat ukur sah>

<ID `SC-{n}` berurutan mulai `SC-1`, permanen sepanjang umur taskdir. Hilir merujuk nomor ini — `contract` di kolom `Sumber` Acceptance Criteria, tiap brief di frontmatter `fulfills`, `REVIEW.md` di `## Cakupan Success Criteria` — sehingga prosa butir tidak pernah perlu disalin ke dokumen hilir.>

## Out of Scope

- <yang tidak dikerjakan> — <alasan: batas modul | opsi yang ditolak | eskalasi ditunda>

## Chain

<ditulis `chain.py init` dari `sections` — dilarang diketik dengan tangan>
````

Baris `## Chain` memuat **tepat** hop yang dijadwalkan `sections`, berurutan: `FLOW` (bila `flow`), `UI` (bila `ui`), `CONTRACT` (bila `sections` non-kosong), dan `BRIEF` (selalu). Hop dicentang hanya oleh `chain.py approve`, dibuka ulang hanya oleh `chain.py reopen`, dan ditambah hanya oleh `chain.py escalate`:

```markdown
- [ ] FLOW     — frontenddev:ux-design     → FLOW.md
- [x] UI       — frontenddev:ui-design     → UI.md @ APPROVED 3f9c2ab
- [~] CONTRACT — frontenddev:contract      → CONTRACT.md @ re-entry 1 (was 7d1e0c4)
- [ ] BRIEF    — frontenddev:plan          → brief-*.md
```

Sha di baris `[x]` adalah commit **konten** yang disetujui user. Gerbang hilir memvonis isi dokumen sekarang identik dengan isinya di sha itu, kecuali baris `status:`; suntingan sesudah approval tanpa `reopen` gagal di setiap skrip prasyarat hilir.

Baris `finding_source:` dan `findings:` hanya ditulis bila akar berangkat dari temuan review; permintaan kerja biasa menghilangkan keduanya sepenuhnya.

______________________________________________________________________

## 2. Self-test Akar

Dijalankan `task` atas `TASK.md` yang baru ditulis, sebelum commit Phase 4 berangkat. Butir 1–4, 6, 7, dan 9 divonis mekanis oleh `scripts/validate_task.py`; butir 5 dan 8 milik model. Satu butir gagal berarti `TASK.md` diperbaiki seketika lalu rangkaian diulang dari butir 1. `TASK.md` adalah akar rantai — cacat di sini menular ke FLOW, UI, CONTRACT, dan tiap brief tanpa satu pun gerbang hilir yang memeriksanya kembali.

1. **Struktur & frontmatter**: frontmatter memuat `status: ACTIVE`, pasangan `lane`/`sections` yang sah (`HOTFIX_MINOR` ⇔ `sections: []`; `FAST_FORWARD`/`REFACTOR_ARCH` ⇔ tepat `[architecture]`; `FULL_PIPELINE` memuat `flow` atau `ui`), dan `created` berformat `YYYY-MM-DD`. Body memuat tepat satu H1 dan tepat empat heading `## Description`, `## Success Criteria`, `## Out of Scope`, `## Chain` dengan nama dan urutan persis bagian 1.
2. **Penomoran `SC-{n}`**: baris `- [ ] **SC-{n}**:` berurut mulai `SC-1` tanpa lompatan dan tanpa nomor ganda, berjumlah 1–7 butir.

   > Lantai satu butir, bukan tiga. Perbaikan satu teks, satu bug lokal, atau satu rename bermuara di satu butir; itu bentuk normalnya, bukan akar yang kurang lengkap.
3. **Alat ukur sah**: tiap butir memuat literal `— verifikasi:` diikuti salah satu alat ukur tabel `SKILL.md` Phase 3 — `test`, `diff`, `typecheck`, `lint`, `build`, atau `QA manual:`. Butir `QA manual:` wajib menyebut rute atau layar, aksi, dan hal yang diamati. Alat ukur subjektif ("review manual", "dinilai layak") atau yang menunjuk dokumen hilir yang belum terbit (`FLOW.md`, `UI.md`, `CONTRACT.md`) adalah kegagalan.
4. **Bukti berpaut kode**: `## Description` memuat minimal satu `file:baris`, dan tiap rujukan menunjuk berkas yang ada dengan nomor baris dalam rentang berkasnya.
5. **Ambang terukur**: tiap butir menyebut nama layar, rute, komponen, state, teks, atau angka spesifik. Kata sifat tanpa ambang ("lebih rapi", "lebih cepat", "intuitif") adalah kegagalan.
6. **Batas kerja bersuara**: `## Out of Scope` memuat minimal satu butir berformat `- <yang tidak dikerjakan> — <alasan>`.
7. **Nol placeholder & temuan terpikul**: tidak ada `TBD`, `TODO`, `FIXME`, `diisi nanti`, atau sisa slot `<...>` (termasuk slot template seperti `<slug>` di dalam backtick). JSX (`<Skeleton />`), generik TS, dan operator perbandingan (`< 300 ms`) bukan placeholder. Bila `finding_source` terisi, tiap ID di `findings` disebut **tepat satu** butir `SC-{n}`, dan butir itu memuat `> Status: FIXED`.
8. **Kecukupan akar**: tiap `SC-{n}` menamai permukaan yang disebut `request` atau terbukti di `evidence`. Butir yang memperkenalkan permukaan di luar keduanya dihapus, dilarang dicarikan akar susulan.
9. **Ledger `## Chain`**: baris hop persis `expected_rows(sections)` dan seluruhnya `[ ]` — ditulis `chain.py init`, bukan diketik.

Hasilnya dilaporkan sebagai satu baris per butir (`butir <n>: lolos` atau `butir <n>: gagal — <rincian>`), dan commit Phase 4 dilarang berangkat sebelum kesembilannya lolos.

______________________________________________________________________

## 3. Contoh Terisi — `order-tracking` (tidak tersalin ke artefak)

````markdown
---
status: ACTIVE
lane: FULL_PIPELINE
sections: [flow, ui]
created: 2026-09-23
---

# Order tracking — layar lacak pengiriman

## Description

Pembeli dapat membuka layar lacak pengiriman dari detail pesanan dan melihat status kurir terakhir. Saat ini detail pesanan tidak punya aksi menuju pelacakan (`src/features/orders/OrderDetail.tsx:88`), dan tabel rute belum memuat rute `/orders/:id/tracking` (`src/app/router.tsx:41`).

## Success Criteria

- [ ] **SC-1**: rute `/orders/:id/tracking` terdaftar dan dapat dibuka dari tombol *Lacak* di detail pesanan — verifikasi: test `OrderDetail.test.tsx` menavigasi ke rute itu hijau
- [ ] **SC-2**: layar tracking menampilkan status kurir terakhir beserta timestamp-nya — verifikasi: QA manual: buka `/orders/<id>/tracking` untuk pesanan terkirim, amati baris status teratas dan jamnya
- [ ] **SC-3**: kegagalan memuat status menampilkan banner error dengan tombol *Coba Lagi* — verifikasi: test `TrackingScreen.test.tsx` kasus error hijau

## Out of Scope

- Peta posisi kurir real-time — opsi yang ditolak pada klarifikasi gate
- Notifikasi push perubahan status — batas modul: `src/features/notifications/` tidak disentuh

## Chain

- [ ] FLOW     — frontenddev:ux-design     → FLOW.md
- [ ] UI       — frontenddev:ui-design     → UI.md
- [ ] CONTRACT — frontenddev:contract      → CONTRACT.md
- [ ] BRIEF    — frontenddev:plan          → brief-*.md
````

Pembanding butir yang **gugur**: `- [ ] **SC-1**: tracking tampil bagus — verifikasi: review manual` — tidak menamai permukaan (rute, layar), kata sifat tanpa ambang, dan alat ukurnya subjektif.

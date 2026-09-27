# TASK Template & Self-test Akar — `task`

Dipakai di Fase 5 (`SKILL.md`) sebagai isi berkas `backenddev/docs/<YYMMDDhhmm>-<slug>/TASK.md`. Ikuti bagian 1 persis — satu H1 dan empat heading (ditambah `## Counters` penutup milik skrip), tidak lebih: begitu dokumen menuntut sub-heading di luar keempatnya, isinya milik `business-analysis`, `system-analysis`, atau `plan`. Bagian 2 tidak ikut tersalin ke artefak.

______________________________________________________________________

## 1. Template Kanonik TASK.md

````markdown
---
status: ACTIVE
chain: <BRD_PRD_BRIEF | PRD_BRIEF | BRIEF>
lane: <PRD_CONVERSION | DIRECT_BRIEF | DEFECT_RCA | EXEC_BRIEF>
risk: <BREAKING | MAJOR | MINOR | ->
created: <YYYY-MM-DD>
ticket_source: <path TICKET.md analyst>
---

# <Domain — jenis kerja, maksimal 8 kata>

## Chain

- [ ] BRD   — backend:business-analysis → BRD.md
- [ ] PRD   — backend:system-analysis  → PRD.md
- [ ] BRIEF — backend:plan             → brief-*.md

<Ledger rantai planning. Muat **tepat** hop milik `chain:` frontmatter, berurutan — hop di luar chain dihapus barisnya, bukan dibiarkan tak tercentang. Hop tuntas dicentang `backend:analyst` beserta jejaknya (`- [x] PRD — backend:system-analysis → PRD.md @ APPROVED a1b2c3d`). Rumah kanonik enum dan aturan pencentangannya di `analyst/references/chain-rules.md` bagian 2. Lane non-planning (`DEFECT_RCA`, `EXEC_BRIEF`): hilangkan seksi ini beserta baris `chain:` frontmatter.>

## Description

<Kalimat 1: Keputusan target perubahan perilaku sistem atau pembuatan artefak saat ini secara definitif.>
<Kalimat 2–4: Kondisi kode teknis terverifikasi dengan minimal satu rujukan `file:baris` (dilarang menulis narasi riwayat/komparasi masa lalu).>

## Success Criteria

- [ ] **SC-1**: <hasil terukur> — verifikasi: <diff, test, atau artefak bernama>
- [ ] **SC-2**: <hasil terukur> — verifikasi: <diff, test, atau artefak bernama>
- [ ] **SC-3**: <hasil terukur> — verifikasi: <diff, test, atau artefak bernama>

<ID `SC-{n}` berurutan mulai `SC-1`, permanen sepanjang umur taskdir. Hilir merujuk nomor ini — `system-analysis` di kolom `Akar` tabel Acceptance Criteria, `plan` di baris `Fulfills:` brief — sehingga prosa butir tidak pernah perlu disalin ke dokumen hilir.>

## Out of Scope

- <yang tidak dikerjakan> — <alasan: batas modul | opsi yang ditolak | eskalasi ditunda>

## Counters

| Kunci | Nilai | Plafon |
|---|---|---|
````

`## Counters` ditulis `task` berisi header tabel saja dan hanya diisi `analyst/scripts/chain_counters.py` (plafon loop re-entry, transisi chain, amandemen akar, penolakan user, pengembalian Open questions, ronde reviewer BRD/PRD); dilarang disunting tangan. Lane non-planning ikut memuatnya.

Baris `ticket_source:` hanya ditulis bila akar berangkat dari tiket analyst (`SKILL.md` Fase 3 butir 7); permintaan lain menghilangkannya sepenuhnya.

______________________________________________________________________

## 2. Self-test Akar

Dijalankan `task` atas `TASK.md` yang baru ditulis, sebelum commit Fase 5 berangkat, lewat `skills/_common/validate_doc.py --kind task --taskdir <taskdir> --fresh [--finding-source <path>]`. `backend:analyst` sesudah transisi eskalasi chain dan gerbang sesudah amandemen menjalankannya ulang tanpa `--fresh`. Validator menagih butir mekanis (ID check di kurung siku); butir `MANUAL` dinilai penulis memakai prosa di bawah. Satu `FAIL` berarti `TASK.md` diperbaiki seketika lalu validator dijalankan ulang. `TASK.md` adalah akar rantai — cacat di sini menular ke BRD, PRD, dan tiap brief tanpa satu pun gerbang hilir yang memeriksanya kembali.

1. **Struktur & frontmatter** [T1]: `status: ACTIVE`, `lane` dan `risk` dari 4 enum masing-masing, `created` `YYYY-MM-DD`; tepat satu H1 dan heading `## Chain` (hanya lane planning), `## Description`, `## Success Criteria`, `## Out of Scope` persis urutan bagian 1, boleh diikuti `## Counters` penutup milik skrip.
2. **Penomoran `SC-{n}`** [T2]: baris `- [ ] **SC-{n}**:` urut mulai `SC-1` tanpa lompatan dan tanpa ganda, 1–7 butir; butir yang dicoret amandemen gerbang (`- [ ] ~~**SC-{n}**: …~~`) tetap dihitung.

   > Lantai satu butir, bukan tiga. Cakupanlah yang menentukan jumlahnya, dan butir 9 di bawah yang menggerbanginya — lantai yang lebih tinggi daripada permukaan yang benar-benar diminta memaksa penambalan yang justru gugur di butir itu. Perbaikan satu temuan, satu bugfix lokal, dan satu rename bermuara di satu butir; itu bentuk normalnya, bukan akar yang kurang lengkap.
3. **Alat ukur sah per lane** [T3a literal `— verifikasi:`, token `BRD.md`/`PRD.md`/`AC-{n}`, alat ukur subjektif, klausa `Status: FIXED` bila `--finding-source`; T3b MANUAL: cocok kolom lane]: tiap butir memuat literal `— verifikasi:` diikuti alat ukur yang terdaftar di kolom "Alat ukur yang sah" tabel Fase 3 untuk `lane` berkas ini. Akar ber-`finding_source`: tiap butir pemikul temuan wajib menambahkan penandaan `> Status: FIXED` atas ID temuannya di samping alat ukur lane itu — atau, bila `finding_source` = `{taskdir}/REVIEW.md`, `ID temuan tidak muncul di REVIEW.md putaran berikutnya` (`SKILL.md` Fase 3 butir 6); butir pemikul temuan yang tidak memuatnya adalah kegagalan. Alat ukur subjektif ("review manual", "dinilai layak"), yang tidak cocok dengan lane-nya, atau yang menunjuk dokumen hop hilir yang belum terbit (`BRD.md`, `PRD.md`) adalah kegagalan. Klausa ini satu-satunya bagian butir SC yang boleh ditulis ulang `backend:analyst` saat eskalasi chain menggeser lane; prosa hasil yang diukur tidak pernah ikut berubah.
4. **Ambang terukur** [T4 MANUAL]: tiap butir menyebut nama entitas, threshold numerik, atau status spesifik. Kata sifat tanpa ambang ("lebih cepat", "optimal", "rapi") adalah kegagalan.
5. **Bukti berpaut kode** [T5]: `## Description` memuat minimal satu `file:baris`, dan tiap rujukan menunjuk berkas yang ada dengan nomor baris dalam jangkauan — dilarang mengarangnya kembali dari ingatan.
6. **Batas kerja bersuara** [T6]: `## Out of Scope` memuat minimal satu butir `- <yang tidak dikerjakan> — <alasan>`; `business-analysis`, `system-analysis`, dan `plan` menegakkan batas ini sebagai plafon ruang lingkupnya.
7. **Nol placeholder** [T7]: nol `TBD`, `TODO`, `diisi nanti`, dan sisa penanda template `<...>` di luar blok kode dan inline code (`## Counters` dikecualikan).
8. **Ledger chain utuh.** 8a memeriksa **struktur** dan berlaku kapan pun `TASK.md` bermutasi; 8b memeriksa **kondisi awal** dan hanya berlaku saat berkasnya baru ditulis.

   - **8a** [T8a]: `chain:` salah satu dari `BRD_PRD_BRIEF`, `PRD_BRIEF`, `BRIEF`, dan `## Chain` memuat **tepat** hop chain itu, urut; `lane` = lane terminal matriks bagian 1.3 `analyst/references/chain-rules.md`, dan pasangan `(risk, chain)` sah menurut bagian 1.4. Lane non-planning: `chain:` dan `## Chain` sama-sama absen. Check ini **tidak menyinggung status centang**, supaya dapat dijalankan ulang sesudah transisi eskalasi — satu-satunya mutasi yang terjadi saat ledger sudah membawa centang.
   - **8b** [T8b, hanya `--fresh`]: seluruh hop `## Chain` belum tercentang.

9. **Kecukupan akar** [T9 MANUAL]: tiap `SC-{n}` menamai permukaan yang disebut `request` atau terbukti di `evidence` — endpoint, modul, aturan, status, atau artefak. Butir yang memperkenalkan permukaan di luar keduanya adalah kegagalan: hapus butirnya, dilarang dicarikan akar susulan. Jumlah butir dinilai dari cakupan, bukan dari plafon — rangkaian yang sudah menutup seluruh permukaan yang diminta lalu ditambah butir demi mendekati angka 7 gagal di butir ini, sekalipun tiap butirnya lolos butir 2–4.
10. **Keterpikulan tiket** [T10, hanya bila frontmatter `ticket_source:` ada]: tiap `AC-{n}` kartu `TICKET.md` disebut sebagai `TAC-{n}` di minimal satu butir `SC-{n}` aktif atau di `## Out of Scope`, dan tidak ada `TAC-{n}` yang nomornya absen dari kartu. Nomor tiket selalu ber-prefix `T` — `AC-{n}` polos tetap token terlarang butir 3.

Hasilnya: keluaran validator ditambah satu baris per butir `MANUAL` (`butir <n>: lolos` atau `butir <n>: gagal — <rincian>`), dan commit Fase 5 dilarang berangkat sebelum seluruhnya lolos.

______________________________________________________________________

## 3. Contoh Terisi — `orders-api` (tidak tersalin ke artefak)

````markdown
---
status: ACTIVE
chain: PRD_BRIEF
lane: PRD_CONVERSION
risk: MAJOR
created: 2026-09-05
---

# Order — pembatalan order berstatus PAID

## Chain

- [ ] PRD   — backend:system-analysis  → PRD.md
- [ ] BRIEF — backend:plan             → brief-*.md

## Description

Order berstatus `PAID` dapat dibatalkan pemilik toko lewat endpoint baru selama stoknya belum dikurangi. Saat ini `OrderService.Cancel` hanya menerima status `PENDING` (`internal/order/service.go:142`), dan transisi `PAID → CANCELLED` tidak terdaftar di `internal/order/state.go:27`.

## Success Criteria

- [ ] **SC-1**: `POST /orders/{id}/cancel` atas order `PAID` mengembalikan 200 dan status berubah `CANCELLED` — verifikasi: `TestCancelPaidOrder` hijau
- [ ] **SC-2**: order `PAID` yang stoknya sudah dikurangi ditolak 409 `ORDER_ALREADY_FULFILLED` — verifikasi: `TestCancelPaidOrder_Fulfilled` hijau
- [ ] **SC-3**: transisi `PAID → CANCELLED` terdaftar di state machine — verifikasi: diff `internal/order/state.go`

## Out of Scope

- Refund otomatis ke payment gateway — batas modul: `internal/payment/` tidak disentuh
- Pembatalan oleh pembeli — opsi yang ditolak pada klarifikasi gerbang
````

Pembanding butir yang **gugur** di self-test bagian 2: `- [ ] **SC-1**: order bisa dibatalkan — verifikasi: test` — tidak menamai permukaan (endpoint, status), dan alat ukurnya tidak menyebut test bernama. Butir `SC-1` di contoh lolos karena keduanya disebut.

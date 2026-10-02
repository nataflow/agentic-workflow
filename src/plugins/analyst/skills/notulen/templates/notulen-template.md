# Template Notulen Rapat — `NOTULEN.md`

Rumah kanonik bentuk notulen `analyst:notulen`. Bagian 1 ditulis `notulen.py new` persis seperti di bawah, dan `tests/analyst/test_notulen_18.py` menagih keduanya sama. Bagian 2 adalah aturan isi tiap seksi, dan bagian 3 self-test sebelum `final`. Aturan yang bisa divonis mesin dijalankan `notulen.py check`.

## 1. Kerangka

````markdown
---
type: meeting
slug: <slug>
meeting_date: <YYYY-MM-DD>
created: <YYYY-MM-DD>
status: DRAFT
source_hash: <12 hex>
final_hash: -
finalized: -
final_answer: -
---

# <judul rapat>

## Ringkasan

_(belum ditulis)_

## Peserta

_(belum ditulis)_

## Agenda

_(belum ditulis)_

## Pembahasan

_(belum ditulis)_

## Keputusan

- Tidak ada.

## Action Item

| ID | Tindakan | PIC | Tenggat |
|---|---|---|---|

## Pertanyaan Terbuka

- Tidak ada.

## Catatan Asli

> <catatan kasar apa adanya>
````

Field frontmatter ditulis skrip. `type`, `slug`, `created`, dan `source_hash` ditulis `new`. `status`, `final_hash`, `finalized`, dan `final_answer` ditulis `final`. `meeting_date` adalah tanggal rapat dari pencatat dan ikut sidik `final_hash`. Skill tidak menyunting frontmatter dengan tangan.

## 2. Aturan Isi

| Seksi | Isi | Bentuk |
|---|---|---|
| `# <judul>` | Judul atau topik rapat dari pencatat. | Satu H1 |
| `## Ringkasan` | 2–4 kalimat: tujuan rapat dan hasil terpentingnya. Hanya merangkum seksi di bawahnya, tanpa fakta baru. | Paragraf |
| `## Peserta` | Nama dan, bila disebut, peran. Nama ditulis seperti di catatan; singkatan yang tidak jelas ditanyakan. | Butir `- ` |
| `## Agenda` | Topik yang dibahas, urut seperti di rapat. | Daftar bernomor atau butir |
| `## Pembahasan` | Poin diskusi per topik agenda: pendapat, data yang disebut, usulan yang belum diputuskan. | Butir, boleh bersub-butir per topik |
| `## Keputusan` | Hanya yang dinyatakan diputuskan di catatan ("putus", "sepakat", "deal", "jadi") atau dikonfirmasi pencatat. | `- **D-n**: <keputusan>`, atau `- Tidak ada.` |
| `## Action Item` | Tindakan yang ditugaskan. PIC dan tenggat hanya bila disebut atau dikonfirmasi. | `\| A-n \| <tindakan> \| <PIC> \| <YYYY-MM-DD> \|`; yang tidak disebut ditulis `belum ditentukan` |
| `## Pertanyaan Terbuka` | Hal yang belum terjawab di rapat, atau celah yang tidak terjawab pencatat. | `- **Q-n**: <pertanyaan> — menunggu: <siapa>`, atau `- Tidak ada.` |
| `## Catatan Asli` | Catatan kasar apa adanya. Dimateraikan `source_hash`; jangan disunting. | Blockquote `> ` |

Aturan lintas seksi:

1. **Keputusan atau pembahasan.** Butir yang ragu ("kayaknya", "usul", "coba") masuk Pembahasan, bukan Keputusan. Bila keraguannya mengubah isi notulen, tanyakan ke pencatat.
2. **Tenggat konkret.** Tenggat relatif ("minggu depan", "Jumat") dihitung dari `meeting_date`, lalu diajukan sebagai opsi tanggal ke pencatat. Tanpa konfirmasi, tenggat ditulis `belum ditentukan`.
3. **Asumsi.** Tafsiran analis yang belum dikonfirmasi ditulis `Asumsi: <...>` di Pembahasan. `final` menolak notulen yang masih memuat `Asumsi:`.
4. **Penomoran.** `D-n`, `A-n`, dan `Q-n` berurutan dari 1. Nomor yang sudah dipakai tidak diganti saat menyunting, agar rujukan ke notulen tetap stabil.
5. **Bahasa rapat.** Istilah, nama produk, dan campuran bahasa dipakai apa adanya. Yang dirapikan hanya kalimat, bukan istilahnya.

## 3. Self-test Sebelum `final`

1. Tiap `D-n` bisa ditunjuk ke baris catatan asli atau ke jawaban pencatat.
2. Tidak ada butir Pembahasan yang sebenarnya keputusan, dan sebaliknya.
3. Tiap `A-n` ber-PIC atau bertenggat `belum ditentukan` memang tidak disebut, bukan terlewat.
4. Ringkasan tidak memuat hal yang tidak ada di seksi lain.
5. Tidak ada informasi dari luar catatan dan jawaban pencatat, termasuk dari kode, tiket, atau rapat lain.

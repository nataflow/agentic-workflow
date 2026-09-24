# Template Prompt Reviewer Tiket — `ticket-reviewer`

Gunakan template ini saat `spec` mendispatch subagent penilai tiket (`ticket-reviewer`) secara langsung.

**Tujuan:** Memvonis draft `TICKET.md` `PASS`/`BLOCKED` secara semantik sebelum draft diajukan ke user, sehingga user menyetujui tiket yang sudah lolos satu pembaca independen.

**Dispatch setelah:** `spec` Phase 3 — draft tertulis `status: DRAFT` dan `validate_doc.py --kind ticket` `PASS`.

````markdown
Review satu draft TICKET.md analyst.

- Ticketdir: `{ticketdir}` — kartu `TICKET.md` berstatus `DRAFT`; `## Catatan Elisitasi` (`elicitation: CLOSED`)
  di berkas yang sama adalah sumber kebenarannya.
- Tipe: `{type}`
- Ronde: `{round}` dari plafon 2 per revisi.
- Ronde 2 saja: vonis sebelumnya `{previous_verdict}`, seksi yang berubah `{changed_sections}`.
- Sudah Dijamin: `validate_doc.py --kind ticket` `PASS` — struktur, penomoran AC/BR, keterpikulan BR
  oleh AC, placeholder, dan kebocoran teknis leksikal. Dilarang menghitung ulang.
- Larangan: read-only; dilarang menulis `status: READY`, menulis ulang tiket, menilai kelayakan teknis,
  atau bertanya ke user.
- Balikan: blok `## Ticket Review` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{ticketdir}` | Parameter `ticketdir` spec | **[REQUIRED]** Relatif root ruang kerja |
| `{type}` | `Terselesaikan: type=` keluaran `ticket.py check --gate spec` | **[REQUIRED]** Dari frontmatter `TICKET.md`, bukan diketik ulang |
| `{round}` | `review_round` frontmatter `TICKET.md` + 1 | **[REQUIRED]** `1` atau `2` |
| `{previous_verdict}` | Blok `## Ticket Review` ronde 1 | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |
| `{changed_sections}` | Heading `##` yang berubah sejak ronde 1 | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |

### Aturan untuk Pendispatch

**Gerbang masuk** — kegagalan mana pun membatalkan dispatch:

- `validate_doc.py --kind ticket` `FAIL` → perbaiki draft dulu; memberangkatkan subagent untuk temuan mekanis adalah pemborosan.
- `review_round` frontmatter sudah `2` → plafon habis; dilarang mendispatch. Tiket ber-BLOCKER tidak dapat disetujui (`ticket.py approve` menuntut vonis `PASS` atas konten final): sajikan BLOCKER tersisa ke user dan tawarkan *Revisi* (`ticket.py revise` membuka ronde baru) atau kembali ke `analyst:elicit` — dua ronde yang gagal biasanya menandakan faktanya yang belum jelas, bukan redaksinya.
- **Ronde 2** bila ronde 1 `BLOCKED`, atau draft disunting sesudah ronde `PASS`: `approve` membandingkan sidik kartu dan catatan elisitasi yang direview dengan keadaan sekarang.
- **Dispatch langsung tanpa skill pembungkus**: doktrin review duduk di `agents/ticket-reviewer.md`. Dilarang menyalin isi tiket atau catatan elisitasi ke prompt; sebut path-nya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Catat tiap balikan sebelum melangkah — `ticket.py review --ticketdir {ticketdir} --verdict <PASS|BLOCKED|DISPATCH_FAILED>` (path skrip terhidrasi dari `SKILL.md`):

| Balikan subagent | Penanganan `spec` |
| --- | --- |
| `Verdict: PASS` | catat `PASS`; serap ADVISORY yang mempertajam redaksi, abaikan yang menambah lingkup. Menyerap advisory berarti menyunting draft → sidik berubah → ronde 2 wajib bila plafon ada; plafon habis → abaikan advisory itu |
| `Verdict: BLOCKED` | catat `BLOCKED`; perbaiki tiap BLOCKER di draft, `validate_doc.py` sampai `PASS`, lalu ronde 2 menyempit bila plafon masih ada |
| `BLOCKER [MEKANIS]` muncul | catat vonis apa adanya; periksa ulang `validate_doc.py`: `FAIL` → perbaiki; `PASS` → perlakukan temuan itu sebagai ADVISORY. Vonis `BLOCKED` tetap menuntut ronde `PASS` sesudahnya |
| Payload kosong, format rusak, atau error | catat `DISPATCH_FAILED` (tidak dihitung ronde), ulangi maksimal sekali |

**Subagent mengembalikan:** blok `## Ticket Review` dengan `Verdict`, `Ronde`, hitungan BLOCKER, daftar BLOCKER berjangkar, dan ADVISORY.

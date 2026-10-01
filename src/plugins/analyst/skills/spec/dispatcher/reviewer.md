# Template Prompt Reviewer Tiket — `ticket-reviewer`

Gunakan template ini saat `spec` mendispatch subagent penilai tiket (`ticket-reviewer`) secara langsung.

**Tujuan:** Memvonis draft `TICKET.md` `PASS`/`BLOCKED` secara semantik sebelum draft diajukan ke user, sehingga user menyetujui tiket yang sudah lolos satu pembaca independen.

**Dispatch setelah:** `spec` Phase 3 — draft tertulis `status: DRAFT` dan `validate_doc.py --kind ticket` `PASS`.

````markdown
Review satu draft TICKET.md analyst.

- Ticketdir: `{ticketdir}` — kartu `TICKET.md` berstatus `DRAFT`; `## Catatan Elisitasi` (`elicitation: CLOSED`)
  di berkas yang sama adalah sumber kebenarannya.
- Tipe: `{type}` · kategori `{category}` (`TECH` → nilai dengan rubrik bagian *Tiket `TECH`* definisi agent-mu)
- Ronde: `{round}` dari plafon 2 per revisi.
- Ronde 2 saja: vonis sebelumnya `{previous_verdict}`, seksi yang berubah `{changed_sections}`.
- Sidik konten yang kamu nilai: `{sidik}` — salin apa adanya ke baris `- Sidik:` balikanmu; dilarang menghitung
  atau mengubahnya.
- Sudah Dijamin: `validate_doc.py --kind ticket` `PASS` — struktur, penomoran AC/BR, keterpikulan BR
  oleh AC, placeholder, dan kebocoran teknis leksikal (`TECH`: penomoran AC/D/C, keterpikulan C oleh AC,
  dan keberadaan tiap `path:baris` di disk). Dilarang menghitung ulang.
- Larangan: read-only; dilarang menulis `status: READY`, menulis ulang tiket, menilai kelayakan teknis,
  atau bertanya ke user.
- Balikan: blok `## Ticket Review` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{ticketdir}` | `<root>/<ticketdir>` (`root` dari baris `Terselesaikan:` `check --gate spec`) | **[REQUIRED]** Path absolut |
| `{type}` | `Terselesaikan: type=` keluaran `ticket.py check --gate spec` | **[REQUIRED]** Dari frontmatter `TICKET.md`, bukan diketik ulang |
| `{category}` | Frontmatter `category` `TICKET.md` | **[REQUIRED]** `TECH` saja; `-` untuk tipe lain |
| `{round}` | `Terselesaikan: ronde=` keluaran `ticket.py check --gate spec` | **[REQUIRED]** `1` atau `2`; `habis` → dilarang dispatch. `ticket.py review` menolak blok yang `- Ronde:`-nya berbeda |
| `{previous_verdict}` | Isi berkas `review_report` dari `check --gate spec` (blok `## Ticket Review` ronde 1) | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |
| `{changed_sections}` | Heading `##` yang berubah sejak ronde 1 | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |
| `{sidik}` | `Terselesaikan: sidik=` keluaran `ticket.py check --gate spec`, diambil **tepat sebelum** dispatch | **[REQUIRED]** `<12 hex>/<12 hex>`; `ticket.py review` menolak balikan yang sidiknya berbeda dari disk |

### Aturan untuk Pendispatch

**Gerbang masuk** — kegagalan mana pun membatalkan dispatch:

- `validate_doc.py --kind ticket` `FAIL` → perbaiki draft dulu; memberangkatkan subagent untuk temuan mekanis adalah pemborosan.
- `ronde=habis` di keluaran `check --gate spec` → plafon habis; dilarang mendispatch. Tiket ber-BLOCKER tidak dapat disetujui (`ticket.py approve` menuntut vonis `PASS` atas konten final): sajikan BLOCKER tersisa ke user dan tawarkan *Revisi* (`ticket.py revise` membuka ronde baru) atau kembali ke `analyst:elicit` — dua ronde yang gagal biasanya menandakan faktanya yang belum jelas, bukan redaksinya.
- **Ronde 2** bila ronde 1 `BLOCKED`, atau draft disunting sesudah ronde `PASS`: `approve` membandingkan sidik kartu dan catatan elisitasi yang direview dengan keadaan sekarang.
- **Dispatch langsung tanpa skill pembungkus**: doktrin review duduk di `agents/ticket-reviewer.md`. Dilarang menyalin isi tiket atau catatan elisitasi ke prompt; sebut path-nya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Catat tiap balikan sebelum melangkah — `ticket.py review --ticketdir {ticketdir} --verdict <PASS|BLOCKED> --report -` dengan blok balikan apa adanya lewat stdin, atau `--verdict DISPATCH_FAILED` tanpa `--report` (path skrip terhidrasi dari `SKILL.md`). `REVIEW FAIL` karena sidik berbeda → draft berubah sesudah dispatch: dispatch ulang dengan `{sidik}` baru, bukan menyunting blok balikan:

| Balikan subagent | Penanganan `spec` |
| --- | --- |
| `Verdict: PASS` | catat `PASS`; serap ADVISORY yang mempertajam redaksi, abaikan yang menambah lingkup. Menyerap advisory berarti menyunting draft → sidik berubah → ronde 2 wajib bila plafon ada; plafon habis → abaikan advisory itu |
| `Verdict: BLOCKED` | catat `BLOCKED`; perbaiki tiap BLOCKER di draft, `validate_doc.py` sampai `PASS`, lalu ronde 2 menyempit bila plafon masih ada |
| `ADVISORY [ELISITASI]` muncul | jangan diserap ke kartu — jawabannya fakta baru yang belum ada di catatan elisitasi. Blok vonis sampai ke user apa adanya di Phase 5, dan jawabannya ditempuh lewat *Kembali ke elisitasi* |
| `BLOCKER [MEKANIS]` muncul | catat vonis apa adanya; periksa ulang `validate_doc.py`: `FAIL` → perbaiki; `PASS` → perlakukan temuan itu sebagai ADVISORY. Vonis `BLOCKED` tetap menuntut ronde `PASS` sesudahnya |
| Payload kosong, format rusak, error, atau `REVIEW FAIL: blok reviewer tidak konsisten` (hitungan BLOCKER ≠ butir, `PASS` ber-BLOCKER, `BLOCKED` tanpa BLOCKER, `- Ronde:` salah) | catat `DISPATCH_FAILED` (tidak dihitung ronde), ulangi maksimal sekali; dilarang menyunting blok balikan agar lolos |

**Subagent mengembalikan:** blok `## Ticket Review` dengan `Verdict`, `Sidik`, `Ronde`, hitungan BLOCKER, daftar BLOCKER berjangkar, dan ADVISORY.

# Template Prompt Reviewer Charter — `charter-reviewer`

Gunakan template ini saat `product:spec` mendispatch subagent penilai charter (`product:charter-reviewer`) secara
langsung.

**Tujuan:** Memvonis draft kartu `CHARTER.md` `PASS`/`BLOCKED` secara semantik sebelum draft diajukan ke user,
sehingga user menyetujui charter yang sudah lolos satu pembaca independen.

**Dispatch setelah:** `spec` Phase 3 — kartu tertulis dan `validate_doc.py --kind charter` `PASS`.

````markdown
Review satu draft CHARTER.md product.

- Charterdir: `{charterdir}` — kartu enam pilar; `## Catatan Elisitasi` (tertutup dan tersegel) di berkas yang sama
  adalah sumber kebenarannya, dengan `### Konteks Awal` sebagai jangkar segmen dan masalah.
- Mode: `{mode}` (fokus 10 definisi agent-mu berlaku untuk NEW_FEATURE dan IMPROVEMENT)
- Ronde: `{round}` dari plafon 2 per revisi.
- Ronde 2 saja: vonis sebelumnya `{previous_verdict}`, seksi yang berubah `{changed_sections}`.
- Sidik konten yang kamu nilai: `{sidik}` — salin apa adanya ke baris `- Sidik:` balikanmu; dilarang menghitung
  atau mengubahnya.
- Sudah Dijamin: `validate_doc.py --kind charter` dan `--kind notes` `PASS` — struktur, penomoran, aktor terdaftar di
  alur, pengecualian BR, angka SC, ID Scope, tanda per mode, placeholder, dan keberadaan tiap `path:baris`. Dilarang
  menghitung ulang.
- Larangan: read-only; dilarang menulis `status: APPROVED`, menulis ulang charter, menilai kelayakan teknis, atau
  bertanya ke user.
- Balikan: blok `## Charter Review` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{charterdir}` | `<root>/<charterdir>` (`root` dari baris `Terselesaikan:` `check --gate spec`) | **[REQUIRED]** Path absolut |
| `{mode}` | `Terselesaikan: mode=` keluaran `charter.py check --gate spec` | **[REQUIRED]** Dari frontmatter, bukan diketik ulang |
| `{round}` | `Terselesaikan: ronde=` keluaran `charter.py check --gate spec` | **[REQUIRED]** `1` atau `2`; `habis` → dilarang dispatch |
| `{previous_verdict}` | isi berkas `review_report` dari `check --gate spec` | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |
| `{changed_sections}` | heading `##` yang berubah sejak ronde 1 | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |
| `{sidik}` | `Terselesaikan: sidik=` keluaran `charter.py check --gate spec`, diambil **tepat sebelum** dispatch | **[REQUIRED]** `<12 hex>/<12 hex>` |

### Aturan untuk Pendispatch

**Gerbang masuk** — kegagalan mana pun membatalkan dispatch:

- `validate_doc.py --kind charter` `FAIL` → perbaiki draft dulu.
- `ronde=habis` → plafon habis; dilarang mendispatch. Charter ber-BLOCKER tidak dapat disetujui: sajikan BLOCKER
  tersisa ke user dan tawarkan *Revisi* (`charter.py revise` membuka ronde baru) atau *Kembali ke elisitasi*.
- **Dispatch langsung tanpa skill pembungkus**. Dilarang menyalin isi charter ke prompt; sebut path-nya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Catat tiap balikan sebelum melangkah — `charter.py review --charterdir {charterdir} --verdict <PASS|BLOCKED> --report -`
dengan blok balikan apa adanya lewat stdin, atau `--verdict DISPATCH_FAILED` tanpa `--report` (path skrip terhidrasi
dari `SKILL.md`). `REVIEW FAIL` karena sidik berbeda → draft berubah sesudah dispatch: dispatch ulang dengan `{sidik}`
baru, bukan menyunting blok balikan.

| Balikan subagent | Penanganan `spec` |
| --- | --- |
| `Verdict: PASS` | catat `PASS`; serap ADVISORY yang mempertajam redaksi, abaikan yang menambah lingkup. Menyerap advisory menyunting draft → sidik berubah → ronde 2 wajib bila plafon ada; plafon habis → abaikan advisory itu |
| `Verdict: BLOCKED` | catat `BLOCKED`; perbaiki tiap BLOCKER, `validate_doc.py` sampai `PASS`, lalu ronde 2 menyempit bila plafon ada |
| `ADVISORY [ELISITASI]` muncul | jangan diserap ke kartu — jawabannya fakta baru. Sampaikan ke user di Phase 5; jawabannya lewat *Kembali ke elisitasi* |
| `BLOCKER [MEKANIS]` muncul | catat vonis apa adanya; periksa ulang `validate_doc.py`: `FAIL` → perbaiki; `PASS` → perlakukan sebagai ADVISORY. Vonis `BLOCKED` tetap menuntut ronde `PASS` sesudahnya |
| Payload kosong, format rusak, error, atau `REVIEW FAIL: blok reviewer tidak konsisten` | catat `DISPATCH_FAILED` (tidak dihitung ronde), ulangi maksimal sekali; dilarang menyunting blok balikan |

**Subagent mengembalikan:** blok `## Charter Review` dengan `Verdict`, `Sidik`, `Ronde`, hitungan BLOCKER, daftar
BLOCKER berjangkar, dan ADVISORY.

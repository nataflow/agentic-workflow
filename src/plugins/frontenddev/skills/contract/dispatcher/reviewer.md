# Template Prompt Reviewer Kontrak — `contract-reviewer`

Gunakan template ini saat `contract` mendispatch subagent penilai kontrak (`contract-reviewer`) secara langsung.

**Tujuan:** Memvonis draft `CONTRACT.md` `PASS`/`BLOCKED` secara semantik sebelum draft di-commit dan diajukan ke user, sehingga user menyetujui kontrak yang sudah lolos satu pembaca independen.

**Dispatch setelah:** `contract` Phase 5 — draft tertulis `status: DRAFT`, `validate_doc.py --kind contract` `PASS`, dan `review_round.py open --gate contract` `PASS`.

````markdown
Review satu draft CONTRACT.md frontend.

- Taskdir: `{taskdir}` — `CONTRACT.md` berstatus `DRAFT`; dokumen hulu `TASK.md` dan, sesuai
  `sections`, `FLOW.md`/`UI.md` sudah disetujui.
- Sections: `{sections}`
- Stack: `{stack}` — idiom penamaan di `{adapter_path}` seksi `## Layer taxonomy`.
- Ronde: `{round}` dari plafon 2 per putaran (putaran baru sesudah draft `PASS` di-commit, atau sesudah `reopen`).
- Ronde 2 saja: vonis sebelumnya `{previous_verdict}`, seksi yang berubah `{changed_sections}`.
- Aturan Semantik: bagian 2 butir 7–13 `${CLAUDE_PLUGIN_ROOT}/skills/contract/templates/contract-template.md`.
- Sudah Dijamin: `validate_doc.py` `PASS` — struktur, penomoran AC, token Sumber, dan keterpikulan
  SC/DD/ST. Dilarang menghitung ulang.
- Larangan: read-only; dilarang menulis `status: APPROVED`, merancang ulang kontrak, atau bertanya ke user.
- Balikan: blok `## Contract Review` sesuai definisi agent-mu, tanpa teks lain.
````

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` contract | **[REQUIRED]** |
| `{sections}` | `Terselesaikan: sections=` prasyarat | **[REQUIRED]** Dari `TASK.md`, bukan diketik ulang |
| `{stack}` | Field `stack` `index.json` profil | **[REQUIRED]** |
| `{adapter_path}` | `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` | **[REQUIRED]** Hasil substitusi, bukan literal |
| `{round}` | Keluaran `review_round.py open --gate contract` | **[REQUIRED]** `1` atau `2` |
| `{previous_verdict}` | Blok `## Contract Review` ronde 1 | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |
| `{changed_sections}` | Heading `##` yang berubah sejak ronde 1 | **[OPTIONAL]** Hanya ronde 2; `-` di ronde 1 |

### Aturan untuk Pendispatch

**Gerbang masuk** — kegagalan mana pun membatalkan dispatch:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind contract --taskdir {taskdir}
python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py open --taskdir {taskdir} --gate contract
```

- `validate_doc.py` `FAIL` → perbaiki draft dulu; memberangkatkan subagent untuk temuan mekanis adalah pemborosan.
- `review_round.py open` `FAIL` → plafon habis (2 per putaran, 8 per taskdir); dilarang mendispatch. Kontrak ber-BLOCKER tidak dapat disetujui (`chain.py approve` menuntut ronde terakhir `PASS`): hentikan Gate Contract, sajikan BLOCKER tersisa ke user, dan serahkan ke `frontenddev:lead` Phase 8 (klarifikasi lingkup: amandemen akar, atau `chain.py abandon`) — dua ronde yang gagal menandakan lingkupnya yang belum jelas, bukan redaksinya.
- **Ronde 2** bila ronde 1 ber-verdict `BLOCKED` — termasuk yang hanya ber-`BLOCKER [MEKANIS]` — atau draft disunting sesudah ronde `PASS`: `chain.py approve` menuntut ronde terakhir `PASS` atas konten final, tanpa `reopen` hop sesudahnya.
- **Dispatch langsung tanpa skill pembungkus**: doktrin review duduk di `agents/contract-reviewer.md`. Dilarang menyalin isi kontrak, FLOW, UI, atau profil ke prompt; sebut path-nya.
- **Audit hidrasi**: batalkan dispatch bila prompt masih memuat slot `{...}` mentah atau `TBD`/`TODO`.

### Penanganan Balikan

Catat tiap balikan sebelum melangkah:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py record --taskdir {taskdir} --gate contract \
  --verdict <PASS|BLOCKED|DISPATCH_FAILED> --mechanical <n> --semantic <n>
```

| Balikan subagent | Penanganan `contract` |
| --- | --- |
| `Verdict: PASS` | `record --verdict PASS`; serap ADVISORY yang menyederhanakan, abaikan yang menambah lingkup; commit draft (Phase 6) |
| `Verdict: BLOCKED` | `record --verdict BLOCKED`; perbaiki tiap BLOCKER di draft, `validate_doc.py` sampai `PASS`, lalu ronde 2 menyempit bila plafon masih ada |
| `BLOCKER [MEKANIS]` muncul | Catat vonis apa adanya (`record --verdict BLOCKED --mechanical <n>`); reviewer menghitung ulang yang sudah dijamin — periksa ulang `validate_doc.py`: `FAIL` → perbaiki sampai `PASS`; `PASS` → perlakukan temuan itu sebagai ADVISORY dan catat penyimpangannya. Lalu ronde menyempit — vonis `BLOCKED` tidak dapat disetujui tanpa ronde `PASS` sesudahnya |
| Payload kosong, format rusak, atau error | `record --verdict DISPATCH_FAILED` (tidak dihitung plafon ronde; maksimal 2 per taskdir), ulangi maksimal sekali |

**Subagent mengembalikan:** blok `## Contract Review` dengan `Verdict`, `Ronde`, hitungan BLOCKER, daftar BLOCKER berjangkar, dan ADVISORY.

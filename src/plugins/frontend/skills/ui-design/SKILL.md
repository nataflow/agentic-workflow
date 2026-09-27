---
name: ui-design
description: Dipanggil frontend:lead ketika sections TASK.md memuat ui, sesudah hop FLOW tercentang bila flow ikut dijadwalkan - merancang layout visual, prioritas P1-P3, dan enam cabang state ke UI.md yang disetujui user di Gate Design, sebelum kontrak teknis atau kode komponen ditulis
user-invocable: false
---

## THE IRON LAW

- `UI.md` lahir dan di-commit `DRAFT`; `APPROVED` hanya ditulis `chain.py approve --row UI` sesudah jawaban eksplisit user di `AskUserQuestion`. Dilarang menulis `APPROVED` dengan tangan.
- Draft diajukan ke user hanya sesudah `validate_doc.py --kind ui` `PASS`.
- Tiap layar merancang enam cabang state ber-ID `ST-{n}`; state fetching dikoordinasikan Controller layar, bukan komponen anak.
- Token visual dari `visual.md` profil dan batas platform dari adapter stack; dilarang membuat atau mengubah berkas di `src/`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ui-design/scripts/check_preconditions.py --taskdir <taskdir>`.
2. `PASS` (9/9): lanjut. `FAIL`: hentikan dan remediasi — akar tidak sah atau `sections` tanpa `ui` → kembali ke `frontend:lead`; hop `FLOW` belum tercentang atau berubah sesudah disetujui → `ux-design` atau `chain.py reopen --row FLOW` lewat lead; `UI.md` sudah `APPROVED` → gate ini tuntas, revisi hanya lewat `chain.py reopen --row UI`; profil/adapter → `frontend:profile`; tree kotor yang menurut skrip seluruhnya artefak taskdir ini (draft tertunda sesi lalu) → commit dulu sebagai `draft`/`revise UI.md` (Phase 5 butir 3), lalu ulangi prasyarat; kotoran lain → laporkan ke user. `WARN` `UI.md` tertunda (`DRAFT`) → tanyakan ke user: putuskan draft itu, revisi, atau tulis ulang.
3. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — taskdir aktif.
- `feature_name` — string — `[REQUIRED]` — layar/fitur yang dirancang.
- `information_density` — string — default `"comfortable"` — `comfortable` | `compact`; pilihan akhir keputusan user di Phase 3.

## Workflow

### Phase 0 — Hulu & Profil Desain

- Buka `FLOW.md` bila `sections` memuat `flow` (tercentang dan utuh, dijamin skrip) dan `TASK.md`: layar dan cabang yang dirancang memikul `SC-{n}`; `## Out of Scope` adalah plafon.
- Baca `index.json` (`stack`), `stack.md`, dan `visual.md` profil, lalu `## UI & navigation surface` adapter: breakpoint web atau safe area/touch target/keyboard mobile, letak design token, atribut aksesibilitas.
- Telusuri komponen bersama di lokasi `structure.md` profil (Button, Card, Modal, Input, Skeleton). **Kuota sapuan gate**: 2 `Glob`+`Grep` dan 2 read ber-offset; komponen tersebar lintas paket, relasi (konsumen komponen, pemilik token), atau kuota habis → hidrasi `dispatcher/explorer.md` dan dispatch `code-explorer`.

### Phase 1 — Orientasi Design System

Utamakan komponen yang sudah ada (`references/ui-patterns.md`). Web (`react-vite`, `sveltekit`, `svelte-vite`): responsif, fokus keyboard terlihat. Mobile (`react-native`): safe area pada container root, area sentuh ≥44×44 dp, keyboard avoidance.

### Phase 2 — Klarifikasi Visual

Kerapatan informasi atau estetika yang ambigu → maksimal 3 pertanyaan sekuensial lewat `AskUserQuestion`, masing-masing dengan mockup ASCII konkret sebagai pratinjau opsi.

### Phase 3 — Opsi Tata Letak

Tawarkan 2–3 opsi — Standard Card/List · Compact/Dense Table · Visual-Driven/Hero Metric — beserta trade-off, rekomendasikan satu, dan minta keputusan user lewat `AskUserQuestion`.

### Phase 4 — Prioritas Informasi & Enam Cabang

- **P1** judul, nilai utama, status utama, CTA primer · **P2** tanggal, kategori, referensi, badge sekunder · **P3** helper text, filter minor, tautan ketentuan.
- **Enam cabang wajib per layar**: normal/ready, loading (skeleton berdimensi, anti-CLS), kosong (ikon + CTA kontekstual), error (pesan manusiawi + *Coba Lagi* yang memanggil handler Controller), initial/idle, stale/mutating (indikator mikro, cegah double-submit). Nomori `ST-{n}` berurutan lintas layar, **enam per layar** (`ST-1..6` layar 1, `ST-7..12` layar 2); cabang yang tidak relevan tetap ditulis beserta alasannya.
- Loading, error, dan refetch dikoordinasikan Controller layar; komponen anak menerima props murni.

### Phase 5 — Tulis Draft

1. Tulis `<taskdir>/UI.md` persis bagian 1 `templates/ui-template.md`: `status: DRAFT`, `based_on` dari `git rev-parse --short HEAD`.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind ui --taskdir <taskdir>` sampai `PASS`, lalu self-test semantik bagian 2 butir 5–8 template.
3. Commit: `git add <taskdir>/UI.md` lalu `docs(<slug>): draft UI.md` (revisi berikutnya: `docs(<slug>): revise UI.md`).

### Phase 6 — Approval User

1. Sajikan mockup, hierarki P1–P3, enam cabang per layar, dan pemetaan data.
2. `AskUserQuestion`: *Setujui desain* · *Revisi (sebut poinnya)* · *Hentikan*.
3. **Setuju** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py approve --taskdir <taskdir> --row UI --answer "<jawaban user apa adanya>"`.
4. **Revisi** → `chain.py revisions --taskdir <taskdir> --row UI` (plafon 2). Di bawah plafon → perbarui, validasi, commit `revise`, ajukan ulang. Plafon habis → hentikan, sajikan poin penolakan berurutan, serahkan ke `frontend:lead` Phase 8 (klarifikasi lingkup: amandemen akar, atau `chain.py abandon`).

## Guardrails

- **REKAM `based_on`**: frontmatter memuat `based_on: <sha 7 digit> (<tanggal>)` saat berkas ditulis.
- **SIX STATES MANDATORY**: validator menolak layar (blok enam `ST-{n}`) yang tidak memuat keenam cabang tepat sekali; cabang yang tidak dirancang lolos ke produksi tanpa penanganan.
- **STATE SCOPE SENTRAL**: dilarang merancang query atau mutasi terisolasi di komponen anak.
- **TOKEN DARI PROFIL**: warna, spacing, radius, tipografi dari `visual.md`; literal tanpa token dicatat sebagai keputusan eksplisit.
- **PLATFORM FROM ADAPTER**: aturan mobile untuk repo web, atau sebaliknya, adalah cacat.
- **NO CODE IN DESIGN**: dilarang membuat, mengubah, atau menghapus berkas di `src/`.
- **PENELUSURAN LEWAT DISPATCH**: sapuan di atas kuota milik `code-explorer`.
- **RATIONALIZATION PREVENTION**:
  - "Empty dan error state nanti saja saat implementasi" — tanpa `ST-{n}`, `contract` tidak punya kriteria untuk dipikul dan brief tidak mengerjakannya.
  - "User sudah bilang oke di chat, saya set APPROVED" — approval hanya lewat `chain.py approve`.
  - "Skeleton cukup spinner" — spinner menggeser layout saat konten tiba.
  - "Warna ini lebih bagus dari token repo" — preferensi pribadi bukan konvensi repo.
  - "Satu grep lagi untuk memastikan komponennya" — kuota mekanis.

## Output [REQUIRED]

Desain disetujui — tutup satu baris: `UI — APPROVED @ <sha konten> · <n> layar · <n> ST · akar SC <daftar> — lanjut ke frontend:contract di main loop.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### UI — <MENUNGGU KEPUTUSAN | TERTAHAN>
- **Draft**: UI.md @ <sha> · validator <PASS | FAIL>
- **Plafon revisi**: <n>/2
- **Rute**: <menunggu jawaban user | frontend:lead Phase 8>
```

## Failure path

1. **User menolak seluruh opsi**: minta preferensi spesifik, ulangi Phase 3.
2. **Token visual absen dari profil**: tanyakan ke user nilai yang dipakai dan catat sebagai keputusan eksplisit; sarankan `frontend:profile` REFRESH.
3. **Commit gagal** (hook, lock): perbaiki penyebab dan ulangi sebelum approval diajukan.
4. **Kebutuhan data layar tidak ada di FLOW**: tanyakan ke user; tambahannya kemungkinan menuntut `chain.py reopen --row FLOW` lewat lead.
5. **Adapter tidak ditemukan**: hentikan; batasan platform tidak boleh ditebak.

## STYLE

- Imperatif aktif; mockup ASCII rapi; hierarki P1–P3 eksplisit.
- Istilah desain dan aksesibilitas baku; nilai token disebut dengan nama tokennya.

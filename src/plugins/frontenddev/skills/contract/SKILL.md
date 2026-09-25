---
name: contract
description: Dipanggil frontenddev:lead pada setiap lane non-MINOR sesudah hop FLOW/UI yang dijadwalkan tercentang - merancang data contract backend dan arsitektur layer 5-tier ke CONTRACT.md, lolos contract-reviewer dan approval user, sebelum brief implementasi dipecah plan
user-invocable: false
---

## THE IRON LAW

- `CONTRACT.md` lahir dan di-commit `DRAFT`; `APPROVED` hanya ditulis `chain.py approve --row CONTRACT` sesudah jawaban eksplisit user di `AskUserQuestion`. Dilarang menulis `APPROVED` dengan tangan.
- Draft diajukan ke user hanya sesudah `validate_doc.py --kind contract` `PASS` **dan** ronde `contract-reviewer` terakhir `PASS` atas konten yang persis sama.
- Presentasi tidak pernah mengonsumsi DTO response; navigasi, toast, dan dialog tidak pernah di API layer.
- Tiap `SC-{n}` aktif `TASK.md`, tiap `DD-{n}` `FLOW.md`, dan tiap `ST-{n}` `UI.md` dipikul minimal satu `AC-{n}`; SC gugur (`~~…~~ — gugur: <alasan>`) tidak dipikul dan dilarang disebut di kolom *Sumber* AC.
- Penamaan dan idiom layer dari adapter stack repo; dilarang membuat atau mengubah berkas di `src/`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/contract/scripts/check_preconditions.py --taskdir <taskdir>`.
2. `PASS` (9/9): lanjut. `FAIL`: hentikan dan remediasi — akar tidak sah atau `sections` kosong → kembali ke `frontenddev:lead`; hop `FLOW`/`UI` belum tercentang atau berubah sesudah disetujui → gate pemiliknya atau `chain.py reopen` lewat lead; `CONTRACT.md` sudah `APPROVED` → gate ini tuntas, revisi hanya lewat `chain.py reopen --row CONTRACT`; profil/adapter → `frontenddev:profile`; tree kotor yang menurut skrip seluruhnya artefak taskdir ini (draft tertunda sesi lalu) → `review_round.py status --ready --gate contract` exit 0 → commit lewat `review_round.py commit` sebagai `draft`/`revise CONTRACT.md` (Phase 6 butir 1), lalu ulangi prasyarat; selain itu **jangan commit** — lanjutkan dari Phase 5 butir 2; kotoran lain → laporkan ke user. `WARN` `CONTRACT.md` tertunda (`DRAFT`) → ikuti tindakannya: ronde terakhir `PASS` atas konten itu → tanyakan ke user: lanjutkan draft itu atau tulis ulang; belum layak diajukan → perbaiki + ronde reviewer dulu, tanpa commit.
3. `Terselesaikan: sections=` adalah cakupan dari `TASK.md`; pakai apa adanya.
4. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `review_round.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`; `contract-template.md` = `${CLAUDE_PLUGIN_ROOT}/skills/contract/templates/contract-template.md`; `adapter` = `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`. Di `dispatcher/*.md` dan `references/*.md`, `«nama»` berarti path absolut dari peta ini.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — taskdir aktif.
- `feature_name` — string — `[REQUIRED]` — modul/fitur yang dirancang.
- `tier_architecture_mode` — string — default `"strict_5_tier"` — `strict_5_tier` | `colocated_controller_vm` | `service_only`; pilihan akhir tetap keputusan user di Phase 4.
- `query_key_factory_prefix` — string — default `""` — nama konstanta factory key (misal `ORDER_KEYS`).

## Workflow

### Phase 0 — Serap Hulu & Profil

- Baca `TASK.md` (`SC-{n}`, `## Out of Scope` sebagai plafon endpoint/DTO/layer, `finding_source`/`findings`), lalu `FLOW.md`/`UI.md` sesuai `sections` — keduanya `APPROVED` dan utuh, dijamin skrip.
- **Re-entry** (hop CONTRACT `[~]`): sumber perubahan dibaca dari disk, bukan ingatan sesi — alasan `reopen` di badan commit (`git log -1 --format=%B -- <taskdir>/TASK.md`), `REVIEW.md`, `.explore/closing-verification.md`, dan `## Triase` tiap `report-<NN>.md` untuk berkas yatim. Files Touched wajib mencakup union `files_touched` **seluruh** brief, termasuk `DONE`/`BLOCKED` (Check E menagihnya); pada eskalasi dari `HOTFIX_MINOR`, berkas brief `DONE` lama ikut dimasukkan. AC yang *Sumber*-nya menyebut SC yang kini gugur → revisi (buang token itu, atau buang AC bila tak memikul apa pun lagi) — `validate_doc.py` menolaknya.
- Baca `.claude/profile/frontenddev/index.json` (`stack`), `stack.md`, `surface-map.md`, `invariants.md`, `layer-adoption.md`, dan `## Layer taxonomy` adapter `stacks/<stack>.md` — kosakata tabel Layer Shape.

### Phase 1 — Penelusuran Kode

Periksa HTTP client bersama, konvensi query key factory, dan tingkat adopsi View-Model/Controller pada fitur terdekat. **Kuota sapuan gate**: 2 `Glob`+`Grep` dan 2 read ber-offset (≤50 baris). Lintas-layer, relasi (pemanggil Controller, konsumen DTO, pemilik query key), simbol tak ketemu, atau kuota habis → hidrasi `dispatcher/explorer.md` dan dispatch `code-explorer`; pakai pointer `file:baris` laporannya sebagai bukti as-is. `confidence: low` → pertajam objective, ulangi sekali.

### Phase 2 — Kontrak Data & Sapuan Dua Arah

1. **Endpoint**: method, path, query params, request DTO, response DTO, error model, pemetaan status → pesan UI manusiawi.
2. **Sapuan maju**: tiap field response DTO punya jalur ke props `*UI`, atau dinyatakan tidak dipakai di *Decisions Not Taken*.
3. **Sapuan mundur**: tiap Data Demand `FLOW.md` dan tiap kebutuhan `UI.md` terakomodasi field DTO. Kebutuhan yang tidak disediakan backend → fallback lokal eksplisit atau tanyakan ke user sebelum kontrak dikunci.
4. **Cache**: list → factory berparameter `KEY_FACTORY.list(filters)`; mutasi → invalidasi eksplisit sesuai idiom adapter.

### Phase 3 — Layer Shape 5-Tier

Rancang DTO → Service → API layer → View-Model → Controller → Presentation mengacu `references/layer-patterns.md`, dengan path dan penamaan dari `## Layer taxonomy` adapter. Satu tanggung jawab per layer; presentasi hanya memanggil Controller.

### Phase 4 — Opsi Arsitektur

Tawarkan 2–3 opsi (Strict 5-Layer · Colocated Controller & View-Model · Shared Service/Store yang sudah ada) beserta trade-off, rekomendasikan satu, dan minta keputusan user lewat `AskUserQuestion` sebelum menulis berkas. Opsi yang ditolak masuk *Decisions Not Taken*.

### Phase 5 — Tulis Draft & Review Independen

1. Tulis `<taskdir>/CONTRACT.md` persis bagian 1 `templates/contract-template.md`: `status: DRAFT`, `based_on` dari `git rev-parse --short HEAD`, `sections` salinan `TASK.md`. Kolom *Sumber* tiap AC menyebut token `SC-{n}`/`DD-{n}`/`ST-{n}` yang dipikulnya.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind contract --taskdir <taskdir>` sampai `PASS`.
3. Hidrasi `dispatcher/reviewer.md`, jalankan gerbang masuknya (`review_round.py open --gate contract`), dispatch `contract-reviewer` (`subagent_type`: `frontenddev:contract-reviewer`), lalu petakan balikan lewat `### Penanganan Balikan` template itu, termasuk `review_round.py record`. `BLOCKED` apa pun — termasuk yang hanya ber-`BLOCKER [MEKANIS]` — → perbaiki, jalankan `validate_doc.py` sampai `PASS`, lalu ronde 2 menyempit atas konten final. Plafon 2 ronde per putaran dan 8 per taskdir — putaran baru dimulai sesudah draft yang lolos ronde `PASS` di-commit (Phase 6 butir 1, artinya sudah diajukan ke user) atau sesudah `reopen` yang membuka hop CONTRACT; commit draft yang belum pernah `PASS` tidak membuka putaran baru; plafon habis dengan BLOCKER tersisa → hentikan gate, serahkan ke `frontenddev:lead` Phase 8 (klarifikasi lingkup: amandemen akar, atau `chain.py abandon`).

### Phase 6 — Commit Draft & Approval User

1. Commit draft lewat skrip, bukan `git commit` langsung: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py commit --taskdir <taskdir> --gate contract --subject "docs(<slug>): draft CONTRACT.md"` (revisi berikutnya: `docs(<slug>): revise CONTRACT.md`). Skrip menolak kecuali ronde terakhir `PASS` atas konten disk sekarang, lalu meng-commit dengan trailer `Review-Round` — jejak ronde yang bertahan walau laci `.explore/` hilang.
2. Sajikan ringkasan keputusan — endpoint beserta DTO, strategi cache, layer shape, Files Touched, tabel AC beserta sumbernya, verdict reviewer — lalu `AskUserQuestion`: *Setujui kontrak* · *Revisi (sebut poinnya)* · *Hentikan*.
3. **Setuju** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py approve --taskdir <taskdir> --row CONTRACT --answer "<jawaban user apa adanya>"`. Skrip memvonis ulang validator dan ronde reviewer terakhir — wajib `PASS` atas konten final (sidik sama, di luar baris `status:`) **dan** tidak didahului `reopen` hop CONTRACT sesudah ronde itu dibuka; commit `draft`/`revise` sesudah ronde tidak membatalkannya — menulis `APPROVED`, dan mencentang ledger dalam satu commit (badan: `Konten disetujui: <sha>` + `Hop: CONTRACT`).
4. **Revisi** → `chain.py revisions --taskdir <taskdir> --row CONTRACT` (plafon 2). Di bawah plafon → perbarui draft, lalu urutan tetap: `validate_doc.py` `PASS` → ronde reviewer atas konten final (Phase 5 butir 3; putaran baru, 2 ronde) → commit `docs(<slug>): revise CONTRACT.md` → ajukan ulang. Suntingan sesudah ronde `PASS` menuntut ronde baru. Plafon habis → hentikan, sajikan poin penolakan berurutan, serahkan ke `frontenddev:lead` Phase 8 (klarifikasi lingkup: amandemen akar, atau `chain.py abandon`).

## Guardrails

- **REKAM `based_on`**: frontmatter memuat `based_on: <sha 7 digit> (<tanggal>)` saat berkas ditulis — artefak basi tidak dapat dibedakan tanpanya.
- **ISOLASI DTO MUTLAK**: presentasi mengonsumsi `*UI`, bukan DTO response.
- **NO SIDE EFFECTS IN API LAYER**: navigasi, modal, toast hanya di Controller.
- **FACTORY QUERY KEYS ONLY**: dilarang query key raw string.
- **ADAPTER NAMING ONLY**: `use*Page.ts` di repo Svelte atau `*.svelte` di repo React adalah cacat.
- **PENELUSURAN LEWAT DISPATCH**: sapuan di atas kuota milik `code-explorer`.
- **NO CODE IN CONTRACT**: dilarang membuat, mengubah, atau menghapus berkas di `src/`.
- **RATIONALIZATION PREVENTION**:
  - "FLOW sudah disepakati di chat walau belum di-approve" — skrip menagih hop tercentang; kesepakatan chat bukan jejak.
  - "Reviewer bilang PASS, tinggal rapikan redaksi lalu minta approval" — suntingan sesudah ronde `PASS` membatalkan vonisnya; `chain.py approve` menolaknya.
  - "Tipe `any` dulu biar fleksibel" — mematikan typecheck dan meloloskan galat runtime.
  - "View-Model tidak perlu untuk transformasi kecil" — transformasi terpisah dapat diuji tanpa render.
  - "DD ini tidak penting, tidak perlu AC" — `validate_doc.py` menolak DD tanpa AC; kebutuhan hulu tanpa kriteria tidak akan dikerjakan brief mana pun.
  - "Satu grep lagi untuk memastikan query key" — kuota mekanis; sapuan berikutnya milik explorer.

## Output [REQUIRED]

Kontrak disetujui — tutup satu baris: `CONTRACT — APPROVED @ <sha konten> · <n> endpoint · <n> berkas · <n> AC (SC <n>/<n>, DD <n>/<n>, ST <n>/<n> terpikul) · reviewer PASS ronde <n> — lanjut ke frontenddev:plan (mode sesuai `taskdir_state.py`: CONTRACT pada seri pertama, APPEND bila hop BRIEF `[~]`) di main loop.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### CONTRACT — <MENUNGGU KEPUTUSAN | TERTAHAN>
- **Draft**: CONTRACT.md @ <sha> · validator <PASS | FAIL>
- **Reviewer**: <verdict ronde n · n BLOCKER tersisa> | belum berangkat
- **Plafon**: <ronde n/2 (taskdir n/8) · revisi n/2>
- **Rute**: <menunggu jawaban user | frontenddev:lead Phase 8>
```

## Failure path

1. **Hop hulu belum sah**: hentikan di Precondition; kembali ke lead.
2. **DTO backend bertentangan dengan kebutuhan UI**: rancang transformer di Service dan catat di *Decisions Not Taken*; kebutuhan yang tak tertutup sama sekali ditanyakan ke user sebelum draft.
3. **Query key bertabrakan**: namespace unik pada root key.
4. **Commit gagal** (hook, lock): perbaiki penyebab dan ulangi `review_round.py commit` yang sama sebelum approval diajukan; dilarang mengajukan draft yang belum ter-commit.
5. **Baseline verifikasi absen di profil**: arahkan ke `frontenddev:profile`.
6. **Adapter tidak ditemukan**: hentikan; Layer Shape tidak boleh ditulis dengan penamaan tebakan.
7. **State ronde rusak atau hilang** (`review_round.py` FAIL `rusak`/`hilang padahal git mencatat`): pulihkan dari `.bak`; bila `.bak` juga tidak ada dan trailer mencatat ronde → `review_round.py rebuild`, lalu satu ronde baru atas konten sekarang. Dilarang menghapus state atau menulisnya dengan tangan.

## STYLE

- Imperatif aktif; interface TypeScript bebas `any`; dua bagian kanonik `# Architecture` dan `# Execution`.
- Kerangka dokumen hanya di template; dilarang menyalinnya ke sini.

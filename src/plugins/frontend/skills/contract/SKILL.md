---
name: contract
description: Dipanggil frontend:lead pada setiap lane non-MINOR sesudah hop FLOW/UI yang dijadwalkan tercentang - merancang data contract backend dan arsitektur layer 5-tier ke CONTRACT.md, lolos contract-reviewer dan approval user, sebelum brief implementasi dipecah plan
user-invocable: false
---

## THE IRON LAW

- `CONTRACT.md` lahir `DRAFT` dan dicatat `chain.py draft --row CONTRACT` sesudah ronde reviewer `PASS` — tanpa commit: dokumen taskdir diabaikan git dan dicerminkan ke nataflow; `APPROVED` hanya ditulis `chain.py approve --row CONTRACT` sesudah jawaban eksplisit user di `AskUserQuestion`. Dilarang menulis `APPROVED` dengan tangan.
- Draft diajukan ke user hanya sesudah `validate_doc.py --kind contract` `PASS` **dan** ronde `contract-reviewer` terakhir `PASS` atas konten yang persis sama.
- Presentasi tidak pernah mengonsumsi DTO response; navigasi, toast, dan dialog tidak pernah di API layer.
- Tiap `SC-{n}` aktif `TASK.md`, tiap `DD-{n}` `FLOW.md`, dan tiap `ST-{n}` `UI.md` dipikul minimal satu `AC-{n}`; SC gugur (`~~…~~ — gugur: <alasan>`) tidak dipikul dan dilarang disebut di kolom *Sumber* AC.
- Penamaan dan idiom layer dari adapter stack repo; dilarang membuat atau mengubah berkas di `src/`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/contract/scripts/check_preconditions.py --taskdir <taskdir>`.
2. `PASS` (9/9): lanjut. `FAIL`: hentikan dan remediasi — akar tidak sah atau `sections` kosong → kembali ke `frontend:lead`; hop `FLOW`/`UI` belum tercentang atau berubah sesudah disetujui → gate pemiliknya atau `chain.py reopen` lewat lead; `CONTRACT.md` sudah `APPROVED` → gate ini tuntas, revisi hanya lewat `chain.py reopen --row CONTRACT`; profil/adapter → `frontend:profile`; tree kotor → laporkan ke user (dokumen taskdir tidak pernah tampak kotor). `WARN` `CONTRACT.md` tertunda (`DRAFT`) → ikuti tindakannya: ronde terakhir `PASS` atas konten itu → catat lewat `chain.py draft --row CONTRACT` bila belum tercatat (Phase 6 butir 1), lalu tanyakan ke user: lanjutkan draft itu atau tulis ulang; belum layak diajukan → perbaiki + ronde reviewer dulu, tanpa mencatat draft.
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
- **Re-entry** (hop CONTRACT `[~]`): sumber perubahan dibaca dari disk, bukan ingatan sesi — alasan kejadian `reopen` terakhir di `## Riwayat Rantai` `TASK.md`, `REVIEW.md`, `.explore/closing-verification.md`, dan `## Triase` tiap `report-<NN>.md` untuk berkas yatim. Files Touched wajib mencakup union `files_touched` **seluruh** brief, termasuk `DONE`/`BLOCKED` (Check E menagihnya); pada eskalasi dari `HOTFIX_MINOR`, berkas brief `DONE` lama ikut dimasukkan. AC yang *Sumber*-nya menyebut SC yang kini gugur → revisi (buang token itu, atau buang AC bila tak memikul apa pun lagi) — `validate_doc.py` menolaknya.
- Baca `.claude/profile/frontenddev/index.json` (`stack`), `stack.md`, `surface-map.md`, `invariants.md`, `layer-adoption.md`, dan `## Layer taxonomy` adapter `stacks/<stack>.md` — kosakata tabel Layer Shape.

### Phase 1 — Penelusuran Kode

Periksa HTTP client bersama, konvensi query key factory, dan tingkat adopsi View-Model/Controller pada fitur terdekat. **Kuota sapuan gate**: 2 `Glob`+`Grep` dan 2 read ber-offset (≤50 baris). Lintas-layer, relasi (pemanggil Controller, konsumen DTO, pemilik query key), simbol tak ketemu, atau kuota habis → hidrasi `dispatcher/explorer.md` dan dispatch `code-explorer` (`subagent_type`: `frontend:code-explorer`); pakai pointer `file:baris` laporannya sebagai bukti as-is. `confidence: low` → pertajam objective, ulangi sekali.

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
3. Hidrasi `dispatcher/reviewer.md`, jalankan gerbang masuknya (`review_round.py open --gate contract`), dispatch `contract-reviewer` (`subagent_type`: `frontend:contract-reviewer`), lalu petakan balikan lewat `### Penanganan Balikan` template itu, termasuk `review_round.py record`. `BLOCKED` apa pun — termasuk yang hanya ber-`BLOCKER [MEKANIS]` — → perbaiki, jalankan `validate_doc.py` sampai `PASS`, lalu ronde 2 menyempit atas konten final. Plafon 2 ronde per putaran dan 8 per taskdir — putaran baru dimulai sesudah draft yang lolos ronde `PASS` dicatat `chain.py draft` (Phase 6 butir 1, artinya sudah diajukan ke user), sesudah `reopen` yang membuka hop CONTRACT atau hop di atasnya, atau sesudah `chain.py escalate`; draft yang belum pernah `PASS` tidak dapat dicatat; plafon habis dengan BLOCKER tersisa → hentikan gate tanpa mencatat draft, sajikan BLOCKER ke user, serahkan ke `frontend:lead` Phase 8 (plafon habis: taskdir baru atau hentikan).

### Phase 6 — Catat Draft & Approval User

1. Catat draft lewat skrip: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py draft --taskdir <taskdir> --row CONTRACT` (revisi berikutnya: perintah yang sama; draft kedua dan seterusnya dihitung revisi). Skrip menolak kecuali `validate_doc.py` `PASS` dan ronde terakhir `PASS` atas konten disk sekarang, lalu mencatat kejadian `draft` di `## Riwayat Rantai` beserta field `review contract r<n> t<total> PASS <sidik>` — jejak ronde yang bertahan walau laci `.explore/` hilang. Dilarang men-stage atau meng-commit `CONTRACT.md`.
2. Sajikan **ringkasan gerbang**, bukan isi dokumen: baris `CONTRACT.md DRAFT @ <sidik12 keluaran chain.py draft> · <taskdir>/CONTRACT.md · <n> endpoint · <n> AC · <n> berkas`, lalu 3–4 kalimat — opsi arsitektur terpilih dan layer shape-nya, endpoint atau DTO yang baru atau berubah, strategi cache beserta asumsi default yang dipakai, dan verdict reviewer dalam satu frasa (mis. `PASS ronde 1 · 2 ADVISORY`). Tabel DTO, Files Touched, dan tabel AC tetap di berkas; dilarang menyalinnya ke chat. Lalu `AskUserQuestion`: *Setujui kontrak* · *Revisi (sebut poinnya)* · *Hentikan*. User meminta rincian → sajikan seksi yang diminta saja, lalu ajukan ulang pertanyaan yang sama.
3. **Setuju** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py approve --taskdir <taskdir> --row CONTRACT --answer "<jawaban user apa adanya>"`. Skrip memvonis ulang validator dan ronde reviewer terakhir — wajib `PASS` atas konten final (sidik sama, di luar baris `status:`) **dan** tidak didahului `reopen` hop CONTRACT sesudah ronde itu dibuka, dan konten disk sama dengan draft yang terakhir dicatat — lalu menulis `APPROVED`, mencentang ledger `@ APPROVED <sidik12>`, dan mencatat kejadian `approve CONTRACT` (sidik, ronde reviewer, sidik `SC-{n}`, jawaban user) di `## Riwayat Rantai`. Approve PASS → jalankan prosedur `lead/references/nataflow-sync.md` (`--taskdir <taskdir>`); segmennya masuk baris penutup, dan `nataflow GAGAL` tidak membatalkan approval.
4. **Revisi** → `chain.py revisions --taskdir <taskdir> --row CONTRACT` (plafon 2; `draft` ulang dan amandemen akar tidak me-reset hitungan). Di bawah plafon → perbarui draft, lalu urutan tetap: `validate_doc.py` `PASS` → ronde reviewer atas konten final (Phase 5 butir 3; putaran baru, 2 ronde) → `chain.py draft --row CONTRACT` (revisi ketiga ditolak skrip) → ajukan ulang. Suntingan sesudah ronde `PASS` menuntut ronde baru. Plafon habis → hentikan, sajikan poin penolakan berurutan, serahkan ke `frontend:lead` Phase 8 (plafon habis: taskdir baru atau hentikan).

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

Kontrak disetujui — tutup satu baris: `CONTRACT — APPROVED @ <sha konten> · <n> endpoint · <n> berkas · <n> AC (SC <n>/<n>, DD <n>/<n>, ST <n>/<n> terpikul) · reviewer PASS ronde <n> · nataflow <segmen> — lanjut ke frontend:plan (mode sesuai `taskdir_state.py`: CONTRACT pada seri pertama, APPEND bila hop BRIEF `[~]`) di main loop.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### CONTRACT — <MENUNGGU KEPUTUSAN | TERTAHAN>
- **Draft**: CONTRACT.md @ <sidik12 | belum tercatat> · validator <PASS | FAIL>
- **Reviewer**: <verdict ronde n · n BLOCKER tersisa> | belum berangkat
- **Plafon**: <ronde n/2 (taskdir n/8) · revisi n/2>
- **Rute**: <menunggu jawaban user | frontend:lead Phase 8>
```

## Failure path

1. **Hop hulu belum sah**: hentikan di Precondition; kembali ke lead.
2. **DTO backend bertentangan dengan kebutuhan UI**: rancang transformer di Service dan catat di *Decisions Not Taken*; kebutuhan yang tak tertutup sama sekali ditanyakan ke user sebelum draft.
3. **Query key bertabrakan**: namespace unik pada root key.
4. **`chain.py draft` gagal** (validator, ronde belum `PASS`, konten sama dengan draft tercatat, plafon revisi): perbaiki penyebab dan ulangi sebelum approval diajukan; dilarang mengajukan draft yang belum tercatat.
5. **Baseline verifikasi absen di profil**: arahkan ke `frontend:profile`.
6. **Adapter tidak ditemukan**: hentikan; Layer Shape tidak boleh ditulis dengan penamaan tebakan.
7. **State ronde rusak atau hilang** (`review_round.py` FAIL `rusak`/`hilang padahal ## Riwayat Rantai mencatat`): pulihkan dari `.bak`; bila `.bak` juga tidak ada dan Riwayat mencatat ronde → `review_round.py rebuild`, lalu satu ronde baru atas konten sekarang. Dilarang menghapus state atau menulisnya dengan tangan.

## STYLE

- Imperatif aktif; interface TypeScript bebas `any`; dua bagian kanonik `# Architecture` dan `# Execution`.
- Kerangka dokumen hanya di template; dilarang menyalinnya ke sini.

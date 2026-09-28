---
name: ux-design
description: Dipanggil frontend:lead ketika sections TASK.md memuat flow - merancang alur pengguna, rute navigasi, deep-link, penanganan batal, dan data demands ke FLOW.md yang disetujui user di Gate Flow, sebelum mockup UI atau kontrak teknis dirancang
user-invocable: false
---

## THE IRON LAW

- `FLOW.md` lahir dan di-commit `DRAFT`; `APPROVED` hanya ditulis `chain.py approve --row FLOW` sesudah jawaban eksplisit user di `AskUserQuestion`. Dilarang menulis `APPROVED` dengan tangan.
- Draft diajukan ke user hanya sesudah `validate_doc.py --kind flow` `PASS`.
- Tiap perjalanan menutup lima dimensi — entry, maju, kembali/batal, cabang, data demands — dan tiap Data Demand ber-ID `DD-{n}`.
- Konvensi rute dari adapter stack dan navigasi aktual repo, bukan dari stack lain; dilarang membuat atau mengubah berkas di `src/`.

## Precondition [REQUIRED]

1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/ux-design/scripts/check_preconditions.py --taskdir <taskdir>`.
2. `PASS` (9/9): lanjut. `FAIL`: hentikan dan remediasi — akar tidak sah atau `sections` tanpa `flow` → kembali ke `frontend:lead`; `FLOW.md` sudah `APPROVED` → gate ini tuntas, revisi hanya lewat `chain.py reopen --row FLOW`; profil/adapter → `frontend:profile`; tree kotor yang menurut skrip seluruhnya artefak taskdir ini (draft tertunda sesi lalu) → commit dulu sebagai `draft`/`revise FLOW.md` (Phase 4 butir 3), lalu ulangi prasyarat; kotoran lain → laporkan ke user. `WARN` `FLOW.md` tertunda (`DRAFT`) → tanyakan ke user: putuskan draft itu, revisi, atau tulis ulang.
3. Konflik rute dengan alur yang sudah ada tidak dapat divonis skrip; periksa di Phase 0.
4. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`.

## Parameter [REQUIRED]

- `taskdir` — string — `[REQUIRED]` — taskdir aktif.
- `feature_name` — string — `[REQUIRED]` — fitur/modul yang alurnya dirancang.
- `allow_modal_flows` — boolean — default `true` — izinkan alternatif modal/bottom-sheet.
- `deep_link_prefix` — string — default `""` — skema deep-link (misal `myapp://orders/`).
- `strict_back_guard` — boolean — default `true` — wajibkan intersep konfirmasi batal pada form kotor.

## Workflow

### Phase 0 — Orientasi Navigasi & Profil

- Baca `surface-map.md` profil dan `## UI & navigation surface` adapter `stacks/<stack>.md`: `react-vite` (React Router/TanStack, `/:id`/`$id`, loader guard) · `react-native` (Expo Router `app/**` atau React Navigation, `scheme`) · `sveltekit` (`src/routes/**`, `[id]`, grup `(app)`) · `svelte-vite` (library router repo).
- Telusuri berkas rute terdekat via read ber-offset (≤30 baris) untuk penamaan parameter nyata. **Kuota sapuan gate**: 2 `Glob`+`Grep` dan 2 read ber-offset. Relasi lintas-berkas (pemilik layout, konsumen param), simbol tak ketemu, atau kuota habis → hidrasi `dispatcher/explorer.md` dan dispatch `code-explorer` (`subagent_type`: `frontend:code-explorer`); pakai pointer `file:baris` laporannya.
- Parameter rute ber-query string atau filter kompleks → dokumentasikan format deserialisasi dan default-nya.

### Phase 1 — Intent & Klarifikasi

- Intent: `"Pengguna ingin <tujuan> melalui <rentang layar> dengan hasil akhir <kondisi sukses>."` — `<kondisi sukses>` diturunkan dari `SC-{n}` `TASK.md`; layar yang disebut `## Out of Scope` dilarang masuk rentang. Perjalanan yang tidak memikul satu pun `SC-{n}` adalah perluasan lingkup — tanyakan ke user.
- Ambiguitas alur bisnis, hak akses, atau percabangan → maksimal 3 pertanyaan sekuensial lewat `AskUserQuestion`, masing-masing dengan opsi konkret.

### Phase 2 — Lima Dimensi Perjalanan

| # | Dimensi | Yang dikunci di `FLOW.md` |
|---|---|---|
| 1 | Entry Points | pemicu masuk & parameter rute bertipe |
| 2 | Forward Transitions | pemicu maju & payload antar layar |
| 3 | Back & Cancel | kembali hardware/software/browser, dirty guard (mekanisme dari adapter: `useBlocker`, `beforeNavigate`, `beforeRemove`, `beforeunload`) |
| 4 | Flow Branches | sukses, gagal validasi, offline/timeout, permission, retry |
| 5 | Data Demands | field yang dibutuhkan tiap layar, ber-ID `DD-{n}` |

Mutasi asinkron menuntut cabang timeout, error koneksi, validasi server, dan *Coba Lagi*. `react-native` menuntut hardware back Android dan swipe-back iOS; `sveltekit` menuntut pembagian data `load` server vs client.

### Phase 3 — Opsi Alur

Tawarkan 2–3 opsi mengacu `references/ux-patterns.md` — Direct/Modal · Multi-Step/Wizard · Seamless In-Place — beserta trade-off, rekomendasikan satu, dan minta keputusan user lewat `AskUserQuestion`. Opsi yang ditolak masuk seksi 6.

### Phase 4 — Tulis Draft

1. Tulis `<taskdir>/FLOW.md` persis bagian 1 `templates/flow-template.md`: `status: DRAFT`, `based_on` dari `git rev-parse --short HEAD`, baris **Akar** menyebut `SC-{n}` yang dilayani.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind flow --taskdir <taskdir>` sampai `PASS`, lalu self-test semantik bagian 2 butir 6–9 template.
3. Commit: `git add <taskdir>/FLOW.md` lalu `docs(<slug>): draft FLOW.md` (revisi berikutnya: `docs(<slug>): revise FLOW.md`).

### Phase 5 — Approval User

1. Sajikan ringkasan: titik masuk, rute utama beserta parameternya, penanganan batal/dirty, cabang error, dan tabel Data Demands.
2. `AskUserQuestion`: *Setujui alur* · *Revisi (sebut poinnya)* · *Hentikan*.
3. **Setuju** → `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py approve --taskdir <taskdir> --row FLOW --answer "<jawaban user apa adanya>"`. Approve PASS → jalankan prosedur `lead/references/nataflow-sync.md` (`--taskdir <taskdir>`); segmennya masuk baris penutup, dan `nataflow GAGAL` tidak membatalkan approval.
4. **Revisi** → `chain.py revisions --taskdir <taskdir> --row FLOW` (plafon 2; `draft` ulang dan amandemen akar tidak me-reset hitungan). Di bawah plafon → perbarui, validasi, commit `revise`, ajukan ulang. Plafon habis → hentikan, sajikan poin penolakan berurutan, serahkan ke `frontend:lead` Phase 8 (plafon habis: taskdir baru atau hentikan).

## Guardrails

- **REKAM `based_on`**: frontmatter memuat `based_on: <sha 7 digit> (<tanggal>)` saat berkas ditulis.
- **NO CODE IN FLOW**: dilarang membuat, mengubah, atau menghapus berkas di `src/`.
- **ANTI ASUMSI RUTE**: nama rute dan parameter dari navigasi aktual repo dan adapter, berjangkar `file:baris`.
- **DIRTY STATE MANDATORY**: tiap form punya penanganan batal eksplisit.
- **DATA DEMANDS ONLY**: dilarang menulis interface TypeScript atau styling di `FLOW.md` — itu milik `contract` dan `ui-design`.
- **PLATFORM FROM ADAPTER**: hardware back untuk repo web atau `beforeunload` untuk React Native adalah cacat.
- **PENELUSURAN LEWAT DISPATCH**: sapuan di atas kuota milik `code-explorer`.
- **RATIONALIZATION PREVENTION**:
  - "Alurnya sudah jelas, langsung UI saja" — tanpa FLOW, cabang kembali/batal/timeout terlewat.
  - "User bilang lanjut di chat, saya set APPROVED sendiri" — approval hanya lewat `chain.py approve` dengan jawaban `AskUserQuestion`; status tulisan tangan ditolak validator hilir sebagai drift.
  - "Data demands ditentukan nanti saat DTO" — data demands adalah kebutuhan pengguna; tanpa `DD-{n}`, `contract` tidak punya yang harus dipikul.
  - "Parameter rute pasti standar" — tiap repo punya konvensi sendiri.
  - "Satu grep lagi untuk memastikan nama rute" — kuota mekanis.

## Output [REQUIRED]

Alur disetujui — tutup satu baris: `FLOW — APPROVED @ <sha konten> · <n> layar · <n> DD · akar SC <daftar> · nataflow <segmen> — lanjut ke frontend:ui-design (bila sections memuat ui) atau frontend:contract di main loop.` Selain itu sajikan blok berikut dan hapus baris bernilai `—`:

```markdown
### FLOW — <MENUNGGU KEPUTUSAN | TERTAHAN>
- **Draft**: FLOW.md @ <sha> · validator <PASS | FAIL>
- **Plafon revisi**: <n>/2
- **Rute**: <menunggu jawaban user | frontend:lead Phase 8>
```

## Failure path

1. **User menolak seluruh opsi alur**: minta preferensi spesifik, perbarui rancangan, ulangi Phase 3.
2. **Konflik rute / parameter duplikat**: sesuaikan namespace segmen dan konfirmasikan ke user.
3. **Commit gagal** (hook, lock): perbaiki penyebab dan ulangi sebelum approval diajukan; dilarang mengajukan draft yang belum ter-commit.
4. **Deep-link menuntut parameter otentikasi yang belum ada di profil**: catat di seksi 6 dan tanyakan ke user.
5. **Adapter tidak ditemukan**: hentikan; konvensi rute tidak boleh ditebak.

## STYLE

- Imperatif aktif; Mermaid valid; tabel Data Demands berbahasa kebutuhan pengguna, bukan skema DTO.
- Tiap parameter URL bertipe dan ber-fallback definitif.

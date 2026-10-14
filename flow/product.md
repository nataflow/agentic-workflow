# Alur Plugin `product`

> Plugin `product` (v0.1.0, `src/plugins/product/.claude-plugin/plugin.json`) menginisiasi produk baru, fitur baru,
> atau improvement fitur menjadi `product/<slug>/CHARTER.md` berisi enam pilar — Purpose, Actors, Business Process,
> Business Rules, Success Criteria, Scope. Tiga skill (`init` sebagai titik masuk, `discover` dan `spec` internal) dan
> dua subagent (`code-scout`, `charter-reviewer`). Kebenaran dijaga skrip stdlib di `skills/_common/`; prosa skill
> hanya mengarahkan. Tanpa hook, tanpa taskdir, tanpa sinkron nataflow.

## Peta Komponen

| Komponen | Path | Peran |
|---|---|---|
| Skill `init` | `src/plugins/product/skills/init/SKILL.md` | titik masuk: ruang kerja, mode, guard konteks minimum, verifikasi mode, duplikat, slug |
| Prasyarat init | `skills/init/scripts/check_preconditions.py` | root sah (bukan home/root fs), berkas plugin, `workspace` EMPTY/CODEBASE, `mode_diizinkan`, `charter_terbuka` |
| Guard | `skills/init/references/konteks-minimum.md` | tiga butir per mode, cara bertanya berbentuk pilihan, larangan lolos dengan asumsi |
| Skill `discover` | `skills/discover/SKILL.md` | `charter.py new`, scout `PETA`, tanya-jawab per pilar, konfirmasi, `charter.py close` |
| Kerangka & panduan | `skills/discover/templates/charter-skeleton.md`, `skills/discover/references/elicitation-guide.md` | kerangka kanonik catatan; urutan pilar dan bank pertanyaan per mode |
| Dispatch scout | `skills/discover/dispatcher/scout.md` | slot `mode` (`CEK_FITUR`/`PETA`), `fokus`, plafon dispatch |
| Skill `spec` | `skills/spec/SKILL.md` | kartu enam pilar, review, approve, reopen, cancel |
| Template kartu | `skills/spec/templates/charter-template.md` | bentuk kartu per mode, aturan validasi, contoh `IMPROVEMENT` |
| Dispatch reviewer | `skills/spec/dispatcher/reviewer.md` | slot `sidik`, `round`, penanganan balikan |
| State machine | `skills/_common/charter.py` | `guard`, `state`, `new`, `check`, `close`, `review`, `revise`, `approve`, `commit`, `reopen`, `cancel` |
| Validator | `skills/_common/validate_doc.py` | `--kind notes` (catatan elisitasi) dan `--kind charter` (kartu) |
| Pustaka | `skills/_common/charter_lib.py` | deteksi ruang kerja, guard, sidik, frontmatter, git |
| Subagent `code-scout` | `agents/code-scout.md` | read-only, sonnet, kuota 12 pemanggilan; balikan `## Product Scout` |
| Subagent `charter-reviewer` | `agents/charter-reviewer.md` | read-only, sonnet; balikan `## Charter Review` bersidik |

## Alur Utama

```
/product:init
 ├─ check_preconditions.py ── FAIL (home, root fs, plugin rusak) ─────────────→ berhenti
 ├─ charter.py state ── charterdir terbuka cocok ────────────────────────────→ discover | spec
 ├─ wilayah ── satu perubahan kecil / bug ───────────────────────────────────→ analyst:intake | engineer
 ├─ mode: EMPTY → NEW_PRODUCT · CODEBASE → NEW_FEATURE | IMPROVEMENT (tanya bila ragu)
 ├─ guard: charter.py guard ── FAIL ×2 ──────────────────────────────────────→ INIT — TERTAHAN
 ├─ (codebase) code-scout CEK_FITUR ── mode tidak cocok → tanya → guard ulang
 ├─ duplikat (state --all)
 └─ slug, judul, requester ──→ product:discover
                                 ├─ charter.py new (guard + mode × ruang kerja ulang) → ELICITATION
                                 ├─ (codebase) code-scout PETA (IMPROVEMENT: 3 fokus paralel)
                                 ├─ giliran ≤ 3 pertanyaan, simpan tiap giliran (plafon 6) ── TERTAHAN
                                 ├─ konfirmasi fakta (Asumsi → fakta)
                                 └─ charter.py close → DRAFT ──→ product:spec
                                                                  ├─ kartu enam pilar
                                                                  ├─ validate_doc.py --kind charter
                                                                  ├─ charter-reviewer → charter.py review (≤ 2 ronde)
                                                                  ├─ charter.py commit --stage draft
                                                                  └─ AskUserQuestion
                                                                       ├─ Setujui → charter.py approve → APPROVED
                                                                       ├─ Revisi → charter.py revise (≤ 3)
                                                                       ├─ Kembali ke elisitasi → reopen --to elicitation
                                                                       └─ Tahan
```

## Artefak & Siklus Status

| Artefak | Lokasi | Penulis |
|---|---|---|
| `CHARTER.md` | `product/<slug>/` di root git, atau cwd tanpa git | frontmatter: `charter.py`; kartu: `spec`; catatan: `discover` (Konteks Awal dan Permintaan Asli: `charter.py new`) |
| `review.md` | `product/<slug>/` | hanya `charter.py review --report` |

Status tersimpan dan keadaan turunan:

```
            new                 close                       review PASS @sidik         approve
   (tidak ada) ──→ ELICITATION ──────→ DRAFT ──────────────────────────→ REVIEW ──────────→ APPROVED
                        ↑                │  ↑  suntingan kartu/catatan ─┘                     │
                        │                │  └─ revise (≤3) / BLOCKED                          │ suntingan
                        └──── reopen --to elicitation (log "Dibuka ulang") ◄──────────────────┤
                                         ↑                                                     ↓
                                         └──────────── reopen --to draft ◄────────────────── DRIFT
   cancel (APPROVED butuh --force) → CANCELLED
```

Sidik:

| Sidik | Atas | Dimateraikan | Dipakai |
|---|---|---|---|
| `context_hash` | `### Konteks Awal` | `new` | validator notes check 3 |
| `request_hash` | `### Permintaan Asli` | `new` | validator notes check 4 |
| `elicit_hash` | `## Catatan Elisitasi` + `mode` | `close` | `check --gate spec`, `review`, `approve` |
| `review` `PASS @<kartu>/<catatan>` | kartu dan catatan | `review` | keadaan `REVIEW`, `approve` |
| `approved_hash` | body utuh + `mode` | `approve` | keadaan `DRIFT`, validator charter check 11 |

## Mode

| | `NEW_PRODUCT` | `NEW_FEATURE` | `IMPROVEMENT` |
|---|---|---|---|
| Ruang kerja | EMPTY (CODEBASE dengan `--confirm-workspace`) | CODEBASE | CODEBASE |
| Label Konteks Awal | Untuk siapa · Masalah utama · Domain | Pengguna · Yang belum bisa dilakukan · Area | Yang terdampak · Yang salah atau kurang · Fitur |
| Scout | tidak pernah | `CEK_FITUR`; `PETA` Actors (+ Business Process) | `CEK_FITUR`; `PETA` Actors, Business Process, Business Rules |
| Actors | tanpa tanda | `[ADA]`/`[BARU]` | `[ADA]`/`[BARU]` |
| Business Process | satu daftar | satu daftar | `### Kondisi Sekarang` (≥ 1 bukti) + `### Kondisi Target` |
| Business Rules | tanpa tanda | tanpa tanda | `[TETAP]`/`[UBAH]`/`[BARU]` |
| `path:baris` | dilarang (catatan dan kartu) | boleh, wajib ada | wajib di Kondisi Sekarang, wajib ada |

## Handoff Lintas Plugin

- **Masuk**: tidak ada; `/product:init` dipanggil user atau model dari gagasan mentah.
- **Keluar (disiapkan, belum aktif)**: butir `S<n>` charter `APPROVED` dibawa satu per satu ke `/analyst:intake`.
  ID `S<n>` divalidasi unik dan tanpa celah atas gabungan Termasuk dan butir yang dibatalkan di Tidak Termasuk (ID
  dibawa serta), dan `spec` dilarang menomori ulang butir yang pernah disetujui.
- **Gerbang engineer**: `hooks/gate_text.py` backend dan frontend mengecualikan `/product:*`, sehingga mode codebase
  berjalan di repo backend/frontend tanpa dicegat.

## Titik Gagal & Pemulihan

| Gejala | Keluaran | Pemulihan |
|---|---|---|
| Permintaan terlalu umum | `GUARD FAIL` / `NEW FAIL: konteks minimum` | tanya butir yang disebut; dua putaran tanpa jawaban → `INIT — TERTAHAN` |
| Mode codebase di folder kosong | `NEW FAIL: … butuh codebase` | pakai `NEW_PRODUCT`, atau jalankan dari repo yang dikembangkan |
| `NEW_PRODUCT` di codebase | `NEW FAIL: … --confirm-workspace` | konfirmasi user, atau pakai mode codebase |
| Ruang kerja home / root fs | check 3 `FAIL` | buat folder proyek |
| Pilar belum terjawab saat close | `CLOSE FAIL` + laporan validator; berkas dikembalikan | lanjutkan tanya-jawab |
| Catatan disunting sesudah close | check 5 / `REVIEW FAIL` / `APPROVE FAIL` segel | pulihkan, atau `reopen --to elicitation` |
| Konteks Awal / Permintaan Asli disunting | validator notes check 3/4 | pulihkan dari git; konteks berubah total → charter baru |
| Sidik reviewer ≠ disk | `REVIEW FAIL` | dispatch ulang dengan `sidik` baru |
| Plafon ronde / revisi habis | `ronde=habis` / `REVISE FAIL` | revisi, kembali ke elisitasi, atau cancel |
| Scout gagal dua kali di `IMPROVEMENT` | `DISCOVER — TERTAHAN` | ulang sesi; Kondisi Sekarang wajib berbukti |
| Commit gagal | exit 3 + perintah commit manual | bereskan hook/gpg, commit dengan perintah tercetak |
| `CHARTER.md` bukan UTF-8 | `BROKEN` / FAIL rapi | pulihkan dari git |

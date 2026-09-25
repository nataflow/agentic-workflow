# Langkah 8.B — Sisa Temuan backenddev (B1–B19), versi detail

Pecahan detail seksi **8.B backenddev** di `ISSUES.md`. ID dan judul item sama dengan `ISSUES.md`. Semua path di berkas ini ditulis dari root repo (`/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow`). Nomor baris mengacu commit `34684ee`.

## Tujuan

Menutup 19 temuan backenddev yang tersisa setelah Langkah 1–7: kontrak `issues/` dan severity yang bentrok, parameter skrip prasyarat yang diterima tapi tidak divalidasi, crash/vonis salah di beberapa skrip, instruksi yang saling bertentangan, dan beban context rantai planning.

## Urutan pengerjaan

| Tahap | Item | Alasan |
|---|---|---|
| 1. Teks murah, risiko rendah | B17, B8, B15, B19 (koreksi klaim), B5, B11, B7 | Hanya markdown (plus satu guard kecil di skrip). Bisa langsung. |
| 2. Keputusan desain dulu | B1 + B2 (bareng L2.1), B9, B18 | Butuh keputusan user sebelum teks ditulis (lihat "Keputusan yang dibutuhkan"). |
| 3. Skrip + test | B4, B16, B10, B14, B6, B3 | Kerjakan sesudah infrastruktur test L6.1 ada. Idealnya sesudah helper `_common` L5.5, atau helper B3/B6 dijadikan cikal bakal L5.5. |
| 4. Konvensi commit | B13 | Bareng L3.6 (pesan commit reviewer), karena keduanya memakai `commit_convention`. |
| 5. Terbesar | B12 | Butuh parser frontmatter/heading L5.1/L5.9 dan keputusan B9. |

## Dependensi dengan langkah lain

| Item | Bergantung pada / terkait |
|---|---|
| B1, B2 | **L2.1** (reviewer meng-commit `issues/README.md`), **L3.6** (commit reviewer), **X1/X2** (path berkas dioper ke agent lewat slot hidrasi) |
| B3 | **L5.2** (pola taskdir debug), **L5.5** (helper `_common`), **L1.1** (`--profile-dir` → konstanta `PROFILE_DIR`), **L6.1** (test) |
| B4 | **L5.5**, **L6.1** |
| B6 | **L5.5** (`dirty_paths` dengan `-z`), **L6.1**; pola filter yang sama juga di analyst/task/tech-lead |
| B10 | **L5.1** (`_frontmatter()` plan masih mencari `risk:` di seluruh isi) |
| B11 | **L2.7** (state plan di `.explore/`) |
| B12 | **L5.1**, **L5.9**, **L5.6** (false positive placeholder), **L6.1**, **B9** |
| B13 | **L3.6** |
| B14 | **L5.5** (path `.gemini`), **L6.3** (cek integritas berkas plugin pindah ke lint) |
| B16 | **L5.4** (parser chain bersama) |
| B17 | **L6.3** (lint bisa menegakkan jumlah baris `## Commands`) |
| B19 | **L3.4** (hook PreToolUse) |

## Estimasi

| Item | Estimasi | Item | Estimasi |
|---|---|---|---|
| B1 | 3 jam | B11 | 1 jam |
| B2 | 2 jam | B12 | 2–3 hari |
| B3 | 1–1,5 hari | B13 | 3–4 jam |
| B4 | 2 jam | B14 | 2 jam |
| B5 | 1 jam | B15 | 2 jam |
| B6 | 4 jam | B16 | 2 jam |
| B7 | 2 jam | B17 | 30 menit |
| B8 | 1 jam | B18 | 2 jam |
| B9 | 1 jam | B19 | 30 menit (klaim); hook ikut L3.4 |
| B10 | 2 jam | **Total** | **±7–8 hari kerja** |

## Keputusan yang dibutuhkan dari user

1. **B2**: severity pelanggaran `## Invariants` profil dan berkas di luar `## File scope`. Usulan: keduanya `P1` di semua berkas.
2. **B1**: kolom `File` di index berisi path relatif root repo untuk kedua jenis laporan (usulan), atau nama berkas saja.
3. **B9**: alat ukur `PRD_CONVERSION` memakai test bernama/diff, bukan `AC-{n}` (usulan opsi A).
4. **B10**: muara eskalasi jalur RCA (usulan: kembali ke `tech-lead`, yang memutuskan lane ulang) dan cara TASK `DEFECT_RCA` naik ke rantai ber-PRD.
5. **B15 (e)**: model amandemen `TASK.md` oleh gerbang (satu titik atau dua pemicu).
6. **B3**: `--stack` document-api dihapus (stack wajib dari profil), `--symptom` debug dihapus, `--profile-dir` profile dihapus.
7. **B13**: tambah field terstruktur `commit_template` di `index.json`.
8. **B14**: `test: tidak berlaku` dianggap FAIL di tech-lead.

## Catatan implementasi (2026-09-25)

Keputusan user: kedelapan usulan dipakai — **B2** invariant dan scope `P1` · **B1** kolom `File` path relatif root · **B9** opsi A · **B10** re-route (a), amandemen TASK di taskdir yang sama · **B15 (e)** dua pemicu (ditambah re-route RCA dari B10 sebagai pemicu ketiga) · **B3** `--stack`/`--symptom`/`--profile-dir` dihapus · **B13** `commit_template` · **B14** `test: tidak berlaku` FAIL. Semuanya tercatat di Log Keputusan `ISSUES.md`; keputusan 05-1 ("document-api bebas bila `--stack` diisi") dicabut oleh B3.

Selesai: B1–B19. Commit: `30dacff` (tahap 1), `070b6d1` (tahap 2), `ae4e096` (tahap 3), `b04d4be` (B13), `a593641` + `451294e` (B12). Hasil: `pytest` 1069 lulus, 1 gagal — `test_profile_paths[backenddev]`, kegagalan lama di luar 08b. `lint_plugins.py` 0 FAIL (6 WARN lama). Test baru: `tests/backenddev/test_08b_{findings_contract,audit_scope,args,tech_lead,git_state,commit_template,validate_doc}.py`, ditambah kasus B-bertanda di `test_adapter_commands`, `test_common_parsing`, `test_debug_audit_docapi_preconditions`, `test_l27_plan_state`, `test_l34_guard_bash`, `test_plan_preconditions`, `test_profile_preconditions`. Test di berkas ini ditulis ulang di atas `tests/conftest.py` (`chain_repo`, `make_repo`, `be_checks`), bukan `conftest` usulan berkas ini; profil ada di `.claude/profile/backenddev/` (L1.1).

Penyimpangan dari rencana di bawah:

- **B3.** Architect sudah 7 check (check 7 = `HALT.md`), jadi `base_branch` resolve dan merge-base masuk check 4 lewat `check_base_branch`, bukan check baru; hitungannya tetap 7/7. Report mendapat check 8 (8/8). Debug: `scope_hint` jadi check 7 (7/7). Document-api: `domain` jadi check 6 (6/6), profil wajib, `## API surface` dicek (B7b). Profile: `--mode` divalidasi di check 6, `--stack` di check 2 terhadap adapter terpasang.
- **B6.** L5.5 sudah menyempitkan `is_scratch` ke laci `backenddev/docs/[<taskdir>/].explore/`. Sisa perbaikan: `dirty_paths` menyumbang path asal rename, `git_operation_in_progress` di architect check 4 dan report check 7, serta `verify_scope.py` (salinan identik kedua plugin) memakai `is_scratch` lokal alih-alih segmen `.explore` di mana pun.
- **B10/B15 (e).** Re-route (a) menjadi pemicu ketiga amandemen gerbang (`gate-lifecycle.md` bagian 1a): gerbang menulis `lane: PRD_CONVERSION`, `chain: PRD_BRIEF`, `risk` naik ke `MAJOR` bila `MINOR`, dan ledger `PRD`/`BRIEF`, lalu `analyst` masuk lewat jalur resume Fase 0 di hop `PRD`. Subjek commit amandemen menjadi `docs(<slug>): amandemen akar TASK (<pemicu>)`, dan baris matriks commit ditambahkan di `gate-scope.md`.
- **B12-A.** `validate_doc.py` ada di `skills/_common/`. B3 (berkas tidak ada) dan "user" B9 dimulai sebagai `WARN`. P9b hanya mencocokkan token ber-backtick di `sementara dipakai:`. P10 menolak nama berkas berekstensi sumber dan nama kelas test; path modul (`internal/order`) tetap sah, sesuai contoh template. Validator menangkap tiga cacat di contoh terisi (slug `Kategori nihil` BRD di luar lima kategori, aktor `terlarang` tanpa `boleh:`, dimensi 2 PRD tanpa jejak bersimbol), jadi contohnya diperbaiki. Fixture test mengekstrak contoh langsung dari template dan melengkapi Impact map PRD yang sengaja dipangkas (3/16) jadi 16 baris.
- **B12-B.** Dikerjakan di worktree terpisah lalu di-cherry-pick. Hasilnya: katalog check plan pindah ke `plan/references/check-catalog.md`; explorer `system-analysis` dipecah jadi `explorer-surface.md` dan `explorer-blast.md`; blok `> Mengapa:` di SKILL plan, architect, task, dan analyst pindah ke `references/rationale.md`; butir 5–8 dan 10 bagian 2 `brief-template.md` diringkas. Re-entry tech-lead (tabel butir 4) sudah pindah sebelumnya. Muatan rantai planning (tech-lead → plan, tanpa adapter) turun dari 374.414 B menjadi 356.332 B (−18 KB, ±5 %), atau −25 KB bila Profil B tidak dimuat. Angka ini **di bawah** target ±40–50 KB: butir 2, 3, 4, 9, 11, dan 12 `brief-template.md` tidak diringkas karena tidak (seluruhnya) ditagih skrip atau dirujuk agent lain, dan pecahan explorer menambah kepala/tabel slot di tiap berkas.
- **B13.** `finding_source` dibaca dari tingkat atas spec/matriks, bukan parameter `--finding-source` baru. Frontmatter brief mendapat `commit_scope`, yang dipakai penanda `wip(...)` implementor. Pesan commit reviewer/report tetap dari `commit_convention` (L3.6).
- **B14.** `parse_commands` tinggal di `precondition_lib.py` dan menerima juga bentuk butir list `- kunci: nilai`. Check 6 lunak di mode `--read-only`.
- **B17.** Kontrak adapter sudah memuat sembilan kunci sejak L3.1/L3.2. Yang diubah hanya gerbang kelayakan butir 3 dan konsumen per-brief; penjaganya test (`test_b17_*`), bukan lint.
- **B18.** Status rantai architect tetap `COMPLETED | COMPLETED (WARNING)` karena dipakai tabel pengirim balik tech-lead. Yang diganti hanya label triase implementor (`Triase DONE`).
- **B19.** L3.4 memakai `agent_type` di input hook, jadi pagar `Write`/`Edit` `code-explorer` langsung ditambahkan ke `hooks/guard_bash.py` (fail-closed), bukan berkas hook baru.

## Definisi selesai (seluruh berkas)

- 19 checkbox di bawah tercentang, masing-masing sesuai "Selesai bila"-nya.
- `pytest src/plugins/backenddev/tests` hijau, termasuk test B3, B4, B6, B10, B14, B16 di bawah. Semua test itu sudah dijalankan di scratch: **48 lolos terhadap patch usulan**, dan 25 gagal terhadap kode `34684ee` (dua berkas test gagal impor karena helper belum ada).
- `grep -n '".explore" in\|".explore" not in' src/plugins/backenddev/skills/*/scripts/*.py` kosong.
- Hitungan check di SKILL sesuai skrip: architect `7/7`, report `8/8`.
- Checkbox B1–B19 di `ISSUES.md` 8.B dicentang.

## Lokasi artefak reproduksi (sementara)

Scratchpad: `/tmp/claude-1000/-home-fakhrulnugroho-work-natakode-nataflow-agentic-workflow/d3694b5e-a45f-49bf-8ba3-1a983c306ba0/scratchpad/detail-08b/`. Isinya: `mkfx.sh` (pembangun fixture), `plug/backenddev` (salinan plugin + patch usulan), `orig/` (salinan asli), `tests/` (pytest), `*.diff`, `commit_lib.py`, `b5.sh`, `b12_size.sh`.

Semua blok reproduksi di bawah memakai pembangun fixture ini. Salin ke tempat lain bila ingin disimpan:

```bash
# mkfx.sh <dir> — repo git minimal: profil backenddev lengkap + taskdir berisi 1 brief READY.
set -euo pipefail
d="$1"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
git init -q -b main; git config user.email t@t; git config user.name t; git config commit.gpgsign false
mkdir -p .claude/profile internal/order backenddev/docs/2609240900-order-fix
cat > .claude/profile/index.json <<'JSON'
{"project":"fx","stack":"go","architecture":"layered","root_namespace":"example.com/fx",
 "source_root":"internal","commit_convention":"conventional: <type>(<scope>): <subject>",
 "base_branch":"main","branch_convention":"feat/<slug>"}
JSON
printf '# Commands\n\nbuild: go build ./... [OK]\ntest: go test ./... [OK]\n' > .claude/profile/commands.md
printf '# Invariants\n\n- tenant scoping\n' > .claude/profile/invariants.md
printf '# Module\n' > .claude/profile/module-structure.md; printf '# Anti\n' > .claude/profile/anti-patterns.md
for f in code-conventions stack domain-map surface-map; do printf "# x\n" > .claude/profile/$f.md; done
printf 'package order\n\nfunc Total() int { return 1 }\n' > internal/order/service.go
T=backenddev/docs/2609240900-order-fix
printf -- '---\nstatus: ACTIVE\nlane: DEFECT_RCA\nrisk: MINOR\ncreated: 2026-09-24\n---\n\n# Order — fix\n\n## Description\nx `internal/order/service.go:3`\n\n## Success Criteria\n\n- [ ] **SC-1**: a — verifikasi: b\n\n## Out of Scope\n\n- c — d\n' > $T/TASK.md
printf -- '---\ntitle: t\nsource: TASK.md\nrisk: MINOR\nstatus: READY\ncommit_message: "fix(order): implement order-fix"\n---\n\n# Brief\n' > $T/brief-01-order-fix.md
git add -A; git commit -qm init
```

Pada setiap blok: `REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills; FX=<path mkfx.sh>`.

---

## B1 [Sedang] Skema `issues/README.md` bentrok.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 3 jam · **Bergantung pada:** keputusan B2 (satu berkas kontrak untuk keduanya); dikerjakan bareng L2.1 · **Memblokir:** filter status temuan `tech-lead` (gate-scope bagian 6), prefix-match `audit` Fase 0 butir 6

### Konteks
`backenddev/issues/README.md` adalah index bersama dua penulis: `backenddev:audit` (laporan `backenddev/issues/*.md`) dan subagent `code-reviewer` (`{taskdir}/REVIEW.md`). Index dibaca untuk dua hal: `audit` mencari temuan lama lewat prefix path kolom `Target`, dan gerbang `tech-lead` menyaring temuan lewat kolom `Status`.

### Lokasi & kode saat ini
Perbandingan skema dari tiap sumber (dikutip persis):

| Sumber | Kutipan |
|---|---|
| `src/plugins/backenddev/skills/audit/templates/issues-template.md:76` | "Kolom persis: `Tanggal`, `File`, `Target`, `P1`, `P2`, `P3`, `Status`. Satu baris per laporan temuan yang pernah ditulis — dari sweep ini, maupun dari subagent `code-reviewer` …" |
| `src/plugins/backenddev/skills/audit/templates/issues-template.md:80-86` (contoh) | `\| 2026-08-14 \| 2026-08-14-002-issues.md \| diff: internal/order/service.go \| 0 \| 1 \| 0 \| OPEN \|` |
| `src/plugins/backenddev/agents/code-reviewer.md:75` | "Buat direktori `backenddev/issues/` dan seed `README.md` berisi header `# Issues Index` plus baris tabel `\| Date \| Issue ID \| Target \| Severity \| Status \|` bila belum ada." |
| `src/plugins/backenddev/skills/architect/dispatcher/reviewer.md:17` | "Pencatatan Isu: Tambahkan baris temuan di `backenddev/issues/README.md` dengan `target` menyebut path file kode riil." |
| `src/plugins/backenddev/skills/audit/SKILL.md:40` | "Cari baris yang kolom `Target`-nya beririsan prefix path dengan cakupan saat ini." |
| `src/plugins/backenddev/skills/tech-lead/references/gate-scope.md:155` | tabel filter "Status di berkas temuan / `README.md`" |

Hasilnya: 7 kolom vs 5 kolom, `File`+`P1/P2/P3` (satu baris per laporan) vs `Issue ID`+`Severity` (ambigu: satu baris per temuan?), header Indonesia vs Inggris.

**Temuan tambahan (tidak ada di ISSUES.md):**
- `issues-template.md` mengizinkan target diff (frontmatter `target: <path…, atau "diff: <path file yang berubah>">` dan contoh baris `diff: internal/order/service.go` untuk berkas audit), padahal `audit/SKILL.md:25` menyatakan "Cakupan diff bukan milik skill ini" dan skrip menolak target diff.
- Format ID temuan juga bentrok: `issues-template.md` memakai `P{severity}-{n}` (`P1-1`), sedangkan `audit/SKILL.md:120` mencontohkan `` `[P1] SEC-01` ``. `code-reviewer.md:164` dan `gate-scope.md:95` memakai `P1-1`.

### Reproduksi
Demonstrasi mandiri (tanpa repo). Tabel diinline sebagai string Python:

```bash
python3 - <<'PY'
# Reviewer men-seed README (5 kolom), lalu audit menambah baris 7 kolom.
readme = """# Issues Index
| Date | Issue ID | Target | Severity | Status |
|---|---|---|---|---|
| 2026-09-20 | P2-1 | internal/order/ | P2 | OPEN |
| 2026-09-22 | 2026-09-22-001-issues.md | internal/order | 1 | 2 | 0 | P1-1 FIXED |
"""
lines = [l for l in readme.splitlines() if l.startswith("|")]
hdr = [c.strip() for c in lines[0].strip("|").split("|")]
for row in lines[2:]:
    cells = [c.strip() for c in row.strip("|").split("|")]
    rec = dict(zip(hdr, cells))
    print(f"{len(cells)} sel -> Target={rec.get('Target')!r} Status={rec.get('Status')!r} (sel dibuang: {cells[len(hdr):]})")
PY
```
Output aktual:
```
5 sel -> Target='internal/order/' Status='OPEN' (sel dibuang: [])
7 sel -> Target='internal/order' Status='2' (sel dibuang: ['0', 'P1-1 FIXED'])
```

### Dampak
- Kolom `Target` kebetulan sama-sama kolom ke-3, jadi prefix-match masih bisa jalan. Yang rusak adalah **`Status`**: di bawah header 5 kolom, baris audit dibaca `Status='2'` dan `P1-1 FIXED` terbuang. Filter gerbang (gate-scope bagian 6) lalu menganggap temuan itu belum pernah diproses dan menawarkannya lagi, sehingga temuan dikerjakan dua kali.
- Tabel markdown rusak (jumlah sel tak seragam). `audit` Failure path 3 lalu "menginisialisasi ulang header", yang bisa menghapus konteks.
- Target berlabel `diff:` merusak prefix-match (string diawali `diff: `).

### Rencana perbaikan
1. **Berkas baru** `src/plugins/backenddev/skills/audit/references/findings-contract.md`, satu rumah untuk severity (B2), ID temuan, status temuan, dan skema index:
   ```markdown
   # Kontrak Temuan backenddev — severity, ID, status, index

   Rumah tunggal. Dipakai `backenddev:audit` (`backenddev/issues/*.md`), subagent `code-reviewer`
   (`{taskdir}/REVIEW.md`), dan `backenddev:architect` (temuan eksekusi Fase 3). Berkas lain merujuk ke
   sini dan dilarang menyalin definisinya.

   ## 1. Severity
   (tabel B2)

   ## 2. ID temuan
   `P{severity}-{n}` per laporan; `{n}` mulai 1 di tiap severity (`P1-1`, `P1-2`, `P2-1`).
   Dimensi (`security` … `architecture`) adalah field `Dimension`, bukan bagian ID.

   ## 3. Status temuan
   (dipindah utuh dari `issues-template.md` "Marking finding status")

   ## 4. Index `backenddev/issues/README.md`
   Berkas dibuka dengan judul `# Issues Index`, lalu header persis:

   | Tanggal | File | Target | P1 | P2 | P3 | Status |
   |---|---|---|---|---|---|---|

   - `Tanggal`: `yyyy-mm-dd`.
   - `File`: path relatif root repo — `backenddev/issues/2026-08-14-001-issues.md` atau
     `backenddev/docs/<YYMMDDhhmm>-<slug>/REVIEW.md`.
   - `Target`: path modul/berkas, dipisah koma bila lebih dari satu, **tanpa** label (`diff:` dilarang).
     Untuk REVIEW.md: folder dari union `## File scope` brief.
   - `P1`/`P2`/`P3`: jumlah temuan per severity.
   - `Status`: `OPEN`, atau daftar `<ID> <STATUS>` dipisah koma (`P1-1 FIXED, P2-2 OBSOLETE`).
   - Satu baris per laporan (audit maupun REVIEW.md). Baris lama tidak pernah dihapus.
   ```
2. `src/plugins/backenddev/skills/audit/templates/issues-template.md`:
   - `:5` ganti dengan: "Severity, format ID temuan, status temuan, dan skema index hidup di `../references/findings-contract.md`. Template ini hanya memuat struktur laporan."
   - Hapus seksi severity `:7-13`, seksi status, dan seksi `## issues/README.md — index` (`:74-86`). Ganti dengan satu baris rujukan ke `findings-contract.md` bagian 3–4.
   - Frontmatter contoh: `target: <path module/package>` (hapus alternatif `diff:`).
3. `src/plugins/backenddev/skills/audit/SKILL.md`:
   - `:84` → "Tambahkan satu baris di `backenddev/issues/README.md` persis skema `references/findings-contract.md` bagian 4."
   - `:120` → ``- **P1 & P2**: `P1-1` <judul singkat> · `<path/ke/Berkas>:45` — satu baris per temuan``.
4. `src/plugins/backenddev/agents/code-reviewer.md:75` → "Saring temuan sesuai `target_severity`, lalu tambahkan satu baris di `backenddev/issues/README.md` persis skema bagian 4 berkas `{findings_contract}` (slot prompt): `File` = `{taskdir}/REVIEW.md`, `Target` = folder union `## File scope`. README belum ada → buat dengan judul dan header dari bagian 4." Baris `:104` (`Issues Index: Updated …`) tetap.
5. `src/plugins/backenddev/skills/architect/dispatcher/reviewer.md`:
   - `:17` → "Pencatatan Isu: tambahkan satu baris index persis skema bagian 4 `{findings_contract}`."
   - Tambah baris slot hidrasi: `| {findings_contract} | ${CLAUDE_PLUGIN_ROOT}/skills/audit/references/findings-contract.md, dihidrasi architect di SKILL.md | [REQUIRED] path absolut; batalkan dispatch bila berkas tidak ada |`. Pola ini sama dengan `{adapter_path}` implementor, dan tahan terhadap X2.
   - `architect/SKILL.md:105` → sebut slot `findings_contract` di daftar hidrasi.
6. Bareng L2.1: Fase 4 reviewer men-stage `REVIEW.md` **dan** `backenddev/issues/README.md`.

### Test yang ditambahkan / Verifikasi manual
- Lint L6.3: cek bahwa header tabel index hanya didefinisikan di `findings-contract.md`. Grep `| Date | Issue ID` di `src/plugins/backenddev` harus kosong.
- Manual: fixture repo → jalankan `audit` lalu `architect` sampai reviewer → `backenddev/issues/README.md` memuat dua baris 7-kolom dengan header tunggal.

### Selesai bila
- Hanya ada satu definisi header index (`findings-contract.md` bagian 4), dan audit serta reviewer sama-sama merujuknya.
- Contoh `diff:` dan ID `[P1] SEC-01` hilang dari berkas mana pun.

### Risiko & catatan
- Repo yang sudah punya README 5-kolom: tambahkan catatan migrasi di `findings-contract.md` ("baris berskema lama dipertahankan; baris baru memakai skema baru; jangan menulis ulang header") agar Failure path 3 audit tidak menghapus riwayat.
- Opsi lain untuk `File` (nama berkas saja) menjaga contoh lama, tapi tidak bisa menunjuk REVIEW.md yang tinggal di luar `issues/`.

---

## B2 [Sedang] Tangga severity invariant tidak konsisten.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** keputusan user (severity invariant & scope); satu berkas dengan B1 · **Memblokir:** triase architect Fase 4 butir 3, seleksi temuan gerbang

### Konteks
`issues-template.md:5` mengklaim definisi severity-nya "**sumber tunggal**", tetapi lima berkas lain memuat tangga sendiri dengan isi yang saling bertentangan.

### Lokasi & kode saat ini

| Kasus | `audit/templates/issues-template.md` | `audit/SKILL.md` | `agents/code-reviewer.md` | `architect/SKILL.md` | `architect/references/lifecycle-recovery.md` |
|---|---|---|---|---|---|
| Pelanggaran invariant profil | tidak disebut (`:9` "P1 — merusak data/uang/keamanan…") | `:36` "pelanggaran invariant otomatis menjadi blocker kepatuhan"; `:73` "**P2 (Major)**: … ketidakpatuhan invariant profil" | `:35` "dilarang dinaikkan ke `P1` — `P1` milik pelanggaran invariant" | — | `:149` "`P2` \| Pelanggaran invariant arsitektur, anti-pola stack" |
| Anti-pattern profil | — | `:73-74` P2, "Dilarang menaikkan anti-pattern ke P1" | `:35` P2, dilarang P1 | — | `:149` P2 |
| Berkas di luar scope | — | — | `:42` "Pelanggaran Scope (`P2`; `P1` bila menyentuh domain luar)"; `:69` "`P2` pelanggaran scope terisolasi" | `:89` "`P1 — berkas di luar scope`"; `:94` "`P1 — berkas yatim`" | `:148` "`P1` \| Pelanggaran kontrak, file di luar scope" |
| Performa query / N+1 | `:10` "P2 — … utang performa yang terukur" | `:73` P2 "N+1 query" | `:69` P2 "debt performa query"; `:170` P3 "Query N+1 non-kritis" | — | — |
| Label | `:28/36/39` Blocker / Should fix / Nice to have | `:72-75`, `:92` Critical / Major / Minor | `:161/166/169` Blocker / Defects–Scope Violations / Style–Optimization | — | — |

**Koreksi terhadap ISSUES.md:** selain tiga lokasi yang disebut (`code-reviewer.md:35`, `audit/SKILL.md:73`, `audit/SKILL.md:36`), kontradiksi juga ada di `lifecycle-recovery.md:148-149` (invariant = P2, scope = P1), `architect/SKILL.md:89/94` (scope = P1), dan `code-reviewer.md:42/69/170` (scope = P2, N+1 bisa P3).

### Reproduksi
Tidak relevan (kontradiksi teks). Bukti: kutipan tabel di atas, diambil lewat mdcp `md_search`.

### Dampak
- Satu pelanggaran invariant bisa divonis P1 oleh reviewer tetapi P2 oleh audit. Karena P1 menahan penutupan (architect Fase 4 butir 3) dan P2 tidak, vonis rantai bergantung pada siapa yang menilai.
- Berkas di luar scope menghentikan rantai di architect Fase 3 (P1), tetapi hanya P2 bila baru ketahuan di REVIEW.md. Berkas yatim yang lolos sampai review pun tidak menahan penutupan, padahal `architect/SKILL.md:94` menyebutnya P1.

### Rencana perbaikan
1. Isi `findings-contract.md` bagian 1 (berkas dari B1):
   ```markdown
   ## 1. Severity

   | Severity | Label | Definisi | Selalu masuk sini |
   |---|---|---|---|
   | P1 | Blocker | Merusak data/uang/keamanan, atau output salah di jalur utama | Pelanggaran `## Invariants` profil; berkas kode di luar union `## File scope` atau simbol di luar `Anchor`; inkoherensi lintas-brief (rollback terselubung, migrasi bertentangan); skema berubah tanpa migrasi; mirrored path tertinggal |
   | P2 | Should fix | Bug nyata di jalur sempit, atau utang performa yang terukur | N+1, kolom `WHERE`/`ORDER BY` tanpa index, batas hasil hilang; kecocokan baris `## Anti-patterns` profil (plafon P2, dilarang naik) |
   | P3 | Nice to have | Konsistensi, kebersihan, keterbacaan | Penamaan, duplikasi, dead code terisolasi |

   Kandidat tanpa bukti dibuang, tidak pernah diturunkan jadi P3. `PLAUSIBLE` adalah label bukti, bukan severity.
   ```
2. Teks pengganti per berkas:
   - `audit/SKILL.md:36` → "… aturan `invariants.md` (pelanggarannya `P1`, `references/findings-contract.md` bagian 1) …"
   - `audit/SKILL.md:71-75` (Fase 3 butir 4) → "Tetapkan severity menurut `references/findings-contract.md` bagian 1. Temuan anti-pattern wajib mengutip **dua** bukti: `file:line` kode pelanggar dan baris profil yang dilanggar; plafonnya `P2`."
   - `audit/SKILL.md:92` → "Rangkum jumlah temuan per severity: P1 (Blocker), P2 (Should fix), P3 (Nice to have)."
   - `agents/code-reviewer.md:35` → "… jadi temuan `P2` dimensi `architecture` (plafon anti-pattern, `{findings_contract}` bagian 1) …"
   - `agents/code-reviewer.md:42` → "Berkas kode di luar union adalah Pelanggaran Scope — `P1` (`{findings_contract}` bagian 1)."
   - `agents/code-reviewer.md:69` → "**Severity**: tetapkan menurut tabel bagian 1 `{findings_contract}`, satu-satunya definisi; dilarang memakai tangga lain."
   - `agents/code-reviewer.md:161/166/169-170` → heading `## P1 Findings (Blocker)`, `## P2 Findings (Should fix)`, `## P3 Findings (Nice to have)`; placeholder P3 menjadi `<penamaan, duplikasi, dead code. Kosongkan jika bersih>`.
   - `architect/references/lifecycle-recovery.md:146-151` → ganti kolom "Definisi Temuan" dengan kalimat pembuka "Definisi severity: `skills/audit/references/findings-contract.md` bagian 1." Kolom tindakan tetap.
   - `architect/SKILL.md:89/90/94` → label `P1 — …` tetap (konsisten dengan keputusan), ditambah rujukan "(findings-contract bagian 1)".
   - `audit/templates/issues-template.md:9-11` → dihapus (B1 butir 2).

### Test yang ditambahkan / Verifikasi manual
- Lint L6.3: pola `\*\*P[123] \(` dan `P[123] —` hanya boleh muncul di `findings-contract.md` dan heading template laporan.
- Manual: baca ulang kelima berkas; tidak ada lagi definisi severity selain rujukan.

### Selesai bila
Satu tabel severity di `findings-contract.md`, dirujuk kelima berkas, tanpa satu pun definisi tandingan. Invariant dan scope bernilai sama di semua berkas.

### Risiko & catatan
- **Keputusan user**: bila invariant/scope dipilih P2, ubah `architect/SKILL.md:89/94` (rantai tidak berhenti untuk P2) dan `lifecycle-recovery.md:148`. Usulan P1 dipilih karena architect sudah menghentikan rantai atas scope, dan invariant di profil memang aturan keras (tenant scoping, zona waktu).
- `dimensions.md` dan dimensi di `code-reviewer.md` Fase 1 butir 5 tetap kembaran; hanya severity yang dipusatkan.

---
## B3 [Sedang] Parameter diterima tapi tak pernah divalidasi.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 1–1,5 hari · **Bergantung pada:** L5.5 (helper `_common`), L5.2 (pola taskdir debug), L1.1 (`PROFILE_DIR`), L6.1 · **Memblokir:** B6 (architect/report memakai helper yang sama)

### Konteks
Setiap SKILL menjalankan skrip prasyarat dengan parameter dari pemanggil, lalu memperlakukan `PASS` sebagai izin lanjut. Parameter yang diterima argparse tapi tidak dinilai membuat `PASS` palsu atas janji yang ditulis SKILL.

### Lokasi & kode saat ini
Tabel dihitung dari kode (`add_argument` dan pemakaian atribut di tiap skrip `src/plugins/backenddev/skills/<skill>/scripts/check_preconditions.py`):

| Skrip | Parameter | argparse | Dipakai? | Divalidasi? | Janji SKILL | Usulan |
|---|---|---|---|---|---|---|
| architect | `--base-branch` | `:499` | tidak — disimpan `:50`, tak pernah dibaca | tidak | `architect/SKILL.md:26` default dari profil; `:178` "Git Detached HEAD State … Minta checkout branch sah" | **validasi** (check 7 baru) |
| report | `--base-branch` | `:414` | tidak — disimpan `:50` | tidak | `report/SKILL.md:26` "nilai yang tidak resolve ke ref git ditolak"; `:47` diff kosong dihentikan | **validasi** + wajib ada diff (check 8 baru) |
| document-api | `--base-branch` | `:271` | tidak — disimpan `:41` | tidak | `document-api/SKILL.md:26` fallback profil→`main`→`master`, branch tak ada → cakupan penuh + ASUMSI | **hapus** dari skrip & baris perintah SKILL:18 (fallback memang milik Fase 0) |
| document-api | `--domain` | `:270` | hanya digema di `to_json` `:263` | tidak | `SKILL.md:25` REQUIRED, "Hentikan … jika parameter kosong" | **validasi** non-kosong |
| document-api | `--stack` | `:272` | ya — menimpa stack profil `:111` | hanya "berkas adapter ada" | tidak ada di `## Parameter`; remediasi `:21` "profil/stack adapter tidak ada → jalankan `backenddev:profile`" | **hapus**; stack hanya dari profil (FAIL bila profil absen) |
| debug | `--symptom` | `:383` | tidak — disimpan `:40` | tidak | `debug/SKILL.md:25` REQUIRED; `:18` dioper lewat shell | **hapus** (lihat B5) |
| debug | `--scope-hint` | `:385` | tidak — disimpan `:42` | tidak | `SKILL.md:27` path, default `-` | **validasi**: `-`/kosong, atau path yang ada di dalam root |
| debug | `--taskdir` | `:384` | ya (check 5) | ada & dapat ditulis; **pola tidak** | `SKILL.md:26` "pola lain ditolak tanpa negosiasi" | → L5.2 `check_taskdir()` |
| audit | `--target-scope` | `:347` | ya (check 6) | kosong → **PASS** `:273-281` | `audit/SKILL.md:25` REQUIRED | **validasi** (FAIL bila kosong) — diff di B4 |
| audit | `--dimensions` | `:348` | tidak — disimpan `:40` | tidak | `SKILL.md:26` "nilai di luar 6 token dimensi ditolak" | **validasi** enum — diff di B4 |
| profile | `--mode` | `:266` | tidak — disimpan `:48` | tidak | `profile/SKILL.md:23` `auto`\|`generate`\|`refresh` | **validasi** enum |
| profile | `--stack` | `:267` | tidak — disimpan `:49` | tidak | `SKILL.md:24` nilai sah = daftar `stacks/_CONTRACT.md` | **validasi** enum + adapter ada |
| profile | `--profile-dir` | `:268` | ya — target probe tulis check 3 `:141-143` | tidak | `SKILL.md:26` default `.claude/profile`, "nilai lain ditolak" | **hapus** (pakai konstanta `PROFILE_DIR` L1.1) |

**Koreksi terhadap ISSUES.md:** `--base-branch` document-api **tidak** perlu ditolak. `document-api/SKILL.md:26` dan `:109` memang merancang fallback ke cakupan penuh plus ASUMSI. Masalahnya parameter itu tidak berguna di skrip, jadi usulannya dihapus, bukan divalidasi.

### Reproduksi
```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); bash "$FX" $tmp/a >/dev/null; cd $tmp/a; T=backenddev/docs/2609240900-order-fix
python3 $P/architect/scripts/check_preconditions.py --taskdir $T --base-branch does-not-exist | head -1   # di main
git checkout -q --detach HEAD; python3 $P/architect/scripts/check_preconditions.py --taskdir $T | head -1; git checkout -q main
sed -i 's/status: READY/status: DONE/' $T/brief-01-order-fix.md; printf '# Review\n' > $T/REVIEW.md; git add -A; git commit -qm done
python3 $P/report/scripts/check_preconditions.py --taskdir $T --base-branch does-not-exist | head -1     # di main, diff kosong
python3 $P/audit/scripts/check_preconditions.py --dimensions foo,bar | sed -n '1p;7p'                     # tanpa --target-scope
mkdir tmpdir; python3 $P/debug/scripts/check_preconditions.py --symptom "" --taskdir tmpdir --scope-hint /tidak/ada | sed -n '1p;6p'
printf 'module x\n' > go.mod; python3 $P/profile/scripts/check_preconditions.py --profile-dir $tmp/elsewhere --mode foo --stack cobol | sed -n '1p;4p'
mkdir -p $tmp/b/src && cd $tmp/b && git init -q -b main
python3 $P/document-api/scripts/check_preconditions.py --stack go --domain "" --base-branch nope | head -1  # tanpa .claude/
```
Output aktual (dijalankan di scratch):
```
PRECONDITION CHECK: architect [PASS] (6/6 passed)
PRECONDITION CHECK: architect [PASS] (6/6 passed)
PRECONDITION CHECK: report [PASS] (7/7 passed)
PRECONDITION CHECK: audit [PASS] (6/6 passed)
[6] Target Scope Validation          : PASS (Parameter target_scope kosong, evaluasi cakupan default di Fase 0)
PRECONDITION CHECK: debug [PASS] (6/6 passed)
[5] Taskdir Write Access             : PASS (Taskdir terverifikasi dan siap ditulis: tmpdir)
PRECONDITION CHECK: profile [PASS] (5/5 passed)
[3] Profile Directory Write Access   : PASS (Direktori /tmp/…/elsewhere siap ditulis)
PRECONDITION CHECK: document-api [PASS] (5/5 passed)
```

### Dampak
- architect dapat mulai (dan implementor meng-commit) langsung di `main` atau di detached HEAD. Reviewer lalu menilai diff kosong (`merge-base main HEAD` = HEAD) atau acuan yang salah.
- report lolos prasyarat di atas diff kosong dan baru berhenti di Fase 2 butir 4, sesudah membuang giliran.
- audit tanpa cakupan menyapu "default" yang tidak didefinisikan di SKILL mana pun.
- profile menulis ke direktori sembarang bila pemanggil salah mengisi.
- document-api jalan tanpa profil, jadi `base_branch` default dan rujukan `## API surface` (B7) tidak punya sumber.

### Rencana perbaikan
1. `src/plugins/backenddev/skills/_common/precondition_lib.py`: tambah `check_base_branch(root, base, require_diff=False)` (bagian dari diff B6 di bawah). Urutan cek: base resolve (`git rev-parse --verify --quiet <base>^{commit}`) → HEAD ter-attach → HEAD ≠ base → merge-base ada → (report) merge-base ≠ HEAD.
2. architect: check 7 "Base Branch & HEAD"; report: check 8 "Base Branch & Merge-Base Diff". Diff lengkap ada di B6 (`b3b6_architect.diff`, `b3b6_report.diff`). Kutipan inti:
   ```python
   def _check_7_base_branch(self):
       base = self.base_branch_arg or json.loads((self.root / ".claude/profile/index.json").read_text()).get("base_branch")
       ok, detail = check_base_branch(self.root, base)          # report: require_diff=True
       self.results.append({"id": 7, "name": "Base Branch & HEAD",
                            "status": "PASS" if ok else "FAIL", "summary": detail,
                            "action": "" if ok else "Pindah ke branch kerja taskdir … dilarang menebak acuan diff."})
   ```
   Teks SKILL: `architect/SKILL.md:20` → "`PASS` (7/7 checks)" dan tambah remediasi "HEAD di base branch/detached atau `base_branch` tak resolve → kembali ke gerbang `backenddev:tech-lead`". `report/SKILL.md:20` → "`PASS` (8/8 checks)".
3. audit: `--target-scope` wajib, `--dimensions` ⊆ `{all, security, transaction, data, persistence, concurrency, architecture}` (diff di B4).
4. debug: hapus `--symptom` (B5). Validasi `--scope-hint`:
   ```python
   hint = (self.scope_hint_arg or "").strip()
   if hint and hint != "-":
       p = (self.root / hint).resolve()
       if not p.is_relative_to(self.root) or not p.exists():
           FAIL(f"scope_hint '{hint}' tidak ada di dalam repo", "Perbaiki atau kosongkan scope_hint (`-`).")
   ```
   Pola taskdir → `check_taskdir()` L5.2.
5. document-api: hapus `--base-branch` dan `--stack`. Tambah validasi `--domain` non-kosong. Check 2 FAIL bila `.claude/profile/index.json` absen. `document-api/SKILL.md:18` → `` python3 ${CLAUDE_PLUGIN_ROOT}/skills/document-api/scripts/check_preconditions.py --domain "<domain>" `` (domain dari user: kutip ganda aman selama tidak memuat `` ` `` atau `$`; SKILL menambahkan "tulis domain tanpa backtick/`$`").
6. profile: validasi `--mode ∈ {auto, generate, refresh}` dan `--stack ∈ {auto} ∪ stack-id _CONTRACT` (+ adapter ada). Hapus `--profile-dir` dari argparse, `profile/SKILL.md:18` dan `:26`. Target tulis = konstanta `PROFILE_DIR` (L1.1).
7. Semua skrip: parameter yang dihapus membuat argparse gagal keras (exit 2) bila masih dikirim. Ini disengaja, supaya SKILL yang belum diperbarui ketahuan.

### Test yang ditambahkan / Verifikasi manual
`src/plugins/backenddev/tests/test_b3_base_branch.py` (dijalankan di scratch: 6/6 lolos dengan patch, 6/6 gagal di kode `34684ee`):
```python
from conftest import TASKDIR, BRIEF_MD, check, git, run_json
ARCH = "architect/scripts/check_preconditions.py"; REPORT = "report/scripts/check_preconditions.py"

def test_architect_menolak_head_di_base_branch(repo):
    r = run_json(ARCH, repo, "--taskdir", TASKDIR)
    assert check(r, 7)["status"] == "FAIL" and "base_branch 'main'" in check(r, 7)["summary"]

def test_architect_menolak_base_yang_tidak_resolve(repo):
    git(repo, "checkout", "-q", "-b", "feat/order-fix")
    r = run_json(ARCH, repo, "--taskdir", TASKDIR, "--base-branch", "does-not-exist")
    assert check(r, 7)["status"] == "FAIL" and "tidak resolve" in check(r, 7)["summary"]

def test_architect_menolak_detached_head(repo):
    git(repo, "checkout", "-q", "--detach", "HEAD")
    assert "detached" in check(run_json(ARCH, repo, "--taskdir", TASKDIR), 7)["summary"]

def test_architect_lolos_di_branch_kerja(repo):
    git(repo, "checkout", "-q", "-b", "feat/order-fix")
    assert run_json(ARCH, repo, "--taskdir", TASKDIR)["status"] == "PASS"

def test_report_menuntut_diff_nyata(repo):
    git(repo, "checkout", "-q", "-b", "feat/order-fix")
    assert "merge-base = HEAD" in check(run_json(REPORT, repo, "--taskdir", TASKDIR), 8)["summary"]

def test_report_lolos_dengan_diff(repo):
    git(repo, "checkout", "-q", "-b", "feat/order-fix")
    td = repo / TASKDIR
    (td / "brief-01-order-fix.md").write_text(BRIEF_MD.format(status="DONE")); (td / "REVIEW.md").write_text("# Review\n")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "done")
    assert run_json(REPORT, repo, "--taskdir", TASKDIR)["status"] == "PASS"
```
`conftest.py` (fixture `repo`, `run_json`, `check`) berstruktur L6.1. Isinya dicantumkan sekali di B4.

Output sesudah patch (scratch):
```
PRECONDITION CHECK: architect [FAIL] (6/7 passed)
[7] Base Branch & HEAD               : FAIL (HEAD berada di base_branch 'main' — rantai wajib berjalan di branch kerja)
[7] Base Branch & HEAD               : FAIL (base_branch 'does-not-exist' tidak resolve ke commit)
[7] Base Branch & HEAD               : PASS (branch 'feat/order-fix' · merge-base d27ecbc terhadap 'main')
```
Test debug/profile/document-api: **belum dijalankan** (pola sama; tulis saat patch dikerjakan): `--scope-hint /tidak/ada` → FAIL; `--mode foo` → FAIL; `--stack cobol` → FAIL; document-api tanpa profil → FAIL; `--domain ""` → FAIL.

### Selesai bila
Tiap baris tabel di atas bervonis "divalidasi" atau "dihapus dari skrip dan SKILL", dan kedelapan contoh reproduksi menghasilkan FAIL.

### Risiko & catatan
- Check 7 architect akan menggagalkan pemakaian yang selama ini "jalan" di `main`. Itu memang tujuannya: gerbang tech-lead Fase 3 selalu membuat branch kerja.
- Dispatcher architect ke report (Fase 5 butir 3) sudah meneruskan `base_branch`, jadi tidak perlu perubahan di sana.

---
## B4 [Sedang] Skrip audit crash dan salah vonis.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** L6.1 (conftest), L5.5 (opsional) · **Memblokir:** —

### Konteks
Prasyarat `backenddev:audit` menilai `source_root` profil (check 1) dan `target_scope` (check 6). Crash membuat mode `--json` tidak mengeluarkan apa pun, sehingga SKILL tidak punya vonis untuk dibaca. Regex diff/PR yang tidak berjangkar menolak path sah.

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/audit/scripts/check_preconditions.py:83-111`:
```python
        src_dir = self.root / src_rel
        if not src_dir.exists() and not (self.root / "src").exists():
            ...
        target_check = src_dir if src_dir.exists() else (self.root / "src")
        ...
            "summary": f"Akses baca kode sumber terverifikasi di {target_check.relative_to(self.root)}",   # :109
```
`:273-292`:
```python
        if not self.target_scope_arg:
            self.results.append({... "status": "PASS", "summary": "Parameter target_scope kosong, evaluasi cakupan default di Fase 0" ...})
            return
        scope_str = self.target_scope_arg.strip()
        if re.search(r"(\.\.|origin/|refs/pull|pr/)", scope_str):                                          # :285
            ... "FAIL" ... "menunjuk diff branch/PR, bukan kode mendarat"
```

**Koreksi terhadap ISSUES.md:** crash di `:109` hanya terjadi bila `source_root` absolut **dan direktorinya ada** di luar root. Absolut yang tidak ada jatuh ke fallback `src/` tanpa crash. **Temuan tambahan:** `target_scope` absolut di luar repo justru PASS, dan `internal/origin/x` ikut divonis diff.

### Reproduksi
```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); bash "$FX" $tmp/r >/dev/null; mkdir -p $tmp/luar/src; cd $tmp/r
python3 - "$tmp/luar/src" <<'PY'
import json,sys;p='.claude/profile/index.json';d=json.load(open(p));d['source_root']=sys.argv[1];json.dump(d,open(p,'w'))
PY
python3 $P/audit/scripts/check_preconditions.py --target-scope internal/order --json > out.txt 2> err.txt; echo "exit=$? stdout=$(wc -c < out.txt)B"; grep 'line 109' err.txt; tail -1 err.txt
git checkout -q .claude/profile/index.json
mkdir -p internal/expr internal/origin/x $tmp/a1/internal
for s in internal/expr/ internal/origin/x ../a1/internal $tmp/luar/src main..HEAD; do
  python3 $P/audit/scripts/check_preconditions.py --target-scope "$s" | grep '^\[6\]'; done
```
Output aktual:
```
exit=1 stdout=0B
  File ".../skills/audit/scripts/check_preconditions.py", line 109, in _check_1_source_root
ValueError: '/tmp/…/luar/src' is not in the subpath of '/tmp/…/r'
[6] Target Scope Validation          : FAIL (target_scope 'internal/expr/' menunjuk diff branch/PR, bukan kode mendarat)
[6] Target Scope Validation          : FAIL (target_scope 'internal/origin/x' menunjuk diff branch/PR, bukan kode mendarat)
[6] Target Scope Validation          : FAIL (target_scope '../a1/internal' menunjuk diff branch/PR, bukan kode mendarat)
[6] Target Scope Validation          : PASS (Target scope terverifikasi: /tmp/…/luar/src)
[6] Target Scope Validation          : FAIL (target_scope 'main..HEAD' menunjuk diff branch/PR, bukan kode mendarat)
```

### Dampak
- Profil dengan `source_root` absolut (misal monorepo yang merujuk submodule) → audit tidak bisa berangkat, dan mode `--json` tidak memberi alasan.
- Package bernama `expr`, `pr`, `origin`, atau path `../` ditolak dengan pesan menyesatkan ("gunakan code-reviewer"), sementara path di luar repo diloloskan dan audit menyapu kode orang lain.

### Rencana perbaikan
1. Normalisasi `source_root` dengan `resolve()`, lalu FAIL rapi bila hasilnya di luar root.
2. `target_scope`: kosong → FAIL (REQUIRED, B3); dimensi divalidasi (B3); cek path dulu. Regex diff/PR hanya dipakai bila path tidak ada, dan berjangkar penuh; path di luar root → FAIL tersendiri.

Diff (diuji di scratch, `b4_audit.diff`):
```diff
--- a/src/plugins/backenddev/skills/audit/scripts/check_preconditions.py
+++ b/src/plugins/backenddev/skills/audit/scripts/check_preconditions.py
@@ -28,6 +28,18 @@
 )
 
 
+VALID_DIMENSIONS = {"security", "transaction", "data", "persistence", "concurrency", "architecture"}
+
+# Bentuk target yang menunjuk diff/PR, dicocokkan terhadap SELURUH string dan hanya
+# bila string itu bukan path yang ada. `a..b`/`a...b` wajib punya ruas kiri bukan
+# titik/garis miring, sehingga `../x` dan `internal/expr/` tidak ikut tertangkap.
+DIFF_TARGET = re.compile(
+    r"^(?:[^\s./][^\s]*?\.\.\.?[^\s/][^\s]*"      # main..HEAD, a...b
+    r"|origin/\S+|refs/pull/\d+(?:/\w+)?|pr/\d+|#\d+|diff:.*)$",
+    re.IGNORECASE,
+)
+
+
 class PreconditionChecker:
     def __init__(
         self,
@@ -80,8 +92,19 @@
             except Exception:
                 pass
 
-        src_dir = self.root / src_rel
-        if not src_dir.exists() and not (self.root / "src").exists():
+        src_dir = (self.root / src_rel).resolve()
+        if not src_dir.is_relative_to(self.root):
+            self.results.append({
+                "id": check_id,
+                "name": name,
+                "status": "FAIL",
+                "summary": f"source_root '{src_rel}' berada di luar root repositori {self.root}",
+                "action": "Perbaiki `source_root` di index.json menjadi path relatif di dalam repo lewat `backenddev:profile`.",
+            })
+            return
+
+        target_check = src_dir if src_dir.exists() else (self.root / "src")
+        if not target_check.exists():
             self.results.append({
                 "id": check_id,
                 "name": name,
@@ -91,7 +114,6 @@
             })
             return
 
-        target_check = src_dir if src_dir.exists() else (self.root / "src")
         if not os.access(target_check, os.R_OK):
             self.results.append({
                 "id": check_id,
@@ -270,47 +292,48 @@
         check_id = 6
         name = "Target Scope Validation"
 
-        if not self.target_scope_arg:
-            self.results.append({
-                "id": check_id,
-                "name": name,
-                "status": "PASS",
-                "summary": "Parameter target_scope kosong, evaluasi cakupan default di Fase 0",
-                "action": "",
-            })
+        def fail(summary: str, action: str):
+            self.results.append({"id": check_id, "name": name, "status": "FAIL",
+                                 "summary": summary, "action": action})
+
+        scope_str = (self.target_scope_arg or "").strip()
+        if not scope_str:
+            fail("Parameter target_scope kosong (REQUIRED)",
+                 "Minta path modul/package/folder yang disapu; audit tidak menebak cakupan.")
             return
 
-        # Check if target scope looks like a diff or PR
-        scope_str = self.target_scope_arg.strip()
-        if re.search(r"(\.\.|origin/|refs/pull|pr/)", scope_str):
-            self.results.append({
-                "id": check_id,
-                "name": name,
-                "status": "FAIL",
-                "summary": f"target_scope '{scope_str}' menunjuk diff branch/PR, bukan kode mendarat",
-                "action": "Gunakan subagent `code-reviewer` untuk penilaian diff, audit hanya menyapu path direktori/modul nyata.",
-            })
+        dims = [d.strip().lower() for d in (self.dimensions_arg or "all").split(",") if d.strip()]
+        unknown = [d for d in dims if d != "all" and d not in VALID_DIMENSIONS]
+        if unknown:
+            fail(f"Dimensi tidak dikenal: {', '.join(unknown)}",
+                 f"Gunakan `all` atau subset dari: {', '.join(sorted(VALID_DIMENSIONS))}.")
             return
 
         scope_path = Path(scope_str)
         if not scope_path.is_absolute():
             scope_path = self.root / scope_path
+        scope_path = scope_path.resolve()
+
+        if not scope_path.exists() and DIFF_TARGET.match(scope_str):
+            fail(f"target_scope '{scope_str}' menunjuk diff branch/PR, bukan kode mendarat",
+                 "Gunakan subagent `code-reviewer` untuk penilaian diff, audit hanya menyapu path direktori/modul nyata.")
+            return
+
+        if not scope_path.is_relative_to(self.root):
+            fail(f"target_scope '{scope_str}' berada di luar root repositori",
+                 "Tentukan path modul/package di dalam repositori target.")
+            return
 
         if not scope_path.exists():
-            self.results.append({
-                "id": check_id,
-                "name": name,
-                "status": "FAIL",
-                "summary": f"Path target_scope '{scope_str}' tidak ditemukan di disk",
-                "action": "Tentukan path modul/package yang valid di repositori.",
-            })
+            fail(f"Path target_scope '{scope_str}' tidak ditemukan di disk",
+                 "Tentukan path modul/package yang valid di repositori.")
             return
 
         self.results.append({
             "id": check_id,
             "name": name,
             "status": "PASS",
-            "summary": f"Target scope terverifikasi: {scope_str}",
+            "summary": f"Target scope terverifikasi: {scope_path.relative_to(self.root)} · dimensi {', '.join(dims)}",
             "action": "",
         })
 
```

### Test yang ditambahkan / Verifikasi manual
`src/plugins/backenddev/tests/conftest.py` (dipakai semua test berkas ini; struktur L6.1):
```python
import json, os, subprocess, sys
from pathlib import Path
import pytest

PLUGIN = Path(os.environ.get("BACKENDDEV_ROOT", Path(__file__).resolve().parents[1]))
SKILLS = PLUGIN / "skills"
TASKDIR = "backenddev/docs/2609240900-order-fix"
INDEX = {"project": "fx", "stack": "go", "architecture": "layered", "root_namespace": "example.com/fx",
         "source_root": "internal", "commit_convention": "conventional: <type>(<scope>): <subject>",
         "base_branch": "main", "branch_convention": "feat/<slug>"}
PROFILE_DOCS = {
    "commands.md": "# Commands\n\nbuild: go build ./... [OK] · typecheck: go vet ./... [OK]\n"
                   "test: go test ./... [OK] · test-single: go test ./<pkg> -run <T> [OK]\n",
    "invariants.md": "# Invariants\n\n- tenant scoping\n", "module-structure.md": "# Module\n",
    "anti-patterns.md": "# Anti\n", "code-conventions.md": "# Conv\n", "stack.md": "# Stack\n",
    "domain-map.md": "# Domain\n", "surface-map.md": "# Surface\n"}
TASK_MD = ("---\nstatus: ACTIVE\nlane: DEFECT_RCA\nrisk: MINOR\ncreated: 2026-09-24\n---\n\n# Order — fix\n\n"
           "## Description\nx `internal/order/service.go:1`\n\n## Success Criteria\n\n- [ ] **SC-1**: a — verifikasi: b\n\n"
           "## Out of Scope\n\n- c — d\n")
BRIEF_MD = ("---\ntitle: t\nsource: TASK.md\nrisk: MINOR\nstatus: {status}\n"
            "commit_message: \"fix(order): implement order-fix\"\n---\n\n# Brief\n")

def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"; r.mkdir()
    git(r, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(r, "config", k, v)
    prof = r / ".claude" / "profile"; prof.mkdir(parents=True)
    (prof / "index.json").write_text(json.dumps(INDEX))
    for name, body in PROFILE_DOCS.items():
        (prof / name).write_text(body)
    (r / "internal" / "order").mkdir(parents=True)
    (r / "internal" / "order" / "service.go").write_text("package order\n")
    td = r / TASKDIR; td.mkdir(parents=True)
    (td / "TASK.md").write_text(TASK_MD)
    (td / "brief-01-order-fix.md").write_text(BRIEF_MD.format(status="READY"))
    git(r, "add", "-A"); git(r, "commit", "-qm", "init")
    return r

def run(script, repo, *args):
    return subprocess.run([sys.executable, str(SKILLS / script), *args], cwd=repo, capture_output=True, text=True)

def run_json(script, repo, *args):
    p = run(script, repo, *args, "--json")
    assert p.stdout.strip(), f"stdout kosong; stderr:\n{p.stderr}"
    assert "Traceback" not in p.stderr, p.stderr
    return json.loads(p.stdout)

def check(result, cid):
    return next(c for c in result["checks"] if c["id"] == cid)
```
`src/plugins/backenddev/tests/test_b4_audit.py` (scratch: 13 kasus lolos dengan patch; 8 gagal di kode `34684ee`):
```python
import json
import pytest
from conftest import check, run_json

AUDIT = "audit/scripts/check_preconditions.py"

def _set_source_root(repo, value):
    p = repo / ".claude" / "profile" / "index.json"; d = json.loads(p.read_text()); d["source_root"] = value; p.write_text(json.dumps(d))

def test_source_root_absolut_di_luar_repo_fail_rapi(repo, tmp_path):
    outside = tmp_path / "elsewhere" / "src"; outside.mkdir(parents=True)
    _set_source_root(repo, str(outside))
    r = run_json(AUDIT, repo, "--target-scope", "internal/order")      # tanpa traceback, stdout JSON
    assert check(r, 1)["status"] == "FAIL" and "di luar root" in check(r, 1)["summary"]

@pytest.mark.parametrize("scope", ["internal/expr/", "internal/pr/x", "internal/origin/y"])
def test_path_nyata_tidak_divonis_diff(repo, scope):
    (repo / scope).mkdir(parents=True, exist_ok=True)
    assert check(run_json(AUDIT, repo, "--target-scope", scope), 6)["status"] == "PASS"

@pytest.mark.parametrize("scope", ["main..HEAD", "main...feat/x", "origin/main", "refs/pull/12/head", "pr/12", "#12"])
def test_diff_atau_pr_divonis_diff(repo, scope):
    assert "diff branch/PR" in check(run_json(AUDIT, repo, "--target-scope", scope), 6)["summary"]

def test_path_relatif_keluar_repo_bukan_diff(repo, tmp_path):
    (tmp_path / "a1" / "internal").mkdir(parents=True)
    assert "di luar root" in check(run_json(AUDIT, repo, "--target-scope", "../a1/internal"), 6)["summary"]

def test_target_scope_wajib(repo):
    assert "REQUIRED" in check(run_json(AUDIT, repo), 6)["summary"]

def test_dimensi_asing_ditolak(repo):
    r = run_json(AUDIT, repo, "--target-scope", "internal/order", "--dimensions", "security,foo")
    assert check(r, 6)["status"] == "FAIL" and "foo" in check(r, 6)["summary"]
```
Jalankan: `cd src/plugins/backenddev && python -m pytest tests/test_b4_audit.py -q`.

### Selesai bila
Kelima contoh reproduksi memberi vonis benar: source_root luar → FAIL dengan JSON; `internal/expr/` dan `internal/origin/x` → PASS; `../a1/internal` dan path absolut luar → FAIL "di luar root"; `main..HEAD` → FAIL diff.

### Risiko & catatan
`audit/SKILL.md:20` tetap "6/6". Kolom action check 6 kini bercabang tiga (diff / luar repo / tidak ada), dan remediasi di `audit/SKILL.md:21` perlu frasa "target scope di luar repo → minta path di dalam repo".

---

## B5 [Sedang] Stacktrace dioper lewat argumen shell.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 1 jam · **Bergantung pada:** — (terkait B3 baris debug) · **Memblokir:** —

### Konteks
`symptom` berisi stacktrace mentah dari user. SKILL menyuruh model menempelkannya ke baris perintah Bash, padahal skrip tidak memakainya sama sekali (`debug/scripts/check_preconditions.py:40` hanya menyimpan).

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/debug/SKILL.md:18`:
```
1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/debug/scripts/check_preconditions.py [--symptom <symptom>] [--taskdir <taskdir>] [--scope-hint <scope_hint>]`.
```
`:33` "Jalankan skrip `check_preconditions.py` dengan parameter `symptom`, `taskdir`, dan `scope_hint`."

**Koreksi terhadap ISSUES.md:** SKILL tidak menulis `--symptom "<…>"` berkutip; slotnya `<symptom>` tanpa kutip. Cara mengutip diserahkan ke model, dan dua pilihannya sama-sama rusak (lihat reproduksi).

### Reproduksi
Aman (printf menggantikan skrip), `b5.sh`:
```bash
show() { printf '  argc=%s\n' "$#"; for a in "$@"; do printf '  [%s]\n' "$a"; done; }
echo "(1) kutip ganda"
show --symptom "java.lang.NullPointerException at com.acme.Order$Line.total(Order.java:42) caused by `echo INJECTED-$(id -un)`"
echo "(2) tanpa kutip"
show --symptom java.lang.IllegalStateException: order not found
echo "(3) tanpa kutip + kurung"
bash -c 'printf "%s\n" --symptom at Order.total(Order.java:42)' 2>&1 | sed 's/^/  /'
echo "(4) heredoc berkutip ke berkas"
cat > symptom.txt <<'EOF'
java.lang.NullPointerException at com.acme.Order$Line.total(Order.java:42) caused by `echo INJECTED`
EOF
printf '  [%s]\n' "$(cat symptom.txt)"
```
Output aktual:
```
(1) kutip ganda
  argc=2
  [--symptom]
  [java.lang.NullPointerException at com.acme.Order.total(Order.java:42) caused by INJECTED-fakhrulnugroho]
(2) tanpa kutip
  argc=5
  [--symptom]
  [java.lang.IllegalStateException:]
  [order]
  [not]
  [found]
(3) tanpa kutip + kurung
  bash: -c: line 1: syntax error near unexpected token `('
  bash: -c: line 1: `printf "%s\n" --symptom at Order.total(Order.java:42)'
(4) heredoc berkutip ke berkas
  [java.lang.NullPointerException at com.acme.Order$Line.total(Order.java:42) caused by `echo INJECTED`]
```
Terhadap skrip asli, kasus (2):
```
$ python3 $P/debug/scripts/check_preconditions.py --symptom java.lang.IllegalStateException: order not found --taskdir backenddev/docs/2609240900-order-fix
check_preconditions.py: error: unrecognized arguments: order not found
exit=2
```

### Dampak
- Kutip ganda: `$Line` (kelas dalam Java/Kotlin) lenyap, dan backtick/`$(…)` dari log user **tereksekusi** di shell user. Ini celah injeksi dari teks tak tepercaya.
- Tanpa kutip: exit 2 (bukan PASS/FAIL), atau syntax error shell. SKILL tidak punya jalur untuk keduanya.

### Rencana perbaikan
1. Hapus `--symptom` dari argparse `debug/scripts/check_preconditions.py:383` dan dari konstruktor (`:34`, `:40`, `:392`).
2. Teks pengganti `debug/SKILL.md:18`:
   ```
   1. Jalankan skrip verifikasi prasyarat: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/debug/scripts/check_preconditions.py --taskdir <taskdir> [--scope-hint <scope_hint>]`. **Jangan pernah menempelkan `symptom` ke baris perintah shell**: stacktrace memuat `$`, backtick, dan kurung yang diekspansi atau dieksekusi shell. Bila gejala perlu disimpan, tulis ke `{taskdir}/.explore/symptom.txt` lewat tool `Write`, bukan `echo`/heredoc.
   ```
3. `debug/SKILL.md:33` → "Jalankan skrip `check_preconditions.py` dengan parameter `taskdir` dan `scope_hint`. Kelayakan `symptom` (tidak kosong, memuat gejala terukur) dinilai di butir ini secara langsung, bukan oleh skrip."
4. Lint L6.3: tolak slot `<symptom>`/`<request>`/`<stacktrace>` di blok perintah `python3 …`.

### Test yang ditambahkan / Verifikasi manual
- pytest (**belum dijalankan**): `run("debug/scripts/check_preconditions.py", repo, "--symptom", "x")` → `returncode == 2` (argumen dihapus); tanpa `--symptom` → PASS pada fixture lengkap.
- Manual: baca SKILL, pastikan tidak ada lagi slot teks bebas di blok perintah.

### Selesai bila
Tidak ada perintah Bash di skill debug yang memuat `symptom`, dan skrip menolak `--symptom`.

### Risiko & catatan
Opsi alternatif `--symptom-file <path>` (validasi berkas ada dan tidak kosong) menambah satu cek mekanis kecil, tapi memaksa model menulis berkas. Usulan: hapus saja, karena skrip tidak pernah memakai isinya.

---
## B6 [Sedang] Filter `.explore` terlalu luas; state git khusus tak terdeteksi.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 4 jam · **Bergantung pada:** L5.5 (`dirty_paths` di `_common`), L6.1 · **Memblokir:** B3 (helper yang sama)

### Konteks
Laci `.explore/` adalah zona kerja `code-explorer` yang sengaja tidak dihitung kotor. Masalahnya, filter membuang **setiap** segmen path bernama `.explore` di mana pun, termasuk sisi baru dari sebuah rename. Selain itu hanya architect yang memeriksa rebase, dan tidak ada skrip yang memeriksa merge/cherry-pick/revert yang menggantung dengan tree bersih.

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/architect/scripts/check_preconditions.py:28-37` (identik di `report/scripts/check_preconditions.py:28-37`):
```python
    for line in status_out.splitlines():
        ...
        path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ")[-1]          # hanya sisi BARU rename yang dinilai
        path = path.strip().strip('"')
        if ".explore" in path.rstrip("/").split("/"):   # :35 — segmen .explore di mana pun
            continue
```
Architect `:330-347` hanya mengecek `rebase-apply`/`rebase-merge`. Report tidak punya cek operasi git sama sekali (`:346-381`).

**Temuan tambahan:** filter segmen yang sama ada di `analyst/scripts/check_preconditions.py:385`, `task/scripts/check_preconditions.py:386`, dan `tech-lead/scripts/check_preconditions.py:243`.

### Reproduksi
```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); bash "$FX" $tmp/r >/dev/null; cd $tmp/r; T=backenddev/docs/2609240900-order-fix
mkdir -p internal/.explore; printf 'package q\n' > internal/.explore/q.go; git add -A; git commit -qm tracked
printf '// ubah\n' >> internal/.explore/q.go; git status --porcelain
python3 $P/architect/scripts/check_preconditions.py --taskdir $T | grep '^\[4\]'; git checkout -q -- internal/.explore/q.go
mkdir -p $T/.explore; git mv internal/order/service.go $T/.explore/service.go; git status --porcelain
python3 $P/architect/scripts/check_preconditions.py --taskdir $T | grep '^\[4\]'; git reset -q --hard
git checkout -q -b other; printf 'x\n' > note.txt; git add note.txt; git commit -qm other; git checkout -q main
printf 'x\n' > note.txt; git add note.txt; git commit -qm same
git cherry-pick other >/dev/null 2>&1; ls .git/CHERRY_PICK_HEAD; git status --porcelain | wc -l
python3 $P/architect/scripts/check_preconditions.py --taskdir $T | grep '^\[4\]'; git cherry-pick --skip 2>/dev/null
git merge --no-commit -s ours other >/dev/null 2>&1; ls .git/MERGE_HEAD; git status --porcelain | wc -l
python3 $P/architect/scripts/check_preconditions.py --taskdir $T | grep '^\[4\]'; git merge --abort
```
Output aktual:
```
 M internal/.explore/q.go
[4] Git Worktree & Status            : PASS (Working tree bersih dan siap dieksekusi)
R  internal/order/service.go -> backenddev/docs/2609240900-order-fix/.explore/service.go
[4] Git Worktree & Status            : PASS (Working tree bersih dan siap dieksekusi)
.git/CHERRY_PICK_HEAD
0
[4] Git Worktree & Status            : PASS (Working tree bersih dan siap dieksekusi)
.git/MERGE_HEAD
0
[4] Git Worktree & Status            : PASS (Working tree bersih dan siap dieksekusi)
```
Report saat rebase berhenti di `edit` (branch kerja, dua commit, `GIT_SEQUENCE_EDITOR="sed -i '1s/^pick/edit/'" git rebase -i HEAD~1`):
```
.git/rebase-merge
  baris porcelain: 0
PRECONDITION CHECK: report [PASS] (7/7 passed)
[4] Git Worktree & Status            : FAIL (Operasi git rebase sedang berlangsung)      ← architect pada repo yang sama
```
Report dengan rename staged ke laci juga `[PASS] (7/7 passed)`.

### Dampak
- Perubahan pada kode ter-track di direktori bernama `.explore` (atau penghapusan `internal/order/service.go` yang disamarkan sebagai rename ke laci) lolos gerbang. Implementor/report lalu meng-commit di atas tree yang tidak bersih, dan commit agregat berikutnya bisa ikut membawa penghapusan itu.
- Commit implementor di tengah merge/cherry-pick yang menggantung menghasilkan merge commit tak sengaja (MERGE_HEAD ikut jadi parent) atau riwayat membingungkan. Report bisa menulis REPORT.md di tengah rebase (HEAD detached).

### Rencana perbaikan
1. `src/plugins/backenddev/skills/_common/precondition_lib.py` — tambah helper (menjadi bagian L5.5):
   - `git_dirty_paths(root, scratch_dirs)`: `git -c core.quotePath=false status --porcelain=v1 -z -uall`. Entri diabaikan **hanya** bila semua path-nya (termasuk path asal rename/copy) berada di bawah `{taskdir}/.explore/` atau `backenddev/docs/.explore/`.
   - `git_operation_in_progress(root)`: cek `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `rebase-merge`, `rebase-apply`, `sequencer`, `BISECT_LOG` lewat `git rev-parse --git-path` (benar juga di worktree tambahan).
   - `check_base_branch(...)` (B3).
2. architect check 4 dan report check 7 memakai keduanya. Hapus `_strip_explore_scratch` dari architect dan report.
3. analyst `:385`, task `:386`, tech-lead `:243`: ganti ke `git_dirty_paths` dengan `scratch_dirs` yang sesuai (tech-lead: `backenddev/docs/.explore/` + laci taskdir bila ada).

Diff helper (`b6_lib.diff`, diuji di scratch):
```diff
--- a/src/plugins/backenddev/skills/_common/precondition_lib.py
+++ b/src/plugins/backenddev/skills/_common/precondition_lib.py
@@ -105,3 +105,105 @@
         f"{n} commit menyentuh '{sr}' sesudah profil terakhir diperbarui — "
         "batas cakupan explorer dan daftar permukaan berpotensi tertinggal"
     )
+
+
+# --- status git (B3, B6) -------------------------------------------------
+
+import subprocess as _sp  # noqa: E402
+from typing import List, Optional, Sequence  # noqa: E402
+
+# Penanda operasi git yang belum selesai. Dicari lewat `git rev-parse --git-path`
+# supaya benar juga di worktree tambahan, tempat `.git` berupa berkas.
+GIT_OPERATION_MARKERS = (
+    ("MERGE_HEAD", "merge"),
+    ("CHERRY_PICK_HEAD", "cherry-pick"),
+    ("REVERT_HEAD", "revert"),
+    ("rebase-merge", "rebase"),
+    ("rebase-apply", "rebase/am"),
+    ("sequencer", "sequencer (cherry-pick/revert beruntun)"),
+    ("BISECT_LOG", "bisect"),
+)
+
+
+def _git(root: Path, *args: str, strip: bool = True) -> Tuple[int, str]:
+    try:
+        r = _sp.run(["git", "-C", str(root), *args], capture_output=True, timeout=15)
+    except (OSError, _sp.SubprocessError) as exc:
+        return 255, str(exc)
+    out = r.stdout.decode("utf-8", "surrogateescape")
+    return r.returncode, out.strip() if strip else out
+
+
+def git_operation_in_progress(root: Path) -> List[str]:
+    """Label operasi git yang masih menggantung (kosong = tidak ada)."""
+    found: List[str] = []
+    for marker, label in GIT_OPERATION_MARKERS:
+        rc, out = _git(root, "rev-parse", "--git-path", marker)
+        if rc != 0 or not out:
+            continue
+        p = Path(out)
+        if not p.is_absolute():
+            p = root / p
+        if p.exists():
+            found.append(label)
+    return found
+
+
+def git_dirty_paths(root: Path, scratch_dirs: Sequence[str] = ()) -> List[str]:
+    """Path kotor dari `git status --porcelain=v1 -z -uall`.
+
+    Entri diabaikan HANYA bila seluruh path-nya (termasuk path asal rename/copy)
+    berada di bawah salah satu `scratch_dirs` (relatif root, mis.
+    `backenddev/docs/2609240900-x/.explore/`). Segmen `.explore` di tempat lain
+    tetap dihitung kotor.
+    """
+    prefixes = [d.rstrip("/") + "/" for d in scratch_dirs if d]
+    # strip=False: kolom XY diawali spasi (" M path") dan wajib utuh.
+    rc, out = _git(root, "-c", "core.quotePath=false", "status", "--porcelain=v1", "-z", "-uall", strip=False)
+    if rc != 0:
+        raise RuntimeError(f"git status gagal (exit {rc}): {out}")
+    entries = out.split("\0")
+    dirty: List[str] = []
+    i = 0
+    while i < len(entries):
+        entry = entries[i]
+        i += 1
+        if len(entry) < 4:
+            continue
+        xy, path = entry[:2], entry[3:]
+        paths = [path]
+        if "R" in xy or "C" in xy:          # format -z: "XY <baru>\0<asal>\0"
+            if i < len(entries):
+                paths.append(entries[i])
+            i += 1
+        if prefixes and all(any(p.startswith(pre) for pre in prefixes) for p in paths):
+            continue
+        dirty.append(" <- ".join(paths))
+    return dirty
+
+
+def check_base_branch(root: Path, base: Optional[str], require_diff: bool = False) -> Tuple[bool, str]:
+    """Validasi `base_branch` dan posisi HEAD untuk skill yang menilai diff merge-base.
+
+    Mengembalikan (ok, keterangan). Urutan: base resolve → HEAD ter-attach →
+    HEAD bukan base → merge-base ada → (opsional) ada commit di atas base.
+    """
+    base = (base or "").strip()
+    if not base:
+        return False, "base_branch kosong di parameter maupun index.json"
+    rc, _ = _git(root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
+    if rc != 0:
+        return False, f"base_branch '{base}' tidak resolve ke commit"
+    rc, head = _git(root, "symbolic-ref", "-q", "--short", "HEAD")
+    if rc != 0 or not head:
+        return False, "HEAD detached — rantai wajib berjalan di branch kerja"
+    if head == base:
+        return False, f"HEAD berada di base_branch '{base}' — rantai wajib berjalan di branch kerja"
+    rc, mb = _git(root, "merge-base", base, "HEAD")
+    if rc != 0 or not mb:
+        return False, f"tidak ada merge-base antara '{base}' dan HEAD"
+    if require_diff:
+        _, head_sha = _git(root, "rev-parse", "HEAD")
+        if mb == head_sha:
+            return False, f"nol commit di atas '{base}' (merge-base = HEAD)"
+    return True, f"branch '{head}' · merge-base {mb[:7]} terhadap '{base}'"
```
Diff architect (`b3b6_architect.diff`, mencakup check 7 B3):
```diff
--- a/src/plugins/backenddev/skills/architect/scripts/check_preconditions.py
+++ b/src/plugins/backenddev/skills/architect/scripts/check_preconditions.py
@@ -15,27 +15,12 @@
 import sys
 from typing import Any, Dict, List, Optional
 
-
-def _strip_explore_scratch(status_out: str) -> str:
-    """Buang baris `git status --porcelain` yang menunjuk laci kerja `.explore/`.
-
-    `code-explorer` menulis laporannya ke `<taskdir>/.explore/<slug>.md` (dan
-    `backenddev/docs/.explore/` untuk dispatch gerbang). Laci itu zona kerja,
-    bukan artefak rantai: tidak pernah di-stage maupun di-commit, sehingga
-    kehadirannya tidak boleh dihitung sebagai working tree kotor.
-    """
-    kept = []
-    for line in status_out.splitlines():
-        if not line.strip():
-            continue
-        path = line[3:] if len(line) > 3 else line.strip()
-        if " -> " in path:
-            path = path.split(" -> ")[-1]
-        path = path.strip().strip('"')
-        if ".explore" in path.rstrip("/").split("/"):
-            continue
-        kept.append(line)
-    return "\n".join(kept)
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
+from precondition_lib import (  # noqa: E402
+    check_base_branch,
+    git_dirty_paths,
+    git_operation_in_progress,
+)
 
 
 class PreconditionChecker:
@@ -72,6 +57,7 @@
         self._check_4_git_worktree()
         self._check_5_dispatchers()
         self._check_6_lifecycle_recovery()
+        self._check_7_base_branch()
         return all(r["status"] == "PASS" for r in self.results)
 
     def _resolve_taskdir(self) -> Optional[Path]:
@@ -311,38 +297,28 @@
                 })
                 return
 
-            status = _strip_explore_scratch(subprocess.check_output(
-                ["git", "status", "--porcelain"],
-                cwd=self.root,
-                stderr=subprocess.DEVNULL,
-                universal_newlines=True,
-            )).strip()
-            if status:
+            rel_td = self._get_rel_taskdir_str()
+            scratch = ["backenddev/docs/.explore/"] + ([f"{rel_td}/.explore/"] if rel_td else [])
+            dirty = git_dirty_paths(self.root, scratch)
+            if dirty:
+                sample = ", ".join(dirty[:3]) + (f", +{len(dirty) - 3} lainnya" if len(dirty) > 3 else "")
                 self.results.append({
                     "id": check_id,
                     "name": name,
                     "status": "FAIL",
-                    "summary": "Working tree git kotor sebelum rantai orkestrasi dimulai",
+                    "summary": f"Working tree git kotor sebelum rantai orkestrasi dimulai ({sample})",
                     "action": "Bersihkan atau simpan perubahan uncommitted sebelum memulai orkestrasi architect.",
                 })
                 return
 
-            # Check rebase in progress
-            git_dir = Path(subprocess.check_output(
-                ["git", "rev-parse", "--git-dir"],
-                cwd=self.root,
-                stderr=subprocess.DEVNULL,
-                universal_newlines=True,
-            ).strip())
-            if not git_dir.is_absolute():
-                git_dir = self.root / git_dir
-            if (git_dir / "rebase-apply").exists() or (git_dir / "rebase-merge").exists():
+            ops = git_operation_in_progress(self.root)
+            if ops:
                 self.results.append({
                     "id": check_id,
                     "name": name,
                     "status": "FAIL",
-                    "summary": "Operasi git rebase sedang berlangsung",
-                    "action": "Selesaikan atau batalkan git rebase sebelum melanjutkan.",
+                    "summary": f"Operasi git belum selesai: {', '.join(ops)}",
+                    "action": "Selesaikan atau batalkan operasi itu (`--continue`/`--abort`) sebelum melanjutkan.",
                 })
                 return
 
@@ -465,6 +441,24 @@
             "action": "",
         })
 
+    def _check_7_base_branch(self):
+        check_id = 7
+        name = "Base Branch & HEAD"
+        base = self.base_branch_arg
+        if not base:
+            try:
+                base = json.loads((self.root / ".claude" / "profile" / "index.json").read_text(encoding="utf-8")).get("base_branch")
+            except Exception:
+                base = None
+        ok, detail = check_base_branch(self.root, base)
+        self.results.append({
+            "id": check_id,
+            "name": name,
+            "status": "PASS" if ok else "FAIL",
+            "summary": detail,
+            "action": "" if ok else "Pindah ke branch kerja taskdir (gerbang `backenddev:tech-lead` Fase 3) atau perbaiki `base_branch`; dilarang menebak acuan diff.",
+        })
+
     def format_text(self) -> str:
         all_passed = all(r["status"] == "PASS" for r in self.results)
         passed_count = sum(1 for r in self.results if r["status"] == "PASS")
```
Diff report (`b3b6_report.diff`, mencakup check 8 B3):
```diff
--- a/src/plugins/backenddev/skills/report/scripts/check_preconditions.py
+++ b/src/plugins/backenddev/skills/report/scripts/check_preconditions.py
@@ -16,26 +16,12 @@
 from typing import Any, Dict, List, Optional
 
 
-def _strip_explore_scratch(status_out: str) -> str:
-    """Buang baris `git status --porcelain` yang menunjuk laci kerja `.explore/`.
-
-    `code-explorer` menulis laporannya ke `<taskdir>/.explore/<slug>.md` (dan
-    `backenddev/docs/.explore/` untuk dispatch gerbang). Laci itu zona kerja,
-    bukan artefak rantai: tidak pernah di-stage maupun di-commit, sehingga
-    kehadirannya tidak boleh dihitung sebagai working tree kotor.
-    """
-    kept = []
-    for line in status_out.splitlines():
-        if not line.strip():
-            continue
-        path = line[3:] if len(line) > 3 else line.strip()
-        if " -> " in path:
-            path = path.split(" -> ")[-1]
-        path = path.strip().strip('"')
-        if ".explore" in path.rstrip("/").split("/"):
-            continue
-        kept.append(line)
-    return "\n".join(kept)
+sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
+from precondition_lib import (  # noqa: E402
+    check_base_branch,
+    git_dirty_paths,
+    git_operation_in_progress,
+)
 
 
 class PreconditionChecker:
@@ -73,6 +59,7 @@
         self._check_5_profile_config()
         self._check_6_report_absence()
         self._check_7_git_clean()
+        self._check_8_base_branch()
         return all(r["status"] == "PASS" for r in self.results)
 
     def _resolve_taskdir(self) -> Optional[Path]:
@@ -347,20 +334,20 @@
         check_id = 7
         name = "Git Working Tree Cleanliness"
         try:
-            status = _strip_explore_scratch(subprocess.check_output(
-                ["git", "status", "--porcelain"],
-                cwd=self.root,
-                stderr=subprocess.DEVNULL,
-                universal_newlines=True,
-            )).strip()
-
-            if status:
+            rel_td = self._get_rel_taskdir_str()
+            scratch = ["backenddev/docs/.explore/"] + ([f"{rel_td}/.explore/"] if rel_td else [])
+            dirty = git_dirty_paths(self.root, scratch)
+            ops = git_operation_in_progress(self.root)
+            if dirty or ops:
+                why = (f"berkas kotor: {', '.join(dirty[:3])}" if dirty else "") + \
+                      ("; " if dirty and ops else "") + \
+                      (f"operasi git belum selesai: {', '.join(ops)}" if ops else "")
                 self.results.append({
                     "id": check_id,
                     "name": name,
                     "status": "FAIL",
-                    "summary": "Working tree git kotor sebelum penulisan REPORT.md",
-                    "action": "Bersihkan atau commit perubahan git sebelum merumuskan REPORT.md.",
+                    "summary": f"Working tree git tidak siap sebelum penulisan REPORT.md ({why})",
+                    "action": "Bersihkan/commit perubahan dan selesaikan operasi git yang menggantung sebelum merumuskan REPORT.md.",
                 })
                 return
 
@@ -380,6 +367,24 @@
                 "action": "Pastikan git repo valid.",
             })
 
+    def _check_8_base_branch(self):
+        check_id = 8
+        name = "Base Branch & Merge-Base Diff"
+        base = self.base_branch_arg
+        if not base:
+            try:
+                base = json.loads((self.root / ".claude" / "profile" / "index.json").read_text(encoding="utf-8")).get("base_branch")
+            except Exception:
+                base = None
+        ok, detail = check_base_branch(self.root, base, require_diff=True)
+        self.results.append({
+            "id": check_id,
+            "name": name,
+            "status": "PASS" if ok else "FAIL",
+            "summary": detail,
+            "action": "" if ok else "REPORT.md menuntut diff merge-base yang nyata di branch kerja; perbaiki `base_branch` atau jalankan dari branch taskdir.",
+        })
+
     def format_text(self) -> str:
         all_passed = all(r["status"] == "PASS" for r in self.results)
         passed_count = sum(1 for r in self.results if r["status"] == "PASS")
```

### Test yang ditambahkan / Verifikasi manual
`src/plugins/backenddev/tests/test_b6_git_state.py` (scratch: 7/7 lolos dengan patch; berkas gagal diimpor di kode `34684ee` karena helper belum ada):
```python
import subprocess, sys
import pytest
from conftest import SKILLS, TASKDIR, BRIEF_MD, check, git, run_json
ARCH = "architect/scripts/check_preconditions.py"; REPORT = "report/scripts/check_preconditions.py"
sys.path.insert(0, str(SKILLS / "_common"))
from precondition_lib import git_dirty_paths, git_operation_in_progress

@pytest.fixture
def branch(repo):
    git(repo, "checkout", "-q", "-b", "feat/order-fix"); return repo

def test_laci_taskdir_diabaikan(branch):
    laci = branch / TASKDIR / ".explore"; laci.mkdir(); (laci / "slug-01.md").write_text("x")
    assert git_dirty_paths(branch, [f"{TASKDIR}/.explore/"]) == []
    assert check(run_json(ARCH, branch, "--taskdir", TASKDIR), 4)["status"] == "PASS"

def test_explore_di_luar_taskdir_tetap_kotor(branch):
    d = branch / "internal" / ".explore"; d.mkdir(); (d / "q.go").write_text("package q\n")
    git(branch, "add", "-A"); git(branch, "commit", "-qm", "tracked")
    (d / "q.go").write_text("package q\n// ubah\n")
    r = run_json(ARCH, branch, "--taskdir", TASKDIR)
    assert check(r, 4)["status"] == "FAIL" and "internal/.explore/q.go" in check(r, 4)["summary"]

def test_rename_staged_ke_laci_tetap_kotor(branch):
    (branch / TASKDIR / ".explore").mkdir()
    git(branch, "mv", "internal/order/service.go", f"{TASKDIR}/.explore/service.go")
    assert git_dirty_paths(branch, [f"{TASKDIR}/.explore/"]) == [f"{TASKDIR}/.explore/service.go <- internal/order/service.go"]
    assert check(run_json(REPORT, branch, "--taskdir", TASKDIR), 7)["status"] == "FAIL"

def test_path_berspasi_dan_unicode(branch):
    (branch / "internal" / "café dir").mkdir(); (branch / "internal" / "café dir" / "a b.go").write_text("x")
    assert git_dirty_paths(branch) == ["internal/café dir/a b.go"]

def test_cherry_pick_kosong_terdeteksi(branch):
    git(branch, "checkout", "-q", "-b", "other"); (branch / "note.txt").write_text("x\n")
    git(branch, "add", "note.txt"); git(branch, "commit", "-qm", "other"); git(branch, "checkout", "-q", "feat/order-fix")
    (branch / "note.txt").write_text("x\n"); git(branch, "add", "note.txt"); git(branch, "commit", "-qm", "same")
    subprocess.run(["git", "-C", str(branch), "cherry-pick", "other"], capture_output=True)
    assert "cherry-pick" in git_operation_in_progress(branch)
    assert check(run_json(ARCH, branch, "--taskdir", TASKDIR), 4)["status"] == "FAIL"

def test_merge_no_commit_terdeteksi(branch):
    git(branch, "checkout", "-q", "-b", "other"); (branch / "o.txt").write_text("o\n")
    git(branch, "add", "o.txt"); git(branch, "commit", "-qm", "o"); git(branch, "checkout", "-q", "feat/order-fix")
    git(branch, "merge", "--no-commit", "-s", "ours", "other")
    assert git_operation_in_progress(branch) == ["merge"]
    assert check(run_json(ARCH, branch, "--taskdir", TASKDIR), 4)["status"] == "FAIL"

def test_report_mendeteksi_rebase_edit(branch):
    td = branch / TASKDIR
    (td / "brief-01-order-fix.md").write_text(BRIEF_MD.format(status="DONE")); (td / "REVIEW.md").write_text("# Review\n")
    git(branch, "add", "-A"); git(branch, "commit", "-qm", "c1")
    (branch / "a.txt").write_text("a\n"); git(branch, "add", "a.txt"); git(branch, "commit", "-qm", "c2")
    subprocess.run(["git", "-C", str(branch), "rebase", "-q", "-i", "HEAD~1"], capture_output=True,
                   env={"GIT_SEQUENCE_EDITOR": "sed -i 1s/^pick/edit/", "PATH": "/usr/bin:/bin"})
    assert "rebase" in git_operation_in_progress(branch)
    assert check(run_json(REPORT, branch, "--taskdir", TASKDIR), 7)["status"] == "FAIL"
```
Output sesudah patch (scratch), rename staged:
```
[4] Git Worktree & Status            : FAIL (Working tree git kotor sebelum rantai orkestrasi dimulai (backenddev/docs/2609240900-order-fix/.explore/service.go <- internal/order/service.go))
```

### Selesai bila
Keenam skenario reproduksi (dua path `.explore`, cherry-pick, merge, rebase di report, rename di report) menghasilkan FAIL; laci taskdir tetap diabaikan; grep filter segmen `.explore` di `skills/*/scripts/*.py` kosong.

### Risiko & catatan
- `-uall` mendaftar tiap berkas untracked. Di repo dengan direktori untracked raksasa (misal `node_modules/` yang tidak di-ignore) daftarnya panjang, tapi hanya 3 contoh yang dicetak.
- Laci gerbang `backenddev/docs/.explore/` tetap diabaikan di semua skrip, sesuai `src/plugins/backenddev/skills/tech-lead/references/gate-scope.md:69`.

---
## B7 [Sedang] Kontrak mati/kontradiktif.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** B3 (document-api wajib profil), L5.5 (hapus path `.gemini`) · **Memblokir:** —

### Konteks
Tiga kontrak antara instruksi dan skrip tidak tersambung: (a) debug, (b) document-api, (c) profile di repo non-git.

### Lokasi & kode saat ini
**(a) debug & `## Failure signatures`.** `src/plugins/backenddev/skills/profile/stacks/_CONTRACT.md:110` mendeklarasikan "### 7. `## Failure signatures` — konsumen: `backenddev:debug`". Ketujuh adapter memuat seksi itu (`go.md:249`, `java-spring.md:201`, `node.md:187`, `bun.md:184`, `rust.md:263`, `php.md:191`, `php-codeigniter.md:184`). Namun `debug/SKILL.md` dan `debug/dispatcher/explorer.md` tidak pernah menyebut adapter maupun seksi itu (mdcp `md_search "adapter|stacks/"` di `skills/debug/**` hanya menemukan remediasi `SKILL.md:21`). Skripnya mengklaim sebaliknya, `debug/scripts/check_preconditions.py:186-202`:
```python
        found = any(p.exists() for p in candidate_paths)      # hanya cek berkas ada
        ...
            "summary": f"Adapter stack '{stack_id}' memuat seksi failure signatures",
```
**(b) document-api & `## API surface`.** `document-api/SKILL.md` Fase 1 butir 1 ("memakai pola dari `## API surface` adapter"), Fase 3 butir 2 dan 5 merujuk "adapter" tanpa pernah menyebut path `../profile/stacks/<stack>.md` atau cara menentukan `stack`.

**(c) profile non-git.** `profile/SKILL.md:158` "| Repositori non-git | Lanjutkan dengan field konvensi git `tidak terdeteksi` dan peringatan kebutuhan input manual. |" dan Fase 5 butir 1 (`:88`) "Bila gagal, catat status non-git dan tulis `commit_convention`, `base_branch`, serta `branch_convention` sebagai `tidak terdeteksi`." Bertentangan dengan `profile/SKILL.md:19` "bukan repo git → inisialisasi git" dan `profile/scripts/check_preconditions.py:165-199` (check 4 FAIL).

### Reproduksi
(c), dijalankan di scratch:
```bash
tmp=$(mktemp -d); mkdir -p $tmp/ng && cd $tmp/ng && printf 'module x\n' > go.mod
python3 $P/profile/scripts/check_preconditions.py | sed -n '1p;5,6p'
```
```
PRECONDITION CHECK: profile [FAIL] (4/5 passed)
[4] Git Inspection Access            : FAIL (Gagal membaca status git: Command '['git', 'rev-parse', '--is-inside-work-tree']' returned non-zero exit status 128.)
    * Tindakan: Pastikan git CLI tersedia.
```
(a) dan (b): tidak relevan untuk direproduksi (teks tidak menyebut sumber). Bukti dari mdcp di atas.

### Dampak
- (a) Debug menyusun hipotesis tanpa pola kegagalan khas stack yang sudah ditulis tim. Pesan PASS skrip menyesatkan.
- (b) Model menebak lokasi adapter atau mengarang pola deklarasi endpoint.
- (c) Profil repo non-git tidak pernah bisa dibuat, meskipun SKILL merancang jalurnya. Pesan remediasinya salah (git CLI ada, repo-nya yang bukan git).

### Rencana perbaikan
1. `src/plugins/backenddev/skills/debug/SKILL.md` Fase 1: sisipkan butir baru sebelum butir 1 (nomor lain bergeser):
   ```
   1. Baca `.claude/profile/index.json` (`stack`) lalu seksi `## Failure signatures` adapter `../profile/stacks/<stack>.md`: format stacktrace, frame paling informatif, dan pola akar masalah lazim di stack ini. Pakai ketiganya saat memecah gejala (butir 2) dan sebagai kandidat hipotesis Fase 3; pola yang dipakai disebut sumbernya.
   ```
2. `debug/scripts/check_preconditions.py` check 3: selain berkas ada, cek heading:
   ```python
   adapter = next((p for p in candidate_paths if p.exists()), None)
   text = adapter.read_text(encoding="utf-8") if adapter else ""
   if not re.search(r"^## Failure signatures\s*$", text, re.MULTILINE):
       FAIL(f"Adapter stacks/{stack_id}.md tanpa seksi ## Failure signatures", "Pulihkan adapter sesuai stacks/_CONTRACT.md bagian 7.")
   ```
   (hapus kandidat `~/.gemini` dan `self.root/src/plugins/...` sesuai L5.5).
3. `document-api/SKILL.md` Fase 0: sisipkan butir sesudah butir 1:
   ```
   2. Baca `stack` dari `.claude/profile/index.json`, lalu seksi `## API surface` adapter `../profile/stacks/<stack>.md`. Seluruh rujukan "`## API surface` adapter" di Fase 1 dan Fase 3 menunjuk seksi ini. Adapter atau seksinya tidak ada → `BLOCKED`, rutekan ke `backenddev:profile`.
   ```
   Skrip check 2 ikut menilai heading `## API surface` (pola sama dengan butir 2).
4. Profile non-git — skrip `profile/scripts/check_preconditions.py` check 4:
   ```python
   try:
       r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=self.root, capture_output=True, text=True)
       inside = r.returncode == 0 and r.stdout.strip() == "true"
   except FileNotFoundError:
       inside = False
   self.results.append({"id": 4, "name": "Git Inspection Access", "status": "PASS",
       "summary": "Repositori git valid" if inside else
                  "Bukan repositori git — Fase 5 menulis commit_convention/base_branch/branch_convention `tidak terdeteksi`",
       "action": ""})
   ```
   Teks `profile/SKILL.md:19`: hapus "bukan repo git → inisialisasi git". Ringkasan check 4 ikut dilaporkan di laporan penutup.

### Test yang ditambahkan / Verifikasi manual
pytest (**belum dijalankan**):
- profile di `tmp_path` tanpa `git init` + `go.mod` → `check(r, 4)["status"] == "PASS"` dan `"tidak terdeteksi" in summary`.
- debug dengan adapter salinan tanpa `## Failure signatures` (plugin di-copy ke `tmp_path`, env `BACKENDDEV_ROOT`) → check 3 FAIL.

### Selesai bila
Debug dan document-api menyebut path adapter serta seksi yang dibaca; skrip memverifikasi seksinya; profile di repo non-git lolos prasyarat dengan catatan.

### Risiko & catatan
Profil non-git akan ditolak tech-lead (`base_branch` `tidak terdeteksi`, Failure path 1). Itu perilaku yang diinginkan: profil boleh ada, rantai eksekusi tidak.

---

## B8 [Sedang] Predikat analyst menolak Approved yang sah.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 1 jam · **Bergantung pada:** — · **Memblokir:** gerbang dokumen analyst Fase 4 untuk review bersih

### Konteks
`analyst` Fase 4 butir 0 memeriksa blok review sebagai predikat keaslian: harus ada jejak konkret, atau string persis `Approved — nol temuan`. Format output kedua reviewer tidak pernah menghasilkan string itu.

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/analyst/references/chain-rules.md:153`:
> "…tambahkan predikat kedua yang dapat diperiksa di sini: **blok review wajib menyebut jejak konkret** — minimal satu ID temuan, nama seksi, atau `file:baris` — atau berbunyi persis `Approved — nol temuan`. Blok berisi prosa pujian tanpa satu pun jejak ditolak sebagai balikan rusak lewat `## Failure path` butir 3…"

`src/plugins/backenddev/agents/brd-reviewer.md:38-47` (sama di `prd-reviewer.md:42-51`):
```markdown
## BRD Review

**Status:** Approved | Issues Found

**Issues (jika ada):**
- [Seksi / BR-n / EC-n / Aktor / Kategori]: [deskripsi isu spesifik] - [alasan …]

**Recommendations (advisory, tidak menahan approval):**
- [saran penyempurnaan redaksional/non-blocking]
```
mdcp `md_search "nol temuan"` di `skills/**` dan `agents/*-reviewer.md`: string itu hanya ada di `chain-rules.md:153`.

### Reproduksi
Tidak relevan (kontrak teks). Hasil bersih yang patuh format reviewer — `**Status:** Approved`, Issues kosong, tanpa Recommendations — tidak memuat ID, nama seksi, `file:baris`, maupun `Approved — nol temuan`, sehingga jatuh ke "balikan rusak".

### Dampak
Dokumen yang bersih sejak ronde 1 justru ditahan sebagai hop rusak (Failure path 3), sementara dokumen dengan satu rekomendasi kosmetik lolos. Model terdorong mengarang rekomendasi supaya lolos predikat.

### Rencana perbaikan
1. `agents/brd-reviewer.md:41` dan `agents/prd-reviewer.md:45`, ganti baris status dan tambahkan aturan di bawah blok:
   ```markdown
   **Status:** Approved — nol temuan | Approved | Issues Found
   ```
   ```
   Tanpa satu pun isu → baris status ditulis persis `**Status:** Approved — nol temuan` dan blok `**Issues (jika ada):**` dihapus. `Approved` (tanpa "nol temuan") hanya dipakai bila ada `Recommendations`, dan tiap rekomendasi dibuka ID atau nama seksinya dalam kurung siku.
   ```
2. `analyst/references/chain-rules.md:153`: ganti "atau berbunyi persis `Approved — nol temuan`" menjadi "atau baris statusnya berbunyi persis `**Status:** Approved — nol temuan` (format output `agents/brd-reviewer.md`/`agents/prd-reviewer.md`)".
3. Opsional, bila B12 dikerjakan: `validate_doc.py --review-block <berkas>` menagih predikat ini secara mekanis.

### Test yang ditambahkan / Verifikasi manual
Manual: dispatch `brd-reviewer` atas BRD contoh terisi `brd-template.md` bagian "Contoh terisi"; balikan bersih memuat baris persis itu, dan analyst Fase 4 butir 0 meloloskannya.

### Selesai bila
String predikat identik di `chain-rules.md` dan kedua format reviewer.

### Risiko & catatan
`brief-reviewer` memakai format yang sama, tetapi bukan objek predikat analyst. Tidak perlu diubah kecuali ingin seragam.

---

## B9 [Sedang] Alat ukur `PRD_CONVERSION` saling bertentangan.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 1 jam · **Bergantung pada:** keputusan user · **Memblokir:** B12 (butir 3 validator TASK)

### Konteks
Tabel Fase 3 `task` menetapkan alat ukur per lane. Self-test akar butir 3 menagih kecocokan dengan tabel itu sambil melarang rujukan ke dokumen hilir yang belum terbit. Untuk `PRD_CONVERSION` kedua aturan tidak bisa dipenuhi bersamaan.

### Lokasi & kode saat ini
| Sumber | Kutipan |
|---|---|
| `src/plugins/backenddev/skills/task/SKILL.md:58` | "\| `PRD_CONVERSION` \| … \| `AC-{n}` PRD yang berakar padanya mendarat di brief pengklaim, dan berkas test pemikul AC itu ada di `## File scope`-nya — sebut permukaannya … \|" |
| `src/plugins/backenddev/skills/task/SKILL.md:64-65` | "**Sumber kriteria tidak pernah dokumen yang belum terbit.** … Kolom alat ukur menyebut brief `READY` karena brief adalah ujung rantai planning…" |
| `src/plugins/backenddev/skills/task/templates/task-template.md:56` | "tiap butir memuat literal `— verifikasi:` diikuti alat ukur yang terdaftar di kolom \"Alat ukur yang sah\" … Alat ukur … yang tidak cocok dengan lane-nya, atau yang menunjuk dokumen hop hilir yang belum terbit (`BRD.md`, `PRD.md`) adalah kegagalan." |
| `src/plugins/backenddev/skills/task/templates/task-template.md:96` (contoh `lane: PRD_CONVERSION`) | "`- [ ] **SC-1**: … — verifikasi: `TestCancelPaidOrder` hijau`" |
| `src/plugins/backenddev/skills/analyst/references/chain-rules.md:131` | "Tulis ulang klausa `— verifikasi:` tiap `SC-{n}` agar cocok dengan kolom alat ukur lane baru…" |

### Reproduksi
Tidak relevan (teks). Dua jalan penulis sama-sama gagal butir 3: menulis "`AC-{n}` PRD mendarat di brief" berarti menunjuk PRD yang belum terbit; menulis "`TestX` hijau" (seperti contoh) berarti alat ukur tidak ada di kolom `PRD_CONVERSION`. Self-test lalu diulang dari butir 1 tanpa jalan keluar.

### Dampak
Akar lane planning ber-PRD tidak pernah lolos uji akar 9/9, atau lolos karena model mengabaikan satu aturan. Eskalasi `BRIEF → PRD_BRIEF` (chain-rules bagian 3 langkah 4) mewarisi kebingungan yang sama.

### Rencana perbaikan
**Opsi A (disarankan):** alat ukur `PRD_CONVERSION` mengukur permukaan dengan test/diff, sesuai contoh `:96`.
1. `task/SKILL.md:58`, kolom ketiga baris `PRD_CONVERSION` →
   ```
   Test bernama pemikul permukaan itu hijau (mis. `TestCancelPaidOrder`), atau diff berkas permukaannya — sebut permukaannya (endpoint, transisi, atau aturan bernama) di butir SC-nya. Dilarang menyebut `AC-{n}`, `PRD.md`, atau `BRD.md`: keterlacakan SC→AC ditagih kolom `Akar` PRD (predikat G2 `analyst`), bukan di sini.
   ```
2. `task/SKILL.md:65`: hapus kalimat "Kolom alat ukur menyebut brief `READY` karena … (`analyst/references/chain-rules.md` bagian 1.4)."
3. `task-template.md:56` dan `:96` tetap (sudah konsisten dengan opsi A).
4. `chain-rules.md:131` tetap. Perubahan klausa saat eskalasi DIRECT_BRIEF→PRD_CONVERSION menjadi kecil (diff + test → test bernama/diff).

**Opsi B:** pertahankan `AC-{n}` di kolom, lalu tambahkan pengecualian di `task-template.md:56`: "kecuali token `AC-{n}` pada lane `PRD_CONVERSION`". Kelemahannya, nomor AC belum ada saat TASK ditulis, sehingga butir itu tidak bisa diverifikasi siapa pun.

### Test yang ditambahkan / Verifikasi manual
Bila B12 dikerjakan: `validate_doc.py --kind task` atas contoh `task-template.md` bagian 3 → T3a lolos. Manual: jalankan self-test butir 3 atas contoh; lolos tanpa aturan yang dilanggar.

### Selesai bila
Tabel, self-test butir 3, dan contoh terisi menyatakan satu aturan yang sama untuk `PRD_CONVERSION`.

### Risiko & catatan
Keputusan user dibutuhkan (A atau B).

---
## B10 [Sedang] Jalur RCA plan longgar dan tanpa muara eskalasi.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** L5.1 (`_frontmatter()` plan mencari `risk:` di seluruh isi, bukan hanya frontmatter), keputusan user (muara eskalasi) · **Memblokir:** B15 (c)

### Konteks
Jalur `entry_mode: RCA` dipanggil gerbang langsung (tanpa analyst) sesudah `RCA.md` `ROOT_CAUSE_CONFIRMED`. SKILL plan menyatakan `risk` dan `file_scope` REQUIRED, dan Check K/E bergantung pada keduanya. Skrip justru meloloskan jalur itu sebelum menagih apa pun.

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/plan/scripts/check_preconditions.py:653-661`:
```python
        # Jalur RCA dirutekan gerbang langsung, bukan lane planning:
        # ia tidak memikul chain dan tidak diperiksa di sini.
        if self.entry_mode_arg == "RCA" and not chain:
            self.results.append({
                "id": check_id, "name": name, "status": "PASS",
                "summary": f"Jalur {self.entry_mode_arg} dirutekan gerbang; parameter chain tidak berlaku",
                "action": "",
            })
            return
```
`src/plugins/backenddev/skills/plan/SKILL.md:28-29`: "`risk` — enum — `[REQUIRED]`…", "`file_scope` — string — `[REQUIRED]` — … Kosong → skrip prasyarat `FAIL` di check 8, bukan diloloskan dengan catatan."

Muara eskalasi, `src/plugins/backenddev/skills/plan/references/entry-rules.md:64` (1C): "Terapkan 5 pemicu bagian 1A bila perbaikan menuntut DTO, endpoint, atau kolom baru." Sedangkan 1A `:39`: "kembalikan pemicunya ke `backenddev:analyst` sebagai pemicu eskalasi chain nomor 1 — `analyst` menaikkan `chain` ke `PRD_BRIEF`…". TASK `DEFECT_RCA` tidak punya `chain` (`task/SKILL.md:26`), dan analyst tidak ada di jalur RCA (`tech-lead/SKILL.md:109`).

### Reproduksi
```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); bash "$FX" $tmp/r >/dev/null; cd $tmp/r; T=backenddev/docs/2609240900-order-fix
git rm -q $T/brief-01-order-fix.md; sed -i '/^risk:/d' $T/TASK.md
printf -- '---\nstatus: ROOT_CAUSE_CONFIRMED\n---\n\n# RCA\n\n## Arah perbaikan\n\n| Berkas | Aksi |\n|---|---|\n| internal/order/service.go | modify |\n' > $T/RCA.md
git add -A; git commit -qm rca
python3 $P/plan/scripts/check_preconditions.py --taskdir $T --entry-mode RCA; echo "exit=$?"
python3 $P/plan/scripts/check_preconditions.py --taskdir $T --entry-mode LANGSUNG --chain BRIEF --risk MINOR | grep '^\[8\]'
```
Output aktual:
```
PRECONDITION CHECK: plan [PASS] (8/8 passed)
…
[8] Planning Parameters & Entry Mode Alignment : PASS (Jalur RCA dirutekan gerbang; parameter chain tidak berlaku)
exit=0
[8] Planning Parameters & Entry Mode Alignment : FAIL (file_scope kosong pada lane planning (chain BRIEF) — Check E akan berjalan terdegradasi dengan `## Out of Scope` TASK.md sebagai satu-satunya pembanding)
```

### Dampak
- Jalur RCA menulis brief tanpa plafon risk (Check K) dan dengan Check E terdegradasi, persis kondisi yang dicegah keras di lane planning.
- Perbaikan RCA yang ternyata butuh kontrak baru "dieskalasi ke analyst", yang tidak ada di jalur ini dan tidak punya chain untuk dinaikkan. Rantai berhenti tanpa pemilik.

### Rencana perbaikan
1. Skrip (diff diuji di scratch, `b10_plan.diff`):
```diff
--- a/src/plugins/backenddev/skills/plan/scripts/check_preconditions.py
+++ b/src/plugins/backenddev/skills/plan/scripts/check_preconditions.py
@@ -650,12 +650,28 @@
 
         chain = self._effective_chain()
 
-        # Jalur RCA dirutekan gerbang langsung, bukan lane planning:
-        # ia tidak memikul chain dan tidak diperiksa di sini.
+        # Jalur RCA dirutekan gerbang langsung, bukan lane planning: ia tidak
+        # memikul chain, tetapi Check K dan Check E tetap butuh `risk` dan
+        # `file_scope` — keduanya wajib dari slot rute gerbang.
         if self.entry_mode_arg == "RCA" and not chain:
+            risk = self._effective_risk()
+            if risk not in VALID_RISKS:
+                fail(
+                    f"Risk '{risk or '(kosong)'}' tidak sah pada jalur RCA (wajib BREAKING | MAJOR | MINOR)",
+                    "Minta gerbang `backenddev:tech-lead` meneruskan `--risk` dari Keputusan 2, "
+                    "atau pastikan `risk:` TASK.md DEFECT_RCA terisi.",
+                )
+                return
+            if not self.file_scope_arg:
+                fail(
+                    "file_scope kosong pada jalur RCA — Check E akan berjalan terdegradasi",
+                    "Minta gerbang `backenddev:tech-lead` meneruskan slot `File Scope` laporan rutenya "
+                    "sebagai `--file-scope`; `## Arah perbaikan` RCA.md bukan pengganti batas yang diizinkan.",
+                )
+                return
             self.results.append({
                 "id": check_id, "name": name, "status": "PASS",
-                "summary": f"Jalur {self.entry_mode_arg} dirutekan gerbang; parameter chain tidak berlaku",
+                "summary": f"Jalur RCA dirutekan gerbang · risk {risk} · file_scope terisi; parameter chain tidak berlaku",
                 "action": "",
             })
             return
```
2. `entry-rules.md:64` (1C, "Batas kewenangan"), teks pengganti:
   ```
   **Batas kewenangan**: dilarang mengubah `## Rantai kausal` atau menambah root cause di brief. Bila perbaikan menyentuh salah satu dari 5 pemicu bagian 1A (DTO, endpoint, kolom baru, transisi status, permission), BERHENTI dan kembalikan ke `backenddev:tech-lead` — bukan ke `analyst`: taskdir `DEFECT_RCA` tidak memikul `chain` yang dapat dinaikkan. Gerbang memutuskan ulang lane-nya.
   ```
3. `entry-rules.md:29` (1A): "eskalasi ke `system-analysis`" → "kembalikan ke pemanggil menurut jalan keluar di bawah (jalur `RCA`: bagian 1C)" (sekaligus menutup B15 (c)).
4. `plan/SKILL.md` Failure path 1: tambah "jalur `RCA` menyentuh pemicu eskalasi → kembalikan ke `backenddev:tech-lead` (`references/entry-rules.md` 1C)". Fase 2 butir 4: "…terapkan 5 pemicu eskalasi bagian 1A (jalur `RCA`: muara bagian 1C)".
5. `tech-lead/SKILL.md:109` (Keputusan 2 butir 4): tambah "Slot `First Action` juga menyebut `risk` (Keputusan 2) dan `file_scope` (slot `File Scope`) eksplisit; tanpanya `plan` berhenti di check 8." `tech-lead/SKILL.md` Fase 5: tambah penanganan pengirim `plan` jalur RCA yang membawa eskalasi.
6. **Keputusan user** — bentuk re-route: (a) gerbang mengamandemen TASK (`lane: PRD_CONVERSION`, tambah `chain: PRD_BRIEF` + ledger) lalu memanggil analyst re-entry di taskdir yang sama dengan `RCA.md` sebagai `evidence`; atau (b) taskdir baru lane `PLANNING` dengan `finding_source` = `RCA.md`. Opsi (a) menjaga riwayat, tapi menambah satu jenis amandemen gerbang (lihat B15 (e)).

### Test yang ditambahkan / Verifikasi manual
`src/plugins/backenddev/tests/test_b10_plan_rca.py` (scratch: 3/3 lolos dengan patch; 2 gagal di kode `34684ee`, yang ketiga memang PASS di keduanya):
```python
from conftest import TASKDIR, check, git, run_json
PLAN = "plan/scripts/check_preconditions.py"
RCA = "---\nstatus: ROOT_CAUSE_CONFIRMED\n---\n\n# RCA\n\n## Arah perbaikan\n\n| internal/order/service.go | modify |\n"

def _rca(repo, task_risk=True):
    td = repo / TASKDIR
    (td / "brief-01-order-fix.md").unlink(); (td / "RCA.md").write_text(RCA)
    if not task_risk:
        (td / "TASK.md").write_text((td / "TASK.md").read_text().replace("risk: MINOR\n", ""))
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "rca")

def test_rca_tanpa_file_scope_fail(repo):
    _rca(repo)
    r = run_json(PLAN, repo, "--taskdir", TASKDIR, "--entry-mode", "RCA")
    assert "file_scope kosong pada jalur RCA" in check(r, 8)["summary"]

def test_rca_tanpa_risk_fail(repo):
    _rca(repo, task_risk=False)
    r = run_json(PLAN, repo, "--taskdir", TASKDIR, "--entry-mode", "RCA", "--file-scope", "internal/order/")
    assert "Risk '(kosong)'" in check(r, 8)["summary"]

def test_rca_lengkap_pass(repo):
    _rca(repo)
    r = run_json(PLAN, repo, "--taskdir", TASKDIR, "--entry-mode", "RCA", "--file-scope", "internal/order/")
    assert r["status"] == "PASS"
```

### Selesai bila
`--entry-mode RCA` tanpa `--file-scope` atau tanpa risk sah → FAIL check 8; 1A/1C menunjuk satu muara (`tech-lead`) untuk jalur RCA.

### Risiko & catatan
Sebelum L5.1, `_effective_risk()` bisa membaca `risk:` dari badan TASK (bukan frontmatter), sehingga test `tanpa_risk` bisa lolos palsu bila badan memuat teks "risk: …".

---

## B11 [Sedang] Lokasi `spec.json` tidak ditentukan.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 1 jam · **Bergantung pada:** L2.7 (laci `.explore/` di-gitignore) · **Memblokir:** —

### Konteks
`scaffold_brief.py --write-matrix --spec <json>` membutuhkan berkas spec. SKILL tidak menyebut di mana model harus menulisnya, sedangkan commit agregat plan hanya men-stage `brief-*.md`.

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/plan/SKILL.md:55`: "…lalu jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/scaffold_brief.py --taskdir <taskdir> --write-matrix --spec <spec.json> [--risk <risk>]`." (juga `:57` untuk `--append`). `src/plugins/backenddev/skills/plan/scripts/scaffold_brief.py:499` sudah mendukung `` `-` berarti stdin ``, dan `:518` membaca path apa pun tanpa batas lokasi.

### Reproduksi
```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); bash "$FX" $tmp/r >/dev/null; cd $tmp/r; T=backenddev/docs/2609240900-order-fix
git rm -q $T/brief-01-order-fix.md; printf -- '---\nstatus: ROOT_CAUSE_CONFIRMED\n---\n# RCA\n' > $T/RCA.md; git add -A; git commit -qm rca
echo '{"briefs":[{"nn":"01","unit":"order-total-null","title":"Perbaiki NPE total","risk":"MINOR","fulfills":["SC-1"]}]}' > $T/spec.json
python3 $P/plan/scripts/scaffold_brief.py --taskdir $T --write-matrix --spec $T/spec.json | head -1
python3 $P/plan/scripts/scaffold_brief.py --taskdir $T --nn 01 | head -1
git add $T/brief-01-order-total-null.md; git commit -qm "docs(plan): add 1 briefs for order-fix"   # commit agregat: hanya brief
git status --porcelain
python3 $P/architect/scripts/check_preconditions.py --taskdir $T | grep -E '^PRECONDITION|^\[4\]'
mv $T/spec.json $T/.explore/brief-spec.json
python3 $P/architect/scripts/check_preconditions.py --taskdir $T | grep '^\[4\]'
```
Output aktual:
```
BRIEF MATRIX: [PASS] 1 brief teralokasi; plafon risk MINOR
SCAFFOLD: [PASS]
?? backenddev/docs/2609240900-order-fix/.explore/
?? backenddev/docs/2609240900-order-fix/spec.json
PRECONDITION CHECK: architect [FAIL] (5/6 passed)
[4] Git Worktree & Status            : FAIL (Working tree git kotor sebelum rantai orkestrasi dimulai)
[4] Git Worktree & Status            : PASS (Working tree bersih dan siap dieksekusi)
```

### Dampak
Rantai berhenti di architect Fase 0 atas berkas kerja plan sendiri. Model lalu cenderung meng-commit `spec.json` (artefak tanpa pemilik di matriks commit) atau menghapusnya dengan `rm`.

### Rencana perbaikan
1. `plan/SKILL.md:55`, teks pengganti:
   ```
   1. **Kunci Matriks Alokasi Batch**: susun spesifikasi batch — `nn`, `unit`, `title`, `risk`, `covers`, `fulfills`, `consumes`, `produces`, `explore`, serta opsional `commit_type` dan `domain` (B13) tiap brief — dan tulis ke `{taskdir}/.explore/brief-spec.json` lewat tool `Write`. Lalu jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/scaffold_brief.py --taskdir <taskdir> --write-matrix --spec {taskdir}/.explore/brief-spec.json [--risk <risk>]`. Spec di luar laci `.explore/` ditolak skrip: berkas liar di taskdir membuat prasyarat `architect` check 4 FAIL. …(lanjutan kalimat PASS/FAIL tetap)
   ```
   `:57`: `--spec {taskdir}/.explore/brief-spec.json`.
2. `scaffold_brief.py` sesudah `:517`, guard lokasi:
   ```python
   if args.spec != "-":
       spec_path = Path(args.spec)
       spec_path = (spec_path if spec_path.is_absolute() else tool.root / spec_path).resolve()
       if not spec_path.is_relative_to((tool.taskdir / LACI).resolve()):
           print(f"SCAFFOLD: [FAIL] spec wajib di {tool.taskdir / LACI}/ atau stdin (`-`): {args.spec}")
           sys.exit(1)
   ```

### Test yang ditambahkan / Verifikasi manual
pytest (**belum dijalankan**): `--spec {taskdir}/spec.json` → exit 1 dengan pesan "spec wajib di"; `--spec {taskdir}/.explore/brief-spec.json` → PASS; sesudahnya architect check 4 PASS.

### Selesai bila
SKILL menyebut satu lokasi spec, dan skrip menolak lokasi lain.

### Risiko & catatan
`.explore/` di-gitignore (L2.7): spec hilang di clone lain. Itu diterima karena spec hanyalah masukan matriks, dan matriksnya sendiri direkonstruksi L2.7.

---
## B12 [Sedang] Beban context dan self-test manual.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2–3 hari (validator ±1,5 hari, pemangkasan ±1 hari) · **Bergantung pada:** L5.1 (`read_frontmatter`), L5.9 (parser sadar fence/BOM), L5.6 (placeholder tanpa false positive), L6.1, **B9** (aturan butir 3 TASK) · **Memblokir:** —

### Konteks
Semua skill rantai planning berjalan di main loop satu sesi, sehingga SKILL, references, template, dan dispatcher yang dibacanya menumpuk di context yang sama. Self-test TASK (9 butir), BRD (12 butir), dan PRD (13 butir) dikerjakan model lewat Grep satu per satu, padahal brief sudah punya validator (`validate_briefs.py`) dan frontenddev punya `skills/_common/validate_doc.py` untuk FLOW/UI/CONTRACT.

### Lokasi & kode saat ini
Ukuran diukur dengan `wc -c` (skrip `b12_size.sh`). Token ≈ byte/4 (perkiraan kasar). "Muatan main loop" = SKILL.md + references/templates/dispatcher yang diperintahkan SKILL untuk dibaca (ditelusuri lewat mdcp `md_search` pola `references/|templates/|dispatcher/` di tiap SKILL.md).

| Skill | SKILL.md (B) | Muatan main loop (B) | ≈ token | Berkas yang dihitung |
|---|---|---|---|---|
| tech-lead | 27.560 | 74.798 | 18.699 | SKILL, references/decisions, gate-lifecycle, gate-scope, dispatcher/explorer |
| analyst | 24.021 | 47.014 | 11.753 | SKILL, references/chain-rules |
| task | 13.420 | 22.696 | 5.674 | SKILL, templates/task-template |
| business-analysis | 13.365 | 45.841 | 11.460 | SKILL, elicitation-guide, brd-template, dispatcher/explorer, dispatcher/reviewer |
| system-analysis | 17.202 | 69.242 | 17.310 | SKILL, analysis-protocol, prd-template, dispatcher/explorer, dispatcher/reviewer |
| plan | 22.213 | 101.999 | 25.499 | SKILL, entry-rules, slicing-and-scan, review-and-commit, brief-template, dispatcher/explorer, dispatcher/reviewer |
| architect | 24.264 | 44.110 | 11.027 | SKILL, lifecycle-recovery, dispatcher/implementor, dispatcher/reviewer |
| report | 8.526 | 9.909 | 2.477 | SKILL, report-template |
| audit | 12.454 | 23.753 | 5.938 | SKILL, dimensions, issues-template |
| debug | 12.318 | 27.297 | 6.824 | SKILL, rca-template, dispatcher/explorer |
| document-api | 11.038 | 13.720 | 3.430 | SKILL, api-doc-template |
| profile | 16.536 | 56.122 | 14.030 | SKILL, scan-guide, convention-scan, profile-template, stacks/_CONTRACT |

Ditambah satu adapter stack per sesi (dibaca plan, system-analysis, audit, profile, architect): 12.838 (bun) – 19.725 (rust) B. Prompt subagent (context terpisah): `agents/` total 70.847 B (code-explorer 15.883, code-reviewer 15.012, brief-reviewer 14.745, brd-/prd-reviewer masing-masing 9.085, code-implementor 7.037).

Rantai planning satu sesi (tech-lead → analyst → task → business-analysis → system-analysis → plan): **361.590 B ≈ 90 rb token**, +adapter ≈ 374–381 KB (≈ 94–95 rb token). Total markdown backenddev: **718.989 B**.

**Koreksi terhadap ISSUES.md:** angka "±307 KB (±77 rb token)" cocok dengan analyst..plan saja (286.792 B) + adapter go (19.246 B) = 306.038 B. Bila tech-lead ikut dihitung (ia selalu jalan lebih dulu di sesi yang sama), angkanya 361,6 KB tanpa adapter. Angka total ±719 KB benar. BRD juga punya self-test manual (12 butir, `brd-template.md:77-96`), di samping PRD 13 butir (`prd-template.md:123-141`) dan TASK 9 butir (`task-template.md:48-70`).

### Reproduksi
```bash
cd /home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow/src/plugins/backenddev
find . -name '*.md' -print0 | xargs -0 wc -c | tail -1          # 718989 total
bash /tmp/claude-1000/-home-fakhrulnugroho-work-natakode-nataflow-agentic-workflow/d3694b5e-a45f-49bf-8ba3-1a983c306ba0/scratchpad/detail-08b/b12_size.sh
```
Output aktual: tabel di atas.

### Dampak
Sekitar 90 rb token instruksi sebelum satu baris kode repo dibaca. Instruksi awal cenderung terdesak saat context dipadatkan, dan 34 butir self-test manual menghabiskan puluhan panggilan Grep per dokumen tanpa jaminan konsisten antarsesi.

### Rencana perbaikan
**A. `validate_doc.py` untuk TASK/BRD/PRD.**
Letak: `src/plugins/backenddev/skills/_common/validate_doc.py`. Antarmuka:
```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind task|brd|prd --taskdir <taskdir> [--fresh] [--finding-source <path>] [--json]
```
Keluaran berpola sama dengan validator lain; `MANUAL` tidak menggagalkan exit code:
```
DOC VALIDATION: prd [FAIL] (10/11 mekanis lolos) · 2 butir manual
[P1]  Cakupan BR-{n}              : FAIL (BR-3 tidak disebut kolom Dasar mana pun)
[P10b] Kecukupan kontrak          : MANUAL (nilai sendiri — prd-template.md Self-test butir 10b)
```
Pustaka yang dipakai: `read_frontmatter` (L5.1), `sections()`/`outside_fences()` (L5.9), `parse_chain` (L5.4), `RISK_CHAINS`/`CHAIN_TERMINAL_LANES` yang kini ada di skrip analyst/task dipindah ke `_common`.

Pemetaan butir self-test (dikutip dari template) ke check:

TASK — `task/templates/task-template.md:48-70`

| Butir | Kutipan inti | Check | Mekanis? |
|---|---|---|---|
| 1 | "frontmatter memuat `status: ACTIVE`, `lane` … `risk` … `created` berformat `YYYY-MM-DD`. Body memuat tepat satu H1 dan tepat empat heading…" | T1 | ya |
| 2 | "baris `- [ ] **SC-{n}**:` berurut mulai `SC-1` tanpa lompatan dan tanpa nomor ganda, berjumlah 1–7" | T2 | ya |
| 3 | "tiap butir memuat literal `— verifikasi:` … yang menunjuk dokumen hop hilir yang belum terbit (`BRD.md`, `PRD.md`) adalah kegagalan"; finding_source → `> Status: FIXED` | T3a (literal, token terlarang, klausa Status bila `--finding-source`) | sebagian; "cocok lane" = T3b MANUAL |
| 4 | "tiap butir menyebut nama entitas, threshold numerik, atau status spesifik" | T4 | MANUAL (daftar kata sifat hanya WARN) |
| 5 | "`## Description` memuat minimal satu `file:baris`, dan tiap rujukan itu … menunjuk berkas yang benar-benar ada" | T5 (berkas ada dan nomor baris ≤ jumlah baris) | ya |
| 6 | "`## Out of Scope` memuat minimal satu butir berformat `- <yang tidak dikerjakan> — <alasan>`" | T6 | ya |
| 7 | "`Grep` seluruh berkas atas `TBD`, `TODO`, `diisi nanti`, dan sisa penanda template berbentuk `<...>`" | T7 (di luar fence dan inline code, aturan L5.6) | ya |
| 8a | "`chain:` … dan baris `## Chain` memuat **tepat** hop chain itu … `lane` cocok … pasangan `(risk, chain)` sah" | T8a | ya |
| 8b | "Seluruh hop `## Chain` belum tercentang" | T8b (hanya dengan `--fresh`) | ya |
| 9 | "tiap `SC-{n}` menamai permukaan yang disebut `request` atau terbukti di `evidence`" | T9 | MANUAL |

BRD — `business-analysis/templates/brd-template.md:77-96`

| Butir | Kutipan inti | Check | Mekanis? |
|---|---|---|---|
| 1 | "frontmatter memuat `title`, `requester`, dan `status: DRAFT`; sembilan seksi baku…" | B1 | ya |
| 2 | "`- **BR-{n}**:` berurutan … `EC-{n}` … atau tepat satu baris `EC-0` … `BM-LUAR-RANTAI` tidak memperkenalkan nomor baru" | B2 | ya |
| 3 | "tiap kalimat hasil membaca kode berlabel `Observasi kode:` beserta `file:baris`" | B3 (token `path:baris` di `## Current state` wajib satu baris dengan `Observasi kode:`, berkasnya ada) | ya (heuristik) |
| 4 | "`TBD`, `TODO`, dan `diisi nanti`" | B4 | ya |
| 5 | "`## Edge cases`, `## Business metrics`, `## Out of scope`, dan `## Open questions` dilarang kosong" | B5 | ya |
| 6 | "maksimal tiga entri, tiap entri memuat `terdampak:` dan `sementara dipakai:` … menyebut `## Business rules` atau `## Target state` bersifat memblokir" | B6 | ya |
| 7 | "tiap `BR-{n}` terpetakan ke minimal satu `SC-{n}` … Tiap `BM-{n}` … `digerakkan:` … rujukan hantu" | B7a (BM→SC nyata, rujukan hantu) mekanis; B7b (BR→SC, sentuhan Out of Scope) MANUAL | sebagian |
| 8 | "tiap baris `EC-{n}` membawa tepat satu slug kategori dari lima yang sah … `Kategori nihil:`" | B8 | ya |
| 9 | "jenis peran (`primer`/`approver`/`sistem`/`terlarang`) beserta `boleh:` dan `dilarang:` … minimal satu baris berjenis `terlarang` … kata \"user\" berdiri sendiri" | B9 | ya |
| 10 | "`## Problem` memuat ketiga baris `Finansial:`, `Operasional:`, dan `Integritas data:` … ditambah frekuensi" | B10 (baris ada, tidak kosong, token frekuensi ada) | sebagian |
| 11 | "heading `## Success criteria` dan `## Success Criteria`. Satu kecocokan adalah kegagalan" | B11 | ya |
| 12 | "Kecukupan aturan … aturan yang tidak punya akar sama sekali" | B12 | MANUAL |

PRD — `system-analysis/templates/prd-template.md:123-141`

| Butir | Kutipan inti | Check | Mekanis? |
|---|---|---|---|
| 1 | "seluruh `BR-{n}` … sandingkan dengan gabungan seluruh kolom `Dasar` … `BR-DISANGGAH: BR-{n}` … rujukan hantu" | P1 | ya |
| 2 | "seluruh `EC-{n}` … kolom `Dasar` tabel `## Acceptance criteria` … `EC-0` lolos" | P2 | ya |
| 3 | "tiap `SC-{n}` … wajib disebut minimal satu kolom `Akar`" | P3 | ya |
| 4 | "tidak satu pun endpoint … menyentuh butir `## Out of scope` BRD maupun `## Out of Scope` `TASK.md`" | P4 | MANUAL |
| 5 | "kolom \"Cara verifikasi\" bernilai persis `test otomatis`, atau `QA manual:` diikuti langkah konkret" | P5 | ya |
| 6 | "frontmatter memuat `title`, `source_brd`, dan `status: DRAFT`; sembilan seksi baku" | P6 | ya |
| 7 | "tepat 16 baris bernomor 1–16 … `Mendarat di` … lima dimensi rawan bocor (2, 4, 11, 13, 16)" | P7 | ya |
| 8 | "`TBD` dan `TODO`, lalu periksa empat pilar kontrak dari sel tabel kosong" | P8 | ya |
| 9 | "maksimal tiga entri termasuk entri `BR-DISANGGAH:` … `terdampak:` menyebut `## Task breakdown` maupun `## Business rules`" | P9 | ya |
| 9b | "ambil tiap nilai … di `sementara dipakai:` … lalu `Grep` kelimanya di `## API contract`…" | P9b (token ber-backtick di `sementara dipakai:` dicari di lima seksi) | ya (hanya token ber-backtick) |
| 10 | "`Grep` `## Task breakdown` dan `## Acceptance criteria` atas ekstensi berkas sumber stack, separator path, dan pola nama kelas test" | P10 | ya |
| 10b | "Kecukupan kontrak … yang tak berakar pada satu pun adalah kegagalan" | P10b | MANUAL |
| 11 | "Pengecualian: BRD absen … melewati butir 1 dan 2 …" | logika lewati di P1/P2/P4 | ya |

Total: TASK 8 check mekanis (T1, T2, T3a, T5, T6, T7, T8a, T8b) + 3 manual (T3b, T4, T9); BRD 11 check mekanis (B7a dan B10 sebagian) + 2 manual (B7b, B12); PRD 10 check mekanis (+ logika pengecualian butir 11) + 2 manual (P4, P10b).

Teks pengganti di SKILL:
- `task/SKILL.md` Fase 5 butir 3: "**Self-test akar**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind task --taskdir <taskdir> --fresh [--finding-source <finding_source>]`. `FAIL` → perbaiki seluruh pelanggaran satu keluaran, jalankan sekali lagi. Butir bertanda `MANUAL` (3b, 4, 9) dinilai sendiri memakai predikat `templates/task-template.md` bagian 2."
- `business-analysis/SKILL.md:73` (Fase 5 butir 1): sama, dengan `--kind brd`.
- `system-analysis/SKILL.md:82` (Fase 8 butir 1): sama, dengan `--kind prd`.
- `analyst/references/chain-rules.md:131`: "…jalankan ulang `validate_doc.py --kind task` (tanpa `--fresh`)…".
- `tech-lead/SKILL.md:146`: "jalankan ulang `validate_doc.py --kind task`" menggantikan "butir 2–6".
- Ketiga template: butir mekanis diringkas satu baris ("[T2 mekanis] penomoran SC"); butir MANUAL tetap berprosa lengkap.

**B. Pemangkasan muatan (usulan konkret).** Ukuran bagian dihitung proporsional jumlah baris (`md_tree`), jadi hanya perkiraan:

| # | Berkas | Bagian | Perkiraan | Usulan |
|---|---|---|---|---|
| 1 | `plan/references/review-and-commit.md` (23.666 B) | bagian 4 katalog check (baris 5–76 dari 135) | ±12,6 KB | Pindah ke `plan/references/check-catalog.md`; SKILL Fase 4 menyuruh membukanya **hanya** untuk ID check yang FAIL |
| 2 | `system-analysis/dispatcher/explorer.md` (19.688 B) | Profil S (18–110) dan Profil B (112–234) dalam satu berkas | hemat ±8–10 KB per muat | Pecah jadi `explorer-surface.md` dan `explorer-blast.md`; Fase 1 memuat yang pertama, sebelum Fase 4 memuat yang kedua |
| 3 | `task-template.md`, `brd-template.md`, `prd-template.md` | seksi self-test | ±19 KB total → ±6 KB | Butir mekanis diganti validator (A) |
| 4 | `tech-lead/SKILL.md` (27.560 B) | Fase 5 re-entry per pengirim (baris 137–155) | ±2,6 KB (proporsional; paragrafnya panjang, jadi nyatanya lebih besar) | Pindah ke `tech-lead/references/gate-lifecycle.md` bagian baru "Re-entry per pengirim"; hanya dibaca saat re-entry |
| 5 | 4 SKILL (plan ×3, architect ×2, task ×1, analyst ×1) | 7 blok "`> Mengapa:`" | ±3 KB | Pindah ke `references/rationale.md` per skill, dibaca bila ada sengketa |
| 6 | `plan/templates/brief-template.md` bagian 2 (baris 104–197) | aturan yang sudah ditagih `validate_briefs.py` | ±9 KB | Ringkas butir yang sudah ber-check ID menjadi satu baris + ID check |

Perkiraan total pemangkasan muatan rantai planning: ±40–50 KB (≈ 10–12 rb token), atau ±12–14 %.

### Test yang ditambahkan / Verifikasi manual
- `src/plugins/backenddev/tests/test_validate_doc.py` (**belum dijalankan**, belum ditulis): contoh terisi di ketiga template (`task-template.md` bagian 3, `brd-template.md:98-147`, `prd-template.md:143-223`) harus lolos semua check mekanis; satu fixture rusak per check (SC-2 hilang, BR tak ber-Dasar, Impact map 15 baris, EC tanpa slug, dst.) harus FAIL tepat di check-nya; fixture CRLF/BOM/code fence (L5.9).
- Ukuran: lint L6.3 mencetak tabel muatan per skill (reuse `b12_size.sh`) dan gagal bila rantai planning melewati ambang yang disepakati.

### Selesai bila
`validate_doc.py` menagih seluruh butir mekanis di tabel; ketiga SKILL memanggilnya; contoh terisi template lolos; muatan rantai planning turun sesuai tabel B (diukur ulang dengan `wc -c`).

### Risiko & catatan
- Validator hanya aman di atas parser frontmatter/heading yang benar (L5.1/L5.9). Bila dikerjakan lebih dulu, bug substring L5.1 ikut tersalin.
- Heuristik "user berdiri sendiri" (B9) dan "Observasi kode" (B3) rawan false positive. Mulai sebagai WARN, naikkan ke FAIL setelah contoh nyata lolos.

---
## B13 [Rendah] `commit_message` dipaksa `feat(...)`.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 3–4 jam · **Bergantung pada:** L3.6 (konvensi commit reviewer), keputusan user (`commit_template`) · **Memblokir:** —

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/plan/scripts/scaffold_brief.py:441-450`:
```python
        commit_type = row.get("commit_type") or "feat"
        domain = row.get("domain") or unit.split("-")[0]
        ...
            f'commit_message: "{commit_type}({domain}): implement {unit}"',
```
`src/plugins/backenddev/skills/plan/scripts/validate_briefs.py:773-778`:
```python
            commit = fm.get("commit_message") or ""
            if commit and not re.match(r"^[a-z]+\([a-z0-9_.-]+\):\s*implement\s+\S", commit):
```
`src/plugins/backenddev/skills/plan/templates/brief-template.md:106`: "Ditulis `backenddev:plan` dari `commit_convention` profil, berbentuk `<type>(<domain>): implement <unit>`." `plan/SKILL.md:55` tidak menyebut `commit_type`/`domain` di daftar field spec. `commit_convention` di profil berupa prosa bebas satu baris (`profile/references/scan-guide.md` bagian 10; contoh `profile-template.md:167` "conventional: <type>(<scope>): <subject> — subject bahasa Inggris huruf kecil"; prefix tiket `OMS-123: ...` juga sah).

### Masalah
Tipe default selalu `feat` (brief RCA/perbaikan temuan pun `feat`), dan konvensi profil tidak pernah dibaca skrip. Validator juga menolak pesan yang mengikuti konvensi tiket. Reproduksi (scratch, TASK `lane: DEFECT_RCA`, profil `commit_convention: "ticket: OMS-<n>: <subject> (tanpa type)"`):
```
BRIEF MATRIX: [PASS] 1 brief teralokasi; plafon risk MINOR
SCAFFOLD: [PASS]
6:commit_message: "feat(order): implement order-total-null"
    - brief-01-order-total-null.md: `commit_message` "OMS-412: fix null total in order" tidak berbentuk `<type>(<domain>): implement <unit>`
```

### Perbaikan
1. Profil: tambah field terstruktur `commit_template` di `index.json` (placeholder `{type}`, `{scope}`, `{subject}`, `{ticket}`), ditulis `backenddev:profile` dari pemindaian `scan-guide.md` bagian 10. Contoh: `"{type}({scope}): {subject}"` atau `"{ticket}: {subject}"`. Field prosa `commit_convention` tetap ada sebagai acuan manusia. Bila `commit_template` absen, fallback Conventional Commits.
2. Satu modul `src/plugins/backenddev/skills/_common/commit_lib.py`, dipakai scaffold **dan** validator (dan kelak reviewer/report, L3.6). Prototipe diuji di scratch:
   ```python
   COMMIT_TYPES = ("feat", "fix", "refactor", "perf", "test", "chore", "docs")
   DEFAULT_TEMPLATE = "{type}({scope}): {subject}"
   _SLOT = re.compile(r"\{(type|scope|subject|ticket)\}")

   def commit_template(index):
       tpl = (index.get("commit_template") or "").strip()
       if tpl and "{subject}" in tpl and not re.search(r"\{(?!type\}|scope\}|subject\}|ticket\})[^}]*\}", tpl):
           return tpl
       return DEFAULT_TEMPLATE

   def default_commit_type(lane, finding_source):
       return "fix" if (lane or "").upper() == "DEFECT_RCA" or finding_source else "feat"

   def render(tpl, *, ctype, scope, unit, ticket=None):
       if ctype not in COMMIT_TYPES:
           raise ValueError(f"commit_type '{ctype}' di luar {COMMIT_TYPES}")
       if "{ticket}" in tpl and not ticket:
           raise ValueError("commit_template memuat {ticket} tetapi spec tidak memberi `ticket`")
       return tpl.format(type=ctype, scope=scope, subject=f"implement {unit}", ticket=ticket or "")

   def pattern(tpl):   # regex Check S diturunkan dari template yang sama
       parts, pos = [], 0
       for m in _SLOT.finditer(tpl):
           parts.append(re.escape(tpl[pos:m.start()]))
           parts.append({"type": "(?:" + "|".join(COMMIT_TYPES) + ")", "scope": r"[a-z0-9_.-]+",
                         "subject": r"implement\s+\S.*", "ticket": r"[A-Z][A-Z0-9]+-\d+"}[m.group(1)])
           pos = m.end()
       parts.append(re.escape(tpl[pos:]))
       return re.compile("^" + "".join(parts) + "$")
   ```
   Hasil uji prototipe:
   ```
   fix(order): implement order-total-null True
   OMS-412: implement order-total-null True
   True False      # pattern conventional: menerima feat(order)…, menolak "OMS-412: fix x"
   ```
3. `scaffold_brief.py:441-450` → `ctype = row.get("commit_type") or default_commit_type(lane_TASK, finding_source_TASK)` (lane dibaca dari frontmatter TASK via L5.1; `finding_source` diteruskan plan sebagai `--finding-source`), `scope = row.get("domain") or unit.split("-")[0]`, `commit_message = render(commit_template(index), …)`. Nilai `commit_type` di luar enum → FAIL `validate_spec`.
4. `validate_briefs.py:774` → `pattern(commit_template(index)).match(commit)`.
5. Dokumentasi: `plan/SKILL.md:55` daftar field spec + "`commit_type` (opsional; default `fix` pada lane `DEFECT_RCA` atau akar ber-`finding_source`, selain itu `feat`), `domain` (opsional; default segmen pertama `unit`), `ticket` (wajib bila `commit_template` memuat `{ticket}`)". `brief-template.md:106` → "diturunkan dari `commit_template` profil lewat `scripts/scaffold_brief.py`".

### Test
pytest (**belum dijalankan**): TASK `DEFECT_RCA` tanpa `commit_type` → brief `fix(order): implement …`; profil `commit_template: "{ticket}: {subject}"` + spec `ticket: OMS-412` → `OMS-412: implement …` lolos Check S; `commit_type: "wip"` → FAIL matriks.

### Selesai bila
Tidak ada lagi literal `"feat"` default di scaffold, dan scaffold serta validator memakai satu fungsi yang membaca profil.

**Catatan:** penanda BLOCKED implementor `wip(<domain>): …` (`agents/code-implementor.md:25`) mengambil domain "dari kurung `commit_message`". Pada template tanpa `{scope}` kurungnya tidak ada. Usulan: frontmatter brief tambah `commit_scope:` (ditulis scaffold) sebagai sumber `<domain>`.

---

## B14 [Rendah] Cek tech-lead lemah.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** L5.5 (path `.gemini`), L6.3 (integritas berkas plugin) · **Memblokir:** —

### Konteks
Check 5 menilai `commands.md` dengan substring pada seluruh isi. Check 6 menilai keberadaan berkas plugin sendiri, yang selalu ada selama plugin terpasang.

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/tech-lead/scripts/check_preconditions.py:343-348`:
```python
        try:
            content = commands_file.read_text(encoding="utf-8").lower()
            has_build = "build" in content or "compile" in content
            has_test = "test" in content
            if not (has_build and has_test):
```
`:374-420` check 6 memeriksa `skills/tech-lead/dispatcher/explorer.md` dan kandidat `agents/code-explorer.md`, termasuk `Path.home() / ".gemini" / …` (`:390`).

Format `commands.md` yang sebenarnya (`profile/templates/profile-template.md:142-155`): baris `kunci: nilai [status]` dipisah ` · `, misal `build: <command> [OK|FAIL|tidak berlaku] · typecheck: …`.

**Koreksi terhadap ISSUES.md:** `commands.md` **bukan tabel**. Perbaikannya mem-parse segmen `kunci: nilai` per baris, bukan "parse tabel".

### Reproduksi
```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow; P=$REPO/src/plugins/backenddev/skills
tmp=$(mktemp -d); bash "$FX" $tmp/r >/dev/null; cd $tmp/r
printf '# Commands\n\nTidak ada perintah yang bisa dijalankan; build belum disiapkan. Protest dari tim ops.\n' > .claude/profile/commands.md; git add -A; git commit -qm c
python3 $P/tech-lead/scripts/check_preconditions.py | sed -n '1p;6,7p'
printf '# Commands\n\nbuild: tidak berlaku · typecheck: tidak berlaku\ntest: tidak berlaku · test-single: tidak berlaku\n' > .claude/profile/commands.md; git add -A; git commit -qm c2
python3 $P/tech-lead/scripts/check_preconditions.py | grep '^\[5\]'
```
Output aktual:
```
PRECONDITION CHECK: tech-lead [PASS] (6/6 passed)
[5] Profile Commands             : PASS (Perintah build dan test terdefinisi di commands.md)
[6] Explorer Dispatcher & Agent  : PASS (Template dispatcher/explorer.md dan agent code-explorer.md terverifikasi)
[5] Profile Commands             : PASS (Perintah build dan test terdefinisi di commands.md)
```

### Perbaikan
1. `parse_commands()` per segmen `kunci: nilai`, sadar fence/BOM. FAIL bila `build:` tidak ada, `test:` tidak ada, atau `test: tidak berlaku` (architect Fase 4 butir 1 menjalankan "kompilasi lalu test penuh"; tanpa test, gerbang penutup tidak punya alat ukur). `build: tidak berlaku` tetap sah (adapter bun: "tidak berlaku bila repo dijalankan langsung dari sumber").
2. Check 6 diganti dengan bahan yang benar-benar dipakai Fase 3: `base_branch` resolve ke commit dan `branch_convention` memuat `<slug>` (`profile/templates/profile-template.md:42` "pola nama branch memuat placeholder <slug>"). Integritas berkas plugin pindah ke lint L6.3. Path `.gemini` ikut hilang.

Diff (diuji di scratch, `b14_techlead.diff`):
```diff
--- a/src/plugins/backenddev/skills/tech-lead/scripts/check_preconditions.py
+++ b/src/plugins/backenddev/skills/tech-lead/scripts/check_preconditions.py
@@ -12,6 +12,7 @@
 import json
 import os
 from pathlib import Path
+import re
 import subprocess
 import sys
 from typing import Any, Dict, List, Optional
@@ -39,6 +40,29 @@
 )
 
 
+# commands.md ditulis `backenddev:profile` sebagai baris `kunci: nilai [status]`
+# yang dipisah ` · ` (profile/templates/profile-template.md bagian 9), bukan tabel.
+_CMD_SEGMENT = re.compile(r"^\s*([a-z][a-z-]*)\s*:\s*(.*?)\s*$")
+_NOT_APPLICABLE = re.compile(r"^tidak berlaku\b", re.IGNORECASE)
+
+
+def parse_commands(text: str) -> Dict[str, str]:
+    """Peta `kunci -> nilai` dari commands.md; kunci pertama yang muncul menang."""
+    cmds: Dict[str, str] = {}
+    in_fence = False
+    for line in text.lstrip("\ufeff").splitlines():
+        if line.strip().startswith("```"):
+            in_fence = not in_fence
+            continue
+        if in_fence or line.lstrip().startswith("#"):
+            continue
+        for seg in line.split("·"):
+            m = _CMD_SEGMENT.match(seg)
+            if m and m.group(2):
+                cmds.setdefault(m.group(1), m.group(2))
+    return cmds
+
+
 class PreconditionChecker:
     def __init__(self, target_root: Optional[Path] = None, re_entry: bool = False):
         self.root = (target_root or self._find_repo_root()).resolve()
@@ -66,7 +90,7 @@
         self._check_3_git_status()
         self._check_4_write_access()
         self._check_5_commands()
-        self._check_6_explorer_dispatcher()
+        self._check_6_branch_resolution()
         return all(r["status"] == "PASS" for r in self.results)
 
     def _check_1_profile(self):
@@ -341,27 +365,7 @@
             return
 
         try:
-            content = commands_file.read_text(encoding="utf-8").lower()
-            has_build = "build" in content or "compile" in content
-            has_test = "test" in content
-
-            if not (has_build and has_test):
-                self.results.append({
-                    "id": check_id,
-                    "name": name,
-                    "status": "FAIL",
-                    "summary": "Perintah build atau test belum didefinisikan di commands.md",
-                    "action": "Lengkapi seksi ## Commands dengan instruksi build dan test yang sah."
-                })
-                return
-
-            self.results.append({
-                "id": check_id,
-                "name": name,
-                "status": "PASS",
-                "summary": "Perintah build dan test terdefinisi di commands.md",
-                "action": ""
-            })
+            cmds = parse_commands(commands_file.read_text(encoding="utf-8"))
         except Exception as e:
             self.results.append({
                 "id": check_id,
@@ -370,44 +374,24 @@
                 "summary": f"Gagal membaca commands.md: {e}",
                 "action": "Periksa permissions berkas .claude/profile/commands.md."
             })
-
-    def _check_6_explorer_dispatcher(self):
-        """Template dispatch code-explorer milik gerbang beserta definisi agentnya.
-
-        Gerbang mendispatch `code-explorer` langsung lewat `dispatcher/explorer.md`,
-        tanpa skill pembungkus. Template itu satu-satunya prompt dispatch yang sah di
-        Fase 1 butir 2; tanpanya pemicu dispatch wajib bagian 4E tidak punya jalur
-        berangkat dan gerbang diam-diam jatuh ke sapuan manual berkuota.
-        """
-        check_id = 6
-        name = "Explorer Dispatcher & Agent"
-        skill_dir = Path(__file__).resolve().parent.parent
-        dispatcher_file = skill_dir / "dispatcher" / "explorer.md"
-
-        candidate_agents = [
-            skill_dir.parent.parent / "agents" / "code-explorer.md",
-            self.root / "src" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
-            Path.home() / ".gemini" / "config" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
-            Path.home() / ".claude" / "plugins" / "backenddev" / "agents" / "code-explorer.md",
-        ]
-
-        if not dispatcher_file.exists():
-            self.results.append({
-                "id": check_id,
-                "name": name,
-                "status": "FAIL",
-                "summary": "Berkas dispatcher/explorer.md tidak ditemukan di skill tech-lead",
-                "action": "Pastikan template dispatcher/explorer.md tersedia untuk dispatch langsung code-explorer."
-            })
             return
 
-        if not any(p.exists() for p in candidate_agents):
+        problems = []
+        if "build" not in cmds:
+            problems.append("baris `build:` tidak ada")
+        test = cmds.get("test")
+        if test is None:
+            problems.append("baris `test:` tidak ada")
+        elif _NOT_APPLICABLE.match(test):
+            problems.append("`test: tidak berlaku` — verifikasi penutup architect tidak punya alat ukur")
+
+        if problems:
             self.results.append({
                 "id": check_id,
                 "name": name,
                 "status": "FAIL",
-                "summary": "Definisi subagent agents/code-explorer.md tidak ditemukan",
-                "action": "Pastikan berkas agents/code-explorer.md tersedia di plugin backenddev."
+                "summary": f"commands.md tidak memenuhi kontrak: {'; '.join(problems)}",
+                "action": "Jalankan `backenddev:profile` (mode refresh) agar baris `build:`/`test:` tertulis dari eksekusi nyata."
             })
             return
 
@@ -415,10 +399,44 @@
             "id": check_id,
             "name": name,
             "status": "PASS",
-            "summary": "Template dispatcher/explorer.md dan agent code-explorer.md terverifikasi",
+            "summary": f"build: {cmds['build']} · test: {test}",
             "action": ""
         })
 
+    def _check_6_branch_resolution(self):
+        """Bahan Fase 3 (isolasi branch): base_branch resolve dan branch_convention berslot <slug>.
+
+        Integritas berkas plugin (dispatcher/agent) bukan keadaan repo user dan
+        dipindah ke lint plugin (ISSUES L6.3).
+        """
+        check_id = 6
+        name = "Base Branch & Branch Convention"
+        try:
+            data = json.loads((self.root / ".claude" / "profile" / "index.json").read_text(encoding="utf-8"))
+        except Exception:
+            data = {}
+        base = (data.get("base_branch") or "").strip()
+        conv = (data.get("branch_convention") or "").strip()
+        problems = []
+        if base in ("", "tidak terdeteksi"):
+            problems.append("base_branch kosong/tidak terdeteksi")
+        elif subprocess.run(["git", "-C", str(self.root), "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
+                            capture_output=True).returncode != 0:
+            problems.append(f"base_branch '{base}' tidak resolve ke commit")
+        if "<slug>" not in conv:
+            problems.append(f"branch_convention '{conv or '(kosong)'}' tanpa placeholder <slug>")
+        if problems:
+            self.results.append({
+                "id": check_id, "name": name, "status": "FAIL",
+                "summary": "; ".join(problems),
+                "action": "Perbaiki index.json lewat `backenddev:profile`; gerbang tidak menebak branch acuan (Failure path butir 1)."
+            })
+            return
+        self.results.append({
+            "id": check_id, "name": name, "status": "PASS",
+            "summary": f"base '{base}' resolve · pola branch '{conv}'", "action": ""
+        })
+
     def format_text(self) -> str:
         all_passed = all(r["status"] == "PASS" for r in self.results)
         passed_count = sum(1 for r in self.results if r["status"] == "PASS")
```
Output sesudah patch (scratch, `commands.md` prosa):
```
[5] Profile Commands             : FAIL (commands.md tidak memenuhi kontrak: baris `build:` tidak ada; baris `test:` tidak ada)
[6] Base Branch & Branch Convention : PASS (base 'main' resolve · pola branch 'feat/<slug>')
```

### Test
`src/plugins/backenddev/tests/test_b14_techlead.py` (scratch: 7/7 lolos dengan patch; gagal impor di kode `34684ee`):
```python
import json, sys
import pytest
from conftest import SKILLS, check, git, run_json
TL = "tech-lead/scripts/check_preconditions.py"
sys.path.insert(0, str(SKILLS / "tech-lead" / "scripts"))
from check_preconditions import parse_commands

TEMPLATE_EXAMPLE = ("# Commands\n\n"
    "build: go build ./... [OK] · typecheck: go vet ./... [OK] · lint: golangci-lint run [FAIL]\n"
    "typecheck-scoped: go build ./<paket>/... [OK] · typecheck-per-brief: ya — inkremental\n"
    "test: go test ./... [OK] · test-single: go test ./internal/order -run <TestName> [OK]\n"
    "migration: migrate -path db/migrations -database $DATABASE_URL up · folder db/migrations\n")

def test_parse_contoh_template():
    c = parse_commands(TEMPLATE_EXAMPLE)
    assert c["build"] == "go build ./... [OK]" and c["test"] == "go test ./... [OK]" and "folder" not in c

def _commands(repo, text):
    (repo / ".claude" / "profile" / "commands.md").write_text(text); git(repo, "add", "-A"); git(repo, "commit", "-qm", "cmd")

@pytest.mark.parametrize("text", [
    "# Commands\n\nTidak ada perintah yang bisa dijalankan; build belum disiapkan. Protest dari tim ops.\n",
    "# Commands\n\nbuild: go build ./... [OK]\n",
    "# Commands\n\nbuild: tidak berlaku · test: tidak berlaku\n"])
def test_commands_tanpa_build_test_sah_fail(repo, text):
    _commands(repo, text)
    assert check(run_json(TL, repo), 5)["status"] == "FAIL"

def test_contoh_template_pass(repo):
    _commands(repo, TEMPLATE_EXAMPLE)
    assert check(run_json(TL, repo), 5)["status"] == "PASS"

def _index(repo, **kv):
    p = repo / ".claude" / "profile" / "index.json"; d = json.loads(p.read_text()); d.update(kv)
    p.write_text(json.dumps(d)); git(repo, "add", "-A"); git(repo, "commit", "-qm", "idx")

def test_branch_convention_tanpa_slug_fail(repo):
    _index(repo, branch_convention="feature-branch")
    assert check(run_json(TL, repo), 6)["status"] == "FAIL"

def test_base_branch_tidak_resolve_fail(repo):
    _index(repo, base_branch="develop")
    assert "tidak resolve" in check(run_json(TL, repo), 6)["summary"]
```

### Selesai bila
Kedua contoh reproduksi → check 5 FAIL; contoh `commands.md` di template → PASS; check 6 tidak lagi memeriksa berkas plugin.

**Catatan:** `test: tidak berlaku` → FAIL adalah keputusan (butir 8 "Keputusan yang dibutuhkan"). Alternatifnya PASS bertanda `TERDEGRADASI` seperti banner Check E plan.

---
## B15 [Rendah] Rujukan mati dan kontradiksi kecil.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** B10 (muara eskalasi RCA untuk poin b/c), keputusan user (poin e) · **Memblokir:** —

### Lokasi & kode saat ini
| # | Lokasi | Kutipan | Bertentangan dengan |
|---|---|---|---|
| a | `src/plugins/backenddev/skills/business-analysis/SKILL.md:115` | "…catat kendalanya pada slot `Explorasi` laporan penutup." | Blok `## Output` (`:90-104`) tidak punya slot `Explorasi` |
| a | `src/plugins/backenddev/skills/system-analysis/SKILL.md:125` | "…laporkan penyimpangannya pada baris `Explorasi` `## Output`." | Blok `## Output` (`:99-113`) tidak punya baris itu |
| b | `src/plugins/backenddev/skills/plan/templates/brief-template.md:189` | "…hentikan penulisan batch dan kembalikan klasifikasinya ke gerbang…" | `plan/SKILL.md` Failure path 6: "kembalikan ke `backenddev:analyst` menyebut pemicu eskalasi chain nomor 2" |
| c | `src/plugins/backenddev/skills/plan/references/entry-rules.md:29` | "…eskalasi ke `system-analysis`:" | `entry-rules.md:39` "Dilarang memanggil `system-analysis` sendiri" |
| d | `src/plugins/backenddev/skills/tech-lead/references/decisions.md:139` | "…dilarang menjalankan `git push`, … atau checkout ke branch lain di luar persetujuan eksplisit user." | Tabel di berkas yang sama `:134-136` (`git checkout -b`, `git checkout <branch_name>`, `git checkout <base_branch>`) dan `tech-lead/SKILL.md:124` (isolasi branch Fase 3) |
| e | `src/plugins/backenddev/skills/tech-lead/references/gate-lifecycle.md:32` | "\| User menyisipkan permintaan susulan yang masih di dalam batas \| Satu butir `## Success Criteria` baru \|" (pemicu amandemen kedua) | `tech-lead/SKILL.md:146` "Ini satu-satunya titik gerbang menulis `TASK.md`" (hanya amandemen dari `analyst`); matriks commit `gate-scope.md:47-61` tidak memuat commit `docs(<slug>): amandemen akar TASK` |

**Temuan tambahan pada (e):** `gate-lifecycle.md:31` menyuruh butir gugur "dicoret `~~...~~`, bukan dihapus", sedangkan `SKILL.md:146` menyuruh "tulis ulang butir … lalu jalankan ulang butir 2–6 Self-test Akar". Butir 2 menuntut penomoran `SC-{n}` tanpa lompatan, sehingga baris yang dicoret bisa terbaca sebagai lompatan.

### Masalah
Model diarahkan ke slot yang tidak ada, ke pemilik eskalasi yang salah, atau dilarang melakukan langkah yang diwajibkan fase lain.

### Perbaikan (teks pengganti)
- **a.** Tambahkan baris ke blok TERTAHAN `business-analysis/SKILL.md` Output: `- **Explorasi**: <n> dispatch · <kendala dispatch/confidence low> | —`. Untuk bentuk satu baris, tambahkan kalimat "Ada kendala eksplorasi → tambahkan ` · Explorasi: <kendala>` di ujung baris." Terapkan juga di `system-analysis/SKILL.md` Output (`- **Explorasi**: Profil S <n> · Profil B <n> · <permukaan tak tertutup> | —`).
- **b.** `brief-template.md:189` → "…hentikan penulisan batch dan kembalikan ke pemanggil — `backenddev:analyst` sebagai pemicu eskalasi chain nomor 2 pada lane planning; `backenddev:tech-lead` pada jalur `RCA` (`../references/entry-rules.md` 1C). Dilarang melunakkan predikat…"
- **c.** `entry-rules.md:29` → "Kena salah satu → BERHENTI SEGERA, batalkan rute MINOR beserta penulisan brief, dan kembalikan ke pemanggil menurut **Jalan keluar eskalasi** di bawah (jalur `RCA`: bagian 1C):"
- **d.** `decisions.md:139` → "**Larangan Operasi Remote/Destruktif**: Plugin dilarang menjalankan `git push`, `git merge`, `git rebase`, `gh pr create`, `git branch -d`, atau checkout ke branch **di luar tabel resolusi branch di atas** tanpa persetujuan eksplisit user."
- **e. Keputusan user** — pilih satu:
  - (disarankan) Pertahankan dua pemicu. `tech-lead/SKILL.md:146` → "Ini satu dari dua titik gerbang menulis `TASK.md` (pemicu kedua: susulan user di dalam batas, `references/gate-lifecycle.md` bagian 1a)". Tambah baris matriks `gate-scope.md` bagian 3: `| backenddev/docs/<taskdir>/TASK.md saat amandemen gerbang | Amandemen akar disetujui user | tech-lead | docs(<slug>): amandemen akar TASK |`. Seragamkan cara menulis butir gugur: coret `~~…~~` **dengan ID tetap** (`- [ ] ~~**SC-2**: …~~`), dan tulis "butir tercoret dihitung dalam penomoran" di self-test butir 2.
  - Atau hapus pemicu kedua dari `gate-lifecycle.md:32`, sehingga susulan user selalu lewat kanal analyst Fase 4a atau taskdir baru.

### Test
Manual: mdcp `md_search "Explorasi"` menemukan slot di kedua blok Output; `md_search "eskalasi ke \`system-analysis\`"` kosong; lint L6.3 (rujukan slot) opsional.

### Selesai bila
Kelima kontradiksi hilang, dan matriks commit memuat setiap commit yang ditulis gerbang.

---

## B16 [Rendah] Parsing argumen.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** L5.4 (parser chain bersama) · **Memblokir:** —

### Lokasi & kode saat ini
- `src/plugins/backenddev/skills/plan/scripts/validate_briefs.py:219`, `:429-433`:
  ```python
          self.brief_filter = (brief or "").strip().lstrip("#") or None
          ...
          if self.brief_filter:
              paths = [p for p in paths if p.name.startswith(f"brief-{self.brief_filter}")]
  ```
- `src/plugins/backenddev/skills/plan/scripts/scaffold_brief.py:518-528` (`spec.get("briefs")` tanpa cek tipe) dan `:245-247` (`b.get(field)`).
- `src/plugins/backenddev/skills/task/scripts/check_preconditions.py:452` `--chain` wajib bernilai. `task/SKILL.md:19` mencetak `--chain <chain>` tanpa kurung opsional, padahal `chain` kosong di lane non-planning (`task/SKILL.md:26`).

### Masalah
Reproduksi (scratch, taskdir berisi brief-01/02/03):
```
== validate_briefs --brief 1
BRIEF VALIDATION: [FAIL] Brief dengan nomor '1' tidak ditemukan di …/backenddev/docs/2609240900-order-fix
== validate_briefs --brief 0
mode: single | brief dinilai: ['brief-01-order-fix.md', 'brief-02-order-fix.md', 'brief-03-order-fix.md']
== scaffold --write-matrix, spec berupa list        (exit=1, stdout 0 B)
AttributeError: 'list' object has no attribute 'get'        ← scaffold_brief.py line 528, in main
== scaffold --write-matrix, entri briefs bukan dict (exit=1)
AttributeError: 'str' object has no attribute 'get'         ← line 548 → validate_spec line 245
== task --chain tanpa nilai                          (exit=2)
check_preconditions.py: error: argument --chain: expected one argument
```
**Temuan tambahan (lebih berat dari ISSUES.md):** bila taskdir punya `brief-10-…`, `--brief 1` **memvalidasi brief-10**, bukan gagal:
```
mode: single | brief: ['brief-10-order-fix.md']
```
Gerbang per-brief Fase 3 butir 4 bisa meloloskan brief-01 yang cacat karena yang dinilai brief lain.

### Perbaikan
Diff (diuji di scratch, `b16.diff`):
```diff
--- a/src/plugins/backenddev/skills/plan/scripts/validate_briefs.py
+++ b/src/plugins/backenddev/skills/plan/scripts/validate_briefs.py
@@ -216,7 +216,7 @@
-        self.brief_filter = (brief or "").strip().lstrip("#") or None
+        self.brief_filter = self._normalize_nn(brief)
@@ -416,6 +416,18 @@
+    @staticmethod
+    def _normalize_nn(raw: Optional[str]) -> Optional[str]:
+        """`--brief` → `NN` dua digit; `None` = seluruh batch; `"INVALID"` = tolak."""
+        val = (raw or "").strip().lstrip("#")
+        if val.lower().startswith("brief-"):
+            val = val[6:].split("-", 1)[0]
+        if not val:
+            return None
+        if not val.isdigit() or not 1 <= int(val) <= 99:
+            return "INVALID"
+        return f"{int(val):02d}"
+
@@ -426,9 +438,11 @@
+        if self.brief_filter == "INVALID":
+            return "Nomor brief wajib 1..99 (mis. `3` atau `03`); `0`, `00`, dan nilai non-angka ditolak"
         paths = sorted(self.taskdir.glob("brief-*.md"))
         if self.brief_filter:
-            paths = [p for p in paths if p.name.startswith(f"brief-{self.brief_filter}")]
+            paths = [p for p in paths if p.name.startswith(f"brief-{self.brief_filter}-")]
--- a/src/plugins/backenddev/skills/plan/scripts/scaffold_brief.py
+++ b/src/plugins/backenddev/skills/plan/scripts/scaffold_brief.py
@@ -489,6 +489,32 @@
+SPEC_LIST_FIELDS = ("covers", "fulfills", "consumes", "produces")
+SPEC_STR_FIELDS = ("nn", "unit", "title", "risk", "explore", "commit_type", "domain", "source",
+                   "covers_note", "fulfills_note")
+
+
+def spec_shape_problems(spec: Any) -> List[str]:
+    """Tolak bentuk spec yang akan membuat skrip crash, sebelum validasi isi."""
+    if not isinstance(spec, dict):
+        return [f"akar spec wajib objek JSON `{{\"briefs\": [...]}}`, bukan {type(spec).__name__}"]
+    briefs = spec.get("briefs")
+    if not isinstance(briefs, list):
+        return ["`briefs` wajib berupa list objek"]
+    problems: List[str] = []
+    for i, b in enumerate(briefs, start=1):
+        if not isinstance(b, dict):
+            problems.append(f"entri ke-{i} wajib objek, bukan {type(b).__name__}")
+            continue
+        for f in SPEC_LIST_FIELDS:
+            if f in b and not (isinstance(b[f], list) and all(isinstance(x, str) for x in b[f])):
+                problems.append(f"entri ke-{i}: `{f}` wajib list string")
+        for f in SPEC_STR_FIELDS:
+            if f in b and not isinstance(b[f], (str, int)):
+                problems.append(f"entri ke-{i}: `{f}` wajib string")
+    return problems
+
@@ -521,6 +547,12 @@
             print(f"SCAFFOLD: [FAIL] spec bukan JSON sah: {exc}")
             sys.exit(1)
+        shape = spec_shape_problems(spec)
+        if shape:
+            print(f"SCAFFOLD: [FAIL] bentuk spec tidak sah ({len(shape)} pelanggaran)")
+            for p in shape:
+                print(f"    - {p}")
+            sys.exit(1)
--- a/src/plugins/backenddev/skills/task/scripts/check_preconditions.py
+++ b/src/plugins/backenddev/skills/task/scripts/check_preconditions.py
@@ -449,7 +449,8 @@
-    parser.add_argument("--chain", type=str, required=False, help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF)")
+    parser.add_argument("--chain", type=str, nargs="?", const="", default=None,
+                        help="Chain enum (BRD_PRD_BRIEF | PRD_BRIEF | BRIEF); kosong/tanpa nilai pada lane non-planning")
```
Teks: `task/SKILL.md:19` → `--taskdir <taskdir> --lane <lane> [--chain <chain>]` ("hilangkan `--chain` pada lane `DEFECT_RCA`/`EXEC_BRIEF`"). Nilai `--chain` asing tetap FAIL di check 6; normalisasi huruf besar-kecil ikut L5.4.

### Test
`src/plugins/backenddev/tests/test_b16_args.py` (scratch: 12/12 lolos dengan patch; 9 gagal di kode `34684ee`):
```python
import json
import pytest
from conftest import TASKDIR, BRIEF_MD, run
VB = "plan/scripts/validate_briefs.py"; SCAFFOLD = "plan/scripts/scaffold_brief.py"; TASK = "task/scripts/check_preconditions.py"

@pytest.fixture
def batch(repo):
    for nn in ("02", "10"):
        (repo / TASKDIR / f"brief-{nn}-order-fix.md").write_text(BRIEF_MD.format(status="READY"))
    return repo

@pytest.mark.parametrize("arg", ["1", "01", "#1", "brief-01"])
def test_brief_satu_digit_dinormalisasi(batch, arg):
    d = json.loads(run(VB, batch, "--taskdir", TASKDIR, "--brief", arg, "--json").stdout)
    assert d.get("error") is None and d["mode"] == "single"

@pytest.mark.parametrize("arg", ["0", "00", "x"])
def test_brief_nol_atau_asing_ditolak(batch, arg):
    d = json.loads(run(VB, batch, "--taskdir", TASKDIR, "--brief", arg, "--json").stdout)
    assert d["status"] == "FAIL" and "1..99" in d["error"]

def test_brief_1_tidak_menangkap_brief_10(batch):
    assert "brief-10" not in run(VB, batch, "--taskdir", TASKDIR, "--brief", "1", "--json").stdout

@pytest.mark.parametrize("spec", ['[{"nn": "01"}]', '{"briefs": ["01-order-fix"]}', '{"briefs": [{"nn": "01", "covers": "AC-1"}]}'])
def test_spec_bentuk_salah_fail_tanpa_traceback(repo, tmp_path, spec):
    f = tmp_path / "spec.json"; f.write_text(spec)
    p = run(SCAFFOLD, repo, "--taskdir", TASKDIR, "--write-matrix", "--spec", str(f))
    assert p.returncode == 1 and "Traceback" not in p.stderr and "bentuk spec tidak sah" in p.stdout

def test_task_chain_tanpa_nilai(repo):
    p = run(TASK, repo, "--taskdir", TASKDIR, "--lane", "DEFECT_RCA", "--chain")
    assert p.returncode != 2 and "expected one argument" not in p.stderr
```
(Bila B11 dikerjakan, pindahkan `spec.json` test ke `{taskdir}/.explore/`.)

### Selesai bila
Kelima contoh reproduksi + kasus brief-10 memberi vonis benar tanpa traceback.

---

## B17 [Rendah] Drift dokumen adapter.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 30 menit · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/profile/stacks/_CONTRACT.md:64-67`:
> "Enam baris perintah: `build`, `test`, `test-single`, `lint`, `typecheck`, `migration`. Tulis `tidak berlaku` bila stack tidak punya padanannya — dilarang mengarang perintah. `profile` mengeksekusi tiap perintah minimal sekali sebelum menuliskannya ke profil; `architect` memakainya di gerbang verifikasi penutup taskdir."

Ketujuh adapter memuat **8** baris (dicek lewat mdcp `md_content heading "Commands"`): `build`, `typecheck`, `typecheck-scoped`, `typecheck-per-brief`, `lint`, `test`, `test-single`, `migration` — `go.md:55-72`, `java-spring.md:41-56`, `node.md:42-58`, `bun.md:41-56`, `rust.md:56-76`, `php.md:45-61`, `php-codeigniter.md:42-59`. `profile/SKILL.md:79` sudah menyebut dua baris tambahan "disalin dari adapter tanpa dieksekusi", dan `architect/SKILL.md` Fase 3 butir 3b memakai `typecheck-per-brief`/`typecheck-scoped`.

### Masalah
Kontrak mengatakan 6. Adapter baru yang patuh kontrak tidak punya `typecheck-per-brief`, sehingga gerbang kompilasi per-brief architect tidak tahu harus jalan atau tidak. Gerbang kelayakan butir 3 ("Seluruh perintah di `## Commands` sudah dieksekusi") juga mustahil untuk baris `typecheck-per-brief`.

### Perbaikan (teks pengganti `_CONTRACT.md:64-67`)
```
Delapan baris perintah: `build`, `typecheck`, `typecheck-scoped`, `typecheck-per-brief`, `lint`, `test`, `test-single`, `migration`. Tulis `tidak berlaku` bila stack tidak punya padanannya — dilarang mengarang perintah. `typecheck-scoped` berplaceholder target (`<paket>`, `<module>`, `<path>`), dan `typecheck-per-brief` bernilai `ya` atau `tidak` beserta alasannya. Keduanya menjawab cara pemakaian, bukan status jalan, sehingga disalin `profile` tanpa dieksekusi. Enam sisanya dieksekusi `profile` minimal sekali sebelum ditulis ke profil. `architect` memakai `build`/`test` di gerbang verifikasi penutup, serta `typecheck-per-brief`/`typecheck-scoped`/`typecheck` di gerbang kompilasi per-brief.
```
Judul seksi `### 2.` konsumen: tambah "`backenddev:architect` (gerbang kompilasi per-brief)". Gerbang kelayakan butir 3 → "Seluruh perintah **yang dieksekusi** di `## Commands` …".

### Test
Lint L6.3: tiap `stacks/*.md` (kecuali `_CONTRACT.md`) memuat tepat 8 baris tabel `## Commands` dengan kunci di atas.

### Selesai bila
Kontrak dan ketujuh adapter menyebut delapan kunci yang sama.

---

## B18 [Rendah] Drift istilah.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 2 jam · **Bergantung pada:** keputusan user (kosakata) · **Memblokir:** —

### Lokasi & kode saat ini
| Lokasi | Kutipan | Masalah |
|---|---|---|
| `src/plugins/backenddev/skills/architect/SKILL.md:69` | "2. **Triase `COMPLETED`**: Pastikan implementor telah menulis `status: DONE`…" | Status brief/envelope implementor adalah `DONE`/`BLOCKED` (`agents/code-implementor.md` Format Output); `COMPLETED` tidak ada di mana pun selain `:69` dan `:145` |
| `src/plugins/backenddev/agents/code-reviewer.md:98` | "- Status: PASS" | Nilai tetap; tidak ada nilai untuk jalur `BLOCKED` gerbang masuk |
| `src/plugins/backenddev/agents/code-reviewer.md:99` | "- Report File: backenddev/docs/<taskdir>/REVIEW.md" | `{taskdir}` dispatcher sudah `backenddev/docs/2608181430-order-split` (`architect/dispatcher/reviewer.md:33`), jadi hasilnya prefix ganda `backenddev/docs/backenddev/docs/…` |
| `src/plugins/backenddev/agents/code-reviewer.md:94`, `:97-105` | "Kembalikan amplop maksimal 10 baris" + 9 baris amplop | `architect/dispatcher/reviewer.md:20` "Balikan: HANYA path `{taskdir}/REVIEW.md` dan tingkat severity tertinggi"; tabel Penanganan Balikan (`:49-55`) juga mengharapkan "Path + severity" |
| `src/plugins/backenddev/skills/system-analysis/SKILL.md:101` | "…· Self-review PASS" | Reviewer PRD mengembalikan `Approved`/`Issues Found` (`agents/prd-reviewer.md:45`) — **temuan tambahan** |

### Perbaikan
1. Satu kosakata status. Brief dan envelope subagent: `DONE | BLOCKED`. Status rantai architect: `DONE | TERTAHAN | BLOCKED`. Self-review dokumen: `Approved | Issues Found`.
   - `architect/SKILL.md:69` → "2. **Triase `DONE`**: …"; `:145` → "`### ARCHITECT EXECUTION REPORT — DONE · <taskdir> …`".
   - `system-analysis/SKILL.md:101` → "Self-review Approved" (dua kemunculan di baris itu).
2. Satu format envelope reviewer. `agents/code-reviewer.md:94-106`:
   ```markdown
   Kembalikan amplop persis 5 baris, tanpa teks lain. Dilarang mengutip isi `REVIEW.md` ke chat.

   ## Reviewer Report — {taskdir}
   - Status: DONE | BLOCKED (<stop condition gerbang masuk>)
   - Report File: {taskdir}/REVIEW.md
   - Highest Severity: CLEAN | P3 | P2 | P1
   - Commit: <sha7> `<pesan commit>` | SKIPPED (<sebab kegagalan git>)
   ```
   Rincian Scope/Coherence/Steps sudah ada di REVIEW.md, jadi tidak diulang di amplop.
   - `architect/dispatcher/reviewer.md:20-21` → "Balikan: amplop `## Reviewer Report` 5 baris sesuai `## Format Output` definisi agent-mu. Jangan kutip isi file review ke chat."
   - Tabel Penanganan Balikan: baris pertama "`Status: DONE` + `Highest Severity` CLEAN/P3/P2"; tambah baris "`Status: BLOCKED` → gerbang masuk reviewer gagal; baca stop condition, perbaiki, dispatch ulang maksimum sekali".

### Test
Manual: dispatch reviewer di fixture; amplop 5 baris, path tanpa prefix ganda; architect memetakan balikan tanpa jatuh ke "format rusak". Lint L6.3 opsional: string `COMPLETED` dan `Status: PASS` tidak muncul di `src/plugins/backenddev`.

### Selesai bila
Satu kosakata per jenis status, dan satu format envelope reviewer yang dirujuk agent dan dispatcher.

---

## B19 [Rendah] Batas tulis code-explorer hanya lewat prompt.
- [x] Selesai

**Plugin:** backenddev · **Estimasi:** 30 menit (koreksi klaim); hook mengikuti L3.4 · **Bergantung pada:** L3.4 (verifikasi identitas subagen di input hook PreToolUse) · **Memblokir:** —

### Lokasi & kode saat ini
`src/plugins/backenddev/skills/tech-lead/references/gate-scope.md:71`:
> "`code-explorer` terkunci struktural karena tidak memegang `Bash`; `Write`-nya dibatasi pada satu path laporan `.explore/` yang ditentukan pendispatch."

`src/plugins/backenddev/agents/code-explorer.md:4` `tools: Read, Grep, Glob, Write`. Batasnya hanya prosa di `:38`: "`Write` dibatasi pada **tepat satu path**: nilai `Berkas laporan`." `src/plugins/backenddev/hooks/hooks.json` hanya memuat `SessionStart`. Agent plugin mengabaikan field `hooks` (ISSUES.md, "Fakta dokumentasi").

### Masalah
"Terkunci struktural" benar untuk git (tanpa Bash), tetapi salah untuk `Write`: explorer bisa menimpa berkas apa pun, termasuk `src/**` atau `TASK.md`. Dokumen yang mengklaim pagar mekanis membuat reviewer manusia berhenti memeriksa.

### Perbaikan
1. Teks pengganti `gate-scope.md:71` (kalimat kedua): "`code-explorer` tidak memegang `Bash`, sehingga tidak dapat menjalankan git. Batas `Write`-nya ke satu path laporan `.explore/` saat ini **hanya ditegakkan prompt** (`agents/code-explorer.md` Kalibrasi); pagar mekanisnya menunggu hook PreToolUse (L3.4)."
2. Bila L3.4 membuktikan input hook memuat identitas subagen: tambahkan ke `hooks/hooks.json` entri `PreToolUse` matcher `Write|Edit` → `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/guard_write.py`:
   ```python
   import json, re, sys
   ev = json.load(sys.stdin)
   agent = ev.get("agent_type") or ev.get("subagent_type") or ""   # nama field WAJIB diverifikasi (L3.4)
   path = (ev.get("tool_input") or {}).get("file_path", "")
   if agent.endswith("code-explorer") and not re.search(r"(^|/)\.explore/[^/]+\.md$", path):
       print(f"code-explorer hanya boleh menulis laporan .explore/*.md; ditolak: {path}", file=sys.stderr)
       sys.exit(2)          # exit 2 = blokir tool call, stderr dikirim ke model
   sys.exit(0)
   ```
   Bila identitas subagen tidak tersedia, cukup koreksi klaim (butir 1) dan catat di `code-explorer.md` bahwa batasnya prosa.

### Test
Manual (**belum dijalankan**): `echo '{"agent_type":"backenddev:code-explorer","tool_name":"Write","tool_input":{"file_path":"src/x.go"}}' | python3 hooks/guard_write.py; echo $?` → `2`; path `backenddev/docs/x/.explore/a.md` → `0`.

### Selesai bila
Klaim di `gate-scope.md` sesuai kenyataan, dan (bila L3.4 memungkinkan) tulis explorer di luar `.explore/*.md` ditolak mekanis.

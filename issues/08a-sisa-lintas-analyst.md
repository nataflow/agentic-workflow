# Langkah 8a — Sisa Temuan: Lintas Plugin (X1–X2) dan analyst (A1–A12)

Versi detail seksi **8.0 Lintas plugin** dan **8.A analyst** dari `ISSUES.md`. ID dan judul item sama dengan `ISSUES.md`.

- **Path**: semua path di berkas ini relatif **root repo** (bukan relatif `src/plugins/<plugin>/` seperti di ISSUES.md 8.A).
- **Nomor baris**: commit `34684ee`, sama dengan ISSUES.md. Semua nomor baris di bawah sudah dicek ulang ke kode.
- **Bukti**: setiap reproduksi dijalankan ulang di scratchpad sesi ini (Python 3.13.5, git 2.47.3, Claude Code 2.1.281). Output di bawah adalah output nyata. Sidik 12-hex stabil karena fixture-nya deterministik. Yang berubah tiap run hanya path `mktemp`, stempel waktu, dan SHA commit.
- **Patch**: diff A2–A12 sudah diterapkan ke salinan plugin di scratchpad. 19 test di bawah hijau pada salinan ber-patch dan merah pada kode sekarang (19/19).

## Tujuan

1. Menutup dua celah lintas plugin yang membuat path skrip jadi `python3 /skills/...` (X1, X2).
2. Membuat serah-terima tiket analyst ke backenddev/frontenddev nyata, atau minimal jujur (A1).
3. Menambal celah `ticket.py`/`validate_doc.py`/`analyst_lib.py` (A2–A12) dengan test regresi.

## Urutan pengerjaan

| # | Item | Alasan urutan |
|---|---|---|
| 1 | **A2** | Tinggi, patch 6 baris; menutup jalan persetujuan tiket cacat. |
| 2 | **A1 (versi minimal)** | Mengoreksi klaim di plugin.json/README/template hari ini juga (±30 menit), sebelum versi penuh siap. |
| 3 | A7 → A5 → A11 → A8 | Perbaikan kecil di `analyst_lib.py`, tidak saling bergantung. A7 lebih dulu karena `int_field` dipakai A4. |
| 4 | A6 → A10 → A12 | Keluaran/CLI `ticket.py`. A12 menambah subperintah `ref` yang dipakai cek DRIFT A1. |
| 5 | A4 → A3 | A4 menambah `parse_review` dan `review_basi`; A3 memakai fondasi yang sama (`review.md`). |
| 6 | A9 | Menambah check validator. Ini bisa menggagalkan tiket lama, jadi kerjakan sesudah fondasi test ada. |
| 7 | X1 → X2 | Lintas plugin (frontenddev/backenddev). Jalan paralel dengan urutan 1–6. |
| 8 | **A1 (versi penuh)** | Menyentuh ±12 berkas backenddev/frontenddev dan butuh keputusan user (lihat bawah). |

## Dependensi dengan langkah lain

| Item | Terkait | Sifat |
|---|---|---|
| Semua A | L6.1 (`issues/06-test-ci.md`) | Test di sini memakai `tests/conftest.py` versi L6.1 (`git_repo`, `plain_dir`, `run_script`, `skill_script`). 06 sudah memuat test xfail A5/A6; test di sini menggantikan/melengkapinya. |
| A1 | L1.3 | Hook backenddev/frontenddev tidak mengecualikan `analyst:*`. Serah-terima lewat `ticket_source` baru berguna bila hook tidak membelokkan alur analyst. |
| A1 | B8, B9, B15 (Langkah 8.B) | Sama-sama menyunting `backenddev/skills/analyst/references/chain-rules.md` dan `task/SKILL.md`. Satukan PR atau urutkan agar tidak konflik. |
| A1 | L1.1 | Bila profil pindah ke `.claude/profile/<plugin>/`, `task` membaca profil dari lokasi baru. Ini tidak mengubah desain `ticket_source`. |
| A5, A7 | L5.9 | BOM di `split_frontmatter` diperbaiki L5.9. Patch A7 tidak menyentuh baris BOM. |
| X1 | L6.3 | Check lint **R2** (06-test-ci.md:879) baru hijau sesudah X1. R2 mengecualikan baris yang memuat kata "substitusi"; patch X1 di bawah konsisten dengan pengecualian itu. |
| X2 | L3.4 | Keduanya menyentuh agent code-reviewer. Tidak konflik isi. |

## Estimasi usaha

| Item | Estimasi |
|---|---|
| X1 | 3–4 jam |
| X2 | 1–2 jam |
| A1 | minimal 30 menit; penuh 1,5–2 hari |
| A2 | 30 menit |
| A3 | 2–3 jam |
| A4 | 1,5 jam |
| A5 | 45 menit |
| A6 | 1 jam |
| A7 | 45 menit |
| A8 | 30 menit |
| A9 | 1 jam |
| A10 | 1 jam |
| A11 | 30 menit |
| A12 | 1,5 jam |
| **Total** | **±4 hari** (A1 penuh) · ±2,5 hari (A1 minimal) |

## Definisi selesai

- Ke-14 item dicentang, masing-masing sudah memenuhi **Selesai bila**-nya.
- `python -m pytest tests/analyst` hijau, termasuk 19 test di berkas ini (`tests/analyst/test_ticket_8a.py`), tanpa marker `xfail` tersisa untuk A2–A12.
- Lint R2 (L6.3) hijau: nol `${CLAUDE_PLUGIN_ROOT}` literal di berkas non-SKILL.md dan non-agent, kecuali baris slot yang menyebut "substitusi".
- A1: salah satu dari dua varian di **Selesai bila** A1 terpenuhi, dan keputusan user tercatat di Log Keputusan ISSUES.md.

## Keputusan yang dibutuhkan user

| Item | Pilihan | Rekomendasi |
|---|---|---|
| A1-a | Namespace ID tiket: **(i)** tiket tetap menulis `AC-n`/`BR-n`, dan hilir merujuknya sebagai `TAC-n`/`TBR-n` (pemetaan di batas) · **(ii)** analyst menulis `TAC-n`/`TBR-n` langsung di kartu | (i): template, validator, reviewer, dan kartu Jira analyst tidak berubah. |
| A1-b | Tiket READY yang sudah memuat aktor dan aturan: **(i)** butir 2–4 chain-rules §1.1 dinilai hanya atas fakta di luar tiket (BRD bisa tidak terbit) · **(ii)** BRD tetap terbit dalam mode "serap tiket" | (i) plus (ii) sebagai jalur bila sumbu tetap aktif. |
| A1-c | Kerjakan versi penuh sekarang, atau minimal dulu | Minimal dulu, penuh sesudah L1.3. |
| A3 | Blok review disimpan ke `<ticketdir>/review.md` (klaim "TICKET.md satu-satunya berkas" berubah), atau tanpa persistensi (dispatch ulang tiap sesi) | `review.md`. |
| A9 | Check `domain_terms` berjejak: FAIL atau WARN | FAIL, hanya saat `elicitation: CLOSED`. |

## Fixture bersama F0 (untuk semua reproduksi A2–A12)

Salin-tempel sekali per shell (bash atau zsh). Isi heredoc ini juga menjadi berkas `tests/fixtures/analyst/ticket_valid.md` untuk test. Kartu dan catatan lolos kedua validator: `validate ticket` 9/9, `validate elicit` 8/8, `check --gate spec` 4/4.

```bash
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
C=$REPO/src/plugins/analyst/skills/_common
tk() { python3 "$C/ticket.py" "$@"; }
vd() { python3 "$C/validate_doc.py" "$@"; }
T=analyst/tickets/2609231400-cicilan
# fx_ticket <dir>: repo git berisi satu TICKET.md DRAFT (elisitasi CLOSED, kartu sah, belum direview)
fx_ticket() {
  mkdir -p "$1/$T"
  git -C "$1" init -q && git -C "$1" config user.email t@t && git -C "$1" config user.name t
  cat > "$1/$T/TICKET.md" <<'EOF'
---
status: DRAFT
elicitation: CLOSED
type: FEATURE
priority: HIGH
slug: cicilan
requester: Rina (Head of Sales)
created: 2026-09-23
external_ref: -
domain_terms: []
revision: 0
review: -
review_round: 0
---

# Admin Finance dapat mencatat pembayaran invoice korporat secara cicilan

## Latar Belakang

Invoice korporat di atas Rp 50 juta sering dibayar bertahap, tetapi sistem hanya mengenal status Belum Bayar dan Lunas.

## User Story

Sebagai Admin Finance, saya ingin memecah invoice korporat menjadi beberapa cicilan, agar sisa tagihan selalu akurat.

## Acceptance Criteria

- **AC-1**: Given invoice korporat bernilai Rp 60.000.000, when Admin Finance membuat jadwal 3 cicilan, then invoice menampilkan 3 baris cicilan (BR-1)
- **AC-2**: Given invoice bernilai Rp 40.000.000, when Admin Finance membuka invoice itu, then pilihan "Buat Cicilan" tidak tersedia (BR-1)

## Aturan Bisnis

- **BR-1**: Cicilan hanya untuk invoice pelanggan korporat bernilai minimal Rp 50.000.000.

## Di Luar Cakupan

- Denda keterlambatan — ditunda ke fase berikutnya

## Pertanyaan Terbuka

- Tidak ada.

## Lampiran

- Tidak ada.

## Catatan Elisitasi

### Permintaan Asli

> Pelanggan korporat sering minta bayar invoice besar dicicil. Tolong bikin fitur cicilan.

### Fakta

#### Masalah
Invoice korporat di atas Rp 50 juta sering dibayar bertahap; Finance mencatatnya di spreadsheet.

#### Aktor
- Admin Finance — membuat jadwal cicilan.

#### Kondisi Saat Ini
Invoice hanya berstatus Belum Bayar atau Lunas.

#### Kondisi Diinginkan
Admin Finance dapat memecah satu invoice menjadi beberapa cicilan.

#### Aturan Bisnis
- Cicilan hanya untuk invoice minimal Rp 50.000.000.

#### Batas Cakupan
Hanya pelanggan korporat.

#### Urgensi
Tinggi — dua klien besar menunggu.

#### Kasus Khusus
Tidak dibahas — peminta belum punya contoh.

#### Ukuran Keberhasilan
Tidak dibahas — belum diukur.

### Log Tanya-Jawab

| # | Tanggal | Pertanyaan | Jawaban | Sumber |
|---|---|---|---|---|
| 1 | 2026-09-23 | Invoice mana yang boleh dicicil? | Di atas 50 juta | Rina |

### Pertanyaan Terbuka

- Tidak ada.
EOF
  git -C "$1" add -A && git -C "$1" commit -qm init
}
```

## Kerangka test bersama

Berkas `tests/analyst/test_ticket_8a.py` memakai fixture L6.1 (`issues/06-test-ci.md` sub-tugas 3). Kepalanya di bawah; fungsi test tiap item ada di seksi item masing-masing. Ikuti prinsip 06: sebelum patch mendarat, pasang `@pytest.mark.xfail(reason="<ID>: …")` dan cabut di commit perbaikan.

```python
"""Regresi Langkah 8.A (A2–A12) — skenario = bagian Reproduksi issues/08a-sisa-lintas-analyst.md."""
import sys
from pathlib import Path

import pytest

from conftest import skill_script

TICKET = skill_script("analyst", "_common", "ticket.py")
VALIDATE = skill_script("analyst", "_common", "validate_doc.py")
TDIR = "analyst/tickets/2609231400-cicilan"
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "analyst" / "ticket_valid.md"
sys.path.insert(0, str(TICKET.parent))
import analyst_lib  # noqa: E402


@pytest.fixture
def repo(git_repo):
    """Repo git berisi satu TICKET.md DRAFT sah (elisitasi CLOSED, kartu lolos validator, belum direview)."""
    git_repo.write(f"{TDIR}/TICKET.md", FIXTURE.read_text(encoding="utf-8"))
    git_repo.commit("docs(ticket): fixture")
    return git_repo


@pytest.fixture
def tk(repo, run_script):
    return lambda *a, cwd=None, **kw: run_script(TICKET, *a, cwd=cwd or repo.path, **kw)


@pytest.fixture
def vd(repo, run_script):
    return lambda kind: run_script(VALIDATE, "--kind", kind, "--ticketdir", TDIR, cwd=repo.path)


def edit(repo, old, new):
    p = repo.path / TDIR / "TICKET.md"
    text = p.read_text(encoding="utf-8")
    assert old in text, old
    p.write_text(text.replace(old, new), encoding="utf-8")


def states(tk, root):
    return {r["ticketdir"]: r["state"] for r in tk("--root", str(root), "state", "--all", "--json").json()["ticketdirs"]}
```

Hasil nyata terhadap salinan ber-patch vs kode sekarang (`AW_REPO=<salinan> python -m pytest tests/analyst`):

```
== PATCHED
...................                                                      [100%]
19 passed in 1.90s
== ORIG
19 failed in 1.46s
```

## Ringkasan koreksi terhadap ISSUES.md

- **X1**: ISSUES.md mendaftar 15 baris. Ada **5 kemunculan tambahan**:
  - 4 baris tabel slot: `backenddev/.../architect/dispatcher/implementor.md:40`, `frontenddev/.../architect/dispatcher/implementor.md:71`, `frontenddev/.../architect/dispatcher/reviewer.md:39`, `frontenddev/.../contract/dispatcher/reviewer.md:32`.
  - 1 teks Tindakan skrip: `frontenddev/skills/task/scripts/validate_task.py:194`, yang dicetak ke model lalu disalin ke Bash.
  - Dua baris slot (`reviewer.md:39` `{template}` dan `contract/dispatcher/reviewer.md:32` `{adapter_path}`) menyuruh mengisi "hasil substitusi". Padahal SKILL.md pemiliknya tidak memuat path itu, sehingga tidak ada sumber substitusi.
- **A9**: README tidak menjanjikan kedua cek itu secara eksplisit. Yang ada adalah prinsip README:9–11 ("yang dapat divonis mesin divonis skrip") dan Iron Law `elicit/SKILL.md:10,13`.
- **A10**: temuan tambahan: direktori bertanda tidak sah (`draft-lama`) juga memblokir `new --slug lama` ("slug masih terbuka").
- Klaim dan nomor baris lain di 8.0/8.A cocok dengan kode sekarang.

---

## X1 [Sedang] `${CLAUDE_PLUGIN_ROOT}` literal di berkas yang dibaca lewat Read
- [ ] Selesai

**Plugin:** frontenddev (utama), backenddev · **Estimasi:** 3–4 jam · **Bergantung pada:** — · **Memblokir:** L6.3 check R2 hijau

### Konteks
Claude Code menyubstitusi `${CLAUDE_PLUGIN_ROOT}` hanya di isi SKILL.md (dan prompt agent, lihat X2). Berkas yang dimuat belakangan lewat Read tidak disubstitusi: dispatcher, references, dan stacks. Environment variable itu juga tidak ada di shell tool Bash. Akibatnya, blok perintah yang disalin apa adanya menjadi `python3 /skills/...`.

### Lokasi & kode saat ini
Inventaris lengkap diambil dengan `md_grep "${CLAUDE_PLUGIN_ROOT}"` di `src/plugins/**`, ditambah `grep` untuk `.py`/`.sh`/`.json`. Hasilnya 84 kemunculan di 39 berkas. Di luar SKILL.md ada 23 baris markdown (4 di antaranya agent, dibahas di X2) dan 1 baris Python. `hooks.json` sah karena perintah hook disubstitusi.

Kelas: **(a)** masuk ke prompt subagent · **(b)** blok perintah atau teks perintah yang akan disalin model ke Bash · **(c)** rujukan dokumentasi atau tabel slot.

Notasi usulan: `«nama.py»` berarti path absolut dari peta **Skrip:** di Precondition SKILL.md pemilik (yang sudah tersubstitusi). Ini prinsip yang sama dengan `analyst/skills/spec/dispatcher/reviewer.md:46` ("path skrip terhidrasi dari `SKILL.md`"). Tanda `«»` dipakai agar tidak tertukar dengan placeholder `<...>` maupun slot `{...}`.

| # | Berkas:baris (src/plugins/…) | Kutipan ringkas | Kelas | Pengganti usulan |
|---|---|---|---|---|
| 1 | `frontenddev/skills/contract/dispatcher/reviewer.md:18` | di dalam blok prompt (baris 9–23): ``Aturan Semantik: bagian 2 butir 7–13 `${CLAUDE_PLUGIN_ROOT}/skills/contract/templates/contract-template.md` `` | **(a)** | ``Aturan Semantik: bagian 2 butir 7–13 `{contract_template}`.``, ditambah baris slot baru (lihat sub-tugas 1) |
| 2 | `frontenddev/skills/contract/dispatcher/reviewer.md:32` | slot ``{adapter_path}`` · ``${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`` · "Hasil substitusi, bukan literal" | (c), **tanpa sumber** | `contract/SKILL.md` tidak memuat path adapter ber-`${…}` (hanya `stacks/<stack>.md` di :36). Tambah entri `adapter` ke peta Skrip `contract/SKILL.md:21`. Kolom sumber: "entri `adapter` peta **Skrip:** SKILL.md; `<stack>` dari `index.json`" |
| 3 | `…/contract/dispatcher/reviewer.md:42` | ```` ```bash ```` `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py --kind contract …` | **(b)** | `python3 «validate_doc.py» --kind contract --taskdir {taskdir}` |
| 4 | `…/contract/dispatcher/reviewer.md:43` | `python3 ${…}/skills/_common/review_round.py open …` | **(b)** | `python3 «review_round.py» open --taskdir {taskdir} --gate contract` |
| 5 | `…/contract/dispatcher/reviewer.md:57` | `python3 ${…}/review_round.py record …` | **(b)** | `python3 «review_round.py» record --taskdir {taskdir} --gate contract \` |
| 6 | `frontenddev/skills/plan/dispatcher/reviewer.md:137` | `python3 ${…}/skills/plan/scripts/validate_briefs.py …` | **(b)** | `python3 «validate_briefs.py» --taskdir {taskdir} --contract`, ditambah entri `validate_briefs.py` ke peta Skrip `plan/SKILL.md:20` (kini hanya ada di perintah :58) |
| 7 | `…/plan/dispatcher/reviewer.md:138` | `… review_round.py open …` | **(b)** | `python3 «review_round.py» open --taskdir {taskdir} --gate plan` |
| 8 | `…/plan/dispatcher/reviewer.md:157` | `… review_round.py record …` | **(b)** | `python3 «review_round.py» record --taskdir {taskdir} --gate plan \` |
| 9 | `frontenddev/skills/architect/dispatcher/reviewer.md:39` | slot ``{template}`` · Tetap · ``${…}/skills/architect/templates/review-template.md` — hasil substitusi`` | (c), **tanpa sumber**, lalu masuk prompt :20 | `architect/SKILL.md` tidak memuat path review-template. Tambah entri `review-template.md` ke peta Skrip `architect/SKILL.md:21`. Kolom sumber: "entri `review-template.md` peta **Skrip:** SKILL.md" |
| 10 | `…/architect/dispatcher/reviewer.md:53` | `python3 ${…}/skills/architect/scripts/validate_review.py …` | **(b)** | `python3 «validate_review.py» --taskdir {taskdir}` (sudah ada di peta `architect/SKILL.md:21`) |
| 11 | `frontenddev/skills/architect/references/execution-protocol.md:14` | `python3 ${…}/skills/architect/scripts/check_preconditions.py \ --taskdir <taskdir> --brief <NN>` | **(b)** | `python3 «check_preconditions.py» --taskdir <taskdir> --brief <NN>`, ditambah entri `check_preconditions.py` ke peta Skrip :21. SKILL Phase 1 (:38) merujuk ke sini untuk varian `--brief`. |
| 12 | `frontenddev/skills/architect/dispatcher/implementor.md:71` | slot ``{adapter_path}`` "diisi hasil substitusi di badan `architect/SKILL.md`" | (c), pola benar | biarkan (sumber ada di `architect/SKILL.md:42`) |
| 13 | `backenddev/skills/architect/dispatcher/implementor.md:40` | slot ``{adapter_path}`` "Substitusi … terjadi di badan `architect/SKILL.md`" | (c), pola benar | biarkan (sumber ada di `backenddev/skills/architect/SKILL.md:68`) |
| 14 | `frontenddev/skills/contract/references/layer-patterns.md:3` | "adapter `${…}/skills/profile/stacks/<stack-id>.md`" | (c) | "adapter `skills/profile/stacks/<stack-id>.md` (relatif root plugin)" |
| 15 | `frontenddev/skills/review/references/nine-dimensions-catalog.md:3` | idem | (c) | idem |
| 16 | `frontenddev/skills/profile/stacks/_CONTRACT.md:6` | "merujuknya lewat path `${…}/skills/profile/stacks/<stack-id>.md`" | (c) | "lewat path `skills/profile/stacks/<stack-id>.md` relatif root plugin (skill menerimanya sebagai path absolut dari peta **Skrip:** SKILL.md-nya)" |
| 17 | `frontenddev/skills/profile/stacks/_CONTRACT.md:98` | "menghidrasi slot `{adapter_path}` … dengan `${…}/…/<stack-id>.md`" | (c) | "… dengan path absolut adapter hasil substitusi di `architect/SKILL.md` Phase 2 butir 1" |
| 18 | `backenddev/skills/profile/stacks/_CONTRACT.md:73` | idem backend | (c) | "… hasil substitusi di `architect/SKILL.md` Fase 3 butir 1" |
| 19 | `frontenddev/skills/lead/references/lane-routing-matrix.md:82` | "divonis `python3 ${…}/skills/lead/scripts/taskdir_state.py` dari disk" | (c), berisiko (b) | "divonis `taskdir_state.py` (path di peta **Skrip:** `lead/SKILL.md:21`) dari disk" |
| 20 | `frontenddev/skills/task/scripts/validate_task.py:194` | teks Tindakan: ``"Tulis ledger lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py init "`` | **(b)** (dicetak skrip) | cetak path absolut dari `__file__` (sub-tugas 4) |

Ringkasan: (a) 1 + 1 tidak langsung (#9 masuk prompt `{template}`) · (b) 9 · (c) 10, dengan 2 di antaranya tanpa sumber substitusi.

### Reproduksi
```bash
echo "CLAUDE_PLUGIN_ROOT=[${CLAUDE_PLUGIN_ROOT}]"; env | grep -c '^CLAUDE_PLUGIN_ROOT='
bash -c 'echo python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py'
claude --version
```
Output (shell tool Bash sesi ini):
```
CLAUDE_PLUGIN_ROOT=[]
0
python3 /skills/_common/review_round.py
2.1.281 (Claude Code)
```

### Dampak
- #3–#8, #10, #11, #20: perintah gerbang review dan prasyarat unit frontenddev yang disalin apa adanya gagal dengan `can't open file '/skills/...'`. Model lalu menebak path atau melewati gerbang.
- #1, #9: subagent reviewer menerima path literal yang tidak bisa dibuka lewat Read. Aturan semantik atau kerangka laporan tidak terbaca.
- #2: slot `{adapter_path}` tidak punya sumber tersubstitusi, jadi contract-reviewer menerima path tebakan.

### Rencana perbaikan
1. **`frontenddev/skills/contract/SKILL.md:21`**: perluas peta Skrip.
   ```text
   4. Skrip: `chain.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py`; `review_round.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/review_round.py`; `validate_doc.py` = `${CLAUDE_PLUGIN_ROOT}/skills/_common/validate_doc.py`; `contract-template.md` = `${CLAUDE_PLUGIN_ROOT}/skills/contract/templates/contract-template.md`; `adapter` = `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`. Di `dispatcher/*.md`, `«nama»` berarti path absolut dari peta ini.
   ```
   `contract/dispatcher/reviewer.md`: baris 18 diganti sesuai tabel #1. Tambah slot:
   ```text
   | `{contract_template}` | Entri `contract-template.md` peta **Skrip:** SKILL.md | **[REQUIRED]** Path absolut hasil substitusi |
   ```
   Baris 32 diganti: ``| `{adapter_path}` | Entri `adapter` peta **Skrip:** SKILL.md, `<stack>` dari `index.json` | **[REQUIRED]** Hasil substitusi, bukan literal |``. Baris 42–43, 57 sesuai tabel. Tambah satu kalimat di atas blok bash :41: "`«nama.py»` = path absolut dari peta **Skrip:** SKILL.md."
2. **`frontenddev/skills/plan/SKILL.md:20`**: tambah ``; `validate_briefs.py` = `${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/validate_briefs.py` ``. Dispatcher :137, :138, :157 sesuai tabel.
3. **`frontenddev/skills/architect/SKILL.md:21`**: tambah ``; `check_preconditions.py` = `${CLAUDE_PLUGIN_ROOT}/skills/architect/scripts/check_preconditions.py`; `review-template.md` = `${CLAUDE_PLUGIN_ROOT}/skills/architect/templates/review-template.md` ``. Lalu ganti `dispatcher/reviewer.md:39`, `:53`, dan `references/execution-protocol.md:14` sesuai tabel.
4. **`frontenddev/skills/task/scripts/validate_task.py`**: path absolut dihitung dari lokasi skrip (skrip lain sudah mem-bootstrap `_common` lewat `__file__`, lihat baris 22).
   ```diff
   @@ top-level
   +CHAIN_PY = Path(__file__).resolve().parents[2] / "_common" / "chain.py"
   @@ def _check_9_chain
   -                  "Tulis ledger lewat `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py init "
   -                  "--taskdir <taskdir>`; dilarang mengetik baris ledger dengan tangan.")
   +                  f"Tulis ledger lewat `python3 {CHAIN_PY} init --taskdir <taskdir>`; "
   +                  "dilarang mengetik baris ledger dengan tangan.")
   ```
5. #14–#19: teks prosa sesuai kolom pengganti. Tidak ada perubahan perilaku.
6. Lint (L6.3 check R2) menjaga agar temuan ini tidak muncul lagi. Aturan pengecualiannya sudah ada di `issues/06-test-ci.md:1095` (baris yang memuat "substitusi" dikecualikan). Baris #12 dan #13 tetap lolos.

### Test yang ditambahkan / Verifikasi manual
- Check lint R2 (`scripts/lint_plugins.py`, 06-test-ci.md L6.3) menjadi hijau untuk 18 baris markdown non-agent. Tambah satu kasus R2 untuk `.py`:
  ```python
  def test_x1_skrip_tidak_mencetak_plugin_root_literal():
      plugins = Path(__file__).resolve().parents[1] / "src" / "plugins"
      bad = [f"{p.relative_to(plugins)}:{n}" for p in plugins.rglob("*.py") if "__pycache__" not in p.parts
             for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if "${CLAUDE_PLUGIN_ROOT}" in line]
      assert not bad, bad
  ```
- Verifikasi manual (sesi Claude Code nyata di repo React+Vite berprofil): jalankan Gate Contract. Periksa bahwa perintah `review_round.py open` yang dijalankan model memakai path absolut plugin, dan prompt contract-reviewer tidak memuat `${`.

### Selesai bila
- Tabel #1–#11 dan #14–#20 sudah diganti; #12 dan #13 tetap.
- Peta Skrip `contract`, `plan`, dan `architect` SKILL.md memuat setiap nama `«…»` yang dirujuk dispatcher/references-nya.
- R2 hijau dan test `.py` di atas hijau.

### Risiko & catatan
- Notasi `«»` baru. Alternatifnya meniru analyst persis (nama skrip polos plus kalimat "path dari SKILL.md"). Yang penting konsisten satu notasi per plugin.
- Menambah entri ke peta Skrip menambah beberapa baris di SKILL.md. Tidak ada risiko ke batas 1.536 karakter deskripsi karena yang bertambah badan SKILL, bukan frontmatter.

---

## X2 [Rendah] `${CLAUDE_PLUGIN_ROOT}` di badan agent
- [ ] Selesai

**Plugin:** backenddev, frontenddev · **Estimasi:** 1–2 jam · **Bergantung pada:** X1 (pola peta Skrip) · **Memblokir:** L6.3 R2 tanpa pengecualian agent

### Lokasi & kode saat ini
- `src/plugins/backenddev/agents/code-reviewer.md:25` (gerbang 4): ``adapter `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` … Absen → `BLOCKED` ``
- `src/plugins/frontenddev/agents/code-reviewer.md:25` (gerbang 5): ``dan `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md` memuat `## Review checklist`. Absen → … `BLOCKED`.``
- `src/plugins/frontenddev/agents/code-reviewer.md:31`: `` `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py files --taskdir {taskdir}` ``
- `src/plugins/frontenddev/agents/contract-reviewer.md:16`: ``Aturan semantik kanonik: bagian 2 butir 7–13 `${CLAUDE_PLUGIN_ROOT}/skills/contract/templates/contract-template.md`.``

### Masalah
Inspeksi binary 2.1.281 menunjukkan prompt agent disubstitusi, tetapi perilaku ini tidak terdokumentasi resmi. Bila versi berikutnya berhenti menyubstitusi, gerbang 4/5 code-reviewer selalu `BLOCKED`, rentang review frontenddev gagal dihitung, dan aturan semantik contract-reviewer tidak terbaca. Slot hidrasi di `backenddev/skills/architect/dispatcher/reviewer.md` hanya berisi `{taskdir}`, `{base_branch}` (:33–34). Di frontenddev, `architect/dispatcher/reviewer.md` tidak mengirim `adapter_path` maupun path `chain.py`.

### Perbaikan
1. Tambah slot di dispatcher, dengan sumber peta Skrip SKILL.md (pola X1):
   - `backenddev/skills/architect/dispatcher/reviewer.md`: `{adapter_path}` (sumbernya path yang sudah dipakai `architect/SKILL.md:68`).
   - `frontenddev/skills/architect/dispatcher/reviewer.md`: `{adapter_path}` (`architect/SKILL.md:42`) dan `{chain_py}` (peta `architect/SKILL.md:21`).
   - `frontenddev/skills/contract/dispatcher/reviewer.md`: `{contract_template}` dari X1 #1 (sudah menutup contract-reviewer).
2. Agent memakai slot, bukan env:
   - be code-reviewer:25 menjadi ``adapter `{adapter_path}` ada serta memuat `## Audit checklist` ``
   - fe code-reviewer:25 menjadi ``` `{adapter_path}` memuat `## Review checklist` ```
   - fe code-reviewer:31 menjadi `` `python3 {chain_py} files --taskdir {taskdir}` ``
   - contract-reviewer:16 menjadi ``bagian 2 butir 7–13 `{contract_template}` ``
3. Tambah baris di "Gerbang Masuk" tiap agent: "slot `{adapter_path}`/`{chain_py}` kosong atau memuat `${` → `BLOCKED`, minta dispatch ulang".

### Test
- Lint R2 tanpa pengecualian `agents/` (level WARN di 06-test-ci.md:1099 naik menjadi FAIL).
- Verifikasi manual: dispatch code-reviewer frontenddev di rantai contoh. Envelope tidak `BLOCKED` pada gerbang 5, dan `REVIEW.md` memuat rentang berkas rantai.

### Selesai bila
Nol `${CLAUDE_PLUGIN_ROOT}` di `src/plugins/*/agents/*.md`, dan ketiga dispatcher memuat slot pengganti beserta baris tabel Slot Hidrasi-nya.

---

## A1 [Tinggi] Serah-terima ke hilir tidak dikenali
- [ ] Selesai

**Plugin:** analyst, backenddev, frontenddev · **Estimasi:** minimal 30 menit · penuh 1,5–2 hari · **Bergantung pada:** keputusan A1-a/b/c; L1.3 (untuk versi penuh) · **Memblokir:** —

### Konteks
analyst menerbitkan `TICKET.md` READY yang sudah melewati review independen dan persetujuan user. Keempat titik keluarnya mengklaim tiket "diserahkan ke backenddev/frontenddev". Namun kedua plugin hilir tidak mengenal format ini: parameter mereka hanya string bebas, dan predikat BRD backenddev tidak menghitung `BR-{n}` tiket sebagai aturan yang sudah disepakati.

### Lokasi & kode saat ini
Klaim di analyst:
- `src/plugins/analyst/.claude-plugin/plugin.json:3`: `"… dengan review independen dan persetujuan user sebelum diserahkan ke backenddev/frontenddev"` (teks yang sama ada di `.claude-plugin/marketplace.json:12`).
- `src/plugins/analyst/README.md:115-117`: "tiket `READY` diserahkan dengan menempelkan isi `TICKET.md` sebagai permintaan ke `backenddev:tech-lead` dan/atau `frontenddev:lead`". Bandingkan README:139–140 ("Sengaja Belum Ada — Rujukan `AC-{n}` di `TASK.md` engineer … ditunda"): README sendiri mengakui keterlacakan belum ada.
- `src/plugins/analyst/skills/spec/SKILL.md:94`: `… — serahkan ke engineer: tempel isi TICKET.md (kartunya; …) sebagai permintaan ke backenddev:tech-lead dan/atau frontenddev:lead.`
- `src/plugins/analyst/skills/spec/templates/ticket-template.md:5`: `… milik engineer lewat backenddev:tech-lead / frontenddev:lead, yang menerbitkan TASK.md teknisnya sendiri dari tiket ini.`
- `src/plugins/analyst/skills/_common/ticket.py:128`: `row.update(state="READY", route="selesai — serahkan ke backenddev:tech-lead / frontenddev:lead")`

Hilir:
- `src/plugins/backenddev/skills/tech-lead/SKILL.md:25`: ``- `request` — string — `[REQUIRED]` — Permintaan kerja baru atau susulan; …``
- `src/plugins/frontenddev/skills/lead/SKILL.md:25`: ``- `prompt` — string — `[REQUIRED]` — permintaan kerja: fitur, bug, …``
- `src/plugins/backenddev/skills/analyst/references/chain-rules.md:13` (§1.1 butir 1):
  ```text
  1. Aturan bisnis yang disentuh belum disepakati user, dan tidak terbukti sebagai konstanta, guard, atau `BR-{n}` di taskdir mana pun.
  ```
  Butir 2 (:14, lebih dari satu aktor manusia), butir 4 (:16, kuota/batas waktu/hak persetujuan), dan butir 5 (:17, pertanyaan yang jawabannya "tidak ditemukan di kode maupun di taskdir mana pun").
- Tabrakan ID di hilir:
  - `backenddev/skills/business-analysis/templates/brd-template.md:35,65` (`BR-{n}` BRD).
  - `backenddev/skills/task/SKILL.md:58` (`AC-{n}` PRD).
  - `frontenddev/agents/code-reviewer.md:65`: AC `terbukti` bila ada "berkas test yang menyebut nomor AC itu". Test bernama `AC-3` dari tiket akan tercatat sebagai bukti `AC-3` CONTRACT.

### Reproduksi
Bukti statis (mdcp):
```
md_grep "TICKET|analyst/tickets|analyst:" src/plugins/frontenddev/**                     → files: 0, total: 0
md_grep "TICKET"                              src/plugins/backenddev/**                  → files: 0, total: 0
md_grep "analyst/tickets|analyst:intake|analyst:spec|tiket" src/plugins/backenddev/**    → 1 hit, tidak relevan
      (scan-guide.md:133 "prefix tiket (`OMS-123: ...`)")
```
Skenario (contoh terisi `ticket-template.md` bagian 3, `cicilan-pembayaran`): tiket READY dengan 3 aktor (Admin Finance, Pelanggan Korporat, Sales) serta BR-2 "maksimal 6 cicilan; jarak minimal 14 hari". Tiket ditempel sebagai `request` ke `backenddev:tech-lead`, lalu masuk lane PLANNING dan `backenddev:analyst` Fase 1:
- butir 1 aktif: BR tiket bukan "`BR-{n}` di taskdir mana pun";
- butir 2 aktif: lebih dari satu aktor manusia;
- butir 4 aktif: kuota dan batas waktu.

Hasilnya chain `BRD_PRD_BRIEF`, dan `business-analysis` Fase 2 "Elisitasi Kebutuhan Domain" (`business-analysis/SKILL.md:46`) menanyakan ulang aktor dan kuota yang sudah disetujui user di `analyst:spec`.

### Dampak
- Fakta yang sudah disetujui user bisa digali ulang, atau malah dikontradiksi oleh jawaban baru di BRD.
- Keterlacakan AC tiket → SC → brief → test hilang. `AC-3` tiket dan `AC-3` PRD/CONTRACT tidak bisa dibedakan.
- Klaim di keempat titik keluar analyst tidak benar hari ini.

### Rencana perbaikan

**Varian minimal (kerjakan dulu, tanpa menyentuh hilir).** Ganti klaim menjadi jujur:
1. `plugin.json:3` dan `marketplace.json:12`:
   ```text
   Skill dan subagent jembatan antara pengguna/stakeholder dan engineer: klasifikasi permintaan, elisitasi terarah dengan peminta non-engineer, dan penulisan TICKET.md non-teknis (user story, acceptance criteria, aturan bisnis) setara kartu Jira/Trello — dengan review independen dan persetujuan user. Serah-terima ke backenddev/frontenddev masih manual (tempel kartu); gerbang engineer belum mengenal format TICKET.md
   ```
2. `README.md:115-119` (paragraf pertama seksi Serah Terima):
   ```text
   Serah-terima **masih manual**: tempel kartu `TICKET.md` (H1 sampai `## Lampiran`) sebagai permintaan ke
   `backenddev:tech-lead` dan/atau `frontenddev:lead`. Gerbang engineer belum mengenal format ini:
   `BR-{n}` tiket tidak dihitung sebagai aturan yang sudah disepakati, sehingga `backenddev:analyst` dapat
   menjadwalkan BRD dan menanyakan ulang aturannya — sebutkan saat menempel bahwa aturan di tiket sudah
   disetujui peminta. Nomor `AC-{n}`/`BR-{n}` tiket bertabrakan dengan nomor PRD/BRD/CONTRACT; rujuk
   sebagai "AC-3 tiket <slug>".
   ```
3. `spec/SKILL.md:94`: ganti ekor kalimat menjadi `… — serah-terima manual: tempel kartu TICKET.md sebagai permintaan ke backenddev:tech-lead dan/atau frontenddev:lead (gerbang engineer belum membaca format ini; lihat README Serah Terima).`
4. `ticket-template.md:5`: ganti `…, yang menerbitkan TASK.md teknisnya sendiri dari tiket ini.` menjadi `…, yang menerbitkan TASK.md teknisnya sendiri dari kartu ini (serah-terima manual — gerbang engineer belum membaca format TICKET.md).`
5. `ticket.py:128`: `route="selesai — tempel kartu ke backenddev:tech-lead / frontenddev:lead (serah-terima manual)"`.

**Varian penuh (kontrak serah-terima `ticket_source`).** Polanya meniru `finding_source` yang sudah ada di kedua plugin (`backenddev/.../chain-rules.md:105`, `frontenddev/skills/task/SKILL.md:30,72`, `frontenddev/skills/task/scripts/validate_task.py:166-176`).

*Kontrak*
- **Parameter**: `ticket_source` berisi path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` relatif root repo. Isinya diteruskan apa adanya dan dilarang disimpulkan dari isi `request`/`prompt`. Permintaan yang tampak seperti tiket tanpa path membuat gerbang menanyakan path lewat `AskUserQuestion`.
- **Syarat tiket**:
  - frontmatter `status: READY` dan `elicitation: CLOSED`;
  - di repo git, commit terakhir yang menyentuh berkas bersubjek `docs(ticket): kunci TICKET <slug> READY` atau `docs(ticket): ref TICKET <slug>` (A12), **dan** `git status --porcelain -- <path>` kosong.

  Ini deteksi DRIFT berbasis git, tanpa menyalin algoritma sidik analyst. Di luar git, periksa frontmatter saja dengan WARN.
- **Cara hilir membaca**: yang dibaca hanya kartu (H1 sampai sebelum `## Catatan Elisitasi`), dengan pola baris kanonik `ticket-template.md` bagian 1: `- **AC-{n}**: …` dan `- **BR-{n}**: …`. Catatan elisitasi boleh dibaca sebagai jejak, tetapi tidak menjadi sumber kriteria.
- **Namespace (A1-a opsi i)**: hilir menulis `TAC-{n}` untuk `AC-{n}` tiket dan `TBR-{n}` untuk `BR-{n}` tiket. Analyst tidak berubah.
- **Keterlacakan**: tiap `TAC-{n}` dipikul **minimal satu** `SC-{n}` di `TASK.md` (disebut di prosa hasil), atau tercatat di `## Out of Scope` sebagai `- TAC-{n} <ringkas> — <alasan>`. Alasan ini wajib, misalnya porsi frontend yang dikerjakan frontenddev.
- **Kesepakatan aturan**: `TBR-{n}` dihitung "disepakati user" di chain-rules §1.1.

*Teks pengganti usulan per berkas (baris persis)*

1. `backenddev/skills/tech-lead/SKILL.md`: sisipkan sesudah :29.
   ```text
   - `ticket_source` — string — default `""` — path `analyst/tickets/<YYMMDDhhmm>-<slug>/TICKET.md` berstatus `READY` bila kerja ini lahir dari tiket analyst. Terisi → `request` = kartu tiket (H1 sampai `## Lampiran`) apa adanya. Dilarang disimpulkan dari isi `request`: permintaan yang tampak seperti tiket tanpa path → tanyakan path-nya lewat `AskUserQuestion`.
   ```
   Di :63 (Fase 1 butir 4), tambah di akhir: ``` `ticket_source` terisi → tiap `TAC-{n}` tiket (= `AC-{n}` kartunya) dihitung satu permukaan yang disebut `request`. ```
   Di :132 (Fase 4 butir 1), tambah: ``` Handoff dari tiket memikul slot `Ticket Source` (path TICKET.md; `references/gate-scope.md` bagian 4 B-2) dan meneruskannya sebagai `ticket_source`. ```
2. `backenddev/skills/tech-lead/references/gate-scope.md`: framing baru sesudah B-1 (:93–97).
   ```text
   ### B-2. Lane `PLANNING` → `analyst` (dari tiket analyst `READY`)

   > Rancang dan terbitkan brief untuk tiket `analyst/tickets/2609231400-cicilan-pembayaran/TICKET.md`. **Taskdir**: `backenddev/docs/2609241000-invoice-installment/` **Risk Level**: `MAJOR`. **Ticket Source**: `analyst/tickets/2609231400-cicilan-pembayaran/TICKET.md` — `TAC-1`…`TAC-7`, `TBR-1`…`TBR-3`. **Evidence**: `internal/invoice/service.go:88`. **File Scope**: `internal/invoice/`. **Acceptance Criteria**: `TASK.md` terkunci dengan tiap `TAC-{n}` dipikul `SC-{n}` atau tercatat di `## Out of Scope` beralasan, tiap hop ledger `## Chain` tercentang, seluruh brief `READY` ter-commit. **Stop Condition**: tiket tidak lagi `READY` atau disunting sesudah approve → BERHENTI, kembalikan ke `analyst:spec`.
   ```
3. `backenddev/skills/analyst/SKILL.md`: sisipkan sesudah :30.
   ```text
   - `ticket_source` — string — default `""` — path TICKET.md `READY` dari gerbang; diteruskan apa adanya ke `task` (dan ke `business-analysis` bila sumbu bisnis tetap aktif) menurut bagian 2.1 `references/chain-rules.md`; menyalakan pengakuan `TBR-{n}` di bagian 1.1. Dilarang disimpulkan dari isi `request`.
   ```
   Di :45 (Fase 2 butir 1), ganti ``… `chain`, dan `finding_source` apa adanya.`` menjadi ``… `chain`, `finding_source`, dan `ticket_source` apa adanya.``
4. `backenddev/skills/analyst/references/chain-rules.md`:
   - :13 (butir 1) diganti:
     ```text
     1. Aturan bisnis yang disentuh belum disepakati user, dan tidak terbukti sebagai konstanta, guard, `BR-{n}` di taskdir mana pun, atau `TBR-{n}` tiket `ticket_source` (`BR-{n}` kartu TICKET.md `READY` — sudah disetujui user lewat `analyst:spec`).
     ```
   - Sesudah :17, paragraf baru (A1-b opsi i):
     ```text
     **Tiket analyst sebagai bukti kesepakatan.** `ticket_source` terisi → butir 2–4 dinilai hanya atas aktor, urutan kerja, dan kebijakan yang **tidak** tertulis di kartu tiket atau pilar `Aktor`/`Aturan Bisnis`/`Kondisi Diinginkan` catatan elisitasinya; yang tertulis dihitung disepakati. Butir 5 aktif hanya untuk pertanyaan yang tidak dijawab tiket. Tiket yang tidak lagi `READY`, atau disunting sesudah approve, bukan bukti — hentikan dan kembalikan ke `analyst:spec`.
     ```
   - Sesudah :105 (§2.1, paragraf `finding_source`):
     ```text
     **`ticket_source` — penanda akar yang berangkat dari tiket analyst.** Gerbang mengisinya dengan path TICKET.md `READY`. `analyst` meneruskannya ke `task` (Fase 3 butir 7: keterpikulan `TAC-{n}`) dan, bila sumbu bisnis tetap aktif, ke `business-analysis`, yang memasukkan tiap `TBR-{n}` ke `## Business rules` sebagai `BR-{n}` ber-`Asal: TBR-{n}` tanpa menanyakannya ulang. Hop `PRD` dan `BRIEF` tidak memikulnya; keterlacakan mengalir lewat `SC-{n}`.
     ```
5. `backenddev/skills/task/SKILL.md`: sisipkan sesudah :31.
   ```text
   - `ticket_source` — string — default `""` — path TICKET.md `READY` saat akar berangkat dari tiket analyst; menyalakan Fase 3 butir 7. Dilarang disimpulkan dari isi `request`.
   ```
   Sesudah :69, butir baru:
   ```text
   7. **Akar dari tiket analyst.** `ticket_source` terisi → baca kartu TICKET.md (H1 sampai `## Lampiran`). Tiap `AC-{n}` tiket dirujuk sebagai `TAC-{n}` dan wajib disebut **minimal satu** butir `SC-{n}`, atau tercatat di `## Out of Scope` sebagai `- TAC-{n} <ringkas> — <alasan: porsi frontend | ditunda | tiket terpisah>`. Tulis frontmatter `ticket_source:`. Kalimat Given/When/Then tiket dilarang disalin apa adanya sebagai SC — SC tetap menamai permukaan teknis (endpoint, transisi, aturan).
   ```
   Di :73 (Fase 4), ganti "dari 3 sumber: …" menjadi "dari 4 sumber: …; dan `TAC-{n}` tiket yang bukan porsi taskdir ini (Fase 3 butir 7)."
   Di `task/templates/task-template.md:10-16`, tambah baris opsional `ticket_source: <path TICKET.md analyst>` sesudah `created:`, dengan catatan "hanya bila akar dari tiket; hilangkan bila tidak".
6. `backenddev/skills/task/scripts/check_preconditions.py`: tambah argumen `--ticket-source` dan check baru. Isinya sama dengan sketsa di butir 9.
7. `frontenddev/skills/lead/SKILL.md`: sisipkan sesudah :29 bullet `ticket_source` yang sama dengan butir 1 (ganti `request` → `prompt`). Di :108 (Phase 7), ganti `{ taskdir, lane, sections, request, evidence, clarification, finding_source, finding_ids }` menjadi `{ …, finding_ids, ticket_source }`.
8. `frontenddev/skills/task/SKILL.md`: sisipkan sesudah :31 bullet `ticket_source` (menyalakan Phase 3 butir 6). Sesudah :72, butir 6 (isi = butir 7 backenddev, dengan "SC menamai layar, rute, atau aksi"). Di :76, tambahkan sumber keempat. Di `task/templates/task-template.md:17-19`, tambah baris opsional `ticket_source:`. Di `:55`, tambah kalimat "Baris `ticket_source:` hanya bila akar dari tiket analyst". Di `:71` (self-test butir 7), tambah "Bila `ticket_source` terisi, tiap `TAC-{n}` kartu disebut minimal satu SC atau tercatat di `## Out of Scope`".
9. Validator frontenddev (**sketsa, diuji saat implementasi**). Di `frontenddev/skills/task/scripts/validate_task.py` `_check_7_placeholder_findings`, sesudah blok `finding_source`:
   ```python
   TICKET_AC = re.compile(r"^- \*\*AC-(\d+)\*\*:", re.MULTILINE)
   ...
           tsrc = str(self.fm.get("ticket_source") or "")
           if tsrc:
               tpath = self.root / tsrc
               if not tpath.is_file():
                   errors.append(f"ticket_source `{tsrc}` tidak ada")
               else:
                   card = tpath.read_text(encoding="utf-8").split("\n## Catatan Elisitasi", 1)[0]
                   carried = "\n".join(m.group(2) for m in self._sc_lines())
                   oos = "\n".join(self.sections.get("## Out of Scope", []))
                   lost = [f"TAC-{n}" for n in TICKET_AC.findall(card)
                           if not re.search(rf"\bTAC-{n}\b", carried + "\n" + oos)]
                   if lost:
                       errors.append("TAC tanpa SC pemikul maupun Out of Scope: " + ", ".join(lost))
   ```
   Di `frontenddev/skills/task/scripts/check_preconditions.py`, tambah `_check_6_ticket_source`, meniru `_check_5_finding_source` (:93-107):
   ```python
       def _check_6_ticket_source(self) -> None:
           name = "ticket_source READY & terkunci"
           if not self.ticket_source:
               return self._add(6, name, "PASS", "bukan dari tiket analyst")
           rel = normalize_taskdir(self.ticket_source)
           f = self.root / rel
           if not re.fullmatch(r"analyst/tickets/\d{10}-[a-z0-9-]+/TICKET\.md", rel) or not f.is_file():
               return self._add(6, name, "FAIL", f"`{rel}` bukan TICKET.md analyst", "Minta path dari analyst:spec.")
           fm = parse_frontmatter(f.read_text(encoding="utf-8"))
           if fm.get("status") != "READY" or fm.get("elicitation") != "CLOSED":
               return self._add(6, name, "FAIL", f"status `{fm.get('status', '-')}`", "Selesaikan di analyst:spec.")
           subj = git_out(self.root, "log", "-1", "--format=%s", "--", rel)
           dirty = git_out(self.root, "status", "--porcelain", "--", rel)
           if dirty or not subj.startswith(("docs(ticket): kunci TICKET", "docs(ticket): ref TICKET")):
               return self._add(6, name, "FAIL", "tiket disunting sesudah approve (DRIFT)",
                                "analyst:spec REVISE (reopen) lalu approve ulang.")
           self._add(6, name, "PASS", rel)
   ```
   (`git_out` = helper subprocess yang sudah ada di `_common/precondition_lib.py`; sesuaikan namanya dengan yang dipakai `is_committed`.)
10. Analyst, klaim versi penuh:
    - `plugin.json:3` / `marketplace.json:12`: `… dengan review independen dan persetujuan user; tiket READY diserahkan ke backenddev:tech-lead / frontenddev:lead lewat parameter ticket_source`.
    - `spec/SKILL.md:94`: `… — serahkan ke engineer: backenddev:tech-lead dan/atau frontenddev:lead dengan ticket_source: <ticketdir>/TICKET.md.`
    - `ticket-template.md:5`: `…, yang menerima path tiket ini sebagai ticket_source, merujuk AC-{n}/BR-{n} di sini sebagai TAC-{n}/TBR-{n}, lalu menerbitkan TASK.md teknisnya sendiri.`
    - `ticket.py:128`: `route="selesai — serahkan path TICKET.md sebagai ticket_source ke backenddev:tech-lead / frontenddev:lead"`.
    - README:113–122 ditulis ulang dengan inti kontrak di atas. Butir README:139–140 "Rujukan `AC-{n}`" dihapus dari "Sengaja Belum Ada".

### Test yang ditambahkan / Verifikasi manual
- Varian minimal: tidak ada test; cukup verifikasi manual `md_search "tempel|manual" src/plugins/analyst/README.md`.
- Varian penuh, `tests/frontenddev/test_validate_task.py`:
  - `test_a1_tac_tanpa_pemikul_gagal`: TASK.md ber-`ticket_source` ke tiket fixture (AC-1, AC-2); SC hanya menyebut `TAC-1` → FAIL "TAC tanpa SC pemikul maupun Out of Scope: TAC-2".
  - `test_a1_tac_di_out_of_scope_lolos`: tambah `- TAC-2 tombol cicilan — porsi frontend` → PASS.
- `tests/frontenddev/test_task_preconditions.py`: `test_a1_ticket_source_drift_gagal`. Tiket READY ter-commit dengan subjek `docs(ticket): kunci TICKET cicilan READY` → PASS. Sunting satu baris tanpa commit → FAIL "DRIFT".
- Tes yang sama untuk `backenddev/skills/task/scripts/check_preconditions.py`.
- Verifikasi manual (sesi nyata): tiket `cicilan-pembayaran` diserahkan ke `backenddev:tech-lead` dengan `ticket_source`. Chain turun ke `PRD_BRIEF` (bukan `BRD_PRD_BRIEF`) karena aktor dan kuota tercakup tiket, dan TASK.md memuat `TAC-1`…`TAC-7` di SC atau Out of Scope.

### Selesai bila
- **Varian minimal**: kelima teks analyst di atas diganti, dan tidak ada lagi kalimat yang mengklaim hilir "menerima" TICKET.md.
- **Varian penuh**: parameter `ticket_source` ada di 5 SKILL (tech-lead, analyst be, task be, lead, task fe); chain-rules §1.1 dan §2.1 diperbarui; kedua `check_preconditions.py` task memvonis READY/DRIFT; `validate_task.py` menagih keterpikulan TAC; test di atas hijau; klaim analyst diperbarui ke versi penuh.

### Risiko & catatan
- Deteksi DRIFT berbasis subjek commit bergantung pada pesan commit analyst (`ticket.py:297`). Bila format pesan itu berubah, check hilir ikut diubah. Catat keterkaitan ini sebagai komentar di kedua sisi.
- `ticket.py ref` (A12) mengubah berkas sesudah READY. Subjek commit-nya harus masuk daftar yang diterima check DRIFT.
- Opsi A1-a (ii) (analyst menulis `TAC-n`) mengubah `validate_doc.py` (`AC_LINE`, `BR_LINE`, `BR_TOKEN`), kedua template, dan `ticket-reviewer`. Kartu yang dilihat peminta non-engineer juga ikut berubah.

---

## A2 [Tinggi] `approve` meloloskan catatan elisitasi yang rusak
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 30 menit · **Bergantung pada:** — · **Memblokir:** —

### Konteks
README:89 menjanjikan `validate_doc.py --kind elicit` memvonis "`CLOSED` ⇒ nol pilar kosong dan nol pertanyaan memblokir". Tetapi `approve` dan `review` hanya menjalankan validator kartu. `check --gate spec` memang menjalankan validator elisitasi (check 4), tetapi `review`/`approve` tidak memanggil `check`.

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/ticket.py:274-283`:
```python
    errors = []
    if fm.get("status") != "DRAFT":
        errors.append(f"status `{fm.get('status', '-')}` bukan DRAFT")
    v = DocValidator("ticket", rel, root)
    if not v.run_all():
        errors.append("validate_doc.py --kind ticket FAIL")
    if fm.get("elicitation") != "CLOSED":
        errors.append("elicitation bukan CLOSED — elisitasi dibuka ulang; tuntaskan analyst:elicit dulu")
    digest = review_digest(path.parent)
    if str(fm.get("review", "")) != f"PASS @{digest}":
```
`cmd_review` (`ticket.py:232-248`) tidak menjalankan validator sama sekali.

### Reproduksi
Prasyarat: F0 dimuat.
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
python3 - "$T/TICKET.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("Tinggi — dua klien besar menunggu.", "_(belum terjawab)_")
s = s.replace("### Pertanyaan Terbuka\n\n- Tidak ada.\n",
              "### Pertanyaan Terbuka\n\n- **Q-2** [MEMBLOKIR]: Berapa maksimal cicilan? — menunggu: Budi\n")
p.write_text(s)
PY
vd --kind elicit --ticketdir $T | grep -E 'CHECK|FAIL'
vd --kind ticket --ticketdir $T | head -1
tk review --ticketdir $T --verdict PASS
tk approve --ticketdir $T --answer "Setujui" --no-commit; echo "exit=$?"
tk state --ready | tail -2
```
Output:
```
CHECK: validate TICKET.md (elicit) [FAIL] (6/8 passed)
[4] Pilar FEATURE                  : FAIL (CLOSED dengan pilar belum terjawab: Urgensi)
[6] Pertanyaan terbuka             : FAIL (CLOSED dengan 1 pertanyaan MEMBLOKIR)
CHECK: validate TICKET.md (ticket) [PASS] (9/9 passed)
REVIEW PASS: ronde 1/2 · PASS @59a53330c4c8/920596bb4187
APPROVE PASS: analyst/tickets/2609231400-cicilan/TICKET.md READY @a81adc4753d2
exit=0
- analyst/tickets/2609231400-cicilan · READY · FEATURE · Admin Finance dapat mencatat pembayaran invoice korporat secara cicilan
    → selesai — serahkan ke backenddev:tech-lead / frontenddev:lead
```

### Dampak
Tiket dengan pertanyaan memblokir yang belum terjawab dimateraikan READY dan diserahkan ke engineer. Aturan bisnisnya masih tebakan.

### Rencana perbaikan
1. `cmd_approve`: jalankan kedua validator.
2. `cmd_review`: tolak mencatat vonis (selain `DISPATCH_FAILED`) bila salah satu validator FAIL. Dispatch seperti itu melanggar gerbang masuk `spec/dispatcher/reviewer.md:38`.
```diff
--- a/src/plugins/analyst/skills/_common/ticket.py
+++ b/src/plugins/analyst/skills/_common/ticket.py
@@ def cmd_review
     if args.verdict == "DISPATCH_FAILED":
         print("REVIEW PASS: dispatch gagal dicatat, tidak dihitung ronde")
         return 0
+    rel = str(path.parent.relative_to(root))
+    bad = [k for k in ("ticket", "elicit") if not DocValidator(k, rel, root).run_all()]
+    if bad:
+        print("REVIEW FAIL: " + ", ".join(f"validate_doc.py --kind {k} FAIL" for k in bad)
+              + " — dispatch tidak sah; perbaiki draft (atau kembali ke analyst:elicit) lalu dispatch ulang")
+        return 1
@@ def cmd_approve
-    v = DocValidator("ticket", rel, root)
-    if not v.run_all():
-        errors.append("validate_doc.py --kind ticket FAIL")
+    for kind in ("ticket", "elicit"):
+        if not DocValidator(kind, rel, root).run_all():
+            errors.append(f"validate_doc.py --kind {kind} FAIL"
+                          + (" — catatan elisitasi rusak; kembali ke analyst:elicit" if kind == "elicit" else ""))
```
(Di `cmd_review`, blok `DISPATCH_FAILED` dipindah ke atas cek plafon. Perilakunya setara karena cek plafon lama sudah mengecualikan `DISPATCH_FAILED`.)

### Test yang ditambahkan
```python
def test_a2_review_menolak_elisitasi_rusak(repo, tk, vd):
    edit(repo, "Tinggi — dua klien besar menunggu.", "_(belum terjawab)_")
    assert vd("elicit").code == 1
    r = tk("review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert r.code == 1 and "--kind elicit FAIL" in r.out


def test_a2_approve_menolak_elisitasi_rusak(repo, tk):
    edit(repo, "### Pertanyaan Terbuka\n\n- Tidak ada.\n",
         "### Pertanyaan Terbuka\n\n- **Q-2** [MEMBLOKIR]: Berapa maksimal cicilan? — menunggu: Budi\n")
    p = repo.path / TDIR / "TICKET.md"          # vonis PASS atas sidik sekarang, seolah tercatat jalur lama
    text = p.read_text(encoding="utf-8")
    digest = f"{analyst_lib.content_hash(text, 'card')}/{analyst_lib.content_hash(text, 'elicit')}"
    p.write_text(analyst_lib.set_frontmatter_field(text, "review", f"PASS @{digest}"), encoding="utf-8")
    r = tk("approve", "--ticketdir", TDIR, "--answer", "Setujui", "--no-commit")
    assert r.code == 1 and "--kind elicit FAIL" in r.out
    assert "status: DRAFT" in p.read_text(encoding="utf-8")
```

### Selesai bila
Skenario Reproduksi berakhir dengan `REVIEW FAIL: validate_doc.py --kind elicit FAIL …` (exit 1), dan `approve` atas vonis PASS yang ditulis manual juga FAIL. Kedua test hijau.

### Risiko & catatan
`review` kini menjalankan dua validator (±ms). Tiket yang sedang DRAFT dengan elisitasi rusak tidak bisa direview sampai elisitasi dibenahi. Ini perilaku yang dimaksud.

---

## A3 [Sedang] Blok `## Ticket Review` tidak pernah disimpan
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 2–3 jam · **Bergantung pada:** A4 (`parse_review`), keputusan A3 · **Memblokir:** —

### Konteks
Reviewer bersifat read-only (`agents/ticket-reviewer.md:4` `tools: Read, Grep, Glob`), dan balikannya hanya hidup di percakapan. Tiga instruksi spec membutuhkan blok itu lintas sesi, tetapi `ticket.py review` hanya menyimpan `PASS|BLOCKED @sidik`.

### Lokasi & kode saat ini
- `src/plugins/analyst/skills/spec/SKILL.md:31`: "Keadaan `DRAFT` dengan `review_segar=ya` (draft tertunda yang belum diputuskan) → langsung Phase 5 tanpa menulis ulang."
- `spec/SKILL.md:70`: "… ditambah blok `## Ticket Review` terakhir apa adanya."
- `spec/dispatcher/reviewer.md:31`: ``| `{previous_verdict}` | Blok `## Ticket Review` ronde 1 | **[OPTIONAL]** Hanya ronde 2 …``
- `agents/ticket-reviewer.md:54`: "Laporan ini diteruskan `analyst:spec` apa adanya ke `ticket.py review` dan ke user". Padahal `ticket.py review` tidak menerima laporan.
- `src/plugins/analyst/skills/_common/ticket.py:245-247`:
  ```python
      digest = review_digest(path.parent)
      write_fields(path, review=f"{args.verdict} @{digest}", review_round=str(rnd + 1))
      print(f"REVIEW PASS: ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest}")
  ```

### Reproduksi
Prasyarat: F0 dimuat.
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
tk review --ticketdir $T --verdict BLOCKED
ls -A "$T"
grep -nE '^review' "$T/TICKET.md"
git status --porcelain
```
Output:
```
REVIEW PASS: ronde 1/2 · BLOCKED @59a53330c4c8/349039f58360
TICKET.md
12:review: BLOCKED @59a53330c4c8/349039f58360
13:review_round: 1
 M analyst/tickets/2609231400-cicilan/TICKET.md
```
Isi BLOCKER tidak tersimpan di mana pun.

### Dampak
Di sesi baru, Phase 5 harus menyajikan blok yang tidak ada, sehingga model mengarang atau membuangnya. Ronde 2 tidak punya `previous_verdict`, jadi "ronde menyempit" (`ticket-reviewer.md:35`) tidak bisa dilakukan. Model juga bisa mencatat `--verdict PASS` padahal blok reviewer berkata BLOCKED, dan tidak ada yang memeriksanya.

### Rencana perbaikan
1. `ticket.py review --report <berkas|->`: menyimpan blok ke `<ticketdir>/review.md` (timpa, hanya ronde terakhir) dengan kepala `<!-- ronde n/2 · VERDICT @sidik … -->`. Skrip juga **mencocokkan `- Verdict:` di blok dengan `--verdict`**.
2. `check --gate spec` mengeluarkan `review_report=<path>|-`.
3. `approve` ikut meng-commit `review.md` bila ada.
```diff
@@ top-level
+REVIEW_FILE = "review.md"  # blok `## Ticket Review` terakhir, ditulis hanya oleh `ticket.py review --report`
@@ def cmd_check (keadaan DRAFT)
+                resolved["review_report"] = f"{rel}/{REVIEW_FILE}" if (d / REVIEW_FILE).is_file() else "-"
@@ def cmd_review (sebelum write_fields)
+    report = ""
+    if args.report:
+        report = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
+        if not re.search(r"^## Ticket Review\s*$", report, re.MULTILINE):
+            print("REVIEW FAIL: --report bukan blok `## Ticket Review` reviewer")
+            return 1
+        said = re.search(r"^- Verdict:\s*(PASS|BLOCKED)\b", report, re.MULTILINE)
+        if not said or said.group(1) != args.verdict:
+            print(f"REVIEW FAIL: --verdict {args.verdict} tidak sama dengan `- Verdict:` di blok "
+                  f"({said.group(1) if said else 'tidak ada'}) — catat vonis reviewer apa adanya")
+            return 1
     digest = review_digest(path.parent)
     write_fields(path, review=f"{args.verdict} @{digest}", review_round=str(rnd + 1))
-    print(f"REVIEW PASS: ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest}")
+    if report:
+        (path.parent / REVIEW_FILE).write_text(
+            f"<!-- ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest} · ditulis ticket.py review; "
+            f"jangan disunting -->\n{report.strip()}\n", encoding="utf-8")
+    print(f"REVIEW PASS: ronde {rnd + 1}/{REVIEW_CAP} · {args.verdict} @{digest}"
+          + (f" · blok tersimpan {rel}/{REVIEW_FILE}" if report else ""))
@@ def cmd_approve
-        ok, out = git_commit(root, [f"{rel}/{TICKET_FILE}"], …)
+        paths = [f"{rel}/{TICKET_FILE}"] + ([f"{rel}/{REVIEW_FILE}"] if (path.parent / REVIEW_FILE).is_file() else [])
+        ok, out = git_commit(root, paths, …)
@@ main()
+    s.add_argument("--report", default="", help="blok `## Ticket Review` reviewer: path berkas atau `-` (stdin)")
```
4. Teks pengganti:
   - `spec/SKILL.md:62` (Phase 3 butir 3): "Catat balikan **seketika** … `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/ticket.py review --ticketdir <ticketdir> --verdict <PASS|BLOCKED> --report - <<'EOF'` + blok `## Ticket Review` reviewer apa adanya + `EOF` (`DISPATCH_FAILED` tanpa `--report`). Skrip menolak bila `- Verdict:` di blok berbeda dengan `--verdict`."
   - `spec/SKILL.md:31` (Phase 0): "… `review_segar=ya` → langsung Phase 5, sajikan isi `review_report` apa adanya; `review_report=-` (vonis tercatat sebelum `--report` ada) → dispatch ulang reviewer satu ronde bila plafon masih ada, bila tidak sajikan hanya baris vonis."
   - `spec/SKILL.md:66` (Phase 4): stage `<ticketdir>/TICKET.md` dan `<ticketdir>/review.md`.
   - `dispatcher/reviewer.md:31`: sumber `{previous_verdict}` = "path `review_report` dari `check --gate spec` (ronde 1)".
   - `agents/ticket-reviewer.md:54`: tetap, karena kini benar.
   - README:6–7, `elicit-template.md:3`: "`TICKET.md` adalah satu-satunya artefak yang disunting skill; `review.md` jejak vonis reviewer terakhir, hanya ditulis `ticket.py`."

### Test yang ditambahkan
```python
BLOCK = ("## Ticket Review\n- Verdict: BLOCKED\n- Ronde: 1\n- BLOCKER: 0 [MEKANIS] · 1 [SEMANTIK]\n\n"
         "**BLOCKER:**\n- [SEMANTIK] `TICKET.md:30` (fokus #2) — AC tidak teramati — QA tidak bisa menguji\n\n"
         "**ADVISORY:**\n- —\n")


def test_a3_blok_review_tersimpan_dan_verdict_dicocokkan(repo, tk):
    r = tk("review", "--ticketdir", TDIR, "--verdict", "PASS", "--report", "-", stdin=BLOCK)
    assert r.code == 1 and "tidak sama" in r.out
    assert tk("review", "--ticketdir", TDIR, "--verdict", "BLOCKED", "--report", "-", stdin=BLOCK).code == 0
    saved = (repo.path / TDIR / "review.md").read_text(encoding="utf-8")
    assert saved.startswith("<!-- ronde 1/2 · BLOCKED @") and "## Ticket Review" in saved
    assert f"review_report={TDIR}/review.md" in tk("check", "--gate", "spec", "--ticketdir", TDIR).out
```

### Selesai bila
`review --report` menyimpan blok dan menolak verdict yang berbeda; `check` mengeluarkan `review_report`; ketiga instruksi spec (Phase 0, 3, 4) dan dispatcher merujuk `review.md`; test hijau.

### Risiko & catatan
- Klaim "satu-satunya berkas ticketdir" (README:6, `elicit-template.md:3`) berubah. `classify()` tidak terpengaruh karena hanya membaca `TICKET.md`.
- Heredoc ber-delimiter berkutip (`<<'EOF'`) mencegah shell mengeksekusi backtick di dalam blok reviewer. Pola yang sama dipakai di B5.

---

## A4 [Sedang] Ronde review tidak di-reset saat elisitasi berubah
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 1,5 jam · **Bergantung pada:** A7 (`int_field`) · **Memblokir:** A3

### Konteks
Nilai `review` menyimpan sidik `<kartu>/<elisitasi>` saat vonis. `check` hanya mengeluarkan `review_segar=ya|tidak`, sehingga model tidak tahu bagian mana yang berubah. `revise` sudah mereset ronde bila basis fakta berubah (pola `revision_base`), tetapi SKILL hanya menyuruh `revise` untuk kasus "kembali dari elisitasi", dan sesi baru tidak bisa mengenali kasus itu.

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/ticket.py:215-219`:
```python
            if state["state"] == "DRAFT":
                resolved["revision"] = str(t.get("revision", "0"))
                resolved["review_round"] = str(t.get("review_round", "0"))
                fresh = str(t.get("review", "")) == f"PASS @{review_digest(d)}"
                resolved["review_segar"] = "ya" if fresh else "tidak"
```
`ticket.py:238-241`:
```python
    rnd = int(str(fm.get("review_round", "0")) or 0)
    if args.verdict != "DISPATCH_FAILED" and rnd >= REVIEW_CAP:
        print(f"REVIEW FAIL: plafon {REVIEW_CAP} ronde per revisi habis — sajikan temuan tersisa ke user")
        return 1
```
Rujukan lain: `spec/SKILL.md:31-32` (Phase 0), `:60` (Phase 3: plafon → lompat ke Phase 5), `:71` (Phase 5 selalu menawarkan *Setujui*).

### Reproduksi
Prasyarat: F0 dimuat.
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
tk review --ticketdir $T --verdict BLOCKED >/dev/null
tk review --ticketdir $T --verdict BLOCKED            # ronde 2/2
tk check --gate elicit --ticketdir $T --reopen | tail -1
python3 - "$T/TICKET.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("Hanya pelanggan korporat.", "Hanya pelanggan korporat di Jabodetabek.")
p.write_text(s)
PY
tk check --gate spec --ticketdir $T | tail -1
tk review --ticketdir $T --verdict PASS; echo "exit=$?"
tk approve --ticketdir $T --answer "Setujui" --no-commit; echo "exit=$?"
```
Output:
```
REVIEW PASS: ronde 2/2 · BLOCKED @59a53330c4c8/349039f58360
Terselesaikan: git=ya; keadaan=DRAFT
Terselesaikan: git=ya; keadaan=DRAFT; type=FEATURE; revision=0; review_round=2; review_segar=tidak
REVIEW FAIL: plafon 2 ronde per revisi habis — sajikan temuan tersisa ke user
exit=1
APPROVE FAIL: vonis review terakhir `BLOCKED @59a53330c4c8/349039f58360` bukan `PASS @59a53330c4c8/8729d98e67c6` (belum direview, BLOCKED, atau tiket/elisitasi berubah sesudah review → review ulang)
exit=1
```
Sidik kartu tetap (`59a53330c4c8`), sidik elisitasi berubah (`349039f58360` → `8729d98e67c6`), tetapi `check` tidak menyebutkannya.

### Dampak
Sesi baru mengikuti Phase 0 → Phase 2 → Phase 3, dilarang dispatch karena plafon, lalu Phase 5 menawarkan *Setujui* yang pasti FAIL. User baru menemukan jalan keluar (*Revisi*) sesudah satu kegagalan.

### Rencana perbaikan
```diff
@@ top-level
+REVIEW_VALUE = re.compile(r"^(PASS|BLOCKED) @([0-9a-f]{12})/([0-9a-f]{12})$")
+def parse_review(value: Any) -> Any:
+    """`PASS @<kartu>/<elisitasi>` → (verdict, sidik kartu, sidik elisitasi); selain itu None."""
+    m = REVIEW_VALUE.match(str(value).strip())
+    return m.groups() if m else None
@@ def cmd_check (keadaan DRAFT)
+                prev, cur = parse_review(t.get("review", "")), review_digest(d).split("/")
+                stale = [n for n, i in (("kartu", 1), ("elisitasi", 2)) if prev and prev[i] != cur[i - 1]]
+                resolved["review_basi"] = "belum" if not prev else (",".join(stale) or "-")
@@ def cmd_review
-    rnd = int(str(fm.get("review_round", "0")) or 0)
-    if args.verdict != "DISPATCH_FAILED" and rnd >= REVIEW_CAP:
+    rnd = int_field(fm, "review_round")
+    prev = parse_review(fm.get("review", ""))
+    elicit_now = content_hash(path.read_text(encoding="utf-8"), "elicit")
+    if prev and prev[2] != elicit_now:
+        rnd = 0  # basis fakta berubah sesudah ronde terakhir → siklus ronde baru (pola revision_base)
+    if rnd >= REVIEW_CAP:
```
Teks pengganti:
- `spec/SKILL.md:19` (Precondition 3): tambahkan `review_basi` ke daftar yang dibaca dari `Terselesaikan:`.
- `spec/SKILL.md:32` (Phase 0 butir 2) diganti: "**`review_basi` memuat `elisitasi`** (catatan elisitasi berubah sesudah ronde terakhir): jalankan `ticket.py revise` lebih dulu — basis fakta baru membuka siklus revisi — lalu Phase 1. `review_basi=kartu` → Phase 2 atas draft yang ada."
- `spec/SKILL.md:71` (Phase 5 butir 2) diganti: "`AskUserQuestion`: *Setujui (READY)* — **hanya bila `review_segar=ya`** · *Revisi (sebut poinnya)* · *Kembali ke elisitasi* · *Tahan*. `review_segar=tidak` dengan plafon habis → sajikan sebabnya tanpa opsi *Setujui*." (Ini juga menutup A12 butir 5.)

### Test yang ditambahkan
```python
def test_a4_ronde_reset_saat_elisitasi_berubah(repo, tk):
    for _ in range(2):
        assert tk("review", "--ticketdir", TDIR, "--verdict", "BLOCKED").code == 0
    edit(repo, "Hanya pelanggan korporat.", "Hanya pelanggan korporat di Jabodetabek.")
    assert "review_basi=elisitasi" in tk("check", "--gate", "spec", "--ticketdir", TDIR).out
    r = tk("review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert r.code == 0 and "ronde 1/2" in r.out
    assert tk("approve", "--ticketdir", TDIR, "--answer", "ok", "--no-commit").code == 0


def test_a4_kartu_berubah_tetap_kena_plafon(repo, tk):
    for _ in range(2):
        tk("review", "--ticketdir", TDIR, "--verdict", "BLOCKED")
    edit(repo, "- Denda keterlambatan — ditunda ke fase berikutnya",
         "- Denda keterlambatan — ditunda ke fase berikutnya atas keputusan peminta")
    assert "review_basi=kartu" in tk("check", "--gate", "spec", "--ticketdir", TDIR).out
    assert tk("review", "--ticketdir", TDIR, "--verdict", "PASS").code == 1
```

### Selesai bila
`check` mengeluarkan `review_basi`; `review` membuka siklus ronde baru hanya bila sidik elisitasi berubah (kartu yang berubah tetap kena plafon); Phase 5 tidak menawarkan *Setujui* saat review basi; kedua test hijau.

### Risiko & catatan
Reset otomatis tidak bisa dipakai untuk mengakali plafon: elisitasi hanya berubah lewat `analyst:elicit` (Iron Law spec :13, `CATATAN MILIK ELICIT`). Penyuntingan tangan tetap mungkin, tetapi itu melanggar guardrail, bukan celah skrip baru.

---

## A5 [Sedang] `cancel` merusak berkas tanpa frontmatter
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 45 menit · **Bergantung pada:** — · **Memblokir:** —

### Konteks
`intake/SKILL.md:106` menyarankan `ticket.py cancel` untuk ticketdir RUSAK. Tiket tanpa frontmatter adalah salah satu penyebab RUSAK.

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/analyst_lib.py:145-154`:
```python
def set_frontmatter_field(text: str, key: str, value: str) -> str:
    """Ganti nilai `key` di frontmatter, atau sisipkan sebelum pagar penutup."""
    end = text.find("\n---", 3)
    head, rest = text[:end], text[end:]
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    if pattern.search(head):
        head = pattern.sub(lambda _: f"{key}: {value}", head, count=1)
    else:
        head = f"{head}\n{key}: {value}"
    return head + rest
```
Bila `end == -1`, `head = text[:-1]` dan `rest` = karakter terakhir, sehingga field ditempel di akhir body. `ticket.py:325-330` (`cmd_cancel`) lalu memanggilnya tanpa pemeriksaan.

### Reproduksi
Prasyarat: F0 dimuat.
```bash
tmp=$(mktemp -d); cd "$tmp"; git init -q
D=analyst/tickets/2609231500-rusak; mkdir -p $D
printf '# Tiket tanpa frontmatter\n\n## Catatan Elisitasi\n\nisi\n' > $D/TICKET.md
tk state | tail -2
tk cancel --ticketdir $D --reason "dibatalkan user"; echo "exit=$?"
tail -3 $D/TICKET.md
tk state --all | tail -2
```
Output:
```
- analyst/tickets/2609231500-rusak · RUSAK · - · Tiket tanpa frontmatter
    → status tidak sah (elicitation -, status -)
CANCEL PASS: analyst/tickets/2609231500-rusak (TICKET.md)
exit=0
isi
status: CANCELLED
cancel_reason: "dibatalkan user"
- analyst/tickets/2609231500-rusak · RUSAK · - · Tiket tanpa frontmatter
    → status tidak sah (elicitation -, status -)
```

### Dampak
Skrip melapor PASS, tetapi tiket tetap RUSAK dan muncul terus di pemindaian. Body tiket ternoda dua baris frontmatter palsu.

### Rencana perbaikan
1. `set_frontmatter_field` raise `ValueError` bila tidak diawali `---` atau pagar penutup tidak ada.
2. `cmd_cancel`: tangkap `ValueError`, lalu sisipkan frontmatter baru (`status: CANCELLED`, `cancel_reason`) di atas isi lama tanpa menyentuh isi itu. Hasilnya tiket DIBATALKAN dan isinya tetap utuh sebagai jejak.
```diff
--- a/src/plugins/analyst/skills/_common/analyst_lib.py
+++ b/src/plugins/analyst/skills/_common/analyst_lib.py
@@ def set_frontmatter_field
-    """Ganti nilai `key` di frontmatter, atau sisipkan sebelum pagar penutup."""
+    """Ganti nilai `key` di frontmatter, atau sisipkan sebelum pagar penutup.
+
+    `ValueError` bila berkas tidak diawali pagar `---` atau pagar penutupnya tidak ada —
+    menyisipkan di posisi lain merusak body tanpa membuat frontmatter terbaca.
+    """
+    if not text.startswith("---"):
+        raise ValueError("berkas tanpa frontmatter (tidak diawali `---`)")
     end = text.find("\n---", 3)
+    if end == -1:
+        raise ValueError("frontmatter tanpa pagar penutup `---`")
--- a/src/plugins/analyst/skills/_common/ticket.py
+++ b/src/plugins/analyst/skills/_common/ticket.py
@@ def cmd_cancel
-    write_fields(d / TICKET_FILE, status="CANCELLED", cancel_reason=clean_value(args.reason))
-    print(f"CANCEL PASS: {rel} ({TICKET_FILE})")
+    try:
+        write_fields(f, status="CANCELLED", cancel_reason=clean_value(args.reason))
+        print(f"CANCEL PASS: {rel} ({TICKET_FILE})")
+    except ValueError as exc:
+        text = f.read_text(encoding="utf-8")
+        f.write_text(f"---\nstatus: CANCELLED\ncancel_reason: {clean_value(args.reason)}\n---\n\n{text}",
+                     encoding="utf-8")
+        print(f"CANCEL PASS: {rel} ({TICKET_FILE}: {exc} — frontmatter baru disisipkan di atas isi lama)")
     return 0
```
Perintah lain (`review`/`revise`/`approve`/`reopen`) sudah FAIL lebih dulu pada cek `status`, sehingga tidak pernah memanggil `write_fields` atas berkas tanpa frontmatter.

### Test yang ditambahkan
```python
def test_a5_set_frontmatter_field_menolak_tanpa_pagar():
    for text in ("# judul\n", "---\nstatus: DRAFT\n# tanpa pagar penutup\n"):
        with pytest.raises(ValueError):
            analyst_lib.set_frontmatter_field(text, "status", "CANCELLED")


def test_a5_cancel_berkas_tanpa_frontmatter(plain_dir, run_script):
    rel = "analyst/tickets/2609231500-rusak"
    plain_dir.write(f"{rel}/TICKET.md", "# Tiket\n\n## Catatan Elisitasi\n\nisi\n")
    r = run_script(TICKET, "cancel", "--ticketdir", rel, "--reason", "dibatalkan user", cwd=plain_dir.path)
    assert r.code == 0
    text = (plain_dir.path / rel / "TICKET.md").read_text(encoding="utf-8")
    assert text.startswith("---\nstatus: CANCELLED\n") and text.rstrip().endswith("isi")
    rows = run_script(TICKET, "state", "--all", "--json", cwd=plain_dir.path).json()["ticketdirs"]
    assert rows[0]["state"] == "DIBATALKAN"
```
Test ini menggantikan `test_cancel_berkas_tanpa_frontmatter` (xfail A5) di `issues/06-test-ci.md`.

### Selesai bila
Reproduksi berakhir dengan keadaan `DIBATALKAN` dan isi lama utuh; kedua test hijau.

### Risiko & catatan
Berkas ber-BOM (L5.9) juga tidak diawali `---` dan kini masuk jalur `ValueError`. Sesudah L5.9 menormalkan BOM di pembaca/penulis, jalur itu tidak lagi terpicu untuk kasus BOM.

---

## A6 [Sedang] Path root-relatif patah bila cwd di subdirektori
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 1 jam · **Bergantung pada:** — · **Memblokir:** —

### Konteks
Skrip me-resolve root lewat `git rev-parse --show-toplevel` (`analyst_lib.py:51-60`), sehingga semua path yang dicetak relatif root. Tetapi instruksi skill memakai path itu seolah relatif cwd: `git add`, dan slot `{ticketdir}` yang diteruskan ke Read milik reviewer.

### Lokasi & kode saat ini
- `src/plugins/analyst/skills/_common/ticket.py:176-177`:
  ```python
      (root / rel).mkdir(parents=True)
      print(f"NEW PASS: {rel} · git={'ya' if is_git_repo(root) else 'tidak'}")
  ```
- `src/plugins/analyst/skills/elicit/SKILL.md:66`: ``git add <ticketdir>/TICKET.md`` lalu ``git commit -m "docs(ticket): elisitasi <slug>" -- <ticketdir>/TICKET.md``. Pola yang sama di `spec/SKILL.md:66`.
- `spec/dispatcher/reviewer.md:29`: ``| `{ticketdir}` | … | **[REQUIRED]** Relatif root ruang kerja |``

### Reproduksi
Prasyarat: F0 dimuat.
```bash
tmp=$(mktemp -d); cd "$tmp"; git init -q; git config user.email t@t; git config user.name t
mkdir -p src/sub && cd src/sub
tk new --slug sub --type FEATURE
ls -d "$PWD/analyst" 2>&1
ls "$tmp/analyst/tickets"
D=$(ls -d "$tmp"/analyst/tickets/*-sub); D=analyst/tickets/${D##*/}
cp /dev/null "$tmp/$D/TICKET.md"
git add "$D/TICKET.md"; echo "git add exit=$?"
```
Output (stempel waktu berbeda tiap run):
```
NEW PASS: analyst/tickets/2609241954-sub · git=ya
ls: cannot access '/tmp/tmp.niTVfVxrPN/src/sub/analyst': No such file or directory
2609241954-sub
warning: could not open directory 'src/sub/analyst/tickets/2609241954-sub/': No such file or directory
fatal: pathspec 'analyst/tickets/2609241954-sub/TICKET.md' did not match any files
git add exit=128
```

### Dampak
Commit elisitasi dan draft gagal ketika sesi dimulai dari subdirektori (Failure path 5 elicit menampilkan galat mentah). Reviewer bisa diberi path yang tidak terbaca dari cwd sesi.

### Rencana perbaikan
1. `NEW PASS` dan baris `Terselesaikan:` pada `check` mencetak `root=<abs>`.
```diff
@@ def cmd_new
-    print(f"NEW PASS: {rel} · git={'ya' if is_git_repo(root) else 'tidak'}")
+    print(f"NEW PASS: {rel} · root={root} · git={'ya' if is_git_repo(root) else 'tidak'}")
@@ def cmd_check
-    resolved: Dict[str, str] = {"git": "ya" if is_git_repo(root) else "tidak"}
+    resolved: Dict[str, str] = {"root": str(root), "git": "ya" if is_git_repo(root) else "tidak"}
```
2. Teks pengganti:
   - `elicit/SKILL.md:18`: "→ `NEW PASS: <ticketdir> · root=<root> · git=<ya|tidak>`"; `:19`: "catat `root=` dan `git=` dari `Terselesaikan:`".
   - `elicit/SKILL.md:66` dan `spec/SKILL.md:66`: "`git -C <root> add <ticketdir>/TICKET.md` lalu `git -C <root> commit -m \"…\" -- <ticketdir>/TICKET.md`".
   - `spec/dispatcher/reviewer.md:29`: ``| `{ticketdir}` | `<root>/<ticketdir>` (root dari `Terselesaikan:`) | **[REQUIRED]** Path absolut |``

### Test yang ditambahkan
```python
def test_a6_new_dan_check_dari_subdir_mencetak_root(repo, tk):
    sub = repo.path / "src" / "sub"
    sub.mkdir(parents=True)
    r = tk("new", "--slug", "sub", "--type", "FEATURE", cwd=sub)
    assert r.code == 0 and f"root={repo.path}" in r.out
    assert not (sub / "analyst").exists()
    assert f"root={repo.path}" in tk("check", "--gate", "spec", "--ticketdir", TDIR, cwd=sub).out
```
Test ini menggantikan `test_new_dari_subdirektori_mencetak_root_absolut` (xfail A6) di 06.

### Selesai bila
Keluaran `new`/`check` memuat `root=`; tiga instruksi git dan satu slot dispatcher memakai root; test hijau.

### Risiko & catatan
Tidak ada. Menambah field keluaran tidak mengubah parser siapa pun (`--json` sudah memuat `root` di `state`).

---

## A7 [Rendah] Nilai frontmatter kosong diparse jadi `[]`
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 45 menit · **Bergantung pada:** — · **Memblokir:** A4 (`int_field`)

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/analyst_lib.py:117-120`:
```python
        key, _, value = line.partition(":")
        value = value.strip()
        if value in ("[]", ""):
            data[key.strip()] = []
```
Konsumennya:
- `validate_doc.py:107` `if not str(self.fm.get("requester", "")).strip()`, sedangkan `str([])` = `"[]"`;
- `ticket.py:238` `int(str(fm.get("review_round", "0")) or 0)`, juga `:260` (`revision`) dan `:312` (`reopened`).

### Masalah
Reproduksi (prasyarat F0):
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
sed -i 's/^requester: .*/requester:/' "$T/TICKET.md"
vd --kind elicit --ticketdir $T | sed -n '1,2p'
sed -i 's/^review_round: .*/review_round: dua/' "$T/TICKET.md"
tk review --ticketdir $T --verdict PASS 2>&1 | tail -1
sed -i 's/^review_round: .*/review_round:/' "$T/TICKET.md"
tk review --ticketdir $T --verdict PASS 2>&1 | tail -1
```
Output:
```
CHECK: validate TICKET.md (elicit) [PASS] (8/8 passed)
[1] Frontmatter                    : PASS (lolos)
ValueError: invalid literal for int() with base 10: 'dua'
ValueError: invalid literal for int() with base 10: '[]'
```
`requester` kosong lolos validasi, sedangkan field bilangan yang rusak menghasilkan traceback.

### Perbaikan
```diff
--- a/src/plugins/analyst/skills/_common/analyst_lib.py
+++ b/src/plugins/analyst/skills/_common/analyst_lib.py
@@
 UNANSWERED = "_(belum terjawab)_"
+LIST_FIELDS = ("domain_terms",)  # satu-satunya field frontmatter bertipe list
@@ def split_frontmatter
         key, _, value = line.partition(":")
-        value = value.strip()
-        if value in ("[]", ""):
-            data[key.strip()] = []
+        key, value = key.strip(), value.strip()
+        if value == "[]" or (value == "" and key in LIST_FIELDS):
+            data[key] = []
         elif value.startswith("[") and value.endswith("]"):
             items = _LIST_ITEM.findall(value[1:-1])
-            data[key.strip()] = [_unquote(v.strip()) for v in items if v.strip()]
+            data[key] = [_unquote(v.strip()) for v in items if v.strip()]
         else:
-            data[key.strip()] = _unquote(value)
+            data[key] = _unquote(value)
--- a/src/plugins/analyst/skills/_common/ticket.py
+++ b/src/plugins/analyst/skills/_common/ticket.py
@@
+def int_field(fm: Dict[str, Any], key: str) -> int:
+    """Field pembukuan bilangan; nilai rusak → FAIL rapi, bukan traceback."""
+    raw = str(fm.get(key, "0")).strip()
+    if not raw.isdigit():
+        raise SystemExit(f"FAIL: field `{key}: {raw}` bukan bilangan — field ini hanya ditulis ticket.py; "
+                         f"pulihkan nilainya dari riwayat git, dilarang menebak")
+    return int(raw)
@@ cmd_review / cmd_revise / cmd_reopen
-    rnd = int(str(fm.get("review_round", "0")) or 0)
+    rnd = int_field(fm, "review_round")
-    rev = int(str(fm.get("revision", "0")) or 0) if …
+    rev = int_field(fm, "revision") if …
-    n = int(str(fm.get("reopened", "0")) or 0) + 1
+    n = int_field(fm, "reopened") + 1
```
Field yang tidak ada tetap dibaca `0` (tiket lama tanpa `reopened`). Field yang ada tetapi kosong atau bukan angka menghasilkan FAIL.

### Test
```python
def test_a7_requester_kosong_gagal_domain_terms_kosong_tetap_list(repo, vd):
    edit(repo, "requester: Rina (Head of Sales)", "requester:")
    edit(repo, "domain_terms: []", "domain_terms:")
    r = vd("elicit")
    assert r.code == 1 and "requester kosong" in r.out
    assert "[8] domain_terms                   : PASS" in r.out


@pytest.mark.parametrize("value", ["dua", ""])
def test_a7_review_round_rusak_fail_rapi(repo, tk, value):
    edit(repo, "review_round: 0", f"review_round: {value}".rstrip())
    r = tk("review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert r.code == 1 and not r.traceback and "bukan bilangan" in r.err
```

### Selesai bila
`requester:` kosong menghasilkan FAIL "requester kosong"; `domain_terms:` kosong tetap list; `review_round` rusak menghasilkan FAIL tanpa traceback; ketiga test hijau.

---

## A8 [Rendah] Nomor baris temuan kebocoran relatif terhadap body
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 30 menit · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/analyst_lib.py:273`: `for no, raw in enumerate(body.splitlines(), 1):`. Pemanggilnya `validate_doc.py:317`: `leaks = scan_leaks(self.body, terms, skip_sections=("Lampiran", ELICIT_H2))`. `body` adalah hasil `split_frontmatter`, yaitu tanpa frontmatter dan tanpa baris kosong awal.

### Masalah
Reproduksi (prasyarat F0):
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
sed -i 's/hanya mengenal status Belum Bayar dan Lunas\./hanya menyimpan status Belum Bayar dan Lunas di database./' "$T/TICKET.md"
vd --kind ticket --ticketdir $T | grep '\[9\]'
grep -n 'database' "$T/TICKET.md"
```
Output:
```
[9] Nol kebocoran teknis           : FAIL (baris 5: istilah teknis «database»)
20:Invoice korporat di atas Rp 50 juta sering dibayar bertahap, tetapi sistem hanya menyimpan status Belum Bayar dan Lunas di database.
```
Validator menunjuk "baris 5", padahal baris berkasnya 20. Model yang menyunting berdasarkan nomor itu mendarat di frontmatter.

### Perbaikan
```diff
--- a/src/plugins/analyst/skills/_common/analyst_lib.py
+++ b/src/plugins/analyst/skills/_common/analyst_lib.py
@@
+def body_offset(text: str, body: str) -> int:
+    """Jumlah baris berkas sebelum `body` (frontmatter + baris kosong yang dibuang `split_frontmatter`)."""
+    return text[: len(text) - len(body)].count("\n") if text.endswith(body) else 0
@@
-def scan_leaks(body: str, allowed_terms: List[str], skip_sections: Tuple[str, ...] = ()) -> List[str]:
+def scan_leaks(body: str, allowed_terms: List[str], skip_sections: Tuple[str, ...] = (),
+               line_offset: int = 0) -> List[str]:
@@
-    for no, raw in enumerate(body.splitlines(), 1):
+    for no, raw in enumerate(body.splitlines(), 1 + line_offset):
--- a/src/plugins/analyst/skills/_common/validate_doc.py
+++ b/src/plugins/analyst/skills/_common/validate_doc.py
@@
-        leaks = scan_leaks(self.body, terms, skip_sections=("Lampiran", ELICIT_H2))
+        leaks = scan_leaks(self.body, terms, skip_sections=("Lampiran", ELICIT_H2),
+                           line_offset=body_offset(self.text, self.body))
```
(`body` selalu sufiks `text` karena `split_frontmatter` memotong `text[end + 4:]` lalu `lstrip("\n")`. Tambahkan juga `body_offset` ke daftar impor `validate_doc.py`.)

### Test
```python
def test_a8_nomor_baris_kebocoran_relatif_berkas(repo, vd):
    edit(repo, "hanya mengenal status Belum Bayar dan Lunas.", "hanya menyimpan status di database.")
    text = (repo.path / TDIR / "TICKET.md").read_text(encoding="utf-8")
    lineno = next(i for i, l in enumerate(text.splitlines(), 1) if "database" in l)
    assert f"baris {lineno}: istilah teknis «database»" in vd("ticket").out
```

### Selesai bila
Nomor baris temuan kebocoran = nomor baris berkas; test hijau.

---

## A9 [Rendah] Cek mekanis yang dijanjikan README belum ada
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 1 jam · **Bergantung pada:** keputusan A9 · **Memblokir:** —

**Koreksi terhadap ISSUES.md:** README tidak menjanjikan kedua cek ini secara eksplisit (md_search "Asumsi" di README hanya menemukan :71, "asumsinya" untuk kartu). Yang ada adalah prinsip README:9–11, "yang dapat divonis mesin divonis skrip", ditambah aturan yang hanya ditegakkan secara semantik:
- `elicit/SKILL.md:10` (Asumsi wajib dikonfirmasi di Phase 4) dan `:13` (`CLOSED` hanya sesudah konfirmasi fakta Phase 4);
- `elicit/SKILL.md:60` (asumsi yang dikonfirmasi dihapus labelnya);
- `elicit-template.md:86` (`domain_terms` "dikonfirmasi peminta").

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/validate_doc.py:214-216` (check terakhir `_elicit`):
```python
        terms = self.fm.get("domain_terms", [])
        self.add(8, "domain_terms", isinstance(terms, list), f"{len(terms) if isinstance(terms, list) else '-'} istilah",
                 "Tulis `domain_terms: [<istilah>, ...]` atau `domain_terms: []`.")
```
Tidak ada cek atas baris `Asumsi:` maupun bukti `domain_terms`.

### Masalah
Reproduksi (prasyarat F0):
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
sed -i 's/^Hanya pelanggan korporat\.$/Asumsi: hanya pelanggan korporat./' "$T/TICKET.md"
sed -i 's/^domain_terms: \[\]/domain_terms: [API]/' "$T/TICKET.md"
sed -i 's/pilihan "Buat Cicilan" tidak tersedia (BR-1)/pilihan "Buat Cicilan" tidak tersedia di API mitra (BR-1)/' "$T/TICKET.md"
vd --kind elicit --ticketdir $T | head -1
vd --kind ticket --ticketdir $T | head -1
grep -c 'API' "$T/TICKET.md"
```
Output:
```
CHECK: validate TICKET.md (elicit) [PASS] (8/8 passed)
CHECK: validate TICKET.md (ticket) [PASS] (9/9 passed)
2
```
Elisitasi CLOSED dengan asumsi yang belum dikonfirmasi tetap lolos. "API" masuk `domain_terms` sehingga lolos pemindai kebocoran kartu, padahal tidak ada jejak konfirmasinya di permintaan asli maupun log (dua kemunculan "API" itu hanya frontmatter dan baris AC).

### Perbaikan
Dua check baru di `_elicit`, aktif hanya saat `CLOSED`:
```diff
--- a/src/plugins/analyst/skills/_common/validate_doc.py
+++ b/src/plugins/analyst/skills/_common/validate_doc.py
@@
+ASSUMPTION = re.compile(r"^\s*(?:[-*]\s+)?Asumsi:")
@@ def _elicit (sesudah check 8)
+        assumed = [l.strip()[:50] for l in self.h3.get("Fakta", []) if ASSUMPTION.match(l)]
+        self.add(9, "Asumsi terkonfirmasi", not (closed and assumed),
+                 f"{len(assumed)} baris `Asumsi:`" + (" pada CLOSED" if closed and assumed else ""),
+                 "Konfirmasi tiap `Asumsi:` di Phase 4 elicit (hapus labelnya) atau kembalikan pilarnya ke "
+                 "Phase 2 sebelum `elicitation: CLOSED`.")
+
+        trail = "\n".join(self.h3.get("Permintaan Asli", []) + self.h3.get("Log Tanya-Jawab", [])).lower()
+        listed = terms if isinstance(terms, list) else []
+        untraced = [t for t in listed if t.strip() and not re.search(
+            rf"(?<![\w-]){re.escape(t.strip().lower())}(?![\w-])", trail)]
+        self.add(10, "domain_terms berjejak", not (closed and untraced),
+                 "lolos" if not untraced else "tanpa jejak di Permintaan Asli/Log: " + ", ".join(untraced),
+                 "Tiap istilah `domain_terms` wajib muncul di permintaan asli atau baris log konfirmasinya "
+                 "(`| n | ... | Apakah \"<istilah>\" nama produk? | Ya | <peminta> |`).")
```
Teks pengganti: `elicit-template.md` bagian 2 (daftar mekanis :86–92) mendapat butir 8 "**Asumsi**: `CLOSED` menuntut nol baris `Asumsi:` di `### Fakta`" dan butir 9 "**Jejak istilah domain**: tiap `domain_terms` muncul di `### Permintaan Asli` atau baris log". Butir semantik 8–12 dinomori ulang menjadi 10–14. `elicit/SKILL.md:65` merujuk "butir semantik 10–14" (lihat juga A12). Di Phase 1 (`elicit/SKILL.md:39`), konfirmasi istilah domain dicatat sebagai baris log.

### Test
```python
def test_a9_closed_dengan_asumsi_gagal(repo, vd):
    edit(repo, "Hanya pelanggan korporat.\n", "Asumsi: hanya pelanggan korporat.\n")
    r = vd("elicit")
    assert r.code == 1 and "[9] Asumsi terkonfirmasi" in r.out


def test_a9_domain_term_wajib_berjejak(repo, vd):
    edit(repo, "domain_terms: []", "domain_terms: [API]")
    r = vd("elicit")
    assert r.code == 1 and "tanpa jejak di Permintaan Asli/Log: API" in r.out
    row = "| 1 | 2026-09-23 | Invoice mana yang boleh dicicil? | Di atas 50 juta | Rina |"
    edit(repo, row, row + '\n| 2 | 2026-09-23 | Apakah "API" nama produk mitra? | Ya | Rina |')
    assert vd("elicit").code == 0
```

### Selesai bila
Kedua check ada dan hanya FAIL pada `CLOSED`; template bagian 2 dan penomoran SKILL diperbarui; kedua test hijau; contoh terisi kedua template tetap lolos (`domain_terms: []`, tanpa `Asumsi:`).

### Catatan
Tiket lama yang CLOSED dengan `domain_terms` tanpa jejak akan FAIL di `check --gate spec` (check 4 memanggil validator elisitasi). Umumkan di catatan rilis. Bila tidak diinginkan, jadikan check 10 WARN (`Checker.add(..., warn=True)`).

---

## A10 [Rendah] Kasus tepi `state`/`cancel`
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 1 jam · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini
- `src/plugins/analyst/skills/_common/ticket.py:132-136`: `ticketdirs()` memindai **semua** subdirektori `analyst/tickets/`.
- `:107-110`: `classify()` tidak memeriksa nama, sehingga direktori kosong bernama apa pun divonis `KOSONG`.
- `:165-167`: `cmd_new` mencocokkan slug dengan `rel.split("-", 1)[-1]`.
- `:325-327`:
  ```python
      if not (d / TICKET_FILE).is_file():
          print(f"CANCEL PASS: {rel} (direktori kosong — hapus saja)")
          return 0
  ```

### Masalah
Reproduksi (prasyarat F0):
```bash
tmp=$(mktemp -d); cd "$tmp"; git init -q
mkdir -p analyst/tickets/draft-lama analyst/tickets/2609231600-kosong
tk state
tk check --gate elicit --ticketdir analyst/tickets/draft-lama | sed -n '1,3p'
tk cancel --ticketdir analyst/tickets/draft-lama --reason x; echo "exit=$?"
tk new --slug lama --type FEATURE; echo "exit=$?"
tk cancel --ticketdir analyst/tickets/2609231600-kosong --reason x; echo "exit=$?"
ls analyst/tickets
```
Output:
```
TICKET STATE: 2 ticketdir
- analyst/tickets/2609231600-kosong · KOSONG · - · -
    → analyst:intake → analyst:elicit menulis TICKET.md ke ticketdir ini
- analyst/tickets/draft-lama · KOSONG · - · -
    → analyst:intake → analyst:elicit menulis TICKET.md ke ticketdir ini
CHECK: prasyarat elicit [FAIL] (1/2 passed)
[1] Ticketdir sah                  : FAIL (`analyst/tickets/draft-lama` bukan direktori analyst/tickets/<YYMMDDhhmm>-<slug>)
    * Tindakan: Alokasikan lewat `ticket.py new` dari analyst:intake.
CANCEL FAIL: `analyst/tickets/draft-lama` bukan ticketdir sah
exit=1
NEW FAIL: slug `lama` masih terbuka di analyst/tickets/draft-lama (KOSONG) — lanjutkan itu, atau pilih slug lain
exit=1
CANCEL PASS: analyst/tickets/2609231600-kosong (direktori kosong — hapus saja)
exit=0
2609231600-kosong
draft-lama
```
- `draft-lama` divonis KOSONG dengan rute elicit, tetapi `check` FAIL dan `cancel` FAIL. Ini jalan buntu.
- Temuan tambahan (**belum ada di ISSUES.md**): `new --slug lama` ikut diblokir.
- `cancel` atas direktori kosong melapor PASS tanpa menghapus apa pun, sehingga direktori itu muncul terus.

### Perbaikan
```diff
@@ def classify
     row = {"ticketdir": rel, "type": t.get("type", "-"), "title": title_of(ticket)}
-    if ts == "CANCELLED":
+    if not TICKETDIR_RE.match(rel):
+        row.update(state="NAMA_TIDAK_SAH", route=f"bukan ticketdir analyst — ganti nama ke {TICKETS_DIR}/"
+                                                 "<YYMMDDhhmm>-<slug> (git mv) atau pindahkan keluar analyst/tickets/")
+    elif ts == "CANCELLED":
@@ def cmd_new
     for rel in ticketdirs(root):
         r = classify(root, rel)
+        if r["state"] == "NAMA_TIDAK_SAH":
+            continue
@@ def cmd_cancel
-    if not (d / TICKET_FILE).is_file():
-        print(f"CANCEL PASS: {rel} (direktori kosong — hapus saja)")
+    f = d / TICKET_FILE
+    if not f.is_file():
+        if any(d.iterdir()):
+            print(f"CANCEL FAIL: {rel} tanpa {TICKET_FILE} tetapi berisi berkas lain — periksa dan hapus manual")
+            return 1
+        d.rmdir()
+        print(f"CANCEL PASS: {rel} (direktori kosong dihapus)")
         return 0
```
Teks pengganti `intake/SKILL.md` tabel Phase 1 (:32–38), tambah baris: ``| `NAMA_TIDAK_SAH` | bukan ticketdir analyst — laporkan baris skrip; tawarkan `git mv` ke nama `<YYMMDDhhmm>-<slug>` atau pindahkan keluar `analyst/tickets/` atas keputusan user |``. README:87 juga ditambah keadaan `NAMA_TIDAK_SAH`.

### Test
```python
def test_a10_nama_tidak_sah_dan_cancel_kosong(plain_dir, run_script):
    root = plain_dir.path
    (root / "analyst/tickets/draft-lama").mkdir(parents=True)
    (root / "analyst/tickets/2609231600-kosong").mkdir()
    rows = {r["ticketdir"]: r["state"]
            for r in run_script(TICKET, "state", "--json", cwd=root).json()["ticketdirs"]}
    assert rows["analyst/tickets/draft-lama"] == "NAMA_TIDAK_SAH"
    assert run_script(TICKET, "new", "--slug", "lama", "--type", "FEATURE", cwd=root).code == 0
    r = run_script(TICKET, "cancel", "--ticketdir", "analyst/tickets/2609231600-kosong", "--reason", "x", cwd=root)
    assert r.code == 0 and not (root / "analyst/tickets/2609231600-kosong").exists()
```

### Selesai bila
Keadaan `NAMA_TIDAK_SAH` beserta rutenya ada; `new` tidak diblokir direktori bernama tidak sah; `cancel` atas direktori kosong benar-benar menghapusnya (`rmdir` hanya berhasil bila kosong); test hijau.

---

## A11 [Rendah] Pesan gagal commit tidak informatif
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 30 menit · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini
`src/plugins/analyst/skills/_common/ticket.py:294-300`:
```python
    msg = f"APPROVE PASS: {rel}/{TICKET_FILE} READY @{sealed}"
    if is_git_repo(root) and not args.no_commit:
        ok, out = git_commit(root, [f"{rel}/{TICKET_FILE}"],
                             f"docs(ticket): kunci TICKET {rel.split('-', 1)[-1]} READY")
        msg += f" · commit {out}" if ok else f" · COMMIT GAGAL: {out.splitlines()[-1] if out else '-'}"
    print(msg)
    return 0
```

### Masalah
Reproduksi (prasyarat F0):
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"
git rm -rq --cached analyst && echo 'analyst/' > .gitignore && git add .gitignore && git commit -qm ignore
tk review --ticketdir $T --verdict PASS >/dev/null
tk approve --ticketdir $T --answer "Setujui"; echo "exit=$?"
git log --oneline | head -1
```
Output:
```
APPROVE PASS: analyst/tickets/2609231400-cicilan/TICKET.md READY @d7bbadd4a609 · COMMIT GAGAL: hint: Disable this message with "git config advice.addIgnoredFile false"
exit=0
ddb3af1 ignore
```
Penyebab sebenarnya (berkas di-ignore) hilang; yang tercetak hanya baris `hint:` terakhir. Exit 0 membuat kegagalan commit tidak terbedakan dari sukses, padahal `spec/SKILL.md:110` (Failure path 5) menuntut galat mentah disajikan.

### Perbaikan
```diff
--- a/src/plugins/analyst/skills/_common/analyst_lib.py
+++ b/src/plugins/analyst/skills/_common/analyst_lib.py
@@
+def git_error_line(out: str) -> str:
+    """Baris galat git yang bermakna: `fatal:`/`error:` lebih dulu, lalu baris non-`hint:` pertama."""
+    lines = [l.strip() for l in out.splitlines() if l.strip()]
+    for prefix in ("fatal:", "error:"):
+        hit = [l for l in lines if l.startswith(prefix)]
+        if hit:
+            return hit[0]
+    plain = [l for l in lines if not l.startswith("hint:")]
+    return " ".join(plain[:2]) if plain else (lines[0] if lines else "-")
--- a/src/plugins/analyst/skills/_common/ticket.py
+++ b/src/plugins/analyst/skills/_common/ticket.py
@@ def cmd_approve
-        msg += f" · commit {out}" if ok else f" · COMMIT GAGAL: {out.splitlines()[-1] if out else '-'}"
+        if not ok:
+            print(f"{msg} · COMMIT GAGAL: {git_error_line(out)} — READY sudah tertulis; commit manual "
+                  f"`git -C {root} commit -- {' '.join(paths)}` sesudah sebabnya dibereskan")
+            return 3
+        msg += f" · commit {out}"
```
Kontrak exit: 0 = READY dan ter-commit (atau tanpa git), 1 = approve ditolak, **3 = READY tertulis tetapi commit gagal**. Teks pengganti `spec/SKILL.md:110`: "**`approve` gagal commit** (exit 3; hook, gpg, `.gitignore`): status `READY` sudah tertulis; sajikan baris `COMMIT GAGAL` apa adanya dan minta user meng-commit sendiri dengan perintah yang dicetak. Dilarang `--no-verify`."

### Test
```python
def test_a11_commit_gagal_informatif_dan_exit_3(repo, tk):
    repo.git("rm", "-rq", "--cached", "analyst")
    repo.write(".gitignore", "analyst/\n")
    repo.commit("chore: ignore analyst", [".gitignore"])
    assert tk("review", "--ticketdir", TDIR, "--verdict", "PASS").code == 0
    r = tk("approve", "--ticketdir", TDIR, "--answer", "ok")
    assert r.code == 3 and "ignored" in r.out and "hint:" not in r.out


def test_a11_git_error_line():
    assert analyst_lib.git_error_line("hint: a\nfatal: index.lock ada\nhint: b") == "fatal: index.lock ada"
```

### Selesai bila
Pesan memuat penyebab (`The following paths are ignored …: analyst`), exit 3, SKILL Failure path 5 menyebut exit 3, dan test hijau.

---

## A12 [Rendah] Inkonsistensi instruksi
- [ ] Selesai

**Plugin:** analyst · **Estimasi:** 1,5 jam · **Bergantung pada:** A4 (butir 5), A9 (penomoran butir 1) · **Memblokir:** A1 penuh (subjek commit `ref`)

### Lokasi & kode saat ini, serta perbaikan per butir

| # | Lokasi | Saat ini | Perbaikan |
|---|---|---|---|
| 1 | `src/plugins/analyst/skills/elicit/SKILL.md:65` | "lalu self-test semantik butir 8–11 template" | Template memuat butir semantik **8–12** (`elicit/templates/elicit-template.md:96-100`; butir 12 = "Nol istilah teknis rekaan analis" di :100). Ganti menjadi "butir 8–12", atau "10–14" bila A9 mendarat. |
| 2 | `elicit/references/elicitation-guide.md:3` | "Dibaca di Phase 2 (`SKILL.md`) sebelum menyusun pertanyaan." | SKILL membacanya di Phase 1 (`elicit/SKILL.md:39` "Baca `references/elicitation-guide.md`"). Ganti menjadi "Dibaca di Phase 1 (`SKILL.md`); bagian 2 dipakai tiap giliran Phase 2." |
| 3 | `elicit-template.md:78`; `spec/templates/ticket-template.md:62` | Daftar field milik `ticket.py` tidak memuat `revision_base` (ditulis `ticket.py:265`). `ticket-template.md:62` juga tidak memuat `cancel_reason`. | Tambah `revision_base` (dan `cancel_reason`, `external_ref` bila `ref` diadopsi) ke kedua daftar. |
| 4 | `spec/SKILL.md:25` (`external_ref`), `ticket.py:206-208` (spec menolak READY) | Tidak ada jalur resmi mengisi `external_ref` sesudah READY. Menyunting tangan tidak memicu DRIFT (field di luar sidik `CONTENT_FIELDS`, `analyst_lib.py:195-199`), tetapi melanggar kepemilikan field. | Subperintah `ticket.py ref --ticketdir --ref <key>` (DRAFT/READY), dengan commit bersubjek `docs(ticket): ref TICKET <slug>`. Diff inti di bawah. Tambahkan juga ke tabel README:93 dan `spec/SKILL.md` Parameter `external_ref`: "sesudah READY → `ticket.py ref`". |
| 5 | `spec/SKILL.md:71` | *Setujui* selalu ditawarkan, termasuk saat plafon habis dan review basi. | Ditutup teks pengganti A4 (*Setujui* hanya bila `review_segar=ya`). |
| 6 | `ticket.py:162-164` vs `:343` | `if args.type not in TYPES:` tidak pernah tercapai karena argparse `choices=TYPES`. | Hapus :162–164; `--type` diberi `type=str.upper` agar `feature` diterima. |

Bukti butir 4 (prasyarat F0; `external_ref` disunting tangan sesudah READY tidak terdeteksi, dan `spec` menolak READY):
```bash
tmp=$(mktemp -d); fx_ticket "$tmp"; cd "$tmp"; tk review --ticketdir $T --verdict PASS >/dev/null
tk approve --ticketdir $T --answer ok --no-commit >/dev/null
sed -i "s/^external_ref: -/external_ref: FIN-123/" $T/TICKET.md
tk state --ready | head -2; tk check --gate spec --ticketdir $T | sed -n "4p"
```
```
TICKET STATE: 1 ticketdir
- analyst/tickets/2609231400-cicilan · READY · FEATURE · Admin Finance dapat mencatat pembayaran invoice korporat secara cicilan
[3] Keadaan menerima spec          : FAIL (READY)
```
Bukti butir 6:
```bash
tmp=$(mktemp -d); cd "$tmp"; tk new --slug x --type feature; echo "exit=$?"
```
```
usage: ticket.py new [-h] --slug SLUG --type {FEATURE,IMPROVEMENT,BUG}
ticket.py new: error: argument --type: invalid choice: 'feature' (choose from FEATURE, IMPROVEMENT, BUG)
exit=2
```

Diff inti (butir 4 dan 6):
```diff
@@ def cmd_new
-    if args.type not in TYPES:
-        print(f"NEW FAIL: type `{args.type}` bukan {'|'.join(TYPES)}")
-        return 1
@@
+def cmd_ref(root: Path, args: argparse.Namespace) -> int:
+    """`external_ref` di luar sidik konten: boleh diisi pada DRAFT maupun READY tanpa DRIFT."""
+    path = _ticket_path(root, args)
+    fm = read(path)
+    if fm.get("status") not in ("DRAFT", "READY"):
+        print(f"REF FAIL: TICKET.md berstatus `{fm.get('status', '-')}`")
+        return 1
+    write_fields(path, external_ref=clean_value(args.ref, 120))
+    print(f"REF PASS: external_ref = {clean_value(args.ref, 120)}")
+    return 0
@@ main()
-    s.add_argument("--type", required=True, choices=TYPES)
+    s.add_argument("--type", required=True, type=str.upper, choices=TYPES)
+    s = sub.add_parser("ref")
+    s.add_argument("--ticketdir", required=True)
+    s.add_argument("--ref", required=True, help="kunci atau tautan kartu Jira/Trello")
```
(Commit `docs(ticket): ref TICKET <slug>` lewat `git_commit` ditambahkan saat implementasi, dengan pola yang sama seperti `cmd_approve` dan exit 3 bila gagal. Salinan uji di scratchpad belum meng-commit.)

### Test
```python
def test_a12_type_huruf_kecil_diterima(plain_dir, run_script):
    assert run_script(TICKET, "new", "--slug", "x", "--type", "bug", cwd=plain_dir.path).code == 0


def test_a12_ref_sesudah_ready_tanpa_drift(repo, tk):
    tk("review", "--ticketdir", TDIR, "--verdict", "PASS")
    assert tk("approve", "--ticketdir", TDIR, "--answer", "ok", "--no-commit").code == 0
    assert tk("ref", "--ticketdir", TDIR, "--ref", "FIN-123").code == 0
    assert states(tk, repo.path)[TDIR] == "READY"
```
Tambahkan saat commit diimplementasikan: `test_a12_ref_commit_bersubjek_ref` (`git log -1 --format=%s` = `docs(ticket): ref TICKET cicilan`).

### Selesai bila
Keenam butir tabel ditangani; `new --type bug` diterima; `ref` mengisi `external_ref` pada READY tanpa DRIFT dan meng-commit dengan subjek yang diterima check DRIFT A1; test hijau.

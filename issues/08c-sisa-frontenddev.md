# 08c — Sisa Temuan frontenddev (C1–C14): Rincian Perbaikan

Sumber: `ISSUES.md` seksi **8.C frontenddev** (basis commit `34684ee`). Semua path di berkas ini relatif terhadap root repo. Nomor baris diverifikasi ulang ke kode saat ini (2026-09-24); isi `.md` dibaca lewat `mdcp`.

## Tujuan

Menutup 14 temuan sisa frontenddev (2 Sedang, 12 Rendah) dengan perubahan kecil yang dapat dikerjakan satu per satu. Item skrip dilengkapi reproduksi mandiri, patch yang **sudah diuji** pada salinan plugin di scratchpad, dan test pytest. Item teks dilengkapi kutipan dan teks pengganti.

## Cara memakai reproduksi dan patch

- Tiap skrip reproduksi mandiri: membuat repo git sementara (`mktemp -d`), memakai kode di `REPO`, dan meng-export `PYTHONDONTWRITEBYTECODE=1` agar tidak menulis `__pycache__` di repo.
- Variabel `PLUGIN` (default `$REPO/src/plugins/frontenddev`) bisa diarahkan ke salinan yang sudah dipatch untuk membuktikan perbaikan.
- Semua diff di bawah diuji dengan cara itu. Output "sebelum" di tiap item adalah output aktual dari kode `34684ee`. Nama direktori `/tmp/tmp.*` berubah tiap jalan.
- Hasil pytest (lihat [Infrastruktur test](#infrastruktur-test-bersama)): **39 passed** pada salinan yang dipatch; **27 failed, 12 passed** pada kode asli. Test yang lolos di kode asli adalah kasus kontrol.

## Urutan pengerjaan

| # | Item | Alasan urutan |
|---|---|---|
| 0 | Infrastruktur test (`src/plugins/frontenddev/tests/conftest.py`) | Dipakai semua test di bawah; selaraskan dengan L6.1 |
| 1 | C12 | Satu parameter di `format_report`, dipakai C5 (berkas yang sama) |
| 2 | C5 | `validate_task.py`, patch kecil |
| 3 | C3 | `chain.py` + helper `precondition_lib.py`; kerjakan sebelum L4.1/L4.5 menyentuh fungsi yang sama |
| 4 | C2 | `validate_doc.py` + teks template/SKILL ui-design |
| 5 | C4 | `taskdir_state.py` |
| 6 | C6 | `architect/scripts/check_preconditions.py` |
| 7 | C11 + C14 | Satu berkas (`review/scripts/check_preconditions.py`), satu PR |
| 8 | C1, C9 | Teks saja, cepat |
| 9 | C7 → C8 | C7 menetapkan nama/slug kanonik; C8 memindahkan butir berdasarkan nama itu |
| 10 | C10 | Sesudah keputusan L1.1 (lokasi profil) |
| 11 | C13 | Paling besar; bergantung pada C10 dan L1.1 |

## Dependensi dengan langkah lain

| Item | Terkait | Sifat |
|---|---|---|
| C2 | L5.6, L5.9 (`validate_doc.py`) | Berkas sama; urutan bebas, gabungkan test |
| C3 | L4.1 (`_require_review_pass`), L4.5 (`reopen`) di `chain.py` | Kerjakan C3 lebih dulu (kecil) lalu rebase L4.x; L4.5 perlu memulihkan `originals` bertipe `bytes` hasil C3 |
| C4 | L5.9 (BOM di `taskdir_state.py`), L4.6 (TUNTAS dari keberadaan REPORT) | Berkas sama; L4.6 harus juga menyentuh `taskdir_state.py:146-149` |
| C5 | L5.6, L5.7 (`validate_task.py`) | Berkas sama |
| C6 | — | Mandiri |
| C7, C8 | X1 (`${CLAUDE_PLUGIN_ROOT}` literal di `nine-dimensions-catalog.md:3`, `_CONTRACT.md:6,98`), L4.10 (`sveltekit.md:43`, `svelte-vite.md:42`), L6.3 (lint) | Berkas sama; lint L6.3 menegakkan hasil C8 |
| C10 | **L1.1** (konstanta `PROFILE_DIR`, direktori per plugin) | Diblokir L1.1: nilai default akan berubah |
| C11 | L4.7 (`chain_files` mengecualikan `frontenddev/reviews`), L3.3 (verifikasi penutup) | C11 memakai `chain_files`; perbaikan L4.7 otomatis ikut |
| C12 | L4.2 (`validate_report.py`) | Berkas sama |
| C13 | **L1.1**, C10, L4.10 (`commands.md`) | Diblokir L1.1 dan C10 |
| C14 | C11 | Berkas sama |

## Estimasi

| Item | Estimasi |
|---|---|
| Infrastruktur test | 1 jam |
| C1 | 0,5 jam |
| C2 | 2,5 jam |
| C3 | 1,5 jam |
| C4 | 2 jam |
| C5 | 1 jam |
| C6 | 1,5 jam |
| C7 | 1,5 jam |
| C8 | 2,5 jam |
| C9 | 0,25 jam |
| C10 | 1 jam |
| C11 | 1,5 jam |
| C12 | 0,5 jam |
| C13 | 5 jam |
| C14 | 0,75 jam |
| **Total** | **± 23 jam (± 3 hari kerja)** |

## Definisi selesai

- Ke-14 checkbox tercentang, masing-masing sesudah kriteria **Selesai bila**-nya terpenuhi.
- `python3 -m pytest src/plugins/frontenddev/tests -q` hijau, termasuk seluruh test di berkas ini.
- Skrip reproduksi tiap item skrip, dijalankan terhadap kode baru, menghasilkan output "sesudah" yang tercantum.
- Untuk item teks: `md_search` atas string lama yang disebut di **Selesai bila** mengembalikan 0 hasil.
- Contoh terisi di template (`ui-template.md` bagian 3, `task-template.md` bagian 3) tetap lolos validatornya.

## Ringkasan koreksi terhadap ISSUES.md

| Item | Koreksi / tambahan |
|---|---|
| C1 | Tambahan: dari lima dispatcher explorer, hanya milik `lead` yang tidak memuat `### Not Found`; `contract`, `plan`, `ui-design`, `ux-design` sudah memuatnya |
| C2 | Tambahan: template (`ui-template.md:75`) dan guardrail SKILL (`SKILL.md:69`) juga mendokumentasikan semantik "total ≥ 6", jadi ikut diubah |
| C3 | Tambahan: jalur pemulihan saat commit gagal (`chain.py:147-148`) juga menulis ulang berkas dengan LF, jadi tidak memulihkan byte asli |
| C4 | Tambahan: docstring juga salah untuk rute `LAPORAN` (`:20` menulis `frontenddev:report`, kode `frontenddev:architect (Phase 5)`) dan tidak memuat keadaan `DITUTUP` |
| C6 | **Koreksi**: rebase di worktree tetap tertahan Check 9 karena HEAD detached (pesannya "detached HEAD"). Yang benar-benar lolos adalah `git am` yang berhenti di worktree (`rebase-apply`, HEAD tetap di branch) |
| C8 | **Koreksi**: ketiga butir identik secara makna di keempat adapter, tetapi identik byte hanya di 2–3 adapter. Tambahan: dua butir lain (`: any`, `queryKey` tanpa factory) juga ada di keempatnya, dan kelimanya sudah ada di katalog netral. Membuang lima butir itu saja belum cukup untuk `sveltekit.md` (± 14.139 karakter) |
| C9 | Tambahan: `architect/SKILL.md:55` juga menulis "tepat sekali" |
| C11 | Tambahan: ambang macet ada di tiga tempat: `review` 60 detik, `profile` 60 detik (`profile/SKILL.md:85,195`), `architect` 5 menit |
| C12 | Tambahan: `task/scripts/validate_task.py:198` punya masalah yang sama (`PRECONDITION CHECK: task self-test`) |
| C14 | Tambahan: path absolut **di dalam** repo ditolak dengan pesan menyesatkan, dan symlink yang keluar repo lolos |

---

## Infrastruktur test bersama

Test di berkas ini memakai satu `conftest.py` di `src/plugins/frontenddev/tests/` (struktur usulan L6.1). Bila L6.1 sudah menulis conftest, cukup pastikan helper berikut tersedia: `run_script`, fixture `repo`, `init_repo`, `Repo.write/commit/git`, `task_md`, `TASKDIR`.

```python
# src/plugins/frontenddev/tests/conftest.py
"""Fixture bersama test frontenddev (struktur usulan L6.1)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILLS = PLUGIN / "skills"


def run_script(rel, *args, cwd=None):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run([sys.executable, str(SKILLS / rel), *map(str, args)],
                          cwd=cwd, capture_output=True, text=True, env=env)


class Repo:
    def __init__(self, root: Path):
        self.root = root

    def git(self, *args, check=True):
        return subprocess.run(["git", "-C", str(self.root), *args], check=check,
                              capture_output=True, text=True).stdout

    def write(self, rel, text, crlf=False):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.replace("\n", "\r\n" if crlf else "\n").encode("utf-8"))
        return path

    def commit(self, subject, *body):
        self.git("add", "-A")
        args = ["commit", "-q", "-m", subject]
        for b in body:
            args += ["-m", b]
        self.git(*args)
        return self.git("rev-parse", "--short", "HEAD").strip()


def init_repo(path: Path) -> Repo:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo(path)
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "t@t")
    repo.git("config", "user.name", "t")
    repo.git("config", "commit.gpgsign", "false")
    return repo


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path / "repo")


TASKDIR = "frontenddev/docs/2609240900-label"


def task_md(lane="HOTFIX_MINOR", sections="[]", sc_lines=None, chain=None, desc="Contoh."):
    sc = sc_lines or ["- [ ] **SC-1**: label benar — verifikasi: test `A.test.ts` hijau"]
    rows = chain if chain is not None else ["- [ ] BRIEF    — frontenddev:plan          → brief-*.md"]
    return ("---\nstatus: ACTIVE\nlane: %s\nsections: %s\ncreated: 2026-09-24\n---\n\n# Label\n\n"
            "## Description\n\n%s\n\n## Success Criteria\n\n%s\n\n## Out of Scope\n\n- Lainnya — di luar lingkup\n\n"
            "## Chain\n\n%s\n" % (lane, sections, desc, "\n".join(sc), "\n".join(rows)))


def as_json(proc):
    return json.loads(proc.stdout)
```

---

## C1 [Sedang] Dispatcher explorer lead menunggu seksi yang tidak selalu ada.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 0,5 jam · **Bergantung pada:** — · **Memblokir:** —

### Konteks

`code-explorer` punya dua keluaran: Bentuk A (ringkasan 400–900 token di context pendispatch, kerangkanya dari blok `Format laporan` milik pendispatch) dan Bentuk B (berkas detail di laci kerja). Agent diwajibkan menyalin seksi Bentuk A **persis** dari `Format laporan`. Tabel Penanganan Balikan milik `lead` punya baris untuk `### Not Found`, tetapi blok `Format laporan` milik `lead` tidak memuat seksi itu. Seksi itu hanya ada di Bentuk B.

### Lokasi & kode saat ini

Bentuk B — `src/plugins/frontenddev/agents/code-explorer.md:129-133`:

```markdown
## Gaps
- <hal yang belum dapat dipastikan dari pembacaan kode lokal>

### Not Found
<simbol yang dicari tapi TIDAK ditemukan, beserta direktori yang sudah disisir>
```

Aturan Bentuk A — `src/plugins/frontenddev/agents/code-explorer.md:144`, `:148`, dan batas `:163`:

```markdown
Kembalikan ringkasan **400–900 token** ke pendispatch, seksinya persis mengikuti blok `Format laporan` pada prompt — urutan seksi dan judul seksi disalin apa adanya.
- Seksi tanpa temuan dihapus, bukan diisi "tidak ada". ...
- [FORBIDDEN] Menyimpulkan tipe DTO dari pemakaian di presentasi, atau mengabaikan ketiadaan simbol — DTO diverifikasi dari deklarasi riil, fakta negatif wajib masuk `### Not Found`.
```

Blok `Format laporan` lead — `src/plugins/frontenddev/skills/lead/dispatcher/explorer.md:49-57` (akhir blok):

```markdown
### Risks
- <side-effect atau konsumen lain yang ikut terdampak bila bagian ini diubah>

### Caveats
<unknown, ambiguitas kode, atau penyimpangan konvensi dari `surface-map.md` profil>

### Full detail
<path Bentuk B yang benar-benar ditulis>
```

Penanganan balikan lead — `src/plugins/frontenddev/skills/lead/dispatcher/explorer.md:93-94`:

```markdown
| `confidence: low`, atau objective tidak terjawab | Dilarang mengarang temuan. Pertajam `{objective}` ... ulangi maksimum sekali dengan `{slug}` baru ... |
| `### Not Found` terisi | Fakta negatif yang sah: simbolnya memang belum ada, jadi pekerjaan ini pembuatan baru. Tetapkan slug baru berbasis konvensi kebab-case, bukan dari folder yang tidak ada |
```

Pembanding: `skills/ui-design/dispatcher/explorer.md:56`, `skills/ux-design/dispatcher/explorer.md:56`, `skills/contract/dispatcher/explorer.md:56`, `skills/plan/dispatcher/explorer.md:61` **memuat** `### Not Found` di blok `Format laporan`, di antara `### Caveats` dan `### Full detail`.

### Reproduksi

Tidak ada skrip: perilaku ini ada di teks prompt. Bukti statis lewat `mdcp`:

```
md_search "Not Found" di src/plugins/frontenddev/**/*.md
  agents/code-explorer.md:132 (Bentuk B, in_code), :163, :182, :194
  skills/contract/dispatcher/explorer.md:56 (Format laporan), :96 (balikan)
  skills/plan/dispatcher/explorer.md:61 (Format laporan), :102 (balikan)
  skills/ui-design/dispatcher/explorer.md:56 (Format laporan), :96 (balikan)
  skills/ux-design/dispatcher/explorer.md:56 (Format laporan), :96 (balikan)
  skills/lead/dispatcher/explorer.md:94 (balikan SAJA — tidak ada di Format laporan)
```

### Dampak

Saat simbol yang ditanya lead memang belum ada (kasus "fitur baru"), explorer harus memilih antara dua instruksi yang bertentangan: menaati `Format laporan` (fakta negatif hilang atau terselip di `### Caveats`), atau menaati `:163` dan menambah seksi di luar format. Bila memilih yang pertama, lead tidak melihat `### Not Found` dan jatuh ke baris `confidence: low`. Akibatnya lead mempertajam objective dan mendispatch ulang, alih-alih menetapkan pekerjaan sebagai pembuatan baru. Satu dispatch (400–900 token plus biaya penelusuran) terbuang per permintaan fitur baru.

### Rencana perbaikan

1. **`src/plugins/frontenddev/skills/lead/dispatcher/explorer.md`**: sisipkan seksi di blok `Format laporan`, tepat sesudah `### Caveats` (sama dengan empat dispatcher lain):

   ```markdown
   ### Caveats
   <unknown, ambiguitas kode, atau penyimpangan konvensi dari `surface-map.md` profil>

   ### Not Found
   <simbol, berkas, atau rute yang dicari tetapi TIDAK ditemukan, beserta direktori yang sudah disisir>

   ### Full detail
   <path Bentuk B yang benar-benar ditulis>
   ```

2. **`src/plugins/frontenddev/agents/code-explorer.md` Fase 5** (sesudah baris `:148`): tambah satu butir agar dispatcher baru yang lupa seksi ini tetap aman:

   ```markdown
   - `### Not Found` satu-satunya seksi yang boleh ditambahkan di luar blok `Format laporan`: bila ada fakta negatif dan blok itu tidak memuatnya, sisipkan tepat sebelum `### Full detail`. Fakta negatif dilarang dibuang atau dipindah ke `### Caveats`.
   ```

3. (Kebersihan, opsional) `agents/code-explorer.md:189-190`: dua butir Failure path bernomor `11.`. Ubah yang kedua menjadi `12.`.

### Test yang ditambahkan / Verifikasi manual

- `md_search` `"### Not Found"` di `skills/lead/dispatcher/explorer.md` → 2 hasil (blok format dan tabel balikan).
- Usulan untuk lint L6.3: untuk tiap `skills/*/dispatcher/explorer.md`, setiap `` `### <Seksi>` `` yang disebut di tabel "Penanganan Balikan" wajib muncul sebagai heading di blok `Format laporan` berkas yang sama.
- Manual: dari lead, dispatch explorer dengan objective simbol fiktif (`useInvoiceExportPage`). Bentuk A wajib memuat `### Not Found`, dan lead memilih baris "pembuatan baru", bukan re-dispatch.

### Selesai bila

Kelima dispatcher explorer memuat `### Not Found` di blok `Format laporan`, dan `code-explorer.md` Fase 5 menyatakan pengecualian untuk seksi itu.

### Risiko & catatan

Anggaran Bentuk A (400–900 token) tidak berubah: seksi tanpa temuan tetap dihapus.

---

## C2 [Sedang] Validator UI hanya menagih total state.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 2,5 jam · **Bergantung pada:** — · **Memblokir:** —

### Konteks

Instruksi ui-design menuntut **enam cabang per layar**, dan penomoran `ST-{n}` berlanjut lintas layar (layar kedua mulai `ST-7`). Validator hanya menghitung total `ST` dan menagih ≥ 6. UI.md dua layar dengan layar kedua hanya punya satu cabang tetap lolos. Begitu juga satu layar dengan cabang ganda dan cabang yang hilang.

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/_common/validate_doc.py:250-262`:

```python
    def _check_ids(self, prefix: str, ids: List[str]) -> None:
        problems = []
        if not ids:
            problems.append(f"nol `{prefix}-{{n}}` — seksi ID wajib memuat minimal satu baris")
        else:
            seq = sequential(ids, prefix)
            if seq:
                problems.append(seq)
        if prefix == "ST" and 0 < len(ids) < 6:
            problems.append(f"hanya {len(ids)} cabang ST — enam cabang state wajib dirancang "
                            "(normal, loading, kosong, error, initial, stale/mutating)")
        self._add("I", f"Penomoran {prefix}", problems, f"{len(ids)} {prefix} berurutan",
                  f"Nomori `{prefix}-{{n}}` berurutan dari `{prefix}-1` tanpa lompatan.")
```

Aturan "per layar" di instruksi:

- `src/plugins/frontenddev/skills/ui-design/SKILL.md:12` — "Tiap layar merancang enam cabang state ber-ID `ST-{n}`; ..."
- `src/plugins/frontenddev/skills/ui-design/SKILL.md:50` — "**Enam cabang wajib per layar**: normal/ready, loading (...), kosong (...), error (...), initial/idle, stale/mutating (...). Nomori `ST-{n}` berurutan lintas layar."
- `src/plugins/frontenddev/skills/ui-design/SKILL.md:61` — "Sajikan mockup, hierarki P1–P3, enam cabang per layar, dan pemetaan data."

Semantik "total" yang ikut terdokumentasi:

- `src/plugins/frontenddev/skills/ui-design/SKILL.md:69` — "**SIX STATES MANDATORY**: validator menolak kurang dari enam `ST-{n}`; ..."
- `src/plugins/frontenddev/skills/ui-design/templates/ui-template.md:75` — "3. **Cabang state**: heading `### ST-{n}. <nama>` berurutan dari `ST-1`, **minimal enam** — satu per cabang normal, loading, kosong, error, initial, stale/mutating. Layar kedua dan seterusnya melanjutkan nomornya (`ST-7`, ...), bukan mengulang dari `ST-1`. ..."

### Reproduksi

````bash
#!/usr/bin/env bash
# C2 — validator UI hanya menagih total ST >= 6
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
export PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d); cd "$tmp"; git init -q
TD=frontenddev/docs/2609240900-order-checkout; mkdir -p "$TD"

head_ui() { cat <<'H'
---
status: DRAFT
slug: order-checkout
order: 20
stack: react-vite
based_on: 3f9c2ab (2026-09-23)
---

# UI Design — Checkout

Rancangan antarmuka dua layar checkout.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+----------------+
| Keranjang      |
+----------------+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| CTA Bayar | Primary (P1) | `button.primary` | Aksi utama |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

H
}
tail_ui() { cat <<'T'

## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris item | `name` | View-Model | apa adanya |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: `useCheckoutPage`.
T
}
six() { # $1 = nomor awal
  local n=$1
  printf '### ST-%d. State Normal (Data Terisi / Ready)\n- Daftar item.\n\n' $n
  printf '### ST-%d. State Loading (Skeleton Shimmer)\n- Skeleton.\n\n' $((n+1))
  printf '### ST-%d. State Kosong (Empty State)\n- Kosong + CTA.\n\n' $((n+2))
  printf '### ST-%d. State Error (Connection / Server Failure)\n- Banner + Coba Lagi.\n\n' $((n+3))
  printf '### ST-%d. State Initial / Idle\n- Sama dengan loading.\n\n' $((n+4))
  printf '### ST-%d. State Stale / Mutating (Optimistic Overlay)\n- Overlay.\n' $((n+5))
}
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
run() { echo "== $1"; out=$(python3 "$PLUGIN/skills/_common/validate_doc.py" --kind ui --taskdir "$TD" --root "$tmp"); rc=$?
        echo "$out" | grep -E '^DOC|\[I\]|      - '; echo "exit=$rc"; }

# (a) satu layar, enam cabang lengkap — seharusnya PASS
{ head_ui; six 1; tail_ui; } > "$TD/UI.md"; run "a: 1 layar x 6 cabang"
# (b) dua layar: layar 2 hanya punya ST-7 Normal — seharusnya FAIL
{ head_ui; six 1; printf '\n### ST-7. State Normal — Layar 2: Pembayaran\n- Form kartu.\n'; tail_ui; } > "$TD/UI.md"; run "b: layar 2 hanya 1 cabang"
# (c) satu layar, enam ST tapi 'loading' ganda dan 'kosong' hilang — seharusnya FAIL
{ head_ui; six 1 | sed 's/State Kosong (Empty State)/State Loading Ulang (Skeleton)/'; tail_ui; } > "$TD/UI.md"; run "c: 6 ST, cabang kosong hilang"
````

Output aktual (kode `34684ee`):

```
== a: 1 layar x 6 cabang
DOC VALIDATION: UI.md [PASS] (4/4 passed)
[I] Penomoran ST                         : PASS (6 ST berurutan)
exit=0
== b: layar 2 hanya 1 cabang
DOC VALIDATION: UI.md [PASS] (4/4 passed)
[I] Penomoran ST                         : PASS (7 ST berurutan)
exit=0
== c: 6 ST, cabang kosong hilang
DOC VALIDATION: UI.md [PASS] (4/4 passed)
[I] Penomoran ST                         : PASS (6 ST berurutan)
exit=0
```

Output sesudah patch (`PLUGIN=<salinan-terpatch> bash c2.sh`):

```
== a: 1 layar x 6 cabang
DOC VALIDATION: UI.md [PASS] (4/4 passed)
[I] Penomoran ST                         : PASS (6 ST berurutan)
exit=0
== b: layar 2 hanya 1 cabang
DOC VALIDATION: UI.md [FAIL] (3/4 passed)
[I] Penomoran ST                         : FAIL (1 pelanggaran)
      - layar 2 (ST-7..ST-7): cabang hilang — loading, kosong, error, initial, stale/mutating
exit=1
== c: 6 ST, cabang kosong hilang
DOC VALIDATION: UI.md [FAIL] (3/4 passed)
[I] Penomoran ST                         : FAIL (2 pelanggaran)
      - layar 1 (ST-1..ST-6): cabang `loading` ganda (ST-2, ST-3)
      - layar 1 (ST-1..ST-6): cabang hilang — kosong
exit=1
```

### Dampak

Layar kedua dan seterusnya bisa lolos Gate Design tanpa cabang loading/kosong/error. `contract` hanya menagih AC untuk `ST` yang ada, jadi cabang yang hilang tidak pernah punya kriteria penerimaan dan tidak dikerjakan brief. Guardrail SKILL sendiri menyebut akibatnya: "cabang yang tidak dirancang lolos ke produksi tanpa penanganan".

### Rencana perbaikan

Keputusan desain: **blok enam `ST` berurutan = satu layar** (`ST-1..6` layar 1, `ST-7..12` layar 2, dst.). Aturan ini sudah tersirat di template ("Layar kedua ... melanjutkan nomornya (`ST-7`, ...)") dan tidak butuh heading baru. Jenis cabang dibaca dari kata kunci judul; kata kunci yang muncul paling awal menang. Urutan cabang di dalam blok bebas.

1. **`src/plugins/frontenddev/skills/_common/validate_doc.py`** (diuji):

```diff
--- a/src/plugins/frontenddev/skills/_common/validate_doc.py
+++ b/src/plugins/frontenddev/skills/_common/validate_doc.py
@@ -28,7 +28,7 @@
 import re
 import sys
 from pathlib import Path
-from typing import Any, Dict, List, Optional, Set
+from typing import Any, Dict, List, Optional, Set, Tuple
 
 sys.path.insert(0, str(Path(__file__).resolve().parent))
 from precondition_lib import (  # noqa: E402
@@ -94,9 +94,47 @@
 
 DD_ROW = re.compile(r"^\|\s*`?(DD-\d+)`?\s*\|")
 ST_HEAD = re.compile(r"^###\s+(ST-\d+)\.\s")
+ST_TITLE = re.compile(r"^###\s+(ST-\d+)\.\s+(.*)$")
 AC_ROW = re.compile(r"^\|\s*`?(AC-\d+)`?\s*\|(.*)\|\s*$")
 TOKEN = re.compile(r"\b(SC|DD|ST)-\d+\b")
 FILES_ROW = re.compile(r"^\s*[-*]\s+`(CREATE|MODIFY)`\s+`[^`<>]+`")
+# Enam cabang wajib per layar (ui-design Phase 4). Jenis sebuah ST = kata kunci
+# yang muncul PALING AWAL di judulnya ("State Error saat Loading" = error).
+STATE_KINDS = (
+    ("normal", re.compile(r"\b(normal|ready)\b", re.IGNORECASE)),
+    ("loading", re.compile(r"\b(loading|skeleton)\b", re.IGNORECASE)),
+    ("kosong", re.compile(r"\b(kosong|empty)\b", re.IGNORECASE)),
+    ("error", re.compile(r"\b(error|failure|gagal)\b", re.IGNORECASE)),
+    ("initial", re.compile(r"\b(initial|idle)\b", re.IGNORECASE)),
+    ("stale/mutating", re.compile(r"\b(stale|mutating|optimistic)\b", re.IGNORECASE)),
+)
+KIND_NAMES = [k for k, _ in STATE_KINDS]
+
+
+def state_kind(title: str) -> str:
+    hits = [(m.start(), kind) for kind, rx in STATE_KINDS for m in [rx.search(title)] if m]
+    return min(hits)[1] if hits else ""
+
+
+def per_screen_problems(heads: List[Tuple[str, str]]) -> List[str]:
+    """Blok enam ST berurutan = satu layar (ST-1..6, ST-7..12, ...); tiap blok
+    wajib memuat keenam jenis cabang tepat sekali. Urutan di dalam blok bebas."""
+    problems: List[str] = []
+    for start in range(0, len(heads), 6):
+        block = heads[start:start + 6]
+        label = f"layar {start // 6 + 1} ({block[0][0]}..{block[-1][0]})"
+        seen: Dict[str, List[str]] = {}
+        for sid, title in block:
+            kind = state_kind(title)
+            if not kind:
+                problems.append(f"{label}: judul `{sid}` tidak menyebut jenis cabang ({', '.join(KIND_NAMES)})")
+                continue
+            seen.setdefault(kind, []).append(sid)
+        problems += [f"{label}: cabang `{k}` ganda ({', '.join(v)})" for k, v in seen.items() if len(v) > 1]
+        missing = [k for k in KIND_NAMES if k not in seen]
+        if missing:
+            problems.append(f"{label}: cabang hilang — {', '.join(missing)}")
+    return problems
 
 
 def outside_fences(lines: List[str]) -> List[str]:
@@ -170,6 +208,10 @@
         lines = section_lines(body if body is not None else self.body, heading)
         return [m.group(1) for m in (ST_HEAD.match(l.strip()) for l in lines) if m]
 
+    def st_heads(self) -> List[Tuple[str, str]]:
+        lines = section_lines(self.body, SPECS["ui"]["headings"][2])
+        return [(m.group(1), m.group(2)) for m in (ST_TITLE.match(l.strip()) for l in lines) if m]
+
     # ------------------------------------------------------------------ checks
 
     def _check_frontmatter(self) -> None:
@@ -255,11 +297,12 @@
             seq = sequential(ids, prefix)
             if seq:
                 problems.append(seq)
-        if prefix == "ST" and 0 < len(ids) < 6:
-            problems.append(f"hanya {len(ids)} cabang ST — enam cabang state wajib dirancang "
-                            "(normal, loading, kosong, error, initial, stale/mutating)")
+        if prefix == "ST" and ids:
+            problems += per_screen_problems(self.st_heads())
         self._add("I", f"Penomoran {prefix}", problems, f"{len(ids)} {prefix} berurutan",
-                  f"Nomori `{prefix}-{{n}}` berurutan dari `{prefix}-1` tanpa lompatan.")
+                  f"Nomori `{prefix}-{{n}}` berurutan dari `{prefix}-1` tanpa lompatan"
+                  + ("; tiap layar tepat enam ST (ST-1..6, ST-7..12, ...), satu per cabang "
+                     "normal, loading, kosong, error, initial, stale/mutating." if prefix == "ST" else "."))
 
     def _check_contract(self) -> None:
         # Files Touched
```

   `st_ids()` (dipakai `--kind contract` untuk keterlacakan AC) tidak berubah.

2. **`src/plugins/frontenddev/skills/ui-design/templates/ui-template.md:75`**: ganti butir 3 dengan:

   > 3. **Cabang state**: heading `### ST-{n}. State <jenis> ...` berurutan dari `ST-1`. **Tiap layar tepat enam ST berurutan** (layar 1 = `ST-1..ST-6`, layar 2 = `ST-7..ST-12`, dst.), satu per jenis cabang: normal, loading, kosong, error, initial, stale/mutating. Urutan di dalam blok bebas. Jenis dibaca dari kata kunci judul (`Normal`/`Ready`, `Loading`/`Skeleton`, `Kosong`/`Empty`, `Error`/`Failure`/`Gagal`, `Initial`/`Idle`, `Stale`/`Mutating`/`Optimistic`). Cabang yang tidak relevan untuk suatu layar tetap ditulis beserta alasannya. Bila lebih dari satu layar, sebut layarnya di judul (`### ST-7. State Normal — Layar 2: Pembayaran`). `validate_doc.py --kind contract` menagih tiap `ST-{n}` dipikul minimal satu AC.

3. **`src/plugins/frontenddev/skills/ui-design/SKILL.md:50`**: ganti kalimat terakhir "Nomori `ST-{n}` berurutan lintas layar." dengan:

   > Nomori `ST-{n}` berurutan lintas layar, **enam per layar** (`ST-1..6` layar 1, `ST-7..12` layar 2); cabang yang tidak relevan tetap ditulis beserta alasannya.

4. **`src/plugins/frontenddev/skills/ui-design/SKILL.md:69`**: ganti guardrail dengan:

   > - **SIX STATES MANDATORY**: validator menolak layar (blok enam `ST-{n}`) yang tidak memuat keenam cabang tepat sekali; cabang yang tidak dirancang lolos ke produksi tanpa penanganan.

Fixture contoh **lolos**. Dua layar; judul boleh memuat nama layar:

````markdown
## 3. Cabang State Tampilan (The 6-State Branches Matrix)

### ST-1. State Normal (Data Terisi / Ready)
- Daftar item dengan subtotal; CTA aktif.

### ST-2. State Loading (Skeleton Shimmer)
- Tiga baris skeleton setinggi baris item.

### ST-3. State Kosong (Empty State)
- "Keranjangmu kosong" + CTA *Belanja Sekarang*.

### ST-4. State Error (Connection / Server Failure)
- Banner + *Coba Lagi* memanggil `refetch` dari `useCheckoutPage`.

### ST-5. State Initial / Idle
- Sama dengan ST-2 sampai query pertama berangkat.

### ST-6. State Stale / Mutating (Optimistic Overlay)
- Ubah kuantitas seketika; rollback bila gagal.

### ST-7. State Normal — Layar 2: Pembayaran
- Form kartu terisi; CTA *Bayar* aktif.

### ST-8. State Loading — Layar 2: Pembayaran
- Skeleton form setinggi field.

### ST-9. State Kosong — Layar 2: Pembayaran
- Tidak berlaku sebagai daftar: tanpa metode tersimpan → form kosong + teks bantuan.

### ST-10. State Error — Layar 2: Pembayaran
- Pesan penolakan kartu + *Coba Lagi* memanggil `submitPayment`.

### ST-11. State Initial — Layar 2: Pembayaran
- Form kosong, CTA disabled sampai valid.

### ST-12. State Mutating — Layar 2: Pembayaran
- CTA spinner, double-submit dicegah.
````

Fixture **gagal**. Layar 2 hanya satu cabang (sesudah ST-6 yang sama seperti di atas):

````markdown
### ST-7. State Normal — Layar 2: Pembayaran
- Form kartu.
````

→ `layar 2 (ST-7..ST-7): cabang hilang — loading, kosong, error, initial, stale/mutating`.

### Test yang ditambahkan / Verifikasi manual

`src/plugins/frontenddev/tests/test_validate_doc_ui.py`:

```python
"""C2 — validate_doc.py --kind ui menagih enam cabang PER LAYAR."""
import pytest

from conftest import TASKDIR, run_script

SIX = ["Normal (Data Terisi / Ready)", "Loading (Skeleton Shimmer)", "Kosong (Empty State)",
       "Error (Connection / Server Failure)", "Initial / Idle", "Stale / Mutating (Optimistic Overlay)"]

HEAD = """---
status: DRAFT
slug: label
order: 20
stack: react-vite
based_on: 3f9c2ab (2026-09-23)
---

# UI Design — Label

Rancangan.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+---+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| CTA | Primary (P1) | `button.primary` | Aksi utama |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

"""
TAIL = """
## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris | `name` | View-Model | apa adanya |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: `useLabelPage`.
"""


def ui(titles):
    body = "".join(f"### ST-{i}. State {t}\n- Perilaku.\n\n" for i, t in enumerate(titles, 1))
    return HEAD + body + TAIL


def validate(repo, titles):
    repo.write(f"{TASKDIR}/UI.md", ui(titles))
    return run_script("_common/validate_doc.py", "--kind", "ui", "--taskdir", TASKDIR, "--root", repo.root)


@pytest.mark.parametrize("titles", [SIX, SIX + SIX, SIX[::-1], SIX + SIX[3:] + SIX[:3]])
def test_lolos_bila_tiap_layar_enam_cabang(repo, titles):
    proc = validate(repo, titles)
    assert proc.returncode == 0, proc.stdout


def test_layar_kedua_hanya_satu_cabang_gagal(repo):
    proc = validate(repo, SIX + ["Normal — Layar 2: Pembayaran"])
    assert proc.returncode == 1
    assert "layar 2 (ST-7..ST-7): cabang hilang — loading, kosong, error, initial, stale/mutating" in proc.stdout


def test_cabang_ganda_dan_hilang_dalam_satu_layar_gagal(repo):
    titles = list(SIX)
    titles[2] = "Loading Ulang (Skeleton)"
    proc = validate(repo, titles)
    assert proc.returncode == 1
    assert "cabang `loading` ganda (ST-2, ST-3)" in proc.stdout
    assert "cabang hilang — kosong" in proc.stdout


def test_kurang_dari_enam_tetap_gagal(repo):
    proc = validate(repo, SIX[:4])
    assert proc.returncode == 1
    assert "cabang hilang — initial, stale/mutating" in proc.stdout


def test_judul_tanpa_jenis_cabang_dilaporkan(repo):
    titles = list(SIX)
    titles[4] = "Awalan Layar"
    proc = validate(repo, titles)
    assert proc.returncode == 1
    assert "judul `ST-5` tidak menyebut jenis cabang" in proc.stdout
```

Verifikasi manual: contoh terisi `ui-template.md` bagian 3 (judul identik dengan `SIX`) tetap PASS.

### Selesai bila

Skenario (b) dan (c) FAIL dengan pesan yang menyebut layar dan cabangnya, skenario (a) dan fixture dua layar di atas PASS, dan teks `ui-template.md:75` serta `SKILL.md:50,69` menyatakan aturan per layar.

### Risiko & catatan

- Judul dengan istilah di luar daftar kata kunci (mis. "State Refreshing") akan FAIL dengan pesan yang menyebut judulnya. Tambah kata kunci bila pola itu sah.
- UI.md lama yang lolos dengan susunan bebas (mis. layar 2 hanya tiga cabang) akan FAIL saat di-`reopen`. Itu memang tujuannya, tetapi sebut di catatan rilis.

---

## C3 [Rendah] `chain.py approve` mengubah CRLF menjadi LF.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1,5 jam · **Bergantung pada:** — · **Memblokir:** L4.5 (sebaiknya dikerjakan sesudah C3)

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/_common/chain.py:145-157` dan `:237-240` (pola yang sama di `:338-342` untuk `reopen`):

```python
            for rel, text in (originals or {}).items():
                (self.root / rel).write_text(text, encoding="utf-8")
            ...
    def snapshot(self, *rels: str) -> Dict[str, str]:
        return {r: (self.root / r).read_text(encoding="utf-8") for r in rels if (self.root / r).is_file()}

    def write_task(self, text: str) -> None:
        self.task.write_text(text, encoding="utf-8")
    ...
        path.write_text(set_frontmatter_field(path.read_text(encoding="utf-8"), "status", "APPROVED"),
                        encoding="utf-8")
```

`read_text` menormalkan `\r\n` menjadi `\n` (universal newlines), lalu `write_text` menulis `\n` (di Linux). Seluruh baris berkas CRLF pun berubah.

### Masalah

Commit approval/reopen/escalate/abandon atas berkas CRLF menjadi diff satu berkas penuh (TASK.md dan dokumen hop). Pemulihan sesudah commit gagal juga tidak byte-exact. Drift check tetap aman, karena `show_at` (`universal_newlines=True`) dan `read_text` sama-sama menormalkan.

### Reproduksi

```bash
#!/usr/bin/env bash
# C3 — chain.py approve mengubah CRLF menjadi LF
set -eu
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
export PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d); cd "$tmp"; git init -q -b main
git config user.email t@t; git config user.name t
TD=frontenddev/docs/2609240900-order-checkout; mkdir -p "$TD"
cat > "$TD/TASK.md" <<'T'
---
status: ACTIVE
lane: FULL_PIPELINE
sections: [ui]
created: 2026-09-24
---

# Checkout — ringkasan keranjang

## Description

Contoh.

## Success Criteria

- [ ] **SC-1**: layar keranjang tampil — verifikasi: test `Cart.test.tsx` hijau

## Out of Scope

- Pembayaran — di luar lingkup
T
python3 "$PLUGIN/skills/_common/chain.py" init --taskdir "$TD" >/dev/null
git add -A; git commit -qm "docs(order-checkout): kunci akar TASK"
{ cat <<'U'
---
status: DRAFT
slug: order-checkout
order: 20
stack: react-vite
based_on: 3f9c2ab (2026-09-23)
---

# UI Design — Keranjang

Rancangan satu layar.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+-----------+
| Keranjang |
+-----------+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| CTA | Primary (P1) | `button.primary` | Aksi utama |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

U
  for t in "Normal (Ready)" "Loading (Skeleton)" "Kosong (Empty)" "Error (Failure)" "Initial / Idle" "Stale / Mutating"; do
    n=$((${n:-0}+1)); printf '### ST-%d. State %s\n- Perilaku.\n\n' $n "$t"; done
  cat <<'U'
## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris | `name` | View-Model | apa adanya |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: `useCartPage`.
U
} | sed 's/$/\r/' > "$TD/UI.md"
git add -A; git commit -qm "docs(order-checkout): draft UI.md"
echo "sebelum : $(file -b "$TD/UI.md")"
python3 "$PLUGIN/skills/_common/chain.py" approve --taskdir "$TD" --row UI --answer "Setujui desain"
echo "sesudah : $(file -b "$TD/UI.md")"
git show --stat --format='%s' HEAD | sed '/^$/d'
python3 "$PLUGIN/skills/_common/chain.py" verify --taskdir "$TD" --rows UI
```

Output aktual (kode `34684ee`):

```
sebelum : Unicode text, UTF-8 text, with CRLF line terminators
CHAIN APPROVE: UI @ APPROVED 688de33 — commit ebb717d
sesudah : Unicode text, UTF-8 text
docs(order-checkout): approve UI.md
 frontenddev/docs/2609240900-order-checkout/TASK.md |   2 +-
 frontenddev/docs/2609240900-order-checkout/UI.md   | 108 ++++++++++-----------
 2 files changed, 55 insertions(+), 55 deletions(-)
CHAIN VERIFY: [PASS] UI
```

Output sesudah patch:

```
sebelum : Unicode text, UTF-8 text, with CRLF line terminators
CHAIN APPROVE: UI @ APPROVED 125285a — commit 3139f3b
sesudah : Unicode text, UTF-8 text, with CRLF line terminators
docs(order-checkout): approve UI.md
 frontenddev/docs/2609240900-order-checkout/TASK.md | 2 +-
 frontenddev/docs/2609240900-order-checkout/UI.md   | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)
CHAIN VERIFY: [PASS] UI
```

(TASK.md di skrip ini ber-LF, jadi baris `TASK.md | 2 +-` di output "sebelum" hanya berisi perubahan ledger.)

### Perbaikan

Tambah dua helper di `precondition_lib.py` dan pakai di semua titik tulis `chain.py`. Snapshot pemulihan disimpan sebagai `bytes`.

```diff
--- a/src/plugins/frontenddev/skills/_common/precondition_lib.py
+++ b/src/plugins/frontenddev/skills/_common/precondition_lib.py
@@ -318,6 +318,21 @@
     return value.strip() if isinstance(value, str) else ""
 
 
+def newline_of(path: Path) -> str:
+    """Gaya line ending mayoritas berkas: `\r\n` atau `\n` (default untuk berkas baru)."""
+    try:
+        data = path.read_bytes()
+    except OSError:
+        return "\n"
+    crlf = data.count(b"\r\n")
+    return "\r\n" if crlf > data.count(b"\n") - crlf else "\n"
+
+
+def write_keep_newline(path: Path, text: str) -> None:
+    """Tulis `text` (ber-`\n`, hasil `read_text`) dengan gaya line ending berkas yang ditimpa."""
+    path.write_text(text, encoding="utf-8", newline=newline_of(path))
+
+
 def set_frontmatter_field(text: str, key: str, value: str) -> str:
     """Ganti (atau sisipkan di akhir frontmatter) satu field skalar."""
     if not text.startswith("---"):
--- a/src/plugins/frontenddev/skills/_common/chain.py
+++ b/src/plugins/frontenddev/skills/_common/chain.py
@@ -73,6 +73,7 @@
     task_lane_sections,
     taskdir_slug,
     verify_chain_row,
+    write_keep_newline,
 )
 
 PLUGIN_SKILLS = Path(__file__).resolve().parents[1]
@@ -136,7 +137,7 @@
                                  "commit draft/revisinya lebih dulu.")
 
     def commit(self, paths: List[str], subject: str, body: str = "",
-               originals: Optional[Dict[str, str]] = None) -> str:
+               originals: Optional[Dict[str, bytes]] = None) -> str:
         """Commit **hanya** `paths` — index user yang lain tidak ikut; gagal → isi dipulihkan."""
         ok, out = git_ok(self.root, "add", "--", *paths)
         if ok:
@@ -144,17 +145,18 @@
             ok, out = git_ok(self.root, *args)
         if not ok:
             git_ok(self.root, "reset", "-q", "--", *paths)
-            for rel, text in (originals or {}).items():
-                (self.root / rel).write_text(text, encoding="utf-8")
+            for rel, data in (originals or {}).items():
+                (self.root / rel).write_bytes(data)
             raise ChainError(f"`git commit` gagal (hook/lock?) — berkas dipulihkan ke keadaan "
                              f"semula: {out.strip()[-400:]}")
         return git(self.root, "rev-parse", "--short", "HEAD").strip()
 
-    def snapshot(self, *rels: str) -> Dict[str, str]:
-        return {r: (self.root / r).read_text(encoding="utf-8") for r in rels if (self.root / r).is_file()}
+    def snapshot(self, *rels: str) -> Dict[str, bytes]:
+        """Isi byte persis — pemulihan sesudah commit gagal tidak boleh mengubah line ending."""
+        return {r: (self.root / r).read_bytes() for r in rels if (self.root / r).is_file()}
 
     def write_task(self, text: str) -> None:
-        self.task.write_text(text, encoding="utf-8")
+        write_keep_newline(self.task, text)
 
     def briefs(self) -> List[Path]:
         return sorted(self.taskdir.glob(BRIEF_GLOB))
@@ -236,8 +238,7 @@
             self._require_review_pass("contract", [rel])
         sha = last_commit(self.root, rel)
         originals = self.snapshot(rel, self.task_rel)
-        path.write_text(set_frontmatter_field(path.read_text(encoding="utf-8"), "status", "APPROVED"),
-                        encoding="utf-8")
+        write_keep_newline(path, set_frontmatter_field(path.read_text(encoding="utf-8"), "status", "APPROVED"))
         tail = f"APPROVED {sha}" + (f" (re-entry {entry['n']}, was {entry['sha']})" if entry["mark"] == "~" else "")
         self.write_task(replace_chain_row(self.text(), row, chain_line(row, "x", tail)))
         new = self.commit([rel, self.task_rel], f"docs({self.slug}): approve {doc}",
@@ -338,8 +339,7 @@
             if r in DOC_ROWS:
                 rel = f"{self.taskdir_rel}/{CHAIN_BY_ROW[r][2]}"
                 p = self.root / rel
-                p.write_text(set_frontmatter_field(p.read_text(encoding="utf-8"), "status", "DRAFT"),
-                             encoding="utf-8")
+                write_keep_newline(p, set_frontmatter_field(p.read_text(encoding="utf-8"), "status", "DRAFT"))
                 paths.append(rel)
         self.write_task(text)
         rows = " ".join(e["row"] for e in cascade)
```

`newline=` pada `Path.write_text` butuh Python ≥ 3.10; target CI L6.2 adalah 3.11–3.13.

### Test

`src/plugins/frontenddev/tests/test_chain_newline.py`:

```python
"""C3 — chain.py mempertahankan gaya line ending dokumen dan TASK.md."""
import pytest

from conftest import TASKDIR, run_script, task_md

UI = """---
status: DRAFT
slug: label
order: 20
stack: react-vite
based_on: 3f9c2ab (2026-09-23)
---

# UI Design — Label

Rancangan.

## 1. Mockup Antarmuka (Layout Mockup ASCII)

```
+---+
```

## 2. Hierarki Prioritas Informasi (Information Priority)

| Elemen Antarmuka Pengguna | Tingkat Prioritas | Bobot Visual & Penempatan | Alasan Desain |
|---|---|---|---|
| CTA | Primary (P1) | `button.primary` | Aksi utama |

## 3. Cabang State Tampilan (The 6-State Branches Matrix)

""" + "".join(f"### ST-{i}. State {t}\n- Perilaku.\n\n" for i, t in enumerate(
    ["Normal (Ready)", "Loading (Skeleton)", "Kosong (Empty)", "Error (Failure)", "Initial / Idle",
     "Stale / Mutating"], 1)) + """## 4. Pemetaan Kebutuhan Data (Data Demands Mapping)

| Elemen UI | Field Data yang Ditampilkan | Asal Sumber Data | Keterangan & Transformasi |
|---|---|---|---|
| Baris | `name` | View-Model | apa adanya |

## 5. Batasan State Scope & Isolasi Komponen
- **Koordinasi Sentral**: `useLabelPage`.
"""


def setup_ui(repo, crlf):
    chain = ["- [ ] UI       — frontenddev:ui-design     → UI.md",
             "- [ ] CONTRACT — frontenddev:contract      → CONTRACT.md",
             "- [ ] BRIEF    — frontenddev:plan          → brief-*.md"]
    repo.write(f"{TASKDIR}/TASK.md", task_md("FULL_PIPELINE", "[ui]", chain=chain), crlf=crlf)
    repo.commit("docs(label): kunci TASK sebagai akar rantai")
    repo.write(f"{TASKDIR}/UI.md", UI, crlf=crlf)
    repo.commit("docs(label): draft UI.md")


@pytest.mark.parametrize("crlf", [True, False])
def test_approve_hanya_mengubah_satu_baris(repo, crlf):
    setup_ui(repo, crlf)
    proc = run_script("_common/chain.py", "approve", "--taskdir", TASKDIR, "--row", "UI",
                      "--answer", "Setujui desain", "--root", repo.root)
    assert proc.returncode == 0, proc.stdout
    stat = repo.git("show", "--numstat", "--format=", "HEAD").split()
    assert stat == ["1", "1", f"{TASKDIR}/TASK.md", "1", "1", f"{TASKDIR}/UI.md"]
    for doc in ("UI.md", "TASK.md"):
        data = (repo.root / TASKDIR / doc).read_bytes()
        assert (b"\r\n" in data) is crlf
    verify = run_script("_common/chain.py", "verify", "--taskdir", TASKDIR, "--rows", "UI", "--root", repo.root)
    assert verify.returncode == 0, verify.stdout


def test_commit_gagal_memulihkan_byte_persis(repo):
    setup_ui(repo, crlf=True)
    before = {d: (repo.root / TASKDIR / d).read_bytes() for d in ("UI.md", "TASK.md")}
    hook = repo.root / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    proc = run_script("_common/chain.py", "approve", "--taskdir", TASKDIR, "--row", "UI",
                      "--answer", "Setujui desain", "--root", repo.root)
    assert proc.returncode == 1 and "gagal" in proc.stdout
    assert {d: (repo.root / TASKDIR / d).read_bytes() for d in before} == before
```

### Selesai bila

Approve atas UI.md dan TASK.md ber-CRLF menghasilkan diff 1 baris per berkas, berkas tetap CRLF, `chain.py verify` tetap PASS, dan pemulihan sesudah hook menolak commit mengembalikan byte asli.

---

## C4 [Rendah] `taskdir_state.py` kode mati dan vonis menyesatkan.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 2 jam · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/lead/scripts/taskdir_state.py`:

- `:14-20`: docstring menaruh `EKSEKUSI` (5) sebelum `TERHENTI` (6). Kode `:127-136` memeriksa `TERHENTI` lebih dulu. Deskripsi `TEMUAN` (`:18`) menulis "kerja baru lewat lead (`finding_source`)", padahal kode `:143` merutekan ke reopen BRIEF di taskdir yang sama. `LAPORAN` (`:20`) menulis `frontenddev:report`, padahal kode `:147` menulis `frontenddev:architect (Phase 5)`. `DITUTUP` (`:83-85`) tidak tercantum.
- `:56-66`, `:69`, `:167-170`: kode mati.

```python
def followups(root: Path) -> Dict[str, str]:
    """`{path finding_source: taskdir penerus}` dari frontmatter seluruh `TASK.md`."""
    ...
def classify(root: Path, rel: str, successors: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    ...                                   # `successors` tidak pernah dipakai di badan fungsi
    successors = followups(root)
    rows = [classify(root, r, successors) for r in rels]
    if not args.all and not args.taskdir:
        rows = [r for r in rows if r["state"] not in ("TUNTAS", "DILANJUTKAN", "DITUTUP")]  # DILANJUTKAN tak pernah dihasilkan
```

- `:75-82`: taskdir yang tidak ada = "taskdir kosong".
- `:165-166`: mode pindai menyaring nama dengan `TASKDIR_NAME = ^\d{10}-[a-z0-9-]+$`; direktori di luar pola diabaikan diam-diam.
- `:92-94`: `is_committed` gagal di repo non-git, lalu divonis "TASK.md belum ter-commit".

### Reproduksi

```bash
#!/usr/bin/env bash
# C4 — taskdir_state.py: kode mati & vonis menyesatkan
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
S="$PLUGIN/skills/lead/scripts/taskdir_state.py"
export PYTHONDONTWRITEBYTECODE=1
task() { cat <<'T'
---
status: ACTIVE
lane: HOTFIX_MINOR
sections: []
created: 2026-09-24
---

# Perbaikan label

## Description

Contoh.

## Success Criteria

- [ ] **SC-1**: label benar — verifikasi: test `Label.test.tsx` hijau

## Out of Scope

- Lainnya — di luar lingkup

## Chain

- [ ] BRIEF    — frontenddev:plan          → brief-*.md
T
}
brief() { printf -- '---\nstatus: %s\nfiles_touched: [src/a.ts]\n---\n\n# Brief %s\n' "$1" "$2"; }

tmp=$(mktemp -d); cd "$tmp"; git init -q -b main; git config user.email t@t; git config user.name t
echo "== (1) --taskdir yang tidak ada"
python3 "$S" --root "$tmp" --taskdir frontenddev/docs/2609240900-tidak-ada

echo "== (2) taskdir berhuruf besar berisi TASK.md ter-commit, mode pindai"
TD=frontenddev/docs/2609240900-Order-Checkout; mkdir -p "$TD"; task > "$TD/TASK.md"
git add -A; git commit -qm "docs(Order-Checkout): kunci akar TASK"
python3 "$S" --root "$tmp"
echo "   ...dan bila disebut eksplisit:"
python3 "$S" --root "$tmp" --taskdir "$TD"

echo "== (3) repo non-git"
ng=$(mktemp -d); mkdir -p "$ng/frontenddev/docs/2609240900-label"; task > "$ng/frontenddev/docs/2609240900-label/TASK.md"
python3 "$S" --root "$ng"

echo "== (4) urutan vonis: brief READY + brief BLOCKED tanpa remedi"
TD=frontenddev/docs/2609240901-label; mkdir -p "$TD"; task > "$TD/TASK.md"
brief READY 01 > "$TD/brief-01-a.md"; brief READY 02 > "$TD/brief-02-b.md"
git add -A; git commit -qm "docs(label): draft breakdown"; sha=$(git rev-parse --short HEAD)
sed -i "s/^- \[ \] BRIEF .*/- [x] BRIEF    — frontenddev:plan          → brief-*.md @ READY $sha/" "$TD/TASK.md"
git add -A; git commit -qm "docs(label): approve breakdown (2 briefs)" -m "Konten disetujui: $sha" -m "Hop: BRIEF"
sed -i 's/^status: READY/status: BLOCKED/' "$TD/brief-02-b.md"; git add -A; git commit -qm "docs(label): brief 02 BLOCKED"
python3 "$S" --root "$tmp" --taskdir "$TD"

echo "== (5) kode mati"
grep -n "successors\|DILANJUTKAN\|def followups" "$S"
```

Output aktual (kode `34684ee`):

```
== (1) --taskdir yang tidak ada
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240900-tidak-ada [-] AKAR → frontenddev:task (lead Phase 7), atau hapus direktori kosong bila user batal (taskdir kosong)
== (2) taskdir berhuruf besar berisi TASK.md ter-commit, mode pindai
TASKDIR STATE: nol taskdir terbuka — aman membuat taskdir baru
   ...dan bila disebut eksplisit:
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240900-Order-Checkout [HOTFIX_MINOR] GATE → frontenddev:plan (mode MINOR) (hop BRIEF `[ ]`, 0 brief)
== (3) repo non-git
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240900-label [HOTFIX_MINOR] AKAR → frontenddev:task (commit akar) (TASK.md belum ter-commit)
== (4) urutan vonis: brief READY + brief BLOCKED tanpa remedi
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240901-label [HOTFIX_MINOR] TERHENTI → chain.py reopen --row BRIEF → frontenddev:plan (mode APPEND) (brief-02 BLOCKED tanpa remedi)
== (5) kode mati
56:def followups(root: Path) -> Dict[str, str]:
69:def classify(root: Path, rel: str, successors: Optional[Dict[str, str]] = None) -> Dict[str, str]:
167:    successors = followups(root)
168:    rows = [classify(root, r, successors) for r in rels]
170:        rows = [r for r in rows if r["state"] not in ("TUNTAS", "DILANJUTKAN", "DITUTUP")]
```

Kasus (2) paling berbahaya: lead Phase 2 menyimpulkan "aman membuat taskdir baru" padahal ada taskdir berisi akar ter-commit. Kasus (4) menunjukkan kode menaruh `TERHENTI` sebelum `EKSEKUSI`, berlawanan dengan docstring (dan sejalan dengan `architect/scripts/check_preconditions.py:184-191`, jadi docstring-lah yang salah).

Output sesudah patch:

```
== (1) --taskdir yang tidak ada
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240900-tidak-ada [-] RUSAK → periksa path taskdir; taskdir dibuat lead Phase 5 (direktori tidak ada)
== (2) taskdir berhuruf besar berisi TASK.md ter-commit, mode pindai
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240900-Order-Checkout [-] RUSAK → laporkan ke user (nama `2609240900-Order-Checkout` di luar pola <YYMMDDhhmm>-<slug> (huruf kecil, angka, `-`))
   ...dan bila disebut eksplisit:
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240900-Order-Checkout [-] RUSAK → laporkan ke user (nama `2609240900-Order-Checkout` di luar pola <YYMMDDhhmm>-<slug> (huruf kecil, angka, `-`))
== (3) repo non-git
TASKDIR STATE: [FAIL] `/tmp/tmp.DiaSi7KshD` bukan repo git — akar dan ledger tidak dapat dibuktikan
== (4) urutan vonis: brief READY + brief BLOCKED tanpa remedi
TASKDIR STATE: 1 taskdir terbuka
- frontenddev/docs/2609240901-label [HOTFIX_MINOR] TERHENTI → chain.py reopen --row BRIEF → frontenddev:plan (mode APPEND) (brief-02 BLOCKED tanpa remedi)
== (5) kode mati
```

### Perbaikan

```diff
--- a/src/plugins/frontenddev/skills/lead/scripts/taskdir_state.py
+++ b/src/plugins/frontenddev/skills/lead/scripts/taskdir_state.py
@@ -6,19 +6,27 @@
 dari ingatan sesi, dan bukan dari model yang membaca frontmatter satu per satu.
 Tabel keadaan yang dulu hidup sebagai prosa di Phase 2 kini hidup di sini.
 
-Urutan vonis (yang pertama cocok menang):
+Urutan vonis (yang pertama cocok menang) — sama persis dengan `classify()`:
 
-1. `RUSAK`      — artefak rantai tanpa `TASK.md`, atau pasangan lane/sections tidak sah.
-2. `AKAR`       — taskdir kosong, atau `TASK.md` belum ter-commit → `frontenddev:task`.
-3. `DRIFT`      — hop `[x]` yang kontennya berubah sesudah disetujui → `chain.py reopen`.
-4. `GATE`       — hop ledger pertama yang belum `[x]` → skill pemiliknya (beserta mode `plan`).
-5. `EKSEKUSI`   — brief `READY` dapat berangkat → `frontenddev:architect`.
-6. `TERHENTI`   — brief `BLOCKED` tanpa remedi → `chain.py reopen --row BRIEF` → `plan` APPEND.
-7. `PENUTUP`    — seluruh brief tertutup, `REVIEW.md` absen → `frontenddev:architect` Phase 4.
-8. `TEMUAN`     — `REVIEW.md` ber-verdict `BLOCKED` → kerja baru lewat lead (`finding_source`).
-   Perbaikannya di taskdir yang sama: reopen BRIEF → `plan` APPEND → review ulang.
-9. `LAPORAN`    — `REVIEW.md` `PASS`/`WARNING`, `REPORT.md` absen → `frontenddev:report`.
-10. `TUNTAS`    — `REPORT.md` ada.
+1. `RUSAK`      — direktori tidak ada, nama di luar pola `<YYMMDDhhmm>-<slug>`, atau
+                  artefak rantai tanpa `TASK.md`.
+2. `AKAR`       — taskdir kosong → `frontenddev:task`.
+3. `DITUTUP`    — `TASK.md` `status: ABANDONED` (`chain.py abandon`).
+4. `RUSAK`      — pasangan lane/sections tidak sah atau diubah di luar akar/eskalasi.
+5. `AKAR`       — `TASK.md` belum ter-commit → lead memvalidasi lalu meng-commit akar.
+6. `RUSAK`      — ledger `## Chain` ≠ jadwal sections.
+7. `DRIFT`      — hop `[x]` yang kontennya berubah sesudah disetujui → `chain.py reopen`.
+8. `GATE`       — hop ledger pertama yang belum `[x]` → skill pemiliknya (beserta mode `plan`).
+9. `TERHENTI`   — brief `BLOCKED` tanpa remedi → `chain.py reopen --row BRIEF` → `plan` APPEND.
+10. `EKSEKUSI`  — brief `READY` dapat berangkat → `frontenddev:architect`.
+11. `PENUTUP`   — seluruh brief tertutup, `REVIEW.md` absen atau basi → `architect` Phase 4.
+12. `TEMUAN`    — `REVIEW.md` `BLOCKED` → reopen BRIEF → `plan` APPEND brief perbaikan di
+                  taskdir yang sama → review ulang.
+13. `LAPORAN`   — `REVIEW.md` `PASS`/`WARNING`, `REPORT.md` absen → `architect` Phase 5.
+14. `TUNTAS`    — `REPORT.md` ada.
+
+Repo non-git tidak divonis per taskdir: skrip keluar `FAIL` karena akar dan
+ledger hanya dapat dibuktikan lewat riwayat commit.
 
 Zero external dependencies (Python Standard Library only). Satu impor
 intra-plugin: `skills/_common/precondition_lib.py`.
@@ -29,7 +37,7 @@
 import re
 import sys
 from pathlib import Path
-from typing import Dict, List, Optional
+from typing import Dict
 
 sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
 from precondition_lib import (  # noqa: E402
@@ -39,6 +47,7 @@
     brief_closure,
     expected_rows,
     find_repo_root,
+    is_git_repo,
     review_is_fresh,
     is_committed,
     lane_sections_problem,
@@ -53,23 +62,18 @@
 CHAIN_ARTIFACTS = ("FLOW.md", "UI.md", "CONTRACT.md", "REVIEW-PLAN.md", "REVIEW.md", "REPORT.md")
 
 
-def followups(root: Path) -> Dict[str, str]:
-    """`{path finding_source: taskdir penerus}` dari frontmatter seluruh `TASK.md`."""
-    out: Dict[str, str] = {}
-    base = root / DOCS
-    if not base.is_dir():
-        return out
-    for task in sorted(base.glob("*/TASK.md")):
-        source = read_status(task, "finding_source").strip().strip("./")
-        if source:
-            out[source] = f"{DOCS}/{task.parent.name}"
-    return out
-
-
-def classify(root: Path, rel: str, successors: Optional[Dict[str, str]] = None) -> Dict[str, str]:
+def classify(root: Path, rel: str) -> Dict[str, str]:
     taskdir = root / rel
     task = taskdir / "TASK.md"
     out = {"taskdir": rel, "lane": "-", "state": "", "next": "", "detail": ""}
+    if not taskdir.is_dir():
+        out.update(state="RUSAK", next="periksa path taskdir; taskdir dibuat lead Phase 5",
+                   detail="direktori tidak ada")
+        return out
+    if not TASKDIR_NAME.match(taskdir.name):
+        out.update(state="RUSAK", next="laporkan ke user",
+                   detail=f"nama `{taskdir.name}` di luar pola <YYMMDDhhmm>-<slug> (huruf kecil, angka, `-`)")
+        return out
     artifacts = [a for a in CHAIN_ARTIFACTS if (taskdir / a).is_file()] + \
                 [p.name for p in taskdir.glob("brief-*.md")]
     if not task.is_file():
@@ -158,16 +162,19 @@
     parser.add_argument("--json", action="store_true")
     args = parser.parse_args()
     root = (Path(args.root) if args.root else find_repo_root()).resolve()
+    if not is_git_repo(root):
+        print(f"TASKDIR STATE: [FAIL] `{root}` bukan repo git — akar dan ledger tidak dapat dibuktikan")
+        sys.exit(1)
     if args.taskdir:
         rels = [args.taskdir.strip().strip("/").replace("./", "")]
     else:
         base = root / DOCS
+        # Nama di luar pola tetap dilaporkan (RUSAK) bila berisi berkas, bukan diabaikan diam-diam.
         rels = [f"{DOCS}/{p.name}" for p in sorted(base.iterdir())
-                if p.is_dir() and TASKDIR_NAME.match(p.name)] if base.is_dir() else []
-    successors = followups(root)
-    rows = [classify(root, r, successors) for r in rels]
+                if p.is_dir() and (TASKDIR_NAME.match(p.name) or any(p.glob("*.md")))] if base.is_dir() else []
+    rows = [classify(root, r) for r in rels]
     if not args.all and not args.taskdir:
-        rows = [r for r in rows if r["state"] not in ("TUNTAS", "DILANJUTKAN", "DITUTUP")]
+        rows = [r for r in rows if r["state"] not in ("TUNTAS", "DITUTUP")]
     if args.json:
         print(json.dumps(rows, indent=2))
         return
```

Teks pendamping: `src/plugins/frontenddev/skills/lead/SKILL.md` Phase 2, baris tabel `RUSAK`. Tambahkan di awal isinya: "taskdir yang disebut tidak ada, nama direktori di luar pola `<YYMMDDhhmm>-<slug>`, ...". Tambah juga kalimat sesudah tabel: "Skrip keluar `[FAIL] ... bukan repo git` → hentikan; rantai frontenddev menuntut git."

### Test

`src/plugins/frontenddev/tests/test_taskdir_state.py`:

```python
"""C4 — taskdir_state.py: vonis tidak menyesatkan, tanpa kode mati."""
from conftest import PLUGIN, TASKDIR, run_script, task_md

SCRIPT = "lead/scripts/taskdir_state.py"


def test_taskdir_yang_tidak_ada_bukan_akar(repo):
    proc = run_script(SCRIPT, "--root", repo.root, "--taskdir", "frontenddev/docs/2609240900-tidak-ada")
    assert "RUSAK" in proc.stdout and "direktori tidak ada" in proc.stdout
    assert "AKAR" not in proc.stdout


def test_nama_di_luar_pola_dilaporkan_saat_pindai(repo):
    repo.write("frontenddev/docs/2609240900-Order-Checkout/TASK.md", task_md())
    repo.commit("docs(Order-Checkout): kunci TASK sebagai akar rantai")
    proc = run_script(SCRIPT, "--root", repo.root)
    assert "nol taskdir terbuka" not in proc.stdout
    assert "2609240900-Order-Checkout" in proc.stdout and "RUSAK" in proc.stdout


def test_repo_non_git_gagal_eksplisit(tmp_path):
    (tmp_path / TASKDIR).mkdir(parents=True)
    (tmp_path / TASKDIR / "TASK.md").write_text(task_md())
    proc = run_script(SCRIPT, "--root", tmp_path)
    assert proc.returncode == 1
    assert "bukan repo git" in proc.stdout


def test_blocked_tanpa_remedi_menang_atas_ready(repo):
    brief = "---\nstatus: {}\nfiles_touched: [src/a.ts]\n---\n\n# Brief\n"
    repo.write(f"{TASKDIR}/TASK.md", task_md())
    repo.write(f"{TASKDIR}/brief-01-a.md", brief.format("READY"))
    repo.write(f"{TASKDIR}/brief-02-b.md", brief.format("READY"))
    sha = repo.commit("docs(label): draft breakdown")
    repo.write(f"{TASKDIR}/TASK.md", task_md(chain=[
        f"- [x] BRIEF    — frontenddev:plan          → brief-*.md @ READY {sha}"]))
    repo.commit("docs(label): approve breakdown (2 briefs)", f"Konten disetujui: {sha}", "Hop: BRIEF")
    repo.write(f"{TASKDIR}/brief-02-b.md", brief.format("BLOCKED"))
    repo.commit("docs(label): brief 02 BLOCKED")
    proc = run_script(SCRIPT, "--root", repo.root, "--taskdir", TASKDIR)
    assert "TERHENTI" in proc.stdout


def test_kode_mati_dibuang():
    src = (PLUGIN / "skills" / SCRIPT).read_text(encoding="utf-8")
    assert "def followups" not in src and "DILANJUTKAN" not in src and "successors" not in src
```

### Selesai bila

Kelima skenario reproduksi menghasilkan output "sesudah". Docstring mencantumkan 14 langkah dengan urutan dan rute yang sama dengan `classify()`. `followups`, `successors`, dan `DILANJUTKAN` tidak ada lagi.

### Risiko & catatan

Direktori non-pola yang kosong tetap diabaikan saat pindai (tidak ada yang hilang). Keputusan "non-git = FAIL" konsisten dengan skrip prasyarat lain yang menuntut akar ter-commit.

---

## C5 [Rendah] Batas SC 1–7.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1 jam · **Bergantung pada:** C12 (berkas sama, urutan bebas) · **Memblokir:** —

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/task/scripts/validate_task.py:111-115`:

```python
    def _check_2_numbering(self) -> None:
        nums = [int(m.group(1)) for m in self._sc_lines()]
        ok = 1 <= len(nums) <= 7 and nums == list(range(1, len(nums) + 1))
        self._add(2, "Penomoran SC-{n}", ok, f"SC {nums}" if nums else "nol butir SC",
                  "Nomori 1–7 butir berurutan dari SC-1 tanpa lompatan atau ganda.")
```

Aturan amandemen: `src/plugins/frontenddev/skills/lead/SKILL.md:122`, yaitu "SC baru ditambah di akhir tanpa menomori ulang; SC gugur tetap bernomor, ditulis `- [ ] **SC-n**: ~~<teks lama ...>~~ — gugur: <alasan>` ... Jalankan `validate_task.py --taskdir <taskdir> --amend`". Pustaka bersama sudah membedakan SC aktif: `precondition_lib.py:372-386` `success_criteria()` membuang baris ber-`—\s*gugur:`.

### Masalah

SC gugur ikut dihitung dalam batas 7. Amandemen berulang (menggugurkan dan menambah di akhir) cepat menembus 7 walau SC aktif lebih sedikit, dan lead tidak punya jalan sah selain menomori ulang (dilarang).

### Reproduksi

```bash
#!/usr/bin/env bash
# C5 — validate_task.py membatasi SC 1–7 termasuk SC gugur
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
export PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d); cd "$tmp"; git init -q -b main
TD=frontenddev/docs/2609240900-label; mkdir -p "$TD" src; printf 'a\nb\nc\n' > src/a.ts
gen() { # $1 = jumlah SC aktif, $2 = jumlah SC gugur (gugur ditaruh di depan, aktif ditambah di akhir)
  cat <<'T'
---
status: ACTIVE
lane: HOTFIX_MINOR
sections: []
created: 2026-09-24
---

# Perbaikan label

## Description

Label salah di `src/a.ts:2`.

## Success Criteria

T
  n=0
  for i in $(seq 1 "$2"); do n=$((n+1)); echo "- [ ] **SC-$n**: ~~label lama $n benar — verifikasi: test \`A.test.ts\` hijau~~ — gugur: diganti amandemen"; done
  for i in $(seq 1 "$1"); do n=$((n+1)); echo "- [ ] **SC-$n**: label $n benar — verifikasi: test \`A.test.ts\` hijau"; done
  cat <<'T'

## Out of Scope

- Lainnya — di luar lingkup

## Chain

- [x] BRIEF    — frontenddev:plan          → brief-*.md @ READY abc1234
T
}
for combo in "7 0" "6 2" "5 3"; do
  set -- $combo; gen "$1" "$2" > "$TD/TASK.md"
  echo "== $1 SC aktif + $2 SC gugur (total $(( $1 + $2 )))"
  python3 "$PLUGIN/skills/task/scripts/validate_task.py" --taskdir "$TD" --root "$tmp" --amend | grep -E "^PRECONDITION|^\[2\]|^[A-Z]+ VALIDATION|^\[2\]"
done
```

Output aktual (kode `34684ee`):

```
== 7 SC aktif + 0 SC gugur (total 7)
PRECONDITION CHECK: task self-test [PASS] (7/7 passed)
[2] Penomoran SC-{n}                 : PASS (SC [1, 2, 3, 4, 5, 6, 7])
== 6 SC aktif + 2 SC gugur (total 8)
PRECONDITION CHECK: task self-test [FAIL] (6/7 passed)
[2] Penomoran SC-{n}                 : FAIL (SC [1, 2, 3, 4, 5, 6, 7, 8])
== 5 SC aktif + 3 SC gugur (total 8)
PRECONDITION CHECK: task self-test [FAIL] (6/7 passed)
[2] Penomoran SC-{n}                 : FAIL (SC [1, 2, 3, 4, 5, 6, 7, 8])
```

Output sesudah patch (label baris pertama sudah ikut C12):

```
== 7 SC aktif + 0 SC gugur (total 7)
TASK VALIDATION: TASK.md [PASS] (7/7 passed)
[2] Penomoran SC-{n}                 : PASS (SC [1, 2, 3, 4, 5, 6, 7])
== 6 SC aktif + 2 SC gugur (total 8)
TASK VALIDATION: TASK.md [PASS] (7/7 passed)
[2] Penomoran SC-{n}                 : PASS (SC [1, 2, 3, 4, 5, 6, 7, 8] (6 aktif, gugur: SC-1, SC-2))
== 5 SC aktif + 3 SC gugur (total 8)
TASK VALIDATION: TASK.md [PASS] (7/7 passed)
[2] Penomoran SC-{n}                 : PASS (SC [1, 2, 3, 4, 5, 6, 7, 8] (5 aktif, gugur: SC-1, SC-2, SC-3))
```

### Perbaikan

Batas 1–7 hanya untuk SC **aktif**. Penomoran tetap berurutan untuk semua baris. SC gugur hanya sah pada `--amend`.

```diff
--- a/src/plugins/frontenddev/skills/task/scripts/validate_task.py
+++ b/src/plugins/frontenddev/skills/task/scripts/validate_task.py
@@ -41,6 +41,8 @@
 INLINE_CODE = re.compile(r"`[^`\n]*`")
 PLACEHOLDER = re.compile(r"\bTBD\b|\bTODO\b|diisi nanti|<[^<>\n]+>")
 OOS_LINE = re.compile(r"^- .+ — .+$")
+GUGUR = re.compile(r"—\s*gugur:")  # sama dengan precondition_lib.success_criteria
+MAX_ACTIVE_SC = 7
 
 
 class TaskValidator:
@@ -109,10 +111,22 @@
                   "Ikuti bagian 1 template persis.")
 
     def _check_2_numbering(self) -> None:
-        nums = [int(m.group(1)) for m in self._sc_lines()]
-        ok = 1 <= len(nums) <= 7 and nums == list(range(1, len(nums) + 1))
-        self._add(2, "Penomoran SC-{n}", ok, f"SC {nums}" if nums else "nol butir SC",
-                  "Nomori 1–7 butir berurutan dari SC-1 tanpa lompatan atau ganda.")
+        lines = self._sc_lines()
+        nums = [int(m.group(1)) for m in lines]
+        dropped = [f"SC-{m.group(1)}" for m in lines if GUGUR.search(m.group(2))]
+        active = len(nums) - len(dropped)
+        errors = []
+        if nums != list(range(1, len(nums) + 1)):
+            errors.append(f"SC {nums} tidak berurutan dari SC-1")
+        if not 1 <= active <= MAX_ACTIVE_SC:
+            errors.append(f"{active} SC aktif, sah 1–{MAX_ACTIVE_SC}")
+        if dropped and not self.amend:
+            errors.append(f"SC gugur {dropped} hanya sah pada amandemen akar (`--amend`)")
+        summary = "; ".join(errors) or (f"SC {nums}" + (f" ({active} aktif, gugur: {', '.join(dropped)})"
+                                                         if dropped else ""))
+        self._add(2, "Penomoran SC-{n}", not errors, summary if nums else "nol butir SC",
+                  f"Nomori berurutan dari SC-1 tanpa lompatan atau ganda; 1–{MAX_ACTIVE_SC} SC aktif "
+                  "(SC gugur `~~…~~ — gugur:` tetap bernomor dan tidak dihitung).")
 
     def _check_3_measure(self) -> None:
         bad = []
```

Teks pendamping:

- `src/plugins/frontenddev/skills/task/templates/task-template.md:64`: ganti "berjumlah 1–7 butir." dengan "berjumlah 1–7 butir **aktif**; butir gugur hasil amandemen (`~~…~~ — gugur: <alasan>`) tetap bernomor dan tidak dihitung."
- `src/plugins/frontenddev/skills/lead/SKILL.md:122`: sesudah "SC baru ditambah di akhir tanpa menomori ulang;", sisipkan "SC aktif maksimal 7 (butir gugur tidak dihitung);".

### Test

`src/plugins/frontenddev/tests/test_validate_task_sc.py`:

```python
"""C5 — batas 1–7 hanya menghitung SC aktif; SC gugur tetap bernomor."""
import pytest

from conftest import TASKDIR, run_script, task_md


def sc(active, dropped):
    lines, n = [], 0
    for _ in range(dropped):
        n += 1
        lines.append(f"- [ ] **SC-{n}**: ~~label {n} — verifikasi: test `A.test.ts` hijau~~ — gugur: amandemen")
    for _ in range(active):
        n += 1
        lines.append(f"- [ ] **SC-{n}**: label {n} benar — verifikasi: test `A.test.ts` hijau")
    return lines


def run(repo, active, dropped, amend=True):
    repo.write("src/a.ts", "a\nb\n")
    chain = ["- [x] BRIEF    — frontenddev:plan          → brief-*.md @ READY abc1234"] if amend else None
    repo.write(f"{TASKDIR}/TASK.md", task_md(sc_lines=sc(active, dropped), chain=chain,
                                             desc="Label salah di `src/a.ts:2`."))
    args = ["--taskdir", TASKDIR, "--root", repo.root] + (["--amend"] if amend else [])
    return run_script("task/scripts/validate_task.py", *args)


@pytest.mark.parametrize("active,dropped", [(7, 0), (6, 2), (5, 3), (1, 7)])
def test_amandemen_berulang_lolos(repo, active, dropped):
    proc = run(repo, active, dropped)
    assert proc.returncode == 0, proc.stdout


@pytest.mark.parametrize("active,dropped", [(8, 0), (0, 3)])
def test_sc_aktif_di_luar_1_sampai_7_gagal(repo, active, dropped):
    proc = run(repo, active, dropped)
    assert proc.returncode == 1
    assert f"{active} SC aktif, sah 1–7" in proc.stdout


def test_sc_gugur_di_akar_baru_ditolak(repo):
    proc = run(repo, 3, 1, amend=False)
    assert proc.returncode == 1
    assert "hanya sah pada amandemen akar" in proc.stdout
```

### Selesai bila

Kombinasi 6+2, 5+3, dan 1+7 lolos dengan `--amend`; 8 aktif dan 0 aktif gagal; SC gugur tanpa `--amend` ditolak.

---

## C6 [Rendah] Filter commit architect.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1,5 jam · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/architect/scripts/check_preconditions.py:218-229` (Check 9) dan `:307-312` (Check 13):

```python
        branch = git(self.root, "symbolic-ref", "--short", "-q", "HEAD").strip()
        if not branch:
            self._add(9, name, "FAIL", "detached HEAD", ...)
            return
        rebase = any((self.root / ".git" / d).exists() for d in ("rebase-apply", "rebase-merge"))
        ...
        for f in as_list(fm.get("files_touched")):
            newer = git(self.root, "log", "--oneline", f"{m.group(1)}..HEAD", "--", f).strip()
            own = [l for l in newer.splitlines() if "implement unit" not in l]
```

Subjek commit unit resmi: `feat(<slug>): implement unit <NN> - <nama unit>` (`skills/architect/references/execution-protocol.md:71`).

### Masalah

1. `:310` membuang commit ber-"implement unit" dari taskdir **mana pun**. Commit `feat(taskdir-lain): implement unit 03` yang menyentuh `files_touched` brief ini tidak memicu WARN kesegaran (Check 13 PASS).
2. `:225` memeriksa `<root>/.git/rebase-*`. Di git worktree (dan submodule) `.git` berupa berkas, jadi jalur itu tidak pernah ada.

**Koreksi terhadap ISSUES.md:** rebase yang berhenti di worktree tetap tertahan, karena HEAD detached dan Check 9 FAIL dengan pesan "detached HEAD" (diverifikasi: `git symbolic-ref -q HEAD` exit 1 saat rebase berhenti di worktree). Yang benar-benar lolos adalah **`git am` yang berhenti** (`rebase-apply`). Di situ HEAD tetap di branch dan tree bersih, jadi Check 8 dan Check 9 sama-sama PASS di worktree, sementara di repo utama Check 9 FAIL.

### Reproduksi

```bash
#!/usr/bin/env bash
# C6 — architect check_preconditions: filter "implement unit" lintas taskdir & deteksi rebase di worktree
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
S="$PLUGIN/skills/architect/scripts/check_preconditions.py"
export PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d); cd "$tmp"; git init -q -b main; git config user.email t@t; git config user.name t
TD=frontenddev/docs/2609240900-label; mkdir -p "$TD" src
printf 'a\n' > src/a.ts; printf 'b1\nb2\nb3\n' > src/b.ts; git add -A; git commit -qm "chore: awal"
sha0=$(git rev-parse --short HEAD)
printf -- '---\nstatus: READY\nbased_on: %s (2026-09-24)\nfiles_touched: [src/a.ts]\n---\n\n# Brief 01\n' "$sha0" > "$TD/brief-01-a.md"
git add -A; git commit -qm "docs(label): draft breakdown"

echo "== (A) commit taskdir LAIN menyentuh src/a.ts, subjek memuat 'implement unit'"
echo x >> src/a.ts; git commit -qam "feat(taskdir-lain): implement unit 03"
python3 "$S" --root "$tmp" --taskdir "$TD" --brief 01 | grep '^\[13\]'
echo "   kontrol: commit user biasa menyentuh berkas yang sama"
echo y >> src/a.ts; git commit -qam "fix: suntingan user"
python3 "$S" --root "$tmp" --taskdir "$TD" --brief 01 | grep '^\[13\]'

echo "== (B) 'git am' berhenti (rebase-apply) — repo utama vs git worktree"
git checkout -q -b donor; sed -i 's/b2/B2/' src/b.ts; git commit -qam "ubah b2"; git format-patch -1 -o "$tmp/.." -q >/dev/null
P=$(ls -t "$tmp"/../0001-*.patch | head -1); git checkout -q main
sed -i 's/b2/bX/' src/b.ts; git commit -qam "ubah b2 di main"
git worktree add -q "$tmp-wt" -b wt
git am "$P" >/dev/null 2>&1; echo "   repo utama : $(git status | sed -n 2p)"
python3 "$S" --root "$tmp" --taskdir "$TD" | grep '^\[9\]'
( cd "$tmp-wt"; git am "$P" >/dev/null 2>&1; echo "   worktree   : $(git status | sed -n 2p)"; ls -d "$(git rev-parse --git-path rebase-apply)" )
python3 "$S" --root "$tmp-wt" --taskdir "$TD" | grep '^\[9\]'
```

Output aktual (kode `34684ee`):

```
== (A) commit taskdir LAIN menyentuh src/a.ts, subjek memuat 'implement unit'
[13] Kesegaran brief (based_on)       : PASS (nol commit asing menyentuh `files_touched` sesudah cc10442)
   kontrol: commit user biasa menyentuh berkas yang sama
[13] Kesegaran brief (based_on)       : WARN (berkas berubah sesudah brief ditulis: src/a.ts (1 commit))
== (B) 'git am' berhenti (rebase-apply) — repo utama vs git worktree
   repo utama : You are in the middle of an am session.
[9] HEAD pada branch                 : FAIL (rebase sedang berjalan)
   worktree   : You are in the middle of an am session.
/tmp/tmp.CFSVayBn7C/.git/worktrees/tmp.CFSVayBn7C-wt/rebase-apply
[9] HEAD pada branch                 : PASS (branch `wt`)
```

Output sesudah patch:

```
== (A) commit taskdir LAIN menyentuh src/a.ts, subjek memuat 'implement unit'
[13] Kesegaran brief (based_on)       : WARN (berkas berubah sesudah brief ditulis: src/a.ts (1 commit))
   kontrol: commit user biasa menyentuh berkas yang sama
[13] Kesegaran brief (based_on)       : WARN (berkas berubah sesudah brief ditulis: src/a.ts (2 commit))
== (B) 'git am' berhenti (rebase-apply) — repo utama vs git worktree
   repo utama : You are in the middle of an am session.
[9] HEAD pada branch                 : FAIL (rebase/`git am` sedang berjalan (`rebase-apply`))
   worktree   : You are in the middle of an am session.
/tmp/tmp.MOQKPqgLzc/.git/worktrees/tmp.MOQKPqgLzc-wt/rebase-apply
[9] HEAD pada branch                 : FAIL (rebase/`git am` sedang berjalan (`rebase-apply`))
```

### Perbaikan

Filter per slug memakai pola subjek yang sama dengan `precondition_lib.chain_commits`. Deteksi rebase lewat `git rev-parse --git-path` dan diperiksa **sebelum** cek detached HEAD, agar rebase yang berhenti juga mendapat pesan yang tepat. `--git-path` yang kosong (repo non-git) dijaga agar tidak menjadi `root` dan tidak memberi vonis palsu.

```diff
--- a/src/plugins/frontenddev/skills/architect/scripts/check_preconditions.py
+++ b/src/plugins/frontenddev/skills/architect/scripts/check_preconditions.py
@@ -49,6 +49,7 @@
     read_status,
     report_json,
     review_is_fresh,
+    taskdir_slug,
 )
 
 VALIDATE_BRIEFS = Path(__file__).resolve().parents[2] / "plan" / "scripts" / "validate_briefs.py"
@@ -217,15 +218,18 @@
 
     def _check_9_head(self) -> None:
         name = "HEAD pada branch"
+        # `--git-path` menunjuk git dir yang benar juga di worktree/submodule, tempat `.git` berupa berkas.
+        paths = {d: git(self.root, "rev-parse", "--git-path", d).strip() for d in ("rebase-apply", "rebase-merge")}
+        ongoing = [d for d, p in paths.items() if p and (self.root / p).exists()]
+        if ongoing:
+            self._add(9, name, "FAIL", f"rebase/`git am` sedang berjalan (`{ongoing[0]}`)",
+                      "Selesaikan atau batalkan (`git rebase --abort` / `git am --abort`) dulu.")
+            return
         branch = git(self.root, "symbolic-ref", "--short", "-q", "HEAD").strip()
         if not branch:
             self._add(9, name, "FAIL", "detached HEAD",
                       "Checkout branch sah sebelum commit unit mana pun.")
             return
-        rebase = any((self.root / ".git" / d).exists() for d in ("rebase-apply", "rebase-merge"))
-        if rebase:
-            self._add(9, name, "FAIL", "rebase sedang berjalan", "Selesaikan atau batalkan rebase dulu.")
-            return
         self._add(9, name, "PASS", f"branch `{branch}`")
 
     # ---------------------------------------------------------------- ingest
@@ -304,12 +308,14 @@
             self._add(13, name, "WARN", f"`based_on` {m.group(1)} tidak ada di repo — kesegaran tak dapat divonis",
                       "Sebut ke user sebelum dispatch; brief mungkin ditulis di cabang lain.")
             return
+        # Hanya commit unit taskdir INI yang dikecualikan; `implement unit` milik taskdir lain tetap asing.
+        own_unit = re.compile(rf"^[a-z]+!?\({re.escape(taskdir_slug(self.taskdir_rel))}\)!?: implement unit \d+")
         stale = []
         for f in as_list(fm.get("files_touched")):
-            newer = git(self.root, "log", "--oneline", f"{m.group(1)}..HEAD", "--", f).strip()
-            own = [l for l in newer.splitlines() if "implement unit" not in l]
-            if own:
-                stale.append(f"{f} ({len(own)} commit)")
+            subjects = git(self.root, "log", "--format=%s", f"{m.group(1)}..HEAD", "--", f).splitlines()
+            foreign = [s for s in subjects if s.strip() and not own_unit.match(s)]
+            if foreign:
+                stale.append(f"{f} ({len(foreign)} commit)")
         if stale:
             self._add(13, name, "WARN", "berkas berubah sesudah brief ditulis: " + "; ".join(stale[:4]),
                       "Sebut ke user; brief yang tak lagi cocok dikembalikan ke `frontenddev:plan`.")
```

Teks pendamping: `src/plugins/frontenddev/skills/architect/SKILL.md:104` (Failure path 7), "Detached HEAD atau rebase berjalan" → "Detached HEAD, rebase, atau `git am` yang berhenti".

### Test

`src/plugins/frontenddev/tests/test_architect_preconditions.py`:

```python
"""C6 — Check 13 memfilter commit unit per slug; Check 9 mendeteksi rebase/am lewat --git-path."""
import subprocess

from conftest import TASKDIR, run_script

SCRIPT = "architect/scripts/check_preconditions.py"


def line(proc, cid):
    return next(l for l in proc.stdout.splitlines() if l.startswith(f"[{cid}]"))


def setup(repo):
    repo.write("src/a.ts", "a\n")
    repo.write("src/b.ts", "b1\nb2\nb3\n")
    sha = repo.commit("chore: awal")
    repo.write(f"{TASKDIR}/brief-01-a.md",
               f"---\nstatus: READY\nbased_on: {sha} (2026-09-24)\nfiles_touched: [src/a.ts]\n---\n\n# Brief\n")
    repo.commit("docs(label): draft breakdown")


def test_implement_unit_taskdir_lain_tetap_asing(repo):
    setup(repo)
    repo.write("src/a.ts", "a\nx\n")
    repo.commit("feat(taskdir-lain): implement unit 03 - lain")
    assert "WARN" in line(run_script(SCRIPT, "--root", repo.root, "--taskdir", TASKDIR, "--brief", "01"), 13)


def test_implement_unit_taskdir_sendiri_dikecualikan(repo):
    setup(repo)
    repo.write("src/a.ts", "a\nx\n")
    repo.commit("feat(label): implement unit 02 - label")
    assert "PASS" in line(run_script(SCRIPT, "--root", repo.root, "--taskdir", TASKDIR, "--brief", "01"), 13)


def test_git_am_berhenti_di_worktree_terdeteksi(repo, tmp_path):
    setup(repo)
    repo.git("checkout", "-q", "-b", "donor")
    repo.write("src/b.ts", "b1\nB2\nb3\n")
    repo.commit("ubah b2")
    patch = repo.git("format-patch", "-1", "-o", str(tmp_path)).strip()
    repo.git("checkout", "-q", "main")
    repo.write("src/b.ts", "b1\nbX\nb3\n")
    repo.commit("ubah b2 di main")
    wt = tmp_path / "wt"
    repo.git("worktree", "add", "-q", str(wt), "-b", "wt")
    subprocess.run(["git", "-C", str(wt), "am", patch], capture_output=True)
    proc = run_script(SCRIPT, "--root", wt, "--taskdir", TASKDIR)
    assert "FAIL" in line(proc, 9) and "rebase" in line(proc, 9)
```

### Selesai bila

Commit `implement unit` milik slug lain memicu WARN Check 13, commit unit milik slug sendiri tetap dikecualikan, dan `git am` yang berhenti di worktree membuat Check 9 FAIL.

---

## C7 [Rendah] Penamaan 9 dimensi tidak seragam.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1,5 jam · **Bergantung pada:** — · **Memblokir:** C8

### Lokasi & kode saat ini

Nama dimensi per sumber, dikutip persis:

| # | `skills/architect/templates/review-template.md:69-77` (dan `review/templates/audit-template.md:95-103`) | `agents/code-reviewer.md:47-55` | `skills/review/references/nine-dimensions-catalog.md` (heading) | `skills/review/SKILL.md:40` | `skills/profile/stacks/_CONTRACT.md:50-58` | `skills/review/references/review-checklist.md:57,69` (contoh) |
|---|---|---|---|---|---|---|
| 1 | Layer Boundaries | Layer Boundaries | `:7` Layer Boundaries & 5-Tier Architecture | Layer Boundaries | `layer-boundaries` | Dimension 1 (Layer Boundaries) |
| 2 | Data Flow & DTO | Data Flow, Typing & DTO | `:21` Data Flow, Typing & DTO Integrity | Data Flow & DTO | `data-flow` | Dimension 2 (DTO Integrity) |
| 3 | API Layer | API Layer Zero Side Effects | `:33` API Layer (Zero Side Effects) | API Layer | `api-layer` | — |
| 4 | State Scope & Ownership | State Scope & Ownership | `:45` State Scope & Ownership | State Scope | `state-scope` | — |
| 5 | UI & 6-State Branches | UI & 6-State Branches | `:57` UI & The 6-State Branches | Enam Cabang State | `ui-states` | Dimension 5 (6-State Branches) |
| 6 | Platform Semantics | Platform & Framework Boundary | `:70` Platform & Framework Boundary Semantics | Platform & Framework | `platform` | — |
| 7 | Error Handling | Error Handling | `:80` Error Handling & Boundary Model | Error Handling | `error-handling` | Dimension 7 (Error Handling) |
| 8 | Performance & Leaks | Performance & Leaks | `:91` Performance, Memory Leaks & Cleanup | Performance & Leaks | `performance` | — |
| 9 | Test Quality & Coverage | Test Quality | `:102` Test Quality & Coverage → persisnya "Test Quality & Co-located Coverage" | Test Quality | `tests` | — |

Nama enam cabang state:

- `review-checklist.md:42`: "Seluruh 6 cabang state (Initial, Loading, Empty, Error, Ready, Stale) tertangani."
- `nine-dimensions-catalog.md:60`: "Setiap layar mengimplementasikan seluruh 6 cabang state: Initial, Loading (CLS-safe skeleton), Empty, Error with Retry, Ready, dan Mutating."
- `_CONTRACT.md:54`: "6 cabang state: initial, loading, empty, error+retry, ready, mutating"
- Pembanding (kanonik UI.md): `ui-design/templates/ui-template.md` ST-6 "State Stale / Mutating", validator "stale/mutating".

Rubrik dan konsumen:

- `nine-dimensions-catalog.md:76`: "Severity dan butir konkret **sepenuhnya milik adapter** (`#### platform`)". Sementara `:120` (baris P2 rubrik) menulis "..., touch target <44dp, ...".
- `_CONTRACT.md:116`: "### 5. `## Review checklist` — konsumen: `frontenddev:review`". Padahal `agents/code-reviewer.md:25,33` juga membaca `## Review checklist` adapter.

Severity: tidak ada kontradiksi substantif. `react-native.md:153` juga menetapkan touch target P2.

### Masalah

Tiga pola penamaan (slug adapter, nama tampilan template, judul katalog) tanpa satu sumber. Pembaca REVIEW.md, AUDIT, dan katalog melihat nama berbeda untuk dimensi yang sama. Label cabang "Ready/Stale/Mutating" berbeda dari UI.md ("Normal", "Stale / Mutating").

### Perbaikan

Keputusan kanonik (perubahan minimal):

- **Slug** tetap dari `_CONTRACT.md` (dipakai 36 heading `#### ` di empat adapter; tidak disentuh).
- **Nama tampilan** mengikuti dua template artefak (REVIEW, AUDIT), dengan dua koreksi: 6 → "Platform & Framework Boundary" (sama dengan code-reviewer dan katalog), 9 → "Test Quality".
- **Cabang state**: normal, loading, kosong, error, initial, stale/mutating (sama dengan UI.md dan validator).

| # | Slug | Nama tampilan kanonik |
|---|---|---|
| 1 | `layer-boundaries` | Layer Boundaries |
| 2 | `data-flow` | Data Flow & DTO |
| 3 | `api-layer` | API Layer |
| 4 | `state-scope` | State Scope & Ownership |
| 5 | `ui-states` | UI & 6-State Branches |
| 6 | `platform` | Platform & Framework Boundary |
| 7 | `error-handling` | Error Handling |
| 8 | `performance` | Performance & Leaks |
| 9 | `tests` | Test Quality |

Teks pengganti per berkas:

1. `src/plugins/frontenddev/skills/profile/stacks/_CONTRACT.md:46-58`: jadikan tabel ini sumber tunggal.

   ```markdown
   ## Sembilan dimensi review (netral stack)

   Sumber tunggal nama dimensi. Adapter memakai kolom **Slug** sebagai `#### <slug>`; template REVIEW/AUDIT, `agents/code-reviewer.md`, katalog, dan SKILL memakai kolom **Nama** persis.

   | # | Slug | Nama | Cakupan |
   |---|---|---|---|
   | 1 | `layer-boundaries` | Layer Boundaries | DTO terisolasi dari presentasi, Controller dipanggil dari presentasi, Service murni |
   | 2 | `data-flow` | Data Flow & DTO | Nol `any`, View-Model memetakan seluruh field DTO ke `*UI` |
   | 3 | `api-layer` | API Layer | Nol navigasi/toast di API layer, query key array factory |
   | 4 | `state-scope` | State Scope & Ownership | State query di Controller, tidak ada fetch tersembunyi di komponen anak |
   | 5 | `ui-states` | UI & 6-State Branches | 6 cabang state per layar: normal, loading, kosong, error (+retry), initial, stale/mutating |
   | 6 | `platform` | Platform & Framework Boundary | Batas framework & platform: safe area, touch target, server/client boundary |
   | 7 | `error-handling` | Error Handling | Error backend dipetakan ke pesan manusiawi, retry aktif |
   | 8 | `performance` | Performance & Leaks | Cleanup efek/subscription, memoisasi kalkulasi berat |
   | 9 | `tests` | Test Quality | Test View-Model/Service punya assertion nyata, tidak di-skip |
   ```

2. `_CONTRACT.md:116`: "### 5. `## Review checklist` — konsumen: `frontenddev:review`, `agents/code-reviewer.md` (review penutup `frontenddev:architect`)".
3. `skills/architect/templates/review-template.md:74,77` dan `:174,177`, serta `skills/review/templates/audit-template.md:100,103`: `Platform Semantics` → `Platform & Framework Boundary`; `Test Quality & Coverage` → `Test Quality`.
4. `agents/code-reviewer.md:48`: `**Data Flow, Typing & DTO**` → `**Data Flow & DTO**`. `:49`: `**API Layer Zero Side Effects**` → `**API Layer**` (penjelasan "zero side effects" sudah ada di predikatnya).
5. `skills/review/references/nine-dimensions-catalog.md`: heading jadi `## <n>. Dimension <n>: <Nama> (\`<slug>\`)`, mis. `## 1. Dimension 1: Layer Boundaries (\`layer-boundaries\`)`. Subjudul lama ("& 5-Tier Architecture", "Zero Side Effects", "Boundary Model", "Co-located Coverage") pindah ke kalimat pertama "Target Periksa".
   - `:60` → "Setiap layar mengimplementasikan seluruh 6 cabang state: normal, loading (skeleton berdimensi, CLS aman), kosong, error dengan retry, initial, dan stale/mutating."
   - `:120` → "| **P2 (Peringatan)** | State di kartu anak, query key raw string, error state tanpa retry, missing cleanup, pelanggaran platform P2 adapter | ... |" (buang "touch target <44dp", karena dimensi 6 milik adapter).
6. `skills/review/SKILL.md:40`: "1 Layer Boundaries · 2 Data Flow & DTO · 3 API Layer · 4 State Scope & Ownership · 5 UI & 6-State Branches · 6 Platform & Framework Boundary · 7 Error Handling · 8 Performance & Leaks · 9 Test Quality."
7. `skills/review/references/review-checklist.md:42` → "- [ ] Seluruh 6 cabang state (normal, loading, kosong, error, initial, stale/mutating) tertangani di tiap layar." `:57` "Dimension 2 (DTO Integrity)" → "Dimension 2 (Data Flow & DTO)". `:69` "Dimension 5 (6-State Branches)" → "Dimension 5 (UI & 6-State Branches)".

### Test / Verifikasi

- `md_search` di `src/plugins/frontenddev/**/*.md` untuk `Platform Semantics`, `Test Quality & Coverage`, `API Layer Zero`, `Data Flow, Typing`, `Initial, Loading`, `Ready, dan Mutating`, `touch target <44dp`, `DTO Integrity)` → 0 hasil.
- Usulan lint L6.3: ambil kolom Nama dari tabel `_CONTRACT.md` dan cocokkan dengan kolom 2 tabel `## 9 Dimensi` di kedua template.
- `validate_review.py` hanya menghitung 9 baris (`:119`), jadi tidak terpengaruh.

### Selesai bila

Kesembilan nama dan enam label cabang sama di semua berkas di atas, `_CONTRACT.md` menyatakan diri sumber tunggal, dan konsumen `## Review checklist` mencantumkan `code-reviewer`.

---

## C8 [Rendah] Adapter melanggar kontraknya sendiri.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 2,5 jam · **Bergantung pada:** C7 · **Memblokir:** —

### Lokasi & kode saat ini

Kontrak: `src/plugins/frontenddev/skills/profile/stacks/_CONTRACT.md:24` ("Satu adapter ditargetkan 7.000–14.000 karakter"), `:27` ("**Nol duplikasi lintas-adapter.** Butir yang berlaku di semua stack adalah tanda butir itu salah tempat; ia milik `SKILL.md` atau `references/` skill"), `:143` (gerbang 4: "Tidak ada butir yang identik dengan butir di adapter lain."), `:20` (≥12 butir / ≥5 dimensi).

Butir yang ada di keempat adapter (kutipan persis, `## Review checklist`):

| Predikat | `react-vite.md` | `react-native.md` | `sveltekit.md` | `svelte-vite.md` |
|---|---|---|---|---|
| `it.skip`/`.only` P1 | `:167` `- **\`it.skip\`/\`test.only\` tertinggal.** P1. Grep: \`Grep -n "it\.skip\|test\.skip\|\.only("\`.` | `:170` `- **\`it.skip\`/\`.only\` tertinggal.** P1. Grep: …` (sama) | `:178` sama dengan RN | `:168` sama dengan RN |
| render tanpa expect P1 | `:166` `- **\`test(\` yang hanya \`render(\` tanpa \`expect(\`.** P1. Coverage semu.` | `:169` `- **Test hanya \`render(\` tanpa \`expect(\`.** P1.` | `:177` `- **Test \`render(\` tanpa \`expect(\`.** P1.` | `:167` sama dengan SK |
| `error.message` mentah P2 | `:157` `- **\`error.message\` mentah ditampilkan ke user.** P2. Teks \`AxiosError: …\` bocor ke layar.` | `:160` `- **\`error.message\` mentah di \`<Text>\`.** P2.` | `:167` `- **\`error.message\` mentah di template.** P2.` | `:158` sama dengan SK |
| `: any` P1 | `:131` `- **\`: any\` atau \`as any\` di DTO, Service, atau View-Model.** P1. … Grep: \`Grep -n ": any\|as any" src/features/\`.` | `:134` `- **\`: any\` / \`as any\` di jalur data.** P1. Grep: \`Grep -n ": any\|as any" src/features/\`.` | `:139` `- **\`: any\` / \`as any\` di DTO, Service, View-Model.** P1. Grep: … \`src/lib/\`.` | `:130` sama dengan RN |
| `queryKey` tanpa factory P2 | `:137` `- **\`queryKey\` berupa string atau array literal tanpa factory.** P2. … Grep: \`Grep -n "queryKey: \['"\`.` | `:139` `- **\`queryKey\` tanpa factory.** P2. Grep: (sama)` | `:145` `- **\`queryKey\` literal tanpa factory.** P2. Grep: (sama)` | `:136` sama dengan SK |

Hitungan: **5 predikat** sama makna dan severity di keempat adapter. Identik byte: `it.skip` di 3 adapter (RN, SK, SV); `render(`, `error.message`, `queryKey` di 2 (SK, SV); `: any` di 2 (RN, SV). Kelimanya **sudah** ada di katalog netral (`nine-dimensions-catalog.md` Dimensi 2 `:28`, 3 `:40`, 7 `:86`, 9 `:109-110`) dan di `agents/code-reviewer.md:48-55`.

Butir SK yang identik dengan katalog: `sveltekit.md:179` "View-Model dites lewat render komponen alih-alih fungsi murni. P3" (katalog Dimensi 9 [P3], kalimat sama) dan `sveltekit.md:157` "Loading merender kosong alih-alih skeleton. P2" (katalog Dimensi 5 [P2]).

Ukuran (`wc -m`, tanpa membaca isi):

```
 8661 _CONTRACT.md
13257 react-native.md
12985 react-vite.md
14493 sveltekit.md
12938 svelte-vite.md
```

Jumlah butir `## Review checklist` saat ini: react-vite 18, react-native 19, sveltekit 23, svelte-vite 21.

**Koreksi terhadap ISSUES.md:** "identik di keempat adapter" benar untuk makna, tidak untuk teks. Selain tiga butir yang disebut, `: any` dan `queryKey` tanpa factory juga duplikat di keempatnya.

### Masalah

Adapter memuat butir netral stack yang sudah ada di katalog, sehingga menambah biaya context tiap sesi. `sveltekit.md` menembus batas 14.000 karakter.

### Perbaikan

1. **Katalog netral** `skills/review/references/nine-dimensions-catalog.md`: predikatnya sudah ada; tambahkan hanya resep grep yang kini seragam:
   - Dimensi 2: `Grep: \`Grep -n ": any\|as any" <source_root dari structure.md profil>\``
   - Dimensi 3: `Grep: \`Grep -n "queryKey: \['"\``
   - Dimensi 9: `Grep: \`Grep -n "it\.skip\|test\.skip\|\.only("\``
2. **Hapus dari adapter** (5 butir per adapter): react-vite `:131,137,157,166,167`; react-native `:134,139,160,169,170`; sveltekit `:139,145,167,177,178`; svelte-vite `:130,136,158,167,168`. Hapus heading `#### <slug>` yang menjadi kosong (`_CONTRACT.md:118`: "Hanya dimensi yang punya butir nyata yang ditulis"): react-vite `error-handling`, `tests`; react-native `data-flow`, `error-handling`; svelte-vite `error-handling`, `tests`.
3. **sveltekit** tambahan: hapus juga `:179` dan `:157` (identik dengan katalog) serta heading `#### tests` yang kosong. Hitungan dari `wc -m` baris-baris itu: 5 butir umum = 354 karakter; `:179` + `:157` + heading + baris kosong = 141 karakter. Hasilnya ± **13.998**, tepat di bawah batas. Pangkas ≥ 300 karakter lagi dari butir yang paling jarang terbukti (aturan 4) agar ada margin (target ≤ 13.700).
4. **Perkiraan sesudah** (dari `wc -m` baris yang dihapus, tanpa heading): react-vite ± 12.412 (13 butir, 7 dimensi); react-native ± 12.914 (14 butir, 7 dimensi); svelte-vite ± 12.593 (16 butir, 7 dimensi); sveltekit ± 13.998 sebelum pangkas tambahan (16 butir, 8 dimensi). Semua tetap ≥ 12 butir / ≥ 5 dimensi.
5. **Cakupan tidak hilang**: skill `review` membaca katalog + adapter; `code-reviewer` membaca Fase 2 miliknya (`agents/code-reviewer.md:47-55`, sudah memuat kelima predikat) + adapter.
6. **Keputusan (butuh user)**, `_CONTRACT.md:143` gerbang 4: pasangan adapter sefamili masih punya butir identik byte yang memakai idiom bersama. Contoh: `sveltekit.md` dan `svelte-vite.md` "`import ... from '.../dto/...'` di `.svelte`" dan "`{#await}` tanpa `{:catch}`"; `react-vite.md` dan `svelte-vite.md` "Alias hanya di salah satu `tsconfig`/`vite.config`". Usulan teks pengganti gerbang 4:

   > 4. Tidak ada butir netral stack di adapter (predikat yang sudah ada di `skills/review/references/nine-dimensions-catalog.md`). Butir yang sama di dua adapter sefamili (Svelte, SPA Vite) sah hanya bila memakai idiom atau resep grep/glob yang spesifik keluarga itu.

   Alternatifnya: pertahankan teks lama dan pindahkan butir Svelte bersama ke seksi keluarga di katalog.

### Test / Verifikasi

- `wc -m src/plugins/frontenddev/skills/profile/stacks/*.md` → keempat adapter ≤ 14.000.
- `md_search` untuk `tertinggal.** P1` dan `mentah di template` di `skills/profile/stacks/*.md` → 0 hasil.
- Usulan lint L6.3 (boleh membaca `.md`, karena larangan mdcp hanya untuk agen): (a) batas karakter per adapter; (b) tidak ada butir `- **…**` di `## Review checklist` yang teksnya (dinormalkan: huruf kecil, tanpa backtick) sama di ≥ 3 adapter atau sama dengan predikat katalog; (c) ≥ 12 butir / ≥ 5 dimensi.

### Selesai bila

Kelima predikat umum hanya ada di katalog (dengan grep), keempat adapter ≤ 14.000 karakter dan tetap memenuhi ambang, dan gerbang 4 `_CONTRACT.md` diputuskan (teks lama ditegakkan atau diganti).

---

## C9 [Rendah] "Tepat sekali" vs "ulangi maksimal sekali".

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 0,25 jam · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini

- `src/plugins/frontenddev/skills/architect/SKILL.md:13`: "Dispatch `code-reviewer` tepat sekali per penutup; `REVIEW.md` di-commit hanya sesudah `validate_review.py` `PASS`. Review ulang (sesudah brief perbaikan) menimpa `REVIEW.md` utuh."
- `src/plugins/frontenddev/skills/architect/SKILL.md:55`: "... dan dispatch `code-reviewer` (`subagent_type`: `frontenddev:code-reviewer`) tepat sekali."
- `src/plugins/frontenddev/skills/architect/dispatcher/reviewer.md:60`: "| Validator `FAIL` | Laporan tidak sah. Ulangi dispatch maksimal sekali dengan slot yang sama; tetap `FAIL` → review tidak tuntas ..."
- `src/plugins/frontenddev/skills/architect/dispatcher/reviewer.md:61`: "| `REVIEW.md` tidak ada | Cacat kerja subagent: ulangi maksimal sekali; ..."
- Sudah selaras dengan dispatcher: `SKILL.md:76` (Guardrails, "dispatch ulang sekali atau laporkan tidak tuntas") dan `:103` (Failure path 6 "Reviewer gagal dua kali").

### Masalah

IRON LAW dan Phase 4 melarang dispatch kedua, sementara dispatcher, Guardrails, dan Failure path mengizinkannya. Model yang menaati IRON LAW berhenti sesudah satu kegagalan validator, padahal pemulihan yang dirancang adalah satu kali ulang.

### Perbaikan

Pertahankan perilaku dispatcher (maksimal 2 dispatch per penutup). Teks pengganti:

- `SKILL.md:13`:

  > - Dispatch `code-reviewer` sekali per penutup; dispatch ulang **maksimal satu kali**, hanya bila `REVIEW.md` absen atau `validate_review.py` `FAIL` (`dispatcher/reviewer.md` Penanganan Balikan). Gagal kedua kalinya → Failure path 6. `REVIEW.md` di-commit hanya sesudah `validate_review.py` `PASS`. Review ulang (sesudah brief perbaikan) menimpa `REVIEW.md` utuh.

- `SKILL.md:55`: ganti "tepat sekali." dengan "; ulang maksimal sekali sesuai Penanganan Balikan `dispatcher/reviewer.md`."

### Test / Verifikasi

`md_search` "tepat sekali" di `skills/architect/SKILL.md` hanya menyisakan `:12` (lint/test/build) dan `:42` (implementor).

### Selesai bila

Tidak ada kalimat di `architect/SKILL.md` yang melarang dispatch ulang reviewer yang diizinkan dispatcher.

---

## C10 [Rendah] Profil: parameter dan template.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1 jam · **Bergantung pada:** **L1.1** · **Memblokir:** C13

### Lokasi & kode saat ini

- `src/plugins/frontenddev/skills/profile/SKILL.md:23`: "- `profile_dir` — string — default `".claude/profile"` — target tulis Phase 6; nilai lain ditolak."
- `src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py:59-60` dan `:297-298`: nilai apa pun diterima.

  ```python
        self.profile_rel = profile_dir or DEFAULT_PROFILE_DIR
        self.profile_dir = self.root / self.profile_rel
  ...
    parser.add_argument("--profile-dir", default=None, dest="profile_dir",
                        help=f"direktori profil, default {DEFAULT_PROFILE_DIR}")
  ```

- `src/plugins/frontenddev/skills/profile/templates/profile-template.md:24`: "| `index.json` | `project`, `stack`, `platform`, `framework`, `source_root`, `workspace`, `commit_convention` | ...". Tanpa `target_app`, sedangkan skema `:44-53` memuat `"target_app": "<kosong bila single; mis. apps/web pada monorepo>"` (`:51`), begitu juga `SKILL.md` Phase 6.
- Konteks: `hooks/lead-gate.sh:44,76` dan semua markdown membaca `.claude/profile/` apa adanya. Sepuluh skrip menerima `--profile-dir` (ux-design, ui-design, contract, plan, `plan/validate_briefs.py`, task, architect, review, profile).

### Reproduksi

```bash
#!/usr/bin/env bash
# C10 — profile: --profile-dir selain .claude/profile diterima
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
export PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d); cd "$tmp"; git init -q -b main
echo '{"dependencies":{"react":"19.0.0"},"devDependencies":{"vite":"6.0.0"}}' > package.json
out=$(mktemp -d)
for d in docs/elsewhere "$out/luar-repo"; do
  echo "== --profile-dir $d"
  python3 "$PLUGIN/skills/profile/scripts/check_preconditions.py" --root "$tmp" --profile-dir "$d" | grep -E '^PRECONDITION|^\[3\]|^Terselesaikan'
done
```

Output aktual (kode `34684ee`):

```
== --profile-dir docs/elsewhere
PRECONDITION CHECK: profile [PASS] (6/6 passed)
[3] Direktori profil dapat ditulis   : PASS (induk terdekat `/tmp/tmp.by5WTb391g` dapat ditulis)
Terselesaikan: stack `react-vite` · mode `GENERATE`
== --profile-dir /tmp/tmp.L1lDRUSsnx/luar-repo
PRECONDITION CHECK: profile [PASS] (6/6 passed)
[3] Direktori profil dapat ditulis   : PASS (induk terdekat `/tmp/tmp.L1lDRUSsnx` dapat ditulis)
Terselesaikan: stack `react-vite` · mode `GENERATE`
```

Output sesudah patch:

```
== --profile-dir docs/elsewhere
PRECONDITION CHECK: profile [FAIL] (5/6 passed)
[3] Direktori profil dapat ditulis   : FAIL (`--profile-dir docs/elsewhere` ditolak)
Terselesaikan: stack `react-vite` · mode `GENERATE`
== --profile-dir /tmp/tmp.zuJ00ycMZa/luar-repo
PRECONDITION CHECK: profile [FAIL] (5/6 passed)
[3] Direktori profil dapat ditulis   : FAIL (`--profile-dir /tmp/tmp.zuJ00ycMZa/luar-repo` ditolak)
Terselesaikan: stack `react-vite` · mode `GENERATE`
```

### Masalah

Profil yang ditulis ke path lain tidak pernah dibaca hook maupun skill hilir. Hook tetap berkata "profil BELUM DIBUAT", sehingga profiling diulang. Template peta berkas tidak sinkron dengan skema.

### Perbaikan

1. `check_preconditions.py`: tolak nilai selain default (diuji). Sesudah L1.1, bandingkan dengan konstanta `PROFILE_DIR` dari `precondition_lib` (mis. `.claude/profile/frontenddev`), bukan literal lokal.

```diff
--- a/src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py
+++ b/src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py
@@ -179,6 +179,12 @@
 
     def _check_3_profile_writable(self) -> None:
         name = "Direktori profil dapat ditulis"
+        # Hook `lead-gate.sh` dan seluruh skill hilir membaca `.claude/profile/` apa adanya;
+        # profil di path lain tidak pernah terbaca, jadi SKILL.md menyatakan "nilai lain ditolak".
+        if os.path.normpath(self.profile_rel) != DEFAULT_PROFILE_DIR:
+            self._add(3, name, "FAIL", f"`--profile-dir {self.profile_rel}` ditolak",
+                      f"Profil hanya sah di `{DEFAULT_PROFILE_DIR}/`; hapus parameter `profile_dir`.")
+            return
         if self.profile_dir.exists() and not self.profile_dir.is_dir():
             self._add(3, name, "FAIL", f"`{self.profile_rel}` ada tetapi bukan direktori",
                       "Bereskan path itu; profil hanya sah ditulis sebagai satu direktori.")
```

2. `SKILL.md:23`: "- `profile_dir` — string — default `".claude/profile"` — hanya untuk kompatibilitas; nilai lain ditolak skrip prasyarat (Check 3 `FAIL`) karena hook dan seluruh skill membaca `.claude/profile/`." Sesudah L1.1, ganti default dengan path per plugin.
3. `profile-template.md:24`: "| `index.json` | `project`, `stack`, `platform`, `framework`, `source_root`, `workspace`, `target_app`, `commit_convention` | ...".
4. (Ikut L1.1) Pertimbangkan membuang `--profile-dir` dari sembilan skrip lain agar path profil hanya berasal dari satu konstanta.

### Test

`src/plugins/frontenddev/tests/test_profile_preconditions.py`:

```python
"""C10 — profile menolak profile_dir selain .claude/profile."""
import pytest

from conftest import run_script

SCRIPT = "profile/scripts/check_preconditions.py"


@pytest.fixture
def react(repo):
    repo.write("package.json", '{"dependencies":{"react":"19.0.0"},"devDependencies":{"vite":"6.0.0"}}')
    return repo


@pytest.mark.parametrize("value", ["docs/elsewhere", "/tmp/luar-repo"])
def test_profile_dir_lain_ditolak(react, value):
    proc = run_script(SCRIPT, "--root", react.root, "--profile-dir", value)
    assert proc.returncode == 1 and "ditolak" in proc.stdout


@pytest.mark.parametrize("value", [None, ".claude/profile", "./.claude/profile/"])
def test_profile_dir_kanonik_diterima(react, value):
    args = ["--root", react.root] + (["--profile-dir", value] if value else [])
    assert run_script(SCRIPT, *args).returncode == 0
```

### Selesai bila

`--profile-dir` selain lokasi kanonik FAIL, lokasi kanonik (termasuk bentuk `./…/`) PASS, dan peta berkas template memuat `target_app`.

---

## C11 [Rendah] Rentang skill review bukan berkas rantai.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 1,5 jam · **Bergantung pada:** — · **Memblokir:** — (dikerjakan satu PR dengan C14)

### Lokasi & kode saat ini

- `src/plugins/frontenddev/skills/review/scripts/check_preconditions.py:117-119`:

  ```python
        sha = task_root_sha(self.root, self.taskdir_rel)
        self.resolved_range = f"{sha[:7]}..HEAD" if sha else ""
        self._add(1, name, "PASS", f"taskdir tuntas, rentang `{self.resolved_range}`")
  ```

- `src/plugins/frontenddev/skills/review/SKILL.md:31`: "Tetapkan objek: `git diff <range> --name-only`, isi `path`, atau rentang `akar..HEAD` taskdir tuntas (kecualikan `frontenddev/docs/**`, `.claude/**`)."
- Pembanding, review penutup: `src/plugins/frontenddev/agents/code-reviewer.md:31`: "Rentang wajib **berkas rantai**: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py files --taskdir {taskdir}` ... Commit di luar rantai (kerja user di rentang yang sama) tidak dinilai".
- Ambang macet: `review/SKILL.md:70` "(>60 detik)"; `profile/SKILL.md:85,195` "lebih dari 60s" / "(> 60s)"; `architect/SKILL.md:102` "(>5 menit)".

### Reproduksi

Skrip gabungan C11 + C14 (bagian C14 ada di item C14):

```bash
#!/usr/bin/env bash
# C11 + C14 — skill review: rentang taskdir dan target path
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
S="$PLUGIN/skills/review/scripts/check_preconditions.py"
export PYTHONDONTWRITEBYTECODE=1
base=$(mktemp -d); tmp="$base/repo"; mkdir -p "$tmp" "$base/rahasia"; echo s > "$base/rahasia/token.txt"
cd "$tmp"; git init -q -b main; git config user.email t@t; git config user.name t
mkdir -p src; echo a > src/a.ts; git add -A; git commit -qm "chore: awal"

echo "== C14: target path di luar repo"
for p in ../rahasia "$tmp/src" src; do
  printf '%-28s ' "--path $p"; python3 "$S" --root "$tmp" --target path --path "$p" | grep '^\[1\]'
done
ln -s ../../rahasia src/tautan; printf '%-28s ' "--path src/tautan (symlink)"; python3 "$S" --root "$tmp" --target path --path src/tautan | grep '^\[1\]'
rm src/tautan

echo "== C11: rentang target taskdir vs berkas rantai"
TD=frontenddev/docs/2609240900-label; mkdir -p "$TD"; printf -- '---\nstatus: ACTIVE\n---\n# Label\n' > "$TD/TASK.md"
git add -A; git commit -qm "docs(label): kunci TASK sebagai akar rantai"
echo b >> src/a.ts; git commit -qam "feat(label): implement unit 01 - label"
echo c > src/lain.ts; git add -A; git commit -qm "feat: kerja user di luar rantai"
echo "# r" > "$TD/REPORT.md"; git add -A; git commit -qm "docs(label): report"
echo d > src/sesudah.ts; git add -A; git commit -qm "feat(taskdir-lain): implement unit 01 - lain"
out=$(python3 "$S" --root "$tmp" --target taskdir --taskdir "$TD"); echo "$out" | grep -E '^\[1\]|^Terselesaikan'
rng=$(echo "$out" | sed -n 's/.*rentang=\([^;]*\);.*/\1/p')
echo "-- git diff $rng --name-only (Phase 0 review/SKILL.md):"; git diff "$rng" --name-only -- . ':(exclude)frontenddev/docs' ':(exclude).claude'
echo "-- chain.py files (rentang review penutup architect):"; python3 "$PLUGIN/skills/_common/chain.py" files --taskdir "$TD" --root "$tmp"
```

Output aktual (kode `34684ee`, bagian C11):

```
== C11: rentang target taskdir vs berkas rantai
[1] Objek review `taskdir` tersedia  : PASS (taskdir tuntas, rentang `4ef20f1..HEAD`)
Terselesaikan: rentang=4ef20f1..HEAD; tulis=tidak
-- git diff 4ef20f1..HEAD --name-only (Phase 0 review/SKILL.md):
src/a.ts
src/lain.ts
src/sesudah.ts
-- chain.py files (rentang review penutup architect):
src/a.ts
```

Output sesudah patch (bagian C11):

```
== C11: rentang target taskdir vs berkas rantai
[1] Objek review `taskdir` tersedia  : PASS (taskdir tuntas, rentang `bff78e7..HEAD`, 1 berkas rantai)
Terselesaikan: rentang=bff78e7..HEAD; tulis=tidak; berkas=chain.py files --taskdir frontenddev/docs/2609240900-label
```

### Masalah

Review ulang atas taskdir tuntas ikut menilai kerja user dan taskdir lain yang mendarat sesudah akar (`src/lain.ts`, `src/sesudah.ts`), sehingga temuannya bisa diajukan sebagai `finding_source` untuk kode yang bukan milik rantai itu. Vonisnya berbeda dari review penutup architect atas rantai yang sama. Ambang macet yang berbeda juga membuat baseline profil (`TIMEOUT` sesudah 60 detik) tidak sebanding dengan verifikasi penutup (5 menit).

### Perbaikan

1. Skrip (diuji; diff gabungan C11 + C14 ada di item C14): `chain_files()` jadi objek target `taskdir`, dengan WARN bila nol berkas, `chain_files` di keluaran JSON, dan `berkas=chain.py files …` di baris `Terselesaikan`.
2. `review/SKILL.md:31` → "- Tetapkan objek: `git diff <range> --name-only`, isi `path`, atau — untuk `target: taskdir` — **berkas rantai** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/chain.py files --taskdir <t>` (commit bersubjek `<type>(<slug>):` sejak akar, tanpa `frontenddev/docs/**` dan `.claude/**`); hunk per berkas `git diff <akar>..HEAD -- <berkas>`. Rentang ini sama dengan review penutup `agents/code-reviewer.md` Fase 0."
3. **Ambang macet (keputusan)**: satu nilai untuk ketiga skill. Usulan **5 menit per perintah** (nilai architect), karena test suite nyata sering melewati 60 detik dan baseline wajib sebanding dengan verifikasi penutup. Teks pengganti:
   - `review/SKILL.md:70`: "2. **Perintah verifikasi macet** (>5 menit per perintah, ambang yang sama dengan verifikasi penutup `architect`): tandai `UNVERIFIED / TIMEOUT`, lanjutkan sembilan dimensi."
   - `profile/SKILL.md:85`: "- `TIMEOUT / UNVERIFIED` — perintah macet lebih dari 5 menit (ambang yang sama dengan verifikasi penutup `architect`); batalkan prosesnya dan lanjutkan."
   - `profile/SKILL.md:195`: "| Perintah verifikasi macet (> 5 menit) | ... |"

### Test

Di `src/plugins/frontenddev/tests/test_review_preconditions.py` (berkas lengkap di C14): `test_target_taskdir_hanya_berkas_rantai`.

### Selesai bila

Target `taskdir` hanya menilai berkas rantai (sama dengan `chain.py files`), SKILL Phase 0 menyebut sumber yang sama, dan ambang macet di `review`, `profile`, dan `architect` bernilai sama.

---

## C12 [Rendah] Label keluaran salah.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 0,5 jam · **Bergantung pada:** — · **Memblokir:** —

### Lokasi & kode saat ini

- `src/plugins/frontenddev/skills/report/scripts/validate_report.py:158-159`: `return format_report("report validate", self.results)`
- `src/plugins/frontenddev/skills/task/scripts/validate_task.py:197-198`: `return format_report("task self-test", self.results)`
- `src/plugins/frontenddev/skills/_common/precondition_lib.py:611`: `lines = [f"PRECONDITION CHECK: {title} [{label}] ({passed}/{len(results)} passed"`

**Koreksi terhadap ISSUES.md:** `validate_task.py:198` punya masalah yang sama. Tidak ada konsumen yang mem-parse label ini (`md_search` "PRECONDITION CHECK|report validate|task self-test" di markdown plugin = 0 hasil).

### Reproduksi

```bash
#!/usr/bin/env bash
# C12 — label keluaran validator REPORT/TASK
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
PLUGIN=${PLUGIN:-$REPO/src/plugins/frontenddev}
export PYTHONDONTWRITEBYTECODE=1
tmp=$(mktemp -d); cd "$tmp"; git init -q -b main
TD=frontenddev/docs/2609240900-label; mkdir -p "$TD"
printf -- '---\nstatus: ACTIVE\n---\n\n# Label\n' > "$TD/TASK.md"
printf '# Label — Report\n\n## Ringkasan\n\nSelesai.\n\n## Perubahan\n\n- x (src)\n' > "$TD/REPORT.md"
python3 "$PLUGIN/skills/report/scripts/validate_report.py" --root "$tmp" --taskdir "$TD" | head -1
python3 "$PLUGIN/skills/task/scripts/validate_task.py"     --root "$tmp" --taskdir "$TD" | head -1
```

Output aktual lalu sesudah patch:

```
PRECONDITION CHECK: report validate [FAIL] (5/6 passed)
PRECONDITION CHECK: task self-test [FAIL] (1/7 passed)
---
REPORT VALIDATION: REPORT.md [FAIL] (5/6 passed)
TASK VALIDATION: TASK.md [FAIL] (1/7 passed)
```

### Perbaikan

Label mengikuti validator lain (`DOC VALIDATION`, `REVIEW VALIDATION`, `BRIEF VALIDATION`):

```diff
--- a/src/plugins/frontenddev/skills/_common/precondition_lib.py
+++ b/src/plugins/frontenddev/skills/_common/precondition_lib.py
@@ -601,14 +616,16 @@
 
 
 def format_report(title: str, results: List[Dict[str, Any]],
-                  resolved: Optional[Dict[str, str]] = None) -> str:
-    """Keluaran teks baku skrip prasyarat; `resolved` menjadi baris `Terselesaikan:`."""
+                  resolved: Optional[Dict[str, str]] = None,
+                  kind: str = "PRECONDITION CHECK") -> str:
+    """Keluaran teks baku skrip prasyarat/validator; `kind` = label baris pertama
+    (`PRECONDITION CHECK`, `REPORT VALIDATION`, ...); `resolved` menjadi baris `Terselesaikan:`."""
     results = sorted(results, key=lambda r: (str(r["id"]).zfill(3)))
     passed = sum(1 for r in results if r["status"] == "PASS")
     warned = sum(1 for r in results if r["status"] == "WARN")
     failed = sum(1 for r in results if r["status"] == "FAIL")
     label = "FAIL" if failed else ("PASS (WARN)" if warned else "PASS")
-    lines = [f"PRECONDITION CHECK: {title} [{label}] ({passed}/{len(results)} passed"
+    lines = [f"{kind}: {title} [{label}] ({passed}/{len(results)} passed"
              + (f", {warned} warn)" if warned else ")")]
     for r in results:
         lines.append(f"[{r['id']}] {r['name']:<32} : {r['status']} ({r['summary']})")
--- a/src/plugins/frontenddev/skills/report/scripts/validate_report.py
+++ b/src/plugins/frontenddev/skills/report/scripts/validate_report.py
@@ -156,7 +156,7 @@
                   "Isi seluruh slot template dan hapus komentar.")
 
     def format_text(self) -> str:
-        return format_report("report validate", self.results)
+        return format_report("REPORT.md", self.results, kind="REPORT VALIDATION")
 
     def to_json(self) -> str:
         return report_json(self.results, root=str(self.root), taskdir=self.taskdir_rel)
--- a/src/plugins/frontenddev/skills/task/scripts/validate_task.py
+++ b/src/plugins/frontenddev/skills/task/scripts/validate_task.py
@@ -197,2 +197,2 @@
     def format_text(self) -> str:
-        return format_report("task self-test", self.results)
+        return format_report("TASK.md", self.results, kind="TASK VALIDATION")
```

(Offset hunk `precondition_lib.py` di atas mengasumsikan patch C3 sudah masuk.)

### Test

`src/plugins/frontenddev/tests/test_output_labels.py`:

```python
"""C12 — validator tidak berlabel PRECONDITION CHECK."""
import pytest

from conftest import TASKDIR, run_script


@pytest.mark.parametrize("script,label", [("report/scripts/validate_report.py", "REPORT VALIDATION: REPORT.md"),
                                          ("task/scripts/validate_task.py", "TASK VALIDATION: TASK.md")])
def test_label_baris_pertama(repo, script, label):
    repo.write(f"{TASKDIR}/TASK.md", "---\nstatus: ACTIVE\n---\n\n# Label\n")
    repo.write(f"{TASKDIR}/REPORT.md", "# Label — Report\n\n## Ringkasan\n\nSelesai.\n\n## Perubahan\n\n- x (src)\n")
    first = run_script(script, "--root", repo.root, "--taskdir", TASKDIR).stdout.splitlines()[0]
    assert first.startswith(label)
```

### Selesai bila

Baris pertama `validate_report.py` dan `validate_task.py` berlabel `REPORT VALIDATION` / `TASK VALIDATION`, dan skrip prasyarat tetap `PRECONDITION CHECK`.

---

## C13 [Rendah] REFRESH profil penuh untuk satu baris drift.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 5 jam · **Bergantung pada:** **L1.1**, C10 · **Memblokir:** —

### Konteks

Sesudah review `PASS`/`WARNING`, architect meneruskan pola "preseden menyesatkan" yang disetujui user ke `frontenddev:profile` lewat `reported_drift`. Profile tidak punya mode selain GENERATE/REFRESH. Dengan `index.json` yang sudah ada, mode terselesaikan `REFRESH`: konfirmasi (tanpa `force`), 18 titik pemindaian, wawancara Phase 3, eksekusi ulang semua perintah, penulisan ulang sembilan berkas. Semua itu hanya untuk menambah satu baris `drift.md`, dan terjadi di tengah Phase 5, sebelum `REPORT.md` terbit.

### Lokasi & kode saat ini

- `src/plugins/frontenddev/skills/architect/SKILL.md:61`: "2. Verdict `PASS`/`WARNING` → kumpulkan baris `preseden menyesatkan` ... tanyakan sekali lewat `AskUserQuestion` ... Yang disetujui diteruskan ke `frontenddev:profile` lewat `reported_drift`."
- `src/plugins/frontenddev/skills/profile/SKILL.md:10` (IRON LAW): "... PADA MODE REFRESH DITULIS ULANG PENUH TANPA MERGE PARSIAL. ..."
- `profile/SKILL.md:50-51`: "`REFRESH` (profil sudah ada): ... minta konfirmasi "Lakukan REFRESH (tulis ulang penuh) atau BATAL?" ... Profil **ditulis ulang penuh** dari pemindaian segar; dilarang merge parsial."
- `profile/SKILL.md:55` (Phase 2 — 18 titik), `:71-72` (Phase 3 butir 4: `reported_drift` hanya diproses di dalam wawancara REFRESH), `:144` (Guardrail REFRESH TULIS ULANG PENUH).
- `profile/scripts/check_preconditions.py:240-256` `_resolve_mode`: hanya `GENERATE`/`REFRESH`.
- Format sumber: `agents/code-implementor.md:70` "`` `<file:baris>` — preseden menyesatkan — <pola> → <pola pengganti> ``". Format tujuan: `profile/SKILL.md:28` "`<file#simbol> — <pola warisan> → <pola pengganti>`". Format baris drift: `profile/templates/profile-template.md:183` "`- <pola warisan> (<sebaran>) → <pola modern> · deteksi \`<pola grep> @ <glob>\` · bukti <file#simbol>`".

### Reproduksi

Tidak ada skrip: alurnya ditentukan teks SKILL. Jejaknya: architect Phase 5 butir 2 → `frontenddev:profile {reported_drift}` → prasyarat `Terselesaikan: mode REFRESH` → Phase 1 minta konfirmasi (architect tidak meneruskan `force`) → Phase 2–6 penuh → commit `docs: refresh frontenddev profile`.

### Dampak

Menutup satu rantai memicu profiling penuh: biaya waktu, token, dan wawancara user. Bila REFRESH dibatalkan atau macet, `frontenddev:report` (butir 3) tertunda, dan umpan balik yang sudah disetujui user hilang. Karena mahal, model cenderung melewatkan umpan balik, sehingga preseden menyesatkan terus disalin brief berikutnya.

### Rencana perbaikan — mode `PATCH`

**Syarat** (ditagih skrip prasyarat; FAIL berarti arahkan ke REFRESH terpisah, bukan di tengah penutupan):

1. `index.json` ada, JSON valid, `stack` sama dengan stack terdeteksi.
2. Sepuluh berkas profil lengkap.
3. `reported_drift` tidak kosong (syarat skill; skrip tidak tahu isinya).
4. Tidak ada perubahan menggantung di direktori profil, karena PATCH hanya meng-commit `drift.md`.

**Langkah** (Phase P, pengganti Phase 1–6 pada mode PATCH):

1. **Normalisasi**: tiap butir berbentuk `<file#simbol> — <pola warisan> → <pola pengganti>`. Architect sudah mengubah `file:baris` menjadi `file#simbol` sebelum memanggil. Butir yang bentuknya lain ditolak dan dilaporkan.
2. **Deduplikasi**: lewati butir yang pola warisan atau resep `deteksi`-nya sudah ada di `drift.md`; catat "dilewati (duplikat)".
3. **Konflik**: bila pola pengganti tercatat sebagai pola warisan di `drift.md`, atau pola warisan tercatat sebagai gaya mayoritas di `layer-adoption.md`, hentikan PATCH dan sarankan REFRESH. Ini keputusan tim, bukan penambahan baris.
4. **Resep `deteksi`**: susun `<pola grep> @ <glob>` dalam **satu** span backtick (syarat Check P `validate_briefs.py`) dan jalankan Grep. ≥ 1 hit → `bukti <file#simbol>`; 0 hit → `bukti user` (sama dengan Phase 3 butir 4).
5. **Tulis**: tambahkan baris di akhir `drift.md` dengan format template §9. Berkas lain tidak disentuh: tanpa pemindaian 18 titik, tanpa baseline, tanpa `.gitignore`.
6. **Tanpa AskUserQuestion**: persetujuan sudah diambil architect Phase 5 butir 2.
7. **Commit**: `git add .claude/profile/drift.md` → `docs: patch frontenddev profile (drift +<n>)`.
8. **Output**: `### FRONTEND PROFILE REPORT — PATCH · drift +<n> baris · <k> dilewati (duplikat) · <m> bukti user`.

**Berkas yang disentuh:**

| Berkas | Perubahan |
|---|---|
| `src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py` | `--mode patch` + syarat 1–2 (sketsa diuji di bawah); syarat 4 via `git status --porcelain -- <profile_dir>` |
| `src/plugins/frontenddev/skills/profile/SKILL.md` | Parameter `mode` (+`"patch"`); IRON LAW: tambah "MODE PATCH HANYA MENAMBAH BARIS `drift.md` DARI `reported_drift`; BERKAS LAIN TIDAK DISENTUH."; Phase P baru sesudah Phase 1; Guardrail `:144` "(tidak berlaku untuk PATCH, yang tidak menghapus apa pun)"; Output: baris PATCH |
| `src/plugins/frontenddev/skills/profile/templates/profile-template.md` §9 | Kalimat: "Mode PATCH menambah baris dengan format yang sama; baris lama tidak disentuh." |
| `src/plugins/frontenddev/skills/architect/SKILL.md:61` | Teks pengganti di bawah |

Teks pengganti `architect/SKILL.md:61`:

> 2. Verdict `PASS`/`WARNING` → kumpulkan baris `preseden menyesatkan` dari seluruh `report-<NN>.md` dan `## Umpan balik profil` `REVIEW.md`. Ada isinya → tanyakan sekali lewat `AskUserQuestion`: tandai permanen di profil, atau buang. Yang disetujui diubah ke bentuk `<file#simbol> — <pola warisan> → <pola pengganti>` lalu diteruskan ke `frontenddev:profile` dengan `{ mode: "patch", reported_drift }`. PATCH hanya menambah baris `drift.md` dan meng-commitnya sendiri. Prasyarat PATCH `FAIL` (profil tidak utuh atau stack berubah) → catat `Umpan balik profil tertunda — butuh REFRESH` di Output dan lanjut ke butir 3; dilarang menjalankan REFRESH di tengah penutupan rantai.

Sketsa skrip prasyarat (diuji pada salinan, di atas patch C10):

```diff
--- a/src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py
+++ b/src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py
@@ -243,8 +243,28 @@
 
     # ------------------------------------------------------------------ mode
 
+    def _resolve_patch(self) -> None:
+        """PATCH = tambah baris `drift.md` saja; sah hanya di atas profil utuh berstack sama."""
+        name = "Mode operasi selaras"
+        try:
+            stack = json.loads(self.index_path.read_text(encoding="utf-8")).get("stack", "")
+        except (OSError, ValueError, AttributeError):
+            stack = None
+        missing = [f for f in PROFILE_FILES if not (self.profile_dir / f).is_file()]
+        problem = ("`index.json` absen atau bukan JSON valid" if stack is None
+                   else f"{len(missing)} berkas profil hilang: {', '.join(missing[:4])}" if missing
+                   else f"stack profil `{stack}` ≠ stack terdeteksi `{self.stack}`" if stack != self.stack
+                   else "")
+        self.mode = "PATCH" if not problem else ("REFRESH" if self.index_path.is_file() else "GENERATE")
+        self._add(6, name, "FAIL" if problem else "PASS",
+                  problem or "`PATCH` — hanya `drift.md` yang ditambah baris",
+                  "Profil tidak utuh atau stack berubah — PATCH tidak sah; jalankan mode REFRESH." if problem else "")
+
     def _resolve_mode(self) -> None:
-        """Selesaikan GENERATE vs REFRESH; ketidakcocokan jadi WARN, bukan FAIL."""
+        """Selesaikan GENERATE vs REFRESH (atau PATCH eksplisit); ketidakcocokan jadi WARN, bukan FAIL."""
+        if self.mode_arg == "patch":
+            self._resolve_patch()
+            return
         exists = self.index_path.is_file()
         actual = "REFRESH" if exists else "GENERATE"
         if self.mode_arg in ("generate", "refresh"):
@@ -297,7 +317,7 @@
 
 def main() -> None:
     parser = argparse.ArgumentParser(description="Profile Preconditions Checker")
-    parser.add_argument("--mode", default=None, help="auto | generate | refresh")
+    parser.add_argument("--mode", default=None, help="auto | generate | refresh | patch")
     parser.add_argument("--stack", default=None,
                         help="paksa <stack-id>; default auto (deteksi dari manifest)")
     parser.add_argument("--profile-dir", default=None, dest="profile_dir",
```

Hasil uji sketsa (skrip `c13.sh`: profil absen → profil utuh → `stack` diubah):

```
== profil belum ada
[6] Mode operasi selaras             : FAIL (`index.json` absen atau bukan JSON valid)
Terselesaikan: stack `react-vite` · mode `GENERATE`
== profil utuh, stack sama
[6] Mode operasi selaras             : PASS (`PATCH` — hanya `drift.md` yang ditambah baris)
Terselesaikan: stack `react-vite` · mode `PATCH`
== stack profil berbeda
[6] Mode operasi selaras             : FAIL (stack profil `sveltekit` ≠ stack terdeteksi `react-vite`)
Terselesaikan: stack `react-vite` · mode `REFRESH`
```

### Test yang ditambahkan / Verifikasi manual

- pytest (berkas `test_profile_preconditions.py`): tiga skenario di atas (`--mode patch`), plus syarat 4 (berkas profil lain termodifikasi → FAIL).
- Manual: rantai dengan satu `preseden menyesatkan` disetujui → architect memanggil profile PATCH → `git show --stat HEAD` hanya `.claude/profile/drift.md` (+1 baris) → `frontenddev:report` berjalan pada sesi yang sama.

### Selesai bila

Umpan balik profil dari architect menambah baris `drift.md` dalam satu commit tanpa pemindaian atau eksekusi perintah, dan kegagalan prasyarat PATCH tidak menahan `REPORT.md`.

### Risiko & catatan

- Keputusan user: apakah PATCH juga boleh dipakai di luar architect (mis. user meminta "tambah drift X")? Usulan: ya, dengan `AskUserQuestion` konfirmasi di langkah 6 bila pemanggilnya bukan architect.
- Path profil mengikuti L1.1 (`.claude/profile/frontenddev/drift.md` bila Opsi A dipilih).

---

## C14 [Rendah] Target `path` skill review tidak dibatasi ke dalam repo.

- [ ] Selesai

**Plugin:** frontenddev · **Estimasi:** 0,75 jam · **Bergantung pada:** C11 (berkas sama) · **Memblokir:** —

### Lokasi & kode saat ini

`src/plugins/frontenddev/skills/review/scripts/check_preconditions.py:59` dan `:101-107`:

```python
        self.path = path.strip().strip("/")
        ...
        if self.target == "path":
            if not self.path or not (self.root / self.path).exists():
                self._add(1, name, "FAIL", f"path `{self.path or '(kosong)'}` tidak ada",
                          "Sebut direktori fitur atau berkas yang ada di repo.")
                return
            self._add(1, name, "PASS", f"path `{self.path}`")
```

### Masalah

`../` dan symlink yang keluar repo lolos. Path absolut di dalam repo ditolak dengan pesan menyesatkan, karena `strip("/")` mengubah `/tmp/…/repo/src` menjadi `tmp/…/repo/src`. Path absolut di luar repo hanya tertolak kebetulan, dengan alasan yang sama.

### Reproduksi

Skrip gabungan ada di C11. Output aktual bagian C14 (kode `34684ee`):

```
== C14: target path di luar repo
--path ../rahasia            [1] Objek review `path` tersedia     : PASS (path `../rahasia`)
--path /tmp/tmp.tuQ2ftDoXI/repo/src [1] Objek review `path` tersedia     : FAIL (path `tmp/tmp.tuQ2ftDoXI/repo/src` tidak ada)
--path src                   [1] Objek review `path` tersedia     : PASS (path `src`)
--path src/tautan (symlink)  [1] Objek review `path` tersedia     : PASS (path `src/tautan`)
```

Sesudah patch:

```
== C14: target path di luar repo
--path ../rahasia            [1] Objek review `path` tersedia     : FAIL (path `../rahasia` berada di luar repo `/tmp/tmp.ZnhYgniXsD/repo`)
--path /tmp/tmp.ZnhYgniXsD/repo/src [1] Objek review `path` tersedia     : PASS (path `src`)
--path src                   [1] Objek review `path` tersedia     : PASS (path `src`)
--path src/tautan (symlink)  [1] Objek review `path` tersedia     : FAIL (path `src/tautan` berada di luar repo `/tmp/tmp.ZnhYgniXsD/repo`)
```

### Perbaikan

Diff gabungan C11 + C14 (diuji):

```diff
--- a/src/plugins/frontenddev/skills/review/scripts/check_preconditions.py
+++ b/src/plugins/frontenddev/skills/review/scripts/check_preconditions.py
@@ -29,6 +29,7 @@
 sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_common"))
 from precondition_lib import (  # noqa: E402
     TASKDIR_PATTERN,
+    chain_files,
     check_adapter,
     check_plugin_files,
     check_profile,
@@ -56,7 +57,8 @@
         self.root = (root or find_repo_root()).resolve()
         self.target = (target or "").lower()
         self.range = rng.strip()
-        self.path = path.strip().strip("/")
+        self.path_raw = path.strip()
+        self.path = ""
         self.taskdir_rel = normalize_taskdir(taskdir or "")
         self.write = write
         self.profile_dir = self.root / (profile_dir or ".claude/profile")
@@ -64,6 +66,7 @@
         self.results: List[Dict[str, Any]] = []
         self.stack = ""
         self.resolved_range = ""
+        self.chain_files: List[str] = []
 
     def _add(self, cid: int, name: str, status: str, summary: str, action: str = "") -> None:
         self.results.append({"id": cid, "name": name, "status": status,
@@ -99,10 +102,19 @@
             self._add(1, name, "PASS", f"diff `{rng}`")
             return
         if self.target == "path":
-            if not self.path or not (self.root / self.path).exists():
-                self._add(1, name, "FAIL", f"path `{self.path or '(kosong)'}` tidak ada",
+            raw = self.path_raw
+            full = (Path(raw) if Path(raw).is_absolute() else self.root / raw).resolve() if raw else None
+            try:
+                rel = full.relative_to(self.root) if full else None
+            except ValueError:
+                self._add(1, name, "FAIL", f"path `{raw}` berada di luar repo `{self.root}`",
+                          "Review ad-hoc hanya menilai berkas di dalam toplevel git repo ini.")
+                return
+            if rel is None or not full.exists():
+                self._add(1, name, "FAIL", f"path `{raw or '(kosong)'}` tidak ada",
                           "Sebut direktori fitur atau berkas yang ada di repo.")
                 return
+            self.path = rel.as_posix()
             self._add(1, name, "PASS", f"path `{self.path}`")
             return
         taskdir = self.root / self.taskdir_rel
@@ -116,15 +128,26 @@
             return
         sha = task_root_sha(self.root, self.taskdir_rel)
         self.resolved_range = f"{sha[:7]}..HEAD" if sha else ""
-        self._add(1, name, "PASS", f"taskdir tuntas, rentang `{self.resolved_range}`")
+        # Objek = berkas rantai (commit bersubjek `<type>(<slug>):`), sama dengan review penutup
+        # architect — bukan seluruh diff akar..HEAD yang ikut memuat kerja user dan taskdir lain.
+        self.chain_files = chain_files(self.root, self.taskdir_rel)
+        if not self.chain_files:
+            self._add(1, name, "WARN", f"taskdir tuntas, rentang `{self.resolved_range}`, nol berkas rantai",
+                      "Tidak ada kode yang dinilai; sebut ke user sebelum melanjutkan.")
+            return
+        self._add(1, name, "PASS", f"taskdir tuntas, rentang `{self.resolved_range}`, "
+                                   f"{len(self.chain_files)} berkas rantai")
 
     def format_text(self) -> str:
-        return format_report(f"review ({self.target or '-'})", self.results,
-                             {"rentang": self.resolved_range or "-", "tulis": "ya" if self.write else "tidak"})
+        resolved = {"rentang": self.resolved_range or "-", "tulis": "ya" if self.write else "tidak"}
+        if self.target == "taskdir":
+            resolved["berkas"] = "chain.py files --taskdir " + self.taskdir_rel
+        return format_report(f"review ({self.target or '-'})", self.results, resolved)
 
     def to_json(self) -> str:
         return report_json(self.results, root=str(self.root), target=self.target,
                            range=self.resolved_range, path=self.path, write=self.write,
+                           chain_files=self.chain_files,
                            stack=self.stack)
```

Teks pendamping `src/plugins/frontenddev/skills/review/SKILL.md:18` (Precondition butir 2): tambahkan "path di luar repo (termasuk lewat symlink) → minta path di dalam repo".

### Test

`src/plugins/frontenddev/tests/test_review_preconditions.py`:

```python
"""C11 + C14 — skill review: objek taskdir = berkas rantai; target path dibatasi ke repo."""
import json
import os

import pytest

from conftest import TASKDIR, run_script

SCRIPT = "review/scripts/check_preconditions.py"


def check1(proc):
    return next(l for l in proc.stdout.splitlines() if l.startswith("[1]"))


@pytest.fixture
def with_src(repo):
    repo.write("src/a.ts", "a\n")
    repo.commit("chore: awal")
    (repo.root.parent / "rahasia").mkdir()
    return repo


@pytest.mark.parametrize("path", ["../rahasia", "src/tautan"])
def test_path_di_luar_repo_ditolak(with_src, path):
    os.symlink("../../rahasia", with_src.root / "src" / "tautan")
    proc = run_script(SCRIPT, "--root", with_src.root, "--target", "path", "--path", path)
    assert "FAIL" in check1(proc) and "di luar repo" in check1(proc)


@pytest.mark.parametrize("path", ["src", "./src/", "{root}/src"])
def test_path_di_dalam_repo_diterima(with_src, path):
    proc = run_script(SCRIPT, "--root", with_src.root, "--target", "path",
                      "--path", path.format(root=with_src.root))
    assert "PASS (path `src`)" in check1(proc)


def test_target_taskdir_hanya_berkas_rantai(with_src):
    repo = with_src
    repo.write(f"{TASKDIR}/TASK.md", "---\nstatus: ACTIVE\n---\n# Label\n")
    repo.commit("docs(label): kunci TASK sebagai akar rantai")
    repo.write("src/a.ts", "a\nb\n")
    repo.commit("feat(label): implement unit 01 - label")
    repo.write("src/lain.ts", "c\n")
    repo.commit("feat: kerja user di luar rantai")
    repo.write(f"{TASKDIR}/REPORT.md", "# r\n")
    repo.commit("docs(label): report")
    proc = run_script(SCRIPT, "--root", repo.root, "--target", "taskdir", "--taskdir", TASKDIR, "--json")
    assert json.loads(proc.stdout)["chain_files"] == ["src/a.ts"]
```

### Selesai bila

`../`, path absolut di luar repo, dan symlink keluar repo FAIL dengan pesan "di luar repo"; path relatif, `./…/`, dan path absolut di dalam repo PASS dan dinormalkan menjadi path relatif.

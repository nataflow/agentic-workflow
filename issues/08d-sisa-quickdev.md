# Langkah 8d — Sisa Temuan: quickdev (D1–D13)

Versi detail seksi **8.D quickdev** dari `ISSUES.md`. ID dan judul item sama dengan `ISSUES.md`.

- **Path**: semua path di berkas ini relatif **root repo**. Di ISSUES.md 8.D, path relatif `src/plugins/quickdev/`.
- **Nomor baris**: commit `34684ee`, sama dengan ISSUES.md. Semua nomor baris sudah dicek ulang lewat mdcp.
- **Bukti**: quickdev tidak punya skrip, jadi reproduksi di sini dua jenis. Pertama, skrip git yang menjalankan predikat persis seperti tertulis di SKILL. Kedua, uji kerangka `plan_lock.py` usulan. Semua dijalankan di scratchpad sesi ini (git 2.47.3, Python 3.13.5, Claude Code 2.1.281). Output di bawah adalah output nyata; SHA dan path `mktemp` berubah tiap run.
- **Rujukan gate**: teks pengganti di bawah sudah memakai prefix `quickdev:` sesuai L1.3.

## Tujuan

quickdev berjanji "review diff terhadap rencana satu berkas". Janji itu kini hanya ditopang disiplin model. Langkah ini:
1. mengunci rencana secara mekanis (D1);
2. memberi execute jalan masuk ulang dan commit dasar (D2);
3. memindahkan state gate dari percakapan ke berkas rencana (D7);
4. membatasi loop dan cakupan perbaikan (D3, D5, D10);
5. merapikan predikat git, baseline, dan monorepo yang rapuh (D4, D6, D8, D9, D11–D13).

## Urutan pengerjaan

| # | Item | Alasan urutan |
|---|---|---|
| 1 | D8 | Predikat git yang benar (`-uall`, seluruh `plan_dir`, repo tanpa commit) dipakai D1, D2, dan D9. |
| 2 | **D1** | Tinggi. Memperkenalkan format metadata rencana dan `plan_lock.py` (atau pipeline shell) yang menjadi fondasi D2, D3, dan D7. |
| 3 | **D2** | Tinggi. Mode `resume` dan `Base-Commit` memakai blok `## Execution Status` dari D1. |
| 4 | D7 | Gate state, temuan review, dan konfirmasi manual ditulis ke berkas yang sama. |
| 5 | D3 → D5 | Plafon remediasi dan batas cakupan perbaikan. Keduanya sisi execute, bergantung D1/D7. |
| 6 | D4 (+ L3.5) | Template baseline dan aturan pembandingnya. Kerjakan bersama konfirmasi eksekusi L3.5. |
| 7 | D6 → D12 | Profil: workspace/cwd, lalu repo tanpa test runner (kolom Status dari D4). |
| 8 | D9 → D10 → D11 → D13 | Rendah, independen. |

## Dependensi dengan langkah lain

| Item | Terkait | Sifat |
|---|---|---|
| Semua | **L1.3** | Rujukan "gate `profile`/`plan`/`execute`" tanpa prefix membuat model bisa menjalankan `backenddev:*`. Teks pengganti di sini sudah memakai `quickdev:*`. Kerjakan L1.3 sebelum atau bersamaan agar tidak menyunting baris yang sama dua kali. |
| D4 | **L3.5** | L3.5 menambah konfirmasi dan timeout sebelum profile menjalankan test/build. D4 mengubah bentuk tabel hasilnya. Satu PR. |
| D6 | L1.1 opsi A butir 7 | Bila `repo-profile.md` dipindah ke `.claude/profile/quickdev/`, default `profile_path` di 5 SKILL ikut berubah. D6 menambah `Profile:` di metadata rencana, jadi lokasi apa pun tetap terbaca. |
| D1, D2, D3, D7 | L6.1 / L6.2 | Bila `plan_lock.py` diadopsi, test-nya di `tests/quickdev/test_plan_lock.py` memakai fixture `git_repo`/`run_script`/`skill_script` dari `issues/06-test-ci.md`. Matriks 06 (baris "quickdev 0") perlu ditambah. |
| D1 | L6.3 | Check S2 lint (skrip yang dirujuk `${CLAUDE_PLUGIN_ROOT}/skills/…/*.py` di SKILL.md harus ada) otomatis mencakup `plan_lock.py`. |
| D13 | L2.8 (backenddev) | Masalah serupa (gerbang terlalu berat untuk permintaan kecil). Tidak ada konflik berkas. |

## Estimasi usaha

| Item | Estimasi |
|---|---|
| D1 | 1 hari (skrip + 3 SKILL + test) · 0,5 hari bila varian shell |
| D2 | 0,5–1 hari (sesudah D1) |
| D3 | 1–2 jam |
| D4 | 2–3 jam (tanpa L3.5) |
| D5 | 45 menit |
| D6 | 2 jam |
| D7 | 2 jam |
| D8 | 1 jam |
| D9 | 30 menit |
| D10 | 1 jam |
| D11 | 1,5 jam |
| D12 | 45 menit |
| D13 | 1 jam |
| **Total** | **±4,5 hari** (varian `plan_lock.py`) |

## Definisi selesai

- Ke-13 item dicentang, masing-masing sudah memenuhi **Selesai bila**-nya.
- Rencana yang diubah teksnya sesudah APPROVED terdeteksi sebelum execute dan sebelum review, secara mekanis.
- Execute yang terputus bisa dilanjutkan tanpa commit, stash, atau rollback, dan review tetap menilai seluruh kerja sejak `Base-Commit`.
- Semua state yang dibaca gate hilir ada di berkas rencana atau profil, bukan hanya di percakapan.
- Bila `plan_lock.py` diadopsi, `python -m pytest tests/quickdev` hijau (6 test D1/D2/D3/D7 di bawah sudah hijau terhadap kerangka).

## Keputusan yang dibutuhkan user

| Item | Pilihan | Rekomendasi |
|---|---|---|
| D1-a | Mekanisme kunci: **(A)** skrip `skills/_common/plan_lock.py` (Python stdlib) · **(B)** pipeline shell `awk`/`sed`/`sha256sum` di SKILL · **(C)** commit rencana saat approval, lalu review memeriksa `git diff <commit> -- plan_path` | (A). Mekanis, teruji, satu sumber untuk D2/D3/D7. Konsekuensinya quickdev menambah dependensi `python3` (plugin lain sudah mewajibkannya). |
| D1-b | Bila (A) ditolak karena prinsip "tanpa skrip": (B) untuk hash saja, sedangkan resume/remediasi tetap instruksi | (B) sebagai cadangan. |
| D3 | Plafon putaran remediasi | 2 putaran, masing-masing dengan konfirmasi user. |
| D6 | Lokasi profil workspace: `<workspace_dir>/repo-profile.md` atau `.claude/profile/quickdev/<workspace-slug>.md` (ikut L1.1) | Ikut keputusan L1.1. Yang wajib adalah `Profile:` di metadata rencana. |
| D11 | Fullstack: template ketiga, atau template frontend + field `Server-side` | Field `Server-side` (tanpa template ketiga). |

---

## D1 [Tinggi] Rencana "satu berkas" tidak benar-benar terkunci
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 1 hari · **Bergantung pada:** D8, keputusan D1-a · **Memblokir:** D2, D3, D7

### Konteks
Satu-satunya "kunci" rencana adalah baris `Status: APPROVED` yang ditulis model sendiri. Berkas rencana sengaja dibiarkan uncommitted, lalu dimutasi execute (checkbox, blok penutup). Review mengeluarkan `plan_path` dari diff lalu membandingkan kode dengan isi `plan_path` **saat review**. Akibatnya, bila teks langkah diubah sesudah persetujuan, pembandingnya ikut berubah dan tidak ada yang mendeteksinya.

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/plan/SKILL.md:33`: "Buat direktori tujuan `plan_dir` (default: `plan/`) pada root repositori jika direktori tersebut belum ada".
- `plan/SKILL.md:66`: "Metadata blok: `Status: DRAFT`, `Author: quickdev:plan`, `Date: <timestamp>`".
- `plan/SKILL.md:84`: "**Jika user menyatakan persetujuan eksplisit**: Perbarui status di header berkas markdown menjadi `Status: APPROVED`."
- `plan/SKILL.md:89`: "Catat timestamp persetujuan resmi dan pastikan seluruh checklist siap dieksekusi."
- `plan/SKILL.md:99`: "MUST NOT menimpa berkas rencana yang telah berstatus `APPROVED` tanpa instruksi revisi eksplisit dari user."
- `src/plugins/quickdev/skills/execute/SKILL.md:15`: tree harus bersih "selain `plan_path` dan `profile_path`".
- `execute/SKILL.md:54`: "perbarui checkbox langkah terkait di `plan_path` menjadi `- [x]`".
- `execute/SKILL.md:77`: "Tulis blok penutupan di akhir berkas … `Execution Status: …`, `Verification: …`, `Remediation Round: …`, `Timestamp: …`".
- `execute/SKILL.md:89`: "MUST NOT menyimpang dari langkah-langkah yang telah disepakati" (tidak melarang mengubah teks langkah).
- `src/plugins/quickdev/skills/review/SKILL.md:33`: "Keluarkan `plan_path` dan `profile_path` dari daftar karena keduanya artefak gate".
- `review/SKILL.md:40-43`: kontrak dibaca dari `plan_path`, lalu selisih dua arah dihitung.
- `review/SKILL.md:51`: dimensi 2 "Kepatuhan Kontrak Plan … terhadap `plan_path`".

### Reproduksi
Predikat review dijalankan persis seperti tertulis; rencana "dirapikan" sesudah approval:
```bash
tmp=$(mktemp -d); cd "$tmp"; git init -q; git config user.email t@t; git config user.name t
echo a > app.js; echo b > lib.js; echo '# profil' > repo-profile.md; git add -A; git commit -qm init
mkdir plan; cat > plan/t.md <<'MD'
# Implementation Plan — t
Status: APPROVED

## 3. Atomic Implementation Steps
- [ ] 1. Ubah `app.js`: tambah `checkQuota()`
- [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`
MD
cp plan/t.md /tmp/plan-approved.$$        # salinan saat user menyetujui (hanya pembanding di skrip ini)
echo 'a2' >> app.js                                           # execute hanya mengerjakan langkah 1
sed -i 's/- \[ \] 1\./- [x] 1./; /lib\.js/d' plan/t.md        # lalu "merapikan" rencana
echo "--- himpunan berkas review (plan_path & profile_path dikeluarkan, review/SKILL.md:33):"
{ git diff HEAD --name-only; git ls-files --others --exclude-standard; } | grep -vx -e plan/t.md -e repo-profile.md
echo "--- berkas direncanakan menurut plan_path sekarang:"; grep -o '`[a-z]*\.js`' plan/t.md
echo "--- yang disetujui user vs sekarang:"; diff /tmp/plan-approved.$$ plan/t.md; rm -f /tmp/plan-approved.$$
```
Output:
```
--- himpunan berkas review (plan_path & profile_path dikeluarkan, review/SKILL.md:33):
app.js
--- berkas direncanakan menurut plan_path sekarang:
`app.js`
--- yang disetujui user vs sekarang:
5,6c5
< - [ ] 1. Ubah `app.js`: tambah `checkQuota()`
< - [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`
---
> - [x] 1. Ubah `app.js`: tambah `checkQuota()`
```
Selisih dua arah Fase 2 review kosong (berubah = direncanakan = `app.js`), sehingga langkah 2 yang dihapus tidak tercatat sebagai "LANGKAH TERLEWAT". Hanya salinan yang dibuat di luar alur (baris `cp`) yang bisa menunjukkan perubahan itu.

### Dampak
Klaim utama quickdev ("review diff terhadap rencana") bisa batal diam-diam. Model yang "merapikan" rencana agar cocok dengan hasil kerjanya akan lolos review sebagai `REVIEWED`. Persetujuan user juga tidak berjejak: tidak ada kutipan jawaban dan tidak ada sidik.

### Rencana perbaikan

**Format metadata rencana (berlaku untuk varian mana pun).** Baris polos `Kunci: nilai` tepat di bawah H1, sebelum `## 1.` (bukan butir daftar, bukan tebal), sehingga bisa diparse:
```text
# Implementation Plan — <task_name>
Status: DRAFT | APPROVED
Author: quickdev:plan
Date: <ISO>
Profile: <profile_path>                      (D6)
Gates: explore=<EXPLORED|DILEWATI> clarify=<CLARIFIED|SKIPPED>   (D7)
Approved-At: <ISO>                           ← ditulis saat lock
Approval: "<jawaban user apa adanya>"        ← ditulis saat lock
Plan-Hash: sha256:<64 hex>                   ← ditulis saat lock
```
**Cakupan sidik**: dari heading `## 1.` sampai sebelum `## Execution Status` (atau akhir berkas). Normalisasi: CRLF → LF, spasi ujung baris dibuang, dan `- [x]`/`- [X]` dihitung sebagai `- [ ]`. Artinya checkbox dan blok penutup boleh berubah, sedangkan teks Section 1–5 tidak.

**Blok penutup** diberi heading sendiri, **`## Execution Status`**, di akhir berkas, dengan butir `- Kunci: nilai`. Tanpa heading, blok lama (`execute/SKILL.md:77`) jatuh ke dalam Section 5 dan ikut tersidik.

**Varian A (disarankan): `src/plugins/quickdev/skills/_common/plan_lock.py`.** Subperintah yang dijalankan skill:

| Skill | Titik | Perintah |
|---|---|---|
| `quickdev:plan` Fase 3 (persetujuan) | sesudah jawaban eksplisit user | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py lock --plan <plan_dir>/<task_name>.md --answer "<jawaban user apa adanya>" --profile <profile_path>` |
| `quickdev:plan` revisi rencana APPROVED | atas permintaan user | `plan_lock.py unlock --plan <p> --reason "<alasan>"`, lalu revisi, lalu `lock` lagi |
| `quickdev:execute` Fase 0 | sebelum mutasi apa pun | `plan_lock.py start --plan <p> [--findings]` (memanggil `verify` di dalamnya; D2) |
| `quickdev:execute` Fase 4 | penutupan | `plan_lock.py close --plan <p> --status <COMPLETED\|BLOCKED\|VERIFICATION_MANUAL_REQUIRED> --verification "<ringkas>" [--blocked-step <n>]` |
| `quickdev:review` Fase 1 | sebelum membaca diff | `plan_lock.py verify --plan <p>` lalu `plan_lock.py status --plan <p> --json` (ambil `Base-Commit`, D2/D9) |

Kerangka lengkap (sudah dijalankan; 6 test di bawah hijau):
```python
#!/usr/bin/env python3
"""Kunci rencana quickdev: sidik Section 1–5, blok `## Execution Status`, dan commit dasar.

- `lock`    DRAFT → APPROVED: tulis `Approved-At`, `Approval`, `Plan-Hash`, `Profile`.
- `verify`  APPROVED dan sidik Section 1–5 sekarang = `Plan-Hash` (checkbox dinormalkan).
- `start`   vonis mode eksekusi (awal | resume | remediasi | manual | selesai); tulis blok
            `## Execution Status` (IN_PROGRESS + Base-Commit) bila belum ada.
- `close`   tulis status terminal execute ke blok (COMPLETED | BLOCKED | VERIFICATION_MANUAL_REQUIRED).
- `confirm` VERIFICATION_MANUAL_REQUIRED → COMPLETED (manual) dengan jawaban user apa adanya.
- `status`  ringkasan untuk execute/review (`--json`).
- `unlock`  APPROVED → DRAFT untuk revisi atas permintaan user; blok eksekusi dipertahankan.

Zero external dependencies (Python Standard Library only).
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

EXEC_H2 = "## Execution Status"
STEP = re.compile(r"^\s*- \[([ xX])\]\s*(.*)$")
META = re.compile(r"^([A-Z][A-Za-z-]+): ?(.*)$")
ITEM = re.compile(r"^- ([A-Z][A-Za-z-]+): ?(.*)$")
REMEDIATION_CAP = 2


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def quote(v: str) -> str:
    return '"' + " ".join(v.replace('"', "'").split())[:300] + '"'


def head_commit(cwd: Path) -> str:
    r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--verify", "-q", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "none"


class Plan:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")

    def _first(self, pred) -> int:
        return next((i for i, l in enumerate(self.lines) if pred(l)), len(self.lines))

    @property
    def body_start(self) -> int:          # heading `## 1.` pertama
        return self._first(lambda l: l.startswith("## 1."))

    @property
    def exec_start(self) -> int:
        return self._first(lambda l: l.strip() == EXEC_H2)

    def meta(self) -> dict:
        return {m.group(1): m.group(2) for m in (META.match(l) for l in self.lines[:self.body_start]) if m}

    def block(self) -> dict:
        return {m.group(1): m.group(2) for m in (ITEM.match(l) for l in self.lines[self.exec_start + 1:]) if m}

    def steps(self) -> list:
        s3 = self._first(lambda l: l.startswith("## 3."))
        end = next((i for i in range(s3 + 1, len(self.lines)) if self.lines[i].startswith("## ")), len(self.lines))
        return [(m.group(1) != " ", m.group(2)) for m in (STEP.match(l) for l in self.lines[s3 + 1:end]) if m]

    def digest(self) -> str:
        region = self.lines[self.body_start:self.exec_start]
        norm = [STEP.sub(lambda m: m.group(0).replace(f"[{m.group(1)}]", "[ ]", 1), l).rstrip() for l in region]
        return "sha256:" + hashlib.sha256("\n".join(norm).strip().encode("utf-8")).hexdigest()

    def set_meta(self, **kv: str) -> None:
        for key, val in kv.items():
            key = key.replace("_", "-")
            idx = next((i for i in range(self.body_start) if self.lines[i].startswith(f"{key}:")), None)
            if idx is None:
                last = max((i for i in range(self.body_start) if META.match(self.lines[i])), default=0)
                self.lines.insert(last + 1, f"{key}: {val}")
            else:
                self.lines[idx] = f"{key}: {val}"

    def set_block(self, **kv: str) -> None:
        while self.lines and not self.lines[-1].strip():
            self.lines.pop()
        if self.exec_start == len(self.lines):
            self.lines += ["", EXEC_H2]
        for key, val in kv.items():
            key = key.replace("_", "-")
            idx = next((i for i in range(self.exec_start + 1, len(self.lines))
                        if self.lines[i].startswith(f"- {key}:")), None)
            if idx is None:
                self.lines.append(f"- {key}: {val}")
            else:
                self.lines[idx] = f"- {key}: {val}"

    def save(self) -> None:
        self.path.write_text("\n".join(self.lines).rstrip("\n") + "\n", encoding="utf-8")


def fail(msg: str) -> int:
    print(msg)
    return 1


def cmd_lock(p: Plan, a) -> int:
    if p.meta().get("Status") != "DRAFT":
        return fail(f"LOCK FAIL: Status `{p.meta().get('Status', '-')}` bukan DRAFT")
    if not a.answer.strip():
        return fail("LOCK FAIL: jawaban user kosong")
    if not p.steps():
        return fail("LOCK FAIL: Section 3 tanpa langkah checkbox `- [ ]`")
    p.set_meta(Status="APPROVED", Approved_At=now(), Approval=quote(a.answer), Plan_Hash=p.digest(),
               Profile=a.profile)
    p.save()
    print(f"LOCK PASS: {p.path} APPROVED @{p.digest()[7:19]}")
    return 0


def cmd_verify(p: Plan, a) -> int:
    m = p.meta()
    if m.get("Status") != "APPROVED":
        return fail(f"VERIFY FAIL: Status `{m.get('Status', '-')}` bukan APPROVED")
    if m.get("Plan-Hash") != p.digest():
        return fail(f"VERIFY FAIL: Section 1–5 berubah sesudah APPROVED (tercatat {m.get('Plan-Hash', '-')[7:19]}, "
                    f"sekarang {p.digest()[7:19]}) — pulihkan teksnya, atau `unlock` lalu approval ulang di quickdev:plan")
    print(f"VERIFY PASS: {p.path} @{p.digest()[7:19]}")
    return 0


def cmd_start(p: Plan, a) -> int:
    if cmd_verify(p, a):
        return 1
    b, steps = p.block(), p.steps()
    done = sum(1 for ok, _ in steps if ok)
    st = b.get("Status", "")
    rnd = int(b.get("Remediation-Round", "0") or 0)
    if a.findings:
        if st != "COMPLETED":
            return fail(f"START FAIL: remediasi menuntut Status COMPLETED, tercatat `{st or '-'}`")
        if rnd >= REMEDIATION_CAP:
            return fail(f"START FAIL: plafon {REMEDIATION_CAP} putaran remediasi habis — serahkan temuan ke user")
        mode = "remediasi"
        p.set_block(Status="IN_PROGRESS", Remediation_Round=str(rnd + 1), Timestamp=now())
    elif st == "VERIFICATION_MANUAL_REQUIRED":
        mode = "manual"
    elif st.startswith("COMPLETED"):
        mode = "selesai"
    elif st in ("IN_PROGRESS", "BLOCKED") or done:
        mode = "resume"
        if not b.get("Base-Commit"):
            p.set_block(Base_Commit=head_commit(p.path.parent), Base_Note="tidak tercatat sebelum sesi putus")
        p.set_block(Status="IN_PROGRESS", Timestamp=now())
    else:
        mode = "awal"
        p.set_block(Status="IN_PROGRESS", Base_Commit=head_commit(p.path.parent), Remediation_Round="0",
                    Timestamp=now())
    p.save()
    nxt = next((t for ok, t in steps if not ok), "-")
    print(f"START PASS: mode={mode} · langkah {done}/{len(steps)} · berikutnya: {nxt} · "
          f"base={p.block().get('Base-Commit', '-')[:12]}")
    return 0


def cmd_close(p: Plan, a) -> int:
    if a.status == "COMPLETED" and any(not ok for ok, _ in p.steps()):
        return fail("CLOSE FAIL: COMPLETED dengan langkah `- [ ]` tersisa")
    p.set_block(Status=a.status, Verification=quote(a.verification), Blocked_Step=a.blocked_step or "-",
                Timestamp=now())
    p.save()
    print(f"CLOSE PASS: {a.status}")
    return 0


def cmd_confirm(p: Plan, a) -> int:
    if p.block().get("Status") != "VERIFICATION_MANUAL_REQUIRED":
        return fail("CONFIRM FAIL: blok bukan VERIFICATION_MANUAL_REQUIRED")
    p.set_block(Status="COMPLETED (manual)", Manual_Confirmation=quote(a.answer), Timestamp=now())
    p.save()
    print("CONFIRM PASS: COMPLETED (manual)")
    return 0


def cmd_unlock(p: Plan, a) -> int:
    if p.meta().get("Status") != "APPROVED":
        return fail("UNLOCK FAIL: bukan APPROVED")
    p.set_meta(Status="DRAFT", Plan_Hash="-", Unlock_Reason=quote(a.reason))
    p.save()
    print("UNLOCK PASS: DRAFT — blok Execution Status dipertahankan")
    return 0


def cmd_status(p: Plan, a) -> int:
    m, b, steps = p.meta(), p.block(), p.steps()
    out = {"status": m.get("Status", "-"), "hash_ok": m.get("Plan-Hash") == p.digest(),
           "profile": m.get("Profile", "-"), "steps_done": sum(ok for ok, _ in steps), "steps_total": len(steps),
           "next_step": next((t for ok, t in steps if not ok), "-"), "execution": b}
    print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else
          f"STATUS: {out['status']} · hash {'ok' if out['hash_ok'] else 'DRIFT'} · langkah "
          f"{out['steps_done']}/{out['steps_total']} · eksekusi {b.get('Status', '-')} · base {b.get('Base-Commit', '-')}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Kunci rencana quickdev")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("lock", "verify", "start", "close", "confirm", "status", "unlock"):
        s = sub.add_parser(name)
        s.add_argument("--plan", required=True)
        if name in ("lock", "confirm"):
            s.add_argument("--answer", required=True)
        if name == "lock":
            s.add_argument("--profile", default="repo-profile.md")
        if name == "start":
            s.add_argument("--findings", action="store_true", help="putaran remediasi dari review CHANGES_REQUIRED")
        if name == "close":
            s.add_argument("--status", required=True, choices=("COMPLETED", "BLOCKED", "VERIFICATION_MANUAL_REQUIRED"))
            s.add_argument("--verification", required=True)
            s.add_argument("--blocked-step", default="")
        if name == "unlock":
            s.add_argument("--reason", required=True)
        if name == "status":
            s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    path = Path(a.plan)
    if not path.is_file():
        sys.exit(f"FAIL: {path} tidak ada")
    sys.exit(globals()[f"cmd_{a.cmd}"](Plan(path), a))


if __name__ == "__main__":
    main()
```
Uji kerangka end-to-end (rencana 2 langkah; `PL` = path skrip):
```bash
$PL lock --plan plan/t.md --answer "setuju, lanjut"
$PL start --plan plan/t.md
sed -i 's/- \[ \] 1\./- [x] 1./' plan/t.md; echo a2 >> app.js           # langkah 1 dikerjakan
$PL verify --plan plan/t.md                                             # checkbox bukan drift
sed -i 's/tambah `checkQuota()`/tambah `checkQuota()` dan `logQuota()`/' plan/t.md   # "merapikan" rencana
$PL verify --plan plan/t.md; echo "exit=$?"
sed -i 's/ dan `logQuota()`//' plan/t.md
$PL start --plan plan/t.md                                              # sesi baru → resume
$PL close --plan plan/t.md --status COMPLETED --verification "npm test PASS"; echo "exit=$?"
```
```
LOCK PASS: plan/t.md APPROVED @0c8baf9c21e8
VERIFY PASS: plan/t.md @0c8baf9c21e8
START PASS: mode=awal · langkah 0/2 · berikutnya: 1. Ubah `app.js`: tambah `checkQuota()` · base=c8248009590d
VERIFY PASS: plan/t.md @0c8baf9c21e8
VERIFY FAIL: Section 1–5 berubah sesudah APPROVED (tercatat 0c8baf9c21e8, sekarang 0792f7863851) — pulihkan teksnya, atau `unlock` lalu approval ulang di quickdev:plan
exit=1
VERIFY PASS: plan/t.md @0c8baf9c21e8
START PASS: mode=resume · langkah 1/2 · berikutnya: 2. Ubah `lib.js`: ekspor `QUOTA_MAX` · base=c8248009590d
CLOSE FAIL: COMPLETED dengan langkah `- [ ]` tersisa
exit=1
```

**Varian B (cadangan tanpa Python): pipeline shell** yang ditulis sama persis di plan, execute, dan review. Blank line diabaikan; portabel ke macOS (`shasum`).
```bash
planhash() { awk '/^## 1\./{f=1} /^## Execution Status[[:space:]]*$/{f=0} f' "$1" | tr -d '\r' \
  | sed -E 's/^([[:space:]]*)- \[[xX]\]/\1- [ ]/; s/[[:space:]]+$//' | grep -v '^$' \
  | { sha256sum 2>/dev/null || shasum -a 256; } | cut -c1-64; }
```
Uji: sidik awal, lalu sesudah checkbox dicentang dan blok penutup ditambah, lalu sesudah teks langkah diubah:
```
awal=f5c83a387645 sesudah-checkbox+blok=f5c83a387645 sesudah-ubah-teks=f15c1221fa58
```
Varian B hanya mengunci teks. Mode resume (D2), plafon (D3), dan konfirmasi manual (D7) kembali menjadi instruksi.

**Varian C: commit rencana saat approval** (`git add <plan_path> && git commit -m "docs(plan): approve <task_name>"`). Review lalu menuntut `git diff <commit> -- <plan_path>` hanya berisi baris checkbox dan blok penutup. Kelemahannya: skill jadi menulis ke riwayat git user (termasuk di `main`), bertentangan dengan semangat "MUST NOT commit" execute (`execute/SKILL.md:91`), dan tidak jalan di repo tanpa commit awal.

**Teks pengganti (varian A)**
1. `plan/SKILL.md:66` diganti: "Metadata: baris polos `Kunci: nilai` tepat di bawah H1 (tanpa butir/tebal): `Status: DRAFT`, `Author: quickdev:plan`, `Date: <ISO>`, `Profile: <profile_path>`, `Gates: explore=<…> clarify=<…>`. Baris `Approved-At`, `Approval`, `Plan-Hash` hanya ditulis `plan_lock.py lock`."
2. `plan/SKILL.md:84` diganti: "**Jika user menyatakan persetujuan eksplisit**: jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py lock --plan <plan_dir>/<task_name>.md --answer \"<jawaban user apa adanya>\" --profile <profile_path>`. `LOCK FAIL` → perbaiki sebabnya; dilarang menulis `Status: APPROVED` dengan tangan."
3. `plan/SKILL.md:89` diganti: "Pastikan keluaran `LOCK PASS` memuat sidik; `Approved-At` dan `Approval` sudah ditulis skrip."
4. `plan/SKILL.md:99` diganti: "MUST NOT mengubah Section 1–5 berkas `APPROVED`. Revisi atas permintaan user: `plan_lock.py unlock --reason \"…\"` → revisi → approval ulang (`lock`). Blok `## Execution Status` dipertahankan apa adanya."
5. `execute/SKILL.md:14` (Precondition 1) diganti: "`python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py verify --plan <plan_path>` → `VERIFY PASS`. `FAIL` (bukan APPROVED, atau Section 1–5 berubah sesudah disetujui) → hentikan, arahkan ke `quickdev:plan`."
6. `execute/SKILL.md:54`: tambahkan "Hanya baris checkbox Section 3 dan blok `## Execution Status` yang boleh diubah di `plan_path`; teks langkah, Section 1, 2, 4, 5, dan metadata dilarang disentuh."
7. `execute/SKILL.md:77` diganti: "Tutup lewat `plan_lock.py close --plan <plan_path> --status <status> --verification \"<ringkasan>\" [--blocked-step <n>]`. Skrip menulis/menimpa blok `## Execution Status` dan menolak `COMPLETED` bila masih ada `- [ ]`."
8. `execute/SKILL.md:89`: tambahkan "… termasuk mengubah teks langkah agar cocok dengan hasil kerja."
9. `review/SKILL.md:14` (Precondition 1) diganti: "`plan_lock.py verify --plan <plan_path>` → PASS, **dan** `plan_lock.py status --plan <plan_path> --json` → `execution.Status` ∈ {`COMPLETED`, `COMPLETED (manual)`}. Selain itu hentikan dan kembalikan ke `quickdev:execute`."
10. `review/SKILL.md:40`: tambahkan "Kontrak = isi `plan_path` yang lolos `verify` (sidik = yang disetujui user; kutipan persetujuan di baris `Approval:`)."

### Test yang ditambahkan / Verifikasi manual
`tests/quickdev/test_plan_lock.py` (fixture L6.1; hijau terhadap kerangka di atas). Kepala dan test D1:
```python
"""Regresi D1/D2/D3/D7 — kunci rencana quickdev (`skills/_common/plan_lock.py`)."""
import pytest

from conftest import skill_script

PL = skill_script("quickdev", "_common", "plan_lock.py")
PLAN = """# Implementation Plan — t
Status: DRAFT
Author: quickdev:plan
Date: 2026-09-24T10:00:00+07:00

## 1. Overview & Objectives
Tambah validasi kuota.

## 3. Atomic Implementation Steps
- [ ] 1. Ubah `app.js`: tambah `checkQuota()`
- [ ] 2. Ubah `lib.js`: ekspor `QUOTA_MAX`

## 4. Verification & Testing Strategy
- `npm test`
"""


@pytest.fixture
def repo(git_repo):
    git_repo.write("plan/t.md", PLAN)
    return git_repo


@pytest.fixture
def pl(repo, run_script):
    return lambda *a: run_script(PL, *a, "--plan", "plan/t.md", cwd=repo.path)


def tick(repo, *ns):
    p = repo.path / "plan/t.md"
    text = p.read_text()
    for n in ns:
        text = text.replace(f"- [ ] {n}.", f"- [x] {n}.")
    p.write_text(text)


def test_d1_checkbox_bukan_drift_teks_langkah_drift(repo, pl):
    assert pl("lock", "--answer", "setuju").code == 0
    tick(repo, 1)
    assert pl("verify").code == 0
    p = repo.path / "plan/t.md"
    p.write_text(p.read_text().replace("tambah `checkQuota()`", "tambah `checkQuota()` dan `logQuota()`"))
    r = pl("verify")
    assert r.code == 1 and "berubah sesudah APPROVED" in r.out


def test_d1_lock_menolak_jawaban_kosong_dan_non_draft(pl):
    assert pl("lock", "--answer", " ").code == 1
    assert pl("lock", "--answer", "ok").code == 0
    assert pl("lock", "--answer", "ok").code == 1
```
Hasil nyata (`AW_REPO=<salinan> python -m pytest tests/quickdev`, 6 test termasuk D2/D3/D7): `6 passed in 0.98s`.

Verifikasi manual: jalankan alur quickdev pada repo contoh. Sesudah approval, minta model menghapus satu langkah dari rencana lalu jalankan `quickdev:review`. Review harus berhenti di Precondition 1 dengan `VERIFY FAIL`.

### Selesai bila
- Persetujuan menghasilkan `Plan-Hash` dan `Approval` di metadata lewat skrip.
- Execute dan review menolak rencana yang Section 1–5-nya berubah sesudah persetujuan.
- Checkbox dan blok `## Execution Status` tidak dihitung perubahan.
- Test D1 hijau.

### Risiko & catatan
- Rencana lama (sebelum format baru) tidak punya `Plan-Hash`, sehingga `verify` FAIL. Beri jalur migrasi: `Status: APPROVED` tanpa `Plan-Hash` → minta user menyetujui ulang (set `DRAFT` lalu `lock`).
- Model tetap bisa mengubah rencana **dan** memanggil `unlock` + `lock` sendiri. `lock` menuntut `--answer`, dan baris `Approval:`/`Unlock-Reason:` tercatat di berkas. Ini bukti audit, bukan pencegahan mutlak. Pencegahan penuh butuh hook PreToolUse (lihat L3.4).
- `quickdev` bertambah dependensi `python3`. Tambahkan ke README/Precondition skill.

---

## D2 [Tinggi] execute tidak punya jalan masuk ulang sesudah BLOCKED atau sesi putus
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 0,5–1 hari · **Bergantung pada:** D1 (blok `## Execution Status`, `plan_lock.py start`), D8 · **Memblokir:** D7, D9

### Konteks
Execute hanya mengenal dua pintu. Putaran awal mensyaratkan tree bersih. Putaran remediasi mensyaratkan `review_findings`. Eksekusi yang berhenti di tengah (BLOCKED, `stop_on_error`, sesi putus, atau limit API) meninggalkan perubahan uncommitted tanpa `review_findings`, sehingga tidak masuk pintu mana pun. Padahal Output menjanjikan user bisa memilih "lanjut perbaiki".

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/execute/SKILL.md:15`: "pada putaran awal (`review_findings` kosong) keluarannya tidak memuat perubahan selain `plan_path` dan `profile_path` — perubahan lain wajib di-commit atau di-stash user lebih dulu …; pada putaran remediasi, perubahan uncommitted hasil putaran sebelumnya memang diharapkan dan `plan_path` wajib sudah memuat blok `Execution Status`."
- `execute/SKILL.md:55`: "… hentikan loop, pertahankan checklist terakhir di `plan_path`, dan set status `BLOCKED` beserta langkah penyebabnya."
- `execute/SKILL.md:104`: "`BLOCKED` tidak membuka `review` — user memilih lanjut perbaiki, revisi rencana di gate `plan`, atau rollback."
- `execute/SKILL.md:121-124` (Failure path 2): sesudah `max_fix_iterations`, status `BLOCKED` dan tawarkan rollback.
- `review/SKILL.md:16,33`: diff dihitung terhadap `HEAD` (`git diff HEAD`).
- `plan/SKILL.md:83`: revisi = "Perbarui dokumen `<plan_dir>/<task_name>.md` sesuai feedback". Tidak ada ketentuan mempertahankan blok `Execution Status`.

### Reproduksi
```bash
tmp=$(mktemp -d); cd "$tmp"; git init -q; git config user.email t@t; git config user.name t
echo 'a' > app.js; echo 'b' > lib.js; echo '# profil' > repo-profile.md; git add -A; git commit -qm init
BASE=$(git rev-parse --short HEAD)
mkdir plan; cat > plan/t.md <<'MD'
# Implementation Plan — t
Status: APPROVED

## 3. Atomic Implementation Steps
- [x] 1. Ubah `app.js`
- [ ] 2. Ubah `lib.js`
MD
echo 'a2' >> app.js                      # langkah 1 selesai, lalu sesi putus
echo "--- predikat putaran awal (harus kosong selain plan/profil):"
git status --porcelain -uall | grep -v -e ' plan/' -e 'repo-profile.md'
echo "--- user meng-commit kerja parsial agar tree 'bersih', langkah 2 dikerjakan belakangan:"
git add app.js && git commit -qm wip && echo 'b2' >> lib.js
echo "diff HEAD   :" $(git diff HEAD --name-only)
echo "diff $BASE:" $(git diff "$BASE" --name-only)
```
Output:
```
--- predikat putaran awal (harus kosong selain plan/profil):
 M app.js
--- user meng-commit kerja parsial agar tree 'bersih', langkah 2 dikerjakan belakangan:
diff HEAD   : lib.js
diff 18a69b3: app.js lib.js
```
Putaran awal tertolak (` M app.js`), dan putaran remediasi juga tertolak (tidak ada `review_findings`). Bila user meng-commit supaya "bersih", review yang memakai `git diff HEAD` kehilangan `app.js`, sehingga langkah 1 tercatat "LANGKAH TERLEWAT". Stash sama dengan rollback. Hanya diff terhadap commit dasar (`18a69b3`) yang melihat seluruh kerja.

### Dampak
Setiap interupsi memaksa rollback atau pelanggaran precondition. Kerja yang sudah benar dibuang, atau model "menyiasati" precondition tanpa jejak. Revisi rencana sesudah BLOCKED (Failure path 5) dapat menulis ulang berkas utuh dan menghapus blok `Execution Status`.

### Rencana perbaikan — mode `resume`

**Syarat masuk** (divonis `plan_lock.py start`, tanpa parameter baru; mode diturunkan dari berkas):

| Keadaan `plan_path` | Mode | Keterangan |
|---|---|---|
| `verify` FAIL | — | hentikan, ke `quickdev:plan` (D1) |
| tanpa blok `## Execution Status`, nol `[x]` | `awal` | predikat tree bersih (D8) berlaku; tulis `Status: IN_PROGRESS`, `Base-Commit: <HEAD atau none>` |
| blok `IN_PROGRESS`/`BLOCKED`, **atau** tanpa blok tetapi ada `[x]` (sesi putus sebelum blok pernah ditulis) | `resume` | perubahan uncommitted diizinkan; `Base-Commit` dipertahankan (atau diisi HEAD dengan `Base-Note` bila belum pernah tercatat) |
| blok `COMPLETED` + dipanggil dengan `review_findings` (`--findings`) | `remediasi` | plafon D3 |
| blok `VERIFICATION_MANUAL_REQUIRED` | `manual` | konfirmasi user (D7) |
| blok `COMPLETED`/`COMPLETED (manual)` tanpa temuan | `selesai` | tidak ada kerja; arahkan ke `quickdev:review` |

**Langkah mode `resume`** (execute Fase 0 butir baru dan Fase 1):
1. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/plan_lock.py start --plan <plan_path>` → `START PASS: mode=resume · langkah n/m · berikutnya: <teks> · base=<sha>`.
2. Pagar tree: `git status --porcelain -uall` (D8). Setiap berkas berubah wajib termasuk berkas target Section 3, `plan_dir/`, atau `profile_path`. Berkas lain berarti hentikan dan tanyakan user (jangan ikut di-review sebagai hasil eksekusi).
3. Periksa langkah `[x]` terakhir. Berkas targetnya wajib berubah terhadap base (`git diff --stat <Base-Commit> -- <berkas>`, atau `git ls-files --others` untuk berkas baru). Bila tidak berubah, centangnya tidak sah: kembalikan ke `[ ]` dan catat di laporan.
4. Lanjutkan loop Fase 1 dari langkah `[ ]` pertama. Sebelum mengedit, baca ulang berkas target karena langkah bisa setengah jadi. Edit harus idempoten: jangan menambah blok yang sudah ada.
5. Fase 2–4 seperti biasa. Penutupan lewat `plan_lock.py close`. `Base-Commit` tidak pernah ditimpa.
6. Revisi rencana sesudah `BLOCKED` (Failure path 5): `plan_lock.py unlock` → `quickdev:plan` merevisi Section 1–5 **tanpa menyentuh** blok `## Execution Status` → `lock` → `quickdev:execute` masuk `resume`. Langkah `[x]` yang teksnya tidak berubah tetap `[x]`.

**Output** (`execute/SKILL.md:107`): `EXECUTE: <plan_path> — putaran <awal | resume dari langkah n/m | remediasi ke-n | manual>`, ditambah baris `BASE: <Base-Commit>`.

**Review memakai base** (juga D9): diff = `git diff <Base-Commit>` + untracked; `Base-Commit: none` berarti diff terhadap tree kosong (D8).

**Teks pengganti**
1. `execute/SKILL.md:15` (Precondition 2) diganti:
   "Mode dari `plan_lock.py start` (tabel mode di README quickdev). `awal`: `git status --porcelain -uall` tidak memuat perubahan di luar `<plan_dir>/` dan `profile_path`. `resume`/`remediasi`: perubahan uncommitted diizinkan hanya pada berkas target Section 3, `<plan_dir>/`, dan `profile_path`; berkas lain → hentikan dan tanyakan user. Dilarang meminta user meng-commit atau men-stash kerja parsial: review membandingkan terhadap `Base-Commit`, bukan `HEAD`."
2. `execute/SKILL.md:55`: tambahkan "… lalu `plan_lock.py close --status BLOCKED --blocked-step <n>`. Kerja parsial dibiarkan di working tree; pemanggilan `quickdev:execute` berikutnya masuk mode `resume`."
3. `execute/SKILL.md:104` diganti: "… `BLOCKED` tidak membuka `review` — user memilih: lanjut (panggil `quickdev:execute` lagi → mode `resume`), revisi rencana (`quickdev:plan`; blok `## Execution Status` dipertahankan), atau rollback (hanya atas perintah eksplisit user)."
4. `plan/SKILL.md:83`: tambahkan "Rencana yang sudah memuat `## Execution Status`: revisi hanya Section 1–5 lewat Edit terarah; blok itu dan checkbox langkah yang teksnya tidak berubah dipertahankan."
5. `review/SKILL.md:16,26,33,34`: ganti `git diff HEAD` menjadi `git diff <Base-Commit>` (dari `plan_lock.py status --json`, `execution.Base-Commit`), dengan fallback `HEAD` bila blok belum ada.

### Test yang ditambahkan / Verifikasi manual
```python
def test_d2_resume_sesudah_sesi_putus(repo, pl):
    pl("lock", "--answer", "ok")
    base = repo.git("rev-parse", "HEAD")
    assert "mode=awal" in pl("start").out
    tick(repo, 1)
    r = pl("start")
    assert "mode=resume" in r.out and "berikutnya: 2. Ubah `lib.js`" in r.out
    assert f"- Base-Commit: {base}" in (repo.path / "plan/t.md").read_text()


def test_d2_close_completed_menolak_langkah_terbuka(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1)
    assert pl("close", "--status", "COMPLETED", "--verification", "x").code == 1
```
Verifikasi manual: di tengah execute rencana 3 langkah, hentikan sesi sesudah langkah 1. Buka sesi baru dan panggil `/quickdev:execute plan_path=plan/x.md`. Model masuk `resume`, mengerjakan langkah 2–3 tanpa meminta commit/stash, dan review menilai ketiga berkas.

### Selesai bila
- Keenam baris tabel mode ditangani skrip dan SKILL.
- Execute yang terputus dapat dilanjutkan tanpa commit/stash.
- Review membandingkan terhadap `Base-Commit`.
- Revisi rencana mempertahankan blok eksekusi.
- Kedua test hijau.

### Risiko & catatan
- `Base-Commit` yang diisi saat `resume` pertama (kasus "tanpa blok tetapi ada `[x]`") menunjuk HEAD sesudah interupsi. Bila user sempat meng-commit kerja parsial sebelum itu, kerja tersebut tidak terlihat oleh review. `Base-Note` menandai kasus ini, dan review harus menyebutnya di ringkasan.
- Tanpa varian A (D1-b), tabel mode ditulis sebagai instruksi di Fase 0 execute, dengan `Base-Commit` ditulis manual via `git rev-parse HEAD`.

---

## D3 [Sedang] Loop review ↔ execute tanpa batas dan tanpa persetujuan user
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 1–2 jam · **Bergantung pada:** D1, D2 (`plan_lock.py start --findings`), D7 (temuan tersimpan) · **Memblokir:** —

### Konteks
`CHANGES_REQUIRED` langsung diserahkan ke execute, yang lalu mengubah kode lagi. Tidak ada persetujuan baru dan tidak ada plafon. `Remediation Round` hanya dicatat. Reviewer adalah konteks percakapan yang sama dengan pelaksana, sehingga rawan bias konfirmasi.

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/review/SKILL.md:75`: "Bila status `CHANGES_REQUIRED`, serahkan daftar temuan ke gate `execute` lewat parameter `review_findings` (dengan `plan_path` yang sama) untuk remediasi; dilarang memperbaiki sendiri di sesi review."
- `src/plugins/quickdev/skills/execute/SKILL.md:29`: `review_findings` — "Bila terisi, skill berjalan pada putaran remediasi".
- `execute/SKILL.md:77`: "`Remediation Round: <0 | n>`". Hanya dicatat; tidak ada batas di SKILL mana pun (md_search "Remediation" di quickdev: hanya :77 dan Output :107/:110).

### Reproduksi
Tidak ada skrip. Jejak alurnya: review (:73) memvonis `CHANGES_REQUIRED` bila ada satu MAJOR. Lalu :75 menyerahkan ke execute. Execute Fase 0 butir 4 (:42–44) mengerjakan temuan tanpa `AskUserQuestion`. Lalu :84 kembali ke review, dan seterusnya. Tidak ada predikat berhenti selain "nol BLOCKER/MAJOR".

### Dampak
Temuan yang bolak-balik (perbaikan A memunculkan temuan B) menghabiskan konteks tanpa batas dan mengubah kode tanpa sepengetahuan user. User kehilangan titik keputusan "terima dengan catatan" atau "revisi rencana".

### Rencana perbaikan
1. **Plafon 2 putaran remediasi**, ditegakkan `plan_lock.py start --findings`. Skrip menolak bila `Remediation-Round` sudah 2 (`REMEDIATION_CAP`, lihat D1).
2. **Persetujuan per putaran** di sisi review (review tetap read-only). `review/SKILL.md:75` diganti:
   "Bila status `CHANGES_REQUIRED`: sajikan temuan, lalu `AskUserQuestion`: *Remediasi otomatis (putaran <n+1>/2)* · *Revisi rencana (`quickdev:plan`)* · *Terima apa adanya — keputusan commit di tangan user*. Opsi pertama tidak ditawarkan bila `Remediation-Round` (dari `plan_lock.py status --json`) sudah 2. Hanya opsi pertama yang memanggil `quickdev:execute` dengan `review_findings` dan `plan_path` yang sama; jawaban user dikutip apa adanya di laporan."
3. `execute/SKILL.md:29` diganti: "`review_findings` — … Bila terisi: hanya sesudah user memilih *Remediasi otomatis* di `quickdev:review`; Fase 0 menjalankan `plan_lock.py start --plan <plan_path> --findings` (plafon 2 putaran). `START FAIL` plafon → jangan mengubah kode; serahkan temuan tersisa ke user."
4. `execute/SKILL.md:77`: `Remediation-Round` ditulis skrip (`start --findings`), bukan tangan.
5. Independensi (mitigasi, bukan mekanis): tambahkan di `review/SKILL.md` Fase 1 butir 1 "Bila review dijalankan di sesi yang sama dengan execute, nyatakan di ringkasan (`MODE: … sesi-sama=ya`) dan sarankan user menjalankan ulang `/quickdev:review` di sesi baru untuk putaran terakhir."

### Test yang ditambahkan / Verifikasi manual
```python
def test_d3_plafon_remediasi(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    for _ in range(2):
        assert pl("close", "--status", "COMPLETED", "--verification", "ok").code == 0
        assert pl("start", "--findings").code == 0
    pl("close", "--status", "COMPLETED", "--verification", "ok")
    r = pl("start", "--findings")
    assert r.code == 1 and "plafon 2 putaran" in r.out
```
Verifikasi manual: review menghasilkan `CHANGES_REQUIRED`. Model harus menampilkan `AskUserQuestion` tiga opsi dan tidak memanggil execute sebelum user memilih. Pada putaran ketiga, opsi remediasi tidak muncul.

### Selesai bila
- Tiap putaran remediasi didahului pilihan user.
- Putaran ke-3 ditolak skrip dan tidak ditawarkan review.
- Test hijau.

### Risiko & catatan
Angka 2 adalah keputusan user (tabel keputusan). Plafon ini terpisah dari `max_fix_iterations` (perbaikan mandiri di dalam satu putaran verifikasi, `execute/SKILL.md:28`).

---

## D4 [Sedang] Data baseline yang dibutuhkan execute tidak disediakan template
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 2–3 jam (tanpa L3.5) · **Bergantung pada:** L3.5 (satu PR) · **Memblokir:** D12

### Konteks
Profile wajib mencatat baseline issues dan status `UNVERIFIED_ENV_NOT_READY`. Execute membandingkan hasil verifikasi dengan "baseline" itu. Tetapi Section 5 kedua template hanya berisi baris perintah, tanpa status, tanpa daftar issue bawaan, dan tanpa aturan untuk perintah yang belum pernah terverifikasi.

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/profile/SKILL.md:75-76`: "Catat status eksekusi (`PASSED` atau `FAILED`; `SKIPPED` …) beserta durasi …" dan "Tangkap baseline issues eksisting … dokumentasikan secara transparan pada profil agar tidak menjadi false positive saat regresi di gate implementasi."
- `profile/SKILL.md:127`: Output `ISSUE BAWAAN: <ringkasan error/warning baseline eksisting | ->`; `:131`: nilai status termasuk `UNVERIFIED_ENV_NOT_READY`.
- `profile/SKILL.md:136` (Failure path 2): "catat status `UNVERIFIED_ENV_NOT_READY` pada seksi baseline profil".
- `src/plugins/quickdev/skills/profile/references/backend-profile-template.md:49-56`:
  ```text
  ## 5. Verification Baseline

  Perintah pengujian dan audit kualitas kode yang wajib dijalankan sebelum dan sesudah perubahan:

  - **Typecheck**: `<perintah: misal pnpm tsc --noEmit / mypy src>`
  - **Linter**: `<perintah: misal pnpm lint / ruff check . / golangci-lint run>`
  - **Unit & Integration Tests**: `<perintah: misal pnpm test / pytest / go test ./...>`
  - **Build / Bundle Check**: `<perintah: misal pnpm build / go build ./...>`
  ```
  `frontend-profile-template.md:47-54` memuat bentuk yang sama.
- `src/plugins/quickdev/skills/execute/SKILL.md:70-71`: "Bandingkan hasil dengan baseline bawaan di `profile_path`: Error baru di luar baseline: diagnosa dan perbaiki …"

### Reproduksi
Statis: template tidak punya tempat untuk status, durasi, maupun daftar issue. Konsekuensinya, `profile/SKILL.md:85` ("Wajib menyertakan keenam section header template terpilih dengan teks heading persis") dan `:76` saling tarik: data baseline harus ditulis di luar bentuk template, atau hilang.

### Dampak
- Execute tidak bisa membedakan error lama dan regresi, sehingga salah satu dari dua hal terjadi: "memperbaiki" error lama di luar cakupan (lihat D5), atau menyatakan regresi sebagai bawaan.
- Perintah `UNVERIFIED_ENV_NOT_READY`/`SKIPPED` dijalankan pertama kali di execute tanpa aturan tafsir.

### Rencana perbaikan
1. **Template** (kedua berkas), Section 5 diganti tabel. Heading tetap, jadi `profile/SKILL.md:85` terpenuhi:
   ```text
   ## 5. Verification Baseline

   Dijalankan dari root repo kecuali kolom Cwd menyebut lain (D6). Status: PASSED | FAILED | SKIPPED | UNVERIFIED_ENV_NOT_READY | TIDAK_ADA (D12).

   | Jenis | Perintah | Cwd | Status | Durasi | Known issues (baseline) |
   |---|---|---|---|---|---|
   | Typecheck | `<perintah>` | `.` | <status> | <detik> | `<berkas:baris kode/aturan>` per issue, atau `-` |
   | Linter | `<perintah>` | `.` | <status> | <detik> | … |
   | Test | `<perintah>` | `.` | <status> | <detik> | `<nama test gagal/skip>` per issue |
   | Build | `<perintah>` | `.` | <status> | <detik> | … |
   ```
   Known issues memakai **penanda persis** (mis. `src/legacy/a.ts:12 no-explicit-any`, `test_order_refund`), maksimal 10 baris. Bila lebih, tulis `<n> issue — contoh: …` beserta perintah untuk mereproduksi daftar lengkap.
2. `profile/SKILL.md:75-76` diganti: "Tulis hasil tiap perintah ke tabel Section 5 template: Status, Durasi, dan Known issues dengan penanda persis. `UNVERIFIED_ENV_NOT_READY` beserta pesan penyebab satu baris masuk kolom Known issues." (L3.5 menambah konfirmasi dan timeout sebelum eksekusi, di butir yang sama.)
3. `execute/SKILL.md:70-71` diganti dengan aturan per status:
   ```text
   2. Bandingkan per perintah dengan baris Section 5 `profile_path`:
      - PASSED → galat apa pun sekarang = regresi.
      - FAILED → galat yang penandanya ada di Known issues = bawaan; galat lain = regresi.
      - SKIPPED / UNVERIFIED_ENV_NOT_READY → jalankan sekarang. Gagal karena lingkungan (modul/binari hilang) → status akhir
        `VERIFICATION_MANUAL_REQUIRED`, bukan COMPLETED. Jalan tetapi gagal → tidak ada pembanding: laporkan tiap galat
        di berkas yang disentuh rencana sebagai regresi, sisanya sebagai `UNVERIFIED` di laporan, lalu minta user memutuskan.
      - TIDAK_ADA → lewati, catat `<jenis>=TIDAK_ADA` (D12).
      Regresi: perbaiki di tempat hingga `max_fix_iterations` dalam batas D5; bila masih gagal → Failure path 2.
   ```
4. `execute/SKILL.md:112` (Output): `VERIFIKASI: typecheck=<status> lint=<status> test=<status> build=<status>`; status boleh `bawaan(n)` untuk issue lama yang masih ada.

### Test yang ditambahkan / Verifikasi manual
Tanpa skrip, tidak ada test otomatis. Opsional: bila L6.3 menambah check template, tuntut heading kolom `| Jenis | Perintah | Cwd | Status | Durasi | Known issues (baseline) |` di kedua template.

Verifikasi manual:
1. Jalankan `quickdev:profile` di repo dengan 2 warning lint lama. Profil memuat baris Linter `FAILED` beserta kedua penanda.
2. Rencana yang menyentuh berkas lain berakhir `COMPLETED` dengan `lint=bawaan(2)`, tanpa perbaikan di berkas lama.

### Selesai bila
- Kedua template memuat tabel.
- Profile mengisinya.
- Execute memakai aturan per status di atas.
- Verifikasi manual lolos.

### Risiko & catatan
Profil lama (tanpa tabel) harus dibaca sebagai "status tidak diketahui", yaitu diperlakukan seperti `UNVERIFIED`. Tambahkan kalimat itu di execute dan sarankan `quickdev:profile mode=REFRESH`.

---

## D5 [Sedang] Perbaikan saat verifikasi tanpa batas cakupan
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 45 menit · **Bergantung pada:** D1/D2 (`close --status BLOCKED`, `unlock`) · **Memblokir:** —

### Konteks
Iron Law melarang perubahan di luar cakupan rencana. Loop perbaikan verifikasi menyuruh "perbaiki di tempat" tanpa batas berkas. Regresi di modul konsumen (misalnya pemanggil fungsi yang signature-nya berubah) memaksa model memilih antara melanggar Iron Law atau `BLOCKED`, dan keduanya tidak didefinisikan untuk kasus ini.

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/execute/SKILL.md:10` (Iron Law): "… TANPA MENAMBAHKAN PERUBAHAN DI LUAR CAKUPAN."
- `execute/SKILL.md:71`: "Error baru di luar baseline: diagnosa dan perbaiki di tempat hingga `max_fix_iterations`; bila masih gagal, alihkan ke Failure path 2."
- `execute/SKILL.md:123` (Failure path 2): "Terapkan perbaikan terarah pada baris kode yang bermasalah."
- Aturan cakupan hanya ada untuk temuan review (`:43`, Failure path 5 `:127`), tidak untuk galat verifikasi.

### Reproduksi
Statis. Contoh: langkah rencana mengubah signature `calcTotal(a)` → `calcTotal(a, b)` di `src/order/service.ts`, lalu typecheck gagal di `src/report/summary.ts:40` yang tidak tercantum di Section 3. Kalimat :71 menyuruh memperbaiki `summary.ts`, sedangkan :10 melarangnya.

### Dampak
Model cenderung "memperbaiki di tempat" (lebih cepat), sehingga lahir scope creep yang lalu dilaporkan review sebagai temuan (dimensi 2), atau lolos bila rencana juga "dirapikan" (D1). Review terhadap `plan_path` jadi tidak bermakna.

### Rencana perbaikan
1. `execute/SKILL.md:71` diganti:
   "Error baru di luar baseline (D4): perbaiki hanya bila perbaikannya berada di berkas target Section 3 (termasuk berkas test yang tercantum di sana), hingga `max_fix_iterations`. Perbaikan yang menuntut berkas di luar Section 3 → hentikan loop, `plan_lock.py close --status BLOCKED --blocked-step <n> --verification \"<perintah>: <galat> di <berkas:baris> (di luar rencana)\"`, dan laporkan ke user. Jalan lanjutnya revisi lewat `quickdev:plan` (`unlock` → tambah langkah → `lock`) lalu `quickdev:execute` mode `resume` (D2)."
2. `execute/SKILL.md:123`: tambahkan "… pada baris kode yang bermasalah **di berkas target Section 3**; di luar itu → butir 1 di atas."
3. Iron Law :10: tambahkan "Perbaikan galat verifikasi tunduk pada batas yang sama."
4. Output `:113`: `REGRESI BARU: <n> | - — di luar rencana: <daftar berkas> | -`.

### Test yang ditambahkan / Verifikasi manual
Verifikasi manual dengan skenario di Reproduksi. Execute harus berakhir `BLOCKED` beserta `Blocked-Step` dan daftar berkas di luar rencana, tanpa perubahan di `summary.ts`. Sesudah revisi rencana (langkah baru untuk `summary.ts`), `resume` mengerjakannya dan review tidak mencatat scope creep.

### Selesai bila
- Ketiga teks diganti.
- Skenario manual berakhir `BLOCKED` tanpa sentuhan di luar Section 3.
- Jalur revisi → `resume` terbukti.

### Risiko & catatan
Rencana yang terlalu sempit akan lebih sering BLOCKED. Ini sengaja: explore (dimensi dampak, `explore/SKILL.md:75-76`) seharusnya sudah menemukan konsumen. Cara mengurangi frekuensinya: plan Fase 1 menambah satu langkah "sesuaikan konsumen" bila explore melaporkan modul konsumen terdampak.

---

## D6 [Sedang] Monorepo tidak tahan lintas sesi
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 2 jam · **Bergantung pada:** D1 (metadata `Profile:`), D4 (kolom Cwd), keputusan L1.1 · **Memblokir:** —

### Konteks
Profil dibuat per workspace dengan `target_path` berbeda. Satu-satunya jalur yang membawa `target_path` itu ke gate hilir adalah percakapan ("diteruskan sebagai `profile_path`"). Kelima skill hilir default ke `repo-profile.md` di root. Perintah baseline juga dicatat tanpa direktori kerja, padahal execute menjalankannya "persis seperti tercatat".

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/profile/SKILL.md:25`: "`workspace_dir` … satu workspace per profil, dengan `target_path` berbeda per workspace yang diteruskan sebagai `profile_path` ke gate hilir."
- `profile/SKILL.md:45`: "Profil dibuat per workspace: bila `workspace_dir` kosong, tanyakan workspace target … lalu jadikan direktorinya root pemindaian Fase 1–2."
- `src/plugins/quickdev/skills/explore/SKILL.md:26`: "`profile_path` … default `\"repo-profile.md\"` — path profil hasil gate `profile` (samakan dengan `target_path` di sana)". Parameter serupa ada di `plan/SKILL.md:24`, `execute/SKILL.md:23`, `review/SKILL.md:23`, dan `clarify/SKILL.md:23`.
- `src/plugins/quickdev/skills/execute/SKILL.md:65`: "jalankan perintah baseline persis seperti tercatat di `profile_path` (dan Section 4 rencana) secara sequential".
- Template Section 5 (`backend-profile-template.md:53-56`, `frontend-profile-template.md:51-54`) tidak punya kolom direktori kerja. Section 1 tidak punya field workspace.

### Reproduksi
Statis. Alurnya:
1. Sesi 1: `quickdev:profile workspace_dir=apps/api target_path=apps/api/repo-profile.md` mencatat `pnpm test`. Perintah itu dijalankan dari `apps/api` pada Fase 2, tetapi cwd-nya tidak ditulis.
2. Sesi 2: `/quickdev:execute plan_path=plan/x.md`. `profile_path` default `repo-profile.md` tidak ada, dan fallback `.dev/profile.md` juga tidak ada, sehingga Precondition 4 menghentikan dan mengarahkan ke `profile`.
3. Bila user menyebut path profil, `pnpm test` dijalankan dari root. Hasilnya script root atau "missing script". Tidak ada yang menyebut cwd.

### Dampak
Profil monorepo praktis tidak terpakai di sesi berikutnya, atau perintah baseline dijalankan di direktori yang salah sehingga verifikasi palsu (hijau karena menjalankan test paket lain, atau merah karena script tidak ada).

### Rencana perbaikan
1. **Template** Section 1 (kedua berkas): tambah baris `- **Workspace**: \`<workspace_dir | . (root)>\``. Section 5 memakai kolom `Cwd` (D4).
2. `profile/SKILL.md:25` diganti: "`workspace_dir` — … default `target_path` untuk workspace: `<workspace_dir>/repo-profile.md` (atau lokasi L1.1). Workspace dan cwd tiap perintah dicatat di profil (Section 1 `Workspace`, Section 5 `Cwd`), bukan hanya di percakapan."
3. `plan/SKILL.md:66`: metadata `Profile: <profile_path>` (lihat D1). `plan_lock.py lock --profile` menulisnya.
4. `execute/SKILL.md:23` dan `review/SKILL.md:23` diganti: "`profile_path` — default: nilai `Profile:` di metadata `plan_path`; bila absen, `repo-profile.md`, lalu `.dev/profile.md`."
5. `explore/SKILL.md:26` dan `clarify/SKILL.md:23` diganti: "… default `repo-profile.md`. Bila repo memuat lebih dari satu profil (`**/repo-profile.md`, `git ls-files`), tanyakan workspace mana lewat `AskUserQuestion`, jangan memakai root diam-diam."
6. `execute/SKILL.md:65` diganti: "jalankan tiap perintah baseline dari kolom `Cwd` Section 5 profil, sebagai `(cd <Cwd> && <perintah>)` dari root repo; `Cwd` kosong (profil lama) → root, dan catat `cwd tidak tercatat` di laporan."

### Test yang ditambahkan / Verifikasi manual
Bila `plan_lock.py` diadopsi, tambah test:
```python
def test_d6_profile_tercatat_di_metadata(repo, run_script):
    repo.write("plan/t.md", PLAN)
    run_script(PL, "lock", "--plan", "plan/t.md", "--answer", "ok", "--profile", "apps/api/repo-profile.md", cwd=repo.path)
    assert run_script(PL, "status", "--plan", "plan/t.md", "--json", cwd=repo.path).json()["profile"] == "apps/api/repo-profile.md"
```
(Belum dijalankan. Perilakunya sudah tercakup kerangka: `lock --profile` menulis `Profile:`, dan `status` membacanya.)

Verifikasi manual: monorepo `apps/api` + `apps/web`. Buat profil `apps/api`, rencana, lalu sesi baru untuk execute. Execute harus membaca profil dari metadata dan menjalankan `pnpm test` dari `apps/api`.

### Selesai bila
- Workspace dan cwd tercatat di profil.
- `Profile:` tercatat di rencana.
- Execute/review membaca profil dari metadata.
- Explore/clarify bertanya bila ada lebih dari satu profil.
- Skenario manual lolos.

### Risiko & catatan
Bila L1.1 memindahkan profil ke `.claude/profile/quickdev/`, butir 2 ikut. `Profile:` di metadata membuat lokasi mana pun tetap terbaca.

---

## D7 [Sedang] State gate hanya hidup di percakapan
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 2 jam · **Bergantung pada:** D1, D2 · **Memblokir:** D3 (temuan tersimpan)

### Konteks
Empat state yang dipakai gate hilir tidak pernah ditulis ke berkas:
- status `EXPLORED`/`CLARIFIED`;
- `task_spec`;
- konfirmasi manual untuk `VERIFICATION_MANUAL_REQUIRED`;
- `review_findings`.

Sesudah sesi berganti, gate hilir harus menebak atau mengulang.

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/plan/SKILL.md:14` (Precondition 1): "Gate `explore` dan `clarify` telah selesai dengan status `EXPLORED` dan `CLARIFIED` (atau `SKIPPED`)." Status itu hanya ada di Output percakapan (`explore/SKILL.md:117`, `clarify/SKILL.md:106`).
- `plan/SKILL.md:22`: "`task_spec` … bila tidak dikirim, ambil dari laporan `explore` dan spesifikasi `clarify` terakhir di percakapan."
- `plan/SKILL.md:124-127` (Failure path): tidak ada jalur bila explore/clarify belum dijalankan atau laporannya tidak ada di percakapan.
- `src/plugins/quickdev/skills/review/SKILL.md:14`: "… atau `VERIFICATION_MANUAL_REQUIRED` yang hasil perintah manualnya sudah dikonfirmasi lolos oleh user". Konfirmasi itu tidak ditulis siapa pun.
- `review/SKILL.md:90`: "Skill ini menghasilkan laporan terminal saja tanpa artefak berkas." `review/SKILL.md:75` menyerahkan temuan lewat parameter `review_findings`, yang hanya hidup di percakapan (`execute/SKILL.md:29`).

### Reproduksi
Statis. Contoh sesi baru yang langsung memanggil `/quickdev:plan task_name=x`: Precondition 1 tidak bisa diverifikasi karena tidak ada berkas yang memuat `EXPLORED`. Model menebak "sudah" atau "belum", dan tidak ada failure path. Contoh lain: sesi baru `/quickdev:review` sesudah user menjalankan test manual. Precondition 1 menuntut konfirmasi yang tidak tercatat di mana pun.

### Dampak
Gerbang plan dan review bergantung pada ingatan sesi. Temuan review hilang bila remediasi dimulai di sesi baru, sehingga execute tidak punya daftar kerja atau mengarangnya.

### Rencana perbaikan
1. **Gate hulu → metadata rencana.**
   - `plan/SKILL.md:14` diganti: "Status explore/clarify dibaca dari percakapan atau dari user. Plan menuliskannya ke metadata `Gates: explore=<EXPLORED|DILEWATI> clarify=<CLARIFIED|SKIPPED|DILEWATI>`. `DILEWATI` hanya atas pilihan eksplisit user dan disebut di Fase 3."
   - Section 1 (sudah memuat "keputusan terkunci dari `clarify`", `:67`) menjadi satu-satunya sumber `task_spec` untuk execute/review.
2. **Failure path baru plan** (sesudah :127): "5. **Explore/clarify tidak ada di percakapan**: tanyakan lewat `AskUserQuestion`: *Jalankan `quickdev:explore` dulu (disarankan)* · *Lanjut tanpa explore — saya sebutkan berkas targetnya* · *Batal*. Opsi kedua menulis `Gates: explore=DILEWATI`."
3. **Temuan review → blok eksekusi.** Review tetap read-only. Execute yang memulai putaran remediasi menulis temuan yang diterimanya ke blok `## Execution Status` sebelum mengubah kode: `- Findings-<n>: "<ID> <berkas:baris> — <rekomendasi>; …"`. Perluasan kerangka D1: `start --findings --findings-text "<…>"` menulis `Findings-<n>` (belum ada di kerangka; tambahkan satu baris `p.set_block(**{f"Findings_{rnd + 1}": quote(a.findings_text)})`). Teks pengganti `execute/SKILL.md:42` (Fase 0 butir 4): "Bila `review_findings` terisi: `plan_lock.py start --plan <plan_path> --findings --findings-text \"<temuan ringkas>\"` sebelum mutasi apa pun."
4. **Konfirmasi manual → blok eksekusi.** `plan_lock.py confirm --plan <p> --answer "<jawaban user>"` menulis `Status: COMPLETED (manual)` dan `Manual-Confirmation`. Siapa yang menjalankannya: `quickdev:execute` mode `manual` (D2), yang menanyakan hasil perintah manual lewat `AskUserQuestion` lalu `confirm`. Review tidak menulis apa pun.
   - `review/SKILL.md:14` diganti: "… `execution.Status` ∈ {`COMPLETED`, `COMPLETED (manual)`} (dari `plan_lock.py status --json`); `VERIFICATION_MANUAL_REQUIRED` → kembalikan ke `quickdev:execute` untuk mencatat konfirmasi user."
   - `execute/SKILL.md:104`: "`VERIFICATION_MANUAL_REQUIRED` menahan `review` sampai user menjalankan perintah manual dan `quickdev:execute` (mode `manual`) mencatat konfirmasinya."

### Test yang ditambahkan / Verifikasi manual
```python
def test_d7_konfirmasi_manual_tercatat(repo, pl):
    pl("lock", "--answer", "ok"), pl("start")
    tick(repo, 1, 2)
    pl("close", "--status", "VERIFICATION_MANUAL_REQUIRED", "--verification", "test manual")
    assert "mode=manual" in pl("start").out
    assert pl("confirm", "--answer", "sudah jalan, hijau").code == 0
    assert "- Status: COMPLETED (manual)" in (repo.path / "plan/t.md").read_text()
```
Tambahkan `test_d7_findings_tersimpan` sesudah `--findings-text` diimplementasikan: `start --findings --findings-text "R1 app.js:3 — cek null"` ditulis ke blok sebagai `- Findings-1: "R1 app.js:3 — cek null"`.

Verifikasi manual:
1. Sesi baru `/quickdev:plan` tanpa explore menampilkan Failure path 5.
2. Sesi baru `/quickdev:review` sesudah verifikasi manual ditolak sampai execute mencatat konfirmasi.

### Selesai bila
- `Gates:`, `Findings-<n>`, dan `Manual-Confirmation` tertulis di berkas rencana.
- Plan punya Failure path 5.
- Review dan execute membaca state dari berkas.
- Test D7 hijau.

### Risiko & catatan
`Findings-<n>` bisa panjang. Batasi dengan `quote()` (300 karakter) dan rujuk laporan review untuk rinciannya. Bila detail temuan penting lintas sesi, pertimbangkan review menulis `<plan_dir>/<task>.review.md`. Itu mengubah prinsip "review tanpa artefak" (`review/SKILL.md:90`) dan butuh keputusan user; tidak diusulkan di sini.

---

## D8 [Rendah] Predikat git literal
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 1 jam · **Bergantung pada:** — · **Memblokir:** D1, D2, D9

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/execute/SKILL.md:15`: "`git status --porcelain`: … keluarannya tidak memuat perubahan selain `plan_path` dan `profile_path`".
- `src/plugins/quickdev/skills/review/SKILL.md:16,33`: `git diff HEAD --name-only` / `--name-status` + `git ls-files --others --exclude-standard`; "Keluarkan `plan_path` dan `profile_path` dari daftar".

### Masalah
Reproduksi:
```bash
tmp=$(mktemp -d); cd "$tmp"; git init -q; git config user.email t@t; git config user.name t
echo 'x' > app.js; echo '# profil' > repo-profile.md; git add -A; git commit -qm init
mkdir plan; printf 'Status: APPROVED\n' > plan/t.md
echo "--- porcelain:"; git status --porcelain
echo "--- porcelain -uall:"; git status --porcelain -uall
printf 'Status: APPROVED\n' > plan/lama.md
echo "--- porcelain -uall (dua rencana):"; git status --porcelain -uall
echo 'y' >> app.js
echo "--- himpunan review (tanpa plan_path & profile_path):"
{ git diff HEAD --name-only; git ls-files --others --exclude-standard; } | grep -vx -e plan/t.md -e repo-profile.md
t2=$(mktemp -d); cd "$t2"; git init -q; echo a > a.js; git add a.js
echo "--- git diff HEAD di repo tanpa commit:"; git diff HEAD --name-only; echo "exit=$?"
echo "--- pengganti: diff terhadap tree kosong:"; git diff --cached --name-only "$(git hash-object -t tree /dev/null)"; echo "exit=$?"
```
Output:
```
--- porcelain:
?? plan/
--- porcelain -uall:
?? plan/t.md
--- porcelain -uall (dua rencana):
?? plan/lama.md
?? plan/t.md
--- himpunan review (tanpa plan_path & profile_path):
app.js
plan/lama.md
--- git diff HEAD di repo tanpa commit:
fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
exit=128
--- pengganti: diff terhadap tree kosong:
a.js
exit=0
```
Tiga kegagalan:
1. `?? plan/` tidak cocok secara literal dengan `plan/t.md`, sehingga execute pertama kali di repo mana pun bisa tertolak.
2. Rencana lama yang uncommitted memblokir execute dan terhitung scope creep di review.
3. Repo tanpa commit langsung `fatal`.

### Perbaikan
1. `execute/SKILL.md:15`: `git status --porcelain -uall` dan kecualikan **seluruh** `<plan_dir>/` beserta `profile_path` (lihat teks D2 butir 1).
2. `review/SKILL.md:33`: "Keluarkan seluruh berkas di bawah `<plan_dir>/` dan `profile_path` dari daftar."
3. Repo tanpa commit (`git rev-parse --verify -q HEAD` kosong): `Base-Commit: none` (ditulis `plan_lock.py start`). Review lalu memakai `EMPTY=$(git hash-object -t tree /dev/null)`, `git diff --cached --name-status $EMPTY` (berkas yang sudah di-add) + `git ls-files --others --exclude-standard`. Tambahkan kalimat ini di `review/SKILL.md:16` dan `:34`.
4. `review/SKILL.md:121` (Failure path 2): ganti "working tree bersih" menjadi predikat dengan pengecualian `<plan_dir>/` yang sama.

### Test
Tanpa skrip, verifikasi dengan skrip Reproduksi di atas: sesudah perbaikan, perintah yang tertulis di SKILL menghasilkan himpunan `app.js` saja dan tidak `fatal` di repo tanpa commit. Bila `plan_lock.py` diadopsi, `start` di repo tanpa commit menulis `Base-Commit: none` (tambahkan fixture `empty_git_repo` dari 06).

### Selesai bila
Ketiga kasus di Reproduksi memberi hasil benar dengan perintah persis dari SKILL yang baru.

---

## D9 [Rendah] Instruksi mati di review
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 30 menit · **Bergantung pada:** D2 (`Base-Commit`) · **Memblokir:** —

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/review/SKILL.md:121` (Failure path 2): "laporkan status `NO_CHANGES` beserta kemungkinan penyebab (perubahan sudah ter-commit sehingga review perlu menargetkan rentang commit)".
- `review/SKILL.md:21-26` (Parameter): hanya `plan_path`, `profile_path`, `scope_paths`, `strict`, `include_staged`. Tidak ada base/range.

### Masalah
Failure path menyarankan hal yang tidak bisa dilakukan skill. User yang sudah meng-commit hasil execute tidak punya cara me-review-nya.

### Perbaikan
1. Parameter baru (sesudah `:26`):
   ```text
   - `base_ref` — string — default `""` — commit pembanding. Kosong → `Base-Commit` blok `## Execution Status` `plan_path` (D2); blok absen → `HEAD`. Terisi → diff = `git diff <base_ref>` (committed + uncommitted sejak base) + untracked; wajib resolve (`git rev-parse --verify <base_ref>^{commit}`), bila gagal hentikan.
   ```
2. `review/SKILL.md:121` diganti: "… laporkan `NO_CHANGES`; bila `git log <Base-Commit>..HEAD` tidak kosong, perubahan sudah ter-commit → ulangi dengan `base_ref=<Base-Commit>` (atau commit yang disebut user)."
3. Fase 1 butir 2–3 (`:33-34`) dan Output `:105` (`REVIEW: <task-name> — <base_ref>..working tree`) memakai base yang sama.

### Test
Verifikasi manual: execute selesai, lalu user commit, lalu `/quickdev:review`. Tanpa `base_ref`, `Base-Commit` dari blok dipakai otomatis dan diff memuat berkas yang sudah di-commit. Dengan `base_ref=HEAD` hasilnya `NO_CHANGES` beserta saran di atas.

### Selesai bila
Parameter `base_ref` ada dan divalidasi, Failure path 2 menunjuk jalur yang benar-benar ada, dan diff memakai `Base-Commit` bila tersedia.

---

## D10 [Rendah] Kontradiksi dan instruksi mati di clarify
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 1 jam · **Bergantung pada:** D7 (Failure path plan) · **Memblokir:** —

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/clarify/SKILL.md:24`: "`skip_if_clear` — boolean — default `true` — bila `true`, langsung mengalirkan status `SKIPPED` …". Tidak ada perilaku yang didefinisikan untuk `false`.
- `clarify/SKILL.md:10` (Iron Law): "BILA SELURUH KEBUTUHAN TELAH JELAS … SKILL WAJIB MENGAMBIL JALUR CEPAT (FAST-PATH SKIP)".
- `clarify/SKILL.md:91` (Guardrail): "MUST NOT mengajukan pertanyaan klarifikasi jika seluruh kebutuhan sudah terdefinisi pasti … (wajib Fast-Path Skip)".
- `clarify/SKILL.md:120` (FP1): "simpan status draf klarifikasi". Tidak disebut di mana; clarify tidak menulis berkas apa pun.
- `clarify/SKILL.md:68`: sisa ambiguitas "sebagai batch berikutnya", tanpa plafon batch.
- `clarify/SKILL.md:122` (FP3 → kembali ke explore) dan `plan/SKILL.md:126` (FP3 → kembali ke clarify): tanpa plafon putaran.

### Masalah
`skip_if_clear=false` tidak bisa dijalankan karena Iron Law dan guardrail mewajibkan fast-path. FP1 menyuruh menyimpan sesuatu tanpa lokasi. Loop explore ↔ clarify ↔ plan bisa berputar tanpa titik keputusan user.

### Perbaikan
1. `clarify/SKILL.md:24` diganti: "`skip_if_clear` — default `true`. `false` → meski tanpa ambiguitas, sajikan ringkasan spesifikasi terkunci sebagai **satu** `AskUserQuestion` (*Spesifikasi benar* · *Ada koreksi (sebut)*) sebelum `SKIPPED`."
2. Iron Law `:10` dan guardrail `:91`: tambahkan "… kecuali `skip_if_clear: false` (satu konfirmasi ringkasan, bukan pertanyaan basa-basi)."
3. `clarify/SKILL.md:120` (FP1) diganti: "… jangan menulis berkas. Sajikan blok `CLARIFY — TERTAHAN` di Output: keputusan yang sudah terkunci, pertanyaan tersisa beserta opsi, dan fallback konvensi profil. Sesi berikutnya melanjutkan dari blok itu (atau dari Section 1 rencana bila plan sudah berjalan)."
4. Plafon: `:68` → "maksimal 3 batch per pemanggilan"; `:122` → "kembali ke `quickdev:explore` maksimal satu kali per tugas"; `plan/SKILL.md:126` → "kembali ke `quickdev:clarify` maksimal satu kali". Bila plafon habis: `AskUserQuestion` *Lanjut dengan asumsi tertulis di Section 1* · *Perkecil lingkup* · *Batal*.

### Test
Verifikasi manual:
1. `/quickdev:clarify skip_if_clear=false` pada kebutuhan yang jelas menghasilkan tepat satu pertanyaan konfirmasi.
2. Ambiguitas yang tak kunjung selesai berhenti sesudah batch ke-3 dengan tiga opsi di atas.

### Selesai bila
`skip_if_clear=false` punya perilaku terdefinisi dan tidak bertentangan dengan Iron Law; FP1 tidak lagi menyuruh menyimpan tanpa lokasi; ketiga plafon tertulis.

---

## D11 [Rendah] Fullstack tidak selaras
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 1,5 jam · **Bergantung pada:** keputusan D11 · **Memblokir:** —

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/profile/SKILL.md:123` (Output): `TIPE: <backend | frontend> — sumber <parameter type | deteksi manifes>`. Hanya ada dua template (`:82-83`).
- `profile/SKILL.md:45`: fullstack/monorepo diprofilkan **per workspace**, lalu tiap workspace diklasifikasikan backend atau frontend.
- `src/plugins/quickdev/skills/clarify/SKILL.md:63-64`: "**Cabang Dinamis C — Fullstack / Monorepo** … integrasi boundary antara API contract backend dan data demand komponen UI".
- `src/plugins/quickdev/skills/explore/SKILL.md:33`: "Identifikasi jenis arsitektur proyek (Backend, Frontend, atau Fullstack)".
- Aplikasi satu paket (Next.js API routes/route handlers, SvelteKit `+server.ts`, Remix loaders) tidak punya aturan pemutus. `profile/SKILL.md:43` mengklasifikasikan `next` dan `svelte` sebagai frontend.

### Masalah
Clarify dan explore mengharapkan tipe "Fullstack" yang tidak pernah dihasilkan profile. Di app satu paket, sisi server (validasi, status code, akses DB) tidak masuk template frontend, sehingga clarify cabang C dan dimensi layer review tidak punya acuan.

### Perbaikan (rekomendasi, tanpa template ketiga)
1. `frontend-profile-template.md` Section 4 (Routing & Navigation Architecture, `:39`): tambah baris `- **Server-side**: \`<pola path route server: app/api/**/route.ts | src/routes/**/+server.ts | … | tidak ada>\` — <konvensi validasi & error singkat>`.
2. `profile/SKILL.md:45`: tambah "App satu paket dengan route server (Next route handlers/API routes, SvelteKit `+server`, Remix loader/action) → TIPE `frontend` dan isi `Server-side`; bukan monorepo." Output `:123` diganti: `TIPE: <backend | frontend> — server-side <ya: pola | tidak>`.
3. `explore/SKILL.md:33` diganti: "Identifikasi jenis dari profil: `backend`, `frontend`, atau fullstack (= `frontend` dengan `Server-side` ≠ `tidak ada`, atau beberapa profil workspace, D6)."
4. `clarify/SKILL.md:63` diganti: "**Cabang Dinamis C — Fullstack**: dipakai bila berkas target explore mencakup pola `Server-side` **dan** berkas UI, atau lebih dari satu workspace. Gabungkan pertanyaan cabang A untuk sisi server dan cabang B untuk sisi UI, maksimal `batch_limit`."

### Test
Verifikasi manual: profilkan repo Next.js dengan `app/api/orders/route.ts`, lalu pastikan `Server-side` terisi dan TIPE `frontend`. Permintaan yang menyentuh form dan route handler harus memicu clarify cabang C.

### Selesai bila
Profile menghasilkan informasi server-side yang dipakai explore/clarify; tidak ada lagi tipe "Fullstack" yang dirujuk tanpa sumber.

---

## D12 [Rendah] Repo tanpa infrastruktur test
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 45 menit · **Bergantung pada:** D4 (status `TIDAK_ADA`) · **Memblokir:** —

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/plan/SKILL.md:25`: "`require_test_plan` — boolean — default `true` — bila `true`, Section 4 wajib memuat skenario test unit/integration beserta langkah test di Section 3".
- `src/plugins/quickdev/skills/execute/SKILL.md:68`: "**Perintah 3 — Unit & Integration Tests** … test baru dan eksisting berstatus `PASSED`."
- `execute/SKILL.md:90`: "MUST NOT membiarkan ada … failing test yang belum terselesaikan sebelum menyatakan tugas selesai."
- `src/plugins/quickdev/skills/profile/SKILL.md:77`: "Dilarang mencatat perintah verifikasi rekaan". Untuk repo tanpa runner tidak ada status yang tepat (hanya `PASSED`/`FAILED`/`SKIPPED`/`UNVERIFIED_ENV_NOT_READY`, `:131`).

### Masalah
Di repo tanpa test runner, default `true` memaksa rencana memuat langkah test, dan execute menuntut test `PASSED`. Jalan pintas yang tersisa bagi model adalah menambah framework test (dependensi baru, konfigurasi) di luar kebutuhan user.

### Perbaikan
1. Status baru `TIDAK_ADA` di profil (Section 5, D4): runner test tidak ditemukan di manifest/konfigurasi. Tambahkan ke `profile/SKILL.md:75` dan daftar nilai `:131`.
2. `plan/SKILL.md:25` diganti: "`require_test_plan` — default `true`, **kecuali** baris Test profil berstatus `TIDAK_ADA` → default `false` dan Section 4 menulis `Tests: repo tanpa test runner — verifikasi: typecheck/lint/build tercatat + langkah QA manual`. Menambah framework test hanya sebagai langkah rencana eksplisit yang disetujui user."
3. `execute/SKILL.md:68`: tambahkan "Baris Test profil `TIDAK_ADA` → lewati, catat `test=TIDAK_ADA`; sertakan langkah QA manual Section 4 di laporan."
4. Guardrail execute (sesudah `:92`): "MUST NOT memasang framework/dependensi test yang tidak tercantum di Section 3 rencana."

### Test
Verifikasi manual: pada repo PHP/JS kecil tanpa runner, profile mencatat `Test | … | TIDAK_ADA`, plan tidak menambah langkah test, dan execute berakhir `COMPLETED` dengan `test=TIDAK_ADA` tanpa menambah dependensi.

### Selesai bila
Status `TIDAK_ADA` ada di profil; plan dan execute punya jalur untuknya; guardrail melarang framework test di luar rencana.

---

## D13 [Rendah] Prasyarat tool dan klaim "ringan"
- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 1 jam · **Bergantung pada:** — · **Memblokir:** —

**Koreksi terhadap ISSUES.md:** `explore/SKILL.md:10` (Iron Law) menuntut penelusuran pemanggil sampai `trace_depth` dan analisis dampak. Tuntutan env, skema DB, dan test ada di Fase 3 `:77-81` dan guardrail `:102-103`, bukan di `:10`. Substansi temuannya tetap.

### Lokasi & kode saat ini
- `src/plugins/quickdev/skills/explore/SKILL.md:17` (Precondition 4): "Tool `Glob` (pola nama berkas), `Grep` (pencarian teks), dan `Read` (pembaca berkas) tersedia." Tidak ada failure path bila tidak tersedia (Failure path `:133-136`).
- `explore/SKILL.md:45,48`: Fase 1 memakai `Glob` dan "Grep Search".
- `explore/SKILL.md:10`: "… WAJIB DITELUSURI HINGGA PEMANGGIL DAN DEFINISI SUMBERNYA SAMPAI KEDALAMAN `trace_depth`. DILARANG MELANJUTKAN … TANPA MENGETAHUI DAMPAK …"
- `explore/SKILL.md:77-78`: skema DB, tabel relasi, `.env`. `:79-81`: test suite. `:103`: "MUST NOT menghentikan penelusuran pada layer permukaan tanpa memeriksa implementasi logika bisnis inti."

### Masalah
- Sesi utama Claude Code 2.1.281 tidak menyediakan tool `Glob`/`Grep` (sudah dicek agen review). Sesi agen penyusun berkas ini juga hanya punya Bash/Read/Edit/Write, tanpa Glob/Grep. Precondition 4 gagal, dan tidak ada jalur lanjut.
- Kedalaman penuh (env, DB, test, logika inti) diwajibkan juga untuk perubahan satu baris. Ini bertentangan dengan deskripsi marketplace ("alur kerja ringan", `.claude-plugin/marketplace.json:42`).

### Perbaikan
1. `explore/SKILL.md:17` diganti: "Pencarian berkas/teks: tool `Glob`/`Grep` bila tersedia; bila tidak, Bash baca-saja: `git ls-files | grep -i '<pola>'` (nama berkas), `grep -rn --include='*.<ext>' '<pola>' <dir>` atau `rg -n '<pola>'` bila terpasang (isi). `Read` wajib."
2. `explore/SKILL.md:45,48`: ganti "Jalankan `Glob`" dan "Grep Search" menjadi "pencarian nama berkas" dan "pencarian teks" (alat per Precondition 4).
3. **Skala kedalaman** (Fase 0, butir baru sesudah `:41`):
   "Tentukan skala dari permintaan dan temuan pertama:
   - **kecil**: ≤2 berkas, tanpa perubahan kontrak publik, skema, atau env → `trace_depth=1`, Fase 3 hanya pemanggil langsung dan test berkas target; env/DB dilewati dan dicatat `tidak relevan`;
   - **standar**: selain itu → aturan penuh.
   
   Nyatakan skala di Output (`SKALA: kecil | standar`)."
4. Iron Law `:10` dan guardrail `:103`: tambahkan "… sesuai skala Fase 0".

### Test
Verifikasi manual:
1. Di sesi tanpa Glob/Grep, `/quickdev:explore query="tombol simpan"` berjalan memakai `git ls-files`/`grep` dan menghasilkan `file:baris`.
2. Permintaan typo satu berkas menghasilkan `SKALA: kecil` tanpa penelusuran env/DB.

### Selesai bila
Explore punya jalur fallback Bash yang eksplisit; skala kedalaman tertulis dan tampil di Output; Iron Law serta guardrail konsisten dengan skala.

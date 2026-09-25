# Langkah 1 — Profil per Plugin, Hook, dan Koeksistensi (rincian L1.1–L1.4)

Sumber: `ISSUES.md` Langkah 1 (commit `34684ee`). Semua nomor baris, kutipan kode, dan output di berkas ini diverifikasi ulang terhadap kode saat ini. Output reproduksi adalah hasil nyata eksekusi di scratchpad; yang tidak dijalankan ditandai **belum dijalankan**.

## Tujuan langkah

1. Tiap plugin engineer (`backenddev`, `frontenddev`) punya profil sendiri, dan tidak ada plugin yang membaca, menimpa, atau menggerbangi repo berdasarkan profil milik plugin lain.
2. Hook SessionStart mendeteksi repo dengan **satu** implementasi Python, sama persis dengan skrip prasyarat, sehingga hook dan skrip tidak pernah memberi vonis berbeda.
3. `analyst` dan `quickdev` bisa dipakai di repo yang juga dilayani `backenddev`/`frontenddev` tanpa dibelokkan hook.
4. Teks hook dan SKILL tidak saling bertentangan soal profil yang belum ada.

## Urutan pengerjaan di dalam langkah

| Urutan | Pekerjaan | Alasan |
|---|---|---|
| 0 | **K1** (Opsi A/B L1.1) diputuskan user | Menentukan path profil yang dipakai `detect.py`, skrip, dan markdown |
| 1 | L1.2 — `hooks/detect.py` + `hooks/gate_text.py` + `hooks.json`, pembungkus di `precondition_lib.py` | Membangun fondasi deteksi yang sudah membaca tata letak Opsi A (termasuk lokasi lama). Bagian hook L1.1 selesai di sini. |
| 2 | L1.1 — konstanta/resolver path di skrip, mode MIGRATE, markdown, zona commit | Memakai `detect.read_profile` dari langkah 1 |
| 3 | L1.3 — teks LEWATI (sudah di `gate_text.py`), penanda opt-out, teks quickdev | `gate_text.py` sudah ada |
| 4 | L1.4 — penyelarasan teks hook ↔ SKILL | Paling akhir; kalimat "baca-kode" bergantung L2.8 |

## Dependensi dengan langkah lain

| Item | Terkait | Sifat |
|---|---|---|
| L1.1 | L2.8 (tech-lead read-only), 8.B **B3** dan 8.C **C10** (`--profile-dir` diterima padahal "nilai lain ditolak"), 8.C **C13** (mode patch profil) | B3/C10 diselesaikan sekaligus di L1.1 sub-tugas 5. C13 bisa memakai mode MIGRATE sebagai pola. |
| L1.2 | L5.5 (konsolidasi `_common` backenddev), L5.9 (BOM: `detect.py` sudah memakai `utf-8-sig`), L6.1/L6.2 (test & CI; `shellcheck` hook tidak diperlukan lagi setelah `.sh` dihapus), L3.4 (menambah `PreToolUse` di `hooks.json` yang sama), L7.3 (klaim hook di README frontenddev) | Kerjakan L1.2 sebelum L5.5 agar L5.5 tidak menyalin ulang deteksi lama. Gabungkan perubahan `hooks.json` dengan L3.4 bila dikerjakan berdekatan. |
| L1.3 | 8.D **D3, D5, D6, D7** (berkas SKILL quickdev yang sama), L3.5 (`quickdev:profile`), 8.A **A1** (serah-terima analyst) | Edit quickdev dalam satu PR agar tidak konflik. |
| L1.4 | L2.8 | Kalimat hook backenddev soal "baca-kode" ditulis final setelah L2.8 menentukan mode `--read-only`. |

## Estimasi usaha

| Item | Severity | Estimasi |
|---|---|---|
| L1.1 (Opsi A) | Kritis | 2,5–3 hari (Opsi B: 1–1,5 hari) |
| L1.2 | Tinggi | 2 hari |
| L1.3 | Tinggi | 1 hari (termasuk verifikasi sesi nyata) |
| L1.4 | Rendah | 0,25 hari |
| **Total** | | **±6 hari kerja** (Opsi B: ±4,5 hari) |

## Ringkasan berkas yang disentuh

| Area | Berkas |
|---|---|
| Hook backenddev | `src/plugins/backenddev/hooks/hooks.json` (ubah), `tech-lead-gate.sh` (hapus), `detect.py` (baru), `gate_text.py` (baru) |
| Hook frontenddev | `src/plugins/frontenddev/hooks/hooks.json` (ubah), `lead-gate.sh` (hapus), `detect.py` (baru, identik), `gate_text.py` (baru) |
| Skrip backenddev | `skills/_common/precondition_lib.py` + 13 skrip (tabel L1.1) |
| Skrip frontenddev | `skills/_common/precondition_lib.py` + 9 skrip (tabel L1.1) |
| Markdown backenddev | 31 berkas / 92 baris `.claude/profile` (tabel L1.1); adapter `stacks/node.md`, `bun.md`, `rust.md`; `profile/SKILL.md` Fase 0 |
| Markdown frontenddev | 15 berkas / 43 baris `.claude/profile` (tabel L1.1); rujukan `hooks/lead-gate.sh` di 4 berkas markdown (L1.2 sub-tugas 7) |
| quickdev | 6 × `skills/*/SKILL.md` |
| analyst | `README.md:121-122` |
| Test (baru) | `tests/hooks/test_detect.py`, `tests/test_profile_paths.py`, `src/plugins/{backenddev,frontenddev,quickdev}/tests/…` |

## Keputusan yang dibutuhkan user

| ID | Item | Pilihan | Saran |
|---|---|---|---|
| K1 | L1.1 | Opsi A (direktori per plugin) / Opsi B (field pemilik) | **A** |
| K2 | L1.1 | Skrip hilir boleh membaca profil di lokasi lama selama masa transisi (dengan catatan MIGRATE) / langsung FAIL | **Boleh**, satu versi minor |
| K3 | L1.2 | Hono di atas Node → `node` (tambah `hono` ke penanda `stacks/node.md`, sesuai `bun.md:11`) / tetap tidak terdeteksi | **`node`** |
| K4 | L1.2 | React/Svelte tanpa Vite (CRA, Rollup) → di luar cakupan (sesuai adapter) / tetap `react-vite`/`svelte-vite` | **Di luar cakupan** |
| K5 | L1.2 | Kedua hook ikut memindai anak langsung root (`frontend/`, `backend/`, `server/`) dengan daftar lewati / hanya workspace + `apps|packages|services` | **Ikut memindai** |
| K6 | L1.2 | Dependensi Go bertanda `// indirect` diabaikan / dihitung | **Diabaikan** |
| K7 | L1.3 | `disable-model-invocation: true` di keenam skill quickdev / hanya `execute` / tidak sama sekali | **Keenamnya** |
| K8 | L1.3 | Penanda opt-out `.claude/workflow` (daftar plugin yang boleh menggerbangi repo) / tidak ada | **Ada** |
| K9 | L1.4 | Profil belum ada → gerbang merutekan profil otomatis lalu melanjutkan / berhenti dan minta user | **Otomatis via gerbang** |

## Definisi selesai langkah ini

- Keempat item memenuhi **Selesai bila** masing-masing dan checkbox-nya dicentang di berkas ini dan di `ISSUES.md`.
- `pytest tests/hooks tests/test_profile_paths.py src/plugins/*/tests` hijau di Python 3.11–3.13. Semua kasus di tabel L1.1 dan L1.2 menjadi parameter test.
- `tests/hooks/test_detect.py::test_detect_py_identik` hijau: `backenddev/hooks/detect.py` dan `frontenddev/hooks/detect.py` identik byte-per-byte.
- Tidak ada lagi `tech-lead-gate.sh`/`lead-gate.sh` maupun rujukan ke keduanya di markdown dan Python.
- Verifikasi manual L1.1 dan L1.3 (sesi Claude Code nyata) dijalankan dan hasilnya ditempel di PR.
- `Log Keputusan` di `ISSUES.md` terisi untuk K1–K9.

## Artefak reproduksi (scratchpad, sementara)

`/tmp/claude-1000/-home-fakhrulnugroho-work-natakode-nataflow-agentic-workflow/d3694b5e-a45f-49bf-8ba3-1a983c306ba0/scratchpad/detail-01/`:
`repro-l1-1.sh`, `repro-l1-2.sh`, `repro-l1-3.sh`, `proto-matrix.sh`, `proto/hooks/detect.py` (prototipe yang dikutip di L1.2), `proto/be/gate_text.py`, `proto/fe/gate_text.py`, `fe-copy/` (salinan frontenddev dengan `precondition_lib.py` yang sudah dibungkus). Salin ke tempat lain bila ingin dipakai sebagai dasar test.

---

## L1.1 [Kritis] backenddev dan frontenddev berebut `.claude/profile/`

- [ ] Selesai

**Plugin:** backenddev, frontenddev (berdampak ke analyst dan quickdev lewat hook) · **Estimasi:** 2,5–3 hari (Opsi A) · **Bergantung pada:** K1, K2; L1.2 (hook memakai `detect.read_profile`) · **Memblokir:** L1.3 (teks hook), L1.4, B3, C10

### Konteks

Keempat plugin dipasang user-wide dari satu marketplace. `backenddev:profile` dan `frontenddev:profile` sama-sama menulis ke `.claude/profile/`, dengan skema `index.json` dan isi berkas yang berbeda. Kedua hook dan semua skrip prasyarat menganggap `index.json` di sana miliknya. Lima nama berkas bertabrakan dengan format berbeda: `index.json`, `stack.md`, `surface-map.md`, `invariants.md`, `commands.md`.

| | backenddev | frontenddev |
|---|---|---|
| Field `index.json` | `project`, `stack`, `architecture`, `root_namespace`, `source_root`, `commit_convention`, `base_branch`, `branch_convention` | `project`, `stack`, `platform`, `framework`, `source_root`, `workspace`, `target_app`, `commit_convention` |
| Nilai `stack` | `java-spring`, `go`, `node`, `bun`, `rust`, `php`, `php-codeigniter` | `react-vite`, `react-native`, `sveltekit`, `svelte-vite` |
| Berkas | `index.json` + 8 `.md` (`stack`, `module-structure`, `domain-map`, `surface-map`, `code-conventions`, `anti-patterns`, `invariants`, `commands`) | `index.json` + 9 `.md` (`stack`, `structure`, `surface-map`, `invariants`, `commands`, `layer-adoption`, `visual`, `drift`, `manual-notes`) |

### Lokasi & kode saat ini

`src/plugins/backenddev/hooks/tech-lead-gate.sh:37-41` — profil apa pun di `.claude/profile/` dianggap milik backenddev:
```sh
# 1. Repo sudah di-onboard ke backenddev — penanda milik plugin ini sendiri; stack dibaca dari profil.
if [ -f "$cwd/.claude/profile/index.json" ]; then
  stack=$(sed -n 's/.*"stack"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$cwd/.claude/profile/index.json" | head -n 1)
  [ -n "$stack" ] || stack="terdaftar di profil"
  has_profile=1
```

`src/plugins/frontenddev/hooks/lead-gate.sh:43-46` dan `:95-99` — penanda sama; stack backend divonis "TIDAK SAH" lalu disuruh REFRESH:
```sh
# 1. Repo sudah di-onboard ke frontenddev — marker milik plugin ini sendiri; stack dibaca dari profil.
if [ -f "$cwd/.claude/profile/index.json" ]; then
  stack=$(sed -n 's/.*"stack"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$cwd/.claude/profile/index.json" | head -n 1)
  has_profile=1
...
elif [ "$stack_known" = 0 ]; then
  context=$( { printf '<frontenddev-lead-gate>\nRepo ini terdeteksi sebagai repo frontend, tetapi `.claude/profile/index.json` TIDAK SAH: field `stack` terbaca "%s", di luar daftar sah (react-vite, react-native, sveltekit, svelte-vite).\n\n' "$stack"
cat <<'TXT'
Tanpa field itu, tak satu pun skill hilir dapat memuat adapter `skills/profile/stacks/<stack-id>.md`.
Jika ada permintaan kerja baru, BERHENTI SEGERA dan minta user menulis ulang profil via `frontenddev:profile` (mode REFRESH).
```

`src/plugins/backenddev/skills/profile/scripts/check_preconditions.py:20-26` — `package.json` apa pun dianggap manifest backend:
```python
MANIFEST_MAP = [
    (["pom.xml", "build.gradle", "build.gradle.kts"], "java-spring"),
    (["go.mod"], "go"),
    (["package.json"], "node"),  # or bun, resolved by stack adapter
    (["Cargo.toml"], "rust"),
    (["composer.json"], "php"),  # or php-codeigniter, resolved by stack adapter
]
```

`src/plugins/frontenddev/skills/profile/scripts/check_preconditions.py:240-256` — mode diputuskan dari keberadaan `index.json` saja, tanpa melihat pemiliknya:
```python
    def _resolve_mode(self) -> None:
        """Selesaikan GENERATE vs REFRESH; ketidakcocokan jadi WARN, bukan FAIL."""
        exists = self.index_path.is_file()
        actual = "REFRESH" if exists else "GENERATE"
```

`src/plugins/frontenddev/skills/_common/precondition_lib.py:38-43`:
```python
KNOWN_STACKS = ("react-vite", "react-native", "sveltekit", "svelte-vite")
TASKDIR_PATTERN = re.compile(r"^frontenddev/docs/\d{10}-[a-z0-9-]+$")
PROFILE_FILES = ("index.json", "stack.md", "structure.md", "surface-map.md",
                 "invariants.md", "commands.md", "layer-adoption.md", "visual.md",
                 "drift.md", "manual-notes.md")
```

Instruksi yang mengizinkan penimpaan tanpa konfirmasi:
- `src/plugins/frontenddev/skills/lead/SKILL.md:158` — "rute `PROFILE` ke `frontenddev:profile` mode `GENERATE` tanpa titik henti konfirmasi; `force: true` hanya bila rute ini menyala di atas profil yang ternyata ada."
- `src/plugins/frontenddev/skills/profile/SKILL.md:22` — "`force` … bila `true`, Phase 1 melewati konfirmasi REFRESH dan langsung menulis ulang." `:146` — "Dilarang menulis ulang profil yang sudah ada tanpa konfirmasi user, kecuali `force: true` disetel pendispatch."
- `src/plugins/backenddev/skills/profile/SKILL.md:51-53` — Fase 1: `index.json` ada → REFRESH, tanpa memeriksa pemilik.
- Skema: `backenddev/skills/profile/templates/profile-template.md:29-46`, `frontenddev/skills/profile/templates/profile-template.md:39-58`, `frontenddev/skills/profile/SKILL.md:109`.

### Reproduksi

```bash
#!/usr/bin/env bash
# Reproduksi L1.1 — dua plugin berebut .claude/profile/
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
P=$REPO/src/plugins
BE_HOOK=$P/backenddev/hooks/tech-lead-gate.sh
FE_HOOK=$P/frontenddev/hooks/lead-gate.sh
tmp=$(mktemp -d)
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

# Cetak baris ke-2 additionalContext (baris vonis) atau "(kosong)".
hook() { printf '{"cwd":"%s","hook_event_name":"SessionStart","source":"startup"}' "$2" | sh "$1" |
  python3 -c 'import json,sys; d=sys.stdin.read().strip(); print(json.loads(d)["hookSpecificOutput"]["additionalContext"].splitlines()[1] if d else "(kosong)")'; }

be_profile() {  # profil backenddev lengkap (index.json + 8 .md)
  mkdir -p "$1/.claude/profile"
  printf '{"project":"x","stack":"%s","architecture":"layered","root_namespace":"x","source_root":"%s","commit_convention":"conventional","base_branch":"main","branch_convention":"feat/<slug>"}\n' "$2" "$3" > "$1/.claude/profile/index.json"
  for f in stack module-structure domain-map surface-map code-conventions anti-patterns invariants commands; do echo "# $f" > "$1/.claude/profile/$f.md"; done
}
fe_profile() {  # profil frontenddev lengkap (index.json + 9 .md)
  mkdir -p "$1/.claude/profile"
  printf '{"project":"x","stack":"%s","platform":"React SPA (Vite)","framework":"React 19","source_root":"src","workspace":"%s","target_app":"%s","commit_convention":"conventional"}\n' "$2" "$3" "$4" > "$1/.claude/profile/index.json"
  for f in stack structure surface-map invariants commands layer-adoption visual drift manual-notes; do echo "# $f" > "$1/.claude/profile/$f.md"; done
}

echo "== A. Repo Go ber-profil backenddev =="
git init -q "$tmp/a"; printf 'module example.com/svc\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.10.0\n' > "$tmp/a/go.mod"
be_profile "$tmp/a" go internal
echo "BE hook: $(hook "$BE_HOOK" "$tmp/a")"
echo "FE hook: $(hook "$FE_HOOK" "$tmp/a")"

echo "== B. Repo React+Vite ber-profil frontenddev =="
git init -q "$tmp/b"; echo '{"dependencies":{"react":"^19","react-dom":"^19"},"devDependencies":{"vite":"^6"}}' > "$tmp/b/package.json"
fe_profile "$tmp/b" react-vite single ""
echo "BE hook: $(hook "$BE_HOOK" "$tmp/b")"
echo "FE hook: $(hook "$FE_HOOK" "$tmp/b")"

echo "== C. Monorepo fullstack (apps/web React, apps/api Express) ber-profil backenddev =="
git init -q "$tmp/c"; mkdir -p "$tmp/c/apps/web" "$tmp/c/apps/api/src"
echo '{"private":true,"workspaces":["apps/*"]}' > "$tmp/c/package.json"
echo '{"dependencies":{"react":"^19","react-dom":"^19"},"devDependencies":{"vite":"^6"}}' > "$tmp/c/apps/web/package.json"
echo '{"dependencies":{"express":"^4"}}' > "$tmp/c/apps/api/package.json"
be_profile "$tmp/c" node apps/api/src
git -C "$tmp/c" add -A; git -C "$tmp/c" commit -qm init
echo "BE hook: $(hook "$BE_HOOK" "$tmp/c")"
echo "FE hook: $(hook "$FE_HOOK" "$tmp/c")"
echo "-- frontenddev:profile prasyarat:"
python3 $P/frontenddev/skills/profile/scripts/check_preconditions.py --root "$tmp/c" | grep -E 'PRECONDITION|^\[3\]|^\[6\]|Terselesaikan'
echo "-- frontenddev:ux-design prasyarat (profil backend dibaca sebagai profil frontenddev):"
python3 $P/frontenddev/skills/ux-design/scripts/check_preconditions.py --root "$tmp/c" --taskdir frontenddev/docs/2601010000-x | grep -E '^\[(5|6)\]' -A1
echo "-- simulasi frontenddev:profile REFRESH (force) menimpa profil:"
fe_profile "$tmp/c" react-vite monorepo apps/web
git -C "$tmp/c" add -A; git -C "$tmp/c" commit -qm 'docs: refresh frontenddev profile'
(cd "$tmp/c" && python3 $P/backenddev/skills/tech-lead/scripts/check_preconditions.py | grep -E 'PRECONDITION|^\[1\]')

echo "== D. Repo React+Vite murni ber-profil frontenddev → prasyarat backenddev:profile =="
git -C "$tmp/b" add -A; git -C "$tmp/b" commit -qm init
(cd "$tmp/b" && python3 $P/backenddev/skills/profile/scripts/check_preconditions.py | head -3)
rm -rf "$tmp"
```

Output aktual:
```
== A. Repo Go ber-profil backenddev ==
BE hook: Repo backend, stack terdeteksi: go. Plugin `backenddev` aktif.
FE hook: Repo ini terdeteksi sebagai repo frontend, tetapi `.claude/profile/index.json` TIDAK SAH: field `stack` terbaca "go", di luar daftar sah (react-vite, react-native, sveltekit, svelte-vite).
== B. Repo React+Vite ber-profil frontenddev ==
BE hook: Repo backend, stack terdeteksi: react-vite. Plugin `backenddev` aktif.
FE hook: Repo frontend, stack terdeteksi: react-vite. Plugin `frontenddev` aktif di sini.
== C. Monorepo fullstack (apps/web React, apps/api Express) ber-profil backenddev ==
BE hook: Repo backend, stack terdeteksi: node. Plugin `backenddev` aktif.
FE hook: Repo ini terdeteksi sebagai repo frontend, tetapi `.claude/profile/index.json` TIDAK SAH: field `stack` terbaca "node", di luar daftar sah (react-vite, react-native, sveltekit, svelte-vite).
-- frontenddev:profile prasyarat:
PRECONDITION CHECK: profile [PASS] (6/6 passed)
[3] Direktori profil dapat ditulis   : PASS (5/10 berkas profil ada, seluruhnya dapat ditimpa)
[6] Mode operasi selaras             : PASS (`REFRESH` — index.json ada)
Terselesaikan: stack `react-vite` · mode `REFRESH`
-- frontenddev:ux-design prasyarat (profil backend dibaca sebagai profil frontenddev):
[5] Profil repo memuat berkas wajib  : PASS (2 berkas wajib ada, stack `node`)
[6] Adapter stack terbaca            : FAIL (`node` di luar ['react-native', 'react-vite', 'svelte-vite', 'sveltekit'])
    * Tindakan: Repo di luar cakupan plugin; hentikan rantai dan laporkan ke user.
-- simulasi frontenddev:profile REFRESH (force) menimpa profil:
PRECONDITION CHECK: tech-lead [FAIL] (4/6 passed)
[1] Profile Index & Invariants   : FAIL (Field kritis hilang/kosong di index.json: root_namespace, base_branch, branch_convention, architecture)
== D. Repo React+Vite murni ber-profil frontenddev → prasyarat backenddev:profile ==
PRECONDITION CHECK: profile [PASS] (5/5 passed)
[1] Backend Manifest Detection       : PASS (Manifest backend terdeteksi: package.json)
[2] Stack Adapter Availability       : PASS (Koleksi adapter stack dan kontrak stacks/_CONTRACT.md tersedia)
```

Semua bukti di `ISSUES.md` terkonfirmasi. Penimpaan di skenario C disimulasikan dengan menulis profil frontenddev langsung. Apakah model benar-benar merutekan `frontenddev:profile` dengan `force: true` di sesi nyata **belum dijalankan** (lihat Koreksi).

**Koreksi terhadap ISSUES.md:**
- Hitungan rujukan Python: backenddev **14 berkas / 27 titik konstruksi path** (termasuk `_common/precondition_lib.py`), ditambah ±20 string pesan; frontenddev **10 berkas / 9 titik konstruksi** ditambah hook (3). ISSUES menulis 13/23 dan 10/16. Markdown: backenddev **31 berkas / 92 baris**, frontenddev **15 berkas / 43 baris**, sebelumnya ditulis "puluhan".
- 5 berkas backenddev yang harus memakai konstanta baru **tidak** mengimpor `_common` (`analyst`, `architect`, `report`, `task` `check_preconditions.py`, dan `plan/scripts/validate_briefs.py`). Perbaikan "tambah `PROFILE_DIR` di `_common` dan pakai di ke-13 skrip" harus disertai bootstrap impor di kelima berkas itu.
- "lead merutekan dengan `force: true`": jalur instruksinya memang ada (lead Phase 3 lane `PROFILE` "perlu refresh" + Failure path 1). Namun lead Failure path 2 (`lead/SKILL.md:159`) menyuruh berhenti bila `stack` profil di luar kontrak. Jalur mana yang dipilih model perlu diverifikasi di sesi nyata. Kontradiksi ini ikut diselesaikan di L1.4.

### Dampak

- Di setiap repo yang sudah di-onboard salah satu plugin, hook plugin lain menyuntik perintah gerbang yang salah (A, B).
- Di monorepo fullstack kedua plugin saling mengunci: frontenddev memvonis profil backend "di luar cakupan", lalu `frontenddev:profile` menimpanya sebagai REFRESH (5/10 berkas "dapat ditimpa"). Sesudah itu backenddev FAIL permanen (C).
- `commands.md`/`invariants.md` yang tertimpa membuat architect salah satu plugin menjalankan perintah verifikasi stack lain.
- `backenddev:profile` mau memprofilkan repo React murni (D), sehingga profil frontenddev bisa tertimpa dari arah sebaliknya.

### Rencana perbaikan — Opsi A (disarankan): `.claude/profile/<plugin>/`

Tata letak baru:
```
.claude/profile/backenddev/index.json   (+ 8 .md)   "plugin": "backenddev"
.claude/profile/frontenddev/index.json  (+ 9 .md)   "plugin": "frontenddev"
.claude/profile/index.json              lokasi lama — hanya dibaca untuk MIGRATE
```

1. **Konstanta dan resolver path per plugin.**
   `src/plugins/backenddev/skills/_common/precondition_lib.py` (tambahan di bawah impor):
   ```python
   import sys
   sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
   import detect as _detect  # noqa: E402  (L1.2; identik di kedua plugin)

   PLUGIN = "backenddev"
   PROFILE_DIR_REL = f".claude/profile/{PLUGIN}"      # satu-satunya lokasi tulis
   LEGACY_PROFILE_DIR_REL = ".claude/profile"          # lokasi lama, dibaca hanya untuk MIGRATE (K2)


   def resolve_profile_dir(root: Path) -> Tuple[Path, str]:
       """(direktori profil yang dibaca, catatan untuk laporan prasyarat).

       Lokasi baru selalu menang. Lokasi lama dipakai hanya bila `index.json`-nya
       milik plugin ini (field `plugin`, atau `stack` anggota daftar backenddev),
       dan selalu disertai catatan MIGRATE. Profil milik plugin lain tidak pernah
       dikembalikan: skrip melihatnya sebagai profil yang tidak ada.
       """
       own = root / PROFILE_DIR_REL
       if (own / "index.json").exists():
           return own, ""
       prof = _detect.read_profile(root, PLUGIN)
       if prof.location == "legacy" and prof.state not in ("OTHER_OWNER", "ABSENT", "INVALID_JSON"):
           return root / LEGACY_PROFILE_DIR_REL, (
               "profil backenddev masih di lokasi lama `.claude/profile/`; "
               "jalankan `backenddev:profile` mode MIGRATE")
       return own, ""
   ```
   `profile_staleness()` (`:67`, `:90`) memakai `resolve_profile_dir(root)[0]` dan `git log -- <PROFILE_DIR_REL>`. Tanpa ini, commit profil frontenddev ikut me-reset vonis kesegaran profil backenddev.
   `src/plugins/frontenddev/skills/_common/precondition_lib.py`: pola sama dengan `PLUGIN = "frontenddev"`, ditambah `DEFAULT_PROFILE_DIR = PROFILE_DIR_REL` yang dipakai semua `profile_dir or ".claude/profile"`.

2. **Ganti titik konstruksi path di skrip** sesuai tabel checklist di bawah. Pola perubahan backenddev:
   ```diff
   -        profile_dir = self.root / ".claude" / "profile"
   -        index_file = profile_dir / "index.json"
   +        profile_dir, legacy_note = resolve_profile_dir(self.root)
   +        index_file = profile_dir / "index.json"
   ```
   Pesan `"Berkas .claude/profile/index.json tidak ditemukan"` → `f"Berkas {PROFILE_DIR_REL}/index.json tidak ditemukan"`. Bila `legacy_note` terisi, tempelkan ke `summary` check yang PASS (backenddev tidak punya status WARN). Pola frontenddev:
   ```diff
   -        self.profile_dir = self.root / (profile_dir or ".claude/profile")
   +        self.profile_dir = (self.root / profile_dir) if profile_dir else resolve_profile_dir(self.root)[0]
   ```
   Di `tech-lead/scripts/check_preconditions.py:23-28`:
   ```diff
    RE_ENTRY_ALLOWED_PREFIXES = (
   -    ".claude/profile/",
   +    ".claude/profile/backenddev/",
   +    ".claude/profile/index.json",   # hanya selama MIGRATE (git mv meninggalkan penghapusan di lokasi lama)
        "backenddev/docs/",
   ```

3. **Field `plugin` di `index.json`** sebagai pertahanan kedua. Template: `backenddev/skills/profile/templates/profile-template.md:34-43` dan `frontenddev/skills/profile/templates/profile-template.md:44-53` mendapat baris pertama `"plugin": "backenddev"` / `"plugin": "frontenddev"`. Skrip prasyarat hilir: `index.json` dengan `plugin` ≠ plugin sendiri → FAIL `"profil milik <x>; bukan profil <plugin>"`.

4. **Mode MIGRATE di skill profile.** Skrip baru `skills/profile/scripts/migrate_profile.py` di kedua plugin (logika sama, konstanta berbeda). Skrip ini hanya memindahkan berkas milik plugin itu sendiri dan tidak meng-commit:
   ```python
   def migrate(root: Path, plugin: str, files: Tuple[str, ...]) -> Tuple[List[str], List[str]]:
       """Pindahkan profil lama milik `plugin` ke .claude/profile/<plugin>/. (dipindah, sisa)."""
       legacy, target = root / ".claude" / "profile", root / ".claude" / "profile" / plugin
       data, state = _detect.read_index(legacy / "index.json")
       if state != "OK" or _detect.owner_of(data) != plugin:
           raise SystemExit(f"MIGRATE FAIL: .claude/profile/index.json bukan milik {plugin}")
       target.mkdir(parents=True, exist_ok=True)
       moved = []
       for name in files:
           src = legacy / name
           if not src.is_file():
               continue
           ok, _ = git_ok(root, "mv", "--", src.relative_to(root).as_posix(),
                          (target / name).relative_to(root).as_posix())
           if not ok:                       # berkas belum ter-track
               src.rename(target / name)
           moved.append(name)
       data["plugin"] = plugin
       (target / "index.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
       leftovers = sorted(p.name for p in legacy.iterdir() if p.is_file())
       return moved, leftovers
   ```
   - `frontenddev/skills/profile/scripts/check_preconditions.py:_resolve_mode` menghasilkan `MIGRATE` bila `detect.read_profile(root, "frontenddev").location == "legacy"` dan pemiliknya frontenddev. Hasilnya `REFRESH` hanya bila `.claude/profile/frontenddev/index.json` ada.
   - `backenddev/skills/profile/scripts/check_preconditions.py`: tambah check 6 "Mode & kepemilikan profil" (GENERATE/REFRESH/MIGRATE) dan cetak baris `Terselesaikan: mode <...>` seperti frontenddev.
   - SKILL: Fase 1 backenddev (`profile/SKILL.md:49-55`) dan Phase 1 frontenddev (`profile/SKILL.md:46-53`) mendapat cabang MIGRATE: "jalankan `migrate_profile.py`, laporkan berkas sisa di `.claude/profile/` sebagai **bukan milik plugin ini — tidak disentuh**, lalu lanjut ke Fase 7 tanpa pemindaian ulang".
   - Commit: frontenddev meng-commit sendiri (`docs: migrate frontenddev profile`, di `profile/SKILL.md:123`); backenddev meng-commit lewat tech-lead Fase 5 (`tech-lead/SKILL.md:142`, matriks `references/gate-scope.md:49`).
   - Profil yang **sudah tertimpa** (skenario C) tidak bisa dipulihkan dari disk. Tambahkan ke laporan MIGRATE: "profil backenddev sebelumnya bisa dipulihkan dari riwayat: `git log --oneline -- .claude/profile/index.json`".

5. **Prasyarat skill profile menolak profil asing dan parameter liar.**
   - `.claude/profile/<plugin>/index.json` ber-`plugin` lain → FAIL.
   - Lokasi lama milik plugin lain → PASS dengan catatan "profil lama milik `<x>` diabaikan; profil `<plugin>` ditulis ke `.claude/profile/<plugin>/`". Status ini **bukan** REFRESH.
   - `--profile-dir` selain `PROFILE_DIR_REL` → FAIL. Ini sekaligus menutup B3 (backenddev) dan C10 (frontenddev).
   - `backenddev/skills/profile/scripts/check_preconditions.py:76-112` check 1 memakai `detect.detect_backend(root)` (L1.2) sebagai ganti `MANIFEST_MAP`. Repo React murni → FAIL "tidak ada penanda framework server backend".
   - Teks `force` di `frontenddev/skills/profile/SKILL.md:22,146` dan `backenddev/skills/profile/SKILL.md:25`: tambahkan "`force` tidak pernah berlaku atas profil milik plugin lain atau lokasi lama; keduanya ditolak prasyarat".

6. **Hook**: sudah tercakup L1.2. `detect.read_profile()` membaca `.claude/profile/<plugin>/` lebih dulu, lalu lokasi lama beserta pemiliknya. Profil milik plugin lain dianggap tidak ada (hasilnya diverifikasi prototipe; lihat tabel A1–A6 di bawah).

7. **Markdown**: ganti semua rujukan sesuai tabel checklist markdown. Perintah bantu (dijalankan implementor; tinjau hasil diff baris per baris):
   ```bash
   cd src/plugins/backenddev  && grep -rlZ '\.claude/profile' --include='*.md' . | xargs -0 perl -pi -e 's#\.claude/profile(?!/backenddev)#.claude/profile/backenddev#g'
   cd ../frontenddev          && grep -rlZ '\.claude/profile' --include='*.md' . | xargs -0 perl -pi -e 's#\.claude/profile(?!/frontenddev)#.claude/profile/frontenddev#g'
   ```
   Pengecualian yang ditulis manual sesudahnya: cabang MIGRATE di Fase/Phase 1 profile (harus menyebut lokasi lama `.claude/profile/index.json`), dan `backenddev/skills/profile/stacks/_CONTRACT.md:74` (`.claude/profile/stacks/` → `.claude/profile/backenddev/stacks/`, tetap berupa larangan).

8. **Zona commit dan staging**: `backenddev/skills/tech-lead/SKILL.md:141` (daftar zona `--re-entry`), `backenddev/skills/tech-lead/references/gate-scope.md:49` (baris matriks `.claude/profile/` → `.claude/profile/backenddev/`, subjek tetap), `frontenddev/skills/profile/SKILL.md:123` (`git add .claude/profile/` → `git add .claude/profile/frontenddev/`). Baris `.gitignore` (`.backenddev/`, `.frontenddev/`, `.explore/`) tidak berubah.

9. **quickdev** (`repo-profile.md` → `.claude/profile/quickdev/`): **tunda**. quickdev tidak membaca `index.json` dan tidak bertabrakan. Memindahkannya hanya mengubah default `profile_path`/`target_path` di 6 SKILL tanpa mengurangi risiko. Koeksistensinya ditangani L1.3.

#### Checklist titik sentuh — Python dan hook

"Konstruksi" = baris yang membentuk path. "Pesan" = string/dokstring yang menyebut path. Baris diambil dari `grep -nE '"\.claude" / "profile"|profile_dir or "\.claude/profile"|DEFAULT_PROFILE_DIR|\.claude/profile'`.

| ☐ | Plugin | Berkas (relatif `src/plugins/<plugin>/`) | Konstruksi | Pesan | Impor `_common`? | Perubahan Opsi A |
|---|---|---|---|---|---|---|
| ☐ | backenddev | `hooks/tech-lead-gate.sh` | 38, 39 | 76, 78 | — | Hapus; diganti `detect.py` (L1.2) |
| ☐ | backenddev | `skills/_common/precondition_lib.py` | 67, 90 | 49, 69 | rumah | Tambah `PROFILE_DIR_REL`, `resolve_profile_dir`; `:67` → resolver, `:90` → `PROFILE_DIR_REL` |
| ☐ | backenddev | `skills/analyst/scripts/check_preconditions.py` | 157 | 164 | **tidak** | Tambah bootstrap; resolver |
| ☐ | backenddev | `skills/architect/scripts/check_preconditions.py` | 142 | 150 | **tidak** | Tambah bootstrap; resolver |
| ☐ | backenddev | `skills/audit/scripts/check_preconditions.py` | 70, 116, 174 | 124 | ya | Resolver (3×) |
| ☐ | backenddev | `skills/business-analysis/scripts/check_preconditions.py` | 147, 206 | 155 | ya | Resolver (2×) |
| ☐ | backenddev | `skills/debug/scripts/check_preconditions.py` | 72, 167, 319 | 80 | ya | Resolver (3×) |
| ☐ | backenddev | `skills/document-api/scripts/check_preconditions.py` | 71, 108 | — | ya | Resolver (2×) |
| ☐ | backenddev | `skills/plan/scripts/check_preconditions.py` | 176, 398 | 184, 221 | ya | Resolver (2×) |
| ☐ | backenddev | `skills/plan/scripts/validate_briefs.py` | 450, 1062, 1488 | 168, 1053 (docstring), 1088 | **tidak** | Tambah bootstrap; resolver (3×) |
| ☐ | backenddev | `skills/profile/scripts/check_preconditions.py` | 50 (default `--profile-dir`) | 153 | ya | Default `PROFILE_DIR_REL`, tolak nilai lain, check kepemilikan + MIGRATE, check 1 via `detect_backend` |
| ☐ | backenddev | `skills/report/scripts/check_preconditions.py` | 276 | 284 | **tidak** | Tambah bootstrap; resolver |
| ☐ | backenddev | `skills/system-analysis/scripts/check_preconditions.py` | 187, 293 | 195 | ya | Resolver (2×) |
| ☐ | backenddev | `skills/task/scripts/check_preconditions.py` | 212 | 219 | **tidak** | Tambah bootstrap; resolver |
| ☐ | backenddev | `skills/tech-lead/scripts/check_preconditions.py` | 24 (prefix re-entry), 75, 332 | 85, 129, 338, 371 | ya | Prefix `.claude/profile/backenddev/`; resolver (2×) |
| ☐ | frontenddev | `hooks/lead-gate.sh` | 44, 45, 76 | 3, 88, 96, 104 | — | Hapus; diganti `detect.py` (L1.2) |
| ☐ | frontenddev | `skills/_common/precondition_lib.py` | (baru) `DEFAULT_PROFILE_DIR` | 12, 96 (docstring hook), 680 | rumah | Konstanta + resolver; pesan `:680` → `DEFAULT_PROFILE_DIR`; `:942` (`:(exclude).claude`) tidak berubah |
| ☐ | frontenddev | `skills/architect/scripts/check_preconditions.py` | 71 | — | ya | Resolver |
| ☐ | frontenddev | `skills/contract/scripts/check_preconditions.py` | 42 | 75 (help) | ya | Resolver; help |
| ☐ | frontenddev | `skills/plan/scripts/check_preconditions.py` | 74 | 235 (help) | ya | Resolver; help |
| ☐ | frontenddev | `skills/plan/scripts/validate_briefs.py` | 204 | 1094 (help) | ya | Resolver; help |
| ☐ | frontenddev | `skills/profile/scripts/check_preconditions.py` | 44 (`DEFAULT_PROFILE_DIR`) | — | ya | Impor dari lib; hapus duplikat `PROFILE_FILES` `:48-50`; kepemilikan + MIGRATE di `_resolve_mode` |
| ☐ | frontenddev | `skills/review/scripts/check_preconditions.py` | 62 | — | ya | Resolver |
| ☐ | frontenddev | `skills/task/scripts/check_preconditions.py` | 48 | 126 (help) | ya | Resolver; help |
| ☐ | frontenddev | `skills/ui-design/scripts/check_preconditions.py` | 42 | 75 (help) | ya | Resolver; help |
| ☐ | frontenddev | `skills/ux-design/scripts/check_preconditions.py` | 42 | 75 (help) | ya | Resolver; help |

#### Checklist titik sentuh — markdown (`md_grep ".claude/profile"`)

| ☐ | Plugin | Berkas (relatif `src/plugins/<plugin>/`) | Baris |
|---|---|---|---|
| ☐ | backenddev | `agents/code-explorer.md` | 18 |
| ☐ | backenddev | `agents/code-implementor.md` | 12 |
| ☐ | backenddev | `agents/code-reviewer.md` | 25, 35, 60 |
| ☐ | backenddev | `skills/architect/dispatcher/implementor.md` | 20, 40, 44 |
| ☐ | backenddev | `skills/architect/dispatcher/reviewer.md` | 34, 40 |
| ☐ | backenddev | `skills/audit/SKILL.md` | 36 |
| ☐ | backenddev | `skills/audit/references/dimensions.md` | 5, 55, 78 |
| ☐ | backenddev | `skills/business-analysis/SKILL.md` | 44, 108 |
| ☐ | backenddev | `skills/business-analysis/dispatcher/explorer.md` | 61, 71, 73 |
| ☐ | backenddev | `skills/debug/SKILL.md` | 114 |
| ☐ | backenddev | `skills/debug/dispatcher/explorer.md` | 82, 92 |
| ☐ | backenddev | `skills/document-api/SKILL.md` | 26 |
| ☐ | backenddev | `skills/plan/SKILL.md` | 19 |
| ☐ | backenddev | `skills/plan/dispatcher/explorer.md` | 77, 89, 91 |
| ☐ | backenddev | `skills/plan/references/entry-rules.md` | 9 |
| ☐ | backenddev | `skills/plan/references/review-and-commit.md` | 31, 46, 55, 70, 74 |
| ☐ | backenddev | `skills/plan/references/slicing-and-scan.md` | 26 |
| ☐ | backenddev | `skills/plan/templates/brief-template.md` | 172 |
| ☐ | backenddev | `skills/profile/SKILL.md` | 3, 14, 26, 51, 86, 95, 99, 115, 124, 134, 138, 141, 146, 159 |
| ☐ | backenddev | `skills/profile/references/convention-scan.md` | 3 |
| ☐ | backenddev | `skills/profile/references/scan-guide.md` | 3 |
| ☐ | backenddev | `skills/profile/stacks/_CONTRACT.md` | 9, 59, 74 (manual), 95 |
| ☐ | backenddev | `skills/profile/templates/profile-template.md` | 1, 3, 4, 29, 48, 60, 76, 88, 100, 112, 127, 142, 159, 173, 180, 191, 200, 216, 230, 240, 252 |
| ☐ | backenddev | `skills/report/SKILL.md` | 26 |
| ☐ | backenddev | `skills/system-analysis/SKILL.md` | 15 |
| ☐ | backenddev | `skills/system-analysis/dispatcher/explorer.md` | 181, 193, 195 |
| ☐ | backenddev | `skills/system-analysis/references/analysis-protocol.md` | 47 |
| ☐ | backenddev | `skills/task/SKILL.md` | 38 |
| ☐ | backenddev | `skills/tech-lead/SKILL.md` | 51, 80, 141 |
| ☐ | backenddev | `skills/tech-lead/dispatcher/explorer.md` | 63, 64, 78, 80 |
| ☐ | backenddev | `skills/tech-lead/references/gate-scope.md` | 49, 120 |
| ☐ | frontenddev | `README.md` | 10, 19, 62, 277 |
| ☐ | frontenddev | `agents/code-explorer.md` | 36, 186 |
| ☐ | frontenddev | `agents/code-implementor.md` | 25, 60 |
| ☐ | frontenddev | `agents/code-reviewer.md` | 25, 33 |
| ☐ | frontenddev | `agents/contract-reviewer.md` | 16 |
| ☐ | frontenddev | `agents/doc-reviewer.md` | 23 |
| ☐ | frontenddev | `skills/architect/SKILL.md` | 32 |
| ☐ | frontenddev | `skills/contract/SKILL.md` | 36 |
| ☐ | frontenddev | `skills/lead/SKILL.md` | 19, 37 |
| ☐ | frontenddev | `skills/lead/dispatcher/explorer.md` | 78 |
| ☐ | frontenddev | `skills/lead/references/lane-routing-matrix.md` | 11 |
| ☐ | frontenddev | `skills/plan/dispatcher/reviewer.md` | 128 |
| ☐ | frontenddev | `skills/profile/SKILL.md` | 3, 10, 20, 23, 92, 105, 123, 129, 148, 169, 175, 183 |
| ☐ | frontenddev | `skills/profile/stacks/_CONTRACT.md` | 10 |
| ☐ | frontenddev | `skills/profile/templates/profile-template.md` | 1, 39, 60, 75, 92, 110, 125, 145, 170, 181, 194 |

`analyst` dan `quickdev`: nol rujukan `.claude/profile` (md_grep).

### Rencana perbaikan — Opsi B (alternatif): tetap `.claude/profile/` + field `plugin`

1. Template kedua plugin menambah `"plugin": "<plugin>"` di `index.json`.
2. `detect.read_profile()` hanya membaca lokasi lama. `owner_of()` (field `plugin`, atau keanggotaan `stack` untuk profil tanpa field) ≠ plugin sendiri → profil dianggap tidak ada, dan hook diam kecuali manifest mendeteksi stack plugin itu.
3. Semua skrip hilir: `index.json` milik plugin lain → FAIL `"profil milik <x>"` (satu check baru di tiap skrip; titik sentuh sama dengan tabel Python di atas, tetapi path tidak berubah).
4. Skill profile: prasyarat FAIL bila `.claude/profile/index.json` milik plugin lain. `force` tidak berlaku atasnya.
5. Migrasi: REFRESH kecil yang hanya menambah field `plugin` pada profil lama. Tidak ada pemindahan berkas.
6. Markdown: tidak perlu diganti massal. Cukup tambahkan kalimat kepemilikan di kedua `profile/SKILL.md` dan template.

Konsekuensi: monorepo fullstack **hanya bisa punya satu profil**. Plugin kedua selalu FAIL "profil milik plugin lain" dan tidak bisa dipakai di repo itu. Kriteria "Selesai bila" butir 3 tidak terpenuhi.

### Test yang ditambahkan

`tests/hooks/test_detect.py` (root repo, lintas plugin; fixture `make_repo(tmp_path, files)` dan `run_hook(plugin, cwd) -> dict | None`):
- `test_backend_profile_silences_frontend_hook` — fixture A1: hook frontenddev stdout kosong, exit 0.
- `test_frontend_profile_silences_backend_hook` — A2: hook backenddev stdout kosong.
- `test_fullstack_two_profiles_both_ok` — A3: kedua hook emit, `profile.state == "OK"`, `location == "own"`.
- `test_legacy_own_profile_offers_migrate` — A5: teks backenddev memuat `MIGRATE` dan tidak memuat `REFRESH`.
- `test_legacy_foreign_profile_ignored` — A4: frontenddev emit dari `apps/web/package.json` dan teks memuat `milik \`backenddev\``.

`src/plugins/frontenddev/tests/test_profile_preconditions.py`:
- `test_foreign_profile_in_own_dir_fails` — `.claude/profile/frontenddev/index.json` ber-`"plugin": "backenddev"` → exit 1, check kepemilikan FAIL.
- `test_legacy_own_profile_resolves_mode_migrate` — profil frontenddev di lokasi lama → `mode == "MIGRATE"` di `--json`.
- `test_legacy_backend_profile_is_not_refresh` — skenario C → mode `GENERATE`, bukan `REFRESH`.
- `test_profile_dir_other_value_rejected` — `--profile-dir docs/elsewhere` → FAIL (C10).

`src/plugins/backenddev/tests/test_profile_preconditions.py`:
- `test_frontend_only_repo_fails_check1` — skenario D → check 1 FAIL.
- `test_legacy_frontend_profile_not_refresh` — profil frontenddev di lokasi lama + manifest Go → mode `GENERATE`.
- `test_profile_dir_other_value_rejected` — B3.

`src/plugins/backenddev/tests/test_precondition_lib.py`:
- `test_resolve_profile_dir_prefers_new_location`, `test_resolve_profile_dir_ignores_foreign_legacy`.
- `test_profile_staleness_ignores_frontend_profile_commits` — commit ke `.claude/profile/frontenddev/` tidak mengubah vonis `BASI`.

`src/plugins/backenddev/tests/test_tech_lead_preconditions.py`:
- `test_reentry_allows_own_profile_dir_only` — `--re-entry` dengan berkas kotor di `.claude/profile/backenddev/` → check 3 PASS; di `.claude/profile/frontenddev/` → FAIL.

`src/plugins/{backenddev,frontenddev}/tests/test_migrate_profile.py`:
- `test_migrate_moves_only_own_files` — lokasi lama berisi index frontenddev + 4 `.md` sisa backenddev → 10 berkas pindah, 4 sisa dilaporkan, `plugin` tertulis.
- `test_migrate_refuses_foreign_profile` — exit ≠ 0.

`tests/test_profile_paths.py` (lint):
- `test_no_hardcoded_profile_path_in_python` — di luar `_common/precondition_lib.py` dan `hooks/detect.py`, nol kecocokan `"\.claude" / "profile"` dan `\.claude/profile"`.
- `test_markdown_profile_paths_namespaced` — tiap `.claude/profile` di markdown backenddev diikuti `/backenddev`, di frontenddev diikuti `/frontenddev`, kecuali baris yang memuat kata `MIGRATE`/`lokasi lama`.

### Verifikasi manual

1. Buat fixture monorepo fullstack skenario C tanpa profil. Pasang keempat plugin dari marketplace lokal (`/plugin marketplace add /home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow`).
2. `claude -p "Kutip verbatim baris kedua blok <backenddev-tech-lead-gate> dan <frontenddev-lead-gate> di konteksmu"` → keduanya ada dan masing-masing menyebut profil `.claude/profile/<plugin>/` BELUM ADA.
3. Di sesi interaktif: minta "profilkan repo ini untuk frontend", lalu "untuk backend". Kedua direktori terbentuk, dan `git log --stat` menunjukkan tidak ada berkas plugin lain yang tersentuh.
4. Ulangi dengan profil backenddev di lokasi lama. Permintaan kerja apa pun harus memicu tawaran MIGRATE, bukan REFRESH, dan tidak ada penimpaan.
5. Skenario C lama (profil backend di lokasi lama) + minta "refresh profil frontend" → `frontenddev:profile` menulis ke `.claude/profile/frontenddev/`. Berkas di `.claude/profile/` tidak berubah (`git status` bersih di luar direktori baru).

### Selesai bila

- Repo backend ber-profil backenddev → hook frontenddev tidak mengeluarkan apa pun (A1).
- Repo frontend ber-profil frontenddev → hook backenddev tidak mengeluarkan apa pun (A2).
- Monorepo fullstack: kedua profil hidup berdampingan, dan prasyarat `backenddev:tech-lead` check 1 serta `frontenddev:ux-design` check 5–6 sama-sama PASS (A3).
- Repo dengan profil di lokasi lama terdeteksi dan ditawari MIGRATE, tanpa penimpaan diam-diam (A4, A5).
- `frontenddev:profile` dengan `force: true` tidak pernah menimpa profil milik plugin lain.
- Kedua tabel checklist tercentang penuh dan test lint `tests/test_profile_paths.py` hijau.

### Risiko & catatan

- **Repo yang sudah di-onboard**: tanpa fallback baca (K2), semua repo lama langsung FAIL di setiap skrip sampai MIGRATE dijalankan. Dengan fallback, skrip tetap jalan dan mencetak catatan MIGRATE.
- **Profil yang sudah tertimpa** tidak bisa dipulihkan otomatis. Laporan MIGRATE harus menunjuk riwayat git.
- `git mv` meninggalkan penghapusan di lokasi lama. Zona re-entry tech-lead harus mengizinkan jalur lama selama MIGRATE (sub-tugas 2), lalu dicabut di rilis berikutnya.
- Perintah `perl` massal bisa mengubah contoh/penjelasan yang memang menyebut lokasi lama. Wajib tinjau diff.
- Versi plugin campuran (backenddev baru + frontenddev lama) masih bisa bentrok: frontenddev lama tetap menulis ke lokasi lama. Naikkan versi kedua plugin bersamaan (L7.1).

---

## L1.2 [Tinggi] Deteksi repo di hook berbasis grep dan tidak sama dengan versi Python

- [ ] Selesai

**Plugin:** backenddev, frontenddev · **Estimasi:** 2 hari · **Bergantung pada:** K1 (tata letak profil), K3–K6 · **Memblokir:** L1.1 bagian hook, L1.3 (teks di `gate_text.py`), L5.5, L6.1 (test hook)

### Konteks

Kedua hook adalah `sh` + `sed`/`grep`, sedangkan skrip prasyarat memakai Python dengan parser JSON. Dua detektor yang berselisih membuat repo lolos hook tetapi ditolak skrip (atau sebaliknya), tanpa pesan penyebab. Komentar hook sendiri (`tech-lead-gate.sh:64-66`) menyebut "gerbang yang diam adalah kegagalan yang paling mahal", padahal hook diam di subdirektori dan di path berkarakter khusus.

### Lokasi & kode saat ini

`src/plugins/backenddev/hooks/tech-lead-gate.sh:9-13` (juga `frontenddev/hooks/lead-gate.sh:10-14`) — cwd diambil dengan `sed` tanpa unescape JSON dan tanpa resolve toplevel git:
```sh
input=$(cat)

cwd=$(printf '%s' "$input" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
[ -n "${cwd:-}" ] || cwd=$PWD
[ -d "$cwd" ] || exit 0
```

`tech-lead-gate.sh:17-32` dan `:47-60` — `grep -E` tak berjangkar di seluruh isi manifest, hanya satu tingkat `*/`:
```sh
marker() {
  [ -f "$1" ] && grep -qE "$2" "$1"
}
...
    for _m in "$cwd"/*/"$_name"; do
...
elif marker_deep 'gin-gonic/gin|gofiber/fiber|labstack/echo|go-chi/chi|gorilla/mux|grpc-go' go.mod; then
  stack="go"
elif marker_deep 'hono|elysiajs' package.json && { [ -f "$cwd/bun.lockb" ] || [ -f "$cwd/bunfig.toml" ]; }; then
  stack="bun"
elif marker_deep '@nestjs/core|"express"|"fastify"|"koa"|@hapi/hapi' package.json; then
  stack="node"
elif marker_deep 'axum|actix-web|rocket|warp|poem' Cargo.toml; then
  stack="rust"
```

`tech-lead-gate.sh:67-69` (identik di `lead-gate.sh:66-68`) — escape JSON buatan sendiri, karakter kontrol lolos:
```sh
json_escape() {
  sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk '{ printf "%s%s", $0, "\\n" }'
}
```

`frontenddev/hooks/lead-gate.sh:23-38` — `"react":` di posisi mana pun (termasuk `overrides`, `peerDependenciesMeta`), tanpa syarat Vite:
```sh
has_dep() {
  [ -f "$1" ] && grep -qE "\"($2)\"[[:space:]]*:" "$1"
}
...
  if has_dep "$_pkg" 'svelte'; then printf 'svelte-vite'; return 0; fi
  if has_dep "$_pkg" 'react'; then printf 'react-vite'; return 0; fi
```

`frontenddev/skills/_common/precondition_lib.py:92-113` — klaim "byte-identik" yang tidak benar, dan `react` → `react-vite` tanpa Vite:
```python
def detect_stack(manifest: Path) -> Optional[str]:
    """Turunkan `<stack-id>` dari satu `package.json`, atau `None`.

    Urutan pemutus dari yang paling spesifik, **byte-identik** dengan
    `detect_stack()` di `hooks/lead-gate.sh`. ...
    """
    ...
    if "svelte" in deps:
        return "svelte-vite"
    if "react" in deps:
        return "react-vite"
    return None
```
Adapter justru mewajibkan Vite: `frontenddev/skills/profile/stacks/react-vite.md:9` ("`react` dan `react-dom` di `dependencies`, plus `vite` di `devDependencies` atau berkas `vite.config.{ts,js,mjs}`"), `stacks/svelte-vite.md:9`, `references/framework-matrix.md:43`.

Penanda backend di dokumen yang tidak sinkron dengan hook: `backenddev/skills/profile/stacks/bun.md:10-11` (paket `elysia`; "`hono` di atas Node adalah stack `node`"), `stacks/node.md:9-10` (penanda node tanpa `hono`), `stacks/rust.md:10` (`salvo` ada di adapter, tidak ada di hook), `stacks/go.md:10` (`grpc-go`, bukan path modul), `profile/SKILL.md:37-42`.

### Reproduksi

```bash
#!/usr/bin/env bash
# Reproduksi L1.2 — vonis hook (grep) vs vonis Python, per kasus.
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
P=$REPO/src/plugins
BE_HOOK=$P/backenddev/hooks/tech-lead-gate.sh
FE_HOOK=$P/frontenddev/hooks/lead-gate.sh
tmp=$(mktemp -d)

# Ringkas vonis hook: "-" bila stdout kosong; "JSON-RUSAK" bila stdout bukan JSON; selain itu potongan baris vonis.
hook() {  # $1=hook $2=json-stdin
  out=$(printf '%s' "$2" | sh "$1" 2>/dev/null)
  [ -z "$out" ] && { echo "-"; return; }
  printf '%s' "$out" | python3 -c '
import json,sys,re
try: ctx=json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"]
except Exception: print("JSON-RUSAK"); sys.exit()
l=ctx.splitlines()[1]
m=re.search(r"stack terdeteksi: ([^.]+)\.",l) or re.search(r"\(stack: ([^)]+)\)",l)
tag="BELUM-DIBUAT" if "BELUM DIBUAT" in l else "TIDAK-SAH" if "TIDAK SAH" in l else "TIDAK-LENGKAP" if "TIDAK LENGKAP" in l else "aktif"
print((m.group(1) if m else "?")+" ["+tag+"]")'
}
in_cwd() { python3 -c 'import json,sys; print(json.dumps({"cwd":sys.argv[1],"hook_event_name":"SessionStart","source":"startup"}))' "$1"; }
# Vonis Python frontenddev: detect_stack pada candidate_manifests dari toplevel git (sama dengan check_preconditions profile).
py_fe() { python3 - "$1" <<'PY'
import sys; from pathlib import Path
sys.path.insert(0, "/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow/src/plugins/frontenddev/skills/_common")
from precondition_lib import candidate_manifests, detect_stack, read_profile_stack
import subprocess
r=subprocess.run(["git","-C",sys.argv[1],"rev-parse","--show-toplevel"],capture_output=True,text=True)
root=Path(r.stdout.strip() or sys.argv[1]); prof=root/".claude/profile"
if (prof/"index.json").exists(): print("profil:"+(read_profile_stack(prof) or "''")); sys.exit()
hits=[s for s in (detect_stack(m) for m in candidate_manifests(root)) if s]
print(hits[0] if hits else "None")
PY
}
row() {  # $1=id $2=dir [$3=stdin-json override]
  local js=${3:-$(in_cwd "$2")}
  printf '%-4s | BE: %-26s | FE: %-26s | PyFE: %s\n' "$1" "$(hook "$BE_HOOK" "$js")" "$(hook "$FE_HOOK" "$js")" "$(py_fe "$2")"
}
mk() { rm -rf "$tmp/$1"; mkdir -p "$tmp/$1"; git init -q "$tmp/$1"; echo "$tmp/$1"; }
fe_full_profile() { mkdir -p "$1/.claude/profile"; for f in stack structure surface-map invariants commands layer-adoption visual drift manual-notes; do echo x > "$1/.claude/profile/$f.md"; done; }
VITE='"devDependencies":{"vite":"^6"}'

d=$(mk b1); echo "{\"dependencies\":{\"react\":\"^19\",\"react-dom\":\"^19\"},\"devDependencies\":{\"vite\":\"^6\",\"express\":\"^4\"}}" > $d/package.json; row B1 $d
d=$(mk b2); printf '[package]\nname = "poems-cli"\nversion = "0.1.0"\n\n[dependencies]\nclap = "4"\n' > $d/Cargo.toml; row B2 $d
d=$(mk b3); printf 'module example.com/rpc\n\ngo 1.22\n\nrequire google.golang.org/grpc v1.66.0\n' > $d/go.mod; row B3 $d
d=$(mk b4); echo '{"dependencies":{"hono":"^4","@hono/node-server":"^1"}}' > $d/package.json; row B4 $d
d=$(mk b5); echo '{"private":true,"workspaces":["apps/*"]}' > $d/package.json; mkdir -p $d/apps/api; echo '{"dependencies":{"express":"^4"}}' > $d/apps/api/package.json; row B5 $d
d=$(mk 'b6"q'); echo '{"dependencies":{"express":"^4"}}' > "$d/package.json"; row B6 "$d"
d=$(mk 'b6é'); echo '{"dependencies":{"express":"^4"}}' > "$d/package.json"; row B6u "$d" "$(python3 -c 'import json,sys; print(json.dumps({"cwd":sys.argv[1]}))' "$d")"
d=$(mk b7); echo '{"dependencies":{"express":"^4"}}' > $d/package.json; mkdir -p $d/.claude/profile; printf '{"stack":"no\tde"}\n' > $d/.claude/profile/index.json; row B7 $d
d=$(mk b8); echo '{"dependencies":{"elysia":"^1"}}' > $d/package.json; : > $d/bun.lockb; row B8 $d
d=$(mk b9); echo '{"dependencies":{"hono":"^4"}}' > $d/package.json; : > $d/bun.lock; row B9 $d
d=$(mk b10); echo '{"name":"ui-kit","keywords":["express","koa"],"dependencies":{"lodash":"^4"}}' > $d/package.json; row B10 $d
d=$(mk b11); mkdir -p $d/services/api; echo '{"dependencies":{"fastify":"^5"}}' > $d/services/api/package.json; row B11 $d
d=$(mk b12); printf '[package]\nname = "api"\n\n[dependencies]\nsalvo = "0.7"\n' > $d/Cargo.toml; row B12 $d
d=$(mk f1); echo '{"dependencies":{"express":"^4","react":"^19","@react-email/components":"^0.0.25"}}' > $d/package.json; row F1 $d
d=$(mk f2); echo '{"dependencies":{"lodash":"^4"},"overrides":{"react":"^19"}}' > $d/package.json; row F2 $d
d=$(mk f3); echo '{"name":"lib","peerDependenciesMeta":{"react":{"optional":true}}}' > $d/package.json; row F3 $d
d=$(mk f4); echo "{\"dependencies\":{\"react\":\"^19\"},$VITE}" > $d/package.json; fe_full_profile $d; printf '{\n  "stack": "react-vite",\n}\n' > $d/.claude/profile/index.json; row F4 $d
d=$(mk f5); echo "{\"dependencies\":{\"react\":\"^19\"},$VITE}" > $d/package.json; fe_full_profile $d; printf '{\n  "meta": {\n    "stack": "react-native"\n  },\n  "stack": "react-vite"\n}\n' > $d/.claude/profile/index.json; row F5 $d
d=$(mk f6); echo "{\"dependencies\":{\"react\":\"^19\"},$VITE}" > $d/package.json; mkdir -p $d/src/features; row F6 $d/src/features
d=$(mk 'f7\w'); echo "{\"dependencies\":{\"react\":\"^19\"},$VITE}" > "$d/package.json"; row F7 "$d"
d=$(mk f8); echo '{"dependencies":{"react":"^18","react-dom":"^18","react-scripts":"5.0.1"}}' > $d/package.json; row F8 $d
d=$(mk f9); echo '{"devDependencies":{"svelte":"^4","rollup":"^4","rollup-plugin-svelte":"^7"}}' > $d/package.json; row F9 $d
d=$(mk f10); mkdir -p $d/frontend $d/backend; echo "{\"dependencies\":{\"react\":\"^19\"},$VITE}" > $d/frontend/package.json; echo '{"dependencies":{"express":"^4"}}' > $d/backend/package.json; row F10 $d
rm -rf "$tmp"
```

Output aktual:
```
B1   | BE: node [aktif]               | FE: react-vite [BELUM-DIBUAT]  | PyFE: react-vite
B2   | BE: rust [aktif]               | FE: -                          | PyFE: None
B3   | BE: -                          | FE: -                          | PyFE: None
B4   | BE: -                          | FE: -                          | PyFE: None
B5   | BE: -                          | FE: -                          | PyFE: None
B6   | BE: -                          | FE: -                          | PyFE: None
B6u  | BE: -                          | FE: -                          | PyFE: None
B7   | BE: JSON-RUSAK                 | FE: JSON-RUSAK                 | PyFE: profil:''
B8   | BE: -                          | FE: -                          | PyFE: None
B9   | BE: -                          | FE: -                          | PyFE: None
B10  | BE: node [aktif]               | FE: -                          | PyFE: None
B11  | BE: -                          | FE: -                          | PyFE: None
B12  | BE: -                          | FE: -                          | PyFE: None
F1   | BE: node [aktif]               | FE: react-vite [BELUM-DIBUAT]  | PyFE: react-vite
F2   | BE: -                          | FE: react-vite [BELUM-DIBUAT]  | PyFE: None
F3   | BE: -                          | FE: react-vite [BELUM-DIBUAT]  | PyFE: None
F4   | BE: react-vite [aktif]         | FE: react-vite [aktif]         | PyFE: profil:''
F5   | BE: react-native [aktif]       | FE: react-native [aktif]       | PyFE: profil:react-vite
F6   | BE: -                          | FE: -                          | PyFE: react-vite
F7   | BE: -                          | FE: -                          | PyFE: react-vite
F8   | BE: -                          | FE: react-vite [BELUM-DIBUAT]  | PyFE: react-vite
F9   | BE: -                          | FE: svelte-vite [BELUM-DIBUAT] | PyFE: svelte-vite
F10  | BE: node [aktif]               | FE: -                          | PyFE: None
```

Uji tambahan (dijalankan): cwd `…/café` yang dikirim sebagai UTF-8 mentah (`json.dumps(..., ensure_ascii=False)`) → hook backenddev **menyala normal**. Yang gagal hanya bila dikirim ter-escape `\u00e9` (B6u).

**Koreksi terhadap ISSUES.md:**
- `:11` "karakter non-ASCII tertentu": hook hanya gagal bila cwd dikirim ter-escape `\uXXXX`. UTF-8 mentah lolos. Claude Code berbasis Node (`JSON.stringify` tidak meng-escape non-ASCII), jadi kasus ini kemungkinan jarang terjadi; bentuk persis input hook perlu dicek sekali di sesi nyata. `\"` (B6) dan backslash (F7, simulasi cwd Windows di Linux) tetap gagal, dan sudah direproduksi.
- `json_escape` rusak di **kedua** hook: frontenddev juga menghasilkan JSON rusak (B7). Pemicunya `index.json` dengan tab mentah di dalam string, yang berarti `index.json` itu sendiri sudah bukan JSON valid.
- **Temuan tambahan** (tidak ada di ISSUES, direproduksi): B8 — pola `elysiajs` bukan nama paket (paketnya `elysia`; `elysiajs` hanya cocok dengan plugin `@elysiajs/*`); B9 — lockfile teks Bun `bun.lock` tidak dikenali; B10 — kata `"express"`/`"koa"` di `keywords` dianggap dependensi; B11 — `services/api` (dua tingkat) tidak terdeteksi; B12 — `salvo` ada di adapter `rust.md:10` tetapi tidak di hook; F10 — tata letak `frontend/` + `backend/`: hook frontenddev diam.

### Tabel kasus salah deteksi (skenario test)

"Sekarang" = output reproduksi di atas. "Seharusnya" = vonis yang ditagih test. "Prototipe" = hasil `proto/hooks/detect.py` (kode di sub-tugas 1) lewat `proto-matrix.sh`, **dijalankan**. Format prototipe: `stack @sumber status-profil/lokasi`.

| ID | Input (fixture) | Sekarang BE / FE / Py-FE | Seharusnya | Prototipe BE / FE |
|---|---|---|---|---|
| B1 | React+Vite, `express` di `devDependencies` | node / react-vite / react-vite | BE diam; FE react-vite | - / react-vite @package.json |
| B2 | Cargo `name = "poems-cli"`, dep `clap` | rust / - / None | keduanya diam | - / - |
| B3 | go.mod `require google.golang.org/grpc` | - / - / None | BE go | go @go.mod / - |
| B4 | `hono` + `@hono/node-server`, tanpa lockfile Bun | - / - / None | BE node (K3) | node @package.json / - |
| B5 | root `workspaces: ["apps/*"]`, `apps/api` express | - / - / None | BE node @apps/api | node @apps/api/package.json / - |
| B6 | express, cwd memuat `"` | - / - / None | BE node | node @package.json / - |
| B6u | express, cwd `\u00e9` ter-escape | - / - / None | BE node | node @package.json / - |
| B7 | express + `index.json` lama dengan tab mentah | JSON-RUSAK / JSON-RUSAK / `''` | stdout JSON valid; BE node + catatan index.json rusak; FE diam | node @package.json INVALID_JSON/legacy / - |
| B8 | `elysia` + `bun.lockb` | - / - / None | BE bun | bun / - |
| B9 | `hono` + `bun.lock` | - / - / None | BE bun | bun / - |
| B10 | `keywords: ["express","koa"]`, dep lodash | node / - / None | keduanya diam | - / - |
| B11 | `services/api` fastify | - / - / None | BE node @services/api | node @services/api/package.json / - |
| B12 | Cargo dep `salvo` | - / - / None | BE rust | rust @Cargo.toml / - |
| F1 | Express + `react` (email templating), tanpa Vite | node / react-vite / react-vite | BE node; FE diam (K4) | node / - |
| F2 | `react` hanya di `overrides` | - / react-vite / None | keduanya diam | - / - |
| F3 | `react` hanya di `peerDependenciesMeta` | - / react-vite / None | keduanya diam | - / - |
| F4 | profil frontenddev, `index.json` bukan JSON valid | react-vite aktif / react-vite aktif / `''` | FE: index.json TIDAK SAH (bukan JSON) → REFRESH; BE diam | - / INVALID_JSON/own |
| F5 | `index.json` dengan `stack` bersarang lebih dulu | react-native / react-native / react-vite | FE react-vite (sama dengan Python) | - / react-vite @profile OK/own |
| F6 | sesi dimulai di `repo/src/features` | - / - / react-vite | FE react-vite (toplevel git) | - / react-vite @package.json |
| F7 | cwd mengandung backslash (simulasi Windows) | - / - / react-vite | FE react-vite | - / react-vite @package.json |
| F8 | CRA (`react-scripts`, tanpa Vite) | - / react-vite / react-vite | diam, alasan `cra` (K4) | - / - |
| F9 | Svelte + Rollup, tanpa Vite | - / svelte-vite / svelte-vite | diam, alasan `svelte-tanpa-vite` (K4) | - / - |
| F10 | `frontend/` React+Vite + `backend/` express | node / - / None | BE node @backend; FE react-vite @frontend (K5) | node @backend/package.json / react-vite @frontend/package.json |

Tabel A1–A6 (tata letak Opsi A, L1.1) dan Q1–Q2 (opt-out, L1.3) dijalankan dengan prototipe yang sama:

| ID | Input | Prototipe BE / FE | Sesuai target |
|---|---|---|---|
| A1 | Go + `.claude/profile/backenddev/` | go @profile OK/own / - | ya |
| A2 | React+Vite + `.claude/profile/frontenddev/` | - / react-vite @profile OK/own | ya |
| A3 | fullstack + kedua profil | node @profile OK/own / react-vite @profile OK/own | ya |
| A4 | fullstack + profil backend di lokasi lama | node @profile OK/legacy / react-vite @apps/web/package.json OTHER_OWNER/legacy | ya |
| A5 | Go + profil backend di lokasi lama | go @profile OK/legacy / - | ya |
| A6 | React+Vite + `.claude/profile/backenddev/` ber-`"plugin":"frontenddev"` | - / react-vite @package.json | ya (profil salah tempat diabaikan) |
| Q1 | express + `.claude/workflow` = `quickdev` | - / - | ya |
| Q2 | React+Vite + `.claude/workflow` = `frontenddev quickdev` | - / react-vite | ya |

### Dampak

Pengguna diarahkan ke gerbang yang salah (B1, B10, F1–F3, F8, F9). Dua gerbang wajib menyala bersamaan (B1, F1). Repo yang semestinya dilayani tidak digerbangi sama sekali (B3–B6, B8, B9, B11, B12, F6, F7, F10). JSON rusak membuat konteks tidak tersuntik atau tersuntik sebagai teks mentah (B7). Hook dan skrip memberi vonis berbeda tanpa pesan (F2–F7).

### Rencana perbaikan

1. **`hooks/detect.py` baru, identik byte-per-byte di `backenddev/hooks/` dan `frontenddev/hooks/`.** File ini berisi seluruh logika deteksi (manifest, monorepo, profil, opt-out) dan dipakai hook sekaligus skrip. Teks milik tiap plugin dipisah ke `hooks/gate_text.py`. Prototipe di bawah sudah dijalankan pada tabel kasus (`proto/hooks/detect.py`; 0,07 detik di repo ini).

   Soal reuse `precondition_lib`: arah impornya **dibalik**. `precondition_lib.py` tiap plugin mengimpor `detect.py` (sub-tugas 4), bukan sebaliknya. Alasannya: `detect.py` harus identik di kedua plugin, sedangkan kedua `precondition_lib.py` berbeda isi. Dengan arah ini, `detect_stack()` di skrip adalah fungsi yang sama dengan yang dipakai hook.

   ```python
   #!/usr/bin/env python3
   """Deteksi repo untuk hook SessionStart `backenddev` dan `frontenddev`.

   Berkas ini IDENTIK byte-per-byte di `backenddev/hooks/detect.py` dan
   `frontenddev/hooks/detect.py` (ditegakkan `test_detect_py_identik`). Teks
   gerbang milik tiap plugin ada di `hooks/gate_text.py` masing-masing. Skrip
   prasyarat mengimpor fungsi deteksi dari sini lewat
   `skills/_common/precondition_lib.py`, sehingga vonis hook = vonis skrip.

   Standard library saja. `tomllib` dipakai bila ada (Python >= 3.11).
   """
   from __future__ import annotations

   import argparse
   import json
   import re
   import subprocess
   import sys
   import xml.etree.ElementTree as ET
   from dataclasses import asdict, dataclass, field
   from pathlib import Path
   from typing import List, Optional, Set, Tuple

   try:
       import tomllib  # Python >= 3.11
   except ImportError:  # pragma: no cover
       tomllib = None

   PLUGINS = ("backenddev", "frontenddev")
   STACKS = {
       "backenddev": ("java-spring", "go", "node", "bun", "rust", "php", "php-codeigniter"),
       "frontenddev": ("react-vite", "react-native", "sveltekit", "svelte-vite"),
   }
   PROFILE_ROOT = Path(".claude") / "profile"          # Opsi A: <root>/.claude/profile/<plugin>/
   PROFILE_FILES = {
       "backenddev": ("index.json", "stack.md", "module-structure.md", "domain-map.md",
                      "surface-map.md", "code-conventions.md", "anti-patterns.md",
                      "invariants.md", "commands.md"),
       "frontenddev": ("index.json", "stack.md", "structure.md", "surface-map.md",
                       "invariants.md", "commands.md", "layer-adoption.md", "visual.md",
                       "drift.md", "manual-notes.md"),
   }
   OPT_FILE = Path(".claude") / "workflow"              # L1.3: daftar plugin yang boleh menggerbangi repo
   SKIP_DIRS = {"node_modules", "vendor", "target", "build", "dist", "out", ".git", "docs",
                "example", "examples", "fixtures", "test", "tests", "e2e", "playground", "demo"}
   CONVENTIONAL = ("apps/*", "packages/*", "services/*")
   MAX_CANDIDATES = 200

   NODE_SERVER = {"@nestjs/core", "express", "fastify", "koa", "@hapi/hapi", "hono"}
   BUN_MARKERS = ("bun.lockb", "bun.lock", "bunfig.toml")
   GO_SERVER = ("github.com/gin-gonic/gin", "github.com/gofiber/fiber", "github.com/labstack/echo",
                "github.com/go-chi/chi", "github.com/gorilla/mux", "google.golang.org/grpc")
   RUST_SERVER = {"axum", "actix-web", "rocket", "warp", "poem", "salvo"}
   PHP_FRAMEWORK = {"laravel/framework", "symfony/framework-bundle", "slim/slim",
                    "laminas/laminas-mvc", "yiisoft/yii2"}
   GRADLE_FILES = ("build.gradle", "build.gradle.kts", "gradle/libs.versions.toml")


   @dataclass
   class Hit:
       path: str   # manifest relatif root, mis. "apps/api/package.json"
       stack: str


   @dataclass
   class Profile:
       state: str                  # ABSENT | OK | INVALID_JSON | NO_STACK | UNKNOWN_STACK | INCOMPLETE | OTHER_OWNER
       location: str = ""          # own | legacy | ""
       stack: str = ""
       owner: str = ""
       missing: List[str] = field(default_factory=list)


   @dataclass
   class Verdict:
       plugin: str
       root: str
       emit: bool = False
       stack: str = ""
       source: str = ""            # "profile" atau path manifest
       profile: Profile = field(default_factory=lambda: Profile("ABSENT"))
       hits: List[Hit] = field(default_factory=list)
       out_of_scope: List[Hit] = field(default_factory=list)   # frontenddev: next/cra/tanpa-vite
       opted_out: bool = False


   # ------------------------------------------------------------------ manifest

   def _json(path: Path) -> Optional[dict]:
       try:
           data = json.loads(path.read_text(encoding="utf-8-sig"))
       except (OSError, ValueError):
           return None
       return data if isinstance(data, dict) else None


   def _keys(data: dict, *fields: str) -> Set[str]:
       out: Set[str] = set()
       for name in fields:
           block = data.get(name)
           if isinstance(block, dict):
               out.update(k for k in block if isinstance(k, str))
       return out


   def backend_from_package(pkg: Path, root: Path) -> Optional[str]:
       """Backend hanya dari `dependencies`; devDependencies/overrides/peer tidak dihitung."""
       data = _json(pkg)
       if data is None:
           return None
       deps = _keys(data, "dependencies")
       bun = any((d / m).is_file() for d in {pkg.parent, root} for m in BUN_MARKERS)
       if not deps & {"@nestjs/core", "express"} and ("elysia" in deps or (bun and "hono" in deps)):
           return "bun"
       return "node" if deps & NODE_SERVER else None


   def go_requires(gomod: Path) -> Set[str]:
       """Path modul di `require` (tunggal maupun blok), tanpa `// indirect`."""
       try:
           lines = gomod.read_text(encoding="utf-8").splitlines()
       except OSError:
           return set()
       mods: Set[str] = set()
       block = False
       for raw in lines:
           indirect = "// indirect" in raw
           line = raw.split("//", 1)[0].strip()
           if block:
               if line == ")":
                   block = False
                   continue
               body = line
           elif line.startswith("require"):
               body = line[len("require"):].strip()
               if body == "(":
                   block = True
                   continue
           else:
               continue
           parts = body.split()
           if len(parts) >= 2 and not indirect:
               mods.add(parts[0])
       return mods


   def _go_match(mod: str, marker: str) -> bool:
       return mod == marker or (mod.startswith(marker + "/v") and mod[len(marker) + 2:].isdigit())


   def cargo_deps(cargo: Path) -> Set[str]:
       """Nama crate di [dependencies], [workspace.dependencies], [target.*.dependencies]."""
       try:
           text = cargo.read_text(encoding="utf-8")
       except OSError:
           return set()
       if tomllib is None:
           return _cargo_deps_fallback(text)
       try:
           data = tomllib.loads(text)
       except tomllib.TOMLDecodeError:
           return set()
       tables = [data.get("dependencies"), (data.get("workspace") or {}).get("dependencies")]
       tables += [t.get("dependencies") for t in (data.get("target") or {}).values() if isinstance(t, dict)]
       names: Set[str] = set()
       for table in tables:
           if isinstance(table, dict):
               for key, val in table.items():
                   names.add(val.get("package", key) if isinstance(val, dict) else key)
       return names


   def _cargo_deps_fallback(text: str) -> Set[str]:  # Python < 3.11
       names: Set[str] = set()
       in_deps = False
       for line in text.splitlines():
           s = line.strip()
           if s.startswith("["):
               hdr = s.strip("[]").split("#", 1)[0].strip()
               in_deps = hdr in ("dependencies", "workspace.dependencies") or (
                   hdr.startswith("target.") and hdr.endswith(".dependencies"))
               if hdr.startswith("dependencies."):
                   names.add(hdr.split(".", 1)[1].strip('"'))
               continue
           m = re.match(r"([A-Za-z0-9_-]+)\s*=", s)
           if in_deps and m:
               names.add(m.group(1))
       return names


   def backend_from_composer(path: Path) -> Optional[str]:
       data = _json(path)
       if data is None:
           return None
       req = {k.lower() for k in _keys(data, "require")}
       if "codeigniter4/framework" in req:
           return "php-codeigniter"
       return "php" if req & PHP_FRAMEWORK else None


   def _pom_is_spring(pom: Path) -> bool:
       try:
           tree = ET.parse(pom)
       except (ET.ParseError, OSError):
           return False
       return any(el.tag.rsplit("}", 1)[-1] == "groupId"
                  and (el.text or "").strip() == "org.springframework.boot" for el in tree.iter())


   def _gradle_is_spring(path: Path) -> bool:
       try:
           text = path.read_text(encoding="utf-8")
       except OSError:
           return False
       text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
       lines = [ln.split("//", 1)[0].split("#", 1)[0] if path.suffix == ".toml" else ln.split("//", 1)[0]
                for ln in text.splitlines()]
       return re.search(r"org\.springframework\.boot", "\n".join(lines)) is not None


   def frontend_from_package(pkg: Path) -> Tuple[Optional[str], str]:
       """(stack, alasan_di_luar_cakupan). Penanda Vite wajib untuk react-vite/svelte-vite."""
       data = _json(pkg)
       if data is None:
           return None, "manifest-rusak" if pkg.is_file() else ""
       deps = _keys(data, "dependencies", "devDependencies")
       if "next" in deps:
           return None, "next"
       if deps & {"react-native", "expo"}:
           return "react-native", ""
       if "@sveltejs/kit" in deps:
           return "sveltekit", ""
       vite = "vite" in deps or any(pkg.parent.glob("vite.config.*"))
       if "svelte" in deps:
           return ("svelte-vite", "") if vite else (None, "svelte-tanpa-vite")
       if "react" in deps:
           if vite:
               return "react-vite", ""
           return None, "cra" if "react-scripts" in deps else "react-tanpa-vite"
       return None, ""


   # ------------------------------------------------------------------ monorepo

   def _workspace_globs(root: Path) -> List[str]:
       globs: List[str] = []
       ws = (_json(root / "package.json") or {}).get("workspaces")
       if isinstance(ws, dict):
           ws = ws.get("packages")
       if isinstance(ws, list):
           globs += [w for w in ws if isinstance(w, str)]
       pnpm = root / "pnpm-workspace.yaml"
       if pnpm.is_file():
           inside = False
           for line in pnpm.read_text(encoding="utf-8", errors="replace").splitlines():
               if re.match(r"^packages\s*:", line):
                   inside = True
                   continue
               m = re.match(r"""^\s*-\s*['"]?([^'"#]+?)['"]?\s*(#.*)?$""", line)
               if inside and m:
                   globs.append(m.group(1))
               elif inside and line.strip() and not line[0].isspace():
                   inside = False
       gowork = root / "go.work"
       if gowork.is_file():
           text = gowork.read_text(encoding="utf-8", errors="replace")
           for blk in re.findall(r"^use\s*\(([^)]*)\)", text, flags=re.M):
               globs += [ln.split("//", 1)[0].strip() for ln in blk.splitlines() if ln.strip()]
           globs += re.findall(r"^use\s+([^\s(]+)", text, flags=re.M)
       cargo = root / "Cargo.toml"
       if tomllib is not None and cargo.is_file():
           try:
               members = tomllib.loads(cargo.read_text(encoding="utf-8")).get("workspace", {}).get("members", [])
               globs += [m for m in members if isinstance(m, str)]
           except (OSError, tomllib.TOMLDecodeError):
               pass
       return globs


   def candidate_dirs(root: Path) -> List[Path]:
       """Root, workspace terdeklarasi, apps/packages/services, lalu anak langsung root."""
       seen: Set[Path] = set()
       out: List[Path] = []

       def add(d: Path) -> None:
           if len(out) >= MAX_CANDIDATES or d in seen or not d.is_dir():
               return
           parts = d.relative_to(root).parts
           if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
               return
           seen.add(d)
           out.append(d)

       add(root)
       for pat in _workspace_globs(root) + list(CONVENTIONAL):
           pat = pat.strip().replace("**", "*")
           while pat.startswith("./"):
               pat = pat[2:]
           pat = pat.rstrip("/")
           if pat and not pat.startswith(("!", "/", "..")):
               for d in sorted(root.glob(pat)):
                   add(d)
       for d in sorted(p for p in root.iterdir() if p.is_dir()):
           add(d)
       return out


   def detect_backend(root: Path) -> List[Hit]:
       hits: List[Hit] = []
       for d in candidate_dirs(root):
           rel = lambda name: (d / name).relative_to(root).as_posix()  # noqa: E731
           if (d / "pom.xml").is_file() and _pom_is_spring(d / "pom.xml"):
               hits.append(Hit(rel("pom.xml"), "java-spring"))
           else:
               for g in GRADLE_FILES:
                   if (d / g).is_file() and _gradle_is_spring(d / g):
                       hits.append(Hit(rel(g), "java-spring"))
                       break
           if (d / "go.mod").is_file() and any(_go_match(m, k) for m in go_requires(d / "go.mod") for k in GO_SERVER):
               hits.append(Hit(rel("go.mod"), "go"))
           stack = backend_from_package(d / "package.json", root) if (d / "package.json").is_file() else None
           if stack:
               hits.append(Hit(rel("package.json"), stack))
           if (d / "Cargo.toml").is_file() and cargo_deps(d / "Cargo.toml") & RUST_SERVER:
               hits.append(Hit(rel("Cargo.toml"), "rust"))
           stack = backend_from_composer(d / "composer.json") if (d / "composer.json").is_file() else None
           if stack:
               hits.append(Hit(rel("composer.json"), stack))
       return hits


   def detect_frontend(root: Path) -> Tuple[List[Hit], List[Hit]]:
       hits: List[Hit] = []
       skipped: List[Hit] = []
       for d in candidate_dirs(root):
           pkg = d / "package.json"
           if not pkg.is_file():
               continue
           stack, why = frontend_from_package(pkg)
           rel = pkg.relative_to(root).as_posix()
           if stack:
               hits.append(Hit(rel, stack))
           elif why:
               skipped.append(Hit(rel, why))
       return hits, skipped


   # ------------------------------------------------------------------ profil

   def read_index(path: Path) -> Tuple[Optional[dict], str]:
       try:
           raw = path.read_text(encoding="utf-8-sig")
       except FileNotFoundError:
           return None, "ABSENT"
       except OSError:
           return None, "INVALID_JSON"
       try:
           data = json.loads(raw)
       except ValueError:
           return None, "INVALID_JSON"
       return (data, "OK") if isinstance(data, dict) else (None, "INVALID_JSON")


   def owner_of(data: dict) -> str:
       """Field `plugin` bila ada; profil lama tanpa field → dari keanggotaan `stack`."""
       if data.get("plugin") in PLUGINS:
           return data["plugin"]
       for plugin, stacks in STACKS.items():
           if data.get("stack") in stacks:
               return plugin
       return ""


   def _grade(d: Path, plugin: str, data: dict, location: str) -> Profile:
       stack = data.get("stack")
       stack = stack.strip() if isinstance(stack, str) else ""
       owner = data.get("plugin") or plugin
       if owner != plugin:
           return Profile("OTHER_OWNER", location, stack, owner)
       if not stack:
           return Profile("NO_STACK", location)
       if stack not in STACKS[plugin]:
           return Profile("UNKNOWN_STACK", location, stack, plugin)
       missing = [f for f in PROFILE_FILES[plugin] if not (d / f).is_file()]
       return Profile("INCOMPLETE" if missing else "OK", location, stack, plugin, missing)


   def read_profile(root: Path, plugin: str) -> Profile:
       own = root / PROFILE_ROOT / plugin
       data, st = read_index(own / "index.json")
       if st == "INVALID_JSON":
           return Profile("INVALID_JSON", "own")
       if data is not None:
           return _grade(own, plugin, data, "own")
       legacy = root / PROFILE_ROOT
       data, st = read_index(legacy / "index.json")
       if st != "OK":
           return Profile(st, "legacy" if st == "INVALID_JSON" else "")
       owner = owner_of(data)
       if owner != plugin:
           return Profile("OTHER_OWNER", "legacy", str(data.get("stack", "")), owner)
       return _grade(legacy, plugin, data, "legacy")


   # ------------------------------------------------------------------ vonis

   def opted_out(root: Path, plugin: str) -> bool:
       try:
           words = (root / OPT_FILE).read_text(encoding="utf-8").split()
       except OSError:
           return False
       return plugin not in words


   def evaluate(root: Path, plugin: str) -> Verdict:
       v = Verdict(plugin=plugin, root=str(root))
       if opted_out(root, plugin):
           v.opted_out = True
           return v
       v.profile = read_profile(root, plugin)
       if plugin == "backenddev":
           v.hits = detect_backend(root)
       else:
           v.hits, v.out_of_scope = detect_frontend(root)
       legacy_broken = v.profile.location == "legacy" and v.profile.state == "INVALID_JSON"
       if v.profile.state not in ("ABSENT", "OTHER_OWNER") and not legacy_broken:
           v.emit, v.stack, v.source = True, v.profile.stack, "profile"
       elif v.hits:
           v.emit, v.stack, v.source = True, v.hits[0].stack, v.hits[0].path
       return v


   def resolve_root(cwd: str) -> Optional[Path]:
       p = Path(cwd).expanduser() if cwd else Path.cwd()
       if not p.is_dir():
           return None
       try:
           out = subprocess.run(["git", "-C", str(p), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True, timeout=2)
           if out.returncode == 0 and out.stdout.strip():
               return Path(out.stdout.strip())
       except (OSError, subprocess.SubprocessError):
           pass
       return p.resolve()


   def emit(text: str) -> None:
       payload = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}
       sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


   def main(argv: Optional[List[str]] = None) -> int:
       ap = argparse.ArgumentParser(description="Deteksi repo untuk hook SessionStart")
       ap.add_argument("--plugin", required=True, choices=PLUGINS)
       ap.add_argument("--explain", action="store_true", help="cetak Verdict mentah (debug/test)")
       args = ap.parse_args(argv)
       try:
           data = json.load(sys.stdin)
       except (ValueError, OSError):
           data = {}
       cwd = data.get("cwd") if isinstance(data, dict) else None
       root = resolve_root(cwd if isinstance(cwd, str) else "")
       if root is None:
           return 0
       try:
           verdict = evaluate(root, args.plugin)
       except Exception as exc:  # noqa: BLE001 — gerbang yang diam paling mahal
           print(f"detect.py: {exc!r}", file=sys.stderr)
           if (root / PROFILE_ROOT / args.plugin).is_dir():
               emit(f"<{args.plugin}-gate>\nDeteksi hook gagal ({exc!r}). Jalankan skrip "
                    f"prasyarat skill secara manual sebelum merutekan kerja.\n</{args.plugin}-gate>")
           return 0
       if args.explain:
           print(json.dumps(asdict(verdict), ensure_ascii=False, indent=2))
           return 0
       if verdict.emit:
           sys.path.insert(0, str(Path(__file__).resolve().parent))
           from gate_text import render  # teks milik plugin ini
           emit(render(verdict))
       return 0


   if __name__ == "__main__":
       sys.exit(main())
   ```

   Pemetaan kebutuhan → kode: stdin `json.load` (`main`); toplevel git dengan fallback cwd (`resolve_root`); `package.json` backend hanya dari `dependencies`, frontend dari `dependencies`+`devDependencies` dengan penanda Vite (`backend_from_package`, `frontend_from_package`); `Cargo.toml` via `tomllib` + fallback (`cargo_deps`); `go.mod` `require` persis + sufiks `/vN` (`go_requires`, `_go_match`); `composer.json` `require` (`backend_from_composer`); `pom.xml` via `ElementTree` dan Gradle tanpa komentar (`_pom_is_spring`, `_gradle_is_spring`); monorepo (`_workspace_globs`: `workspaces`, `pnpm-workspace.yaml`, `go.work`, Cargo `members`; `candidate_dirs`: + `apps|packages|services/*` + anak langsung root); keluaran `json.dumps` (`emit`).

2. **`hooks/gate_text.py` per plugin** (teks saja; bukan identik). Versi backenddev (sudah memuat teks LEWATI L1.3 dan kalimat profil L1.4):
   ```python
   """Teks gerbang SessionStart `backenddev`. Hanya teks — semua keputusan ada di `detect.py`."""

   PROFILE_DIR = ".claude/profile/backenddev/"

   RULES = """`backenddev:tech-lead` jalan lebih dulu untuk tiap permintaan kerja baru — panggil lewat tool Skill
   sebelum skill backenddev lain, sebelum menelusuri repo, sebelum menulis kode. Gerbang sendiri yang
   explore kodenya lalu bertanya; rute diputuskan sesudah itu, bukan sebelum.

   WAJIB lewat gerbang:
   - permintaan kerja apa pun: memahami, mengubah, menambah, memperbaiki, mengaudit, mendokumentasikan
   - susulan di tengah sesi, sekecil apa pun — "sekalian ganti X", "oh iya Y juga"
   - menjalankan artefak backenddev yang sudah ada (brief, `TASK.md`, `RCA.md`) — apa pun statusnya

   LEWATI hanya empat:
   - jawaban user yang memasok informasi ke rute yang sudah diputuskan gerbang di giliran sebelumnya
   - pertanyaan pengetahuan umum yang tidak menyentuh repo
   - operasi VCS (commit, push, PR, rebase, diff) atas kerja yang sudah selesai
   - permintaan yang memanggil atau melanjutkan alur plugin lain secara eksplisit — `/analyst:*`,
     `/quickdev:*`, atau susulan di tengah skill `analyst:*`/`quickdev:*` yang sedang berjalan
     (elisitasi tiket, `plan/<task>.md`). Kerja itu milik plugin tersebut sampai user sendiri meminta
     pindah ke gerbang ini.

   Pengingat ini disuntik sekali per sesi, tidak diulang tiap giliran. Berlaku sama di permintaan ke-1
   dan ke-40; jaraknya dari prompt yang sedang kamu baca bukan tanda ia kedaluwarsa."""


   def _profile_note(v) -> str:
       p = v.profile
       if p.state == "OK" and p.location == "own":
           return (f"Profil `{PROFILE_DIR}` ADA. Isinya sengaja tidak disalin ke sini: skill yang "
                   "membutuhkannya membaca berkasnya sendiri, supaya yang terbaca selalu versi terakhir.")
       if p.location == "legacy" and p.state in ("OK", "INCOMPLETE"):
           return ("Profil backenddev masih di lokasi lama `.claude/profile/`. Gerbang merutekan "
                   f"`backenddev:profile` mode MIGRATE (pindah ke `{PROFILE_DIR}`) sebelum rute lain; "
                   "dilarang REFRESH atau GENERATE di atasnya.")
       if p.state in ("ABSENT", "OTHER_OWNER"):
           note = (f"Profil `{PROFILE_DIR}` BELUM ADA. Permintaan kerja tetap lewat `backenddev:tech-lead`; "
                   "gerbang merutekan `backenddev:profile` (GENERATE) lebih dulu, lalu melanjutkan rute tertunda.")
           if p.state == "OTHER_OWNER":
               note += (f" `.claude/profile/` berisi profil milik `{p.owner}` (stack `{p.stack}`) — "
                        "biarkan; jangan dibaca sebagai profil backenddev, jangan ditimpa.")
           return note
       if p.state == "INVALID_JSON":
           where = PROFILE_DIR if p.location == "own" else ".claude/profile/"
           return (f"`{where}index.json` bukan JSON valid; semua skrip prasyarat backenddev akan FAIL. "
                   "Gerbang merutekan `backenddev:profile` mode REFRESH sebelum rute lain.")
       if p.state in ("NO_STACK", "UNKNOWN_STACK"):
           return (f"`{PROFILE_DIR}index.json` TIDAK SAH: field `stack` = `{p.stack or 'kosong'}`, di luar "
                   "java-spring, go, node, bun, rust, php, php-codeigniter. Gerbang merutekan "
                   "`backenddev:profile` mode REFRESH sebelum rute lain.")
       return (f"Profil `{PROFILE_DIR}` TIDAK LENGKAP, berkas hilang: {', '.join(p.missing)}. "
               "Gerbang merutekan `backenddev:profile` mode REFRESH sebelum rute lain.")


   def render(v) -> str:
       head = f"Repo backend, stack terdeteksi: {v.stack or 'tidak terbaca'} (sumber: {v.source}). Plugin `backenddev` aktif."
       extra = [f"{h.path} → {h.stack}" for h in v.hits[1:4]]
       if extra:
           head += " Kandidat lain: " + "; ".join(extra) + "."
       return "\n\n".join(["<backenddev-tech-lead-gate>\n" + head, _profile_note(v), RULES + "\n</backenddev-tech-lead-gate>"])
   ```
   Versi frontenddev (`proto/fe/gate_text.py`) berstruktur sama. Perbedaannya: `PROFILE_DIR = ".claude/profile/frontenddev/"`, tag `<frontenddev-lead-gate>`, paragraf aturan lama `lead-gate.sh:115-125` dengan butir LEWATI keempat, setiap cabang profil berbunyi "Permintaan kerja tetap lewat `frontenddev:lead`; lead merutekan lane PROFILE …" (L1.4), cabang `OTHER_OWNER` menambahkan "`force: true` tidak berlaku atasnya", dan kandidat monorepo menambahkan "pilih `target_app` di lead". Kedua renderer sudah dijalankan untuk ketujuh status profil; keluarannya lolos `python3 -m json.tool`.

3. **`hooks/hooks.json` kedua plugin**:
   ```diff
   -            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/tech-lead-gate.sh",
   +            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/detect.py\" --plugin backenddev",
                "timeout": 5
   ```
   (frontenddev: `--plugin frontenddev`.) Matcher `startup|resume|clear|compact` tetap.

4. **Hapus** `backenddev/hooks/tech-lead-gate.sh` dan `frontenddev/hooks/lead-gate.sh`.

5. **`frontenddev/skills/_common/precondition_lib.py`**: ganti `_deps`/`detect_stack`/`is_next`/`candidate_manifests` (`:76-135`) dengan pembungkus. Diff ini sudah diterapkan dan dijalankan di salinan scratchpad `fe-copy/`: F1 dan F8 → FAIL, B1 dan F10 → PASS.
   ```python
   # Deteksi stack tinggal di `hooks/detect.py` (identik di kedua plugin) — satu
   # implementasi untuk hook dan skrip, sehingga vonis keduanya tidak bisa berselisih.
   sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
   import detect as _detect  # noqa: E402


   def detect_stack(manifest: Path) -> Optional[str]:
       """`<stack-id>` dari satu `package.json`, atau `None` (lihat `detect.frontend_from_package`)."""
       return _detect.frontend_from_package(manifest)[0]


   def is_next(manifest: Path) -> bool:
       return _detect.frontend_from_package(manifest)[1] == "next"


   def out_of_scope_reason(manifest: Path) -> str:
       """`next` | `cra` | `react-tanpa-vite` | `svelte-tanpa-vite` | `manifest-rusak` | ''."""
       return _detect.frontend_from_package(manifest)[1]


   def candidate_manifests(root: Path) -> list:
       """Manifest yang diperiksa hook dan skrip: urutan `detect.candidate_dirs`."""
       return [d / "package.json" for d in _detect.candidate_dirs(root) if (d / "package.json").is_file()]
   ```
   Tambahkan `import sys`. `read_profile_stack()` memakai `_detect.read_index()`. `frontenddev/skills/profile/scripts/check_preconditions.py:132-144` memakai `out_of_scope_reason` agar pesan FAIL menyebut sebabnya ("CRA/tanpa Vite di luar cakupan"). Pesan `:111` ("nol `package.json` di root maupun `apps/*`, `packages/*`") disesuaikan dengan kandidat baru. Hapus klaim "byte-identik" di docstring `:11-14` dan `:95-98`.

6. **backenddev**: `skills/_common/precondition_lib.py` mendapat impor `detect` yang sama (lihat L1.1 sub-tugas 1). `skills/profile/scripts/check_preconditions.py:76-112` (check 1) diganti:
   ```python
       def _check_1_backend_manifest(self):
           hits = _detect.detect_backend(self.root)
           if not hits:
               self.results.append({"id": 1, "name": "Backend Manifest Detection", "status": "FAIL",
                   "summary": "Nol penanda framework server backend di root, workspace, apps/*, packages/*, services/*",
                   "action": "Repo bukan target backenddev; jangan buat profil."})
               return
           stacks = sorted({h.stack for h in hits})
           summary = ", ".join(f"{h.path} → {h.stack}" for h in hits[:4])
           self.results.append({"id": 1, "name": "Backend Manifest Detection",
               "status": "PASS", "summary": summary + (" (monorepo multi-stack: pilih `stack`)" if len(stacks) > 1 else ""),
               "action": ""})
   ```

7. **Sinkronkan dokumen deteksi** dengan `detect.py` (tanpa ini, model yang membaca dokumen akan tetap memakai aturan lama):
   - `backenddev/skills/profile/SKILL.md:37-42` (Fase 0 butir 2): `grpc-go` → `google.golang.org/grpc`; `elysiajs` → `elysia`; tambah `bun.lock`; tambah `hono` di daftar node (K3); tambah `salvo`, `laminas/laminas-mvc`; frasa "hanya dari `dependencies`".
   - `backenddev/skills/profile/stacks/node.md:9-13` (tambah `hono`; `elysiajs` → `elysia`), `stacks/bun.md:10` (tambah `bun.lock`), `stacks/go.md:10` (`google.golang.org/grpc`).
   - `frontenddev/skills/profile/SKILL.md:38` (urutan pemutus: Vite wajib; rujukan `hooks/lead-gate.sh` → `hooks/detect.py`), `:122`, `:154`.
   - `frontenddev/skills/profile/stacks/_CONTRACT.md:12,64,144`; `frontenddev/skills/profile/templates/profile-template.md:24,41`; `frontenddev/skills/profile/references/framework-matrix.md:40` (resep svelte-vite tambah `ls vite.config.*`).
   - `frontenddev/README.md:288-293` (seksi Gate Hook; beririsan dengan L7.3).

### Test yang ditambahkan

`tests/hooks/test_detect.py` (root repo; memanggil `python3 src/plugins/<p>/hooks/detect.py --plugin <p>` lewat `subprocess`):
- `test_case[<ID>]`, diparametrisasi atas B1–B12, F1–F10, A1–A6, Q1–Q2. Assert: exit 0; stdout kosong atau `json.loads(stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart"`; `--explain` menghasilkan `emit`, `stack`, `source`, dan `profile.state` sesuai kolom "Seharusnya".
- `test_detect_py_identik` — `filecmp.cmp(be/hooks/detect.py, fe/hooks/detect.py, shallow=False)`.
- `test_hook_equals_script_verdict[<ID>]` — untuk kasus F*, stack dari `frontenddev/skills/profile/scripts/check_preconditions.py --json --root <fixture>` == stack hook (atau keduanya kosong). Untuk kasus B*, check 1 `backenddev:profile` PASS ⇔ hook backenddev emit.
- `test_output_valid_json_with_control_chars` — `index.json` berisi tab/`\x01` mentah → stdout tetap JSON valid (B7).
- `test_cwd_escaped_quote_and_backslash` — B6, F7.
- `test_cwd_subdirectory_resolves_toplevel` — F6.
- `test_non_git_dir_uses_cwd` — direktori tanpa `.git` tetap dideteksi dari cwd.
- `test_malformed_stdin_is_silent` — stdin `not json` → exit 0, stdout kosong.

`tests/hooks/test_detect_parsers.py` (impor langsung `detect`):
- `test_go_requires_block_single_and_indirect` — blok + tunggal; `// indirect` diabaikan (K6); `fiber/v2`, `chi/v5` cocok.
- `test_cargo_deps_tomllib_and_fallback` — `monkeypatch.setattr(detect, "tomllib", None)`; hasil kedua jalur sama; `[dev-dependencies]` tidak dihitung; `[dependencies.axum]` dan `[target.'cfg(unix)'.dependencies]` dihitung.
- `test_pom_comment_ignored`, `test_gradle_comment_ignored`, `test_gradle_version_catalog`.
- `test_workspace_globs_pnpm_negation_skipped`, `test_go_work_use_block`, `test_cargo_workspace_members`.
- `test_candidate_dirs_skip_list_and_cap` — `node_modules/x/package.json` tidak dipindai; 250 direktori → maksimal 200 kandidat.
- `test_runtime_budget` — monorepo 200 paket selesai < 1 detik.

### Verifikasi manual

1. Pasang kedua plugin dari marketplace lokal, lalu buka sesi di fixture B5 dan F6 (subdirektori). `claude -p "Kutip verbatim baris kedua blok <backenddev-tech-lead-gate> dan <frontenddev-lead-gate> bila ada"` → hanya blok yang sesuai tabel yang muncul.
2. `claude --debug` di fixture B7: log hook tidak menunjukkan galat parse JSON.
3. Windows (bila tersedia): sesi di `C:\…\repo` React+Vite → blok frontenddev muncul. Periksa juga bahwa perintah `python3` tersedia; bila tidak, catat sebagai risiko di bawah. **Belum dijalankan.**

### Selesai bila

- Semua kasus di tabel menjadi test (`test_case[...]`) dan hijau. Output selalu JSON valid atau kosong.
- Vonis hook = vonis skrip prasyarat di setiap skenario (`test_hook_equals_script_verdict`).
- `tech-lead-gate.sh`/`lead-gate.sh` terhapus; tidak ada rujukan `lead-gate.sh`/`tech-lead-gate.sh` di markdown maupun Python (`grep -rn "lead-gate" src/` kosong).
- Dokumen deteksi (sub-tugas 7) memuat aturan yang sama dengan `detect.py`.

### Risiko & catatan

- **`python3` di Windows** sering tidak ada (yang ada `py`/`python`). Hook `.sh` lama juga tidak jalan di Windows tanpa `sh`, jadi ini bukan regresi. Catat di README.
- **Toplevel git yang terlalu tinggi**: bila `$HOME` adalah repo dotfiles, sesi di `~/scratch` yang bukan repo akan memindai `$HOME`. `MAX_CANDIDATES` dan `SKIP_DIRS` membatasi biayanya. Perilakunya sama dengan skrip prasyarat (`find_repo_root`).
- **Anak langsung root (K5)** bisa menyalakan hook frontenddev di repo pustaka yang punya `playground/`/`demo/` React+Vite. Keduanya ada di `SKIP_DIRS`; tambahkan nama lain bila muncul laporan.
- **Waktu**: hook punya batas 5 detik (`hooks.json`); `git rev-parse` diberi batas 2 detik.
- Pengecualian yang tak terduga ditelan dan hanya dilaporkan bila `.claude/profile/<plugin>/` ada, agar repo tak terkait tidak menerima noise.

---

## L1.3 [Tinggi] Hook membajak alur analyst dan quickdev; rujukan quickdev tanpa namespace

- [ ] Selesai

**Plugin:** backenddev, frontenddev (hook), quickdev, analyst · **Estimasi:** 1 hari · **Bergantung pada:** L1.2 (`gate_text.py`, `detect.opted_out`), K7, K8 · **Memblokir:** —

### Konteks

Hook mendeteksi dari manifest, bukan dari alur yang sedang dipakai user. Di repo express/React yang memakai quickdev atau analyst, blok gerbang engineer disuntik dengan kata "WAJIB"/"BERHENTI SEGERA". quickdev tidak pernah menyebut hook, backenddev, atau frontenddev. Rujukannya ke "gate `profile`"/"gate `plan`" tanpa prefix, sementara tiga plugin memasang skill bernama `profile` dan tiga memasang `plan`.

### Lokasi & kode saat ini

Daftar LEWATI hook — `src/plugins/backenddev/hooks/tech-lead-gate.sh:88-96`:
```
WAJIB lewat gerbang:
- permintaan kerja apa pun: memahami, mengubah, menambah, memperbaiki, mengaudit, mendokumentasikan
- susulan di tengah sesi, sekecil apa pun — "sekalian ganti X", "oh iya Y juga"
- menjalankan artefak yang sudah ada — "jalankan brief itu" — apa pun statusnya

LEWATI hanya tiga:
- jawaban user yang memasok informasi ke rute yang sudah diputuskan gerbang di giliran sebelumnya
- pertanyaan pengetahuan umum yang tidak menyentuh repo
- operasi VCS (commit, push, PR, rebase, diff) atas kerja yang sudah selesai
```
`src/plugins/frontenddev/hooks/lead-gate.sh:91` ("Jika ada permintaan kerja baru, BERHENTI SEGERA, laporkan ketiadaan profil, dan instruksikan user menjalankan `frontenddev:profile` (mode GENERATE) terlebih dahulu.") dan `:119-121` (tiga pengecualian yang sama, dalam prosa).

Deskripsi frontmatter quickdev (baris 3 tiap `src/plugins/quickdev/skills/*/SKILL.md`), tanpa kata "quickdev":
- `plan`: "Gunakan ketika kebutuhan sudah jelas dan siap dirumuskan menjadi rencana kerja terstruktur - penyusunan dokumen rencana di plan folder, sebelum eksekusi perubahan kode tanpa review plan user"
- `profile`: "Gunakan ketika repo backend atau frontend belum memiliki berkas profil atau perlu diperbarui - …"
- (`clarify`, `execute`, `explore`, `review` berpola sama). Pembandingnya `backenddev:plan`/`frontenddev:plan` diawali "Dipanggil …". Tidak ada skill di repo yang memakai `disable-model-invocation`.

`src/plugins/analyst/README.md:121-122`: "Di repo yang memasang `backenddev`/`frontenddev`, hook SessionStart kedua plugin itu mengarahkan permintaan kerja ke gerbang engineer. Panggil `/analyst:intake` secara eksplisit untuk menulis tiket di repo tersebut."

Rujukan quickdev tanpa namespace: lihat tabel penggantian di Rencana perbaikan sub-tugas 3.

### Reproduksi

```bash
#!/usr/bin/env bash
# Reproduksi L1.3 — hook engineer menyala di repo yang memakai quickdev.
set -u
REPO=/home/fakhrulnugroho/work/natakode/nataflow/agentic-workflow
P=$REPO/src/plugins
tmp=$(mktemp -d)
ctx() { printf '{"cwd":"%s","hook_event_name":"SessionStart","source":"startup"}' "$2" | sh "$1" |
  python3 -c 'import json,sys; d=sys.stdin.read().strip(); print(json.loads(d)["hookSpecificOutput"]["additionalContext"] if d else "(kosong)")'; }

git init -q "$tmp/api"; echo '{"dependencies":{"express":"^4"}}' > "$tmp/api/package.json"
printf '# Backend Repository Profile\nTIPE: backend\n' > "$tmp/api/repo-profile.md"   # profil quickdev
echo "== express + repo-profile.md (quickdev) → hook backenddev =="
ctx $P/backenddev/hooks/tech-lead-gate.sh "$tmp/api" | sed -n '2,4p;10,13p'

git init -q "$tmp/web"; echo '{"dependencies":{"react":"^19","react-dom":"^19"},"devDependencies":{"vite":"^6"}}' > "$tmp/web/package.json"
printf '# Frontend Repository Profile\nTIPE: frontend\n' > "$tmp/web/repo-profile.md"
echo "== React+Vite + repo-profile.md (quickdev) → hook frontenddev =="
ctx $P/frontenddev/hooks/lead-gate.sh "$tmp/web" | sed -n '2,5p'
rm -rf "$tmp"
```

Output aktual:
```
== express + repo-profile.md (quickdev) → hook backenddev ==
Repo backend, stack terdeteksi: node. Plugin `backenddev` aktif.

Profile repo `.claude/profile/` BELUM ADA. Tiap rute selain baca-kode berhenti di Phase 0 karenanya. Tawarkan `backenddev:profile` di giliran ini juga, jangan tunggu rutenya mentok dulu.
WAJIB lewat gerbang:
- permintaan kerja apa pun: memahami, mengubah, menambah, memperbaiki, mengaudit, mendokumentasikan
- susulan di tengah sesi, sekecil apa pun — "sekalian ganti X", "oh iya Y juga"
- menjalankan artefak yang sudah ada — "jalankan brief itu" — apa pun statusnya
== React+Vite + repo-profile.md (quickdev) → hook frontenddev ==
Repo ini terdeteksi sebagai repo frontend (stack: react-vite), tetapi profil `.claude/profile/` BELUM DIBUAT.

Dilarang memulai penelusuran fitur, perancangan arsitektur, atau penulisan kode sebelum profil repo siap.
Jika ada permintaan kerja baru, BERHENTI SEGERA, laporkan ketiadaan profil, dan instruksikan user menjalankan `frontenddev:profile` (mode GENERATE) terlebih dahulu.
```
Perilaku model di sesi nyata (apakah `/quickdev:*` atau susulan analyst benar-benar dibelokkan): **belum dijalankan**. Tetap perlu verifikasi seperti dicatat ISSUES.

**Koreksi terhadap ISSUES.md:** daftar rujukan tanpa namespace di ISSUES (12 baris) tidak lengkap. Hasil `md_grep` menemukan **32 baris di 6 berkas** yang merujuk skill quickdev tanpa prefix `quickdev:`, termasuk baris parameter `profile_path` ("hasil gate `profile`") di keempat skill hilir dan handoff "gate berikutnya". Daftar lengkapnya ada di tabel sub-tugas 3. Satu-satunya rujukan ber-prefix adalah `Author: quickdev:plan` (`plan/SKILL.md:66`), dan ini benar.

### Dampak

- quickdev praktis hanya aman di stack yang tidak dilayani backenddev/frontenddev (Next.js, FastAPI).
- "gate `profile`" bisa diselesaikan model dengan `backenddev:profile`. Akibatnya terbentuk `.claude/profile/…` yang tidak dibaca quickdev, `quickdev:plan` berhenti lagi di precondition 4 (berputar), dan hook berpindah ke mode "profil ADA" sehingga repo terkunci ke gating backenddev.
- Susulan user di tengah elisitasi analyst bisa ditangkap gerbang engineer, padahal analyst ditujukan untuk peminta non-engineer.

### Rencana perbaikan

1. **Butir LEWATI keempat di kedua hook**: sudah ditulis di `gate_text.py` (L1.2 sub-tugas 2), yaitu "permintaan yang memanggil atau melanjutkan alur plugin lain secara eksplisit — `/analyst:*`, `/quickdev:*`, atau susulan di tengah skill `analyst:*`/`quickdev:*` yang sedang berjalan (elisitasi tiket, `plan/<task>.md`). Kerja itu milik plugin tersebut sampai user sendiri meminta pindah ke gerbang ini." Butir WAJIB ketiga dipersempit menjadi "menjalankan artefak **backenddev** yang sudah ada (brief, `TASK.md`, `RCA.md`)". Frontenddev: "artefak frontenddev (brief, `TASK.md`, `CONTRACT.md`)".

2. **Penanda opt-out `.claude/workflow`** (K8): berkas teks berisi nama plugin yang boleh menggerbangi repo, dipisah spasi/baris. Isi `quickdev` → kedua hook engineer diam. Isi `frontenddev quickdev` → hanya hook frontenddev yang menyala. Berkas tidak ada → perilaku normal. Implementasinya `detect.opted_out()` (L1.2), diuji Q1/Q2. Dokumentasikan di README kedua plugin engineer dan quickdev. `quickdev:profile` Fase 4 menawarkan penulisan berkas ini bila `detect.py` (atau blok gerbang di konteks) menunjukkan hook engineer aktif. Penulisan hanya dilakukan dengan persetujuan user.

3. **Namespace semua rujukan quickdev** (path relatif `src/plugins/quickdev/skills/`):

| ☐ | Berkas:baris | Teks sekarang (potongan) | Pengganti |
|---|---|---|---|
| ☐ | `clarify/SKILL.md:14` | "pada gate `explore` telah selesai" | "pada `quickdev:explore` telah selesai" |
| ☐ | `clarify/SKILL.md:21` | "dari gate `explore` … laporan `explore` terakhir" | "dari `quickdev:explore` … laporan `quickdev:explore` terakhir" |
| ☐ | `clarify/SKILL.md:23` | "path profil hasil gate `profile`" | "path profil hasil `quickdev:profile` (bukan `.claude/profile/` milik backenddev/frontenddev)" |
| ☐ | `clarify/SKILL.md:24` | "langsung mengalirkan status `SKIPPED` ke gate berikutnya" | "melaporkan `SKIPPED` dan menawarkan `quickdev:plan`" |
| ☐ | `clarify/SKILL.md:41` | "Teruskan eksekusi langsung ke gate `plan` tanpa menghentikan proses…" | "Laporkan `SKIPPED` dalam satu baris dan tawarkan `quickdev:plan`; jangan memanggilnya sebelum user setuju." |
| ☐ | `clarify/SKILL.md:86` | "Alirkan spesifikasi terkunci ke gate berikutnya: `plan`." | "Tawarkan `quickdev:plan` dengan spesifikasi terkunci; tunggu user." |
| ☐ | `clarify/SKILL.md:122` | "kembalikan alur kerja ke gate `explore`" | "tawarkan `quickdev:explore` ulang untuk area yang kurang" |
| ☐ | `execute/SKILL.md:15` | "agar diff gate `review` hanya berisi hasil eksekusi" | "agar diff `quickdev:review` hanya berisi hasil eksekusi" |
| ☐ | `execute/SKILL.md:17` | "arahkan pemanggil ke gate `profile`" | "arahkan pemanggil ke `quickdev:profile` (jangan `backenddev:profile`/`frontenddev:profile`)" |
| ☐ | `execute/SKILL.md:23` | "path profil hasil gate `profile`" | "path profil hasil `quickdev:profile`" |
| ☐ | `execute/SKILL.md:29` | "daftar temuan gate `review`" | "daftar temuan `quickdev:review`" |
| ☐ | `execute/SKILL.md:60` | "(`require_test_plan: false` di gate `plan`)" | "(`require_test_plan: false` di `quickdev:plan`)" |
| ☐ | `execute/SKILL.md:84` | "Serahkan handoff ke gate `review` … agar gate `review` dapat menilai" | "Tawarkan `quickdev:review` … agar `quickdev:review` dapat menilai" |
| ☐ | `execute/SKILL.md:91` | "hanya membuka gate `review`" | "hanya membuka `quickdev:review`" |
| ☐ | `execute/SKILL.md:104` | "membuka gate `review` … menahan `review` … tidak membuka `review` … revisi rencana di gate `plan`" | ganti keempatnya dengan `quickdev:review` / `quickdev:plan` |
| ☐ | `execute/SKILL.md:120` | "persetujuan user di gate `plan`" | "persetujuan user di `quickdev:plan`" |
| ☐ | `execute/SKILL.md:127` | "merevisi rencana di gate `plan`" | "merevisi rencana lewat `quickdev:plan`" |
| ☐ | `explore/SKILL.md:26` | "path profil hasil gate `profile`" | "path profil hasil `quickdev:profile`" |
| ☐ | `explore/SKILL.md:93` | "klarifikasi lebih lanjut di gate hilir" | "klarifikasi lebih lanjut di `quickdev:clarify`" |
| ☐ | `explore/SKILL.md:95` | "Alirkan laporan hasil eksplorasi ke gate berikutnya: `clarify`." | "Tawarkan `quickdev:clarify` (atau `quickdev:plan` bila nol celah); tunggu user." |
| ☐ | `explore/SKILL.md:135` | "mengeksekusi gate `profile` terlebih dahulu" | "menjalankan `quickdev:profile` terlebih dahulu" |
| ☐ | `plan/SKILL.md:14` | "Gate `explore` dan `clarify` telah selesai" | "`quickdev:explore` dan `quickdev:clarify` telah selesai" |
| ☐ | `plan/SKILL.md:17` | "arahkan pemanggil ke gate `profile`" | "arahkan pemanggil ke `quickdev:profile` (jangan `backenddev:profile`/`frontenddev:profile`)" |
| ☐ | `plan/SKILL.md:24` | "path profil hasil gate `profile`" | "path profil hasil `quickdev:profile`" |
| ☐ | `plan/SKILL.md:126` | "kembalikan sementara ke gate `clarify`" | "tawarkan `quickdev:clarify` untuk detail yang hilang" |
| ☐ | `profile/SKILL.md:25` | "diteruskan sebagai `profile_path` ke gate hilir" | "diteruskan sebagai `profile_path` ke skill quickdev hilir (`quickdev:explore`, `quickdev:plan`, …)" |
| ☐ | `profile/SKILL.md:100` | "Alirkan konteks profil … ke gate berikutnya: `explore`." | "Tawarkan `quickdev:explore`; tunggu user." |
| ☐ | `review/SKILL.md:14` | "kembalikan pemanggil ke gate `execute`" | "kembalikan pemanggil ke `quickdev:execute`" |
| ☐ | `review/SKILL.md:26` | "berkas baru hasil gate `execute`" | "berkas baru hasil `quickdev:execute`" |
| ☐ | `review/SKILL.md:75` | "serahkan daftar temuan ke gate `execute` lewat parameter `review_findings`" | "tawarkan `quickdev:execute` dengan `review_findings` (dan `plan_path` yang sama); jalankan hanya bila user setuju" (beririsan D3) |
| ☐ | `review/SKILL.md:120` | "**Gate execute belum COMPLETED** … di gate `execute`" | "**`quickdev:execute` belum COMPLETED** … di `quickdev:execute`" |
| ☐ | `review/SKILL.md:123` | "menjalankan gate `profile` lebih dahulu" | "menjalankan `quickdev:profile` lebih dahulu" |

   Rujukan generik yang boleh tetap: `review/SKILL.md:82` ("artefak gate hulu") dan `:133` ("konsisten dengan gate hulu").

4. **Seksi Koeksistensi** di keenam SKILL quickdev, disisipkan tepat sesudah `## Precondition [REQUIRED]`:
   ```markdown
   ## Koeksistensi [REQUIRED]

   - Skill ini bagian dari alur ringan `quickdev` (`repo-profile.md`, `plan/<task>.md`, tanpa taskdir). Setiap rujukan skill di berkas ini berarti `quickdev:*`. Dilarang memakai `backenddev:*` atau `frontenddev:*` sebagai pengganti: `backenddev:profile`/`frontenddev:profile` menulis `.claude/profile/<plugin>/`, bukan `repo-profile.md`, dan tidak memenuhi precondition skill ini.
   - Bila konteks sesi memuat blok `<backenddev-tech-lead-gate>` atau `<frontenddev-lead-gate>`:
     - User memanggil `/quickdev:<skill>` secara eksplisit, atau melanjutkan artefak quickdev (`plan/<task>.md`, `repo-profile.md`) → lanjutkan skill ini. Blok gerbang itu mengecualikan alur plugin lain yang dipanggil eksplisit.
     - Permintaan kerja baru tanpa pilihan alur → tanyakan sekali lewat `AskUserQuestion`: "Alur ringan quickdev (`plan/<task>.md`)" atau "Gerbang `<backenddev:tech-lead | frontenddev:lead>` (taskdir + brief)". Jangan memilih sendiri.
   - `.claude/workflow` ada dan tidak memuat kata `quickdev` → repo ini memilih alur lain; laporkan dan tanyakan dulu sebelum lanjut.
   ```

5. **Deskripsi frontmatter** (baris 3). Semua diawali penanda alur. Usulan:
   - `profile`: "Alur ringan quickdev (repo-profile.md, plan/<task>.md, tanpa taskdir) — dipanggil eksplisit lewat /quickdev:profile ketika repo belum punya repo-profile.md atau profilnya perlu diperbarui: pemindaian stack, layer, dan baseline verifikasi. Bukan untuk .claude/profile/ milik backenddev/frontenddev."
   - `explore`: "Alur ringan quickdev (…) — penelusuran arsitektur kode dan pemetaan simbol file:baris sebagai bahan quickdev:clarify/quickdev:plan; dipanggil eksplisit lewat /quickdev:explore."
   - `clarify`: "Alur ringan quickdev (…) — klarifikasi celah spesifikasi dari laporan quickdev:explore sebelum quickdev:plan; dipanggil eksplisit lewat /quickdev:clarify."
   - `plan`: "Alur ringan quickdev (…) — menyusun satu berkas rencana plan/<task>.md dari kebutuhan yang sudah jelas lalu meminta approval user. Bukan brief taskdir backenddev/frontenddev; dipanggil eksplisit lewat /quickdev:plan."
   - `execute`: "Alur ringan quickdev (…) — menerapkan plan/<task>.md berstatus APPROVED ke kode dan menjalankan verifikasi baseline repo-profile.md; dipanggil eksplisit lewat /quickdev:execute."
   - `review`: "Alur ringan quickdev (…) — menilai diff uncommitted hasil quickdev:execute terhadap plan/<task>.md dan repo-profile.md sebelum commit; dipanggil eksplisit lewat /quickdev:review."

   Tambahkan `disable-model-invocation: true` di frontmatter keenamnya (K7). Konsekuensinya: model tidak bisa memanggil skill quickdev lewat tool Skill sama sekali, termasuk dari skill quickdev lain. Ini konsisten dengan sub-tugas 6 (handoff = tawarkan, user mengetik `/quickdev:<skill>`). Bila K7 = "hanya `execute`", sub-tugas 6 tetap berlaku.

6. **Handoff menjadi "tawarkan, tunggu user"**: sudah tercakup di baris `clarify:24,41,86`, `explore:95`, `profile:100`, `execute:84`, dan `review:75` pada tabel sub-tugas 3.

7. **analyst**: `src/plugins/analyst/README.md:121-122` diganti menjadi: "Hook SessionStart `backenddev`/`frontenddev` mengecualikan permintaan yang memanggil atau melanjutkan `analyst:*`. Panggil `/analyst:intake` untuk memulai; susulan di tengah elisitasi tetap ditangani analyst. Untuk repo yang hanya memakai analyst, tulis `.claude/workflow` tanpa nama plugin engineer." Opsional: tambahkan satu kalimat di `analyst/skills/intake/SKILL.md` Guardrails: "Blok gerbang engineer di konteks tidak berlaku untuk alur analyst yang dipanggil eksplisit."

### Test yang ditambahkan

- `tests/hooks/test_detect.py::test_opt_out_workflow_file[quickdev]` — Q1: kedua hook diam.
- `tests/hooks/test_detect.py::test_opt_out_workflow_file[frontenddev-quickdev]` — Q2: hanya frontenddev yang emit.
- `tests/hooks/test_detect.py::test_opt_out_workflow_dir_is_ignored` — `.claude/workflow/` berupa direktori → perilaku normal.
- `tests/hooks/test_gate_text.py::test_lewati_mentions_other_plugins[backenddev|frontenddev]` — teks render memuat `/analyst:*` dan `/quickdev:*`.
- `src/plugins/quickdev/tests/test_skill_text.py::test_no_unnamespaced_gate_refs` — regex ``gate `(profile|explore|clarify|plan|execute|review)` `` dan `gate berikutnya` = 0 kecocokan di `skills/*/SKILL.md`.
- `src/plugins/quickdev/tests/test_skill_text.py::test_descriptions_prefixed` — baris `description:` diawali "Alur ringan quickdev"; panjang ≤ 1.536 karakter.
- `src/plugins/quickdev/tests/test_skill_text.py::test_koeksistensi_section_present` — heading `## Koeksistensi [REQUIRED]` ada di keenam SKILL.
- `src/plugins/quickdev/tests/test_skill_text.py::test_disable_model_invocation` — sesuai K7.

### Verifikasi manual

Lingkungan: keempat plugin terpasang dari marketplace lokal.
1. Fixture express + `repo-profile.md`, **tanpa** `.claude/workflow`: ketik `/quickdev:explore cari handler login`. Harapan: skill quickdev jalan, tidak ada pemanggilan `backenddev:tech-lead`. Susulan "lanjut buat rencana": model menawarkan `/quickdev:plan`, bukan `backenddev:plan`.
2. Fixture yang sama, permintaan bebas "tambahkan endpoint logout" tanpa perintah slash: model bertanya lewat AskUserQuestion (quickdev vs tech-lead), atau langsung ke tech-lead bila quickdev belum pernah disebut. Keduanya sah; yang tidak sah adalah menjalankan `backenddev:profile` untuk memenuhi precondition quickdev.
3. Fixture React+Vite + `.claude/workflow` = `quickdev`: `claude -p "Adakah blok <frontenddev-lead-gate> di konteksmu?"` → tidak ada.
4. analyst: `/analyst:intake tiket cicilan`, jawab satu pertanyaan, lalu susulan "lanjut tiket cicilan, tambah aturan denda". Harapan: tetap di `analyst:elicit`, tidak berpindah ke `backenddev:tech-lead`.
5. Catat transkrip keempat skenario di PR.

### Selesai bila

- Di repo express/React yang memakai quickdev, memanggil `/quickdev:*` tidak dibelokkan hook (verifikasi manual 1 dan 3).
- Di tengah alur analyst, susulan user tetap ditangani analyst (verifikasi manual 4).
- Tidak ada lagi rujukan gate quickdev tanpa prefix `quickdev:` (`test_no_unnamespaced_gate_refs` hijau; tabel sub-tugas 3 tercentang).
- Opt-out `.claude/workflow` bekerja (Q1/Q2 hijau) dan terdokumentasi.

### Risiko & catatan

- Butir LEWATI hanyalah instruksi. Model tetap bisa salah menilai "melanjutkan alur plugin lain" untuk permintaan ambigu. Penanda opt-out adalah satu-satunya jaminan mekanis.
- `disable-model-invocation: true` menghapus kemampuan model menemukan quickdev secara otomatis. User yang belum tahu quickdev tidak akan ditawari. Ini disengaja (opt-in).
- Edit teks quickdev beririsan dengan D3 (loop review ↔ execute), D5, D6, D7. Kerjakan dalam satu PR.

---

## L1.4 [Rendah] Hook bertentangan dengan skill soal profil yang belum ada

- [ ] Selesai

**Plugin:** backenddev, frontenddev · **Estimasi:** 0,25 hari · **Bergantung pada:** K9, L1.2 (`gate_text.py`), L2.8 (kalimat baca-kode) · **Memblokir:** —

### Lokasi & kode

- `src/plugins/frontenddev/hooks/lead-gate.sh:91`: "Jika ada permintaan kerja baru, BERHENTI SEGERA, laporkan ketiadaan profil, dan instruksikan user menjalankan `frontenddev:profile` (mode GENERATE) terlebih dahulu." Bandingkan `src/plugins/frontenddev/skills/lead/SKILL.md:158`: "rute `PROFILE` ke `frontenddev:profile` mode `GENERATE` tanpa titik henti konfirmasi".
- `lead-gate.sh:99` (profil TIDAK SAH → "minta user menulis ulang profil via `frontenddev:profile` (mode REFRESH)"). Bandingkan `lead/SKILL.md:159` (Failure path 2: `stack` profil di luar kontrak → "hentikan, jangan buat taskdir"). **Tambahan terhadap ISSUES.**
- `src/plugins/backenddev/hooks/tech-lead-gate.sh:78`: "Tiap rute selain baca-kode berhenti di Phase 0 karenanya. Tawarkan `backenddev:profile` di giliran ini juga". Bandingkan `backenddev/skills/tech-lead/SKILL.md:43` (Gerbang Masuk mengaktifkan gerbang untuk "permintaan pemahaman kode") dan `:50` (Fase 0: "Hentikan eksekusi segera jika skrip menghasilkan `FAIL`"). Pertanyaan baca-kode pun berhenti (L2.8).

### Masalah

Untuk keadaan yang sama, model menerima dua instruksi berbeda: berhenti dan menyuruh user (hook) vs merutekan otomatis (lead); "baca-kode lolos" (hook) vs semua berhenti di Fase 0 (tech-lead); REFRESH (hook) vs hentikan (lead FP2).

### Perbaikan

SKILL (gerbang) menjadi sumber kebenaran; hook hanya merujuk ke gerbang (K9):
1. `gate_text.py` kedua plugin (sudah tertulis di L1.2 sub-tugas 2): semua cabang profil berbunyi "Permintaan kerja tetap lewat `<gerbang>`; gerbang/lead merutekan `<plugin>:profile` (GENERATE | REFRESH | MIGRATE) lebih dulu, lalu melanjutkan rute tertunda". Kalimat "BERHENTI SEGERA … instruksikan user" dan "selain baca-kode" dihapus.
2. `frontenddev/skills/lead/SKILL.md:159` (FP2): bedakan "manifest `next` → hentikan" dari "`stack` profil tidak sah → rute `PROFILE` mode REFRESH". Profil milik plugin lain sudah ditangani L1.1, jadi tidak lagi jatuh ke cabang ini.
3. `backenddev/skills/tech-lead/SKILL.md:50-52`: samakan dengan hook, yaitu "profil hilang → rute `PROFILE` (Keputusan 1), lalu ulangi Fase 0 dan lanjutkan rute tertunda". Setelah L2.8 menambah mode `--read-only`, tambahkan ke hook dan SKILL sekaligus: "pertanyaan baca-kode dijawab tanpa profil".
4. Bila K9 = "berhenti & minta user": balik arahnya. Hook dipertahankan, lalu `lead/SKILL.md:158` dan `profile/SKILL.md:22` diubah menjadi "tanyakan dulu lewat AskUserQuestion".

### Test

- `tests/hooks/test_gate_text.py::test_profile_absent_text_defers_to_gate[backenddev|frontenddev]` — render dengan `Profile("ABSENT")` tidak memuat `BERHENTI SEGERA` maupun `selain baca-kode`, dan memuat nama gerbang (`backenddev:tech-lead` / `frontenddev:lead`).
- Lint teks: `grep -n "BERHENTI SEGERA" src/plugins/*/hooks/` kosong.

### Selesai bila

Untuk setiap keadaan profil (absen, tidak sah, tidak lengkap, lokasi lama), teks hook dan `## Failure path`/Fase 0 SKILL gerbang menyebut tindakan yang sama. Diperiksa dengan membaca berdampingan tujuh cabang `_profile_note` di tiap `gate_text.py` terhadap SKILL, dan hasil pemeriksaannya dicatat di PR.

# Template Prompt Reviewer Diff Branch — `code-reviewer`

Gunakan template ini saat `architect` mendispatch subagent penilai diff (`code-reviewer`) secara langsung.

**Tujuan:** Menilai seluruh diff branch satu taskdir terhadap kontrak gabungan briefnya, tepat satu kali di akhir tiap putaran rantai, dan mengunci hasilnya sebagai `{taskdir}/REVIEW.md`.

**Dispatch setelah:** Fase 4 butir 1 hijau — build dan test penutup lulus dan tiap brief taskdir sudah tertutup — `DONE` dengan commitnya mendarat, atau `SUPERSEDED` bertaut ke penggantinya.

```markdown
Review seluruh branch pekerjaan untuk satu direktori tugas.

- Objek: `{taskdir}/`, dinilai terhadap seluruh diff branch ini terhadap `{base_branch}`.
- Rentang Git: `git merge-base {base_branch} HEAD`..`HEAD` — bukan `{base_branch}..HEAD` polos.
- Kontrak Penilai: Gabungan seluruh brief di `{taskdir}/`, bukan kualitas umum modul sekitarnya.
- Acceptance: Tulis `{taskdir}/REVIEW.md` (selalu, termasuk bila diff bersih) sesuai `## Kontrak
  REVIEW.md` di definisi agent-mu.
- Pencatatan Isu: Tambahkan baris temuan di `backenddev/issues/README.md` dengan `target` menyebut
  path file kode riil.
- Di Luar Penilaian: Perubahan di bawah `backenddev/` dan `.claude/`.
- Balikan: HANYA path `{taskdir}/REVIEW.md` dan tingkat severity tertinggi (`P1`, `P2`, `P3`, atau
  `CLEAN`). Jangan kutip isi file review ke chat.
- Commit: Commit sendiri `{taskdir}/REVIEW.md` **dan** `backenddev/issues/README.md` dalam satu
  commit sesudah laporan selesai ditulis, hanya di branch kerja (bukan detached, bukan `{base_branch}`),
  dengan pesan yang disusun dari `commit_convention` profil (default `docs(<slug>): add final review report`).
- Stop Condition: Dilarang melebar mengaudit kode di luar rentang diff; sweep konvensi umum adalah
  milik `audit`. Gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan lapor sesuai jalur
  gagal di sana, jangan menebak.
```

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` architect | **[REQUIRED]** Direktori tugas yang dinilai — misal `backenddev/docs/2608181430-order-split`. Dilarang dikosongkan atau diganti path induknya; reviewer menurunkan kontrak penilaiannya dari brief di direktori ini |
| `{base_branch}` | Field `base_branch` di `.claude/profile/backenddev/index.json` | **[REQUIRED]** Titik cabang dasar — misal `main` atau `dev`. Batalkan dispatch bila profil tidak terbaca; menebak `main` pada repo ber-`base_branch` lain menghasilkan rentang diff yang salah dan review yang menilai pekerjaan orang lain |

### Aturan untuk Pendispatch

- **Tepat satu kali di akhir tiap putaran**: reviewer berangkat sekali atas seluruh diff branch gabungan, sesudah brief terakhir `DONE`. Dilarang mendispatch per brief. Review ulang sah tepat sekali per putaran, yaitu saat check 3 skrip prasyarat menyatakan `REVIEW.md` basi.
- **Sesudah verifikasi penutup hijau**: build dan test Fase 4 butir 1 lulus lebih dulu. Mendispatch reviewer di atas branch yang buildnya merah menghasilkan temuan yang tak dapat dipisahkan dari kegagalan build.
- **Dilarang menyalin isi berkas**: jangan salin isi brief, diff, atau `.claude/profile/backenddev/` ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Audit hidrasi sebelum berangkat**: batalkan dispatch bila prompt masih memuat slot kurung kurawal `{...}` mentah atau placeholder `TBD`/`TODO`.
- **Read-only terhadap `src/`**: reviewer tidak pernah memperbaiki kode atau menjalankan build/test; ia hanya menulis dan meng-commit laporannya sendiri beserta baris indeks `backenddev/issues/README.md`.
- **Dispatch langsung tanpa skill pembungkus**: seluruh doktrin review — gerbang masuk, lima pemeriksaan, kontrak `REVIEW.md`, dan amplop balikan — duduk di `agents/code-reviewer.md`. Dilarang memanggil skill perantara atau menyalin potongan doktrin itu ke dalam prompt.

### Penanganan Balikan

`architect` memetakan balikan sendiri; tidak ada amplop pembungkus pada jalur ini.

| Balikan subagent | Penanganan `architect` |
| --- | --- |
| Path `REVIEW.md` + severity `CLEAN`, `P3`, atau `P2` | Serap ke laporan penutup apa adanya. Severity berada di luar sistem status brief dan dilarang dipaksa jadi `BLOCKED` |
| Severity `P1` | Jangan perbaiki di tempat. Catat di laporan akhir dan arahkan user kembali ke gerbang `tech-lead` — `## Failure path` butir 5 |
| `{taskdir}/REVIEW.md` tidak ada di disk | Cacat kerja subagent. Ulangi dispatch maksimum sekali; tetap gagal → laporkan review tidak tuntas ke gerbang. Dilarang menulis `REVIEW.md` sendiri atau mengarang verdict |
| Balikan menyebut `git commit` gagal, atau `REVIEW.md`/`backenddev/issues/README.md` ada tetapi uncommitted | Kunci sendiri **kedua** berkas itu dalam satu commit dengan staging path eksplisit dan pesan dari `commit_convention` profil (default `docs(<slug>): add final review report`); ditolak hook `commit-msg` → laporkan pesan hook ke user, dilarang mengulang pesan yang sama atau `--no-verify`. Catat penyimpangannya — `## Failure path` butir 6 |
| Payload kosong, format rusak, atau subagent error | Kegagalan dispatch, bukan cacat kerja subagent. Periksa disk lebih dulu lewat matriks bukti `references/lifecycle-recovery.md` sebelum menyimpulkan review tidak pernah berjalan |

**Batas serap.** Verdict reviewer diteruskan utuh ke laporan penutup, tanpa parafrase maupun penyaringan temuan. Guardrail **STRICT NON-AUTHORING** berlaku penuh: temuan severity apa pun dilarang ditambal `architect` sendiri di `src/`, dan perbaikan `P1` berjalan di **taskdir yang sama** lewat gerbang (`tech-lead` Fase 5 butir 4 → lane `PLANNING` → `analyst` re-entry → `plan --append`), lalu satu review baru di putaran berikutnya (`REVIEW.md` basi, `references/lifecycle-recovery.md` bagian 1).

**Subagent mengembalikan:** Path `{taskdir}/REVIEW.md` beserta satu tingkat severity tertinggi (`P1`, `P2`, `P3`, atau `CLEAN`), tanpa kutipan isi laporan ke context.

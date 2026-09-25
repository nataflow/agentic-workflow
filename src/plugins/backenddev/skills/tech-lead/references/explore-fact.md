# Jalur Cepat `EXPLORE_FACT` — Pertanyaan Baca-Kode

Rumah kanonik jalur baca-kode gerbang `backenddev:tech-lead`: pertanyaan faktual tentang repo — letak simbol, pemanggil, tracing alur — tanpa mutasi apa pun. Jalur ini tetap lewat gerbang, tetapi tidak menuntut tree bersih, branch, `commands.md`, maupun profil.

## 1. Prasyarat Read-Only

Fase 0 tiap permintaan menjalankan `check_preconditions.py --read-only`. Mode ini **tidak menilai** tree kotor, HEAD detached, izin tulis zona artefak, `commands.md`, dan profil yang belum ada — kondisinya tetap tertulis di ringkasan check, berakhiran `(tidak dinilai: mode read-only)`.

| Kondisi | Mode read-only | Mode penuh (Fase 3 butir 0) |
| --- | --- | --- |
| Tree kotor di `src/` | PASS, dicatat | FAIL — minta stash/commit |
| HEAD detached (mis. bisect) | PASS, dicatat | FAIL — `HEAD detached` |
| `commands.md` hilang | PASS, dicatat | FAIL — rute `PROFILE` |
| Profil backenddev belum ada | PASS **TERDEGRADASI** — jawab dari sapuan manual, tawarkan `backenddev:profile` | FAIL — rute `PROFILE` |
| Bukan repo git, `index.json` rusak | FAIL — hentikan | FAIL |

Permintaan yang ternyata menuntut mutasi keluar dari jalur ini ke Keputusan 1; prasyarat penuh baru berjalan di Fase 3 butir 0, sebelum taskdir atau branch diprovisi.

## 2. Eksplorasi

Aturan Fase 1 `SKILL.md` berlaku apa adanya:

1. **Kuota sapuan main loop**: maksimal 3 panggilan gabungan `Glob`+`Grep`, potongan tertarget ≤40 baris, 0 berkas dibaca penuh, 0 query database, 0 `Bash` penelusuran.
2. **Dispatch wajib**: satu pemicu mekanis `gate-scope.md` bagian 4E aktif → berangkatkan `code-explorer` lewat `dispatcher/explorer.md` terhidrasi penuh, tanpa sapuan pendahulu.
3. **Fast-path**: tanpa pemicu dispatch — satu `Glob` domain di bawah `source_root` profil (atau root repo bila profil absen), sisa kuota untuk `Grep` simbol.
4. **Stop condition**: tiap permukaan yang ditanyakan berstatus **terbukti** (`file:line`) atau **tercatat belum terbukti**.

Profil absen: `source_root` tidak diketahui, jadi `Glob` pertama menyapu root repo dan jawaban menyebut `profil absen — sapuan tanpa batas modul` sekali.

## 3. Jawaban

Jawab langsung di chat dari temuan eksplorasi, tanpa blok `TECH-LEAD GATEWAY DECISION`:

```markdown
<jawaban 1–3 kalimat>
- `<file:baris>` — <peran baris itu>
Bukti: code-explorer <slug> | fast-path <n>/3 · belum terbukti: <daftar | nihil> · <TERDEGRADASI (profil absen) | —>
```

Dilarang membuat taskdir, branch, atau berkas apa pun di jalur ini; laporan `code-explorer` di laci `backenddev/docs/.explore/` adalah satu-satunya jejak disk dan tidak di-commit. Profil absen → tutup dengan satu kalimat tawaran `backenddev:profile`.

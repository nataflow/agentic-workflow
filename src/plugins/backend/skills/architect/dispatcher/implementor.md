# Template Prompt Implementor Brief

Gunakan template ini saat mendispatch subagent eksekutor brief (`code-implementor`).

**Tujuan:** Mengubah satu brief berstatus `READY` menjadi perubahan `src/**` yang terkunci di commit atomik sendiri, tanpa build maupun test.

**Dispatch setelah:** Brief `NN` terpilih sebagai titik mulai rantai di Fase 1 dan working tree bersih.

```markdown
Eksekusi satu brief implementasi.

- Brief: `{brief_path}` (unit `{unit_name}`). Baca utuh sebelum menulis baris kode pertama.
- Taskdir: `{taskdir}`
- Batas File: `## File scope` di brief adalah batas mutlak — jangan menyentuh file di luar daftar
  itu. Gunakan kolom `Anchor` sebagai acuan posisi sisip relatif.
- Adapter Stack: `{adapter_path}` — seksi `## Layer taxonomy` di sana mengikat urutan layer,
  penamaan berkas, dan letak direktori. Baca sendiri; isinya tidak disalin ke prompt ini.
- Acceptance: tiap item `## Work status` tuntas dikerjakan sesuai `## Steps` dan statusnya diperbarui.
  Dilarang menjalankan build atau test — verifikasi milik gerbang penutup taskdir.
- Konvensi: `.claude/profile/backenddev/code-conventions.md` dan `.claude/profile/backenddev/anti-patterns.md` mengikat.
  Idiom default stack yang bertentangan dengan baris konvensi repo tidak boleh dipakai, dan brief yang
  menuntut pola terlarang dihentikan sebagai `BLOCKED`.
- Stop Condition: gerbang masuk lengkap ada di definisi agent-mu — BERHENTI dan lapor sesuai jalur
  gagal di sana, jangan menebak.
- Commit: Kunci sendiri pekerjaanmu — frontmatter brief jadi `status: DONE` lebih dulu, lalu `git add`
  tiap path `## File scope` + berkas brief satu per satu, lalu `git commit -m "<commit_message>"` —
  satu `-m` berisi persis `commit_message` frontmatter brief, tanpa trailer, heredoc, atau `$`
  (pagar hook menolaknya, termasuk trailer atribusi yang diminta pengingat harness).
- Balikan: maksimum 10 baris terstruktur sesuai `## Format Output` agent-mu. Jalur gagal wajib
  menulis `{taskdir}/report-<NN>.md` — `NN` dua digit prefiks `{unit_name}` — lebih dulu lalu
  menyebut path-nya.
```

### Slot Hidrasi

| Slot | Sumber Pengisian | Keterangan & Batasan Kritis |
| --- | --- | --- |
| `{taskdir}` | Parameter `taskdir` architect | Direktori tugas — misal `backenddev/docs/2608181430-order-split` |
| `{brief_path}` | Brief aktif hasil traversal Fase 1 | Path brief berstatus `READY` — misal `{taskdir}/brief-01-lock.md` |
| `{unit_name}` | Nama unit brief aktif | Format `NN-unit` — misal `01-lock`; `<NN>` diturunkan dari prefiksnya |
| `{adapter_path}` | `${CLAUDE_PLUGIN_ROOT}/skills/profile/stacks/<stack>.md`, `<stack>` dari `.claude/profile/backenddev/index.json` | Path absolut adapter. Substitusi `${CLAUDE_PLUGIN_ROOT}` terjadi di badan `architect/SKILL.md`, bukan di berkas ini — architect mengisi slot dengan hasil substitusinya, bukan literal placeholder |

### Aturan untuk Pendispatch

- **Dilarang menyalin isi berkas**: jangan salin isi `.claude/profile/backenddev/`, adapter stack, atau brief ke dalam prompt. Sebutkan path-nya; subagent membacanya sendiri secara terisolasi.
- **Satu brief per dispatch**: eksekusi implementor sekuensial, satu dispatch per brief, tanpa paralelisasi.
- **Penanda kurung sudut bukan slot**: `<NN>` dan `<domain>` diturunkan subagent saat runtime dan wajib dibiarkan apa adanya. Batalkan dispatch bila masih tersisa slot kurung kurawal yang belum terhidrasi.

**Subagent mengembalikan:** Amplop `## Implementor Report — brief-{NN}-{unit}` dengan status `DONE` atau `BLOCKED`, memuat baris `Commit:` dan baris `Simbol Tersentuh:`.

Baris `Simbol Tersentuh:` mengenumerasi simbol yang benar-benar diubah, termasuk yang **tidak** disebut kolom `Anchor` brief. `architect` Fase 3 butir 4 membandingkannya dengan peta simbol `scripts/symbol_map.py`, dan selisih di antara keduanya dicatat apa adanya. Batas scope brief mengikat berkas **dan** simbol: berkas yang sama menampung banyak simbol, sehingga perbandingan tingkat berkas saja meloloskan penyuntingan simbol mana pun asalkan berkasnya kebetulan terdaftar.

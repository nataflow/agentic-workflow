# Langkah 32 — `backend`: ongkos tetap rantai kecil — cek simbol deklarasi baru, `symbol_map` ringkas, serah terima sesudah PRD, explorer delta, dispatcher terpisah (S1–S2, H3–H4, E1–E2, T1, L1, C1, D1)

Sumber: umpan balik sesi OrderHub tiket nataflow #80 (wajibkan minimal 1 foto pada dua endpoint Recall Order) dan
pembedahan transkripnya (sesi `b54b99fe`, backend 0.20.2). Keputusan diambil 2026-11-11. Basis kode: commit `0f09eb8`
(backend 0.20.2). Alat ukur: `scripts/token_usage.py` (Langkah 30 U1).

**Status (2026-11-11):** SELESAI di branch `feat/ongkos-tetap-32` (belum di-commit). Seluruh tahap 0–5 terpasang;
backend 0.21.0 (`MIGRATION_v0.20.2_to_v0.21.0.md`). Suite penuh 2.932 lulus / 5 skip, lint `--base origin/main`
0 FAIL, `claude plugin validate .` lolos, test baru lulus juga di Python 3.12. Belum dilakukan: uji lapangan satu
rantai `PRD_BRIEF` di repo nyata dan compare `token_usage.py` sesudah 0.21.0 terpasang (bagian Verifikasi).

**Uji lapangan atas data kasus #80 (2026-11-11, salinan `oms-api` @ `ef04d05` + taskdir asli, skrip 0.21.0):**

- `close_brief.py` atas empat commit brief: brief 01 dan 04 — dulu `outside_anchor` palsu — kini `PASS` dengan
  `requirePhotos`, `hasPhoto`, dan sembilan test baru di `new_declared`; brief 03 `PASS`. Brief 02 `SYMBOL` hanya atas
  `pickupShipmentNonSerialMembawaMetasNull`, test **eksisting** yang disunting tanpa disebut `Anchor` (anchor brief
  hanya menamai `onDeliveryMenurunkanStokDanMelepasBooking`) — temuan sah menurut K4; test baru brief itu tidak lagi
  ditandai. Celah tersisa ada di sisi `plan`: Check N tidak menagih agar tiap simbol eksisting yang disebut `## Steps`
  ikut tercantum di `Anchor` (kandidat langkah berikutnya, bukan bagian issue ini).
- L1 atas empat brief: brief 02 dan 03 kini 0 langkah produksi (4 dan 3 langkah test); gabungan 02+03+04 = 2 langkah
  produksi + 7 test → muat satu brief, dulu terpecah tiga.
- Belum: rantai `PRD_BRIEF` utuh dengan plugin 0.21.0 terpasang (H3/H4/E1/E2/T1 berjalan di main loop dan butuh
  persetujuan user di gerbang dokumen) dan compare `token_usage.py`; keduanya menunggu plugin 0.21.0 dipasang.

**Keputusan uji lapangan (2026-11-11, user):** branch di-push dan dibuka sebagai PR #7; user memasang 0.21.0
sendiri. Uji lapangan menumpang tiket backend nyata berikutnya yang butuh PRD (bukan kode tiruan atau ulang #80).
Sesudah sesi itu: cek berhenti di serah terima PRD → `/clear` → "lanjutkan" sampai `plan`, Profil S mode delta,
`plan` tanpa dispatch untuk unit tertutup laci, dispatch lewat `.explore/prompt/`, `close_brief.py` per brief, lalu
`token_usage.py ringkas`/`explorer` `--since <waktu 0.21.0 terpasang>` dibanding baseline Tahap 0.

Test baru: `tests/backend/test_symbol_map_32.py` (S1–S2), `test_serah_terima_32.py` (H3–H4),
`test_explorer_delta_32.py` (E1–E2, patok prosa), `test_slicing_steps_32.py` (L1), `test_close_brief_32.py` (C1),
`test_render_prompt_32.py` (T1); `tests/test_smoke.py` mendapat `close_brief.py`, `render_prompt.py`, dan
`symbol_map.py --brief`.

**Hasil Tahap 0 (baseline sejak 0.20.x, `--since "2026-11-10 15:40"`, wms + orderhub):** 12 sesi, 543 pemanggilan
main loop, konteks rata-rata 186.021 (p90 331.348). Fase `plan` 23,7% biaya main loop (konteks 301.706),
`architect` 13,4% (191.362), `system-analysis` 12,8% (230.807). Dispatch `backend:code-explorer`: 4 gerbang
(198.745/agent), 3 Profil S (335.368), 2 Profil B (488.823, satu masih tumpang tindih), 2 `plan` (136.949).

Selisih pelaksanaan terhadap Kontrak:

- **S2**: Kontrak menyebut `test_l29_symbol_map.py` memakai `lines` hanya di mode tanpa `--anchor`; satu test
  (`test_signature_change_maps_to_own_method`) ternyata memakainya di mode anchor. Test itu kini memakai `--verbose`.
- **H3**: `tech-lead/SKILL.md` dibatasi 14.000 byte (`test_l28_tech_lead.py`); tambahan H3/H4/T1 muat dengan
  memadatkan beberapa kalimat tanpa membuang aturan (contoh `COMPLETED (WARNING)` dipatok `test_l212`, dipertahankan).
- **H4**: field `hop_terakhir` tidak diperlukan — `journey.py show --json` sudah mengembalikan `entri` lengkap dengan
  `hop`; 6a butir 4 membaca unsur terakhirnya.
- **E1**: mode delta tetap menagih `### Key Pointers & Evidence`, tetapi hanya klaim kontrak (tipe, enum, anotasi,
  batas transaksi) atas pointer laporan gerbang. Laporan gerbang `ringkas` tidak memuat tipe field, sedangkan kolom
  tipe `## API contract` PRD bersandar pada seksi itu.
- **E2**: kolom `explore` matriks diisi slug laporan Profil S untuk unit yang tertutup laci; tidak ada perubahan
  skrip. Penegakannya prosa (patok teks), bukan mekanis.
- **T1**: tanpa opsi `--profil` (Profil S dan B sudah berkas terpisah). Prompt jadi ditulis ke subdirektori
  `.explore/prompt/` — bukan `.explore/prompt-<slug>.md` — karena `validate_briefs.py` memanen seluruh
  `.explore/*.md` dan prompt `plan` memuat kerangka `### File Map`. Slot dibaca dari tabel `### Slot Hidrasi`; slot
  bertanda `[OPTIONAL]` atau "Diisi hanya …" opsional. `${CLAUDE_PLUGIN_ROOT}` dilarang lint di luar `SKILL.md`, jadi
  dispatcher menyebut `_common/render_prompt.py` relatif root plugin. Keenam agent mendapat aturan "prompt berupa
  rujukan berkas". **Koreksi perkiraan:** blok template hanya ±15–30% isi dispatcher (sisanya tabel slot, aturan,
  dan penanganan balikan yang tetap dibaca per seksi), jadi penghematan baca jauh di bawah ±68 ribu karakter.
  Penghematan yang lebih pasti ada di output main loop: prompt Agent kini satu kalimat, bukan 2–7 ribu karakter per
  dispatch (±50 ribu karakter output pada kasus #80).
- **C1**: lease selalu dicabut di akhir `close_brief.py`, apa pun vonisnya; jalur yang berhenti sebelum butir 4
  (`BLOCKED`, `HALT.md` gerbang kompilasi) tetap memakai `guard_bash.py lease --clear`.

## Temuan dasar (data transkrip)

Kasus: 3 berkas produksi (17 baris) dan 8 berkas test (212 baris) di satu modul; risk `BREAKING`, chain `PRD_BRIEF`;
rantai `tech-lead` → `analyst` → `task` → `system-analysis` → `plan` (4 brief) → `architect` → `code-reviewer` →
`report`. Review akhir `CLEAN`.

Main loop: 153 giliran, 34,7 juta cache read (termasuk percakapan sesudah `report`). Konteks tumbuh dari 68 ribu ke
420 ribu sebelum `/compact`.

| Fase (skill terakhir dimuat) | Giliran | Konteks rata-rata | Cache read |
|---|---|---|---|
| `tech-lead` | 19 | 107 ribu | 2,0 juta |
| `analyst` + `task` | 11 | ±160 ribu | 1,7 juta |
| `system-analysis` | 29 | 240 ribu | 6,9 juta |
| **`plan`** | **35** | **357 ribu** | **12,5 juta (36%)** |
| `architect` (sesudah `/compact`) | 37 | 180 ribu | 6,6 juta |

Prosa plugin yang masuk konteks main loop: isi skill yang dimuat 165 ribu karakter, berkas plugin yang dibaca
(reference, template, dispatcher) ±220 ribu karakter. Totalnya kira-kira sepertiga dari pertumbuhan 68 → 420 ribu
(perkiraan 3,5 karakter per token). Komponen terbesar:

| Jenis | Berkas | Karakter |
|---|---|---|
| Dispatcher | `tech-lead`/`plan` `explorer.md`, `explorer-surface.md`, `explorer-blast.md`, tiga `reviewer.md`, `implementor.md` | ±68 ribu |
| Template dokumen | `prd-template.md`, `brief-template.md`, `task-template.md` | ±46 ribu |

Dispatcher dibaca utuh untuk menghasilkan prompt sepanjang 2–7 ribu karakter, lalu menetap di konteks.

Explorer: 8 dispatch. Tiga dispatch gerbang (`ringkas`), dua Profil S + satu Profil B (`menyeluruh`), dua `plan`
(`ringkas`). Profil S dan `plan` memetakan ulang `RecallOrderService.process`/`pickupShipmentProcess` beserta DTO yang
sudah dipetakan gerbang. Prompt kedua explorer `plan` sendiri menulis "pemetaan layer sudah ada di laci taskdir —
panen lewat Tahap 0, jangan ulangi".

Lain-lain yang terukur:

- Dua panggilan `symbol_map.py` menghasilkan 15,6 ribu karakter; isinya didominasi daftar `lines`.
- Cek simbol memvonis `outside_anchor` pada method dan test baru di brief 01, 02, dan 04 → satu `AskUserQuestion` dan
  tiga penyimpangan dicatat.
- Pickup butuh 6 berkas fixture + DTO + test baru → 3 brief, karena `MAX_STEPS = 5` menghitung langkah test.
- `architect`: 37 giliran untuk 4 brief (±9 per brief).

## Tujuan

1. Hilangkan alarm palsu cek simbol tanpa melonggarkan penjagaan atas suntingan simbol yang sudah ada.
2. Turunkan konteks main loop di fase `plan` dan ongkos prosa plugin per giliran.
3. Hentikan penelusuran ulang permukaan yang sudah dibuktikan explorer sebelumnya.
4. Kurangi brief dan giliran yang lahir dari aturan mekanis, bukan dari kerumitan kerja.

## Keputusan

- **K1 — Backend saja.** Frontend dan plugin lain di luar cakupan.
- **K2 — Langkah 30 K2 dicabut.** Titik serah terima menjadi dua: PRD `APPROVED` → `plan` (hanya chain ber-PRD:
  `PRD_BRIEF`, `BRD_PRD_BRIEF`) dan `READY_FOR_IMPLEMENTATION` → `architect` (tetap). Alasan: fase `plan` memakan 36%
  cache read main loop sambil membawa prosa `tech-lead`/`analyst`/`task`/`system-analysis` dan proses penulisan PRD
  yang tidak ia butuhkan; seluruh state yang ia butuhkan sudah di disk (materai, ledger, `JOURNEY.md`, laci
  `.explore/`). Sesudah `REPORT.md` tetap bukan titik henti.
- **K3 — Langkah 31 K5 ditutup dengan usulan 1 hasil X4.** Profil S berobjektif sempit: pointer laporan gerbang
  menjadi `konteks_diketahui`, dan objective S hanya menagih yang tidak dimiliki laporan gerbang (`### Flow & Trace`,
  `### Rules, Invariants & Config`, `### Error Surface`, mirrored path). Kedalaman tetap `menyeluruh` untuk bagian
  yang ditagih.
- **K4 — Cek simbol membedakan deklarasi baru dari suntingan.** Simbol yang deklarasinya tidak ada di `sha^:path`
  dinilai terhadap `## Steps` brief (brief berisi kode lengkap, jadi nama barunya tertulis di sana). Suntingan atas
  simbol yang sudah ada tetap dinilai terhadap kolom `Anchor`. Risiko yang dijaga, suntingan diam-diam pada kode lama,
  tetap terjaga.
- **K5 — Gerbang mutu tidak dilonggarkan.** Aturan chain (`chain-rules.md` bagian 1.2 dan 1.4), ronde review PRD dan
  brief, `code-reviewer` opus, dan brief berkode lengkap tidak berubah.
- **K6 — Badan prompt dirender skrip ke laci `.explore/`, dibaca subagent.** Skrip mengisi slot dan menulis prompt
  jadi ke laci kerja di dalam repo; prompt Agent hanya menunjuk berkas itu. Main loop tidak pernah memuat badan
  template. Dipilih atas dua alternatif: render ke stdout (prompt jadi tetap lewat konteks dua kali) dan subagent
  membaca template di cache plugin (subagent background tidak dapat meminta izin `Read` di luar repo).
- **K7 — `plan` memanen laci lalu mendispatch delta.** Unit yang berkasnya sudah tertutup laporan Profil S dan
  Profil B tidak didispatch; celah yang tercatat di laporan itu didispatch dengan objective sempit atas celahnya saja
  (pola yang sama dengan K3).
- **K8 — Langkah test dikenali dari `## File scope`, format brief tidak berubah.** Tidak ada penanda baru di template
  brief; langkah yang tautannya tak terbaca tetap dihitung (fail-closed).
- **K9 — Blok serah terima sesudah PRD milik `tech-lead`.** `analyst` mengembalikan vonis, `tech-lead` mencetak blok
  dan berhenti. Teks serah terima tetap satu rumah di `gate-lifecycle.md` bagian 6a, seperti Langkah 30 H1.

## Kontrak

### S1 — Deklarasi baru di cek simbol (K4)

- `symbol_map.py` menerima `--brief <brief_path>`. Dengan opsi itu skrip membaca sendiri kolom `Anchor` baris
  `--path` di `## File scope` (menggantikan salinan manual `--anchor`) dan teks `## Steps`.
- Simbol `fn` yang deklarasinya tidak ada di `sha^:path` dan namanya disebut `## Steps` → `new_declared`, bukan
  `outside_anchor`. Tidak disebut `## Steps` → tetap `outside_anchor` (exit 1).
- `--anchor` tanpa `--brief` tetap berlaku dengan perilaku lama (kompatibilitas).
- `architect/SKILL.md` Fase 3 butir 4 dan `brief-template.md` bagian 2 (aturan "simbol di luar kolom `Anchor`")
  diselaraskan: simbol baru sah bila dideklarasikan di `## Steps`.

### S2 — Keluaran `symbol_map.py` ringkas

Dengan `--anchor` atau `--brief`, `lines` tidak dicetak; keluaran memuat `status`, `path`, `sha`, `symbols`,
`outside_anchor` (beserta nomor barisnya), `type_level_unanchored`, dan `new_declared`. `--verbose` mengembalikan
`lines`. Tanpa `--anchor`/`--brief`, keluaran tidak berubah (test `test_l29_symbol_map.py` memakai `lines` di mode
itu).

### H3 — Titik serah terima PRD → `plan` (K2)

- **Vonis `analyst` (K9).** Sesudah Fase 4 menulis materai PRD `APPROVED` dan entri journey `PRD` **pada pemanggilan
  yang sama**, bila hop berikutnya di ledger adalah `BRIEF`: `analyst` tidak memanggil `plan`, tetapi mengembalikan
  vonis baru `PRD_APPROVED_SERAH_TERIMA` ke `backend:tech-lead` (seksi Output `analyst/SKILL.md` dan
  `chain-rules.md` bagian 4). `analyst` tidak punya aturan "lanjutkan hop berikutnya di giliran yang sama", jadi
  tidak ada pengecualian IRON LAW yang perlu ditulis di sisinya.
- **Syarat "pemanggilan yang sama" mencegah putaran.** `analyst` yang masuk lewat Fase 0 resume (H4) dengan PRD yang
  sudah `APPROVED` sebelumnya langsung menjalankan hop `BRIEF`; ia tidak pernah mengembalikan vonis serah terima lagi.
- **Titik henti di `tech-lead`.** Tabel pengirim balik `gate-lifecycle.md` bagian 6 butir 3 mendapat baris
  `PRD_APPROVED_SERAH_TERIMA` → bagian 6a. Di sana gerbang mencetak blok di bawah apa adanya di slot **Langkah Lanjut**
  `### TECH-LEAD RE-ENTRY DECISION` dengan **Status Rantai** `TERTAHAN (serah terima PRD)`, lalu berhenti. Pengecualian
  IRON LAW `tech-lead` "langkah pertama di giliran yang sama" diperluas eksplisit ke titik ini. Balasan "lanjut" di
  sesi yang sama → rute H4 (`analyst` pada taskdir sama).

  ```
  PRD disetujui. Journey dicatat di <taskdir>/JOURNEY.md.
  Hemat konteks sebelum plan (pilih salah satu):
    a. /clear → /backend:tech-lead lanjutkan <taskdir>      (paling hemat: mulai dari ±70 ribu token)
    b. /compact fokus taskdir <taskdir> → /backend:tech-lead lanjutkan <taskdir>
  Atau balas "lanjut" untuk menulis brief di sesi ini tanpa membersihkan konteks.
  ```

- **Re-entry** lewat `tech-lead`, bukan `/backend:analyst` langsung (konsisten dengan Langkah 30 K4); rutenya H4.
- **Blok 6a yang ada** mendapat keterangan ongkos yang sama pada opsi a/b.
- Tidak ada state baru: "sudah berhenti di serah terima" hanya tercatat di journey (sama seperti Langkah 30 H2).

### H4 — Rute lanjutan hop `BRIEF` di gerbang `tech-lead`

**Celah sekarang.** Sisi `analyst` sudah siap: prasyarat check 7 (`analyst/scripts/check_preconditions.py`
`_check_7_resume_point`) membaca ledger `## Chain` dan mengembalikan `Resume: hop BRIEF` bila `PRD` `[x]` dan `BRIEF`
`[ ]`, lalu Fase 0 butir 3 masuk Fase 3 pada hop itu. Yang belum ada adalah rute gerbang ke sana. Taskdir berkeadaan
"PRD `APPROVED`, hop `BRIEF` belum tercentang, belum ada brief" tidak cocok dengan satu baris pun di:

- tabel `tech-lead/references/gate-lifecycle.md` bagian 1 (hanya `BRD.md`/`PRD.md` `DRAFT` → `analyst`);
- state machine `tech-lead/references/decisions.md` bagian 4 (butir 3 hanya "Artefak DRAFT");
- enumerasi `tech-lead/SKILL.md` Fase 3 butir 1;
- `gate-lifecycle.md` bagian 6a butir 4 (lanjutan serah terima hanya untuk entri journey terakhir ber-hop `READY`).

Tanpa baris itu, "lanjutkan `<taskdir>`" jatuh ke penilaian bebas model, dan yang paling mungkin terjadi adalah
gerbang biasa yang mengulang Fase 1–4 (explorer gerbang, keputusan lane, dan risk) di atas taskdir yang sudah berakar.

**Kontrak.**

1. **Baris tabel baru** (bagian 1, `decisions.md` bagian 4, dan enumerasi Fase 3 butir 1, ketiganya selaras):
   taskdir berledger `## Chain` dengan hop belum tercentang (`[ ]`/`[~]`), tanpa brief `BLOCKED`, tanpa `HALT.md`
   aktif, tanpa brief `READY`, dan tanpa `BRD.md`/`PRD.md` `DRAFT` → rutekan ke `backend:analyst` pada taskdir sama,
   **tanpa** `reentry_reason` (hop yang terbuka bukan re-entry). Baris ini umum, bukan khusus `BRIEF`: ia juga menutup
   hop `PRD` yang belum mulai sesudah BRD `APPROVED` (chain `BRD_PRD_BRIEF`).
2. **Urutan presedensi tabel tidak berubah.** `BLOCKED`/`HALT.md` aktif → brief `READY` → artefak `DRAFT` → baris
   baru. Taskdir yang sudah punya brief `DRAFT` (plan sempat berjalan lalu terputus) jatuh ke baris baru, karena hop
   `BRIEF` belum tercentang. Di sana `analyst` Fase 0 masuk hop `BRIEF`, dan `plan` menangani brief yang sudah ada
   lewat prasyaratnya sendiri.
3. **Lanjutan serah terima** (bagian 6a butir 4 diperluas): `request` hanya meminta melanjutkan `taskdir` yang
   diberikan, dan entri journey terakhir ber-hop `PRD` → Fase 0 (termasuk `journey.py show`) → prasyarat penuh
   `--re-entry` (Fase 5 butir 1) → rutekan langsung ke `backend:analyst` dengan `taskdir`; Fase 1–4 dilewati. Parameter
   `lane`, `risk`, dan `chain` dibaca dari frontmatter `TASK.md`, bukan diturunkan ulang (prasyarat `analyst` check 4
   menolak nilai yang berbeda). Branch kerja taskdir di-checkout bila belum aktif, tanpa mencabangkan ulang.
4. **Disk menang atas journey** (Langkah 30 K5). Entri journey hanya membuka jalur cepat "lewati Fase 1–4". Tujuan rute
   tetap dari disk: bila disk menunjukkan brief `READY`, rutenya `architect` walaupun entri terakhir `PRD`; bila
   ledger `PRD` belum tercentang, rutenya baris `DRAFT`/baris baru sesuai keadaan.
5. **`request` membawa permukaan baru di luar taskdir** → gerbang biasa, sama seperti butir 4 sekarang.

**Yang tidak berubah.** `analyst` Fase 0, prasyarat check 7, dan `journey.py` (enum `HOPS` sudah memuat `PRD`). Tahap 2
memastikan `journey.py show --json` cukup untuk membaca hop entri terakhir; bila belum, tambahkan field
`hop_terakhir` (perubahan aditif, `--json` tetap valid untuk `test_smoke`).

### E1 — Profil S delta (K3)

`system-analysis/references/analysis-protocol.md` bagian A Tahap 0 dan `dispatcher/explorer-surface.md`: untuk simbol
yang sudah dipetakan laporan gerbang, objective Profil S hanya menagih seksi yang tidak dimiliki laporan gerbang
(K3); permukaan (a) dan (b) yang sudah tertutup tidak dipetakan ulang. Simbol tanpa laporan gerbang → Profil S penuh
seperti sekarang.

### E2 — Predikat dispatch `plan` menghitung laci (K7)

`plan/SKILL.md` Fase 2 butir 2, `references/slicing-and-scan.md`, dan `dispatcher/explorer.md`:

1. **Unit tertutup** bila kedua syarat terpenuhi:
   - tiap berkas kode unit punya simbol anchor berbukti `file:baris` di `### Key Pointers & Evidence` atau
     `### Flow & Trace` laporan Profil S, dan
   - tiap berkas test yang menguji simbol itu tercantum di baris dimensi 11 `### Blast Map` laporan Profil B.

   Unit tertutup tidak didispatch. Fase 3 langkah 3 memanen seksi-seksi itu sebagai pengganti `### File Map`.
2. **Celah tercatat** dihitung dari dua tempat: `### Risks, Gaps & Not Found` laporan S atau B, dan catatan "tidak
   dibuktikan" di kolom bukti dimensi 11. Contoh di #80: "isi builder body tidak dibuktikan per berkas". Celah
   seperti ini didispatch lewat template `plan` dengan `Kedalaman: ringkas`, dan objective-nya hanya menagih celah itu.
   Laporannya tetap `<slug>-<NN>.md` dengan `### File Map` untuk baris yang ditagih saja.
3. **Laporan `confidence: low`**, atau unit tanpa laporan S/B → dispatch penuh seperti sekarang.
4. **Gerbang mekanis tidak berubah.** Check I (berkas test) dan Check N (resolusi anchor) tetap menagih brief. Panen
   laci `validate_briefs.py` (`explore_map`) yang tidak menemukan `### File Map` turun ke resolusi disk, karena
   ketiadaan laci memang bukan kegagalan. Tahap 3 memastikan perilaku ini dengan test.

### T1 — Dispatcher dirender ke laci (K6)

**Skrip baru `skills/_common/render_prompt.py`** (backend saja, bukan salinan byte-identik):

```
render_prompt.py --template <dispatcher.md> [--profil S|B] --slot nama=nilai ... [--slots-json <path>] --out <path>
```

- Mengambil blok template prompt dari dispatcher, yaitu blok berpagar di bawah heading template, atau blok profil yang
  diminta `--profil` untuk `explorer-surface.md`/`explorer-blast.md`. Lalu mengisi slot.
- **Slot wajib kosong** → exit 1 beserta nama slotnya; prompt tidak ditulis.
- **Slot `[OPTIONAL]` kosong** → barisnya dihapus utuh, sesuai aturan Slot Hidrasi yang berlaku sekarang.
- **`--slots-json`** untuk nilai multi-baris (mis. `konteks_diketahui`).
- **`--out`** wajib berada di laci kerja:
  - `{taskdir}/.explore/prompt-<slug>.md` untuk skill hilir;
  - `backenddev/docs/.explore/prompt-<slug>.md` untuk dispatch gerbang `tech-lead`, yang belum punya taskdir.

  Di luar laci → exit 2.
- **`--json`** selalu JSON valid (path keluaran, jumlah karakter, slot yang terisi); skrip masuk `CASES` `test_smoke`.

**Berkas dispatcher tidak dipecah.** Blok template tetap di tempatnya; yang berubah adalah cara bacanya. Main loop
hanya membaca seksi Slot Hidrasi, aturan pendispatch, dan `### Penanganan Balikan` (per heading), lalu menjalankan
skrip. Prompt Agent berisi satu kalimat: "Baca dan jalankan instruksi di `<path>`; jangan menyuntingnya." Subagent
membacanya dengan `Read` di dalam repo, sehingga tidak ada izin di luar repo, dan `guard_bash.py` tidak memagari `Read`.

**Cakupan:** seluruh dispatcher `backend`:

| Skill | Dispatcher |
|---|---|
| `tech-lead` | explorer |
| `system-analysis` | explorer-surface, explorer-blast, reviewer |
| `plan` | explorer, reviewer |
| `business-analysis` | explorer, reviewer |
| `debug` | explorer |
| `architect` | implementor, reviewer |

Kalimat "dilarang menyusun prompt di luar template resminya" di guardrail tiap SKILL ditulis ulang menjadi
"dispatch hanya lewat `render_prompt.py` atas template resminya".

### L1 — Langit-langit langkah tidak menghitung langkah test (K8)

`validate_briefs.py` `_check_slicing` dan `_count_steps`:

- **Langkah test**: semua baris `## File scope` yang disebut langkah itu adalah berkas test (`_is_test_path`). Cara
  menyebut berkas dihitung dua: path lengkap, atau nama berkas tanpa ekstensi (mis. `RecallOrderPickupSerialStockTest`).
- **Langkah test tidak dihitung terhadap `MAX_STEPS`.** Ini selaras dengan `MAX_CODE_FILES`, yang sudah mengecualikan
  berkas test.
- **Langkah yang tidak menyebut satu pun baris `## File scope` tetap dihitung** (fail-closed).
- **Plafon 120 baris `## Steps` per brief** tetap menjadi pengaman ukuran.
- **Pesan Check L** menyebut kedua angka, mis. `6 langkah (2 produksi, 4 test; langit-langit 5 produksi)`.

Prosa langit-langit di `slicing-and-scan.md` bagian 3A butir 3, `check-catalog.md`, `plan/SKILL.md`,
`plan/dispatcher/reviewer.md`, dan `agents/brief-reviewer.md` diselaraskan.

### C1 — Satu perintah penutup per brief

Perintah baru `architect/scripts/close_brief.py --taskdir <t> --brief <b> --sha <sha>` menjalankan berurutan:
`git status --porcelain` (kecuali `.explore/`), `verify_scope.py`, `symbol_map.py --brief` atas tiap berkas `modify`,
`guard_bash.py lease --clear`, dan pembacaan status brief. Keluaran: satu baris vonis per brief (`PASS`, atau
`STRAY`/`SCOPE`/`SYMBOL` beserta path dan simbol), `--json` selalu JSON valid. Vonis tetap exit skrip yang dipanggil;
`HALT.md` tetap ditulis main loop. `verify_scope.py` dipanggil, tidak diubah (salinan byte-identik dengan frontend).

### D1 — Dokumen dan rilis

`flow/backend.md`, README backend, `MIGRATION_v0.20.2_to_v0.21.0.md` (titik serah terima kedua mengubah perilaku yang
dilihat user), `plugin.json` 0.21.0.

## Perkiraan dampak (kasus #80, belum diuji)

| Item | Perkiraan |
|---|---|
| H3 | `plan` mulai dari ±90 ribu, rata-rata ±150 ribu alih-alih 357 ribu → ±7 juta cache read (±20% main loop) |
| S1 | Satu `AskUserQuestion` dan tiga catatan penyimpangan hilang |
| S2 | ±13 ribu karakter per rantai sejenis tidak masuk konteks |
| E1–E2 | 2–3 dari 8 dispatch explorer hilang atau menyempit |
| L1 | Pickup: 3 brief → 1–2 brief; tiap brief yang hilang menghemat lease, dispatch implementor (27–69 ribu cache write), dan ±9 giliran `architect` |
| C1 | ±3 giliran per brief → ±2 juta cache read untuk 4 brief |
| T1 | ±68 ribu karakter dispatcher tidak menetap di konteks main loop |

## Peta blast radius (awal — diverifikasi ulang di tiap tahap)

| Berkas | Item |
|---|---|
| `skills/architect/scripts/symbol_map.py`, `skills/architect/SKILL.md` (Fase 3 butir 4), `skills/architect/references/rationale.md` (R2/R3), `skills/plan/templates/brief-template.md` (bagian 2), `skills/architect/dispatcher/implementor.md` | S1, S2 |
| `tests/backend/test_l29_symbol_map.py`, `tests/backend/test_11_robustness.py`, `tests/test_smoke.py` | S1, S2 |
| `skills/analyst/SKILL.md` (Fase 4 dan Output), `skills/analyst/references/chain-rules.md` (bagian 4), `skills/tech-lead/references/gate-lifecycle.md` (bagian 6 butir 3 dan 6a), `skills/tech-lead/SKILL.md` (IRON LAW, Fase 5), `tests/backend/test_journey_30.py` (satu-satunya test yang mematok vonis `READY_FOR_IMPLEMENTATION`) | H3 |
| `skills/tech-lead/references/gate-lifecycle.md` (bagian 1 dan 6a butir 4), `skills/tech-lead/references/decisions.md` (bagian 4), `skills/tech-lead/SKILL.md` (Fase 3 butir 1), `skills/_common/journey.py` (bila `hop_terakhir` diperlukan), `tests/backend/test_l211_route_lint.py`, `tests/backend/test_l25_analyst_resume.py`, `tests/backend/test_journey_30.py`, `tests/test_smoke.py` | H4 |
| `skills/system-analysis/references/analysis-protocol.md`, `skills/system-analysis/dispatcher/explorer-surface.md`, `skills/system-analysis/SKILL.md`, `tests/backend/test_explorer_balikan_31.py` | E1 |
| `skills/plan/SKILL.md` (Fase 2 dan Fase 3 langkah 3), `skills/plan/references/slicing-and-scan.md`, `skills/plan/dispatcher/explorer.md` (Penanganan Balikan), `skills/plan/scripts/validate_briefs.py` (hanya bila panen `explore_map` perlu disesuaikan), `tests/backend/test_validate_briefs_matching.py` | E2 |
| `skills/_common/render_prompt.py` (baru); sebelas dispatcher di tabel T1; guardrail DISPATCH di `SKILL.md` `tech-lead`, `system-analysis`, `plan`, `business-analysis`, `debug`, `architect`; `tests/backend/test_render_prompt_32.py` (baru); `tests/backend/test_explorer_balikan_31.py`; `tests/test_smoke.py` (`CASES`); `agents/code-explorer.md` dan agent reviewer hanya bila definisinya menyebut cara prompt diterima | T1 |
| `skills/plan/scripts/validate_briefs.py`, `skills/plan/references/slicing-and-scan.md`, `skills/plan/references/check-catalog.md`, `skills/plan/SKILL.md`, `skills/plan/dispatcher/reviewer.md`, `agents/brief-reviewer.md`, `skills/plan/scripts/scaffold_brief.py`, `tests/backend/test_validate_briefs_matching.py` | L1 |
| `skills/architect/scripts/close_brief.py` (baru), `skills/architect/SKILL.md` (Fase 3 butir 1 dan 4), `tests/backend/test_close_brief_32.py` (baru), `tests/test_smoke.py` (`CASES`) | C1 |
| `flow/backend.md`, `src/plugins/backend/README.md`, `MIGRATION_v0.20.2_to_v0.21.0.md`, `plugin.json` | D1 |

Path berkas plugin di atas relatif terhadap `src/plugins/backend/`.

## Urutan pengerjaan

| Tahap | Item | Alasan urutan |
|---|---|---|
| 0 | Baseline | `token_usage.py` atas sesi OrderHub/WMS sejak 0.20.2: cache read per fase, dispatch explorer per fase, ukuran keluaran `symbol_map`. |
| 1 | S1, S2 | Bug yang menghentikan rantai dengan alarm palsu; perubahan satu skrip dan prosa pemakainya. |
| 2 | H4, lalu H3 | Penghematan terbesar; berdiri di atas mekanisme Langkah 30. Rute lanjutan (H4) dipasang sebelum titik henti (H3), supaya titik henti tidak pernah terbit tanpa jalan kembali. |
| 3 | E1, E2 | Mengubah predikat dispatch; diukur terpisah dari H3. |
| 4 | T1, L1, C1 | T1 menyentuh banyak dispatcher; L1 dan C1 bergantung pada S1 (C1 memanggil `symbol_map.py --brief`). |
| 5 | D1 | Dokumen, migrasi, versi. |

## Verifikasi ujung ke ujung

- Suite penuh hijau, lint `--base origin/main` 0 FAIL, `claude plugin validate .`.
- S1: fixture commit yang menambah method baru yang disebut `## Steps` → `PASS` dengan `new_declared`; menyunting
  method lama di luar `Anchor` → tetap `FAIL`; method baru yang tidak disebut `## Steps` → tetap `FAIL`.
- H3 + H4: uji manual satu rantai `PRD_BRIEF` di repo nyata: berhenti sesudah PRD `APPROVED`, `/clear`, "lanjutkan"
  sampai ke `plan` hop `BRIEF` tanpa menulis ulang PRD dan tanpa explorer gerbang baru.
- H3: `analyst` yang masuk lewat resume dengan PRD sudah `APPROVED` menjalankan hop `BRIEF`, tidak mengembalikan
  `PRD_APPROVED_SERAH_TERIMA` (tidak ada putaran).
- E2: fixture laci dengan laporan S + B yang menutup unit → nol dispatch `plan`; laporan B bercatatan "tidak
  dibuktikan" → satu dispatch delta; `validate_briefs.py` lolos Check N lewat resolusi disk tanpa `### File Map`.
- T1: `render_prompt.py` menolak slot wajib kosong, menghapus baris slot opsional kosong, menolak `--out` di luar laci;
  satu rantai nyata berjalan tanpa main loop membaca badan template mana pun (dicek dari transkrip lewat
  `token_usage.py`).
- L1: brief-02 + brief-03 + brief-04 kasus #80 digabung jadi satu brief (2 langkah produksi, 7 langkah test) → Check L
  lolos; langkah yang tak menyebut berkas `## File scope` tetap dihitung.
- H4: test rute untuk empat keadaan taskdir: (a) PRD `APPROVED` + `BRIEF` `[ ]` tanpa brief → `analyst`; (b) sama tetapi
  ada brief `DRAFT` → `analyst`; (c) entri journey terakhir `PRD` tetapi brief `READY` di disk → `architect`;
  (d) BRD `APPROVED` + `PRD` `[ ]` tanpa `PRD.md` → `analyst`.
- Ukur ulang dengan `token_usage.py` dibanding Tahap 0: konteks rata-rata fase `plan`, jumlah dispatch explorer per
  taskdir ber-PRD, giliran `architect` per brief.

## Trade-off yang diterima

- H3 menambah satu interupsi pada rantai ber-PRD. Opsi "lanjut" tetap ada bagi user yang tidak ingin berhenti.
- E1 dan E2 bergantung pada kualitas laporan sebelumnya; laporan `confidence: low` tetap memicu dispatch penuh.
- L1 dapat menghasilkan brief dengan banyak langkah fixture; plafon 120 baris `## Steps` yang membatasinya. Langkah
  yang menyebut berkas test hanya lewat nama kelas tanpa path tetap terkenali; yang tidak menyebut berkas sama sekali
  dihitung sebagai langkah produksi.
- T1 menambah satu panggilan Bash per dispatch (render) dan berkas `prompt-<slug>.md` di laci. Laci tetap tidak
  di-stage. Prompt jadi dapat dibaca ulang untuk audit dispatch.

## Di luar cakupan

- Usulan umpan balik nomor 6 (jalur PRD lebih pendek untuk `BREAKING`, atau melewati review PRD bila
  `validate_doc.py` lolos): `chain-rules.md` 1.2 butir 1 mewajibkan PRD untuk `BREAKING`, dan butir 2 (aturan validasi
  baru) memicu PRD walaupun `MAJOR`. Ditolak (K5).
- Pemangkasan template dokumen (`prd-template.md`, `brief-template.md`, `task-template.md`) dan body SKILL: tetap
  ditunda bersama pemangkasan SKILL (Langkah 30, Di luar cakupan).
- Isi brief tetap berkode lengkap; `code-reviewer` tetap opus.
- Konteks awal yang bukan milik plugin `backend` (memori proyek user, daftar agent seluruh plugin).

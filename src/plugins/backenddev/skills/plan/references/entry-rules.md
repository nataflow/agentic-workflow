# Repo Intake & Entry Rules Reference — `plan`

Penyerapan profil repositori, aturan jalur masuk Fase 1, dan kontrak panen artefak hulu untuk `backenddev:plan`. 12 dimensi scan dan batas slicing hidup di `slicing-and-scan.md`; uji mandiri rantai brief dan commit agregat di `review-and-commit.md`.

## 0. Penyerapan Profil Repositori

Dijalankan sesudah skrip prasyarat lulus dan sebelum jalur masuk ditetapkan.

1. Baca `../profile/stacks/<stack>.md` dengan `<stack>` dari field `stack` di `.claude/profile/index.json`. Seksi `## Layer taxonomy` di sana adalah sumber tunggal pola spesifik stack — dilarang memakai pola stack lain atau mengarangnya sendiri. Pilih sub-bagian sesuai field `architecture`; nilai `hybrid` atau `tidak terdeteksi` → ikuti struktur nyata modul target dan tulis bukti `file:line`-nya di brief. Berkas adapter tidak ada → hentikan eksekusi, rutekan ke `backenddev:profile`.
2. Serap `root_namespace` dan `source_root` dari `index.json`, pola penamaan modul dari `module-structure.md`, konvensi tipe batas, perintah test dan konfigurasi migrasi modul target dari `commands.md`, lalu `code-conventions.md`, `anti-patterns.md`, dan `invariants.md` (setelan skema penyimpanan, tenant scoping, zona waktu).
3. Identifikasi struktur modul target agar slicing Fase 3 tetap berada di dalam batasnya.

## 1. Jalur Masuk & Protokol Pintu Masuk (Fase 1)

Tentukan jalur dari matriks berikut; kondisi kolom ketiga berarti tolak dan kembalikan ke penerbit artefaknya:

| `entry_mode` | Masukan | Kondisi berhenti |
|---|---|---|
| `PRD` | `{taskdir}/PRD.md` | `status: DRAFT`, atau `## Open questions` menyentuh `## Task breakdown` (kontrak panen: bagian 1D) |
| `RCA` | `{taskdir}/RCA.md` | `status: INCONCLUSIVE`, atau `## Arah perbaikan` kosong (bagian 1C) |
| `LANGSUNG` | Permintaan terisolasi, diteruskan `backenddev:analyst` pada `chain: BRIEF` — perbaikan temuan berakar termasuk (bagian 1B) | Menyentuh 1 dari 5 pemicu eskalasi (bagian 1A) |

Ketiga nilai di atas adalah satu-satunya yang sah. `entry_mode` dipakai apa adanya dari pemanggil dan **tidak pernah disimpulkan dari artefak yang ada di taskdir**: kesimpulan itu membuat chain ber-PRD yang PRD-nya gagal terbit terbaca sebagai `LANGSUNG` yang sah, dan seluruh pemeriksaan ber-gate PRD dilewati tanpa satu pun kegagalan tercatat. Nilai kosong atau di luar ketiga enum dihentikan skrip prasyarat di check 3 dan dikembalikan ke `backenddev:analyst`, bukan ditebak di sini.

Sesudah jalur tetap, kunci daftar item masukan yang dipetakan ke rangkaian brief atomik.

### 1A. 5 Pemicu Eskalasi — `LANGSUNG`

Kena salah satu → BERHENTI SEGERA, batalkan rute MINOR beserta penulisan brief, eskalasi ke `system-analysis`:

1. **Kontrak API belum pasti**: endpoint baru dengan bentuk request/response belum ditetapkan, field response yang dipakai konsumen eksternal bertambah/hilang, atau HTTP status berubah.
2. **Transisi status / lifecycle berubah**: nilai enum status baru, transisi baru antar status eksisting, atau perubahan pihak yang berhak memicu transisi.
3. **Validation policy baru**: aturan validasi lintas-field yang belum pernah ada di modul tersebut, atau pelonggaran validasi eksisting.
4. **Permission atau boundary scope berubah**: role baru, perubahan hak akses method/endpoint, atau perubahan aturan scoping (`store_id`/`tenant_id`) di `## Invariants`.
5. **Side-effect lintas modul belum dipetakan**: perubahan memicu event queue, scheduled job, atau consumer di modul lain tanpa bukti `file:line` konsumen terdampak.

Kelimanya **tidak berlaku** di jalur `PRD` — PRD `APPROVED` sudah menguncinya. Investigasi akar masalah yang belum menemukan `file:line` konkret di jalur mana pun → BERHENTI, dispatch `code-explorer` via template `../dispatcher/explorer.md`.

**Jalan keluar eskalasi**: kembalikan pemicunya ke `backenddev:analyst` sebagai pemicu eskalasi chain nomor 1 — `analyst` menaikkan `chain` ke `PRD_BRIEF` beserta `risk` ke `MAJOR`, memverifikasi pasangan `(risk, chain)` hasilnya terhadap `analyst/references/chain-rules.md` bagian 1.4, lalu memberangkatkan hop PRD. Rutenya sama persis untuk batch ber-`finding_source`: temuan yang ternyata menuntut kontrak baru naik lewat kanal itu, bukan dikembalikan ke gerbang untuk diklasifikasi ulang dari nol. Dilarang memanggil `system-analysis` sendiri: skill itu menolak `risk_level` bernilai `MINOR` di Fase 0-nya, sehingga eskalasi tanpa reklasifikasi berhenti buntu.

### 1B. Akar dari Temuan — `finding_source`

`finding_source` terisi berarti `## Success Criteria` `TASK.md` berdiri di atas temuan terpilih dari `backenddev/issues/<file>.md` atau `{taskdir}/REVIEW.md`. Nilainya diteruskan `backenddev:analyst` apa adanya dan **tidak pernah disimpulkan** dari isi taskdir — ia menempel pada asal-usul akar, bukan pada jalur masuk, sehingga berlaku sama di `LANGSUNG` maupun `PRD`.

Seleksi temuan mana yang masuk beserta filter statusnya (`FIXED`, `DROPPED`, `OBSOLETE` keluar; `DEFERRED` dan tanpa penanda masuk) bukan pekerjaan skill ini: keduanya sudah dijalankan gerbang saat user memilih temuan, berplafon tujuh temuan per taskdir, dan rumah kanoniknya `../../tech-lead/references/gate-scope.md` bagian 6. Yang tersisa di sini dua kewajiban, keduanya dieksekusi di Fase 2 (`slicing-and-scan.md` bagian 2 butir 1 dan 7):

1. **Re-verification**: baca kode di `Lokasi` tiap temuan; sudah diperbaiki → tandai `OBSOLETE`, keluarkan dari batch, catat buktinya di `## Analysis trace`. Filter gerbang hanya menyaring status yang **tertulis** di berkas temuan; sapuan inilah satu-satunya yang menangkap temuan yang diam-diam tidak berlaku lagi.
2. **Temuan `PLAUSIBLE`**: yang blocker-nya belum terjawab user → tandai `DROPPED`, catat di `## Analysis trace`.

Temuan yang gugur di salah satu dari keduanya melepaskan `SC-{n}` pemikulnya, dan `SC-{n}` tanpa pemikul adalah kegagalan Check G yang tidak dapat diperbaiki di brief. Kembalikan ia ke `backenddev:analyst` sebagai permintaan amandemen akar (`../../analyst/references/chain-rules.md` bagian 5) beserta bukti gugurnya, lalu tunggu keputusan user. Dilarang menambal dengan brief kosong pemikul `SC-{n}` itu, dan dilarang pula menghapus nomornya sendiri dari `TASK.md`.

### 1C. Pemanenan `RCA.md` — `RCA`

`RCA.md` sudah membuktikan penyebab; `plan` tidak mengulang investigasinya. Tiga seksinya dipanen langsung jadi kontrak brief:

| Seksi `RCA.md` | Tujuan di brief | Aturan panen |
|---|---|---|
| `## Arah perbaikan` | `## File scope` | Tiap baris tabel jadi satu entri beserta aksinya (`modify`/`create`); baris tanpa path konkret dibuang, bukan ditebak |
| `## Regression guard` | `## File scope` + `## Risk & rollback` | Kelas test terdampak masuk `## File scope` (`modify`); nama assertion dan cara deteksi kegagalannya ditulis sebagai kalimat di `## Risk & rollback`, begitu pula mekanisme pencegahan pengganti beserta alasannya bila bertanda `tidak dapat digerbangi test` |
| `## Blast radius` | `## Mirrored paths` + batas slicing | Pemanggil lain dan endpoint terdampak menentukan perbaikan muat satu unit atau perlu dipecah |

**Gerbang masuk**: kembalikan ke `tech-lead` bila `status: INCONCLUSIVE` — rantai kausalnya belum utuh sehingga `## File scope` di atasnya adalah tebakan. Kembalikan ke `debug` bila `## Arah perbaikan` kosong padahal statusnya `ROOT_CAUSE_CONFIRMED`, atau bila scan Fase 2 menemukan bukti yang membantah rantai kausalnya — brief bukan tempat merevisi diagnosis.

**Batas kewenangan**: dilarang mengubah `## Rantai kausal` atau menambah root cause di brief. Terapkan 5 pemicu bagian 1A bila perbaikan menuntut DTO, endpoint, atau kolom baru.

### 1D. Pemanenan `PRD.md` — `PRD`

`PRD.md` `APPROVED` sudah mengunci kontraknya; `plan` menerjemahkannya, bukan merundingkannya ulang. Sembilan seksinya dipanen ke seksi brief menurut tabel berikut, dan seksi berisi yang tidak mendarat di satu pun brief adalah kegagalan Check A:

| Seksi `PRD.md` | Tujuan di brief | Aturan panen |
|---|---|---|
| `## API contract` | `## Interfaces` + `## Steps` | Tiap endpoint jadi langkah bersnippet: field request beserta tipe dan validasinya jadi definisi tipe batas, response sukses jadi bentuk kembalian, dan tiap baris tabel error jadi cabang penanganan yang menyebut kode dan pesannya persis PRD. Signature tipe batas yang dipakai brief lain masuk `Produces` |
| `## Status lifecycle` | `## Steps` | Tiap baris transisi jadi satu langkah bertitik sisip konkret; kolom `Efek samping` yang menyentuh berkas lain jadi langkah tersendiri, bukan catatan |
| `## Validation policy` | `## Steps` | Urutan evaluasi disalin jadi urutan langkah apa adanya. Dilarang meringkas atau menukar urutannya — determinisme itulah isi seksinya |
| `## Permission & scope` | `## Steps` + `## File scope` | Tiap baris matriks jadi anotasi atau filter security pada berkas yang disebut; boundary scoping jadi predikat konkret di query/guard, bukan kalimat sifat |
| `## Impact map` | `## File scope` + `## Mirrored paths` | Tiap baris bervonis `terdampak` wajib mendarat, dan kolom `Mendarat di`-nya menentukan unit penampungnya. Baris `tidak relevan` dibuang, bukan disalin jadi catatan |
| `## Migration requirements` | `## Migration` + `## Risk & rollback` | Aturan panennya di `../templates/brief-template.md` bagian 2 butir 10; ditagih Check J |
| `## Task breakdown` | Urutan brief (`NN`) + `## Steps` | Kolom `Bergantung pada` jadi arah DAG antar-brief dan tiap baris punya minimal satu langkah penampung. Kolom `Permukaan` menamai modul atau layer, bukan berkas: **pemilihan berkas beserta penamaannya adalah wewenang `plan`**, diturunkan dari profil repositori dan `## Layer taxonomy` adapter, lalu ditulis ke `## File scope`. PRD tidak pernah menetapkannya, dan perbedaan penamaan tidak pernah menuntut amandemen PRD |
| `## Acceptance criteria` | `Covers:` + `## File scope` | Nomor `AC-{n}` ke baris `Covers:` (ditagih Check H); tiap AC bertanda `test otomatis` menuntut minimal satu berkas test di `## File scope` brief pengklaimnya, dinamai menurut konvensi repo (ditagih Check I) |
| `## Open questions` | `## Objective` atau `## Risk & rollback` brief pengklaim | Pertanyaannya tidak dipanen, tetapi **asumsi aktifnya dipanen**. Entri yang menyentuh `## Task breakdown` atau `## Business rules` BRD adalah kondisi berhenti jalur ini. Tiap `sementara dipakai:` yang membentuk langkah brief turun jadi kalimat di `## Objective` brief itu — atau `## Risk & rollback` bila ia hanya perlu diawasi — bukan ke `## Analysis trace`: seksi itu dinyatakan "BUKAN pekerjaan eksekutor" oleh `../templates/brief-template.md`, sehingga asumsi yang mendarat di sana tak terlihat di titik eksekusi. Entri `BR-DISANGGAH:` tidak dipanen sama sekali; ia sudah diputuskan user di gerbang dokumen |

**Batas kewenangan**: dilarang menambah endpoint, field, transisi status, atau aturan validasi yang tidak ada di PRD. Kebutuhan yang muncul saat Fase 2 tetapi tidak tertutup PRD dikembalikan ke **pemanggilnya** — `backenddev:analyst` pada lane planning, `backenddev:tech-lead` pada jalur `RCA` — bukan diputuskan sendiri di brief dan bukan pula dikirim langsung ke `system-analysis`. Langkah brief yang menyentuh `## Out of Scope` `TASK.md` mengikuti rute yang sama: ia permintaan amandemen akar (`../../analyst/references/chain-rules.md` bagian 5), bukan keputusan `plan`.

# Chain Self-Review & Aggregate Commit Reference — `plan`

Protokol uji mandiri rantai brief (Fase 4), dispatch self-review kolektif, dan commit agregat (Fase 5) untuk `backenddev:plan`. Aturan jalur masuk hidup di `entry-rules.md`, 12 dimensi scan dan batas slicing di `slicing-and-scan.md`, kaidah isi brief di `../templates/brief-template.md` bagian 2.

## 4. Protokol Chain Self-Review (Fase 4)

Lima belas pemeriksaan mandiri dijalankan sesudah seluruh brief batch aktif selesai ditulis. Empat belas di antaranya — seluruhnya kecuali Check A — mekanis atas token, dan **dieksekusi `scripts/validate_briefs.py`**, bukan dibaca satu per satu main loop. Skrip melaporkan seluruh pelanggaran dalam satu keluaran; remediasinya dikerjakan sekaligus lalu skrip dijalankan sekali lagi sebagai konfirmasi. Rangkaian tidak pernah diulang per satu cacat.

Daftar di bawah adalah **rumah kanonik predikatnya** — apa yang ditagih tiap check dan bagaimana kegagalannya diremediasi. Skrip menegakkannya; teks ini yang mendefinisikannya. Menyunting salah satu tanpa yang lain membuat keduanya memvonis dengan aturan berbeda.

### Batch aktif vs brief terkunci

Taskdir yang sudah sebagian dieksekusi memuat dua populasi brief, dan predikat di bawah tidak berlaku sama atas keduanya:

| Populasi | `status:` | Predikat **rencana** (S, B, F, L, N, D, K, E) | Predikat **cakupan** (C, G, H, I, J) |
|---|---|---|---|
| batch aktif | `READY` | ditagih penuh | ditagih penuh |
| terkunci | `DONE` · `BLOCKED` · `SUPERSEDED` | **dilewati** | ditagih penuh (kecuali `SUPERSEDED`: tidak dihitung — penggantinya yang memikul) |

Brief terkunci dilewati predikat rencana karena remediasinya mustahil dikerjakan tanpa memalsukan riwayat: `status:`-nya memang bukan `READY`, berkas beraksi `create` miliknya memang sudah ada di disk, dan anchornya menunjuk kode yang sudah bergeser oleh brief sesudahnya. Gerbang yang menagihnya menyisakan satu-satunya jalan keluar berupa mengabaikan keluaran skrip — dan gerbang yang rutin diabaikan berhenti menggerbangi apa pun.

Predikat cakupan tetap menilai seluruh brief yang tidak digantikan: `Covers:`, `Fulfills:`, dan `Produces` brief yang sudah `DONE` masih menopang rantai keterlacakan dan masih menjadi sumber `Consumes` brief penerusnya. Keduanya tidak gugur oleh eksekusi. Brief `SUPERSEDED` dikecualikan: klaimnya dipikul pengganti, dan Check C menolak brief `READY` yang masih mengonsumsinya.

Skrip melaporkan populasi terkunci sebagai baris `LOCKED` — informasi, bukan kegagalan. `--include-locked` menagih predikat rencana atas keduanya; ia alat **audit**, dan dilarang dipakai sebagai gerbang Fase 4.

1. **Check A — Source Coverage** *(main loop, bukan skrip)*: cocokkan setiap butir PRD, tiap temuan yang dipikul `SC-{n}` akar saat `finding_source` terisi, atau permintaan `LANGSUNG` terhadap seluruh brief. Seluruhnya wajib terpetakan ke `## Steps` atau `## Analysis trace`. Check ini semantik — ia menilai apakah maksud butir hulu benar-benar dikerjakan, bukan apakah nomornya disebut — sehingga ia satu-satunya yang tidak diserahkan ke skrip.
2. **Check B — Placeholder Sweep**: sisir seluruh `## Steps` dari 5 placeholder terlarang yang didaftar di `../templates/brief-template.md` bagian 2 butir 4.
3. **Check C — Cross-Brief Consistency**: periksa `Consumes` terhadap `Produces` brief pendahulunya. Selaraskan signature dan pastikan tidak ada dependensi melingkar.

   **Satu baris `Consumes` menyebut tepat satu `brief-NN`.** Baris yang menyebut dua sumber adalah kegagalan check dengan remediasi memecahnya jadi dua baris — bukan kegagalan signature. Pasangan simbol-ke-sumber pada baris multi-sumber tidak dapat dipetakan, sehingga pemeriksaan terpaksa menyandingkan simbol pertama baris itu dengan tiap brief yang disebut lalu melaporkan kegagalan hantu atas simbol yang memang milik brief yang lain. Rumah kanonik aturannya `../templates/brief-template.md` bagian 2 butir 8. Pencocokan signature memakai tiap penggal identifier, bukan hanya penggal terakhirnya: `Tipe.Field` sah dipenuhi `Produces` yang menyebut tipe induknya.
4. **Check D — Test Reality**: pastikan tiap berkas test di `## File scope` menunjuk berkas nyata (aksi `modify`) atau path baru yang ditulis brief ini (aksi `create`), bukan nama yang diandaikan. Letak dan pola penamaannya dibaca dari baris `test:` `.claude/profile/backenddev/code-conventions.md`; bila baris itu absen, dari baris `Test` `## Layer taxonomy` adapter stack. Bila keduanya absen, turunkan dari berkas test nyata yang ditemukan di repo lalu catat resepnya di `## Analysis trace`.
5. **Check E — Scope Containment**: pastikan `## File scope` tidak memuat berkas di luar parameter `file_scope` — slot `File Scope` laporan rute gerbang yang diteruskan pemanggil. `file_scope` kosong pada lane planning tidak pernah sampai ke sini — skrip prasyarat sudah `FAIL` di check 8. Pada jalur `RCA`, `file_scope` kosong diturunkan dari `## Out of Scope` `TASK.md` sebagai satu-satunya pembanding, dan penyimpangan itu dicatat satu baris di `## Analysis trace`.

   **`file_scope` kosong divonis `WARN`, bukan `PASS`.** Kedua pembanding tidak setara: `file_scope` menyebut apa yang **diizinkan**, `## Out of Scope` menyebut apa yang **dilarang** — sehingga berkas di luar batas yang kebetulan tidak tersebut di sana lolos tanpa terdeteksi. Check terkuat rantai ini pernah berjalan terdegradasi sepanjang satu sesi penuh sambil mencetak `PASS` enam kali berturut-turut, karena parameternya tidak pernah sampai ke skrip dan kata `PASS` tidak membedakan keduanya. Vonis `WARN` tidak menahan batch; ia membuat degradasinya terbaca, dan skrip mencetak banner `TERDEGRADASI` di puncak keluaran.

   Remediasi sesungguhnya bukan menerima `WARN`, melainkan meneruskan `file_scope` dari pemanggil — `analyst` pada lane planning, gerbang pada jalur `RCA`. Dilarang membaca laporan gerbang sendiri: pada lane planning `plan` dipanggil `backenddev:analyst`, bukan gerbang.
6. **Check F — Verification Sweep**: `Grep` tiap brief atas pola `— verifikasi:`, `## Verification`, dan perintah build/test. Kecocokan di seksi mana pun adalah cacat: hapus perintahnya, bukan dipindahkan. Brief lulus hanya bila nol kecocokan.
7. **Check G — Criteria Coverage**: **berlaku hanya pada rantai tanpa PRD.** `{taskdir}/PRD.md` ada → check ini `SKIP`, dan brief tidak menulis baris `Fulfills:` sama sekali: keterlacakan `SC-{n}` diangkut kolom `Akar` tabel `## Acceptance criteria` PRD, tergerbangi predikat G2 `analyst` lalu Check H di sini. Sumbu langsung `SC-{n}` → `Fulfills:` di atasnya memvonis ulang kesimpulan yang sama dari ujung yang berbeda tanpa menambah informasi. Check S menolak brief ber-`Fulfills:` pada rantai ber-PRD.

   Pada rantai tanpa PRD — `chain: BRIEF` dan jalur `RCA` — sumbu ini satu-satunya rute ke akar dan ditagih penuh: bila `{taskdir}/TASK.md` ada, kumpulkan seluruh nomor di baris `Fulfills:` tiap brief batch ini lalu sandingkan dengan `## Success Criteria` `TASK.md`. `SC-{n}` yang tak disebut satu pun baris `Fulfills:` adalah kegagalan check — petakan ke brief yang mengerjakannya atau tambah brief, dilarang diturunkan jadi catatan. Nomor `Fulfills:` yang tidak ada di `TASK.md` juga gagal: hapus rujukan hantunya. Brief tanpa baris `Fulfills:` gagal sekalipun seluruh SC tertutup brief lain. Brief yang menyentuh butir `## Out of Scope` akar juga gagal: buang langkahnya, atau ajukan amandemen akar ke pemanggilnya — `backenddev:analyst` pada lane planning, `backenddev:tech-lead` pada jalur `RCA` — dan tunggu keputusannya sebelum batch ditutup. Check ini mekanis atas nomor; dilarang menyalin prosa butir SC ke seksi brief mana pun — prosa itu memuat `— verifikasi:` yang ditolak Check F. Bila `TASK.md` tidak ada, tiap brief tetap menulis `Fulfills: — (akar absen)`.
8. **Check H — AC Coverage**: bila `{taskdir}/PRD.md` ada, kumpulkan seluruh nomor di baris `Covers:` tiap brief batch ini lalu sandingkan dengan `## Acceptance criteria` PRD. `AC-{n}` yang tak disebut satu pun baris `Covers:` adalah kegagalan check — petakan ke brief yang mengerjakannya atau tambah brief, dilarang diturunkan jadi catatan. Nomor `Covers:` yang tidak ada di PRD juga gagal: hapus rujukan hantunya. Brief tanpa baris `Covers:` gagal sekalipun seluruh AC tertutup brief lain. Bila `PRD.md` tidak ada (jalur `RCA` dan `LANGSUNG`), tiap brief tetap menulis `Covers: — (<alasan>)`.
9. **Check I — AC Test Landing**: kebalikan Check D. Bila `{taskdir}/PRD.md` ada, kumpulkan tiap `AC-{n}` yang kolom "Cara verifikasi"-nya bernilai `test otomatis`, lalu cari brief yang mengklaimnya di baris `Covers:`. Predikatnya: **minimal satu baris berkas test di antara brief pengklaim wajib menamai `AC-{n}` itu** — di kolom `Anchor` atau di kolom "Apa yang berubah". Nol baris yang menamainya adalah kegagalan check.

   Predikat lama hanya menuntut "ada berkas test di brief pengklaim", dan itu lolos secara massal: tiga brief yang masing-masing kebetulan menyentuh berkas test karena alasan lain — menyunting literal, menambah assert kosong, memasang guard — bertiga lolos mengklaim satu AC yang tidak satu pun di antaranya benar-benar menguji. Celahnya baru ketahuan saat brief kesembilan dipaksa punya AC. Menagih **penamaan** membuat pemikul assertion tertulis, bukan tersirat, dan menutup celah itu tanpa menuntut skrip memahami isi test.

   Remediasinya menandai baris test pemikulnya, bukan menambah berkas test baru ke tiap pengklaim. AC berawalan `QA manual:` dikecualikan dari penagihan berkas test, **tetapi bukan dari pendaratan**: langkah manualnya turun ke `## Risk & rollback` brief pengklaim sebagai kalimat operasional yang menyebut nomor `AC-{n}`-nya. Dilarang menaruhnya di `## Analysis trace` — seksi itu dinyatakan bukan pekerjaan eksekutor, sehingga satu-satunya bentuk verifikasi AC tersebut jadi tak terlihat di titik eksekusi. AC `QA manual:` yang tak mendarat di seksi mana pun adalah kegagalan check. **Penamaan berkas test milik check ini, bukan milik PRD**: nama diturunkan dari baris `test:` `.claude/profile/backenddev/code-conventions.md` atau baris `Test` `## Layer taxonomy` adapter, dan perbedaan nama tidak pernah menuntut amandemen PRD. Bila `PRD.md` tidak ada, lewati check ini.

10. **Check J — Migration Landing**: check ini berlaku pada **dua** pemicu, bukan hanya jalur PRD.

    - *Jalur PRD*: `{taskdir}/PRD.md` ada dan `## Migration requirements`-nya bukan "tidak perlu".
    - *Jalur tanpa PRD*: scan Fase 2 butir 5 (`slicing-and-scan.md`) menetapkan berkas migrasi baru, apa pun `entry_mode`-nya. Urutan deploy dan rollback plan tidak pernah divonis hulu di jalur ini, sehingga tanpa check ini keduanya jatuh ke orang yang menjalankan deploy — keputusan operasional yang seharusnya selesai di fase planning.

    Pada kedua pemicu, minimal satu brief batch wajib memuat `## Migration` berisi DDL beserta urutan deploy sebagai langkah bernomor, dan `## Risk & rollback` yang menyebut cara mengembalikan skema beserta tanda kegagalannya. Predikat lengkapnya di `../templates/brief-template.md` bagian 2 butir 10. Satu unsur hilang adalah kegagalan check — lengkapi briefnya, dilarang diturunkan jadi catatan. Nol berkas migrasi pada batch dan `## Migration requirements` bernilai "tidak perlu" atau absen: lewati check ini.

    **Skema dibentuk ORM.** Brief yang `## Migration`-nya memuat baris `Berkas migrasi: tidak ada — skema dibentuk ORM` dibebaskan dari kewajiban mendaftarkan berkas migrasi di `## File scope`, **hanya** bila `.claude/profile/backenddev/invariants.md` atau `commands.md` menyatakan skema dibentuk ORM saat startup (`ddl-auto`, `hbm2ddl`, `synchronize: true`, `AutoMigrate`). DDL setara, urutan deploy bernomor, dan rollback plan tetap ditagih. Token tanpa pernyataan profil gagal: tanpa guard itu token menjadi jalan pintas menghindari berkas migrasi di repo yang skemanya dikelola tool migrasi.

11. **Check K — Risk Derivation**: tiap brief batch memikul frontmatter `risk:` bernilai `BREAKING`, `MAJOR`, atau `MINOR` yang diturunkan dari tabel predikat `../templates/brief-template.md` bagian 2 butir 11 atas isi `## File scope` dan `## Steps` brief itu sendiri. Nilai kosong, nilai `-`, atau nilai yang tidak cocok dengan predikatnya adalah kegagalan check. Nilai yang **melampaui** `risk:` frontmatter `{taskdir}/TASK.md` juga gagal, dan remediasinya bukan menurunkan nilainya: hentikan batch, kembalikan klasifikasi ke gerbang. `TASK.md` absen → plafon diambil dari risk level rute gerbang; `risk:` bernilai `-` → plafon `MINOR`.

12. **Check S — Struktur & Frontmatter**: sepuluh seksi baku hadir **berurutan** menurut `../templates/brief-template.md` bagian 1, frontmatter lima field terisi, `status: READY`, `commit_message` berbentuk `<type>(<domain>): implement <unit>`, nama berkas berpola `brief-<NN>-<unit>.md`, nol seksi `## Open questions` maupun `## Verification`, baris `Covers:`/`Fulfills:` berdiri di dalam `## Objective` tanpa token tercampur, dan nol penanda `<!-- scaffold: ... -->` tersisa. Penanda yang masih ada berarti seksi itu belum diisi sama sekali. Kerangka ditulis `scripts/scaffold_brief.py`; kegagalan check ini diremediasi dengan mengisi seksinya, bukan dengan menyalin ulang contoh template.

13. **Check L — Langit-langit Slicing**: tiap brief memuat minimal satu langkah bernomor `## Steps` dan maksimal `5`, serta maksimal `4` file kode di `## File scope` (berkas test tidak dihitung) — langit-langit `slicing-and-scan.md` bagian 3A butir 3. Pelanggaran diremediasi dengan memecah brief jadi dua brief berurutan; penggabungan kembali hanya sah bila pemecahannya merusak kompilasi, dan alasannya dicatat di `## Analysis trace`.

14. **Check N — Resolusi Anchor**: tiap baris `modify` `## File scope` wajib membawa kolom `Anchor` terisi, dan simbolnya memikul **dua** predikat.

    - **Resolve.** Cocok dengan kolom `Simbol anchor` sebuah laporan `{taskdir}/.explore/*.md`, atau ditemukan di berkas yang disebut **pada baris berbentuk deklarasi**. Anchor yang tidak resolve adalah anchor karangan: eksekutor akan mencari titik sisip yang tidak pernah ada. Simbol yang ada di berkas itu tetapi hanya sebagai penyebutan — di komentar, di pemanggilan, di dalam literal — divonis `WARN`, bukan `FAIL`: bentuk deklarasi tiap stack tidak pernah tertangkap penuh satu regex, sehingga vonis kerasnya akan meleset sesekali. Ia tetap wajib terbaca, karena anchor semacam itu tetap mengirim eksekutor ke titik sisip yang salah.
    - **Dipakai `## Steps`.** Minimal satu langkah wajib menyebut token anchornya. Anchor yang resolve tetapi tak pernah disebut langkah mana pun berarti brief menamai satu titik sisip lalu mengerjakan titik lain — persis bentuk cacat yang membuat brief lolos menunjuk fungsi test nyata sebagai lokasi literal yang tidak ada di dalamnya. Ini separuh mekanis dari tuntutan `../templates/brief-template.md` bagian 2 butir 5; separuh sisanya — apakah **klaim isi** anchornya benar — tetap milik `brief-reviewer`.

    Remediasi keduanya memanen ulang laporan `.explore` unit itu lalu menyalin anchornya apa adanya, bukan menebak ulang. Baris `create` yang berkasnya sudah ada di disk juga gagal check ini — aksinya `modify`.

15. **Check P — Sapuan Anti-pattern**: baca `.claude/profile/backenddev/anti-patterns.md`, ambil tiap baris ber-resep `deteksi \`<pola> @ <cakupan>\``, lalu jalankan polanya atas `## Steps` (snippet ikut) tiap brief yang `## File scope`-nya menyentuh cakupan itu. Kecocokan adalah kegagalan check: batalkan langkahnya dan rancang ulang memakai pola pengganti yang tertulis di baris `anti-patterns.md` yang sama.

    Penyempitan ke cakupan bukan kelonggaran — ia yang membuat check ini presisi. Satu resep bercakupan handler tidak menuduh brief yang hanya menyentuh domain.

    Baris `anti-patterns.md` bersumber konfirmasi user tidak punya resep `deteksi` — polanya memang tak berjejak di kode — dan karena itu tidak dapat digerbangi di sini; ia tetap milik `brief-reviewer`. `.claude/profile/backenddev/anti-patterns.md` yang absen atau nol baris ber-`deteksi` membuat check ini `SKIP`.

    Check ini menutup jarak antara `SKILL.md` Fase 3 butir 6 ("Batalkan langkah yang menuntut pola terdaftar di `## Anti-patterns`") dan penegakannya. Tanpa check ini butir itu hanya niat: brief lolos menerbitkan pola yang persis terdaftar di baris kelima profil, dan yang menghentikannya baru `code-implementor` — sesudah satu putaran orkestrasi penuh terbayar.

## 5. Dispatch Self-Review Kolektif (Fase 5)

Seluruh check bagian 4 lulus lebih dulu; dispatch dilarang berangkat sebelum titik itu. Reviewer berangkat di atas brief yang predikat mekanisnya **sudah dijamin skrip**, sehingga fokusnya menyempit ke yang memang menuntut penilaian: keselarasan aturan bisnis, pendaratan kontrak PRD, dan kualitas langkah.

- **Baca state ronde lebih dulu.** Jalankan `scripts/validate_briefs.py --taskdir <taskdir> --review-state`. Keluarannya menyebut generasi batch aktif, ronde terpakai di generasi itu, sisa plafon, plafon keras taskdir, dan brief yang berubah sejak ronde terakhir.

  **Plafon 2 ronde per generasi batch, 4 ronde per taskdir.** Satu *generasi* adalah himpunan berkas brief yang ada di taskdir; ia berganti hanya saat brief **ditambahkan** — re-entry `analyst`, berkas yatim `architect`, atau brief perbaikan. Menyunting isi brief tidak pernah membuka generasi baru, sehingga plafon tidak dapat diakali dengan mengedit.

  Plafon per-taskdir yang lama membuat brief yang lahir sesudah ronde kedua mustahil direview: skrip membalas "plafon habis" atas berkas yang belum pernah dilihat reviewer mana pun, dan brief itu terpaksa dikunci lewat jalur "self-review tidak tuntas". Plafon keras taskdir tetap ada supaya penambahan brief berulang tidak menjadi loop tanpa batas.

  Sisa nol pada generasi aktif **dan** taskdir belum menyentuh plafon kerasnya → tambahan brief berikutnya akan membuka generasi baru; sisa nol karena plafon keras taskdir → serahkan brief apa adanya dengan status self-review tidak tuntas.

- **Buka ronde tepat sebelum dispatch berangkat**: `scripts/validate_briefs.py --taskdir <taskdir> --open-round`. Perintah ini memateraikan snapshot isi tiap brief **pada saat dispatch**, dan menolak berangkat bila plafon sudah habis. Snapshot itulah pembanding daftar `{brief_berubah}` ronde berikutnya.
- Muat template prompt dari `../dispatcher/reviewer.md`, hidrasi slot `taskdir`, `chain`, `ronde`, dan dokumen acuan, lalu panggil subagent `brief-reviewer` secara langsung. Tangkap balikan `## Brief Review` berstatus `Approved` atau `Issues Found`, dan teruskan bloknya apa adanya ke laporan penutup — pemanggil memakainya sebagai predikat serah terima, bukan sebagai catatan.
- **Ronde 1** dikirim sekaligus untuk seluruh `brief-*.md`; dilarang memecahnya jadi satu dispatch per berkas.
- **Ronde 2 berangkat hanya bila ronde 1 meninggalkan `BLOCKER [SEMANTIK]`.** Reviewer melabeli tiap `BLOCKER` `MEKANIS` atau `SEMANTIK`. Seluruh `BLOCKER` ronde 1 berlabel `MEKANIS` → perbaiki, jalankan ulang `validate_briefs.py` sampai `PASS`, lalu **lanjut ke commit tanpa ronde 2**: skrip memvonis hal yang sama dengan biaya nol, sementara satu ronde penuh membaca ulang `TASK.md`, `PRD.md`, dan tiap brief untuk menyimpulkan apa yang sudah dijamin. Catat pelewatan itu di laporan penutup (`Self-Review: Approved (ronde 1/2 · BLOCKER mekanis <n> tertutup skrip)`).
- **Ronde 2** menyempit ke brief yang berubah. Hidrasi `{brief_berubah}` dari keluaran `--review-state` dan `{previous_report}` dari laporan ronde 1. Brief yang tidak tersentuh sejak ronde 1 byte-identik dengan yang sudah dinilai, dan menilainya ulang tidak menambah satu pun informasi — sementara `validate_briefs.py` tetap berjalan penuh atas seluruh batch sebagai jaring regresi.
- **Hanya `BLOCKER` yang menahan.** Reviewer menandai tiap temuan `BLOCKER` atau `ADVISORY`. Nol `BLOCKER` berarti `Approved`, dan `ADVISORY`-nya ikut ke laporan penutup tanpa menahan commit. Dilarang membuka ronde baru atas `ADVISORY`: satu nit redaksional di satu brief tidak pernah sepadan dengan satu ronde penuh.
- Perbaiki temuan `BLOCKER` pada berkas brief terkait dan pertahankan `status: READY` tanpa commit selama masih ada yang terbuka.
- **Materaikan tiap ronde yang selesai** dengan `scripts/validate_briefs.py --taskdir <taskdir> --record-round "<verdict>"`. Ronde yang tidak dimateraikan tidak terhitung, dan plafonnya bocor pada invokasi berikutnya.

  Urutannya tidak lagi menentukan kebenaran daftar `{brief_berubah}`: snapshot pembandingnya diambil `--open-round`, bukan di sini. Materai yang mendarat sesudah perbaikan `BLOCKER` karena itu tetap menghasilkan daftar yang benar. Ronde yang dimateraikan tanpa pernah dibuka tetap diterima, tetapi snapshot-nya terpaksa diambil belakangan dan skrip menandainya `[snapshot menyusul]` — pada ronde itu daftar brief berubah berikutnya memang tidak dapat dipercaya.
- Dispatch gagal atau balikan formatnya rusak → ulangi maks sekali **tanpa** memateraikannya sebagai ronde; tetap gagal → serahkan brief tanpa commit dan tandai self-review tidak tuntas. Dilarang mengarang verdict `Approved`.

## 6. Protokol Commit Agregat (Fase 5)

Brief lahir `status: READY` tanpa gerbang approval, berbeda dari `BRD.md` dan `PRD.md`. Commit-nya karena itu dieksekusi `plan` sendiri tepat sesudah self-review kolektif lolos, bukan ditunda ke `tech-lead`. Urutan wajib dan tidak boleh dibalik:

```
matriks alokasi terkunci → tiap brief lolos gerbang per-brief Fase 3
  → Fase 4  validate_briefs.py PASS + Check A tertutup
  → Fase 5  dispatch brief-reviewer → nol temuan BLOCKER (`Approved`)
  → Fase 5  git commit agregat
  → handoff ke backenddev:analyst        (lane planning)
  → handoff ke backenddev:tech-lead      (jalur RCA yang dirutekan gerbang)
```

1. **Satu commit untuk seluruh batch**, sekalipun batch memuat brief hasil perbaikan cacat — bukan satu commit tambahan per perbaikan.
2. **Staging eksplisit per path**, tiap berkas brief yang baru terbit **dan** tiap brief lama yang baru ditandai `SUPERSEDED` (baris `Stage bersama di commit agregat` keluaran `scaffold_brief.py --nn`) disebut satu per satu:
   ```
   git add {taskdir}/brief-02-<unit>.md {taskdir}/brief-03-<unit>.md {taskdir}/brief-04-<unit>.md {taskdir}/brief-05-<unit>.md
   git rm -q {taskdir}/HALT.md        # hanya bila keluaran --nn menyebut HALT.md dihapus (baris `repairs`)
   git commit -m "docs(plan): add <N> briefs for <slug>" -m "Brief-Review-Rounds: gen=<generasi> rounds=<n> total=<n>"
   ```
   Trailer `Brief-Review-Rounds:` disalin apa adanya dari baris `trailer commit agregat` keluaran `validate_briefs.py --review-state`. State ronde di laci `.explore/` tidak ter-commit; trailer inilah yang membuat plafon ronde bertahan di clone baru.
   `<N>` diisi jumlah brief yang benar-benar terbit pada batch ini (brief `SUPERSEDED` tidak dihitung); `<slug>` diambil dari nama direktori taskdir tanpa awalan timestamp.
3. **Eksekusi seketika saat `Approved`**, tanpa menunggu persetujuan user, gerbang, maupun main loop — self-review satu-satunya prasyarat commit. Sebaliknya, tahan commit tanpa pengecualian bila status belum `Approved`.
4. **Dilarang staging wildcard.** `git add .` dan `git add -A` berisiko menarik berkas scratch, log, atau pekerjaan user yang belum di-commit.
5. **Batas kewenangan.** Commit ini satu-satunya mutasi git milik `plan` dan hanya memuat `brief-*.md` pada taskdir aktif — brief baru, brief yang baru ditandai `SUPERSEDED`, dan penghapusan `HALT.md` yang dicabut baris `repairs`; berkas lain milik skill penulisnya. `git push`, `git merge`, `git rebase`, `git branch`, dan `git checkout` terlarang tanpa kecuali.

### Kegagalan Commit & Mitigasi Mandiri

| Kondisi | Predikat terdeteksi | Tindakan |
|---|---|---|
| Working tree memuat perubahan asing | `git status --porcelain` memuat path di luar `{taskdir}` | Tetap stage hanya path brief; jangan merapikan berkas milik user |
| Signing gpg memblokir | `git commit` gagal dengan galat gpg | Jangan mengulang dengan `--no-gpg-sign`; laporkan brief tertulis namun belum ter-commit |
| Bukan repositori git | `git rev-parse --is-inside-work-tree` bukan `true` | Lewati commit tanpa menggagalkan perencanaan; catat di laporan penutup |
| Indeks terkunci atau commit gagal sebagian | `git commit` mengembalikan kode keluar bukan nol | Jangan menyatakan brief ter-commit; sertakan pesan galat mentah pada laporan |

Pada seluruh kondisi di atas berkas brief tetap berstatus `READY` dan tetap diserahkan ke gerbang — kegagalan commit tidak pernah menurunkan status brief, membatalkan hasil perencanaan, maupun memicu penulisan ulang batch.

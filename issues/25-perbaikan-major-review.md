# Langkah 25 — Perbaikan temuan major review lintas plugin (R1–R12)

Sumber: review kerapihan, flow, dan konsistensi ketujuh plugin (2026-10-14), lalu permintaan user "perbaiki semua
major secara bertahap". Review menemukan 12 temuan major dan sekitar 55 temuan minor. Langkah ini hanya
menutup yang major; temuan minor tidak dikerjakan di sini.

Basis kode: commit `b2701bd` (analyst 0.16.0, backend 0.15.0, frontend 0.14.0, quickdev 0.8.0, nataflow 0.1.0,
product 0.1.0, fullstack 0.3.0).

**Status (2026-10-14):** SELESAI. R1–R12 mendarat sebagai satu commit per temuan, masing-masing dengan test
regresi `@pytest.mark.regression("25 R<n>")` yang gagal tanpa perbaikannya. Rilis: backend 0.16.0, frontend
0.15.0, quickdev 0.9.0, product 0.1.1, nataflow 0.1.1. analyst dan fullstack tidak berubah.

## Tujuan

1. Tidak ada jalur rantai yang macet atau berputar karena prosa dan skrip gerbang tidak sepakat.
2. Tidak ada prosa yang menyuruh model meng-commit atau memulihkan dari git dokumen taskdir, yang sejak Langkah 24
   diabaikan git.
3. Ketergantungan ke server `nataflow-api` terdokumentasi bersama dampaknya bila server tidak ada.

## Temuan dan perbaikan

| ID | Plugin | Temuan | Perbaikan | Test |
|---|---|---|---|---|
| R1 | backend | `backend:profile` GENERATE menulis `.backenddev/` ke `.gitignore`, tetapi check 3 `--re-entry` tech-lead menolak `.gitignore` sebagai berkas kotor di luar zona artefak, sehingga re-entry macet di hampir setiap repo baru | `.gitignore` akar lolos bila selisihnya terhadap HEAD semata baris `.backenddev/`; prosa architect dan gate-lifecycle diselaraskan | `tests/backend/test_tech_lead_preconditions.py` |
| R2 | backend, frontend | `docs_git.py` menebak plugin dari nama direktori, yang di cache terpasang berupa versi (`…/frontend/0.14.0/`); migrasi frontend tanpa `--plugin` gagal "plugin tidak dikenal" | nama dibaca dari `.claude-plugin/plugin.json`; prosa lead frontend mengirim `--plugin frontend` | `tests/test_24_docs_git.py` |
| R3 | frontend | `chain.py escalate --reason ""` menulis kejadian Riwayat tak terbaca, sehingga taskdir `RUSAK` permanen | guard di `escalate` dan di `record` untuk semua teks bebas | `tests/frontend/test_12_ledger.py` |
| R4 | frontend | template `TASK.md` bagian 1 memuat placeholder `base_commit` dan `## Riwayat Rantai`; `chain.py init` memvonis Riwayat rusak | keduanya keluar dari template; `init` membuang seksi Riwayat yang hanya berisi placeholder | `tests/frontend/test_24_riwayat.py` |
| R5 | backend, frontend, nataflow | skill nataflow mengklaim bebas gerbang engineer, tetapi daftar pengecualian `gate_text.py` tertutup pada tiga plugin | `/nataflow:*` beserta susulannya masuk pengecualian keempat | `tests/hooks/test_gate_text.py` |
| R6 | backend, frontend | brief `DONE` tanpa commit unit: backend tanpa penulis sah `DONE → READY`; frontend salah rute ke `TERHENTI (DAG)`/`PENUTUP` dan memantul architect ↔ lead | backend: `doc_seal.py buka-done` (gerbang); frontend: fase `TERPUTUS` di `taskdir_state` dan architect, matriks bukti disk tanpa dispatch; `report-NN.md` yang hilang sesudah commit mendarat hanya `WARN` | `tests/backend/test_24_doc_seal.py`, `tests/frontend/test_12_orchestration.py` |
| R7 | backend | rute pemakaian ulang taskdir memakai keberadaan `HALT.md`, padahal HALT yang dicabut kini tetap di disk sebagai `status: DICABUT` | rute hanya untuk HALT aktif | `tests/backend/test_l24_halt.py` |
| R8 | backend, frontend | prosa menyuruh meng-commit `TASK.md`/`REVIEW.md` atau memulihkan dokumen taskdir dari riwayat git | instruksi dihapus atau diarahkan ke cermin nataflow dan `counters-log.json` | `tests/test_24_docs_git.py` |
| R9 | quickdev | baseline profil yang diukur di tree kotor tetap dipakai sebagai pembanding bila SHA-nya sama | `plan_lock.py start` mode `awal` mencetak `PEMBANDING:`; profil hanya bila `tree bersih: ya` | `tests/quickdev/test_13_state.py` |
| R10 | product | `S<n>` dijanjikan tetap, tetapi validator menolak celah di Termasuk | butir yang dibatalkan pindah ke Tidak Termasuk beserta ID-nya; kontinuitas dihitung atas gabungannya | `tests/product/test_validate_doc.py` |
| R11 | backend | `architect` membaca `Umpan balik profil:` dari `report-NN.md`, tetapi kontrak implementor tidak pernah menulisnya | kontrak agent menulis baris itu; `lifecycle-recovery.md` merujuk seksi yang sama | `tests/backend/test_25_report_contract.py` |
| R12 | lintas | ketergantungan ke server privat `nataflow-api` tidak terdokumentasi | bagian "Server nataflow" di README root, README nataflow, dan deskripsi plugin | `tests/test_15_nataflow_sync.py` |

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | Satu commit per temuan, rilis dalam satu `chore(release)` terpisah. | Mengikuti konvensi repo; tiap perbaikan dapat dibaca dan di-revert sendiri. |
| K2 | R1 tidak membebaskan `.gitignore` utuh, hanya selisih baris `.backenddev/`. | Suntingan user di berkas yang sama tetap milik user dan tidak boleh ikut commit gerbang. |
| K3 | R6 backend: `DONE → READY` milik gerbang (`doc_seal.py buka-done`), bukan architect. | Gerbang yang mencabut HALT sesudah reset; architect tetap hanya `READY → DONE`. Skrip menolak bila commit unit terbukti, tree kotor, atau HALT aktif menahan brief itu. |
| K4 | R6 frontend: fase `TERPUTUS` memberi `WARN`, bukan `FAIL`, pada check 4 dan tree kotor check 8. | `FAIL` membuat architect kembali ke lead dan tak ada pihak yang menjalankan matriks bukti disk. Kotoran yang asal-usulnya tak diketahui tidak dipulihkan otomatis. Rantai tuntas yang di-squash-merge (commit unit hilang, `head:` review bukan leluhur `HEAD`) tetap `TUNTAS`, sejalan dengan `taskdir_state.py` (12 J44). |
| K5 | R9 dimekanisasi lewat baris `PEMBANDING:`, bukan prosa saja. | Keputusan pembanding kini dihitung skrip dari profil, sejalan dengan prinsip "skrip adalah kontrak". |
| K6 | R12 tidak menulis cara autentikasi server. | Skema autentikasinya milik server dan tidak tercatat di repo ini; dokumentasi hanya menyebut sumber aksesnya. |

## Batas yang dinyatakan apa adanya

- R5 tetap pengecualian berbasis prosa: gerbang engineer adalah teks pengingat, bukan pagar mekanis.
- R7 dan R11 adalah perbaikan prosa yang dikunci test teks; tidak ada skrip yang merutekan taskdir backend.
- Architect frontend memperlakukan `report-NN.md` yang hilang sesudah commit unit mendarat sebagai `WARN`: commit itu
  tetap bukti `DONE`, dan laporannya hanya dapat dipulihkan dari cermin nataflow, tidak direkonstruksi.

## Di luar cakupan

Temuan minor review, seperti drift dokumentasi, kode mati, duplikasi konstanta, konvensi CLI dan penamaan,
CHANGELOG, job CI Windows, dan kebersihan `issues/`, tetap terbuka untuk langkah berikutnya.

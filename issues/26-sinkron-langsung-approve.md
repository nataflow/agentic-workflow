# Langkah 26 — Sinkron nataflow langsung di tiap approve (backend, frontend)

Sumber: permintaan user (2026-10-14): "di tiap plugin, saat dokumen di-approve oleh user/engineer, langsung sync semua
file di workdir ke nataflow" — backend: task → approve → sync, BRD → approve → sync, PRD → approve → sync, brief →
approve → sync, review & report → sync; berlaku juga untuk frontend, supaya nataflow sinkron selama plugin berjalan.

Basis kode: commit `4890a49` (backend 0.16.0, frontend 0.15.0).

**Status (2026-10-14):** SELESAI. S1–S7 terpasang; test `tests/test_26_sinkron_approve.py` (18, sebelas di antaranya
gagal tanpa perubahan ini). Rilis: backend 0.17.0, frontend 0.16.0. analyst dan quickdev sudah menyinkron di titik
approve-nya (`spec` sesudah `ticket.py approve`, `plan` sesudah `PLAN_APPROVED`) dan tidak berubah; product belum
punya sinkron nataflow sama sekali (README product) dan di luar langkah ini.

## Keadaan sebelum

Prosedur sinkron (`sync_payload.py` + `nataflow-sync.md`) sudah mendorong seluruh berkas taskdir yang sah dengan
diff manifest, jadi "semua file di workdir" sudah terpenuhi per panggilan. Yang kurang adalah **kapan** ia dipanggil:

| Dokumen | Backend sebelum | Frontend sebelum |
|---|---|---|
| `TASK.md` | `analyst` Fase 2 saja; lane `DEFECT_RCA` dan backfill `EXEC_BRIEF` menunggu `tech-lead` Fase 5 | `task` sesudah `chain.py root` ✓ |
| BRD / PRD (FLOW / UI / CONTRACT) | `analyst` Fase 4 sesudah `doc_seal.py approve` ✓ | tiap gate sesudah `chain.py approve` ✓ |
| Brief | menunggu sapuan `tech-lead` Fase 5 sesudah `analyst` kembali | `plan` sesudah `chain.py approve --row BRIEF` ✓ |
| `REVIEW.md` | menunggu `tech-lead` Fase 5 sesudah seluruh `architect` (termasuk `report`) kembali | `architect` sekali per putaran di akhir — sesudah `REPORT.md`, termasuk sesudah pertanyaan umpan balik profil ke user |
| `REPORT.md` | menunggu `tech-lead` Fase 5 | `report` Phase 4 ✓, lalu disinkron ulang `architect` di akhir |

## Perubahan

| ID | Plugin | Bagian | Perubahan |
|---|---|---|---|
| S1 | backend | `task/SKILL.md` Fase 5 butir 5, Output | Akar terkunci → sinkron di `task` sendiri, sehingga ketiga lane berakar tercermin seketika; laporan `### TASK ROOT LOCKED` membawa segmen `Nataflow`. `analyst` Fase 2 butir 4 hanya membawa segmen itu, tanpa sinkron kedua |
| S2 | backend | `analyst/SKILL.md` Fase 6 butir 0, Output | Sesudah `doc_seal.py tick --hop BRIEF` → sinkron. Brief backend tidak punya approval user (guardrail APPROVAL HANYA BRD & PRD); kunci batch `lock-briefs` + centang ledger adalah titik approval-nya. Baris `Nataflow` vonis `READY_FOR_IMPLEMENTATION` kini selalu ada |
| S3 | backend | `architect/SKILL.md` Fase 4 butir 2, Fase 5 butir 3, Output | `REVIEW.md` terbit → sinkron seketika, apa pun severity-nya. Putaran yang berhenti sebelum review atau mendapati `REPORT.md` sudah ada menyinkron sekali sebelum laporan penutup. Laporan berslot `Nataflow` |
| S4 | backend | `report/SKILL.md` Fase 4 butir 4, Output | `REPORT.md` tertulis → sinkron di `report` sendiri (workdir `done`) |
| S5 | backend | `tech-lead/references/gate-lifecycle.md` bagian 6 butir 2a, `nataflow-sync.md` | Fase 5 tetap menyapu (`plan` jalur `RCA`, `debug`, dokumen repo, `analyst` selain `READY`), tetapi tidak menyinkron ulang `architect` dan `analyst` bervonis `READY_FOR_IMPLEMENTATION`: segmen laporannya disalin. Tabel titik panggil ditulis ulang per dokumen |
| S6 | frontend | `architect/SKILL.md` Phase 4 butir 4, Phase 5 butir 4 | `REVIEW.md` lolos `validate_review.py` → sinkron seketika, apa pun verdict-nya (sebelumnya menunggu akhir putaran) |
| S7 | frontend | `architect/SKILL.md` Output, `lead/references/nataflow-sync.md` | "Sekali per putaran" diganti: penutup hanya menyinkron putaran yang tidak melewati titik review maupun laporan (rantai berhenti sebelum review, `REPORT.md` sudah terbit), sehingga `REPORT.md` tidak lagi disinkron dua kali |

Dokumen ikut: `README.md` backend/frontend (seksi Sinkron nataflow), `flow/backend.md`, `flow/frontend.md`.

## Keputusan

| ID | Keputusan | Alasan |
|---|---|---|
| K1 | Sinkron menempel ke skill pemilik materai, bukan ke gerbang | Gerbang hanya terlewati saat skill hilir pulang; titik tunggal di akhir membuat nataflow tertinggal selama rantai berjalan, padahal disk adalah satu-satunya salinan lain |
| K2 | Sinkron `TASK.md` dipindah dari `analyst` ke `task` | Lane `DEFECT_RCA` dan backfill `EXEC_BRIEF` memanggil `task` dari gerbang tanpa `analyst`; satu titik menutup ketiganya tanpa sinkron ganda |
| K3 | Tidak menambah gerbang approval user untuk brief backend | Permintaannya soal sinkron, bukan alur approval; menahan brief menunggu user bertentangan dengan guardrail `analyst` dan `plan`. Kunci batch sudah materai yang setara |
| K4 | Sapuan `tech-lead` Fase 5 dipertahankan, dengan pengecualian pengirim yang sudah tersinkron | Sapuan tetap jaring pengaman untuk pengirim tanpa titik sinkron sendiri; pengecualian hanya untuk pengirim yang sinkronnya terbukti sesudah mutasi disk terakhir, sehingga tidak ada dorongan ganda |
| K5 | Tidak ada perubahan skrip | `sync_payload.py` sudah memilih berkas, membaca disk, dan men-diff manifest; MCP hanya dapat dipanggil model, jadi yang berubah adalah titik panggil di prosa, dikunci test teks |
| K6 | Sinkron per unit `DONE` di `architect` tidak ditambah | Tidak diminta, dan mengalikan panggilan MCP per brief; status unit ikut tercermin di titik review atau penutup |

## Titik gagal

Tidak berubah: `.claude/nataflow.json` absen → `dilewati`; config rusak, server mati, atau tool galat →
`GAGAL: <sebab>` di slot/segmen Nataflow, rantai tetap lanjut, ulang lewat rute "sinkron ulang taskdir".

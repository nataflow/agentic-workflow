# Langkah 3 — Keamanan & Verifikasi Penutup (rincian L3.1–L3.6)

> Sumber: `ISSUES.md` baris 468–582. Nomor baris di berkas ini diverifikasi ulang terhadap commit `34684ee` pada 2026-09-24. Path relatif terhadap root repo kecuali disebut lain. Skrip kerangka (`run_verification.py`, `guard_bash.py`, `verify_scope.py`) sudah dijalankan di scratchpad sesi ini; salinannya sementara di `/tmp/claude-1000/-home-fakhrulnugroho-work-natakode-nataflow-agentic-workflow/d3694b5e-a45f-49bf-8ba3-1a983c306ba0/scratchpad/detail-03/` (akan hilang, salin bila perlu).

## Tujuan langkah

Menutup jalur tempat plugin bisa merusak data atau kerja user — migrasi DB saat profiling, build PHP yang menghapus tool dev, Bash implementor tanpa pagar, test/build quickdev tanpa izin, commit laporan di branch yang salah — dan menjadikan vonis verifikasi penutup berbasis exit code yang dicatat mesin, bukan tebakan dari 40 baris terakhir log.

## Urutan pengerjaan

1. **L3.2** — satu baris per adapter PHP; kemenangan cepat, sekaligus memberi fixture PHP untuk L3.3.
2. **L3.1** — kontrak `migration-status`/`migration-apply` dan pola izin `AskUserQuestion` (dipakai ulang L3.5).
3. **L3.5** — pola izin yang sama untuk quickdev.
4. **L3.3** — `run_verification.py` + baseline mesin.
5. **L3.4** — putuskan Opsi A/B per plugin dulu (Log Keputusan `ISSUES.md`), lalu kerjakan.
6. **L3.6** — kerjakan dalam satu suntingan dengan L2.1 (baris yang sama di `code-reviewer.md` Fase 4).

## Dependensi dengan langkah lain

| Item | Bergantung pada | Membantu / memblokir |
|---|---|---|
| L3.1 | — | pola izin dipakai L3.5 |
| L3.2 | — | fixture PHP untuk test L3.3 |
| L3.3 | L6.1 (struktur `tests/`, lunak) | membantu L2.4 (vonis & baseline di disk, tidak diukur ulang tiap sesi) dan L4.2 (angka "galat baru" dari mesin, bukan diketik) |
| L3.4 | keputusan user; L2.6 (apakah `finding_source` masuk daftar path lease); L1.2/L1.3 (sama-sama menyunting `hooks/hooks.json`) | L2.9 tetap terpisah (cek simbol hunk header) |
| L3.5 | L3.1 (teks pola izin) | — |
| L3.6 | L2.1 (baris sama di `code-reviewer.md:80`) | — |

## Estimasi

| Item | Estimasi |
|---|---|
| L3.1 | 4–5 jam |
| L3.2 | 1 jam |
| L3.3 | 1,5 hari |
| L3.4 | Opsi A (hook): 2 hari · Opsi B (cabut Bash): frontenddev 2–3 jam, backenddev 1 hari |
| L3.5 | 2 jam |
| L3.6 | 2–3 jam |
| **Total** | **±4,5–5 hari kerja** (rekomendasi campuran: frontenddev Opsi B, backenddev Opsi A) |

## Berkas yang disentuh

| Berkas | Item |
|---|---|
| `src/plugins/backenddev/skills/profile/stacks/{go,bun,java-spring,node,php,php-codeigniter,rust}.md` | L3.1 (baris migrasi), L3.2 (php, php-codeigniter: baris build) |
| `src/plugins/backenddev/skills/profile/stacks/_CONTRACT.md` | L3.1 |
| `src/plugins/backenddev/skills/profile/SKILL.md`, `references/scan-guide.md`, `templates/profile-template.md` | L3.1 |
| `src/plugins/{backenddev,frontenddev}/skills/_common/run_verification.py` (baru) | L3.3 |
| `src/plugins/backenddev/skills/architect/SKILL.md` | L3.3, L3.4 |
| `src/plugins/frontenddev/skills/architect/SKILL.md`, `references/execution-protocol.md` | L3.3, L3.4 |
| `src/plugins/{backenddev,frontenddev}/hooks/hooks.json`, `hooks/guard_bash.py` (baru) | L3.4 Opsi A |
| `src/plugins/{backenddev,frontenddev}/skills/_common/verify_scope.py` (baru) | L3.4 |
| `src/plugins/backenddev/agents/code-implementor.md`, `src/plugins/frontenddev/agents/code-implementor.md` | L3.4 |
| `src/plugins/backenddev/skills/architect/dispatcher/implementor.md`, `references/lifecycle-recovery.md` | L3.4 Opsi B (backenddev) |
| `src/plugins/backenddev/agents/code-reviewer.md`, `skills/architect/dispatcher/reviewer.md`, `skills/architect/scripts/check_preconditions.py` | L3.6 |
| `src/plugins/quickdev/skills/profile/SKILL.md`, `references/backend-profile-template.md` | L3.5 |
| `src/plugins/{backenddev,frontenddev}/tests/test_*.py` (baru) | semua item berskrip |

## Keputusan desain yang butuh user

1. **L3.4** — Opsi A (hook `PreToolUse` + lease) atau Opsi B (cabut Bash) per plugin. Rekomendasi: frontenddev B (hampir gratis, matriks architect sudah memulihkan), backenddev A (tidak mengubah doktrin "implementor commit sendiri").
2. **L3.3** — baseline `test` penuh diambil di Fase/Phase 0 (akurat, mahal di suite lama) atau diturunkan dari status baseline `commands.md` profil (murah, basi).
3. **L3.3/L3.4** — skrip ditaruh di `skills/_common/` tiap plugin (dua salinan identik + test paritas) karena plugin dipasang terpisah dan tidak bisa berbagi berkas.
4. **L3.1** — `migration-status` dijalankan sesudah izin, atau tidak pernah dijalankan (cukup dicatat).
5. **L3.2** — `composer install --optimize-autoloader` (default usulan) atau `composer dump-autoload -o` (tanpa jaringan, tidak menyentuh `vendor/`).

## Definisi selesai langkah ini

- Keenam checkbox tercentang, masing-masing memenuhi **Selesai bila**-nya.
- Tidak ada perintah apply migrasi di jalur eksekusi skill mana pun; test lint adapter (L3.1/L3.2) hijau.
- Tidak ada lagi `2>&1 | tail -40` di instruksi verifikasi kedua architect; vonis penutup dibaca dari `.explore/closing-verification.md` hasil skrip.
- `pytest` hijau untuk `run_verification.py`, `verify_scope.py`, dan `guard_bash.py` (bila Opsi A), termasuk test paritas salinan antar-plugin.
- Baris L3.4 di Log Keputusan `ISSUES.md` terisi.

---

## L3.1 [Tinggi] Profiling backenddev bisa menerapkan migrasi database ✔ diverifikasi ulang

- [ ] Selesai

**Plugin:** backenddev (cek silang frontenddev, quickdev) · **Estimasi:** 4–5 jam · **Bergantung pada:** — · **Memblokir:** L3.5 (memakai pola izin yang sama)

### Konteks

Fase 4 `backenddev:profile` wajib mengeksekusi enam perintah `commands.md`, termasuk `migration`. Nilai `migration` di ketujuh adapter adalah perintah **apply**. "Read-only mutlak" di Iron Law hanya mengikat kode sumber; tidak ada satu kalimat pun yang melarang menyentuh DB. Template profil sendiri tidak memberi slot status untuk baris migrasi — tanda penulisnya tidak bermaksud mengeksekusinya — tetapi Fase 4 tetap menyuruh.

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/profile/SKILL.md:12-13`
```
- Setiap perintah di `commands.md` wajib dieksekusi minimal sekali sebelum ditulis ke profil.
- Profiling read-only mutlak: dilarang mengubah, membuat, atau memperbaiki kode di source root.
```
`src/plugins/backenddev/skills/profile/SKILL.md:79` (Fase 4 butir 1)
```
1. Eksekusi berurutan `build`, `typecheck`, `lint`, `test`, `test-single`, `migration`. Tulis `tidak berlaku` ...
```
`src/plugins/backenddev/skills/profile/references/scan-guide.md:104`
```
Enam perintah dieksekusi: `build`, `typecheck`, `lint`, `test`, `test-single`, `migration`. ...
```
`src/plugins/backenddev/skills/profile/stacks/_CONTRACT.md:64-67` dan `:123` (gerbang kelayakan butir 3)
```
Enam baris perintah: `build`, `test`, `test-single`, `lint`, `typecheck`, `migration`. Tulis
`tidak berlaku` bila stack tidak punya padanannya — dilarang mengarang perintah. `profile`
mengeksekusi tiap perintah minimal sekali sebelum menuliskannya ke profil; `architect` memakainya di
gerbang verifikasi penutup taskdir.
...
3. Seluruh perintah di `## Commands` sudah dieksekusi minimal sekali di repo nyata stack itu.
```
`src/plugins/backenddev/skills/profile/templates/profile-template.md:152` dan `:259`
```
migration: <command> · folder <path> · pola <format nama berkas>
migration: migrate -path db/migrations -database $DATABASE_URL up · folder db/migrations · pola {n}_{deskripsi}.up.sql
```
Baris `migration` ketujuh adapter, kutip persis:
```
stacks/go.md:66              | migration | sesuai tool: `migrate -path <dir> -database $DATABASE_URL up`, atau `goose -dir <dir> up` |
stacks/bun.md:52             | migration | `bunx drizzle-kit migrate`, `bunx prisma migrate deploy`, atau skrip `bun run` repo |
stacks/java-spring.md:52     | migration | Flyway `./mvnw flyway:migrate`; Liquibase `./mvnw liquibase:update` | tugas Gradle padanannya |
stacks/node.md:53            | migration | `npx prisma migrate deploy`, `npx typeorm migration:run`, atau `npx drizzle-kit migrate` |
stacks/php.md:56             | migration | `php artisan migrate` | `php bin/console doctrine:migrations:migrate` |
stacks/php-codeigniter.md:53 | migration | `php spark migrate`; status per berkas `php spark migrate:status` |
stacks/rust.md:67            | migration | `sqlx migrate run`, `diesel migration run`, atau `refinery` sesuai crate yang dipakai |
```

### Reproduksi

Statis — tidak ada migrasi atau perintah DB yang dijalankan.
```bash
#!/usr/bin/env bash
# Tampilkan perintah yang akan dieksekusi backenddev:profile Fase 4.
cd "$(git rev-parse --show-toplevel)"
grep -n '^| migration |' src/plugins/backenddev/skills/profile/stacks/*.md
grep -n 'test-single`, `migration`' src/plugins/backenddev/skills/profile/SKILL.md \
  src/plugins/backenddev/skills/profile/references/scan-guide.md
```
Output (dikumpulkan lewat pencarian `mdcp` atas berkas yang sama karena aturan baca `.md` sesi ini; baris dan nomornya identik): tujuh baris adapter persis seperti blok kutipan di atas, ditambah `SKILL.md:79` dan `scan-guide.md:104`.

### Dampak

- DB yang ditunjuk env (`DATABASE_URL`, `.env` Laravel, `application.yml`) bisa DB staging atau bersama; migrasi tertunda — termasuk milik branch lain — diterapkan tanpa rollback dari plugin.
- Fase 4 butir 3 ("perbaiki perintahnya lalu uji ulang bila gagal karena sintaks salah") mendorong model mencoba varian lain sampai berhasil, termasuk menambah flag paksa.
- `stacks/rust.md:74-76` menyatakan `cargo check` ikut gagal bila migrasi belum dijalankan (makro `sqlx::query!`) — godaan menjalankan `sqlx migrate run` supaya baseline hijau.
- Jalur tersembunyi yang sama lewat `test`: Spring Boot menjalankan Flyway/Liquibase otomatis saat context `@SpringBootTest` naik; trait `RefreshDatabase` Laravel menjalankan `migrate:fresh` (menghapus semua tabel) pada koneksi test; `DatabaseTestTrait` CodeIgniter bisa menjalankan migrasi pada grup `tests`; TypeORM `synchronize: true` mengubah skema saat app naik. Aman atau tidaknya bergantung konfigurasi test repo — alasan butir izin di bawah juga mencakup `test`.

### Rencana perbaikan

1. **Ketujuh adapter** — ganti satu baris `migration` dengan dua baris. Perintah status wajib read-only (hanya membaca tabel versi atau berkas migrasi); tetap membuka koneksi DB, jadi dijalankan hanya sesudah izin.

   | Adapter | `migration-status` usulan | `migration-apply` — dicatat, dilarang dijalankan (termasuk varian perusak) |
   |---|---|---|
   | `go.md:66` | `migrate -path <dir> -database "$DATABASE_URL" version`; `goose -dir <dir> status`; atlas: `atlas migrate status --dir file://<dir> --url "$DATABASE_URL"` | `migrate … up\|down\|goto\|force\|drop`; `goose … up\|up-by-one\|up-to\|down\|down-to\|redo\|reset`; `atlas migrate apply`, `atlas schema apply` |
   | `bun.md:52` | `bunx prisma migrate status`; Drizzle: `bunx drizzle-kit check` (konsistensi berkas migrasi, tanpa DB) | `drizzle-kit migrate\|push`; `prisma migrate deploy\|dev\|reset`; `prisma db push`; skrip `bun run` yang memanggil salah satunya |
   | `java-spring.md:52` | Maven `./mvnw flyway:info` / `./mvnw liquibase:status`; Gradle `./gradlew flywayInfo` / tugas `status` plugin Liquibase | `flyway:migrate\|clean\|repair\|baseline`, `flywayMigrate\|flywayClean`; `liquibase:update\|rollback\|dropAll`, Gradle `update\|dropAll` |
   | `node.md:53` | `npx --no-install prisma migrate status`; `npx --no-install typeorm migration:show -d <datasource>`; `npx --no-install drizzle-kit check`; knex: `npx --no-install knex migrate:status` | `prisma migrate deploy\|dev\|reset`, `prisma db push`; `typeorm migration:run\|revert`, `schema:sync\|schema:drop`; `drizzle-kit migrate\|push`; `knex migrate:latest\|up\|down\|rollback` |
   | `php.md:56` | Laravel `php artisan migrate:status`; Symfony `php bin/console doctrine:migrations:status` | `migrate`, `migrate:fresh\|refresh\|reset\|rollback`, `db:wipe`, `db:seed`; `doctrine:migrations:migrate\|execute`, `doctrine:schema:update --force`, `doctrine:schema:drop` |
   | `php-codeigniter.md:53` | `php spark migrate:status` (sudah disebut, tapi di posisi kedua sesudah apply) | `php spark migrate`, `migrate:rollback\|refresh`, `db:seed` |
   | `rust.md:67` | `sqlx migrate info`; `diesel migration list`; `sea-orm-cli migrate status`; `refinery`: tanpa subperintah status yang terbukti → `tidak berlaku` | `sqlx migrate run\|revert`, `sqlx database setup\|reset\|drop`; `diesel migration run\|revert\|redo`, `diesel database setup\|reset`; `sea-orm-cli migrate up\|down\|fresh\|refresh\|reset`; `refinery migrate` |

   Cocokkan tiap perintah status dengan dokumentasi tool versi repo sebelum ditulis (gerbang kelayakan butir 3) — terutama `refinery` dan tugas Gradle Liquibase.

   Contoh diff `go.md`:
   ```diff
   -| migration | sesuai tool: `migrate -path <dir> -database $DATABASE_URL up`, atau `goose -dir <dir> up` |
   +| migration-status | `migrate -path <dir> -database "$DATABASE_URL" version`, atau `goose -dir <dir> status` — membaca tabel versi DB; `profile` menjalankannya hanya sesudah izin user |
   +| migration-apply | `migrate -path <dir> -database "$DATABASE_URL" up`, atau `goose -dir <dir> up` — **dicatat untuk manusia, tidak pernah dijalankan plugin** |
   ```
   Tambahan per adapter: `go.md` — `atlas` ada di `## Detection` (`:42`) tetapi tidak punya perintah di `## Commands`; `rust.md` — tambah kalimat "Pakai `SQLX_OFFLINE=true` bila `.sqlx/` ada; dilarang menjalankan migrasi agar `cargo check` hijau."

2. **`stacks/_CONTRACT.md:64-67`** — teks pengganti:
   > Tujuh baris perintah: `build`, `test`, `test-single`, `lint`, `typecheck`, `migration-status`, `migration-apply`. Tulis `tidak berlaku` bila stack tidak punya padanannya — dilarang mengarang perintah. `migration-status` wajib read-only. `migration-apply` dicatat untuk manusia dan **tidak pernah dieksekusi** skill atau agent mana pun. `profile` mengeksekusi perintah lain minimal sekali sebelum menuliskannya ke profil; perintah yang menyentuh DB, jaringan, atau docker (`migration-status`, test integrasi) hanya sesudah izin user. `architect` memakainya di gerbang verifikasi penutup taskdir.

   **`_CONTRACT.md:123`** (butir 3) — teks pengganti:
   > 3. Seluruh perintah di `## Commands` kecuali `migration-apply` sudah dieksekusi minimal sekali di repo nyata stack itu; `migration-apply` hanya diuji penulis adapter terhadap DB sekali pakai.

3. **`profile/SKILL.md:12`** (Iron Law) — teks pengganti, plus satu butir baru:
   > - Setiap perintah di `commands.md` wajib dieksekusi minimal sekali sebelum ditulis ke profil, **kecuali `migration-apply`**, yang hanya dicatat. Dilarang menjalankan perintah yang mengubah skema atau data (`migrate`, `up`, `deploy`, `push`, `seed`, `reset`, `fresh`) dalam kondisi apa pun, termasuk untuk menghijaukan baseline.
   > - Perintah yang menyentuh DB, jaringan, atau docker dijalankan hanya sesudah user menyetujui daftarnya lewat `AskUserQuestion`.

4. **`profile/SKILL.md:77-82`** (Fase 4) — teks pengganti:
   > Uji perintah hasil Fase 2 titik 7 sebelum ditulis ke `commands.md`:
   >
   > 1. Susun daftar eksekusi: `build`, `typecheck`, `lint`, `test`, `test-single`, `migration-status`. Baris `migration-apply`, `typecheck-scoped`, dan `typecheck-per-brief` **disalin dari adapter tanpa dieksekusi**.
   > 2. Tandai perintah yang menyentuh DB/jaringan/docker: `migration-status` selalu; `test`/`test-single` bila repo memuat test integrasi (mis. `@SpringBootTest`, `RefreshDatabase`, `DatabaseTestTrait`, Testcontainers, docker-compose di skrip test). Ajukan **satu** `AskUserQuestion`: daftar perintah bertanda, target DB/host yang terbaca dari konfigurasi (tanpa kredensial), risikonya, dan opsi `jalankan semua` · `hanya yang offline` · `batal`.
   > 3. Eksekusi yang diizinkan, satu per satu, dengan `timeout` tool Bash 300000 ms. Catat status: `OK` (exit 0), `FAIL` (exit bukan 0), `TIMEOUT`, `UNVERIFIED_ENV_NOT_READY` (dependensi belum terpasang), atau `DILEWATI (tanpa izin)`.
   > 4. Perbaiki perintah lalu uji ulang hanya bila gagal karena sintaks salah. Dilarang mengganti perintah status dengan varian apply, menambah flag paksa (`--force`, `-y`), atau menjalankan migrasi agar `build`/`test` hijau — catat `FAIL` apa adanya.
   > 5. Dilarang memperbaiki kode sumber agar baseline hijau.

5. **`references/scan-guide.md:104`** — teks pengganti:
   > Enam perintah dieksekusi: `build`, `typecheck`, `lint`, `test`, `test-single`, `migration-status` — yang menyentuh DB hanya sesudah izin user (Fase 4 `SKILL.md`). `migration-apply` disalin dari adapter tanpa dieksekusi: plugin tidak pernah menerapkan migrasi.

   Di §6 (`scan-guide.md:92-94`) tambah butir: "Catat perintah status dan apply terpisah; apply tidak pernah dijalankan."

6. **`templates/profile-template.md:152` dan `:259`** — teks pengganti:
   ```
   migration-status: <command read-only> [OK|FAIL|TIMEOUT|DILEWATI (tanpa izin)|tidak berlaku] · migration-apply: <command> [tidak dijalankan plugin] · folder <path> · pola <format nama berkas>
   migration-status: migrate -path db/migrations -database $DATABASE_URL version [DILEWATI (tanpa izin)] · migration-apply: migrate -path db/migrations -database $DATABASE_URL up [tidak dijalankan plugin] · folder db/migrations · pola {n}_{deskripsi}.up.sql
   ```
   `agents/code-implementor.md:14` ("terapkan lewat berkas migrasi baru sesuai `commands.md`") tetap sah karena ia hanya membaca folder/pola.

7. **Cek silang plugin lain** (hasil pemeriksaan, tidak perlu diubah di item ini kecuali disebut):
   - **frontenddev**: keempat adapter tidak punya baris migrasi; `profile/SKILL.md:80` hanya mengeksekusi `typecheck`, `lint`, `test`, `build`. Tidak ada perintah DB.
   - **quickdev**: `profile/SKILL.md:69-77` hanya typecheck/lint/test/build; tidak ada eksekusi migrasi. Tetapi `references/backend-profile-template.md:36` mencontohkan `pnpm prisma migrate dev / alembic upgrade head` sebagai "Migration Command" — diperbaiki di L3.5.
   - **Risiko sampingan `npx`** (backenddev `node.md`, frontenddev `react-vite.md:37`, `react-native.md:38`): dokumentasi npm (`npm-exec.md:28-29`, npm terpasang di mesin ini) menyatakan *"If any requested packages are not present in the local project dependencies, then a prompt is printed ... When standard input is not a TTY or a CI environment is detected, `--yes` is assumed."* Tool Bash bukan TTY, jadi `npx tsc --noEmit` di repo tanpa `typescript` lokal memasang paket `tsc` dari registry. Usulan: `npx --no-install …` atau `<pm> exec …` di semua adapter. Catat sebagai temuan baru untuk Langkah 8 bila tidak dikerjakan di sini.

### Test yang ditambahkan

`src/plugins/backenddev/tests/test_adapter_commands.py` (menguji isi adapter sebagai data):
```python
import re
from pathlib import Path

STACKS = Path(__file__).resolve().parents[1] / "skills/profile/stacks"
APPLY = re.compile(r"migrate\s+(deploy|dev|reset|run)\b|migration:run|migration (run|revert|redo)\b|"
                   r"flyway:(migrate|clean)|flyway(Migrate|Clean)|liquibase:(update|dropAll)|db push|"
                   r"drizzle-kit (migrate|push)|migrations:migrate|schema:update --force|"
                   r"(artisan|spark) migrate(?![:\w])|-database\s+\S+\s+up\b|goose[^|`]*\sup\b|"
                   r"migrate:(latest|fresh|refresh|reset|rollback)|migrate (up|down|fresh|refresh|reset)\b")

def rows(md: str) -> dict:
    sec = md.split("## Commands", 1)[1].split("\n## ", 1)[0]
    return {c[0]: "|".join(c[1:]) for c in (
        [x.strip() for x in ln.strip().strip("|").split("|")] for ln in sec.splitlines() if ln.startswith("| "))}

def test_migration_split_and_no_apply_outside_apply_row():
    for f in sorted(STACKS.glob("[!_]*.md")):
        r = rows(f.read_text(encoding="utf-8"))
        assert "migration" not in r, f"{f.name}: baris `migration` lama masih ada"
        assert {"migration-status", "migration-apply"} <= r.keys(), f.name
        for key, val in r.items():
            if key != "migration-apply":
                assert not APPLY.search(val), f"{f.name}: perintah apply di baris `{key}`: {val}"
```
Regex `APPLY` sudah diuji sesi ini terhadap string perintah (bukan terhadap berkas adapter): kedelapan varian status di tabel butir 1 tidak tertangkap, sepuluh baris apply saat ini (ketujuh adapter + `sea-orm-cli migrate up`) tertangkap. Target test: gagal di `34684ee`, hijau sesudah perbaikan. Test ini juga menjadi bagian lint L6.3.

### Verifikasi manual

Fixture Go dengan shim `migrate` yang hanya mencatat argumen (tidak menyentuh DB):
```bash
FX=$(mktemp -d); mkdir -p "$FX/bin" "$FX/repo"
printf '#!/bin/sh\necho "$@" >> %s/migrate.log\n' "$FX" > "$FX/bin/migrate"; chmod +x "$FX/bin/migrate"
cd "$FX/repo" && git init -q && printf 'module x\n\ngo 1.22\nrequire github.com/gin-gonic/gin v1.10.0\n' > go.mod
mkdir -p db/migrations && touch db/migrations/1_init.up.sql && git add -A && git commit -qm init
PATH="$FX/bin:$PATH" claude --plugin-dir <repo-plugin>/src/plugins/backenddev   # jalankan backenddev:profile
cat "$FX/migrate.log"
```
Harapan: `AskUserQuestion` muncul memuat `migration-status`; opsi `hanya yang offline` → `migrate.log` tidak ada; opsi `jalankan semua` → log hanya memuat `… version`; tidak pernah `up`. `commands.md` memuat dua baris migrasi.

### Selesai bila

- Tidak ada perintah pengubah skema di jalur eksekusi profile (`SKILL.md`, `scan-guide.md`, `_CONTRACT.md`, template).
- Ketujuh adapter memuat `migration-status` dan `migration-apply`; `test_adapter_commands.py` hijau.
- Verifikasi manual shim: `up` tidak pernah dipanggil.

### Risiko & catatan

- `_CONTRACT.md:64` menyebut "Enam baris" padahal adapter sudah punya delapan (termasuk `typecheck-scoped`, `typecheck-per-brief`); sesuaikan sekalian agar kontrak tidak menyimpang lagi.
- Perintah status tetap membuka koneksi DB — karena itu tetap di balik izin. Bila user memilih "tidak pernah" (Keputusan 4), baris status cukup `DILEWATI`.
- Profil lama berbaris `migration:` tetap terbaca implementor (folder/pola); REFRESH menulis format baru.

---

## L3.2 [Tinggi] Build adapter PHP menghapus dependensi dev ✔ diverifikasi ulang

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 1 jam · **Bergantung pada:** — · **Memblokir:** — (memberi fixture PHP untuk test L3.3)

### Konteks

Baris `build` adapter PHP dan CodeIgniter memakai flag deploy `--no-dev`. Profile Fase 4 menjalankan `build` lebih dulu lalu `typecheck`, `lint`, `test` — ketiganya `vendor/bin/*` milik dependensi dev. Architect Fase 4 menjalankan "kompilasi lalu test penuh"; bila "kompilasi" dibaca sebagai `build` (untuk PHP `typecheck-per-brief: tidak`, tidak ada kompilator lain), test penutup selalu gagal.

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/profile/stacks/php.md:49-53`
```
| build | `composer install --no-dev --optimize-autoloader` | sama |
| typecheck | `vendor/bin/phpstan analyse` atau `vendor/bin/psalm` | sama |
| typecheck-scoped | `vendor/bin/phpstan analyse <path>` | sama |
| typecheck-per-brief | `tidak` — phpstan bukan compiler; ... | sama |
| lint | `vendor/bin/pint --test`, atau `vendor/bin/php-cs-fixer fix --dry-run` | sama |
```
`src/plugins/backenddev/skills/profile/stacks/php-codeigniter.md:46`
```
| build | `composer install --no-dev --optimize-autoloader`; tambah `php spark optimize` bila pipeline deploy repo memakainya |
```
`src/plugins/backenddev/skills/profile/SKILL.md:79` (urutan `build`, `typecheck`, `lint`, `test`, …); `src/plugins/backenddev/skills/architect/SKILL.md:102` ("Jalankan kompilasi lalu test penuh dari `## Commands` profil").

### Reproduksi

Mandiri dan offline (paket dev palsu dari path repository lokal; butuh `php` + `composer`):
```bash
#!/usr/bin/env bash
set -u
W=$(mktemp -d); export COMPOSER_HOME="$W/.composer" COMPOSER_NO_INTERACTION=1
mkdir -p "$W/pkgs/fake-phpunit/bin" "$W/app/src"
echo '{"name":"fake/phpunit","version":"1.0.0","bin":["bin/phpunit"]}' > "$W/pkgs/fake-phpunit/composer.json"
printf '#!/bin/sh\necho "fake phpunit OK"\n' > "$W/pkgs/fake-phpunit/bin/phpunit"; chmod +x "$W/pkgs/fake-phpunit/bin/phpunit"
cat > "$W/app/composer.json" <<'J'
{"name":"demo/app","repositories":[{"type":"path","url":"../pkgs/*","options":{"symlink":false}}],
 "require":{},"require-dev":{"fake/phpunit":"1.0.0"},"autoload":{"psr-4":{"App\\":"src/"}}}
J
cd "$W/app"
composer install -q && echo "[1] dev install  : $(vendor/bin/phpunit)"
composer install --no-dev --optimize-autoloader -q          # baris build php.md:49 / php-codeigniter.md:46
vendor/bin/phpunit; echo "[2] sesudah build --no-dev: exit=$?"
composer install --optimize-autoloader -q && echo "[3] build dengan dev: $(vendor/bin/phpunit)"
composer dump-autoload -o -q && echo "[4] dump-autoload -o : $(vendor/bin/phpunit)"
rm -rf "$W"
```
Output aktual (dijalankan 2026-09-24, composer di `/usr/local/bin/composer`):
```
[1] dev install  : fake phpunit OK
repro.sh: line 20: vendor/bin/phpunit: No such file or directory
[2] sesudah build --no-dev: exit=127
[3] build dengan dev: fake phpunit OK
[4] dump-autoload -o : fake phpunit OK
```

### Dampak

- Profile: `typecheck`, `lint`, `test` sesudah `build` → exit 127 → tercatat `FAIL`/`UNVERIFIED_ENV_NOT_READY` di setiap repo PHP/CI4, dan instruksi failure path menyuruh user "memasang dependensi" — yang baru saja dihapus plugin.
- Architect: verifikasi penutup selalu merah → rantai PHP tidak pernah tuntas.
- Efek samping di luar `.claude/profile/`: `vendor/` user kehilangan tool dev sesudah profiling, bertentangan dengan guardrail "OUTPUT MODULAR TUNGGAL".

### Rencana perbaikan

1. `stacks/php.md:49` — teks pengganti:
   ```
   | build | `composer install --optimize-autoloader --no-interaction` (dengan dev; `--no-dev` hanya untuk artefak deploy, tidak pernah dipakai plugin) | sama |
   ```
2. `stacks/php-codeigniter.md:46` — teks pengganti:
   ```
   | build | `composer install --optimize-autoloader --no-interaction` (dengan dev) |
   ```
   Pindahkan `php spark optimize` ke paragraf catatan di bawah tabel sebagai langkah deploy, bukan build verifikasi.
3. Tambah satu kalimat di bawah tabel `## Commands` kedua adapter:
   > `--no-dev` adalah flag artefak deploy. Build verifikasi wajib mempertahankan dependensi dev karena `typecheck`, `lint`, dan `test` memanggil `vendor/bin/*`.
4. Alternatif (Keputusan 5): `composer dump-autoload -o` — tanpa jaringan dan tidak menyentuh isi `vendor/`, tetapi tidak memasang dependensi yang belum ada.

### Test yang ditambahkan

- Di `test_adapter_commands.py` (L3.1): tidak ada `--no-dev` di baris `build` adapter mana pun.
- `test_php_build_keeps_dev.py`: bungkus skrip reproduksi di atas sebagai test integrasi, `pytest.mark.skipif(shutil.which("composer") is None)`, dengan asersi `vendor/bin/phpunit` masih ada sesudah perintah `build` yang diambil dari baris adapter.

### Verifikasi manual

Jalankan skrip reproduksi (baris [3] harus lolos), lalu `backenddev:profile` di repo Laravel nyata: `commands.md` mencatat `typecheck`/`lint`/`test` dengan status dari exit code perintahnya sendiri, bukan 127.

### Selesai bila

Urutan build → test di fixture PHP hijau (baris [3] reproduksi), dan test lint `--no-dev` hijau.

### Risiko & catatan

`composer install` butuh jaringan bila `vendor/` tidak sinkron dengan `composer.lock`; di sandbox tertutup statusnya `UNVERIFIED_ENV_NOT_READY` (status yang sudah ada).

---

## L3.3 [Sedang] Verifikasi penutup menelan exit code

- [ ] Selesai

**Plugin:** backenddev, frontenddev · **Estimasi:** 1,5 hari · **Bergantung pada:** — (lunak: L6.1) · **Memblokir:** — (membantu L2.4, L4.2)

### Konteks

Kedua architect menjalankan perintah verifikasi penutup dengan `2>&1 | tail -40`. Exit code pipeline adalah milik `tail` (0), sehingga tool Bash menganggap hasilnya sukses dan vonis hijau/merah ditebak dari teks. Baseline hanya ada untuk kompilasi/typecheck — dan hanya bila `typecheck-per-brief: ya` — sehingga test yang sudah merah sebelum rantai dimulai membuat backenddev tidak pernah bisa menutup rantai, dan di frontenddev angka "galat baru" diketik manual.

**Koreksi terhadap ISSUES.md:**
1. *"build lama dibunuh tool, bukan ditandai TIMEOUT"* — tidak tepat. Dokumentasi tool Bash (`code.claude.com/docs/en/tools-reference`, bagian *Timeout and output limits* dan *Background commands*): *"`BASH_DEFAULT_TIMEOUT_MS` — the default when Claude passes no timeout; two minutes out of the box"*, *"`BASH_MAX_TIMEOUT_MS` — … ten minutes out of the box"*, dan *"When a command reaches its timeout without finishing, Claude Code moves it to the background instead of stopping it, unless the command starts with `sleep`."* Jadi perintah tidak dibunuh; ia pindah ke background. Dampaknya tetap buruk: dengan `| tail -40` belum ada keluaran sama sekali saat pemindahan, architect hanya menerima pesan *"Command did not complete within its 120s timeout and was moved to the background"*, dan aturan TIMEOUT 5 menit tidak punya pengukur mesin.
2. *"untuk lint/test/build tidak disebut sumbernya"* — sebagian. `commands.md` profil frontenddev menyimpan kolom "Status Baseline Aktual" dan "Error Pre-existing" per perintah (`frontenddev/skills/profile/templates/profile-template.md:127-133`). Sumber itu ada, tetapi (a) architect tidak merujuknya, (b) diambil saat profiling — bisa basi berpuluh commit, (c) hanya jumlah, tidak bisa dibandingkan per galat.

### Lokasi & kode saat ini

`src/plugins/backenddev/skills/architect/SKILL.md:102-104`
```
1. **Gerbang Verifikasi Taskdir**: Jalankan kompilasi lalu test penuh dari `## Commands` profil, dipipe `2>&1 | tail -40`.
   - Catat `Verifikasi Penutup: PASS` dan lanjut ke butir 2 jika keduanya hijau.
   - Hentikan eksekusi segera jika salah satu merah, lalu jalankan klasifikasi `## Failure path` butir 4 ...
```
`src/plugins/backenddev/skills/architect/SKILL.md:37` (Fase 0 butir 3a): baseline hanya kompilasi, hanya bila `typecheck-per-brief` `ya`.

`src/plugins/frontenddev/skills/architect/SKILL.md:33`, `:54`, `:102`
```
2. `typecheck-per-brief: ya` → jalankan `typecheck` sekali sekarang dan simpan jumlah galatnya sebagai baseline gerbang kompilasi. ...
1. Jalankan seluruh perintah `commands.md` profil plus `verification` brief yang belum tercakup, sekali, dipipe `2>&1 | tail -40`; tulis tabel hasilnya ke `{taskdir}/.explore/closing-verification.md` (bagian 7). Merah berarti `TIMEOUT` atau galat baru > 0 dibanding baseline; ...
5. **Verifikasi penutup macet** (>5 menit): tandai perintah itu `TIMEOUT` di log — bernilai merah; ...
```
`src/plugins/frontenddev/skills/architect/references/execution-protocol.md:152-163` (format log yang diketik LLM)
```
| Perintah | Hasil | Galat baru vs baseline |
|---|---|---|
| `pnpm typecheck` | HIJAU | 0 |

## <perintah yang MERAH>
<40 baris terakhir keluaran mentah>
```
`src/plugins/frontenddev/skills/architect/scripts/validate_review.py:215-222` — konsumen tabel itu (membaca `cells[0..2]`):
```python
            rows += 1
            result, new = cells[1].upper(), cells[2]
            if result not in ("HIJAU", "MERAH", "TIMEOUT"):
                p.append(f"hasil `{cells[1]}` di luar HIJAU|MERAH|TIMEOUT ({cells[0]})")
            if not new.isdigit():
                p.append(f"galat baru `{new}` bukan bilangan ({cells[0]})")
            # Merah warisan baseline (galat baru 0) bukan kegagalan rantai ini; TIMEOUT tetap merah.
            if result == "TIMEOUT" or (new.isdigit() and int(new) > 0) or not new.isdigit():
```

### Reproduksi

```bash
#!/usr/bin/env bash
sh -c 'echo "FAIL: 3 tests failed" >&2; exit 2' 2>&1 | tail -40; echo "tanpa pipefail : exit=$?"
set -o pipefail
sh -c 'echo "FAIL: 3 tests failed" >&2; exit 2' 2>&1 | tail -40; echo "dengan pipefail: exit=$?"
```
Output aktual:
```
FAIL: 3 tests failed
tanpa pipefail : exit=0
FAIL: 3 tests failed
dengan pipefail: exit=2
```
(Di zsh tanpa `pipefail` hasilnya sama: `exit=0`.)

### Dampak

- Tidak ada sinyal kegagalan mesin; vonis bergantung pada apakah ringkasan galat kebetulan jatuh di 40 baris terakhir.
- `validate_review.py` memvonis `BLOCKED`/`PASS` dari angka yang diketik tangan — validasi mekanis di atas input non-mekanis.
- backenddev: satu test merah warisan menahan rantai selamanya (menuntut hijau absolut tanpa baseline test).
- Build/test lama melewati batas 2 menit → pindah ke background → architect tanpa hasil.

### Rencana perbaikan

1. **Tambah `skills/_common/run_verification.py`** di backenddev dan frontenddev (dua salinan identik; plugin dipasang terpisah). Kerangka yang sudah diuji:
   ```python
   #!/usr/bin/env python3
   """Jalankan perintah verifikasi dengan exit code, durasi, timeout, dan ekor log yang tercatat mesin.

   Mode:
     baseline  jalankan tiap perintah, simpan {taskdir}/.explore/verification-baseline.json
     closing   jalankan tiap perintah, bandingkan dengan baseline, tulis
               {taskdir}/.explore/closing-verification.md (format tabel yang dibaca validate_review.py)

   Exit: 0 = tidak ada merah baru; 1 = ada TIMEOUT atau galat baru; 2 = argumen/IO salah.
   Hanya pustaka standar.
   """
   import argparse
   import json
   import os
   import re
   import signal
   import subprocess
   import sys
   import time
   from pathlib import Path

   ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
   ERROR_LINE = re.compile(r"\b(error|errors|failed|failure|fatal|exception)\b|✗|✖|\bFAIL\b", re.I)
   VOLATILE = [
       (re.compile(r":\d+:\d+\b"), ":L:C"),                        # posisi baris:kolom bergeser antar-commit
       (re.compile(r"\(\d+(\.\d+)?\s?(ms|s)\)|\b\d+(\.\d+)?\s?(ms|s)\b"), "<dur>"),
       (re.compile(r"0x[0-9a-f]+", re.I), "<addr>"),
   ]


   def signatures(text: str) -> set:
       """Baris galat yang dinormalisasi; selisih himpunan = galat baru."""
       sigs = set()
       for raw in text.splitlines():
           line = ANSI.sub("", raw).strip()
           if not line or not ERROR_LINE.search(line):
               continue
           for pat, rep in VOLATILE:
               line = pat.sub(rep, line)
           sigs.add(line[:300])
       return sigs


   def run_one(name: str, cmd: str, timeout: int, log_dir: Path, cwd: Path) -> dict:
       log_path = log_dir / f"{name}.log"
       start = time.monotonic()
       status, exit_code = None, None
       with open(log_path, "wb") as log:
           # start_new_session: seluruh pohon proses (worker jest, daemon gradle) bisa dibunuh saat timeout
           proc = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
           try:
               exit_code = proc.wait(timeout=timeout)
           except subprocess.TimeoutExpired:
               os.killpg(proc.pid, signal.SIGTERM)
               try:
                   proc.wait(timeout=10)
               except subprocess.TimeoutExpired:
                   os.killpg(proc.pid, signal.SIGKILL)
                   proc.wait()
               status = "TIMEOUT"
       text = log_path.read_text(encoding="utf-8", errors="replace")
       return {
           "name": name, "cmd": cmd, "exit": exit_code,
           "status": status or ("HIJAU" if exit_code == 0 else "MERAH"),
           "duration_s": round(time.monotonic() - start, 1),
           "signatures": sorted(signatures(text)),
           "tail": text.splitlines()[-40:],
           "log": str(log_path),
       }


   def new_errors(res: dict, base: dict) -> int:
       if res["status"] == "HIJAU":
           return 0
       cur = set(res["signatures"])
       if base is None or base.get("status") == "HIJAU":
           # tidak ada baseline merah yang bisa memaafkan: merah minimal 1 galat baru
           return max(1, len(cur - set((base or {}).get("signatures", []))))
       return len(cur - set(base.get("signatures", [])))


   def render_md(results: list, baseline: dict) -> str:
       # Tiga kolom pertama = kontrak validate_review.py (_verification_red membaca cells[0..2]).
       # Perintah penuh di kolom terakhir: '|' di dalam perintah tidak menggeser tiga kolom itu.
       out = ["| Perintah | Hasil | Galat baru vs baseline | Exit | Durasi | Perintah penuh |",
              "|---|---|---|---|---|---|"]
       for r in results:
           out.append(f"| `{r['name']}` | {r['status']} | {r['new']} | "
                      f"{'—' if r['exit'] is None else r['exit']} | {r['duration_s']}s | `{r['cmd']}` |")
       if not baseline:
           out += ["", "> Baseline absen: tiap MERAH dihitung minimal 1 galat baru."]
       for r in results:
           if r["status"] != "HIJAU":
               out += ["", f"## {r['name']} — {r['status']}", "```", *r["tail"], "```",
                       f"Log penuh: `{r['log']}`"]
       return "\n".join(out) + "\n"


   def main() -> int:
       ap = argparse.ArgumentParser()
       ap.add_argument("mode", choices=["baseline", "closing"])
       ap.add_argument("--taskdir", required=True)
       ap.add_argument("--cmd", action="append", required=True, metavar="NAMA=PERINTAH")
       ap.add_argument("--timeout", type=int, default=300, help="detik per perintah (default 300)")
       ap.add_argument("--out", help="closing: berkas hasil (default .explore/closing-verification.md)")
       ap.add_argument("--force", action="store_true", help="baseline: timpa baseline yang sudah ada")
       args = ap.parse_args()

       root = Path.cwd()
       explore = Path(args.taskdir) / ".explore"
       base_path = explore / "verification-baseline.json"
       if args.mode == "baseline" and base_path.exists() and not args.force:
           # Re-entry lintas sesi: baseline lama dipakai ulang, bukan diukur ulang di atas brief yang
           # sudah mendarat (galat brief itu akan tertelan jadi "warisan" — lihat L2.4).
           print(f"BASELINE ada, dipakai ulang: {base_path}")
           return 0
       log_dir = explore / "verification-logs" / args.mode
       try:
           log_dir.mkdir(parents=True, exist_ok=True)
           pairs = [c.split("=", 1) for c in args.cmd]
           if any(len(p) != 2 or not p[0] or not p[1].strip() for p in pairs):
               raise ValueError("--cmd wajib berbentuk NAMA=PERINTAH")
       except (OSError, ValueError) as e:
           print(f"ERROR: {e}", file=sys.stderr)
           return 2

       results = [run_one(n, c, args.timeout, log_dir, root) for n, c in pairs]

       if args.mode == "baseline":
           base_path.write_text(json.dumps({r["name"]: r for r in results}, indent=1), encoding="utf-8")
           for r in results:
               print(f"BASELINE {r['name']}: {r['status']} exit={r['exit']} {r['duration_s']}s "
                     f"galat={len(r['signatures'])}")
           return 0

       baseline = json.loads(base_path.read_text(encoding="utf-8")) if base_path.exists() else {}
       red = False
       for r in results:
           r["new"] = new_errors(r, baseline.get(r["name"]))
           red |= r["status"] == "TIMEOUT" or r["new"] > 0
           print(f"CLOSING {r['name']}: {r['status']} exit={r['exit']} baru={r['new']} {r['duration_s']}s")
       out = Path(args.out) if args.out else explore / "closing-verification.md"
       out.write_text(render_md(results, baseline), encoding="utf-8")
       print(f"VERDICT: {'MERAH' if red else 'HIJAU'} -> {out}")
       return 1 if red else 0


   if __name__ == "__main__":
       sys.exit(main())
   ```
   Perintah datang dari architect (`--cmd nama=perintah`, disalin dari `commands.md`), sehingga skrip netral terhadap format `commands.md` yang berbeda di kedua plugin (baris `·` di backenddev, tabel di frontenddev). `.explore/` sudah di-gitignore kedua profile (backenddev `profile/SKILL.md` Fase 5 butir 4; frontenddev `profile/SKILL.md:96`).

2. **Cara memanggil dari main loop.** Total waktu empat perintah bisa melewati batas 10 menit tool Bash, jadi panggil dengan `run_in_background: true`, tunggu notifikasi selesai, lalu baca berkas hasil. Vonis = exit runner (0 lolos, 1 merah, 2 salah pakai) dan tabel berkas — bukan teks log.

3. **frontenddev `architect/SKILL.md:33`** (Phase 0 butir 2) — teks pengganti:
   > 2. Ambil baseline seluruh perintah `commands.md` profil (typecheck, lint, test, build) sekali, sebelum implementor pertama: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py baseline --taskdir <taskdir> --cmd typecheck='<…>' --cmd lint='<…>' --cmd test='<…>' --cmd build='<…>'` lewat Bash `run_in_background: true`. Baseline yang sudah ada dipakai ulang (re-entry), tidak diukur ulang. Merah di sini bukan alasan berhenti — ia yang membuat penutup dapat memvonis galat **baru**.

4. **frontenddev `architect/SKILL.md:54`** (Phase 4 butir 1) — teks pengganti untuk baris `2>&1 | tail -40`:
   > 1. Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py closing --taskdir <taskdir> --cmd <nama>='<perintah>' …` untuk seluruh perintah `commands.md` profil plus `verification` brief yang belum tercakup, sekali, lewat Bash `run_in_background: true`. Dilarang memipe keluaran ke `tail`/`head` atau menyimpulkan vonis dari teks log. Skrip menulis `{taskdir}/.explore/closing-verification.md` (bagian 7); exit 0 = tidak ada merah baru, exit 1 = `TIMEOUT` atau galat baru > 0. `MERAH` bergalat baru 0 adalah warisan baseline, bukan alasan berhenti. Exit 1 → klasifikasikan tiap berkas galat: …(sisa kalimat klasifikasi tetap)…

5. **frontenddev `architect/SKILL.md:102`** — teks pengganti:
   > 5. **Perintah verifikasi melewati batas waktu**: `run_verification.py` membunuh pohon prosesnya pada `--timeout` (default 300 detik) dan mencatat `TIMEOUT` — bernilai merah; klasifikasi Phase 4 butir 1 tetap berjalan.

6. **frontenddev `references/execution-protocol.md`** — §7 (`:152-163`): ganti kalimat "Hasilnya ditulis ke …" menjadi "`run_verification.py closing` menulis …", dan contoh tabel menjadi enam kolom keluaran skrip. §5 (`:128-133`): gerbang typecheck per unit memakai `run_verification.py closing --cmd typecheck='<…>' --out {taskdir}/.explore/gate-<NN>.md` dengan baseline yang sama.

7. **backenddev `architect/SKILL.md:37`** (Fase 0 butir 3a) — teks pengganti:
   > 3a. **Baseline verifikasi.** Sebelum brief pertama berangkat, jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py baseline --taskdir {taskdir} --cmd build='<build>' --cmd test='<test>'` (tambah `--cmd typecheck='<…>'` bila `typecheck-per-brief` `ya`) lewat Bash `run_in_background: true`. Baseline yang sudah ada dipakai ulang pada re-entry. Merah di titik ini bukan alasan menghentikan rantai. Catat `Baseline: <ringkasan baris BASELINE skrip>` di laporan penutup.

8. **backenddev `architect/SKILL.md:102`** (Fase 4 butir 1) — teks pengganti untuk baris `2>&1 | tail -40`:
   > 1. **Gerbang Verifikasi Taskdir**: Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/run_verification.py closing --taskdir {taskdir} --cmd build='<build>' --cmd test='<test>'` (perintah dari `## Commands` profil; `build` `tidak berlaku` → `typecheck`) lewat Bash `run_in_background: true`, lalu baca `{taskdir}/.explore/closing-verification.md`. Dilarang memipe keluaran ke `tail`/`head` atau menebak hijau dari teks log.
   >    - Exit 0 → catat `Verifikasi Penutup: PASS (<n> perintah, merah warisan <m>)` dan lanjut ke butir 2.
   >    - Exit 1 (`TIMEOUT` atau galat baru) → hentikan eksekusi, jalankan klasifikasi `## Failure path` butir 4 (4a/4b) atas berkas yang disebut ekor log. Dilarang menambal kode sendiri.

   Di Failure path butir 4 (`:168`) tambah: "`TIMEOUT` diperlakukan merah."

9. **Bila tetap memakai pipe di tempat lain** (mis. debug): `set -o pipefail` dan catat `$?`, serta beri tool Bash `timeout` sampai 600000 ms.

### Test yang ditambahkan

`src/plugins/frontenddev/tests/test_run_verification.py` (salin ke backenddev, plus test paritas):
```python
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RV = ROOT / "skills/_common/run_verification.py"

def run(tmp, mode, *cmds, timeout=5):
    args = [sys.executable, str(RV), mode, "--taskdir", "td", "--timeout", str(timeout)]
    for c in cmds: args += ["--cmd", c]
    return subprocess.run(args, cwd=tmp, capture_output=True, text=True)

def test_exit_code_captured_and_timeout(tmp_path):
    r = run(tmp_path, "closing", "t=sh -c 'exit 2'", "b=sleep 30", timeout=1)
    assert r.returncode == 1
    md = (tmp_path / "td/.explore/closing-verification.md").read_text()
    assert "| `t` | MERAH | 1 | 2 |" in md and "| `b` | TIMEOUT |" in md

def test_inherited_red_is_not_new(tmp_path):
    run(tmp_path, "baseline", "t=sh -c 'echo \"FAIL a.test.ts (12 ms)\"; exit 1'")
    r = run(tmp_path, "closing", "t=sh -c 'echo \"FAIL a.test.ts (15 ms)\"; exit 1'")
    assert r.returncode == 0 and "| `t` | MERAH | 0 |" in (tmp_path / "td/.explore/closing-verification.md").read_text()

def test_baseline_reused_not_remeasured(tmp_path):
    run(tmp_path, "baseline", "t=true"); r = run(tmp_path, "baseline", "t=false")
    assert "dipakai ulang" in r.stdout
    assert json.loads((tmp_path / "td/.explore/verification-baseline.json").read_text())["t"]["exit"] == 0

def test_copies_identical():
    other = ROOT.parents[0] / "backenddev/skills/_common/run_verification.py"
    assert hashlib.sha256(RV.read_bytes()).digest() == hashlib.sha256(other.read_bytes()).digest()
```
Tambahkan juga test kompatibilitas: tabel keluaran dibungkus `## Verifikasi Penutup` dan diumpankan ke parser `validate_review.py` (fungsi `section_lines` + logika `_verification_red`) — tiap baris terbaca dengan kolom `Galat baru` berupa digit.

### Verifikasi manual

Fixture yang dipakai sesi ini (typecheck warisan + galat baru, lint dengan pipe di perintah, test merah warisan, build macet):
```bash
mkdir -p rv/td && cd rv
printf '#!/bin/sh\necho "src/old.ts:10:5 - error TS2304: Cannot find name '"'"'legacy'"'"'."\n[ "$(cat phase)" = closing ] && echo "src/new.ts:3:1 - error TS2322: Type '"'"'string'"'"' is not assignable to type '"'"'number'"'"'."\nexit 2\n' > tc.sh; chmod +x tc.sh
echo baseline > phase
python3 run_verification.py baseline --taskdir td --timeout 2 --cmd typecheck=./tc.sh --cmd lint=true \
  --cmd test="sh -c 'echo \"FAIL src/a.test.ts (12 ms)\"; exit 1'" --cmd build="sleep 5"
echo closing > phase
python3 run_verification.py closing --taskdir td --timeout 2 --cmd typecheck=./tc.sh --cmd lint="true | cat" \
  --cmd test="sh -c 'echo \"FAIL src/a.test.ts (15 ms)\"; exit 1'" --cmd build="sleep 5"; echo "runner exit=$?"
```
Output aktual:
```
BASELINE typecheck: MERAH exit=2 0.0s galat=1
BASELINE lint: HIJAU exit=0 0.0s galat=0
BASELINE test: MERAH exit=1 0.0s galat=1
BASELINE build: TIMEOUT exit=None 2.0s galat=0
CLOSING typecheck: MERAH exit=2 baru=1 0.0s
CLOSING lint: HIJAU exit=0 baru=0 0.0s
CLOSING test: MERAH exit=1 baru=0 0.0s
CLOSING build: TIMEOUT exit=None baru=0 2.0s
VERDICT: MERAH -> td/.explore/closing-verification.md
runner exit=1
```
Tabel yang dihasilkan (tiga kolom pertama terbaca parser `validate_review.py` sebagai `typecheck MERAH 1`, `lint HIJAU 0`, `test MERAH 0`, `build TIMEOUT 0` — semua kolom galat berupa digit):
```
| Perintah | Hasil | Galat baru vs baseline | Exit | Durasi | Perintah penuh |
|---|---|---|---|---|---|
| `typecheck` | MERAH | 1 | 2 | 0.0s | `./tc.sh` |
| `lint` | HIJAU | 0 | 0 | 0.0s | `true | cat` |
| `test` | MERAH | 0 | 1 | 0.0s | `sh -c 'echo "FAIL src/a.test.ts (15 ms)"; exit 1'` |
| `build` | TIMEOUT | 0 | — | 2.0s | `sleep 5` |
```
Sesudah itu, jalankan satu rantai frontenddev dan satu backenddev di repo contoh; pastikan architect memakai `run_in_background` dan membaca berkas hasil.

### Selesai bila

- Perintah yang gagal selalu tercatat `MERAH` beserta exit code; perintah macet tercatat `TIMEOUT`.
- Baseline tersedia untuk keempat jenis perintah (frontenddev) dan untuk `build`+`test` (backenddev), dan dipakai ulang pada re-entry.
- Tidak ada `| tail -40` di instruksi verifikasi kedua architect.
- Test di atas hijau di kedua plugin.

### Risiko & catatan

- Heuristik tanda galat (`ERROR_LINE`) bisa meleset untuk tool yang tidak mencetak kata "error"/"fail". Contoh nyata: fallback lint `gofmt -l .` di `go.md:63` selalu exit 0 walau ada berkas yang perlu diformat — runner akan mencatat HIJAU. Usulan adapter: `test -z "$(gofmt -l .)"` (catat untuk Langkah 8 bila tidak dikerjakan di sini).
- Galat baru yang pesannya identik dengan galat warisan terhitung 0; normalisasi `VOLATILE` perlu ditambah per stack bila ada stempel waktu di keluaran.
- Biaya baseline test penuh di awal rantai (Keputusan 2).
- Skrip menjalankan perintah dari profil dengan `shell=True` — tingkat kepercayaan sama dengan praktik saat ini (perintah itu memang sudah dijalankan LLM).

---

## L3.4 [Tinggi] Bash di code-implementor tanpa pagar mekanis

- [ ] Selesai

**Plugin:** backenddev, frontenddev · **Estimasi:** Opsi A 2 hari · Opsi B frontenddev 2–3 jam, backenddev 1 hari · **Bergantung pada:** keputusan user (Log Keputusan L3.4), L2.6 (path `finding_source` di lease/daftar staging), L1.2/L1.3 (menyunting `hooks/hooks.json` yang sama) · **Memblokir:** —

### Konteks

Batas Bash implementor hanya prosa. backenddev melarang push/merge/rebase/reset/pindah branch/build/test dan `--no-gpg-sign`, tetapi tidak menyebut `git checkout -- .`, `git clean -fd`, `git stash`, `rm -rf`, `commit --amend`, `--no-verify`. Scope berkas baru diperiksa **sesudah** commit oleh LLM yang membaca `git show --stat`; efek di luar git (hapus berkas ignored seperti `.env.local`) tidak terdeteksi dan tidak terpulihkan. frontenddev implementor tidak punya Grep/Glob, sehingga terdorong mencari lewat Bash — melanggar Iron Law-nya sendiri.

**Temuan dokumentasi resmi (diambil 2026-09-24 dari `code.claude.com/docs/en/hooks`, `/sub-agents`, `/plugins-reference`):**

1. Input hook memuat identitas subagen — *hooks*, "Common input fields":
   > When running with `--agent` or inside a subagent, two additional fields are included:
   >
   > `agent_id` — Unique identifier for the subagent. Present only when the hook fires inside a subagent call. Use this to distinguish subagent hook calls from main-thread calls.
   >
   > `agent_type` — Agent name (for example, `"Explore"` or `"security-reviewer"`). Present when the session uses `--agent` or the hook fires inside a subagent. For subagents, the subagent's type takes precedence over the session's `--agent` value. …
2. Hook plugin ikut berjalan di subagen — *hooks*, "Hook locations":
   > Hooks from settings files, managed policy settings, and plugins also run inside subagents. When a subagent calls a tool, tool events such as `PreToolUse` and `PostToolUse` fire the same configured hooks as in the main conversation, and the input carries the `agent_id` and `agent_type` common input fields that identify the subagent.
3. Nilai untuk agent plugin — *hooks*, "SubagentStart":
   > For subagents shipped by a plugin, the agent type is the plugin-scoped identifier such as `my-plugin:reviewer`, not the bare frontmatter name.

   → nilai yang dicocokkan: `backenddev:code-implementor`, `frontenddev:code-implementor` (nama plugin dari `.claude-plugin/plugin.json`).
4. Semantik blokir — *hooks*, "PreToolUse decision control" dan "Timeouts":
   > A hook that blocks by exiting 2 routes the same way as `"deny"`: Claude sees the stderr message as the denial reason.

   > Any other exit code doesn't block on its own for most hook events.

   > A timed-out `command`, `http`, or `mcp_tool` hook doesn't block the tool call.

   → pagar harus fail-closed sendiri (tangkap semua galat → exit 2) dan cepat.
5. Frontmatter agent plugin tidak bisa memasang hook — *sub-agents*:
   > For security reasons, plugin subagents don't support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin.
6. Field `tools` tidak mendukung pola perintah — *sub-agents*, tabel frontmatter: `tools` = *"Tools the subagent can use, as a comma-separated string such as `Read, Grep, Bash` or a YAML list."* Satu-satunya specifier yang terdokumentasi untuk `tools` adalah `Agent(agent_type)`, dan itu pun *"applies only to an agent running as the main thread with `claude --agent`"*. Untuk `disallowedTools`: *"An entry with a specifier, such as `Bash(git push *)`, still removes the whole tool from the subagent, not only the matching commands."* Contoh resmi `db-reader` memakai hook PreToolUse *"when you need finer control than the `tools` field provides"*. **Kesimpulan: `Bash(git add:*)` di `tools` tidak terdokumentasi dan tidak boleh diandalkan.**
7. Plugin tidak bisa mengirim aturan izin — *plugins-reference*: `settings.json` plugin *"Only the `agent` and `subagentStatusLine` keys are supported"*. Jadi `permissions.deny` bukan jalur plugin.
8. *hooks*, field `if`: *"Because the `if` filter is best-effort, use the permission system rather than a hook to enforce a hard allow or deny."* → pagar tidak memakai `if`; ia berjalan untuk semua Bash dan mem-parse sendiri.

Kesimpulan: identitas subagen **tersedia**, jadi Opsi A (hook plugin) layak secara dokumentasi. Tetap wajib dibuktikan empiris (Verifikasi manual butir 1) sebelum diandalkan.

### Lokasi & kode saat ini

`src/plugins/backenddev/agents/code-implementor.md:4`, `:21-22`
```
tools: Read, Grep, Glob, Edit, Write, Bash
...
- **Staging eksplisit**: `git add` menyebut tiap path satu per satu. Dilarang `git add .`/`-A`, `git commit -a`, `push`, `merge`, `rebase`, `reset`, pindah branch, dan staging susulan.
- **Nol dialog & terminal**: dilarang meminta konfirmasi atau input interaktif, menjalankan build/test, dan menyalin output terminal.
```
`:16` — implementor meng-commit sendiri (`git add` per path, `git commit -m "<commit_message brief>"`); `:25` — commit penanda `wip(<domain>)` pada jalur gagal.

`src/plugins/frontenddev/agents/code-implementor.md:4`, `:14`, `:64`
```
tools: Read, Edit, Write, Bash
TOOL `Bash` HANYA UNTUK `git restore -- <path files_touched>`, `rm -- <path>` ATAS BERKAS BERAKSI `CREATE` DI `files_touched` YANG DIBUAT UNIT INI (ROLLBACK), DAN `git status --porcelain`; ...
- [FORBIDDEN] Menjalankan perintah `Bash` selain `git restore -- <path files_touched>`, `rm -- <path>` atas berkas `CREATE` ...
```
`src/plugins/backenddev/hooks/hooks.json` dan `src/plugins/frontenddev/hooks/hooks.json` — hanya `SessionStart` (matcher `startup|resume|clear|compact`, perintah `tech-lead-gate.sh` / `lead-gate.sh`).

`src/plugins/frontenddev/skills/architect/references/execution-protocol.md:49` — matriks bukti disk dijalankan LLM ("Jalankan `git status --porcelain` … dan sandingkan dengan `files_touched`"). `src/plugins/backenddev/skills/architect/SKILL.md:88-89` — perbandingan `git show --stat <sha>` vs `## File scope` oleh LLM.

### Reproduksi

```bash
#!/usr/bin/env bash
cd "$(git rev-parse --show-toplevel)"
for p in backenddev frontenddev; do
  python3 -c "import json;d=json.load(open('src/plugins/$p/hooks/hooks.json'));print('$p hooks:', sorted(d['hooks']))"
done
```
Output aktual:
```
backenddev hooks: ['SessionStart']
frontenddev hooks: ['SessionStart']
```
Tidak ada `PreToolUse`, dan field `hooks` di frontmatter agent plugin diabaikan (fakta 5) — tidak ada lapisan mekanis antara implementor dan `git clean -fd`.

### Dampak

Satu perintah destruktif dari model sonnet (`git checkout -- .`, `git clean -fdx`, `rm -rf`) menghapus kerja user yang belum di-commit atau berkas ignored (`.env.local`) tanpa jejak git; `commit --amend` bisa menimpa commit brief sebelumnya; `--no-verify` melewati hook repo.

### Rencana perbaikan

**0. Keputusan (Log Keputusan L3.4).** Rekomendasi: **frontenddev → Opsi B**, **backenddev → Opsi A** (fallback B bila Verifikasi manual 1 gagal).

| | Opsi A — hook `PreToolUse` + lease | Opsi B — cabut Bash dari implementor |
|---|---|---|
| Kekuatan | Additif; doktrin "implementor commit sendiri" backenddev tetap | Tidak ada Bash = tidak ada yang perlu dipagari; tidak bergantung hook |
| Kelemahan | Bergantung hook plugin aktif (bisa dimatikan `disableAllHooks`/kebijakan managed); hook yang timeout tidak memblokir | backenddev: commit pindah ke architect (menyentuh 5 berkas, berinteraksi dengan L2.6) |
| frontenddev | Perlu lease + allowlist restore/rm | Hampir gratis: matriks §3 sudah memulihkan (`git restore -- <files_touched>`, hapus berkas baru), prasyarat Ingest sudah menjamin tree bersih dan HEAD tidak detached (`architect/scripts/check_preconditions.py` check 9 + cek tree kotor) |

**Opsi A**

A1. **`hooks/guard_bash.py`** (satu berkas per plugin, parameter `--plugin`). Kerangka yang sudah diuji:
```python
#!/usr/bin/env python3
"""Pagar mekanis tool Bash untuk `<plugin>:code-implementor` (hook PreToolUse, matcher Bash).

  guard_bash.py hook  --plugin backenddev|frontenddev   # dibaca dari stdin JSON hook
  guard_bash.py lease --plugin P --brief <path>          # ditulis architect sebelum dispatch
  guard_bash.py lease --plugin P --clear                 # dihapus architect sesudah triase

Hanya berlaku bila input hook membawa agent_type == "<plugin>:code-implementor".
Panggilan lain (main loop, agent lain, plugin lain) lolos tanpa keputusan (exit 0).
Untuk implementor: fail-closed — galat internal pun menolak (exit 2), karena exit selain 2
tidak memblokir (docs hooks: "Any other exit code doesn't block on its own").
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

META = re.compile(r"[;&|<>`\n]|\$\(")        # rantai/pengalihan/substitusi -> tolak
READ_ONLY_GIT = {"status", "diff", "log", "show", "rev-parse", "ls-files"}
FORBIDDEN_FLAGS = {"-a", "--all", "-A", "--amend", "--no-verify", "-n", "--no-gpg-sign",
                   "--output", "-f", "--force", "-r", "-rf", "-fr", "-u", "--update"}


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def repo_root(cwd: str) -> Path:
    out = git(Path(cwd), "rev-parse", "--show-toplevel")
    if out.returncode != 0:
        raise RuntimeError("bukan repo git")
    return Path(out.stdout.strip())


def lease_path(root: Path, plugin: str) -> Path:
    gd = Path(git(root, "rev-parse", "--git-dir").stdout.strip())
    return (gd if gd.is_absolute() else root / gd) / "agentic-workflow" / f"lease-{plugin}.json"


def allowed_from_brief(plugin: str, text: str) -> list:
    """Minimal; implementasi final memakai parser yang sudah ada (lihat butir A3)."""
    if plugin == "backenddev":   # tabel `## File scope`: | modify|create | path | anchor | ket |
        sec = text.split("## File scope", 1)[-1].split("\n## ", 1)[0]
        return [m.group(2).strip("` ") for m in
                re.finditer(r"^\|\s*`?(modify|create)`?\s*\|\s*([^|]+?)\s*\|", sec, re.M | re.I)]
    fm = text.split("---", 2)[1] if text.startswith("---") else ""   # frontmatter files_touched
    m = re.search(r"^files_touched:\s*\n((?:\s+-\s+.+\n?)+)", fm, re.M)
    return [ln.split("-", 1)[1].strip().strip("\"'") for ln in m.group(1).splitlines()] if m else []


def norm(root: Path, p: str) -> str:
    if any(ch in p for ch in "*?[]") or p.startswith("-"):
        raise ValueError(f"path `{p}` memuat glob atau menyerupai flag")
    full = (root / p).resolve()
    if root.resolve() not in full.parents and full != root.resolve():
        raise ValueError(f"path `{p}` di luar repo")
    return full.relative_to(root.resolve()).as_posix()


def paths_after_dashdash(tokens: list) -> list:
    return tokens[tokens.index("--") + 1:] if "--" in tokens else [t for t in tokens if not t.startswith("-")]


def decide(plugin: str, cmd: str, root: Path, lease: dict) -> str:
    """Kembalikan '' bila boleh, atau alasan penolakan."""
    if META.search(cmd):
        return "rantai/pipe/pengalihan/substitusi dilarang; jalankan satu perintah polos per panggilan"
    tok = shlex.split(cmd)
    if tok and tok[0] == "git" and len(tok) > 1 and tok[1] in READ_ONLY_GIT:
        bad = FORBIDDEN_FLAGS.intersection(t.split("=")[0] for t in tok)
        return f"flag {sorted(bad)} dilarang" if bad else ""
    allowed = set(lease.get("allowed", []))
    if plugin == "backenddev":
        if tok[:2] == ["git", "add"]:
            ps = paths_after_dashdash(tok[2:])
            flags = [t for t in tok[2:] if t.startswith("-") and t != "--"]
            if flags or not ps:
                return "`git add` hanya menerima path eksplisit tanpa flag"
            out = [p for p in ps if norm(root, p) not in allowed]
            return f"path di luar File scope/lease: {out}" if out else ""
        if tok[:2] == ["git", "commit"]:
            rest = tok[2:]
            if len(rest) == 2 and rest[0] in ("-m", "--message") and rest[1].strip():
                return ""
            return "hanya `git commit -m '<commit_message brief>'` (tanpa -a/--amend/--no-verify/-n/heredoc)"
    if plugin == "frontenddev":
        if tok[:2] == ["git", "restore"] and "--" in tok and tok.index("--") == 2:
            out = [p for p in tok[3:] if norm(root, p) not in allowed]
            return f"path di luar files_touched: {out}" if out or len(tok) == 3 else ""
        if tok[:2] == ["rm", "--"] and len(tok) == 3:
            p = norm(root, tok[2])
            if p not in allowed:
                return f"`{p}` di luar files_touched"
            if git(root, "ls-files", "--error-unmatch", "--", p).returncode == 0:
                return f"`{p}` ter-track git: hanya berkas CREATE buatan unit ini yang boleh dihapus"
            return ""
    return f"perintah di luar allowlist {plugin}:code-implementor: `{cmd[:80]}`"


def deny(reason: str) -> int:
    print(f"guard_bash: DITOLAK — {reason}", file=sys.stderr)
    return 2   # exit 2 = blokir; stderr menjadi alasan yang dibaca subagen


def hook(plugin: str) -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0                                  # tak bisa mengenali agen: bukan urusan pagar ini
    if data.get("agent_type") != f"{plugin}:code-implementor" or data.get("tool_name") != "Bash":
        return 0
    try:
        root = repo_root(data.get("cwd") or ".")
        lp = lease_path(root, plugin)
        if not lp.exists():
            return deny(f"lease absen ({lp}); architect wajib menjalankan `guard_bash.py lease` sebelum dispatch")
        reason = decide(plugin, data["tool_input"]["command"], root, json.loads(lp.read_text()))
        return deny(reason) if reason else 0
    except Exception as e:                        # fail-closed khusus implementor
        return deny(f"galat internal pagar: {e!r}")


def lease(plugin: str, brief: str, clear: bool) -> int:
    root = repo_root(".")
    lp = lease_path(root, plugin)
    if clear:
        lp.unlink(missing_ok=True)
        print(f"LEASE CLEARED {lp}")
        return 0
    b = Path(brief)
    allowed = [norm(root, p) for p in allowed_from_brief(plugin, b.read_text(encoding="utf-8"))]
    if not allowed:
        print("ERROR: File scope/files_touched kosong atau tak terbaca", file=sys.stderr)
        return 2
    extra = [norm(root, str(b))]                  # berkas brief ikut di-stage backenddev
    nn = re.match(r"brief-(\d+)-", b.name)
    if plugin == "backenddev" and nn:             # jalur gagal: commit wip menstage report-NN.md
        extra.append(norm(root, str(b.parent / f"report-{nn.group(1)}.md")))
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps({"plugin": plugin, "brief": extra[0], "allowed": allowed + extra}, indent=1))
    print(f"LEASE {lp}: {len(allowed)} path")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["hook", "lease"])
    ap.add_argument("--plugin", required=True, choices=["backenddev", "frontenddev"])
    ap.add_argument("--brief")
    ap.add_argument("--clear", action="store_true")
    a = ap.parse_args()
    sys.exit(hook(a.plugin) if a.mode == "hook" else lease(a.plugin, a.brief or "", a.clear))
```
Lease disimpan di `<git-dir>/agentic-workflow/lease-<plugin>.json`: di luar working tree, jadi tidak pernah muncul di `git status --porcelain` dan tidak mengganggu cek tree bersih.

A2. **`hooks/hooks.json`** — tambah entri (contoh backenddev; frontenddev sama dengan `--plugin frontenddev`). Bentuk exec (`args`) disarankan dokumentasi untuk path placeholder:
```json
{
  "hooks": {
    "SessionStart": [ "…entri yang sudah ada, tidak diubah…" ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/guard_bash.py", "hook", "--plugin", "backenddev"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```
Matcher PreToolUse menyaring nama tool, bukan agen; penyaringan agen terjadi di skrip (keluar 0 dalam milidetik untuk panggilan non-implementor).

A3. **Lease di architect.** backenddev `architect/SKILL.md:68` (Fase 3 butir 1) dan frontenddev `architect/SKILL.md:42` (Phase 2 butir 1) — sisipkan sebelum dispatch:
> Tulis lease pagar: `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/guard_bash.py lease --plugin <plugin> --brief <brief_path>`. Gagal (scope kosong/tak terbaca) → batalkan dispatch. Sesudah triase unit selesai (commit mendarat atau BLOCKED ter-commit): `guard_bash.py lease --plugin <plugin> --clear`.

Ganti parser minimal `allowed_from_brief` dengan parser yang sudah ada: backenddev `plan/scripts/validate_briefs.py::_parse_file_scope` (`:570-598`, pindahkan ke `_common`), frontenddev `split_frontmatter` di `_common/precondition_lib.py`. Bila L2.6 memilih "staging `finding_source`", tambahkan path itu ke lease.

A4. **(Disarankan) pagar Edit/Write dengan lease yang sama** — entri kedua `"matcher": "Edit|Write"` yang memeriksa `tool_input.file_path` (dokumentasi: *"For the file tools `Write`, `Edit`, and `Read`, `tool_input.file_path` is always absolute"*) terhadap `allowed` + `report-<NN>.md`. Ini menegakkan scope **sebelum** berkas berubah, bukan sesudah commit.

A5. **Lengkapi prosa** backenddev `code-implementor.md:21` — teks pengganti:
> - **Staging eksplisit**: `git add` menyebut tiap path `## File scope` satu per satu; commit hanya `git commit -m "<commit_message brief>"`. Dilarang `git add .`/`-A`, `git commit -a`, `--amend`, `--no-verify`, `--no-gpg-sign`, `push`, `merge`, `rebase`, `reset`, `checkout`/`switch`/`restore` apa pun, `git clean`, `git stash`, `rm`, rantai perintah (`&&`, `;`, `|`), dan staging susulan. Perintah di luar daftar ini ditolak hook `guard_bash.py`.

A6. **frontenddev `code-implementor.md:4`** → `tools: Read, Grep, Glob, Edit, Write, Bash` (berlaku juga di Opsi B tanpa `Bash`).

A7. **`skills/_common/verify_scope.py`** — vonis skrip menggantikan pembacaan manual. Kerangka yang sudah diuji:
```python
#!/usr/bin/env python3
"""Vonis mekanis berkas yang berubah vs scope brief.

  verify_scope.py --plugin P --brief <brief> --commit <sha>   # backenddev: sesudah implementor commit
  verify_scope.py --plugin P --brief <brief> --worktree       # frontenddev: sebelum architect commit

PASS (exit 0): tiap berkas ada di scope (+ brief itu sendiri + report-NN.md); laci .explore/ diabaikan.
FAIL (exit 1): daftar berkas liar. Exit 2: argumen/git salah.
Pemeriksaan simbol (hunk header vs Anchor) tetap milik L2.9.
"""
import argparse, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard_bash import allowed_from_brief  # implementasi final: parser bersama di _common


def changed(commit: str, worktree: bool) -> list:
    if worktree:
        out = subprocess.run(["git", "status", "--porcelain", "-uall"], capture_output=True, text=True, check=True)
        return [ln[3:].split(" -> ")[-1].strip('"') for ln in out.stdout.splitlines() if ln.strip()]
    out = subprocess.run(["git", "show", "--name-only", "--format=", commit], capture_output=True, text=True, check=True)
    return [p for p in out.stdout.splitlines() if p.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True, choices=["backenddev", "frontenddev"])
    ap.add_argument("--brief", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--commit")
    g.add_argument("--worktree", action="store_true")
    a = ap.parse_args()
    b = Path(a.brief)
    allowed = set(allowed_from_brief(a.plugin, b.read_text(encoding="utf-8"))) | {b.as_posix()}
    nn = re.match(r"brief-(\d+)-", b.name)
    if nn:
        allowed.add((b.parent / f"report-{nn.group(1)}.md").as_posix())
    try:
        touched = changed(a.commit, a.worktree)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e.stderr.strip()}", file=sys.stderr)
        return 2
    stray = [p for p in touched if p not in allowed and ".explore" not in p.split("/")]
    where = "worktree" if a.worktree else a.commit[:7]
    if stray:
        print(f"FAIL scope {where}: {len(stray)} berkas di luar scope: {', '.join(stray)}")
        return 1
    print(f"PASS scope {where}: {len(touched)} berkas, semua di scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
Teks pengganti backenddev `architect/SKILL.md:89` (kalimat pertama butir): "Jalankan `python3 ${CLAUDE_PLUGIN_ROOT}/skills/_common/verify_scope.py --plugin backenddev --brief <brief_path> --commit <sha>`. `FAIL` → **hentikan rantai di brief ini** …(sisa kalimat tetap)". frontenddev `execution-protocol.md:49`: jalankan `verify_scope.py --plugin frontenddev --brief <brief_path> --worktree` sebelum membuka cabang matriks; `FAIL` = baris "ada berkas berubah di luar `files_touched`".

**Opsi B**

B1. **frontenddev** — `code-implementor.md:4` → `tools: Read, Grep, Glob, Edit, Write`. Hapus kalimat Bash di `:3` (description), `:14` (Iron Law), `:26` (gerbang masuk 5 — sudah dijamin prasyarat Ingest architect), `:50` (self-check "`git restore` berkas liar" → "catat di `## Out of Scope / Mismatch`"), `:55` dan `:87` (rollback → "catat berkas yang perlu dipulihkan di `## Rollback`; pendispatch memulihkannya lewat matriks bukti disk"), `:64` (FORBIDDEN → "Dilarang memakai terminal; tool `Bash` tidak tersedia"). Matriks `execution-protocol.md` §3 baris `status: FAILED | kotor di dalam files_touched` sudah memuat pemulihan oleh architect — tidak perlu baris baru.

B2. **backenddev** — `code-implementor.md:4` → `tools: Read, Grep, Glob, Edit, Write`; `:16` langkah (b)–(d) dan `:25` dihapus: implementor menulis `status: DONE`/`BLOCKED` + `report-{NN}.md` lalu berhenti. Architect Fase 3 butir 2 (`architect/SKILL.md:69-71`) mengambil alih pola "Commit unit" frontenddev (`execution-protocol.md:66-72`): `verify_scope.py --worktree` → `git add <File scope> <brief> [report]` → `git commit -m "<commit_message brief>"`. Sesuaikan `dispatcher/implementor.md:25-29`, guardrail `COMMIT MILIK PENULISNYA` (`architect/SKILL.md:130`), `references/lifecycle-recovery.md` bagian 3, dan baris `Commit:` di Format Output implementor.

### Test yang ditambahkan

- `tests/test_guard_bash.py` — tabel kasus (fixture git `tmp_path`, lease dari brief contoh), minimal kasus yang sudah dijalankan di bawah, ditambah: lease absen → tolak; `shlex` gagal (kutip tak seimbang) → tolak (fail-closed); agent lain → exit 0; `git -C /x add`, `/usr/bin/git clean`, `git diff --output=../x` → tolak.
- `tests/test_verify_scope.py` — commit dalam scope → PASS; commit menyentuh berkas lain → FAIL; `--worktree` dengan berkas untracked di luar scope → FAIL; berkas di `.explore/` diabaikan.

Hasil aktual `guard_bash.py` atas input hook sintetis (repo git sementara, lease dari brief contoh; kolom: plugin, `agent_type`, exit, perintah, stderr):
```
backenddev  backenddev:code-implementor rc=0 git status --porcelain
backenddev  backenddev:code-implementor rc=0 git add internal/order/service.go backenddev/docs/2609241200-demo/brief-01-lock.md
backenddev  backenddev:code-implementor rc=2 git add .                                guard_bash: DITOLAK — path di luar File scope/lease: ['.']
backenddev  backenddev:code-implementor rc=2 git add internal/order/../../.env.local  guard_bash: DITOLAK — path di luar File scope/lease: [...]
backenddev  backenddev:code-implementor rc=0 git commit -m 'feat(order): implement lock'
backenddev  backenddev:code-implementor rc=2 git commit --amend -m x                  guard_bash: DITOLAK — hanya `git commit -m '<commit_message brief>'` ...
backenddev  backenddev:code-implementor rc=2 git commit --no-verify -m x              guard_bash: DITOLAK — hanya `git commit -m '<commit_message brief>'` ...
backenddev  backenddev:code-implementor rc=2 git checkout -- .                        guard_bash: DITOLAK — perintah di luar allowlist ...
backenddev  backenddev:code-implementor rc=2 git clean -fd                            guard_bash: DITOLAK — perintah di luar allowlist ...
backenddev  backenddev:code-implementor rc=2 git stash                                guard_bash: DITOLAK — perintah di luar allowlist ...
backenddev  backenddev:code-implementor rc=2 rm -rf internal                          guard_bash: DITOLAK — perintah di luar allowlist ...
backenddev  backenddev:code-implementor rc=2 cd internal && git add order/service.go  guard_bash: DITOLAK — rantai/pipe/pengalihan/substitusi dilarang ...
backenddev  backenddev:code-implementor rc=2 git commit -m "$(cat <<EOF ...)"         guard_bash: DITOLAK — rantai/pipe/pengalihan/substitusi dilarang ...
backenddev  backenddev:code-implementor rc=2 php artisan migrate                      guard_bash: DITOLAK — perintah di luar allowlist ...
backenddev  backenddev:code-reviewer    rc=0 git clean -fd
backenddev  (tanpa agent_type/main loop) rc=0 git clean -fd
frontenddev frontenddev:code-implementor rc=0 git restore -- src/app/old.ts
frontenddev frontenddev:code-implementor rc=2 git restore -- .env.local               guard_bash: DITOLAK — path di luar files_touched: ['.env.local']
frontenddev frontenddev:code-implementor rc=0 rm -- src/app/new.ts
frontenddev frontenddev:code-implementor rc=2 rm -- src/app/old.ts                    guard_bash: DITOLAK — `src/app/old.ts` ter-track git: ...
frontenddev frontenddev:code-implementor rc=2 rm -rf src                              guard_bash: DITOLAK — perintah di luar allowlist ...
frontenddev frontenddev:code-implementor rc=2 git checkout .                          guard_bash: DITOLAK — perintah di luar allowlist ...
frontenddev backenddev:code-implementor  rc=0 git clean -fd                           (bukan agen milik plugin ini)
backenddev  backenddev:code-implementor rc=2 git status --porcelain  (sesudah lease --clear)  guard_bash: DITOLAK — lease absen ...
```
Hasil aktual `verify_scope.py`:
```
PASS scope HEAD~1: 1 berkas, semua di scope            (exit 0)
FAIL scope HEAD: 1 berkas di luar scope: src/app/old.ts (exit 1)
PASS scope worktree: 2 berkas, semua di scope          (exit 0)
FAIL scope worktree: 1 berkas di luar scope: src/other/leak.ts (exit 1)
```

### Verifikasi manual

1. **Bukti empiris `agent_type`** (wajib sebelum Opsi A diandalkan): pasang sementara hook pencatat di `hooks.json` fixture — `{"matcher": "Bash", "hooks": [{"type": "command", "command": "sh -c 'cat >> /tmp/hook-input.jsonl'"}]}` — jalankan `claude --plugin-dir src/plugins/backenddev`, dispatch implementor atas brief sepele, lalu periksa baris yang `tool_name`-nya `Bash`: `agent_type` harus `backenddev:code-implementor` dan `agent_id` terisi; panggilan dari main loop tanpa kedua field. Gagal → pindah ke Opsi B.
2. Opsi A: di rantai fixture, minta implementor (lewat brief uji) menjalankan `git clean -fd` → ditolak dengan pesan `guard_bash: DITOLAK …`; commit normal tetap mendarat.
3. Opsi B: frontmatter implementor tanpa `Bash`; rantai fixture frontenddev dengan satu unit `FAILED` → architect memulihkan lewat matriks §3, tree bersih.

### Selesai bila

- Perintah di luar allowlist dari implementor ditolak mekanis (Opsi A), atau implementor tidak punya Bash (Opsi B).
- Pelanggaran scope divonis `verify_scope.py`, bukan pembacaan manual `git show --stat`.
- frontenddev implementor punya `Grep, Glob`.
- Log Keputusan L3.4 terisi.

### Risiko & catatan

- Hook plugin bisa tidak berjalan (hook dimatikan user/kebijakan, atau timeout — dan hook yang timeout tidak memblokir). `verify_scope.py` dan matriks architect tetap lapisan kedua.
- Parser minimal `allowed_from_brief` hanya untuk kerangka; jangan dirilis tanpa diganti parser bersama (A3).
- Bila ternyata `Write` tidak membuat direktori induk untuk berkas `create` di direktori baru, tambahkan `mkdir -p -- <dir induk path lease>` ke allowlist (perilaku `Write` soal direktori induk tidak ditemukan di dokumentasi tools-reference).
- Hook berjalan di semua panggilan Bash sesi yang memuat plugin; biaya start Python per panggilan kecil, tetapi tetap ada.

---

## L3.5 [Sedang] quickdev:profile menjalankan test/build tanpa konfirmasi

- [ ] Selesai

**Plugin:** quickdev · **Estimasi:** 2 jam · **Bergantung pada:** L3.1 (teks pola izin) · **Memblokir:** —

### Konteks

quickdev tidak punya skrip; semua bergantung pada teks SKILL. Profile wajib mengeksekusi typecheck, lint, test, dan build (kecuali `skip_baseline_exec`) tanpa izin, tanpa timeout, tanpa pemeriksaan artefak. Test integrasi backend bisa mengenai DB dari `.env`, jaringan, atau docker; build bisa meninggalkan berkas untracked yang lalu membuat precondition `execute` (`execute/SKILL.md:15`, "tidak memuat perubahan selain `plan_path` dan `profile_path`") gagal.

### Lokasi & kode saat ini

`src/plugins/quickdev/skills/profile/SKILL.md:10` (Iron Law, dipotong)
```
... SETIAP PERINTAH VERIFIKASI (TYPECHECK, LINT, TEST) WAJIB DIUJI EKSEKUSI MINIMAL SATU KALI UNTUK MEMASTIKAN VALIDITAS RUNTIME, KECUALI `skip_baseline_exec` BERNILAI `true` DAN STATUSNYA DICATAT `SKIPPED`. ...
```
`src/plugins/quickdev/skills/profile/SKILL.md:72-77`
```
   - Perintah Unit & Integration Test: `pnpm test`, `npm test`, `vitest run`, `jest`, `pytest`, atau `go test ./...`.
   - Perintah Build / Bundle Check: `pnpm build`, `npm run build`, `vite build`, atau `go build ./...`.
2. Jalankan setiap perintah verifikasi tersebut minimal 1 kali secara nyata via terminal runner (kecuali `skip_baseline_exec: true`):
   - Catat status eksekusi (`PASSED` atau `FAILED`; `SKIPPED` bila `skip_baseline_exec: true`) beserta durasi waktu running.
   - Tangkap baseline issues eksisting: ...
3. Dilarang mencatat perintah verifikasi rekaan yang tidak dapat dieksekusi di runtime aktual repositori.
```
`:105` (guardrail "MUST NOT mengabaikan eksekusi baseline …"), `:131` (enum status tanpa `TIMEOUT`), `:136` (failure path baseline).

`src/plugins/quickdev/skills/profile/references/backend-profile-template.md:36`
```
- **Migration Command**: `<misal: pnpm prisma migrate dev / alembic upgrade head>`
```
Catatan: Iron Law menyebut tiga perintah (TYPECHECK, LINT, TEST) sementara Fase 2 (`:73`) dan Output (`:127`) juga menjalankan/melaporkan build — tidak konsisten.

### Reproduksi

Tidak relevan (instruksi prosa, tanpa skrip). Bukti = kutipan di atas.

### Dampak

- Test integrasi mengenai DB/jaringan dari `.env` tanpa sepengetahuan user.
- Perintah macet menahan sesi (tanpa timeout; tool Bash memindahkannya ke background sesudah 2 menit, lihat koreksi di L3.3).
- Artefak build untracked yang tidak di-ignore memblokir `quickdev:execute` di putaran awal.
- Contoh `prisma migrate dev` di template menanam perintah apply sebagai "Migration Command" di profil.

### Rencana perbaikan

1. **`SKILL.md:10`** (Iron Law) — teks pengganti kalimat kedua:
   > SETIAP PERINTAH VERIFIKASI (TYPECHECK, LINT, TEST, BUILD) WAJIB DIUJI EKSEKUSI MINIMAL SATU KALI SESUDAH USER MENYETUJUI DAFTAR PERINTAH BESERTA RISIKONYA LEWAT `AskUserQuestion`; PERINTAH YANG DITOLAK, ATAU SEMUANYA BILA `skip_baseline_exec` BERNILAI `true`, DICATAT `SKIPPED`. DILARANG MENJALANKAN PERINTAH MIGRASI ATAU PERINTAH APA PUN YANG MENGUBAH SKEMA ATAU DATA.
2. **`SKILL.md:74-76`** (Fase 2 butir 2) — teks pengganti:
   > 2. Sebelum eksekusi (kecuali `skip_baseline_exec: true`):
   >    - Catat `git status --porcelain` sebagai keadaan awal.
   >    - Sajikan satu `AskUserQuestion`: daftar perintah beserta risikonya — test yang tampak integrasi (membaca `.env`, docker-compose, Testcontainers, `DATABASE_URL`) ditandai "menyentuh DB/jaringan"; build ditandai "dapat menulis artefak". Opsi: `jalankan semua` · `lewati yang menyentuh DB/jaringan` · `lewati semua (SKIPPED)`.
   > 3. Jalankan perintah yang disetujui satu per satu dengan `timeout` tool Bash 300000 ms:
   >    - Catat status (`PASSED`, `FAILED`, `TIMEOUT`, `SKIPPED`) beserta durasi.
   >    - Tangkap baseline issues eksisting: …(kalimat lama tetap)…
   > 4. Bandingkan `git status --porcelain` dengan keadaan awal. Berkas baru yang tidak di-ignore dicatat di profil sebagai "artefak build perlu di-ignore" dan dilaporkan ke user; dilarang menghapusnya sendiri.
   (Nomor butir 3 lama menjadi 5.)
3. **`SKILL.md:105`** (guardrail) — teks pengganti:
   > - MUST NOT mengeksekusi perintah baseline tanpa izin `AskUserQuestion`, tanpa timeout, atau perintah migrasi/pengubah data apa pun.
4. **`SKILL.md:131`** — enum status: `PASSED`, `FAILED`, `TIMEOUT`, `SKIPPED` (ditolak user atau `skip_baseline_exec`), `UNVERIFIED_ENV_NOT_READY`.
5. **`references/backend-profile-template.md:36`** — teks pengganti:
   ```
   - **Migration Status Command**: `<misal: pnpm prisma migrate status / alembic current>` — read-only
   - **Migration Apply Command**: `<misal: pnpm prisma migrate deploy / alembic upgrade head>` — dicatat, tidak pernah dijalankan skill
   ```

### Test yang ditambahkan

Tidak ada skrip untuk dites. Tambah cek teks di lint L6.3 (`scripts/lint_plugins.py`): `quickdev/skills/profile/SKILL.md` Fase 2 memuat `AskUserQuestion` dan `TIMEOUT`; `backend-profile-template.md` tidak memuat `migrate dev`/`upgrade head` di luar baris "Apply".

### Verifikasi manual

Fixture Node: `package.json` dengan `"test": "node -e \"require('fs').writeFileSync('touched.txt','x')\""` dan `"build": "mkdir -p out && echo x > out/a.js"` tanpa `.gitignore` untuk `out/`. Jalankan `quickdev:profile`:
- `AskUserQuestion` muncul sebelum perintah pertama.
- Pilih `lewati semua` → `BASELINE: … SKIPPED`, tidak ada berkas baru.
- Pilih `jalankan semua` → profil mencatat `out/` dan `touched.txt` sebagai artefak yang perlu di-ignore; berkasnya tidak dihapus skill.

### Selesai bila

quickdev:profile tidak mengeksekusi perintah apa pun sebelum izin user, setiap perintah dibatasi timeout dan bisa berstatus `TIMEOUT`, artefak baru dilaporkan, dan template tidak lagi mencontohkan perintah apply.

### Risiko & catatan

`quickdev:execute` Fase 3 (`execute/SKILL.md:65-70`) juga menjalankan test/build ketika `auto_verify: true`; pertimbangkan pola izin + timeout yang sama di sana (di luar cakupan item ini).

---

## L3.6 [Sedang] Commit laporan code-reviewer backenddev tanpa pemeriksaan branch dan konvensi

- [ ] Selesai

**Plugin:** backenddev · **Estimasi:** 2–3 jam · **Bergantung pada:** L2.1 (baris yang sama: `code-reviewer.md:80`) · **Memblokir:** —

### Konteks

Reviewer meng-commit `REVIEW.md` sendiri tanpa memastikan HEAD berada di branch sah, dengan pesan tetap yang mengabaikan `commit_convention` profil. Tidak ada lapisan mekanis di atasnya: berbeda dari frontenddev (`architect/scripts/check_preconditions.py:218-229`, check 9 "HEAD pada branch"), skrip prasyarat architect backenddev (`_check_4_git_worktree`, `:294-364`) hanya memeriksa repo git, tree bersih, dan rebase — tidak ada cek detached HEAD maupun HEAD = `base_branch`. Kalimat `git branch --show-current` sesuai branch taskdir di `architect/SKILL.md:38` hanya prosa.

### Lokasi & kode saat ini

`src/plugins/backenddev/agents/code-reviewer.md:80`, `:86`, `:105`
```
1. Jalankan `git add {taskdir}/REVIEW.md` lalu `git commit -m "docs(<slug>): add final review report"`, `<slug>` dari nama taskdir. Staging path eksplisit — dilarang `git add .`/`-A`, dan `src/**` dilarang ikut ter-stage.
- **Batas `Bash`**: HANYA inspeksi non-mutasi (`git diff`, `git log`, `git merge-base`, `git status`, `ls`) plus `git add`/`git commit` atas laporannya sendiri. Dilarang build, test, `push`, `merge`, `rebase`, `reset`, dan pindah branch.
- Commit: <sha7> `docs(<slug>): add final review report` | SKIPPED (<sebab kegagalan git>)
```
`src/plugins/backenddev/agents/code-reviewer.md:26` — gerbang merge-base hanya menuntut SHA ada (lolos walau HEAD = `base_branch`, rentang kosong).

`src/plugins/backenddev/skills/architect/dispatcher/reviewer.md:22`, `:54` — pesan tetap yang sama, termasuk untuk commit susulan oleh architect.

`src/plugins/backenddev/skills/architect/scripts/check_preconditions.py:339-347` — satu-satunya cek HEAD adalah rebase:
```python
            if (git_dir / "rebase-apply").exists() or (git_dir / "rebase-merge").exists():
                self.results.append({
                    "id": check_id,
                    "name": name,
                    "status": "FAIL",
                    "summary": "Operasi git rebase sedang berlangsung",
```

### Reproduksi

```bash
#!/usr/bin/env bash
set -eu
W=$(mktemp -d); cd "$W"; git init -q -b main .; git config user.email t@t; git config user.name t
echo a > a.txt; git add a.txt; git commit -qm init
git switch -q -c feat/x; echo b > b.txt; git add b.txt; git commit -qm "feat(x): implement unit"
git checkout -q --detach HEAD                        # sesi user/IDE meninggalkan detached HEAD
mkdir -p td; echo review > td/REVIEW.md
git add td/REVIEW.md; git commit -qm "docs(x): add final review report"; echo "commit di detached: exit=$?"
git switch -q feat/x 2>/dev/null
echo "REVIEW.md di feat/x? $(git ls-files td/REVIEW.md | wc -l) berkas"
git switch -q main
echo "HEAD=main: merge-base main HEAD = $(git merge-base main HEAD | cut -c1-7), HEAD = $(git rev-parse --short HEAD), commit di rentang = $(git rev-list --count $(git merge-base main HEAD)..HEAD)"
echo "symbolic-ref saat detached: $(git checkout -q --detach; git symbolic-ref -q --short HEAD; echo exit=$?)"
rm -rf "$W"
```
Output aktual:
```
commit di detached: exit=0
REVIEW.md di feat/x? 0 berkas
HEAD=main: merge-base main HEAD = 75e63c7, HEAD = 75e63c7, commit di rentang = 0
symbolic-ref saat detached: exit=1
```

### Dampak

- Detached HEAD: commit `REVIEW.md` sukses lalu hilang dari branch saat user kembali ke branch-nya; architect mengambil SHA dari `git log` dan melaporkan laporan yang tidak ada di branch.
- HEAD = `base_branch`: rentang `merge-base..HEAD` kosong → review "bersih" atas nol commit, lalu commit laporan langsung ke `main`/`dev`.
- Repo dengan `commit-msg` hook (commitlint, kunci tiket) menolak pesan tetap → reviewer `Commit: SKIPPED`, architect mengulang dengan pesan tetap yang sama (`dispatcher/reviewer.md:54`) → gagal lagi.

### Rencana perbaikan

1. **`code-reviewer.md` Gerbang Masuk** — tambah butir 7 (judul "6 stop condition" → "7 stop condition"):
   > 7. **Branch**: `git symbolic-ref -q --short HEAD` menghasilkan nama branch (exit 0) dan nama itu ≠ `<base_branch>`. Detached HEAD atau HEAD = `<base_branch>` → `BLOCKED`, minta user checkout branch taskdir; dilarang menilai rentang kosong atau meng-commit di luar branch kerja.
2. **`code-reviewer.md:80`** (Fase 4 butir 1) — teks pengganti (digabung dengan perbaikan L2.1):
   > 1. Ulangi pemeriksaan gerbang 7 tepat sebelum commit. Susun pesan dari `commit_convention` `.claude/profile/index.json` dengan type `docs`, scope `<slug>`, subjek `add final review report` (sesuaikan bahasa/huruf bila konvensi menuntut); `commit_convention` `tidak terdeteksi` → `docs(<slug>): add final review report`. Jalankan `git add {taskdir}/REVIEW.md backenddev/issues/README.md` (L2.1) lalu `git commit -m "<pesan>"`. Staging path eksplisit — dilarang `git add .`/`-A`, `--no-verify`, dan `src/**` ikut ter-stage.
3. **`code-reviewer.md:105`** — `- Commit: <sha7> \`<pesan sesuai commit_convention>\` | SKIPPED (<sebab kegagalan git>)`.
4. **`dispatcher/reviewer.md:22`** — "Commit: Commit sendiri `{taskdir}/REVIEW.md` (dan `backenddev/issues/README.md`) dengan pesan yang disusun dari `commit_convention` profil." **`:54`** — "Kunci sendiri dengan staging path eksplisit dan pesan dari `commit_convention` profil; bila commit ditolak hook `commit-msg`, laporkan pesan hook ke user — dilarang mengulang pesan yang sama atau `--no-verify`."
5. **`architect/scripts/check_preconditions.py`** — tambah cek mekanis di `_check_4_git_worktree` (atau check 7 baru), meniru frontenddev check 9:
   ```python
   branch = subprocess.run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=self.root,
                           capture_output=True, text=True).stdout.strip()
   if not branch:
       self.results.append({"id": check_id, "name": name, "status": "FAIL",
                            "summary": "Detached HEAD", "action": "Checkout branch taskdir sebelum orkestrasi."})
       return
   base = self.base_branch_arg or self._profile_base_branch()   # field base_branch index.json (dibaca di check 2)
   if base and branch == base:
       self.results.append({"id": check_id, "name": name, "status": "FAIL",
                            "summary": f"HEAD berada di base branch `{base}`",
                            "action": "Buat/checkout branch kerja taskdir; rentang review akan kosong di base branch."})
       return
   ```
   (`_profile_base_branch` helper kecil yang membaca `base_branch` dari `.claude/profile/index.json`; check 2 sudah memvalidasi field itu ada.)

### Test yang ditambahkan

`src/plugins/backenddev/tests/test_architect_preconditions.py`: fixture repo+profil+taskdir minimal —
- detached HEAD → check 4 `FAIL` "Detached HEAD";
- HEAD = `base_branch` dari `index.json` → `FAIL`;
- branch fitur → `PASS`.

### Verifikasi manual

Jalankan skrip reproduksi (memperlihatkan kedua kondisi); lalu di rantai fixture backenddev: `git checkout --detach` sebelum architect Fase 4 → prasyarat/reviewer `BLOCKED`, tidak ada commit. Repo dengan `commit_convention` bukan conventional (mis. `"[TIKET-123] <subject>"`) → pesan commit `REVIEW.md` mengikuti pola itu.

### Selesai bila

Commit laporan ditolak bila HEAD detached atau branch = base branch (di reviewer dan di skrip prasyarat), dan pesan commit dibentuk dari `commit_convention`.

### Risiko & catatan

- Nama branch taskdir tidak tercatat di mana pun secara mesin, jadi cek hanya bisa memastikan "bukan detached dan bukan base branch", bukan "branch yang benar".
- `commit_convention` berupa teks bebas; pembentukan pesan tetap dikerjakan model — test hanya bisa memeriksa kasus `tidak terdeteksi` → pesan default.

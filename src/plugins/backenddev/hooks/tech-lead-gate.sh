#!/bin/sh
# SessionStart — menyuntikkan pengingat gerbang `backenddev:tech-lead` sekali per sesi, tapi hanya di
# repo backend yang stack-nya benar-benar terdeteksi. Plugin ini aktif user-wide; tanpa penjagaan ini
# pengingatnya ikut muncul di repo frontend, repo docs, dan repo apa pun yang lain.
#
# Keluar diam-diam (exit 0, stdout kosong) berarti tidak ada yang disuntikkan.
set -eu

input=$(cat)

cwd=$(printf '%s' "$input" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
[ -n "${cwd:-}" ] || cwd=$PWD
[ -d "$cwd" ] || exit 0

# Penanda framework di berkas manifest, bukan sekadar "ada manifest". Repo Java biasa, modul Go
# pustaka, dan paket npm frontend tidak lolos — yang dicari adalah bukti server backend.
marker() {
  [ -f "$1" ] && grep -qE "$2" "$1"
}

# Satu tingkat submodule ikut diperiksa untuk manifest yang lazim dipakai monorepo.
marker_deep() {
  _pat=$1
  shift
  for _name in "$@"; do
    if marker "$cwd/$_name" "$_pat"; then return 0; fi
    for _m in "$cwd"/*/"$_name"; do
      if marker "$_m" "$_pat"; then return 0; fi
    done
  done
  return 1
}

stack=""
has_profile=0

# 1. Repo sudah di-onboard ke backenddev — penanda milik plugin ini sendiri; stack dibaca dari profil.
if [ -f "$cwd/.claude/profile/index.json" ]; then
  stack=$(sed -n 's/.*"stack"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$cwd/.claude/profile/index.json" | head -n 1)
  [ -n "$stack" ] || stack="terdaftar di profil"
  has_profile=1

# 2. Spring Boot — dilayani adapter `skills/profile/stacks/java-spring.md`.
elif marker_deep 'org\.springframework\.boot|spring-boot' pom.xml build.gradle build.gradle.kts gradle/libs.versions.toml; then
  stack="java-spring"

# 3. Stack lain — deteksi dari dependensi framework server di manifest.
elif marker_deep 'gin-gonic/gin|gofiber/fiber|labstack/echo|go-chi/chi|gorilla/mux|grpc-go' go.mod; then
  stack="go"
elif marker_deep 'hono|elysiajs' package.json && { [ -f "$cwd/bun.lockb" ] || [ -f "$cwd/bunfig.toml" ]; }; then
  stack="bun"
elif marker_deep '@nestjs/core|"express"|"fastify"|"koa"|@hapi/hapi' package.json; then
  stack="node"
elif marker_deep 'axum|actix-web|rocket|warp|poem' Cargo.toml; then
  stack="rust"
elif marker_deep '"codeigniter4/framework"' composer.json; then
  stack="php-codeigniter"
elif marker_deep 'laravel/framework|symfony/framework-bundle|slim/slim|laminas/laminas-mvc|yiisoft/yii2' composer.json; then
  stack="php"
fi

[ -n "$stack" ] || exit 0

# `SessionStart` membaca `hookSpecificOutput.additionalContext`, dan bentuk itu yang dipakai di sini
# alih-alih stdout mentah: kalau bentuknya salah hook gagal terbuka — diam, bukan berisik — dan
# gerbang yang diam adalah kegagalan yang paling mahal di plugin ini.
json_escape() {
  sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk '{ printf "%s%s", $0, "\\n" }'
}

# Yang disuntik soal profile cuma SATU BARIS status, bukan isinya. Isi profile bisa ditulis ulang di
# tengah sesi oleh `backenddev:profile`, dan salinan basi di context tidak kelihatan basi —
# dua versi hidup bersamaan, dan yang salah bisa terpakai. Yang stabil sepanjang sesi cuma ada atau
# belum ada, dan justru itu yang menentukan apakah sebuah rute akan berhenti di Phase 0.
if [ "$has_profile" = 1 ]; then
  profile_note='Profile repo `.claude/profile/` ADA. Isinya sengaja tidak disalin ke sini: skill yang membutuhkannya membaca berkasnya sendiri saat rutenya jalan, supaya yang terbaca selalu versi terakhir.'
else
  profile_note='Profile repo `.claude/profile/` BELUM ADA. Tiap rute selain baca-kode berhenti di Phase 0 karenanya. Tawarkan `backenddev:profile` di giliran ini juga, jangan tunggu rutenya mentok dulu.'
fi

context=$( { printf '<backenddev-tech-lead-gate>\nRepo backend, stack terdeteksi: %s. Plugin `backenddev` aktif.\n\n' "$stack"
printf '%s\n\n' "$profile_note"
cat <<'TXT'
`backenddev:tech-lead` jalan lebih dulu untuk tiap permintaan kerja baru — panggil lewat tool Skill
sebelum skill backenddev lain, sebelum menelusuri repo, sebelum menulis kode. Gerbang sendiri yang
explore kodenya lalu bertanya; rute diputuskan sesudah itu, bukan sebelum.

WAJIB lewat gerbang:
- permintaan kerja apa pun: memahami, mengubah, menambah, memperbaiki, mengaudit, mendokumentasikan
- susulan di tengah sesi, sekecil apa pun — "sekalian ganti X", "oh iya Y juga"
- menjalankan artefak yang sudah ada — "jalankan brief itu" — apa pun statusnya

LEWATI hanya tiga:
- jawaban user yang memasok informasi ke rute yang sudah diputuskan gerbang di giliran sebelumnya
- pertanyaan pengetahuan umum yang tidak menyentuh repo
- operasi VCS (commit, push, PR, rebase, diff) atas kerja yang sudah selesai

Pengingat ini disuntik sekali per sesi, tidak diulang tiap giliran. Berlaku sama di permintaan ke-1
dan ke-40; jaraknya dari prompt yang sedang kamu baca bukan tanda ia kedaluwarsa.
</backenddev-tech-lead-gate>
TXT
} | json_escape )

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$context"

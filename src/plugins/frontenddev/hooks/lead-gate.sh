#!/bin/sh
# SessionStart — menyuntikkan pengingat gate `frontenddev:lead` dan memvalidasi prasyarat profil
# `.claude/profile/` sekali per sesi, tapi hanya di repo frontend yang stack-nya
# benar-benar terdeteksi. Plugin ini aktif user-wide; tanpa penjagaan ini pengingatnya ikut muncul
# di repo backend, repo docs, dan repo apa pun yang lain.
#
# Keluar diam-diam (exit 0, stdout kosong) berarti tidak ada yang disuntikkan.
set -eu

input=$(cat)

cwd=$(printf '%s' "$input" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
[ -n "${cwd:-}" ] || cwd=$PWD
[ -d "$cwd" ] || exit 0

# Penanda framework di berkas manifest, bukan sekadar "ada package.json". Yang dicari adalah bukti
# aplikasi frontend dari stack yang didukung adapter `skills/profile/stacks/<stack-id>.md`:
# `react-vite`, `react-native`, `sveltekit`, `svelte-vite`. Next.js sengaja tidak dilayani.
#
# Deteksi ini dievaluasi sekali di awal sesi. Repo yang baru di-onboard `frontenddev:profile` di
# tengah sesi karena itu belum menyala sampai sesi berikutnya; matcher `clear` dan `compact` yang
# menutup sebagian celah itu, dan sisanya ditutup restart.
has_dep() {
  [ -f "$1" ] && grep -qE "\"($2)\"[[:space:]]*:" "$1"
}

# Urutan pemutus dari yang paling spesifik. Satu manifest yang memuat `next` bukan repo plugin ini,
# apa pun penanda lain yang ikut hadir.
detect_stack() {
  _pkg=$1
  [ -f "$_pkg" ] || return 1
  if has_dep "$_pkg" 'next'; then return 1; fi
  if has_dep "$_pkg" 'react-native|expo'; then printf 'react-native'; return 0; fi
  if has_dep "$_pkg" '@sveltejs/kit'; then printf 'sveltekit'; return 0; fi
  if has_dep "$_pkg" 'svelte'; then printf 'svelte-vite'; return 0; fi
  if has_dep "$_pkg" 'react'; then printf 'react-vite'; return 0; fi
  return 1
}

stack=""
has_profile=0

# 1. Repo sudah di-onboard ke frontenddev — marker milik plugin ini sendiri; stack dibaca dari profil.
if [ -f "$cwd/.claude/profile/index.json" ]; then
  stack=$(sed -n 's/.*"stack"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$cwd/.claude/profile/index.json" | head -n 1)
  has_profile=1
# 2. package.json di root memuat penanda stack yang didukung.
elif stack=$(detect_stack "$cwd/package.json"); then
  :
else
  # 3. Monorepo JS: hanya direktori workspace yang lazim, bukan sembarang subfolder.
  for pkg in "$cwd"/apps/*/package.json "$cwd"/packages/*/package.json; do
    if stack=$(detect_stack "$pkg"); then
      break
    fi
  done
fi

# Profil yang ada tetapi `stack`-nya tidak terbaca TIDAK boleh keluar diam-diam di sini: itu justru
# keadaan yang paling perlu dilaporkan. Ia jatuh ke cabang "index.json tidak sah" di bawah.
[ -n "$stack" ] || [ "$has_profile" = 1 ] || exit 0

# `SessionStart` membaca `hookSpecificOutput.additionalContext`, dan bentuk itu yang dipakai di sini
# alih-alih stdout mentah: kalau bentuknya salah hook gagal terbuka — diam, bukan berisik — dan gate
# yang diam adalah kegagalan yang paling mahal di plugin ini.
json_escape() {
  sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk '{ printf "%s%s", $0, "\\n" }'
}

# Sepuluh berkas profil. Kelengkapannya divonis di sini, bukan sekadar keberadaan `index.json`:
# profil yang setengah tertulis meloloskan gate lalu gagal di tengah rantai, di tempat yang jauh dari
# sebabnya.
PROFILE_FILES="index.json stack.md structure.md surface-map.md invariants.md commands.md layer-adoption.md visual.md drift.md manual-notes.md"
KNOWN_STACKS="react-vite react-native sveltekit svelte-vite"

profile_dir="$cwd/.claude/profile"
missing=""
for f in $PROFILE_FILES; do
  [ -f "$profile_dir/$f" ] || missing="$missing $f"
done

stack_known=0
for s in $KNOWN_STACKS; do
  [ "$stack" = "$s" ] && stack_known=1
done

if [ "$has_profile" = 0 ]; then
  context=$( { printf '<frontenddev-lead-gate>\nRepo ini terdeteksi sebagai repo frontend (stack: %s), tetapi profil `.claude/profile/` BELUM DIBUAT.\n\n' "$stack"
cat <<'TXT'
Dilarang memulai penelusuran fitur, perancangan arsitektur, atau penulisan kode sebelum profil repo siap.
Jika ada permintaan kerja baru, BERHENTI SEGERA, laporkan ketiadaan profil, dan instruksikan user menjalankan `frontenddev:profile` (mode GENERATE) terlebih dahulu.
</frontenddev-lead-gate>
TXT
} | json_escape )
elif [ "$stack_known" = 0 ]; then
  context=$( { printf '<frontenddev-lead-gate>\nRepo ini terdeteksi sebagai repo frontend, tetapi `.claude/profile/index.json` TIDAK SAH: field `stack` terbaca "%s", di luar daftar sah (react-vite, react-native, sveltekit, svelte-vite).\n\n' "$stack"
cat <<'TXT'
Tanpa field itu, tak satu pun skill hilir dapat memuat adapter `skills/profile/stacks/<stack-id>.md`.
Jika ada permintaan kerja baru, BERHENTI SEGERA dan minta user menulis ulang profil via `frontenddev:profile` (mode REFRESH).
</frontenddev-lead-gate>
TXT
} | json_escape )
elif [ -n "$missing" ]; then
  context=$( { printf '<frontenddev-lead-gate>\nRepo ini terdeteksi sebagai repo frontend, tetapi profil `.claude/profile/` TIDAK LENGKAP. Berkas yang hilang:%s\n\n' "$missing"
cat <<'TXT'
Berkas profil yang datanya nihil tetap wajib ada berisi `tidak terdeteksi`; berkas yang absen adalah profil yang gagal ditulis, bukan profil tanpa data.
Dilarang merutekan pekerjaan repo dengan profil yang tidak lengkap.
Jika ada permintaan kerja baru, BERHENTI SEGERA dan minta user melakukan refresh via `frontenddev:profile` (mode REFRESH).
</frontenddev-lead-gate>
TXT
} | json_escape )
else
  context=$( { printf '<frontenddev-lead-gate>\nRepo frontend, stack terdeteksi: %s. Plugin `frontenddev` aktif di sini.\n\n' "$stack"
cat <<'TXT'
Gate `frontenddev:lead` jalan lebih dulu untuk tiap permintaan kerja baru — panggil lewat tool Skill
sebelum menjalankan skill frontenddev lain, sebelum menelusuri repo, dan sebelum menulis kode. Berlaku
juga untuk susulan di tengah sesi, sekecil apa pun ("sekalian ganti X").

Lewati hanya untuk tiga hal: jawaban user yang memasok informasi ke kerja yang rutenya sudah
diputuskan gate di giliran sebelumnya, pertanyaan pengetahuan umum yang tidak menyentuh repo, dan
operasi VCS (commit, push, PR, rebase, diff) atas kerja yang sudah selesai.

Pengingat ini disuntik sekali per sesi dan tidak diulang tiap giliran. Ia berlaku sama untuk
permintaan pertama dan permintaan ke-40; jaraknya dari prompt yang sedang kamu baca bukan tanda
bahwa ia sudah kedaluwarsa.
</frontenddev-lead-gate>
TXT
} | json_escape )
fi

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$context"

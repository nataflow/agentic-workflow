"""Teks gerbang SessionStart `frontenddev`. Hanya teks — semua keputusan ada di `detect.py`."""

PROFILE_DIR = ".claude/profile/frontenddev/"

RULES = """Gate `frontenddev:lead` jalan lebih dulu untuk tiap permintaan kerja baru — panggil lewat tool Skill
sebelum menjalankan skill frontenddev lain, sebelum menelusuri repo, dan sebelum menulis kode. Berlaku
juga untuk susulan di tengah sesi, sekecil apa pun ("sekalian ganti X"), dan untuk menjalankan artefak
frontenddev yang sudah ada (brief, `TASK.md`, `CONTRACT.md`) apa pun statusnya.

Lewati hanya untuk empat hal: jawaban user yang memasok informasi ke kerja yang rutenya sudah
diputuskan gate di giliran sebelumnya; pertanyaan pengetahuan umum yang tidak menyentuh repo; operasi
VCS (commit, push, PR, rebase, diff) atas kerja yang sudah selesai; dan permintaan yang memanggil atau
melanjutkan alur plugin lain secara eksplisit — `/analyst:*`, `/quickdev:*`, atau susulan di tengah
skill `analyst:*`/`quickdev:*` yang sedang berjalan (elisitasi tiket, `plan/<task>.md`). Kerja itu
milik plugin tersebut sampai user sendiri meminta pindah ke gate ini.

Pengingat ini disuntik sekali per sesi dan tidak diulang tiap giliran. Ia berlaku sama untuk
permintaan pertama dan permintaan ke-40; jaraknya dari prompt yang sedang kamu baca bukan tanda
bahwa ia sudah kedaluwarsa."""


def _profile_note(v) -> str:
    p = v.profile
    lead = "Permintaan kerja tetap lewat `frontenddev:lead`; lead merutekan lane PROFILE"
    if p.state == "OK" and p.location == "own":
        return (f"Profil `{PROFILE_DIR}` lengkap (stack `{p.stack}`). Isinya sengaja tidak disalin ke sini: "
                "skill yang membutuhkannya membaca berkasnya sendiri, supaya yang terbaca selalu versi terakhir.")
    if p.location == "legacy" and p.state in ("OK", "INCOMPLETE"):
        return (f"Profil frontenddev masih di lokasi lama `.claude/profile/`. {lead} "
                f"ke `frontenddev:profile` mode MIGRATE (pindah ke `{PROFILE_DIR}`) sebelum rute lain; "
                "dilarang REFRESH atau GENERATE di atasnya.")
    if p.state in ("ABSENT", "OTHER_OWNER"):
        note = (f"Profil `{PROFILE_DIR}` BELUM DIBUAT. {lead} (`frontenddev:profile` mode GENERATE) "
                "lebih dulu, lalu melanjutkan rute tertunda.")
        if p.state == "OTHER_OWNER":
            note += (f" `.claude/profile/` berisi profil milik `{p.owner}` (stack `{p.stack}`) — biarkan; "
                     "jangan dibaca sebagai profil frontenddev, jangan ditimpa; `force: true` tidak berlaku atasnya.")
        return note
    if p.state == "INVALID_JSON":
        where = PROFILE_DIR if p.location == "own" else ".claude/profile/"
        return (f"`{where}index.json` bukan JSON valid; semua skrip prasyarat frontenddev akan FAIL. "
                f"{lead} mode REFRESH sebelum rute lain.")
    if p.state in ("NO_STACK", "UNKNOWN_STACK"):
        return (f"`{PROFILE_DIR}index.json` TIDAK SAH: field `stack` = `{p.stack or 'kosong'}`, di luar "
                f"react-vite, react-native, sveltekit, svelte-vite. {lead} mode REFRESH sebelum rute lain.")
    return (f"Profil `{PROFILE_DIR}` TIDAK LENGKAP, berkas hilang: {', '.join(p.missing)}. Berkas yang datanya "
            "nihil tetap wajib ada berisi `tidak terdeteksi`. "
            f"{lead} mode REFRESH sebelum rute lain.")


def render(v) -> str:
    head = f"Repo frontend, stack terdeteksi: {v.stack or 'tidak terbaca'} (sumber: {v.source}). Plugin `frontenddev` aktif."
    extra = [f"{h.path} → {h.stack}" for h in v.hits[1:4]]
    if extra:
        head += " Kandidat lain: " + "; ".join(extra) + " — pilih `target_app` di lead."
    return "\n\n".join(["<frontenddev-lead-gate>\n" + head, _profile_note(v), RULES + "\n</frontenddev-lead-gate>"])

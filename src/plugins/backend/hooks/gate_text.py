"""Teks gerbang SessionStart `backend`. Hanya teks — semua keputusan ada di `detect.py`."""

PROFILE_DIR = ".claude/profile/backenddev/"

RULES = """`backend:tech-lead` jalan lebih dulu untuk tiap permintaan kerja baru — panggil lewat tool Skill
sebelum skill backend lain, sebelum menelusuri repo, sebelum menulis kode. Gerbang sendiri yang
explore kodenya lalu bertanya; rute diputuskan sesudah itu, bukan sebelum.

WAJIB lewat gerbang:
- permintaan kerja: mengubah, menambah, memperbaiki, mengaudit, mendokumentasikan
- pertanyaan memahami kode — lewat jalur cepat read-only; tidak menuntut tree bersih atau branch
- susulan di tengah sesi, sekecil apa pun — "sekalian ganti X", "oh iya Y juga"
- menjalankan artefak backend yang sudah ada (brief, `TASK.md`, `RCA.md`) — apa pun statusnya

LEWATI hanya empat:
- jawaban user yang memasok informasi ke rute yang sudah diputuskan gerbang di giliran sebelumnya
- pertanyaan pengetahuan umum yang tidak menyentuh repo
- operasi VCS (commit, push, PR, rebase, diff) atas kerja yang sudah selesai
- permintaan yang memanggil atau melanjutkan alur plugin lain secara eksplisit — `/analyst:*`,
  `/quickdev:*`, atau susulan di tengah skill `analyst:*`/`quickdev:*` yang sedang berjalan
  (elisitasi tiket, `plan/<task>.md`). Kerja itu milik plugin tersebut sampai user sendiri meminta
  pindah ke gerbang ini.

Pengingat ini disuntik sekali per sesi, tidak diulang tiap giliran. Berlaku sama di permintaan ke-1
dan ke-40; jaraknya dari prompt yang sedang kamu baca bukan tanda ia kedaluwarsa."""


def _profile_note(v) -> str:
    p = v.profile
    if p.state == "OK" and p.location == "own":
        return (f"Profil `{PROFILE_DIR}` ADA. Isinya sengaja tidak disalin ke sini: skill yang "
                "membutuhkannya membaca berkasnya sendiri, supaya yang terbaca selalu versi terakhir.")
    if p.location == "legacy" and p.state in ("OK", "INCOMPLETE"):
        return ("Profil backend masih di lokasi lama `.claude/profile/`. Gerbang merutekan "
                f"`backend:profile` mode MIGRATE (pindah ke `{PROFILE_DIR}`) sebelum rute lain; "
                "dilarang REFRESH atau GENERATE di atasnya.")
    if p.state in ("ABSENT", "OTHER_OWNER"):
        note = (f"Profil `{PROFILE_DIR}` BELUM ADA. Permintaan kerja tetap lewat `backend:tech-lead`: "
                "pertanyaan baca-kode dijawab lewat jalur cepat read-only gerbang (terdegradasi, tanpa profil); "
                "rute yang mengubah kode dirutekan ke `backend:profile` (GENERATE) lebih dulu, lalu "
                "melanjutkan rute tertunda. Tawarkan `backend:profile` di giliran ini juga.")
        if p.state == "OTHER_OWNER":
            note += (f" `.claude/profile/` berisi profil milik `{p.owner}` (stack `{p.stack}`) — "
                     "biarkan; jangan dibaca sebagai profil backend, jangan ditimpa.")
        return note
    if p.state == "INVALID_JSON" and p.location == "legacy":
        return (f"Profil `{PROFILE_DIR}` BELUM ADA; `.claude/profile/index.json` lama bukan JSON valid dan "
                "tidak disentuh. Permintaan kerja tetap lewat `backend:tech-lead`; gerbang merutekan "
                "`backend:profile` (GENERATE) lebih dulu, lalu melanjutkan rute tertunda.")
    if p.state == "INVALID_JSON":
        return (f"`{PROFILE_DIR}index.json` bukan JSON valid; semua skrip prasyarat backend akan FAIL. "
                "Gerbang merutekan `backend:profile` mode REFRESH sebelum rute lain.")
    if p.state in ("NO_STACK", "UNKNOWN_STACK"):
        return (f"`{PROFILE_DIR}index.json` TIDAK SAH: field `stack` = `{p.stack or 'kosong'}`, di luar "
                "java-spring, go, node, bun, rust, php, php-codeigniter. Gerbang merutekan "
                "`backend:profile` mode REFRESH sebelum rute lain.")
    if p.state == "BAD_PLUGIN":
        return (f"`{PROFILE_DIR}index.json` TIDAK SAH: field `plugin` = `{p.owner}`, bukan `backend`. "
                "Gerbang merutekan `backend:profile` mode REFRESH sebelum rute lain.")
    return (f"Profil `{PROFILE_DIR}` TIDAK LENGKAP, berkas hilang: {', '.join(p.missing)}. "
            "Gerbang merutekan `backend:profile` mode REFRESH sebelum rute lain.")


def render(v) -> str:
    head = f"Repo backend, stack terdeteksi: {v.stack or 'tidak terbaca'} (sumber: {v.source}). Plugin `backend` aktif."
    extra = [f"{h.path} → {h.stack}" for h in v.hits[1:4]]
    if extra:
        head += " Kandidat lain: " + "; ".join(extra) + "."
    return "\n\n".join(["<backend-tech-lead-gate>\n" + head, _profile_note(v), RULES + "\n</backend-tech-lead-gate>"])

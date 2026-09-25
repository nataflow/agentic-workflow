# Rasional — `architect`

Alasan di balik aturan `SKILL.md` yang ditandai `> Rasional: … R<n>`. Dibaca hanya bila aturannya disengketakan atau hendak diubah; menjalankan skill tidak menuntut berkas ini.

## R1 — Fase 3 butir 3b — gerbang kompilasi per-brief

Mengapa: tanpa gerbang ini lantai slicing tidak punya penegak — brief yang menerbitkan import tak terselesaikan bertahan sampai build penutup, beberapa brief terlambat, dengan diagnosis yang sudah bercampur pekerjaan brief sesudahnya. Vonis relatif baseline mencegah repo yang sudah merah sejak awal (mis. `cargo check` merah karena `SQLX_OFFLINE` belum disiapkan, `profile/stacks/rust.md`) menghentikan rantai atas galat yang bukan milik brief mana pun.

## R2 — Fase 3 butir 4 — simbol, bukan hunk header

Mengapa bukan hunk header: driver diff bawaan git mengambil konteks dari baris tak-terindentasi terakhir di berkas **lama**, sehingga method Java/PHP/Kotlin/TS dan `fn` di `impl` Rust tercatat sebagai nama kelasnya, dan driver bahasa pun melekatkan perubahan signature serta method baru ke method sebelumnya.

## R3 — Fase 3 butir 4 — bandingkan simbol, bukan hanya berkas

Mengapa: perbandingan berkas saja meloloskan implementor yang menyunting simbol mana pun asalkan berkasnya terdaftar — bentuk kebocoran scope yang paling sering terjadi, karena satu berkas menampung banyak simbol.

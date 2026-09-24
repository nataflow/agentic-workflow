# Kerangka Dokumen API

Dibaca pada Fase 5 sebelum menulis `docs/api/<slug>.md`. Isi tiap placeholder dari hasil ekstraksi Fase 3; buang baris yang predikatnya kosong, jangan tulis "N/A".

```markdown
# API <Nama Domain>

> Dihasilkan dari kode di `src/`. Sumber kebenaran adalah kode, bukan dokumen ini.

## Ringkasan Endpoint

| Method | Path | Ringkasan | Auth | Sumber |
|---|---|---|---|---|
| `GET` | `/api/products` | Ambil daftar produk | `ROLE_USER` | `internal/product/handler.go:31` |

## `GET /api/products`

<ringkasan satu kalimat>

- **Auth**   : `ROLE_USER` — `internal/product/handler.go:29`
- **Sumber** : `internal/product/handler.go:31`

### Query Parameter

| Nama | Tipe | Wajib | Default | Aturan |
|---|---|---|---|---|
| `page` | `int` | tidak | `0` | minimal `0` |

### Path Parameter

| Nama | Tipe | Aturan |
|---|---|---|
| `id` | `Long` | identitas produk |

### Request Body — `ProductRequest`

| Field | Tipe | Wajib | Aturan validasi | Sumber |
|---|---|---|---|---|
| `name` | `string` | ya | wajib tidak kosong, maksimal 100 karakter | `internal/product/dto.go:14` |

```json
{
  "name": "Kopi Arabika 250g"
}
```

### Response `200 OK` — `ProductResponse`

| Field | Tipe | Keterangan | Sumber |
|---|---|---|---|
| `id` | `int64` | identitas produk | `internal/product/dto.go:29` |

```json
{
  "id": 1
}
```

### Error

| Status | Kode | Kondisi | Sumber |
|---|---|---|---|
| `404` | `PRODUCT_NOT_FOUND` | id tidak terdaftar | `internal/product/service.go:58` |

### Contoh

```bash
curl -X GET '<base-url>/api/products?page=0' \
  -H 'Authorization: Bearer <token>'
```

## Katalog Error

| Status | Kode | Makna | Sumber |
|---|---|---|---|
| `400` | `VALIDATION_ERROR` | payload gagal validasi | `internal/platform/httpx/error.go:41` |

## Catatan

- `UNVERIFIED: <butir>` — <alasan singkat mengapa tidak dapat dipastikan dari kode>
```

## Aturan Pengisian

- Seksi `Query Parameter`, `Path Parameter`, `Request Body`, dan `Contoh` ditulis hanya bila endpoint benar-benar memilikinya.
- Tabel `Request Body` dan `Response` wajib diikuti satu blok ```json contoh payload; nilainya diturunkan dari tipe dan aturan validasi kolom di atasnya, tidak disalin dari data nyata repo.
- Kolom `Sumber` wajib berisi `path/ke/Berkas:<line>`; tanpa bukti, tulis `UNVERIFIED` pada kolom itu dan catat alasannya di seksi `Catatan`.
- Seksi `Katalog Error` menggabungkan seluruh error unik lintas endpoint; error khusus satu endpoint tetap ditulis pada tabel endpoint itu.
- Seksi `Catatan` dilewati bila tidak ada butir `UNVERIFIED`.
- Saat mode UPDATE TERARAH, seksi buatan user di luar blok endpoint dan katalog error dipertahankan apa adanya.

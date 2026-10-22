# Process Boundary Review — Kriteria 8

Ruang lingkup: simulator lokal dan data sintetis. Tidak ada WhatsApp, Baileys, pairing, QR, gateway, perubahan ACL Windows, atau konfigurasi Hermes.

## Ringkasan status

| Area | Status | Bukti |
|---|---|---|
| Kontrak observer hanya menghasilkan event tersanitasi | LULUS (simulator) | `test_subprocess_observer_emits_only_sanitized_event` |
| Observer tidak mempunyai kemampuan send/reply/react/forward | LULUS (simulator) | `test_read_only_observer_has_no_delivery_methods` |
| Komponen pengiriman terpisah | TIDAK BERLAKU PADA SIMULATOR | Tidak ada komponen pengiriman; `DELIVERY_PATH_ENABLED = False` |
| Isolasi proses/akun layanan nyata | BELUM DIUJI | Tidak ada proses layanan atau akun yang dibuat |
| ACL filesystem, sandbox, dan kebijakan jaringan OS | BELUM DIUJI | Tidak ada ACL atau konfigurasi host yang diubah/diperiksa |

Kriteria 8 secara keseluruhan tetap BELUM DIUJI karena bukti isolasi runtime dan hak akses OS belum ada.

## 1. Batas proses yang dirancang

```text
SUBPROCESS LOKAL: observer
  input: event sintetis
  capability: observe_event
  output: JSON tersanitasi
  tidak memiliki: send/reply/react/forward
                |
                | stdout JSON lokal; bukan jaringan dan bukan IPC layanan
                v
PROSES TEST HARNESS
  memvalidasi bentuk payload dan ketiadaan teks mentah

JALUR PENGIRIMAN
  tidak dibuat pada simulator
  DELIVERY_PATH_ENABLED = False
  DELIVERY_CAPABILITIES = {}
```

Subprocess pada tes dipakai sebagai batas proses minimal: interpreter Python anak mengimpor simulator, memanggil `isolated_observer_payload()`, lalu hanya mencetak JSON hasil observer. Proses test induk membaca stdout untuk memverifikasi hasilnya. Tidak ada socket, HTTP, gateway, akun, atau koneksi eksternal.

## 2. Kemampuan tiap komponen

| Komponen | Kemampuan tersedia | Kemampuan yang tidak tersedia |
|---|---|---|
| `SyntheticReadOnlyObserver` | `observe_event(event)` | send, reply, react, forward, unduh media, preview URL |
| Pemroses sintetis | allowlist, kill switch, klasifikasi, reminder, TTL buffer | tool execution dari teks grup, penyimpanan sesi, jaringan |
| Test harness | membuat subprocess Python lokal dan membaca stdout | mengirim pesan atau membuat sesi akun |
| Jalur pengiriman | Tidak berlaku; tidak diimplementasikan | seluruh pengiriman/balasan/reaksi/penerusan |

## 3. Bukti observer tanpa fungsi pengiriman

`SyntheticReadOnlyObserver.capabilities` bernilai tepat `{"observe_event"}`. Tes `test_read_only_observer_has_no_delivery_methods` memeriksa bahwa instance tidak memiliki atribut berikut:

```text
send
reply
react
forward
```

Selain itu, `test_delivery_path_is_explicitly_disabled` memeriksa:

```text
DELIVERY_PATH_ENABLED == False
DELIVERY_CAPABILITIES == frozenset()
```

Ini adalah bukti kontrak interface simulator. Ini bukan bukti bahwa library atau adapter nyata tidak akan menyediakan API pengiriman; adapter nyata belum ada dan tidak dibuat dalam review ini.

## 4. Bukti subprocess menghasilkan event tersanitasi

Tes `test_subprocess_observer_emits_only_sanitized_event` menjalankan interpreter Python anak secara lokal. Event input sengaja memuat marker teks mentah sintetis. Child process memanggil:

```text
isolated_observer_payload(allowlist, event)
```

Helper tersebut hanya melakukan serialisasi JSON atas hasil `SyntheticReadOnlyObserver.observe_event()`. Tes membuktikan:

- stdout subprocess tidak memuat marker teks mentah;
- JSON hasil memiliki status keputusan observer;
- JSON hasil tidak memiliki field `text`;
- notifikasi hasil masih memiliki ID grup sintetis yang dibutuhkan untuk keputusan.

Status: LULUS (simulator).

## 5. Batas yang belum dapat diklaim

Status: BELUM DIUJI

Review ini tidak mengklaim hal-hal berikut:

- ACL Windows, izin folder, atau akun layanan terpisah;
- sandbox atau container proses;
- pemisahan process token/identity;
- firewall atau egress network policy tingkat OS;
- isolasi adapter WhatsApp nyata dari komponen pengiriman;
- ketahanan terhadap kompromi proses pada runtime produksi.

Tidak satu pun konfigurasi host diubah untuk review ini. Karena itu, bukti subprocess lokal tidak cukup untuk meluluskan kriteria 8 secara penuh.

## 6. Keputusan

- Kontrak observer dan sanitasi lintas subprocess lokal: LULUS.
- Jalur pengiriman pada simulator: TIDAK BERLAKU PADA SIMULATOR dan dinonaktifkan.
- Isolasi proses serta hak akses runtime: BELUM DIUJI.
- Kriteria 8 checklist: tetap BELUM DIUJI.

Koneksi nomor kedua tetap tidak diizinkan.

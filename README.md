# X Assistant - Tahap 1 (Simulator Lokal)

Simulator lokal untuk data sintetis. Tidak ada WhatsApp, pairing, QR scan, gateway, pemasangan paket, perubahan konfigurasi sistem, atau pesan sungguhan.

## Struktur
- `simulator.py` - logika dan demo simulator
- `data/allowlist.json` - allowlist grup dan `owner_dm` sintetis
- `data/synthetic_messages.json` - pesan sintetis
- `tests/test_simulator.py` - pengujian otomatis

## Menjalankan demo
```bash
python simulator.py
```

Contoh hasil utama:
- Pesan `Meeting jam 9. Reminder 5 menit sebelumnya dong.` menghasilkan acara `09:00` dan reminder `08:55`.
- DM owner sintetis dapat meminta rangkuman, reminder, dan opt-in memori.
- Demo memakai jawaban memori `tidak`; tidak ada ringkasan atau teks pesan yang disimpan.

## Tahap pilot satu grup (belum terhubung ke WhatsApp)

`pilot_core.py` adalah inti pemrosesan tanpa adapter WhatsApp, pairing QR, sesi, jaringan, atau pengiriman nyata.

- Hanya satu grup allowlist dan hanya pesan yang me-mention X yang masuk buffer RAM sementara (TTL 60 detik).
- Owner DM dapat meminta `ringkas` untuk memperoleh intent ringkasan bertopik (`Deadline`, `Rapat`, atau `Tindak lanjut`).
- Owner DM dapat memakai `ingatkan saya rapat jam 09:00, 5 menit sebelumnya`; hasilnya hanya intent reminder ke DM owner, bukan pesan sungguhan.
- Pesan grup di luar allowlist, pesan tanpa mention, dan DM non-owner diabaikan.

Untuk membuat manifest audit satu grup tanpa mengaktifkan gateway atau meminta QR:

```bash
cd pilot-config-validator
python -B setup_pilot.py --one-group
```

Masukkan hanya ID grup di terminal lokal. Jangan memasukkan OTP, QR, token, secret, atau file sesi lewat chat.

## Menjalankan semua pengujian
```bash
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s pilot-config-validator/tests -v
```

## Batas keamanan simulator
- Grup di luar allowlist diabaikan.
- Pesan tanpa mention tidak membuat notifikasi real-time.
- Seluruh pesan grup diperlakukan sebagai data; tidak dapat menjalankan tool, terminal, atau mengirim pesan.
- Hanya pengirim yang persis sama dengan `owner_dm` dapat meminta fitur DM owner.
- Contoh memori hanya memakai data sintetis, berada di RAM, dan hilang ketika proses selesai.
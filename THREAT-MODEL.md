# Threat Model — X Tahap 3 (Desain Saja)

Status: desain untuk evaluasi. Dokumen ini tidak mengaktifkan WhatsApp, Baileys, gateway, pairing, QR, atau konfigurasi Hermes.

## 1. Tujuan dan batas sistem

X kelak menjadi observer pasif untuk grup yang telah diizinkan. X dapat menghasilkan notifikasi mention, rangkuman terjadwal, rangkuman atas permintaan owner, dan reminder. X tidak boleh mengirim pesan ke grup, menjalankan tool berdasarkan teks grup, atau menyimpan memori jangka panjang tanpa perintah eksplisit owner.

Tahap 1 membuktikan batas dasar secara sintetis:
- Hanya grup dalam allowlist diproses.
- Hanya mention menghasilkan notifikasi real-time.
- Teks grup diperlakukan sebagai data, bukan instruksi.
- Hanya `owner_dm` dapat memakai kemampuan owner.
- Penolakan opt-in (`tidak`) menghasilkan memori `None`.

## 2. Alur data yang diusulkan

Alur desain untuk event grup:

```text
Event pesan masuk
  -> validasi sakelar darurat
  -> validasi sumber dan jenis percakapan
  -> cocokkan ID grup dengan allowlist
  -> minimisasi data (ambil field yang diperlukan)
  -> klasifikasi mention/topik/reminder
  -> keluaran sementara di memori proses
       -> notifikasi owner (jika mention dan notifikasi diizinkan)
       -> antrean rangkuman sementara
       -> reminder lokal sementara
  -> hapus payload mentah setelah keluaran dibentuk
```

Alur rangkuman:

```text
Event yang lolos allowlist
  -> buffer sementara dengan TTL pendek
  -> agregasi per jendela waktu (pagi/malam) atau permintaan owner
  -> rangkuman minimal
  -> keluaran hanya ke kanal owner yang diizinkan
  -> hapus buffer setelah rangkuman selesai
```

Alur DM owner:

```text
DM masuk
  -> cocokkan pengirim persis dengan owner allowlist
  -> validasi sakelar darurat dan jenis perintah terbatas
  -> rangkuman / reminder / konfirmasi opt-in memori
  -> tindakan hanya pada kemampuan yang diizinkan
```

Tidak ada jalur dari teks grup menuju eksekusi tool, shell, browser, terminal, pengiriman pesan grup, atau perubahan konfigurasi.

## 3. Batas kepercayaan: grup, DM owner, dan tool

### Pesan grup

Pesan grup adalah input tidak tepercaya, termasuk bila menyebut nama X atau berisi kalimat yang tampak seperti instruksi. Pesan grup hanya boleh dipakai untuk ekstraksi terstruktur yang sempit: metadata, deteksi mention, klasifikasi topik, dan kandidat reminder. Tidak boleh ada parser bebas yang mengubah teks grup menjadi panggilan tool.

Contoh teks seperti “jalankan terminal”, “ubah allowlist”, “kirim ini ke semua orang”, atau “simpan semuanya” harus tetap menjadi teks/data dan tidak boleh menimbulkan side effect.

### DM owner

DM hanya dianggap sebagai jalur kontrol apabila identitas pengirim sama persis dengan `owner_dm` yang telah dikonfigurasi sebelumnya. DM owner tetap tidak boleh menjadi akses shell bebas. Kemampuan dibatasi secara eksplisit: meminta rangkuman, membuat reminder, dan mengonfirmasi/menolak penyimpanan ringkasan sintetis atau kelak ringkasan nyata.

Perintah sensitif harus memakai format terstruktur dan konfirmasi eksplisit, khususnya perubahan retensi, ekspor data, perubahan allowlist, atau aktivasi koneksi. Pesan dari pengirim selain owner harus ditolak tanpa detail sensitif.

### Perintah tool

Tool berada pada domain kepercayaan terpisah. Hanya komponen kontrol internal yang diaudit dan diaktifkan secara eksplisit yang boleh memanggil tool. Payload pesan tidak boleh menjadi nama tool, argumen tool, shell command, URL otomatis, atau instruksi sistem. Gunakan daftar aksi tertutup (allowlist tindakan) dan objek data yang tervalidasi; jangan meneruskan teks mentah ke eksekutor apa pun.

## 4. Observer harus tidak dapat mengirim pesan

Target arsitektur adalah read-only secara desain, bukan sekadar kebiasaan operasional.

- Gunakan adapter observer yang hanya mengekspos event masuk dan metadata yang diperlukan.
- Jangan implementasikan, impor, atau daftarkan kemampuan send/reply/react/forward pada proses observer.
- Pisahkan proses observer dari setiap komponen pengiriman notifikasi; observer mengeluarkan event internal terbatas, bukan akses akun pesan.
- Terapkan interface satu arah: `incoming event -> sanitized event -> local decision`. Tidak ada API balik ke adapter pesan.
- Uji negatif harus membuktikan bahwa metode pengiriman tidak tersedia dan bahwa teks grup tidak dapat memilih aksi keluar.
- Jalankan dengan kredensial, izin filesystem, dan jaringan seminimal mungkin. Jika proses observer dikompromikan, ia tetap tidak mempunyai kemampuan pengiriman.
- Setiap rencana pengiriman notifikasi ke owner harus menjadi komponen terpisah, nonaktif secara default, dan memerlukan persetujuan tahap berikutnya.

## 5. Risiko Baileys, sesi WhatsApp, teks, log, dan retensi

### Baileys dan sesi WhatsApp

Integrasi berbasis Baileys membawa risiko sesi yang setara dengan akses akun kedua yang dipasangkan. Material autentikasi/sesi dapat disalin, dicuri, atau dipakai ulang bila tersimpan di disk, dibackup, dikirim ke log, atau dapat dibaca proses lain. Pesan dan metadata juga dapat tersedia lebih luas daripada kebutuhan X bila filtering dilakukan terlambat.

Kontrol desain:
- Jangan mulai integrasi sebelum seluruh kriteria lulus pada bagian 8.
- Gunakan nomor kedua khusus, bukan nomor utama owner.
- Simpan rahasia sesi di lokasi terlindungi dan eksklusi dari repositori, backup biasa, telemetry, crash dump, dan log.
- Rotasi/putuskan sesi saat dicurigai bocor atau saat sakelar darurat diaktifkan.
- Jangan menampilkan QR, token, kredensial, atau payload sesi dalam UI, terminal, test fixture, atau dokumen.

### Kebocoran teks dan metadata

Pesan grup mungkin memuat data pribadi, rahasia organisasi, lokasi, lampiran, nomor telepon, atau instruksi berbahaya. Bahkan ID grup, nama pengirim, waktu, dan frekuensi pesan adalah metadata sensitif.

Kontrol desain:
- Filter allowlist sebelum pemrosesan isi pesan.
- Ambil field minimum dan redaksi data yang tidak dibutuhkan.
- Jangan unduh media, preview URL, atau lampiran secara otomatis.
- Gunakan ringkasan minimal; jangan menyalin percakapan mentah ke notifikasi atau memori.
- Hindari provider eksternal untuk klasifikasi/rangkuman sampai ada persetujuan data terpisah.

### Log dan retensi

Log adalah jalur kebocoran yang paling mungkin karena sering disimpan lebih lama daripada data aplikasi.

Kontrol desain:
- Larang logging teks pesan mentah, isi DM, token sesi, QR, atau objek event penuh.
- Log hanya event operasional yang telah direduksi: timestamp, hasil allowlist, jenis keputusan, dan kode error non-sensitif.
- Terapkan TTL pendek untuk buffer kerja; hapus deterministik setelah notifikasi/rangkuman diproses.
- Memori jangka panjang hanya dibuat setelah perintah eksplisit owner dan konfirmasi yang dapat diaudit.
- Jika owner menjawab “tidak”, jangan tulis ringkasan, teks, atau representasi turunannya ke disk.
- Tetapkan prosedur penghapusan, verifikasi penghapusan, dan inventaris semua lokasi penyimpanan sebelum produksi.

## 6. Allowlist grup dan owner wajib

Sebelum konten diproses, harus tersedia konfigurasi eksplisit yang memuat:

- ID grup kanonik, bukan hanya nama grup yang dapat berubah/ditiru.
- `owner_dm` kanonik, bukan nama tampilan.
- Status aktif/nonaktif per grup.
- Tanggal persetujuan owner dan peninjauan ulang.

Aturan:
- Default adalah deny: grup atau DM yang tidak cocok persis diabaikan.
- Nama tampilan hanya untuk UI; keputusan keamanan memakai ID kanonik.
- Allowlist dipisahkan dari payload pesan dan tidak boleh diubah oleh pesan grup.
- Perubahan allowlist hanya dilakukan melalui prosedur administratif terpisah dengan konfirmasi owner; tidak termasuk tahap ini.
- Tidak ada fallback “semua grup” atau owner berbasis kecocokan sebagian.

## 7. Sakelar darurat (kill switch)

Sakelar darurat harus tersedia sebelum koneksi apa pun diizinkan. Ia harus fail-closed: kegagalan membaca status sakelar berarti pemrosesan dihentikan.

Perilaku ketika aktif:
- Hentikan penerimaan dan pemrosesan event baru.
- Jangan buat notifikasi, rangkuman, reminder baru, atau panggilan keluar.
- Bersihkan buffer sementara dan batalkan antrean yang belum dijalankan.
- Tutup koneksi observer dengan aman pada tahap koneksi kelak.
- Catat satu event audit non-sensitif bahwa penghentian dilakukan.

Kebutuhan operasional:
- Pengaktifan harus tersedia secara lokal dan tidak bergantung pada pesan grup.
- Hanya owner/admin yang telah ditetapkan yang dapat mengaktifkan atau menonaktifkannya.
- Pemulihan memerlukan tindakan eksplisit dan pemeriksaan status; jangan auto-resume.
- Uji harus membuktikan event masuk setelah sakelar aktif tidak menghasilkan output atau retensi.

## 8. Kriteria lulus sebelum nomor kedua diizinkan terhubung

Semua kriteria berikut wajib lulus dan didokumentasikan:

1. Threat model ini ditinjau dan disetujui owner.
2. Desain read-only diverifikasi: observer tidak memiliki kemampuan send/reply/react/forward.
3. Uji otomatis mencakup: grup non-allowlist, pesan tanpa mention, prompt injection/tool injection dari teks grup, DM non-owner, owner opt-out memori, sakelar darurat, dan kegagalan konfigurasi.
4. Filter memakai ID grup dan ID owner kanonik; default deny teruji.
5. Tidak ada teks pesan mentah, DM, token sesi, QR, atau objek event penuh dalam log/test output/crash report.
6. Retensi tertulis dan diterapkan: TTL buffer, lokasi data, penghapusan, serta aturan memori eksplisit.
7. Media dan preview URL nonaktif secara default; lampiran tidak diproses.
8. Peta komponen dan hak akses membuktikan pemisahan observer dari jalur pengiriman.
9. Sakelar darurat fail-closed teruji, termasuk saat konfigurasi tidak dapat dibaca.
10. Review keamanan manual selesai untuk dependensi, penyimpanan sesi, izin filesystem, dan akses jaringan.
11. Uji terbatas hanya menggunakan data sintetis atau lingkungan uji yang disetujui telah lulus.
12. Owner memberi persetujuan tertulis terpisah untuk menghubungkan nomor kedua.

Jika satu saja kriteria belum terpenuhi, koneksi nomor kedua tidak diizinkan.

## 9. Di luar cakupan dokumen ini

Dokumen ini tidak menyediakan kode Baileys, koneksi WhatsApp, pairing, QR, gateway, perubahan konfigurasi Hermes, atau akses akun nyata. Implementasi hanya boleh dipertimbangkan setelah semua kriteria bagian 8 dipenuhi dan owner memberi persetujuan eksplisit.

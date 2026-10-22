# Rencana Bootstrap Discovery untuk satu ID grup WhatsApp

## Status dan batas keras

Dokumen ini adalah rencana operasional, bukan instruksi untuk menjalankan Hermes sekarang.

Pada pemeriksaan CLI dan dokumentasi Hermes saat ini, tidak ada mode WhatsApp yang terdokumentasi untuk mengambil metadata grup saja tanpa menyalakan bridge/gateway. Karena itu, discovery hanya boleh diteruskan bila operator dapat menyediakan lingkungan bootstrap yang benar-benar membatasi koneksi ke pengambilan metadata grup dan dapat membuktikan kontrol di bawah. Bila tidak, berhenti dan gunakan WhatsApp Web/Desktop atau prosedur resmi organisasi untuk memperoleh ID grup secara manual.

Dilarang dalam bootstrap ini:

- menjalankan gateway Hermes penuh;
- mengirim, membalas, react, forward, atau membuat pesan apa pun;
- meneruskan pesan masuk ke model, agent, tool, terminal, webhook, atau log aplikasi;
- mengunduh atau menyimpan media/lampiran;
- menyimpan QR, token, kredensial, atau direktori sesi di laporan, repositori, atau manifest pilot;
- memakai lebih dari satu grup untuk discovery.

## Prasyarat sebelum pairing

1. Gunakan nomor bot khusus, bukan akun pribadi atau akun produksi.
2. Pastikan grup testing sudah ada, operator berwenang melihat metadata grup, dan scope hanya satu grup itu.
3. Siapkan lingkungan bootstrap sementara dan terisolasi dari profil Hermes aktif, konfigurasi Hermes aktif, direktori sesi Hermes, serta folder proyek.
4. Siapkan aturan egress minimum: hanya endpoint WhatsApp yang diperlukan untuk pairing dan lookup metadata; blokir webhooks, tool gateway lain, dan semua tujuan jaringan yang tidak diperlukan.
5. Tetapkan batas waktu singkat untuk sesi bootstrap dan kill switch lokal yang memutus proses dan jaringan bootstrap.
6. Siapkan pencatat hasil minimal yang hanya menerima satu nilai dengan pola `...@g.us`. Pencatat harus menolak nama grup, nomor peserta, subject/deskripsi grup, isi chat, media, token, QR, dan data sesi.
7. Tetapkan bukti keberhasilan yang boleh dicatat: `DISCOVERY_OK`, format ID valid, jumlah ID = 1, dan waktu penghentian sesi. Jangan catat nilai ID lengkap di laporan umum.

Jika salah satu prasyarat tidak dapat dipenuhi atau diverifikasi, jangan melakukan pairing.

## Pembatasan sesi bootstrap

Jika dan hanya jika alat yang dipakai mendukung pemisahan tersebut, sesi bootstrap harus dijalankan dengan profil/direktori sementara yang baru dan kosong.

Kontrol wajib:

- Tidak memuat konfigurasi pilot Hermes, `.env` Hermes, sesi lama, atau plugin/toolset agent.
- Tidak memulai gateway service, worker, webhook listener, cron, atau proses otomatis lain.
- Tidak ada route inbound ke agent/model. Semua event pesan harus dibuang sebelum batching, transkripsi, parsing command, atau dispatch tool.
- Tidak ada penyimpanan transcript, cache pesan, cache media, database percakapan, atau log event mentah.
- Read receipt, typing indicator, presence update, URL preview, media download, attachment handling, dan semua tindakan outbound harus nonaktif.
- Kebijakan outbound harus default-deny pada transport. Tidak cukup hanya mengandalkan instruksi model atau prompt.
- Batas data yang diizinkan dari adapter: hanya metadata minimal yang diperlukan untuk mengidentifikasi satu grup; tidak boleh mengambil riwayat atau isi pesan.

Bila adaptor tidak dapat membuktikan kontrol-kontrol tersebut secara teknis, bootstrap tidak aman dan harus dibatalkan.

## Urutan discovery lokal

1. Operator memulai lingkungan bootstrap terisolasi secara lokal, bukan gateway Hermes.
2. Operator melakukan pairing hanya pada lingkungan tersebut dan tidak menyalin QR, token, atau data sesi ke chat, file proyek, atau laporan.
3. Setelah tersambung, alat hanya meminta metadata grup yang sudah ditentukan dalam scope.
4. Filter lokal memvalidasi bahwa hasilnya tepat satu string berakhiran `@g.us` dan menolak semua field lain.
5. Simpan ID itu hanya di penyimpanan lokal berizin sempit atau input no-echo ke manifest pilot lokal yang gitignored. Jangan menaruhnya di `config.yaml` Hermes, README, issue tracker, transcript, atau commit.
6. Tulis status tereduksi saja, misalnya: `group_id_collected=true`, `group_id_format_valid=true`, `group_count=1`, `session_terminated=true`. Jangan tampilkan ID lengkap.
7. Hentikan proses bootstrap segera setelah ID tervalidasi; cabut akses jaringan bootstrap dan unlink perangkat dari WhatsApp bila sesi masih terdaftar.
8. Hapus direktori sesi sementara, QR sementara, token, cache, dan log bootstrap menggunakan prosedur penghapusan lokal yang sesuai. Verifikasi bahwa artefak tidak berada di folder proyek atau Hermes home.

## Penghentian segera dan kondisi gagal

Hentikan bootstrap sebelum atau sesudah pairing bila terjadi salah satu hal berikut:

- alat mulai membaca, menampilkan, menyimpan, atau meneruskan isi pesan;
- proses mencoba mengirim outbound, read receipt, presence, react, atau typing;
- lebih dari satu grup masuk ke hasil;
- ada agent/tool/terminal/webhook yang menerima event WhatsApp;
- sesi tidak dapat dipisahkan dari gateway Hermes atau direktori sesi normal;
- artefak sesi tidak dapat dihapus atau perangkat tidak dapat di-unlink;
- validator pilot penuh belum dapat memverifikasi kontrol dasar dan bootstrap tidak dapat membuktikan isolasi sendiri.

Dalam setiap kondisi tersebut, hasil discovery dianggap tidak dapat dipercaya dan tidak boleh dipakai untuk mengaktifkan pilot.

## Risiko tambahan: pairing sebelum validator pilot penuh lulus

Pairing sendiri membuat kredensial sesi yang dapat memberi akses penuh sebagai perangkat tertaut. Karena validator pilot penuh belum lulus, belum ada bukti bahwa allowlist, sender authorization, default-deny, kill switch, retensi, isolasi proses, filesystem permissions, dan egress policy efektif pada runtime.

Akibatnya, pairing lebih awal membawa risiko berikut:

- sesi bootstrap dapat dipakai kembali secara tidak sengaja oleh gateway atau proses lain;
- event pesan dapat masuk ke log, cache, atau pipeline agent sebelum filter berlaku;
- konfigurasi atau override efektif dapat berbeda dari manifest pilot lokal;
- perangkat tertaut dapat bertahan setelah discovery dan memperluas permukaan serangan;
- ID grup yang benar tidak membuktikan bahwa pilot aman untuk menerima atau mengirim pesan.

Mitigasi minimum adalah profil sementara terpisah, data minimum, outbound default-deny yang ditegakkan oleh transport, kill switch, penghapusan sesi terverifikasi, dan unlink perangkat segera. Jika mitigasi tersebut tidak dapat dibuktikan, jangan pairing; gunakan pengambilan ID manual di WhatsApp Web/Desktop atau prosedur resmi organisasi.

## Kriteria selesai

Discovery dianggap selesai hanya jika:

- tepat satu ID berformat `@g.us` diperoleh secara lokal;
- tidak ada isi pesan/media yang diproses atau disimpan;
- tidak ada tindakan outbound;
- tidak ada gateway Hermes yang dijalankan;
- sesi bootstrap sudah dihentikan, perangkat di-unlink bila perlu, dan artefak sesi dihapus;
- hasil dicatat hanya sebagai status tereduksi atau disimpan lokal pada manifest pilot terpisah.

Mendapatkan ID grup bukan persetujuan untuk menjalankan pilot. Pilot tetap terblokir sampai validator dan isolasi runtime terverifikasi secara terpisah.

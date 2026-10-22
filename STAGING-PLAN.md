# Rencana staging kriteria 8 — belum dijalankan

Status: RENCANA TERSEDIA; kriteria 8 tetap BELUM DIUJI. Dokumen ini bukan persetujuan untuk mengaktifkan koneksi atau mengubah host. Lingkup pembuktian awal hanya data sintetis; tidak ada akun, sesi, nomor kedua, WhatsApp, Baileys, pairing, QR, maupun gateway. Acuan: `THREAT-MODEL.md` bagian 4, 7, 8; `PROCESS-BOUNDARY-REVIEW.md`; `CHECKLIST-STATUS.md`.

## 1. Lingkungan dan batas proses yang perlu disiapkan kelak

- Gunakan mesin/VM staging khusus yang terpisah dari komputer pribadi dan profil Hermes. Snapshot bersih sebelum uji. Tidak boleh diberi kredensial, sesi, atau data chat nyata. Persetujuan owner diperlukan sebelum menyiapkan lingkungan atau menjalankan uji.
- Jalankan observer stub sintetis sebagai proses tersendiri dengan identitas non-admin khusus; pemroses sintetis sebagai proses/identitas lain. Tidak ada proses pengiriman yang berjalan. Bila perlu membuktikan pemisahannya, gunakan stub penerima *lokal* yang tidak punya API jaringan atau kredensial pengiriman.
- Kontrak satu arah: observer menerima event sintetis, memvalidasi allowlist dan kill switch, lalu hanya menyerahkan event tereduksi melalui saluran lokal terbatas ke pemroses. Tidak ada kanal balik dari pemroses ke observer yang dapat meminta pengiriman.
- Tes subprocess saat ini (`test_subprocess_observer_emits_only_sanitized_event`) hanya membuktikan stdout tereduksi; belum membuktikan identitas proses, sandbox, atau ACL. Jangan menyamakan hasil tes itu dengan isolasi runtime.

## 2. Hak filesystem minimum yang akan diverifikasi

| Identitas | Kebutuhan yang direncanakan | Larangan dan bukti uji yang diperlukan |
|---|---|---|
| Observer stub | Baca hanya executable/runtime dan fixture allowlist serta event sintetis yang diperlukan; output tereduksi ke saluran lokal sementara. | Tidak boleh menulis kode, konfigurasi, fixture, log berisi payload, direktori home/Hermes, atau lokasi sesi. Bukti: inspeksi hak efektif dan percobaan tulis yang ditolak di VM staging. |
| Pemroses sintetis | Baca event tereduksi; buffer di RAM dengan TTL; tulis hanya artefak tes tereduksi bila memang diperlukan. | Tidak boleh membaca input mentah observer atau direktori sesi/kredensial. Bukti: uji akses negatif dan inventaris file sebelum/sesudah uji. |
| Stub pengiriman (jika diuji) | Tidak ada izin; proses tidak dijalankan. | Buktikan tidak ada jalur menuju API pengiriman, antrean keluar, atau kredensial. |
| Operator staging | Akses administratif hanya untuk menyiapkan/mengaudit VM terisolasi. | Perubahan izin harus dicatat dan dikembalikan ke snapshot; jangan mengubah ACL Windows host pengguna. |

Default deny: bila izin tidak dapat diperiksa, konfigurasi tidak terbaca, atau identitas proses tidak sesuai, uji dihentikan tanpa memproses event.

## 3. Kebijakan jaringan minimum yang akan diverifikasi

- Untuk uji sintetis, observer dan pemroses tidak memerlukan koneksi keluar atau masuk. Matikan seluruh egress/ingress pada VM staging untuk kedua proses; saluran antarkomponen hanya lokal, dengan akses berdasarkan identitas proses.
- Jangan memakai domain, server, akun, atau jaringan WhatsApp sebagai target uji. Tes penolakan akses jaringan harus menuju endpoint uji yang dikendalikan di VM terisolasi, bukan internet/layanan nyata; catat hasil tolaknya tanpa payload.
- Periksa aturan efektif (bukan hanya nilai konfigurasi), koneksi proses, dan kegagalan percobaan koneksi. Jika aturan tidak dapat diverifikasi, status tetap BELUM DIUJI dan hentikan uji.
- Bila kelak ada usulan koneksi nyata, kebijakan jaringan wajib didesain dan disetujui ulang secara terpisah; rencana ini tidak mengizinkannya.

## 4. Verifikasi observer tidak dapat mengirim

1. Audit kontrak stub dan modul yang dimuat: hanya `observe_event`; tidak ada `send`, `reply`, `react`, `forward`, klien pengiriman, atau referensi antrean keluar. Pertahankan tes `test_read_only_observer_has_no_delivery_methods`.
2. Beri input sintetis yang mengandung permintaan eksplisit mengirim/membalas/bereaksi/meneruskan atau menjalankan tool. Pastikan hanya keputusan tereduksi yang keluar; tidak ada aksi/tool call. Pertahankan tes sanitasi subprocess.
3. Uji batas OS pada VM staging: proses observer tidak memperoleh izin menulis ke lokasi pengiriman/sesi, tidak dapat mengakses stub pengiriman, dan tidak bisa membuat sambungan jaringan. Catat identitas proses, hak efektif, penolakan akses, dan observasi egress.
4. Verifikasi dari sisi penerima stub bahwa jumlah pesan/aksi keluar tetap nol. Kegagalan salah satu kontrol berarti GAGAL; bukti interface saja tidak cukup untuk menyatakan kriteria 8 LULUS.

## 5. Rollback dan kill switch

- Sebelum pengujian, ambil snapshot VM bersih, inventaris izin/aturan jaringan dan file, serta definisikan penanggung jawab penghentian. Jangan membuat snapshot yang memuat rahasia atau pesan nyata.
- Kill switch lokal harus fail-closed: saat aktif atau statusnya tidak terbaca, hentikan event baru, kosongkan antrean/buffer RAM, dan jangan mengeluarkan notifikasi/reminder/aksi. Uji lewat event sintetis sebelum dan sesudah sakelar, termasuk saat konfigurasinya gagal dibaca.
- Jika ada kegagalan atau kebocoran: hentikan seluruh proses staging, blokir saluran lokal/egress pada VM, simpan hanya bukti audit tereduksi, verifikasi buffer/antrean kosong, lalu kembalikan VM ke snapshot bersih. Jangan auto-resume.
- Pemulihan hanya setelah peninjauan insiden dan persetujuan eksplisit owner; jalankan ulang tes dari awal. Karena tidak ada sesi/akun dalam rencana sintetis, tidak ada sesi nyata yang perlu diputus pada tahap ini.

## 6. Data sintetis

- Gunakan fixture `data/allowlist.json` dan `data/synthetic_messages.json` yang berisi ID sintetis, ditambah kasus uji negatif: grup bukan allowlist, DM bukan owner, tanpa mention, media/lampiran/URL sintetis, teks instruksi berbahaya, allowlist rusak, dan sakelar aktif.
- Gunakan marker payload buatan untuk mendeteksi kebocoran lintas proses. Output yang boleh disimpan: status, ID sintetis, waktu simulasi, kategori, keputusan, dan hitungan; tanpa teks mentah, isi DM, token, QR, atau event lengkap.
- Tidak membaca akun/chat pribadi; tidak mengunduh media atau membuka URL.

## 7. Bukti wajib sebelum nomor kedua boleh *dipertimbangkan* untuk pairing

- Persetujuan owner atas threat model dan rencana staging, disimpan terpisah dari artefak teknis.
- Versi artefak yang diuji, diagram proses aktual, identitas proses, matriks hak efektif, dan log penolakan akses filesystem/jaringan dari VM staging (semuanya tereduksi).
- Hasil suite tes sintetis lengkap, tes subprocess sanitasi, tes injeksi/pengiriman negatif, bukti egress ditolak, serta counter aksi keluar = 0.
- Bukti kill switch fail-closed, pembersihan buffer/TTL, rollback snapshot, dan tidak ada sesi/kredensial atau payload mentah dalam file/log/output.
- Review manual oleh owner/peninjau atas bukti di atas dan status setiap kriteria 1–11. Kriteria 8 tidak menjadi LULUS sampai isolasi proses dan hak akses runtime benar-benar dijalankan serta diverifikasi; kriteria lain yang masih BELUM DIUJI juga harus ditutup.
- Setelah semua prasyarat lulus, tetap diperlukan persetujuan tertulis owner yang *terpisah* untuk pairing nomor kedua (kriteria 12). Persetujuan staging tidak sama dengan persetujuan pairing.

## 8. Titik persetujuan eksplisit owner

| Titik keputusan | Persetujuan yang diperlukan |
|---|---|
| Menyiapkan VM staging terisolasi, identitas proses, izin, kebijakan jaringan, atau menjalankan uji di sana | Ya; belum diminta atau diberikan oleh dokumen ini. |
| Mengubah ACL/kebijakan jaringan di VM staging yang disetujui | Ya, dengan cakupan dan rencana rollback tertulis; ACL/config Windows host pengguna tetap di luar cakupan. |
| Menyimpan atau membagikan artefak hasil audit | Ya; hanya data tereduksi dan lokasi/retensi yang disepakati. |
| Mengaktifkan kembali proses setelah kill switch/insiden | Ya, setelah review dan verifikasi ulang. |
| Menambahkan konektor, kredensial, akun, gateway, atau jaringan nyata | Persetujuan proyek terpisah; tidak tercakup dalam rencana sintetis ini. |
| Memasangkan nomor kedua | Persetujuan tertulis owner terpisah setelah seluruh kriteria 1–11 lulus. |

Tidak ada langkah rencana ini yang dijalankan saat dokumen dibuat. Status kriteria 8: BELUM DIUJI; rencana tersedia, bukan bukti lulus.

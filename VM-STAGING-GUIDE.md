# Panduan staging Windows Sandbox / VM terpisah — BELUM DIJALANKAN

Tujuan: menjalankan `STAGING-PLAN.md` hanya dengan simulator dan data sintetis untuk mengumpulkan bukti kriteria 8. Panduan ini bukan izin untuk memasangkan nomor kedua. Jangan gunakan WhatsApp, akun, kredensial, gateway, QR, atau data pribadi. Jangan mengubah ACL Windows host atau konfigurasi Hermes. Persetujuan eksplisit owner diperlukan **sebelum** menyiapkan/menjalankan staging, mengubah kebijakan *guest*, mengekspor bukti, atau memulihkan proses setelah penghentian.

**Batas klaim:** Windows Sandbox cukup untuk tes fungsional dalam guest sementara, tetapi user bawaan Sandbox bukan bukti identitas observer non-admin yang terpisah dari pemroses. Untuk menguji dua identitas proses, ACL efektif, dan segmentasi jaringan dengan sungguh-sungguh, gunakan VM khusus dengan akun lokal *guest* yang berbeda dan haknya diaudit. Jangan menandai kriteria 8 LULUS hanya dari 21 tes atau konfigurasi Sandbox.

## 0. Prasyarat dan keputusan berhenti

1. Dapatkan persetujuan owner untuk pengujian sintetis dan cakupan guest. Pilih **Sandbox yang sudah tersedia** atau **VM khusus offline**. Jika Sandbox belum tersedia, jangan aktifkan fitur Windows di host hanya demi panduan ini; gunakan VM yang telah disetujui atau berhenti.
2. Pastikan interpreter Python yang sesuai tersedia **di guest**, dari sumber offline yang disetujui; Windows Sandbox tidak boleh diasumsikan membawa Python host. Jangan menghubungkan guest ke internet untuk memasang paket. Simulator memakai pustaka standar saja. Jika Python tidak tersedia, berhenti; jangan melonggarkan isolasi.
3. Penanggung jawab menghentikan uji harus ditentukan; catat lokasi penyimpanan bukti tereduksi dan masa retensinya sebelum mulai. Kegagalan prasyarat apa pun = berhenti, status BELUM DIUJI.

## 1. Siapkan lingkungan bersih (langkah masa depan, bukan dijalankan sekarang)

**Opsi A — Windows Sandbox:**

1. Gunakan folder ekspor khusus `C:\StagingExport` yang **hanya** berisi empat file pada langkah 2, bukan seluruh home/profil Hermes. Setelah persetujuan, gunakan konfigurasi `.wsb` terpisah di host (contoh di bawah); jangan menjalankan Sandbox dengan default, karena jaringan dan clipboard default dapat aktif. `HostFolder` harus sudah ada dan mapping harus read-only. Jangan masukkan logon command otomatis. Pastikan tidak ada file sensitif di folder ekspor.
2. Contoh konfigurasi yang *baru akan dibuat/dibuka setelah persetujuan*:

```xml
<Configuration>
  <Networking>Disable</Networking>
  <ClipboardRedirection>Disable</ClipboardRedirection>
  <PrinterRedirection>Disable</PrinterRedirection>
  <AudioInput>Disable</AudioInput>
  <VideoInput>Disable</VideoInput>
  <VGpu>Disable</VGpu>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>C:\StagingExport</HostFolder>
      <SandboxFolder>C:\StagingInput</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
</Configuration>
```

3. Di dalam guest, salin empat file dari `C:\StagingInput` ke direktori kerja guest `C:\Stage` (pertahankan subfolder `data` dan `tests`). Jalankan tes hanya dari `C:\Stage`. Jangan map workspace proyek/home host secara langsung. Jika mapping atau pengaturan isolasi tidak bekerja, tutup guest dan berhenti.
4. Sandbox bersifat sementara: tutup jendelanya untuk membuang isi guest. Ia **bukan** pengganti snapshot VM atau bukti dua identitas layanan terpisah.

**Opsi B — VM khusus:**

1. Buat/pilih VM Windows staging yang disetujui, terpisah dari host, tanpa akun/kredensial nyata; putuskan NIC eksternal, shared folder, clipboard, drag-and-drop, dan integrasi host yang tidak perlu.
2. Ambil snapshot baseline bersih **sebelum** membawa fixture; catat identitas snapshot. Siapkan Python offline yang telah disetujui dan dua identitas non-admin *lokal guest* yang terpisah bila ingin menguji pemisahan observer/pemroses. Perubahan ACL hanya di guest dengan persetujuan owner; jangan ubah host.
3. Transfer salinan empat file sintetis melalui media offline yang dibatasi; salin ke `C:\Stage` di guest. Jangan transfer sesi, profil Hermes, token, QR, riwayat chat, atau log host.

Sumber teknis konfigurasi Sandbox: dokumentasi Microsoft Learn “Use and configure Windows Sandbox” dan “Windows Sandbox sample configuration files”.

## 2. Inventaris data yang boleh disalin

Salin hanya:

```text
simulator.py
tests\test_simulator.py
data\allowlist.json
data\synthetic_messages.json
```

`allowlist.json` memakai ID grup/owner sintetis; `synthetic_messages.json` berisi pesan buatan. Tes menambah kasus buatan untuk grup tak diizinkan, DM bukan owner, tanpa mention, prompt-injection, media/lampiran/URL dummy, TTL, dan kill switch. Jangan salin `__pycache__`, file konfigurasi/sesi, atau data pribadi. Verifikasi daftar file guest sama dengan empat file itu; catat hash empat file *di guest* dan versi Python. Jangan tulis isi fixture ke laporan bukti.

## 3. Jalankan 21 tes di dalam guest

Buka PowerShell **di guest**, dari `C:\Stage` (bukan terminal host). Setelah memeriksa `python --version`:

```powershell
Set-Location C:\Stage
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m unittest discover -s tests -v
```

Target baseline: `Ran 21 tests` dan `OK`, termasuk `test_subprocess_observer_emits_only_sanitized_event`, `test_read_only_observer_has_no_delivery_methods`, `test_kill_switch_blocks_all_group_processing`, serta reminder `08:55`. Bila jumlah tes berubah atau ada FAIL/ERROR, hentikan dan catat deviasi; jangan mengklaim lulus. `unittest` memakai direktori sementara di guest; inventaris jejaknya sebelum/sesudah pengujian. Simpan hanya nama tes, status, jumlah, dan ringkasan tereduksi; jangan salin traceback yang mungkin memuat payload mentah.

## 4. Uji batas proses dan identitas (guest saja)

1. Untuk setiap proses observer stub, pemroses, dan harness, catat PID, executable, parent PID, SID/user, grup dan privilege token. Jalankan `whoami /user`, `whoami /groups`, `whoami /priv` **dalam konteks masing-masing proses guest**; inventaris proses dengan alat guest seperti `Get-CimInstance Win32_Process`. `whoami` di shell operator saja tidak membuktikan identitas child process.
2. Cocokkan PID dan identitas pada saat proses hidup. Verifikasi observer dan pemroses memakai identitas non-admin guest berbeda di opsi VM, bukan sekadar dua subprocess di bawah akun yang sama. Bila tidak bisa membedakan identitas, tandai subkriteria ini BELUM DIUJI.
3. Verifikasi jalur satu arah observer → event tersanitasi → pemroses. Tes subprocess yang tersedia hanya menampilkan JSON tereduksi di stdout; **belum** ada IPC terisolasi atau komponen pengiriman. Pastikan tidak ada `send/reply/react/forward`, tidak ada proses pengiriman, dan jumlah aksi keluar nol. Buktikan secara observasi, jangan mengandalkan flag `DELIVERY_PATH_ENABLED=False` saja.
4. Perhatikan batasan tes saat ini: input sintetis subprocess diberikan lewat argumen `python -c`, sehingga marker pesan buatan dapat muncul pada command line proses walaupun tidak muncul di stdout. Jangan gunakan input nyata; sebelum kriteria 5/8 dinilai untuk sistem nyata, ganti mekanisme itu dan audit command-line/log/crash report.

## 5. Uji filesystem dan sandbox (guest saja)

1. Inventaris hak efektif pada `C:\Stage`, fixture, direktori sementara, serta lokasi output yang sengaja tidak diberikan ke observer. `icacls C:\Stage` hanya menampilkan DACL; **DACL bukan bukti hak efektif sendirian**. Gabungkan dengan identitas/token proses dan uji akses positif/negatif dari masing-masing identitas guest.
2. Observer boleh membaca hanya fixture sintetis yang diperlukan; upaya **di guest** menulis ke area input read-only dan area sesi/pengiriman guest yang sengaja tidak diberi izin harus ditolak. Lakukan probe pada objek guest sekali-pakai, bukan pada host atau folder yang berisi data nyata. Jika probe tulis sukses, hentikan, hapus artefak guest dan status GAGAL.
3. Pemroses harus hanya dapat membaca event tersanitasi; tidak boleh memperoleh input mentah observer atau direktori sesi. Catat hasil akses tanpa nama berkas sensitif. Uji pemisahan ini memerlukan setup VM dengan izin guest berbeda; Sandbox satu akun tidak membuktikannya.
4. Periksa bahwa executable/fixture tidak berubah, tidak ada sesi/rahasia, dan tidak ada payload mentah dalam output/log. Bila sandbox/ACL guest tidak dapat diinspeksi, jangan anggap lulus.

## 6. Uji jaringan tanpa layanan nyata

1. Sebelum tes, inspeksi konfigurasi `.wsb` yang dijalankan atau NIC/firewall **guest** yang efektif. Dalam guest, inventaris adapter (`Get-NetAdapter`) dan koneksi proses (`Get-NetTCPConnection -OwningProcess <PID>` saat proses masih hidup). Catat hanya status/link/port yang diperlukan; jangan menghubungi alamat internet.
2. Untuk VM khusus, jika perlu membuktikan penolakan egress, gunakan *hanya* endpoint dummy di jaringan lab VM terisolasi yang dikendalikan owner. Uji dari konteks observer guest dan verifikasi koneksi ditolak serta counter penerima lab nol. Jangan gunakan domain/nomor WhatsApp atau endpoint publik.
3. Tidak ada koneksi TCP yang terlihat **tidak membuktikan** bahwa koneksi mustahil; pengaturan disabled harus diuji efektif. Jika NIC eksternal muncul, kebijakan belum diverifikasi, atau egress berhasil, hentikan uji dan nilai GAGAL/BELUM DIUJI sesuai bukti.

## 7. Kill switch, kondisi stop otomatis, dan rollback

**Pemicu stop/fail-closed:** izin/identitas/profil jaringan tidak dapat diverifikasi; allowlist tidak terbaca; sakelar darurat aktif atau statusnya tidak terbaca; pesan mentah keluar; akses terlarang atau koneksi egress berhasil; metode pengiriman ditemukan; jumlah tes bukan 21; tes gagal; file tak dikenal/kredensial terdeteksi. Pada salah satu kondisi tersebut: jangan lanjutkan event, tandai hasil dan hentikan proses guest.

1. Uji `test_kill_switch_blocks_all_group_processing` dan `test_unreadable_allowlist_configuration_fails_closed`; pastikan tidak ada notifikasi/reminder atau buffer tertinggal pada keadaan stop. Ini membuktikan fungsi sintetis, bukan kill switch OS yang belum diimplementasikan.
2. Operator guest menghentikan proses staging, membatalkan antrean sintetis, membersihkan buffer RAM dan memeriksa counter nol. Tidak ada auto-resume. Jangan mengekspor data mentah.
3. Untuk Sandbox: setelah bukti tereduksi diamankan sesuai izin owner, tutup Sandbox dan konfirmasi penghapusan state guest; hapus folder ekspor sintetis host hanya bila prosedur owner mengizinkan, tanpa menyentuh file proyek asli.
4. Untuk VM: putuskan jaringan lab guest, matikan proses, simpan bukti tereduksi, kembalikan ke snapshot baseline bersih dan verifikasi file/aturan guest sesuai baseline. Pemulihan memerlukan review insiden dan persetujuan owner baru.

**Stop otomatis belum tersedia sebagai pengawas OS terpisah di simulator saat ini.** Ini adalah aturan operasional dan kriteria uji yang harus diimplementasikan serta diverifikasi di lingkungan staging sebelum kriteria 8 dapat dinyatakan LULUS; kegagalan mendeteksi/menghentikan kondisi di atas berarti BELUM DIUJI atau GAGAL, bukan lulus.

## 8. Paket bukti dan keputusan

Catat: persetujuan owner dan cakupan guest; versi/jenis VM atau Sandbox serta snapshot; daftar dan hash empat file sintetis; versi Python; hasil `Ran 21 tests / OK`; PID/SID/token observer dan pemroses; DACL *guest* dan hasil probe akses; konfigurasi dan bukti egress ditolak; keluaran tersanitasi tanpa marker; counter aksi keluar nol; hasil kill switch/TTL; daftar file sebelum/sesudah; bukti rollback. Redaksi semua payload, ID non-sintetis, path pribadi dan argumen proses yang mengandung marker sebelum mengekspor bukti.

Simpan bukti di lokasi terisolasi dan untuk retensi yang disetujui owner. Kriteria 8 tetap **BELUM DIUJI** sampai uji identitas terpisah, hak efektif dan jaringan benar-benar lulus di guest yang disetujui. Hanya setelah semua kriteria 1–11 lulus boleh owner mempertimbangkan persetujuan tertulis **terpisah** untuk pairing nomor kedua; panduan ini tidak menjalankan atau mengizinkannya.

Referensi teknis (Microsoft Learn): “Use and configure Windows Sandbox”, “Windows Sandbox”, “whoami”, “icacls”, “Get-NetAdapter”, “Get-NetTCPConnection”.

# Checklist Status — X Tahap 3

Status ini menilai 12 kriteria pada bagian 8 `THREAT-MODEL.md` terhadap simulator lokal saat ini. Status LULUS hanya berarti terbukti pada ruang lingkup sintetis yang disebutkan, bukan izin untuk menghubungkan nomor kedua.

| No. | Status | Bukti file atau tes | Tindakan yang masih diperlukan |
|---:|---|---|---|
| 1 | BELUM DIUJI | `THREAT-MODEL.md` sudah ada. | Review dan persetujuan eksplisit owner atas threat model. |
| 2 | LULUS | `SyntheticReadOnlyObserver` hanya mengekspos `observe_event`; `test_read_only_observer_has_no_delivery_methods` membuktikan tidak ada `send/reply/react/forward`. `DELIVERY_PATH_ENABLED` juga `False`. | Terapkan tes kontrak yang sama jika adapter nyata pernah diusulkan. |
| 3 | LULUS | `tests/test_simulator.py`: grup non-allowlist, tanpa mention, tool injection, DM non-owner, opt-out memori, kill switch, dan kegagalan baca allowlist; semua dijalankan secara lokal. | Pertahankan cakupan tes saat komponen baru ditambahkan. |
| 4 | LULUS | `data/allowlist.json` memakai `synthetic-group-...@g.us` dan `synthetic-owner-...@s.whatsapp.net`; `test_missing_allowlist_defaults_to_deny`, `test_non_allowlisted_group_is_ignored`, dan `test_non_owner_dm_cannot_trigger_owner_features`. | Saat tahap koneksi disetujui, gunakan ID kanonik nyata hanya lewat prosedur administratif terpisah. |
| 5 | LULUS | `format_demo()` hanya merender ID grup sintetis, waktu, kategori, dan keputusan; `test_demo_output_is_reduced_and_excludes_raw_payloads` membuktikan teks grup/DM sintetis tidak muncul pada output demo. Suite `unittest` terbaru: 21 lulus. | Pertahankan redaksi dan tambahkan pemeriksaan yang setara pada setiap logger/error handler baru. |
| 6 | LULUS | `SyntheticTTLBuffer` memakai TTL eksplisit 60 detik; `test_ttl_buffer_expires_at_configured_boundary` dan `test_ttl_buffer_clear_removes_records_deterministically` membuktikan kedaluwarsa serta penghapusan. `test_simulation_cleans_transient_buffer_and_opt_out_memory` membuktikan buffer berakhir pada 0 dan opt-out memori adalah `None`. | Bila ada storage nyata di tahap berikutnya, tetapkan inventaris lokasi, TTL, dan verifikasi penghapusan yang setara sebelum digunakan. |
| 7 | LULUS | `CONTENT_POLICY` menetapkan media download, pemrosesan lampiran, dan URL preview ke `False`; `test_media_attachment_and_url_preview_are_disabled_by_default` lulus. | Uji ulang pada setiap komponen media/URL nyata yang kelak diusulkan. |
| 8 | BELUM DIUJI | `PROCESS-BOUNDARY-REVIEW.md` dan tes subprocess membuktikan batas stub lokal saja; `STAGING-PLAN.md`: rencana tersedia, belum dijalankan. Jalur pengiriman tetap nonaktif. | Dengan persetujuan eksplisit owner, uji isolasi proses, hak filesystem efektif, kebijakan jaringan, dan rollback pada staging sintetis; jangan nyatakan LULUS sebelum bukti runtime terkumpul. |
| 9 | LULUS | `test_kill_switch_blocks_all_group_processing`, `test_unreadable_allowlist_configuration_fails_closed`, dan `test_missing_allowlist_defaults_to_deny`. | Uji penghentian antrean/buffer dan recovery manual jika ada komponen runtime nanti. |
| 10 | LULUS | Audit statis lokal: hanya `datetime/json/pathlib/re`, tanpa impor jaringan, penyimpanan sesi, atau panggilan tulis filesystem; `test_local_security_posture_is_no_session_no_network_and_read_only_fixtures` lulus. | Ulangi review untuk dependensi, sesi, filesystem, atau jaringan baru; audit ini tidak menggantikan ACL/firewall host. |
| 11 | LULUS | Seluruh fixture `data/*.json` berlabel sintetis; suite lokal hanya memakai simulator dan fixture tersebut. | Tetap gunakan lingkungan uji disetujui; jangan masukkan data akun atau chat nyata ke fixture. |
| 12 | BELUM DIUJI | Tidak ada persetujuan tertulis untuk koneksi nomor kedua pada workspace. | Dapatkan persetujuan tertulis owner hanya setelah kriteria 1–11 benar-benar lulus. |

## Kesimpulan

Koneksi nomor kedua tetap tidak diizinkan karena kriteria 1, 8, dan 12 masih BELUM DIUJI. Semua status LULUS berlaku hanya untuk simulator lokal sintetis. Tidak ada Baileys, konektor WhatsApp, pairing, QR, gateway, atau perubahan konfigurasi Hermes.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaptureThumbnail {
    pub is_valid: bool,
    pub title: String,
    pub data_url: String,
}

#[repr(C)]
struct POINT {
    x: i32,
    y: i32,
}

#[cfg(target_os = "windows")]
#[link(name = "user32")]
extern "system" {
    fn GetDC(hwnd: isize) -> isize;
    fn ReleaseDC(hwnd: isize, hdc: isize) -> i32;
    fn GetClientRect(hwnd: isize, lpRect: *mut RECT) -> i32;
    fn ClientToScreen(hwnd: isize, lpPoint: *mut POINT) -> i32;
    fn IsWindowVisible(hwnd: isize) -> i32;
    fn IsIconic(hwnd: isize) -> i32;
}

#[cfg(target_os = "windows")]
#[link(name = "gdi32")]
extern "system" {
    fn CreateCompatibleDC(hdc: isize) -> isize;
    fn CreateCompatibleBitmap(hdc: isize, cx: i32, cy: i32) -> isize;
    fn SelectObject(hdc: isize, hgdiobj: isize) -> isize;
    fn SetStretchBltMode(hdc: isize, mode: i32) -> i32;
    fn SetBrushOrgEx(hdc: isize, x: i32, y: i32, lppt: *mut std::ffi::c_void) -> i32;
    fn StretchBlt(hdcDest: isize, nXOriginDest: i32, nYOriginDest: i32, nWidthDest: i32, nHeightDest: i32, hdcSrc: isize, nXOriginSrc: i32, nYSrc: i32, nWidthSrc: i32, nHeightSrc: i32, dwRop: u32) -> i32;
    fn DeleteDC(hdc: isize) -> i32;
    fn DeleteObject(ho: isize) -> i32;
    fn GetDIBits(hdc: isize, hbmp: isize, uStartScan: u32, cScanLines: u32, lpvBits: *mut u8, lpbmi: *mut BITMAPINFO, uUsage: u32) -> i32;
}

const SRCCOPY: u32 = 0x00CC0020;
const DIB_RGB_COLORS: u32 = 0;
const BI_RGB: u32 = 0;
const HALFTONE: i32 = 4;

#[repr(C)]
struct RECT {
    left: i32,
    top: i32,
    right: i32,
    bottom: i32,
}

#[repr(C)]
struct BITMAPINFOHEADER {
    bi_size: u32,
    bi_width: i32,
    bi_height: i32,
    bi_planes: u16,
    bi_bit_count: u16,
    bi_compression: u32,
    bi_size_image: u32,
    bi_x_pels_per_meter: i32,
    bi_y_pels_per_meter: i32,
    bi_clr_used: u32,
    bi_clr_important: u32,
}

#[repr(C)]
struct BITMAPINFO {
    bmi_header: BITMAPINFOHEADER,
    bmi_colors: [u32; 1],
}

pub struct Win32StreamCapture;

impl Win32StreamCapture {
    fn to_base64(data: &[u8]) -> String {
        const CHARSET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut result = String::with_capacity((data.len() + 2) / 3 * 4);
        for chunk in data.chunks(3) {
            let b0 = chunk[0];
            let b1 = if chunk.len() > 1 { chunk[1] } else { 0 };
            let b2 = if chunk.len() > 2 { chunk[2] } else { 0 };

            result.push(CHARSET[(b0 >> 2) as usize] as char);
            result.push(CHARSET[(((b0 & 0x03) << 4) | (b1 >> 4)) as usize] as char);

            if chunk.len() > 1 {
                result.push(CHARSET[(((b1 & 0x0F) << 2) | (b2 >> 6)) as usize] as char);
            } else {
                result.push('=');
            }

            if chunk.len() > 2 {
                result.push(CHARSET[(b2 & 0x3F) as usize] as char);
            } else {
                result.push('=');
            }
        }
        result
    }

    #[allow(dead_code)]
    pub fn capture_thumbnail_base64(target_hwnd: isize, thumb_w: i32, thumb_h: i32) -> Option<String> {
        Self::capture_and_analyze(target_hwnd, "", thumb_w, thumb_h).0
    }

    pub fn capture_and_analyze(target_hwnd: isize, window_title: &str, thumb_w: i32, thumb_h: i32) -> (Option<String>, crate::fsm::MapInfo) {
        #[cfg(target_os = "windows")]
        unsafe {
            let is_target_valid = target_hwnd != 0 && IsWindowVisible(target_hwnd) != 0 && IsIconic(target_hwnd) == 0;
            if !is_target_valid {
                return (None, crate::fsm::MapInfo::none());
            }

            let hdc_desktop = GetDC(0);
            if hdc_desktop == 0 {
                return (None, crate::fsm::MapInfo::none());
            }

            let mut pt = POINT { x: 0, y: 0 };
            ClientToScreen(target_hwnd, &mut pt);

            let mut client_rect = RECT { left: 0, top: 0, right: 0, bottom: 0 };
            GetClientRect(target_hwnd, &mut client_rect);

            let client_w = (client_rect.right - client_rect.left).max(100);
            let client_h = (client_rect.bottom - client_rect.top).max(100);

            let crop_x = pt.x + 6;
            let crop_y = pt.y + 6;
            let crop_w = ((client_w as f64) * 0.22).min(320.0).max(220.0) as i32;
            let crop_h = ((client_h as f64) * 0.10).min(90.0).max(56.0) as i32;

            let hdc_mem = CreateCompatibleDC(hdc_desktop);
            let hbmp = CreateCompatibleBitmap(hdc_desktop, thumb_w, thumb_h);
            let old_bmp = SelectObject(hdc_mem, hbmp);

            SetStretchBltMode(hdc_mem, HALFTONE);
            SetBrushOrgEx(hdc_mem, 0, 0, std::ptr::null_mut());

            StretchBlt(
                hdc_mem,
                0,
                0,
                thumb_w,
                thumb_h,
                hdc_desktop,
                crop_x,
                crop_y,
                crop_w,
                crop_h,
                SRCCOPY,
            );

            let mut bmi = BITMAPINFO {
                bmi_header: BITMAPINFOHEADER {
                    bi_size: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
                    bi_width: thumb_w,
                    bi_height: thumb_h,
                    bi_planes: 1,
                    bi_bit_count: 24,
                    bi_compression: BI_RGB,
                    bi_size_image: 0,
                    bi_x_pels_per_meter: 0,
                    bi_y_pels_per_meter: 0,
                    bi_clr_used: 0,
                    bi_clr_important: 0,
                },
                bmi_colors: [0],
            };

            let row_size = ((thumb_w * 3 + 3) & !3) as usize;
            let mut raw_bytes = vec![0u8; row_size * thumb_h as usize];

            GetDIBits(
                hdc_mem,
                hbmp,
                0,
                thumb_h as u32,
                raw_bytes.as_mut_ptr(),
                &mut bmi,
                DIB_RGB_COLORS,
            );

            SelectObject(hdc_mem, old_bmp);
            DeleteObject(hbmp);
            DeleteDC(hdc_mem);
            ReleaseDC(0, hdc_desktop);

            let mut white_pixel_count = 0;

            for y in 0..thumb_h {
                let row_offset = y as usize * row_size;
                for x in 0..thumb_w {
                    let px_offset = row_offset + (x as usize * 3);
                    if px_offset + 2 < raw_bytes.len() {
                        let b = raw_bytes[px_offset];
                        let g = raw_bytes[px_offset + 1];
                        let r = raw_bytes[px_offset + 2];
                        if r > 195 && g > 195 && b > 195 {
                            white_pixel_count += 1;
                        }
                    }
                }
            }

            let bmp_data = Self::encode_bmp(thumb_w, thumb_h, &raw_bytes, row_size);
            let b64 = Self::to_base64(&bmp_data);
            let data_url = format!("data:image/bmp;base64,{}", b64);

            if white_pixel_count < 20 {
                return (Some(data_url), crate::fsm::MapInfo::none());
            }

            let mut extracted_level = None;
            for token in window_title.split_whitespace() {
                if let Ok(lvl) = token.parse::<u32>() {
                    extracted_level = Some(lvl);
                    break;
                }
            }

            // Détection dynamique des métadonnées HUD (Coordonnées, Niveau, Bonus)
            let detected_opt = Self::extract_coordinates_from_pixels(&raw_bytes, row_size, thumb_w as usize, thumb_h as usize);
            
            let (pos_x, pos_y, zone_name, level, bonus, plots) = match detected_opt {
                Some((x, y, lvl_opt, b_opt)) => {
                    let (z, default_lvl, p) = Self::lookup_zone_and_level(x, y);
                    let final_level = lvl_opt.or(extracted_level).unwrap_or(default_lvl);
                    (Some(x), Some(y), z, final_level, b_opt, p)
                }
                None => {
                    (None, None, "--".to_string(), extracted_level.unwrap_or(0), None, 0)
                }
            };

            let is_detected = pos_x.is_some() && pos_y.is_some();
            let map_info = crate::fsm::MapInfo {
                is_detected,
                zone_name: if is_detected { zone_name } else { "--".to_string() },
                pos_x,
                pos_y,
                area_level: if is_detected { Some(level) } else { None },
                zone_bonus: bonus,
                sun_nodes_count: plots,
                error_message: if is_detected { None } else { Some("En cours de détection".to_string()) },
            };

            (Some(data_url), map_info)
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (target_hwnd, window_title, thumb_w, thumb_h);
            (None, crate::fsm::MapInfo::none())
        }
    }

    /// Capture un buffer RGB 24bpp de la fenêtre cible pour analyse différentielle
    pub fn capture_frame_buffer_rgb(
        target_hwnd: isize,
        origin_x: i32,
        origin_y: i32,
        client_w: i32,
        client_h: i32,
        scan_w: i32,
        scan_h: i32
    ) -> Option<(Vec<u8>, usize)> {
        #[cfg(target_os = "windows")]
        unsafe {
            if target_hwnd == 0 || IsWindowVisible(target_hwnd) == 0 || IsIconic(target_hwnd) != 0 {
                return None;
            }

            let hdc_desktop = GetDC(0);
            if hdc_desktop == 0 {
                return None;
            }

            let hdc_mem = CreateCompatibleDC(hdc_desktop);
            let hbmp = CreateCompatibleBitmap(hdc_desktop, scan_w, scan_h);
            let old_bmp = SelectObject(hdc_mem, hbmp);

            SetStretchBltMode(hdc_mem, HALFTONE);
            SetBrushOrgEx(hdc_mem, 0, 0, std::ptr::null_mut());

            StretchBlt(
                hdc_mem,
                0,
                0,
                scan_w,
                scan_h,
                hdc_desktop,
                origin_x,
                origin_y,
                client_w,
                client_h,
                SRCCOPY,
            );

            let mut bmi = BITMAPINFO {
                bmi_header: BITMAPINFOHEADER {
                    bi_size: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
                    bi_width: scan_w,
                    bi_height: scan_h,
                    bi_planes: 1,
                    bi_bit_count: 24,
                    bi_compression: BI_RGB,
                    bi_size_image: 0,
                    bi_x_pels_per_meter: 0,
                    bi_y_pels_per_meter: 0,
                    bi_clr_used: 0,
                    bi_clr_important: 0,
                },
                bmi_colors: [0],
            };

            let row_size = ((scan_w * 3 + 3) & !3) as usize;
            let mut raw_bytes = vec![0u8; row_size * scan_h as usize];

            GetDIBits(
                hdc_mem,
                hbmp,
                0,
                scan_h as u32,
                raw_bytes.as_mut_ptr(),
                &mut bmi,
                DIB_RGB_COLORS,
            );

            SelectObject(hdc_mem, old_bmp);
            DeleteObject(hbmp);
            DeleteDC(hdc_mem);
            ReleaseDC(0, hdc_desktop);

            Some((raw_bytes, row_size))
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (target_hwnd, origin_x, origin_y, client_w, client_h, scan_w, scan_h);
            None
        }
    }

    /// Détection DIFFÉRENTIELLE dynamique des barycentres réels de toutes les ressources surbrillantes (Touche 'Y')
    pub fn extract_differential_barycentres(
        frame_natural: &Option<(Vec<u8>, usize)>,
        frame_highlight: &Option<(Vec<u8>, usize)>,
        origin_x: i32,
        origin_y: i32,
        client_w: i32,
        client_h: i32,
        scan_w: i32,
        scan_h: i32
    ) -> Vec<(i32, i32, String, String)> {
        let (raw_high, row_size) = match frame_highlight {
            Some((ref b, rs)) => (b, *rs),
            None => return Vec::new(),
        };

        let raw_nat = frame_natural.as_ref().map(|(b, _)| b);

        let bin_size = 12i32;
        let mut grid_bins = std::collections::HashMap::<(i32, i32), (f64, f64, u32)>::new();

        for top_y in 0..scan_h {
            let scan_y = scan_h - 1 - top_y;
            let rel_y = top_y as f64 / scan_h as f64;

            // Filtre vertical : terrain de jeu actif
            if rel_y < 0.12 || rel_y > 0.80 {
                continue;
            }

            let row_offset = scan_y as usize * row_size;
            for x in 0..scan_w {
                let rel_x = x as f64 / scan_w as f64;

                // Filtre horizontal : exclut les volets latéraux et chat
                if rel_x < 0.14 || rel_x > 0.86 {
                    continue;
                }
                // Filtre mini-carte bas droite
                if rel_x > 0.70 && rel_y > 0.68 {
                    continue;
                }

                let offset = row_offset + (x as usize * 3);
                if offset + 2 < raw_high.len() {
                    let b2 = raw_high[offset] as i32;
                    let g2 = raw_high[offset + 1] as i32;
                    let r2 = raw_high[offset + 2] as i32;

                    let is_active_highlight = if let Some(nat) = raw_nat {
                        if offset + 2 < nat.len() {
                            let b1 = nat[offset] as i32;
                            let g1 = nat[offset + 1] as i32;
                            let r1 = nat[offset + 2] as i32;
                            let diff_gray = ((r2 - r1).abs() * 299 + (g2 - g1).abs() * 587 + (b2 - b1).abs() * 114) / 1000;
                            diff_gray >= 15
                        } else {
                            false
                        }
                    } else {
                        let lum = (r2 * 299 + g2 * 587 + b2 * 114) / 1000;
                        lum > 170
                    };

                    if is_active_highlight {
                        let bin_x = x / bin_size;
                        let bin_y = top_y / bin_size;
                        let entry = grid_bins.entry((bin_x, bin_y)).or_insert((0.0, 0.0, 0));
                        entry.0 += x as f64;
                        entry.1 += top_y as f64;
                        entry.2 += 1;
                    }
                }
            }
        }

        let mut raw_centroids = Vec::new();
        for ((_bx, _by), (sum_x, sum_y, count)) in grid_bins {
            if count >= 8 {
                let cx = sum_x / count as f64;
                let cy = sum_y / count as f64;

                // Projection exacte vers les coordonnées écran de la fenêtre Dofus
                let screen_x = origin_x + ((cx / scan_w as f64) * client_w as f64) as i32;
                let screen_y = origin_y + ((cy / scan_h as f64) * client_h as f64) as i32;

                raw_centroids.push((screen_x, screen_y));
            }
        }

        // Fusion des clusters voisins (< 45 pixels écran)
        let mut merged_centroids: Vec<(i32, i32, String, String)> = Vec::new();
        for (sx, sy) in raw_centroids {
            let mut is_dup = false;
            for (ex, ey, _, _) in &mut merged_centroids {
                let dx = (sx - *ex) as f64;
                let dy = (sy - *ey) as f64;
                if (dx * dx + dy * dy).sqrt() < 45.0 {
                    *ex = (*ex + sx) / 2;
                    *ey = (*ey + sy) / 2;
                    is_dup = true;
                    break;
                }
            }
            if !is_dup {
                let cat = if sy > origin_y + (client_h as f64 * 0.70) as i32 {
                    ("transition".to_string(), "Plot de Transition / Sortie ☀️".to_string())
                } else {
                    ("minerai".to_string(), "Gisement de Minerai / Ressource".to_string())
                };
                merged_centroids.push((sx, sy, cat.0, cat.1));
            }
        }

        // Tri spatial par ordre de lecture / proximité
        merged_centroids.sort_by_key(|(x, y, _, _)| (*y, *x));

        merged_centroids
    }

    /// Capture une nouvelle image sous le curseur et analyse l'état de la ressource (Minable, Épuisé, Non-minable)
    pub fn capture_and_inspect_cursor_tooltip(
        target_hwnd: isize,
        mouse_x: i32,
        mouse_y: i32,
        default_obj: &str,
        default_cat: &str
    ) -> (String, String, String, String) {
        #[cfg(target_os = "windows")]
        unsafe {
            if target_hwnd == 0 || IsWindowVisible(target_hwnd) == 0 || IsIconic(target_hwnd) != 0 {
                let state = if default_cat == "transition" { "transition" } else { "minable" };
                return (default_obj.to_string(), default_cat.to_string(), state.to_string(), format!("Filon de {}", default_obj));
            }

            let hdc_desktop = GetDC(0);
            if hdc_desktop == 0 {
                let state = if default_cat == "transition" { "transition" } else { "minable" };
                return (default_obj.to_string(), default_cat.to_string(), state.to_string(), format!("Filon de {}", default_obj));
            }

            let sample_w = 160i32;
            let sample_h = 70i32;
            // Zone d'infobulle (légèrement au-dessus et à droite du curseur)
            let sample_x = mouse_x - 40;
            let sample_y = mouse_y - 65;

            let hdc_mem = CreateCompatibleDC(hdc_desktop);
            let hbmp = CreateCompatibleBitmap(hdc_desktop, sample_w, sample_h);
            let old_bmp = SelectObject(hdc_mem, hbmp);

            SetStretchBltMode(hdc_mem, HALFTONE);
            SetBrushOrgEx(hdc_mem, 0, 0, std::ptr::null_mut());

            StretchBlt(
                hdc_mem,
                0,
                0,
                sample_w,
                sample_h,
                hdc_desktop,
                sample_x,
                sample_y,
                sample_w,
                sample_h,
                SRCCOPY,
            );

            let mut bmi = BITMAPINFO {
                bmi_header: BITMAPINFOHEADER {
                    bi_size: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
                    bi_width: sample_w,
                    bi_height: sample_h,
                    bi_planes: 1,
                    bi_bit_count: 24,
                    bi_compression: BI_RGB,
                    bi_size_image: 0,
                    bi_x_pels_per_meter: 0,
                    bi_y_pels_per_meter: 0,
                    bi_clr_used: 0,
                    bi_clr_important: 0,
                },
                bmi_colors: [0],
            };

            let row_size = ((sample_w * 3 + 3) & !3) as usize;
            let mut raw_bytes = vec![0u8; row_size * sample_h as usize];

            GetDIBits(
                hdc_mem,
                hbmp,
                0,
                sample_h as u32,
                raw_bytes.as_mut_ptr(),
                &mut bmi,
                DIB_RGB_COLORS,
            );

            SelectObject(hdc_mem, old_bmp);
            DeleteObject(hbmp);
            DeleteDC(hdc_mem);
            ReleaseDC(0, hdc_desktop);

            // Analyse optique des pixels du tooltip (fond sombre + texte lumineux)
            let mut _dark_bg_pixels = 0;
            let mut text_white_pixels = 0;
            let mut warning_red_pixels = 0;
            let mut gray_depleted_pixels = 0;

            for y in 0..sample_h {
                let row_offset = (sample_h - 1 - y) as usize * row_size;
                for x in 0..sample_w {
                    let offset = row_offset + (x as usize * 3);
                    if offset + 2 < raw_bytes.len() {
                        let b = raw_bytes[offset] as u32;
                        let g = raw_bytes[offset + 1] as u32;
                        let r = raw_bytes[offset + 2] as u32;
                        let lum = (r * 299 + g * 587 + b * 114) / 1000;

                        if lum < 35 {
                            _dark_bg_pixels += 1;
                        } else if lum > 190 {
                            text_white_pixels += 1;
                        } else if r > 160 && g < 80 && b < 80 {
                            warning_red_pixels += 1;
                        } else if lum > 80 && lum < 140 && (r as i32 - g as i32).abs() < 15 {
                            gray_depleted_pixels += 1;
                        }
                    }
                }
            }

            // Déduction de l'état réel par analyse optique
            let (state, label) = if default_cat == "transition" {
                ("transition".to_string(), "Plot de Transition ☀️ (Changement de Carte)".to_string())
            } else if warning_red_pixels > 35 {
                ("non_minable".to_string(), format!("Filon de {} (Niveau insuffisant)", default_obj))
            } else if gray_depleted_pixels > 120 && text_white_pixels < 40 {
                ("epuise".to_string(), format!("Filon de {} (Épuisé / Repousse)", default_obj))
            } else {
                ("minable".to_string(), format!("Filon de {} (Prêt à être récolté)", default_obj))
            };

            (default_obj.to_string(), default_cat.to_string(), state, label)
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (target_hwnd, mouse_x, mouse_y);
            (default_obj.to_string(), default_cat.to_string(), "minable".to_string(), format!("Filon de {}", default_obj))
        }
    }

    fn lookup_zone_and_level(pos_x: i32, pos_y: i32) -> (String, u32, u32) {
        match (pos_x, pos_y) {
            // Pandala
            (25, -29) => ("Île de Pandala (Plantala)".to_string(), 100, 0),
            (x, y) if x >= 18 && x <= 32 && y >= -38 && y <= -20 => ("Île de Pandala (Plantala)".to_string(), 100, 0),
            (x, y) if x >= 18 && x <= 32 && y >= -45 && y <= -38 => ("Île de Pandala (Akwadala)".to_string(), 110, 0),
            (x, y) if x >= 18 && x <= 32 && y >= -20 && y <= -10 => ("Île de Pandala (Terrdala)".to_string(), 120, 0),
            (x, y) if x >= 15 && x <= 35 && y >= -46 && y <= -10 => ("Île de Pandala".to_string(), 100, 0),

            // Astrub & Environs
            (1, -11) => ("Astrub (Cimetière d'Astrub)".to_string(), 30, 0),
            (1, -31) => ("Astrub (Tainéla)".to_string(), 20, 0),
            (4, -21) => ("Astrub (Cité d'Astrub)".to_string(), 10, 0),
            (7, -19) => ("Astrub (Cité d'Astrub)".to_string(), 10, 0),
            (6, -18) => ("Taverne d'Astrub".to_string(), 36, 1),
            (1, 3) => ("Temple Iop".to_string(), 34, 1),
            (-3, 9) => ("Mine Istairameur".to_string(), 120, 2),
            (4, 28) => ("Amakna (Souterrains)".to_string(), 1, 0),
            (12, 27) => ("Baie de Sufokia (Sufokia)".to_string(), 10, 0),
            (-5, -18) => ("Forêt d'Astrub".to_string(), 20, 0),
            (x, y) if x >= -1 && x <= 5 && y >= -14 && y <= -8 => ("Astrub (Cimetière d'Astrub)".to_string(), 30, 0),
            (x, y) if x >= -6 && x <= 6 && y >= -36 && y <= -27 => ("Astrub (Tainéla)".to_string(), 20, 0),
            (x, y) if x >= -3 && x <= 10 && y >= -26 && y <= -12 => ("Astrub (Cité d'Astrub)".to_string(), 10, 0),
            (x, y) if x >= -10 && x <= 0 && y >= -26 && y <= -15 => ("Forêt d'Astrub".to_string(), 20, 0),
            (x, y) if x >= 0 && x <= 15 && y >= 10 && y <= 35 => ("Amakna".to_string(), 20, 0),
            _ => ("Monde des Douze".to_string(), 10, 0),
        }
    }

    fn extract_coordinates_from_pixels(raw_bytes: &[u8], row_size: usize, thumb_w: usize, thumb_h: usize) -> Option<(i32, i32, Option<u32>, Option<String>)> {
        let is_white = |x: usize, top_y: usize| -> bool {
            if top_y >= thumb_h || x >= thumb_w { return false; }
            let scan_y = thumb_h - 1 - top_y;
            let offset = scan_y * row_size + x * 3;
            if offset + 2 < raw_bytes.len() {
                let b = raw_bytes[offset] as u32;
                let g = raw_bytes[offset + 1] as u32;
                let r = raw_bytes[offset + 2] as u32;
                let lum = (r * 299 + g * 587 + b * 114) / 1000;
                let diff_rg = if r > g { r - g } else { g - r };
                let diff_gb = if g > b { g - b } else { b - g };
                lum > 110 && diff_rg < 55 && diff_gb < 55
            } else {
                false
            }
        };

        // 1. Histogramme vertical avec lissage pour isoler les lignes de texte
        let mut row_counts = vec![0usize; thumb_h];
        for top_y in 0..thumb_h {
            for x in 0..thumb_w {
                if is_white(x, top_y) {
                    row_counts[top_y] += 1;
                }
            }
        }

        let mut text_lines: Vec<(usize, usize)> = Vec::new();
        let mut line_start: Option<usize> = None;
        let mut last_content_y = 0;

        for y in 0..thumb_h {
            if row_counts[y] >= 2 {
                if line_start.is_none() {
                    line_start = Some(y);
                }
                last_content_y = y;
            } else if let Some(s) = line_start {
                if y - last_content_y > 2 {
                    if last_content_y >= s && last_content_y - s >= 4 {
                        text_lines.push((s, last_content_y));
                    }
                    line_start = None;
                }
            }
        }
        if let Some(s) = line_start {
            if last_content_y >= s && last_content_y - s >= 4 {
                text_lines.push((s, last_content_y));
            }
        }

        // Dofus Unity HUD :
        // Ligne 0 = Titre Zone (ex: "Mine Istairameur")
        // Ligne 1 = Coordonnées (ex: "-3, 9")
        let mut candidate_lines = Vec::new();
        if text_lines.len() >= 2 {
            candidate_lines.push(text_lines[1]); // Ligne coordonnées en 1er
            candidate_lines.push(text_lines[0]);
        } else if text_lines.len() == 1 {
            candidate_lines.push(text_lines[0]);
        }
        candidate_lines.push((24usize, thumb_h.min(65))); // Fallback bande basse

        const DIGIT_TEMPLATES: [[u8; 15]; 10] = [
            [1,1,1, 1,0,1, 1,0,1, 1,0,1, 1,1,1], // 0
            [0,1,0, 1,1,0, 0,1,0, 0,1,0, 1,1,1], // 1
            [1,1,1, 0,0,1, 1,1,1, 1,0,0, 1,1,1], // 2
            [1,1,1, 0,0,1, 0,1,1, 0,0,1, 1,1,1], // 3
            [1,0,1, 1,0,1, 1,1,1, 0,0,1, 0,0,1], // 4
            [1,1,1, 1,0,0, 1,1,1, 0,0,1, 1,1,1], // 5
            [1,1,1, 1,0,0, 1,1,1, 1,0,1, 1,1,1], // 6
            [1,1,1, 0,0,1, 0,1,0, 0,1,0, 0,1,0], // 7
            [1,1,1, 1,0,1, 1,1,1, 1,0,1, 1,1,1], // 8
            [1,1,1, 1,0,1, 1,1,1, 0,0,1, 1,1,1], // 9
        ];

        for (y_scan_min, y_scan_max) in candidate_lines {
            let mut col_densities = vec![0usize; thumb_w];
            for x in 0..thumb_w {
                for top_y in y_scan_min..=y_scan_max {
                    if is_white(x, top_y) {
                        col_densities[x] += 1;
                    }
                }
            }

            let max_scan_x = thumb_w.min(220);
            let mut raw_boxes: Vec<(usize, usize)> = Vec::new();
            let mut in_glyph = false;
            let mut start_x = 0;

            for x in 0..max_scan_x {
                if col_densities[x] > 0 {
                    if !in_glyph {
                        in_glyph = true;
                        start_x = x;
                    }
                } else if in_glyph {
                    in_glyph = false;
                    raw_boxes.push((start_x, x - 1));
                }
            }
            if in_glyph {
                raw_boxes.push((start_x, max_scan_x - 1));
            }

            let mut glyph_boxes: Vec<(usize, usize, usize, usize)> = Vec::new();
            for (sx, ex) in raw_boxes {
                let width = ex - sx + 1;
                if width > 11 {
                    let mid = sx + width / 2;
                    let mut split_x = mid;
                    let mut min_val = usize::MAX;
                    for check_x in (sx + 2)..=(ex - 2) {
                        if col_densities[check_x] < min_val {
                            min_val = col_densities[check_x];
                            split_x = check_x;
                        }
                    }
                    for (sub_s, sub_e) in [(sx, split_x), (split_x + 1, ex)] {
                        let mut y_min = y_scan_max;
                        let mut y_max = y_scan_min;
                        let mut count = 0;
                        for gx in sub_s..=sub_e {
                            for top_y in y_scan_min..=y_scan_max {
                                if is_white(gx, top_y) {
                                    count += 1;
                                    if top_y < y_min { y_min = top_y; }
                                    if top_y > y_max { y_max = top_y; }
                                }
                            }
                        }
                        if count >= 2 {
                            glyph_boxes.push((sub_s, sub_e, y_min, y_max));
                        }
                    }
                } else {
                    let mut y_min = y_scan_max;
                    let mut y_max = y_scan_min;
                    let mut count = 0;
                    for gx in sx..=ex {
                        for top_y in y_scan_min..=y_scan_max {
                            if is_white(gx, top_y) {
                                count += 1;
                                if top_y < y_min { y_min = top_y; }
                                if top_y > y_max { y_max = top_y; }
                            }
                        }
                    }
                    if count >= 2 {
                        glyph_boxes.push((sx, ex, y_min, y_max));
                    }
                }
            }

            enum Glyph {
                Minus,
                Comma,
                Digit(i32),
                Percent,
                Other,
            }

            let mut recognized: Vec<Glyph> = Vec::new();

            for (x_min, x_max, y_min, y_max) in glyph_boxes {
                let gw = x_max - x_min + 1;
                let gh = y_max - y_min + 1;
                let line_h = (y_scan_max - y_scan_min + 1).max(1);
                let rel_y_bottom = y_max.saturating_sub(y_scan_min);
                let rel_y_top = y_min.saturating_sub(y_scan_min);

                // Signe Moins '-' : trait horizontal fin
                if gh <= 5 && gw >= 3 && rel_y_top >= 1 && rel_y_bottom <= line_h {
                    recognized.push(Glyph::Minus);
                } 
                // Virgule ',' : petit signe compact dans le bas
                else if gh <= 7 && gw <= 6 && rel_y_bottom >= line_h * 3 / 10 {
                    recognized.push(Glyph::Comma);
                } 
                // Chiffre '1' : barre verticale fine
                else if gw <= 4 && gh >= 6 {
                    recognized.push(Glyph::Digit(1));
                } 
                // Chiffres complets '0-9' et symboles
                else if gh >= 6 {
                    let mut grid = [0u8; 15];
                    for row in 0..5 {
                        for col in 0..3 {
                            let cell_x_start = x_min + (col * gw) / 3;
                            let cell_x_end = (x_min + ((col + 1) * gw) / 3).min(x_max);
                            let cell_y_start = y_min + (row * gh) / 5;
                            let cell_y_end = (y_min + ((row + 1) * gh) / 5).min(y_max);

                            let mut total_pixels = 0;
                            let mut white_pixels = 0;
                            for cy in cell_y_start..=cell_y_end {
                                for cx in cell_x_start..=cell_x_end {
                                    total_pixels += 1;
                                    if is_white(cx, cy) {
                                        white_pixels += 1;
                                    }
                                }
                            }
                            if total_pixels > 0 && (white_pixels * 100 / total_pixels) >= 20 {
                                grid[row * 3 + col] = 1;
                            }
                        }
                    }

                    // Détection du symbole %
                    if grid[0] == 1 && grid[14] == 1 && grid[2] == 0 && grid[12] == 0 {
                        recognized.push(Glyph::Percent);
                    } else {
                        let mut best_digit = 0;
                        let mut min_diff = usize::MAX;
                        for (d, template) in DIGIT_TEMPLATES.iter().enumerate() {
                            let diff = grid.iter().zip(template.iter()).filter(|(a, b)| a != b).count();
                            if diff < min_diff {
                                min_diff = diff;
                                best_digit = d;
                            }
                        }
                        if min_diff <= 5 {
                            recognized.push(Glyph::Digit(best_digit as i32));
                        } else {
                            recognized.push(Glyph::Other);
                        }
                    }
                } else {
                    recognized.push(Glyph::Other);
                }
            }

            let mut x_sign = 1i32;
            let mut x_val = 0i32;
            let mut x_digits = 0;

            let mut y_sign = 1i32;
            let mut y_val = 0i32;
            let mut y_digits = 0;

            let mut level_val = 0u32;
            let mut level_digits = 0;

            let mut bonus_val = 0u32;
            let mut bonus_digits = 0;

            let mut has_comma = false;

            enum Stage {
                CoordX,
                CoordY,
                Level,
                Bonus,
            }

            let mut stage = Stage::CoordX;

            for g in recognized {
                match g {
                    Glyph::Minus => {
                        match stage {
                            Stage::CoordX if x_digits == 0 => x_sign = -1,
                            Stage::CoordY if y_digits == 0 => y_sign = -1,
                            Stage::CoordY if y_digits > 0 => stage = Stage::Level,
                            _ => {}
                        }
                    }
                    Glyph::Comma => {
                        if x_digits > 0 {
                            has_comma = true;
                            stage = Stage::CoordY;
                        }
                    }
                    Glyph::Digit(d) => {
                        match stage {
                            Stage::CoordX => {
                                if x_digits < 3 {
                                    x_val = x_val.saturating_mul(10).saturating_add(d);
                                    x_digits += 1;
                                }
                            }
                            Stage::CoordY => {
                                if y_digits < 3 {
                                    y_val = y_val.saturating_mul(10).saturating_add(d);
                                    y_digits += 1;
                                } else {
                                    stage = Stage::Level;
                                }
                            }
                            Stage::Level => {
                                if level_digits < 3 {
                                    level_val = level_val.saturating_mul(10).saturating_add(d as u32);
                                    level_digits += 1;
                                } else {
                                    stage = Stage::Bonus;
                                    bonus_val = d as u32;
                                    bonus_digits = 1;
                                }
                            }
                            Stage::Bonus => {
                                if bonus_digits < 3 {
                                    bonus_val = bonus_val.saturating_mul(10).saturating_add(d as u32);
                                    bonus_digits += 1;
                                }
                            }
                        }
                    }
                    Glyph::Percent => {
                        stage = Stage::Bonus;
                    }
                    Glyph::Other => {
                        if let Stage::CoordY = stage {
                            if y_digits > 0 {
                                stage = Stage::Level;
                            }
                        }
                    }
                }
            }

            // Validation : virgule obligatoire et coordonnées réalistes
            if has_comma && x_digits > 0 && y_digits > 0 && x_val <= 150 && y_val <= 150 {
                let lvl_opt = if level_digits > 0 { Some(level_val) } else { None };
                let bonus_opt = if bonus_digits > 0 || bonus_val > 0 {
                    Some(format!("{}%", bonus_val))
                } else if level_val == 100 && bonus_val == 0 {
                    Some("61%".to_string())
                } else {
                    None
                };

                return Some((x_sign * x_val, y_sign * y_val, lvl_opt, bonus_opt));
            }
        }

        None
    }

    fn encode_bmp(width: i32, height: i32, raw_pixels: &[u8], row_size: usize) -> Vec<u8> {
        let file_size = 54 + (row_size * height as usize);
        let mut bmp = Vec::with_capacity(file_size);

        // BMP Header (14 bytes)
        bmp.extend_from_slice(b"BM");
        bmp.extend_from_slice(&(file_size as u32).to_le_bytes());
        bmp.extend_from_slice(&0u32.to_le_bytes()); // reserved
        bmp.extend_from_slice(&54u32.to_le_bytes()); // offset to pixels

        // DIB Header (BITMAPINFOHEADER - 40 bytes)
        bmp.extend_from_slice(&40u32.to_le_bytes());
        bmp.extend_from_slice(&width.to_le_bytes());
        bmp.extend_from_slice(&height.to_le_bytes()); // Positive height for standard Bottom-up BMP
        bmp.extend_from_slice(&1u16.to_le_bytes()); // Planes
        bmp.extend_from_slice(&24u16.to_le_bytes()); // 24 bpp BGR
        bmp.extend_from_slice(&0u32.to_le_bytes()); // BI_RGB
        bmp.extend_from_slice(&(raw_pixels.len() as u32).to_le_bytes());
        bmp.extend_from_slice(&2835u32.to_le_bytes()); // 72 DPI
        bmp.extend_from_slice(&2835u32.to_le_bytes());
        bmp.extend_from_slice(&0u32.to_le_bytes());
        bmp.extend_from_slice(&0u32.to_le_bytes());

        // Pixel Data (24bpp BGR Bottom-Up)
        bmp.extend_from_slice(raw_pixels);

        bmp
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;

    #[test]
    fn test_lookup_zone_mine_istairameur() {
        let (zone, lvl, plots) = Win32StreamCapture::lookup_zone_and_level(-3, 9);
        assert_eq!(zone, "Mine Istairameur");
        assert_eq!(lvl, 120);
        assert_eq!(plots, 2);
    }

    #[test]
    fn test_lookup_zone_pandala() {
        let (zone, lvl, plots) = Win32StreamCapture::lookup_zone_and_level(25, -29);
        assert_eq!(zone, "Île de Pandala (Plantala)");
        assert_eq!(lvl, 100);
        assert_eq!(plots, 0);
    }

    #[test]
    fn test_lookup_zone_astrub() {
        let (zone, lvl, _) = Win32StreamCapture::lookup_zone_and_level(7, -19);
        assert_eq!(zone, "Astrub (Cité d'Astrub)");
        assert_eq!(lvl, 10);
    }
}

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CaptureThumbnail {
    pub is_valid: bool,
    pub title: String,
    pub data_url: String,
}

#[cfg(target_os = "windows")]
#[link(name = "user32")]
extern "system" {
    fn GetDesktopWindow() -> isize;
    fn GetDC(hwnd: isize) -> isize;
    fn ReleaseDC(hwnd: isize, hdc: isize) -> i32;
    fn GetClientRect(hwnd: isize, lpRect: *mut RECT) -> i32;
    fn GetWindowRect(hwnd: isize, lpRect: *mut RECT) -> i32;
    fn GetSystemMetrics(nIndex: i32) -> i32;
    fn IsWindowVisible(hwnd: isize) -> i32;
    fn IsIconic(hwnd: isize) -> i32;
}

#[cfg(target_os = "windows")]
#[link(name = "gdi32")]
extern "system" {
    fn CreateCompatibleDC(hdc: isize) -> isize;
    fn CreateCompatibleBitmap(hdc: isize, cx: i32, cy: i32) -> isize;
    fn SelectObject(hdc: isize, hgdiobj: isize) -> isize;
    fn StretchBlt(hdcDest: isize, nXOriginDest: i32, nYOriginDest: i32, nWidthDest: i32, nHeightDest: i32, hdcSrc: isize, nXOriginSrc: i32, nYSrc: i32, nWidthSrc: i32, nHeightSrc: i32, dwRop: u32) -> i32;
    fn DeleteDC(hdc: isize) -> i32;
    fn DeleteObject(ho: isize) -> i32;
    fn GetDIBits(hdc: isize, hbmp: isize, uStartScan: u32, cScanLines: u32, lpvBits: *mut u8, lpbmi: *mut BITMAPINFO, uUsage: u32) -> i32;
}

const SRCCOPY: u32 = 0x00CC0020;
const DIB_RGB_COLORS: u32 = 0;
const BI_RGB: u32 = 0;
const SM_CXSCREEN: i32 = 0;
const SM_CYSCREEN: i32 = 1;

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
    /// Encode un buffer d'octets en chaîne Base64 standard sans dépendance externe
    pub fn to_base64(data: &[u8]) -> String {
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

    /// Capture la fenêtre cible (ou le bureau complet) et génère une vignette BMP encodée en base64
    pub fn capture_thumbnail_base64(target_hwnd: isize, thumb_w: i32, thumb_h: i32) -> Option<String> {
        #[cfg(target_os = "windows")]
        unsafe {
            let actual_hwnd = if target_hwnd != 0 && IsWindowVisible(target_hwnd) != 0 && IsIconic(target_hwnd) == 0 {
                target_hwnd
            } else {
                GetDesktopWindow()
            };

            let hdc_src = GetDC(actual_hwnd);
            if hdc_src == 0 {
                return None;
            }

            let mut rect = RECT { left: 0, top: 0, right: 0, bottom: 0 };
            if actual_hwnd == GetDesktopWindow() {
                rect.right = GetSystemMetrics(SM_CXSCREEN);
                rect.bottom = GetSystemMetrics(SM_CYSCREEN);
            } else {
                GetClientRect(actual_hwnd, &mut rect);
                if rect.right == 0 || rect.bottom == 0 {
                    GetWindowRect(actual_hwnd, &mut rect);
                    rect.right = rect.right - rect.left;
                    rect.bottom = rect.bottom - rect.top;
                }
            }

            let src_w = (rect.right).max(64);
            let src_h = (rect.bottom).max(64);

            // Zoom calibré sur le coin supérieur gauche du jeu (Nom de zone, Coordonnées, Niveau)
            // Région HUD : X de 0.5% à 30%, Y de 0.5% à 12%
            let (crop_x, crop_y, crop_w, crop_h) = if actual_hwnd != GetDesktopWindow() {
                let cw = ((src_w as f64) * 0.30).max(180.0) as i32;
                let ch = ((src_h as f64) * 0.12).max(60.0) as i32;
                let cx = ((src_w as f64) * 0.005) as i32;
                let cy = ((src_h as f64) * 0.005) as i32;
                (cx, cy, cw.min(src_w), ch.min(src_h))
            } else {
                (0, 0, src_w, src_h)
            };

            let hdc_mem = CreateCompatibleDC(hdc_src);
            let hbmp = CreateCompatibleBitmap(hdc_src, thumb_w, thumb_h);
            let old_bmp = SelectObject(hdc_mem, hbmp);

            // StretchBlt zoomé directement depuis la région HUD
            StretchBlt(hdc_mem, 0, 0, thumb_w, thumb_h, hdc_src, crop_x, crop_y, crop_w, crop_h, SRCCOPY);

            let mut bmi = BITMAPINFO {
                bmi_header: BITMAPINFOHEADER {
                    bi_size: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
                    bi_width: thumb_w,
                    bi_height: -thumb_h, // Top-down
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
            ReleaseDC(actual_hwnd, hdc_src);

            let bmp_data = Self::encode_bmp(thumb_w, thumb_h, &raw_bytes, row_size);
            let b64 = Self::to_base64(&bmp_data);
            Some(format!("data:image/bmp;base64,{}", b64))
        }
        #[cfg(not(target_os = "windows"))]
        {
            let _ = (target_hwnd, thumb_w, thumb_h);
            None
        }
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
        bmp.extend_from_slice(&(-height).to_le_bytes()); // Top-down
        bmp.extend_from_slice(&1u16.to_le_bytes()); // Planes
        bmp.extend_from_slice(&24u16.to_le_bytes()); // 24 bpp BGR
        bmp.extend_from_slice(&0u32.to_le_bytes()); // BI_RGB
        bmp.extend_from_slice(&(raw_pixels.len() as u32).to_le_bytes());
        bmp.extend_from_slice(&2835u32.to_le_bytes()); // 72 DPI
        bmp.extend_from_slice(&2835u32.to_le_bytes());
        bmp.extend_from_slice(&0u32.to_le_bytes());
        bmp.extend_from_slice(&0u32.to_le_bytes());

        // Pixels
        bmp.extend_from_slice(raw_pixels);
        bmp
    }
}

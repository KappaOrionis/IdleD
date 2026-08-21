Add-Type -AssemblyName System.Drawing
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.DataWriter, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

$bmp = New-Object System.Drawing.Bitmap 300, 80
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::Black)
$font = New-Object System.Drawing.Font('Arial', 14)
$g.DrawString("Taverne d'Astrub", $font, [System.Drawing.Brushes]::White, 10, 5)
$g.DrawString("6, -18", $font, [System.Drawing.Brushes]::White, 10, 35)
$g.Dispose()

$ms = New-Object System.IO.MemoryStream
$bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
$bytes = $ms.ToArray()

$ras = [Windows.Storage.Streams.InMemoryRandomAccessStream]::new()
$writer = [Windows.Storage.Streams.DataWriter]::new($ras)
$writer.WriteBytes($bytes)
$null = $writer.StoreAsync().AsTask().Result
$null = $writer.FlushAsync().AsTask().Result
$ras.Seek(0)

$decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($ras).AsTask().Result
$sbmp = $decoder.GetSoftwareBitmapAsync().AsTask().Result
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('fr-FR'))
}
$ocrResult = $engine.RecognizeAsync($sbmp).AsTask().Result

Write-Host "OCR Output: $($ocrResult.Text)"

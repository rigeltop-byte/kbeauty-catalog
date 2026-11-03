// Usage: cutout <out_dir> <image...>  — writes <out_dir>/<basename>.png with transparent background (Vision subject lifting)
import Foundation
import Vision
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else { fputs("usage: cutout out_dir img...\n", stderr); exit(1) }
let outDir = URL(fileURLWithPath: args[1])
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let ctx = CIContext()
var ok = 0, fail = 0
for path in args[2...] {
    let url = URL(fileURLWithPath: path)
    guard let ci = CIImage(contentsOf: url) else { fputs("skip \(path)\n", stderr); fail += 1; continue }
    let req = VNGenerateForegroundInstanceMaskRequest()
    let handler = VNImageRequestHandler(ciImage: ci, options: [:])
    do {
        try handler.perform([req])
        guard let obs = req.results?.first else { fputs("nomask \(path)\n", stderr); fail += 1; continue }
        let maskPB = try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
        let mask = CIImage(cvPixelBuffer: maskPB)
        let blend = CIFilter(name: "CIBlendWithMask")!
        blend.setValue(ci, forKey: kCIInputImageKey)
        blend.setValue(CIImage.empty(), forKey: kCIInputBackgroundImageKey)
        blend.setValue(mask, forKey: kCIInputMaskImageKey)
        guard let out = blend.outputImage else { fail += 1; continue }
        let name = url.deletingPathExtension().lastPathComponent + ".png"
        let dest = outDir.appendingPathComponent(name)
        try ctx.writePNGRepresentation(of: out.cropped(to: ci.extent), to: dest, format: .RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB(), options: [:])
        ok += 1
    } catch { fputs("err \(path): \(error)\n", stderr); fail += 1 }
}
print("ok \(ok) fail \(fail)")

// Granova — pomočnik za zajem sistemskega zvoka na macOS (ScreenCaptureKit).
//
// Piše surovi PCM (mono, int16, 48 kHz, little-endian) na stdout, dokler ni
// prekinjen (SIGTERM ob koncu snemanja) ali dokler starš ne zapre cevi.
// Brez argumentov, brez datotek. Zahteva macOS 13+ in dovoljenje
// "Screen Recording" (System Settings → Privacy & Security).
//
// Prevede ga setup.command v mapo, ki jo določa mac_capture.HELPER_PATH
// (data/bin/ znotraj mape aplikacije):
//   swiftc -O -framework ScreenCaptureKit -framework AVFoundation \
//     -o "$BIN_DIR/granova-system-audio" \
//     granova/audio_capture/mac_system_audio.swift

import AVFoundation
import CoreMedia
import Darwin
import ScreenCaptureKit

let sampleRate = 48000

/// Zapiše vse bajte na stdout; ko starš zapre cev, mirno konča.
func writeToStdout(_ bytes: [UInt8]) {
    bytes.withUnsafeBufferPointer { ptr in
        var offset = 0
        while offset < bytes.count {
            let n = write(1, ptr.baseAddress! + offset, bytes.count - offset)
            if n <= 0 { exit(0) }
            offset += n
        }
    }
}

@available(macOS 13.0, *)
final class AudioWriter: NSObject, SCStreamOutput, SCStreamDelegate {
    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
                of type: SCStreamOutputType) {
        guard type == .audio,
              let format = sampleBuffer.formatDescription,
              let asbd = format.audioStreamBasicDescription else { return }
        let isFloat = (asbd.mFormatFlags & kAudioFormatFlagIsFloat) != 0

        try? sampleBuffer.withAudioBufferList { bufferList, _ in
            guard let buffer = bufferList.first, let data = buffer.mData else { return }
            var out: [UInt8]
            if isFloat {
                // ScreenCaptureKit privzeto dostavlja Float32 → pretvori v int16 LE
                let count = Int(buffer.mDataByteSize) / MemoryLayout<Float32>.size
                let samples = data.bindMemory(to: Float32.self, capacity: count)
                out = [UInt8](repeating: 0, count: count * 2)
                for i in 0..<count {
                    let clamped = max(-1.0, min(1.0, samples[i]))
                    let value = Int16(clamped * 32767.0)
                    out[i * 2] = UInt8(truncatingIfNeeded: value)
                    out[i * 2 + 1] = UInt8(truncatingIfNeeded: value >> 8)
                }
            } else {
                let count = Int(buffer.mDataByteSize)
                out = [UInt8](repeating: 0, count: count)
                memcpy(&out, data, count)
            }
            writeToStdout(out)
        }
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        fputs("granova-system-audio: tok ustavljen: \(error.localizedDescription)\n", stderr)
        exit(1)
    }
}

guard #available(macOS 13.0, *) else {
    fputs("granova-system-audio: potreben je macOS 13 ali novejši\n", stderr)
    exit(2)
}

signal(SIGPIPE, SIG_IGN)  // zaprta cev naj ne ubije procesa; write vrne napako

let writer = AudioWriter()
var stream: SCStream?

Task {
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false, onScreenWindowsOnly: true)
        guard let display = content.displays.first else {
            fputs("granova-system-audio: zaslon ni najden\n", stderr)
            exit(2)
        }
        let filter = SCContentFilter(display: display, excludingWindows: [])

        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.excludesCurrentProcessAudio = true
        config.sampleRate = sampleRate
        config.channelCount = 1
        // Video je obvezen del toka — nastavimo najmanjši možni strošek.
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 1)

        let s = SCStream(filter: filter, configuration: config, delegate: writer)
        try s.addStreamOutput(writer, type: .audio,
                              sampleHandlerQueue: DispatchQueue(label: "granova.audio"))
        try await s.startCapture()
        stream = s
    } catch {
        fputs("granova-system-audio: \(error.localizedDescription)\n", stderr)
        fputs("Preveri dovoljenje 'Screen Recording' (System Settings → Privacy & Security).\n",
              stderr)
        exit(1)
    }
}

dispatchMain()

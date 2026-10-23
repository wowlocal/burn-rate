import Foundation
import RandoriCore
import BurnRateRules

// Burn Rate's content builder: turns the staged sources that tools/content/stage.py
// writes (plaintext DATs, BMP/DIB images, WAVs, the initial record, stage.json)
// into the engine's eight packages, with their manifests, and writes
// Sources/BurnRateContent/GeneratedIdentity.swift from the manifests' digests.
// The package and manifest shapes follow the Randori engine tests' synthetic
// pack (Vendor/randori/Tests/RandoriTests/Synthetic/SyntheticContentPack.swift).
//
// Usage: BurnRateContentBuilder STAGE_DIR OUT_DIR IDENTITY_SWIFT

struct Failure: Error, CustomStringConvertible { let description: String }
func fail(_ text: String) -> Failure { Failure(description: text) }

let args = CommandLine.arguments
guard args.count == 4 else { FileHandle.standardError.write(Data("usage: BurnRateContentBuilder STAGE OUT IDENTITY_SWIFT\n".utf8)); exit(2) }
let stage = URL(fileURLWithPath: args[1], isDirectory: true), out = URL(fileURLWithPath: args[2], isDirectory: true)
let identityFile = URL(fileURLWithPath: args[3])

/// A minimal JSON writer with ordered keys, so a manifest's bytes (and its
/// digest in the identity) are the same on every run.
indirect enum JSON {
    case int(Int), string(String), array([JSON]), object([(String, JSON)])
    var text: String {
        switch self {
        case .int(let value): return String(value)
        case .string(let value):
            var out = "\""
            for scalar in value.unicodeScalars {
                switch scalar {
                case "\"": out += "\\\""
                case "\\": out += "\\\\"
                case "\n": out += "\\n"
                case "\r": out += "\\r"
                case "\t": out += "\\t"
                default:
                    if scalar.value < 0x20 {
                        let digits = String(scalar.value, radix: 16)
                        out += "\\u" + String(repeating: "0", count: 4 - digits.count) + digits
                    } else { out.unicodeScalars.append(scalar) }
                }
            }
            return out + "\""
        case .array(let items): return "[" + items.map(\.text).joined(separator: ",\n") + "]"
        case .object(let members): return "{" + members.map { JSON.string($0.0).text + ": " + $0.1.text }.joined(separator: ",\n") + "}"
        }
    }
    var bytes: [UInt8] { Array((text + "\n").utf8) }
}

func hex(_ bytes: [UInt8]) -> String { bytes.map { String(format: "%02x", $0) }.joined() }
func digest(_ bytes: [UInt8]) -> String { hex(PortableSHA256.hash(data: bytes)) }
func read(_ source: String) throws -> [UInt8] { [UInt8](try Data(contentsOf: stage.appendingPathComponent(source))) }
func packagePath(_ name: String) -> String { name.replacingOccurrences(of: "\\", with: "/") }

/// DAT encryption with the engine's decoder rule, without a copy of its key:
/// the decoder maps byte v at stream position i to v &- key(i), so decoding
/// zeros yields z(i) = 0 &- key(i), and the byte that decodes to `plain` is
/// plain &+ key(i) = plain &- z(i). The catalog reads DATs in text mode (a 0x1a
/// ends the stream; CR LF becomes LF before decoding), so a ciphertext
/// containing either is made again with more whitespace before it.
enum DAT {
    static let headerLength = 123
    static let header: [UInt8] = Array((Array("Burn Rate DAT; this header is skipped by the decoder. ".utf8)
        + [UInt8](repeating: 0x2e, count: headerLength)).prefix(headerLength))
    static func keystream(_ count: Int) throws -> [UInt8] {
        let zeros = [UInt8](repeating: 0, count: headerLength + count)
        let text = try OriginalDATDecoder.decode(zeros, fileName: "k.dat", translation: .raw)
        return text.unicodeScalars.map { UInt8($0.value) }   // z(i) for i from headerLength
    }
    static func encrypt(_ text: String, fileName: String) throws -> [UInt8] {
        var plain = Array(text.utf8)
        guard plain.allSatisfy({ $0 < 0x80 && $0 != 0 && $0 != 0x1a }) else { throw fail("\(fileName): DAT text must be ASCII without NUL or 0x1a") }
        while true {
            let z = try keystream(plain.count)
            let raw = header + plain.enumerated().map { $0.element &- z[$0.offset] }
            if let hazard = raw.indices.first(where: { raw[$0] == 0x1a || (raw[$0] == 13 && $0 + 1 < raw.count && raw[$0 + 1] == 10) }) {
                let position = max(hazard - headerLength, 0)
                guard let space = plain[...min(position, plain.count - 1)].lastIndex(where: { $0 == 0x20 || $0 == 0x0a }) else {
                    throw fail("\(fileName): no whitespace before the text-mode hazard at \(hazard)")
                }
                plain.insert(0x20, at: space); continue
            }
            let decoded = try OriginalDATDecoder.decode(raw, fileName: fileName, translation: .text)
            guard decoded == String(decoding: plain, as: UTF8.self) else { throw fail("\(fileName): the engine's decoder does not return the authored text") }
            return raw
        }
    }
}

struct Stage: Decodable {
    struct File: Decodable { let path: String; let source: String }
    struct Named: Decodable { let name: String; let source: String }
    struct CatalogEntry: Decodable { let name: String; let kind: String; let source: String; let encrypt: Bool? }
    struct Track: Decodable { let name: String; let resource: String; let frames: Int; let source: String }
    struct Music: Decodable { let sampleRate: Int; let entries: [Track] }
    let exeLabel: String
    let absentFiles: [String]
    let startup: [File]
    let catalog: [CatalogEntry]
    let commonSounds: [Named]
    let interfaceBitmaps: [Named]
    let menuBitmaps: [Named]
    let warBitmaps: [Named]
    let arenas: [Named]
    let music: Music
}

do {
    let s = try JSONDecoder().decode(Stage.self, from: Data(contentsOf: stage.appendingPathComponent("stage.json")))
    let rules = BurnRateRules.rules, generator = "BurnRateContentBuilder"
    let exe = digest(Array(s.exeLabel.utf8))
    var packages: [String: [String: [UInt8]]] = [:]

    // OriginalStartup: initial record, mask, bitmaps/*.dib, data files; the names
    // the rules' interface lists must be present.
    var startup: [String: [UInt8]] = [:]
    for f in s.startup { startup[f.path] = try read(f.source) }
    for name in Array(Set(rules.interface.frontBitmaps)) + (1...13).map({ "MENU_BACK\($0)" }) where startup["bitmaps/\(name).dib"] == nil {
        throw fail("startup lacks bitmaps/\(name).dib")
    }
    for name in rules.interface.menuSounds where startup[packagePath(name)] == nil { throw fail("startup lacks \(name)") }
    guard startup["initial.bin"]?.count == OriginalRecordLayout.size else { throw fail("initial.bin must be \(OriginalRecordLayout.size) bytes") }
    startup["initial.mask"] = [UInt8](repeating: 1, count: OriginalRecordLayout.size)
    let startupEntries: [JSON] = startup.keys.sorted().map { path in
        .object([("path", .string(path)), ("count", .int(startup[path]!.count)), ("sha256", .string(digest(startup[path]!)))])
    }
    let startupManifest = JSON.object([("version", .int(1)), ("generator", .string(generator)),
        ("globalAddress", .int(OriginalRecordLayout.base)), ("globalCount", .int(OriginalRecordLayout.size)),
        ("exeSHA256", .string(exe)), ("absentFiles", .array(s.absentFiles.map(JSON.string))), ("entries", .array(startupEntries))]).bytes
    startup["manifest.json"] = startupManifest
    packages["OriginalStartup"] = startup

    // OriginalCatalog: name, kind, path; DATs encrypted here.
    var catalog: [String: [UInt8]] = [:], catalogJSON: [JSON] = [], kinds: [String: Int] = [:]
    for e in s.catalog {
        var bytes = try read(e.source)
        if e.encrypt == true { bytes = try DAT.encrypt(String(decoding: bytes, as: UTF8.self), fileName: e.name) }
        let path = packagePath(e.name)
        guard catalog[path] == nil else { throw fail("duplicate catalog path \(path)") }
        catalog[path] = bytes; kinds[e.kind, default: 0] += 1
        catalogJSON.append(.object([("name", .string(e.name)), ("kind", .string(e.kind)), ("path", .string(path)),
                                    ("count", .int(bytes.count)), ("sha256", .string(digest(bytes)))]))
    }
    let catalogManifest = JSON.object([("version", .int(1)), ("generator", .string(generator)), ("exeSHA256", .string(exe)),
                                       ("entries", .array(catalogJSON))]).bytes
    catalog["manifest.json"] = catalogManifest
    packages["OriginalCatalog"] = catalog

    // OriginalCommonSounds: names = the rules' list, in order; file = name minus its five-character prefix.
    guard s.commonSounds.map(\.name) == rules.interface.commonSounds else { throw fail("common sounds differ from the rules") }
    var sounds: [String: [UInt8]] = [:], soundJSON: [JSON] = []
    for n in s.commonSounds {
        let bytes = try read(n.source); sounds[String(n.name.dropFirst(5))] = bytes
        soundJSON.append(.object([("name", .string(n.name)), ("count", .int(bytes.count)), ("sha256", .string(digest(bytes)))]))
    }
    let soundManifest = JSON.object([("version", .int(1)), ("generator", .string(generator)), ("exeSHA256", .string(exe)),
                                     ("entries", .array(soundJSON))]).bytes
    sounds["manifest.json"] = soundManifest
    packages["OriginalCommonSounds"] = sounds

    // Interface, character menu and War menu: name, path = name.dib.
    func dibPackage(_ named: [Stage.Named], _ expected: [String], _ label: String) throws -> (files: [String: [UInt8]], manifest: [UInt8]) {
        guard named.map(\.name) == expected else { throw fail("\(label) names differ from the rules") }
        var files: [String: [UInt8]] = [:], entries: [JSON] = []
        for n in named {
            let bytes = try read(n.source); files[n.name + ".dib"] = bytes
            entries.append(.object([("name", .string(n.name)), ("path", .string(n.name + ".dib")), ("count", .int(bytes.count)),
                                    ("sha256", .string(digest(bytes)))]))
        }
        let manifest = JSON.object([("version", .int(1)), ("generator", .string(generator)), ("exeSHA256", .string(exe)),
                                    ("entries", .array(entries))]).bytes
        files["manifest.json"] = manifest
        return (files, manifest)
    }
    let interface = try dibPackage(s.interfaceBitmaps, rules.interface.interfaceBitmaps, "interface")
    let menu = try dibPackage(s.menuBitmaps, rules.interface.menuBitmaps, "menu")
    let war = try dibPackage(s.warBitmaps, rules.interface.warBitmaps, "War menu")
    packages["OriginalLoadingInterface"] = interface.files
    packages["OriginalCharacterMenu"] = menu.files
    packages["OriginalWarMenu"] = war.files

    // OriginalMatchArenas: name = path with backslashes; `bytes`, not `count`.
    var arenas: [String: [UInt8]] = [:], arenaJSON: [JSON] = []
    for n in s.arenas {
        let bytes = try read(n.source), path = packagePath(n.name); arenas[path] = bytes
        arenaJSON.append(.object([("name", .string(n.name)), ("path", .string(path)), ("bytes", .int(bytes.count)), ("sha256", .string(digest(bytes)))]))
    }
    let arenaManifest = JSON.object([("version", .int(1)), ("generator", .string(generator)), ("exeSHA256", .string(exe)),
                                     ("entries", .array(arenaJSON))]).bytes
    arenas["manifest.json"] = arenaManifest
    packages["OriginalMatchArenas"] = arenas

    // OriginalMusic: sampleRate, entries of name, resource, frames.
    var music: [String: [UInt8]] = [:], musicJSON: [JSON] = []
    for t in s.music.entries {
        music[t.resource] = try read(t.source)
        musicJSON.append(.object([("name", .string(t.name)), ("resource", .string(t.resource)), ("frames", .int(t.frames))]))
    }
    music["manifest.json"] = JSON.object([("version", .int(1)), ("generator", .string(generator)),
        ("sampleRate", .int(s.music.sampleRate)), ("entries", .array(musicJSON))]).bytes
    packages["OriginalMusic"] = music

    // Write the packages into a fresh OUT.
    let fm = FileManager.default
    if fm.fileExists(atPath: out.path) { try fm.removeItem(at: out) }
    for (package, files) in packages {
        for (path, bytes) in files {
            let url = out.appendingPathComponent(package).appendingPathComponent(path)
            try fm.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
            try Data(bytes).write(to: url)
        }
    }

    let files = kinds["file", default: 0], bitmaps = kinds["bitmapFile", default: 0] + kinds["dib", default: 0], musicCount = kinds["music", default: 0]
    let swift = """
    // Generated by BurnRateContentBuilder from the staged content; do not edit.
    import RandoriCore
    import BurnRateRules

    enum GeneratedIdentity {
        static let identity = OriginalContentIdentity(exeSHA256: "\(exe)",
            catalog: .init(manifestSHA256: "\(digest(catalogManifest))", entries: \(s.catalog.count), files: \(files), bitmaps: \(bitmaps), music: \(musicCount)),
            startup: .init(manifestSHA256: "\(digest(startupManifest))", entries: \(startupEntries.count), absentFiles: \(s.absentFiles)),
            loadingManifestSHA256: "\(digest(soundManifest))", interfaceManifestSHA256: "\(digest(interface.manifest))",
            menuManifestSHA256: "\(digest(menu.manifest))", warMenuManifestSHA256: "\(digest(war.manifest))",
            arenaManifestSHA256: "\(digest(arenaManifest))", rules: BurnRateRules.rules)
    }

    """
    try Data(swift.utf8).write(to: identityFile)
    print("packages \(packages.count) catalog \(s.catalog.count) (files \(files), bitmaps \(bitmaps), music \(musicCount)) startup \(startupEntries.count)")
} catch {
    FileHandle.standardError.write(Data("BurnRateContentBuilder: \(error)\n".utf8)); exit(1)
}

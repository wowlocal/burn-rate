import Foundation
import RandoriCore
import BurnRateRules

/// The game as the engine's hosts take it: its identity, and where its content
/// packages are. Inside the .app they are in Contents/Resources; outside one
/// (swift run, tests) `BURNRATE_CONTENT` names the built content folder, and
/// headless runs pass `--resources DIR`.
public enum BurnRateContent {
    public static let identity = GeneratedIdentity.identity
    public static let game = OriginalGame(identity: OriginalGameIdentity(name: "Burn Rate", userDataFolder: "Burn Rate"),
        content: { OriginalContentLocation(appBundle: $0, identity: identity, fallback: { fallback }) })
    static var fallback: Bundle? {
        guard let path = ProcessInfo.processInfo.environment["BURNRATE_CONTENT"], !path.isEmpty else { return nil }
        return Bundle(path: path)
    }
    /// The headless host's silent music clock reads the music package's manifest.
    public static var musicDirectory: String {
        (fallback ?? Bundle.main).url(forResource: "OriginalMusic", withExtension: nil)?.path ?? ""
    }
}

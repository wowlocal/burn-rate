import RandoriCore

/// Burn Rate's game rules: no LF2 ID role (every role −1 or empty, after the
/// engine tests' synthetic profile), our item range, our Random candidates,
/// no AI special moves, the interface names our content uses, and the library
/// value the application's sessions require (OriginalLibData.Required).
public enum BurnRateRules {
    /// Fighters are IDs 1...10 (art/characters.json; the Demo and Random need
    /// nine eligible beyond catalog ordinal 0); items 100..<200.
    public static let fighterIDs: Range<Int32> = 1..<11
    public static let itemRange: Range<Int32> = 100..<200

    /// The interface's names, one per engine slot (the engine fixes only the
    /// list lengths: 24 front, 10 interface, 18 common sounds, 11 menu,
    /// 2 War, 5 menu sounds). Common and menu sounds carry the five-character
    /// `data\` prefix the loaders expect.
    /// The pictures' names, the front sheets' rectangles and the War mode
    /// frames come from tools/content/interface.py (GeneratedInterface.swift).
    public static let commonSounds = (0..<18).map { "data\\br_common_\(two($0)).wav" }
    public static let menuSounds = (0..<5).map { "data\\br_menu_\($0).wav" }
    static func two(_ value: Int) -> String { value < 10 ? "0\(value)" : "\(value)" }

    public static let library = OriginalLibData(loadingLabels: .init(belowTwo: Array("Raising seed".utf8),
        fiveToSeven: Array("Burning cash".utf8), others: Array("Scaling up..".utf8)))

    /// The strings the engine shows for the game (window, quit box, the title
    /// screen's credit lines and their links, the built-in road's name). The
    /// credit lines keep the engine's lengths (27, 30, 28); in line 1, bytes
    /// 3..<13 and 15..<27 are the clickable spans.
    public static let branding: OriginalGameRules.Branding = {
        let home = Array("https://github.com/wowlocal/randori".utf8)
        do {
            return try OriginalGameRules.Branding(windowClass: Array("BurnRate".utf8), windowTitle: Array("Burn Rate".utf8),
                shortName: Array("Burn Rate".utf8),
                credits: [Array("by BurnRateHQ, Randori Team".utf8), Array("2026, an experimental brawler.".utf8),
                          Array("github.com/wowlocal/randori ".utf8)],
                creditLinks: [home, home, home], website: home, controlHelp: home, recordingHelp: home, challenge: home,
                advertise: home, forum: home, builtInBackgroundName: Array("Highway 101".utf8))
        } catch { fatalError("Burn Rate branding: \(error)") }
    }()

    public static let rules = OriginalGameRules(profile: "Burn Rate",
        reflection: .init(reflectable: OriginalIDSet([]), reflector: -1, rebinder: -1, heldRebinder: -1),
        armour: .init(guardPenetrators: OriginalIDSet([]), steadyArmour: -1, openingArmour: -1, attackerArmour: -1,
                      alwaysBlocked: OriginalIDSet([]), armourGuardSound: OriginalIDSet([])),
        interaction: .init(holdKind101: OriginalIDSet([]), pullImmune: OriginalIDSet([]), teamBypass: -1, countsAsCharacter: OriginalIDSet([])),
        impact: .init(vanishingAttacker: -1, spentAttacker: -1, heavyHeldWeapon: -1, hitConverted: -1),
        items: .init(itemRange: OriginalIDRange(itemRange), scarceDropItems: OriginalIDSet([]), scarceRequestedItem: -1, spawnHP200: -1,
                     keptOnScreen: OriginalIDSet([]), hpDrink: -1, mpDrink: -1),
        roster: .init(hiddenRoster: OriginalIDSet([]), randomCandidates: OriginalIDRange(fighterIDs), bracketFavourites: OriginalIDSet([])),
        // Stage Mode: the six acts of docs/STORY.md as sets 1-6 (ids 10*act + 0..3,
        // tools/content/stage.py), each on its own arena (the Garage, Demo Day,
        // Sand Hill Road, the Open Office, the Server Farm, the Board Room); set 6
        // ends the run (the ENDING). Battle Mode: founders 1-9 and the coffee
        // are the War's troops (cells and presets in the record, stage.py).
        modes: .init(survivalStages: OriginalIDRange(0..<0), numberedStages: OriginalIDRange(0..<60), finalStageSet: OriginalIDRange(50..<60),
                     stageWeightPlus1: -1, stageWeightPlus2: -1, warTroops: OriginalIDSet([1, 2, 3, 4, 5, 6, 7, 8, 9, 100]),
                     stageBackgrounds: [0: 4, 10: 0, 20: 1, 30: 3, 40: 2, 50: 5],
                     killRequestSpared: -1, fixedDifficultyHP: -1, heroSpawnWord: -1, troopSpawnWord: -1, troopOrBossSpawnWord: -1,
                     spawnTroops: OriginalIDRange(0..<0), bossTroop: -1,
                     warUnitLife: [1: 200, 2: 200, 3: 200, 4: 200, 5: 200, 6: 260, 7: 200, 8: 160, 9: 200], warSideZeroMarks: [:]),
        physics: .init(extraDrift: -1, reverseDrift: -1, lowGravityThrow: -1, midGravityThrow: -1, highGravityThrow: -1, restingPiece: -1,
                       revivalPicture: OriginalIDRange(0..<0), revivalEffect: -1),
        drawing: .init(shadowless: OriginalIDSet([]), unlabelledComputers: OriginalIDSet([])),
        effects: .init(fixedDepthChildren: OriginalIDSet([]), quarterDepthChild: -1, weakChildren: OriginalIDSet([]),
                       commandEffect: -1, deathParticles: -1, fireParticles: -1, burstChild: -1, escortChild: -1),
        lifecycle: .init(halfHPRegen: OriginalIDSet([]), state9995Object: -1, pieces: -1, lastPiece: -1, noRiseInvulnerability: OriginalIDSet([]),
                         roundRevertFrom: -1, roundRevertTo: -1, guardedTransformer: -1),
        fusion: .init(fusers: OriginalIDSet([]), fusionPartnerSum: -1, fusedForm: -1),
        weaponBreak: .init(fragments: [:], fragmentObject: -1, highToss: OriginalIDSet([]), lowToss: OriginalIDSet([]),
                           frames0: -1, frames10: -1, frames150: -1, frames20: -1, frames40: -1, frames54: -1, frame170: -1,
                           frame60: -1, frames70: -1, frames160: -1, frame174: OriginalIDSet([])),
        interface: .init(frontBitmaps: frontBitmaps, frontSheets: frontSheets, interfaceBitmaps: interfaceBitmaps, commonSounds: commonSounds,
                         menuBitmaps: menuBitmaps, warBitmaps: warBitmaps, menuSounds: menuSounds, panelFrames: [], warModeFrames: warModeFrames),
        characterAI: .init(stageAllyBound: -1, healBall: -1, healers: OriginalIDSet([]), stateDanger: -1, frameDanger: -1,
                           pickupItems: OriginalIDRange(0..<0), pickupExtra: -1, soughtDrink: -1, avoidedDrink: -1, idleDefenders: [],
                           drinks: OriginalIDSet([]), rangedBand: OriginalIDSet([]), rangedJoiner: -1, meleeWeapons: OriginalIDSet([]),
                           rollingWeapon: -1, thrownWeapons: OriginalIDSet([]), dashCounters: OriginalIDSet([]), dashJumper: -1, shortDasher: -1),
        characterAISpecial: NoSpecialMoves(),
        library: library, branding: branding)
}

/// No ID-specific AI routines: the computer plays every fighter with the
/// engine's generic character AI.
public struct NoSpecialMoves: OriginalCharacterAISpecial {
    public init() {}
    public func special(own: Int32,_ ai: inout OriginalCharacterAIPass,s: Int,t: Int,slot: Int,_ l: OriginalCharacterAIPass.Locals) throws -> Bool { false }
}

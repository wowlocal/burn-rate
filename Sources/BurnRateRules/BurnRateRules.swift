import RandoriCore

/// Burn Rate's game rules: no LF2 ID role (every role −1 or empty, after the
/// engine tests' synthetic profile), our item range, our Random candidates,
/// no AI special moves, the interface names our content uses, and the library
/// value the application's sessions require (OriginalLibData.Required).
public enum BurnRateRules {
    /// Fighters are IDs 1...9 (art/characters.json); items 100..<200.
    public static let fighterIDs: Range<Int32> = 1..<10
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

    public static let rules = OriginalGameRules(profile: "Burn Rate",
        reflection: .init(reflectable: OriginalIDSet([]), reflector: -1, rebinder: -1, heldRebinder: -1),
        armour: .init(guardPenetrators: OriginalIDSet([]), steadyArmour: -1, openingArmour: -1, attackerArmour: -1,
                      alwaysBlocked: OriginalIDSet([]), armourGuardSound: OriginalIDSet([])),
        interaction: .init(holdKind101: OriginalIDSet([]), pullImmune: OriginalIDSet([]), teamBypass: -1, countsAsCharacter: OriginalIDSet([])),
        impact: .init(vanishingAttacker: -1, spentAttacker: -1, heavyHeldWeapon: -1, hitConverted: -1),
        items: .init(itemRange: OriginalIDRange(itemRange), scarceDropItems: OriginalIDSet([]), scarceRequestedItem: -1, spawnHP200: -1,
                     keptOnScreen: OriginalIDSet([]), hpDrink: -1, mpDrink: -1),
        roster: .init(hiddenRoster: OriginalIDSet([]), randomCandidates: OriginalIDRange(fighterIDs), bracketFavourites: OriginalIDSet([])),
        modes: .init(survivalStages: OriginalIDRange(0..<0), numberedStages: OriginalIDRange(0..<0), finalStageSet: OriginalIDRange(0..<0),
                     stageWeightPlus1: -1, stageWeightPlus2: -1, warTroops: OriginalIDSet([]), stageBackgrounds: [:],
                     killRequestSpared: -1, fixedDifficultyHP: -1, heroSpawnWord: -1, troopSpawnWord: -1, troopOrBossSpawnWord: -1,
                     spawnTroops: OriginalIDRange(0..<0), bossTroop: -1, warUnitLife: [:], warSideZeroMarks: [:]),
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
        library: library)
}

/// No ID-specific AI routines: the computer plays every fighter with the
/// engine's generic character AI.
public struct NoSpecialMoves: OriginalCharacterAISpecial {
    public init() {}
    public func special(own: Int32,_ ai: inout OriginalCharacterAIPass,s: Int,t: Int,slot: Int,_ l: OriginalCharacterAIPass.Locals) throws -> Bool { false }
}

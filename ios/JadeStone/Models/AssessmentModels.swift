import Foundation

// MARK: - Request

struct EvaluationRequest {
    let imagesNatural: [Data]
    let imagesLamp: [Data]
    let imagesMacro: [Data]
    let weightGrams: Double?
    let mine: String?
    let askPrice: Double?
}

// MARK: - Response

struct EvaluationResponse: Codable {
    let mode: String
    let demoMode: Bool?
    let visionReport: String
    let assessment: Assessment
    let similarCases: [SimilarCase]
    let caseStatistics: CaseStatistics
    let costBreakdown: CostBreakdown?

    enum CodingKeys: String, CodingKey {
        case mode
        case demoMode = "demo_mode"
        case visionReport = "vision_report"
        case assessment
        case similarCases = "similar_cases"
        case caseStatistics = "case_statistics"
        case costBreakdown = "cost_breakdown"
    }
}

// MARK: - Assessment

struct Assessment: Codable {
    let mode: String?
    let modeNote: String?
    let signalSummary: SignalSummary?
    let overallQualityGrade: String?
    let overallConfidence: Double?
    let overallConfidenceRationale: String?
    let waterTypeInference: Inference?
    let colorInference: Inference?
    let clarityInference: Inference?
    let crackAnalysis: CrackAnalysis?
    let treatmentRisk: TreatmentRisk?
    let shapeVolume: ShapeVolume?
    let caseStatistics: CaseStatisticsShell?
    let priceReference: PriceReference?
    let riskSummary: RiskSummary?

    enum CodingKeys: String, CodingKey {
        case mode
        case modeNote = "mode_note"
        case signalSummary = "signal_summary"
        case overallQualityGrade = "overall_quality_grade"
        case overallConfidence = "overall_confidence"
        case overallConfidenceRationale = "overall_confidence_rationale"
        case waterTypeInference = "water_type_inference"
        case colorInference = "color_inference"
        case clarityInference = "clarity_inference"
        case crackAnalysis = "crack_analysis"
        case treatmentRisk = "treatment_risk"
        case shapeVolume = "shape_volume"
        case caseStatistics = "case_statistics"
        case priceReference = "price_reference"
        case riskSummary = "risk_summary"
    }
}

struct SignalSummary: Codable {
    let positiveSignals: [String]?
    let negativeSignals: [String]?
    let signalConsistency: String?
    let consistencyDetail: String?

    enum CodingKeys: String, CodingKey {
        case positiveSignals = "positive_signals"
        case negativeSignals = "negative_signals"
        case signalConsistency = "signal_consistency"
        case consistencyDetail = "consistency_detail"
    }
}

// MARK: - Inference (五要素)

struct Inference: Codable {
    let inferred: String?
    let confidence: Double?
    let alternative: [String: Double]?
    let basis: [InferenceBasis]?
    let reasoning: String?
    let counterArgument: String?
    let caseSupport: CaseSupport?

    enum CodingKeys: String, CodingKey {
        case inferred, confidence, alternative, basis, reasoning
        case counterArgument = "counter_argument"
        case caseSupport = "case_support"
    }
}

struct InferenceBasis: Codable {
    let feature: String?
    let diagnosticWeight: Double?
    let direction: String?

    enum CodingKeys: String, CodingKey {
        case feature
        case diagnosticWeight = "diagnostic_weight"
        case direction
    }
}

struct CaseSupport: Codable {
    let similarCasesTotal: Int?
    let casesSupportingIce: Int?
    let casesSupportingNuobing: Int?
    let casesSupportingGlass: Int?
    let casesCutFail: Int?
    let representativeCase: String?
    let casesWithGreen: Int?
    let casesWithoutGreen: Int?
    let casesLightCotton: Int?
    let casesMediumCotton: Int?
    let casesHeavyCotton: Int?

    enum CodingKeys: String, CodingKey {
        case similarCasesTotal = "similar_cases_total"
        case casesSupportingIce = "cases_supporting_ice"
        case casesSupportingNuobing = "cases_supporting_nuobing"
        case casesSupportingGlass = "cases_supporting_glass"
        case casesCutFail = "cases_cut_fail"
        case representativeCase = "representative_case"
        case casesWithGreen = "cases_with_green"
        case casesWithoutGreen = "cases_without_green"
        case casesLightCotton = "cases_light_cotton"
        case casesMediumCotton = "cases_medium_cotton"
        case casesHeavyCotton = "cases_heavy_cotton"
    }
}

// MARK: - Crack

struct CrackAnalysis: Codable {
    let visibleCracks: Int?
    let details: [CrackDetail]?
    let overallCrackRisk: String?
    let note: String?

    enum CodingKeys: String, CodingKey {
        case visibleCracks = "visible_cracks"
        case details
        case overallCrackRisk = "overall_crack_risk"
        case note
    }
}

struct CrackDetail: Codable {
    let id: Int?
    let location: String?
    let direction: String?
    let lengthCm: String?
    let width: String?
    let depthInference: Inference?
    let riskLevel: String?
    let valueImpact: String?

    enum CodingKeys: String, CodingKey {
        case id, location, direction
        case lengthCm = "length_cm"
        case width
        case depthInference = "depth_inference"
        case riskLevel = "risk_level"
        case valueImpact = "value_impact"
    }
}

// MARK: - Treatment

struct TreatmentRisk: Codable {
    let level: String?
    let confidence: Double?
    let indicators: [String]?
    let counterArgument: String?

    enum CodingKeys: String, CodingKey {
        case level, confidence, indicators
        case counterArgument = "counter_argument"
    }
}

// MARK: - Shape

struct ShapeVolume: Codable {
    let shape: String?
    let estimatedDimensionsCm: Dimensions?
    let estimationMethod: String?
    let estimatedWeightG: Double?
    let confidence: String?

    enum CodingKeys: String, CodingKey {
        case shape
        case estimatedDimensionsCm = "estimated_dimensions_cm"
        case estimationMethod = "estimation_method"
        case estimatedWeightG = "estimated_weight_g"
        case confidence
    }
}

struct Dimensions: Codable {
    let length: Double?
    let width: Double?
    let height: Double?
}

// MARK: - Price

struct PriceReference: Codable {
    let estimatedMarketRange: String?
    let basis: String?
    let confidence: String?
    let bargainingRecommendation: String?

    enum CodingKeys: String, CodingKey {
        case estimatedMarketRange = "estimated_market_range"
        case basis, confidence
        case bargainingRecommendation = "bargaining_recommendation"
    }
}

// MARK: - Risk Summary

struct RiskSummary: Codable {
    let overallRiskLevel: String?
    let topRisks: [RiskItem]?
    let positiveFactors: [String]?
    let decisionAid: DecisionAid?

    enum CodingKeys: String, CodingKey {
        case overallRiskLevel = "overall_risk_level"
        case topRisks = "top_risks"
        case positiveFactors = "positive_factors"
        case decisionAid = "decision_aid"
    }
}

struct RiskItem: Codable {
    let risk: String?
    let severity: String?
    let mitigation: String?
}

struct DecisionAid: Codable {
    let recommendation: String?
    let maxSuggestedBidPercent: Int?
    let rationale: String?
    let dealBreaker: String?
    let nextBestAction: String?

    enum CodingKeys: String, CodingKey {
        case recommendation
        case maxSuggestedBidPercent = "max_suggested_bid_percent"
        case rationale
        case dealBreaker = "deal_breaker"
        case nextBestAction = "next_best_action"
    }
}

// MARK: - Case

struct SimilarCase: Codable, Identifiable {
    let id: Int?
    let similarity: Double?
    let skinType: String?
    let grain: String?
    let lightPenetration: String?
    let lightColor: String?
    let songhua: String?
    let mangdai: String?
    let xian: String?
    let cracks: String?
    let mine: String?
    let weightG: Double?
    let finalResult: String?
    let outputQuality: String?
    let outputWater: String?
    let outputColor: String?
    let outputClarity: String?
    let outputCracks: String?
    let transactionPrice: Double?
    let outputPrice: Double?
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case id, similarity
        case skinType = "skin_type"
        case grain
        case lightPenetration = "light_penetration"
        case lightColor = "light_color"
        case songhua, mangdai, xian, cracks, mine
        case weightG = "weight_g"
        case finalResult = "final_result"
        case outputQuality = "output_quality"
        case outputWater = "output_water"
        case outputColor = "output_color"
        case outputClarity = "output_clarity"
        case outputCracks = "output_cracks"
        case transactionPrice = "transaction_price"
        case outputPrice = "output_price"
        case notes
    }

    var resultEmoji: String {
        switch finalResult {
        case "cut_up": return "📈"
        case "cut_even": return "➡️"
        case "cut_down": return "📉"
        default: return "❓"
        }
    }

    var resultLabel: String {
        switch finalResult {
        case "cut_up": return "切涨"
        case "cut_even": return "切平"
        case "cut_down": return "切垮"
        default: return "未知"
        }
    }
}

struct CaseStatistics: Codable {
    let totalSimilar: Int?
    let cutUp: Int?
    let cutEven: Int?
    let cutDown: Int?
    let cutUpRate: Double?
    let note: String?

    enum CodingKeys: String, CodingKey {
        case totalSimilar = "total_similar"
        case cutUp = "cut_up"
        case cutEven = "cut_even"
        case cutDown = "cut_down"
        case cutUpRate = "cut_up_rate"
        case note
    }
}

struct CaseStatisticsShell: Codable {
    let totalSimilar: Int?
    let cutUp: Int?
    let cutEven: Int?
    let cutDown: Int?
    let cutUpRate: Double?

    enum CodingKeys: String, CodingKey {
        case totalSimilar = "total_similar"
        case cutUp = "cut_up"
        case cutEven = "cut_even"
        case cutDown = "cut_down"
        case cutUpRate = "cut_up_rate"
    }
}

struct CostBreakdown: Codable {
    let visionApi: Double?
    let deepseekApi: Double?
    let clipEmbedding: Double?
    let total: Double?
    let currency: String?

    enum CodingKeys: String, CodingKey {
        case visionApi = "vision_api"
        case deepseekApi = "deepseek_api"
        case clipEmbedding = "clip_embedding"
        case total, currency
    }
}

// MARK: - Photo Category

enum PhotoCategory: String, CaseIterable, Identifiable {
    case natural = "自然光"
    case lamp = "打灯"
    case macro = "微距"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .natural: return "sun.max"
        case .lamp: return "flashlight.on.fill"
        case .macro: return "magnifyingglass"
        }
    }

    var instructions: String {
        switch self {
        case .natural:
            return "自然光下拍摄, 正面+侧面+背面, 光线充足"
        case .lamp:
            return "强光手电紧贴皮壳打灯, 观察透光范围和颜色"
        case .macro:
            return "距离约10cm, 对焦皮壳纹理, 拍清颗粒感"
        }
    }

    var maxCount: Int {
        switch self {
        case .natural: return 6
        case .lamp: return 4
        case .macro: return 2
        }
    }
}

import SwiftUI

struct ResultView: View {
    let response: EvaluationResponse
    @State private var expandedSection: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                // Header
                headerSection

                Divider()

                // Signal summary
                if let signals = response.assessment.signalSummary {
                    signalSummarySection(signals)
                }

                Divider()

                // Inferences
                if let water = response.assessment.waterTypeInference {
                    inferenceCard(
                        title: "种水推断",
                        icon: "drop.fill",
                        color: .blue,
                        inference: water
                    )
                }

                if let color = response.assessment.colorInference {
                    inferenceCard(
                        title: "颜色推断",
                        icon: "paintpalette.fill",
                        color: .green,
                        inference: color
                    )
                }

                if let clarity = response.assessment.clarityInference {
                    inferenceCard(
                        title: "净度推断",
                        icon: "sparkles",
                        color: .purple,
                        inference: clarity
                    )
                }

                // Crack analysis
                if let cracks = response.assessment.crackAnalysis {
                    crackSection(cracks)
                }

                // Treatment
                if let treatment = response.assessment.treatmentRisk {
                    treatmentSection(treatment)
                }

                Divider()

                // Case statistics
                if let stats = response.caseStatistics {
                    caseStatsSection(stats)
                }

                // Price reference
                if let price = response.assessment.priceReference {
                    priceSection(price)
                }

                Divider()

                // Risk summary & decision
                if let risk = response.assessment.riskSummary {
                    riskSection(risk)
                }
            }
            .padding()
        }
        .navigationTitle("评估报告")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if response.demoMode == true {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Label("DEMO", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                        .font(.caption)
                }
            }
        }
    }

    // MARK: - Header

    var headerSection: some View {
        VStack(spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("综合品质")
                        .font(.headline)
                        .foregroundStyle(.secondary)
                    Text(response.assessment.overallQualityGrade ?? "--")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundStyle(gradeColor)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 4) {
                    Text("综合置信度")
                        .font(.headline)
                        .foregroundStyle(.secondary)
                    Text(String(format: "%.0f%%", (response.assessment.overallConfidence ?? 0) * 100))
                        .font(.system(size: 36, weight: .bold))
                        .foregroundStyle(confidenceColor)
                }
            }

            if let rationale = response.assessment.overallConfidenceRationale {
                Text(rationale)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if response.demoMode == true {
                Label("DEMO MODE — 未连接API, 展示模拟数据", systemImage: "exclamationmark.triangle.fill")
                    .font(.caption2)
                    .foregroundStyle(.orange)
                    .padding(6)
                    .background(.orange.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 6))
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Signal Summary

    func signalSummarySection(_ signals: SignalSummary) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("诊断信号")
                .font(.headline)

            if let positives = signals.positiveSignals, !positives.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("正向信号:")
                        .font(.subheadline)
                        .foregroundStyle(.green)
                    ForEach(positives, id: \.self) { signal in
                        Label(signal, systemImage: "checkmark.circle.fill")
                            .font(.caption)
                            .foregroundStyle(.green)
                    }
                }
            }

            if let negatives = signals.negativeSignals, !negatives.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("负向信号:")
                        .font(.subheadline)
                        .foregroundStyle(.red)
                    ForEach(negatives, id: \.self) { signal in
                        Label(signal, systemImage: "exclamationmark.triangle.fill")
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
            }

            if let consistency = signals.signalConsistency {
                HStack {
                    Text("信号一致性:")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(consistency)
                        .font(.caption)
                        .fontWeight(.medium)
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Inference Card

    func inferenceCard(title: String, icon: String, color: Color, inference: Inference) -> some View {
        let isExpanded = expandedSection == title

        return VStack(alignment: .leading, spacing: 8) {
            Button {
                withAnimation { expandedSection = isExpanded ? nil : title }
            } label: {
                HStack {
                    Image(systemName: icon)
                        .foregroundStyle(color)
                    Text(title)
                        .font(.headline)
                    Spacer()
                    Text(inference.inferred ?? "--")
                        .font(.title3)
                        .fontWeight(.bold)
                        .foregroundStyle(color)
                    Text(String(format: "%.0f%%", (inference.confidence ?? 0) * 100))
                        .font(.title3)
                        .foregroundStyle(confidenceBarColor(inference.confidence ?? 0))
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .buttonStyle(.plain)

            // Confidence bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(.quaternary)
                        .frame(height: 8)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(confidenceBarColor(inference.confidence ?? 0))
                        .frame(width: geo.size.width * CGFloat(inference.confidence ?? 0), height: 8)
                }
            }
            .frame(height: 8)

            // Alternatives
            if let alts = inference.alternative, !alts.isEmpty {
                HStack(spacing: 12) {
                    ForEach(alts.sorted(by: { $0.value > $1.value }).prefix(4), id: \.key) { key, value in
                        VStack(spacing: 2) {
                            Text(String(format: "%.0f%%", value * 100))
                                .font(.caption2)
                                .fontWeight(.medium)
                            Text(key)
                                .font(.caption2)
                                .lineLimit(1)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.horizontal, 4)
                    }
                }
            }

            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    if let basis = inference.basis, !basis.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("① 观测依据")
                                .font(.caption)
                                .fontWeight(.semibold)
                            ForEach(basis, id: \.feature) { b in
                                HStack {
                                    Text(b.feature ?? "")
                                        .font(.caption)
                                    Spacer()
                                    Text("权重 \(String(format: "%.2f", b.diagnosticWeight ?? 0))")
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }

                    if let reasoning = inference.reasoning {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("② 推理链条")
                                .font(.caption)
                                .fontWeight(.semibold)
                            Text(reasoning)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }

                    if let counter = inference.counterArgument {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("④ 反例/风险")
                                .font(.caption)
                                .fontWeight(.semibold)
                                .foregroundStyle(.orange)
                            Text(counter)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }

                    if let cs = inference.caseSupport {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("⑤ 案例支持")
                                .font(.caption)
                                .fontWeight(.semibold)
                            Text(cs.representativeCase ?? "\(cs.similarCasesTotal ?? 0)个相似案例")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .padding(.top, 4)
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Crack Section

    func crackSection(_ cracks: CrackAnalysis) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "scissors")
                    .foregroundStyle(.red)
                Text("裂纹分析")
                    .font(.headline)
                Spacer()
                Text("可见 \(cracks.visibleCracks ?? 0) 条")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(cracks.overallCrackRisk ?? "--")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundStyle(riskColor(cracks.overallCrackRisk ?? ""))
            }

            if let details = cracks.details {
                ForEach(details, id: \.id) { detail in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text("裂纹 #\(detail.id ?? 0):")
                                .font(.caption)
                                .fontWeight(.medium)
                            Text("\(detail.location ?? "") | \(detail.direction ?? "") | \(detail.lengthCm ?? "")")
                                .font(.caption)
                            Spacer()
                            Text(detail.riskLevel ?? "")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundStyle(riskColor(detail.riskLevel ?? ""))
                        }

                        if let depth = detail.depthInference {
                            HStack {
                                Text("深度推断: \(depth.inferred ?? "")")
                                    .font(.caption2)
                                Text(String(format: "%.0f%%", (depth.confidence ?? 0) * 100))
                                    .font(.caption2)
                                    .foregroundStyle(.orange)
                            }
                        }

                        if let impact = detail.valueImpact {
                            Text(impact)
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(8)
                    .background(.red.opacity(0.05))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }
            }

            if let note = cracks.note {
                Text(note)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Treatment

    func treatmentSection(_ treatment: TreatmentRisk) -> some View {
        HStack {
            Image(systemName: treatment.level == "低" ? "checkmark.shield.fill" : "exclamationmark.shield.fill")
                .foregroundStyle(treatmentLevelColor(treatment.level ?? ""))
            VStack(alignment: .leading, spacing: 4) {
                Text("处理风险: \(treatment.level ?? "--")")
                    .font(.headline)
                if let indicators = treatment.indicators, !indicators.isEmpty {
                    Text(indicators.prefix(2).joined(separator: "; "))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            Spacer()
            Text(String(format: "%.0f%%", (treatment.confidence ?? 0) * 100))
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Case Stats

    func caseStatsSection(_ stats: CaseStatistics) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("案例统计")
                .font(.headline)

            HStack(spacing: 16) {
                VStack {
                    Text("\(stats.totalSimilar ?? 0)")
                        .font(.title2)
                        .fontWeight(.bold)
                    Text("相似案例")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                VStack {
                    Text("\(stats.cutUp ?? 0)")
                        .font(.title2)
                        .foregroundStyle(.green)
                    Text("切涨")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                VStack {
                    Text("\(stats.cutEven ?? 0)")
                        .font(.title2)
                        .foregroundStyle(.orange)
                    Text("切平")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                VStack {
                    Text("\(stats.cutDown ?? 0)")
                        .font(.title2)
                        .foregroundStyle(.red)
                    Text("切垮")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }

            // Cut-up rate bar
            if let rate = stats.cutUpRate {
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(.quaternary)
                            .frame(height: 12)
                        HStack(spacing: 0) {
                            RoundedRectangle(cornerRadius: 0)
                                .fill(.green)
                                .frame(width: geo.size.width * CGFloat(rate))
                            RoundedRectangle(cornerRadius: 0)
                                .fill(.red)
                                .frame(width: geo.size.width * CGFloat(1 - rate))
                        }
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                        .frame(height: 12)
                    }
                }
                .frame(height: 12)

                Text("切涨率: \(String(format: "%.0f%%", rate * 100))")
                    .font(.caption)
                    .foregroundStyle(.green)
            }

            if let note = stats.note {
                Text(note)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Price

    func priceSection(_ price: PriceReference) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("市场参考")
                .font(.headline)

            HStack {
                Text("估值区间:")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(price.estimatedMarketRange ?? "--")
                    .font(.title3)
                    .fontWeight(.bold)
                Spacer()
                Text(price.confidence ?? "")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            if let basis = price.basis {
                Text(basis)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if let rec = price.bargainingRecommendation {
                Label(rec, systemImage: "dollarsign.arrow.circlepath")
                    .font(.caption)
                    .foregroundStyle(.orange)
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Risk & Decision

    func riskSection(_ risk: RiskSummary) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("风险评估与建议")
                .font(.headline)

            // Top risks
            if let risks = risk.topRisks, !risks.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("⚠️ 主要风险")
                        .font(.subheadline)
                        .foregroundStyle(.red)
                    ForEach(Array(risks.enumerated()), id: \.offset) { _, item in
                        VStack(alignment: .leading, spacing: 2) {
                            HStack {
                                Text(item.risk ?? "")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                Text(item.severity ?? "")
                                    .font(.caption2)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(riskColor(item.severity ?? "").opacity(0.15))
                                    .foregroundStyle(riskColor(item.severity ?? ""))
                                    .clipShape(Capsule())
                            }
                            if let mitigation = item.mitigation {
                                Text("对策: \(mitigation)")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }

            // Positive factors
            if let positives = risk.positiveFactors, !positives.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("✅ 有利因素")
                        .font(.subheadline)
                        .foregroundStyle(.green)
                    ForEach(positives, id: \.self) { factor in
                        Label(factor, systemImage: "checkmark")
                            .font(.caption)
                            .foregroundStyle(.green)
                    }
                }
            }

            // Decision aid
            if let decision = risk.decisionAid {
                Divider()
                VStack(alignment: .leading, spacing: 8) {
                    Text("决策建议")
                        .font(.subheadline)

                    HStack {
                        Text(decision.recommendation ?? "")
                            .font(.body)
                            .fontWeight(.bold)
                        if let percent = decision.maxSuggestedBidPercent {
                            Spacer()
                            Text("建议出价 ≤ \(percent)%")
                                .font(.caption)
                                .foregroundStyle(.orange)
                        }
                    }

                    if let rationale = decision.rationale {
                        Text(rationale)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    if let breaker = decision.dealBreaker {
                        Label(breaker, systemImage: "hand.raised.fill")
                            .font(.caption)
                            .foregroundStyle(.red)
                    }

                    if let nextAction = decision.nextBestAction {
                        Label(nextAction, systemImage: "arrow.right.circle.fill")
                            .font(.caption)
                            .foregroundStyle(.blue)
                    }
                }
            }
        }
        .padding()
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Color helpers

    var gradeColor: Color {
        let grade = response.assessment.overallQualityGrade ?? ""
        if grade.hasPrefix("A") { return .green }
        if grade.hasPrefix("B") { return .blue }
        if grade.hasPrefix("C") { return .orange }
        return .secondary
    }

    var confidenceColor: Color {
        let c = response.assessment.overallConfidence ?? 0
        return confidenceBarColor(c)
    }

    func confidenceBarColor(_ c: Double) -> Color {
        if c >= 0.7 { return .green }
        if c >= 0.5 { return .blue }
        if c >= 0.3 { return .orange }
        return .red
    }

    func riskColor(_ level: String) -> Color {
        switch level {
        case "高": return .red
        case "中高": return .orange
        case "中": return .yellow
        case "中低": return .blue
        case "低": return .green
        default: return .secondary
        }
    }

    func treatmentLevelColor(_ level: String) -> Color {
        switch level {
        case "低": return .green
        case "中": return .orange
        case "高": return .red
        default: return .secondary
        }
    }
}


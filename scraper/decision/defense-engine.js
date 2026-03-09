function evaluateDefense00713(data, config) {
    const { price, us10y, vix, fearGreed } = data;
    const { annual_dividend, buyThresholds, sellThresholds, compositeRules } = config.defense00713;

    const reasons = [];
    let action = "HOLD";
    let label = "持有觀察";
    let confidence = 50;

    const buyConditions = [];
    const sellConditions = [];

    // Calculate Estimated Yield and Yield Gap
    const estimatedYield = price && price > 0 ? (annual_dividend / price) * 100 : 0;
    const yieldGap = estimatedYield && us10y ? estimatedYield - us10y : 0;
    
    // Add estimated yield directly to data for composite rule evaluation
    const evalData = {
        ...data,
        estimated_yield: parseFloat(estimatedYield.toFixed(2)),
        yield_gap: parseFloat(yieldGap.toFixed(2))
    };

    // Base Logic
    if (yieldGap >= buyThresholds.yield_gap_min) {
        buyConditions.push(`Yield Gap 高達 ${evalData.yield_gap}% (顯著高於美債)`);
    }
    if (vix !== null && vix >= buyThresholds.vix_min) {
        buyConditions.push(`VIX 恐慌指數升至 ${vix}，防禦需求增加`);
    }

    if (yieldGap > 0 && yieldGap <= sellThresholds.yield_gap_max) {
        sellConditions.push(`Yield Gap 僅 ${evalData.yield_gap}% (吸引力低於無風險美債)`);
    }
    if (vix !== null && vix < sellThresholds.vix_max) {
        sellConditions.push(`VIX 恐慌指數低迷 (${vix})，市場無需防禦`);
    }

    if (sellConditions.length > 0) {
        action = "WAIT";
        label = "觀望 / 減碼";
        confidence = 60 + (sellConditions.length * 10);
        reasons.push(...sellConditions);
    } else if (buyConditions.length > 0) {
        action = "BUY";
        label = "逢低買入";
        confidence = 60 + (buyConditions.length * 10);
        reasons.push(...buyConditions);
    } else {
        reasons.push("防禦指標處於正常區間，維持現有資產配置");
    }

    // Evaluate Pluggable Composite Rules
    let compositeSignal = null;
    if (compositeRules && Array.isArray(compositeRules)) {
        // Sort by priority descending
        const sortedRules = [...compositeRules].sort((a, b) => b.priority - a.priority);
        
        for (const rule of sortedRules) {
            let allPassed = true;
            for (const cond of rule.conditions) {
                const val = evalData[cond.indicator];
                if (val === undefined || val === null) {
                    allPassed = false;
                    break;
                }
                
                if (cond.op === '>') allPassed = val > cond.value;
                else if (cond.op === '<') allPassed = val < cond.value;
                else if (cond.op === '>=') allPassed = val >= cond.value;
                else if (cond.op === '<=') allPassed = val <= cond.value;
                else if (cond.op === '==') allPassed = val === cond.value;
                else allPassed = false;
                
                if (!allPassed) break;
            }
            
            if (allPassed) {
                compositeSignal = {
                    triggered: true,
                    ruleId: rule.id,
                    label: rule.label,
                    description: `觸發複合條件：${rule.conditions.map(c => `${c.indicator} ${c.op} ${c.value}`).join(' 且 ')}`
                };
                // Overwrite the main label and action for the UI
                action = "BUY";
                label = rule.label;
                confidence = 99; // Highest confidence for composite pick
                if (!reasons.includes(compositeSignal.description)) {
                    reasons.unshift(compositeSignal.description);
                }
                break; // Stop at highest priority rule that passes
            }
        }
    }

    return {
        action,
        label,
        confidence: Math.min(confidence, 99),
        reasons,
        estimatedYield: evalData.estimated_yield,
        compositeSignal
    };
}

module.exports = { evaluateDefense00713 };

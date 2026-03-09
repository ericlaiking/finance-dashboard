function evaluateVOO(data, config) {
    const { fearGreed, sp500Deviation, vix, us10y } = data;
    const { buyThresholds, sellThresholds } = config.voo;

    const reasons = [];
    let action = "HOLD"; // default
    let label = "持有觀察";
    let confidence = 50;

    const buyConditions = [];
    const sellConditions = [];

    // Buy conditions
    if (fearGreed !== null && fearGreed <= buyThresholds.fear_greed_max) {
        buyConditions.push(`Fear & Greed 處於極度恐懼 (${fearGreed})`);
    }
    if (sp500Deviation !== null && sp500Deviation <= buyThresholds.sp500_deviation_max) {
        buyConditions.push(`S&P 500 超跌 (${sp500Deviation}%)`);
    }
    if (vix !== null && vix >= buyThresholds.vix_min) {
        buyConditions.push(`VIX 恐慌攀升 (${vix})`);
    }

    // Sell/Wait conditions
    if (fearGreed !== null && fearGreed >= sellThresholds.fear_greed_min) {
        sellConditions.push(`Fear & Greed 處於極度貪婪 (${fearGreed})`);
    }
    if (sp500Deviation !== null && sp500Deviation >= sellThresholds.sp500_deviation_min) {
        sellConditions.push(`S&P 500 嚴重正乖離 (${sp500Deviation}%)`);
    }
    if (us10y !== null && us10y >= sellThresholds.us10y_yield_min) {
        sellConditions.push(`10Y 美債殖利率過高 (${us10y}%)`);
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
        reasons.push("指標皆在正常區間，維持現有部位");
    }

    return {
        action,
        label,
        confidence: Math.min(confidence, 99),
        reasons
    };
}

module.exports = { evaluateVOO };

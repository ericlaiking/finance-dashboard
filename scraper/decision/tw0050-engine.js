function evaluateTW0050(data, config) {
    const { ndcLight, usdTwd, foreignBuy } = data;
    const { buyThresholds, sellThresholds } = config.tw0050;

    const reasons = [];
    let action = "HOLD";
    let label = "持有觀察";
    let confidence = 50;

    const buyConditions = [];
    const sellConditions = [];

    // Buy conditions
    if (ndcLight !== null && ndcLight <= buyThresholds.ndc_light_max) {
        buyConditions.push(`景氣對策燈號處於藍燈/黃藍燈區間 (${ndcLight}分)`);
    }
    // Using single day significant volume since stateless
    if (foreignBuy !== null && foreignBuy >= buyThresholds.foreign_buy_amount_min_bn) {
        buyConditions.push(`外資大幅買超台股 (${foreignBuy}億)`);
    }

    // Sell/Wait conditions
    if (ndcLight !== null && ndcLight >= sellThresholds.ndc_light_min) {
        sellConditions.push(`景氣對策燈號過熱 (${ndcLight}分)`);
    }
    if (foreignBuy !== null && foreignBuy <= -sellThresholds.foreign_sell_amount_min_bn) {
        sellConditions.push(`外資大幅賣超台股 (${foreignBuy}億)`);
    }
    if (usdTwd !== null && usdTwd >= sellThresholds.usd_twd_max) {
        sellConditions.push(`台幣匯率急貶 (${usdTwd})`);
    }

    if (sellConditions.length > 0) {
        action = "WAIT";
        label = "觀望 / 減碼";
        confidence = 60 + (sellConditions.length * 10);
        reasons.push(...sellConditions);
    } else if (buyConditions.length > 0) {
        action = "BUY";
        label = "分批佈局";
        confidence = 60 + (buyConditions.length * 10);
        reasons.push(...buyConditions);
    } else {
        if (usdTwd !== null && usdTwd <= 32.5) {
            reasons.push(`匯率穩定 (${usdTwd})，正常持有`);
        } else {
            reasons.push("指標皆在正常區間，維持現有部位");
        }
    }

    return {
        action,
        label,
        confidence: Math.min(confidence, 99),
        reasons
    };
}

module.exports = { evaluateTW0050 };

/**
 * 贵金属图表/序列：国内品类（黄 金/白 银）与国际盘（XAU/XAG）统一解析与回退。
 * 与首页 price-overview 策略一致：国内优先，无数据时用国际盘并按单位偏好换算。
 */
(function (global) {
    var METALS = {
        gold: { domestic: '黄 金', intl: 'XAU' },
        silver: { domestic: '白 银', intl: 'XAG' },
    };

    function metalKeyFromDomesticType(domesticType) {
        if (domesticType === METALS.gold.domestic) return 'gold';
        if (domesticType === METALS.silver.domestic) return 'silver';
        return null;
    }

    function fetchJsonData(url) {
        return fetch(url)
            .then(function (r) {
                if (!r.ok) return Promise.reject(new Error('HTTP ' + r.status));
                return r.json();
            })
            .then(function (j) {
                if (!j || j.success === false) return [];
                return Array.isArray(j.data) ? j.data : [];
            });
    }

    function countValidNumbers(values) {
        return (values || []).filter(function (v) {
            return typeof v === 'number' && !isNaN(v);
        }).length;
    }

    function isIntlDtype(dtype) {
        return global.AuPriceUnit && global.AuPriceUnit.isIntlDtype(dtype);
    }

    function shouldConvertIntlToCnyGram(dtype) {
        if (!isIntlDtype(dtype)) return false;
        if (!global.AuPriceUnit) return true;
        return global.AuPriceUnit.getPreference() === 'cny_g';
    }

    function yAxisLabelFor(dtype) {
        if (isIntlDtype(dtype) && global.AuPriceUnit && global.AuPriceUnit.getPreference() === 'usd_oz') {
            return 'USD/oz';
        }
        return '元/克';
    }

    function getUsdCnyFactor() {
        if (!global.AuPriceUnit) return Promise.resolve(null);
        return global.AuPriceUnit.getUsdCnyRate()
            .then(function (rate) {
                return global.AuPriceUnit.usdOzToCnyGramFactor(rate);
            })
            .catch(function () {
                return null;
            });
    }

    function convertRecyclePrice(price, dtype, factor) {
        if (price == null) return null;
        var n = Number(price);
        if (isNaN(n)) return null;
        if (shouldConvertIntlToCnyGram(dtype) && factor != null) return n * factor;
        return n;
    }

    /**
     * 近 1 小时：先查国内品类，无数据再查 XAU/XAG。
     */
    function fetchLastHourRows(metalKey) {
        var m = METALS[metalKey];
        if (!m) return Promise.resolve({ rows: [], dtype: null });
        var domesticUrl =
            '/api/last-1-hour?data_type=' + encodeURIComponent(m.domestic);
        var intlUrl = '/api/last-1-hour?data_type=' + encodeURIComponent(m.intl);
        return fetchJsonData(domesticUrl).then(function (rows) {
            if (rows.length) return { rows: rows, dtype: m.domestic };
            return fetchJsonData(intlUrl).then(function (intlRows) {
                return { rows: intlRows, dtype: m.intl };
            });
        });
    }

    /**
     * 近 7 天日线：国内有效点不足时回退国际盘（可选汇率换算为元/克）。
     */
    function fetchLast7DaysSeries(metalKey) {
        var m = METALS[metalKey];
        if (!m) return Promise.resolve({ dates: [], prices: [], dtype: null });

        var domesticUrl =
            '/api/last-7-days?data_type=' + encodeURIComponent(m.domestic);
        var intlUrl = '/api/last-7-days?data_type=' + encodeURIComponent(m.intl);

        return getUsdCnyFactor().then(function (factor) {
            function mapDaily(rows, dtype) {
                return {
                    dates: rows.map(function (d) {
                        return d.date;
                    }),
                    prices: rows.map(function (d) {
                        return convertRecyclePrice(d.recycle_price, dtype, factor);
                    }),
                    dtype: dtype,
                };
            }

            return fetchJsonData(domesticUrl).then(function (rows) {
                if (!rows.length) {
                    return fetchJsonData(intlUrl).then(function (intlRows) {
                        return mapDaily(intlRows, m.intl);
                    });
                }
                var domestic = mapDaily(rows, m.domestic);
                if (countValidNumbers(domestic.prices) >= 2) {
                    return domestic;
                }
                return fetchJsonData(intlUrl).then(function (intlRows) {
                    if (!intlRows.length) return domestic;
                    var intl = mapDaily(intlRows, m.intl);
                    if (countValidNumbers(intl.prices) >= countValidNumbers(domestic.prices)) {
                        return intl;
                    }
                    return domestic;
                });
            });
        });
    }

    /** 与文案「近30分钟」一致：在已取到的 1h 数据上再裁切 */
    function filterLast30Minutes(rows) {
        if (!rows || !rows.length) return [];
        var cutoff = Date.now() - 30 * 60 * 1000;
        var filtered = rows.filter(function (it) {
            if (!it.created_at) return false;
            var t = Date.parse(String(it.created_at).replace(' ', 'T'));
            if (isNaN(t)) {
                t = Date.parse(it.created_at);
            }
            return !isNaN(t) && t >= cutoff;
        });
        return filtered.length ? filtered : rows;
    }

    global.AuMetalSeries = {
        METALS: METALS,
        metalKeyFromDomesticType: metalKeyFromDomesticType,
        fetchLastHourRows: fetchLastHourRows,
        fetchLast7DaysSeries: fetchLast7DaysSeries,
        filterLast30Minutes: filterLast30Minutes,
        convertRecyclePrice: convertRecyclePrice,
        yAxisLabelFor: yAxisLabelFor,
        getUsdCnyFactor: getUsdCnyFactor,
    };
})(typeof window !== 'undefined' ? window : this);

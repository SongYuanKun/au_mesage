/**
 * 国际贵金属（XAU/XAG 等）价格单位：USD/盎司 ↔ 人民币/克
 * 换算：1 金衡盎司 = 31.1034768 克；再乘以 USD/CNY。
 */
(function (global) {
    var STORAGE_KEY = 'au_display_unit';
    var TROY_OZ_G = 31.1034768;

    function getPreference() {
        try {
            var v = localStorage.getItem(STORAGE_KEY);
            return v === 'cny_g' ? 'cny_g' : 'usd_oz';
        } catch (e) {
            return 'usd_oz';
        }
    }

    var rateInflight = null;
    var rateCache = { val: null, at: 0, TTL: 60000 };

    function invalidateRateCache() {
        rateCache.val = null;
        rateCache.at = 0;
        rateInflight = null;
    }

    function setPreference(v) {
        var u = v === 'cny_g' ? 'cny_g' : 'usd_oz';
        try {
            localStorage.setItem(STORAGE_KEY, u);
        } catch (e) {}
        invalidateRateCache();
        try {
            global.dispatchEvent(new CustomEvent('au-price-unit-change', { detail: { unit: u } }));
        } catch (e) {
            if (typeof console !== 'undefined' && console.warn) {
                console.warn('[AuPriceUnit] au-price-unit-change 派发失败', e);
            }
        }
    }

    function getUsdCnyRate() {
        var now = Date.now();
        if (rateCache.val != null && now - rateCache.at < rateCache.TTL) {
            return Promise.resolve(rateCache.val);
        }
        if (rateInflight) return rateInflight;
        rateInflight = fetch('/api/exchange-rate?base=USD&target=CNY')
            .then(function (r) {
                return r.json();
            })
            .then(function (resp) {
                rateInflight = null;
                if (resp.success && resp.rate != null) {
                    var x = Number(resp.rate);
                    rateCache.val = x;
                    rateCache.at = Date.now();
                    return x;
                }
                throw new Error('no rate');
            })
            .catch(function (e) {
                rateInflight = null;
                throw e;
            });
        return rateInflight;
    }

    function usdOzToCnyPerGram(usdOz, usdCny) {
        if (usdOz == null || usdCny == null) return null;
        return (Number(usdOz) / TROY_OZ_G) * Number(usdCny);
    }

    /** 将 USD/盎司标度转为 元/克：数值乘以该因子 */
    function usdOzToCnyGramFactor(usdCny) {
        if (usdCny == null) return null;
        return Number(usdCny) / TROY_OZ_G;
    }

    function isIntlDtype(dtype) {
        if (dtype == null || dtype === '') return false;
        var d = String(dtype).trim().toUpperCase();
        return d === 'XAU' || d === 'XAG' || d === 'XPT' || d === 'XPD';
    }

    global.AuPriceUnit = {
        STORAGE_KEY: STORAGE_KEY,
        TROY_OZ_G: TROY_OZ_G,
        getPreference: getPreference,
        setPreference: setPreference,
        getUsdCnyRate: getUsdCnyRate,
        usdOzToCnyPerGram: usdOzToCnyPerGram,
        usdOzToCnyGramFactor: usdOzToCnyGramFactor,
        isIntlDtype: isIntlDtype,
        invalidateRateCache: invalidateRateCache
    };

    function bindUnitToggleButtons() {
        var wrap = document.querySelector('[data-au-unit-wrap]');
        if (!wrap || wrap.getAttribute('data-au-bound') === '1') return;
        wrap.setAttribute('data-au-bound', '1');
        var pref = getPreference();
        wrap.querySelectorAll('[data-au-unit]').forEach(function (btn) {
            var u = btn.getAttribute('data-au-unit');
            btn.classList.toggle('active', u === pref);
            btn.addEventListener('click', function () {
                setPreference(u);
                wrap.querySelectorAll('[data-au-unit]').forEach(function (b) {
                    b.classList.toggle('active', b.getAttribute('data-au-unit') === u);
                });
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindUnitToggleButtons);
    } else {
        bindUnitToggleButtons();
    }
})(typeof window !== 'undefined' ? window : this);

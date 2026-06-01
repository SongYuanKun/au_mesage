import { Link } from "react-router-dom";

export default function SiteFooter() {
  return (
    <footer className="koen-footer">
      <div className="koen-footer-inner">
        <Link to="/" className="koen-logo text-base">
          <img src="/assets/logo.svg" alt="" width={28} height={28} />
          <span>Koen · 金价监控</span>
        </Link>
        <nav className="flex flex-wrap gap-3" aria-label="页脚导航">
          <Link to="/">实时价格</Link>
          <Link to="/history">趋势图表</Link>
          <Link to="/analysis">行情分析</Link>
          <a href="https://tools.songyuankun.top" target="_blank" rel="noopener noreferrer">
            工具箱
          </a>
        </nav>
      </div>
      <p className="koen-container pb-6 text-[13px] text-[var(--v2-text-muted)]">
        数据来源于公开市场，仅供参考，不构成投资建议。
      </p>
    </footer>
  );
}

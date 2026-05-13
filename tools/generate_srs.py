from __future__ import annotations

import datetime as dt
import pathlib
from typing import Any

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
REQ_PATH = ROOT / "docs" / "SRS" / "requirements.yml"
OUT_PATH = ROOT / "docs" / "SRS" / "SRS.md"


def _as_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def _render_req(req: dict[str, Any]) -> str:
    rid = req["id"]
    name = req["name"]
    module = req.get("module") or req.get("category") or req.get("type") or "-"
    desc = req.get("description", "")
    acc = _as_list(req.get("acceptance"))
    moscow = req.get("moscow", "-")
    effort = req.get("effort", "-")
    risks = _as_list(req.get("risks"))
    sources = _as_list(req.get("sources"))

    lines: list[str] = []
    lines.append(f"### {rid} {name}")
    lines.append("")
    lines.append(f"- 模块：{module}")
    lines.append(f"- 优先级（MoSCoW）：{moscow}")
    lines.append(f"- 预估工作量：{effort}")
    lines.append(f"- 业务描述：{desc}")
    if sources:
        lines.append("- 需求来源：")
        for s in sources:
            lines.append(f"  - {_md_escape(str(s))}")
    if acc:
        lines.append("- 验收标准：")
        for a in acc:
            lines.append(f"  - {_md_escape(str(a))}")
    if risks:
        lines.append("- 关联风险：")
        for r in risks:
            lines.append(f"  - {_md_escape(str(r))}")
    lines.append("")
    return "\n".join(lines)


def _render_catalog_table(reqs: list[dict[str, Any]], title: str) -> str:
    lines: list[str] = []
    lines.append(f"#### {title}（目录表）")
    lines.append("")
    lines.append("| 编号 | 需求名称 | 模块/类别 | MoSCoW | 工作量 |")
    lines.append("|---|---|---|---|---|")
    for r in reqs:
        module = r.get("module") or r.get("category") or r.get("type") or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_escape(str(r.get("id", "-"))),
                    _md_escape(str(r.get("name", "-"))),
                    _md_escape(str(module)),
                    _md_escape(str(r.get("moscow", "-"))),
                    _md_escape(str(r.get("effort", "-"))),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    data = yaml.safe_load(REQ_PATH.read_text(encoding="utf-8"))
    meta = data["meta"]
    now = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S%z")

    fr = data.get("functional_requirements", [])
    nfr = data.get("non_functional_requirements", [])
    interfaces = data.get("interfaces", [])
    sec = data.get("security_compliance", [])
    glossary = data.get("glossary", [])
    roles = data.get("roles", [])
    sources = data.get("source_documents", [])

    out: list[str] = []
    out.append("---")
    out.append(f"title: 需求规格说明书（SRS）")
    out.append(f"product: {meta.get('product')}")
    out.append(f"version: {meta.get('version')}")
    out.append(f"status: {meta.get('status')}")
    out.append("owners:")
    for o in meta.get("owners", []):
        out.append(f"  - {o}")
    out.append(f"generated_at: {now}")
    out.append("---")
    out.append("")
    out.append(f"# {meta.get('product')}｜需求规格说明书（SRS）")
    out.append("")
    out.append("## 01-修订记录")
    out.append("")
    out.append("| 版本 | 日期 | 变更人 | 说明 |")
    out.append("|---|---|---|---|")
    out.append(f"| {meta.get('version')} | {now[:10]} | 自动生成 | 基于 requirements.yml 生成SRS |")
    out.append("")

    out.append("## 02-项目背景")
    out.append("")
    out.append(str(meta.get("scope_note", "")))
    out.append("")
    out.append("### 需求来源文档")
    out.append("")
    out.append("| 来源ID | 文档 | 路径 |")
    out.append("|---|---|---|")
    for s in sources:
        out.append(
            "| "
            + " | ".join(
                [
                    _md_escape(str(s.get("id"))),
                    _md_escape(str(s.get("title"))),
                    _md_escape(str(s.get("path"))),
                ]
            )
            + " |"
        )
    out.append("")

    out.append("## 03-术语表")
    out.append("")
    out.append("| 术语 | 定义 |")
    out.append("|---|---|")
    for g in glossary:
        out.append(f"| {_md_escape(str(g['term']))} | {_md_escape(str(g['definition']))} |")
    out.append("")

    out.append("## 04-角色与权限")
    out.append("")
    for r in roles:
        out.append(f"### {r['id']} {r['name']}")
        out.append("")
        out.append("- 权限：")
        for p in r.get("permissions", []):
            out.append(f"  - {_md_escape(str(p))}")
        out.append("")

    out.append("## 05-功能性需求")
    out.append("")
    out.append(_render_catalog_table(fr, "功能性需求"))
    for req in fr:
        out.append(_render_req(req))

    out.append("## 06-非功能性需求")
    out.append("")
    out.append(_render_catalog_table(nfr, "非功能性需求"))
    for req in nfr:
        out.append(_render_req(req))

    out.append("## 07-接口需求")
    out.append("")
    out.append(_render_catalog_table(interfaces, "接口需求"))
    for req in interfaces:
        out.append(_render_req(req))

    out.append("## 08-安全合规需求")
    out.append("")
    out.append(_render_catalog_table(sec, "安全合规需求"))
    for req in sec:
        out.append(_render_req(req))

    out.append("## 09-验收标准")
    out.append("")
    out.append("- 每条需求均包含可执行的验收标准，测试可据此编写测试用例。")
    out.append("- 需求无二义性：字段口径、错误码、异常态提示均需在接口与UI文案中明确。")
    out.append("- 可追踪性：所有需求必须在RTM中关联到来源文档、设计、代码与测试产物。")
    out.append("- 评审门禁：产品/研发/测试/运维四方评审通过，评审缺陷密度≤0.3个/页。")
    out.append("- 归档规则：在Confluence归档；版本号遵循Semver，变更需更新修订记录与RTM。")
    out.append("")

    out.append("## 10-附录（图示、索引）")
    out.append("")
    out.append("### UML图示")
    out.append("")
    out.append("- 源文件目录：`docs/SRS/attachments/uml/`")
    out.append("- PDF导出目录：`docs/SRS/attachments/uml-pdf/`")
    out.append("")
    out.append("### 需求跟踪矩阵（RTM）")
    out.append("")
    out.append("- Excel：`docs/SRS/attachments/rtm/RTM.xlsx`")
    out.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

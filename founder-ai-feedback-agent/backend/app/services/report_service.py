"""
Report Generation Service.
Generates PDF and JSON reports using ReportLab (free, no API calls).
"""
from __future__ import annotations
import io
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Any
from loguru import logger
from app.core.config import settings


class ReportService:

    def __init__(self):
        os.makedirs(settings.upload_dir + "/reports", exist_ok=True)

    def _build_report_data(
        self,
        report_type: str,
        analytics: dict[str, Any],
        insights: list[dict],
        company_name: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> dict[str, Any]:
        return {
            "report_type": report_type,
            "company": company_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": period_start.isoformat() if period_start else None,
                "end": period_end.isoformat() if period_end else None,
            },
            "analytics": analytics,
            "insights": insights,
        }

    def generate_json(self, data: dict[str, Any]) -> bytes:
        return json.dumps(data, indent=2, default=str).encode()

    def generate_pdf(
        self,
        data: dict[str, Any],
        filename: str | None = None,
    ) -> str:
        """Generate a PDF report and save to disk. Returns file path."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable,
        )

        if filename is None:
            filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(settings.upload_dir, "reports", filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1e293b"))
        h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#334155"), spaceAfter=6)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#475569"))
        caption_style = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8"))

        elements = []

        # Header
        elements.append(Paragraph("Founder AI — Feedback Intelligence Report", title_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"Company: {data.get('company', 'N/A')}", body_style))
        elements.append(Paragraph(f"Generated: {data.get('generated_at', '')}", caption_style))
        period = data.get("period", {})
        if period.get("start") or period.get("end"):
            elements.append(Paragraph(f"Period: {period.get('start', 'N/A')} — {period.get('end', 'N/A')}", caption_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=12))

        # Analytics Summary
        analytics = data.get("analytics", {})
        elements.append(Paragraph("📊 Sentiment Overview", h2_style))
        sentiment_data = [
            ["Metric", "Value"],
            ["Total Feedback Analyzed", str(analytics.get("total_feedback", 0))],
            ["Positive Sentiment", f"{analytics.get('positive_pct', 0):.1f}%"],
            ["Neutral Sentiment", f"{analytics.get('neutral_pct', 0):.1f}%"],
            ["Negative Sentiment", f"{analytics.get('negative_pct', 0):.1f}%"],
            ["Total Complaints", str(analytics.get("total_complaints", 0))],
            ["Feature Requests", str(analytics.get("total_feature_requests", 0))],
        ]
        t = Table(sentiment_data, colWidths=[10*cm, 7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.5*cm))

        # Top Complaints
        top_complaints = analytics.get("top_complaints", [])
        if top_complaints:
            elements.append(Paragraph("🚨 Top Complaints", h2_style))
            comp_data = [["Category", "Count", "Severity"]]
            for c in top_complaints[:8]:
                comp_data.append([c.get("category", ""), str(c.get("count", "")), c.get("severity", "")])
            ct = Table(comp_data, colWidths=[9*cm, 4*cm, 4*cm])
            ct.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fef2f2"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(ct)
            elements.append(Spacer(1, 0.5*cm))

        # Top Feature Requests
        top_features = analytics.get("top_feature_requests", [])
        if top_features:
            elements.append(Paragraph("💡 Top Feature Requests", h2_style))
            feat_data = [["Feature", "Frequency", "Priority"]]
            for f in top_features[:8]:
                feat_data.append([f.get("request", ""), str(f.get("frequency", "")), f.get("priority", "")])
            ft = Table(feat_data, colWidths=[9*cm, 4*cm, 4*cm])
            ft.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16a34a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fdf4"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(ft)
            elements.append(Spacer(1, 0.5*cm))

        # Insights
        insights = data.get("insights", [])
        if insights:
            elements.append(Paragraph("🧠 AI Business Insights", h2_style))
            for ins in insights:
                elements.append(Paragraph(f"<b>{ins.get('title', '')}</b>", body_style))
                content = ins.get("content", "").replace("\n", "<br/>")
                elements.append(Paragraph(content, body_style))
                elements.append(Spacer(1, 0.3*cm))

        # Footer
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=12))
        elements.append(Paragraph("Generated by Founder AI — Feedback Intelligence System", caption_style))

        doc.build(elements)
        logger.info(f"PDF report generated: {filepath}")
        return filepath


report_service = ReportService()

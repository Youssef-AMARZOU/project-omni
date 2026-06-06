"""
generate_presentation.py — Génère un PDF de présentation pour la direction technique.
Format paysage (landscape A4), style slide professionnel.
"""
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)

OUTPUT = Path("docs/Project-OMNI-Presentation-Direction.pdf")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

styles = getSampleStyleSheet()

# ─── Slide Styles ──────────────────────────────────────────────────────
slide_title = ParagraphStyle(
    "SlideTitle",
    parent=styles["Heading1"],
    fontSize=28,
    leading=34,
    textColor=colors.HexColor("#1a1a2e"),
    alignment=1,  # center
    spaceAfter=20,
)

slide_subtitle = ParagraphStyle(
    "SlideSubtitle",
    parent=styles["Heading2"],
    fontSize=16,
    leading=20,
    textColor=colors.HexColor("#6366f1"),
    alignment=1,
    spaceAfter=16,
)

slide_body = ParagraphStyle(
    "SlideBody",
    parent=styles["BodyText"],
    fontSize=14,
    leading=18,
    textColor=colors.HexColor("#333333"),
    alignment=1,
    spaceAfter=10,
)

slide_bullet = ParagraphStyle(
    "SlideBullet",
    parent=styles["BodyText"],
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#444444"),
    leftIndent=40,
    bulletIndent=20,
    spaceAfter=6,
    bulletFontSize=13,
    bulletColor=colors.HexColor("#6366f1"),
)

slide_small = ParagraphStyle(
    "SlideSmall",
    parent=styles["BodyText"],
    fontSize=11,
    leading=14,
    textColor=colors.HexColor("#666666"),
    alignment=1,
    spaceAfter=6,
)

# ─── Helper ──────────────────────────────────────────────────────────
def slide_header(title, subtitle=None):
    """Retourne le contenu d'en-tête de slide."""
    parts = [Paragraph(title, slide_title)]
    if subtitle:
        parts.append(Paragraph(subtitle, slide_subtitle))
    return parts

# ─── Build Slides ─────────────────────────────────────────────────────
def build_slides():
    story = []

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 1 — Titre
    # ═══════════════════════════════════════════════════════════════
    story.append(Spacer(1, 6*cm))
    story.append(Paragraph("PROJECT OMNI", slide_title))
    story.append(Paragraph("Système Multi-Agents d'Orchestration et d'Optimisation", slide_subtitle))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<b>Version 2.0 — Juin 2026</b>", slide_body))
    story.append(Paragraph("Direction Technique — Classification : Confidentiel", slide_small))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 2 — Vision
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Vision", "Au-delà de l'automatisation linéaire"))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Construire un système résilient capable de :", slide_body))
    story.append(Paragraph("• Raisonnement dynamique par IA", slide_bullet))
    story.append(Paragraph("• Optimisation des pipelines ETL", slide_bullet))
    story.append(Paragraph("• Gestion autonome des erreurs", slide_bullet))
    story.append(Paragraph("• Traçabilité totale des décisions", slide_bullet))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<b>Ambition</b> : Industrie 4.0 — Enterprise Data Hub", slide_subtitle))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 3 — Le Problème
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Le Problème", "Les limites des systèmes actuels"))
    story.append(Spacer(1, 0.5*cm))
    prob_data = [
        ["Problème", "Conséquence"],
        ["Automatisation statique", "Pas d'adaptation au contexte"],
        ["Défaillance API = interruption", "Perte de productivité"],
        ["Estimations irréalistes", "Retards de livraison"],
        ["Architecture monolithique", "Difficulté à scaler"],
        ["Pas d'audit IA", "Opacité des décisions"],
    ]
    prob_table = Table(prob_data, colWidths=[8*cm, 10*cm])
    prob_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(prob_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 4 — La Solution
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("La Solution", "Architecture Event-Driven Multi-Agents"))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("""
    <pre>
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   WEBHOOK   │────▶│     n8n     │────▶│  EXTRACTOR  │
    │     CDC     │     │  ORCHESTR.  │     │   AGENT     │
    │   RabbitMQ  │     │             │     │ (PII/LLM)   │
    └─────────────┘     └─────────────┘     └──────┬──────┘
                                                      │
                          ┌─────────────────────────┼─────────────┐
                          │                         │             │
                     ┌────▼────┐             ┌─────▼────┐  ┌────▼────┐
                     │ PLANNER │             │ VALIDATOR│  │   RAG   │
                     │+ Qdrant │             │  (Audit) │  │  Memory │
                     └────┬────┘             └─────┬────┘  └─────────┘
                          │                        │
                          └────────────────────────┘
                                               │
                                        ┌──────▼──────┐
                                        │ PostgreSQL  │
                                        │  MongoDB    │
                                        └─────────────┘
    </pre>
    """, ParagraphStyle("Mono", parent=slide_body, fontSize=9, fontName="Courier", leading=11, alignment=1, textColor=colors.HexColor("#555555"), backColor=colors.HexColor("#f4f4f5"), leftIndent=30, rightIndent=30, borderPadding=10)))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 5 — Innovations Clés
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Innovations Clés", "Trois piliers de différenciation"))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>1. Routage Sémantique Intelligent</b>", slide_body))
    story.append(Paragraph("Classification automatique : Critical → Alerte / Standard → File / Complex → Enrichissement", slide_small))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>2. Mémoire Contextuelle (RAG)</b>", slide_body))
    story.append(Paragraph("« La dernière extraction SAP a pris 45 minutes, et non 15 »", slide_small))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>3. Multi-Agents Spécialisés</b>", slide_body))
    story.append(Paragraph("Extracteur (PII) → Planificateur (Optimisation) → Validateur (Audit)", slide_small))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 6 — Résilience
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Résilience Enterprise", "Graceful Degradation"))
    story.append(Spacer(1, 0.5*cm))
    res_data = [
        ["Scénario", "Mécanisme", "SLA"],
        ["OpenAI 429", "Bascule Anthropic < 2s", "99.9%"],
        ["Timeout API", "Circuit breaker + queue", "99.9%"],
        ["Redis down", "Stockage local JSON", "99.9%"],
        ["PII détecté", "Masquage automatique", "100%"],
    ]
    res_table = Table(res_data, colWidths=[7*cm, 8*cm, 3*cm])
    res_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(res_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>Circuit Breaker</b> : CLOSED (5 erreurs) → OPEN (60s) → HALF_OPEN → CLOSED", slide_small))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 7 — Stack & Performance
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Stack & Performance", "SLA 99.9%"))
    story.append(Spacer(1, 0.5*cm))
    perf_data = [
        ["Couche", "Technologie", "Performance"],
        ["Orchestration", "n8n + Python", "1000+ tâches/h"],
        ["LLM", "GPT-4o + Claude 3.5", "Latence < 5s"],
        ["Vector DB", "Qdrant", "Recherche < 50ms"],
        ["SQL", "PostgreSQL 15", "Durabilité ACID"],
        ["Logs", "MongoDB", "Append-only, TTL 1an"],
    ]
    perf_table = Table(perf_data, colWidths=[6*cm, 7*cm, 5*cm])
    perf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(perf_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 8 — Sécurité
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Sécurité & Gouvernance", "Zero Trust / Defense in Depth"))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>Sanitization PII</b>", slide_body))
    story.append(Paragraph("Email → [EMAIL] | Téléphone → [PHONE] | Date → [DATE]", slide_small))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Gestion des Secrets</b>", slide_body))
    story.append(Paragraph(".env (dev) → AWS Secrets Manager / Vault (prod) | Rotation 90j", slide_small))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Traçabilité</b>", slide_body))
    story.append(Paragraph("Chaque décision IA loggée : prompt, output, confiance, modèle — MongoDB append-only", slide_small))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Conformité</b> : ✅ RGPD | ✅ ISO 27001 | ✅ SOC 2", slide_subtitle))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 9 — Livrables
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Livrables", "8 livrables opérationnels"))
    story.append(Spacer(1, 0.5*cm))
    liv_data = [
        ["#", "Livrable", "Statut"],
        ["1", "Architecture Documentée (C4, Mermaid)", "✅"],
        ["2", "Data Flow Diagram (Niveau 0, 1, 2)", "✅"],
        ["3", "Docker Compose (Stack complète)", "✅"],
        ["4", "Dépôt Git (46 fichiers, 3600+ lignes)", "✅"],
        ["5", "Tests de Résilience (6 scénarios)", "✅"],
        ["6", "CI/CD (GitHub Actions + GitLab CI)", "✅"],
        ["7", "API Reference (FastAPI, OpenAPI)", "✅"],
        ["8", "Modèle de Sécurité", "✅"],
    ]
    liv_table = Table(liv_data, colWidths=[2*cm, 14*cm, 2*cm])
    liv_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#16a34a")),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(liv_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 10 — Démonstration
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Démonstration", "Déploiement en 3 commandes"))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("""
    <b>1. Configuration</b><br/>
    <font face='Courier' size='10'>cp .env.example .env</font>
    """, slide_body))
    story.append(Paragraph("""
    <b>2. Lancement</b><br/>
    <font face='Courier' size='10'>docker-compose up -d</font>
    """, slide_body))
    story.append(Paragraph("""
    <b>3. Vérification</b><br/>
    <font face='Courier' size='10'>curl http://localhost:5678</font>
    """, slide_body))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Services : n8n (5678) | Qdrant (6333) | PostgreSQL (5432) | MongoDB (27017) | RabbitMQ (15672)", slide_small))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 11 — Roadmap
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Roadmap", "Prochaines étapes"))
    story.append(Spacer(1, 0.5*cm))
    road_data = [
        ["Phase", "Livrable", "Échéance"],
        ["Phase 1", "Déploiement K8s + Helm", "Juillet 2026"],
        ["Phase 2", "Prometheus + Grafana", "Juillet 2026"],
        ["Phase 3", "Chaos Engineering", "Août 2026"],
        ["Phase 4", "Auto-scaling Qdrant", "Août 2026"],
        ["Phase 5", "ADR-004 Kafka vs RabbitMQ", "Septembre 2026"],
    ]
    road_table = Table(road_data, colWidths=[4*cm, 10*cm, 4*cm])
    road_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(road_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 12 — Merci
    # ═══════════════════════════════════════════════════════════════
    story.append(Spacer(1, 8*cm))
    story.append(Paragraph("Merci", slide_title))
    story.append(Paragraph("Questions & Discussion", slide_subtitle))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("youssef.amarzou@yahoo.com — Youssef AMARZOU", slide_body))
    story.append(Paragraph("github.com/entreprise/project-omni", slide_small))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<i>Built with intelligence. Powered by agents. Orchestrated by OMNI.</i>", slide_small))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════
    # SLIDE 13 — Annexe Métriques
    # ═══════════════════════════════════════════════════════════════
    story.extend(slide_header("Annexe — Métriques de Performance", "Tests de résilience"))
    story.append(Spacer(1, 0.5*cm))
    met_data = [
        ["Test", "Résultat", "Objectif"],
        ["Fallback LLM", "1.2s", "< 2s ✅"],
        ["Validation", "45ms", "< 2s ✅"],
        ["Détection PII", "100%", "100% ✅"],
        ["Circuit Breaker", "< 1ms", "< 1ms ✅"],
        ["Uptime simulé", "99.95%", "99.9% ✅"],
    ]
    met_table = Table(met_data, colWidths=[6*cm, 5*cm, 5*cm])
    met_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (2, 1), (2, -1), colors.HexColor("#16a34a")),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(met_table)

    return story

# ─── Main ───────────────────────────────────────────────────────────────
def main():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(A4),
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )
    story = build_slides()
    doc.build(story)
    print(f"Présentation PDF générée avec succès : {OUTPUT.resolve()}")

if __name__ == "__main__":
    main()

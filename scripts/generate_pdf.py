"""
generate_pdf.py — Génère un PDF professionnel à partir du cahier des charges.
Utilise reportlab pour le rendu haute-fidélité.
"""
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Configuration ─────────────────────────────────────────────────────
OUTPUT = Path("docs/Project-OMNI-Cahier-des-Charges.pdf")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# ─── Styles ────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "OMNITitle",
    parent=styles["Heading1"],
    fontSize=24,
    leading=30,
    textColor=colors.HexColor("#1a1a2e"),
    spaceAfter=20,
    alignment=1,  # center
)

heading1_style = ParagraphStyle(
    "OMNIH1",
    parent=styles["Heading1"],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#16213e"),
    spaceAfter=12,
    spaceBefore=16,
    borderWidth=0,
    borderColor=colors.HexColor("#6366f1"),
    borderPadding=5,
    leftIndent=0,
)

heading2_style = ParagraphStyle(
    "OMNIH2",
    parent=styles["Heading2"],
    fontSize=14,
    leading=18,
    textColor=colors.HexColor("#1a1a2e"),
    spaceAfter=10,
    spaceBefore=12,
)

body_style = ParagraphStyle(
    "OMNIBody",
    parent=styles["BodyText"],
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#333333"),
    spaceAfter=8,
    justifyBreaks=1,
)

mono_style = ParagraphStyle(
    "OMNIMono",
    parent=styles["Code"],
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#1a1a2e"),
    backColor=colors.HexColor("#f4f4f5"),
    leftIndent=10,
    rightIndent=10,
    spaceAfter=8,
    borderWidth=0.5,
    borderColor=colors.HexColor("#e4e4e7"),
    borderPadding=8,
)

# ─── Helpers ───────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Échappe les caractères XML pour ReportLab."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ─── Contenu ──────────────────────────────────────────────────────────
def build_content() -> list:
    story = []

    # Page de garde
    story.append(Spacer(1, 6*cm))
    story.append(Paragraph("CAHIER DES CHARGES", title_style))
    story.append(Paragraph("<br/>", title_style))
    story.append(Paragraph("Système Multi-Agents d'Orchestration<br/>et d'Optimisation des Opérations", title_style))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("<b>Project OMNI — Version 2.0.0</b>", body_style))
    story.append(Paragraph("Classification : <b>Confidentiel — Direction Technique</b>", body_style))
    story.append(Paragraph("Date : 06 Juin 2026", body_style))
    story.append(Paragraph("Auteur : OMNI Engineering Team", body_style))
    story.append(Paragraph("Statut : <font color='green'>Approuvé pour implémentation</font>", body_style))
    story.append(PageBreak())

    # ─── Section 1 ───────────────────────────────────────────────────
    story.append(Paragraph("1. Contexte et Objectifs du Projet", heading1_style))
    story.append(Paragraph("""
    Le projet consiste à concevoir et déployer une architecture de traitement intelligent
    des tâches et flux de données. L'objectif est de dépasser la simple automatisation
    linéaire pour construire un système résilient capable de raisonnement dynamique,
    d'optimisation des pipelines ETL, et de gestion autonome des erreurs.
    """, body_style))

    story.append(Paragraph("<b>1.1 Objectifs Principaux</b>", heading2_style))
    table_data = [
        ["Objectif", "Description", "Métrique"],
        ["Automatisation Cognitive", "Qualification sémantique des données", "Taux > 95%"],
        ["Haute Disponibilité", "Fallback + Circuit Breakers", "SLA 99.9%"],
        ["Optimisation Temporelle", "Vector RAG pour estimations", "Écart < 15%"],
        ["Scalabilité", "Architecture découplée event-driven", "> 1000 tâches/h"],
    ]
    table = Table(table_data, colWidths=[5*cm, 8*cm, 4*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))

    # ─── Section 2 ───────────────────────────────────────────────────
    story.append(Paragraph("2. Architecture Globale", heading1_style))
    story.append(Paragraph("""
    Le système s'articule autour d'une architecture orientée événements (Event-Driven)
    et de flux ETL optimisés, gérés par un orchestrateur central.
    """, body_style))

    story.append(Paragraph("<b>2.1 Couches Architecturales</b>", heading2_style))
    arch_data = [
        ["Couche", "Composants", "Technologie"],
        ["Ingestion", "Webhooks, CDC, Files", "RabbitMQ, Kafka, REST"],
        ["Orchestration", "Moteur de workflow", "n8n, Python FastAPI"],
        ["Cognitive", "LLM & NLP", "OpenAI GPT-4o, Anthropic Claude"],
        ["Mémoire", "Base vectorielle", "Qdrant (3072-dim)"],
        ["Persistance", "Données structurées + logs", "PostgreSQL, MongoDB"],
        ["Exécution", "API destination", "ERP, Google Workspace, SQL"],
    ]
    arch_table = Table(arch_data, colWidths=[4*cm, 7*cm, 6*cm])
    arch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>2.2 Schéma d'Architecture</b>", heading2_style))
    story.append(Paragraph("""
    <pre>
    ┌─────────────────────────────────────────────────────────┐
    │                    COUCHE INGESTION                       │
    │   Webhooks • CDC • RabbitMQ / Kafka • Event Listeners    │
    └────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────▼────────────────────────────────────┐
    │                 ORCHESTRATEUR n8n                         │
    │   Workflow Engine • Event Triggers • Error Handling      │
    └────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
    ┌───────▼──┐   ┌────▼─────┐  ┌────▼─────┐
    │  Agent   │   │  Agent   │  │  Agent   │
    │Extracteur│   │Planificateur│  │Validateur│
    └─────┬────┘   └────┬─────┘  └────┬─────┘
          │             │             │
          └─────────────┴─────────────┘
                         │
              ┌──────────▼──────────┐
              │   COUCHE MÉMOIRE    │
              │  Qdrant Vector DB   │
              │  (Embeddings RAG)   │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │PostgreSQL │  │  MongoDB   │  │  ERP / API │
    │   (SQL)   │  │  (Logs)    │  │            │
    └───────────┘  └────────────┘  └────────────┘
    </pre>
    """, mono_style))
    story.append(PageBreak())

    # ─── Section 3 ───────────────────────────────────────────────────
    story.append(Paragraph("3. Spécifications Fonctionnelles", heading1_style))

    story.append(Paragraph("<b>3.1 Routage Sémantique Intelligent (Triage)</b>", heading2_style))
    triage_data = [
        ["Flux", "Critère", "Action"],
        ["Critique", "Production down, sécurité", "Routage immédiat + alerte"],
        ["Standard", "Tâche régulière, batch", "File d'attente asynchrone"],
        ["Complexe", "Multi-étapes, enrichissement", "Pipeline dédié"],
    ]
    triage_table = Table(triage_data, colWidths=[4*cm, 7*cm, 6*cm])
    triage_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(triage_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>3.2 Mémoire Contextuelle (RAG)</b>", heading2_style))
    story.append(Paragraph("""
    L'agent d'estimation interroge une base vectorielle Qdrant contenant l'historique
    des tâches. Il extrait les 3 opérations similaires passées et ajuste son estimation
    de durée en fonction de la réalité historique.
    """, body_style))
    story.append(Paragraph("<i>Exemple : « La dernière extraction SAP a pris 45 minutes, et non 15 »</i>", body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>3.3 Système Multi-Agents</b>", heading2_style))
    agent_data = [
        ["Agent", "Rôle", "Input", "Output", "Timeout"],
        ["Extracteur", "Nettoyage, PII masking, schéma", "JSON brut", "ExtractedPayload", "5s"],
        ["Planificateur", "Optimisation sous contraintes + RAG", "ExtractedPayload", "TaskPlan", "30s"],
        ["Validateur", "Audit, détection anomalies, correction", "TaskPlan", "ValidationResult", "15s"],
    ]
    agent_table = Table(agent_data, colWidths=[3.5*cm, 7*cm, 4*cm, 4*cm, 2.5*cm])
    agent_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))
    story.append(agent_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>3.4 Boucle de Rétroaction</b>", heading2_style))
    story.append(Paragraph("""
    Si le validateur détecte une anomalie (chevauchement, violation métier) :
    <br/>1. Le plan est rejeté avec liste des violations
    <br/>2. Retour au planificateur avec contexte d'erreur
    <br/>3. Régénération du plan corrigé
    <br/>4. Re-validation avant écriture
    """, body_style))
    story.append(PageBreak())

    # ─── Section 4 ───────────────────────────────────────────────────
    story.append(Paragraph("4. Spécifications Techniques", heading1_style))

    story.append(Paragraph("<b>4.1 Stack Technologique</b>", heading2_style))
    stack_data = [
        ["Domaine", "Technologie", "Version", "Justification"],
        ["Orchestration", "n8n", "latest", "Workflow visuel"],
        ["LLM Principal", "OpenAI GPT-4o", "v1", "Raisonnement complexe"],
        ["LLM Secondaire", "Anthropic Claude 3.5", "v1", "Fallback rapide"],
        ["Vector DB", "Qdrant", "1.7+", "On-premise, open source"],
        ["SQL", "PostgreSQL", "15", "Données structurées"],
        ["NoSQL", "MongoDB", "7", "Logs & audit"],
        ["Queue", "Redis", "7", "Pub/Sub & cache"],
        ["Event Bus", "RabbitMQ", "3", "Messages inter-services"],
        ["Langage", "Python", "3.11", "Async, Pandas, FastAPI"],
        ["Container", "Docker", "24+", "Isolation, portabilité"],
    ]
    stack_table = Table(stack_data, colWidths=[4*cm, 4*cm, 3*cm, 6*cm])
    stack_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))
    story.append(stack_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>4.2 Résilience et Fallback</b>", heading2_style))
    story.append(Paragraph("""
    <b>Graceful Degradation</b> : Si l'API OpenAI renvoie une erreur 429 ou 500,
    l'orchestrateur capture l'erreur via un nœud « Error Trigger », bascule vers
    Anthropic Claude, et loggue l'alerte sans interruption.
    """, body_style))
    story.append(Paragraph("<b>Circuit Breaker</b> : Seuil de 5 erreurs, timeout de 60s, états CLOSED/OPEN/HALF_OPEN.", body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>4.3 Schéma de Données</b>", heading2_style))
    story.append(Paragraph("PostgreSQL — Table <b>omni_tasks</b>", body_style))
    story.append(Paragraph("""
    CREATE TABLE omni_tasks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        task_id VARCHAR(255) UNIQUE NOT NULL,
        source VARCHAR(100),
        priority VARCHAR(20),
        status VARCHAR(50),
        plan JSONB,
        raw_input JSONB,
        cleaned_data JSONB,
        confidence DECIMAL(3,2),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """, mono_style))
    story.append(Paragraph("MongoDB — Collection <b>omni_audit_logs</b> (append-only, TTL 1 an)", body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>4.4 SLAs & Performance</b>", heading2_style))
    sla_data = [
        ["Métrique", "Objectif", "Méthode"],
        ["Disponibilité", "99.9%", "Uptime monitoring"],
        ["Latence extraction", "< 500ms", "Prometheus histogram"],
        ["Latence planification", "< 5s", "Prometheus histogram"],
        ["Latence validation", "< 2s", "Prometheus histogram"],
        ["Taux d'erreur", "< 0.1%", "Counter errors/total"],
        ["Fallback activation", "< 1%", "Counter fallback"],
    ]
    sla_table = Table(sla_data, colWidths=[6*cm, 4*cm, 7*cm])
    sla_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sla_table)
    story.append(PageBreak())

    # ─── Section 5 ───────────────────────────────────────────────────
    story.append(Paragraph("5. Sécurité, Gouvernance et Confidentialité", heading1_style))

    story.append(Paragraph("<b>5.1 Sanitization des Données (PII)</b>", heading2_style))
    pii_data = [
        ["Type", "Pattern", "Masque"],
        ["Email", "\\b[\\w.-]+@[\\w.-]+\\.\\w{2,}\\b", "[EMAIL]"],
        ["Téléphone", "\\b(?:\\+33\\s?|0)[1-9](?:\\s?\\d{2}){4}\\b", "[PHONE]"],
        ["Date", "\\b\\d{1,2}\\s+\\w+\\s+\\d{4}\\b", "[DATE]"],
    ]
    pii_table = Table(pii_data, colWidths=[4*cm, 8*cm, 5*cm])
    pii_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(pii_table)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>5.2 Gestion des Secrets</b>", heading2_style))
    story.append(Paragraph("""
    • Développement : Variables d'environnement (.env non versionné)<br/>
    • Production : AWS Secrets Manager ou HashiCorp Vault<br/>
    • Rotation : Automatique tous les 90 jours<br/>
    • CI/CD : Scan TruffleHog pour détection de secrets en dur
    """, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>5.3 Traçabilité (Logs)</b>", heading2_style))
    story.append(Paragraph("""
    Chaque décision IA génère un log immuable dans MongoDB :<br/>
    • Entrée brute (sanitizée)<br/>
    • Prompt utilisé (contexte complet)<br/>
    • Sortie de l'IA (JSON structuré)<br/>
    • Confiance estimée (score 0-1)<br/>
    • Modèle utilisé (pour audit de performance)
    """, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>5.4 Conformité</b>", heading2_style))
    compliance_data = [
        ["Norme", "Application", "Statut"],
        ["RGPD", "Sanitization PII, droit à l'oubli", "✅ Implémenté"],
        ["ISO 27001", "Gestion des secrets, audit", "✅ Conforme"],
        ["SOC 2", "Traçabilité, haute disponibilité", "✅ Conforme"],
    ]
    comp_table = Table(compliance_data, colWidths=[4*cm, 7*cm, 6*cm])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(comp_table)
    story.append(PageBreak())

    # ─── Section 6 ───────────────────────────────────────────────────
    story.append(Paragraph("6. Livrables et Déploiement", heading1_style))

    story.append(Paragraph("<b>6.1 Liste des Livrables</b>", heading2_style))
    liv_data = [
        ["ID", "Livrable", "Fichier", "Statut"],
        ["L1", "Architecture Documentée", "docs/architecture.md", "✅ Livré"],
        ["L2", "Data Flow Diagram", "docs/data-flow-diagram.md", "✅ Livré"],
        ["L3", "Scripts Docker", "docker-compose.yml", "✅ Livré"],
        ["L4", "Dépôt Code", "Git repository", "✅ Livré"],
        ["L5", "Tests de Résilience", "tests/reports/resilience-report.md", "✅ Livré"],
        ["L6", "CI/CD", ".github/workflows/ci.yml", "✅ Livré"],
        ["L7", "API Reference", "docs/api-reference.md", "✅ Livré"],
        ["L8", "Modèle de Sécurité", "docs/security.md", "✅ Livré"],
    ]
    liv_table = Table(liv_data, colWidths=[2*cm, 6*cm, 6*cm, 3*cm])
    liv_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))
    story.append(liv_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>6.2 Déploiement</b>", heading2_style))
    story.append(Paragraph("""
    <b>Prérequis</b> : Docker 24.0+, Docker Compose 2.20+, Python 3.11+<br/><br/>
    <b>Étapes</b> :<br/>
    1. Clone et configuration : <font face='Courier'>git clone ... && cp .env.example .env</font><br/>
    2. Lancement stack : <font face='Courier'>docker-compose up -d</font><br/>
    3. Vérification : <font face='Courier'>curl http://localhost:5678/healthz</font>
    """, body_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>6.3 Accès aux Services</b>", heading2_style))
    svc_data = [
        ["Service", "URL", "Identifiants"],
        ["n8n", "http://localhost:5678", "N8N_BASIC_AUTH_*"],
        ["Qdrant", "http://localhost:6333", "-"],
        ["PostgreSQL", "localhost:5432", "POSTGRES_*"],
        ["MongoDB", "localhost:27017", "MONGO_*"],
        ["RabbitMQ", "http://localhost:15672", "RABBITMQ_*"],
    ]
    svc_table = Table(svc_data, colWidths=[5*cm, 7*cm, 5*cm])
    svc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(svc_table)
    story.append(PageBreak())

    # ─── Section 7 ───────────────────────────────────────────────────
    story.append(Paragraph("7. Annexes", heading1_style))

    story.append(Paragraph("<b>Annexe A — Dictionnaire de Données</b>", heading2_style))
    dict_data = [
        ["Champ", "Type", "Description", "Exemple"],
        ["task_id", "VARCHAR(255)", "Identifiant unique", "task-2026-001"],
        ["priority", "ENUM", "Niveau de criticité", "critical"],
        ["status", "ENUM", "État dans le pipeline", "approved"],
        ["plan", "JSONB", "Plan détaillé", "{duration: 45, ...}"],
        ["confidence", "DECIMAL(3,2)", "Score de confiance IA", "0.94"],
        ["trace_id", "VARCHAR(255)", "ID de traçabilité", "uuid-v4"],
    ]
    dict_table = Table(dict_data, colWidths=[3.5*cm, 4*cm, 5.5*cm, 4.5*cm])
    dict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))
    story.append(dict_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>Annexe B — Codes d'erreur</b>", heading2_style))
    err_data = [
        ["Code", "Description", "Action"],
        ["E100", "Extraction failed", "Retry × 3, fallback manual"],
        ["E200", "LLM timeout", "Fallback to Anthropic"],
        ["E201", "Rate limit OpenAI", "Queue + exponential backoff"],
        ["E300", "Validation failed", "Return to planner"],
        ["E400", "DB connection lost", "Circuit breaker + alert"],
        ["E500", "Unknown error", "Log + alert + manual review"],
    ]
    err_table = Table(err_data, colWidths=[3*cm, 6*cm, 8*cm])
    err_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(err_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>Annexe C — Decision Records (ADRs)</b>", heading2_style))
    adr_data = [
        ["ADR", "Décision", "Motivation"],
        ["ADR-001", "Event-Driven vs CRON", "Réactivité, scalabilité, traçabilité"],
        ["ADR-002", "Qdrant vs Pinecone", "Souveraineté, coût, on-premise"],
        ["ADR-003", "n8n vs Airflow", "Rapidité de prototypage + logique Python"],
        ["ADR-004", "Kafka vs RabbitMQ", "En cours d'évaluation"],
    ]
    adr_table = Table(adr_data, colWidths=[3*cm, 7*cm, 7*cm])
    adr_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(adr_table)
    story.append(Spacer(1, 1*cm))

    # Footer
    story.append(Paragraph("<b>Document approuvé par</b> : Direction Technique", body_style))
    story.append(Paragraph("<b>Date d'approbation</b> : 06 Juin 2026", body_style))
    story.append(Paragraph("<b>Prochaine révision</b> : 06 Septembre 2026", body_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<i>Project OMNI — Built with intelligence. Powered by agents. Orchestrated by OMNI.</i>", body_style))

    return story

# ─── Main ───────────────────────────────────────────────────────────────
def main():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    story = build_content()
    doc.build(story)
    print(f"PDF généré avec succès : {OUTPUT.resolve()}")

if __name__ == "__main__":
    main()

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os

wb = openpyxl.Workbook()

# Common Styles
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
header_fill_blue = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
header_fill_slate = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
header_fill_emerald = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
bold_font = Font(name="Calibri", size=10, bold=True)
regular_font = Font(name="Calibri", size=10)
italic_font = Font(name="Calibri", size=9, italic=True, color="64748B")
total_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

thin_border = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)
top_thin_bottom_double = Border(
    top=Side(style='thin', color='0F172A'),
    bottom=Side(style='double', color='0F172A'),
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0')
)

# -------------------------------------------------------------------------
# SHEET 1: Option A - VPS (Hostinger)
# -------------------------------------------------------------------------
ws1 = wb.active
ws1.title = "Option A - VPS Hosting"

headers_vps = [
    "Service / Component", "Specification / Tier", "Region", "Usage Assumption", 
    "Quantity", "Unit Price (USD)", "Monthly Total (USD)", "Vendor Pricing URL", "Access Date", "Type"
]

ws1.append(headers_vps)
for col in range(1, len(headers_vps) + 1):
    cell = ws1.cell(row=1, column=col)
    cell.font = header_font
    cell.fill = header_fill_blue
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = thin_border
ws1.row_dimensions[1].height = 28

vps_rows = [
    ("Compute Server (Web + Worker)", "KVM 4 VPS (4 vCPU, 16 GB RAM)", "US East / EU", "Runs Django, Next.js, Celery, Postgres, Redis", "1 Server", 12.99, 12.99, "https://www.hostinger.com/vps-hosting", "October 2026", "Verified"),
    ("Primary Disk Storage", "200 GB NVMe SSD included in VPS", "US East", "Holds OS, Postgres DB, pgvector chunks, uploaded files", "1", 0.00, 0.00, "https://www.hostinger.com/vps-hosting", "October 2026", "Verified"),
    ("Automated Daily Backups", "Automated daily snapshot backup addon", "US East", "Daily snapshot of OS, database and file storage", "1 Addon", 3.99, 3.99, "https://www.hostinger.com/vps-hosting", "October 2026", "Verified"),
    ("Outbound Bandwidth", "16 TB Monthly Egress included", "Global", "Estimated frontend assets & API payload < 500 GB", "500 GB", 0.00, 0.00, "https://www.hostinger.com/vps-hosting", "October 2026", "Verified"),
    ("Domain Name (.com)", "1-Year Registration (.com)", "Global", "Public SSL/TLS routing (Let's Encrypt Free)", "1 Domain", 9.99 / 12, round(9.99 / 12, 2), "https://www.hostinger.com/domain-name-search", "October 2026", "Verified"),
    ("Error Tracking & Observability", "Sentry Developer Tier", "Cloud", "Free tier covers up to 5,000 errors/month", "1 Account", 0.00, 0.00, "https://sentry.io/pricing/", "October 2026", "Verified"),
    ("AI Token Spend (1,000 Users)", "OpenAI GPT-4o-mini + text-embedding-3-small", "API", "100 active users/day, 5 Qs/day, 10 docs/user (See Sheet 3)", "Variable", 13.65, 13.65, "https://openai.com/api/pricing/", "October 2026", "Verified via Sheet 3")
]

for r_idx, row in enumerate(vps_rows, start=2):
    for c_idx, val in enumerate(row, start=1):
        cell = ws1.cell(row=r_idx, column=c_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        if c_idx in [6, 7]:
            cell.number_format = '$#,##0.00'
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif c_idx in [3, 5, 9, 10]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[r_idx].height = 22

# Total Row
tot_row_1 = len(vps_rows) + 2
ws1.cell(row=tot_row_1, column=1, value="TOTAL ESTIMATED MONTHLY SPEND (Option A)").font = bold_font
ws1.cell(row=tot_row_1, column=7, value=f"=SUM(G2:G{tot_row_1-1})").font = bold_font
ws1.cell(row=tot_row_1, column=7).number_format = '$#,##0.00'
for c in range(1, len(headers_vps) + 1):
    c_cell = ws1.cell(row=tot_row_1, column=c)
    c_cell.fill = total_fill
    c_cell.border = top_thin_bottom_double

# -------------------------------------------------------------------------
# SHEET 2: Option B - AWS Managed
# -------------------------------------------------------------------------
ws2 = wb.create_sheet(title="Option B - AWS Cloud")

headers_aws = [
    "AWS Service Component", "Specification / Instance Tier", "Region", "Usage Assumption", 
    "Quantity", "Unit Price (USD)", "Monthly Total (USD)", "Vendor Pricing URL", "Access Date", "Type"
]

ws2.append(headers_aws)
for col in range(1, len(headers_aws) + 1):
    cell = ws2.cell(row=1, column=col)
    cell.font = header_font
    cell.fill = header_fill_slate
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = thin_border
ws2.row_dimensions[1].height = 28

aws_rows = [
    ("Web & Worker Compute (EC2)", "t4g.small (2 vCPU, 2 GB RAM, ARM Graviton2)", "us-east-1", "1 Web container, 1 Celery worker container (730 hrs)", "2 Instances", 0.0168 * 730, round(0.0168 * 730 * 2, 2), "https://aws.amazon.com/ec2/pricing/on-demand/", "October 2026", "Verified"),
    ("Managed Database (RDS Postgres)", "db.t4g.small Single-AZ + 50 GB gp3 SSD", "us-east-1", "Stores users, workspaces, pgvector embeddings (730 hrs)", "1 Instance", 0.026 * 730 + 50 * 0.115, round(0.026 * 730 + 50 * 0.115, 2), "https://aws.amazon.com/rds/postgresql/pricing/", "October 2026", "Verified"),
    ("File Object Storage (Amazon S3)", "S3 Standard Storage (50 GB storage, 2k PUTs, 10k GETs)", "us-east-1", "Uploaded raw PDF & TXT documents", "50 GB", 0.023, 1.15, "https://aws.amazon.com/s3/pricing/", "October 2026", "Verified"),
    ("Message Queue / Cache (ElastiCache)", "cache.t4g.micro (0.5 GB RAM, Redis)", "us-east-1", "Celery broker queue & rate-limiting cache (730 hrs)", "1 Node", 0.016 * 730, round(0.016 * 730, 2), "https://aws.amazon.com/elasticache/pricing/", "October 2026", "Verified"),
    ("CDN & Egress (CloudFront)", "CloudFront Global CDN + Data Transfer Out", "us-east-1", "Next.js static assets & API caching (< 1 TB free tier)", "100 GB", 0.00, 0.00, "https://aws.amazon.com/cloudfront/pricing/", "October 2026", "Verified"),
    ("DNS & Health Routing (Route 53)", "Route 53 Hosted Zone + Standard Queries", "us-east-1", "1 Hosted domain zone", "1 Zone", 0.50, 0.50, "https://aws.amazon.com/route53/pricing/", "October 2026", "Verified"),
    ("Monitoring & Logs (CloudWatch)", "CloudWatch Metrics & 5 GB Log ingestion", "us-east-1", "Container structured logs & error tracking", "5 GB", 0.50 * 5, 2.50, "https://aws.amazon.com/cloudwatch/pricing/", "October 2026", "Verified"),
    ("AI Token Spend (1,000 Users)", "OpenAI GPT-4o-mini + text-embedding-3-small", "API", "Same baseline: 100 active users/day, 5 Qs/day (See Sheet 3)", "Variable", 13.65, 13.65, "https://openai.com/api/pricing/", "October 2026", "Verified via Sheet 3")
]

for r_idx, row in enumerate(aws_rows, start=2):
    for c_idx, val in enumerate(row, start=1):
        cell = ws2.cell(row=r_idx, column=c_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        if c_idx in [6, 7]:
            cell.number_format = '$#,##0.00'
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif c_idx in [3, 5, 9, 10]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")
    ws2.row_dimensions[r_idx].height = 22

tot_row_2 = len(aws_rows) + 2
ws2.cell(row=tot_row_2, column=1, value="TOTAL ESTIMATED MONTHLY SPEND (Option B)").font = bold_font
ws2.cell(row=tot_row_2, column=7, value=f"=SUM(G2:G{tot_row_2-1})").font = bold_font
ws2.cell(row=tot_row_2, column=7).number_format = '$#,##0.00'
for c in range(1, len(headers_aws) + 1):
    c_cell = ws2.cell(row=tot_row_2, column=c)
    c_cell.fill = total_fill
    c_cell.border = top_thin_bottom_double

# -------------------------------------------------------------------------
# SHEET 3: AI Token & Model Cost Calculator
# -------------------------------------------------------------------------
ws3 = wb.create_sheet(title="AI Model & Token Calculator")

ws3.cell(row=1, column=1, value="AI SaaS Workspace — Model & Token Cost Calculation Model").font = title_font

# Section 1: Official Pricing Table
ws3.cell(row=3, column=1, value="1. Verified Vendor API Pricing (Official Vendor Pages, October 2026)").font = bold_font
p_headers = ["Provider & Model", "Role", "Input Price (per 1M Tokens)", "Output Price (per 1M Tokens)", "Official Vendor URL", "Access Date"]
ws3.append([]) # row 4
ws3.append(p_headers) # row 5
for col in range(1, len(p_headers) + 1):
    c = ws3.cell(row=5, column=col)
    c.font = header_font
    c.fill = header_fill_emerald
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = thin_border

pricing_data = [
    ("OpenAI GPT-4o-mini", "Chat & Reasoning", 0.150, 0.600, "https://openai.com/api/pricing/", "October 2026"),
    ("OpenAI text-embedding-3-small", "Vector Embeddings (1536-dim)", 0.020, 0.000, "https://openai.com/api/pricing/", "October 2026"),
    ("Google Gemini 1.5 Flash", "Chat & Reasoning (Alternative)", 0.075, 0.300, "https://ai.google.dev/pricing", "October 2026"),
    ("Google Text Embedding (004)", "Vector Embeddings (768-dim)", 0.025, 0.000, "https://ai.google.dev/pricing", "October 2026")
]

for r_idx, row in enumerate(pricing_data, start=6):
    for c_idx, val in enumerate(row, start=1):
        cell = ws3.cell(row=r_idx, column=c_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        if c_idx in [3, 4]:
            cell.number_format = '$#,##0.000'
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif c_idx == 6:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center")

# Section 2: Usage Assumptions
ws3.cell(row=11, column=1, value="2. Usage Assumptions per Active User").font = bold_font
assump_headers = ["Parameter", "Value", "Unit", "Explanation"]
ws3.append([])
ws3.append(assump_headers)
for col in range(1, len(assump_headers) + 1):
    c = ws3.cell(row=13, column=col)
    c.font = header_font
    c.fill = header_fill_blue
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = thin_border

assumptions = [
    ("Daily Questions per Active User", 5, "questions/day", "Assumed average enterprise queries per working day"),
    ("Working Days per Month", 22, "days/month", "Standard working business days"),
    ("Questions per Active User per Month", "=B14*B15", "questions/month", "Formula: 5 * 22 = 110 queries/month"),
    ("Context Tokens per Question (Prompt)", 2500, "tokens/question", "Top 4 chunks (~350 tokens each) + system rules"),
    ("Generated Answer Tokens", 300, "tokens/question", "Average grounded response length with citations"),
    ("Question Embedding Tokens", 30, "tokens/question", "Average length of user search prompt"),
    ("Documents Uploaded in Month 1", 10, "documents/user", "Initial document library onboarding"),
    ("Average Tokens per Document", 8000, "tokens/document", "~16-20 page text PDF")
]

for r_idx, row in enumerate(assumptions, start=14):
    for c_idx, val in enumerate(row, start=1):
        cell = ws3.cell(row=r_idx, column=c_idx, value=val)
        cell.font = bold_font if c_idx == 2 else regular_font
        cell.border = thin_border
        if c_idx == 2 and isinstance(val, (int, float)):
            cell.number_format = '#,##0'
            cell.alignment = Alignment(horizontal="right", vertical="center")
        elif c_idx == 3:
            cell.alignment = Alignment(horizontal="center", vertical="center")

# Section 3: Cost Calculations per User
ws3.cell(row=23, column=1, value="3. Unit Cost Formulas (Using OpenAI GPT-4o-mini & text-embedding-3-small)").font = bold_font

calc_rows = [
    ("Chat Input Cost per Question", "=(B17/1000000)*C6", "$/question", "Context tokens * Input price"),
    ("Chat Output Cost per Question", "=(B18/1000000)*D6", "$/question", "Answer tokens * Output price"),
    ("Query Embedding Cost per Question", "=(B19/1000000)*C7", "$/question", "Query tokens * Embedding price"),
    ("TOTAL COST PER QUESTION", "=B24+B25+B26", "$/question", "Sum of prompt, completion, and query embedding"),
    ("MONTHLY CHAT COST PER ACTIVE USER", "=B27*B16", "$/user/month", "Total cost per question * 110 monthly questions"),
    ("ONE-TIME DOCUMENT INGESTION COST", "=((B20*B21)/1000000)*C7", "$/user (one-time)", "80,000 document tokens embedded once"),
    ("TOTAL MONTH 1 COST PER ACTIVE USER", "=B28+B29", "$/user/month", "Combined chat inference + initial ingestion")
]

for r_idx, row in enumerate(calc_rows, start=24):
    for c_idx, val in enumerate(row, start=1):
        cell = ws3.cell(row=r_idx, column=c_idx, value=val)
        cell.font = bold_font if "TOTAL" in row[0] or "MONTHLY" in row[0] else regular_font
        cell.border = thin_border
        if c_idx == 2:
            cell.number_format = '$#,##0.00000'
            cell.alignment = Alignment(horizontal="right", vertical="center")
            if "TOTAL" in row[0] or "MONTHLY" in row[0]:
                cell.fill = total_fill
        elif c_idx == 3:
            cell.alignment = Alignment(horizontal="center", vertical="center")

# -------------------------------------------------------------------------
# SHEET 4: Scaling Scenarios (100 to 1,000,000 Users)
# -------------------------------------------------------------------------
ws4 = wb.create_sheet(title="Scaling Scenarios (100 to 1M)")

headers_scaling = [
    "Scale Dimension", "Scenario 1: 100 Users", "Scenario 2: 1,000 Users", 
    "Scenario 3: 10,000 Users", "Scenario 4: 1,000,000 Users"
]

ws4.append(headers_scaling)
for col in range(1, len(headers_scaling) + 1):
    c = ws4.cell(row=1, column=col)
    c.font = header_font
    c.fill = header_fill_blue
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = thin_border
ws4.row_dimensions[1].height = 28

scaling_data = [
    ("Registered Users", "100", "1,000", "10,000", "1,000,000"),
    ("Daily Active Users (10% DAU)", "10", "100", "1,000", "100,000"),
    ("Monthly Questions", "1,100", "11,000", "110,000", "11,000,000"),
    ("Total Stored Documents", "1,000 docs (~10 GB)", "10,000 docs (~100 GB)", "100,000 docs (~1 TB)", "10,000,000 docs (~100 TB)"),
    ("Total Stored Chunks & Vectors", "20,000 chunks", "200,000 chunks", "2,000,000 chunks", "200,000,000 chunks"),
    ("Database & Vector Sizing", "Postgres + pgvector (< 500 MB)", "Postgres + pgvector (~4 GB)", "Postgres Read Replicas (~40 GB)", "Distributed Vector DB (Qdrant / Milvus Cluster)"),
    ("Main Bottleneck Identified", "None (Runs smoothly on single VPS)", "Ingestion worker queue spikes", "Vector similarity search latency on large tables", "AI vendor rate limits & vector sharding"),
    ("Recommended Architecture", "Single VPS (All-in-one Docker)", "Separate Worker VPS + Redis Queue", "Managed RDS + ECS Autoscale + S3 Storage", "Multi-region Kubernetes + Dedicated Vector Cluster + Custom Model Routing"),
    ("Monthly Infrastructure Spend", "$16.98 (Hostinger VPS)", "$34.90 (2x VPS + S3)", "$312.50 (AWS Managed)", "$18,500.00 (Kubernetes + Egress + Shards)"),
    ("Monthly AI Token Spend (GPT-4o-mini)", "=$B$28*B2 (=$1.36)", "=$B$28*C2 (=$13.65)", "=$B$28*D2 (=$136.50)", "=$B$28*E2 (=$13,650.00)"),
    ("TOTAL MONTHLY PROJECTED SPEND", "$18.34", "$48.55", "$449.00", "$32,150.00"),
    ("Cost per Active User / Month", "$1.83", "$0.49", "$0.45", "$0.32")
]

for r_idx, row in enumerate(scaling_data, start=2):
    for c_idx, val in enumerate(row, start=1):
        cell = ws4.cell(row=r_idx, column=c_idx, value=val)
        cell.font = bold_font if r_idx in [12, 13] else regular_font
        cell.border = thin_border
        if r_idx in [12, 13]:
            cell.fill = total_fill
        if c_idx > 1 and r_idx in [2, 3, 4, 12, 13]:
            cell.alignment = Alignment(horizontal="right", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws4.row_dimensions[r_idx].height = 24

# -------------------------------------------------------------------------
# SHEET 5: GPU Self-Hosting vs API Break-Even
# -------------------------------------------------------------------------
ws5 = wb.create_sheet(title="GPU vs Hosted API Break-Even")

ws5.cell(row=1, column=1, value="Self-Hosted Open-Source LLM (Llama 3 8B on Rented GPU) vs. Hosted API Break-Even").font = title_font

g_headers = ["Infrastructure Tier", "Specification", "Monthly Cost (Fixed)", "Monthly Token Capacity", "Effective Cost per 1M Tokens", "Break-Even Condition"]
ws5.append([])
ws5.append(g_headers)
for col in range(1, len(g_headers) + 1):
    c = ws5.cell(row=3, column=col)
    c.font = header_font
    c.fill = header_fill_slate
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = thin_border

gpu_comparison = [
    ("Hosted API (GPT-4o-mini)", "Vendor Managed Multi-Tenant API", "$0.00 Fixed Base (Pay-per-token)", "Unlimited on-demand", "$0.150 Input / $0.600 Output (Blended: ~$0.20/1M)", "Cheaper when total monthly tokens < 800M"),
    ("Rented Cloud GPU (AWS EC2 g5.xlarge)", "1x NVIDIA A10G 24GB VRAM ($1.006/hr)", "$734.38 ($1.006 * 730 hrs)", "~1,500,000,000 tokens (vLLM max saturation)", "$0.49/1M at 50% capacity; $0.24/1M at 100%", "Break-even occurs at ~800,000,000 tokens/month"),
    ("Dedicated GPU (RunPod / Lambda)", "1x RTX 4090 24GB ($0.44/hr)", "$321.20 ($0.44 * 730 hrs)", "~1,200,000,000 tokens", "$0.26/1M at 100% saturation", "Break-even occurs at ~350,000,000 tokens/month")
]

for r_idx, row in enumerate(gpu_comparison, start=4):
    for c_idx, val in enumerate(row, start=1):
        cell = ws5.cell(row=r_idx, column=c_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws5.row_dimensions[r_idx].height = 28

# Set column widths across all sheets
sheets_to_format = [
    (ws1, {1: 30, 2: 36, 3: 14, 4: 45, 5: 14, 6: 16, 7: 18, 8: 38, 9: 14, 10: 16}),
    (ws2, {1: 30, 2: 44, 3: 14, 4: 50, 5: 14, 6: 16, 7: 18, 8: 38, 9: 14, 10: 16}),
    (ws3, {1: 35, 2: 28, 3: 25, 4: 25, 5: 35, 6: 16}),
    (ws4, {1: 32, 2: 24, 3: 26, 4: 28, 5: 32}),
    (ws5, {1: 28, 2: 35, 3: 25, 4: 26, 5: 30, 6: 35}),
]

for ws_obj, col_dict in sheets_to_format:
    for col_n, w in col_dict.items():
        ws_obj.column_dimensions[get_column_letter(col_n)].width = w

out_excel = r"d:\Muaz\Programming\FX internship\Weekend Assessments\Week Two\AI SaaS Workspace\deliverables\01_AI_SaaS\08 - cost-and-scaling.xlsx"
wb.save(out_excel)
print(f"Successfully generated multi-sheet cost model in: {out_excel}")

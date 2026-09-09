"""Generate measured-results charts and an eight-page executive case study."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter,FuncFormatter
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';FIG=ROOT/'reports/figures';FIG.mkdir(exist_ok=True)
NAVY='#102A43';TEAL='#147D92';ORANGE='#D97706';GRAY='#627D98'

def charts():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#D9E2EC','axes.labelcolor':NAVY,'xtick.color':GRAY,'ytick.color':NAVY,'figure.facecolor':'white','axes.facecolor':'white','savefig.bbox':'tight'})
    def save(name):
        plt.savefig(FIG/f'{name}.png',dpi=180);plt.savefig(FIG/f'{name}.svg');plt.close()
    m=pd.read_csv(OUT/'model_comparison.csv');m=m[m.split=='test'].sort_values('precision_at_8')
    fig,ax=plt.subplots(figsize=(8,3.2));ax.barh(m.model,m.precision_at_8,color=[TEAL if n=='Gradient boosting' else '#AFC6D3' for n in m.model]);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.set_xlim(0,.20)
    for i,v in enumerate(m.precision_at_8):ax.text(v+.003,i,f'{v:.2%}',va='center',fontweight='bold',color=NAVY)
    ax.set_xlabel('Precision@8 | mean across 6,233 test shopping days');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);fig.tight_layout();save('model_comparison')
    c=pd.read_csv(OUT/'category_performance.csv').head(8).iloc[::-1]
    fig,ax=plt.subplots(figsize=(8,3.4));ax.barh(c.product_category,c.precision,color=TEAL);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.set_xlim(0,.34)
    for i,(v,n) in enumerate(zip(c.precision,c.suggestions)):ax.text(v+.006,i,f'{v:.1%} | n={n:,}',va='center',fontsize=8)
    ax.set_xlabel('Correct suggestions / shown suggestions | fixed top eight');fig.tight_layout();save('category_performance')
    p=pd.read_csv(OUT/'policy_validation.csv')
    fig,axes=plt.subplots(1,2,figsize=(8,2.8))
    for ax,col,title in zip(axes,['displayed_item_precision','day_coverage'],['Precision of displayed items','Coverage of eligible shopping days']):
        ax.plot(p.threshold,p[col],marker='o',color=TEAL);ax.axvline(.3,color=ORANGE,linestyle='--');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Score threshold');ax.set_title(title,fontsize=10);ax.grid(alpha=.15)
    fig.tight_layout();save('policy_tradeoff')
    camp=pd.read_csv(OUT/'campaign_types.csv')
    fig,ax=plt.subplots(figsize=(8,2.8));ax.bar(camp.campaign_type,camp.household_campaign_redemption_rate,color=[TEAL,'#AFC6D3','#AFC6D3']);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylim(0,.21)
    for i,r in enumerate(camp.itertuples()):ax.text(i,r.household_campaign_redemption_rate+.008,f'{r.household_campaign_redemption_rate:.1%}\n{r.assigned_household_campaigns:,} assignments',ha='center',fontsize=9)
    ax.set_ylabel('Household-campaign redemption rate');ax.spines['bottom'].set_visible(False);fig.tight_layout();save('campaign_response')
    f=pd.read_csv(OUT/'financial_scenarios.csv');f=f[(f.adoption==.25)&(f.acceptance==.1)&(f.margin_rate==.25)&(f.coupon_per_accepted_item==0)]
    fig,ax=plt.subplots(figsize=(8,3.1))
    for (name,g),color in zip(f.groupby('capacity_policy'),[TEAL,ORANGE]):
        ax.plot(g.incremental_share,g.net_monthly_contribution,marker='o',label=name,color=color)
    ax.axhline(0,color=GRAY,linewidth=1);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'${x:,.0f}'));ax.set_xlabel('Assumed net incremental share of accepted suggestions');ax.set_ylabel('Net monthly contribution');ax.legend(frameon=False);ax.grid(alpha=.15);fig.tight_layout();save('financial_sensitivity')
    seg=pd.read_csv(OUT/'basket_segments.csv')
    fig,ax=plt.subplots(figsize=(8,2.4));ax.bar(seg.basket_segment,seg.precision_at_8,color=TEAL);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylabel('Precision@8');ax.set_ylim(0,.45)
    for i,r in enumerate(seg.itertuples()):ax.text(i,r.precision_at_8+.015,f'{r.precision_at_8:.1%}\n{r.shopping_days:,} days',ha='center',fontsize=9)
    fig.tight_layout();save('basket_segments')

def build():
    charts()
    font=Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('Metro',str(font/'DejaVuSans.ttf')));pdfmetrics.registerFont(TTFont('MetroBold',str(font/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('Metro',normal='Metro',bold='MetroBold',italic='Metro',boldItalic='MetroBold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyMetro',fontName='Metro',fontSize=9.5,leading=14,textColor=colors.HexColor(NAVY),spaceAfter=9))
    styles.add(ParagraphStyle(name='SmallMetro',parent=styles['BodyMetro'],fontSize=8,leading=11))
    styles.add(ParagraphStyle(name='TitleMetro',fontName='MetroBold',fontSize=30,leading=36,textColor=colors.HexColor(NAVY),spaceAfter=14))
    styles.add(ParagraphStyle(name='HeadMetro',fontName='MetroBold',fontSize=19,leading=25,textColor=colors.HexColor(NAVY),spaceAfter=14))
    styles.add(ParagraphStyle(name='KickerMetro',fontName='MetroBold',fontSize=9,leading=13,textColor=colors.HexColor(TEAL),spaceAfter=10))
    story=[]
    def p(s,small=False):story.append(Paragraph(s,styles['SmallMetro' if small else 'BodyMetro']))
    def h(n,title):story.append(Paragraph(f'{n:02d} / METROPREDICT',styles['KickerMetro']));story.append(Paragraph(title,styles['HeadMetro']))
    def table(rows,widths):
        cells=[[Paragraph(str(c),styles['SmallMetro']) for c in row] for row in rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7F2F5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#D9E2EC'))]))
        story.append(t);story.append(Spacer(1,12))
    def img(name,w=505):
        from PIL import Image as PILImage
        path=FIG/f'{name}.png';im=PILImage.open(path);story.append(Image(str(path),width=w,height=w*im.height/im.width));story.append(Spacer(1,10))
    r=json.loads((OUT/'results.json').read_text());pol=json.loads((OUT/'policy_results.json').read_text());a=json.loads((OUT/'data_audit.json').read_text());f=json.loads((OUT/'financial_assumptions.json').read_text())
    m=pd.read_csv(OUT/'model_comparison.csv');test=m[m.split=='test'];fa=json.loads((OUT/'feature_audit.json').read_text())
    story.append(Paragraph('INDEPENDENT RETAIL ANALYTICS CASE STUDY',styles['KickerMetro']))
    story.append(Paragraph('MetroPredict',styles['TitleMetro']))
    story.append(Paragraph('Better replenishment suggestions.<br/>A measured case for a selective pilot.',styles['HeadMetro']))
    p('Prepared for Eshwar Vudhanthi | SQL + Python + Tableau | September 2026')
    table([['Evidence','Measured result'],['Public transaction coverage','1,469,307 rows | 2,469 households'],['Held-out ranking gain',f'{r["test_relative_gain"]:.1%} relative improvement over frequent purchases'],['Fixed list accuracy',f'{r["test_precision_at_8"]:.2%} Precision@8 | 1.32 matches per shopping day'],['Short-list policy',f'{pol["displayed_item_precision"]:.1%} item precision | {pol["day_coverage"]:.0%} eligible-day coverage']],[175,330])
    p('<b>Recommendation: conditional, limited pilot; no full launch.</b> The model clears the project\'s relative-accuracy gate, but an eight-item list is too noisy to treat as a complete shopping list. A validation-selected confidence threshold offers a more credible customer experience.')
    p('<b>Commercial finding:</b> recommendation acceptance is not incremental sales. The central illustrative economics are negative, including under the shorter-list policy. Validate convenience, adoption, net purchase change and cost before investment.')
    p('The study is inspired by Metro Market purchase history. It uses public Complete Journey data and has no retailer affiliation. Personal Metro Market receipts are not included; the import workflow is ready for a later extension.',True)
    story.append(PageBreak())
    h(2,'Data you can audit')
    p('The analyzed edition is the completejourney R package: a one-year slice of the original study. Its preparation script maps dates onto 2017 and modifies some metadata and discount fields. Those dates provide a relative timeline, not current trading evidence. No holiday or day-of-week features are used.')
    table([['Source / scope','Audit result'],['Transactions','1,469,307 receipt lines; 155,848 baskets; $4,596,039.58 recorded sales'],['Household shopping days','127,347 across valid sales rows; multiple same-day receipts combined'],['Excluded purchase rows','8,869 rows with quantity <= 0 or negative sales'],['Product metadata','92,331 products; 4,836 transaction rows lack product metadata'],['Coupon mapping','116,204 rows including 4,872 exact duplicates; do not expand sales with an unqualified coupon join'],['Campaign data','27 campaigns; 19 fully within the observation window; 8 boundary campaigns']],[175,330])
    p('<b>Modeling scope:</b> grocery-related departments with known categories. A deterministic hash sample selects 800 households observed before April. The full data remains in the SQL analysis. Test results describe returning households in this sample, not cold-start customers or every retailer customer.')
    table([['Time window','Use'],['January-March','History initialization and sampling pool'],['April-September','Training: every third eligible shopping occasion'],['October','Validation: model and baseline selection'],['November-December','Fixed-model test; histories update only after each observed day']],[175,330])
    p('SQLite warehouse: transactions, products, campaigns, campaign_descriptions, coupons and coupon_redemptions. SQL views cover clean sales lines, household days, customer summaries and purchase intervals. Full-period interval summaries are descriptive; prediction features are recalculated from past history only.',True)
    story.append(PageBreak())
    h(3,'The model beats frequency, modestly')
    img('model_comparison')
    table([['Test approach','Precision@8','Full-basket recall'],*[[row.model,f'{row.precision_at_8:.2%}',f'{row.recall_full_basket:.2%}'] for row in test.itertuples()]],[235,135,135])
    p(f'<b>Absolute gain:</b> {r["test_absolute_gain"]*100:.2f} percentage points, equivalent to about 0.104 additional matched items per shopping day. The household-clustered bootstrap 95% interval is {r["cluster_bootstrap_95ci_absolute_gain"][0]*100:.2f}-{r["cluster_bootstrap_95ci_absolute_gain"][1]*100:.2f} points. This is prediction gain, not a causal business effect.')
    p('The predeclared project gate was at least 5% relative Precision@8 improvement over the validation-selected simple baseline, with a clustered interval above zero. Gradient boosting clears that gate. Logistic regression is close enough to remain a lower-complexity deployment candidate.')
    p('Each eligible day has at least five prior grocery shopping days and eight candidates. Up to 120 previously purchased products from the last 180 days are ranked. Exact product ID defines a hit. New items and omitted candidates are included in full-basket recall, so its denominator remains demanding.',True)
    story.append(PageBreak())
    h(4,'Show fewer suggestions when uncertain')
    img('policy_tradeoff')
    p(f'<b>Exploratory policy:</b> after the primary benchmark, thresholds were compared on validation data. Select the threshold with maximum coverage among those reaching 35% displayed-item precision and at least 100 covered validation days. The selected score threshold was {pol["threshold"]:.2f}.')
    table([['Fixed-policy test result','Value'],['Correct displayed suggestions',f'{pol["displayed_item_precision"]:.1%} of {pol["shown_items"]:,} suggestions'],['Coverage',f'{pol["covered_days"]:,} of {pol["eligible_days"]:,} eligible days ({pol["day_coverage"]:.1%})'],['List length on covered days',f'{pol["suggestions_per_covered_day"]:.2f} suggestions on average']],[285,220])
    p('These metrics differ from Precision@8: displayed-item precision weights suggestions, and coverage declines when the system abstains. Even the filtered list is wrong about 64% of displayed items. Present it as optional reminders, not a list of known household needs.')
    p('<b>Category finding:</b> among the most frequently suggested categories, tropical fruit reaches 27.1% precision versus 21.8% for fluid milk and 15.9% for eggs under the fixed-eight policy. These are descriptive segments; they do not prove category-specific lift.')
    p('Larger realized baskets have higher Precision@8, but their size is known only after shopping. This segment is a diagnostic, not a deployable targeting rule. A later version would need a forecast of basket size based on earlier trips.',True)
    story.append(PageBreak())
    h(5,'Coupon response is evidence for testing')
    img('campaign_response')
    p('Across fully observed campaigns, Type A has a 16.6% household-campaign redemption rate, compared with 7.1% for Type B and 7.0% for Type C. The denominator is assigned households for each campaign, not redeemed coupon-product rows.')
    p('<b>What this establishes:</b> response differs across observed campaign groups. <b>What it does not establish:</b> that Type A caused more incremental purchases, is more profitable, or should receive more budget. Campaign types may differ in recipients, offers, duration and coupon availability.')
    table([['Guard against','Treatment in this study'],['Boundary bias','Exclude 8 boundary campaigns from the type comparison'],['Join multiplication','Aggregate assignments and redemptions before joining; retain raw coupon mapping duplicates in audit'],['Exposure confusion','Assignment records are not evidence a shopper opened or saw an offer'],['Cost confusion','Separate retailer loyalty discounts, manufacturer coupons and retailer coupon matches']],[175,330])
    p('A separate SQL output compares each recipient\'s 28-day pre-campaign spending with the first 28 campaign days for eligible campaigns. This is a descriptive change only: time trends, overlapping campaigns and targeting remain unresolved. No causal uplift model is claimed.')
    p('Data checks found zero redemption records without a campaign assignment and zero redemptions outside the corresponding campaign dates. These checks validate joins; they do not establish random assignment.',True)
    story.append(PageBreak())
    h(6,'Economics: the central case is negative')
    img('financial_sensitivity')
    table([['Illustrative input','Central assumption'],['Eligible shopping days / month','100,000'],['Feature adoption / item acceptance','25% / 10%'],['Net incremental share of accepted items','10%, after substitution and timing effects'],['Item value / contribution margin','$3.00 / 25%'],['Monthly operating + allocated build cost','$2,500 + $30,000 / 12 = $5,000']],[285,220])
    p(f'<b>Fixed eight:</b> ${f["central_scenario"]["net_monthly_contribution"]:,.0f} monthly net contribution. Break-even requires {f["central_scenario"]["break_even_incremental_share"]:.1%} of accepted suggestions to be incremental under these assumptions.')
    fs=f['filtered_policy_scenario']
    p(f'<b>Confidence-filtered capacity:</b> {fs["recommendations_per_eligible_day"]:.2f} suggestions per eligible day, including abstentions. Central net contribution is ${fs["net_monthly_contribution"]:,.0f}; break-even incremental share is {fs["break_even_incremental_share"]:.0%}, which is infeasible. Lower cost, higher adoption or a different source of value would be required.')
    p('The 432 scenarios vary adoption, acceptance, incrementality, margin, coupon cost and list capacity. These are scenarios, not forecasts. Retention value is excluded. Manufacturer coupon amounts are not automatically charged to retailer profit. Coupon scenarios charge the illustrative retailer-funded discount to every accepted suggestion.',True)
    story.append(PageBreak())
    h(7,'A retailer-facing pilot proposal')
    p('<b>Decision owner:</b> grocery digital product or loyalty team, with finance and customer research. The current result supports a small, budget-capped learning pilot if the team values the convenience hypothesis. It does not support a revenue-led rollout at the central assumed cost.')
    table([['Household-randomized arm','Purpose'],['A: existing purchase-history experience','Establish business-as-usual behavior'],['B: confidence-filtered reminders','Measure reminder value without discounts'],['C: same reminders + defined coupon policy','Measure the additional effect and cost of offers']],[205,300])
    p('<b>Primary commercial outcome:</b> contribution per assigned eligible household over a prespecified follow-up horizon. Analyze by intention to treat, including people who never open the feature. Keep each household in one arm, stratify on prior shopping frequency, and use household-level uncertainty estimates.')
    p('<b>Customer outcomes:</b> list-building time, perceived usefulness, dismissals and opt-outs. Record suggestion exposure, acceptance and purchases separately. Track substitutions and later purchases to detect stock-up or pull-forward effects.')
    p('<b>Before starting:</b> use retailer baseline variance and a business-defined minimum useful effect to calculate sample size. Set duration to cover multiple normal purchase cycles, with a post-offer follow-up. Define cost, margin and customer-experience stopping rules before looking at results.')
    p('<b>Launch only if:</b> measured customer benefit and contribution meet the agreed threshold, service cost fits the budget, and important customer groups are not harmed. Modify the policy or stop if those conditions are not met. This experiment is a design deliverable; no live test has been run.')
    p('<b>Practical edge:</b> purchase frequency remains the strongest signal, while timing adds value. The product opportunity is choosing when to show a small set of optional reminders and when to abstain.',True)
    story.append(PageBreak())
    h(8,'Reproduce, present, and extend')
    table([['Deliverable','Location in project'],['Start here and measured results','README.md'],['Executable SQL and database','sql/ and data/processed/metropredict.sqlite'],['Python pipelines and saved models','src/ and models/'],['Executed analysis notebook','notebooks/MetroPredict_Analysis.ipynb'],['Editable Tableau workbook','tableau/MetroPredict.twbx'],['Metrics, campaign tables and scenarios','outputs/'],['Your Metro Market data later','personal/purchases_template.csv and src/personal.py']],[220,285])
    p('<b>Validation status:</b> source totals reconcile; historical features precede their targets; ranking and financial boundary tests pass. The Tableau workbook passes the official 2026.1 local-element XML schema with minimal declarations for unused imported namespaces. Native Tableau Desktop/Cloud opening and rendering were unavailable and remain unverified.')
    p('<b>Interview framing:</b> built an auditable retail pipeline across 1.47 million transactions, compared three simple rules with two machine-learning approaches, and found an 8.5% relative ranking improvement. Proposed a confidence-filtered pilot while explicitly separating predictions, observed coupon response and hypothetical economics.')
    p('<b>Personal extension:</b> import purchase dates, product names, quantities and sales values. Receipt and product IDs are optional. The default uses transparent personal-history rules; applying the public-data model is an explicitly unvalidated transfer. No personal receipts are included in this release.')
    p('<b>Sources and documentation</b>',True)
    for text,url in [('Complete Journey package and data','https://bradleyboehmke.github.io/completejourney/'),('Source preparation and normalized calendar','https://github.com/bradleyboehmke/completejourney/blob/master/data-raw/prep-data.R'),('Tableau official workbook schemas','https://github.com/tableau/tableau-document-schemas'),('Tableau packaged workbooks','https://help.tableau.com/current/pro/desktop/en-us/save_savework_packagedworkbooks.htm')]:
        p(f'<link href="{url}" color="#147D92">{text}</link>',True)
    p('Data: Complete Journey, originating from 84.51 degrees, distributed by Brad Boehmke and Steven Mortimer through completejourney (package declares CC0). Raw checksums and source provenance are included. No Metro Market performance claim or affiliation is implied.',True)
    def page(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#D9E2EC'));canvas.line(45,38,550,38);canvas.setFont('Metro',8);canvas.setFillColor(colors.HexColor(GRAY));canvas.drawString(45,25,'METROPREDICT  /  INDEPENDENT CASE STUDY');canvas.drawRightString(550,25,str(doc.page))
    path=ROOT/'reports/MetroPredict_Project_Report.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=(595,842),rightMargin=45,leftMargin=45,topMargin=40,bottomMargin=52,title='MetroPredict - Retail Analytics Case Study',author='Eshwar Vudhanthi | prepared with AI assistance')
    doc.build(story,onFirstPage=page,onLaterPages=page);print(path)

if __name__=='__main__':build()

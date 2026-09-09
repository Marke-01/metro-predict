"""Build an editable Tableau 2026.1 workbook with local CSV data; validate XSD."""
from pathlib import Path
import json,uuid,zipfile,copy
import pandas as pd
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1]

def sub(p,t,**a):return E.SubElement(p,t,{k.replace('_','-'):str(v) for k,v in a.items()})
def ident(p,name):sub(p,'simple-id',uuid='{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'metropredict:'+name)).upper()+'}')

def run():
    out=ROOT/'outputs';dest=ROOT/'tableau';data=dest/'Data';data.mkdir(exist_ok=True)
    m=pd.read_csv(out/'model_comparison.csv');m=m[m.split=='test']
    cat=pd.read_csv(out/'category_performance.csv').head(10)
    camp=pd.read_csv(out/'campaign_types.csv')
    fin=pd.read_csv(out/'financial_scenarios.csv');fin=fin[(fin.adoption==.25)&(fin.acceptance==.1)&(fin.margin_rate==.25)&(fin.coupon_per_accepted_item==0)&(fin.capacity_policy=='Confidence filtered')]
    pol=pd.read_csv(out/'policy_validation.csv')
    monthly=pd.read_csv(out/'monthly_sales.csv')
    views=[
       ('Model accuracy - test','Model',m.model,'Precision at 8',m.precision_at_8,'0.0%'),
       ('Category accuracy - test','Category',cat.product_category,'Displayed-item precision',cat.precision,'0.0%'),
       ('Campaign response - observational','Campaign type',camp.campaign_type,'Household campaign redemption',camp.household_campaign_redemption_rate,'0.0%'),
       ('Economics - filtered policy assumptions','Net incremental share',fin.incremental_share.map(lambda x:f'{x:.0%}'),'Net monthly contribution',fin.net_monthly_contribution,'$#,##0;($#,##0)'),
       ('Threshold precision - validation','Score threshold',pol.threshold.map(lambda x:f'{x:.2f}'),'Displayed-item precision',pol.displayed_item_precision,'0.0%'),
       ('Historical sales - all departments','Normalized month',monthly.month,'Recorded sales',monthly.sales_value,'$#,##0')]
    root=E.Element('workbook',{'original-version':'26.1','version':'26.1','source-build':'0.0.0 (0000.0.0.0)','source-platform':'win'},nsmap={'user':'http://www.tableausoftware.com/xml/user'})
    sub(sub(root,'document-format-change-manifest'),'ManifestByVersion')
    sources=sub(root,'datasources');sheets=sub(root,'worksheets')
    files=[]
    for i,(title,dim,labels,measure,values,fmt) in enumerate(views):
        filename=f'view_{i+1}.csv';pd.DataFrame({dim:list(labels),measure:list(values)}).to_csv(data/filename,index=False);files.append(filename)
        name=f'metropredict{i+1}';ds=sub(sources,'datasource',caption=title,inline='true',name=name,version='26.1')
        conn=sub(ds,'connection',**{'class':'textscan','directory':'Data','filename':filename,'separator':',','header':'yes','ignore-first':'0','locale':'en_US','text-qualifier':'"','character-set':'utf-8'})
        rel=sub(conn,'relation',name=filename,table=f'[{filename}]',type='table')
        cols=sub(rel,'columns',header='yes',separator=',',**{'character-set':'UTF-8','locale':'en_US'})
        for ordinal,(field,dt) in enumerate([(dim,'string'),(measure,'real')]):
            sub(cols,'column',name=field,datatype=dt,ordinal=ordinal)
        metadata=sub(conn,'metadata-records')
        for ordinal,(field,dt) in enumerate([(dim,'string'),(measure,'real')]):
            rec=sub(metadata,'metadata-record',**{'class':'column'})
            for tag,val in [('remote-name',field),('remote-type','129' if dt=='string' else '5'),('local-name',f'[{field}]'),('parent-name',f'[{filename}]'),('remote-alias',field),('ordinal',ordinal),('local-type',dt),('aggregation','Count' if dt=='string' else 'Sum'),('contains-null','false')]:
                sub(rec,tag).text=str(val)
        dcol=sub(ds,'column',name=f'[{dim}]',datatype='string',role='dimension',type='nominal')
        vcol=sub(ds,'column',name=f'[{measure}]',datatype='real',role='measure',type='quantitative',default_format=fmt)
        sheet=sub(sheets,'worksheet',name=title);table=sub(sheet,'table');view=sub(table,'view')
        sub(sub(view,'datasources'),'datasource',name=name,caption=title)
        dep=sub(view,'datasource-dependencies',datasource=name);dep.append(copy.deepcopy(dcol));dep.append(copy.deepcopy(vcol))
        di=f'[none:{dim}:nk]';vi=f'[sum:{measure}:qk]'
        sub(dep,'column-instance',column=f'[{dim}]',derivation='None',name=di,pivot='key',type='nominal')
        sub(dep,'column-instance',column=f'[{measure}]',derivation='Sum',name=vi,pivot='key',type='quantitative')
        if i in [0,1,2]:sub(view,'computed-sort',**{'column':f'[{name}].{di}','direction':'DESC','using':f'[{name}].{vi}'})
        sub(view,'aggregation',value='true');sub(table,'style')
        pane=sub(sub(table,'panes'),'pane');sub(sub(pane,'view'),'breakdown',value='auto');sub(pane,'mark',**{'class':'Bar'})
        sub(sub(pane,'encodings'),'text',column=f'[{name}].{vi}')
        style=sub(pane,'style');rule=sub(style,'style-rule',element='mark');sub(rule,'format',attr='mark-color',value='#147D92');sub(rule,'format',attr='mark-labels-show',value='true')
        sub(table,'rows').text=f'[{name}].{di}';sub(table,'cols').text=f'[{name}].{vi}'
        ident(sheet,title)
    results=json.loads((out/'results.json').read_text());p=json.loads((out/'policy_results.json').read_text())
    dashboards=sub(root,'dashboards')
    main_title=f"MetroPredict | Conditional pilot | {results['test_relative_gain']:.1%} relative ranking gain"
    notes=f"Test: {results['test_shopping_days']:,} shopping days, {results['test_households']} households. Confidence-filtered list: {p['displayed_item_precision']:.1%} precision at {p['day_coverage']:.0%} day coverage. Sales uplift unmeasured."
    dashboards_spec=[('Executive decision',[0,1,3,2],main_title,notes),('Analytical detail',[4,5], 'MetroPredict | Validation policy and historical context','Threshold policy chosen on validation; dates are normalized. Full methods and assumptions are in the report.')]
    for title,idxs,headline,note in dashboards_spec:
        dash=sub(dashboards,'dashboard',name=title)
        sub(dash,'size',minwidth='1280',maxwidth='1280',minheight='850',maxheight='850',sizing_mode='fixed')
        zones=sub(dash,'zones')
        z=sub(zones,'zone',id='0',x='1800',y='1500',w='96000',h='6500',type_v2='text')
        sub(sub(z,'formatted-text'),'run',fontsize='20',bold='true',fontcolor='#102A43').text=headline
        z=sub(zones,'zone',id='1',x='1800',y='8200',w='96000',h='6500',type_v2='text')
        sub(sub(z,'formatted-text'),'run',fontsize='11',fontcolor='#334E68').text=note
        for j,index in enumerate(idxs):
            sub(zones,'zone',id=str(j+2),x=str(1800+(j%2)*49000),y=str(17000+(j//2)*39000),w='47500',h='37000',name=views[index][0],show_title='true')
        z=sub(zones,'zone',id='10',x='1800',y='95500',w='96000',h='4000',type_v2='text')
        sub(sub(z,'formatted-text'),'run',fontsize='9',fontcolor='#52606D').text='Independent portfolio study inspired by Metro Market. Public Complete Journey data; no retailer affiliation. Economics: 100k days/month, 25% adoption, 10% acceptance, $3/item, 25% margin, $5k monthly cost.'
        ident(dash,title)
    windows=sub(root,'windows',source_height='1000')
    for title,_,_,_ in dashboards_spec:
        window=sub(windows,'window',**{'class':'dashboard','name':title});sub(window,'viewpoints');sub(window,'active',id='2');ident(window,title+'window')
    sub(sub(root,'explain-data',enabled_for_viewer='false',extreme_values_enabled_for_all='false'),'explanation-types')
    path=dest/'MetroPredict.twb';E.ElementTree(root).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
    # The published XSD declares two imports without schemaLocation. This
    # workbook uses neither imported namespace. Supply minimal declarations
    # for those unused constructs; the official local-element schema is intact.
    user_schema=dest/'user_namespace.xsd';xml_schema=dest/'xml_namespace.xsd'
    user_schema.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://www.tableausoftware.com/xml/user"><xs:attributeGroup name="UserAttributes-AG"/></xs:schema>')
    xml_schema.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://www.w3.org/XML/1998/namespace"><xs:attribute name="base" type="xs:anyURI"/></xs:schema>')
    schema_doc=E.parse(str(ROOT/'docs/source/twb_2026.1.0.xsd'))
    for imp in schema_doc.findall('{http://www.w3.org/2001/XMLSchema}import'):
        imp.set('schemaLocation',str(user_schema if imp.get('namespace').endswith('/user') else xml_schema))
    schema=E.XMLSchema(schema_doc)
    valid=schema.validate(E.parse(str(path)))
    errors=[str(e) for e in schema.error_log]
    check={'xml_well_formed':True,'tableau_2026_1_xsd_valid':valid,'xsd_errors':errors,'worksheets':len(views),'dashboards':len(dashboards_spec),'native_application_open_test':'Not available in this environment'}
    (out/'tableau_validation.json').write_text(json.dumps(check,indent=2));print(json.dumps(check,indent=2))
    if not valid:raise ValueError('Tableau XSD validation failed')
    with zipfile.ZipFile(dest/'MetroPredict.twbx','w',zipfile.ZIP_DEFLATED) as z:
        z.write(path,'MetroPredict.twb')
        for f in files:z.write(data/f,'Data/'+f)

if __name__=='__main__':run()

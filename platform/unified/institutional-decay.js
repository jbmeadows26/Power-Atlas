/* Institutional decay OECD trust evidence viewer; no external dependencies. */
(function(){
  'use strict';
  var loaded=false, pending=false, dataset=null;
  var NS='http://www.w3.org/2000/svg';
  var options={
    'civil-2025':{x:'c25',y:'g25',xLabel:'Civil service trust, 2025 (%)',yLabel:'National government trust, 2025 (%)',min:0,max:100},
    'local-2025':{x:'l25',y:'g25',xLabel:'Local government trust, 2025 (%)',yLabel:'National government trust, 2025 (%)',min:0,max:100},
    'parliament-2025':{x:'p25',y:'g25',xLabel:'National parliament trust, 2025 (%)',yLabel:'National government trust, 2025 (%)',min:0,max:100},
    'civil-change':{x:'dc',y:'dg',xLabel:'Civil service trust change (pp)',yLabel:'National government trust change (pp)',min:-40,max:40},
    'local-change':{x:'dl',y:'dg',xLabel:'Local government trust change (pp)',yLabel:'National government trust change (pp)',min:-40,max:40}
  };
  function el(tag,attrs,value){
    var node=document.createElementNS(NS,tag);
    Object.keys(attrs||{}).forEach(function(k){node.setAttribute(k,String(attrs[k]));});
    if(value!==undefined)node.textContent=String(value);
    return node;
  }
  function pearson(points){
    var n=points.length;
    if(n<3)return null;
    var mx=points.reduce(function(t,p){return t+p.x},0)/n;
    var my=points.reduce(function(t,p){return t+p.y},0)/n;
    var numerator=0,xx=0,yy=0;
    points.forEach(function(p){var a=p.x-mx,b=p.y-my;numerator+=a*b;xx+=a*a;yy+=b*b;});
    return xx>0&&yy>0?numerator/Math.sqrt(xx*yy):null;
  }
  function makePoints(rows,choice){
    var m=options[choice];
    return rows.filter(function(r){return r.group==='oecd_member'}).map(function(r){
      var x= m.x==='dc'?(r.c23===null||r.c25===null?null:r.c25-r.c23):
             m.x==='dl'?(r.l23===null||r.l25===null?null:r.l25-r.l23):r[m.x];
      var y= m.y==='dg'?(r.g23===null||r.g25===null?null:r.g25-r.g23):r[m.y];
      return {id:r.id,name:r.name,x:x,y:y};
    }).filter(function(p){return Number.isFinite(p.x)&&Number.isFinite(p.y);});
  }
  function draw(rows){
    var choice=document.getElementById('idComparison').value;
    var m=options[choice],points=makePoints(rows,choice),r=pearson(points);
    var svg=document.getElementById('idScatter');
    while(svg.firstChild)svg.removeChild(svg.firstChild);
    svg.setAttribute('viewBox','0 0 740 460');
    svg.setAttribute('role','img');
    svg.setAttribute('aria-label',m.yLabel+' against '+m.xLabel+', '+points.length+' countries');
    var x0=74,y0=379,width=603,height=326;
    var xpos=function(n){return x0+width*(n-m.min)/(m.max-m.min)};
    var ypos=function(n){return y0-height*(n-m.min)/(m.max-m.min)};
    for(var i=0;i<=4;i++){
      var v=m.min+(m.max-m.min)*i/4,x=xpos(v),y=ypos(v);
      svg.appendChild(el('line',{x1:x,y1:y0-height,x2:x,y2:y0,stroke:'#dce8ec','stroke-width':1}));
      svg.appendChild(el('line',{x1:x0,y1:y,x2:x0+width,y2:y,stroke:'#dce8ec','stroke-width':1}));
      svg.appendChild(el('text',{x:x,y:y0+22,'text-anchor':'middle','font-size':12,fill:'#557184'},v));
      svg.appendChild(el('text',{x:x0-14,y:y+4,'text-anchor':'end','font-size':12,fill:'#557184'},v));
    }
    svg.appendChild(el('text',{x:x0+width/2,y:432,'text-anchor':'middle','font-size':15,fill:'#24465b'},m.xLabel));
    svg.appendChild(el('text',{x:20,y:213,transform:'rotate(-90 20 213)','text-anchor':'middle','font-size':14,fill:'#24465b'},m.yLabel));
    points.forEach(function(p){
      var c=el('circle',{cx:xpos(p.x),cy:ypos(p.y),r:5.8,fill:'#1d8d97','fill-opacity':'.78',stroke:'#fff','stroke-width':1.3,tabindex:0});
      c.appendChild(el('title',{},p.name+': '+m.xLabel+' '+p.x+', '+m.yLabel+' '+p.y));
      svg.appendChild(c);
    });
    document.getElementById('idR').textContent=r===null?'N/A':(r>=0?'+':'')+r.toFixed(4);
    document.getElementById('idN').textContent=points.length.toString();
    document.getElementById('idXAxis').textContent=m.xLabel;
    document.getElementById('idYAxis').textContent=m.yLabel;
    document.getElementById('idRecordStatus').textContent='Source: OECD Trust Survey 2026, Table 1.3 · '+dataset.asOf+' · Published rounded percentages · Descriptive country associations only';
    var tbody=document.getElementById('idCountryRows');
    tbody.textContent='';
    points.slice().sort(function(a,b){return a.name.localeCompare(b.name)}).forEach(function(p){
      var tr=document.createElement('tr');
      [p.name,p.x,p.y].forEach(function(v){
        var td=document.createElement('td');td.textContent=String(v);td.style.padding='7px 12px';td.style.borderBottom='1px solid #e3eaf0';tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }
  function load(){
    if(loaded||pending)return;
    pending=true;
    var status=document.getElementById('idStatus');
    status.textContent='Loading source-backed country survey values…';
    var urls=['api/trust-metrics.json','https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/site/api/trust-metrics.json'];
    function attempt(i){
      return fetch(urls[i],{cache:'no-store'}).then(function(res){if(!res.ok)throw Error('HTTP '+res.status);return res.json()})
       .catch(function(e){if(i+1<urls.length)return attempt(i+1);throw e;});
    }
    attempt(0).then(function(d){
      if(d.schema!=='power-atlas.institutional-decay.trust-metrics.v1'||!Array.isArray(d.rows)||d.rows.length!==39||d.observedTrustCells!==407)throw Error('Dataset schema or coverage mismatch');
      var ps=makePoints(d.rows,'civil-2025'),r=pearson(ps);
      if(ps.length!==33||Math.abs(r-d.referenceCorrelationGovVsCivil2025)>.0002)throw Error('Correlation reference check failed');
      dataset=d;loaded=true;pending=false;
      draw(d.rows);
      status.textContent='407 verified published cells · 39 country records · 33 OECD participants in 2025 · the United States was not surveyed';
    }).catch(function(e){
      pending=false;status.textContent='Country feed unavailable: '+e.message+'. Read the source dataset or final assessment using the links below.';
    });
  }
  function initialize(){
    var tab=document.querySelector('[data-tab="institutional-decay"]');
    if(!tab)return;
    tab.addEventListener('click',load);
    document.getElementById('idComparison').addEventListener('change',function(){if(dataset)draw(dataset.rows);});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize);
  else initialize();
})();

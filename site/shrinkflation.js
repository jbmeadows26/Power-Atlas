/* Shrinkflation interactive scenarios and evidence-linked category selection. */
(()=>{"use strict";const root=document.getElementById("shrinkflation");if(!root)return;
const $=id=>root.querySelector("#"+id);
root.querySelectorAll("[data-sf-price]").forEach(b=>b.addEventListener("click",()=>{
 const up=b.dataset.sfPrice==="rises",old=up?4.49:4.99,next=4.99;
 root.querySelectorAll("[data-sf-price]").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));
 $("sfOldPrice").textContent="$"+old.toFixed(2);
 $("sfOldUnit").textContent=(old/16*100).toFixed(1)+"¢ per oz";
 $("sfIncrease").textContent="+"+(((next/14)/(old/16)-1)*100).toFixed(1)+"%";
 $("sfExplanation").textContent=up?"higher unit price when the shelf price rises and the package shrinks":"higher unit price, despite an unchanged shelf price";
}));
const names={paper:["Paper products",3.0],snacks:["Snacks",2.6],candy:["Candy and chewing gum",2.3],icecream:["Ice cream",1.8],cereal:["Breakfast cereal",1.6],coffee:["Coffee",1.4]};
root.querySelectorAll("[data-sf-category]").forEach(b=>b.addEventListener("click",()=>{
 root.querySelectorAll("[data-sf-category]").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));
 const item=names[b.dataset.sfCategory];if(!item)return;
 const title=document.createElement("strong");title.textContent=item[0]+": +"+item[1].toFixed(1)+" percentage points";
 const p=document.createElement("p");p.textContent="GAO estimated that downsizing added "+item[1].toFixed(1)+" percentage points to "+item[0].toLowerCase()+" inflation from December 2019 through December 2024.";
 $("sfDetail").replaceChildren(title,p);
}));
})();
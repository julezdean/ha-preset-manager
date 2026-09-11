const t="preset-manager-card";function e(t,e,i,s){var n,r=arguments.length,o=r<3?e:null===s?s=Object.getOwnPropertyDescriptor(e,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(t,e,i,s);else for(var a=t.length-1;a>=0;a--)(n=t[a])&&(o=(r<3?n(o):r>3?n(e,i,o):n(e,i))||o);return r>3&&o&&Object.defineProperty(e,i,o),o}"function"==typeof SuppressedError&&SuppressedError;const i=globalThis,s=i.ShadowRoot&&(void 0===i.ShadyCSS||i.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap;let o=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(s&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&r.set(e,t))}return t}toString(){return this.cssText}};const a=s?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new o("string"==typeof t?t:t+"",void 0,n))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:u,getPrototypeOf:p}=Object,m=globalThis,f=m.trustedTypes,_=f?f.emptyScript:"",v=m.reactiveElementPolyfillSupport,b=(t,e)=>t,g={toAttribute(t,e){switch(e){case Boolean:t=t?_:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},y=(t,e)=>!c(t,e),$={attribute:!0,type:String,converter:g,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=$){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&l(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:n}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const r=s?.call(this);n?.call(this,e),this.requestUpdate(t,r,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??$}static _$Ei(){if(this.hasOwnProperty(b("elementProperties")))return;const t=p(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(b("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(b("properties"))){const t=this.properties,e=[...h(t),...u(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(a(t))}else void 0!==t&&e.push(a(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,e)=>{if(s)t.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const s of e){const e=document.createElement("style"),n=i.litNonce;void 0!==n&&e.setAttribute("nonce",n),e.textContent=s.cssText,t.appendChild(e)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const n=(void 0!==i.converter?.toAttribute?i.converter:g).toAttribute(e,i.type);this._$Em=t,null==n?this.removeAttribute(s):this.setAttribute(s,n),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),n="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:g;this._$Em=s;const r=n.fromAttribute(e,t.type);this[s]=r??this._$Ej?.get(s)??r,this._$Em=null}}requestUpdate(t,e,i,s=!1,n){if(void 0!==t){const r=this.constructor;if(!1===s&&(n=this[t]),i??=r.getPropertyOptions(t),!((i.hasChanged??y)(n,e)||i.useDefault&&i.reflect&&n===this._$Ej?.get(t)&&!this.hasAttribute(r._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:n},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??e??this[t]),!0!==n||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[b("elementProperties")]=new Map,w[b("finalized")]=new Map,v?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,A=t=>t,k=x.trustedTypes,S=k?k.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",T=`lit$${Math.random().toFixed(9).slice(2)}$`,M="?"+T,C=`<${M}>`,P=document,O=()=>P.createComment(""),j=t=>null===t||"object"!=typeof t&&"function"!=typeof t,U=Array.isArray,N="[ \t\n\f\r]",z=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,H=/-->/g,R=/>/g,D=RegExp(`>|${N}(?:([^\\s"'>=/]+)(${N}*=${N}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),L=/'/g,W=/"/g,q=/^(?:script|style|textarea|title)$/i,I=(t=>(e,...i)=>({_$litType$:t,strings:e,values:i}))(1),B=Symbol.for("lit-noChange"),V=Symbol.for("lit-nothing"),J=new WeakMap,K=P.createTreeWalker(P,129);function F(t,e){if(!U(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==S?S.createHTML(e):e}const G=(t,e)=>{const i=t.length-1,s=[];let n,r=2===e?"<svg>":3===e?"<math>":"",o=z;for(let e=0;e<i;e++){const i=t[e];let a,c,l=-1,d=0;for(;d<i.length&&(o.lastIndex=d,c=o.exec(i),null!==c);)d=o.lastIndex,o===z?"!--"===c[1]?o=H:void 0!==c[1]?o=R:void 0!==c[2]?(q.test(c[2])&&(n=RegExp("</"+c[2],"g")),o=D):void 0!==c[3]&&(o=D):o===D?">"===c[0]?(o=n??z,l=-1):void 0===c[1]?l=-2:(l=o.lastIndex-c[2].length,a=c[1],o=void 0===c[3]?D:'"'===c[3]?W:L):o===W||o===L?o=D:o===H||o===R?o=z:(o=D,n=void 0);const h=o===D&&t[e+1].startsWith("/>")?" ":"";r+=o===z?i+C:l>=0?(s.push(a),i.slice(0,l)+E+i.slice(l)+T+h):i+T+(-2===l?e:h)}return[F(t,r+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]};class X{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let n=0,r=0;const o=t.length-1,a=this.parts,[c,l]=G(t,e);if(this.el=X.createElement(c,i),K.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=K.nextNode())&&a.length<o;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(E)){const e=l[r++],i=s.getAttribute(t).split(T),o=/([.?@])?(.*)/.exec(e);a.push({type:1,index:n,name:o[2],strings:i,ctor:"."===o[1]?et:"?"===o[1]?it:"@"===o[1]?st:tt}),s.removeAttribute(t)}else t.startsWith(T)&&(a.push({type:6,index:n}),s.removeAttribute(t));if(q.test(s.tagName)){const t=s.textContent.split(T),e=t.length-1;if(e>0){s.textContent=k?k.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],O()),K.nextNode(),a.push({type:2,index:++n});s.append(t[e],O())}}}else if(8===s.nodeType)if(s.data===M)a.push({type:2,index:n});else{let t=-1;for(;-1!==(t=s.data.indexOf(T,t+1));)a.push({type:7,index:n}),t+=T.length-1}n++}}static createElement(t,e){const i=P.createElement("template");return i.innerHTML=t,i}}function Y(t,e,i=t,s){if(e===B)return e;let n=void 0!==s?i._$Co?.[s]:i._$Cl;const r=j(e)?void 0:e._$litDirective$;return n?.constructor!==r&&(n?._$AO?.(!1),void 0===r?n=void 0:(n=new r(t),n._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=n:i._$Cl=n),void 0!==n&&(e=Y(t,n._$AS(t,e.values),n,s)),e}class Z{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??P).importNode(e,!0);K.currentNode=s;let n=K.nextNode(),r=0,o=0,a=i[0];for(;void 0!==a;){if(r===a.index){let e;2===a.type?e=new Q(n,n.nextSibling,this,t):1===a.type?e=new a.ctor(n,a.name,a.strings,this,t):6===a.type&&(e=new nt(n,this,t)),this._$AV.push(e),a=i[++o]}r!==a?.index&&(n=K.nextNode(),r++)}return K.currentNode=P,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class Q{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=V,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Y(this,t,e),j(t)?t===V||null==t||""===t?(this._$AH!==V&&this._$AR(),this._$AH=V):t!==this._$AH&&t!==B&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>U(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==V&&j(this._$AH)?this._$AA.nextSibling.data=t:this.T(P.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=X.createElement(F(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new Z(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=J.get(t.strings);return void 0===e&&J.set(t.strings,e=new X(t)),e}k(t){U(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const n of t)s===e.length?e.push(i=new Q(this.O(O()),this.O(O()),this,this.options)):i=e[s],i._$AI(n),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=A(t).nextSibling;A(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class tt{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,n){this.type=1,this._$AH=V,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=n,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=V}_$AI(t,e=this,i,s){const n=this.strings;let r=!1;if(void 0===n)t=Y(this,t,e,0),r=!j(t)||t!==this._$AH&&t!==B,r&&(this._$AH=t);else{const s=t;let o,a;for(t=n[0],o=0;o<n.length-1;o++)a=Y(this,s[i+o],e,o),a===B&&(a=this._$AH[o]),r||=!j(a)||a!==this._$AH[o],a===V?t=V:t!==V&&(t+=(a??"")+n[o+1]),this._$AH[o]=a}r&&!s&&this.j(t)}j(t){t===V?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class et extends tt{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===V?void 0:t}}class it extends tt{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==V)}}class st extends tt{constructor(t,e,i,s,n){super(t,e,i,s,n),this.type=5}_$AI(t,e=this){if((t=Y(this,t,e,0)??V)===B)return;const i=this._$AH,s=t===V&&i!==V||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,n=t!==V&&(i===V||s);s&&this.element.removeEventListener(this.name,this,i),n&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class nt{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Y(this,t)}}const rt=x.litHtmlPolyfillSupport;rt?.(X,Q),(x.litHtmlVersions??=[]).push("3.3.3");const ot=globalThis;class at extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let n=s._$litPart$;if(void 0===n){const t=i?.renderBefore??null;s._$litPart$=n=new Q(e.insertBefore(O(),t),t,void 0,i??{})}return n._$AI(t),n})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return B}}at._$litElement$=!0,at.finalized=!0,ot.litElementHydrateSupport?.({LitElement:at});const ct=ot.litElementPolyfillSupport;ct?.({LitElement:at}),(ot.litElementVersions??=[]).push("4.2.2");const lt=t=>(e,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)},dt={attribute:!0,type:String,converter:g,reflect:!1,hasChanged:y},ht=(t=dt,e,i)=>{const{kind:s,metadata:n}=i;let r=globalThis.litPropertyMetadata.get(n);if(void 0===r&&globalThis.litPropertyMetadata.set(n,r=new Map),"setter"===s&&((t=Object.create(t)).wrapped=!0),r.set(i.name,t),"accessor"===s){const{name:s}=i;return{set(i){const n=e.get.call(this);e.set.call(this,i),this.requestUpdate(s,n,t,!0,i)},init(e){return void 0!==e&&this.C(s,void 0,t,e),e}}}if("setter"===s){const{name:s}=i;return function(i){const n=this[s];e.call(this,i),this.requestUpdate(s,n,t,!0,i)}}throw Error("Unsupported decorator location: "+s)};function ut(t){return function(t){return(e,i)=>"object"==typeof i?ht(t,e,i):((t,e,i)=>{const s=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),s?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}({...t,state:!0,attribute:!1})}class pt extends Error{}const mt=["always","never","manual"],ft=["active","picker","edit","all"];function _t(t){throw new pt(t)}function vt(t,e){return null==t?{}:(("object"!=typeof t||Array.isArray(t))&&_t(`"${e}" has to be a group of options, for example "${e}: {visible: false}"`),t)}function bt(t,e,i){return void 0===t?i:("boolean"!=typeof t&&_t(`"${e}" has to be true or false`),t)}function gt(t,e){if(null!=t)return"string"!=typeof t&&_t(`"${e}" has to be text`),t}function yt(t,e,i,s){return void 0===t?s:("string"==typeof t&&i.includes(t)||_t(`"${e}" has to be one of ${i.join(", ")}`),t)}function $t(t,e){if(null!=t)return!1!==t&&("string"!=typeof t&&_t(`"${e}" has to be text, or false to hide it`),t)}function wt(t,e){const i=vt(t,e),s={};for(const[t,n]of Object.entries(i))"string"!=typeof n&&_t(`"${e}.${t}" has to be a colour`),s[t]=n;return s}function xt(t){return null==t?null:(Array.isArray(t)||_t('"values.parameters" has to be a list of parameter keys'),t.map((t,e)=>{const i=`values.parameters[${e}]`;if("string"==typeof t)return{parameter:t};"object"==typeof t&&null!==t&&"parameter"in t||_t(`"${i}" has to be a parameter key, or a group with a "parameter" key`);const s=gt(t.parameter,`${i}.parameter`);s||_t(`"${i}.parameter" is required`);const n={parameter:s},r=gt(t.name,`${i}.name`);void 0!==r&&(n.name=r);const o=$t(t.icon,`${i}.icon`);return void 0!==o&&(n.icon=o),n}))}function At(t){"object"==typeof t&&null!==t||_t("The card needs a configuration.");const e=t,i=gt(e.entity,"entity");i||_t('Pick an entity of Preset Manager, for example "entity: sensor.house_mode_mode" or the active mode sensor of a preset.'),i.includes(".")||_t(`"${i}" is not an entity id.`);const s=vt(e.header,"header"),n=vt(e.modes,"modes"),r=vt(e.values,"values");var o,a,c;return{type:String(e.type??""),entity:i,header:{visible:bt(s.visible,"header.visible",!0),automatic:bt(s.automatic,"header.automatic",!0),title:gt(s.title,"header.title"),subtitle:$t(s.subtitle,"header.subtitle"),icon:$t(s.icon,"header.icon"),icon_color:gt(s.icon_color,"header.icon_color")},modes:{visible:(o=n.visible,a="modes.visible",c="always",void 0===o?c:!0===o?"always":!1===o?"never":("string"==typeof o&&mt.includes(o)||_t(`"${a}" has to be true, false, or one of ${mt.join(", ")}`),o)),icons:bt(n.icons,"modes.icons",!0),colors:wt(n.colors,"modes.colors")},values:{visible:bt(r.visible,"values.visible",!0),mode:yt(r.mode,"values.mode",ft,"active"),parameters:xt(r.parameters),icons:bt(r.icons,"values.icons",!1)},tap_action:e.tap_action,hold_action:e.hold_action,double_tap_action:e.double_tap_action}}function kt(e){const i=String(e.type??`custom:${t}`),s="string"==typeof e.entity?e.entity:"";let n={};try{n=At({type:i,entity:s||"sensor.placeholder"})}catch(t){n={}}const r={type:i,entity:s};for(const[t,i]of Object.entries(e)){if("type"===t||"entity"===t)continue;const e=St(i,n[t]);void 0!==e&&(r[t]=e)}return r}function St(t,e){if(null!=t&&""!==t){if(Array.isArray(t))return t.length?t:void 0;if("object"==typeof t){const i=t,s=e??{},n={};for(const[t,e]of Object.entries(i)){const i=St(e,s[t]);void 0!==i&&JSON.stringify(i)!==JSON.stringify(s[t])&&(n[t]=i)}return Object.keys(n).length?n:void 0}return t===e?void 0:t}}const Et={preset_modes:[],presets:[],blueprints:[]};class Tt{constructor(t){this._hass=t,this._listeners=new Set,this._unsubscribes=[]}get current(){return this._config}async load(t){return this._hass=t,this._config?this._config:(this._pending||(this._pending=this._fetch()),this._pending)}subscribe(t){return this._listeners.add(t),1===this._listeners.size&&this._watch(),()=>{this._listeners.delete(t),this._listeners.size||this._stop()}}async _fetch(){try{const t=await this._hass.callWS({type:"preset_manager/config"});return this._apply(t),t}catch(t){return this._apply(Et),Et}finally{this._pending=void 0}}_apply(t){const e=JSON.stringify(t);if(e!==this._serialised){this._serialised=e,this._config=t;for(const e of this._listeners)e(t)}}async _watch(){for(const t of["entity_registry_updated","device_registry_updated"])try{const e=await this._hass.connection.subscribeEvents(()=>this._scheduleRefresh(),t);this._listeners.size?this._unsubscribes.push(()=>{e()}):e()}catch(t){}}_scheduleRefresh(){this._timer&&clearTimeout(this._timer),this._timer=setTimeout(()=>{this._timer=void 0,this._config=void 0,this._pending=this._fetch()},400)}_stop(){for(this._timer&&clearTimeout(this._timer),this._timer=void 0;this._unsubscribes.length;)this._unsubscribes.pop()()}}const Mt=new WeakMap;function Ct(t){let e=Mt.get(t.connection);return e||(e=new Tt(t),Mt.set(t.connection,e)),e}function Pt(t){return Ct(t).load(t)}function Ot(t){return Ct(t).current}function jt(t,e){return Ct(t).subscribe(e)}function Ut(t,e){return{preset:e,presetMode:t.preset_modes.find(t=>t.id===e.preset_mode)??null,blueprint:t.blueprints.find(t=>t.id===e.blueprint)??null}}function Nt(t){const e=Object.values(t.entities);for(const i of t.parameters)i.entity&&e.push(i.entity),e.push(...Object.values(i.editors));return e}function zt(t){const e=Object.values(t.entities);return t.source_entity&&e.push(t.source_entity),e}function Ht(t,e){for(const i of t.presets)if(Nt(i).includes(e))return Ut(t,i);return null}const Rt={active:"Active",apply:"Apply",automatic:"Automatic",discard:"Discard",editing:"Edit",mode_automatic:"Automatic mode selection",loading:"Loading…",manual:"Manual",mode:"Mode",no_entity:"Set “entity” to any entity of a preset.",not_a_preset:"“{entity}” belongs to a preset mode. A card shows a preset; point it at one of its entities.",no_mode:"No mode active",no_modes:"This preset mode has no modes yet.",no_parameters:"This preset has no parameters yet.",no_preset_mode:"No preset mode",not_editable:"Not editable here",not_found:"“{entity}” does not belong to Preset Manager.",not_set:"Not set",not_set_up:"Preset Manager is not set up.",orphaned:"Waiting for a preset mode; values do not resolve.",unavailable:"Unavailable"},Dt={en:Rt,de:{active:"Aktiv",apply:"Übernehmen",automatic:"Automatik",discard:"Verwerfen",editing:"Bearbeiten",mode_automatic:"Mode-Automatik",loading:"Wird geladen…",manual:"Manuell",mode:"Mode",no_entity:"„entity“ auf eine beliebige Entität eines Presets setzen.",not_a_preset:"„{entity}“ gehört zu einem Preset Mode. Eine Card zeigt ein Preset; zeig auf eine seiner Entitäten.",no_mode:"Kein Mode aktiv",no_modes:"Dieser Preset Mode hat noch keine Modes.",no_parameters:"Dieses Preset hat noch keine Parameter.",no_preset_mode:"Kein Preset Mode",not_editable:"Hier nicht editierbar",not_found:"„{entity}“ gehört nicht zu Preset Manager.",not_set:"Nicht gesetzt",not_set_up:"Preset Manager ist nicht eingerichtet.",orphaned:"Wartet auf einen Preset Mode; die Werte lösen nicht auf.",unavailable:"Nicht verfügbar"}};function Lt(t,e,i={}){const s=(t?.language??"en").toLowerCase().split("-")[0];let n=(Dt[s]??Rt)[e]??Rt[e]??e;for(const[t,e]of Object.entries(i))n=n.replace(`{${t}}`,String(e));return n}const Wt=((t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new o(i,t,n)})`
  :host {
    /* Spacing scale. */
    --pm-padding-x: 16px;
    --pm-padding-y: 14px;
    --pm-gap: 12px;
    --pm-row-gap: 10px;
    --pm-icon-size: 38px;

    --pm-radius: var(--ha-card-border-radius, 12px);
    --pm-chip-radius: 999px;

    --pm-text: var(--primary-text-color);
    --pm-muted: var(--secondary-text-color);
    --pm-divider: var(--divider-color);
    --pm-accent: var(--primary-color);
    --pm-disabled: var(--disabled-text-color);
    --pm-warning: var(--warning-color, #ffa600);
    --pm-error: var(--error-color, #db4437);

    display: block;
  }

  ha-card {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .section {
    padding: var(--pm-padding-y) var(--pm-padding-x);
  }

  /* Header ---------------------------------------------------------------- */

  /* Name and switch share a line while both fit, and the switch drops onto
     its own when they do not - so a toggle in the corner never squeezes the
     name down to two letters on a narrow card. */
  .header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px var(--pm-gap);
  }

  /* The name is the button, not the row: a row that also holds a switch must
     not be one, and making it one anyway is what cost this header its
     keyboard. Everything below only takes the button back out of its default
     appearance - it has to read as the content it wraps. */
  .header-main {
    flex: 1 1 160px;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: var(--pm-gap);
    appearance: none;
    margin: 0;
    padding: 0;
    border: none;
    background: none;
    font: inherit;
    color: inherit;
    text-align: left;
  }

  .header-main.tappable {
    cursor: pointer;
  }

  .header-end {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    margin-left: auto;
  }

  /* A switch with nothing written next to it. It can only belong to the object
     named beside it, so the row says what it switches; the word rides on the
     aria-label, where it is needed and costs no width. */
  .switch-field {
    display: inline-flex;
    align-items: center;
    cursor: pointer;
  }

  .icon {
    flex: 0 0 auto;
    width: var(--pm-icon-size);
    height: var(--pm-icon-size);
    border-radius: 50%;
    display: grid;
    place-items: center;
    color: var(--pm-icon-color, var(--pm-accent));
    background: color-mix(in srgb, var(--pm-icon-color, var(--pm-accent)) 14%, transparent);
    --mdc-icon-size: calc(var(--pm-icon-size) * 0.55);
  }

  .titles {
    /* Wants a readable width before the line breaks, rather than its full
       content width, which would wrap a header that had room to spare. */
    flex: 1 1 120px;
    min-width: 0;
  }

  .title {
    color: var(--pm-text);
    font-size: 15px;
    font-weight: 500;
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .subtitle {
    color: var(--pm-muted);
    font-size: 13px;
    line-height: 1.35;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Modes ----------------------------------------------------------------- */

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .chip {
    appearance: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-height: 32px;
    padding: 0 12px;
    border: none;
    border-radius: var(--pm-chip-radius);
    background: color-mix(in srgb, var(--pm-text) 8%, transparent);
    color: var(--pm-muted);
    font: inherit;
    font-size: 13px;
    line-height: 1;
    cursor: pointer;
    transition: background-color 160ms ease, color 160ms ease;
    --mdc-icon-size: 16px;
  }

  /* A list item is not a control: no pointer, no hover, no press. */
  span.chip {
    cursor: default;
  }

  button.chip:hover:not(:disabled) {
    background: color-mix(in srgb, var(--pm-text) 14%, transparent);
  }

  .chip[aria-pressed="true"] {
    background: color-mix(in srgb, var(--pm-chip-color, var(--pm-accent)) 18%, transparent);
    color: var(--pm-chip-color, var(--pm-accent));
    font-weight: 500;
  }

  .chip:disabled {
    cursor: default;
  }

  .chip:disabled:not([aria-pressed="true"]) {
    color: var(--pm-disabled);
  }

  /* Mode tabs -------------------------------------------------------------- */

  /* The chip row changes the house; this one changes what the card shows. As
     two rows of pills they claimed the same authority, however small the
     second one was made - a pill is a state, a tab is a view. So: no colour,
     no icons, no enclosure, and flush against the list it governs, which is
     why the strip is its own section and pulls back out of its padding. */
  .section.strip {
    padding-bottom: 0;
  }

  .tabs {
    display: flex;
    gap: 18px;
    /* Sideways rather than into a second line: a strip that wraps stops
       reading as one strip. The scrollbar stays hidden; the cut-off tab at
       the edge is what says there is more. */
    overflow-x: auto;
    scrollbar-width: none;
    margin: 0 calc(-1 * var(--pm-padding-x));
    padding: 0 var(--pm-padding-x);
    border-bottom: 1px solid var(--pm-divider);
  }

  .tabs::-webkit-scrollbar {
    display: none;
  }

  .tab {
    appearance: none;
    border: none;
    background: none;
    color: var(--pm-muted);
    font: inherit;
    font-size: 13px;
    line-height: 1;
    white-space: nowrap;
    cursor: pointer;
    padding: 4px 0 10px;
    /* Over the strip's own line, so the two never stack into 3px. */
    margin-bottom: -1px;
    border-bottom: 2px solid transparent;
    transition: color 160ms ease, border-color 160ms ease;
  }

  .tab:hover {
    color: var(--pm-text);
  }

  .tab[aria-selected="true"] {
    color: var(--pm-text);
    border-bottom-color: var(--pm-accent);
  }

  /* Rows ------------------------------------------------------------------ */

  .rows {
    display: flex;
    flex-direction: column;
    gap: var(--pm-row-gap);
  }

  /* One row is a label and the thing it labels. They sit side by side while
     both fit and the second one drops onto its own line when they do not -
     which is what a card in a narrow column or a phone-width view is. Both
     are sized by their content, so the break happens exactly when the two no
     longer fit and not one pixel earlier - a percentage basis wrapped rows
     that had room to spare. */
  .row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px var(--pm-gap);
    min-height: 28px;
  }

  .row-label {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--pm-muted);
    font-size: 14px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    --mdc-icon-size: 18px;
  }

  .row-icon {
    flex: 0 0 auto;
    display: inline-grid;
    place-items: center;
    width: 18px;
  }

  /* A row label that opens the object it names. */
  .link-row {
    appearance: none;
    border: none;
    background: none;
    padding: 0;
    font: inherit;
    text-align: left;
    cursor: pointer;
  }

  .link-row:disabled {
    cursor: default;
  }

  .row-value {
    flex: 0 1 auto;
    /* Keeps it against the right edge on both layouts: beside the label, and
       alone on the line below it. */
    margin-left: auto;
    min-width: 0;
    color: var(--pm-text);
    font-size: 14px;
    font-variant-numeric: tabular-nums;
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row-value.muted {
    color: var(--pm-disabled);
  }

  .row-control {
    flex: 0 1 auto;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    margin-left: auto;
    min-width: 0;
    max-width: 100%;
  }

  /* A slider needs room the label does not; below that width the row breaks
     into two lines rather than squeezing the control to nothing. */
  .row.wide {
    flex-wrap: wrap;
  }

  .row.wide .row-control {
    flex: 1 1 160px;
  }

  .group-label {
    color: var(--pm-muted);
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-top: 4px;
  }

  .rows .group-label:first-child {
    margin-top: 0;
  }

  /* Controls -------------------------------------------------------------- */

  input,
  select {
    font: inherit;
    color: var(--pm-text);
  }

  .text-input,
  .number-input,
  .select-input,
  .date-input {
    box-sizing: border-box;
    min-height: 32px;
    max-width: 100%;
    padding: 4px 8px;
    border: 1px solid var(--pm-divider);
    border-radius: 8px;
    background: transparent;
    font-size: 14px;
  }

  .number-input {
    width: 84px;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .text-input {
    /* Wants 160px, takes what there is. A fixed width here is what pushed the
       label out of a narrow card entirely. */
    width: 160px;
    max-width: 100%;
    min-width: 0;
  }

  .select-input {
    max-width: 180px;
    min-width: 0;
  }

  /* A date or date-and-time input has an intrinsic minimum width of its own
     and would otherwise reach past the card. */
  .date-input {
    min-width: 0;
  }

  input:focus-visible,
  select:focus-visible,
  button:focus-visible,
  .switch:focus-within {
    outline: 2px solid var(--pm-accent);
    outline-offset: 2px;
  }

  .slider {
    flex: 1 1 auto;
    min-width: 80px;
    accent-color: var(--pm-accent);
  }

  .slider-value {
    flex: 0 0 auto;
    min-width: 3.5em;
    text-align: right;
    font-size: 14px;
    font-variant-numeric: tabular-nums;
    color: var(--pm-text);
  }

  /* A switch built from a real checkbox: it keeps the keyboard behaviour and
     the screen reader announcement that a div with a click handler loses. */
  .switch {
    position: relative;
    flex: 0 0 auto;
    width: 40px;
    height: 22px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--pm-text) 20%, transparent);
    transition: background-color 160ms ease;
  }

  .switch input {
    position: absolute;
    inset: 0;
    margin: 0;
    opacity: 0;
    cursor: pointer;
  }

  .switch::after {
    content: "";
    position: absolute;
    top: 3px;
    left: 3px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--card-background-color, #fff);
    transition: transform 160ms ease;
    pointer-events: none;
  }

  .switch:has(input:checked) {
    background: var(--pm-accent);
  }

  .switch:has(input:checked)::after {
    transform: translateX(18px);
  }

  /* Not set is not off. The integration keeps the two apart on purpose - a
     boolean without a value reports "unknown" rather than falling back to
     false - so a switch resting in the off position would claim something
     nobody said. */
  .switch:has(input:indeterminate) {
    background: transparent;
    box-shadow: inset 0 0 0 2px var(--pm-divider);
  }

  .switch:has(input:indeterminate)::after {
    transform: translateX(9px);
    background: var(--pm-disabled);
  }

  .switch:has(input:disabled) {
    opacity: 0.5;
  }

  .switch:has(input:disabled) input {
    cursor: default;
  }

  /* The row that opens the editors, and the one that closes them. */
  /* A label and the switch it belongs to, the whole row clickable. A bare
     toggle in a corner says that something can be turned on, and nothing
     about what - this says it, and says it in the width the sentence needs. */
  .toolbar {
    display: flex;
    align-items: center;
    gap: var(--pm-gap);
    min-height: 28px;
    cursor: pointer;
  }

  .toolbar-label {
    flex: 1 1 auto;
    min-width: 0;
    color: var(--pm-muted);
    font-size: 14px;
  }

  /* Quiet beside the accent: discarding is the way back, not the point of
     the row, and two filled buttons would ask which one is the safe one. */
  .discard {
    appearance: none;
    min-height: 32px;
    padding: 0 12px;
    border: none;
    border-radius: var(--pm-chip-radius);
    background: none;
    color: var(--pm-muted);
    font: inherit;
    font-size: 13px;
    cursor: pointer;
  }

  .discard:hover {
    color: var(--pm-text);
  }

  .apply {
    appearance: none;
    min-height: 32px;
    padding: 0 16px;
    border: none;
    border-radius: var(--pm-chip-radius);
    background: var(--pm-accent);
    color: var(--text-primary-color, #fff);
    font: inherit;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
  }

  .apply:disabled {
    background: color-mix(in srgb, var(--pm-text) 10%, transparent);
    color: var(--pm-disabled);
    cursor: default;
  }

  /* Footer and messages ---------------------------------------------------- */

  .footer {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 10px;
    color: var(--pm-muted);
    font-size: 12px;
  }

  .note {
    color: var(--pm-muted);
    font-size: 13px;
  }

  .warning {
    color: var(--pm-warning);
  }

  .inline-error {
    margin-top: 8px;
    color: var(--pm-error);
    font-size: 13px;
  }

  .skeleton {
    height: 14px;
    border-radius: 7px;
    background: color-mix(in srgb, var(--pm-text) 10%, transparent);
  }

  .fallback-alert {
    padding: 12px 16px;
    color: var(--pm-error);
    font-size: 14px;
  }

  @media (prefers-reduced-motion: reduce) {
    * {
      transition: none !important;
    }
  }
`,qt="unavailable",It="unknown";function Bt(t){return void 0===t||t===qt||t===It}function Vt(t,e){if(t&&e)return t.states[e]}function Jt(t,e,i){t.dispatchEvent(new CustomEvent(e,{detail:i,bubbles:!0,composed:!0}))}function Kt(t,e){if("function"==typeof t.formatEntityState)return t.formatEntityState(e);const i=e.attributes.unit_of_measurement;return i?`${e.state} ${i}`:e.state}function Ft(t){return void 0!==t&&"none"!==t.action}async function Gt(t,e,i,s){if(!i||"none"===i.action)return;const n=i.entity??s;switch(i.action){case"more-info":return void(n&&function(t,e){Jt(t,"hass-more-info",{entityId:e})}(t,n));case"toggle":return void(n&&await e.callService("homeassistant","toggle",{},{entity_id:n}));case"navigate":return void(i.navigation_path&&(r=i.navigation_path,history.pushState(null,"",r),Jt(window,"location-changed",{replace:!1})));case"url":return void(i.url_path&&window.open(i.url_path,"_blank","noreferrer"));case"perform-action":case"call-service":{const t=i.perform_action??i.service;if(!t||!t.includes("."))return;const[s,n]=t.split(".",2);return void await e.callService(s,n,i.data??i.service_data??{},i.target)}default:return}var r}function Xt(t){return"undefined"!=typeof customElements&&!!customElements.get(t)}function Yt(t,e){return function(t){const e=t?.attributes.mode_key;return"string"==typeof e&&e?e:null}(Vt(t,function(t){return t.preset.entities.active_mode}(e)))}function Zt(t){return t.preset.modes}function Qt(t,e){const i=Yt(t,e);return i?Zt(e).find(t=>t.key===i)??null:null}function te(t){return t.preset.entities.automatic}function ee(t){return t.preset.entities.mode_selection}function ie(t,e){const i=Vt(t,te(e));return!i||Bt(i.state)?null:"on"===i.state}function se(t,e){return e.presetMode&&ee(e)?ie(t,e)?"following":null:"missing"}function ne(t){return t&&Xt("ha-icon")?I`<ha-icon .icon=${t} aria-hidden="true"></ha-icon>`:V}function re(t){const{config:e}=t;if(!e.header.visible)return V;const i=function(t){const e=t.config.header.icon;if(!1===e)return null;if(e)return e;const i=Qt(t.hass,t.subject);return i?.icon??"mdi:tune-variant"}(t),s=!1===e.header.subtitle?null:e.header.subtitle??function(t){const{hass:e,subject:i}=t,s=Qt(e,i),n=s?.name??Lt(e,"no_mode");if(!i.presetMode)return`${n} · ${Lt(e,"no_preset_mode")}`;const r=ie(e,i);return null===r?n:`${n} · ${Lt(e,r?"automatic":"manual")}`}(t),n=e.header.icon_color??function(t){const e=Qt(t.hass,t.subject);return e?t.config.modes.colors[e.key]:void 0}(t),{tappable:r}=t,o=function(t){const{hass:e,subject:i,config:s}=t;if(!s.header.automatic)return V;const n=te(i);if(!n)return V;const r=ie(e,i),o=Lt(e,"mode_automatic");return I`
    <label class="switch-field">
      <span class="switch">
        <input
          type="checkbox"
          role="switch"
          aria-label=${o}
          title=${o}
          .checked=${!0===r}
          .disabled=${null===r}
          @change=${i=>{const s=i.target.checked;t.call(e.callService("switch",s?"turn_on":"turn_off",{},{entity_id:n}))}}
        />
      </span>
    </label>
  `}(t),a=I`
    ${i?I`<div class="icon">${ne(i)}</div>`:V}
    <div class="titles">
      <div class="title">${e.header.title??function(t){return t.subject.preset.name}(t)}</div>
      ${s?I`<div class="subtitle">${s}</div>`:V}
    </div>
  `;return I`
    <div class="header section" style=${n?`--pm-icon-color: ${n}`:""}>
      ${r?I`
            <button
              class="header-main tappable"
              type="button"
              @pointerdown=${()=>t.onHeaderDown()}
              @pointerup=${()=>t.onHeaderUp()}
              @pointercancel=${()=>t.onHeaderUp()}
              @click=${()=>t.onHeaderClick()}
            >
              ${a}
            </button>
          `:I`<div class="header-main">${a}</div>`}
      ${o===V?V:I`<div class="header-end">${o}</div>`}
    </div>
  `}function oe(t,e,i,s){const{config:n}=t;return I`
    <div class="chips" role="group">
      ${e.map(e=>{const r=e.key===i,o=n.modes.colors[e.key];return I`
          <button
            class="chip"
            type="button"
            aria-pressed=${r?"true":"false"}
            ?disabled=${s}
            style=${o?`--pm-chip-color: ${o}`:""}
            @click=${()=>function(t,e){const i=ee(t.subject);i&&t.call(t.hass.callService("preset_manager","set_active_mode",{mode:e},{entity_id:i}))}(t,e.key)}
          >
            ${n.modes.icons?ne(e.icon):V}
            <span>${e.name}</span>
          </button>
        `})}
    </div>
  `}function ae(t){return function(t){const e=t.config.modes.visible;return"manual"===e?null===se(t.hass,t.subject):"never"!==e}(t)?I`<div class="section">${function(t){const e=Zt(t.subject);return e.length?oe(t,e,Yt(t.hass,t.subject),null!==se(t.hass,t.subject)):I`<div class="note">${Lt(t.hass,"no_modes")}</div>`}(t)}</div>`:V}function ce(t,e,i,s,n){if(t.stage)return void t.stage(e.entity_id,{service:i,data:s,display:n});const r=e.entity_id.split(".",1)[0];t.call(t.hass.callService(r,i,s,{entity_id:e.entity_id}))}function le(t,e){const i=t.draft?.get(e.entity_id)?.display;return void 0!==i?{disabled:!1,empty:!1,staged:i}:{disabled:(s=e.state,void 0===s||s===qt),empty:Bt(e.state),staged:void 0};var s}function de(t,e,i){const s=t.attributes[e];return null==s?i:s}function he(t,e,i,s){const{disabled:n,empty:r,staged:o}=le(t,e);let a=o??(r?"":e.state);return void 0===o&&("datetime"===s&&(a=r?"":function(t){const e=new Date(t);if(Number.isNaN(e.getTime()))return"";const i=t=>String(t).padStart(2,"0");return`${e.getFullYear()}-${i(e.getMonth()+1)}-${i(e.getDate())}T${i(e.getHours())}:${i(e.getMinutes())}`}(e.state)),"time"===s&&(a=a.slice(0,5))),I`
    <input
      class="date-input"
      type=${"datetime"===s?"datetime-local":s}
      aria-label=${i}
      .value=${a}
      ?disabled=${n}
      @change=${i=>{const n=i.target.value;n&&ce(t,e,"set_value","date"===s?{date:n}:"time"===s?{time:`${n}:00`}:{datetime:`${n.replace("T"," ")}:00`},n)}}
    />
  `}function ue(t,e,i,s){if(!i)return I`<span class="row-value muted">
      ${Lt(t.hass,"unavailable")}
    </span>`;switch(e){case"number":return function(t,e,i){const{disabled:s,empty:n,staged:r}=le(t,e),o=de(e,"min",0),a=de(e,"max",100),c=de(e,"step",1),l=e.attributes.unit_of_measurement??"",d=r??e.state,h=n?"":d,u=i=>{const s=i.target.valueAsNumber;Number.isNaN(s)||ce(t,e,"set_value",{value:s},String(s))};return"slider"===de(e,"mode","box")?I`
      <input
        class="slider"
        type="range"
        aria-label=${i}
        min=${o}
        max=${a}
        step=${c}
        .value=${n?String(o):h}
        ?disabled=${s}
        @change=${u}
      />
      <span class="slider-value">
        ${n?"—":`${d}${l?` ${l}`:""}`}
      </span>
    `:I`
    <input
      class="number-input"
      type="number"
      inputmode="decimal"
      aria-label=${i}
      min=${o}
      max=${a}
      step=${c}
      .value=${h}
      ?disabled=${s}
      @change=${u}
      @keydown=${i=>{const n="ArrowUp"===i.key?1:"ArrowDown"===i.key?-1:0;if(!n||s)return;i.preventDefault();const r=i.target,l=Number.isNaN(r.valueAsNumber)?o:r.valueAsNumber,d=Math.min(a,Math.max(o,l+n*c));if(d===l)return;const h=(String(c).split(".")[1]??"").length;r.value=d.toFixed(h),ce(t,e,"set_value",{value:Number(r.value)},r.value)}}
    />
    ${l?I`<span class="row-value">${l}</span>`:V}
  `}(t,i,s);case"boolean":return function(t,e,i){const{disabled:s,empty:n,staged:r}=le(t,e);return I`
    <label class="switch">
      <input
        type="checkbox"
        role="switch"
        aria-label=${i}
        .checked=${"on"===(r??e.state)}
        .indeterminate=${n}
        ?disabled=${s}
        @change=${i=>{const s=i.target.checked;ce(t,e,s?"turn_on":"turn_off",{},s?"on":"off")}}
      />
    </label>
  `}(t,i,s);case"select":return function(t,e,i){const{disabled:s,empty:n,staged:r}=le(t,e),o=de(e,"options",[]),a=r??e.state;return I`
    <select
      class="select-input"
      aria-label=${i}
      ?disabled=${s}
      @change=${i=>{const s=i.target.value;ce(t,e,"select_option",{option:s},s)}}
    >
      ${n?I`<option value="" selected disabled>${"—"}</option>`:V}
      ${o.map(t=>I`
          <option value=${t} ?selected=${t===a}>
            ${t}
          </option>
        `)}
    </select>
  `}(t,i,s);case"text":return function(t,e,i){const{disabled:s,empty:n,staged:r}=le(t,e),o=e.attributes.pattern;return I`
    <input
      class="text-input"
      type=${"password"===de(e,"mode","text")?"password":"text"}
      aria-label=${i}
      minlength=${de(e,"min",0)}
      maxlength=${de(e,"max",255)}
      pattern=${o??V}
      .value=${n?"":r??e.state}
      ?disabled=${s}
      @change=${i=>{const s=i.target.value;ce(t,e,"set_value",{value:s},s)}}
    />
  `}(t,i,s);case"date":return he(t,i,s,"date");case"time":return he(t,i,s,"time");case"datetime":return he(t,i,s,"datetime");default:return I`<span class="row-value muted">
        ${Lt(t.hass,"not_editable")}
      </span>`}}function pe(t,e){const i=t.config.values.parameters,s=new Map((i??[]).map(t=>[t.parameter,t]));return function(t,e){if(!e)return t.parameters;const i=new Map(t.parameters.map(t=>[t.key,t]));return e.map(t=>i.get(t)).filter(t=>void 0!==t)}(e,i?i.map(t=>t.parameter):null).map(t=>{const e=s.get(t.key);return{parameter:t,label:e?.name??t.name,icon:e?.icon}})}function me(t,e,i){if(!i)return V;const s=!1===e.icon?void 0:e.icon??(t.config.values.icons?Vt(t.hass,e.parameter.entity)?.attributes.icon:void 0);return I`<span class="row-icon">${ne(s)}</span>`}function fe(t,e,i){const{text:s,muted:n}=function(t,e){const i=Vt(t.hass,e.entity);return i?i.state===It?{text:Lt(t.hass,"not_set"),muted:!0}:Bt(i.state)?{text:Lt(t.hass,"unavailable"),muted:!0}:{text:Kt(t.hass,i),muted:!1}:{text:Lt(t.hass,"unavailable"),muted:!0}}(t,e.parameter);return I`
    <div class="row">
      <div class="row-label">
        ${me(t,e,i)}<span>${e.label}</span>
      </div>
      <div class="row-value ${n?"muted":""}">${s}</div>
    </div>
  `}function _e(t,e,i,s,n){const r=i?e.parameter.editors[i]:void 0,o=Vt(t.hass,r),a=function(t,e){return"number"===t&&void 0!==e&&"slider"===de(e,"mode","box")}(e.parameter.type,o);return I`
    <div class="row ${a?"wide":""}">
      <div class="row-label">
        ${me(t,e,n)}<span>${s}</span>
      </div>
      <div class="row-control">
        ${ue(t,e.parameter.type,o,s)}
      </div>
    </div>
  `}function ve(t){const e={ArrowLeft:-1,ArrowRight:1,Home:-1/0,End:1/0}[t.key];if(void 0===e)return;const i=[...t.currentTarget.querySelectorAll("button.tab")],s=i.indexOf(t.target);if(s<0)return;t.preventDefault();const n=Math.min(Math.max(s+e,0),i.length-1);i[n].focus(),i[n].click()}function be(t){const e=Zt(t.subject);if(!e.length)return V;const i=t.editMode,s=(e,s)=>{const n=e===i;return I`
      <button
        class="tab"
        type="button"
        role="tab"
        aria-selected=${n?"true":"false"}
        tabindex=${n?0:-1}
        @click=${()=>t.selectEditMode(e)}
      >
        ${s}
      </button>
    `};return I`
    <div class="section strip">
      <div
        class="tabs"
        role="tablist"
        aria-label=${Lt(t.hass,"mode")}
        @keydown=${ve}
      >
        ${s(null,Lt(t.hass,"active"))}
        ${e.map(t=>s(t.key,t.name))}
      </div>
    </div>
  `}function ge(t){if(!t.config.values.visible)return V;const e=t.subject.preset,i=pe(t,e);if(!i.length)return I`<div class="section note">
      ${Lt(t.hass,"no_parameters")}
    </div>`;const s=null===t.subject.presetMode?I`<div class="note warning">${Lt(t.hass,"orphaned")}</div>`:V,n=function(t,e){return t.config.values.icons||e.some(t=>"string"==typeof t.icon)}(t,i),r=t.draft.size?function(t){return I`
    <div class="toolbar">
      <span class="toolbar-label"></span>
      <button class="discard" type="button" @click=${()=>t.discard()}>
        ${Lt(t.hass,"discard")}
      </button>
      <button class="apply" type="button" @click=${()=>t.apply()}>
        ${Lt(t.hass,"apply")}
      </button>
    </div>
  `}(t):V,o=t.config.values.mode;if("active"===o)return I`
      <div class="section rows">
        ${s}${i.map(e=>fe(t,e,n))}
      </div>
    `;if("all"===o){const e=Zt(t.subject);return I`
      <div class="section rows">
        ${s}
        ${i.map(i=>I`
            <div class="group-label">${i.label}</div>
            ${e.map(e=>_e(t,i,e.key,e.name,n))}
          `)}
        ${r}
      </div>
    `}if("edit"===o){const e=Yt(t.hass,t.subject);return I`
      <div class="section rows">
        ${s}
        ${i.map(i=>_e(t,i,e,i.label,n))}
        ${r}
      </div>
    `}const a=t.editMode;return I`
    ${be(t)}
    <div class="section rows" role="tabpanel">
      ${s}
      ${null===a?i.map(e=>fe(t,e,n)):i.map(e=>_e(t,e,a,e.label,n))}
      ${r}
    </div>
  `}const ye={action:"more-info"};let $e=class extends at{constructor(){super(...arguments),this._draft=new Map,this._watched=[],this._held=!1,this._lastTap=0}setConfig(t){this._config=At(t),this._viewMode=void 0,this._draft=new Map,this._watched=[]}static getConfigElement(){return document.createElement(`${t}-editor`)}static async getStubConfig(e){const i=Ot(e)??await Pt(e),s=i.presets.find(t=>t.entities.active_mode)?.entities.active_mode;return{type:`custom:${t}`,entity:s??""}}set hass(t){const e=this._hass;if(this._hass=t,!e)return this.requestUpdate(),void this._load();if(e.language===t.language&&e.themes===t.themes){for(const i of this._watched)if(e.states[i]!==t.states[i])return void this.requestUpdate()}else this.requestUpdate()}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),this._load()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe?.(),this._unsubscribe=void 0,this._clearTimers()}async _load(){this._hass&&!this._unsubscribe&&(this._unsubscribe=jt(this._hass,t=>{this._structure=t}),this._structure=await Pt(this._hass))}getCardSize(){const t=this._config;if(!t)return 2;let e=t.header.visible?1:0;return"never"!==t.modes.visible&&(e+=1),t.values.visible&&(e+=2),Math.max(1,e)}getGridOptions(){return{columns:12,min_columns:6}}get _tapAction(){return this._config?.tap_action??ye}_clearTimers(){this._holdTimer&&clearTimeout(this._holdTimer),this._tapTimer&&clearTimeout(this._tapTimer),this._errorTimer&&clearTimeout(this._errorTimer),this._holdTimer=this._tapTimer=this._errorTimer=void 0}_headerDown(t){this._held=!1,Ft(this._config?.hold_action)&&(this._holdTimer=setTimeout(()=>{this._held=!0,this._run(this._config?.hold_action,t)},500))}_headerUp(){this._holdTimer&&clearTimeout(this._holdTimer),this._holdTimer=void 0}_headerClick(t){if(this._held)return void(this._held=!1);const e=this._config?.double_tap_action;if(!Ft(e))return void this._run(this._tapAction,t);const i=Date.now();if(i-this._lastTap<250)return this._tapTimer&&clearTimeout(this._tapTimer),this._tapTimer=void 0,this._lastTap=0,void this._run(e,t);this._lastTap=i,this._tapTimer=setTimeout(()=>{this._tapTimer=void 0,this._run(this._tapAction,t)},250)}_run(t,e){if(!this._hass)return;const i=e.preset.entities.active_mode;this._call(Gt(this,this._hass,t,i??this._config?.entity))}_apply(){if(!this._hass||!this._draft.size)return;const t=this._hass,e=[...this._draft].map(([e,i])=>t.callService(e.split(".",1)[0],i.service,i.data,{entity_id:e}));this._draft=new Map,this._viewMode=void 0,this._call(Promise.all(e))}_call(t){t.then(()=>{void 0!==this._error&&(this._error=void 0)},t=>{this._error=this._messageOf(t),this._errorTimer&&clearTimeout(this._errorTimer),this._errorTimer=setTimeout(()=>{this._errorTimer=void 0,this._error=void 0},6e3)})}_messageOf(t){if("string"==typeof t)return t;if(t&&"object"==typeof t){const e=t,i=e.body;for(const t of[e.message,i?.message,e.error])if("string"==typeof t&&t)return t}return String(t)}willUpdate(t){super.willUpdate(t);const e=this._subject;this._watched=e?function(t){const e=Nt(t.preset);return t.presetMode&&e.push(...zt(t.presetMode)),e}(e):[]}get _subject(){return this._config&&this._structure?Ht(this._structure,this._config.entity):null}_viewedMode(){return this._viewMode??null}render(){const t=this._config,e=this._hass;if(!t||!e)return V;if(!this._structure)return this._shell(this._skeleton());const i=this._subject;if(!i){let i;return i=this._structure.preset_modes.length+this._structure.presets.length?function(t,e){return t.preset_modes.some(t=>zt(t).includes(e))}(this._structure,t.entity)?Lt(e,"not_a_preset",{entity:t.entity}):Lt(e,"not_found",{entity:t.entity}):Lt(e,"not_set_up"),this._shell(this._alert(i))}const s={hass:e,config:t,subject:i,host:this,editMode:this._viewedMode(),selectEditMode:t=>{this._viewMode=t},call:t=>this._call(t),draft:this._draft,stage:(t,e)=>{this._draft=new Map(this._draft).set(t,e)},apply:()=>this._apply(),discard:()=>{this._draft=new Map},tappable:Ft(this._tapAction)||Ft(t.hold_action),onHeaderDown:()=>this._headerDown(i),onHeaderUp:()=>this._headerUp(),onHeaderClick:()=>this._headerClick(i)};return this._shell(I`
      ${re(s)} ${ae(s)} ${ge(s)}
     
      ${this._error?I`<div class="section inline-error" role="alert">${this._error}</div>`:V}
    `)}_shell(t){return I`<ha-card>${t}</ha-card>`}_skeleton(){return I`
      <div class="section rows" aria-busy="true" aria-label=${Lt(this._hass,"loading")}>
        <div class="skeleton" style="width:45%"></div>
        <div class="skeleton" style="width:70%"></div>
      </div>
    `}_alert(t){return Xt("ha-alert")?I`<ha-alert alert-type="warning">${t}</ha-alert>`:I`<div class="fallback-alert" role="alert">${t}</div>`}};$e.styles=Wt,e([ut()],$e.prototype,"_config",void 0),e([ut()],$e.prototype,"_structure",void 0),e([ut()],$e.prototype,"_viewMode",void 0),e([ut()],$e.prototype,"_draft",void 0),e([ut()],$e.prototype,"_error",void 0),$e=e([lt(t)],$e);const we={entity:"Entity",header:"Header",modes:"Modes",values:"Values",actions:"Actions",visible:"Show",automatic:"Automatic switch",title:"Title",subtitle:"Subtitle",icon:"Icon",icon_color:"Icon colour",icons:"Show icons",parameters:"Parameters",parameters_note:"Parameters",mode:"Which mode",content:"Content",tap_action:"Tap",hold_action:"Hold",double_tap_action:"Double tap"},xe=["more-info","navigate","url","perform-action","none"];function Ae(t){return{selector:{select:{mode:"dropdown",options:t.map(([t,e])=>({value:t,label:e}))}}}}let ke=class extends at{constructor(){super(...arguments),this._config={},this._label=t=>t.name&&we[t.name]||t.title||t.name||""}set hass(t){this._hass=t,this._structure??=Ot(t),this._load(),this.requestUpdate()}get hass(){return this._hass}setConfig(t){this._config=t}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe?.(),this._unsubscribe=void 0}async _load(){this._hass&&!this._unsubscribe&&(this._unsubscribe=jt(this._hass,t=>{this._structure=t}),this._structure=await Pt(this._hass))}_entityPicker(){const t=(this._structure?.presets??[]).map(t=>t.entities.active_mode).filter(t=>Boolean(t));return t.length?{include_entities:t}:{integration:"preset_manager"}}_hasParameterOverrides(){const t=this._config.values,e=t?.parameters;return Array.isArray(e)&&e.some(t=>"string"!=typeof t)}get _subject(){const t=this._config.entity;return this._structure&&"string"==typeof t&&t?Ht(this._structure,t):null}_schema(t){const e=t?t.preset.modes:[],i=[{name:"entity",required:!0,selector:{entity:this._entityPicker()}},{type:"expandable",name:"header",title:we.header,schema:[{name:"visible",selector:{boolean:{}}},{name:"automatic",selector:{boolean:{}}},{name:"title",selector:{text:{}}},{name:"subtitle",selector:{text:{}}},{name:"icon",selector:{icon:{}}},{name:"icon_color",selector:{ui_color:{}}}]},{type:"expandable",name:"modes",title:we.modes,schema:[{name:"visible",...Ae([["always","Always"],["never","Never"],["manual","While the mode can be set by hand"]])},...e.some(t=>t.icon)?[{name:"icons",selector:{boolean:{}}}]:[]]}];if(t){const e=t.preset.parameters.map(t=>({value:t.key,label:t.name}));i.push({type:"expandable",name:"values",title:we.values,schema:[{name:"visible",selector:{boolean:{}}},{name:"mode",...Ae([["active","Show the active values"],["picker","Pick a mode in the card"],["edit","Edit the active mode"],["all","Every mode at once"]])},this._hasParameterOverrides()?{name:"parameters_note",type:"constant",value:"Renamed parameters are edited in YAML."}:{name:"parameters",selector:{select:{multiple:!0,mode:"list",options:e}}},{name:"icons",selector:{boolean:{}}}]})}return i.push({type:"expandable",title:we.actions,schema:[{name:"tap_action",selector:{ui_action:{actions:xe}}},{name:"hold_action",selector:{ui_action:{actions:xe}}},{name:"double_tap_action",selector:{ui_action:{actions:xe}}}]}),i}_formData(){try{const e=At({type:`custom:${t}`,...this._config,entity:this._config.entity??"sensor.placeholder"});return{...e,entity:this._config.entity??"",values:{...e.values,parameters:this._config.values?.parameters}}}catch(t){return{...this._config}}}_valueChanged(t){t.stopPropagation();Jt(this,"config-changed",{config:kt({...t.detail.value})})}render(){if(!this._hass)return V;const t=this._subject;return I`
      <ha-form
        .hass=${this._hass}
        .data=${this._formData()}
        .schema=${this._schema(t)}
        .computeLabel=${this._label}
        @value-changed=${this._valueChanged}
      ></ha-form>
      ${this._config.entity&&!t&&this._structure?I`<p style="color: var(--error-color)">
            ${Lt(this._hass,"not_found",{entity:String(this._config.entity)})}
          </p>`:V}
    `}};e([ut()],ke.prototype,"_config",void 0),e([ut()],ke.prototype,"_structure",void 0),ke=e([lt(`${t}-editor`)],ke),window.customCards=window.customCards??[],window.customCards.some(e=>e.type===t)||window.customCards.push({type:t,name:"Preset Manager",description:"The values of a preset, with the mode it is on right now.",preview:!1,documentationURL:"https://github.com/julezdean/ha-preset-manager"}),console.info("%c PRESET-MANAGER-CARD %c 0.4.0 ","color: white; background: #03a9f4; font-weight: 700;","color: #03a9f4; background: white; font-weight: 700;");

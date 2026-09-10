const e="preset-manager-card";function t(e,t,i,s){var n,r=arguments.length,o=r<3?t:null===s?s=Object.getOwnPropertyDescriptor(t,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(e,t,i,s);else for(var a=e.length-1;a>=0;a--)(n=e[a])&&(o=(r<3?n(o):r>3?n(t,i,o):n(t,i))||o);return r>3&&o&&Object.defineProperty(t,i,o),o}"function"==typeof SuppressedError&&SuppressedError;const i=globalThis,s=i.ShadowRoot&&(void 0===i.ShadyCSS||i.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap;let o=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(s&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=r.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&r.set(t,e))}return e}toString(){return this.cssText}};const a=s?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new o("string"==typeof e?e:e+"",void 0,n))(t)})(e):e,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:u,getPrototypeOf:p}=Object,m=globalThis,f=m.trustedTypes,_=f?f.emptyScript:"",v=m.reactiveElementPolyfillSupport,b=(e,t)=>e,g={toAttribute(e,t){switch(t){case Boolean:e=e?_:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},y=(e,t)=>!c(e,t),$={attribute:!0,type:String,converter:g,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=$){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(e,i,t);void 0!==s&&l(this.prototype,e,s)}}static getPropertyDescriptor(e,t,i){const{get:s,set:n}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:s,set(t){const r=s?.call(this);n?.call(this,t),this.requestUpdate(e,r,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??$}static _$Ei(){if(this.hasOwnProperty(b("elementProperties")))return;const e=p(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(b("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(b("properties"))){const e=this.properties,t=[...h(e),...u(e)];for(const i of t)this.createProperty(i,e[i])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,i]of t)this.elementProperties.set(e,i)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const i=this._$Eu(e,t);void 0!==i&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(a(e))}else void 0!==e&&t.push(a(e));return t}static _$Eu(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const i of t.keys())this.hasOwnProperty(i)&&(e.set(i,this[i]),delete this[i]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{if(s)e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const s of t){const t=document.createElement("style"),n=i.litNonce;void 0!==n&&t.setAttribute("nonce",n),t.textContent=s.cssText,e.appendChild(t)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$ET(e,t){const i=this.constructor.elementProperties.get(e),s=this.constructor._$Eu(e,i);if(void 0!==s&&!0===i.reflect){const n=(void 0!==i.converter?.toAttribute?i.converter:g).toAttribute(t,i.type);this._$Em=e,null==n?this.removeAttribute(s):this.setAttribute(s,n),this._$Em=null}}_$AK(e,t){const i=this.constructor,s=i._$Eh.get(e);if(void 0!==s&&this._$Em!==s){const e=i.getPropertyOptions(s),n="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:g;this._$Em=s;const r=n.fromAttribute(t,e.type);this[s]=r??this._$Ej?.get(s)??r,this._$Em=null}}requestUpdate(e,t,i,s=!1,n){if(void 0!==e){const r=this.constructor;if(!1===s&&(n=this[e]),i??=r.getPropertyOptions(e),!((i.hasChanged??y)(n,t)||i.useDefault&&i.reflect&&n===this._$Ej?.get(e)&&!this.hasAttribute(r._$Eu(e,i))))return;this.C(e,t,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:i,reflect:s,wrapped:n},r){i&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,r??t??this[e]),!0!==n||void 0!==r)||(this._$AL.has(e)||(this.hasUpdated||i||(t=void 0),this._$AL.set(e,t)),!0===s&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,i]of e){const{wrapped:e}=i,s=this[t];!0!==e||this._$AL.has(t)||void 0===s||this.C(t,void 0,i,s)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[b("elementProperties")]=new Map,w[b("finalized")]=new Map,v?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,A=e=>e,k=x.trustedTypes,E=k?k.createPolicy("lit-html",{createHTML:e=>e}):void 0,S="$lit$",M=`lit$${Math.random().toFixed(9).slice(2)}$`,T="?"+M,C=`<${T}>`,P=document,j=()=>P.createComment(""),N=e=>null===e||"object"!=typeof e&&"function"!=typeof e,O=Array.isArray,U="[ \t\n\f\r]",z=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,H=/-->/g,R=/>/g,D=RegExp(`>|${U}(?:([^\\s"'>=/]+)(${U}*=${U}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),L=/'/g,B=/"/g,I=/^(?:script|style|textarea|title)$/i,W=(e=>(t,...i)=>({_$litType$:e,strings:t,values:i}))(1),q=Symbol.for("lit-noChange"),F=Symbol.for("lit-nothing"),V=new WeakMap,J=P.createTreeWalker(P,129);function K(e,t){if(!O(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(t):t}const G=(e,t)=>{const i=e.length-1,s=[];let n,r=2===t?"<svg>":3===t?"<math>":"",o=z;for(let t=0;t<i;t++){const i=e[t];let a,c,l=-1,d=0;for(;d<i.length&&(o.lastIndex=d,c=o.exec(i),null!==c);)d=o.lastIndex,o===z?"!--"===c[1]?o=H:void 0!==c[1]?o=R:void 0!==c[2]?(I.test(c[2])&&(n=RegExp("</"+c[2],"g")),o=D):void 0!==c[3]&&(o=D):o===D?">"===c[0]?(o=n??z,l=-1):void 0===c[1]?l=-2:(l=o.lastIndex-c[2].length,a=c[1],o=void 0===c[3]?D:'"'===c[3]?B:L):o===B||o===L?o=D:o===H||o===R?o=z:(o=D,n=void 0);const h=o===D&&e[t+1].startsWith("/>")?" ":"";r+=o===z?i+C:l>=0?(s.push(a),i.slice(0,l)+S+i.slice(l)+M+h):i+M+(-2===l?t:h)}return[K(e,r+(e[i]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),s]};class X{constructor({strings:e,_$litType$:t},i){let s;this.parts=[];let n=0,r=0;const o=e.length-1,a=this.parts,[c,l]=G(e,t);if(this.el=X.createElement(c,i),J.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(s=J.nextNode())&&a.length<o;){if(1===s.nodeType){if(s.hasAttributes())for(const e of s.getAttributeNames())if(e.endsWith(S)){const t=l[r++],i=s.getAttribute(e).split(M),o=/([.?@])?(.*)/.exec(t);a.push({type:1,index:n,name:o[2],strings:i,ctor:"."===o[1]?te:"?"===o[1]?ie:"@"===o[1]?se:ee}),s.removeAttribute(e)}else e.startsWith(M)&&(a.push({type:6,index:n}),s.removeAttribute(e));if(I.test(s.tagName)){const e=s.textContent.split(M),t=e.length-1;if(t>0){s.textContent=k?k.emptyScript:"";for(let i=0;i<t;i++)s.append(e[i],j()),J.nextNode(),a.push({type:2,index:++n});s.append(e[t],j())}}}else if(8===s.nodeType)if(s.data===T)a.push({type:2,index:n});else{let e=-1;for(;-1!==(e=s.data.indexOf(M,e+1));)a.push({type:7,index:n}),e+=M.length-1}n++}}static createElement(e,t){const i=P.createElement("template");return i.innerHTML=e,i}}function Y(e,t,i=e,s){if(t===q)return t;let n=void 0!==s?i._$Co?.[s]:i._$Cl;const r=N(t)?void 0:t._$litDirective$;return n?.constructor!==r&&(n?._$AO?.(!1),void 0===r?n=void 0:(n=new r(e),n._$AT(e,i,s)),void 0!==s?(i._$Co??=[])[s]=n:i._$Cl=n),void 0!==n&&(t=Y(e,n._$AS(e,t.values),n,s)),t}class Z{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:i}=this._$AD,s=(e?.creationScope??P).importNode(t,!0);J.currentNode=s;let n=J.nextNode(),r=0,o=0,a=i[0];for(;void 0!==a;){if(r===a.index){let t;2===a.type?t=new Q(n,n.nextSibling,this,e):1===a.type?t=new a.ctor(n,a.name,a.strings,this,e):6===a.type&&(t=new ne(n,this,e)),this._$AV.push(t),a=i[++o]}r!==a?.index&&(n=J.nextNode(),r++)}return J.currentNode=P,s}p(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class Q{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,s){this.type=2,this._$AH=F,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=Y(this,e,t),N(e)?e===F||null==e||""===e?(this._$AH!==F&&this._$AR(),this._$AH=F):e!==this._$AH&&e!==q&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>O(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==F&&N(this._$AH)?this._$AA.nextSibling.data=e:this.T(P.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:i}=e,s="number"==typeof i?this._$AC(e):(void 0===i.el&&(i.el=X.createElement(K(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(t);else{const e=new Z(s,this),i=e.u(this.options);e.p(t),this.T(i),this._$AH=e}}_$AC(e){let t=V.get(e.strings);return void 0===t&&V.set(e.strings,t=new X(e)),t}k(e){O(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,s=0;for(const n of e)s===t.length?t.push(i=new Q(this.O(j()),this.O(j()),this,this.options)):i=t[s],i._$AI(n),s++;s<t.length&&(this._$AR(i&&i._$AB.nextSibling,s),t.length=s)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=A(e).nextSibling;A(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class ee{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,s,n){this.type=1,this._$AH=F,this._$AN=void 0,this.element=e,this.name=t,this._$AM=s,this.options=n,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=F}_$AI(e,t=this,i,s){const n=this.strings;let r=!1;if(void 0===n)e=Y(this,e,t,0),r=!N(e)||e!==this._$AH&&e!==q,r&&(this._$AH=e);else{const s=e;let o,a;for(e=n[0],o=0;o<n.length-1;o++)a=Y(this,s[i+o],t,o),a===q&&(a=this._$AH[o]),r||=!N(a)||a!==this._$AH[o],a===F?e=F:e!==F&&(e+=(a??"")+n[o+1]),this._$AH[o]=a}r&&!s&&this.j(e)}j(e){e===F?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class te extends ee{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===F?void 0:e}}class ie extends ee{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==F)}}class se extends ee{constructor(e,t,i,s,n){super(e,t,i,s,n),this.type=5}_$AI(e,t=this){if((e=Y(this,e,t,0)??F)===q)return;const i=this._$AH,s=e===F&&i!==F||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,n=e!==F&&(i===F||s);s&&this.element.removeEventListener(this.name,this,i),n&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ne{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){Y(this,e)}}const re=x.litHtmlPolyfillSupport;re?.(X,Q),(x.litHtmlVersions??=[]).push("3.3.3");const oe=globalThis;class ae extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{const s=i?.renderBefore??t;let n=s._$litPart$;if(void 0===n){const e=i?.renderBefore??null;s._$litPart$=n=new Q(t.insertBefore(j(),e),e,void 0,i??{})}return n._$AI(e),n})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return q}}ae._$litElement$=!0,ae.finalized=!0,oe.litElementHydrateSupport?.({LitElement:ae});const ce=oe.litElementPolyfillSupport;ce?.({LitElement:ae}),(oe.litElementVersions??=[]).push("4.2.2");const le=e=>(t,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)},de={attribute:!0,type:String,converter:g,reflect:!1,hasChanged:y},he=(e=de,t,i)=>{const{kind:s,metadata:n}=i;let r=globalThis.litPropertyMetadata.get(n);if(void 0===r&&globalThis.litPropertyMetadata.set(n,r=new Map),"setter"===s&&((e=Object.create(e)).wrapped=!0),r.set(i.name,e),"accessor"===s){const{name:s}=i;return{set(i){const n=t.get.call(this);t.set.call(this,i),this.requestUpdate(s,n,e,!0,i)},init(t){return void 0!==t&&this.C(s,void 0,e,t),t}}}if("setter"===s){const{name:s}=i;return function(i){const n=this[s];t.call(this,i),this.requestUpdate(s,n,e,!0,i)}}throw Error("Unsupported decorator location: "+s)};function ue(e){return function(e){return(t,i)=>"object"==typeof i?he(e,t,i):((e,t,i)=>{const s=t.hasOwnProperty(i);return t.constructor.createProperty(i,e),s?Object.getOwnPropertyDescriptor(t,i):void 0})(e,t,i)}({...e,state:!0,attribute:!1})}class pe extends Error{}const me=["chips","dropdown"],fe=["always","never","manual"],_e=["picker","active","all"],ve=["preset_mode","blueprint","source","last_changed"];function be(e){throw new pe(e)}function ge(e,t){return null==e?{}:(("object"!=typeof e||Array.isArray(e))&&be(`"${t}" has to be a group of options, for example "${t}: {visible: false}"`),e)}function ye(e,t,i){return void 0===e?i:("boolean"!=typeof e&&be(`"${t}" has to be true or false`),e)}function $e(e,t){if(null!=e)return"string"!=typeof e&&be(`"${t}" has to be text`),e}function we(e,t,i,s){return void 0===e?s:("string"==typeof e&&i.includes(e)||be(`"${t}" has to be one of ${i.join(", ")}`),e)}function xe(e,t){if(null!=e)return!1!==e&&("string"!=typeof e&&be(`"${t}" has to be text, or false to hide it`),e)}function Ae(e,t){const i=ge(e,t),s={};for(const[e,n]of Object.entries(i))"string"!=typeof n&&be(`"${t}.${e}" has to be a colour`),s[e]=n;return s}function ke(e){return null==e?null:(Array.isArray(e)||be('"values.parameters" has to be a list of parameter keys'),e.map((e,t)=>{const i=`values.parameters[${t}]`;if("string"==typeof e)return{parameter:e};"object"==typeof e&&null!==e&&"parameter"in e||be(`"${i}" has to be a parameter key, or a group with a "parameter" key`);const s=$e(e.parameter,`${i}.parameter`);s||be(`"${i}.parameter" is required`);const n={parameter:s},r=$e(e.name,`${i}.name`);void 0!==r&&(n.name=r);const o=xe(e.icon,`${i}.icon`);return void 0!==o&&(n.icon=o),n}))}function Ee(e){return null==e?[]:(Array.isArray(e)||be('"footer.content" has to be a list'),e.map((e,t)=>we(e,`footer.content[${t}]`,ve,"preset_mode")))}function Se(e){"object"==typeof e&&null!==e||be("The card needs a configuration.");const t=e,i=$e(t.entity,"entity");i||be('Pick an entity of Preset Manager, for example "entity: sensor.house_mode_mode" or the active mode sensor of a preset.'),i.includes(".")||be(`"${i}" is not an entity id.`);const s=ge(t.header,"header"),n=ge(t.modes,"modes"),r=ge(t.values,"values"),o=ge(t.editor,"editor"),a=ge(t.footer,"footer"),c={type:String(t.type??""),entity:i,header:{visible:ye(s.visible,"header.visible",!0),automatic:ye(s.automatic,"header.automatic",!0),title:$e(s.title,"header.title"),subtitle:xe(s.subtitle,"header.subtitle"),icon:xe(s.icon,"header.icon"),icon_color:$e(s.icon_color,"header.icon_color")},modes:{visible:(l=n.visible,d="modes.visible",h="always",void 0===l?h:!0===l?"always":!1===l?"never":("string"==typeof l&&fe.includes(l)||be(`"${d}" has to be true, false, or one of ${fe.join(", ")}`),l)),icons:ye(n.icons,"modes.icons",!0),colors:Ae(n.colors,"modes.colors")},values:{visible:ye(r.visible,"values.visible",!0),parameters:ke(r.parameters),icons:ye(r.icons,"values.icons",!1)},editor:{enabled:ye(o.enabled,"editor.enabled",!1),mode:we(o.mode,"editor.mode",_e,"picker"),style:we(o.style,"editor.style",me,"chips"),default_mode:$e(o.default_mode,"editor.default_mode")},footer:{visible:ye(a.visible,"footer.visible",void 0!==a.content),content:Ee(a.content)},tap_action:t.tap_action,hold_action:t.hold_action,double_tap_action:t.double_tap_action};var l,d,h;return c.footer.visible&&!c.footer.content.length&&(c.footer.content=["preset_mode"]),c}function Me(t){const i=String(t.type??`custom:${e}`),s="string"==typeof t.entity?t.entity:"";let n={};try{n=Se({type:i,entity:s||"sensor.placeholder"})}catch(e){n={}}const r={type:i,entity:s};for(const[e,i]of Object.entries(t)){if("type"===e||"entity"===e)continue;const t=Te(i,n[e]);void 0!==t&&(r[e]=t)}return r}function Te(e,t){if(null!=e&&""!==e){if(Array.isArray(e))return e.length?e:void 0;if("object"==typeof e){const i=e,s=t??{},n={};for(const[e,t]of Object.entries(i)){const i=Te(t,s[e]);void 0!==i&&JSON.stringify(i)!==JSON.stringify(s[e])&&(n[e]=i)}return Object.keys(n).length?n:void 0}return e===t?void 0:e}}const Ce={preset_modes:[],presets:[],blueprints:[]};class Pe{constructor(e){this._hass=e,this._listeners=new Set,this._unsubscribes=[]}get current(){return this._config}async load(e){return this._hass=e,this._config?this._config:(this._pending||(this._pending=this._fetch()),this._pending)}subscribe(e){return this._listeners.add(e),1===this._listeners.size&&this._watch(),()=>{this._listeners.delete(e),this._listeners.size||this._stop()}}async _fetch(){try{const e=await this._hass.callWS({type:"preset_manager/config"});return this._apply(e),e}catch(e){return this._apply(Ce),Ce}finally{this._pending=void 0}}_apply(e){const t=JSON.stringify(e);if(t!==this._serialised){this._serialised=t,this._config=e;for(const t of this._listeners)t(e)}}async _watch(){for(const e of["entity_registry_updated","device_registry_updated"])try{const t=await this._hass.connection.subscribeEvents(()=>this._scheduleRefresh(),e);this._listeners.size?this._unsubscribes.push(()=>{t()}):t()}catch(e){}}_scheduleRefresh(){this._timer&&clearTimeout(this._timer),this._timer=setTimeout(()=>{this._timer=void 0,this._config=void 0,this._pending=this._fetch()},400)}_stop(){for(this._timer&&clearTimeout(this._timer),this._timer=void 0;this._unsubscribes.length;)this._unsubscribes.pop()()}}const je=new WeakMap;function Ne(e){let t=je.get(e.connection);return t||(t=new Pe(e),je.set(e.connection,t)),t}function Oe(e){return Ne(e).load(e)}function Ue(e){return Ne(e).current}function ze(e,t){return Ne(e).subscribe(t)}const He="unavailable",Re="unknown";function De(e){return void 0===e||e===He||e===Re}function Le(e,t){if(e&&t)return e.states[t]}function Be(e,t,i){e.dispatchEvent(new CustomEvent(t,{detail:i,bubbles:!0,composed:!0}))}function Ie(e,t){if("function"==typeof e.formatEntityState)return e.formatEntityState(t);const i=t.attributes.unit_of_measurement;return i?`${t.state} ${i}`:t.state}function We(e){return void 0!==e&&"none"!==e.action}async function qe(e,t,i,s){if(!i||"none"===i.action)return;const n=i.entity??s;switch(i.action){case"more-info":return void(n&&function(e,t){Be(e,"hass-more-info",{entityId:t})}(e,n));case"toggle":return void(n&&await t.callService("homeassistant","toggle",{},{entity_id:n}));case"navigate":return void(i.navigation_path&&(r=i.navigation_path,history.pushState(null,"",r),Be(window,"location-changed",{replace:!1})));case"url":return void(i.url_path&&window.open(i.url_path,"_blank","noreferrer"));case"perform-action":case"call-service":{const e=i.perform_action??i.service;if(!e||!e.includes("."))return;const[s,n]=e.split(".",2);return void await t.callService(s,n,i.data??i.service_data??{},i.target)}default:return}var r}function Fe(e){return"undefined"!=typeof customElements&&!!customElements.get(e)}function Ve(e){return e.preset.entities.active_mode}function Je(e,t){return function(e){const t=e?.attributes.mode_key;return"string"==typeof t&&t?t:null}(Le(e,Ve(t)))}function Ke(e){return e.preset.modes}function Ge(e,t){const i=Je(e,t);return i?Ke(t).find(e=>e.key===i)??null:null}function Xe(e){return e.preset.entities.automatic}function Ye(e){return e.preset.entities.mode_selection}function Ze(e,t){const i=Le(e,Xe(t));return!i||De(i.state)?null:"on"===i.state}function Qe(e,t){return t.presetMode&&Ye(t)?Ze(e,t)?"following":null:"missing"}function et(e,t){return{preset:t,presetMode:e.preset_modes.find(e=>e.id===t.preset_mode)??null,blueprint:e.blueprints.find(e=>e.id===t.blueprint)??null}}function tt(e){const t=Object.values(e.entities);for(const i of e.parameters)i.entity&&t.push(i.entity),t.push(...Object.values(i.editors));return t}function it(e){const t=Object.values(e.entities);return e.source_entity&&t.push(e.source_entity),t}function st(e,t){for(const i of e.presets)if(tt(i).includes(t))return et(e,i);return null}const nt={active:"Active",apply:"Apply",automatic:"Automatic",blueprint:"Blueprint",changed:"Changed",editing:"Edit",follows:"Follows {entity}",mode_automatic:"Automatic mode selection",loading:"Loading…",manual:"Manual",mode:"Mode",no_entity:"Set “entity” to any entity of a preset.",not_a_preset:"“{entity}” belongs to a preset mode. A card shows a preset; point it at one of its entities.",no_mode:"No mode active",no_modes:"This preset mode has no modes yet.",no_parameters:"This preset has no parameters yet.",no_preset_mode:"No preset mode",not_editable:"Not editable here",not_found:"“{entity}” does not belong to Preset Manager.",not_set:"Not set",not_set_up:"Preset Manager is not set up.",orphaned:"Waiting for a preset mode; values do not resolve.",preset_mode:"Preset mode",source:"Source",unavailable:"Unavailable"},rt={en:nt,de:{active:"Aktiv",apply:"Übernehmen",automatic:"Automatik",blueprint:"Blueprint",changed:"Geändert",editing:"Bearbeiten",follows:"Folgt {entity}",mode_automatic:"Mode-Automatik",loading:"Wird geladen…",manual:"Manuell",mode:"Mode",no_entity:"„entity“ auf eine beliebige Entität eines Presets setzen.",not_a_preset:"„{entity}“ gehört zu einem Preset Mode. Eine Card zeigt ein Preset; zeig auf eine seiner Entitäten.",no_mode:"Kein Mode aktiv",no_modes:"Dieser Preset Mode hat noch keine Modes.",no_parameters:"Dieses Preset hat noch keine Parameter.",no_preset_mode:"Kein Preset Mode",not_editable:"Hier nicht editierbar",not_found:"„{entity}“ gehört nicht zu Preset Manager.",not_set:"Nicht gesetzt",not_set_up:"Preset Manager ist nicht eingerichtet.",orphaned:"Wartet auf einen Preset Mode; die Werte lösen nicht auf.",preset_mode:"Preset Mode",source:"Quelle",unavailable:"Nicht verfügbar"}};function ot(e,t,i={}){const s=(e?.language??"en").toLowerCase().split("-")[0];let n=(rt[s]??nt)[t]??nt[t]??t;for(const[e,t]of Object.entries(i))n=n.replace(`{${e}}`,String(t));return n}const at=((e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,i,s)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[s+1],e[0]);return new o(i,e,n)})`
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

  /* A rule only ever appears between two sections that are both there, so an
     empty card never shows a line with nothing on either side of it. */
  .section + .section {
    border-top: 1px solid var(--pm-divider);
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

  /* The mode row changes the house; the editing row changes what this card
     shows. Two rows of identical chips said those were the same kind of act.
     This one is smaller, carries no icons and takes its selected colour from
     the text rather than the accent - a switch on the card, not a state of
     the home. */
  .chips.secondary .chip {
    min-height: 26px;
    padding: 0 10px;
    font-size: 12px;
    background: transparent;
    box-shadow: inset 0 0 0 1px var(--pm-divider);
  }

  .chips.secondary .chip:hover:not(:disabled) {
    background: color-mix(in srgb, var(--pm-text) 8%, transparent);
  }

  .chips.secondary .chip[aria-pressed="true"] {
    background: color-mix(in srgb, var(--pm-text) 14%, transparent);
    box-shadow: none;
    color: var(--pm-text);
  }

  .chip:disabled:not([aria-pressed="true"]) {
    color: var(--pm-disabled);
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
`;function ct(e){return e&&Fe("ha-icon")?W`<ha-icon .icon=${e} aria-hidden="true"></ha-icon>`:F}function lt(e){const{config:t}=e;if(!t.header.visible)return F;const i=function(e){const t=e.config.header.icon;if(!1===t)return null;if(t)return t;const i=Ge(e.hass,e.subject);return i?.icon??"mdi:tune-variant"}(e),s=!1===t.header.subtitle?null:t.header.subtitle??function(e){const{hass:t,subject:i}=e,s=Ge(t,i),n=s?.name??ot(t,"no_mode");if(!i.presetMode)return`${n} · ${ot(t,"no_preset_mode")}`;const r=Ze(t,i);return null===r?n:`${n} · ${ot(t,r?"automatic":"manual")}`}(e),n=t.header.icon_color??function(e){const t=Ge(e.hass,e.subject);return t?e.config.modes.colors[t.key]:void 0}(e),{tappable:r}=e,o=function(e){const{hass:t,subject:i,config:s}=e;if(!s.header.automatic)return F;const n=Xe(i);if(!n)return F;const r=Ze(t,i),o=ot(t,"mode_automatic");return W`
    <label class="switch-field">
      <span class="switch">
        <input
          type="checkbox"
          role="switch"
          aria-label=${o}
          title=${o}
          .checked=${!0===r}
          .disabled=${null===r}
          @change=${i=>{const s=i.target.checked;e.call(t.callService("switch",s?"turn_on":"turn_off",{},{entity_id:n}))}}
        />
      </span>
    </label>
  `}(e),a=W`
    ${i?W`<div class="icon">${ct(i)}</div>`:F}
    <div class="titles">
      <div class="title">${t.header.title??function(e){return e.subject.preset.name}(e)}</div>
      ${s?W`<div class="subtitle">${s}</div>`:F}
    </div>
  `;return W`
    <div class="header section" style=${n?`--pm-icon-color: ${n}`:""}>
      ${r?W`
            <button
              class="header-main tappable"
              type="button"
              @pointerdown=${()=>e.onHeaderDown()}
              @pointerup=${()=>e.onHeaderUp()}
              @pointercancel=${()=>e.onHeaderUp()}
              @click=${()=>e.onHeaderClick()}
            >
              ${a}
            </button>
          `:W`<div class="header-main">${a}</div>`}
      ${o===F?F:W`<div class="header-end">${o}</div>`}
    </div>
  `}function dt(e,t,i,s){const{config:n}=e;return W`
    <div class="chips" role="group">
      ${t.map(t=>{const r=t.key===i,o=n.modes.colors[t.key];return W`
          <button
            class="chip"
            type="button"
            aria-pressed=${r?"true":"false"}
            ?disabled=${s}
            style=${o?`--pm-chip-color: ${o}`:""}
            @click=${()=>function(e,t){const i=Ye(e.subject);i&&e.call(e.hass.callService("preset_manager","set_active_mode",{mode:t},{entity_id:i}))}(e,t.key)}
          >
            ${n.modes.icons?ct(t.icon):F}
            <span>${t.name}</span>
          </button>
        `})}
    </div>
  `}function ht(e){return function(e){const t=e.config.modes.visible;return"manual"===t?null===Qe(e.hass,e.subject):"never"!==t}(e)?W`<div class="section">${function(e){const t=Ke(e.subject);return t.length?dt(e,t,Je(e.hass,e.subject),null!==Qe(e.hass,e.subject)):W`<div class="note">${ot(e.hass,"no_modes")}</div>`}(e)}</div>`:F}function ut(e,t,i,s,n){if(e.stage)return void e.stage(t.entity_id,{service:i,data:s,display:n});const r=t.entity_id.split(".",1)[0];e.call(e.hass.callService(r,i,s,{entity_id:t.entity_id}))}function pt(e,t){const i=e.draft?.get(t.entity_id)?.display;return void 0!==i?{disabled:!1,empty:!1,staged:i}:{disabled:(s=t.state,void 0===s||s===He),empty:De(t.state),staged:void 0};var s}function mt(e,t,i){const s=e.attributes[t];return null==s?i:s}function ft(e,t,i,s){const{disabled:n,empty:r,staged:o}=pt(e,t);let a=o??(r?"":t.state);return void 0===o&&("datetime"===s&&(a=r?"":function(e){const t=new Date(e);if(Number.isNaN(t.getTime()))return"";const i=e=>String(e).padStart(2,"0");return`${t.getFullYear()}-${i(t.getMonth()+1)}-${i(t.getDate())}T${i(t.getHours())}:${i(t.getMinutes())}`}(t.state)),"time"===s&&(a=a.slice(0,5))),W`
    <input
      class="date-input"
      type=${"datetime"===s?"datetime-local":s}
      aria-label=${i}
      .value=${a}
      ?disabled=${n}
      @change=${i=>{const n=i.target.value;n&&ut(e,t,"set_value","date"===s?{date:n}:"time"===s?{time:`${n}:00`}:{datetime:`${n.replace("T"," ")}:00`},n)}}
    />
  `}function _t(e,t,i,s){if(!i)return W`<span class="row-value muted">
      ${ot(e.hass,"unavailable")}
    </span>`;switch(t){case"number":return function(e,t,i){const{disabled:s,empty:n,staged:r}=pt(e,t),o=mt(t,"min",0),a=mt(t,"max",100),c=mt(t,"step",1),l=t.attributes.unit_of_measurement??"",d=r??t.state,h=n?"":d,u=i=>{const s=i.target.valueAsNumber;Number.isNaN(s)||ut(e,t,"set_value",{value:s},String(s))};return"slider"===mt(t,"mode","box")?W`
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
    `:W`
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
      @keydown=${i=>{const n="ArrowUp"===i.key?1:"ArrowDown"===i.key?-1:0;if(!n||s)return;i.preventDefault();const r=i.target,l=Number.isNaN(r.valueAsNumber)?o:r.valueAsNumber,d=Math.min(a,Math.max(o,l+n*c));if(d===l)return;const h=(String(c).split(".")[1]??"").length;r.value=d.toFixed(h),ut(e,t,"set_value",{value:Number(r.value)},r.value)}}
    />
    ${l?W`<span class="row-value">${l}</span>`:F}
  `}(e,i,s);case"boolean":return function(e,t,i){const{disabled:s,empty:n,staged:r}=pt(e,t);return W`
    <label class="switch">
      <input
        type="checkbox"
        role="switch"
        aria-label=${i}
        .checked=${"on"===(r??t.state)}
        .indeterminate=${n}
        ?disabled=${s}
        @change=${i=>{const s=i.target.checked;ut(e,t,s?"turn_on":"turn_off",{},s?"on":"off")}}
      />
    </label>
  `}(e,i,s);case"select":return function(e,t,i){const{disabled:s,empty:n,staged:r}=pt(e,t),o=mt(t,"options",[]),a=r??t.state;return W`
    <select
      class="select-input"
      aria-label=${i}
      ?disabled=${s}
      @change=${i=>{const s=i.target.value;ut(e,t,"select_option",{option:s},s)}}
    >
      ${n?W`<option value="" selected disabled>${"—"}</option>`:F}
      ${o.map(e=>W`
          <option value=${e} ?selected=${e===a}>
            ${e}
          </option>
        `)}
    </select>
  `}(e,i,s);case"text":return function(e,t,i){const{disabled:s,empty:n,staged:r}=pt(e,t),o=t.attributes.pattern;return W`
    <input
      class="text-input"
      type=${"password"===mt(t,"mode","text")?"password":"text"}
      aria-label=${i}
      minlength=${mt(t,"min",0)}
      maxlength=${mt(t,"max",255)}
      pattern=${o??F}
      .value=${n?"":r??t.state}
      ?disabled=${s}
      @change=${i=>{const s=i.target.value;ut(e,t,"set_value",{value:s},s)}}
    />
  `}(e,i,s);case"date":return ft(e,i,s,"date");case"time":return ft(e,i,s,"time");case"datetime":return ft(e,i,s,"datetime");default:return W`<span class="row-value muted">
        ${ot(e.hass,"not_editable")}
      </span>`}}function vt(e,t){const i=e.config.values.parameters,s=new Map((i??[]).map(e=>[e.parameter,e]));return function(e,t){if(!t)return e.parameters;const i=new Map(e.parameters.map(e=>[e.key,e]));return t.map(e=>i.get(e)).filter(e=>void 0!==e)}(t,i?i.map(e=>e.parameter):null).map(e=>{const t=s.get(e.key);return{parameter:e,label:t?.name??e.name,icon:t?.icon}})}function bt(e,t,i){if(!i)return F;const s=!1===t.icon?void 0:t.icon??(e.config.values.icons?Le(e.hass,t.parameter.entity)?.attributes.icon:void 0);return W`<span class="row-icon">${ct(s)}</span>`}function gt(e,t,i){const{text:s,muted:n}=function(e,t){const i=Le(e.hass,t.entity);return i?i.state===Re?{text:ot(e.hass,"not_set"),muted:!0}:De(i.state)?{text:ot(e.hass,"unavailable"),muted:!0}:{text:Ie(e.hass,i),muted:!1}:{text:ot(e.hass,"unavailable"),muted:!0}}(e,t.parameter);return W`
    <div class="row">
      <div class="row-label">
        ${bt(e,t,i)}<span>${t.label}</span>
      </div>
      <div class="row-value ${n?"muted":""}">${s}</div>
    </div>
  `}function yt(e,t,i,s,n){const r=i?t.parameter.editors[i]:void 0,o=Le(e.hass,r),a=function(e,t){return"number"===e&&void 0!==t&&"slider"===mt(t,"mode","box")}(t.parameter.type,o);return W`
    <div class="row ${a?"wide":""}">
      <div class="row-label">
        ${bt(e,t,n)}<span>${s}</span>
      </div>
      <div class="row-control">
        ${_t(e,t.parameter.type,o,s)}
      </div>
    </div>
  `}function $t(e){if(!e.config.values.visible)return F;const t=e.subject.preset,i=vt(e,t);if(!i.length)return W`<div class="section note">
      ${ot(e.hass,"no_parameters")}
    </div>`;const s=null===e.subject.presetMode?W`<div class="note warning">${ot(e.hass,"orphaned")}</div>`:F,n=function(e,t){return e.config.values.icons||t.some(e=>"string"==typeof e.icon)}(e,i),{editor:r}=e.config,o=e.draft.size?function(e){return W`
    <div class="toolbar">
      <span class="toolbar-label"></span>
      <button class="apply" type="button" @click=${()=>e.apply()}>
        ${ot(e.hass,"apply")}
      </button>
    </div>
  `}(e):F;if(!r.enabled)return W`
      <div class="section rows">
        ${s}${i.map(t=>gt(e,t,n))}
      </div>
    `;if("all"===r.mode){const t=Ke(e.subject);return W`
      <div class="section rows">
        ${s}
        ${i.map(i=>W`
            <div class="group-label">${i.label}</div>
            ${t.map(t=>yt(e,i,t.key,t.name,n))}
          `)}
        ${o}
      </div>
    `}if("active"===r.mode){const t=Je(e.hass,e.subject);return W`
      <div class="section rows">
        ${s}
        ${i.map(i=>yt(e,i,t,i.label,n))}
        ${o}
      </div>
    `}const a=e.editMode;return W`
    <div class="section rows">
      ${s}${function(e){const t=Ke(e.subject);if(!t.length)return F;const i=ot(e.hass,"mode"),s=e.editMode;return"dropdown"===e.config.editor.style?W`
      <div class="row">
        <div class="row-label"><span>${i}:</span></div>
        <div class="row-control">
          <select
            class="select-input"
            aria-label=${i}
            @change=${t=>{const i=t.target.value;e.selectEditMode(""===i?null:i)}}
          >
            <option value="" ?selected=${null===s}>
              ${ot(e.hass,"active")}
            </option>
            ${t.map(e=>W`
                <option value=${e.key} ?selected=${e.key===s}>
                  ${e.name}
                </option>
              `)}
          </select>
        </div>
      </div>
    `:W`
    <div class="row">
      <div class="row-label"><span>${i}:</span></div>
      <div class="row-control">
        <div class="chips secondary" role="group" aria-label=${i}>
          <button
            class="chip"
            type="button"
            aria-pressed=${null===s?"true":"false"}
            @click=${()=>e.selectEditMode(null)}
          >
            <span>${ot(e.hass,"active")}</span>
          </button>
          ${t.map(t=>W`
              <button
                class="chip"
                type="button"
                aria-pressed=${t.key===s?"true":"false"}
                @click=${()=>e.selectEditMode(t.key)}
              >
                <span>${t.name}</span>
              </button>
            `)}
        </div>
      </div>
    </div>
  `}(e)}
      ${null===a?i.map(t=>gt(e,t,n)):i.map(t=>yt(e,t,a,t.label,n))}
      ${o}
    </div>
  `}function wt(e,t){const{hass:i,subject:s}=e;switch(t){case"preset_mode":return s.presetMode?`${ot(i,"preset_mode")}: ${s.presetMode.name}`:ot(i,"orphaned");case"blueprint":return s.blueprint?`${ot(i,"blueprint")}: ${s.blueprint.name}`:null;case"source":{const e=s.presetMode?.source_entity??null;if(!e)return null;const t=i.states[e];return`${ot(i,"source")}: ${t?.attributes.friendly_name??e}`}case"last_changed":{const e=Le(i,Ve(s));return e?`${ot(i,"changed")}: ${function(e,t){const i=new Date(t).getTime();if(Number.isNaN(i))return"";const s=Math.round((i-Date.now())/1e3),n=[["year",31536e3],["month",2592e3],["day",86400],["hour",3600],["minute",60]],r=new Intl.RelativeTimeFormat(e.language||"en",{numeric:"auto"});for(const[e,t]of n)if(Math.abs(s)>=t)return r.format(Math.round(s/t),e);return r.format(Math.round(s),"second")}(i,e.last_changed)}`:null}default:return null}}const xt={action:"more-info"};let At=class extends ae{constructor(){super(...arguments),this._draft=new Map,this._watched=[],this._held=!1,this._lastTap=0}setConfig(e){this._config=Se(e),this._viewMode=void 0,this._draft=new Map,this._watched=[]}static getConfigElement(){return document.createElement(`${e}-editor`)}static async getStubConfig(t){const i=Ue(t)??await Oe(t),s=i.presets.find(e=>e.entities.active_mode)?.entities.active_mode;return{type:`custom:${e}`,entity:s??""}}set hass(e){const t=this._hass;if(this._hass=e,!t)return this.requestUpdate(),void this._load();if(t.language===e.language&&t.themes===e.themes){for(const i of this._watched)if(t.states[i]!==e.states[i])return void this.requestUpdate()}else this.requestUpdate()}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),this._load()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe?.(),this._unsubscribe=void 0,this._clearTimers()}async _load(){this._hass&&!this._unsubscribe&&(this._unsubscribe=ze(this._hass,e=>{this._structure=e}),this._structure=await Oe(this._hass))}getCardSize(){const e=this._config;if(!e)return 2;let t=e.header.visible?1:0;return"never"!==e.modes.visible&&(t+=1),e.values.visible&&(t+=2),e.footer.visible&&(t+=1),Math.max(1,t)}getGridOptions(){return{columns:12,min_columns:6}}get _tapAction(){return this._config?.tap_action??xt}_clearTimers(){this._holdTimer&&clearTimeout(this._holdTimer),this._tapTimer&&clearTimeout(this._tapTimer),this._errorTimer&&clearTimeout(this._errorTimer),this._holdTimer=this._tapTimer=this._errorTimer=void 0}_headerDown(e){this._held=!1,We(this._config?.hold_action)&&(this._holdTimer=setTimeout(()=>{this._held=!0,this._run(this._config?.hold_action,e)},500))}_headerUp(){this._holdTimer&&clearTimeout(this._holdTimer),this._holdTimer=void 0}_headerClick(e){if(this._held)return void(this._held=!1);const t=this._config?.double_tap_action;if(!We(t))return void this._run(this._tapAction,e);const i=Date.now();if(i-this._lastTap<250)return this._tapTimer&&clearTimeout(this._tapTimer),this._tapTimer=void 0,this._lastTap=0,void this._run(t,e);this._lastTap=i,this._tapTimer=setTimeout(()=>{this._tapTimer=void 0,this._run(this._tapAction,e)},250)}_run(e,t){if(!this._hass)return;const i=t.preset.entities.active_mode;this._call(qe(this,this._hass,e,i??this._config?.entity))}_apply(){if(!this._hass||!this._draft.size)return;const e=this._hass,t=[...this._draft].map(([t,i])=>e.callService(t.split(".",1)[0],i.service,i.data,{entity_id:t}));this._draft=new Map,this._viewMode=void 0,this._call(Promise.all(t))}_call(e){e.then(()=>{void 0!==this._error&&(this._error=void 0)},e=>{this._error=this._messageOf(e),this._errorTimer&&clearTimeout(this._errorTimer),this._errorTimer=setTimeout(()=>{this._errorTimer=void 0,this._error=void 0},6e3)})}_messageOf(e){if("string"==typeof e)return e;if(e&&"object"==typeof e){const t=e,i=t.body;for(const e of[t.message,i?.message,t.error])if("string"==typeof e&&e)return e}return String(e)}willUpdate(e){super.willUpdate(e);const t=this._subject;this._watched=t?function(e){const t=tt(e.preset);return e.presetMode&&t.push(...it(e.presetMode)),t}(t):[]}get _subject(){return this._config&&this._structure?st(this._structure,this._config.entity):null}_viewedMode(e){if(void 0!==this._viewMode)return this._viewMode;const t=this._config?.editor.default_mode,i=Ke(e);return t&&i.some(e=>e.key===t)?t:null}render(){const e=this._config,t=this._hass;if(!e||!t)return F;if(!this._structure)return this._shell(this._skeleton());const i=this._subject;if(!i){let i;return i=this._structure.preset_modes.length+this._structure.presets.length?function(e,t){return e.preset_modes.some(e=>it(e).includes(t))}(this._structure,e.entity)?ot(t,"not_a_preset",{entity:e.entity}):ot(t,"not_found",{entity:e.entity}):ot(t,"not_set_up"),this._shell(this._alert(i))}const s={hass:t,config:e,subject:i,host:this,editMode:this._viewedMode(i),selectEditMode:e=>{this._viewMode=e},call:e=>this._call(e),draft:this._draft,stage:(e,t)=>{this._draft=new Map(this._draft).set(e,t)},apply:()=>this._apply(),tappable:We(this._tapAction)||We(e.hold_action),onHeaderDown:()=>this._headerDown(i),onHeaderUp:()=>this._headerUp(),onHeaderClick:()=>this._headerClick(i)};return this._shell(W`
      ${lt(s)} ${ht(s)} ${$t(s)}
      ${function(e){if(!e.config.footer.visible)return F;const t=e.config.footer.content.map(t=>wt(e,t)).filter(e=>null!==e);return t.length?W`
    <div class="section footer">
      ${t.map(e=>W`<span>${e}</span>`)}
    </div>
  `:F}(s)}
      ${this._error?W`<div class="section inline-error" role="alert">${this._error}</div>`:F}
    `)}_shell(e){return W`<ha-card>${e}</ha-card>`}_skeleton(){return W`
      <div class="section rows" aria-busy="true" aria-label=${ot(this._hass,"loading")}>
        <div class="skeleton" style="width:45%"></div>
        <div class="skeleton" style="width:70%"></div>
      </div>
    `}_alert(e){return Fe("ha-alert")?W`<ha-alert alert-type="warning">${e}</ha-alert>`:W`<div class="fallback-alert" role="alert">${e}</div>`}};At.styles=at,t([ue()],At.prototype,"_config",void 0),t([ue()],At.prototype,"_structure",void 0),t([ue()],At.prototype,"_viewMode",void 0),t([ue()],At.prototype,"_draft",void 0),t([ue()],At.prototype,"_error",void 0),At=t([le(e)],At);const kt={entity:"Entity",header:"Header",modes:"Modes",values:"Values",editor:"Editing",footer:"Footer",actions:"Actions",visible:"Show",automatic:"Automatic switch",title:"Title",subtitle:"Subtitle",icon:"Icon",icon_color:"Icon colour",style:"Style",icons:"Show icons",parameters:"Parameters",parameters_note:"Parameters",enabled:"Editable",mode:"Which mode",default_mode:"Start on",content:"Content",tap_action:"Tap",hold_action:"Hold",double_tap_action:"Double tap"},Et=["more-info","navigate","url","perform-action","none"];function St(e){return{selector:{select:{mode:"dropdown",options:e.map(([e,t])=>({value:e,label:t}))}}}}let Mt=class extends ae{constructor(){super(...arguments),this._config={},this._label=e=>e.name&&kt[e.name]||e.title||e.name||""}set hass(e){this._hass=e,this._structure??=Ue(e),this._load(),this.requestUpdate()}get hass(){return this._hass}setConfig(e){this._config=e}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe?.(),this._unsubscribe=void 0}async _load(){this._hass&&!this._unsubscribe&&(this._unsubscribe=ze(this._hass,e=>{this._structure=e}),this._structure=await Oe(this._hass))}_entityPicker(){const e=(this._structure?.presets??[]).map(e=>e.entities.active_mode).filter(e=>Boolean(e));return e.length?{include_entities:e}:{integration:"preset_manager"}}_hasParameterOverrides(){const e=this._config.values,t=e?.parameters;return Array.isArray(t)&&t.some(e=>"string"!=typeof e)}get _subject(){const e=this._config.entity;return this._structure&&"string"==typeof e&&e?st(this._structure,e):null}_schema(e){const t=e?e.preset.modes:[],i=[{name:"entity",required:!0,selector:{entity:this._entityPicker()}},{type:"expandable",name:"header",title:kt.header,schema:[{name:"visible",selector:{boolean:{}}},{name:"automatic",selector:{boolean:{}}},{name:"title",selector:{text:{}}},{name:"subtitle",selector:{text:{}}},{name:"icon",selector:{icon:{}}},{name:"icon_color",selector:{ui_color:{}}}]},{type:"expandable",name:"modes",title:kt.modes,schema:[{name:"visible",...St([["always","Always"],["never","Never"],["manual","While the mode can be set by hand"]])},...t.some(e=>e.icon)?[{name:"icons",selector:{boolean:{}}}]:[]]}];if(e){const s=e.preset.parameters.map(e=>({value:e.key,label:e.name}));i.push({type:"expandable",name:"values",title:kt.values,schema:[{name:"visible",selector:{boolean:{}}},this._hasParameterOverrides()?{name:"parameters_note",type:"constant",value:"Renamed parameters are edited in YAML."}:{name:"parameters",selector:{select:{multiple:!0,mode:"list",options:s}}},{name:"icons",selector:{boolean:{}}}]},{type:"expandable",name:"editor",title:kt.editor,schema:[{name:"enabled",selector:{boolean:{}}},{name:"mode",...St([["picker","Pick a mode in the card"],["active","The active mode"],["all","Every mode"]])},{name:"style",...St([["chips","Chips"],["dropdown","Dropdown"]])},{name:"default_mode",...St(t.map(e=>[e.key,e.name]))}]})}return i.push({type:"expandable",name:"footer",title:kt.footer,schema:[{name:"visible",selector:{boolean:{}}},{name:"content",selector:{select:{multiple:!0,mode:"list",options:[{value:"preset_mode",label:"Preset mode"},{value:"blueprint",label:"Blueprint"},{value:"source",label:"Source entity"},{value:"last_changed",label:"Last change"}]}}}]},{type:"expandable",title:kt.actions,schema:[{name:"tap_action",selector:{ui_action:{actions:Et}}},{name:"hold_action",selector:{ui_action:{actions:Et}}},{name:"double_tap_action",selector:{ui_action:{actions:Et}}}]}),i}_formData(){try{const t=Se({type:`custom:${e}`,...this._config,entity:this._config.entity??"sensor.placeholder"});return{...t,entity:this._config.entity??"",values:{...t.values,parameters:this._config.values?.parameters}}}catch(e){return{...this._config}}}_valueChanged(e){e.stopPropagation();Be(this,"config-changed",{config:Me({...e.detail.value})})}render(){if(!this._hass)return F;const e=this._subject;return W`
      <ha-form
        .hass=${this._hass}
        .data=${this._formData()}
        .schema=${this._schema(e)}
        .computeLabel=${this._label}
        @value-changed=${this._valueChanged}
      ></ha-form>
      ${this._config.entity&&!e&&this._structure?W`<p style="color: var(--error-color)">
            ${ot(this._hass,"not_found",{entity:String(this._config.entity)})}
          </p>`:F}
    `}};t([ue()],Mt.prototype,"_config",void 0),t([ue()],Mt.prototype,"_structure",void 0),Mt=t([le(`${e}-editor`)],Mt),window.customCards=window.customCards??[],window.customCards.some(t=>t.type===e)||window.customCards.push({type:e,name:"Preset Manager",description:"The values of a preset, or the modes of a preset mode, with the mode it is on right now.",preview:!1,documentationURL:"https://github.com/julezdean/ha-preset-manager"}),console.info("%c PRESET-MANAGER-CARD %c 0.4.0-beta.7 ","color: white; background: #03a9f4; font-weight: 700;","color: #03a9f4; background: white; font-weight: 700;");

const e="preset-manager-card";function t(e,t,s,i){var n,r=arguments.length,o=r<3?t:null===i?i=Object.getOwnPropertyDescriptor(t,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)o=Reflect.decorate(e,t,s,i);else for(var a=e.length-1;a>=0;a--)(n=e[a])&&(o=(r<3?n(o):r>3?n(t,s,o):n(t,s))||o);return r>3&&o&&Object.defineProperty(t,s,o),o}"function"==typeof SuppressedError&&SuppressedError;const s=globalThis,i=s.ShadowRoot&&(void 0===s.ShadyCSS||s.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,n=Symbol(),r=new WeakMap;let o=class{constructor(e,t,s){if(this._$cssResult$=!0,s!==n)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(i&&void 0===e){const s=void 0!==t&&1===t.length;s&&(e=r.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),s&&r.set(t,e))}return e}toString(){return this.cssText}};const a=i?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const s of e.cssRules)t+=s.cssText;return(e=>new o("string"==typeof e?e:e+"",void 0,n))(t)})(e):e,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:u,getPrototypeOf:p}=Object,m=globalThis,f=m.trustedTypes,_=f?f.emptyScript:"",v=m.reactiveElementPolyfillSupport,b=(e,t)=>e,g={toAttribute(e,t){switch(t){case Boolean:e=e?_:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let s=e;switch(t){case Boolean:s=null!==e;break;case Number:s=null===e?null:Number(e);break;case Object:case Array:try{s=JSON.parse(e)}catch(e){s=null}}return s}},$=(e,t)=>!c(e,t),y={attribute:!0,type:String,converter:g,reflect:!1,useDefault:!1,hasChanged:$};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=y){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(e,s,t);void 0!==i&&l(this.prototype,e,i)}}static getPropertyDescriptor(e,t,s){const{get:i,set:n}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:i,set(t){const r=i?.call(this);n?.call(this,t),this.requestUpdate(e,r,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??y}static _$Ei(){if(this.hasOwnProperty(b("elementProperties")))return;const e=p(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(b("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(b("properties"))){const e=this.properties,t=[...h(e),...u(e)];for(const s of t)this.createProperty(s,e[s])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,s]of t)this.elementProperties.set(e,s)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const s=this._$Eu(e,t);void 0!==s&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const s=new Set(e.flat(1/0).reverse());for(const e of s)t.unshift(a(e))}else void 0!==e&&t.push(a(e));return t}static _$Eu(e,t){const s=t.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const s of t.keys())this.hasOwnProperty(s)&&(e.set(s,this[s]),delete this[s]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{if(i)e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const i of t){const t=document.createElement("style"),n=s.litNonce;void 0!==n&&t.setAttribute("nonce",n),t.textContent=i.cssText,e.appendChild(t)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,s){this._$AK(e,s)}_$ET(e,t){const s=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,s);if(void 0!==i&&!0===s.reflect){const n=(void 0!==s.converter?.toAttribute?s.converter:g).toAttribute(t,s.type);this._$Em=e,null==n?this.removeAttribute(i):this.setAttribute(i,n),this._$Em=null}}_$AK(e,t){const s=this.constructor,i=s._$Eh.get(e);if(void 0!==i&&this._$Em!==i){const e=s.getPropertyOptions(i),n="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:g;this._$Em=i;const r=n.fromAttribute(t,e.type);this[i]=r??this._$Ej?.get(i)??r,this._$Em=null}}requestUpdate(e,t,s,i=!1,n){if(void 0!==e){const r=this.constructor;if(!1===i&&(n=this[e]),s??=r.getPropertyOptions(e),!((s.hasChanged??$)(n,t)||s.useDefault&&s.reflect&&n===this._$Ej?.get(e)&&!this.hasAttribute(r._$Eu(e,s))))return;this.C(e,t,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:s,reflect:i,wrapped:n},r){s&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,r??t??this[e]),!0!==n||void 0!==r)||(this._$AL.has(e)||(this.hasUpdated||s||(t=void 0),this._$AL.set(e,t)),!0===i&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,s]of e){const{wrapped:e}=s,i=this[t];!0!==e||this._$AL.has(t)||void 0===i||this.C(t,void 0,s,i)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[b("elementProperties")]=new Map,w[b("finalized")]=new Map,v?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,A=e=>e,k=x.trustedTypes,E=k?k.createPolicy("lit-html",{createHTML:e=>e}):void 0,S="$lit$",M=`lit$${Math.random().toFixed(9).slice(2)}$`,T="?"+M,P=`<${T}>`,C=document,j=()=>C.createComment(""),O=e=>null===e||"object"!=typeof e&&"function"!=typeof e,U=Array.isArray,N="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,z=/-->/g,R=/>/g,D=RegExp(`>|${N}(?:([^\\s"'>=/]+)(${N}*=${N}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),L=/'/g,B=/"/g,I=/^(?:script|style|textarea|title)$/i,W=(e=>(t,...s)=>({_$litType$:e,strings:t,values:s}))(1),q=Symbol.for("lit-noChange"),V=Symbol.for("lit-nothing"),F=new WeakMap,J=C.createTreeWalker(C,129);function K(e,t){if(!U(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(t):t}const G=(e,t)=>{const s=e.length-1,i=[];let n,r=2===t?"<svg>":3===t?"<math>":"",o=H;for(let t=0;t<s;t++){const s=e[t];let a,c,l=-1,d=0;for(;d<s.length&&(o.lastIndex=d,c=o.exec(s),null!==c);)d=o.lastIndex,o===H?"!--"===c[1]?o=z:void 0!==c[1]?o=R:void 0!==c[2]?(I.test(c[2])&&(n=RegExp("</"+c[2],"g")),o=D):void 0!==c[3]&&(o=D):o===D?">"===c[0]?(o=n??H,l=-1):void 0===c[1]?l=-2:(l=o.lastIndex-c[2].length,a=c[1],o=void 0===c[3]?D:'"'===c[3]?B:L):o===B||o===L?o=D:o===z||o===R?o=H:(o=D,n=void 0);const h=o===D&&e[t+1].startsWith("/>")?" ":"";r+=o===H?s+P:l>=0?(i.push(a),s.slice(0,l)+S+s.slice(l)+M+h):s+M+(-2===l?t:h)}return[K(e,r+(e[s]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),i]};class X{constructor({strings:e,_$litType$:t},s){let i;this.parts=[];let n=0,r=0;const o=e.length-1,a=this.parts,[c,l]=G(e,t);if(this.el=X.createElement(c,s),J.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(i=J.nextNode())&&a.length<o;){if(1===i.nodeType){if(i.hasAttributes())for(const e of i.getAttributeNames())if(e.endsWith(S)){const t=l[r++],s=i.getAttribute(e).split(M),o=/([.?@])?(.*)/.exec(t);a.push({type:1,index:n,name:o[2],strings:s,ctor:"."===o[1]?te:"?"===o[1]?se:"@"===o[1]?ie:ee}),i.removeAttribute(e)}else e.startsWith(M)&&(a.push({type:6,index:n}),i.removeAttribute(e));if(I.test(i.tagName)){const e=i.textContent.split(M),t=e.length-1;if(t>0){i.textContent=k?k.emptyScript:"";for(let s=0;s<t;s++)i.append(e[s],j()),J.nextNode(),a.push({type:2,index:++n});i.append(e[t],j())}}}else if(8===i.nodeType)if(i.data===T)a.push({type:2,index:n});else{let e=-1;for(;-1!==(e=i.data.indexOf(M,e+1));)a.push({type:7,index:n}),e+=M.length-1}n++}}static createElement(e,t){const s=C.createElement("template");return s.innerHTML=e,s}}function Y(e,t,s=e,i){if(t===q)return t;let n=void 0!==i?s._$Co?.[i]:s._$Cl;const r=O(t)?void 0:t._$litDirective$;return n?.constructor!==r&&(n?._$AO?.(!1),void 0===r?n=void 0:(n=new r(e),n._$AT(e,s,i)),void 0!==i?(s._$Co??=[])[i]=n:s._$Cl=n),void 0!==n&&(t=Y(e,n._$AS(e,t.values),n,i)),t}class Z{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:s}=this._$AD,i=(e?.creationScope??C).importNode(t,!0);J.currentNode=i;let n=J.nextNode(),r=0,o=0,a=s[0];for(;void 0!==a;){if(r===a.index){let t;2===a.type?t=new Q(n,n.nextSibling,this,e):1===a.type?t=new a.ctor(n,a.name,a.strings,this,e):6===a.type&&(t=new ne(n,this,e)),this._$AV.push(t),a=s[++o]}r!==a?.index&&(n=J.nextNode(),r++)}return J.currentNode=C,i}p(e){let t=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(e,s,t),t+=s.strings.length-2):s._$AI(e[t])),t++}}class Q{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,s,i){this.type=2,this._$AH=V,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=Y(this,e,t),O(e)?e===V||null==e||""===e?(this._$AH!==V&&this._$AR(),this._$AH=V):e!==this._$AH&&e!==q&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>U(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==V&&O(this._$AH)?this._$AA.nextSibling.data=e:this.T(C.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:s}=e,i="number"==typeof s?this._$AC(e):(void 0===s.el&&(s.el=X.createElement(K(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(t);else{const e=new Z(i,this),s=e.u(this.options);e.p(t),this.T(s),this._$AH=e}}_$AC(e){let t=F.get(e.strings);return void 0===t&&F.set(e.strings,t=new X(e)),t}k(e){U(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let s,i=0;for(const n of e)i===t.length?t.push(s=new Q(this.O(j()),this.O(j()),this,this.options)):s=t[i],s._$AI(n),i++;i<t.length&&(this._$AR(s&&s._$AB.nextSibling,i),t.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=A(e).nextSibling;A(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class ee{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,s,i,n){this.type=1,this._$AH=V,this._$AN=void 0,this.element=e,this.name=t,this._$AM=i,this.options=n,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=V}_$AI(e,t=this,s,i){const n=this.strings;let r=!1;if(void 0===n)e=Y(this,e,t,0),r=!O(e)||e!==this._$AH&&e!==q,r&&(this._$AH=e);else{const i=e;let o,a;for(e=n[0],o=0;o<n.length-1;o++)a=Y(this,i[s+o],t,o),a===q&&(a=this._$AH[o]),r||=!O(a)||a!==this._$AH[o],a===V?e=V:e!==V&&(e+=(a??"")+n[o+1]),this._$AH[o]=a}r&&!i&&this.j(e)}j(e){e===V?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class te extends ee{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===V?void 0:e}}class se extends ee{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==V)}}class ie extends ee{constructor(e,t,s,i,n){super(e,t,s,i,n),this.type=5}_$AI(e,t=this){if((e=Y(this,e,t,0)??V)===q)return;const s=this._$AH,i=e===V&&s!==V||e.capture!==s.capture||e.once!==s.once||e.passive!==s.passive,n=e!==V&&(s===V||i);i&&this.element.removeEventListener(this.name,this,s),n&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ne{constructor(e,t,s){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(e){Y(this,e)}}const re=x.litHtmlPolyfillSupport;re?.(X,Q),(x.litHtmlVersions??=[]).push("3.3.3");const oe=globalThis;class ae extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,s)=>{const i=s?.renderBefore??t;let n=i._$litPart$;if(void 0===n){const e=s?.renderBefore??null;i._$litPart$=n=new Q(t.insertBefore(j(),e),e,void 0,s??{})}return n._$AI(e),n})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return q}}ae._$litElement$=!0,ae.finalized=!0,oe.litElementHydrateSupport?.({LitElement:ae});const ce=oe.litElementPolyfillSupport;ce?.({LitElement:ae}),(oe.litElementVersions??=[]).push("4.2.2");const le=e=>(t,s)=>{void 0!==s?s.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)},de={attribute:!0,type:String,converter:g,reflect:!1,hasChanged:$},he=(e=de,t,s)=>{const{kind:i,metadata:n}=s;let r=globalThis.litPropertyMetadata.get(n);if(void 0===r&&globalThis.litPropertyMetadata.set(n,r=new Map),"setter"===i&&((e=Object.create(e)).wrapped=!0),r.set(s.name,e),"accessor"===i){const{name:i}=s;return{set(s){const n=t.get.call(this);t.set.call(this,s),this.requestUpdate(i,n,e,!0,s)},init(t){return void 0!==t&&this.C(i,void 0,e,t),t}}}if("setter"===i){const{name:i}=s;return function(s){const n=this[i];t.call(this,s),this.requestUpdate(i,n,e,!0,s)}}throw Error("Unsupported decorator location: "+i)};function ue(e){return function(e){return(t,s)=>"object"==typeof s?he(e,t,s):((e,t,s)=>{const i=t.hasOwnProperty(s);return t.constructor.createProperty(s,e),i?Object.getOwnPropertyDescriptor(t,s):void 0})(e,t,s)}({...e,state:!0,attribute:!1})}class pe extends Error{}const me=["auto","always","never"],fe=["chips","dropdown"],_e=["picker","active","all"],ve=["preset_mode","blueprint","source","last_changed"];function be(e){throw new pe(e)}function ge(e,t){return null==e?{}:(("object"!=typeof e||Array.isArray(e))&&be(`"${t}" has to be a group of options, for example "${t}: {visible: false}"`),e)}function $e(e,t,s){return void 0===e?s:("boolean"!=typeof e&&be(`"${t}" has to be true or false`),e)}function ye(e,t){if(null!=e)return"string"!=typeof e&&be(`"${t}" has to be text`),e}function we(e,t,s,i){return void 0===e?i:("string"==typeof e&&s.includes(e)||be(`"${t}" has to be one of ${s.join(", ")}`),e)}function xe(e,t){if(null!=e)return!1!==e&&("string"!=typeof e&&be(`"${t}" has to be text, or false to hide it`),e)}function Ae(e,t){const s=ge(e,t),i={};for(const[e,n]of Object.entries(s))"string"!=typeof n&&be(`"${t}.${e}" has to be a colour`),i[e]=n;return i}function ke(e){return null==e?[]:(Array.isArray(e)||be('"footer.content" has to be a list'),e.map((e,t)=>we(e,`footer.content[${t}]`,ve,"preset_mode")))}function Ee(e){"object"==typeof e&&null!==e||be("The card needs a configuration.");const t=e,s=ye(t.entity,"entity");s||be('Pick an entity of Preset Manager, for example "entity: sensor.house_mode_mode" or the active mode sensor of a preset.'),s.includes(".")||be(`"${s}" is not an entity id.`);const i=ge(t.header,"header"),n=ge(t.modes,"modes"),r=ge(t.values,"values"),o=ge(t.editor,"editor"),a=ge(t.presets,"presets"),c=ge(t.footer,"footer"),l={type:String(t.type??""),entity:s,header:{visible:$e(i.visible,"header.visible",!0),title:ye(i.title,"header.title"),subtitle:xe(i.subtitle,"header.subtitle"),icon:xe(i.icon,"header.icon"),icon_color:ye(i.icon_color,"header.icon_color")},modes:{visible:we(n.visible,"modes.visible",me,"auto"),style:we(n.style,"modes.style",fe,"chips"),icons:$e(n.icons,"modes.icons",!0),colors:Ae(n.colors,"modes.colors")},values:{visible:$e(r.visible,"values.visible",!0),parameters:(d=r.parameters,null==d?null:(Array.isArray(d)||be('"values.parameters" has to be a list of parameter keys'),d.map((e,t)=>{const s=`values.parameters[${t}]`;if("string"==typeof e)return{parameter:e};"object"==typeof e&&null!==e&&"parameter"in e||be(`"${s}" has to be a parameter key, or a group with a "parameter" key`);const i=ye(e.parameter,`${s}.parameter`);i||be(`"${s}.parameter" is required`);const n={parameter:i},r=ye(e.name,`${s}.name`);void 0!==r&&(n.name=r);const o=xe(e.icon,`${s}.icon`);return void 0!==o&&(n.icon=o),n}))),icons:$e(r.icons,"values.icons",!1)},editor:{enabled:$e(o.enabled,"editor.enabled",!1),mode:we(o.mode,"editor.mode",_e,"picker"),default_mode:ye(o.default_mode,"editor.default_mode")},presets:{visible:$e(a.visible,"presets.visible",!1),values:$e(a.values,"presets.values",!1)},footer:{visible:$e(c.visible,"footer.visible",void 0!==c.content),content:ke(c.content)},tap_action:t.tap_action,hold_action:t.hold_action,double_tap_action:t.double_tap_action};var d;return l.footer.visible&&!l.footer.content.length&&(l.footer.content=["preset_mode"]),l}function Se(t){const s=String(t.type??`custom:${e}`),i="string"==typeof t.entity?t.entity:"";let n={};try{n=Ee({type:s,entity:i||"sensor.placeholder"})}catch(e){n={}}const r={type:s,entity:i};for(const[e,s]of Object.entries(t)){if("type"===e||"entity"===e)continue;const t=Me(s,n[e]);void 0!==t&&(r[e]=t)}return r}function Me(e,t){if(null!=e&&""!==e){if(Array.isArray(e))return e.length?e:void 0;if("object"==typeof e){const s=e,i=t??{},n={};for(const[e,t]of Object.entries(s)){const s=Me(t,i[e]);void 0!==s&&JSON.stringify(s)!==JSON.stringify(i[e])&&(n[e]=s)}return Object.keys(n).length?n:void 0}return e===t?void 0:e}}const Te={preset_modes:[],presets:[],blueprints:[]};class Pe{constructor(e){this._hass=e,this._listeners=new Set,this._unsubscribes=[]}get current(){return this._config}async load(e){return this._hass=e,this._config?this._config:(this._pending||(this._pending=this._fetch()),this._pending)}subscribe(e){return this._listeners.add(e),1===this._listeners.size&&this._watch(),()=>{this._listeners.delete(e),this._listeners.size||this._stop()}}async _fetch(){try{const e=await this._hass.callWS({type:"preset_manager/config"});return this._apply(e),e}catch(e){return this._apply(Te),Te}finally{this._pending=void 0}}_apply(e){const t=JSON.stringify(e);if(t!==this._serialised){this._serialised=t,this._config=e;for(const t of this._listeners)t(e)}}async _watch(){for(const e of["entity_registry_updated","device_registry_updated"])try{const t=await this._hass.connection.subscribeEvents(()=>this._scheduleRefresh(),e);this._listeners.size?this._unsubscribes.push(()=>{t()}):t()}catch(e){}}_scheduleRefresh(){this._timer&&clearTimeout(this._timer),this._timer=setTimeout(()=>{this._timer=void 0,this._config=void 0,this._pending=this._fetch()},400)}_stop(){for(this._timer&&clearTimeout(this._timer),this._timer=void 0;this._unsubscribes.length;)this._unsubscribes.pop()()}}const Ce=new WeakMap;function je(e){let t=Ce.get(e.connection);return t||(t=new Pe(e),Ce.set(e.connection,t)),t}function Oe(e){return je(e).load(e)}function Ue(e){return je(e).current}function Ne(e,t){return je(e).subscribe(t)}const He="unavailable",ze="unknown";function Re(e){return void 0===e||e===He||e===ze}function De(e,t){if(e&&t)return e.states[t]}function Le(e,t,s){e.dispatchEvent(new CustomEvent(t,{detail:s,bubbles:!0,composed:!0}))}function Be(e,t){if("function"==typeof e.formatEntityState)return e.formatEntityState(t);const s=t.attributes.unit_of_measurement;return s?`${t.state} ${s}`:t.state}function Ie(e,t){Le(e,"hass-more-info",{entityId:t})}function We(e){return void 0!==e&&"none"!==e.action}async function qe(e,t,s,i){if(!s||"none"===s.action)return;const n=s.entity??i;switch(s.action){case"more-info":return void(n&&Ie(e,n));case"toggle":return void(n&&await t.callService("homeassistant","toggle",{},{entity_id:n}));case"navigate":return void(s.navigation_path&&(r=s.navigation_path,history.pushState(null,"",r),Le(window,"location-changed",{replace:!1})));case"url":return void(s.url_path&&window.open(s.url_path,"_blank","noreferrer"));case"perform-action":case"call-service":{const e=s.perform_action??s.service;if(!e||!e.includes("."))return;const[i,n]=e.split(".",2);return void await t.callService(i,n,s.data??s.service_data??{},s.target)}default:return}var r}function Ve(e){return"undefined"!=typeof customElements&&!!customElements.get(e)}function Fe(e){return"preset_mode"===e.kind?e.presetMode.entities.mode:e.preset.entities.active_mode}function Je(e,t){return function(e){const t=e?.attributes.mode_key;return"string"==typeof t&&t?t:null}(De(e,Fe(t)))}function Ke(e){return"preset_mode"===e.kind?e.presetMode.modes:e.preset.modes}function Ge(e,t){const s=Je(e,t);return s?Ke(t).find(e=>e.key===s)??null:null}function Xe(e,t){const s=De(e,t?.entities.automatic);return!s||Re(s.state)?null:"on"===s.state}function Ye(e,t){return t?t.source_entity?"external":t.entities.active_mode?Xe(e,t)?"automatic":null:"missing":"missing"}function Ze(e,t){return{kind:"preset",preset:t,presetMode:e.preset_modes.find(e=>e.id===t.preset_mode)??null,blueprint:e.blueprints.find(e=>e.id===t.blueprint)??null}}function Qe(e,t){return{kind:"preset_mode",presetMode:t,presets:e.presets.filter(e=>e.preset_mode===t.id)}}function et(e){const t=[];e.entities.active_mode&&t.push(e.entities.active_mode);for(const s of e.parameters)s.entity&&t.push(s.entity),t.push(...Object.values(s.editors));return t}function tt(e){const t=Object.values(e.entities);return e.source_entity&&t.push(e.source_entity),t}function st(e,t){for(const s of e.preset_modes)if(tt(s).includes(t))return Qe(e,s);for(const s of e.presets)if(et(s).includes(t))return Ze(e,s);return null}const it={active_is:"Active: {mode}",automatic:"Automatic",automatic_hint:"Turn the automatic off to set the mode by hand.",blueprint:"Blueprint",changed:"Changed",editing:"Editing",external_hint:"The mode follows {entity}.",follows:"Follows {entity}",loading:"Loading…",no_entity:"Set “entity” to any entity of Preset Manager.",no_mode:"No mode active",no_modes:"This preset mode has no modes yet.",no_parameters:"This preset has no parameters yet.",no_preset_mode:"No preset mode",not_editable:"Not editable here",not_found:"“{entity}” does not belong to Preset Manager.",not_set:"Not set",not_set_up:"Preset Manager is not set up.",orphaned:"Waiting for a preset mode; values do not resolve.",preset_mode:"Preset mode",presets_one:"1 preset",presets_other:"{count} presets",source:"Source",unavailable:"Unavailable"},nt={en:it,de:{active_is:"Aktiv: {mode}",automatic:"Automatik",automatic_hint:"Automatik ausschalten, um den Mode von Hand zu setzen.",blueprint:"Blueprint",changed:"Geändert",editing:"Bearbeitet wird",external_hint:"Der Mode folgt {entity}.",follows:"Folgt {entity}",loading:"Wird geladen…",no_entity:"„entity“ auf eine beliebige Entität von Preset Manager setzen.",no_mode:"Kein Mode aktiv",no_modes:"Dieser Preset Mode hat noch keine Modes.",no_parameters:"Dieses Preset hat noch keine Parameter.",no_preset_mode:"Kein Preset Mode",not_editable:"Hier nicht editierbar",not_found:"„{entity}“ gehört nicht zu Preset Manager.",not_set:"Nicht gesetzt",not_set_up:"Preset Manager ist nicht eingerichtet.",orphaned:"Wartet auf einen Preset Mode; die Werte lösen nicht auf.",preset_mode:"Preset Mode",presets_one:"1 Preset",presets_other:"{count} Presets",source:"Quelle",unavailable:"Nicht verfügbar"}};function rt(e,t,s={}){const i=(e?.language??"en").toLowerCase().split("-")[0];let n=(nt[i]??it)[t]??it[t]??t;for(const[e,t]of Object.entries(s))n=n.replace(`{${e}}`,String(t));return n}function ot(e,t,s,i){return rt(e,1===i?t:s,{count:i})}const at=((e,...t)=>{const s=1===e.length?e[0]:t.reduce((t,s,i)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+e[i+1],e[0]);return new o(s,e,n)})`
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

  .header {
    display: flex;
    align-items: center;
    gap: var(--pm-gap);
  }

  .header.tappable {
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
    flex: 1 1 auto;
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

  .header-end {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    gap: 8px;
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

  .chip:hover:not(:disabled) {
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
`;function ct(e){return e&&Ve("ha-icon")?W`<ha-icon .icon=${e} aria-hidden="true"></ha-icon>`:V}function lt(e){const{visible:t}=e.config.modes;return"never"!==t&&("always"===t||"preset_mode"===e.subject.kind)}function dt(e,t,s){const i=t.entities.active_mode;i&&e.call(e.hass.callService("preset_manager","set_active_mode",{mode:s},{entity_id:i}))}function ht(e){if(!lt(e))return V;const t=Ke(e.subject);if(!t.length)return W`<div class="section note">
      ${rt(e.hass,"no_modes")}
    </div>`;const s=function(e){return e.subject.presetMode}(e),i=Je(e.hass,e.subject),n=null!==Ye(e.hass,s),r=function(e,t){const s=Ye(e.hass,t);if("automatic"===s)return rt(e.hass,"automatic_hint");if("external"===s&&t?.source_entity){const s=e.hass.states[t.source_entity];return rt(e.hass,"external_hint",{entity:s?.attributes.friendly_name??t.source_entity})}return"missing"===s&&"preset"===e.subject.kind?rt(e.hass,"orphaned"):null}(e,s);return W`
    <div class="section">
      ${"dropdown"===e.config.modes.style?function(e,t,s,i,n){return W`
    <select
      class="select-input"
      aria-label=${rt(e.hass,"preset_mode")}
      ?disabled=${n}
      @change=${t=>{const s=t.target.value;i&&dt(e,i,s)}}
    >
      ${null===s?W`<option value="" selected>${rt(e.hass,"no_mode")}</option>`:V}
      ${t.map(e=>W`
          <option value=${e.key} ?selected=${e.key===s}>
            ${e.name}
          </option>
        `)}
    </select>
  `}(e,t,i,s,n):function(e,t,s,i,n){const{config:r}=e;return W`
    <div class="chips" role="group">
      ${t.map(t=>{const o=t.key===s,a=r.modes.colors[t.key];return W`
          <button
            class="chip"
            type="button"
            aria-pressed=${o?"true":"false"}
            ?disabled=${n}
            style=${a?`--pm-chip-color: ${a}`:""}
            @click=${()=>i&&dt(e,i,t.key)}
          >
            ${r.modes.icons?ct(t.icon):V}
            <span>${t.name}</span>
          </button>
        `})}
    </div>
  `}(e,t,i,s,n)}
      ${r?W`<div class="note" style="margin-top:8px">${r}</div>`:V}
    </div>
  `}function ut(e){const{config:t}=e;if(!t.header.visible)return V;const s=function(e){const t=e.config.header.icon;if(!1===t)return null;if(t)return t;const s=Ge(e.hass,e.subject);return s?.icon?s.icon:"preset_mode"===e.subject.kind?"mdi:state-machine":"mdi:tune-variant"}(e),i=!1===t.header.subtitle?null:t.header.subtitle??function(e){const{hass:t,subject:s}=e,i=Ge(t,s),n=i?.name??rt(t,"no_mode");if("preset_mode"===s.kind){const{presetMode:e}=s;if(e.source_entity){const s=t.states[e.source_entity];return`${n} · ${rt(t,"follows",{entity:s?.attributes.friendly_name??e.source_entity})}`}return n}return s.presetMode?`${n} · ${s.presetMode.name}`:`${n} · ${rt(t,"no_preset_mode")}`}(e),n=t.header.icon_color??function(e){const t=Ge(e.hass,e.subject);return t?e.config.modes.colors[t.key]:void 0}(e),{tappable:r}=e,o="preset_mode"===e.subject.kind||lt(e)?function(e){const{hass:t,subject:s}=e,i=s.presetMode;if(!i?.entities.automatic)return V;const n=i.entities.automatic,r=Xe(t,i),o=rt(t,"automatic"),a=e=>e.stopPropagation();return W`
    <label
      class="switch"
      title=${o}
      @click=${a}
      @pointerdown=${a}
      @pointerup=${a}
      @keydown=${a}
    >
      <input
        type="checkbox"
        role="switch"
        aria-label=${o}
        .checked=${!0===r}
        .disabled=${null===r}
        @change=${s=>{const i=s.target.checked;e.call(t.callService("switch",i?"turn_on":"turn_off",{},{entity_id:n}))}}
      />
    </label>
  `}(e):V,a=r&&o===V;return W`
    <div
      class="header section ${r?"tappable":""}"
      style=${n?`--pm-icon-color: ${n}`:""}
      role=${a?"button":V}
      tabindex=${a?"0":V}
      @pointerdown=${()=>e.onHeaderDown()}
      @pointerup=${()=>e.onHeaderUp()}
      @pointercancel=${()=>e.onHeaderUp()}
      @click=${()=>e.onHeaderClick()}
      @keydown=${t=>{!a||"Enter"!==t.key&&" "!==t.key||(t.preventDefault(),e.onHeaderClick())}}
    >
      ${s?W`<div class="icon">${ct(s)}</div>`:V}
      <div class="titles">
        <div class="title">${t.header.title??function(e){return"preset_mode"===e.subject.kind?e.subject.presetMode.name:e.subject.preset.name}(e)}</div>
        ${i?W`<div class="subtitle">${i}</div>`:V}
      </div>
      ${o===V?V:W`<div class="header-end">${o}</div>`}
    </div>
  `}function pt(e,t,s,i){const n=t.entity_id.split(".",1)[0];e.call(e.hass.callService(n,s,i,{entity_id:t.entity_id}))}function mt(e){return{disabled:(t=e.state,void 0===t||t===He),empty:Re(e.state)};var t}function ft(e,t,s){const i=e.attributes[t];return null==i?s:i}function _t(e,t,s,i){const{disabled:n,empty:r}=mt(t);let o=r?"":t.state;return"datetime"===i&&(o=r?"":function(e){const t=new Date(e);if(Number.isNaN(t.getTime()))return"";const s=e=>String(e).padStart(2,"0");return`${t.getFullYear()}-${s(t.getMonth()+1)}-${s(t.getDate())}T${s(t.getHours())}:${s(t.getMinutes())}`}(t.state)),"time"===i&&(o=o.slice(0,5)),W`
    <input
      class="date-input"
      type=${"datetime"===i?"datetime-local":i}
      aria-label=${s}
      .value=${o}
      ?disabled=${n}
      @change=${s=>{const n=s.target.value;n&&pt(e,t,"set_value","date"===i?{date:n}:"time"===i?{time:`${n}:00`}:{datetime:n.replace("T"," ")+":00"})}}
    />
  `}function vt(e,t,s,i){if(!s)return W`<span class="row-value muted">
      ${rt(e.hass,"unavailable")}
    </span>`;switch(t){case"number":return function(e,t,s){const{disabled:i,empty:n}=mt(t),r=ft(t,"min",0),o=ft(t,"max",100),a=ft(t,"step",1),c=t.attributes.unit_of_measurement??"",l=n?"":t.state,d=s=>{const i=s.target.valueAsNumber;Number.isNaN(i)||pt(e,t,"set_value",{value:i})};return"slider"===ft(t,"mode","box")?W`
      <input
        class="slider"
        type="range"
        aria-label=${s}
        min=${r}
        max=${o}
        step=${a}
        .value=${n?String(r):l}
        ?disabled=${i}
        @change=${d}
      />
      <span class="slider-value">
        ${n?"—":`${t.state}${c?` ${c}`:""}`}
      </span>
    `:W`
    <input
      class="number-input"
      type="number"
      inputmode="decimal"
      aria-label=${s}
      min=${r}
      max=${o}
      step=${a}
      .value=${l}
      ?disabled=${i}
      @change=${d}
    />
    ${c?W`<span class="row-value">${c}</span>`:V}
  `}(e,s,i);case"boolean":return function(e,t,s){const{disabled:i,empty:n}=mt(t);return W`
    <label class="switch">
      <input
        type="checkbox"
        role="switch"
        aria-label=${s}
        .checked=${"on"===t.state}
        .indeterminate=${n}
        ?disabled=${i}
        @change=${s=>pt(e,t,s.target.checked?"turn_on":"turn_off",{})}
      />
    </label>
  `}(e,s,i);case"select":return function(e,t,s){const{disabled:i,empty:n}=mt(t),r=ft(t,"options",[]);return W`
    <select
      class="select-input"
      aria-label=${s}
      ?disabled=${i}
      @change=${s=>pt(e,t,"select_option",{option:s.target.value})}
    >
      ${n?W`<option value="" selected disabled>${"—"}</option>`:V}
      ${r.map(e=>W`
          <option value=${e} ?selected=${e===t.state}>
            ${e}
          </option>
        `)}
    </select>
  `}(e,s,i);case"text":return function(e,t,s){const{disabled:i,empty:n}=mt(t),r=t.attributes.pattern;return W`
    <input
      class="text-input"
      type=${"password"===ft(t,"mode","text")?"password":"text"}
      aria-label=${s}
      minlength=${ft(t,"min",0)}
      maxlength=${ft(t,"max",255)}
      pattern=${r??V}
      .value=${n?"":t.state}
      ?disabled=${i}
      @change=${s=>pt(e,t,"set_value",{value:s.target.value})}
    />
  `}(e,s,i);case"date":return _t(e,s,i,"date");case"time":return _t(e,s,i,"time");case"datetime":return _t(e,s,i,"datetime");default:return W`<span class="row-value muted">
        ${rt(e.hass,"not_editable")}
      </span>`}}function bt(e,t){const s=e.config.values.parameters,i=new Map((s??[]).map(e=>[e.parameter,e]));return function(e,t){if(!t)return e.parameters;const s=new Map(e.parameters.map(e=>[e.key,e]));return t.map(e=>s.get(e)).filter(e=>void 0!==e)}(t,s?s.map(e=>e.parameter):null).map(e=>{const t=i.get(e.key);return{parameter:e,label:t?.name??e.name,icon:t?.icon}})}function gt(e,t,s){if(!s)return V;const i=!1===t.icon?void 0:t.icon??(e.config.values.icons?De(e.hass,t.parameter.entity)?.attributes.icon:void 0);return W`<span class="row-icon">${ct(i)}</span>`}function $t(e,t,s){const{text:i,muted:n}=function(e,t){const s=De(e.hass,t.entity);return s?s.state===ze?{text:rt(e.hass,"not_set"),muted:!0}:Re(s.state)?{text:rt(e.hass,"unavailable"),muted:!0}:{text:Be(e.hass,s),muted:!1}:{text:rt(e.hass,"unavailable"),muted:!0}}(e,t.parameter);return W`
    <div class="row">
      <div class="row-label">
        ${gt(e,t,s)}<span>${t.label}</span>
      </div>
      <div class="row-value ${n?"muted":""}">${i}</div>
    </div>
  `}function yt(e,t,s,i,n){const r=s?t.parameter.editors[s]:void 0,o=De(e.hass,r),a=function(e,t){return"number"===e&&void 0!==t&&"slider"===ft(t,"mode","box")}(t.parameter.type,o);return W`
    <div class="row ${a?"wide":""}">
      <div class="row-label">
        ${gt(e,t,n)}<span>${i}</span>
      </div>
      <div class="row-control">
        ${vt(e,t.parameter.type,o,i)}
      </div>
    </div>
  `}function wt(e){if("preset"!==e.subject.kind)return V;if(!e.config.values.visible)return V;const t=e.subject.preset,s=bt(e,t);if(!s.length)return W`<div class="section note">
      ${rt(e.hass,"no_parameters")}
    </div>`;const i=null===e.subject.presetMode?W`<div class="note warning">${rt(e.hass,"orphaned")}</div>`:V,n=function(e,t){return e.config.values.icons||t.some(e=>"string"==typeof e.icon)}(e,s),{editor:r}=e.config;if(!r.enabled)return W`
      <div class="section rows">
        ${i}${s.map(t=>$t(e,t,n))}
      </div>
    `;if("all"===r.mode){const t=Ke(e.subject);return W`
      <div class="section rows">
        ${i}${s.map(s=>W`
            <div class="group-label">${s.label}</div>
            ${t.map(t=>yt(e,s,t.key,t.name,n))}
          `)}
      </div>
    `}const o="active"===r.mode?Je(e.hass,e.subject):e.editMode;return W`
    <div class="section rows">
      ${i}${"picker"===r.mode?function(e){const t=Ke(e.subject);if(t.length<2)return V;const s=Je(e.hass,e.subject),i=t.find(e=>e.key===s);return W`
    <div class="group-label">${rt(e.hass,"editing")}</div>
    <div class="chips" role="group" aria-label=${rt(e.hass,"editing")}>
      ${t.map(t=>W`
          <button
            class="chip"
            type="button"
            aria-pressed=${t.key===e.editMode?"true":"false"}
            @click=${()=>e.selectEditMode(t.key)}
          >
            ${e.config.modes.icons?ct(t.icon):V}
            <span>${t.name}</span>
          </button>
        `)}
    </div>
    ${i&&i.key!==e.editMode?W`<div class="note">
          ${rt(e.hass,"active_is",{mode:i.name})}
        </div>`:V}
  `}(e):V}
      ${s.map(t=>yt(e,t,o,t.label,n))}
    </div>
  `}function xt(e){if("preset_mode"!==e.subject.kind)return V;if(!e.config.presets.visible)return V;const{presets:t}=e.subject;if(!t.length)return W`<div class="section note">
      ${ot(e.hass,"presets_one","presets_other",0)}
    </div>`;const s=e.config.presets.values;return W`
    <div class="section rows">
      ${t.map(t=>{const i=t.entities.active_mode,n=W`
          <button
            class="row-label link-row"
            type="button"
            ?disabled=${!i}
            @click=${()=>i&&Ie(e.host,i)}
          >
            <span>${t.name}</span>
          </button>
        `;if(!s){const t=De(e.hass,i);return W`
            <div class="row">
              ${n}
              <div class="row-value ${t&&!Re(t.state)?"":"muted"}">
                ${t&&!Re(t.state)?t.state:rt(e.hass,"no_mode")}
              </div>
            </div>
          `}return W`
          <div class="group-label">${t.name}</div>
          ${function(e,t){return t.parameters.map(t=>{const s=De(e.hass,t.entity);let i,n=!0;return s?s.state===ze?i=rt(e.hass,"not_set"):Re(s.state)?i=rt(e.hass,"unavailable"):(i=Be(e.hass,s),n=!1):i=rt(e.hass,"unavailable"),W`
      <div class="row">
        <div class="row-label"><span>${t.name}</span></div>
        <div class="row-value ${n?"muted":""}">${i}</div>
      </div>
    `})}(e,t)}
        `})}
    </div>
  `}function At(e,t){const{hass:s,subject:i}=e;switch(t){case"preset_mode":return"preset"===i.kind?i.presetMode?`${rt(s,"preset_mode")}: ${i.presetMode.name}`:rt(s,"orphaned"):ot(s,"presets_one","presets_other",i.presets.length);case"blueprint":return"preset"===i.kind&&i.blueprint?`${rt(s,"blueprint")}: ${i.blueprint.name}`:null;case"source":{const e="preset_mode"===i.kind?i.presetMode.source_entity:null;if(!e)return null;const t=s.states[e];return`${rt(s,"source")}: ${t?.attributes.friendly_name??e}`}case"last_changed":{const e=De(s,Fe(i));return e?`${rt(s,"changed")}: ${function(e,t){const s=new Date(t).getTime();if(Number.isNaN(s))return"";const i=Math.round((s-Date.now())/1e3),n=[["year",31536e3],["month",2592e3],["day",86400],["hour",3600],["minute",60]],r=new Intl.RelativeTimeFormat(e.language||"en",{numeric:"auto"});for(const[e,t]of n)if(Math.abs(i)>=t)return r.format(Math.round(i/t),e);return r.format(Math.round(i),"second")}(s,e.last_changed)}`:null}default:return null}}const kt={action:"more-info"};let Et=class extends ae{constructor(){super(...arguments),this._editModeOverride=null,this._watched=[],this._held=!1,this._lastTap=0}setConfig(e){this._config=Ee(e),this._editModeOverride=null,this._watched=[]}static getConfigElement(){return document.createElement(`${e}-editor`)}static async getStubConfig(t){const s=Ue(t)??await Oe(t),i=s.preset_modes.find(e=>e.entities.mode)?.entities.mode??s.presets.find(e=>e.entities.active_mode)?.entities.active_mode;return{type:`custom:${e}`,entity:i??""}}set hass(e){const t=this._hass;if(this._hass=e,!t)return this.requestUpdate(),void this._load();if(t.language===e.language&&t.themes===e.themes){for(const s of this._watched)if(t.states[s]!==e.states[s])return void this.requestUpdate()}else this.requestUpdate()}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),this._load()}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe?.(),this._unsubscribe=void 0,this._clearTimers()}async _load(){this._hass&&!this._unsubscribe&&(this._unsubscribe=Ne(this._hass,e=>{this._structure=e}),this._structure=await Oe(this._hass))}getCardSize(){const e=this._config;if(!e)return 2;let t=e.header.visible?1:0;const s=this._subject;return"never"!==e.modes.visible&&("always"===e.modes.visible||null===s||"preset_mode"===s.kind)&&(t+=1),e.values.visible&&(t+=2),e.presets.visible&&(t+=2),e.footer.visible&&(t+=1),Math.max(1,t)}getGridOptions(){return{columns:12,min_columns:6}}get _tapAction(){return this._config?.tap_action??kt}_clearTimers(){this._holdTimer&&clearTimeout(this._holdTimer),this._tapTimer&&clearTimeout(this._tapTimer),this._errorTimer&&clearTimeout(this._errorTimer),this._holdTimer=this._tapTimer=this._errorTimer=void 0}_headerDown(e){this._held=!1,We(this._config?.hold_action)&&(this._holdTimer=setTimeout(()=>{this._held=!0,this._run(this._config?.hold_action,e)},500))}_headerUp(){this._holdTimer&&clearTimeout(this._holdTimer),this._holdTimer=void 0}_headerClick(e){if(this._held)return void(this._held=!1);const t=this._config?.double_tap_action;if(!We(t))return void this._run(this._tapAction,e);const s=Date.now();if(s-this._lastTap<250)return this._tapTimer&&clearTimeout(this._tapTimer),this._tapTimer=void 0,this._lastTap=0,void this._run(t,e);this._lastTap=s,this._tapTimer=setTimeout(()=>{this._tapTimer=void 0,this._run(this._tapAction,e)},250)}_run(e,t){if(!this._hass)return;const s="preset_mode"===t.kind?t.presetMode.entities.mode:t.preset.entities.active_mode;this._call(qe(this,this._hass,e,s??this._config?.entity))}_call(e){e.then(()=>{void 0!==this._error&&(this._error=void 0)},e=>{this._error=this._messageOf(e),this._errorTimer&&clearTimeout(this._errorTimer),this._errorTimer=setTimeout(()=>{this._errorTimer=void 0,this._error=void 0},6e3)})}_messageOf(e){if("string"==typeof e)return e;if(e&&"object"==typeof e){const t=e,s=t.body;for(const e of[t.message,s?.message,t.error])if("string"==typeof e&&e)return e}return String(e)}willUpdate(e){super.willUpdate(e);const t=this._subject;this._watched=t?function(e){if("preset_mode"===e.kind){const t=tt(e.presetMode);for(const s of e.presets)t.push(...et(s));return t}const t=et(e.preset);return e.presetMode&&t.push(...tt(e.presetMode)),t}(t):[]}get _subject(){return this._config&&this._structure?st(this._structure,this._config.entity):null}_editMode(e){if(this._editModeOverride)return this._editModeOverride;const t=this._config?.editor.default_mode,s=Ke(e);return t&&s.some(e=>e.key===t)?t:Je(this._hass,e)??s[0]?.key??null}render(){const e=this._config,t=this._hass;if(!e||!t)return V;if(!this._structure)return this._shell(this._skeleton());const s=this._subject;if(!s){const s=this._structure.preset_modes.length+this._structure.presets.length;return this._shell(this._alert(s?rt(t,"not_found",{entity:e.entity}):rt(t,"not_set_up")))}const i={hass:t,config:e,subject:s,host:this,editMode:this._editMode(s),selectEditMode:e=>{this._editModeOverride=e},call:e=>this._call(e),tappable:We(this._tapAction)||We(e.hold_action),onHeaderDown:()=>this._headerDown(s),onHeaderUp:()=>this._headerUp(),onHeaderClick:()=>this._headerClick(s)};return this._shell(W`
      ${ut(i)} ${ht(i)} ${wt(i)}
      ${xt(i)} ${function(e){if(!e.config.footer.visible)return V;const t=e.config.footer.content.map(t=>At(e,t)).filter(e=>null!==e);return t.length?W`
    <div class="section footer">
      ${t.map(e=>W`<span>${e}</span>`)}
    </div>
  `:V}(i)}
      ${this._error?W`<div class="section inline-error" role="alert">${this._error}</div>`:V}
    `)}_shell(e){return W`<ha-card>${e}</ha-card>`}_skeleton(){return W`
      <div class="section rows" aria-busy="true" aria-label=${rt(this._hass,"loading")}>
        <div class="skeleton" style="width:45%"></div>
        <div class="skeleton" style="width:70%"></div>
      </div>
    `}_alert(e){return Ve("ha-alert")?W`<ha-alert alert-type="warning">${e}</ha-alert>`:W`<div class="fallback-alert" role="alert">${e}</div>`}};Et.styles=at,t([ue()],Et.prototype,"_config",void 0),t([ue()],Et.prototype,"_structure",void 0),t([ue()],Et.prototype,"_editModeOverride",void 0),t([ue()],Et.prototype,"_error",void 0),Et=t([le(e)],Et);const St={entity:"Entity",header:"Header",modes:"Modes",values:"Values",editor:"Editing",presets:"Presets",footer:"Footer",actions:"Actions",visible:"Show",title:"Title",subtitle:"Subtitle",icon:"Icon",icon_color:"Icon colour",style:"Style",icons:"Show icons",parameters:"Parameters",parameters_note:"Parameters",enabled:"Editable",mode:"Which mode",default_mode:"Start on",content:"Content",tap_action:"Tap",hold_action:"Hold",double_tap_action:"Double tap"},Mt=["more-info","navigate","url","perform-action","none"];function Tt(e){return{selector:{select:{mode:"dropdown",options:e.map(([e,t])=>({value:e,label:t}))}}}}let Pt=class extends ae{constructor(){super(...arguments),this._config={},this._label=e=>e.name&&St[e.name]||e.title||e.name||""}set hass(e){this._hass=e,this._structure??=Ue(e),this._load(),this.requestUpdate()}get hass(){return this._hass}setConfig(e){this._config=e}disconnectedCallback(){super.disconnectedCallback(),this._unsubscribe?.(),this._unsubscribe=void 0}async _load(){this._hass&&!this._unsubscribe&&(this._unsubscribe=Ne(this._hass,e=>{this._structure=e}),this._structure=await Oe(this._hass))}_entityPicker(){const e=[...(this._structure?.preset_modes??[]).map(e=>e.entities.mode),...(this._structure?.presets??[]).map(e=>e.entities.active_mode)].filter(e=>Boolean(e));return e.length?{include_entities:e}:{integration:"preset_manager"}}_hasParameterOverrides(){const e=this._config.values,t=e?.parameters;return Array.isArray(t)&&t.some(e=>"string"!=typeof e)}get _subject(){const e=this._config.entity;return this._structure&&"string"==typeof e&&e?st(this._structure,e):null}_schema(e){const t="preset"===e?.kind,s="preset_mode"===e?.kind,i=e?"preset_mode"===e.kind?e.presetMode.modes:e.preset.modes:[],n=[{name:"entity",required:!0,selector:{entity:this._entityPicker()}},{type:"expandable",name:"header",title:St.header,schema:[{name:"visible",selector:{boolean:{}}},{name:"title",selector:{text:{}}},{name:"subtitle",selector:{text:{}}},{name:"icon",selector:{icon:{}}},{name:"icon_color",selector:{ui_color:{}}}]},{type:"expandable",name:"modes",title:St.modes,schema:[{name:"visible",...Tt([["auto","Automatic"],["always","Always"],["never","Never"]])},{name:"style",...Tt([["chips","Chips"],["dropdown","Dropdown"]])},{name:"icons",selector:{boolean:{}}}]}];if(t){const t=e.preset.parameters.map(e=>({value:e.key,label:e.name}));n.push({type:"expandable",name:"values",title:St.values,schema:[{name:"visible",selector:{boolean:{}}},this._hasParameterOverrides()?{name:"parameters_note",type:"constant",value:"Renamed parameters are edited in YAML."}:{name:"parameters",selector:{select:{multiple:!0,mode:"list",options:t}}},{name:"icons",selector:{boolean:{}}}]},{type:"expandable",name:"editor",title:St.editor,schema:[{name:"enabled",selector:{boolean:{}}},{name:"mode",...Tt([["picker","Pick a mode in the card"],["active","The active mode"],["all","Every mode"]])},{name:"default_mode",...Tt(i.map(e=>[e.key,e.name]))}]})}return s&&n.push({type:"expandable",name:"presets",title:St.presets,schema:[{name:"visible",selector:{boolean:{}}},{name:"values",selector:{boolean:{}}}]}),n.push({type:"expandable",name:"footer",title:St.footer,schema:[{name:"visible",selector:{boolean:{}}},{name:"content",selector:{select:{multiple:!0,mode:"list",options:[{value:"preset_mode",label:"Preset mode"},{value:"blueprint",label:"Blueprint"},{value:"source",label:"Source entity"},{value:"last_changed",label:"Last change"}]}}}]},{type:"expandable",title:St.actions,schema:[{name:"tap_action",selector:{ui_action:{actions:Mt}}},{name:"hold_action",selector:{ui_action:{actions:Mt}}},{name:"double_tap_action",selector:{ui_action:{actions:Mt}}}]}),n}_formData(){try{const t=Ee({type:`custom:${e}`,...this._config,entity:this._config.entity??"sensor.placeholder"});return{...t,entity:this._config.entity??"",values:{...t.values,parameters:this._config.values?.parameters}}}catch(e){return{...this._config}}}_valueChanged(e){e.stopPropagation();Le(this,"config-changed",{config:Se({...e.detail.value})})}render(){if(!this._hass)return V;const e=this._subject;return W`
      <ha-form
        .hass=${this._hass}
        .data=${this._formData()}
        .schema=${this._schema(e)}
        .computeLabel=${this._label}
        @value-changed=${this._valueChanged}
      ></ha-form>
      ${this._config.entity&&!e&&this._structure?W`<p style="color: var(--error-color)">
            ${rt(this._hass,"not_found",{entity:String(this._config.entity)})}
          </p>`:V}
    `}};t([ue()],Pt.prototype,"_config",void 0),t([ue()],Pt.prototype,"_structure",void 0),Pt=t([le(`${e}-editor`)],Pt),window.customCards=window.customCards??[],window.customCards.some(t=>t.type===e)||window.customCards.push({type:e,name:"Preset Manager",description:"The values of a preset, or the modes of a preset mode, with the mode it is on right now.",preview:!1,documentationURL:"https://github.com/julezdean/ha-preset-manager"}),console.info("%c PRESET-MANAGER-CARD %c 0.3.0b6 ","color: white; background: #03a9f4; font-weight: 700;","color: #03a9f4; background: white; font-weight: 700;");

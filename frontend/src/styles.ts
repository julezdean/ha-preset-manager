/**
 * The card's design system.
 *
 * Every colour, radius and spacing is a token, and every token resolves to a
 * Home Assistant variable. A theme the user installs therefore reaches this
 * card without it knowing anything about the theme, and dark mode needs no
 * code at all. Nothing here is a literal colour except the opacities that
 * tint an accent, which are the same in both modes by construction.
 *
 * The layout rule is one column of rows. There is no breakpoint anywhere:
 * a card three columns wide and a card in a narrow sidebar are the same
 * layout, and the rows wrap rather than shrink.
 */

import { css } from "lit";

export const cardStyles = css`
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
`;

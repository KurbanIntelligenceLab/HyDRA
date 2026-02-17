// Math notation helper for rendering chemical/scientific notation
export const MathNotation = {
  Eads: () => <span>E<sub>ads</sub></span>,
  T50: () => <span>T<sub>50</sub></span>,
  OmegaMinus: () => <span>ω<sup>−</sup></span>,
  OmegaPlus: () => <span>ω<sup>+</sup></span>,
  DeltaNmax: () => <span>ΔN<sub>max</sub></span>,
  Theta: () => <span>θ</span>,
  H2: () => <span>H<sub>2</sub></span>,
  TiO2: () => <span>TiO<sub>2</sub></span>,
};

// Text-only versions for chart labels (Recharts doesn't support JSX in labels)
export const MathText = {
  Eads: 'E_ads',
  T50: 'T_50',
  OmegaMinus: 'ω⁻',
  OmegaPlus: 'ω⁺',
  DeltaNmax: 'ΔN_max',
  Theta: 'θ',
  DEelec: 'ΔE_elec',
  DErep: 'ΔE_rep',
  DEdisp: 'ΔE_disp',
  DEtotal: 'ΔE_total',
};

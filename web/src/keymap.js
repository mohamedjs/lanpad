/* Browser KeyboardEvent.code -> X11 keysym name.
   `code` is the physical key, so it survives layout differences; modifiers are
   forwarded as their own keys, which is what makes Shift/Ctrl/Cmd combos work. */
const NAMED = {
  Enter: 'Return', NumpadEnter: 'Return', Escape: 'Escape', Backspace: 'BackSpace',
  Tab: 'Tab', Space: 'space', CapsLock: 'Caps_Lock', Delete: 'Delete', Insert: 'Insert',
  Minus: 'minus', Equal: 'equal', BracketLeft: 'bracketleft', BracketRight: 'bracketright',
  Backslash: 'backslash', Semicolon: 'semicolon', Quote: 'apostrophe', Comma: 'comma',
  Period: 'period', Slash: 'slash', Backquote: 'grave', IntlBackslash: 'less',
  ShiftLeft: 'Shift_L', ShiftRight: 'Shift_R', ControlLeft: 'Control_L', ControlRight: 'Control_R',
  AltLeft: 'Alt_L', AltRight: 'Alt_R', MetaLeft: 'Super_L', MetaRight: 'Super_R',
  ArrowUp: 'Up', ArrowDown: 'Down', ArrowLeft: 'Left', ArrowRight: 'Right',
  Home: 'Home', End: 'End', PageUp: 'Prior', PageDown: 'Next',
  NumLock: 'Num_Lock', NumpadDivide: 'KP_Divide', NumpadMultiply: 'KP_Multiply',
  NumpadSubtract: 'KP_Subtract', NumpadAdd: 'KP_Add', NumpadDecimal: 'KP_Decimal',
};

export function codeToKeysym(code) {
  if (NAMED[code]) return NAMED[code];
  let m = /^Key([A-Z])$/.exec(code);
  if (m) return m[1].toLowerCase();
  m = /^Digit(\d)$/.exec(code);
  if (m) return m[1];
  m = /^Numpad(\d)$/.exec(code);
  if (m) return 'KP_' + m[1];
  m = /^F(\d{1,2})$/.exec(code);
  if (m) return code;                      // F1..F12 are keysym names already
  return null;                             // unmapped: dropped, never guessed
}

export const ALL_KEYSYMS = [
  ...Object.values(NAMED),
  ...'abcdefghijklmnopqrstuvwxyz0123456789'.split(''),
  ...Array.from({ length: 12 }, (_, i) => 'F' + (i + 1)),
  ...Array.from({ length: 10 }, (_, i) => 'KP_' + i),
];

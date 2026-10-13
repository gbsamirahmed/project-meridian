import js from '@eslint/js';
import globals from 'globals';
export default [
  { files: ['**/*.mjs'], ...js.configs.recommended, languageOptions: { globals: globals.node } },
  { files: ['**/test_browser.mjs', '**/test_opacity.mjs'], languageOptions: { globals: { window: 'readonly', document: 'readonly' } } },
  { files: ['**/demo.js'], ...js.configs.recommended, languageOptions: { globals: globals.browser } },
];

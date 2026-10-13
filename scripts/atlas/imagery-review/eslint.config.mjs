import js from '@eslint/js';
import globals from 'globals';
export default [
  { files: ['**/*.mjs'], ...js.configs.recommended, languageOptions: { globals: globals.node } },
  { files: ['**/demo.js', '**/live.js'], ...js.configs.recommended, languageOptions: { globals: { ...globals.browser, __MAPTILER_KEY__: 'readonly' } } },
  { files: ['**/check_browser.mjs'], languageOptions: { globals: globals.browser } },
];
